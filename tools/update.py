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
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import asl_import                                 # noqa: E402
import endgame_import                             # noqa: E402

# --auto-apply-deletes(클라우드)에서 '작은 수정'으로 보고 자동 반영을 허용하는
# 실제 삭제량(그로스)의 상한. 이보다 크게 지워지면(라운드·대량 삭제 등) 사고
# 가능성이 있어 멈추고 슬랙으로 알립니다. 순증감(총합 차이)이 아니라 '실제로
# 줄어든 양'으로 판단하므로, 다른 곳이 늘어 총합이 늘어도 큰 삭제를 놓치지 않습니다.
AUTO_DELETE_MAX_ASL_SETS = 15      # ASL: 줄어든 세트 수 (한 라운드 = 보통 16세트 이상)
AUTO_DELETE_MAX_EG_MATCHES = 2     # 끝장전: 사라진 경기 수

# 유튜브 다시보기 재조회(fetch_videos --refresh)는 두 채널의 업로드 목록을 통째로
# 받아오는 '비싼' 작업입니다 — YouTube Data API 하루 할당량(10,000)을 크게 씁니다.
# 자동 갱신이 15분마다 돌기 때문에(2026-09-16) 매번 하면 할당량을 넘겨 영상이
# 아예 안 붙습니다.
#
# 그래서 **영상이 보통 올라오는 시간대에만** 확인합니다 (2026-09-16 사장님 지시).
# 그 밖의 시간에 뒤져 봐야 새 영상이 없어 할당량만 씁니다.
#
#   VIDEO_WINDOW_KST — 확인할 시각(KST, 24시간). (14, 15) 면 14시대·15시대에만.
#                      빈 튜플 ()로 두면 아무 때도 안 합니다.
#   그 시간대 안에서도 **한 시간에 한 번만** 봅니다(15분마다 실행되므로 네 번 중 한 번).
#
# ⚠ 이 값은 추측하지 말고 실제 업로드 시각을 보고 정하세요:
#       python3 tools/fetch_videos.py --when
#   최근 180일 업로드 시각 분포를 찍고, 넣을 값까지 그대로 알려 줍니다.
#   (자동 갱신 로그에도 매번 이 표가 찍히므로 Actions 로그에서도 볼 수 있습니다.)
VIDEO_WINDOW_KST = (14, 15)   # ⚠ 실측 전 임시값 — 아래 --when 결과로 바꿀 것
STATE_PATH = os.path.join(ROOT, 'data', '.update-state.json')

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
    ap.add_argument('--auto-apply-deletes', action='store_true',
                    help='작은 삭제는 자동 반영(=--force), 큰 삭제는 멈춤+경고 — 클라우드용')
    ap.add_argument('--videos', choices=('auto', 'always', 'never'), default='auto',
                    help='유튜브 다시보기 재조회 — auto(기본): 영상이 보통 올라오는 '
                         'KST %s 에만' % ('·'.join('%d시' % h for h in VIDEO_WINDOW_KST)
                                          or '(없음)'))
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

    # 기록이 줄었을 때(삭제)의 처리:
    #   기본        — 사고 방지를 위해 멈춥니다(사람이 9_삭제반영.bat 로 확인).
    #   --force     — 무조건 반영.
    #   --auto-apply-deletes(클라우드) — 조금 줄면 자동 반영, 대량 감소는 멈춤+경고.
    force = args.force
    if (shrank or eg_lost) and not force:
        # '실제로 줄어든 양'(그로스)으로 판단합니다 — 다른 곳이 늘어 총합이 늘어도
        # 큰 삭제(라운드 통째 삭제 등)를 순증감에 가려 놓치지 않기 위함입니다.
        asl_lost = _asl_lost_sets(old, data)
        eg_lost_matches = eg_lost                  # summarize 가 돌려준 '사라진 경기 수'(그로스)
        big_delete = (asl_lost > AUTO_DELETE_MAX_ASL_SETS
                      or eg_lost_matches > AUTO_DELETE_MAX_EG_MATCHES)
        detail = ('삭제 감지 — ASL 세트 -%d · 끝장전 경기 -%d '
                  '(지금 총합: 끝장전 세트 %d · ASL 세트 %d)'
                  % (asl_lost, eg_lost_matches,
                     eg_new['global']['totalSets'], data['global']['totalSets']))

        if args.auto_apply_deletes and not big_delete:
            # 작은 수정 — 자동 반영하고, 무엇이 얼마나 지워졌는지 슬랙으로 알립니다.
            force = True
            print('\n' + detail + '\n작은 수정이라 자동 반영합니다.')
            try:
                import notify
                notify.send({'title': '끝장전 삭제 자동 반영', 'level': 'warn',
                             'lines': ['시트에서 지운 경기를 사이트에도 반영했습니다.',
                                       detail,
                                       '실수로 지우신 거면 시트를 되살리면 다음 갱신에 자동 복구됩니다.']},
                            key=None)
            except Exception as e:
                print('  (슬랙 알림 건너뜀 — %s)' % e)
        else:
            # 자동 반영을 안 켰거나(수동 모드), 큰 삭제(사고 의심) → 멈춤 + 경고.
            try:
                import notify
                if big_delete:
                    notify.notify_problem('끝장전 갱신 중단 — 큰 삭제 감지',
                        ['기록이 한 번에 크게 줄어(작은 수정 기준 초과) 사고 가능성이 있어 반영하지 않았습니다.',
                         detail,
                         '정말 지우신 게 맞으면 PC에서 9_삭제반영.bat, 아니면 시트를 확인해 주세요.'])
                else:
                    notify.notify_problem('끝장전 갱신 중단 — 데이터가 줄었습니다',
                        ['시트에서 경기·세트가 지워진 것 같아 자동 갱신을 멈췄습니다.',
                         detail,
                         "정말 지우신 게 맞으면 PC에서 '삭제반영'(9_삭제반영.bat)을 눌러 주세요.",
                         '실수라면 시트를 되살려 주세요 — 여기서는 아무것도 바꾸지 않았습니다.'])
            except Exception as e:
                print('  (슬랙 알림 건너뜀 — %s)' % e)
            raise SystemExit(
                '\n⚠ 데이터가 줄었습니다%s — 시트에서 경기·세트가 지워진 것 같습니다.\n'
                "  · 시트에서 '일부러' 지우신 거라면  →  '삭제반영' (9_삭제반영.bat) 을 눌러 주세요.\n"
                '     그러면 위 [사라짐] 목록이 사이트에도 반영됩니다.\n'
                '  · 지운 적이 없다면  →  시트를 확인해 주세요 (부분 로딩·실수일 수 있습니다).\n'
                '  안전을 위해 여기서는 아무것도 바꾸지 않았습니다.'
                % (' (큰 삭제 — 사고 의심)' if big_delete else ''))

    run('asl_import.py', '--sheet')
    run('endgame_import.py', *(['--write', '--force'] if force else ['--write']))
    # 중계진 예측(보너스) — 시트 탭이 없거나 실패해도 전체 갱신은 멈추지 않습니다.
    try:
        subprocess.run([sys.executable, os.path.join(HERE, 'predict_import.py'), '--write'], cwd=ROOT)
    except Exception as e:
        print('  중계진 예측 갱신 건너뜀:', e)
    # 유튜브 다시보기(보너스) — API 로 새 영상까지 다시 받아 경기에 붙임(캐시 무시 --refresh).
    # 비싼 작업이라 필요할 때만 돕니다(위 VIDEO_REFRESH_HOURS 설명 참고).
    # 키·할당량 문제로 실패해도 기존 videos.json 으로 계속 진행합니다.
    state = _load_state()
    why = _video_refresh_reason(args.videos, state)
    if why is None:
        kst, _ = _kst_slot()
        print('\n유튜브 다시보기 재조회는 건너뜁니다 — 지금 KST %02d시, 영상이 보통 '
              '올라오는 시간대(%s)가 아닙니다. (기존 videos.json 을 씁니다)'
              % (kst.hour, '·'.join('%d시' % h for h in VIDEO_WINDOW_KST) or '없음'))
    else:
        print('\n유튜브 다시보기 재조회 — %s' % why)
        try:
            r = subprocess.run([sys.executable, os.path.join(HERE, 'fetch_videos.py'),
                                '--refresh', '--write'], cwd=ROOT)
            if r.returncode == 0:
                now = datetime.now(timezone.utc)
                state['videosCheckedAt'] = now.strftime('%Y-%m-%dT%H:%M:%SZ')
                state['videosCheckedSlot'] = _kst_slot(now)[1]
                _save_state(state)
            else:
                print('  유튜브 영상 갱신 실패(코드 %d) — 기존 videos.json 으로 계속합니다.'
                      % r.returncode)
        except Exception as e:
            print('  유튜브 영상 갱신 건너뜀:', e)
    run('build.py')
    # 데이터 정합성 상시 점검(17종 교차검증) — 어긋나면 콘솔·로그에 남깁니다.
    # 배포는 막지 않습니다(이미 빌드된 것). 자동 갱신마다 돌아 '데이터 감시' 역할.
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, 'data_check.py')], cwd=ROOT)
        if r.returncode != 0:
            print('  ⚠ 데이터 정합성 점검에서 이상이 발견됐습니다 — 위 로그를 확인하세요.')
    except Exception as e:
        print('  데이터 점검 건너뜀:', e)
    if args.no_deploy:
        print('\n--no-deploy 라 올리지 않았습니다. '
              '올리려면 python3 tools/deploy.py 를 실행하세요.')
        return
    run('deploy.py')
    print('\n끝났습니다.')


