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
import re
import sys
import unicodedata
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


def _won(cell):
    """상금 칸을 정수로. '￦100,000' → 100000, 빈칸·'￦0' → 0 (숫자만 남깁니다)."""
    d = ''.join(ch for ch in str(cell) if ch.isdigit())
    return int(d) if d else 0


def fetch_sets(sheet_id, sheet_name):
    """Results 탭을 인증 없이 CSV 로 받아 세트 목록으로 만듭니다.
    상금(7열 Prize)·더블찬스(8열 Double Chance)를 승자별로 합산해 함께 돌려줍니다."""
    url = ('https://docs.google.com/spreadsheets/d/%s/gviz/tq?tqx=out:csv&sheet=%s'
           % (sheet_id, urllib.parse.quote(sheet_name)))
    # 받아오면서 마지막 정상본을 data/sheet-backup/ 에 남깁니다.
    # 시트가 사라지거나 접속이 안 돼도 백업으로 계속 돌아갑니다.
    import sheetbackup
    raw, _used_backup = sheetbackup.fetch_csv(url, 'endgame')
    rows = list(csv.reader(io.StringIO(raw)))
    if len(rows) < 2:
        raise SystemExit('시트를 읽었지만 내용이 없습니다. 공유 설정을 확인하세요.')
    out = []
    prize = {}   # 승자 이름 → {'prize': 기본 상금 합, 'bonus': 더블찬스 합, 'sets': 이긴 세트 수}
    for r in rows[1:]:
        if len(r) < 6:
            continue
        w, wr, lo, lr, mp, dt = (x.strip() for x in r[:6])
        if not (w and lo and dt):
            continue
        out.append((dt, w, wr, lo, lr, mp))
        pz = _won(r[6]) if len(r) > 6 else 0
        bn = _won(r[7]) if len(r) > 7 else 0
        # 상금은 선수 이름으로 찾아 쓰므로 세트 쪽과 **똑같은 규칙**으로 다듬어야
        # 합니다(_player). 안 그러면 이름이 바로잡힌 선수의 상금만 옛 이름에
        # 남아 주인을 못 찾고 통째로 사라집니다 — 실제로 변헌제 → 변현제 건에서
        # 10만원이 증발했습니다.
        e = prize.setdefault(_player(w), {'prize': 0, 'bonus': 0, 'sets': 0, 'byYear': {}})
        e['prize'] += pz
        e['bonus'] += bn
        e['sets'] += 1
        yr = (dt or '')[:4]
        if yr:
            ye = e['byYear'].setdefault(yr, {'prize': 0, 'bonus': 0, 'sets': 0})
            ye['prize'] += pz
            ye['bonus'] += bn
            ye['sets'] += 1
    return out, prize


# ── 겉보기가 같은데 글자 코드만 다른 것을 맞춥니다 ─────────────────
#
# .strip() 은 보통 공백만 지웁니다. 그런데 구글시트에 손으로 넣거나 붙여넣은
# 이름에는 이런 것이 섞입니다.
#   · 한글 자모 분리(NFD) — '김'이 'ㄱ+ㅣ+ㅁ' 으로 들어간 것. 맥에서 붙여넣으면 흔합니다.
#   · 줄바꿈 없는 공백(U+00A0), 제로폭 공백(U+200B) 같은 안 보이는 글자
#
# 화면에서는 똑같아 보이는데 문자열 비교만 어긋나므로, 같은 날 같은 두 선수의
# 9세트가 8세트 + 1세트처럼 둘로 갈라져 보입니다.
# (2026-09-18 김정우 vs 변현제가 5-3 과 0-1 로 쪼개졌던 것이 이 경우입니다.)
# 그래서 이름·날짜·맵을 쓰기 전에 여기서 한 번에 정리합니다.
_INVISIBLE = re.compile(r'[\u200b-\u200f\u2028\u2029\ufeff\u00ad]')
_SPACES = re.compile(r'[\s\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]+')


def _clean(s):
    """겉보기가 같은 글자는 같아지도록 다듬습니다. 보이는 내용은 바뀌지 않습니다."""
    s = unicodedata.normalize('NFC', s or '')   # 분리된 한글 자모를 한 글자로
    s = _INVISIBLE.sub('', s)                   # 안 보이는 글자는 지웁니다
    return _SPACES.sub(' ', s).strip()          # 어떤 공백이든 보통 공백 하나로


