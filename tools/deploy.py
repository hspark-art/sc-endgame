#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""빌드 결과물을 웹서버로 올립니다 — FTP 도, SFTP(SSH) 도 됩니다.

    python3 tools/build.py && python3 tools/deploy.py

바뀐 파일만 올립니다. 처음 한 번은 전부 올라가고, 그다음부터는 실제로 달라진
것만 올라가서 몇 초면 끝납니다.

2026-09-21 서버 이전 — starendgame.com 이 전용 서버로 옮겨 갔고 그 서버는
SSH(SFTP)만 열려 있습니다. 예전 카페24 공유호스팅은 FTP 였습니다. 둘 다
됩니다: **22번 포트면 SFTP, 아니면 FTP** 로 알아서 붙습니다.

접속 정보 — 둘 중 편한 쪽으로 (저장소에는 들어가지 않습니다)

  1) data/deploy.json 파일
     {
       "host": "서버주소",
       "user": "계정",
       "password": "비밀번호",
       "remoteDir": "/var/www/사이트폴더",
       "proto": "sftp",
       "port": 22
     }

  2) 환경변수 (GitHub Actions 는 이쪽 — 시크릿으로 넣습니다)
     export SC_FTP_HOST=...   SC_FTP_USER=...   SC_FTP_PASS=...
     export SC_FTP_DIR=/var/www/사이트폴더
     export SC_FTP_PROTO=sftp   SC_FTP_PORT=22

⚠ 비밀번호는 절대 저장소에 적지 마세요. SFTP 는 paramiko 가 필요합니다
  (pip install paramiko). 서버 키는 처음 본 것을 그대로 받아들입니다 —
  배포 전용 계정 + 키 인증으로 바꾸는 편이 안전합니다.

옵션
  --dry-run   올리지 않고 무엇이 올라갈지만 보여 줍니다
  --all       바뀐 것만이 아니라 전부 다시 올립니다
  --no-tls    FTP 서버가 FTPS 를 못 받을 때 (평문 FTP 로 접속)

