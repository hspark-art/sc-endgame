# -*- coding: utf-8 -*-
"""data/endgame.json 원본에서 사이트가 쓰는 파생 통계를 계산합니다.

원본 수치(선수 전적·맵 전적)는 그대로 두고, 여기서는 원본에서 다시 계산할 수
있는 것만 만듭니다. 세트별 승자는 원본에 없으므로(시트 집계 단계에서 합산됨)
세트 단위 종족 상성은 '매치 스코어 + 두 선수의 종족'으로 재구성합니다.
"""

from collections import defaultdict, Counter

RACES = ['T', 'P', 'Z']
RACE_LABEL = {'T': '테란', 'P': '프로토스', 'Z': '저그'}
# 상성 표기 순서 — 앞에 적힌 종족 기준 승/패
MATCHUPS = [('P', 'T'), ('T', 'Z'), ('P', 'Z')]


def _mu_key(r1, r2):
    """두 종족 → 상성 키. 같은 종족(동족전)이면 None."""
    if r1 == r2:
        return None
    for a, b in MATCHUPS:
        if {r1, r2} == {a, b}:
            return a + 'v' + b
    return None


def chronological(matches):
    """원본은 최신순입니다. 날짜 오름차순으로 다시 정렬해 돌려줍니다."""
    return sorted(matches, key=lambda m: (m['date'], m['players'][0]))


def match_key(m):
    """영상 매핑·CSV 에서 경기를 식별하는 키."""
    return m['date'] + '|' + '|'.join(sorted(m['players']))


def blank_mu():
    return {a + 'v' + b: {'w': 0, 'l': 0} for a, b in MATCHUPS}


def add_match_to_mu(mu, m):
    """매치 하나의 세트 스코어를 상성 집계에 더합니다."""
    a, b = m['players']
    ra, rb = m['race'][a], m['race'][b]
    key = _mu_key(ra, rb)
    if not key:
        return
    front = key[0]                      # 키 앞에 적힌 종족
    wa, wb = m['setWins'][a], m['setWins'][b]
    if ra == front:
        mu[key]['w'] += wa
        mu[key]['l'] += wb
    else:
        mu[key]['w'] += wb
        mu[key]['l'] += wa


def yearly(matches):
    """연도별 요약: 매치·세트 수, 출전 선수, 세트 단위 종족 상성, 최다승 선수."""
    buckets = defaultdict(lambda: {
        'matches': 0, 'sets': 0, 'players': set(),
        'mu': blank_mu(), 'win': Counter(), 'loss': Counter(),
        'setW': Counter(), 'setL': Counter(),
    })
    for m in matches:
        y = m['date'][:4]
        a, b = m['players']
        bk = buckets[y]
        bk['matches'] += 1
        bk['sets'] += m['setWins'][a] + m['setWins'][b]
        bk['players'].update([a, b])
        add_match_to_mu(bk['mu'], m)
        loser = b if m['winner'] == a else a
        bk['win'][m['winner']] += 1
        bk['loss'][loser] += 1
        bk['setW'][a] += m['setWins'][a]
        bk['setL'][a] += m['setWins'][b]
        bk['setW'][b] += m['setWins'][b]
        bk['setL'][b] += m['setWins'][a]

    out = []
    for y in sorted(buckets, reverse=True):
        bk = buckets[y]
        top = bk['win'].most_common(1)
        out.append({
            'year': y,
            'matches': bk['matches'],
            'sets': bk['sets'],
            'players': len(bk['players']),
            'mu': bk['mu'],
            'topPlayer': top[0][0] if top else None,
            'topWins': top[0][1] if top else 0,
            'topLosses': bk['loss'][top[0][0]] if top else 0,
        })
    return out


def player_yearly(matches, names):
    """선수 → 연도 → 매치/세트 전적."""
    out = {n: {} for n in names}
    for m in matches:
        y = m['date'][:4]
        a, b = m['players']
        for me, opp in ((a, b), (b, a)):
            row = out.setdefault(me, {}).setdefault(
                y, {'matchWin': 0, 'matchLoss': 0, 'setWin': 0, 'setLoss': 0,
                    'apps': 0, 'firstDate': m['date'], 'lastDate': m['date']})
            row['apps'] += 1
            row['firstDate'] = min(row['firstDate'], m['date'])
            row['lastDate'] = max(row['lastDate'], m['date'])
            row['setWin'] += m['setWins'][me]
            row['setLoss'] += m['setWins'][opp]
            if m['winner'] == me:
                row['matchWin'] += 1
            else:
                row['matchLoss'] += 1
    return out


