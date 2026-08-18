# -*- coding: utf-8 -*-
"""HTML 조립 — 공통 머리말, 선수 상세 페이지, 구글시트 연동 안내 페이지."""

import html
import json
import urllib.parse

SITE_NAME = '스타크래프트 끝장전 기록실'
BASE_URL = 'https://hspark-art.github.io/sc-endgame'
LOGO = 'https://stimg.sooplive.com/LOGO/ta/talent/m/talent.webp'
SOOP_URL = 'https://www.sooplive.com/station/talent'
YT_TV = 'https://www.youtube.com/@ETALENT-TV'
YT_SC = 'https://www.youtube.com/@ETALENT-SC'

RACE_LABEL = {'T': '테란', 'P': '프로토스', 'Z': '저그'}
RACE_VAR = {'T': 'var(--t)', 'P': 'var(--p)', 'Z': 'var(--z)'}
MU_KEYS = ['PvT', 'TvZ', 'PvZ']


def e(s):
    return html.escape('' if s is None else str(s), quote=True)


def pct(w, l):
    t = w + l
    return '%.1f%%' % (w / t * 100) if t else '-'


def head(title, desc, css, canonical, navbar=''):
    """<head> 부터 <body> 열기까지. navbar 는 사이트 전환 바 HTML 입니다."""
    return (
        '<!DOCTYPE html>\n<html lang="ko">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>%s</title>\n'
        '<meta name="description" content="%s">\n'
        '<link rel="canonical" href="%s">\n'
        '<meta property="og:type" content="website">\n'
        '<meta property="og:site_name" content="%s">\n'
        '<meta property="og:title" content="%s">\n'
        '<meta property="og:description" content="%s">\n'
        '<meta property="og:url" content="%s">\n'
        '<meta property="og:image" content="%s">\n'
        '<meta name="twitter:card" content="summary">\n'
        '<link rel="icon" href="%s">\n'
        '<link rel="stylesheet" as="style" '
        'href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">\n'
        '<style>\n%s</style>\n</head>\n<body>\n'
        '<div class="brandbar"></div>\n<div class="wrap">\n'
        % (e(title), e(desc), e(canonical), e(SITE_NAME), e(title), e(desc),
           e(canonical), e(LOGO), e(LOGO), css)
    ) + navbar


def footer(built, extra=''):
    """built 는 갱신 시각으로 넣을 HTML — 허브는 <span id="built">, 정적 페이지는 문자열."""
    return (
        '<footer>\n'
        '데이터 출처: 방송팀이 직접 기록한 구글시트(끝장전 데이터).'
        ' 표시된 값은 시트의 세트 단위 원본 기록을 그대로 다시 계산한 것입니다.<br>\n'
        + (extra + '<br>\n' if extra else '') +
        '마지막 갱신: ' + built + '\n'
        '<div class="legal">선수 이름과 경기 결과는 공개 방송 기록을 정리한 것입니다. '
        '이 사이트는 SOOP·유튜브 및 각 선수와 공식적인 관계가 없습니다.</div>\n'
        '</footer>\n</div>\n'
    )


SITES = [
    ('endgame', '끝장전', '', 'index.html'),
    ('asl', 'ASL', 'asl/', 'asl/index.html'),
    ('cg', 'CG 제작', 'admin/', 'admin/'),
]


def nav(active, depth=0):
    """모든 페이지 맨 위에 붙는 사이트 전환 바."""
    up = '../' * depth
    items = ''.join(
        '<a class="navlink%s" href="%s%s">%s</a>'
        % (' on' if key == active else '', up, href, label)
        for key, label, _dir, href in SITES)
    return '<nav class="sitenav">%s</nav>\n' % items


def link_banner():
    return (
        '<div class="linkbanner">\n'
        '<a class="linkbtn" href="%s" target="_blank" rel="noopener">📺 SOOP 방송국'
        '<span class="sub2">중계진 공식 채널</span></a>\n'
        '<a class="linkbtn yt" href="%s" target="_blank" rel="noopener">'
        '<span class="yt-ico">▶</span> 다시보기<span class="sub2">ETALENT-TV</span></a>\n'
        '<a class="linkbtn yt" href="%s" target="_blank" rel="noopener">'
        '<span class="yt-ico">▶</span> 끝장전 명경기<span class="sub2">ETALENT-SC</span></a>\n'
        '</div>\n' % (SOOP_URL, YT_TV, YT_SC)
    )


def download_box(depth=0):
    up = '../' * depth
    files = [('선수', 'players'), ('경기', 'matches'), ('세트별 맵', 'sets'),
             ('맵', 'maps'), ('상대전적', 'headtohead'), ('연도별', 'yearly')]
    btns = ''.join(
        '<a class="dlbtn" href="%scsv/%s.csv" download>%s CSV</a>' % (up, f, label)
        for label, f in files)
    return (
        '<div class="dlbox">\n'
        '<span class="t">데이터 내려받기</span>\n'
        '<a class="dlbtn on" href="%sxlsx/sc-endgame.xlsx" download>엑셀 (.xlsx)</a>\n'
        '%s\n'
        '<a class="dlbtn" href="%ssheets.html">구글 시트 연동 →</a>\n'
        '</div>\n' % (up, btns, up)
    )


