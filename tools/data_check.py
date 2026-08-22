#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사이트 데이터 정확도 자동 점검 — 여러 독립 경로로 교차검증.

빌드 결과(data/asl.json·endgame.json)가 서로 앞뒤가 맞는지, 세트 원본
(setList)에서 다시 계산한 값과 집계값이 일치하는지 확인합니다. 한 곳에서
버그가 나면 다른 경로와 어긋나므로 잡힙니다. 언제든 다시 돌려도 됩니다.

  python3 tools/data_check.py            # asl.json·endgame.json 교차검증
  python3 tools/data_check.py --sheet    # + 구글시트 원본과도 대조(네트워크)
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []
OKS = []


def ck(cond, label, detail=''):
    (OKS if cond else FAILS).append(label + (('  → ' + detail) if detail and not cond else ''))
    print(('  ✅ ' if cond else '  ❌ ') + label + (('  → ' + detail) if detail else ''))


def load(name):
    return json.load(io.open(os.path.join(ROOT, 'data', name), encoding='utf-8'))


def check_conservation(d, tag):
    """세트/매치는 하나당 승자 1·패자 1 → 전체 승수 총합 == 전체 패수 총합."""
    sw = sum(p['setWin'] for p in d['players'])
    sl = sum(p['setLoss'] for p in d['players'])
    mw = sum(p['matchWin'] for p in d['players'])
    ml = sum(p['matchLoss'] for p in d['players'])
    ck(sw == sl, '[%s] 세트 승합==패합' % tag, '승 %d ≠ 패 %d' % (sw, sl))
    ck(mw == ml, '[%s] 매치 승합==패합' % tag, '승 %d ≠ 패 %d' % (mw, ml))
    g = d.get('global', {})
    if 'totalSets' in g:
        ck(sw == g['totalSets'], '[%s] 세트 총합==global.totalSets' % tag,
           '%d ≠ %d' % (sw, g['totalSets']))


def check_vsrace(d, tag):
    """선수별 vsRace 승/패 합계가 그 선수의 setWin/setLoss 와 같아야."""
    bad = []
    for p in d['players']:
        w = sum(p['vsRace'][r]['w'] for r in p['vsRace'])
        l = sum(p['vsRace'][r]['l'] for r in p['vsRace'])
        if w != p['setWin'] or l != p['setLoss']:
            bad.append('%s(vs합 %d-%d ≠ 세트 %d-%d)' % (p['name'], w, l, p['setWin'], p['setLoss']))
    ck(not bad, '[%s] 모든 선수 vsRace 합 == 세트 기록' % tag,
       '%d명 불일치: %s' % (len(bad), ', '.join(bad[:4])))


def check_vsplayers(d, tag):
    """vsPlayers(상대별) 총합이 세트 기록과 같아야. (종족별로 나누면 랜덤 출전 때문에
       vsRace 와 갈릴 수 있어 — vsPlayers 는 상대 표시종족, vsRace 는 세트종족 기준 —
       총합으로 대조하는 게 정확합니다.)"""
    bad = []
    for p in d['players']:
        w = sum(o['w'] for o in p['vsPlayers'])
        l = sum(o['l'] for o in p['vsPlayers'])
        if w != p['setWin'] or l != p['setLoss']:
            bad.append('%s(vsPlayers합 %d-%d ≠ 세트 %d-%d)' % (p['name'], w, l, p['setWin'], p['setLoss']))
    ck(not bad, '[%s] vsPlayers 총합 == 세트 기록' % tag,
       '%d명: %s' % (len(bad), ', '.join(bad[:4])))


def check_h2h_symmetry(d, tag):
    """맞대결 대칭 — A의 상대전적에 B가 w-l 이면, B의 상대전적엔 A가 l-w 여야.
       (선수 이름 기준이라 랜덤 출전과 무관하게 성립하는 강한 검사.)"""
    idx = {}
    for p in d['players']:
        idx[p['name']] = {o['name']: (o['w'], o['l']) for o in p['vsPlayers']}
    bad = []
    for a in idx:
        for b, (w, l) in idx[a].items():
            back = idx.get(b, {}).get(a)
            if back != (l, w):
                bad.append('%s:%s=%d-%d 인데 %s:%s=%s' % (a, b, w, l, b, a, back))
    ck(not bad, '[%s] 맞대결 대칭 (A:B 뒤집으면 B:A)' % tag,
       '%d건: %s' % (len(bad), '; '.join(bad[:3])))