def streaks(matches, names):
    """매치 단위 최다 연승·최다 연패, 그리고 마지막 시점의 진행 중인 연속 기록."""
    order = chronological(matches)
    seq = defaultdict(list)
    for m in order:
        for p in m['players']:
            seq[p].append(1 if m['winner'] == p else 0)

    out = {}
    for n in names:
        s = seq.get(n, [])
        best_w = best_l = cur_w = cur_l = 0
        for r in s:
            if r:
                cur_w += 1
                cur_l = 0
            else:
                cur_l += 1
                cur_w = 0
            best_w = max(best_w, cur_w)
            best_l = max(best_l, cur_l)
        out[n] = {
            'bestWin': best_w,
            'bestLoss': best_l,
            'current': cur_w if cur_w else -cur_l,   # 양수=연승, 음수=연패
        }
    return out


def map_yearly(matches):
    """맵 → 연도 → 그 해에 쓰인 세트 수."""
    out = defaultdict(Counter)
    for m in matches:
        y = m['date'][:4]
        for name in m['maps']:
            if name:
                out[name][y] += 1
    return {k: dict(v) for k, v in out.items()}


def rivalries(players, limit=None):
    """맞대결이 많은 순서의 라이벌 목록 (중복 없이 한 쌍당 한 줄, 앞 선수 기준 전적)."""
    seen, rows = set(), []
    race_of = {p['name']: p['race'] for p in players}
    for p in players:
        for o in p['vsPlayers']:
            if o['name'] not in race_of:
                continue
            pair = tuple(sorted([p['name'], o['name']]))
            if pair in seen:
                continue
            seen.add(pair)
            a, b = pair
            flip = p['name'] != a          # o 는 p 기준 기록이므로 a 기준으로 뒤집습니다
            setW, setL = (o['l'], o['w']) if flip else (o['w'], o['l'])
            pw = sum(1 for x in o['matches'] if x['result'] == '승')
            matchW = len(o['matches']) - pw if flip else pw
            rows.append({
                'a': a, 'aRace': race_of[a],
                'b': b, 'bRace': race_of[b],
                'setW': setW, 'setL': setL,
                'matches': len(o['matches']),
                'matchW': matchW, 'matchL': len(o['matches']) - matchW,
            })
    rows.sort(key=lambda r: (-r['matches'], -(r['setW'] + r['setL']), r['a']))
    return rows[:limit] if limit else rows


def _pct(w, l):
    t = w + l
    return (w / t * 100) if t else 0.0