def race_bar(w, l, front, back):
    total = w + l
    wp = (w / total * 100) if total else 50
    return (
        '<div class="murow">'
        '<div class="mulabel"><span><span class="race %s">%s</span>%s <b>%d</b></span>'
        '<span><b>%d</b> %s<span class="race %s">%s</span></span></div>'
        '<div class="mubar">'
        '<span style="width:%.4f%%;background:%s">%s</span>'
        '<span style="width:%.4f%%;background:%s">%s</span>'
        '</div></div>'
        % (front, front, RACE_LABEL[front], w, l, RACE_LABEL[back], back, back,
           wp, RACE_VAR[front], pct(w, l) if total and wp >= 13 else '',
           100 - wp, RACE_VAR[back], pct(l, w) if total and (100 - wp) >= 13 else '')
    )


def _yt_cell(url, a, b):
    if url:
        return ('<a class="yt-mini" href="%s" target="_blank" rel="noopener">▶ 다시보기</a>'
                % e(url))
    q = urllib.parse.quote(a + ' ' + b)
    return ('<a class="yt-mini yt-fallback" href="%s/search?query=%s" '
            'target="_blank" rel="noopener">🔍 채널에서 찾기</a>' % (YT_SC, q))


def player_page(p, ctx, css):
    """선수 한 명의 정적 상세 페이지."""
    name, race, slug = p['name'], p['race'], p['slug']
    slugs = ctx['slugs']
    race_of = ctx['raceOf']
    years = ctx['years']
    strk = ctx['streaks'][name]
    yearly = ctx['playerYearly'].get(name, {})
    matches = [m for m in ctx['matches'] if name in m['players']]

    title = '%s (%s) — %s' % (name, RACE_LABEL[race], SITE_NAME)
    desc = ('%s %s · 매치 %d승 %d패(%s) · 세트 %d승 %d패(%s) · %d경기 출전 (%s ~ %s)'
            % (name, RACE_LABEL[race], p['matchWin'], p['matchLoss'],
               pct(p['matchWin'], p['matchLoss']), p['setWin'], p['setLoss'],
               pct(p['setWin'], p['setLoss']), p['appearances'],
               p['firstDate'], p['lastDate']))
    canonical = '%s/p/%s.html' % (BASE_URL, urllib.parse.quote(slug))

    out = [head(title, desc, css, canonical, nav('endgame', depth=1))]

    out.append('<a class="backlink" href="../index.html">← 기록실 홈으로</a>\n')

    cur = strk['current']
    cur_txt = ('<span class="ptag streak-w">%d연승 중</span>' % cur if cur > 0 else
               '<span class="ptag streak-l">%d연패 중</span>' % -cur if cur < 0 else '')
    out.append(
        '<header style="border-bottom:none;padding-bottom:0">'
        '<div class="phead"><span class="race %s">%s</span>'
        '<span class="pname">%s</span>'
        '<span class="ptag">%s</span>%s</div>'
        '<div class="stats-strip">%s</div></header>\n'
        % (race, race, e(name), RACE_LABEL[race], cur_txt,
           ''.join('<div class="item">%s<b>%s</b></div>' % kv for kv in [
               ('매치 전적', '%d승 %d패 · %s' % (p['matchWin'], p['matchLoss'],
                                             pct(p['matchWin'], p['matchLoss']))),
               ('세트 전적', '%d승 %d패 · %s' % (p['setWin'], p['setLoss'],
                                             pct(p['setWin'], p['setLoss']))),
               ('출전', '%d경기' % p['appearances']),
               ('최다 연승', '%d연승' % strk['bestWin']),
               ('활동 기간', '%s ~ %s' % (p['firstDate'], p['lastDate'])),
           ])))

    # 종족별 세트 전적
    pairs = [(r, p['vsRace'][r]) for r in ['T', 'P', 'Z'] if p['vsRace'][r]['w'] + p['vsRace'][r]['l']]
    out.append('<div class="card" style="margin-top:16px"><div class="cardtitle">'
               '종족별 세트 전적</div>')
    for r, v in pairs:
        out.append(race_bar(v['w'], v['l'], race, r))
    if not pairs:
        out.append('<div class="emptybox">기록이 없습니다.</div>')
    out.append('</div>\n')

    # 연도별 성적
    rows = []
    for y in years:
        v = yearly.get(y)
        if not v:
            continue
        rows.append(
            '<tr><td class="nm">%s</td><td class="num">%d</td>'
            '<td class="num">%d-%d</td><td class="num">%s</td>'
            '<td class="num">%d-%d</td><td class="num">%s</td>'
            '<td class="num muted hide-mobile">%s ~ %s</td></tr>'
            % (y, v['apps'], v['matchWin'], v['matchLoss'],
               pct(v['matchWin'], v['matchLoss']), v['setWin'], v['setLoss'],
               pct(v['setWin'], v['setLoss']), v['firstDate'], v['lastDate']))
    out.append(
        '<div class="card"><div class="cardtitle">연도별 성적</div>'
        '<div class="tblwrap"><table><thead><tr>'
        '<th class="static">연도</th><th class="static num">출전</th>'
        '<th class="static num">매치</th><th class="static num">매치 승률</th>'
        '<th class="static num">세트</th><th class="static num">세트 승률</th>'
        '<th class="static num hide-mobile">기간</th></tr></thead><tbody>%s</tbody>'
        '</table></div></div>\n' % ''.join(rows))

    # 상대 전적
    vs_rows = []
    for o in p['vsPlayers']:
        o_slug = slugs.get(o['name'])
        won = sum(1 for x in o['matches'] if x['result'] == '승')
        label = ('<a href="%s.html"><span class="race %s">%s</span>'
                 '<span class="nm-link">%s</span></a>'
                 % (urllib.parse.quote(o_slug), race_of.get(o['name'], ''),
                    race_of.get(o['name'], '?'), e(o['name']))) if o_slug else e(o['name'])
        vs_rows.append(
            '<tr><td>%s</td><td class="num">%d-%d</td><td class="num">%d-%d</td>'
            '<td class="num">%s</td></tr>'
            % (label, won, len(o['matches']) - won, o['w'], o['l'], pct(o['w'], o['l'])))
    out.append(
        '<div class="card"><div class="cardtitle">상대 전적'
        '<span class="note">%d명</span></div>'
        '<div class="tblwrap"><table><thead><tr><th class="static">상대</th>'
        '<th class="static num">매치</th><th class="static num">세트</th>'
        '<th class="static num">세트 승률</th></tr></thead><tbody>%s</tbody>'
        '</table></div></div>\n' % (len(p['vsPlayers']), ''.join(vs_rows)))

    # 전체 경기
    mrows = []
    for m in matches:
        opp = m['players'][1] if m['players'][0] == name else m['players'][0]
        win = m['winner'] == name
        o_slug = slugs.get(opp)
        label = ('<a href="%s.html"><span class="race %s">%s</span>'
                 '<span class="nm-link">%s</span></a>'
                 % (urllib.parse.quote(o_slug), m['race'][opp], m['race'][opp], e(opp))) \
            if o_slug else e(opp)
        maps = [x for x in m.get('maps') or [] if x]
        mrows.append(
            '<tr><td class="muted">%s</td><td>%s</td>'
            '<td class="num %s">%d-%d</td>'
            '<td class="muted hide-mobile" style="white-space:normal">%s</td>'
            '<td>%s</td></tr>'
            % (m['date'], label, 'win' if win else 'lose',
               m['setWins'][name], m['setWins'][opp], e(', '.join(maps)),
               _yt_cell(m.get('youtubeUrl'), name, opp)))
    out.append(
        '<div class="card"><div class="cardtitle">전체 경기'
        '<span class="note">%d경기 · 최신순</span></div>'
        '<div class="tblwrap"><table><thead><tr><th class="static">날짜</th>'
        '<th class="static">상대</th><th class="static num">스코어</th>'
        '<th class="static hide-mobile">맵</th><th class="static">다시보기</th>'
        '</tr></thead><tbody>%s</tbody></table></div></div>\n'
        % (len(matches), ''.join(mrows)))

    out.append(download_box(depth=1))
    out.append(footer(ctx['builtAtKo']))
    out.append('</body>\n</html>\n')
    return ''.join(out)