def _load_state():
    """갱신 상태(마지막 유튜브 조회 시각 등). 없으면 빈 것으로 봅니다."""
    try:
        return json.load(io.open(STATE_PATH, encoding='utf-8'))
    except (IOError, OSError, ValueError):
        return {}


def _save_state(state):
    try:
        json.dump(state, io.open(STATE_PATH, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
    except (IOError, OSError) as e:
        print('  (갱신 상태 저장 건너뜀 — %s)' % e)


def _kst_slot(now=None):
    """지금이 KST 로 몇 년-월-일-몇 시인지. '이 시간대에 이미 봤나'를 가리는 열쇠입니다."""
    kst = (now or datetime.now(timezone.utc)) + timedelta(hours=9)
    return kst, kst.strftime('%Y-%m-%dT%H')


def _video_refresh_reason(mode, state, now=None):
    """지금 유튜브를 다시 뒤질 이유. 없으면 None (= 건너뜀)."""
    if mode == 'never':
        return None
    if mode == 'always':
        return '--videos always 로 지정하셨습니다'
    kst, slot = _kst_slot(now)
    if kst.hour not in VIDEO_WINDOW_KST:
        return None                       # 영상이 올라오는 시간대가 아닙니다
    if state.get('videosCheckedSlot') == slot:
        return None                       # 이 시간대에는 이미 봤습니다
    return 'KST %02d시 — 영상이 보통 올라오는 시간대입니다' % kst.hour


def _asl_lost_sets(old, new):
    """대회·라운드별로 줄어든 세트 수의 합(그로스). 늘어난 곳은 세지 않습니다.

    순증감(총합 차이)이 아니라 '실제로 줄어든 양'만 봅니다 — 다른 라운드가
    늘어 총합이 늘어도, 어느 라운드가 통째로 지워지면 그 손실을 잡아냅니다.
    """
    if not old:
        return 0
    o = asl_import.summarize(old)                 # {대회: {라운드: 세트수}}
    n = asl_import.summarize(new)
    lost = 0
    for t, rounds in o.items():
        for r, sets in rounds.items():
            after = n.get(t, {}).get(r, 0)
            if after < sets:
                lost += sets - after
    return lost


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
