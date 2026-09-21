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
SKIP_DIRS = {'tools', 'node_modules', '__pycache__', 'logs'}
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
                'data/slack.json'}


def load_settings():
    cfg = {}
    path = os.path.join(ROOT, 'data', 'deploy.json')
    if os.path.exists(path):
        with io.open(path, encoding='utf-8') as f:
            cfg = json.load(f)
    port = os.environ.get('SC_FTP_PORT') or cfg.get('port')
    proto = (os.environ.get('SC_FTP_PROTO') or cfg.get('proto') or '').strip().lower()
    # 둘 중 하나만 적어도 나머지를 알아서 맞춥니다.
    #   22번 포트면 SFTP, SFTP 라고 적었으면 22번 — 흔히 하는 실수 하나를 없앱니다.
    if not proto:
        proto = 'sftp' if str(port) == '22' else 'ftp'
    if not port:
        port = 22 if proto == 'sftp' else 21
    out = {
        'host': os.environ.get('SC_FTP_HOST') or cfg.get('host'),
        'user': os.environ.get('SC_FTP_USER') or cfg.get('user'),
        'password': os.environ.get('SC_FTP_PASS') or cfg.get('password'),
        'remoteDir': os.environ.get('SC_FTP_DIR') or cfg.get('remoteDir') or '/www/endgame',
        'port': int(port),
        'proto': proto,
        'tls': cfg.get('tls', True),
    }
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


def load_state():
    if not os.path.exists(STATE):
        return {}
    try:
        with io.open(STATE, encoding='utf-8') as f:
            return json.load(f).get('files', {})
    except (ValueError, OSError):
        return {}


def save_state(files):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with io.open(STATE, 'w', encoding='utf-8') as f:
        f.write(json.dumps({'files': files}, ensure_ascii=False, indent=0))


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
                ftp = ftplib.FTP_TLS(context=ctx, timeout=30)
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
            ftp = ftplib.FTP(timeout=30)
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
                         password=cfg['password'], timeout=30,
                         look_for_keys=False, allow_agent=False)
        self.sftp = self.cli.open_sftp()
        self.base = base.rstrip('/')
        print('  SFTP(SSH)로 접속했습니다.')
        try:
            self.sftp.stat(self.base)
        except IOError:
            # 잘못된 폴더에 사이트를 통째로 부어 놓는 사고를 막습니다.
            parent = self.base.rsplit('/', 1)[0] or '/'
            try:
                nearby = ', '.join(sorted(self.sftp.listdir(parent))[:20])
            except IOError:
                nearby = '(상위 폴더도 못 읽었습니다)'
            raise SystemExit(
                '올릴 폴더가 서버에 없습니다: %s\n'
                '  %s 안에 있는 것: %s\n'
                '  SC_FTP_DIR 을 실제 폴더로 맞춰 주세요.' % (self.base, parent, nearby))

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

    def close(self):
        for x in (self.sftp, self.cli):
            try:
                x.close()
            except Exception:
                pass


def make_uploader(cfg):
    return SftpUploader(cfg) if cfg['proto'] == 'sftp' else FtpUploader(cfg)


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
    old = {} if args.all else load_state()
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
    up = make_uploader(cfg)
    up.open(base)
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
    finally:
        up.close()

    # 성공한 것만 기록해 둡니다 — 실패한 파일은 다음에 다시 올라갑니다.
    save_state({k: v for k, v in old.items() if k in files})

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
    site = ''
    try:
        with io.open(os.path.join(ROOT, 'data', 'site.json'), encoding='utf-8') as f:
            site = (json.load(f).get('baseUrl') or '').rstrip('/')
    except (IOError, OSError, ValueError):
        pass
    print('완료 — %s/ 에서 확인하세요.' % (site or 'https://%s%s' % (cfg['host'], base)))
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