def _oddchars(raw):
    """무엇 때문에 어긋났는지 사람이 알아볼 수 있게 적어 줍니다."""
    why = []
    if unicodedata.normalize('NFC', raw) != raw:
        why.append('한글 자모 분리')
    codes = sorted({'U+%04X' % ord(ch) for ch in raw
                    if ch != ' ' and (unicodedata.category(ch) in ('Cf', 'Zs', 'Cc')
                                      or ch in '\u00a0\u200b')})
    if codes:
        why.append('안 보이는 글자 ' + ', '.join(codes))
    if raw != raw.strip():
        why.append('앞뒤 공백')
    return ' · '.join(why) or '보이지 않는 차이'


# 시트에 잘못 적힌 선수 이름을 바로잡습니다 (왼쪽 → 오른쪽).
#
# 한 글자만 틀려도 다른 사람이 됩니다. 경기가 둘로 갈라지고 선수 목록에 유령이
# 하나 생깁니다. 2026-09-18 에 '변헌제'(헌)로 한 줄이 들어가, 김정우와의 9세트가
# 8세트 + 1세트로 쪼개지고 선수가 31명 → 32명이 됐습니다.
#
# ⚠ 원본 시트를 고치는 것이 먼저입니다. 여기는 시트가 고쳐지기 전까지의 임시
#   처치입니다. 시트를 고친 뒤에는 줄을 지워도 되고, 남겨 둬도 해롭지 않습니다.
PLAYER_ALIASES = {
    '변헌제': '변현제',
}


def _player(name):
    """선수 이름을 어디서나 같은 규칙으로 다듬습니다 — 세트도 상금도 이것만 씁니다.

    겉보기를 맞추고(_clean), 알려진 오타는 바로잡습니다(PLAYER_ALIASES).
    두 곳이 다른 규칙을 쓰면 상금이 선수를 못 찾고 사라집니다.
    """
    n = _clean(name)
    return PLAYER_ALIASES.get(n, n)


def _edit1(a, b):
    """두 이름이 딱 한 글자만 다른가 (오타 의심)."""
    if a == b:
        return False
    if len(a) == len(b):
        return sum(1 for x, y in zip(a, b) if x != y) == 1
    if len(a) > len(b):
        a, b = b, a
    if len(b) - len(a) != 1:
        return False
    return any(a == b[:i] + b[i + 1:] for i in range(len(b)))


