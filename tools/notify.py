#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사이트가 바뀌면 슬랙으로 알려 줍니다.

    python3 tools/notify.py --test     # 시험 발송
    python3 tools/notify.py --dry-run  # 보내지 않고 무슨 내용이 갈지만 보기

PUBG META(pubgapi)의 src/notify.js 와 같은 방식입니다 — 슬랙 웹훅 주소 하나로
글을 올립니다. 계정 연동도 2단계 인증도 필요 없습니다.

  설정  data/notify.json      무엇을 보낼지 (저장소에 올라갑니다)
  비밀  data/slack.json       웹훅 주소 (저장소에 올리지 않습니다)

웹훅 주소가 없으면 예전 PUBG META 폴더의 .env 에서 찾아 옵니다. 그것도 없으면
알림만 조용히 건너뛰고 배포는 그대로 진행합니다.
"""

import argparse
import io
import json
import os
import re
import sys
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass

CONFIG = os.path.join(ROOT, 'data', 'notify.json')
SECRET = os.path.join(ROOT, 'data', 'slack.json')
STATE = os.path.join(ROOT, 'data', '.notify-state.json')

HOOK_RE = re.compile(r'https://hooks\.slack\.com/services/[A-Za-z0-9/_+-]+')
LEVEL_COLOR = {'error': '#e01e5a', 'warn': '#ecb22e',
               'ok': '#2eb67d', 'info': '#36c5f0'}
LEVEL_ICON = {'error': '🔴', 'warn': '🟡', 'ok': '🟢', 'info': '🔵'}


def _read_json(path, default=None):
    if not os.path.exists(path):
        return default
    try:
        return json.load(io.open(path, encoding='utf-8'))
    except (ValueError, OSError):
        return default


def config():
    return _read_json(CONFIG, {}) or {}


def mask(url):
    """주소가 로그에 통째로 남지 않게 뒷부분을 가립니다."""
    m = HOOK_RE.search(url or '')
    if not m:
        return '(주소 없음)'
    head = 'https://hooks.slack.com/services/'
    return head + m.group(0)[len(head):][:6] + '…(가림)'


def find_webhook():
    """웹훅 주소를 찾습니다. 한 번 찾으면 data/slack.json 에 적어 둡니다."""
    saved = _read_json(SECRET, {}) or {}
    if saved.get('webhookUrl'):
        return saved['webhookUrl']

    env = os.environ.get('SLACK_WEBHOOK_URL')
    if env:
        return env

    # 예전 PUBG META 폴더의 .env 에서 찾아 옵니다 (start.py 가 유튜브 키를
    # 찾아오는 것과 같은 방식입니다).
    home = os.path.expanduser('~')
    for folder in ('pubgapi', 'pubg-meta', 'pubgmeta'):
        path = os.path.join(home, folder, '.env')
        if not os.path.exists(path):
            continue
        try:
            text = io.open(path, encoding='utf-8', errors='ignore').read()
        except OSError:
            continue
        m = HOOK_RE.search(text)
        if m:
            os.makedirs(os.path.dirname(SECRET), exist_ok=True)
            io.open(SECRET, 'w', encoding='utf-8').write(
                json.dumps({'_note': 'PUBG META 폴더에서 찾아온 슬랙 웹훅 주소입니다.'
                                     ' 저장소에는 올라가지 않습니다.',
                            'webhookUrl': m.group(0)},
                           ensure_ascii=False, indent=1) + '\n')
            try:
                os.chmod(SECRET, 0o600)
            except OSError:
                pass
            return m.group(0)
    return None


def post_slack(url, payload):
    """슬랙에 메시지 한 건을 올립니다 — {title, level, lines, fields, link}."""
    title = payload.get('title') or '알림'
    level = payload.get('level') or 'info'
    lines = payload.get('lines') or []
    fields = payload.get('fields') or []
    link = payload.get('link')

    icon = LEVEL_ICON.get(level, '🟡')
    color = LEVEL_COLOR.get(level, '#ecb22e')
    blocks = [{'type': 'header',
               'text': {'type': 'plain_text', 'text': ('%s %s' % (icon, title))[:150],
                        'emoji': True}}]
    if lines:
        blocks.append({'type': 'section',
                       'text': {'type': 'mrkdwn', 'text': '\n'.join(lines)[:2900]}})
    for i in range(0, len(fields), 10):     # 슬랙은 한 칸에 필드 10개까지
        blocks.append({'type': 'section',
                       'fields': [{'type': 'mrkdwn',
                                   'text': ('*%s*\n%s' % (f['k'], f['v']))[:1900]}
                                  for f in fields[i:i + 10]]})
    when = datetime.now().strftime('%Y-%m-%d %H:%M')
    tail = ('<%s|사이트 열기> · %s' % (link, when)) \
        if isinstance(link, str) and link.startswith('http') else when
    blocks.append({'type': 'context',
                   'elements': [{'type': 'mrkdwn', 'text': tail}]})

    body = json.dumps({'text': '%s %s' % (icon, title),
                       'attachments': [{'color': color, 'blocks': blocks}]},
                      ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=body,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            text = r.read().decode('utf-8', 'replace').strip()
        if text != 'ok':
            return False, '슬랙 응답: %s' % text[:200]
        return True, None
    except Exception as e:
        return False, '%s: %s' % (type(e).__name__, e)


def send(payload, key=None):
    """설정을 보고 알아서 보냅니다. 못 보내도 예외를 내지 않습니다."""
    cfg = config()
    if not cfg.get('enabled', True):
        return False, '알림이 꺼져 있습니다 (data/notify.json)'
    if key and not cfg.get('alerts', {}).get(key, True):
        return False, "'%s' 알림이 꺼져 있습니다" % key

    url = find_webhook()
    if not url:
        return False, '슬랙 웹훅 주소가 없습니다'

    ok, err = post_slack(url, payload)
    if ok and key:
        st = _read_json(STATE, {}) or {}
        st[key] = datetime.now().isoformat()
        io.open(STATE, 'w', encoding='utf-8').write(
            json.dumps(st, ensure_ascii=False, indent=1) + '\n')
    return ok, err


# ── 사이트 갱신 내역 ────────────────────────────────────────────────


def _counts():
    eg = _read_json(os.path.join(ROOT, 'data', 'endgame.json'), {}) or {}
    asl = _read_json(os.path.join(ROOT, 'data', 'asl.json'), {}) or {}
    vids = _read_json(os.path.join(ROOT, 'data', 'videos.json'), {}) or {}
    return {
        'egMatches': (eg.get('global') or {}).get('totalMatches', 0),
        'egSets': (eg.get('global') or {}).get('totalSets', 0),
        'egPlayers': (eg.get('global') or {}).get('totalPlayers', 0),
        'aslMatches': (asl.get('global') or {}).get('totalMatches', 0),
        'aslSets': (asl.get('global') or {}).get('totalSets', 0),
        'videos': len(vids.get('matches') or {}),
        'lastDate': (eg.get('global') or {}).get('lastDate', ''),
    }


def _delta(now, before):
    out = []
    label = [('egMatches', '끝장전 경기'), ('egSets', '끝장전 세트'),
             ('aslMatches', 'ASL 경기'), ('aslSets', 'ASL 세트'),
             ('videos', '다시보기 영상')]
    for k, name in label:
        a, b = before.get(k), now.get(k)
        if a is None or a == b:
            continue
        out.append('· %s %s → *%s* (%s%d)'
                   % (name, format(a, ','), format(b, ','),
                      '+' if b > a else '', b - a))
    return out


def deploy_payload(uploaded=None, changed_files=None):
    """배포 뒤 보낼 내용을 만듭니다."""
    now = _counts()
    before = (_read_json(STATE, {}) or {}).get('counts') or {}
    lines = _delta(now, before)
    if not lines:
        lines = ['· 기록 수는 그대로입니다 (화면·기능만 바뀌었습니다)']
    if changed_files:
        lines.append('')
        lines.append('바뀐 파일 %d개' % changed_files)

    fields = [
        {'k': '끝장전', 'v': '%s경기 · %s세트 · 선수 %s명'
            % (format(now['egMatches'], ','), format(now['egSets'], ','),
               format(now['egPlayers'], ','))},
        {'k': 'ASL', 'v': '%s경기 · %s세트'
            % (format(now['aslMatches'], ','), format(now['aslSets'], ','))},
        {'k': '다시보기', 'v': '%d경기 연결' % now['videos']},
        {'k': '마지막 경기', 'v': now['lastDate'] or '-'},
    ]
    site = (_read_json(os.path.join(ROOT, 'data', 'site.json'), {}) or {}).get('baseUrl')
    return now, {'title': '끝장전 기록실이 갱신됐습니다', 'level': 'ok',
                 'lines': lines, 'fields': fields,
                 'link': (site or 'https://pubgin.com/endgame') + '/'}


def notify_problem(title, lines, link=None):
    """문제가 생겼을 때만 슬랙으로 알립니다 (배포 실패·오류 등).

    정상 배포에는 알림을 보내지 않기로 해서(2026-08-20), 이 경로만 씁니다.
    알림 자체가 실패해도 예외를 밖으로 던지지 않습니다.
    """
    try:
        site = (_read_json(os.path.join(ROOT, 'data', 'site.json'), {}) or {}).get('baseUrl')
        payload = {'title': title, 'level': 'error',
                   'lines': lines if isinstance(lines, list) else [str(lines)],
                   'link': link or ((site or 'https://pubgin.com/endgame') + '/')}
        ok, err = send(payload, key=None)     # 문제 알림은 중복 억제 없이 항상
        if ok:
            print('   🚨 슬랙에 문제 알림을 보냈습니다.')
        elif err and '없습니다' not in err and '꺼져' not in err:
            print('   (문제 알림 실패 — %s)' % err)
        return ok
    except Exception as e:
        print('   (문제 알림 건너뜀 — %s)' % e)
        return False


def notify_deploy(uploaded=None, changed_files=None):
    """배포가 끝난 뒤 부릅니다. 실패해도 배포에는 영향을 주지 않습니다."""
    try:
        now, payload = deploy_payload(uploaded, changed_files)
        ok, err = send(payload, key='deployed')
        if ok:
            st = _read_json(STATE, {}) or {}
            st['counts'] = now
            io.open(STATE, 'w', encoding='utf-8').write(
                json.dumps(st, ensure_ascii=False, indent=1) + '\n')
            print('   💬 슬랙 알림 보냈습니다.')
        elif err and '없습니다' not in err and '꺼져' not in err:
            print('   (슬랙 알림 실패 — %s)' % err)
        return ok
    except Exception as e:                        # 알림 때문에 배포가 깨지면 안 됩니다
        print('   (슬랙 알림 건너뜀 — %s)' % e)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--test', action='store_true', help='시험 발송')
    ap.add_argument('--dry-run', action='store_true', help='보내지 않고 내용만 보기')
    args = ap.parse_args()

    url = find_webhook()
    print('웹훅 주소: %s' % (mask(url) if url else '(못 찾았습니다)'))
    cfg = config()
    print('알림 켜짐: %s' % cfg.get('enabled', True))

    _now, payload = deploy_payload()
    if args.dry_run or not (args.test or True):
        print('')
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        return 0
    if not url:
        print('data/slack.json 에 {"webhookUrl": "https://hooks.slack.com/services/..."}'
              ' 로 넣어 주세요.')
        return 1
    payload['title'] = '시험 발송 — 끝장전 기록실'
    payload['level'] = 'info'
    ok, err = post_slack(url, payload)
    print('발송 %s%s' % ('성공' if ok else '실패', '' if ok else ' — ' + str(err)))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