def records(data, sk, strk):
    """기록실 탭에 쓰는 순위 모음. 각 항목은 [{name, race, value, detail}] 형태."""
    players = data['players']
    matches = data['matches']

    def top(rows, n=10):
        return rows[:n]

    def prow(p, value, label, detail):
        # label 은 화면에 그대로 찍는 문자열입니다. 자바스크립트에서 다시 포맷하면
        # 54.0 이 '54' 로 줄어드는 식으로 어긋나므로 여기서 확정합니다.
        return {'name': p['name'], 'race': p['race'], 'slug': sk[p['name']],
                'value': value, 'label': label, 'detail': detail}

    apps = top(sorted(
        (prow(p, p['appearances'], '%d경기' % p['appearances'],
              '%s ~ %s' % (p['firstDate'][:4], p['lastDate'][:4]))
         for p in players), key=lambda r: -r['value']))

    match_win = top(sorted(
        (prow(p, p['matchWin'], '%d승' % p['matchWin'],
              '%d승 %d패 · %.1f%%' % (p['matchWin'], p['matchLoss'],
                                    _pct(p['matchWin'], p['matchLoss'])))
         for p in players), key=lambda r: -r['value']))

    MIN_M = 15
    match_pct = top(sorted(
        (prow(p, _pct(p['matchWin'], p['matchLoss']),
              '%.1f%%' % _pct(p['matchWin'], p['matchLoss']),
              '%d승 %d패' % (p['matchWin'], p['matchLoss']))
         for p in players if p['matchWin'] + p['matchLoss'] >= MIN_M),
        key=lambda r: -r['value']))

    set_win = top(sorted(
        (prow(p, p['setWin'], '%d승' % p['setWin'],
              '%d승 %d패 · %.1f%%' % (p['setWin'], p['setLoss'],
                                    _pct(p['setWin'], p['setLoss'])))
         for p in players), key=lambda r: -r['value']))

    MIN_S = 100
    set_pct = top(sorted(
        (prow(p, _pct(p['setWin'], p['setLoss']),
              '%.1f%%' % _pct(p['setWin'], p['setLoss']),
              '%d승 %d패' % (p['setWin'], p['setLoss']))
         for p in players if p['setWin'] + p['setLoss'] >= MIN_S),
        key=lambda r: -r['value']))

    win_streak = top(sorted(
        (prow(p, strk[p['name']]['bestWin'], '%d연승' % strk[p['name']]['bestWin'],
              '통산 %d경기 출전' % p['appearances'])
         for p in players), key=lambda r: -r['value']))

    # 끝장전은 사실상 9세트 고정이라 '최장 매치'는 기록이 되지 않습니다.
    # 대신 마지막 세트까지 간 5-4 접전을 얼마나 많이 치렀는지를 봅니다.
    thrill_w, thrill_l = Counter(), Counter()
    for m in matches:
        a, b = m['players']
        if sorted([m['setWins'][a], m['setWins'][b]]) != [4, 5]:
            continue
        loser = b if m['winner'] == a else a
        thrill_w[m['winner']] += 1
        thrill_l[loser] += 1
    thriller = top(sorted(
        (prow(p, thrill_w[p['name']] + thrill_l[p['name']],
              '%d경기' % (thrill_w[p['name']] + thrill_l[p['name']]),
              '%d승 %d패' % (thrill_w[p['name']], thrill_l[p['name']]))
         for p in players), key=lambda r: -r['value']))

    # 활동 기간이 같으면 출전이 많은 선수를 위로 올립니다.
    span_src = sorted(players,
                      key=lambda x: (-(int(x['lastDate'][:4]) - int(x['firstDate'][:4])),
                                     -x['appearances'], x['name']))
    span = top([
        prow(x, int(x['lastDate'][:4]) - int(x['firstDate'][:4]),
             '%d년' % (int(x['lastDate'][:4]) - int(x['firstDate'][:4])),
             '%s ~ %s · %d경기' % (x['firstDate'][:4], x['lastDate'][:4],
                                 x['appearances']))
        for x in span_src])

    sweeps = []
    for m in matches:
        a, b = m['players']
        gap = abs(m['setWins'][a] - m['setWins'][b])
        sweeps.append((gap, m))
    sweeps.sort(key=lambda t: (-t[0], t[1]['date']))
    sweep_rows = []
    for gap, m in sweeps[:10]:
        a, b = m['players']
        win, lose = (a, b) if m['winner'] == a else (b, a)
        sweep_rows.append({
            'date': m['date'], 'a': win, 'b': lose,
            'aRace': m['race'][win], 'bRace': m['race'][lose],
            'aSlug': sk.get(win, ''), 'bSlug': sk.get(lose, ''),
            'score': '%d-%d' % (m['setWins'][win], m['setWins'][lose]),
            'value': gap,
        })

    top_maps = top(sorted(
        ({'name': m['name'], 'value': m['totalSets'], 'label': '%d세트' % m['totalSets'],
          'detail': '%s ~ %s · %d일' % (m['firstDate'][:7], m['lastDate'][:7],
                                       m['daysUsed'])}
         for m in data['maps']), key=lambda r: -r['value']))

    return {
        'apps': apps, 'matchWin': match_win, 'matchPct': match_pct,
        'setWin': set_win, 'setPct': set_pct, 'winStreak': win_streak,
        'thriller': thriller, 'span': span, 'sweep': sweep_rows,
        'topMaps': top_maps, 'minMatch': MIN_M, 'minSet': MIN_S,
    }


def global_matchups(matches):
    mu = blank_mu()
    for m in matches:
        add_match_to_mu(mu, m)
    return mu
