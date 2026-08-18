# -*- coding: utf-8 -*-
"""빌드 결과물이 어느 주소에 올려도 깨지지 않는지 검사합니다.

사이트를 지금처럼 하위 폴더(.../sc-endgame/)에 두든, 새 도메인 루트에 통째로
올리든 똑같이 동작해야 합니다. 그러려면 내부 링크가 전부

  - 자기 파일 기준 상대경로이고 (루트 절대경로 '/...' 금지)
  - 사이트 트리 밖으로 나가지 않고 ('../' 가 최상단을 넘지 않기)
  - 실제로 존재하는 파일을 가리켜야

합니다. 아래 검사는 그 세 가지를 확인합니다.
"""

import os
import posixpath
import re
import urllib.parse

# href / src 값을 뽑습니다. 인라인 스크립트 안의 문자열은 보지 않습니다 —
# 그쪽 경로는 별도로 코드에서 관리합니다.
ATTR_RE = re.compile(r'(?:href|src)\s*=\s*"([^"]*)"', re.I)
BASE_RE = re.compile(r'<base\b', re.I)
EXTERNAL_RE = re.compile(r'^(?:[a-z][a-z0-9+.-]*:|//|#|mailto:|data:)', re.I)
# 인라인 <script>/<style> 안은 검사하지 않습니다. 거기 있는 href= 는 자바스크립트
# 문자열 조립이라 정적으로 읽을 수 없고, 그 경로는 브라우저 동작 확인으로 봅니다.
SCRIPT_RE = re.compile(r'<(script|style)\b[^>]*>.*?</\1>', re.I | re.S)


def _walk_html(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in ('.git', 'tools', 'node_modules', '__pycache__')]
        for f in filenames:
            if f.endswith('.html'):
                yield os.path.join(dirpath, f)


def check(root, base_url=None):
    """문제 목록을 돌려줍니다. 빈 리스트면 어디에 올려도 됩니다."""
    problems = []
    root = os.path.abspath(root)

    for path in sorted(_walk_html(root)):
        rel = os.path.relpath(path, root).replace(os.sep, '/')
        here = posixpath.dirname(rel)
        with open(path, encoding='utf-8') as f:
            html = SCRIPT_RE.sub('', f.read())

        if BASE_RE.search(html):
            problems.append((rel, '<base> 태그가 있으면 옮길 때 경로가 어긋납니다'))

        for raw in ATTR_RE.findall(html):
            link = raw.strip()
            if not link or EXTERNAL_RE.match(link):
                continue
            if link.startswith('/'):
                problems.append((rel, '루트 절대경로 "%s" — 하위 폴더에 올리면 깨집니다' % link))
                continue

            target = urllib.parse.unquote(link.split('#')[0].split('?')[0])
            if not target:
                continue
            joined = posixpath.normpath(posixpath.join(here, target))
            if joined.startswith('..'):
                problems.append((rel, '"%s" 는 사이트 밖으로 나갑니다' % link))
                continue
            if not os.path.exists(os.path.join(root, joined.replace('/', os.sep))):
                problems.append((rel, '"%s" 가 가리키는 %s 가 없습니다' % (link, joined)))

    # canonical / og:url 이 설정한 주소를 쓰고 있는지 (도메인 이사 후 흔한 실수)
    if base_url:
        stale = []
        for path in sorted(_walk_html(root)):
            rel = os.path.relpath(path, root).replace(os.sep, '/')
            with open(path, encoding='utf-8') as f:
                html = SCRIPT_RE.sub('', f.read())
            for m in re.finditer(r'<link rel="canonical" href="([^"]+)"', html):
                if not m.group(1).startswith(base_url):
                    stale.append((rel, m.group(1)))
        if stale:
            problems.append((stale[0][0],
                             'canonical 이 설정한 주소(%s)와 다릅니다 — %d개 파일 (예: %s)'
                             % (base_url, len(stale), stale[0][1])))
    return problems


def report(root, base_url=None):
    problems = check(root, base_url)
    if not problems:
        return True, '경로 검사 통과 — 하위 폴더든 도메인 루트든 그대로 옮길 수 있습니다.'
    lines = ['경로 검사에서 %d건 발견:' % len(problems)]
    for rel, msg in problems[:20]:
        lines.append('    %s — %s' % (rel, msg))
    if len(problems) > 20:
        lines.append('    ... 외 %d건' % (len(problems) - 20))
    return False, '\n'.join(lines)
