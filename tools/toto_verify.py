#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""시청자 승부예측 — 사후 검증(리플레이) 도구.

승부예측이 켜져 있는 동안 관제가 서버에 남긴 채팅 원본
(admin/pz/toto_chatlog-날짜.jsonl — 전 채팅 + 개장/오픈/마감/정산 마커)을
그대로 재생해서, 규칙대로 다시 계산한 순위와 실제 기록(시즌/당일)을
대조합니다. 불일치가 있으면 줄 단위로 보여줍니다.

쓰는 법:
  python3 tools/toto_verify.py                 # 오늘 날짜, 서버에서 받아 검증
  python3 tools/toto_verify.py 2026-08-21      # 특정 날짜
  python3 tools/toto_verify.py --file 로그.jsonl   # 로컬 파일로 재생만 (시험용)
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TT_START = 10000
TT_MIN = 100


def norm(s):
    s = re.sub(r'\s+', '', str(s or ''))
    s = re.sub(r'[!~.?]+$', '', s)
    return s.lower()


def replay(lines):
    """관제와 똑같은 규칙으로 로그를 재생합니다. (관제 ttOnChat 미러)"""
    day = None
    gaps = []
    note = []
    for ln in lines:
        ctl = ln.get('ctl')
        if ctl == 'open_day':
            day = {'players': {}, 'round': None, 'rounds': []}
            continue
        if day is None:
            continue
        if ctl == 'round_open':
            day['round'] = {'a': ln.get('a', ''), 'b': ln.get('b', ''),
                            'state': 'open', 'bets': {}}
            continue
        if ctl == 'lock':
            if day['round']:
                day['round']['state'] = 'locked'
            continue
        if ctl == 'cancel':
            r = day['round']
            if r:
                for k, v in r['bets'].items():
                    p = day['players'].get(k)
                    if p:
                        p['bal'] += v['amt']
                        p['bust'] = False
            day['round'] = None
            continue
        if ctl == 'settle':
            r = day['round']
            if not r:
                continue
            winner = 'b' if ln.get('winner') == 'b' else 'a'
            pa = sum(v['amt'] for v in r['bets'].values() if v['p'] == 'a')
            pb = sum(v['amt'] for v in r['bets'].values() if v['p'] == 'b')
            total, pw = pa + pb, (pa if winner == 'a' else pb)
            refund = pw <= 0
            hit = 0
            for k, v in r['bets'].items():
                p = day['players'][k]
                if refund:
                    p['bal'] += v['amt']
                elif v['p'] == winner:
                    p['bal'] += v['amt'] * total // pw
                    p['betW'] += 1
                    hit += 1
                else:
                    p['betL'] += 1
                if p['bal'] <= 0:
                    p['bal'] = 0
                    p['bust'] = True
            day['rounds'].append({'a': r['a'], 'b': r['b'], 'winner': winner,
                                  'poolA': pa, 'poolB': pb, 'hit': hit,
                                  'refund': refund})
            day['round'] = None
            continue
        if ctl == 'gap':
            gaps.append(int(ln.get('sec', 0)))
            continue
        if ctl == 'close_day':
            continue
        # ── 일반 채팅 ──
        m = str(ln.get('m', '')).strip()
        nick = str(ln.get('n', ''))
        key = ln.get('id') or ('nick:' + nick)
        if norm(m) == '도전':
            if key not in day['players']:
                day['players'][key] = {'n': nick, 'bal': TT_START,
                                       'betW': 0, 'betL': 0, 'bust': False}
            continue
        r = day['round']
        if not r or r['state'] != 'open':
            continue
        parts = m.split()
        if len(parts) != 2:
            continue
        amt_raw = parts[1].replace(',', '')
        allin = (amt_raw == '올인')
        if not allin and not amt_raw.isdigit():
            continue
        nm = norm(parts[0])
        pick = 'a' if nm == norm(r['a']) else ('b' if nm == norm(r['b']) else None)
        p = day['players'].get(key)
        if not pick or not p or p['bust'] or key in r['bets']:
            continue
        amt = p['bal'] if allin else int(amt_raw)
        if (not allin and amt > p['bal']) or amt < TT_MIN:
            continue
        p['bal'] -= amt
        r['bets'][key] = {'p': pick, 'amt': amt, 'n': nick}
    return day, gaps, note


