#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""유튜브 채널에서 끝장전 다시보기 영상을 찾아 data/videos.json 을 채웁니다.

    export YOUTUBE_API_KEY=...        # 구글 클라우드 콘솔에서 YouTube Data API v3 키 발급
    python3 tools/fetch_videos.py             # 매칭 결과만 보여주고 끝
    python3 tools/fetch_videos.py --write     # data/videos.json 에 실제로 기록
    python3 tools/fetch_videos.py --write --min-score 3   # 더 엄격하게

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
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
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


def score(match, video):
    """경기와 영상이 얼마나 맞는지 점수. 3점 이상이면 꽤 믿을 만합니다."""
    a, b = match['players']
    text = video['title'] + ' ' + video['desc']
    hit_a, hit_b = a in text, b in text
    if not (hit_a and hit_b):
        return 0

    s = 2                                        # 두 선수 이름이 다 나옴
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
    cand = [v for v in videos
            if any(n in (v['title'] + v['desc']) for n in names)]
    print('선수 이름이 들어간 영상 %d개를 대상으로 맞춰 봅니다.' % len(cand))

    best = {}
    used = defaultdict(list)
    for m in matches:
        top_s, top_v = 0, None
        for v in cand:
            s = score(m, v)
            if s > top_s:
                top_s, top_v = s, v
        if top_v and top_s >= args.min_score:
            best[stats.match_key(m)] = 'https://www.youtube.com/watch?v=' + top_v['id']
            used[top_v['id']].append(m['date'])

    dupes = {k: v for k, v in used.items() if len(v) > 1}
    print('\n%d/%d 경기에 영상을 붙였습니다 (기준 점수 %d 이상).'
          % (len(best), len(matches), args.min_score))
    if dupes:
        print('한 영상이 여러 경기에 걸린 경우 %d건 — 확인이 필요합니다:' % len(dupes))
        for vid, dates in list(dupes.items())[:10]:
            print('   %s → %s' % (vid, ', '.join(dates)))

    if not args.write:
        for k in list(best)[:10]:
            print('   %s  →  %s' % (k, best[k]))
        print('\n실제로 기록하려면 --write 를 붙여 주세요.')
        return

    path = os.path.join(ROOT, 'data', 'videos.json')
    doc = json.load(io.open(path, encoding='utf-8'))
    doc.setdefault('matches', {})
    added = 0
    for k, v in best.items():
        if k not in doc['matches']:              # 손으로 넣은 항목은 건드리지 않습니다
            doc['matches'][k] = v
            added += 1
    print('새로 추가 %d건, 기존 유지 %d건.' % (added, len(doc['matches']) - added))
    doc['matches'] = dict(sorted(doc['matches'].items(), reverse=True))
    io.open(path, 'w', encoding='utf-8').write(
        json.dumps(doc, ensure_ascii=False, indent=1) + '\n')
    print('data/videos.json 에 기록했습니다. 이제 tools/build.py 를 다시 돌리세요.')


if __name__ == '__main__':
    main()
