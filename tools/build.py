#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""끝장전 기록실 사이트를 통째로 다시 만듭니다.

    python3 tools/build.py

입력   data/endgame.json  (정본 기록)
       data/videos.json   (경기 → 다시보기 영상 매핑)
출력   index.html, p/*.html, sheets.html, csv/*, xlsx/*

원본 수치는 손대지 않습니다. 여기서 만드는 값은 전부 원본에서 다시 계산한 것이라
언제 몇 번을 돌려도 같은 결과가 나옵니다.
"""

import csv
import io
import json
import os
import sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import render                                    # noqa: E402
import stats                                     # noqa: E402
from slug import unique_slugs                    # noqa: E402

KST = timezone(timedelta(hours=9))


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with io.open(path, encoding='utf-8') as f:
        return json.load(f)


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with io.open(full, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    return len(text.encode('utf-8'))


def write_csv(name, header, rows):
    """구글 시트·엑셀 양쪽에서 한글이 깨지지 않도록 BOM 을 붙여 저장합니다."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(header)
    w.writerows(rows)
    full = os.path.join(ROOT, 'csv', name)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with io.open(full, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(buf.getvalue())
    return len(rows)


def pct_val(w, l):
    t = w + l
    return round(w / t * 100, 1) if t else ''


# ── 데이터 읽기 ────────────────────────────────────────────────
def load():
    data = read_json(os.path.join(ROOT, 'data', 'endgame.json'))
    if not data:
        raise SystemExit('data/endgame.json 이 없습니다.')
    videos = read_json(os.path.join(ROOT, 'data', 'videos.json'), {}) or {}
    vmap = videos.get('matches') or {}

    matched = 0
    for m in data['matches']:
        url = vmap.get(stats.match_key(m))
        m['youtubeUrl'] = url or None
        if url:
            matched += 1
    return data, matched


# ── 파생 통계 ──────────────────────────────────────────────────
def enrich(data):
    players = data['players']
    matches = data['matches']
    names = [p['name'] for p in players]

    slugs = unique_slugs(names)
    race_of = {p['name']: p['race'] for p in players}
    strk = stats.streaks(matches, names)
    p_year = stats.player_yearly(matches, names)
    m_year = stats.map_yearly(matches)
    yearly = stats.yearly(matches)
    years = [y['year'] for y in yearly]

    for p in players:
        p['slug'] = slugs[p['name']]
        p['streak'] = strk[p['name']]
        p['yearly'] = p_year.get(p['name'], {})
    for mp in data['maps']:
        mp['yearly'] = m_year.get(mp['name'], {})

    ctx = {
        'slugs': slugs, 'raceOf': race_of, 'streaks': strk,
        'playerYearly': p_year, 'years': years, 'yearly': yearly,
        'matches': matches, 'players': players,
        'mu': stats.global_matchups(matches),
        'records': stats.records(data, slugs, strk),
        'rivalries': stats.rivalries(players, 15),
        'mapCoveredSets': sum(mp['totalSets'] for mp in data['maps']),
    }
    return ctx


# ── 허브가 쓰는 데이터 (상대 전적 상세는 선수 페이지에만) ────────
def hub_data(data, ctx, built_at):
    players = [{
        'name': p['name'], 'slug': p['slug'], 'race': p['race'],
        'matchWin': p['matchWin'], 'matchLoss': p['matchLoss'],
        'setWin': p['setWin'], 'setLoss': p['setLoss'],
        'appearances': p['appearances'],
        'firstDate': p['firstDate'], 'lastDate': p['lastDate'],
        'streak': p['streak'], 'yearly': p['yearly'],
    } for p in data['players']]

    maps = [{
        'name': m['name'], 'totalSets': m['totalSets'], 'daysUsed': m['daysUsed'],
        'firstDate': m['firstDate'], 'lastDate': m['lastDate'],
        'matchup': m['matchup'], 'yearly': m['yearly'],
    } for m in data['maps']]

    return {
        'builtAt': built_at,
        'global': data['global'],
        'years': ctx['years'],
        'yearly': ctx['yearly'],
        'mu': ctx['mu'],
        'records': ctx['records'],
        'rivalries': ctx['rivalries'],
        'mapCoveredSets': ctx['mapCoveredSets'],
        'slugs': ctx['slugs'],
        'raceOf': ctx['raceOf'],
        'players': players,
        'maps': maps,
        'matches': data['matches'],
    }


# ── CSV ────────────────────────────────────────────────────────
CSV_SPEC = [
    ('players.csv', '선수', '선수별 통산 전적과 종족별 세트 전적'),
    ('matches.csv', '경기', '매치 한 줄씩 — 날짜·대진·스코어·맵·다시보기'),
    ('sets.csv', '세트별 맵', '매치 안의 세트마다 어떤 맵을 썼는지'),
    ('maps.csv', '맵', '맵별 사용 세트 수와 종족 상성'),
    ('headtohead.csv', '상대전적', '선수 대 선수 맞대결 기록'),
    ('yearly.csv', '연도별', '연도별 매치·세트 수와 종족 상성'),
]


def build_csv(data, ctx):
    counts = {}

    rows = []
    for p in sorted(data['players'], key=lambda x: (-x['matchWin'], x['name'])):
        v = p['vsRace']
        rows.append([
            p['name'], p['slug'], render.RACE_LABEL[p['race']], p['race'],
            p['matchWin'], p['matchLoss'], pct_val(p['matchWin'], p['matchLoss']),
            p['setWin'], p['setLoss'], pct_val(p['setWin'], p['setLoss']),
            p['appearances'], p['firstDate'], p['lastDate'],
            p['streak']['bestWin'], p['streak']['bestLoss'],
            v['T']['w'], v['T']['l'], v['P']['w'], v['P']['l'], v['Z']['w'], v['Z']['l'],
        ])
    counts['players.csv'] = write_csv('players.csv', [
        '선수', '슬러그', '종족', '종족코드', '매치승', '매치패', '매치승률',
        '세트승', '세트패', '세트승률', '출전', '첫출전', '최근출전',
        '최다연승', '최다연패',
        'vs테란_세트승', 'vs테란_세트패', 'vs프로토스_세트승', 'vs프로토스_세트패',
        'vs저그_세트승', 'vs저그_세트패',
    ], rows)

    rows, set_rows = [], []
    for m in data['matches']:
        a, b = m['players']
        maps = [x for x in (m.get('maps') or [])]
        rows.append([
            m['date'], a, m['race'][a], b, m['race'][b],
            m['setWins'][a], m['setWins'][b], m['winner'],
            m['setWins'][a] + m['setWins'][b],
            ' | '.join(x for x in maps if x), m.get('youtubeUrl') or '',
        ])
        for i, name in enumerate(maps, 1):
            set_rows.append([m['date'], a, b, i, name])
    counts['matches.csv'] = write_csv('matches.csv', [
        '날짜', '선수A', '종족A', '선수B', '종족B', '세트A', '세트B', '승자',
        '총세트', '맵목록', '다시보기',
    ], rows)
    counts['sets.csv'] = write_csv('sets.csv',
                                   ['날짜', '선수A', '선수B', '세트번호', '맵'], set_rows)

    rows = []
    for m in sorted(data['maps'], key=lambda x: -x['totalSets']):
        zp, tz, pt = m['matchup']['Z-P'], m['matchup']['T-Z'], m['matchup']['P-T']
        br = m['byRace']
        rows.append([
            m['name'], m['totalSets'], m['daysUsed'], m['firstDate'], m['lastDate'],
            zp['w'], zp['l'], pct_val(zp['w'], zp['l']),
            tz['w'], tz['l'], pct_val(tz['w'], tz['l']),
            pt['w'], pt['l'], pct_val(pt['w'], pt['l']),
            br['T']['w'], br['T']['l'], br['P']['w'], br['P']['l'],
            br['Z']['w'], br['Z']['l'],
        ] + [m['yearly'].get(y, 0) for y in ctx['years'][::-1]])
    counts['maps.csv'] = write_csv('maps.csv', [
        '맵', '총세트', '사용일수', '첫사용', '마지막사용',
        '저그승_vs프로토스', '저그패_vs프로토스', '저그승률_vs프로토스',
        '테란승_vs저그', '테란패_vs저그', '테란승률_vs저그',
        '프로토스승_vs테란', '프로토스패_vs테란', '프로토스승률_vs테란',
        '테란_세트승', '테란_세트패', '프로토스_세트승', '프로토스_세트패',
        '저그_세트승', '저그_세트패',
    ] + ['%s년_세트' % y for y in ctx['years'][::-1]], rows)

    rows = []
    for r in stats.rivalries(data['players']):
        rows.append([
            r['a'], render.RACE_LABEL[r['aRace']], r['b'], render.RACE_LABEL[r['bRace']],
            r['matches'], r['matchW'], r['matchL'],
            r['setW'], r['setL'], pct_val(r['setW'], r['setL']),
        ])
    counts['headtohead.csv'] = write_csv('headtohead.csv', [
        '선수A', '종족A', '선수B', '종족B', '맞대결수',
        'A매치승', 'A매치패', 'A세트승', 'A세트패', 'A세트승률',
    ], rows)

    rows = []
    for y in ctx['yearly']:
        mu = y['mu']
        rows.append([
            y['year'], y['matches'], y['sets'], y['players'],
            y['topPlayer'] or '', y['topWins'], y['topLosses'],
            mu['PvT']['w'], mu['PvT']['l'], pct_val(mu['PvT']['w'], mu['PvT']['l']),
            mu['TvZ']['w'], mu['TvZ']['l'], pct_val(mu['TvZ']['w'], mu['TvZ']['l']),
            mu['PvZ']['w'], mu['PvZ']['l'], pct_val(mu['PvZ']['w'], mu['PvZ']['l']),
        ])
    counts['yearly.csv'] = write_csv('yearly.csv', [
        '연도', '매치', '세트', '출전선수', '최다승선수', '최다승', '최다승선수패',
        '프로토스승_vs테란', '프로토스패_vs테란', '프로토스승률_vs테란',
        '테란승_vs저그', '테란패_vs저그', '테란승률_vs저그',
        '프로토스승_vs저그', '프로토스패_vs저그', '프로토스승률_vs저그',
    ], rows)
    return counts


def build_manifest(counts, built_at, built_ko):
    files = []
    for name, label, desc in CSV_SPEC:
        files.append({
            'label': label, 'desc': desc, 'file': name,
            'rows': counts.get(name, 0),
            'url': '%s/csv/%s' % (render.BASE_URL, name),
        })
    manifest = {
        'updatedAt': built_at,
        'updatedAtKo': built_ko,
        'base': render.BASE_URL,
        'xlsx': '%s/xlsx/sc-endgame.xlsx' % render.BASE_URL,
        'json': '%s/data/endgame.json' % render.BASE_URL,
        'files': files,
    }
    write('csv/index.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return manifest


# ── XLSX ───────────────────────────────────────────────────────
def build_xlsx():
    """CSV 여섯 개를 시트 여섯 장짜리 엑셀 한 파일로 묶습니다."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
    except ImportError:
        print('  ! openpyxl 이 없어 xlsx 는 건너뜁니다 (pip install openpyxl)')
        return None

    wb = Workbook()
    wb.remove(wb.active)
    head_font = Font(bold=True, color='FFFFFF', size=10)
    head_fill = PatternFill('solid', fgColor='1C8CFF')

    for name, label, _desc in CSV_SPEC:
        path = os.path.join(ROOT, 'csv', name)
        with io.open(path, encoding='utf-8-sig', newline='') as f:
            rows = list(csv.reader(f))
        ws = wb.create_sheet(label)
        for r in rows:
            ws.append([_num(c) for c in r])
        for cell in ws[1]:
            cell.font = head_font
            cell.fill = head_fill
            cell.alignment = Alignment(horizontal='center')
        ws.freeze_panes = 'A2'
        if rows:
            ws.auto_filter.ref = 'A1:%s%d' % (get_column_letter(len(rows[0])), len(rows))
            for i in range(1, len(rows[0]) + 1):
                col = get_column_letter(i)
                width = max((_disp_len(r[i - 1]) for r in rows[:200] if len(r) >= i),
                            default=8)
                ws.column_dimensions[col].width = min(max(width + 2, 8), 42)

    out = os.path.join(ROOT, 'xlsx', 'sc-endgame.xlsx')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    wb.save(out)
    return os.path.getsize(out)


def _num(s):
    """숫자로 보이는 칸은 숫자로 넣습니다 — 엑셀에서 정렬·합계가 되도록."""
    if s == '':
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return s


def _disp_len(s):
    """한글은 대략 두 칸을 차지합니다."""
    return sum(2 if ord(c) > 0x2E80 else 1 for c in str(s))


# ── 메인 ───────────────────────────────────────────────────────
def main():
    data, video_matched = load()
    ctx = enrich(data)

    now = datetime.now(timezone.utc)
    built_at = now.strftime('%Y-%m-%dT%H:%M:%S.') + '%03dZ' % (now.microsecond // 1000)
    built_ko = now.astimezone(KST).strftime('%Y년 %m월 %d일 %H:%M (KST)')
    ctx['builtAtKo'] = built_ko

    css = io.open(os.path.join(HERE, 'site.css'), encoding='utf-8').read()
    app_js = io.open(os.path.join(HERE, 'app.js'), encoding='utf-8').read()

    print('끝장전 기록실 빌드')
    print('  매치 %d · 세트 %s · 선수 %d · 맵 %d · 연도 %s'
          % (data['global']['totalMatches'], format(data['global']['totalSets'], ','),
             len(data['players']), len(data['maps']),
             ctx['years'][-1] + '~' + ctx['years'][0]))

    counts = build_csv(data, ctx)
    for name, _l, _d in CSV_SPEC:
        print('  csv/%-16s %5d행' % (name, counts[name]))

    size = build_xlsx()
    if size:
        print('  xlsx/sc-endgame.xlsx  %.0fKB' % (size / 1024))

    manifest = build_manifest(counts, built_at, built_ko)

    n = write('index.html', render.index_page(css, app_js, hub_data(data, ctx, built_at)))
    print('  index.html            %.0fKB' % (n / 1024))

    # 예전 파일이 남지 않도록 선수 페이지 폴더를 비우고 다시 만듭니다.
    pdir = os.path.join(ROOT, 'p')
    if os.path.isdir(pdir):
        for f in os.listdir(pdir):
            if f.endswith('.html'):
                os.remove(os.path.join(pdir, f))
    total = 0
    for p in data['players']:
        total += write('p/%s.html' % p['slug'], render.player_page(p, ctx, css))
    print('  p/*.html              %d개 · 합계 %.0fKB' % (len(data['players']), total / 1024))

    write('sheets.html', render.sheets_page(css, manifest))
    print('  sheets.html           작성')

    if video_matched:
        print('  다시보기 영상 %d/%d 경기 연결' % (video_matched, len(data['matches'])))
    else:
        print('  다시보기 영상 연결 없음 — data/videos.json 이 비어 있습니다.')
        print('    (tools/fetch_videos.py 로 채우거나 직접 적어 넣으면 바로 반영됩니다)')
    print('완료.')


if __name__ == '__main__':
    main()