def sheets_page(css, manifest):
    """구글 시트에서 이 데이터를 바로 끌어 쓰는 방법 안내."""
    title = '구글 시트 연동 — ' + SITE_NAME
    desc = '끝장전 기록실 데이터를 구글 시트에서 IMPORTDATA 로 바로 불러오는 방법.'
    out = [head(title, desc, css, BASE_URL + '/sheets.html', nav('endgame'))]
    out.append(
        '<header><div class="headrow"><img class="brandlogo" src="%s" alt="">'
        '<div><h1><a href="index.html">%s</a></h1>'
        '<div class="sub">구글 시트 연동</div></div></div></header>\n'
        % (LOGO, SITE_NAME))
    out.append('<a class="backlink" href="index.html">← 기록실 홈으로</a>\n')

    out.append(
        '<div class="card"><div class="cardtitle">한 줄 요약</div>'
        '<div class="hint">구글 시트 아무 칸에 아래 수식을 붙여넣으면 끝입니다. '
        '파일을 내려받아 올릴 필요가 없고, 이 사이트가 갱신되면 시트도 따라 갱신됩니다.</div>'
        '<pre>=IMPORTDATA("%s/csv/players.csv")</pre>'
        '<div class="hint">한글이 깨져 보이면 두 번째 인자로 구분자를 지정해 보세요 — '
        '<code class="inline">=IMPORTDATA("…", ",")</code></div></div>\n' % BASE_URL)

    rows = ''.join(
        '<tr><td class="nm">%s</td><td class="muted">%s</td>'
        '<td><code class="inline">=IMPORTDATA("%s")</code></td>'
        '<td><a class="dlbtn" href="csv/%s" download>내려받기</a></td></tr>'
        % (e(f['label']), e(f['desc']), e(f['url']), e(f['file']))
        for f in manifest['files'])
    out.append(
        '<div class="card"><div class="cardtitle">파일 목록</div>'
        '<div class="tblwrap"><table><thead><tr><th class="static">파일</th>'
        '<th class="static">내용</th><th class="static">구글 시트 수식</th>'
        '<th class="static">직접 받기</th></tr></thead><tbody>%s</tbody></table></div></div>\n'
        % rows)

    out.append(
        '<div class="card"><div class="cardtitle">엑셀로 한 번에 받기</div>'
        '<div class="hint">여섯 개 시트가 한 파일에 들어 있습니다. '
        '구글 시트에서 <b>파일 → 가져오기 → 업로드</b> 로 올리면 그대로 열립니다.</div>'
        '<div style="margin-top:10px">'
        '<a class="dlbtn on" href="xlsx/sc-endgame.xlsx" download>sc-endgame.xlsx 내려받기</a>'
        '</div></div>\n')

    out.append(
        '<div class="card"><div class="cardtitle">원본 JSON</div>'
        '<div class="hint">사이트가 쓰는 원본 데이터 전체입니다. '
        '프로그램으로 가공할 때 쓰세요.</div>'
        '<pre>%s/data/endgame.json</pre></div>\n' % BASE_URL)

    out.append(
        '<div class="card"><div class="cardtitle">자동 갱신되게 하려면</div>'
        '<ol class="steps">'
        '<li>시트에 <code class="inline">IMPORTDATA</code> 수식을 넣습니다.</li>'
        '<li><b>파일 → 설정 → 계산</b> 에서 재계산을 <b>변경할 때 및 매시간</b> 으로 둡니다.</li>'
        '<li>이 사이트가 갱신되면 최대 한 시간 안에 시트에도 반영됩니다.</li>'
        '</ol>'
        '<div class="hint">수식이 아니라 값으로 굳히고 싶으면 '
        '범위를 복사한 뒤 <b>선택하여 붙여넣기 → 값만</b> 을 쓰세요.</div></div>\n')

    out.append(footer(manifest['updatedAtKo']))
    out.append('</body>\n</html>\n')
    return ''.join(out)


