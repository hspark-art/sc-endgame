#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""끝장전 구글시트(Results 탭) → data/endgame.json.

    python3 tools/endgame_import.py              # 무엇이 달라지는지만 보여줍니다
    python3 tools/endgame_import.py --write      # data/endgame.json 에 실제로 기록
    python3 tools/endgame_import.py --write --force   # 기록이 줄어도 강행

ASL 의 asl_import.py 와 짝이 되는 도구입니다. 시트에 이미 계산된 탭이 여럿
있지만 믿지 않고 Results 원본 행만 읽어 처음부터 다시 집계합니다 — 시트 수식이
나중에 깨지거나 바뀌어도 사이트가 영향받지 않게 하려는 것입니다.

세트 한 줄이 Winner / Race / Loser / Race / Map / Date 입니다.
같은 날 같은 두 선수의 세트를 하나의 매치로 묶습니다.

주의: Results 탭 헤더에는 'Race' 가 두 번 나옵니다(승자 종족·패자 종족).
이름으로 읽으면 뒤 값이 앞 값을 덮어쓰므로 열 순서(index)로 읽습니다.
시트에 열을 새로 끼워넣으면 이 부분이 깨집니다.

기록이 줄면 멈춥니다. 시트에서 줄이 지워지는 사고를 막기 위해서입니다.
줄어든 것이 의도한 삭제라고 확인되기 전에는 --force 를 붙이지 마세요.
"""

import argparse
import csv
import io
import json
import os
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass

SOURCE = os.path.join(ROOT, 'data', 'endgame-source.json')
TARGET = os.path.join(ROOT, 'data', 'endgame.json')

RACES = ['T', 'P', 'Z']
# 맵별 종족 상성 표기는 이 세 가지로 고정입니다 (앞 종족 기준 승/패).
MU_PAIRS = [('Z', 'P'), ('T', 'Z'), ('P', 'T')]


def load_source():
    if not os.path.exists(SOURCE):
        raise SystemExit('data/endgame-source.json 이 없습니다.')
    c = json.load(io.open(SOURCE, encoding='utf-8'))
    return c['sheetId'], c.get('sheet') or 'Results'


def fetch_sets(sheet_id, sheet_name):
    """Results 탭을 인증 없이 CSV 로 받아 세트 목록으로 만듭니다."""
    url = ('https://docs.google.com/spreadsheets/d/%s/gviz/tq?tqx=out:csv&sheet=%s'
           % (sheet_id, urllib.parse.quote(sheet_name)))
    raw = urllib.request.urlopen(url, timeout=60).read().decode('utf-8')
    rows = list(csv.reader(io.StringIO(raw)))
    if len(rows) < 2:
        raise SystemExit('시트를 읽었지만 내용이 없습니다. 공유 설정을 확인하세요.')
    out = []
    for r in rows[1:]:
        if len(r) < 6:
            continue
        w, wr, lo, lr, mp, dt = (x.strip() for x in r[:6])
        if not (w and lo and dt):
            continue
        out.append((dt, w, wr, lo, lr, mp))
    return out


# 시트에 잘못 적힌 맵 이름을 바로잡습니다 (왼쪽 → 오른쪽).
# 대소문자·띄어쓰기만 다른 것은 아래 normalize_sets 가 알아서 합치므로
# 여기에는 '사람이 판단해야 했던 것'만 적습니다.
MAP_ALIASES = {
    'MatchPoint': 'Match Point',
    'New Heartbreak Ridge': 'Neo Heartbreak Ridge Line',
}


def _mapkey(name):
    """대소문자·띄어쓰기를 무시한 맵 이름 열쇠."""
    return name.replace(' ', '').lower()


def normalize_sets(sets):
    """시트에 잘못 적힌 것을 바로잡습니다.

    원본 시트는 건드리지 않습니다. 무엇을 고쳤는지 함께 돌려주므로
    실행할 때마다 화면에 나옵니다.

      1. 선수 종족이 줄마다 다르게 적힌 경우 → 가장 많이 적힌 종족으로
      2. 맵 이름이 대소문자·띄어쓰기만 다른 경우 → 가장 많이 쓰인 표기로
      3. MAP_ALIASES 에 적어 둔 맵 이름 → 정해 둔 표기로
    """
    race_count = {}
    map_count = {}
    for _dt, w, wr, lo, lr, mp in sets:
        for who, r in ((w, wr), (lo, lr)):
            race_count.setdefault(who, {})
            race_count[who][r] = race_count[who].get(r, 0) + 1
        if mp:
            name = MAP_ALIASES.get(mp, mp)
            k = _mapkey(name)
            map_count.setdefault(k, {})
            map_count[k][name] = map_count[k].get(name, 0) + 1

    # 선수마다 가장 많이 적힌 종족, 맵마다 가장 많이 쓰인 표기를 정답으로 봅니다.
    best_race = {}
    for who, c in race_count.items():
        if len(c) > 1:
            best_race[who] = max(c.items(), key=lambda kv: kv[1])[0]
    best_map = {}
    for k, c in map_count.items():
        best_map[k] = max(c.items(), key=lambda kv: kv[1])[0]

    fixes = []
    out = []
    for dt, w, wr, lo, lr, mp in sets:
        nwr = best_race.get(w, wr)
        nlr = best_race.get(lo, lr)
        if nwr != wr:
            fixes.append('%s  %s 종족 %s → %s' % (dt, w, wr, nwr))
        if nlr != lr:
            fixes.append('%s  %s 종족 %s → %s' % (dt, lo, lr, nlr))
        nmp = mp
        if mp:
            nmp = best_map.get(_mapkey(MAP_ALIASES.get(mp, mp)), mp)
            if nmp != mp:
                fixes.append('%s  맵 이름 %s → %s' % (dt, mp, nmp))
        out.append((dt, w, nwr, lo, nlr, nmp))
    return out, fixes


def load_sets():
    """시트에서 읽고 잘못 적힌 것까지 바로잡아 돌려줍니다."""
    sets = fetch_sets(*load_source())
    return normalize_sets(sets)


def group_matches(sets):
    """같은 날 같은 두 선수의 세트를 하나의 매치로 묶습니다.

    반환값은 (매치 목록, 매치별 세트 목록) 입니다. 세트 목록은 맵 집계에만 씁니다.
    """
    order, bucket = [], {}
    for s in sets:
        dt, w, wr, lo, lr, mp = s
        key = (dt, tuple(sorted((w, lo))))
        if key not in bucket:
            bucket[key] = []
            order.append(key)
        bucket[key].append(s)

    matches, setlist = [], []
    for key in order:
        ss = bucket[key]
        dt = key[0]
        players = sorted(key[1])
        wins = {players[0]: 0, players[1]: 0}
        race = {}
        maps = []
        for dt2, w, wr, lo, lr, mp in ss:
            if w in wins:
                wins[w] += 1
            race[w] = wr
            race[lo] = lr
            maps.append(mp)
        winner = players[0] if wins[players[0]] >= wins[players[1]] else players[1]
        matches.append({
            'date': dt,
            'players': players,
            'race': {p: race.get(p, '') for p in players},
            'setWins': {p: wins[p] for p in players},
            'winner': winner,
            'maps': maps,
            'youtubeUrl': None,
        })
        setlist.append(ss)

    idx = sorted(range(len(matches)), key=lambda i: matches[i]['date'], reverse=True)
    return [matches[i] for i in idx], [setlist[i] for i in idx]


def build_players(matches, setlist):
    acc = {}
    for m, ss in sorted(zip(matches, setlist), key=lambda z: z[0]['date']):
        a, b = m['players']
        for me, foe in ((a, b), (b, a)):
            p = acc.get(me)
            if p is None:
                p = acc[me] = {
                    'name': me, 'race': m['race'][me],
                    'matchWin': 0, 'matchLoss': 0, 'setWin': 0, 'setLoss': 0,
                    'appearances': 0,
                    'firstDate': m['date'], 'lastDate': m['date'],
                    'vsRace': dict((r, {'w': 0, 'l': 0}) for r in RACES),
                    '_vs': {},
                }
            p['race'] = m['race'][me]
            p['appearances'] += 1
            p['lastDate'] = m['date']
            w, l = m['setWins'][me], m['setWins'][foe]
            p['setWin'] += w
            p['setLoss'] += l
            if m['winner'] == me:
                p['matchWin'] += 1
            else:
                p['matchLoss'] += 1
            # 상대 종족별 집계는 '세트 단위'로 셉니다. 같은 경기 안에서도 줄마다
            # 종족이 다르게 적힌 경우가 있어(시트 입력 흔들림), 매치 대표 종족으로
            # 뭉뚱그리면 원본과 어긋납니다.
            for _dt, sw, swr, slo, slr, _mp in ss:
                if sw == me and slr in p['vsRace']:
                    p['vsRace'][slr]['w'] += 1
                elif slo == me and swr in p['vsRace']:
                    p['vsRace'][swr]['l'] += 1
            fr = m['race'][foe]
            v = p['_vs'].get(foe)
            if v is None:
                v = p['_vs'][foe] = {'name': foe, 'race': fr, 'w': 0, 'l': 0,
                                     'matches': []}
            v['race'] = fr
            v['w'] += w
            v['l'] += l
            v['matches'].append({'date': m['date'], 'w': w, 'l': l,
                                 'result': '승' if m['winner'] == me else '패'})

    players = []
    for p in acc.values():
        # 맞붙은 세트가 많은 순. 같으면 처음 만난 순서 그대로 둡니다.
        p['vsPlayers'] = sorted(p.pop('_vs').values(),
                                key=lambda v: -(v['w'] + v['l']))
        players.append(p)
    # 매치 승수가 많은 순. 같으면 먼저 나온 선수 순서 그대로 둡니다.
    players.sort(key=lambda p: -p['matchWin'])
    return players


def build_maps(matches, setlist):
    acc, order = {}, []
    pairs = [(x, y, '%s-%s' % (x, y)) for x, y in MU_PAIRS]
    for m, ss in sorted(zip(matches, setlist), key=lambda z: z[0]['date']):
        for dt, w, wr, lo, lr, name in ss:
            if not name:
                continue
            e = acc.get(name)
            if e is None:
                e = acc[name] = {
                    'name': name, 'totalSets': 0, '_days': set(),
                    'firstDate': dt, 'lastDate': dt,
                    'matchup': dict((k, {'w': 0, 'l': 0}) for _x, _y, k in pairs),
                    'byRace': dict((r, {'w': 0, 'l': 0}) for r in RACES),
                }
                order.append(name)
            e['totalSets'] += 1
            e['_days'].add(dt)
            e['lastDate'] = dt
            if wr in e['byRace']:
                e['byRace'][wr]['w'] += 1
            if lr in e['byRace']:
                e['byRace'][lr]['l'] += 1
            for x, y, k in pairs:
                if wr == x and lr == y:
                    e['matchup'][k]['w'] += 1
                elif wr == y and lr == x:
                    e['matchup'][k]['l'] += 1

    maps = []
    for name in order:
        e = acc[name]
        maps.append({'name': e['name'], 'totalSets': e['totalSets'],
                     'daysUsed': len(e['_days']), 'firstDate': e['firstDate'],
                     'lastDate': e['lastDate'], 'matchup': e['matchup'],
                     'byRace': e['byRace']})
    # 많이 쓰인 순. 같으면 먼저 쓰인 맵 순서 그대로 둡니다.
    maps.sort(key=lambda m: -m['totalSets'])
    return maps


def build_doc(sets, built_at):
    matches, setlist = group_matches(sets)
    players = build_players(matches, setlist)
    maps = build_maps(matches, setlist)
    dates = sorted(m['date'] for m in matches)
    return {
        'builtAt': built_at,
        'global': {
            'totalSets': len(sets),
            'totalMatches': len(matches),
            'totalPlayers': len(players),
            'firstDate': dates[0] if dates else '',
            'lastDate': dates[-1] if dates else '',
        },
        'players': players,
        'maps': maps,
        'matches': matches,
    }


def show_fixes(fixes):
    """시트를 읽으면서 바로잡은 것을 알려 줍니다. 원본 시트는 그대로입니다."""
    if not fixes:
        return
    print('  시트에 잘못 적힌 것을 읽으면서 바로잡았습니다 (원본 시트는 그대로):')
    seen = {}
    for f in fixes:
        seen[f[12:]] = seen.get(f[12:], 0) + 1     # 날짜를 뺀 내용으로 묶습니다
    for what, n in sorted(seen.items()):
        print('    %s%s' % (what, ('  (%d줄)' % n) if n > 1 else ''))


def summarize(old, new):
    """무엇이 달라지는지 한눈에 보여줍니다."""
    og, ng = (old or {}).get('global', {}), new['global']
    for label, key in (('세트', 'totalSets'), ('매치', 'totalMatches'),
                       ('선수', 'totalPlayers')):
        a, b = og.get(key, 0), ng[key]
        mark = '' if a == b else ('  (+%d)' % (b - a) if b > a else '  (%d)' % (b - a))
        print('  %-4s %6d → %6d%s' % (label, a, b, mark))

    def keyset(doc):
        return set((m['date'], tuple(sorted(m['players'])))
                   for m in (doc or {}).get('matches', []))
    added = sorted(keyset(new) - keyset(old))
    gone = sorted(keyset(old) - keyset(new))
    for k in added:
        print('   [추가] %s  %s' % (k[0], ' vs '.join(k[1])))
    for k in gone:
        print('   [사라짐] %s  %s' % (k[0], ' vs '.join(k[1])))
    return len(gone)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help='data/endgame.json 에 기록')
    ap.add_argument('--force', action='store_true', help='기록이 줄어도 강행')
    args = ap.parse_args()

    sheet_id, sheet_name = load_source()
    print('끝장전 시트에서 받아옵니다 — %s 탭' % sheet_name)
    sets, fixes = normalize_sets(fetch_sets(sheet_id, sheet_name))
    print('  세트 %d줄을 읽었습니다.' % len(sets))
    show_fixes(fixes)

    old = None
    if os.path.exists(TARGET):
        try:
            old = json.load(io.open(TARGET, encoding='utf-8'))
        except ValueError:
            old = None
    built_at = (old or {}).get('builtAt') or ''
    doc = build_doc(sets, built_at)
    lost = summarize(old, doc)

    if not args.write:
        print('실제로 기록하려면 --write 를 붙여 주세요.')
        return 0

    if lost and not args.force:
        print('')
        print('기록이 %d경기 줄어들어 멈췄습니다.' % lost)
        print('시트에서 줄이 지워졌을 수 있습니다. 사람이 확인한 뒤,')
        print('의도한 삭제가 맞으면 --force 를 붙여 다시 실행하세요.')
        return 1

    io.open(TARGET, 'w', encoding='utf-8').write(
        json.dumps(doc, ensure_ascii=False, indent=1) + chr(10))
    print('data/endgame.json 에 기록했습니다. 이제 tools/build.py 를 돌리세요.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
