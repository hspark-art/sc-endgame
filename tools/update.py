#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""구글시트 → 사이트까지 한 번에.

    python3 tools/update.py

하는 일
  1. 구글시트에서 ASL 기록을 받아옵니다 (data/asl-source.json 의 주소)
  2. 구글시트에서 끝장전 기록을 받아옵니다 (data/endgame-source.json 의 주소)
  3. 지금 데이터와 무엇이 다른지 보여 주고 data/asl.json · data/endgame.json 을 갱신합니다
  4. 사이트를 다시 만듭니다
  5. FTP 로 올립니다 (바뀐 파일만)

옵션
  --dry-run     아무것도 바꾸지 않고 시트에 무엇이 달라졌는지만 봅니다
  --no-deploy   만들기까지만 하고 올리지는 않습니다
  --force       기록이 줄어든 경우에도 그냥 진행합니다

시트에서 줄이 지워지는 등 기록이 **줄어들면** 멈춥니다. 사고로 데이터가
날아간 것을 사이트에 그대로 반영하지 않기 위해서입니다. 의도한 삭제라면
--force 를 붙이세요.
"""

import argparse
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import asl_import                                 # noqa: E402
import endgame_import                             # noqa: E402

# 윈도우 콘솔에서 한글·기호가 깨지거나 터지지 않게 합니다.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass



def run(script, *args):
    cmd = [sys.executable, os.path.join(HERE, script)] + list(args)
    print('\n$ python3 tools/%s %s' % (script, ' '.join(args)))
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        raise SystemExit('  %s 에서 멈췄습니다 (코드 %d)' % (script, r.returncode))


def main():
    ap = argparse.ArgumentParser(description='구글시트에서 받아 사이트까지 갱신합니다.')
    ap.add_argument('--dry-run', action='store_true', help='바꾸지 않고 차이만 보기')
    ap.add_argument('--no-deploy', action='store_true', help='올리지 않고 만들기까지만')
    ap.add_argument('--force', action='store_true', help='기록이 줄어도 진행')
    args = ap.parse_args()

    print('── 1. 구글시트 받아오기 ' + '─' * 30)
    sets, fixes = asl_import.load_sets()          # 시트에서 읽고 종족까지 맞춥니다
    data = asl_import.build(sets, asl_import.group_matches(sets))

    out = os.path.join(ROOT, 'data', 'asl.json')
    old = None
    if os.path.exists(out):
        try:
            old = json.load(io.open(out, encoding='utf-8'))
        except ValueError:
            old = None

    if fixes:
        print('  여러 종족으로 출전한 선수 (랜덤 출전 — 세트 기록은 그대로 씁니다):')
        for name, best, others in fixes:
            print('    %s 주 종족 %s · 다른 종족으로 뛴 줄: %s'
                  % (name, best, ', '.join('%s %d줄' % kv for kv in sorted(others.items()))))

    print('\n── 2. 지금 데이터와 견주기 ' + '─' * 28)
    shrank = _shrank(old, data)
    asl_import.show_diff(old, data)

    print('')
    print('── 3. 끝장전 시트 받아오기 ' + '─' * 28)
    eg_sets, eg_fixes = endgame_import.load_sets()
    print('  세트 %d줄을 읽었습니다.' % len(eg_sets))
    endgame_import.show_fixes(eg_fixes)
    eg_path = os.path.join(ROOT, 'data', 'endgame.json')
    eg_old = None
    if os.path.exists(eg_path):
        try:
            eg_old = json.load(io.open(eg_path, encoding='utf-8'))
        except ValueError:
            eg_old = None
    eg_new = endgame_import.build_doc(eg_sets, (eg_old or {}).get('builtAt') or '')
    eg_lost = endgame_import.summarize(eg_old, eg_new)

    if args.dry_run:
        print('\n--dry-run 이라 여기서 멈춥니다. 아무것도 바꾸지 않았습니다.')
        return

    if (shrank or eg_lost) and not args.force:
        # 기록이 줄어드는 건 사고 신호라 슬랙으로도 알립니다 (문제 있을 때만).
        try:
            import notify
            notify.notify_problem('끝장전 갱신 중단 — 기록이 줄었습니다',
                ['시트에서 줄이 지워졌을 수 있어 자동 갱신을 멈췄습니다.',
                 '시트를 확인하시고, 의도한 삭제면 --force 로 다시 실행하세요.'])
        except Exception:
            pass
        raise SystemExit(
            '\n기록이 줄었습니다. 시트에서 줄이 지워졌을 수 있어 멈춥니다.\n'
            '  시트를 확인해 보시고, 의도한 것이면 --force 를 붙여 다시 실행하세요.')

    run('asl_import.py', '--sheet')
    run('endgame_import.py', *(['--write', '--force'] if args.force else ['--write']))
    run('build.py')
    if args.no_deploy:
        print('\n--no-deploy 라 올리지 않았습니다. '
              '올리려면 python3 tools/deploy.py 를 실행하세요.')
        return
    run('deploy.py')
    print('\n끝났습니다.')


def _shrank(old, new):
    """대회·라운드별 세트 수가 하나라도 줄었는지."""
    if not old:
        return False
    o = asl_import.summarize(old)
    n = asl_import.summarize(new)
    if set(o) - set(n):
        return True
    for t in o:
        for r, c in o[t].items():
            if n.get(t, {}).get(r, 0) < c:
                return True
    return False


if __name__ == '__main__':
    main()
