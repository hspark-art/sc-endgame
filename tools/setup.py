#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""회사 PC 에서 처음 한 번만 돌리는 준비 스크립트.

    python3 tools/setup.py

하는 일
  1. 파이썬 버전 확인
  2. 엑셀 라이브러리(openpyxl) 설치
  3. FTP 접속 정보를 물어 data/deploy.json 에 저장 (비밀번호는 화면에 안 보임)
  4. FTP 로 실제로 붙어 봅니다
  5. 구글시트를 실제로 받아 봅니다
  6. 사이트를 한 번 만들어 봅니다

하나라도 안 되면 무엇이 문제인지 알려 주고 멈춥니다.
이미 되어 있는 것은 건너뜁니다. 몇 번 돌려도 괜찮습니다.
"""

import io
import json
import os
import subprocess
import sys

# 윈도우 콘솔에서 한글·기호가 깨지거나 터지지 않게 합니다.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

OK, NO = '  [OK]', '  [!!]'


def step(n, title):
    print('\n── %d. %s ' % (n, title) + '─' * max(0, 46 - len(title)))


def ask(prompt, default=''):
    v = input('   %s%s: ' % (prompt, (' [%s]' % default) if default else '')).strip()
    return v or default


def check_python():
    step(1, '파이썬')
    v = sys.version_info
    print('   %d.%d.%d' % (v.major, v.minor, v.micro))
    if v < (3, 8):
        print(NO + ' 파이썬 3.8 이상이 필요합니다.')
        return False
    print(OK + ' 괜찮습니다.')
    return True


def check_openpyxl():
    step(2, '엑셀 라이브러리')
    try:
        import openpyxl                                  # noqa: F401
        print(OK + ' 이미 있습니다.')
        return True
    except ImportError:
        pass
    print('   openpyxl 이 없어 설치합니다...')
    r = subprocess.run([sys.executable, '-m', 'pip', 'install', 'openpyxl'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(NO + ' 설치 실패. 직접 실행해 보세요: pip install openpyxl')
        print('   ' + (r.stderr or '').strip()[:300])
        return False
    print(OK + ' 설치했습니다.')
    return True


def setup_ftp():
    step(3, 'FTP 접속 정보')
    path = os.path.join(ROOT, 'data', 'deploy.json')
    if os.path.exists(path):
        cfg = json.load(io.open(path, encoding='utf-8'))
        if cfg.get('password') and not cfg['password'].startswith('여기에'):
            print('   이미 있습니다 — %s@%s%s'
                  % (cfg.get('user'), cfg.get('host'), cfg.get('remoteDir')))
            if ask('다시 입력할까요? (y/N)', 'N').lower() != 'y':
                print(OK + ' 그대로 씁니다.')
                return cfg
    print('   카페24 FTP 정보를 넣어 주세요. 비밀번호는 화면에 보이지 않습니다.')
    import getpass
    cfg = {
        'host': ask('호스트', 'pubgin.com'),
        'user': ask('아이디', 'pubgin'),
        'password': getpass.getpass('   비밀번호: '),
        'remoteDir': ask('올릴 폴더', '/www/endgame'),
        'tls': True,
    }
    if not cfg['password']:
        print(NO + ' 비밀번호가 비어 있습니다.')
        return None
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(
        json.dumps(cfg, ensure_ascii=False, indent=1) + '\n')
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    print(OK + ' data/deploy.json 에 저장했습니다 (저장소에는 올라가지 않습니다).')
    return cfg


def test_ftp():
    step(4, 'FTP 접속 시험')
    import deploy
    # deploy.py 가 실제로 쓰는 그 설정으로 붙어 봅니다 (환경변수·기본 포트까지 동일).
    try:
        cfg = deploy.load_settings()
    except SystemExit as e:
        print(NO + ' %s' % e)
        return False
    try:
        ftp = deploy.connect(cfg)
    except Exception as e:                                # noqa: BLE001
        print(NO + ' 붙지 못했습니다: %s' % e)
        print('   카페24 관리자 → 보안관리 → FTP/Shell 접속설정 에서')
        print('   지금 쓰는 IP 가 허용돼 있는지 확인해 주세요.')
        return False
    try:
        ftp.cwd(cfg['remoteDir'])
        names = ftp.nlst()
        print('   %s 안에 항목 %d개' % (cfg['remoteDir'], len(names)))
        print(OK + ' 접속과 폴더 확인까지 됐습니다.')
        return True
    except Exception as e:                                # noqa: BLE001
        print(NO + ' 폴더를 열지 못했습니다: %s' % e)
        print('   remoteDir 이 맞는지 확인해 주세요 (보통 /www/endgame).')
        return False
    finally:
        try:
            ftp.quit()
        except Exception:                                 # noqa: BLE001
            pass


def test_sheet():
    step(5, '구글시트 받아오기 시험')
    import asl_import
    try:
        text = asl_import.fetch_sheet_csv()
    except SystemExit as e:
        print(NO + ' %s' % e)
        return False
    sets = asl_import.read_sets_csv(text)
    print('   세트 %d개를 읽었습니다.' % len(sets))
    if not sets:
        print(NO + ' 내용이 비었습니다. 시트 주소(data/asl-source.json)를 확인해 주세요.')
        return False
    print(OK + ' 시트가 잘 읽힙니다.')
    return True


def test_build():
    step(6, '사이트 만들어 보기')
    r = subprocess.run([sys.executable, os.path.join(HERE, 'build.py')],
                       cwd=ROOT, capture_output=True, text=True)
    tail = [x for x in (r.stdout or '').strip().split('\n') if x][-3:]
    for line in tail:
        print('   ' + line)
    if r.returncode != 0:
        print(NO + ' 빌드가 실패했습니다.')
        print('   ' + (r.stderr or '').strip()[-400:])
        return False
    print(OK + ' 사이트가 만들어집니다.')
    return True


def main():
    print('스타크래프트 기록실 — 처음 준비')
    print('폴더: %s' % ROOT)

    if not check_python():
        return 1
    if not check_openpyxl():
        return 1
    cfg = setup_ftp()
    if not cfg:
        return 1
    ftp_ok = test_ftp()
    sheet_ok = test_sheet()
    build_ok = test_build()

    print('\n' + '═' * 56)
    if ftp_ok and sheet_ok and build_ok:
        print('준비가 끝났습니다. 이제 이렇게 쓰시면 됩니다.\n')
        print('   python3 tools/update.py --dry-run   무엇이 달라지는지만 보기')
        print('   python3 tools/update.py             시트부터 사이트까지 한 번에')
        print('\n휴대폰에서 쓰시려면 이 폴더에서 Claude Code 를 켜 두세요.')
        print('그 뒤로는 /갱신 /확인 /배포 /상태 만 치면 됩니다.')
        return 0
    print('아직 안 되는 것이 있습니다:')
    if not ftp_ok:
        print('   - FTP 접속')
    if not sheet_ok:
        print('   - 구글시트 받아오기')
    if not build_ok:
        print('   - 사이트 만들기')
    print('\n위에 적힌 안내를 보고 고친 뒤 다시 돌려 주세요.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
