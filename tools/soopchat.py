#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SOOP(숲) 라이브 채팅 리더.

방송국(예: talent)의 라이브 채팅 서버에 시청자처럼 접속해서
채팅·별풍선·입장 같은 사건을 받아옵니다. 로그인 없이 됩니다.

쓰는 법
    import soopchat
    info = soopchat.live_info('talent')      # 방송 중인지, 채팅 서버 주소
    soopchat.listen('talent', info, on_event)  # 끊길 때까지 사건을 콜백으로

사건(dict)
    {'t': 'chat',    'id': 유저ID, 'nick': 닉네임, 'msg': 내용}
    {'t': 'balloon', 'id': 유저ID, 'nick': 닉네임, 'count': 개수}
    {'t': 'join',    'nicks': [닉네임...]}      # 입장/퇴장 묶음
    {'t': 'raw',     'svc': 번호, 'fields': [...]}  # 아직 해석 안 한 것

주의: 별풍선(svc 18) 칸 배치는 서버가 예고 없이 바꿀 수 있습니다.
해석에 실패해도 'raw' 로 그대로 남기므로, 첫 방송 로그를 보고
_parse_balloon 의 칸 번호만 맞춰 주면 됩니다.
"""

import json
import ssl
import urllib.parse
import urllib.request

ESC = b'\x1b\t'
F = '\x0c'                                   # 칸 나누개

SVC_PING, SVC_CONNECT, SVC_JOIN = 0, 1, 2
SVC_USERLIST, SVC_CHAT = 4, 5
SVC_BALLOON = 18                             # SVC_SENDBALLOON — 별풍선 (SOOP 공식 상수)
SVC_BALLOON_SUB = 33                         # SVC_SENDBALLOONSUB — 중계방 별풍선
SVC_OGQ = 109                                # SVC_OGQ_EMOTICON — 이모티콘 스티커 (별풍선 아님)


def live_info(bid):
    """방송 정보. RESULT 가 1 이면 방송 중입니다."""
    url = 'https://live.sooplive.com/afreeca/player_live_api.php?bjid=' + bid
    data = urllib.parse.urlencode({
        'bid': bid, 'type': 'live', 'confirm_adult': 'false',
        'player_type': 'html5', 'mode': 'landing', 'from_api': '0',
        'pwd': '', 'stream_type': 'common', 'quality': 'HD'}).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={'User-Agent': 'Mozilla/5.0'})
    j = json.loads(urllib.request.urlopen(req, timeout=15).read().decode('utf-8'))
    return j.get('CHANNEL', {})


def _pkt(svc, body):
    b = body.encode('utf-8')
    return ESC + ('%04d%06d00' % (svc, len(b))).encode() + b


def _fields(frame):
    """받은 프레임 → (svc, 칸 목록). 형식이 다르면 (None, [])."""
    if not frame or not frame.startswith(ESC) or len(frame) < 14:
        return None, []
    try:
        svc = int(frame[2:6])
    except ValueError:
        return None, []
    payload = frame[14:].decode('utf-8', 'replace')
    return svc, payload.split(F)


def _clean_nick(s):
    """닉네임 칸에 붙는 (1) 같은 꼬리표를 뗍니다."""
    s = (s or '').strip()
    if s.endswith(')') and '(' in s:
        s = s[:s.rfind('(')]
    return s.strip()


def _parse_balloon(fields, svc=SVC_BALLOON):
    """별풍선 해석 — SOOP 플레이어 공식 레이아웃 (LivePlayer.js 에서 확인).
      svc 18: [1]채널 [2]보낸이ID [3]닉 [4]개수 [8]시그니처 이미지 파일명
      svc 33: [2]채널 [4]보낸이ID [5]닉 [6]개수 (중계방)
    svc 109(OGQ 이모티콘)는 별풍선이 아니므로 여기서 다루지 않습니다.
    닉==ID 시청자도 진짜 별풍선입니다 (공식 파서에 제외 규칙 없음)."""
    if svc == SVC_BALLOON_SUB:
        ci, ui, ni, cc = 2, 4, 5, 6
    else:
        ci, ui, ni, cc = 1, 2, 3, 4
    if len(fields) <= cc:
        return None
    c = fields[cc].strip()
    if not (c.isdigit() and int(c) > 0):
        return None
    nick = _clean_nick(fields[ni])
    uid = _clean_nick(fields[ui])
    if not nick or not uid:
        return None
    return {'t': 'balloon', 'id': uid, 'nick': nick, 'count': int(c),
            'ch': (fields[ci] or '').strip().lower()}


def listen(bid, info, on_event, should_stop=None):
    """채팅 서버에 붙어 사건을 콜백으로 넘깁니다. 끊기면 돌아옵니다."""
    import websocket                          # websocket-client

    dom, pt = info.get('CHDOMAIN'), info.get('CHPT')
    chatno = str(info.get('CHATNO') or '')
    if not (dom and pt and chatno):
        raise RuntimeError('채팅 서버 정보가 없습니다 (방송 전?)')

    ws = websocket.WebSocket(sslopt={'cert_reqs': ssl.CERT_NONE})
    ws.connect('wss://%s:%d/Websocket/%s' % (dom, int(pt) + 1, bid),
               subprotocols=['chat'],
               header=['User-Agent: Mozilla/5.0'],
               timeout=30)
    ws.send_binary(_pkt(SVC_CONNECT, F + F + F + '16' + F))
    ws.recv()                                 # 접속 응답
    ws.send_binary(_pkt(SVC_JOIN, F + chatno + F + F + F + F))

    import time as _t
    seen_balloons = {}                       # (종류|보낸사람|개수) -> 마지막 시각
    BAL_WINDOW = 8.0                         # 초 — 같은 것이 이 안에 다시 오면 재전송
    last_ping = _t.time()
    while True:
        if should_stop and should_stop():
            break
        if _t.time() - last_ping > 55:        # 1분 넘게 조용하면 끊겨서
            ws.send_binary(_pkt(SVC_PING, F))
            last_ping = _t.time()
        try:
            frame = ws.recv()
        except websocket.WebSocketTimeoutException:
            continue
        if isinstance(frame, str):
            frame = frame.encode('utf-8', 'replace')
        svc, fields = _fields(frame)
        if svc is None:
            continue
        if svc == SVC_CHAT and len(fields) > 6:
            ev = {'t': 'chat', 'id': _clean_nick(fields[2]),
                  'nick': _clean_nick(fields[6]), 'msg': fields[1]}
            if ev['nick']:
                on_event(ev)
        elif svc in (SVC_BALLOON, SVC_BALLOON_SUB):
            ev = _parse_balloon(fields, svc)
            if ev and ev.pop('ch', '') not in ('', bid.lower()):
                ev = None                     # 다른 채널로 간 선물
            if ev:
                key = '%s|%s' % (ev['id'], ev['count'])
                now = _t.time()
                last = seen_balloons.get(key)
                seen_balloons[key] = now
                if last is not None and now - last < BAL_WINDOW:
                    continue                 # 재전송 — 건너뜁니다
                if len(seen_balloons) > 5000:   # 긴 방송에서 메모리 방지
                    seen_balloons = {k: v for k, v in seen_balloons.items()
                                     if now - v < BAL_WINDOW}
                on_event(ev)
        elif svc == SVC_OGQ:
            pass                              # OGQ 이모티콘 — 별풍선 아님
        elif svc == SVC_USERLIST:
            nicks = [_clean_nick(x) for x in fields if x and not x.isdigit()]
            on_event({'t': 'join', 'nicks': [n for n in nicks if n][:20]})
        elif svc not in (SVC_PING, SVC_CONNECT, SVC_JOIN):
            on_event({'t': 'raw', 'svc': svc, 'fields': fields[:12]})
    try:
        ws.close()
    except Exception:
        pass
