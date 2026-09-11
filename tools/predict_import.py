#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""중계진 예측(캐스터 승부예측) 시트 → data/predict.json.

같은 끝장전 시트의 '중계진 예측 현황입력용' 탭(gid=99072594)을 읽습니다.
한 줄 = 한 세트에 대한 한 캐스터의 예측입니다.
  0 날짜 · 1 선수1 · 2 선수2 · 3 세트(SET n) · 4 맵 · 5 갯수 ·
  6 중계진(캐스터) · 7 선택(찍은 선수) · 8 성공/실패
오른쪽 블록(10~16열)에는 시트가 계산한 캐스터 순위(전체/승/승률/지수/수익률)가
있어, 지수·수익률만 거기서 가져오고 적중률은 원본 로그로 다시 계산합니다.

python3 tools/predict_import.py            # 미리보기
python3 tools/predict_import.py --write    # data/predict.json 에 기록
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass

SOURCE = os.path.join(ROOT, 'data', 'endgame-source.json')
TARGET = os.path.join(ROOT, 'data', 'predict.json')
GID = '99072594'          # '중계진 예측 현황입력용' 탭
RACE_LABEL = {'T': '테란', 'P': '프로토스', 'Z': '저그'}


def _num(s):
    """'+13,709' → 13709, '-9.4%' → -9.4 (숫자·부호만)."""
    s = str(s).strip().replace(',', '').replace('%', '')
    m = re.match(r'^[+-]?\d+(\.\d+)?$', s)
    return float(s) if m else None


def _race(name):
    """'박상현(Z)' → ('박상현','Z')."""
    m = re.match(r'^(.*?)\s*\(([TPZ])\)\s*$', name.strip())
    if m:
        return m.group(1).strip(), m.group(2)
    return name.strip(), ''


def _mu_key(r1, r2):
    """두 종족을 정해진 순서의 상성 키로. 같은 종족이면 None."""
    if not r1 or not r2 or r1 == r2:
        return None
    for a, b in (('P', 'T'), ('T', 'Z'), ('P', 'Z')):
        if {r1, r2} == {a, b}:
            return a + 'v' + b
    return None


def fetch_rows(sheet_id):
    url = ('https://docs.google.com/spreadsheets/d/%s/gviz/tq?tqx=out:csv&gid=%s'
           % (sheet_id, GID))
    import sheetbackup
    raw, _ = sheetbackup.fetch_csv(url, 'predict')
    return list(csv.reader(io.StringIO(raw)))