def index_page(css, app_js, data):
    title = SITE_NAME
    desc = ('%s 통산 기록 — %d매치 %s세트, 선수 %d명, %s ~ %s. '
            '선수 랭킹·상대 전적·맵 통계·경기 기록·다시보기를 한곳에서.'
            % (SITE_NAME, data['global']['totalMatches'],
               format(data['global']['totalSets'], ','), data['global']['totalPlayers'],
               data['global']['firstDate'], data['global']['lastDate']))
    out = [head(title, desc, css, BASE_URL + '/', nav('endgame'))]
    out.append(
        '<header>\n<div class="headrow">\n'
        '<img class="brandlogo" src="%s" alt="중계진">\n'
        '<div>\n<h1>%s</h1>\n<div class="stats-strip" id="strip"></div>\n</div>\n'
        '</div>\n</header>\n' % (LOGO, SITE_NAME))
    out.append(link_banner())
    out.append('<div id="liveBanner"></div>\n')
    out.append(
        '<div class="vmodal" id="vmodal">\n<div class="vmodal-box">\n'
        '<button class="vmodal-close" id="vmodalClose">✕ 닫기</button>\n'
        '<div class="vmodal-frame" id="vmodalFrame"></div>\n</div>\n</div>\n')
    out.append('<div class="tabs" id="tabs"></div>\n<div id="view"></div>\n')
    out.append(download_box())
    out.append(footer('<span id="built"></span>'))
    out.append('<script>\nconst D = %s;\n%s</script>\n</body>\n</html>\n'
               % (json.dumps(data, ensure_ascii=False, separators=(',', ':')), app_js))
    return ''.join(out)


# ── ASL ────────────────────────────────────────────────────────
ASL_NAME = 'ASL 기록실'
ASL_FULL = 'ASL (AfreecaTV / SOOP 스타리그) 기록실'


def asl_download_box(depth=1):
    up = '../' * depth
    files = [('선수', 'players'), ('매치', 'matches'), ('세트', 'sets'),
             ('맵', 'maps'), ('상대전적', 'headtohead'), ('대회', 'tournaments')]
    btns = ''.join(
        '<a class="dlbtn" href="%scsv/asl-%s.csv" download>%s CSV</a>' % (up, f, label)
        for label, f in files)
    return (
        '<div class="dlbox">\n'
        '<span class="t">ASL 데이터 내려받기</span>\n'
        '<a class="dlbtn on" href="%sxlsx/asl.xlsx" download>엑셀 (.xlsx)</a>\n'
        '%s\n'
        '<a class="dlbtn" href="%ssheets.html">구글 시트 연동 →</a>\n'
        '</div>\n' % (up, btns, up)
    )


def asl_footer(built, depth=1):
    up = '../' * depth
    return (
        '<footer>\n'
        'ASL(스타크래프트 리그) 대회 기록입니다. 방송팀이 정리한 세트 단위 원본을 그대로 다시 계산했습니다.<br>\n'
        '이 기록에는 경기 날짜가 없어 대회와 라운드 순서로만 정리했습니다. '
        '매치(시리즈)는 같은 라운드에서 같은 두 선수가 연달아 치른 세트를 하나로 묶은 것입니다.<br>\n'
        '<a href="%sindex.html">끝장전 기록실</a>은 별개 대회라 따로 있습니다.<br>\n'
        '마지막 갱신: %s\n'
        '<div class="legal">선수 이름과 경기 결과는 공개 방송 기록을 정리한 것입니다. '
        '이 사이트는 SOOP·아프리카TV 및 각 선수와 공식적인 관계가 없습니다.</div>\n'
        '</footer>\n</div>\n' % (up, built)
    )


def asl_index_page(css, app_js, data):
    g = data['global']
    desc = ('%s — 대회 %d개, 매치 %s, 세트 %s, 선수 %d명. %s ~ %s. '
            '역대 우승자·선수 랭킹·상대 전적·맵 통계를 한곳에서.'
            % (ASL_FULL, g['totalTournaments'], format(g['totalMatches'], ','),
               format(g['totalSets'], ','), g['totalPlayers'],
               g['firstTournament'], g['lastTournament']))
    out = [head(ASL_NAME, desc, css, BASE_URL + '/asl/', nav('asl', depth=1))]
    out.append(
        '<header>\n<div class="headrow">\n'
        '<img class="brandlogo" src="%s" alt="중계진">\n'
        '<div>\n<h1>%s</h1>\n<div class="stats-strip" id="strip"></div>\n</div>\n'
        '</div>\n</header>\n' % (LOGO, ASL_NAME))
    out.append('<div class="tabs" id="tabs"></div>\n<div id="view"></div>\n')
    out.append(asl_download_box(depth=1))
    out.append(asl_footer('<span id="built"></span>', depth=1))
    out.append('<script>\nconst D = %s;\n%s</script>\n</body>\n</html>\n'
               % (json.dumps(data, ensure_ascii=False, separators=(',', ':')), app_js))
    return ''.join(out)


