#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""라이브 별풍선 캐처 — 지정 방송에서 별풍선(svc18/33)이 오는 순간을 잡아
원본 필드와 파서 결과를 즉시 파일에 남깁니다. 별풍선은 뜸해서 오래 지켜봅니다.

  python3 balloon_catch.py <채널> [초]     (기본 1800초 = 30분)
"""
import sys, time, ssl, io, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soopchat

ESC = b'\x1b\t'; F = '\x0c'
BID = sys.argv[1] if len(sys.argv) > 1 else 'talent'
DUR = int(sys.argv[2]) if len(sys.argv) > 2 else 1800
LOG = os.path.join(ROOT, 'balloon-catch.log')


def log(m):
    line = '%s %s' % (time.strftime('%H:%M:%S'), m)
    with io.open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
    print(line, flush=True)


def main():
    io.open(LOG, 'w', encoding='utf-8').write('')
    deadline = time.time() + DUR
    caught = 0
    ogq = 0
    chat = 0
    seen = {}
    log('=== %s 별풍선 캐처 시작 (최대 %d분) ===' % (BID, DUR // 60))
    while time.time() < deadline:
        try:
            info = soopchat.live_info(BID)
            if str(info.get('RESULT')) != '1':
                log('방송 대기/종료 — 30초 후 재시도'); time.sleep(30); continue
            dom, pt, chatno = info['CHDOMAIN'], info['CHPT'], str(info['CHATNO'])
            ws = __import__('websocket').WebSocket(sslopt={'cert_reqs': ssl.CERT_NONE})
            ws.connect('wss://%s:%d/Websocket/%s' % (dom, int(pt) + 1, BID),
                       subprotocols=['chat'], header=['User-Agent: Mozilla/5.0'], timeout=30)

            def pkt(svc, body):
                b = body.encode(); return ESC + ('%04d%06d00' % (svc, len(b))).encode() + b
            ws.send_binary(pkt(1, F + F + F + '16' + F)); ws.recv()
            ws.send_binary(pkt(2, F + chatno + F + F + F + F))
            log('접속됨 — %s' % ((info.get('TITLE') or '')[:40]))
            last_ping = time.time()
            while time.time() < deadline:
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
                try: svc = int(fr[2:6])
                except ValueError: continue
                f = fr[14:].decode('utf-8', 'replace').split(F)
                if svc == 5:
                    chat += 1
                elif svc in (18, 33):
                    ev = soopchat._parse_balloon(f, svc)
                    key = (ev['id'], ev['count']) if ev else None
                    now = time.time()
                    dup = key and key in seen and now - seen[key] < 8
                    if key: seen[key] = now
                    tag = '재전송(중복제거됨)' if dup else '★새 별풍선'
                    log('🎈 svc%d %s → 파서:%s | 원본:%s'
                        % (svc, tag, (ev if ev else '파싱실패!'), f[:10]))
                    if ev and not dup:
                        caught += 1
                elif svc == 109:
                    ogq += 1
                    if ogq <= 3:
                        log('   (참고) svc109 OGQ 이모티콘 — 별풍선 아님: %s' % f[:9])
            try: ws.close()
            except Exception: pass
        except Exception as e:
            log('오류: %s — 5초 후 재시도' % (str(e)[:60])); time.sleep(5)
    log('=== 종료 — 채팅 %d · 별풍선 %d건 잡음 · OGQ이모티콘 %d ===' % (chat, caught, ogq))


if __name__ == '__main__':
    main()
