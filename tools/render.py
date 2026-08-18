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


def head(title, desc, css, canonical):
    """<head> 부터 <body> 열기까지."""
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
    )


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
           wp, RACE_VAR[front], pct(w, l) if total else '',
           100 - wp, RACE_VAR[back], pct(l, w) if total else '')
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

    out = [head(title, desc, css, canonical)]

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
    out = [head(title, desc, css, BASE_URL + '/sheets.html')]
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
    out = [head(title, desc, css, BASE_URL + '/')]
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
