#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""유튜브 채널에서 끝장전 다시보기 영상을 찾아 data/videos.json 을 채웁니다.

    export YOUTUBE_API_KEY=...        # 구글 클라우드 콘솔에서 YouTube Data API v3 키 발급
    python3 tools/fetch_videos.py             # 매칭 결과만 보여주고 끝
    python3 tools/fetch_videos.py --write     # data/videos.json 에 실제로 기록
    python3 tools/fetch_videos.py --write --min-score 3   # 더 엄격하게
    python3 tools/fetch_videos.py --write --replace       # 앞서 넣은 것도 새로 덮어쓰기

무엇을 하나요
  1. 채널(@ETALENT-SC, @ETALENT-TV)의 업로드 목록을 전부 받아옵니다.
     (playlistItems 는 호출당 1유닛이라 검색 API 보다 훨씬 쌉니다)
  2. 영상 제목·설명에서 두 선수 이름과 날짜를 찾아 경기와 짝지읍니다.
  3. 확실한 것만 남기고 data/videos.json 의 matches 에 적습니다.

손으로 넣어도 됩니다 — data/videos.json 의 matches 에
  "2026-08-12|김지성|김택용": "https://www.youtube.com/watch?v=..."
처럼 한 줄 추가한 뒤 tools/build.py 를 다시 돌리면 사이트에 반영됩니다.
"""

import argparse
import bisect
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import stats                                     # noqa: E402

# 윈도우 콘솔에서 한글·기호가 깨지거나 터지지 않게 합니다.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass


API = 'https://www.googleapis.com/youtube/v3/'
HANDLES = ['ETALENT-SC', 'ETALENT-TV']           # 끝장전 전용 채널을 먼저 봅니다
# 영상이 경기 당일보다 앞서 올라올 수는 없고, 아주 오래 뒤에 올라오지도 않습니다.
DAY_WINDOW = (-1, 120)


def api_get(path, key, **params):
    params['key'] = key
    url = API + path + '?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def uploads_playlist(handle, key):
    d = api_get('channels', key, part='contentDetails,snippet', forHandle=handle)
    items = d.get('items') or []
    if not items:
        return None, None
    it = items[0]
    return (it['contentDetails']['relatedPlaylists']['uploads'],
            it['snippet']['title'])


def all_videos(playlist_id, key, cap=3000):
    out, token = [], None
    while len(out) < cap:
        d = api_get('playlistItems', key, part='snippet,contentDetails',
                    playlistId=playlist_id, maxResults=50,
                    **({'pageToken': token} if token else {}))
        for it in d.get('items', []):
            sn = it['snippet']
            out.append({
                'id': it['contentDetails']['videoId'],
                'title': sn.get('title', ''),
                'desc': (sn.get('description') or '')[:400],
                'published': (it['contentDetails'].get('videoPublishedAt')
                              or sn.get('publishedAt') or '')[:10],
            })
        token = d.get('nextPageToken')
        if not token:
            break
    return out


DATE_PATTERNS = [
    re.compile(r'(20\d{2})[.\-/년 ]\s*(\d{1,2})[.\-/월 ]\s*(\d{1,2})'),
    re.compile(r'\b(\d{2})(\d{2})(\d{2})\b'),                 # 260812
    re.compile(r'(\d{1,2})[.\-/월 ]\s*(\d{1,2})\s*일'),        # 8월 12일
]


def dates_in(text, fallback_year=None):
    """제목에서 찾을 수 있는 날짜 후보를 모읍니다."""
    found = set()
    for i, pat in enumerate(DATE_PATTERNS):
        for m in pat.finditer(text):
            g = [int(x) for x in m.groups()]
            try:
                if i == 0:
                    found.add(date(g[0], g[1], g[2]))
                elif i == 1:
                    found.add(date(2000 + g[0], g[1], g[2]))
                elif fallback_year:
                    found.add(date(fallback_year, g[0], g[1]))
            except ValueError:
                continue
    return found


# 여러 경기를 한 편에 몰아 담은 편집본입니다 — 특정 경기의 다시보기가 아닙니다.
COMPILATION_RE = re.compile(r'몰아보기|모아보기|명경기 모음|\d+\s*[~∼-]\s*\d+\s*화')


def is_compilation(video):
    return bool(COMPILATION_RE.search(video['title']))


# 제목 끝의 방송 회차 — 'SC1-14', 'Sc1- 221' 처럼 적혀 있습니다.
EPISODE_RE = re.compile('[Ss][Cc]1[- –] *([0-9]{1,3})')


def episode_of(video):
    m = EPISODE_RE.search(video['title'])
    return int(m.group(1)) if m else None


def score(match, video):
    """경기와 영상이 얼마나 맞는지 점수. 3점 이상이면 꽤 믿을 만합니다."""
    a, b = match['players']
    title = video['title']
    text = title + ' ' + video['desc']
    # 두 이름이 '제목'에 다 나와야 합니다. 설명글에는 그날 방송의 다른 경기까지
    # 적혀 있어서, 설명만 보고 맞추면 엉뚱한 경기에 붙습니다.
    if not (a in title and b in title):
        return 0

    s = 4                                        # 제목에 두 선수 이름이 다 나옴
    mdate = date(*map(int, match['date'].split('-')))
    pub = video['published']
    pubd = date(*map(int, pub.split('-'))) if pub else None

    if pubd:
        gap = (pubd - mdate).days
        if not (DAY_WINDOW[0] <= gap <= DAY_WINDOW[1]):
            return 0                             # 시기가 아예 안 맞으면 탈락
        if gap <= 14:
            s += 1
        if gap <= 3:
            s += 1

    if mdate in dates_in(text, fallback_year=mdate.year):
        s += 3                                   # 제목에 경기 날짜가 그대로 있음
    if '끝장전' in text:
        s += 1
    return s


def stored_key():
    """data/youtube.json 에 넣어 둔 키. 환경변수가 없을 때 씁니다."""
    path = os.path.join(ROOT, 'data', 'youtube.json')
    if not os.path.exists(path):
        return None
    try:
        return json.load(io.open(path, encoding='utf-8')).get('apiKey') or None
    except (ValueError, OSError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--key', default=os.environ.get('YOUTUBE_API_KEY') or stored_key())
    ap.add_argument('--write', action='store_true', help='data/videos.json 에 기록')
    ap.add_argument('--min-score', type=int, default=3)
    ap.add_argument('--cache', default=os.path.join(HERE, '.yt-cache.json'),
                    help='받아온 영상 목록을 저장해 두는 곳 (할당량 절약)')
    ap.add_argument('--refresh', action='store_true', help='캐시를 무시하고 다시 받기')
    ap.add_argument('--replace', action='store_true',
                    help='앞서 자동으로 넣은 항목도 새 결과로 덮어쓰기')
    args = ap.parse_args()

    videos = []
    if os.path.exists(args.cache) and not args.refresh:
        videos = json.load(io.open(args.cache, encoding='utf-8'))
        print('캐시에서 영상 %d개를 읽었습니다 (%s)' % (len(videos), args.cache))
    else:
        if not args.key:
            raise SystemExit(
                'YouTube Data API 키가 필요합니다.\n'
                '  data/youtube.json 에  {"apiKey": "..."}  로 넣어 두거나,\n'
                '  YOUTUBE_API_KEY 환경변수  또는  --key ... 로 넘겨 주세요.\n'
                '  (구글 클라우드 콘솔 → API 및 서비스 → YouTube Data API v3 사용 설정 → 키 만들기)')
        for handle in HANDLES:
            pid, title = uploads_playlist(handle, args.key)
            if not pid:
                print('  ! @%s 채널을 찾지 못했습니다' % handle)
                continue
            got = all_videos(pid, args.key)
            print('  @%s (%s) 영상 %d개' % (handle, title, len(got)))
            videos.extend(got)
        json.dump(videos, io.open(args.cache, 'w', encoding='utf-8'),
                  ensure_ascii=False)

    data = json.load(io.open(os.path.join(ROOT, 'data', 'endgame.json'), encoding='utf-8'))
    matches = data['matches']

    # 선수 이름이 하나라도 들어간 영상만 추려서 비교 횟수를 줄입니다.
    names = {p['name'] for p in data['players']}
    named = [v for v in videos
             if any(n in (v['title'] + v['desc']) for n in names)]
    cand = [v for v in named if not is_compilation(v)]
    print('선수 이름이 들어간 영상 %d개를 대상으로 맞춰 봅니다.' % len(cand))
    if len(named) != len(cand):
        print('  여러 경기를 묶은 편집본 %d개는 뺐습니다.' % (len(named) - len(cand)))

    # 짝이 될 만한 것을 전부 모은 뒤 점수가 높은 쪽부터 확정합니다.
    # 영상 하나는 경기 하나에만 붙습니다 — 예전에는 경기마다 따로 고르느라
    # 같은 영상이 여러 경기에 중복으로 걸렸습니다.
    pairs = []
    for mi, m in enumerate(matches):
        mdate = date(*map(int, m['date'].split('-')))
        for v in cand:
            s = score(m, v)
            if s < args.min_score:
                continue
            gap = (abs((date(*map(int, v['published'].split('-'))) - mdate).days)
                   if v['published'] else 999)
            pairs.append((-s, gap, mi, v))
    pairs.sort(key=lambda x: x[:3])               # 점수 높은 순 → 날짜 가까운 순

    best, taken_m, taken_v = {}, set(), set()
    for _s, _gap, mi, v in pairs:
        if mi in taken_m or v['id'] in taken_v:
            continue
        taken_m.add(mi)
        taken_v.add(v['id'])
        best[stats.match_key(matches[mi])] = 'https://www.youtube.com/watch?v=' + v['id']

    # 2차 — 한참 뒤에 올라온 재업로드를 회차 번호로 찾아 붙입니다.
    # 방송 직후 올라온 영상으로 맞춘 경기들이 (회차 → 경기날짜) 기준점이 되고,
    # '회차가 커지면 날짜도 커진다'는 성질로 후보 구간을 좁힙니다.
    # 같은 두 선수가 여러 번 붙었어도 회차가 있으면 어느 경기인지 가려집니다.
    by_id = {v['id']: v for v in cand}
    anchors = {}
    for k, url in best.items():
        v = by_id.get(url.rsplit('=', 1)[-1])
        n = episode_of(v) if v else None
        if n:
            anchors[n] = k.split('|')[0]
    ns = sorted(anchors)
    pair_dates = {}
    for m in matches:
        pair_dates.setdefault(tuple(sorted(m['players'])), []).append(m['date'])

    late = 0
    for mi, m in enumerate(matches):
        if mi in taken_m:
            continue
        pair = tuple(sorted(m['players']))
        for v in cand:
            if v['id'] in taken_v:
                continue
            n = episode_of(v)
            if not n or not all(x in v['title'] for x in pair):
                continue
            i = bisect.bisect_left(ns, n)
            lo = anchors[ns[i - 1]] if i > 0 else ''
            hi = anchors[ns[i]] if i < len(ns) else '9999-99-99'
            fits = [dt for dt in pair_dates[pair] if lo <= dt <= hi]
            if len(fits) == 1 and fits[0] == m['date']:
                taken_m.add(mi)
                taken_v.add(v['id'])
                best[stats.match_key(m)] = 'https://www.youtube.com/watch?v=' + v['id']
                late += 1
                break

    print('')
    print('%d/%d 경기에 영상을 붙였습니다 (기준 점수 %d 이상).'
          % (len(best), len(matches), args.min_score))
    if late:
        print('  그중 %d건은 한참 뒤에 올라온 재업로드를 회차 번호로 찾은 것입니다.' % late)

    if not args.write:
        for k in list(best)[:10]:
            print('   %s  →  %s' % (k, best[k]))
        print('\n실제로 기록하려면 --write 를 붙여 주세요.')
        return

    path = os.path.join(ROOT, 'data', 'videos.json')
    doc = json.load(io.open(path, encoding='utf-8'))
    doc.setdefault('matches', {})
    if args.replace:                             # 잘못 걸린 항목을 걷어내고 다시 채웁니다
        before = len(doc['matches'])
        doc['matches'] = dict(best)
        print('%d건 → %d건으로 새로 채웠습니다 (--replace).' % (before, len(best)))
    else:
        added = 0
        for k, v in best.items():
            if k not in doc['matches']:          # 손으로 넣은 항목은 건드리지 않습니다
                doc['matches'][k] = v
                added += 1
        print('새로 추가 %d건, 기존 유지 %d건.' % (added, len(doc['matches']) - added))
    doc['matches'] = dict(sorted(doc['matches'].items(), reverse=True))
    io.open(path, 'w', encoding='utf-8').write(
        json.dumps(doc, ensure_ascii=False, indent=1) + '\n')
    print('data/videos.json 에 기록했습니다. 이제 tools/build.py 를 다시 돌리세요.')


if __name__ == '__main__':
    main()