서버에만 있는 파일(관리자 계정 admin/config.php, 로그 등)은 건드리지 않습니다.
이 스크립트는 지우는 일을 하지 않습니다 — 올리고 덮어쓰기만 합니다.
"""

import argparse
import ftplib
import hashlib
import io
import json
import os
import shutil
import ssl
import sys

# 윈도우 콘솔에서 한글·기호가 깨지거나 터지지 않게 합니다.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

STATE = os.path.join(ROOT, 'data', '.deploy-state.json')

# 웹서버에 올릴 것 / 올리지 않을 것.
# 점으로 시작하는 폴더(.git, .claude 등)는 전부 건너뜁니다.
# 점으로 시작하는 '파일' 중 .nojekyll 과 admin/.htaccess 는 사이트에 필요해서 올립니다.
# 설명 문서(.md)는 사이트 내용이 아니라서 통째로 뺍니다 — 새로 만들어도 안 올라갑니다.
SKIP_DIRS = {'tools', 'node_modules', '__pycache__', 'logs',
             'deploy'}      # 서버 설치 꾸러미(systemd 설정 등) — 사이트 내용이 아닙니다
SKIP_FILES = {'.gitignore', '.deploy-state.json', 'deploy.json',
              '_사진목록.txt'}          # 사진 넣는 법 안내 — 우리끼리 보는 것
SKIP_EXTS = ('.md', '.bat', '.command', '.sh')
# 절대 웹서버로 나가면 안 되는 것.
#   admin/config.php  관리자 계정 (서버에만 있어야 하고 덮어써서도 안 됩니다)
#   data/deploy.json  FTP·SFTP 비밀번호
#   data/youtube.json 유튜브 API 키
#   data/slack.json   슬랙 웹훅 주소 — 이걸 아는 사람은 누구나 채널에 글을 씁니다
# data/ 는 sheets 페이지가 원본 JSON 을 공개하느라 **통째로** 올라갑니다.
# 그 안에 비밀이 들어오면 반드시 여기에 적어야 합니다. slack.json 은 2026-09-21
# 까지 빠져 있어서, 그 파일이 있는 PC 에서 올리면 웹훅이 그대로 공개됐습니다.
NEVER_UPLOAD = {'admin/config.php', 'data/deploy.json', 'data/youtube.json',
                'data/slack.json', 'data/deploy-target.json'}

# 서버에 남아 있으면 안 되는 것 — 올릴 때마다 있으면 지웁니다 (없으면 조용히 넘어감).
# 이 스크립트는 원래 '올리기만' 했지만, 아래 둘은 그냥 둘 수가 없어 예외로 둡니다.
STALE_REMOTE = (
    ('data/slack.json',
     '슬랙 웹훅 주소 — 웹에서 열리면 누구나 우리 채널에 글을 씁니다'),
    ('logs/records-update.log', '갱신 로그 — 사이트에 있을 것이 아닙니다'),
    ('logs/gdoc-import.log', '당첨자 등록 로그 — 사이트에 있을 것이 아닙니다'),
    ('p/byun-heonje.php',
     '변헌제 오타로 생겼던 유령 선수 페이지 (2026-09-21 이전 때 딸려 옴)'),
)


def _tidy(what, v):
    """접속 정보 앞뒤의 공백·줄바꿈을 떼어냅니다.

    시크릿 칸에 붙여넣을 때 줄바꿈이나 공백이 딸려 오는 일이 흔하고, 그러면
    비밀번호가 맞는데도 인증에서 거절당합니다(AuthenticationException).
    화면에 안 보이는 차이라 찾기가 고약해서, 여기서 떼고 떼어냈다고 알립니다.
    값 자체는 절대 찍지 않습니다.
    """
    if not isinstance(v, str):
        return v
    t = v.strip()
    if t != v:
        print('  ! %s 앞뒤에 공백·줄바꿈이 있어 떼어냈습니다' % what)
    return t


def _read_cfg(name):
    try:
        with io.open(os.path.join(ROOT, 'data', name), encoding='utf-8') as f:
            return json.load(f)
    except (IOError, OSError, ValueError):
        return {}


def load_settings():
    # 사이트가 도는 서버 안에서 돌릴 때(2026-09-24~) — 폴더 경로 하나면 끝입니다.
    # 네트워크도 계정도 비밀번호도 없습니다. 서버의 /opt/starendgame/.env 에
    # DEPLOY_LOCAL_DIR=/var/www/starendgame 한 줄이 이 길을 켭니다.
    local = (os.environ.get('DEPLOY_LOCAL_DIR')
             or _read_cfg('deploy.json').get('localDir') or '').strip()
    if local:
        print('  올릴 곳 이 서버 안 %s (폴더 복사)' % local)
        return {'host': 'local', 'user': '', 'password': '', 'remoteDir': local,
                'port': 0, 'proto': 'local', 'tls': False}

    # 어디에 올릴지(주소·계정·폴더)는 비밀이 아니라 저장소에 적어 둡니다.
    # 비밀은 비밀번호 하나뿐입니다. 자세한 사정은 data/deploy-target.json 주석에.
    cfg = _read_cfg('deploy.json') or _read_cfg('deploy-target.json')
    where = lambda key, env: cfg.get(key) or os.environ.get(env)
    port = cfg.get('port') or os.environ.get('SC_FTP_PORT')
    proto = (cfg.get('proto') or os.environ.get('SC_FTP_PROTO') or '').strip().lower()
    # 둘 중 하나만 적어도 나머지를 알아서 맞춥니다.
    #   22번 포트면 SFTP, SFTP 라고 적었으면 22번 — 흔히 하는 실수 하나를 없앱니다.
    if not proto:
        proto = 'sftp' if str(port) == '22' else 'ftp'
    if not port:
        port = 22 if proto == 'sftp' else 21
    out = {
        'host': _tidy('host', where('host', 'SC_FTP_HOST')),
        'user': _tidy('user', where('user', 'SC_FTP_USER')),
        # 비밀번호만 반대입니다 — 시크릿이 먼저입니다.
        'password': _tidy('password',
                          os.environ.get('SC_FTP_PASS') or cfg.get('password')),
        'remoteDir': _tidy('remoteDir',
                           where('remoteDir', 'SC_FTP_DIR') or '/www/endgame'),
        'port': int(port),
        'proto': proto,
        'tls': cfg.get('tls', True),
    }
    print('  올릴 곳 %s@%s%s (%s)'
          % (out['user'], out['host'], out['remoteDir'], out['proto'].upper()))
    missing = [k for k in ('host', 'user', 'password') if not out[k]]
    if missing:
        raise SystemExit(
            '접속 정보가 없습니다: %s\n'
            '  data/deploy.json 을 만들거나 SC_FTP_HOST / SC_FTP_USER / SC_FTP_PASS 를 넣어 주세요.\n'
            '  자세한 방법은 이 파일 맨 위 설명을 보세요.' % ', '.join(missing))
    return out


def local_files():
    """올릴 파일 목록 → {상대경로: 내용해시}"""
    out = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIRS and not d.startswith('.')]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, ROOT).replace(os.sep, '/')
            if (name in SKIP_FILES or name.endswith(SKIP_EXTS)
                    or rel in NEVER_UPLOAD or rel.startswith('data/.')
                    or rel.startswith('data/chat/') or rel.startswith('data/prizes/')):
                continue
            h = hashlib.sha1()
            with open(full, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    h.update(chunk)
            out[rel] = h.hexdigest()
    return out


def target_key(cfg):
    """'어느 서버의 어느 폴더에 올렸는가'. 상태 파일이 이것과 함께 저장됩니다."""
    return '%s%s' % (cfg['host'], cfg['remoteDir'].rstrip('/'))


def load_state(cfg):
    """지난번에 올린 파일 목록 — **같은 곳에 올렸을 때만** 씁니다.

    이게 없으면 서버를 옮겼을 때 사고가 납니다. 파일 해시만 보고 '안 바뀌었다'고
    판단하므로, 옛 서버에 다 올린 직후 새 서버로 주소를 바꾸면 '올릴 것 없음'이
    되어 **새 서버에는 아무것도 안 올라갑니다.** 겉으로는 성공한 것처럼 보이고요.
    (2026-09-21 서버 이전 때 실제로 밟을 뻔한 지뢰입니다.)
    """
    if not os.path.exists(STATE):
        return {}
    try:
        with io.open(STATE, encoding='utf-8') as f:
            doc = json.load(f)
    except (ValueError, OSError):
        return {}
    if doc.get('target') and doc['target'] != target_key(cfg):
        print('  올리는 곳이 지난번과 다릅니다 (%s → %s) — 전부 다시 올립니다.'
              % (doc['target'], target_key(cfg)))
        return {}
    return doc.get('files', {})


def save_state(cfg, files):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with io.open(STATE, 'w', encoding='utf-8') as f:
        f.write(json.dumps({'target': target_key(cfg), 'files': files},
                           ensure_ascii=False, indent=0))


class LocalUploader(object):
    """같은 기계 안의 사이트 폴더로 바로 복사합니다 (2026-09-24, 서버에서 직접 운영).

    사이트가 도는 서버 안에서 돌리면 네트워크를 탈 이유가 없습니다 — 만든 파일을
    웹루트로 복사하면 끝입니다. pubgin 의 src/local-deploy.js 와 같은 약속입니다.
      · 바뀐 파일만 복사합니다 (상태 파일은 FTP·SFTP 와 같은 data/.deploy-state.json)
      · 임시 이름으로 쓰고 바꿔 끼웁니다 — 방문자가 반쯤 쓴 파일을 보지 않게
      · 지우는 것은 STALE_REMOTE 뿐입니다. 웹루트에 사람이 둔 것(admin/pz 의 당첨자
        명단·채팅 기록, admin/config.php …)은 목록에 없으니 절대 건드리지 않습니다.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.base = ''
        self.made = set()

    def open(self, base):
        self.base = base.rstrip('/') or '/'
        hint = '\n  서버에서 한 번 붙여넣어 주세요:\n    sudo chown -R www-data:www-data %s' % self.base
        try:
            ok = os.path.isdir(self.base) and os.listdir(self.base) is not None
        except PermissionError:
            raise SystemExit('사이트 폴더를 열 권한이 없습니다: %s%s' % (self.base, hint))
        if not ok:
            raise SystemExit('사이트 폴더가 없습니다: %s\n'
                             '  서버의 .env 에서 DEPLOY_LOCAL_DIR 를 확인해 주세요.' % self.base)
        probe = os.path.join(self.base, '.deploy-write-test')
        try:
            with open(probe, 'w') as f:
                f.write('ok')
            os.remove(probe)
        except OSError as e:
            raise SystemExit('사이트 폴더에 쓸 권한이 없습니다: %s (%s)%s'
                             % (self.base, type(e).__name__, hint))
        print('  이 서버 안 폴더로 바로 복사합니다 (네트워크 없음).')

    def put(self, local, rel):
        dest = os.path.join(self.base, rel)
        folder = os.path.dirname(dest)
        if folder not in self.made:
            os.makedirs(folder, exist_ok=True)
            self.made.add(folder)
        tmp = os.path.join(folder, '.%s.deploytmp' % os.path.basename(dest))
        try:
            shutil.copyfile(local, tmp)
            os.replace(tmp, dest)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def remove(self, rel):
        os.remove(os.path.join(self.base, rel))

    def close(self):
        pass