def asl_player_page(p, ctx, css):
    """ASL 선수 한 명의 정적 상세 페이지."""
    name, race, slug = p['name'], p['race'], p['slug']
    slugs = ctx['slugs']
    race_of = ctx['raceOf']
    tours = ctx['tournaments']
    matches = [m for m in ctx['matches'] if name in m['players']]

    title = '%s (%s) — %s' % (name, RACE_LABEL[race], ASL_NAME)
    desc = ('%s %s · ASL 우승 %d회 · 매치 %d승 %d패(%s) · 세트 %d승 %d패(%s) · %d개 대회 출전'
            % (name, RACE_LABEL[race], p['titles'], p['matchWin'], p['matchLoss'],
               pct(p['matchWin'], p['matchLoss']), p['setWin'], p['setLoss'],
               pct(p['setWin'], p['setLoss']), p['tournaments']))
    canonical = '%s/asl/p/%s.html' % (BASE_URL, urllib.parse.quote(slug))

    out = [head(title, desc, css, canonical, nav('asl', depth=2))]
    out.append('<a class="backlink" href="../index.html">← ASL 기록실로</a>\n')

    tags = ''
    if p['titles']:
        tags += '<span class="ptag" style="color:var(--gold);border-color:var(--gold)">' \
                '🏆 우승 %d회</span>' % p['titles']
    if p['runnerUps']:
        tags += '<span class="ptag">준우승 %d회</span>' % p['runnerUps']
    if ctx['endgameSlug'].get(name):
        tags += ('<span class="ptag"><a href="../../p/%s.html">끝장전 기록 보기 →</a></span>'
                 % urllib.parse.quote(ctx['endgameSlug'][name]))

    out.append(
        '<header style="border-bottom:none;padding-bottom:0">'
        '<div class="phead"><span class="race %s">%s</span>'
        '<span class="pname">%s</span>'
        '<span class="ptag">%s</span>%s</div>'
        '<div class="stats-strip">%s</div></header>\n'
        % (race, race, e(name), RACE_LABEL[race], tags,
           ''.join('<div class="item">%s<b>%s</b></div>' % kv for kv in [
               ('매치 전적', '%d승 %d패 · %s' % (p['matchWin'], p['matchLoss'],
                                             pct(p['matchWin'], p['matchLoss']))),
               ('세트 전적', '%d승 %d패 · %s' % (p['setWin'], p['setLoss'],
                                             pct(p['setWin'], p['setLoss']))),
               ('출전 대회', '%d개' % p['tournaments']),
               ('최고 성적', p.get('bestRound') or '-'),
           ])))

    pairs = [(r, p['vsRace'][r]) for r in ['T', 'P', 'Z']
             if p['vsRace'][r]['w'] + p['vsRace'][r]['l']]
    out.append('<div class="card" style="margin-top:16px"><div class="cardtitle">'
               '종족별 세트 전적</div>')
    for r, v in pairs:
        out.append(race_bar(v['w'], v['l'], race, r))
    if not pairs:
        out.append('<div class="emptybox">기록이 없습니다.</div>')
    out.append('</div>\n')

    rows = []
    for t in tours:
        v = p['byTour'].get(t['name'])
        if not v:
            continue
        crown = ' 🏆' if t.get('champion') == name else (
            ' 🥈' if t.get('runnerUp') == name else '')
        tlink = ('<a href="../t/%s.html"><span class="nm-link">%s</span></a>'
                 % (urllib.parse.quote(t['id']), e(t['name'])))
        rows.append(
            '<tr><td class="nm">%s%s</td><td class="num">%d-%d</td><td class="num">%s</td>'
            '<td class="num">%d-%d</td><td class="num">%s</td>'
            '<td class="hide-mobile dim">%s</td></tr>'
            % (tlink, crown, v['matchWin'], v['matchLoss'],
               pct(v['matchWin'], v['matchLoss']), v['setWin'], v['setLoss'],
               pct(v['setWin'], v['setLoss']), e(v.get('best') or '-')))
    out.append(
        '<div class="card"><div class="cardtitle">대회별 성적'
        '<span class="note">%d개 대회</span></div>'
        '<div class="tblwrap"><table><thead><tr>'
        '<th class="static">대회</th><th class="static num">매치</th>'
        '<th class="static num">매치 승률</th><th class="static num">세트</th>'
        '<th class="static num">세트 승률</th>'
        '<th class="static hide-mobile">최고 라운드</th></tr></thead><tbody>%s</tbody>'
        '</table></div></div>\n' % (p['tournaments'], ''.join(rows)))

    vs_rows = []
    for o in p['vsPlayers']:
        o_slug = slugs.get(o['name'])
        label = ('<a href="%s.html"><span class="race %s">%s</span>'
                 '<span class="nm-link">%s</span></a>'
                 % (urllib.parse.quote(o_slug), race_of.get(o['name'], ''),
                    race_of.get(o['name'], '?'), e(o['name']))) if o_slug else e(o['name'])
        vs_rows.append(
            '<tr><td>%s</td><td class="num">%d-%d</td><td class="num">%d-%d</td>'
            '<td class="num">%s</td></tr>'
            % (label, o['mw'], o['ml'], o['w'], o['l'], pct(o['w'], o['l'])))
    out.append(
        '<div class="card"><div class="cardtitle">상대 전적'
        '<span class="note">%d명</span></div>'
        '<div class="tblwrap"><table><thead><tr><th class="static">상대</th>'
        '<th class="static num">매치</th><th class="static num">세트</th>'
        '<th class="static num">세트 승률</th></tr></thead><tbody>%s</tbody>'
        '</table></div></div>\n' % (len(p['vsPlayers']), ''.join(vs_rows)))

    tour_id = {t['name']: t['id'] for t in tours}
    mrows = []
    for m in matches:
        opp = m['players'][1] if m['players'][0] == name else m['players'][0]
        win = m['winner'] == name
        o_slug = slugs.get(opp)
        label = ('<a href="%s.html"><span class="race %s">%s</span>'
                 '<span class="nm-link">%s</span></a>'
                 % (urllib.parse.quote(o_slug), m['race'][opp], m['race'][opp], e(opp))) \
            if o_slug else e(opp)
        maps = [x for x in (m.get('maps') or []) if x]
        mrows.append(
            '<tr><td class="muted hide-mobile">%s</td><td class="muted">%s</td>'
            '<td>%s</td><td class="num %s">%d-%d</td>'
            '<td class="muted hide-mobile" style="white-space:normal">%s</td></tr>'
            % ('<a href="../t/%s.html"><span class="nm-link">%s</span></a>'
               % (urllib.parse.quote(tour_id[m['tournament']]), e(m['tournament']))
               if m['tournament'] in tour_id else e(m['tournament']),
               e(m['round']), label,
               'win' if win else ('lose' if m['winner'] else ''),
               m['setWins'][name], m['setWins'][opp], e(', '.join(maps))))
    out.append(
        '<div class="card"><div class="cardtitle">전체 경기'
        '<span class="note">%d매치 · 최신 대회순</span></div>'
        '<div class="tblwrap"><table><thead><tr>'
        '<th class="static hide-mobile">대회</th><th class="static">라운드</th>'
        '<th class="static">상대</th><th class="static num">스코어</th>'
        '<th class="static hide-mobile">맵</th></tr></thead><tbody>%s</tbody>'
        '</table></div></div>\n' % (len(matches), ''.join(mrows)))

    out.append(asl_download_box(depth=2))
    out.append(asl_footer(ctx['builtAtKo'], depth=2))
    out.append('</body>\n</html>\n')
    return ''.join(out)