def show_name_warnings(sets):
    """오타로 한 선수가 둘로 갈라진 흔적을 찾아 알려 줍니다.

    '한 글자만 다르다'만으로는 못 거릅니다 — 이영호·이영웅·이영한·이재호처럼
    진짜로 비슷한 이름이 수두룩해서 매번 헛경고가 납니다. 그래서 오타일 때만
    나타나는 세 가지가 동시에 맞을 때만 말합니다.

      · 같은 날짜에 둘 다 나온다        (오타는 그날 입력하다 납니다)
      · 그날 같은 상대와 붙었다          (같은 경기를 치던 중이라는 뜻)
      · 한쪽은 3세트 이하로 거의 없다     (한두 줄만 잘못 적힌 모양)

    자동으로 합치지는 않습니다. 진짜 다른 선수일 수도 있으니 사람이 보고
    PLAYER_ALIASES 에 넣거나 시트를 고치게 알리기만 합니다.
    """
    byday = {}
    for dt, w, _wr, lo, _lr, _mp in sets:
        d = byday.setdefault(dt, {})
        d.setdefault(w, {})[lo] = d.setdefault(w, {}).get(lo, 0) + 1
        d.setdefault(lo, {})[w] = d.setdefault(lo, {}).get(w, 0) + 1

    said = False
    for dt in sorted(byday):
        names = sorted(byday[dt])
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if not _edit1(a, b):
                    continue
                fa, fb = byday[dt][a], byday[dt][b]
                if not (set(fa) & set(fb)):
                    continue                      # 그날 같은 상대와 안 붙었으면 넘어갑니다
                na, nb = sum(fa.values()), sum(fb.values())
                few, many = (a, b) if na <= nb else (b, a)
                if min(na, nb) > 3:
                    continue                      # 둘 다 넉넉히 뛰었으면 진짜 다른 선수
                if not said:
                    print('  ⚠ 오타로 한 선수가 둘로 갈라진 것 같습니다 — 시트를 확인해 주세요:')
                    said = True
                print('      %s  %s (%d세트)  ↔  %s (%d세트)  · 같은 상대: %s'
                      % (dt, few, min(na, nb), many, max(na, nb),
                         ', '.join(sorted(set(fa) & set(fb)))))
    if said:
        print('      시트를 고치시거나, tools/endgame_import.py 의 PLAYER_ALIASES 에 넣으면 됩니다.')
    return said


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

      0. 겉보기가 같은데 글자 코드만 다른 이름·날짜 → 같게 맞춤 (자모 분리·안 보이는 공백)
      1. 선수 종족이 줄마다 다르게 적힌 경우 → 가장 많이 적힌 종족으로
      2. 맵 이름이 대소문자·띄어쓰기만 다른 경우 → 가장 많이 쓰인 표기로
      3. MAP_ALIASES 에 적어 둔 맵 이름 → 정해 둔 표기로
    """
    # 0. 겉보기가 같은데 글자 코드만 다른 이름·날짜·맵을 먼저 맞춥니다.
    #    이걸 먼저 해야 아래 종족·맵 집계와 경기 묶기가 같은 사람을 같게 봅니다.
    fixes = []
    cleaned = []
    for dt, w, wr, lo, lr, mp in sets:
        cdt, cw, clo, cmp = _clean(dt), _clean(w), _clean(lo), _clean(mp)
        for raw, fixed, what in ((w, cw, '선수 이름'), (lo, clo, '선수 이름'),
                                 (dt, cdt, '날짜'), (mp, cmp, '맵 이름')):
            if fixed != raw:
                fixes.append('%-10s  %s %s 을(를) 맞췄습니다 — %s'
                             % (cdt, what, fixed or '(빈칸)', _oddchars(raw)))
        # 위에 적어 둔 이름 오타를 바로잡습니다 (PLAYER_ALIASES 설명 참고).
        for who in ('w', 'lo'):
            cur = cw if who == 'w' else clo
            alias = PLAYER_ALIASES.get(cur)
            if alias:
                fixes.append('%-10s  선수 이름 %s → %s' % (cdt, cur, alias))
                if who == 'w':
                    cw = alias
                else:
                    clo = alias
        cleaned.append((cdt, cw, _clean(wr), clo, _clean(lr), cmp))
    sets = cleaned

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
    sets, _prizes = fetch_sets(*load_source())
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


def build_players(matches, setlist, prizes):
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
        pz = prizes.get(p['name'], {})
        p['prize'] = pz.get('prize', 0)          # 기본 상금 합 (원)
        p['prizeBonus'] = pz.get('bonus', 0)     # 더블찬스 합 (원)
        p['prizeTotal'] = p['prize'] + p['prizeBonus']
        p['prizeSets'] = pz.get('sets', 0)       # 상금을 받은(이긴) 세트 수
        p['prizeYearly'] = {yr: {'prize': ye['prize'], 'bonus': ye['bonus'],
                                 'total': ye['prize'] + ye['bonus'], 'sets': ye['sets']}
                            for yr, ye in (pz.get('byYear') or {}).items()}
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


def build_doc(sets, built_at, prizes=None):
    matches, setlist = group_matches(sets)
    players = build_players(matches, setlist, prizes or {})
    maps = build_maps(matches, setlist)
    dates = sorted(m['date'] for m in matches)
    return {
        'builtAt': built_at,
        'global': {
            'totalSets': len(sets),
            'totalMatches': len(matches),
            'totalPlayers': len(players),
            'totalPrize': sum(p.get('prizeTotal', 0) for p in players),
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
    raw_sets, prizes = fetch_sets(sheet_id, sheet_name)
    sets, fixes = normalize_sets(raw_sets)
    print('  세트 %d줄을 읽었습니다.' % len(sets))
    show_fixes(fixes)
    show_name_warnings(sets)

    old = None
    if os.path.exists(TARGET):
        try:
            old = json.load(io.open(TARGET, encoding='utf-8'))
        except ValueError:
            old = None
    built_at = (old or {}).get('builtAt') or ''
    doc = build_doc(sets, built_at, prizes)
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
