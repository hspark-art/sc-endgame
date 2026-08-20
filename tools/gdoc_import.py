#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""구글 문서의 당첨자 명단을 당첨자 시트(서버 winners.json)로 옮깁니다.

    python3 tools/gdoc_import.py            # 실제 병합 업로드
    python3 tools/gdoc_import.py --dry-run  # 올리지 않고 무엇이 들어갈지만

문서: "50당첨자 처리 현황" (이벤트 Trix 구글 문서)의 당첨자 탭만 읽습니다
(탭 주소 t.wacvhvtlbw9a — 다른 탭에는 기획 메모가 섞여 있어 일부러 뺍니다).

문서에 적힌 형식이 날짜마다 제각각이라 네 가지를 다 알아듣습니다.
  ① 닉네임 / 계정            ② 닉네임 / 계정 - 안경 (설명)
  ③ 닉네임 (계정) / 상품      ④ 닉네임 계정 상품
"상품A, 상품B" 처럼 한 사람이 두 개를 받은 줄은 상품별로 두 줄로 나눕니다
(시트가 날짜·상품 기준이라서).

상품 이름 규칙 (사장님 지시, 2026-08-20):
  · 상품 표시가 없으면 / '마우스'  → Razer Viper V3 Pro White
  · '안경'(웨어웨어 안경 포함)     → Wearwhere 안경
  · 그 밖의 것은 문서에 적힌 말 그대로 (유니폼, 페이커 마우스, 마우스패드…)
    — 무엇인지 못 알아본 줄만 비워 둡니다 (시트에서 직접 입력)