class FtpUploader(object):
    """카페24 공유호스팅 시절부터 쓰던 길 — FTPS 로 붙고, 안 되면 평문 FTP."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.ftp = None
        self.made = set()

    def open(self, base):
        cfg = self.cfg
        ftp = None
        if cfg['tls']:
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE   # 공유호스팅은 인증서가 도메인과 다른 일이 흔합니다
                ftp = ftplib.FTP_TLS(context=ctx, timeout=cfg.get('timeout', 30))
                ftp.connect(cfg['host'], cfg['port'])
                ftp.login(cfg['user'], cfg['password'])
                ftp.prot_p()
                print('  FTPS(암호화)로 접속했습니다.')
            except Exception as e:
                print('  FTPS 실패(%s) — 평문 FTP 로 다시 시도합니다.' % type(e).__name__)
                try:
                    ftp.close()
                except Exception:
                    pass
                ftp = None
        if ftp is None:
            ftp = ftplib.FTP(timeout=cfg.get('timeout', 30))
            ftp.connect(cfg['host'], cfg['port'])
            ftp.login(cfg['user'], cfg['password'])
            print('  FTP로 접속했습니다. (암호화 안 됨)')
        self.ftp = ftp
        self._ensure(base.lstrip('/'))
        ftp.cwd(base)

    def _ensure(self, path):
        if not path or path in self.made:
            return
        parent = path.rsplit('/', 1)[0] if '/' in path else ''
        self._ensure(parent)
        try:
            self.ftp.mkd(path)
        except ftplib.error_perm as e:
            if not str(e).startswith('550'):      # 550 = 이미 있음
                raise
        self.made.add(path)

    def put(self, local, rel):
        d = rel.rsplit('/', 1)[0] if '/' in rel else ''
        if d:
            self._ensure(d)
        with open(local, 'rb') as f:
            self.ftp.storbinary('STOR ' + rel, f, blocksize=65536)

    def remove(self, rel):
        self.ftp.delete(rel)

    def close(self):
        try:
            self.ftp.quit()
        except Exception:
            try:
                self.ftp.close()
            except Exception:
                pass


class SftpUploader(object):
    """전용 서버(2026-09-21 이전) 길 — SSH 위의 SFTP. 파일질라가 쓰는 것과 같습니다.

    카페24 공유호스팅은 FTP 였지만 옮겨 간 서버는 SSH 만 열려 있습니다.
    비밀번호로 붙으므로, 서버 키를 처음 보면 그대로 받아들입니다(파일질라의
    '이 호스트를 신뢰' 와 같은 동작). 그래서 **배포 전용 계정과 키 인증으로
    바꾸는 것이 안전합니다** — README 와 CLAUDE.md 에 적어 뒀습니다.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.cli = None
        self.sftp = None
        self.base = ''
        self.made = set()

    def open(self, base):
        try:
            import paramiko
        except ImportError:
            raise SystemExit(
                'SFTP 로 올리려면 paramiko 가 필요합니다.\n'
                '  pip install paramiko\n'
                '  (GitHub Actions 에는 이미 들어가게 해 뒀습니다.)')
        cfg = self.cfg
        self.cli = paramiko.SSHClient()
        self.cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.cli.connect(cfg['host'], port=cfg['port'], username=cfg['user'],
                         password=cfg['password'], timeout=cfg.get('timeout', 30),
                         look_for_keys=False, allow_agent=False)
        self.sftp = self.cli.open_sftp()
        self.base = base.rstrip('/')
        print('  SFTP(SSH)로 접속했습니다.')
        try:
            self.sftp.stat(self.base)
        except IOError:
            self.base = self._rescue_dir()

    def _rescue_dir(self):
        """적어 준 폴더가 없을 때 — 사이트 이름과 같은 폴더가 **딱 하나**면 그리로.

        잘못된 곳에 사이트를 통째로 부어 놓는 사고는 막아야 하지만, 폴더 이름
        하나 때문에 배포가 통째로 멈추는 것도 곤란합니다. 그래서 '도메인 이름과
        같은 폴더'라는 좁은 조건일 때만 옮겨 붙고, 크게 알립니다.
        """
        host = site_host()
        want = {h for h in (host, host.replace('www.', ''),
                            host.replace('www.', '').split('.')[0]) if h}
        # 적어 준 곳의 상위 폴더부터, 그다음은 이 서버의 웹 뿌리(/var/www)를 봅니다.
        # 주소만 바꾸고 폴더를 예전 값(/www/endgame)으로 두고 오는 일이 흔해서입니다.
        parent, entries, hit = '', [], []
        for cand in [self.base.rsplit('/', 1)[0] or '/', '/var/www']:
            if parent and cand == parent:
                continue
            try:
                got = sorted(self.sftp.listdir(cand))
            except IOError:
                continue
            if not parent:
                parent, entries = cand, got
            found_here = [e for e in got if e.lower() in want]
            if found_here:
                parent, entries, hit = cand, got, found_here
                break
        if not parent:
            raise SystemExit('올릴 폴더가 서버에 없습니다: %s (상위 폴더도 못 읽었습니다)'
                             % self.base)
        if len(hit) == 1:
            found = parent.rstrip('/') + '/' + hit[0]
            print('  ! 적어 주신 폴더가 없어 사이트 이름과 같은 폴더로 갑니다: %s' % found)
            print('    (SC_FTP_DIR 을 이 값으로 고쳐 두시면 이 줄이 사라집니다)')
            return found
        raise SystemExit(
            '올릴 폴더가 서버에 없습니다: %s\n'
            '  %s 안에 있는 것: %s\n'
            '  사이트 이름(%s)과 같은 폴더도 %s.\n'
            '  SC_FTP_DIR 을 실제 폴더로 맞춰 주세요.'
            % (self.base, parent, ', '.join(entries[:25]) or '(비어 있음)',
               host or '?', '없습니다' if not hit else '여러 개입니다: %s' % ', '.join(hit)))

    def _ensure(self, rel):
        if not rel or rel in self.made:
            return
        parent = rel.rsplit('/', 1)[0] if '/' in rel else ''
        self._ensure(parent)
        try:
            self.sftp.mkdir(self.base + '/' + rel)
        except IOError:
            pass                                   # 이미 있으면 그대로 둡니다
        self.made.add(rel)

    def put(self, local, rel):
        d = rel.rsplit('/', 1)[0] if '/' in rel else ''
        if d:
            self._ensure(d)
        self.sftp.put(local, self.base + '/' + rel)

    def remove(self, rel):
        self.sftp.remove(self.base + '/' + rel)

    def close(self):
        for x in (self.sftp, self.cli):
            try:
                x.close()
            except Exception:
                pass