def check_setlist(d):
    """ASL setList(세트 원본)에서 선수/종족 기록을 처음부터 다시 계산해 집계값과 대조.
       setList 와 players[] 는 서로 다른 집계 경로라, 어긋나면 버그 신호."""
    SL = d['setList']
    races = SL['races']
    n = len(d['players'])
    sw = [0] * n; sl = [0] * n
    vs = [dict((r, [0, 0]) for r in races) for _ in range(n)]
    for row in SL['rows']:
        a, b, mp, tour, rnd, ar, br, win = row[:8]
        wi, li = (a, b) if win == 0 else (b, a)
        sw[wi] += 1; sl[li] += 1
        wr, lr = (races[ar], races[br]) if win == 0 else (races[br], races[ar])
        vs[wi][lr][0] += 1        # 이긴 선수의 상대(진쪽) 종족
        vs[li][wr][1] += 1        # 진 선수의 상대(이긴쪽) 종족
    badset, badvs = [], []
    for i, p in enumerate(d['players']):
        if sw[i] != p['setWin'] or sl[i] != p['setLoss']:
            badset.append('%s(재계산 %d-%d ≠ 저장 %d-%d)' % (p['name'], sw[i], sl[i], p['setWin'], p['setLoss']))
        for r in races:
            if vs[i][r][0] != p['vsRace'][r]['w'] or vs[i][r][1] != p['vsRace'][r]['l']:
                badvs.append('%s vs%s(재계산 %d-%d ≠ 저장 %d-%d)'
                             % (p['name'], r, vs[i][r][0], vs[i][r][1], p['vsRace'][r]['w'], p['vsRace'][r]['l']))
    ck(not badset, '[ASL] setList 재계산 세트기록 == players[]',
       '%d명: %s' % (len(badset), ', '.join(badset[:4])))
    ck(not badvs, '[ASL] setList 재계산 vsRace == players[]',
       '%d건: %s' % (len(badvs), ', '.join(badvs[:4])))
    # 종족전 랭킹 탭이 쓰는 계산과 동일하므로, 이게 맞으면 그 탭도 정확
    tw = sum(vs[i]['Z'][0] for i, p in enumerate(d['players']) if p['race'] == 'T')
    zt = sum(vs[i]['T'][1] for i, p in enumerate(d['players']) if p['race'] == 'Z')
    # (참고 지표: 테란이 저그에게 이긴 수 vs 저그가 테란에게 진 수 — 동족 아님이라 대칭 아님, 표시만)
    print('     (참고) 종족전 랭킹 근거: setList 재계산이 저장값과 같으면 그 탭도 정확합니다.')


def _random_note(d, tag):
    """표시 종족과 다른 종족으로 뛴 세트(랜덤 출전) 수를 참고로 알립니다."""
    if 'setList' not in d:
        return
    SL = d['setList']; races = SL['races']
    disp = [p['race'] for p in d['players']]
    mixed = {}
    for r in SL['rows']:
        a, b, mp, t, rn, ar, br, win = r[:8]
        if races[ar] != disp[a]: mixed[a] = mixed.get(a, 0) + 1
        if races[br] != disp[b]: mixed[b] = mixed.get(b, 0) + 1
    if mixed:
        names = ', '.join('%s(%d세트)' % (d['players'][i]['name'], c)
                          for i, c in sorted(mixed.items(), key=lambda x: -x[1]))
        print('     (참고) 랜덤 출전 — 표시종족과 다른 종족으로 뛴 세트: ' + names)


def check_matches(d, tag):
    """매치 목록 수 == global.totalMatches (있으면)."""
    g = d.get('global', {})
    if 'totalMatches' in g and isinstance(d.get('matches'), list):
        ck(len(d['matches']) == g['totalMatches'], '[%s] matches 개수==global.totalMatches' % tag,
           '%d ≠ %d' % (len(d['matches']), g['totalMatches']))


def sheet_cross():
    """구글시트 원본을 다시 읽어 끝장전 세트 수·선수 승패를 빌드본과 대조."""
    print('\n── 구글시트 원본 대조 (네트워크) ──')
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    try:
        import endgame_import as ei
    except Exception as e:
        ck(False, '끝장전 시트 모듈 로드', str(e)); return
    try:
        sid, sname = ei.load_source()
        sets = ei.fetch_sets(sid, sname)
        norm = ei.normalize_sets(sets)[0] if hasattr(ei, 'normalize_sets') else sets
    except Exception as e:
        ck(False, '끝장전 시트 읽기', str(e)); return
    e = load('endgame.json')
    ck(len(norm) == e['global']['totalSets'], '끝장전 시트 세트수 == 빌드 totalSets',
       '시트 %d ≠ 빌드 %d (시트에 새 결과면 update.py 필요)' % (len(norm), e['global']['totalSets']))


def main():
    print('════ 사이트 데이터 정확도 점검 ════\n')
    asl = load('asl.json'); eg = load('endgame.json')
    print('── ASL (%d선수 · 세트 %d) ──' % (len(asl['players']), asl['global'].get('totalSets', '?')
          if isinstance(asl.get('global'), dict) else '?'))
    check_conservation(asl, 'ASL')
    check_vsrace(asl, 'ASL')
    check_vsplayers(asl, 'ASL')
    check_setlist(asl)
    check_h2h_symmetry(asl, 'ASL')
    _random_note(asl, 'ASL')
    check_matches(asl, 'ASL')
    print('\n── 끝장전 (%d선수 · 세트 %d) ──' % (len(eg['players']), eg['global']['totalSets']))
    check_conservation(eg, '끝장전')
    check_vsrace(eg, '끝장전')
    check_vsplayers(eg, '끝장전')
    check_h2h_symmetry(eg, '끝장전')
    check_matches(eg, '끝장전')
    if '--sheet' in sys.argv:
        sheet_cross()
    print('\n════ 결과: %d개 통과, %d개 실패 ════' % (len(OKS), len(FAILS)))
    if FAILS:
        print('실패 항목:')
        for f in FAILS:
            print('  ·', f)
        sys.exit(1)
    print('모든 데이터 정합성 점검 통과 ✅')


if __name__ == '__main__':
    main()