# ── CG 제작 툴 ─────────────────────────────────────────────────
def _fld(label, inner):
    return '<div class="fld"><label>%s</label>%s</div>\n' % (label, inner)


def _player_block(n):
    i = n - 1
    return (
        '<div class="card"><div class="cardtitle">선수 %d '
        '<span class="note">%s</span></div>\n'
        % (n, '왼쪽' if i == 0 else '오른쪽') +
        _fld('이름 (기록실에 있는 선수는 종족이 자동으로 채워집니다)',
             '<input type="text" id="name%d" list="playerList" '
             'placeholder="예: 김지성">' % n) +
        '<div class="row2">' +
        _fld('닉네임', '<input type="text" id="nick%d" placeholder="예: RoyaL">' % n) +
        _fld('종족',
             '<select id="race%d"><option value="T">테란 (T)</option>'
             '<option value="P">프로토스 (P)</option>'
             '<option value="Z">저그 (Z)</option>'
             '<option value="">표시 안 함</option></select>' % n) +
        '</div>\n' +
        _fld('사진',
             '<div class="row-inline">'
             '<label class="filebtn">파일 선택<input type="file" id="photo%d" '
             'accept="image/*"></label>'
             '<button class="btn danger" id="photo%dClear" type="button">지우기</button>'
             '</div>' % (n, n)) +
        _fld('사진 크기',
             '<input type="range" id="zoom%d" min="0.4" max="4" step="0.02" value="1">' % n) +
        '<div class="helptxt">사진은 미리보기 위에서 <b>끌어서 위치</b>를 잡고 '
        '<b>휠로 크기</b>를 맞출 수 있습니다. 이미지 파일을 미리보기에 '
        '끌어다 놓아도 바로 들어갑니다.</div>\n'
        '</div>\n')


def _box_block(i, label, hint):
    return (
        '<div class="card"><div class="cardtitle">%s</div>\n' % label +
        _fld('제목', '<input type="text" id="boxTitle%d">' % i) +
        _fld('내용 (한 줄에 하나씩)', '<textarea id="boxBody%d"></textarea>' % i) +
        '<div class="helptxt">%s</div>\n</div>\n' % hint)


