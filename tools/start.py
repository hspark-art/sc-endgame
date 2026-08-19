#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""처음부터 끝까지 한 번에. 보통은 `시작.bat` 을 더블클릭하면 이게 실행됩니다.

    python3 tools/start.py

하는 일
  1. 예전 작업 폴더를 찾아 유튜브 API 키를 가져옵니다
  2. 파이썬·엑셀 라이브러리 확인
  3. FTP 접속 정보를 묻고 저장 (비밀번호는 화면에 안 보임)
  4. FTP·구글시트·빌드가 되는지 확인
  5. 사이트를 만들어 pubgin.com 에 올립니다
  6. GitHub 에 백업을 올립니다
  7. 휴대폰 연결 방법을 알려 줍니다

중간에 안 되는 것이 있어도 멈추지 않고, 할 수 있는 데까지 하고
무엇이 남았는지 마지막에 알려 줍니다. 몇 번 돌려도 괜찮습니다.
"""

import io
import json
import os
import re
import subprocess
import sys

try:                                                  # 윈도우 콘솔에서 한글 깨짐 방지
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import setup as S                                     # noqa: E402

BRANCH = 'claude/starcraft-endgame-site-049jip'
KEY_RE = re.compile(r'AIza[0-9A-Za-z_\-]{35}')
# 키가 들어 있을 법한 파일만 봅니다 — 폴더 전체를 뒤지면 느립니다.
KEY_EXTS = {'.json', '.txt', '.py', '.js', '.env', '.md', '.bat', '.ps1',
            '.ini', '.cfg', '.yml', '.yaml'}


def mask(key):
    return key[:8] + '…' + key[-4:]


def old_folders():
    """예전 끝장전 작업 폴더로 보이는 곳들."""
    seen, out = set(), []
    home = os.path.expanduser('~')
    guesses = [
        os.path.join(home, 'scetalent'),
        os.path.join(home, 'etalentsc'),
        os.path.join(home, 'Documents', 'etalentsc'),
        os.path.join(home, 'Documents', 'scetalent'),
        os.path.join(home, 'Desktop', 'etalentsc'),
        os.path.join(home, 'Desktop', 'scetalent'),
    ]
    # 홈·문서·바탕화면 바로 아래에서 이름으로도 찾아봅니다
    for base in (home, os.path.join(home, 'Documents'), os.path.join(home, 'Desktop')):
        try:
            for name in os.listdir(base):
                low = name.lower().replace('-', '').replace('_', '')
                if ('sc' in low and 'etalent' in low) or low in ('endgame', '끝장전'):
                    guesses.append(os.path.join(base, name))
        except OSError:
            pass
    for g in guesses:
        real = os.path.normcase(os.path.abspath(g))
        if real in seen or real == os.path.normcase(ROOT):
            continue
        seen.add(real)
        if os.path.isdir(g):
            out.append(g)
    return out


def find_key_in(folder, max_files=4000):
    """폴더에서 유튜브 API 키처럼 생긴 문자열을 찾습니다."""
    n = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames
                       if not d.startswith('.') and d not in
                       ('node_modules', '__pycache__', 'venv', '.venv')]
        for name in filenames:
            ext = os.path.splitext(name)[1].lower()
            if ext and ext not in KEY_EXTS:     # 확장자 없는 파일(.env 류)도 봅니다
                continue
            n += 1
            if n > max_files:
                return None
            full = os.path.join(dirpath, name)
            try:
                if os.path.getsize(full) > 2_000_000:
                    continue
                with io.open(full, encoding='utf-8', errors='ignore') as f:
                    m = KEY_RE.search(f.read())
            except OSError:
                continue
            if m:
                return m.group(0), full
    return None


def step_youtube():
    S.step(0, '예전 폴더에서 유튜브 키 찾기')
    path = os.path.join(ROOT, 'data', 'youtube.json')
    if os.path.exists(path):
        try:
            k = json.load(io.open(path, encoding='utf-8')).get('apiKey')
        except (ValueError, OSError):
            k = None
        if k:
            print('   이미 들어 있습니다 — %s' % mask(k))
            print(S.OK + ' 그대로 씁니다.')
            return True
    folders = old_folders()
    if not folders:
        print('   예전 작업 폴더를 못 찾았습니다. 건너뜁니다.')
        print('   (나중에 data/youtube.json 에 {"apiKey": "..."} 로 넣으셔도 됩니다)')
        return False
    for folder in folders:
        print('   찾는 중 — %s' % folder)
        hit = find_key_in(folder)
        if not hit:
            continue
        key, where = hit
        os.makedirs(os.path.dirname(path), exist_ok=True)
        io.open(path, 'w', encoding='utf-8').write(
            json.dumps({'apiKey': key}, ensure_ascii=False, indent=1) + '\n')
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        print('   찾았습니다 — %s' % mask(key))
        print('   (%s)' % where)
        print(S.OK + ' data/youtube.json 에 저장했습니다. 웹서버에도 저장소에도 안 올라갑니다.')
        return True
    print('   폴더는 찾았지만 키는 없었습니다. 건너뜁니다.')
    return False


def step_update():
    S.step(7, '사이트 만들어 올리기')
    r = subprocess.run([sys.executable, os.path.join(HERE, 'update.py')], cwd=ROOT)
    if r.returncode != 0:
        print(S.NO + ' 올리지 못했습니다. 위에 나온 이유를 봐 주세요.')
        return False
    print(S.OK + ' https://pubgin.com/endgame/ 에 올라갔습니다.')
    return True


def step_push():
    S.step(8, 'GitHub 백업')
    if not os.path.isdir(os.path.join(ROOT, '.git')):
        print('   git 폴더가 없어 건너뜁니다.')
        print('   (압축을 풀 때 숨김 폴더가 빠졌을 수 있습니다)')
        return False
    try:
        r = subprocess.run(['git', 'push', '-u', 'origin', BRANCH],
                           cwd=ROOT, capture_output=True, text=True)
    except OSError:
        print('   git 이 설치돼 있지 않아 건너뜁니다.')
        print('   (git-scm.com 에서 받으실 수 있습니다. 없어도 사이트는 잘 돌아갑니다)')
        return False
    out = ((r.stdout or '') + (r.stderr or '')).strip()
    for line in out.split('\n')[-4:]:
        if line:
            print('   ' + line)
    if r.returncode == 0:
        print(S.OK + ' 올렸습니다.')
        return True
    if 'Authentication' in out or '403' in out or 'could not read' in out.lower():
        print(S.NO + ' GitHub 로그인이 필요합니다.')
        print('   깃허브 아이디와 토큰을 물어보면 넣어 주세요.')
        print('   토큰은 github.com → Settings → Developer settings →')
        print('   Personal access tokens 에서 repo 권한으로 만드시면 됩니다.')
    else:
        print(S.NO + ' 올리지 못했습니다.')
    return False


def step_videos():
    S.step(6, '다시보기 영상 채우기')
    path = os.path.join(ROOT, 'data', 'youtube.json')
    if not os.path.exists(path):
        print('   유튜브 키가 없어 건너뜁니다.')
        return False
    r = subprocess.run([sys.executable, os.path.join(HERE, 'fetch_videos.py'),
                        '--write'], cwd=ROOT, capture_output=True, text=True)
    tail = [x for x in ((r.stdout or '') + (r.stderr or '')).strip().split('\n') if x][-6:]
    for line in tail:
        print('   ' + line)
    if r.returncode != 0:
        print(S.NO + ' 영상 매칭에 실패했습니다. 사이트에는 영향 없습니다.')
        return False
    print(S.OK + ' 채웠습니다. 바로 아래에서 사이트에 함께 올라갑니다.')
    return True


def main():
    print('=' * 58)
    print(' 스타크래프트 기록실 — 한 번에 준비하기')
    print(' 폴더: %s' % ROOT)
    print('=' * 58)

    step_youtube()

    if not S.check_python():
        return 1
    if not S.check_openpyxl():
        return 1
    if not S.setup_ftp():
        return 1

    ftp_ok = S.test_ftp()
    sheet_ok = S.test_sheet()

    step_videos()                       # 영상을 먼저 채워야 같은 업로드에 실립니다

    up_ok = step_update() if (ftp_ok and sheet_ok) else False
    if not up_ok:
        print('\n   FTP 나 구글시트가 안 돼서 올리는 것은 건너뛰었습니다.')

    push_ok = step_push()

    print('\n' + '═' * 58)
    left = []
    if not ftp_ok:
        left.append('FTP 접속 — 카페24 보안관리 → FTP/Shell 접속설정에서 IP 허용')
    if not sheet_ok:
        left.append('구글시트 받아오기 — 시트 공유가 "링크가 있는 모든 사용자"인지 확인')
    if not up_ok:
        left.append('사이트 올리기')
    if not push_ok:
        left.append('GitHub 백업 — 없어도 사이트는 잘 돌아갑니다')

    if left:
        print('아직 안 된 것:')
        for x in left:
            print('   - %s' % x)
        print('')
    else:
        print('전부 됐습니다.\n')

    print('이제 휴대폰에서 쓰시려면, 이 창에서 이렇게 하세요.\n')
    print('   claude')
    print('')
    print('들어가서  /remote-control  이라고 치면 QR 코드가 나옵니다.')
    print('휴대폰 카메라로 찍으면 연결됩니다.')
    print('그 뒤로는 휴대폰에서  /갱신  만 치면 시트부터 사이트까지 알아서 돌아갑니다.')
    print('')
    print('다음부터 이 창을 다시 열면 물어보는 것 없이 바로 갱신됩니다.')
    return 0 if not left else 1


if __name__ == '__main__':
    sys.exit(main())
