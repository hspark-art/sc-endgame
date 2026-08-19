#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ASL 선수 프로필 사진 zip → img/players/ 로 옮겨 담습니다.

    python3 tools/import_photos.py "C:/.../ASL 선수 프로필 사진.zip"

무엇을 하나요
  1. zip 안의 폴더 이름에서 시즌(S9·S14·…)을, 파일 이름에서 선수를 알아냅니다.
     이름 규칙이 폴더마다 달라서(ASL_S21_이영호.png · 김명운_196_.jpg ·
     _이제동_1342 WIN.png · 김명운-01.png) 기록실 선수 이름이 파일명에
     들어 있는지로 찾습니다. 단체사진처럼 선수 이름이 없는 파일은 건너뜁니다.
  2. 한 선수의 한 시즌에 여러 장이 있으면 가장 큰(화질 좋은) 파일을 씁니다.
  3. 두 가지로 만들어 둡니다.
       img/players/<슬러그>.webp              가장 최근 시즌 얼굴 (사이트용, 정사각)
       img/players/seasons/<슬러그>-s<NN>.webp 시즌별 전신 (CG 제작용, 누끼 유지)
  4. data/player-photos.json 에 선수별 시즌 목록을 적어 둡니다.

원본은 장당 2~27MB 라 그대로 쓸 수 없어 줄여 담습니다. 누끼(투명 배경)는
CG 에서 그대로 써야 하므로 webp 로 투명도를 살려 둡니다.
"""

import argparse
import io
import json
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass

import slug as slugmod                                  # noqa: E402

SEASON_RE = re.compile(r'S\s*(\d+)')
FACE_PX = 400        # 사이트에 쓸 정사각 얼굴 사진 한 변
BODY_PX = 1200       # CG 에 쓸 전신 사진 높이


def player_names():
    names = {}
    for f in ('data/asl.json', 'data/endgame.json'):
        path = os.path.join(ROOT, f)
        if not os.path.exists(path):
            continue
        for p in json.load(io.open(path, encoding='utf-8'))['players']:
            names[p['name']] = p.get('slug') or slugmod.name_slug(p['name'])
    return names


def has_cutout(im):
    """배경이 이미 빠져 있는지 — 투명 픽셀이 3% 넘으면 누끼로 봅니다."""
    if 'A' not in im.mode:
        return False
    a = im.getchannel('A')
    hist = a.histogram()
    transparent = sum(hist[:16])
    return transparent > a.size[0] * a.size[1] * 0.03


_REMBG = None


def strip_background(im):
    """스튜디오 배경을 AI(rembg·U2Net)로 빼서 누끼로 만듭니다.

    CG 에서 인물만 얹으려면 배경이 없어야 하는데, 받은 사진 중 일부(S19·
    S15 2차 등 JPG)는 배경이 그대로 있습니다. 처음 쓸 때 모델(약 170MB)을
    한 번 내려받고, 그다음부터는 인터넷 없이 됩니다.
    """
    global _REMBG
    if _REMBG is None:
        from rembg import new_session
        _REMBG = new_session('u2net')
    from rembg import remove
    return remove(im, session=_REMBG)


def content_box(im):
    """투명 배경을 뺀 실제 인물 영역."""
    if 'A' in im.mode:
        bb = im.getchannel('A').getbbox()
        if bb:
            return bb
    return (0, 0, im.width, im.height)


def face_square(im):
    """얼굴이 확실히 들어가도록 인물 윗부분을 정사각형으로 자릅니다.

    얼굴 인식을 쓰지 않고, 인물 영역의 위쪽 1/3 을 가로 가운데 기준으로
    잘라냅니다. 프로필 사진은 사람이 가운데 서 있어서 이 방법으로 충분합니다.
    """
    l, t, r, b = content_box(im)
    cw, ch = r - l, b - t
    side = max(1, min(cw, int(ch * 0.34)))
    cx = (l + r) // 2
    x = max(0, min(im.width - side, cx - side // 2))
    y = max(0, t + int(ch * 0.015))
    return im.crop((x, y, x + side, min(im.height, y + side)))


def body_image(im):
    """CG 용 전신. 투명 배경은 그대로 두고 높이만 줄입니다."""
    l, t, r, b = content_box(im)
    im = im.crop((l, t, r, b))
    if im.height > BODY_PX:
        w = max(1, round(im.width * BODY_PX / im.height))
        im = im.resize((w, BODY_PX), 1)               # 1 = LANCZOS
    return im


def collect(zpath, names):
    """(선수, 시즌) → 가장 큰 파일 하나."""
    z = zipfile.ZipFile(zpath)
    best, skipped = {}, []
    for info in z.infolist():
        if info.is_dir():
            continue
        folder, base = (info.filename.rsplit('/', 1) + [''])[:2] \
            if '/' in info.filename else ('', info.filename)
        m = SEASON_RE.search(folder)
        hit = [n for n in names if n in base]
        if not hit or not m:
            skipped.append(info.filename)
            continue
        who = max(hit, key=len)                        # '김성현' 이 '김성' 을 이깁니다
        key = (who, int(m.group(1)))
        if key not in best or info.file_size > best[key].file_size:
            best[key] = info
    return z, best, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('zip', help='ASL 선수 프로필 사진 zip 경로')
    ap.add_argument('--dry-run', action='store_true', help='만들지 않고 무엇이 될지만')
    args = ap.parse_args()

    from PIL import Image

    names = player_names()
    print('기록실 선수 %d명' % len(names))
    z, best, skipped = collect(args.zip, names)
    print('선수-시즌 조합 %d개 · 이름을 못 찾아 건너뛴 파일 %d장' % (len(best), len(skipped)))
    for s in skipped[:6]:
        print('   건너뜀: %s' % s)

    seasons = {}
    for (who, season) in best:
        seasons.setdefault(who, []).append(season)
    for who in seasons:
        seasons[who].sort()

    if args.dry_run:
        for who in sorted(seasons):
            print('  %-8s %s' % (who, seasons[who]))
        return 0

    body_dir = os.path.join(ROOT, 'img', 'players', 'seasons')
    os.makedirs(body_dir, exist_ok=True)
    face_dir = os.path.join(ROOT, 'img', 'players')

    made_body = made_face = cut = 0
    for (who, season), info in sorted(best.items()):
        sl = names[who]
        with z.open(info) as f:
            im = Image.open(io.BytesIO(f.read()))
            im.load()
        # 원본이 아주 커서(장당 2~27MB) 먼저 줄인 뒤에 배경을 뺍니다.
        if im.height > 1400:
            im = im.resize((max(1, round(im.width * 1400 / im.height)), 1400), 1)
        if not has_cutout(im):
            im = strip_background(im.convert('RGBA'))
            cut += 1
        out = os.path.join(body_dir, '%s-s%02d.webp' % (sl, season))
        body_image(im).save(out, 'WEBP', quality=82, method=4)
        made_body += 1
        # 가장 최근 시즌 사진으로 사이트용 얼굴을 만듭니다.
        if season == max(seasons[who]):
            sq = face_square(im)
            if 'A' in sq.mode:                          # 투명 배경은 흰색으로 깝니다
                bg = Image.new('RGB', sq.size, (255, 255, 255))
                bg.paste(sq, mask=sq.getchannel('A'))
                sq = bg
            sq = sq.convert('RGB').resize((FACE_PX, FACE_PX), 1)
            sq.save(os.path.join(face_dir, sl + '.webp'), 'WEBP', quality=86, method=4)
            made_face += 1
        print('  %-10s S%-2d → %s' % (who, season, os.path.basename(out)))

    doc = {
        '_note': ['선수별로 어느 시즌 프로필 사진이 있는지 적어 둔 파일입니다.',
                  'tools/import_photos.py 가 만듭니다. 손으로 고치지 마세요.',
                  '사이트는 가장 최근 시즌 얼굴을 쓰고, CG 제작 툴에서는 시즌을 고를 수 있습니다.'],
        'players': {names[w]: {'name': w, 'seasons': s} for w, s in sorted(seasons.items())},
    }
    io.open(os.path.join(ROOT, 'data', 'player-photos.json'), 'w', encoding='utf-8').write(
        json.dumps(doc, ensure_ascii=False, indent=1) + '\n')

    print('')
    print('전신(CG용) %d장 · 얼굴(사이트용) %d장 · 선수 %d명 · 배경을 새로 뺀 사진 %d장'
          % (made_body, made_face, len(seasons), cut))
    print('data/player-photos.json 에 시즌 목록을 적었습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