def cg_page(css, app_js, players):
    title = 'CG 제작 툴 — ' + SITE_NAME
    desc = '끝장전 대진표 CG(1920×1080)를 만들어 PNG 로 내려받는 방송용 도구.'
    # 로그인한 관리자에게만 내보냅니다. 서버(PHP)가 판단하므로 소스를 봐도 못 뚫습니다.
    out = ["<?php require __DIR__ . '/auth.php'; admin_require_login(); ?>\n"]
    out.append(head(title, desc, css, BASE_URL + '/admin/', nav('cg', depth=1))
               .replace('<div class="wrap">', '<div class="wrap cgwrap">')
               .replace('<meta name="twitter:card" content="summary">',
                        '<meta name="twitter:card" content="summary">\n'
                        '<meta name="robots" content="noindex, nofollow">'))

    out.append(
        '<header style="border-bottom:none;padding-bottom:6px">'
        '<div class="headrow"><div><h1>CG 제작 툴</h1>'
        '<div class="sub">대진표 이미지를 만들어 PNG(1920×1080)로 내려받습니다. '
        '입력한 내용은 이 브라우저에 자동 저장됩니다.</div></div>'
        '<div style="margin-left:auto;text-align:right">'
        '<div class="helptxt" style="margin:0">'
        '<?= htmlspecialchars(admin_user(), ENT_QUOTES) ?> 님</div>'
        '<a class="dlbtn" href="logout.php" style="margin-top:6px;display:inline-block">'
        '로그아웃</a></div>'
        '</div></header>\n')

    out.append('<div class="cglayout">\n<div class="cgpanel">\n')

    out.append('<div class="card"><div class="cardtitle">상단</div>\n')
    out.append('<div class="row2">')
    out.append(_fld('타이틀', '<input type="text" id="title">'))
    out.append(_fld('타이틀 색', '<input type="color" id="titleColor">'))
    out.append('</div>\n')
    out.append(_fld('스폰서 글자 (로고를 올리면 로고가 우선입니다)',
                    '<input type="text" id="sponsorText" placeholder="예: Google Play">'))
    out.append(_fld('스폰서 로고',
                    '<div class="row-inline">'
                    '<label class="filebtn">파일 선택<input type="file" id="logoSponsor" '
                    'accept="image/*"></label>'
                    '<button class="btn danger" id="logoSponsorClear" type="button">지우기</button>'
                    '</div>'))
    out.append(_fld('방송국 로고 (오른쪽 위)',
                    '<div class="row-inline">'
                    '<label class="filebtn">파일 선택<input type="file" id="logoBroadcast" '
                    'accept="image/*"></label>'
                    '<button class="btn danger" id="logoBroadcastClear" type="button">지우기</button>'
                    '</div>'))
    out.append('</div>\n')

    out.append(_player_block(1))
    out.append(_player_block(2))

    out.append('<div class="card"><div class="cardtitle">배경색</div>\n<div class="row2">')
    out.append(_fld('왼쪽', '<input type="color" id="bgLeft">'))
    out.append(_fld('오른쪽', '<input type="color" id="bgRight">'))
    out.append('</div>\n<button class="btn" id="swap" type="button">좌우 선수 바꾸기</button>\n</div>\n')

    hint = ('<code>[글자]</code> 는 노란 테두리 강조 칸, '
            '<code>* 글자</code> 는 작은 회색 주석, '
            '빈 줄은 한 칸 띄우기입니다. 상자 높이는 내용에 맞춰 알아서 늘어납니다.')
    out.append(_box_block(0, '상자 1', hint))
    out.append(_box_block(1, '상자 2', hint))
    out.append(_box_block(2, '상자 3', hint))

    out.append(
        '<div class="card"><div class="cardtitle">내보내기</div>\n'
        '<div class="btnrow">'
        '<button class="btn primary" id="download" type="button">PNG 내려받기</button>'
        '<button class="btn" id="exportJson" type="button">설정 내보내기</button>'
        '<label class="filebtn">설정 불러오기'
        '<input type="file" id="importJson" accept="application/json,.json"></label>'
        '<button class="btn danger" id="reset" type="button">처음으로</button>'
        '</div>\n<div class="note" id="note"></div>\n'
        '<div class="helptxt">사진까지 포함해 자동 저장하므로, 사진이 아주 크면 저장에 '
        '실패할 수 있습니다. 그럴 때는 "설정 내보내기"로 파일에 남겨 두세요.</div>\n'
        '</div>\n')

    out.append('</div>\n')                                  # cgpanel
    out.append('<div class="cgstage"><canvas id="cv"></canvas>\n'
               '<div class="helptxt">미리보기는 실제 1920×1080 캔버스를 줄여 보여 주는 것이라 '
               '내려받은 PNG 와 똑같습니다.</div></div>\n')
    out.append('</div>\n')                                  # cglayout

    out.append('<datalist id="playerList"></datalist>\n')
    out.append(
        '<footer>이 도구는 브라우저 안에서만 동작합니다 — 올린 사진은 어디에도 올라가지 않고 '
        '이 컴퓨터를 벗어나지 않습니다.<br>선수 자동완성 목록은 끝장전·ASL 기록실 데이터에서 '
        '가져온 %d명입니다.</footer>\n</div>\n' % len(players))
    out.append('<script>\nconst PLAYERS = %s;\n%s</script>\n</body>\n</html>\n'
               % (json.dumps(players, ensure_ascii=False, separators=(',', ':')), app_js))
    return ''.join(out)


# ── ASL 대회 상세 페이지 ────────────────────────────────────────
PLACE_LABEL = {'결승전-W': '우승', '결승전-L': '준우승',
               '3-4위전-W': '3위', '3-4위전-L': '4위'}


def _asl_score_cell(m, a, b):
    """스포일러를 가린 스코어 칸. 눌러야 보입니다."""
    return ('<td class="num score-cell" data-awin="%d">'
            '<span class="spoiler">결과 보기</span>'
            '<span class="score-value" hidden>%d - %d</span></td>'
            % (1 if m['winner'] == a else 0, m['setWins'][a], m['setWins'][b]))


