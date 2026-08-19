#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""빌드 결과물을 웹서버(카페24)로 FTP 업로드합니다.

    python3 tools/build.py && python3 tools/deploy.py

바뀐 파일만 올립니다. 처음 한 번은 전부 올라가고, 그다음부터는 실제로 달라진
것만 올라가서 몇 초면 끝납니다.

접속 정보 — 둘 중 편한 쪽으로 (저장소에는 들어가지 않습니다)

  1) data/deploy.json 파일
     {
       "host": "pubgin.com",
       "user": "pubgin",
       "password": "비밀번호",
       "remoteDir": "/www/endgame"
     }

  2) 환경변수
     export SC_FTP_HOST=pubgin.com
     export SC_FTP_USER=pubgin
     export SC_FTP_PASS=비밀번호
     export SC_FTP_DIR=/www/endgame

옵션
  --dry-run   올리지 않고 무엇이 올라갈지만 보여 줍니다
  --all       바뀐 것만이 아니라 전부 다시 올립니다
  --no-tls    서버가 FTPS 를 못 받을 때 (평문 FTP 로 접속)

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
SKIP_DIRS = {'tools', 'node_modules', '__pycache__'}
SKIP_FILES = {'.gitignore', '.deploy-state.json', 'deploy.json',
              '_사진목록.txt'}          # 사진 넣는 법 안내 — 우리끼리 보는 것
SKIP_EXTS = ('.md', '.bat', '.command', '.sh')
# 절대 웹서버로 나가면 안 되는 것.
#   admin/config.php  관리자 계정 (서버에만 있어야 하고 덮어써서도 안 됩니다)
#   data/deploy.json  FTP 비밀번호
#   data/youtube.json 유튜브 API 키
# data/ 는 sheets.html 이 원본 JSON 을 공개하느라 통째로 올라가므로,
# 그 안에 비밀이 들어오면 반드시 여기에 적어야 합니다.
NEVER_UPLOAD = {'admin/config.php', 'data/deploy.json', 'data/youtube.json'}


def load_settings():
    cfg = {}
    path = os.path.join(ROOT, 'data', 'deploy.json')
    if os.path.exists(path):
        with io.open(path, encoding='utf-8') as f:
            cfg = json.load(f)
    out = {
        'host': os.environ.get('SC_FTP_HOST') or cfg.get('host'),
        'user': os.environ.get('SC_FTP_USER') or cfg.get('user'),
        'password': os.environ.get('SC_FTP_PASS') or cfg.get('password'),
        'remoteDir': os.environ.get('SC_FTP_DIR') or cfg.get('remoteDir') or '/www/endgame',
        'port': int(os.environ.get('SC_FTP_PORT') or cfg.get('port') or 21),
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


def connect(cfg):
    """FTPS 로 붙어 보고, 서버가 못 받으면 평문 FTP 로 내려갑니다."""
    if cfg['tls']:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE     # 공유호스팅은 인증서가 도메인과 다른 일이 흔합니다
            ftp = ftplib.FTP_TLS(context=ctx, timeout=30)
            ftp.connect(cfg['host'], cfg['port'])
            ftp.login(cfg['user'], cfg['password'])
            ftp.prot_p()
            print('  FTPS(암호화)로 접속했습니다.')
            return ftp
        except Exception as e:      # 어떤 이유로든 FTPS 가 안 되면 평문으로 내려갑니다
            print('  FTPS 실패(%s) — 평문 FTP 로 다시 시도합니다.' % type(e).__name__)
            try:
                ftp.close()
            except Exception:
                pass
    ftp = ftplib.FTP(timeout=30)
    ftp.connect(cfg['host'], cfg['port'])
    ftp.login(cfg['user'], cfg['password'])
    print('  FTP로 접속했습니다. (암호화 안 됨)')
    return ftp


def ensure_dir(ftp, path, made):
    """원격 폴더가 없으면 만듭니다. 이미 만든 곳은 다시 안 만듭니다."""
    if not path or path in made:
        return
    parent = path.rsplit('/', 1)[0] if '/' in path else ''
    ensure_dir(ftp, parent, made)
    try:
        ftp.mkd(path)
    except ftplib.error_perm as e:
        if not str(e).startswith('550'):        # 550 = 이미 있음
            raise
    made.add(path)


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

    print('배포 대상 %s%s' % (cfg['host'], cfg['remoteDir']))
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
    ftp = connect(cfg)
    made, done, failed = set(), 0, []
    try:
        ensure_dir(ftp, base.lstrip('/'), made)
        ftp.cwd(base)
        for rel in changed:
            remote_dir = rel.rsplit('/', 1)[0] if '/' in rel else ''
            if remote_dir:
                ensure_dir(ftp, remote_dir, made)
            try:
                with open(os.path.join(ROOT, rel), 'rb') as f:
                    ftp.storbinary('STOR ' + rel, f, blocksize=65536)
                done += 1
                old[rel] = files[rel]
                if done % 20 == 0 or done == len(changed):
                    print('  %d/%d 올리는 중...' % (done, len(changed)))
            except ftplib.all_errors as e:
                failed.append((rel, str(e)))
    finally:
        try:
            ftp.quit()
        except ftplib.all_errors:
            ftp.close()

    # 성공한 것만 기록해 둡니다 — 실패한 파일은 다음에 다시 올라갑니다.
    save_state({k: v for k, v in old.items() if k in files})

    print('  올린 파일 %d개' % done)
    if failed:
        print('  실패 %d개:' % len(failed))
        for rel, msg in failed[:10]:
            print('    %s — %s' % (rel, msg))
        sys.exit(1)
    print('완료 — https://%s%s/ 에서 확인하세요.'
          % (cfg['host'], base.replace('/www', '', 1)))

    # 무엇이 바뀌었는지 슬랙으로 알립니다 (PUBG META 와 같은 방식).
    # 알림이 안 되더라도 배포는 이미 끝난 것이므로 그냥 넘어갑니다.
    try:
        import notify
        notify.notify_deploy(uploaded=done, changed_files=len(changed))
    except Exception as e:
        print('   (슬랙 알림 건너뜀 — %s)' % e)


if __name__ == '__main__':
    main()