def site_base_url():
    try:
        with io.open(os.path.join(ROOT, 'data', 'site.json'), encoding='utf-8') as f:
            return (json.load(f).get('baseUrl') or '').rstrip('/')
    except (IOError, OSError, ValueError):
        return ''


def site_host():
    u = site_base_url()
    return u.split('//', 1)[-1].split('/', 1)[0].lower() if u else ''


def _one(cfg, proto, timeout):
    cfg = dict(cfg, proto=proto, timeout=timeout)
    if str(cfg.get('port')) not in ('22', '21'):
        pass
    elif (proto == 'sftp') != (str(cfg['port']) == '22'):
        cfg['port'] = 22 if proto == 'sftp' else 21     # 방식을 바꾸면 포트도 따라갑니다
    return (SftpUploader if proto == 'sftp' else FtpUploader)(cfg)


def ssh_auth_methods(cfg):
    """서버가 받아 주는 인증 방식을 물어봅니다 — 비번이 틀린 건지, 비번 로그인이
    막힌 건지 가르기 위해서입니다.

    둘은 같은 AuthenticationException 으로 보이는데 고칠 사람이 다릅니다.
    (비번이 틀리면 사장님이 시크릿을, 막혀 있으면 서버 주인이 sshd_config 를)
    """
    try:
        import socket
        import paramiko
        # 소켓을 직접 만들어 시간 제한을 겁니다 — 그냥 (host, port) 로 넘기면
        # 서버가 조용할 때 하염없이 기다립니다.
        t = paramiko.Transport(socket.create_connection(
            (cfg['host'], cfg['port']), timeout=15))
        t.banner_timeout = 15
        t.connect()
        try:
            t.auth_none(cfg['user'])
            return ['none']                      # 인증 없이 들어가지는 서버
        except paramiko.BadAuthenticationType as e:
            return list(e.allowed_types)
        finally:
            t.close()
    except Exception as e:
        return ['(물어보지 못했습니다 — %s)' % type(e).__name__]


