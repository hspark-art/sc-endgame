#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""올린 뒤에 사이트를 직접 열어 '정말 그 내용인지' 확인합니다.

    python3 tools/verify_live.py

왜 필요한가 — 배포가 성공했다고 사이트가 최신이라는 보장이 없습니다.
2026-09-21 서버 이전에서 겪은 것만 해도 이렇습니다.

  · 옛 서버 주소로 올리고 있었는데 실행은 초록이었습니다.
  · 엉뚱한 폴더에 올리면 파일은 잘 올라가고 사이트는 그대로입니다.
  · 기본 문서가 index.php 인데 index.html 을 올리면 아무 일도 안 일어납니다.

그래서 **사람이 눈으로 보지 않아도** 어긋나면 바로 알도록, 올린 직후 사이트를
받아 와 방금 만든 것과 대조합니다. 두 가지를 봅니다.

  builtAt   방금 만든 판의 시각 (내용이 바뀔 때만 움직입니다)
  숫자      매치·세트·선수 (설명문에 박혀 있습니다)

어긋나면 슬랙으로 알리고 실패로 끝냅니다. 조용히 옛 사이트가 떠 있는 것보다
빨간 실행 하나가 낫습니다.
"""

import io
import json
import os
import re
import sys
import time
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

BUILT = re.compile(r'"builtAt"\s*:\s*"([^"]+)"')
COUNTS = re.compile(r'(\d[\d,]*)\s*매치\s*(\d[\d,]*)\s*세트,\s*선수\s*(\d+)\s*명')


def marks(text):
    """페이지에서 대조할 표식을 뽑습니다."""
    b = BUILT.search(text or '')
    c = COUNTS.search(text or '')
    return {
        'builtAt': b.group(1) if b else None,
        'counts': tuple(x.replace(',', '') for x in c.groups()) if c else None,
    }


def fetch(url, tries=3, wait=6):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'sc-endgame-verify',
                'Cache-Control': 'no-cache',
            })
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            last = e
            if i + 1 < tries:
                print('  (%d번째 시도 실패 — %s, %d초 뒤 다시)'
                      % (i + 1, type(e).__name__, wait))
                time.sleep(wait)
    raise SystemExit('사이트를 열지 못했습니다: %s (%s: %s)'
                     % (url, type(last).__name__, last))


def main():
    base = ''
    try:
        with io.open(os.path.join(ROOT, 'data', 'site.json'), encoding='utf-8') as f:
            base = (json.load(f).get('baseUrl') or '').rstrip('/')
    except (IOError, OSError, ValueError):
        pass
    if not base:
        raise SystemExit('data/site.json 에 baseUrl 이 없습니다.')

    page = os.path.join(ROOT, 'index.php')
    if not os.path.exists(page):
        page = os.path.join(ROOT, 'index.html')
    if not os.path.exists(page):
        raise SystemExit('만들어 둔 index 페이지가 없습니다 — build.py 를 먼저 돌리세요.')
    mine = marks(io.open(page, encoding='utf-8').read())

    # 인자를 주면 그 주소를 그대로 봅니다 (시험용 — file:// 도 됩니다).
    url = sys.argv[1] if len(sys.argv) > 1 else base + '/'
    print('사이트 확인 — %s' % url)
    theirs = marks(fetch(url))

    same_time = mine['builtAt'] and mine['builtAt'] == theirs['builtAt']
    same_nums = mine['counts'] and mine['counts'] == theirs['counts']
    def show(m):
        n = m['counts']
        return '%s · 매치 %s·세트 %s·선수 %s' % (
            m['builtAt'] or '(없음)', *(n or ('?', '?', '?')))
    print('  만든 것: %s' % show(mine))
    print('  사이트 : %s' % show(theirs))

    if same_time and same_nums:
        print('사이트가 방금 만든 것과 같습니다 ✅')
        return
    why = []
    if not same_time:
        why.append('갱신 시각이 다릅니다 (만든 것 %s · 사이트 %s)'
                   % (mine['builtAt'], theirs['builtAt']))
    if not same_nums:
        def nums(c):
            return '매치 %s·세트 %s·선수 %s' % c if c else '(못 읽음)'
        why.append('기록 수가 다릅니다 (만든 것 %s · 사이트 %s)'
                   % (nums(mine['counts']), nums(theirs['counts'])))
    print('사이트가 방금 만든 것과 다릅니다 ❌')
    for w in why:
        print('  · ' + w)
    print('  올라간 곳이 이 주소가 아니거나(폴더·서버), 기본 문서가 다른 파일일 수 있습니다.')
    try:
        import notify
        notify.notify_problem('끝장전 사이트가 최신이 아닙니다',
                              ['확인한 주소: %s' % url] + ['· ' + w for w in why])
    except Exception as e:
        print('  (문제 알림 건너뜀 — %s)' % e)
    sys.exit(1)


if __name__ == '__main__':
    main()