여러 번 돌려도 안전합니다 — 줄마다 내용으로 고유 번호를 만들어,
이미 시트에 있는 줄은 다시 넣지 않습니다. 시트에서 고친 내용도
건드리지 않습니다 (새 줄만 추가).
"""
import sys
import io
import re
import json
import ssl
import ftplib
import hashlib
import argparse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DOC_ID = '1UL9NulvqK1C7x7-w9WT40xLvTsJUpXskd1CYxY_PTI0'
TAB = 't.wacvhvtlbw9a'                       # 당첨자 탭
YEAR = 2026                                   # 문서의 날짜(0209…)가 속한 해

PRIZE_DEFAULT = 'Razer Viper V3 Pro White'
PRIZE_HEADERS = ('마우스', '안경', '쿠폰')     # 날짜 아래 소제목으로 쓰인 것들
PRIZE_WORD = re.compile(r'안경|마우스|유니폼|패드|포인트|쿠폰|코드|웨어웨어|에디션')

# 문서에 적힌 우리말 표기 → 실제 상품 정식 이름 (사장님 지정, 2026-08-20)
PRIZE_RENAME = {
    '카운터스트라이크 마우스': 'Razer Viper V3 Pro CS2',
    '유니폼': 'Jamie West Uniform',
    '페이커 마우스': 'Viper V3 Pro Faker',
    '마우스패드': 'Gigantus V2 Large CS2',
}

RE_PAREN = re.compile(r'^(.{1,40}?)\s*\(\s*([A-Za-z0-9_]{2,30})\)?\s*/\s*(.+)$')
RE_SLASH = re.compile(r'^(.{1,40}?)\s*/\s*([A-Za-z0-9_]{2,30})(\??)\s*(.*)$')
RE_MID = re.compile(r'^(.{1,40}?)\s+([A-Za-z0-9_]{3,30})\s*/\s*(.+)$')
RE_BARE = re.compile(r'^(.{1,40}?)\s+([a-z0-9_]{3,30})\s+(\S.*)$')


def fetch_doc():
    url = ('https://docs.google.com/document/d/%s/export?format=txt&tab=%s'
           % (DOC_ID, TAB))
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')


def norm_prize(item):
    """상품 한 개 표기 → (상품 이름, 덧붙일 메모)."""
    s = item.strip(' -–—·,()')
    detail = ''
    if '(' in s:                              # '안경 (이승원 해설님 모델)' 같은 꼬리
        s, _, tail = s.partition('(')
        detail = tail.rstrip(') ').strip()
        s = s.strip()
    if not s:
        return '', detail
    if '안경' in s or '웨어웨어' in s:
        extra = s.replace('웨어웨어', '').replace('안경', '').strip()
        if extra:
            detail = (detail + ' ' + extra).strip()
        return 'Wearwhere 안경', detail
    if s == '마우스':
        return PRIZE_DEFAULT, detail
    return PRIZE_RENAME.get(s, s), detail     # 정식 이름으로, 없으면 문서 표기 그대로


def parse_spec(spec, ctx):
    """상품 표기(줄 끝 또는 / 뒤) → [(상품, 메모덧)] 목록. 없으면 소제목(ctx)을 따름."""
    spec = (spec or '').strip(' -–—·')
    if not spec:
        if ctx is None:                       # 못 알아본 소제목 아래 → 비워 둠
            return [('', '')]
        if ctx == '안경':
            return [('Wearwhere 안경', '')]
        if ctx == '쿠폰':
            return [('쿠폰', '')]
        return [(PRIZE_DEFAULT, '')]          # 표기 없음/'마우스' 소제목
    out = []
    for part in spec.split(','):
        if part.strip():
            out.append(norm_prize(part))
    return out or [('', '')]


def parse(text):
    """문서 → 당첨 기록 목록. (기록들, 못 알아본 줄들) 을 돌려줍니다."""
    lines = [l.strip() for l in text.lstrip('﻿').split('\n')]
    if '당첨자 명단' in lines:                 # 전체 문서를 받았을 때 대비
        lines = lines[lines.index('당첨자 명단') + 1:]

    recs, odd = [], []
    date, how, ctx = '', '문서', ''            # ctx = 지금 상품 소제목

    def push(nick, sid, spec, memo0, sent):
        for prize, det in parse_spec(spec, ctx):
            memo = [m for m in (memo0, det) if m]
            key = 'g' + hashlib.md5(('%s|%s|%s|%s|%s' % (date, sid, prize, nick, how))
                                    .encode('utf-8')).hexdigest()[:13]
            recs.append({'id': key, 'date': date, 'nick': nick, 'sid': sid,
                         'prize': prize, 'how': how, 'sent': sent,
                         'memo': ' · '.join(memo)})

    for raw in lines:
        if not raw or 'http' in raw or raw.startswith('*'):
            continue
        # ── 소제목 줄 ──
        if raw == '출연자':
            date, how, ctx = '', '출연자', ''
            continue
        if re.fullmatch(r'\d{4}', raw):
            date = '%d-%s-%s' % (YEAR, raw[:2], raw[2:])
            how, ctx = '문서', ''
            continue
        if raw in PRIZE_HEADERS:
            ctx = raw
            if raw == '쿠폰':                  # 쿠폰 묶음은 날짜가 따로 없음
                date, how = '', '문서'
            continue

        # ── 당첨자 줄 — 공통 꼬리표 먼저 ──
        line, memo0, sent = raw, [], ''
        if '전달 완료' in line:
            sent = '완료'
            memo0.append('전달 완료')
            line = line.replace('(전달 완료)', '').replace('전달 완료', '').strip()
        if '수신거부' in line:
            memo0.append('쪽지 수신거부')
            line = re.sub(r'-?\s*쪽지?\s*수신거부', '', line).strip()

        m = RE_PAREN.match(line)              # ③ 닉네임 (계정) / 상품
        if m:
            push(m.group(1).strip(), m.group(2), m.group(3),
                 ' · '.join(memo0), sent)
            continue
        m = RE_SLASH.match(line)              # ①② 닉네임 / 계정 [상품·메모]
        if m:
            nick, sid, q, ann = (m.group(1).strip(), m.group(2),
                                 m.group(3), m.group(4).strip())
            if nick.endswith('?'):
                nick, q = nick[:-1].strip(), '?'
            if q:
                memo0.append('문서에 ? 표시 (본인 확인 필요)')
            if ann and not PRIZE_WORD.search(ann):
                memo0.append(ann.strip(' -–—()·,'))   # 상품이 아닌 꼬리말 → 메모
                ann = ''
            push(nick, sid, ann, ' · '.join(memo0), sent)
            continue
        m = RE_MID.match(line)                # 닉네임 계정 / 상품
        if m:
            push(m.group(1).strip(), m.group(2), m.group(3),
                 ' · '.join(memo0), sent)
            continue
        m = None if '/' in line else RE_BARE.match(line)
        if m and PRIZE_WORD.search(m.group(3)):   # ④ 닉네임 계정 상품
            push(m.group(1).strip(), m.group(2), m.group(3),
                 ' · '.join(memo0), sent)
            continue
        if len(raw) <= 12:                    # 처음 보는 소제목 → 상품은 비워 둠
            ctx = None
        odd.append(raw)
    return recs, odd


# ── 서버 winners.json 내려받기 / 올리기 (deploy.py 와 같은 FTP 정보) ──

def ftp_connect(cfg):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        f = ftplib.FTP_TLS(context=ctx, timeout=30)
        f.connect(cfg['host'], cfg.get('port', 21))
        f.login(cfg['user'], cfg['password'])
        f.prot_p()
        return f
    except Exception:
        f = ftplib.FTP(timeout=30)
        f.connect(cfg['host'], cfg.get('port', 21))
        f.login(cfg['user'], cfg['password'])
        return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='올리지 않고 결과만 보기')
    ap.add_argument('--full', action='store_true', help='기록 전체를 한 줄씩 보기')
    args = ap.parse_args()

    print('구글 문서(당첨자 탭)를 읽는 중…')
    recs, odd = parse(fetch_doc())
    print('  당첨 기록 %d건을 읽었습니다.' % len(recs))
    if odd:
        print('  ⚠ 못 알아들은 줄 %d개 (시트에 넣지 않음):' % len(odd))
        for o in odd:
            print('     ·', o)

    # 날짜·상품별 정리 출력
    by = {}
    for r in recs:
        k = (r['date'] or ('(출연자)' if r['how'] == '출연자' else '(날짜 없음)'),
             r['prize'] or '(비어 있음)')
        by.setdefault(k, []).append(r['nick'])
    print()
    print('── 날짜·상품별 정리 ──')
    for (d, p), nicks in sorted(by.items()):
        print('  %-12s %-26s %2d명  %s' % (d, p, len(nicks),
              ', '.join(nicks[:6]) + ('…' if len(nicks) > 6 else '')))
    if args.full:
        print()
        print('── 전체 기록 ──')
        for r in recs:
            print('  %-10s %-14s %-22s %-26s %s %s' % (
                r['date'] or '-', r['sid'], r['nick'], r['prize'] or '(비어 있음)',
                r['sent'] or '', r['memo']))

    cfg = json.load(io.open('data/deploy.json', encoding='utf-8'))
    base = cfg.get('remoteDir', '/www/endgame')
    path = base + '/admin/pz/winners.json'
    f = ftp_connect(cfg)
    buf = io.BytesIO()
    try:
        f.retrbinary('RETR ' + path, buf.write)
        doc = json.loads(buf.getvalue().decode('utf-8'))
    except Exception:
        doc = {'list': []}
    have_ids = {x.get('id') for x in doc['list']}
    have_keys = {(x.get('date', ''), x.get('sid', ''), x.get('prize', ''), x.get('nick', ''))
                 for x in doc['list']}
    fresh = [r for r in recs
             if r['id'] not in have_ids
             and (r['date'], r['sid'], r['prize'], r['nick']) not in have_keys]
    print()
    print('서버 시트: 기존 %d건 · 새로 넣을 것 %d건 (이미 있는 %d건은 건너뜀)'
          % (len(doc['list']), len(fresh), len(recs) - len(fresh)))
    if args.dry_run or not fresh:
        f.quit()
        print('(올리지 않았습니다)' if args.dry_run else '(바꿀 것이 없습니다)')
        return
    doc['list'].extend(fresh)
    payload = json.dumps(doc, ensure_ascii=False, indent=4).encode('utf-8')
    f.storbinary('STOR ' + path, io.BytesIO(payload))
    # 확인 삼아 다시 내려받아 개수를 셉니다
    buf2 = io.BytesIO()
    f.retrbinary('RETR ' + path, buf2.write)
    n = len(json.loads(buf2.getvalue().decode('utf-8'))['list'])
    f.quit()
    print('업로드 완료 — 서버 시트가 %d건이 되었습니다.' % n)


if __name__ == '__main__':
    main()
