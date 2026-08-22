#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""채팅·별풍선 파서 라이브 점검 — 아무 방송에나 잠깐 붙어 정확도를 봅니다.

공식 프로토콜 파서(soopchat)가 실제 방송에서 제대로 도는지 확인용입니다.
  · 채팅(svc5): 빈 닉·깨진 글자·계정 누락 비율
  · 별풍선(svc18/33): 몇 명이 몇 개 (표본), 재전송 중복제거 동작
  · OGQ 이모티콘(svc109): 별풍선으로 안 세는지 (개수만 참고 표시)
  · 그 밖에 들어온 svc 코드 전부 (처음 보는 게 있으면 표시)

  python3 tools/chat_probe.py <채널아이디> [초]
  예) python3 tools/chat_probe.py talent 120
"""
import sys, time, ssl, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soopchat

ESC = b'\x1b\t'; F = '\x0c'
# SOOP 플레이어 공식 상수 기준 (LivePlayer.js). 선물이 아닌 제어 이벤트도 포함.
KNOWN_LABEL = {5: '채팅', 18: '별풍선', 33: '별풍선(중계)', 109: 'OGQ이모티콘',
               87: '애드벌룬', 105: '영상풍선', 37: '초콜릿', 38: '초콜릿SUB',
               108: '구독', 121: '미션', 125: '미션정산', 20: '팬레터', 34: '팬레터SUB',
               30: '팬순위', 35: '팬순위SUB', 39: '클랜순위', 41: '슈퍼챗',
               0: 'ping', 1: 'connect', 2: 'join', 3: '방송종료', 4: '유저목록',
               6: '채널명', 7: '채널정보', 8: '유저수', 10: '공지', 11: '아이템',
               12: '유저플래그', 13: '서브BJ', 14: '닉변경', 17: '유저수EX',
               50: '투표알림', 54: '금칙어', 88: '방송종료',
               90: '', 94: '번역상태', 104: 'BJ공지', 110: '', 120: '보석선물',
               127: '유저플러드', 128: '관리자'}


def main():
    bid = sys.argv[1] if len(sys.argv) > 1 else 'talent'
    dur = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    info = soopchat.live_info(bid)
    if str(info.get('RESULT')) != '1':
        print('방송 중이 아닙니다: %s (RESULT=%s)' % (bid, info.get('RESULT')))
        return
    print('● LIVE  %s — %s' % (bid, (info.get('TITLE') or '')[:50]))
    print('%d초 동안 들어오는 것을 봅니다…\n' % dur)
    dom, pt, chatno = info['CHDOMAIN'], info['CHPT'], str(info['CHATNO'])
    ws = __import__('websocket').WebSocket(sslopt={'cert_reqs': ssl.CERT_NONE})
    ws.connect('wss://%s:%d/Websocket/%s' % (dom, int(pt) + 1, bid),
               subprotocols=['chat'], header=['User-Agent: Mozilla/5.0'], timeout=30)

    def pkt(svc, body):
        b = body.encode(); return ESC + ('%04d%06d00' % (svc, len(b))).encode() + b
    ws.send_binary(pkt(1, F + F + F + '16' + F)); ws.recv()
    ws.send_binary(pkt(2, F + chatno + F + F + F + F))

    chat = ids = empty = garble = 0
    chatters = set()
    bcount = bsum = 0
    balloon_senders = {}
    ogq = 0
    svc_seen = {}
    samples_chat, samples_bal, samples_ogq = [], [], []
    seen_bal = {}
    last_ping = time.time(); end = time.time() + dur
    while time.time() < end:
        try:
            if time.time() - last_ping > 50:
                ws.send_binary(pkt(0, F)); last_ping = time.time()
            fr = ws.recv()
        except Exception:
            break
        if isinstance(fr, str):
            fr = fr.encode('utf-8', 'replace')
        if not fr.startswith(ESC) or len(fr) < 14:
            continue
        try:
            svc = int(fr[2:6])
        except ValueError:
            continue
        f = fr[14:].decode('utf-8', 'replace').split(F)
        svc_seen[svc] = svc_seen.get(svc, 0) + 1
        if svc == 5 and len(f) > 6:
            chat += 1
            nick = soopchat._clean_nick(f[6]); uid = soopchat._clean_nick(f[2])
            if not nick: empty += 1
            if '�' in f[1]: garble += 1
            if uid: ids += 1
            if nick: chatters.add(nick)
            if len(samples_chat) < 5:
                samples_chat.append('%s(%s): %s' % (nick, uid, f[1][:24]))
        elif svc in (18, 33):
            ev = soopchat._parse_balloon(f, svc)
            if ev:
                key = '%s|%s' % (ev['id'], ev['count'])
                now = time.time()
                if key in seen_bal and now - seen_bal[key] < 8:
                    seen_bal[key] = now; continue      # 재전송
                seen_bal[key] = now
                bcount += 1; bsum += ev['count']
                balloon_senders[ev['id']] = balloon_senders.get(ev['id'], 0) + ev['count']
                if len(samples_bal) < 8:
                    samples_bal.append('%s(%s) %d개' % (ev['nick'], ev['id'], ev['count']))
        elif svc == 109:
            ogq += 1
            if len(samples_ogq) < 3:
                samples_ogq.append(str(f[:9]))
    try: ws.close()
    except Exception: pass

    print('── 채팅(svc5) ──')
    print('  %d건 · 발화자 %d명 · 계정캡처 %d/%d · 빈닉 %d · 깨짐 %d'
          % (chat, len(chatters), ids, chat, empty, garble))
    for s in samples_chat: print('    ', s)
    print('\n── 별풍선(svc18/33) ──')
    print('  %d건 / %d개 · 보낸이 %d명' % (bcount, bsum, len(balloon_senders)))
    for s in samples_bal: print('    ', s)
    print('\n── OGQ 이모티콘(svc109) — 별풍선 집계 제외됨 ──')
    print('  %d건 (별풍선으로 안 셈)' % ogq)
    for s in samples_ogq: print('    ', s)
    print('\n── 받은 svc 전부 ──')
    for svc, c in sorted(svc_seen.items(), key=lambda x: -x[1]):
        lab = KNOWN_LABEL.get(svc, '❓ 처음 보는 svc')
        mark = '  ← 확인 필요' if lab.startswith('❓') else ''
        print('  svc %-3d %-14s %d회%s' % (svc, lab, c, mark))
    # 진단
    print('\n── 진단 ──')
    issues = []
    if chat and empty / max(1, chat) > 0.05: issues.append('빈 닉 비율 높음')
    if garble: issues.append('깨진 글자 %d건' % garble)
    if chat and ids / max(1, chat) < 0.9: issues.append('계정 누락 많음')
    unknown = [s for s in svc_seen if s not in KNOWN_LABEL]
    if unknown: issues.append('처음 보는 svc %s' % unknown)
    print('  ' + ('이상 없음 ✅' if not issues else '확인 필요 → ' + ' · '.join(issues)))


if __name__ == '__main__':
    main()