def ftp_read(cfg, path):
    import ftplib
    try:
        ftp = ftplib.FTP_TLS(timeout=25)
        ftp.connect(cfg['host'], cfg.get('port', 21))
        ftp.login(cfg['user'], cfg['password'])
        ftp.prot_p()
    except Exception:
        ftp = ftplib.FTP(timeout=25)
        ftp.connect(cfg['host'], cfg.get('port', 21))
        ftp.login(cfg['user'], cfg['password'])
    buf = io.BytesIO()
    try:
        ftp.retrbinary('RETR ' + path, buf.write)
    except Exception:
        ftp.quit()
        return None
    ftp.quit()
    return buf.getvalue().decode('utf-8', 'replace')


def main():
    args = sys.argv[1:]
    local = None
    date = None
    if '--file' in args:
        local = args[args.index('--file') + 1]
    else:
        date = args[0] if args else __import__('time').strftime('%Y-%m-%d')

    if local:
        raw = io.open(local, encoding='utf-8').read()
        season = None
        dayfile = None
    else:
        cfg = json.load(io.open(os.path.join(ROOT, 'data', 'deploy.json'), encoding='utf-8'))
        base = cfg.get('remoteDir', '/www/endgame') + '/admin/pz'
        print('서버에서 %s 로그를 받는 중…' % date)
        raw = ftp_read(cfg, '%s/toto_chatlog-%s.jsonl' % (base, date))
        if raw is None:
            print('로그가 없습니다: toto_chatlog-%s.jsonl (그날 예측을 안 켰거나 날짜 오타)' % date)
            return
        season = ftp_read(cfg, base + '/toto_season.json')
        dayfile = ftp_read(cfg, base + '/toto_day.json')

    lines = []
    for row in raw.splitlines():
        row = row.strip()
        if row:
            try:
                lines.append(json.loads(row))
            except Exception:
                pass
    print('로그 %d줄 재생…' % len(lines))
    day, gaps, _ = replay(lines)
    if not day:
        print('open_day 마커가 없습니다 — 예측을 시작한 기록이 없어요.')
        return

    rows = sorted(({'n': p['n'], 'bal': p['bal'], 'w': p['betW'], 'l': p['betL'],
                    'bust': p['bust']} for p in day['players'].values()),
                  key=lambda r: -r['bal'])
    print('\n── 리플레이로 다시 계산한 순위 ──')
    for i, r in enumerate(rows[:10], 1):
        print(' %2d위  %-16s %8s P  (%d승 %d패)%s'
              % (i, r['n'], format(r['bal'], ','), r['w'], r['l'],
                 '  [파산]' if r['bust'] else ''))
    print(' 참여 %d명 · 라운드 %d판' % (len(rows), len(day['rounds'])))
    if gaps:
        print(' ⚠ 연결 끊김 %d회 (%s초) — 그 구간 채팅은 로그에도 없습니다'
              % (len(gaps), '+'.join(map(str, gaps))))

    # ── 실제 기록과 대조 ──
    issues = []
    if dayfile:
        try:
            dj = json.loads(dayfile)
        except Exception:
            dj = None
        if isinstance(dj, dict) and dj.get('players'):
            rec = {p.get('n'): int(p.get('bal', 0)) for p in dj['players'].values()}
            for r in rows:
                if r['n'] in rec and rec[r['n']] != r['bal']:
                    issues.append('%s: 기록 %sP ≠ 리플레이 %sP'
                                  % (r['n'], format(rec[r['n']], ','), format(r['bal'], ',')))
            print('\n(진행 중인 오늘 판과 대조)')
    if season and date:
        try:
            sj = json.loads(season)
        except Exception:
            sj = None
        entry = None
        for dd in (sj or {}).get('days', []):
            if dd.get('date') == date:
                entry = dd
                break
        if entry:
            print('\n(시즌 기록의 %s 우승과 대조)' % date)
            ch = entry.get('champ', {})
            if rows and (ch.get('n') != rows[0]['n'] or int(ch.get('bal', 0)) != rows[0]['bal']):
                issues.append('우승자: 기록 %s %sP ≠ 리플레이 %s %sP'
                              % (ch.get('n'), format(int(ch.get('bal', 0)), ','),
                                 rows[0]['n'], format(rows[0]['bal'], ',')))
    print('\n── 판정 ──')
    if issues:
        print(' ⚠ 불일치 %d건:' % len(issues))
        for x in issues:
            print('   · ' + x)
        print(' (연결 끊김 구간, 도중 취소, 제외 계정 변경 등이 원인일 수 있습니다)')
    else:
        print(' ✅ 리플레이 결과가 기록과 일치합니다 (대조 대상 범위 안에서)')


if __name__ == '__main__':
    main()