def asl_tournament_page(t, detail, ctx, css):
    """대회 하나의 전체 그림 — 진출 현황·라운드별 경기·선수 성적·맵."""
    slugs = ctx['slugs']
    name = t['name']

    champ = t.get('champion')
    desc = ('%s — 매치 %d · 세트 %d · 선수 %d명%s. 라운드별 경기와 선수 성적을 한곳에서.'
            % (name, t['matches'], t['sets'], t['players'],
               (' · 우승 %s' % champ) if champ else ' · 진행 중'))
    canonical = '%s/asl/t/%s.html' % (BASE_URL, urllib.parse.quote(t['id']))

    out = [head('%s — %s' % (name, ASL_NAME), desc, css, canonical, nav('asl', depth=2))]
    out.append('<a class="backlink" href="../index.html">← ASL 기록실로</a>\n')

    crown = ''
    if champ:
        crown = ('<span class="ptag" style="color:var(--gold);border-color:var(--gold)">'
                 '🏆 %s %s</span>' % (e(champ), e(t.get('finalScore') or '')))
    out.append(
        '<header style="border-bottom:none;padding-bottom:0">'
        '<div class="phead"><span class="pname">%s</span>%s</div>'
        '<div class="stats-strip">%s</div></header>\n'
        % (e(name), crown,
           ''.join('<div class="item">%s<b>%s</b></div>' % kv for kv in [
               ('매치', '%d' % t['matches']),
               ('세트', '%d' % t['sets']),
               ('참가 선수', '%d명' % t['players']),
               ('라운드', '%d개' % len(t['rounds'])),
               ('동족전', '%d세트' % t.get('mirrorSets', 0)),
           ])))

    # 진출 현황 — 어디까지 갔는지
    groups = detail['placements']
    if groups:
        rows = ''.join(
            '<tr><td class="nm" style="white-space:nowrap">%s</td><td>%s</td></tr>'
            % (e(label),
               ' '.join('<a href="../p/%s.html"><span class="race %s">%s</span>'
                        '<span class="nm-link">%s</span></a>'
                        % (urllib.parse.quote(slugs[p['name']]), p['race'], p['race'],
                           e(p['name'])) if p['name'] in slugs else e(p['name'])
                        for p in players))
            for label, players in groups)
        out.append(
            '<div class="card" style="margin-top:16px">'
            '<div class="cardtitle">진출 현황<span class="note">어디까지 올라갔는지</span></div>'
            '<div class="tblwrap"><table><tbody>%s</tbody></table></div></div>\n' % rows)

    # 라운드별 경기
    for rnd in detail['rounds']:
        body = ''
        for m in rnd['matches']:
            a, b = m['players']
            maps = ', '.join(x for x in m['maps'] if x)
            body += ('<tr><td>%s <span class="muted">vs</span> %s</td>%s'
                     '<td class="muted hide-mobile" style="white-space:normal">%s</td></tr>'
                     % (_asl_name_link(a, m['race'][a], slugs),
                        _asl_name_link(b, m['race'][b], slugs),
                        _asl_score_cell(m, a, b), e(maps)))
        out.append(
            '<div class="card"><div class="cardtitle">%s'
            '<span class="note">%d매치 · %d세트</span></div>'
            '<div class="tblwrap"><table><thead><tr>'
            '<th class="static">대진</th><th class="static num">결과</th>'
            '<th class="static hide-mobile">맵</th></tr></thead>'
            '<tbody>%s</tbody></table></div></div>\n'
            % (e(rnd['name']), len(rnd['matches']),
               sum(m['sets'] for m in rnd['matches']), body))

    # 선수 성적
    prows = ''
    for p in detail['players']:
        prows += ('<tr><td>%s</td><td class="num">%d-%d</td><td class="num">%s</td>'
                  '<td class="num">%d-%d</td><td class="num">%s</td>'
                  '<td class="hide-mobile dim">%s</td></tr>'
                  % (_asl_name_link(p['name'], p['race'], slugs),
                     p['matchWin'], p['matchLoss'],
                     pct(p['matchWin'], p['matchLoss']),
                     p['setWin'], p['setLoss'], pct(p['setWin'], p['setLoss']),
                     e(p['best'])))
    out.append(
        '<div class="card"><div class="cardtitle">선수 성적'
        '<span class="note">%d명 · 세트 승 많은 순</span></div>'
        '<div class="tblwrap"><table><thead><tr>'
        '<th class="static">선수</th><th class="static num">매치</th>'
        '<th class="static num">매치 승률</th><th class="static num">세트</th>'
        '<th class="static num">세트 승률</th>'
        '<th class="static hide-mobile">최고 라운드</th></tr></thead>'
        '<tbody>%s</tbody></table></div></div>\n' % (len(detail['players']), prows))

    # 맵과 상성
    mrows = ''.join('<tr><td class="nm">%s</td><td class="num">%d세트</td></tr>'
                    % (e(n), c) for n, c in detail['maps'])
    out.append(
        '<div class="grid2">'
        '<div class="card"><div class="cardtitle">쓰인 맵'
        '<span class="note">%d개</span></div>'
        '<div class="tblwrap"><table><tbody>%s</tbody></table></div></div>'
        '<div class="card"><div class="cardtitle">종족 상성<span class="note">세트 기준</span></div>'
        '%s%s</div></div>\n'
        % (len(detail['maps']), mrows,
           ''.join(race_bar(t['mu'][k]['w'], t['mu'][k]['l'], k[0], k[2]) for k in MU_KEYS),
           ('<div class="hint">동족전 %d세트는 이기고 지는 종족이 같아 상성에 넣지 '
            '않았습니다.</div>' % t['mirrorSets']) if t.get('mirrorSets') else ''))

    out.append(asl_download_box(depth=2))
    out.append(asl_footer(ctx['builtAtKo'], depth=2))
    out.append('''<script>
document.querySelectorAll('.score-cell').forEach(function (cell) {
  cell.addEventListener('click', function () {
    cell.querySelector('.spoiler').hidden = true;
    cell.querySelector('.score-value').hidden = false;
    var aWin = cell.dataset.awin === '1';
    var links = cell.closest('tr').querySelectorAll('.nm-link');
    if (links[0]) links[0].classList.add(aWin ? 'win' : 'lose');
    if (links[1]) links[1].classList.add(aWin ? 'lose' : 'win');
  });
});
</script>
</body>
</html>
''')
    return ''.join(out)


def _asl_name_link(name, race, slugs):
    s = slugs.get(name)
    inner = ('<span class="race %s">%s</span><span class="nm-link">%s</span>'
             % (race, race, e(name)))
    return '<a href="../p/%s.html">%s</a>' % (urllib.parse.quote(s), inner) if s else inner
