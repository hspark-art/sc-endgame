#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""끝장전 상품 추첨 관제 — 방송 PC 에서 돌리는 프로그램.

    python3 tools/prizewatch.py            # SOOP talent 채널에 붙습니다
    python3 tools/prizewatch.py --demo     # 방송 없이 가짜 채팅으로 연습

무엇을 하나요
  · SOOP 라이브 채팅에 시청자처럼 접속해 채팅·별풍선을 실시간으로 받습니다
  · 시청자마다 채팅 수·별풍선을 세어 활약도를 집계합니다
  · 당첨자 장부를 관리하고, 이미 받은 사람은 경고를 띄웁니다
  · 지명 또는 핀볼 추첨으로 당첨자를 뽑고, OBS 자막으로 내보냅니다
  · 상품(이름·사진)을 등록해 두고 골라서 줍니다

화면
  http://localhost:8144          관제 (중계진이 보는 화면)
  http://localhost:8144/overlay  자막 (OBS 브라우저 소스로 등록, 1920x1080)

기록은 전부 이 PC 에만 남습니다 — data/chat/(채팅 로그),
data/prizes/(상품·당첨자). 시청자 닉네임이 들어 있으므로 저장소와
웹서버에는 올라가지 않습니다.
"""

import argparse
import base64
import io
import json
import os
import random
import re
import sys
import threading
import time
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass

BID = 'talent'
PORT = 8144
PRIZE_DIR = os.path.join(ROOT, 'data', 'prizes')
IMG_DIR = os.path.join(PRIZE_DIR, 'img')
CHAT_DIR = os.path.join(ROOT, 'data', 'chat')

DEFAULT_SETTINGS = {
    '_note': '추첨 확률 가중치. 열심히 한 사람이 "조금" 유리하게 — 크게 차이나지 않습니다.',
    'chatFull': 50,        # 채팅 몇 개면 채팅 보너스가 꽉 차나
    'chatBonusMax': 0.3,   # 채팅 보너스 최대 (기본 1.0 에 더해짐)
    'balloonFull': 1000,   # 별풍선 몇 개면 후원 보너스가 꽉 차나
    'balloonBonusMax': 0.5,
    'excludeWinners': False,   # 켜면 이전 당첨자는 추첨에서 뺍니다
}


# ── 저장 ──────────────────────────────────────────────────────

def _read(path, default):
    if not os.path.exists(path):
        return default
    try:
        return json.load(io.open(path, encoding='utf-8'))
    except (ValueError, OSError):
        return default


def _write(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(
        json.dumps(doc, ensure_ascii=False, indent=1) + '\n')


class Store:
    """상품·당첨자·설정 + 오늘 방송의 활약 집계."""

    def __init__(self):
        self.lock = threading.Lock()
        self.prizes = _read(os.path.join(PRIZE_DIR, 'prizes.json'), {'items': []})
        self.winners = _read(os.path.join(PRIZE_DIR, 'winners.json'), {'list': []})
        self.settings = dict(DEFAULT_SETTINGS)
        self.settings.update(_read(os.path.join(PRIZE_DIR, 'settings.json'), {}))
        self.users = {}            # nick → {'id','chats','balloons','last'}
        self.recent = []           # 최근 채팅/별풍선 (관제 화면용)
        self.overlay = {'seq': 0, 'kind': 'none'}
        self.live = {'on': False, 'title': '', 'bno': ''}
        self.session = date.today().isoformat()
        self._load_today()

    # 오늘 로그가 이미 있으면(프로그램 재시작) 집계를 되살립니다.
    def _load_today(self):
        path = self._logpath()
        if not os.path.exists(path):
            return
        n = 0
        for line in io.open(path, encoding='utf-8'):
            try:
                self._count(json.loads(line))
                n += 1
            except ValueError:
                continue
        if n:
            print('  오늘 로그 %d건을 되살렸습니다.' % n)

    def _logpath(self):
        return os.path.join(CHAT_DIR, '%s.jsonl' % self.session)

    def _count(self, ev):
        t = ev.get('t')
        if t == 'chat':
            u = self.users.setdefault(ev['nick'], {
                'id': ev.get('id', ''), 'chats': 0, 'balloons': 0, 'last': ''})
            u['chats'] += 1
            u['last'] = ev.get('at', '')
        elif t == 'balloon':
            u = self.users.setdefault(ev['nick'], {
                'id': ev.get('id', ''), 'chats': 0, 'balloons': 0, 'last': ''})
            u['balloons'] += int(ev.get('count') or 0)
            u['last'] = ev.get('at', '')

    def add_event(self, ev):
        ev['at'] = datetime.now().strftime('%H:%M:%S')
        with self.lock:
            os.makedirs(CHAT_DIR, exist_ok=True)
            io.open(self._logpath(), 'a', encoding='utf-8').write(
                json.dumps(ev, ensure_ascii=False) + '\n')
            self._count(ev)
            if ev.get('t') in ('chat', 'balloon'):
                self.recent.append(ev)
                del self.recent[:-200]

    # ── 가중치와 추첨 ──
    def weight(self, nick):
        s, u = self.settings, self.users.get(nick) or {}
        w = 1.0
        w += min(1.0, (u.get('chats', 0) / max(1, s['chatFull']))) * s['chatBonusMax']
        w += min(1.0, (u.get('balloons', 0) / max(1, s['balloonFull']))) * s['balloonBonusMax']
        return round(w, 3)

    def win_count(self, nick):
        n = _norm(nick)
        hits = [w for w in self.winners['list'] if _norm(w.get('nick')) == n]
        return len(hits), (hits[-1].get('date') if hits else '')

    def pick(self):
        """가중치 추첨. (당첨 닉, 후보 목록[핀볼 슬롯용]) 을 돌려줍니다."""
        pool = [n for n, u in self.users.items() if u['chats'] + u['balloons'] > 0]
        if self.settings.get('excludeWinners'):
            pool = [n for n in pool if self.win_count(n)[0] == 0]
        if not pool:
            return None, []
        weights = [self.weight(n) for n in pool]
        win = random.choices(pool, weights=weights, k=1)[0]
        others = [n for n in pool if n != win]
        random.shuffle(others)
        slots = others[:8] + [win]
        random.shuffle(slots)
        return win, slots


def _norm(s):
    return re.sub(r'\s+', '', str(s or '')).lower()


S = Store()


# ── 채팅 수집 ─────────────────────────────────────────────────

def collector(demo=False):
    if demo:
        return _demo_loop()
    import soopchat
    while True:
        try:
            info = soopchat.live_info(BID)
        except Exception as e:
            print('  ! 방송 정보를 못 가져왔습니다:', e)
            time.sleep(20)
            continue
        if str(info.get('RESULT')) != '1':
            S.live.update({'on': False, 'title': ''})
            time.sleep(20)
            continue
        S.live.update({'on': True, 'title': info.get('TITLE') or '',
                       'bno': str(info.get('BNO') or '')})
        print('  방송 감지 — %s' % S.live['title'])
        try:
            soopchat.listen(BID, info, S.add_event)
        except Exception as e:
            print('  ! 채팅 연결이 끊겼습니다:', e, '— 10초 뒤 다시 붙습니다')
        time.sleep(10)


_DEMO_NICKS = ['별사탕요정', '테란만세', '저글링1000', '프로브혁명', '캐리어가요',
               'GG치지마', '빌드깎는노인', '더블넥좋아', '뮤탈짤짤이', '벙커링장인',
               '스캔없는테란', '럴커밭사랑', '아비터신봉자', '패스트닥템', '커세어한부대']


def _demo_loop():
    """방송 없이 연습할 수 있게 가짜 채팅·별풍선을 만들어 냅니다."""
    S.live.update({'on': True, 'title': '(연습) 스타 끝장전', 'bno': 'demo'})
    msgs = ['ㅋㅋㅋㅋㅋ', '이걸 막네', '별풍 갑니다~', '오늘 폼 미쳤다',
            '9세트 가자', 'GG', '역전각', '드라군 컨 무엇', '지리네요', '캬']
    while True:
        n = random.choice(_DEMO_NICKS)
        if random.random() < 0.12:
            S.add_event({'t': 'balloon', 'id': 'demo_' + n, 'nick': n,
                         'count': random.choice([1, 5, 10, 50, 100, 500])})
        else:
            S.add_event({'t': 'chat', 'id': 'demo_' + n, 'nick': n,
                         'msg': random.choice(msgs)})
        time.sleep(random.uniform(0.2, 1.1))


# ── HTTP ─────────────────────────────────────────────────────

def _state():
    with S.lock:
        rows = []
        for nick, u in S.users.items():
            wins, last = S.win_count(nick)
            rows.append({'nick': nick, 'chats': u['chats'],
                         'balloons': u['balloons'], 'w': S.weight(nick),
                         'wins': wins, 'lastWin': last})
        rows.sort(key=lambda r: (-r['balloons'], -r['chats']))
        return {
            'live': S.live, 'session': S.session,
            'users': rows[:200],
            'totalUsers': len(rows),
            'totalChats': sum(u['chats'] for u in S.users.values()),
            'totalBalloons': sum(u['balloons'] for u in S.users.values()),
            'recent': S.recent[-60:],
            'prizes': S.prizes['items'],
            'winners': S.winners['list'][-300:],
            'settings': {k: v for k, v in S.settings.items() if not k.startswith('_')},
            'overlay': S.overlay,
        }


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):                    # 조용히
        pass

    def _json(self, doc, code=200):
        body = json.dumps(doc, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, text):
        body = text.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = self.path.split('?')[0]
        if p == '/':
            return self._html(PAGE_CONTROL)
        if p == '/overlay':
            return self._html(PAGE_OVERLAY)
        if p == '/api/state':
            return self._json(_state())
        if p == '/api/overlay':
            return self._json(S.overlay)
        if p.startswith('/img/'):
            f = os.path.join(IMG_DIR, os.path.basename(p))
            if os.path.exists(f):
                body = open(f, 'rb').read()
                self.send_response(200)
                self.send_header('Content-Type', 'image/webp')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                return self.wfile.write(body)
        self._json({'error': 'not found'}, 404)

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        try:
            body = json.loads(self.rfile.read(n).decode('utf-8')) if n else {}
        except ValueError:
            return self._json({'error': 'bad json'}, 400)
        p = self.path

        if p == '/api/pick':                       # 지명 or 핀볼 결과 확정
            nick = (body.get('nick') or '').strip()
            prize = next((x for x in S.prizes['items']
                          if x['id'] == body.get('prizeId')), None)
            if not nick:
                return self._json({'error': '닉네임이 없습니다'}, 400)
            rec = {'date': S.session, 'nick': nick,
                   'prize': (prize or {}).get('name', body.get('prizeName') or ''),
                   'how': body.get('how') or '지명',
                   'at': datetime.now().strftime('%H:%M')}
            with S.lock:
                S.winners['list'].append(rec)
                _write(os.path.join(PRIZE_DIR, 'winners.json'), S.winners)
                S.overlay = {'seq': S.overlay['seq'] + 1, 'kind': 'winner',
                             'nick': nick, 'prize': rec['prize'],
                             'photo': (prize or {}).get('photo', ''),
                             'how': rec['how']}
            return self._json({'ok': True, 'record': rec})

        if p == '/api/plinko':                     # 추첨 + 핀볼 연출 시작
            win, slots = S.pick()
            if not win:
                return self._json({'error': '추첨할 시청자가 없습니다'}, 400)
            prize = next((x for x in S.prizes['items']
                          if x['id'] == body.get('prizeId')), None)
            prev_wins = S.win_count(win)[0]
            # 장부 기록은 여기서 바로 합니다 — 자막 화면(OBS)이 꺼져 있어도
            # 당첨은 남아야 하기 때문입니다. 자막은 연출만 맡습니다.
            rec = {'date': S.session, 'nick': win,
                   'prize': (prize or {}).get('name', ''), 'how': '핀볼',
                   'at': datetime.now().strftime('%H:%M')}
            with S.lock:
                S.winners['list'].append(rec)
                _write(os.path.join(PRIZE_DIR, 'winners.json'), S.winners)
                S.overlay = {'seq': S.overlay['seq'] + 1, 'kind': 'plinko',
                             'winner': win, 'slots': slots,
                             'prize': (prize or {}).get('name', ''),
                             'photo': (prize or {}).get('photo', '')}
            return self._json({'ok': True, 'winner': win, 'slots': slots,
                               'wins': prev_wins})

        if p == '/api/overlay/clear':
            with S.lock:
                S.overlay = {'seq': S.overlay['seq'] + 1, 'kind': 'none'}
            return self._json({'ok': True})

        if p == '/api/prize/add':
            name = (body.get('name') or '').strip()
            if not name:
                return self._json({'error': '상품 이름이 없습니다'}, 400)
            pid = 'p%d' % int(time.time() * 1000)
            photo = ''
            if body.get('photo'):                  # dataURL 로 온 사진
                try:
                    head, b64 = body['photo'].split(',', 1)
                    ext = 'png' if 'png' in head else ('webp' if 'webp' in head else 'jpg')
                    os.makedirs(IMG_DIR, exist_ok=True)
                    fn = '%s.%s' % (pid, ext)
                    open(os.path.join(IMG_DIR, fn), 'wb').write(base64.b64decode(b64))
                    photo = '/img/' + fn
                except Exception:
                    photo = ''
            with S.lock:
                S.prizes['items'].append({'id': pid, 'name': name,
                                          'note': body.get('note') or '',
                                          'photo': photo})
                _write(os.path.join(PRIZE_DIR, 'prizes.json'), S.prizes)
            return self._json({'ok': True})

        if p == '/api/prize/del':
            with S.lock:
                S.prizes['items'] = [x for x in S.prizes['items']
                                     if x['id'] != body.get('id')]
                _write(os.path.join(PRIZE_DIR, 'prizes.json'), S.prizes)
            return self._json({'ok': True})

        if p == '/api/winner/add':                 # 지난 기록을 손으로 넣을 때
            rec = {'date': body.get('date') or S.session,
                   'nick': (body.get('nick') or '').strip(),
                   'prize': body.get('prize') or '', 'how': '기록', 'at': ''}
            if not rec['nick']:
                return self._json({'error': '닉네임이 없습니다'}, 400)
            with S.lock:
                S.winners['list'].append(rec)
                S.winners['list'].sort(key=lambda w: w.get('date') or '')
                _write(os.path.join(PRIZE_DIR, 'winners.json'), S.winners)
            return self._json({'ok': True})

        if p == '/api/winner/del':
            i = body.get('i')
            with S.lock:
                if isinstance(i, int) and 0 <= i < len(S.winners['list']):
                    S.winners['list'].pop(i)
                    _write(os.path.join(PRIZE_DIR, 'winners.json'), S.winners)
            return self._json({'ok': True})

        if p == '/api/settings':
            with S.lock:
                for k in ('chatFull', 'chatBonusMax', 'balloonFull',
                          'balloonBonusMax', 'excludeWinners'):
                    if k in body:
                        S.settings[k] = body[k]
                _write(os.path.join(PRIZE_DIR, 'settings.json'), S.settings)
            return self._json({'ok': True})

        self._json({'error': 'not found'}, 404)


# ── 화면 ─────────────────────────────────────────────────────

CSS = """
*{box-sizing:border-box}body{margin:0;background:#0a0d13;color:#e8ecf3;
font-family:'Pretendard','Malgun Gothic',sans-serif;font-size:14px}
.wrap{max-width:1500px;margin:0 auto;padding:14px}
h1{font-size:18px;margin:4px 0 12px}.grid{display:grid;gap:12px;
grid-template-columns:1.1fr .9fr 1fr}.card{background:#141821;
border:1px solid #232a38;border-radius:12px;padding:12px;min-width:0}
.ct{font-weight:800;margin-bottom:8px;display:flex;gap:8px;align-items:center}
.ct .n{color:#8a93a6;font-weight:500;font-size:11.5px}
.scroll{overflow-y:auto;max-height:520px}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{padding:5px 7px;text-align:left;border-bottom:1px solid #171c25;
white-space:nowrap}th{color:#8a93a6;font-size:11px}
.num{text-align:right;font-variant-numeric:tabular-nums}
.chatline{padding:3px 0;border-bottom:1px solid #12161e;font-size:13px}
.chatline b{color:#7cb6ff;font-weight:600}.balloon{color:#ffb020;font-weight:700}
button{background:#1c8cff;border:0;color:#fff;border-radius:8px;
padding:8px 13px;font-weight:700;cursor:pointer;font-family:inherit}
button.gray{background:#232a38}button.red{background:#e0392b}
button:disabled{opacity:.4}
input,select{background:#1b202b;color:#e8ecf3;border:1px solid #232a38;
border-radius:8px;padding:7px 9px;font-family:inherit;font-size:13px}
.row{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin:6px 0}
.warn{color:#ffb020;font-weight:700}.ok{color:#4ade80}
.pill{background:#1b202b;border:1px solid #232a38;border-radius:999px;
padding:2px 9px;font-size:11.5px;color:#8a93a6}
.live{color:#ff4d5a;font-weight:900}
img.thumb{width:44px;height:44px;object-fit:cover;border-radius:8px;
vertical-align:middle;margin-right:6px;background:#0a0d13}
.hint{color:#8a93a6;font-size:11.5px;line-height:1.6;margin-top:6px}
"""

PAGE_CONTROL = """<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<title>끝장전 상품 추첨 관제</title><style>%s</style></head><body><div class="wrap">
<h1>🎁 끝장전 상품 추첨 관제 <span id="liveflag" class="pill">…</span>
<span class="n" style="font-weight:500;font-size:12px;color:#8a93a6">
자막(OBS): http://localhost:8144/overlay</span></h1>
<div class="grid">

<div class="card"><div class="ct">실시간 채팅 <span class="n" id="totline"></span></div>
<div class="scroll" id="chat" style="max-height:560px"></div></div>

<div class="card"><div class="ct">시청자 활약 <span class="n">별풍선·채팅 순</span></div>
<div class="scroll"><table id="users"><thead><tr><th>닉네임</th>
<th class="num">채팅</th><th class="num">별풍선</th><th class="num">확률↑</th>
<th>당첨</th><th></th></tr></thead><tbody></tbody></table></div></div>

<div class="card">
<div class="ct">당첨 만들기</div>
<div class="row"><input id="pickNick" placeholder="닉네임 (지명)" style="flex:1">
<select id="prizeSel" style="flex:1"></select></div>
<div id="dupwarn" class="hint"></div>
<div class="row">
<button onclick="manualPick()">지명 → 자막 내보내기</button>
<button class="gray" onclick="plinko()">🎯 핀볼 추첨</button>
<button class="gray" onclick="post('/api/overlay/clear',{})">자막 지우기</button></div>
<div class="hint">핀볼 추첨은 자막 화면에서 공이 떨어지는 연출과 함께 나옵니다.
확률은 채팅·별풍선에 따라 조금만 올라갑니다 (아래 설정).</div>
<hr style="border-color:#232a38">
<div class="ct">상품 <span class="n">사진은 클릭해서 등록</span></div>
<div id="prizes"></div>
<div class="row"><input id="pName" placeholder="상품 이름" style="flex:1">
<input type="file" id="pPhoto" accept="image/*" style="display:none">
<button class="gray" onclick="document.getElementById('pPhoto').click()">사진</button>
<button onclick="addPrize()">추가</button></div>
<span id="pPhotoName" class="hint"></span>
<hr style="border-color:#232a38">
<div class="ct">당첨자 장부 <span class="n" id="wcount"></span></div>
<div class="scroll" style="max-height:220px"><table id="winners"><tbody></tbody></table></div>
<div class="row"><input id="wDate" placeholder="날짜 2026-08-13" style="width:110px">
<input id="wNick" placeholder="닉네임" style="flex:1">
<input id="wPrize" placeholder="상품" style="flex:1">
<button class="gray" onclick="addWinner()">지난 기록 넣기</button></div>
<hr style="border-color:#232a38">
<div class="ct">확률 설정</div>
<div class="row hint">채팅 <input id="sChatFull" style="width:56px"> 개에
+<input id="sChatMax" style="width:50px"> · 별풍선
<input id="sBalFull" style="width:64px"> 개에 +<input id="sBalMax" style="width:50px">
<label><input type="checkbox" id="sExcl"> 이전 당첨자 제외</label>
<button class="gray" onclick="saveSettings()">저장</button></div>
</div>

</div></div>
<script>
let photoData = '';
document.getElementById('pPhoto').addEventListener('change', e => {
  const f = e.target.files[0]; if (!f) return;
  const r = new FileReader();
  r.onload = () => { photoData = r.result;
    document.getElementById('pPhotoName').textContent = '사진: ' + f.name; };
  r.readAsDataURL(f);
});
async function post(u, b) { const r = await fetch(u, {method:'POST',
  headers:{'Content-Type':'application/json'}, body: JSON.stringify(b)});
  const j = await r.json(); if (j.error) alert(j.error); return j; }
function esc(s){return String(s??'').replace(/[&<>"]/g,
  c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
async function manualPick() {
  const nick = document.getElementById('pickNick').value.trim();
  if (!nick) return alert('닉네임을 넣어 주세요');
  await post('/api/pick', {nick, prizeId: document.getElementById('prizeSel').value, how:'지명'});
}
async function plinko() {
  await post('/api/plinko', {prizeId: document.getElementById('prizeSel').value});
}
async function addPrize() {
  const name = document.getElementById('pName').value.trim();
  if (!name) return alert('상품 이름을 넣어 주세요');
  await post('/api/prize/add', {name, photo: photoData});
  photoData=''; document.getElementById('pName').value='';
  document.getElementById('pPhotoName').textContent='';
}
async function addWinner() {
  await post('/api/winner/add', {date: document.getElementById('wDate').value.trim(),
    nick: document.getElementById('wNick').value.trim(),
    prize: document.getElementById('wPrize').value.trim()});
  document.getElementById('wNick').value='';
}
async function saveSettings() {
  await post('/api/settings', {
    chatFull:+document.getElementById('sChatFull').value||50,
    chatBonusMax:+document.getElementById('sChatMax').value||0.3,
    balloonFull:+document.getElementById('sBalFull').value||1000,
    balloonBonusMax:+document.getElementById('sBalMax').value||0.5,
    excludeWinners:document.getElementById('sExcl').checked});
}
function pickThis(n){ document.getElementById('pickNick').value=n; dupCheck(); }
let ST=null;
function dupCheck(){
  if(!ST) return;
  const n=document.getElementById('pickNick').value.trim().replace(/\\s+/g,'').toLowerCase();
  const hits=ST.winners.filter(w=>String(w.nick||'').replace(/\\s+/g,'').toLowerCase()===n);
  const el=document.getElementById('dupwarn');
  el.innerHTML = !n?'' : hits.length
    ? '<span class="warn">⚠ 이미 '+hits.length+'회 당첨 (마지막 '+esc(hits[hits.length-1].date)+' · '+esc(hits[hits.length-1].prize)+')</span>'
    : '<span class="ok">✓ 당첨 기록 없음</span>';
}
document.getElementById('pickNick').addEventListener('input', dupCheck);
async function tick() {
  try {
    const st = await (await fetch('/api/state')).json(); ST=st;
    document.getElementById('liveflag').innerHTML = st.live.on
      ? '<span class="live">● LIVE</span> ' + esc(st.live.title) : '방송 대기 중';
    document.getElementById('totline').textContent =
      '시청자 ' + st.totalUsers + ' · 채팅 ' + st.totalChats + ' · 별풍선 ' + st.totalBalloons;
    document.getElementById('chat').innerHTML = st.recent.slice().reverse().map(e =>
      e.t === 'balloon'
      ? '<div class="chatline">🎈 <b>' + esc(e.nick) + '</b> <span class="balloon">별풍선 ' + e.count + '개</span> <span class="pill">' + e.at + '</span></div>'
      : '<div class="chatline"><b>' + esc(e.nick) + '</b> ' + esc(e.msg) + '</div>').join('');
    document.querySelector('#users tbody').innerHTML = st.users.map(u =>
      '<tr><td>' + esc(u.nick) + '</td><td class="num">' + u.chats +
      '</td><td class="num balloon">' + (u.balloons||'') + '</td><td class="num">x' + u.w.toFixed(2) +
      '</td><td>' + (u.wins ? '<span class="warn">' + u.wins + '회</span>' : '') +
      '</td><td><button class="gray" style="padding:2px 8px" onclick="pickThis(\\'' +
      esc(u.nick).replace(/'/g,"\\\\'") + '\\')">지명</button></td></tr>').join('');
    const sel = document.getElementById('prizeSel');
    const cur = sel.value;
    sel.innerHTML = '<option value="">상품 없이</option>' + st.prizes.map(x =>
      '<option value="' + x.id + '">' + esc(x.name) + '</option>').join('');
    if ([...sel.options].some(o=>o.value===cur)) sel.value = cur;
    document.getElementById('prizes').innerHTML = st.prizes.map(x =>
      '<div class="row">' + (x.photo ? '<img class="thumb" src="' + x.photo + '">' : '') +
      '<span style="flex:1">' + esc(x.name) + '</span>' +
      '<button class="red" style="padding:3px 9px" onclick="post(\\'/api/prize/del\\',{id:\\'' + x.id + '\\'})">지우기</button></div>').join('')
      || '<div class="hint">아직 상품이 없습니다. 아래에서 추가하세요.</div>';
    document.getElementById('wcount').textContent = st.winners.length + '건';
    document.getElementById('winners').innerHTML = '<tbody>' +
      st.winners.slice().reverse().map((w,ri) =>
      '<tr><td>' + esc(w.date) + '</td><td><b>' + esc(w.nick) + '</b></td><td>' +
      esc(w.prize) + '</td><td class="pill">' + esc(w.how||'') + '</td>' +
      '<td><button class="red" style="padding:1px 7px" onclick="post(\\'/api/winner/del\\',{i:' +
      (st.winners.length-1-ri) + '})">×</button></td></tr>').join('') + '</tbody>';
    const s = st.settings;
    for (const [id,v] of [['sChatFull',s.chatFull],['sChatMax',s.chatBonusMax],
      ['sBalFull',s.balloonFull],['sBalMax',s.balloonBonusMax]]) {
      const el = document.getElementById(id);
      if (document.activeElement !== el) el.value = v;
    }
    document.getElementById('sExcl').checked = !!s.excludeWinners;
  } catch (e) {}
  setTimeout(tick, 1500);
}
tick();
</script></body></html>""" % CSS

PAGE_OVERLAY = """<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<title>당첨 자막</title><style>
*{box-sizing:border-box}html,body{margin:0;width:1920px;height:1080px;
background:transparent;overflow:hidden;font-family:'Pretendard','Malgun Gothic',sans-serif}
#banner{position:absolute;left:50%;bottom:64px;transform:translateX(-50%) scale(0);
display:flex;align-items:center;gap:26px;padding:26px 44px;border-radius:22px;
background:linear-gradient(135deg,rgba(12,16,26,.94),rgba(20,26,40,.94));
border:3px solid #ffc63d;box-shadow:0 18px 60px rgba(0,0,0,.6);
transition:transform .45s cubic-bezier(.2,1.6,.4,1)}
#banner.show{transform:translateX(-50%) scale(1)}
#banner img{width:130px;height:130px;object-fit:cover;border-radius:16px}
#banner .cap{color:#ffc63d;font-weight:900;font-size:30px;letter-spacing:.14em}
#banner .nick{color:#fff;font-weight:900;font-size:62px;line-height:1.15}
#banner .prize{color:#cdd6e4;font-weight:700;font-size:34px}
#board{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);display:none}
#board.show{display:block}
</style></head><body>
<div id="banner"><img id="bimg" hidden>
<div><div class="cap" id="bcap">🎁 상품 당첨</div>
<div class="nick" id="bnick"></div><div class="prize" id="bprize"></div></div></div>
<canvas id="board" width="1200" height="860"></canvas>
<script>
let seq = -1, anim = null;
const cv = document.getElementById('board'), cx = cv.getContext('2d');
function showBanner(nick, prize, photo, cap) {
  const b = document.getElementById('banner');
  document.getElementById('bnick').textContent = nick;
  document.getElementById('bprize').textContent = prize || '';
  document.getElementById('bcap').textContent = cap || '🎁 상품 당첨';
  const im = document.getElementById('bimg');
  if (photo) { im.src = photo; im.hidden = false; } else im.hidden = true;
  b.classList.add('show');
}
function hideAll() {
  document.getElementById('banner').classList.remove('show');
  cv.classList.remove('show');
  if (anim) { cancelAnimationFrame(anim); anim = null; }
}
/* 핀볼: 못을 맞고 떨어져 당첨 칸에 들어가는 연출.
   공정성을 위해 당첨자는 서버가 가중치로 미리 뽑고, 공은 그 칸으로
   떨어지도록 경로를 계산합니다. */
function plinko(st) {
  const slots = st.slots, winIdx = slots.indexOf(st.winner);
  const ROWS = 9, T = 210;
  const slotW = cv.width / slots.length;
  // 위에서 아래로 각 줄에서 왼/오를 정해 마지막에 당첨 칸에 오게 합니다.
  let col = Math.floor(slots.length / 2), path = [];
  const target = winIdx;
  for (let r = 0; r < ROWS; r++) {
    const remain = ROWS - r;
    const diff = target - col;
    let step;
    if (Math.abs(diff) >= remain) step = Math.sign(diff);
    else step = Math.random() < 0.5 + diff * 0.18 ? 1 : -1;
    col = Math.max(0, Math.min(slots.length - 1, col + step));
    path.push(col);
  }
  path[ROWS - 1] = target;
  let t0 = null;
  cv.classList.add('show');
  function frame(ts) {
    if (!t0) t0 = ts;
    const el = ts - t0, total = ROWS * T + 700;
    cx.clearRect(0, 0, cv.width, cv.height);
    // 판
    cx.fillStyle = 'rgba(10,13,20,.88)';
    cx.beginPath(); cx.roundRect(0, 0, cv.width, cv.height, 26); cx.fill();
    cx.strokeStyle = '#ffc63d'; cx.lineWidth = 4; cx.stroke();
    cx.fillStyle = '#ffc63d'; cx.font = '900 40px Pretendard';
    cx.textAlign = 'center';
    cx.fillText('🎯 행운의 핀볼 추첨' + (0 ? '' : ''), cv.width/2, 62);
    // 못
    cx.fillStyle = '#8a93a6';
    for (let r = 0; r < ROWS; r++)
      for (let c = 0; c <= slots.length; c++) {
        const px = c * slotW + (r % 2 ? slotW / 2 : 0);
        if (px > 10 && px < cv.width - 10)
          cx.beginPath(), cx.arc(px, 130 + r * 64, 5, 0, 7), cx.fill();
      }
    // 칸
    slots.forEach((s2, i2) => {
      const hl = el > total - 500 && i2 === winIdx;
      cx.fillStyle = hl ? '#ffc63d' : 'rgba(27,32,43,.9)';
      cx.beginPath();
      cx.roundRect(i2 * slotW + 5, cv.height - 96, slotW - 10, 86, 10); cx.fill();
      cx.fillStyle = hl ? '#0b0d11' : '#e8ecf3';
      cx.font = (hl ? '900 ' : '700 ') + Math.min(26, 300/Math.max(4,s2.length)+10) + 'px Pretendard';
      cx.fillText(s2, i2 * slotW + slotW/2, cv.height - 44);
    });
    // 공
    const step = Math.min(ROWS - 1, Math.floor(el / T));
    const f = Math.min(1, (el - step * T) / T);
    const c0 = step ? path[step - 1] : Math.floor(slots.length / 2);
    const c1 = path[step];
    const bx = (c0 + (c1 - c0) * f + 0.5) * slotW;
    const by = 96 + step * 64 + f * 64 + Math.sin(f * 3.14) * -26;
    const doneY = cv.height - 120;
    const yy = el > ROWS * T ? Math.min(doneY, 96 + ROWS * 64 + (el - ROWS*T) * .9) : by;
    cx.fillStyle = '#ff4d5a';
    cx.beginPath(); cx.arc(el > ROWS*T ? (path[ROWS-1]+0.5)*slotW : bx, yy, 17, 0, 7); cx.fill();
    if (el < total) anim = requestAnimationFrame(frame);
    else {
      cv.classList.remove('show');
      showBanner(st.winner, st.prize, st.photo, '🎯 핀볼 추첨 당첨');
    }
  }
  anim = requestAnimationFrame(frame);
}
async function poll() {
  try {
    const st = await (await fetch('/api/overlay')).json();
    if (st.seq !== seq) {
      seq = st.seq;
      hideAll();
      if (st.kind === 'winner') showBanner(st.nick, st.prize, st.photo,
        st.how === '핀볼' ? '🎯 핀볼 추첨 당첨' : '🎁 상품 당첨');
      else if (st.kind === 'plinko') plinko(st);
    }
  } catch (e) {}
  setTimeout(poll, 900);
}
poll();
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--demo', action='store_true', help='방송 없이 가짜 채팅으로 연습')
    ap.add_argument('--port', type=int, default=PORT)
    args = ap.parse_args()

    threading.Thread(target=collector, args=(args.demo,), daemon=True).start()
    srv = ThreadingHTTPServer(('127.0.0.1', args.port), H)
    print('=' * 56)
    print(' 끝장전 상품 추첨 관제%s' % (' (연습 모드)' if args.demo else ''))
    print('   관제 화면   http://localhost:%d' % args.port)
    print('   OBS 자막    http://localhost:%d/overlay  (1920x1080)' % args.port)
    print('   끝내려면 이 창을 닫으세요.')
    print('=' * 56)
    srv.serve_forever()


if __name__ == '__main__':
    main()
