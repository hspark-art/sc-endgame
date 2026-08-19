#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""구글시트를 받아오면서 마지막으로 성공한 내용을 파일로 남겨 둡니다.

왜 필요한가
  사이트가 읽는 ASL 시트는 방송팀 원본을 IMPORTRANGE 로 비추는 '연동본'입니다.
  원본이 지워지거나 옮겨지면 연동본이 통째로 #REF! 가 되고, 그대로 두면
  사이트의 기록이 하루아침에 비어 버립니다.

  그래서 받아올 때마다 아래를 합니다.
    1. 받아온 내용이 멀쩡한지 본다 (#REF! · 빈 내용 · 갑자기 확 줄어듦)
    2. 멀쩡하면 data/sheet-backup/ 에 그대로 저장한다
    3. 이상하면 저장해 둔 마지막 정상본으로 대신 진행하고 크게 알린다

  백업은 그냥 CSV 파일입니다. 엑셀로 열어 보셔도 되고, 최악의 경우 이 파일만
  있으면 시트를 처음부터 다시 만들 수 있습니다.
"""

import io
import os
import sys
import urllib.request
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BACKUP_DIR = os.path.join(ROOT, 'data', 'sheet-backup')

# 날짜별 사본은 이 개수만 남기고 오래된 것부터 지웁니다.
KEEP_DATED = 5
# 지난번보다 이 비율 밑으로 줄면 사고로 봅니다 (예: 0.5 = 절반 아래).
SHRINK_LIMIT = 0.5


def _paths(name):
    latest = os.path.join(BACKUP_DIR, '%s-latest.csv' % name)
    dated = os.path.join(BACKUP_DIR, '%s-%s.csv' % (name, date.today().isoformat()))
    return latest, dated


def looks_broken(text, prev):
    """받아온 내용이 못 쓸 것인지 판단합니다. 이유를 돌려주고, 멀쩡하면 None."""
    if text is None:
        return '시트를 받아오지 못했습니다'
    body = text.strip()
    if not body:
        return '시트 내용이 비어 있습니다'
    if '#REF!' in text:
        return ('시트가 #REF! 입니다 — 연동본이 원본을 못 읽고 있습니다.\n'
                '     연동본을 열어 A1 의 "액세스 허용"을 눌러 주시거나,\n'
                '     원본 시트가 지워졌는지/옮겨졌는지 확인해 주세요.')
    lines = [x for x in body.split('\n') if x.strip(', ')]
    if len(lines) < 2:
        return '받아온 줄이 %d줄뿐입니다' % len(lines)
    if prev:
        pl = len([x for x in prev.strip().split('\n') if x.strip(', ')])
        if pl and len(lines) < pl * SHRINK_LIMIT:
            return ('줄 수가 %d → %d 로 확 줄었습니다 (사고로 보입니다)' % (pl, len(lines)))
    return None


def read_backup(name):
    latest, _ = _paths(name)
    if not os.path.exists(latest):
        return None
    try:
        return io.open(latest, encoding='utf-8').read()
    except OSError:
        return None


def save_backup(name, text):
    latest, dated = _paths(name)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for p in (latest, dated):
        io.open(p, 'w', encoding='utf-8', newline='').write(text)
    # 날짜별 사본이 너무 쌓이지 않게 오래된 것부터 지웁니다.
    keep = sorted(f for f in os.listdir(BACKUP_DIR)
                  if f.startswith(name + '-') and not f.endswith('-latest.csv'))
    for f in keep[:-KEEP_DATED]:
        try:
            os.remove(os.path.join(BACKUP_DIR, f))
        except OSError:
            pass


def fetch_csv(url, name, timeout=60):
    """시트를 받아옵니다. 못 쓸 내용이면 마지막 정상본으로 대신합니다.

    돌려주는 값은 (CSV 문자열, 백업으로 대신했는지) 입니다.
    """
    prev = read_backup(name)
    text = None
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'sc-endgame/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            text = r.read().decode('utf-8')
    except Exception as e:                        # 접속 실패도 백업으로 넘어갑니다
        why = '%s: %s' % (type(e).__name__, e)
        text = None
    else:
        why = None

    problem = why or looks_broken(text, prev)
    if not problem:
        save_backup(name, text)
        return text, False

    print('')
    print('  !! 시트를 그대로 쓸 수 없습니다 — %s' % problem)
    if prev is None:
        raise SystemExit(
            '  저장해 둔 백업도 없어서 진행할 수 없습니다.\n'
            '  시트를 고치신 뒤 다시 실행해 주세요.')
    print('  !! %s 의 마지막 정상본으로 대신 진행합니다.' % name)
    print('     %s' % os.path.join('data', 'sheet-backup', '%s-latest.csv' % name))
    print('     이번 내용은 백업에 덮어쓰지 않았습니다.')
    print('')
    return prev, True