def build(rows):
    casters = {}      # 캐스터 → [total, correct]
    by_set = {}       # 세트번호 → [total, correct]
    by_player = {}    # 선수 → {'race','total','miss'}
    by_mu = {}        # 상성키 → [total, correct]
    rank = {}         # 오른쪽 블록에서 가져온 지수·수익률 (이름 → {index, roi, sheetPct})
    total = correct = 0

    for r in rows[1:]:
        if len(r) < 9:
            r = r + [''] * (9 - len(r))
        # ── 오른쪽 순위 블록(지수·수익률) ──
        if len(r) > 16 and re.match(r'^\d+$', (r[10] or '').strip()) and (r[11] or '').strip():
            rank[(r[11] or '').strip()] = {
                'index': _num(r[15]), 'roi': _num(r[16]), 'sheetPct': _num(r[14]),
            }
        # ── 예측 로그(왼쪽) ──
        caster = (r[6] or '').strip()
        res = (r[8] or '').strip()
        p1, p2 = (r[1] or '').strip(), (r[2] or '').strip()
        if not caster or res not in ('성공', '실패') or not p1 or not p2:
            continue
        ok = res == '성공'
        total += 1
        correct += ok

        c = casters.setdefault(caster, [0, 0])
        c[0] += 1
        c[1] += ok

        sm = re.search(r'(\d+)', r[3] or '')
        if sm:
            st = int(sm.group(1))
            s = by_set.setdefault(st, [0, 0])
            s[0] += 1
            s[1] += ok

        # 이변 제조기 — 이 세트에 걸린 두 선수 모두에 '빗나감'을 계상
        for nm in (p1, p2):
            name, race = _race(nm)
            e = by_player.setdefault(name, {'race': race, 'total': 0, 'miss': 0})
            if race and not e['race']:
                e['race'] = race
            e['total'] += 1
            e['miss'] += (not ok)

        # 종족별(상성) 예측 적중률
        _, ra = _race(p1)
        _, rb = _race(p2)
        key = _mu_key(ra, rb)
        if key:
            mm = by_mu.setdefault(key, [0, 0])
            mm[0] += 1
            mm[1] += ok

    def pct(a, b):
        return round(a / b * 100, 1) if b else 0.0

    def short(nm):
        # '박상현 캐스터'/'임성춘 해설' → 순위 블록의 '박상현'/'임성춘' 로 맞춤
        return nm.split()[0] if nm.split() else nm

    caster_rows = []
    for nm, (t, ok) in casters.items():
        rk = rank.get(short(nm), {})
        caster_rows.append({
            'name': nm, 'total': t, 'correct': ok, 'pct': pct(ok, t),
            'index': rk.get('index'), 'roi': rk.get('roi'),
        })
    caster_rows.sort(key=lambda x: -x['pct'])

    set_rows = [{'set': k, 'total': v[0], 'correct': v[1], 'pct': pct(v[1], v[0])}
                for k, v in sorted(by_set.items())]

    player_rows = [{'name': n, 'race': e['race'], 'total': e['total'],
                    'miss': e['miss'], 'missPct': pct(e['miss'], e['total'])}
                   for n, e in by_player.items() if e['total'] >= 12]
    player_rows.sort(key=lambda x: (-x['missPct'], -x['total']))

    mu_rows = []
    for key, (t, ok) in by_mu.items():
        a, b = key[0], key[2]
        mu_rows.append({'key': key,
                        'label': '%s vs %s' % (RACE_LABEL[a], RACE_LABEL[b]),
                        'total': t, 'correct': ok, 'pct': pct(ok, t)})
    mu_rows.sort(key=lambda x: -x['pct'])

    return {
        'totalPredictions': total,
        'overallPct': pct(correct, total),
        'casters': caster_rows,
        'bySet': set_rows,
        'byPlayer': player_rows,
        'byMatchup': mu_rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()

    if not os.path.exists(SOURCE):
        raise SystemExit('data/endgame-source.json 이 없습니다.')
    sheet_id = json.load(io.open(SOURCE, encoding='utf-8'))['sheetId']
    print('중계진 예측 탭에서 받아옵니다…')
    doc = build(fetch_rows(sheet_id))
    print('  예측 %d건 · 전체 적중률 %.1f%%' % (doc['totalPredictions'], doc['overallPct']))
    for c in doc['casters']:
        print('    %-12s %d/%d = %.1f%%%s' % (
            c['name'], c['correct'], c['total'], c['pct'],
            ('  지수 %+d · 수익률 %+.1f%%' % (c['index'], c['roi']))
            if c['index'] is not None else ''))

    if not args.write:
        print('실제로 기록하려면 --write 를 붙여 주세요.')
        return 0
    # 기존 것보다 예측 수가 확 줄면(시트 사고) 멈춥니다.
    old = {}
    if os.path.exists(TARGET):
        try:
            old = json.load(io.open(TARGET, encoding='utf-8'))
        except ValueError:
            old = {}
    if old.get('totalPredictions', 0) > doc['totalPredictions'] + 5:
        print('예측 수가 %d → %d 로 줄어 멈췄습니다(시트 확인 필요).'
              % (old['totalPredictions'], doc['totalPredictions']))
        return 1
    io.open(TARGET, 'w', encoding='utf-8').write(
        json.dumps(doc, ensure_ascii=False, indent=1) + chr(10))
    print('data/predict.json 에 기록했습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