def connect_any(cfg, base):
    """적어 준 방식으로 붙어 보고, 안 되면 다른 방식으로 한 번 더.

    2026-09-21 서버 이전 뒤 FTP(21)와 SFTP(22)가 섞여 있습니다. 어느 쪽인지
    시크릿에 안 적었다고 배포가 통째로 멈추면 곤란해서, 한 번은 더 해 봅니다.
    '폴더가 없다' 같은 확실한 문제(SystemExit)는 그대로 알립니다.
    """
    if cfg['proto'] == 'local':
        up = LocalUploader(cfg)
        up.open(base)
        return up
    first = cfg['proto']
    second = 'ftp' if first == 'sftp' else 'sftp'
    try:
        up = _one(cfg, first, 12)
        up.open(base)
        return up
    except SystemExit:
        raise
    except Exception as e:
        print('  %s 로 붙지 못했습니다 (%s) — %s 로 다시 해 봅니다.'
              % (first.upper(), type(e).__name__, second.upper()))
    up = _one(cfg, second, 30)
    try:
        up.open(base)
    except SystemExit:
        raise
    except Exception as e:
        # 두 방식 다 안 되면 십중팔구 접속 정보가 옛것입니다. 무슨 일인지 한눈에
        # 보이게 적어 둡니다 — 2026-09-21 서버 이전 때 실행이 줄줄이 실패하면서
        # 파이썬 역추적만 찍혀 원인을 찾는 데 시간이 걸렸습니다.
        if 'Authentication' in type(e).__name__:
            ways = ssh_auth_methods(dict(cfg, proto='sftp', port=22))
            can_pw = 'password' in ways or 'keyboard-interactive' in ways
            raise SystemExit(
                '서버까지는 갔는데 계정/비밀번호를 거절당했습니다 (%s).\n'
                '  주소·포트는 맞습니다 — SSH(22번)는 열렸고, 막힌 건 인증입니다.\n'
                '  서버가 받아 주는 인증 방식: %s\n'
                '  %s\n'
                '  %s'
                % (type(e).__name__, ', '.join(ways) or '(없음)',
                   '계정 이름은 root 입니다.' if cfg['user'] == 'root' else
                   '계정 이름이 root 가 아닙니다 — SC_FTP_USER 를 확인해 주세요.',
                   '→ 비밀번호 로그인은 받는 서버입니다. 비밀번호가 다릅니다 —\n'
                   '     시크릿 SC_FTP_PASS 에 비밀번호만 다시 붙여넣어 주세요\n'
                   '     (따옴표·설명·앞뒤 공백이 섞이면 안 됩니다).'
                   if can_pw else
                   '→ 이 서버는 비밀번호 로그인을 받지 않습니다. 비밀번호를 아무리\n'
                   '     고쳐도 안 됩니다. 형님께 sshd_config 의 PasswordAuthentication·\n'
                   '     PermitRootLogin 을 확인해 달라고 하시거나, 배포용 SSH 키를\n'
                   '     받아 주세요 (키 방식도 붙일 수 있게 하겠습니다).'))
        raise SystemExit(
            '서버에 붙지 못했습니다 — %s 도, %s 도 안 됩니다. (%s: %s)\n'
            '  지금 보고 있는 곳: %s %s\n'
            '  서버를 옮기셨다면 GitHub 시크릿 세 개를 새 서버 값으로 바꿔 주세요 —\n'
            '  SC_FTP_HOST · SC_FTP_USER · SC_FTP_PASS\n'
            '  (폴더·접속 방식은 알아서 찾습니다. Settings → Secrets and variables → Actions)'
            % (first.upper(), second.upper(), type(e).__name__, e,
               cfg['host'], cfg['remoteDir']))
    print('  (%s 가 맞았습니다 — SC_FTP_PROTO 를 %s 로 적어 두시면 더 빠릅니다)'
          % (second.upper(), second))
    return up


def purge_stale(up):
    """서버에 남아 있으면 안 되는 것들을 지웁니다 (STALE_REMOTE, 없으면 조용히).

    올리기만 하던 스크립트에 예외를 둔 이유는 하나입니다 — 그중에 슬랙 웹훅이
    있습니다. 2026-09-21 서버 이전 때 data/slack.json 이 딸려 올라갔고,
    data/ 는 시트 연동 때문에 통째로 공개되는 폴더입니다.
    """
    gone = []
    for rel, why in STALE_REMOTE:
        try:
            up.remove(rel)
            gone.append((rel, why))
        except Exception:
            pass                                   # 없으면 그만입니다
    if gone:
        print('  서버에서 지운 것 %d개:' % len(gone))
        for rel, why in gone:
            print('    %s — %s' % (rel, why))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='올리지 않고 목록만 보기')
    ap.add_argument('--all', action='store_true', help='바뀐 것만이 아니라 전부 올리기')
    ap.add_argument('--no-tls', action='store_true', help='평문 FTP 로 접속')
    args = ap.parse_args()

    cfg = load_settings()
    if args.no_tls:
        cfg['tls'] = False

    files = local_files()
    old = {} if args.all else load_state(cfg)
    changed = sorted(k for k, v in files.items() if old.get(k) != v)
    total_bytes = sum(os.path.getsize(os.path.join(ROOT, k)) for k in changed)

    print('배포 대상 %s%s  (%s)'
          % (cfg['host'], cfg['remoteDir'], cfg['proto'].upper()))
    print('  전체 %d개 중 바뀐 파일 %d개 (%.1fMB)'
          % (len(files), len(changed), total_bytes / 1048576))

    if not changed:
        print('  올릴 것이 없습니다. 이미 최신입니다.')
        return

    if args.dry_run:
        for k in changed[:40]:
            print('    %s' % k)
        if len(changed) > 40:
            print('    ... 외 %d개' % (len(changed) - 40))
        print('  (--dry-run 이라 실제로 올리지 않았습니다)')
        return

    base = cfg['remoteDir'].rstrip('/')
    up = connect_any(cfg, base)
    done, failed = 0, []
    try:
        for rel in changed:
            try:
                up.put(os.path.join(ROOT, rel), rel)
                done += 1
                old[rel] = files[rel]
                if done % 20 == 0 or done == len(changed):
                    print('  %d/%d 올리는 중...' % (done, len(changed)))
            except Exception as e:
                failed.append((rel, '%s: %s' % (type(e).__name__, e)))
        purge_stale(up)
    finally:
        up.close()

    # 성공한 것만 기록해 둡니다 — 실패한 파일은 다음에 다시 올라갑니다.
    save_state(cfg, {k: v for k, v in old.items() if k in files})

    print('  올린 파일 %d개' % done)
    if failed:
        print('  실패 %d개:' % len(failed))
        for rel, msg in failed[:10]:
            print('    %s — %s' % (rel, msg))
        # 문제가 생겼을 때만 슬랙으로 알립니다 (정상 배포는 조용히, 2026-08-20).
        try:
            import notify
            lines = ['파일 %d개 업로드 실패 (%d개는 성공):' % (len(failed), done)]
            lines += ['· %s — %s' % (rel, msg) for rel, msg in failed[:12]]
            if len(failed) > 12:
                lines.append('· … 외 %d개' % (len(failed) - 12))
            notify.notify_problem('끝장전 배포 실패', lines)
        except Exception as e:
            print('   (문제 알림 건너뜀 — %s)' % e)
        sys.exit(1)
    print('완료 — %s/ 에서 확인하세요.'
          % (site_base_url() or 'https://%s%s' % (cfg['host'], base)))
    # 정상 배포에는 슬랙 알림을 보내지 않습니다 (사장님 요청 — 문제 있을 때만).


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise                                 # 실패 알림은 이미 위에서 보냈습니다
    except Exception as e:
        # 예상 못 한 오류(FTP 접속 불가 등)도 문제 알림으로 보냅니다.
        import traceback
        traceback.print_exc()
        try:
            import notify
            notify.notify_problem('끝장전 배포 오류',
                                  ['%s: %s' % (type(e).__name__, e)])
        except Exception:
            pass
        sys.exit(1)
