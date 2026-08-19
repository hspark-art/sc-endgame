/* 끝장전 방송 CG 제작 툴.
   1920x1080 캔버스에 직접 그립니다 — 바깥 라이브러리를 쓰지 않아서
   인터넷이 끊겨도 되고, 내보낸 PNG 가 화면에 보이는 것과 정확히 같습니다.

   CG 다섯 종류를 한 툴에서 만듭니다.
     matchup  대진표 (경기 방식·상금·사용맵)
     stats    선수 전적
     score    쉬는 시간 (전적 + 스코어)
     winner   경기 결과 (승자 강조·패자 어둡게)
     next     다음 경기 안내

   배치는 방송 포맷 그대로 고정입니다. 대신 글자마다 내용·크기·색·폰트를
   바꿀 수 있고, 사진은 끌어서 위치를, 휠이나 슬라이더로 크기를 맞춥니다. */

var W = 1920, H = 1080;
var cv = document.getElementById('cv');
var ctx = cv.getContext('2d');
cv.width = W; cv.height = H;

var RACE_COLOR = { T: '#4a9eff', P: '#f5c518', Z: '#ff6b6b' };

var FONTS = {
  pretendard: "'Pretendard','Malgun Gothic','맑은 고딕',system-ui,sans-serif",
  gothic: "'Malgun Gothic','맑은 고딕',sans-serif",
  nanum: "'NanumGothic','나눔고딕','Malgun Gothic',sans-serif",
  black: "'Arial Black','Pretendard','Malgun Gothic',sans-serif",
  serif: "'Batang','바탕',serif",
  script: "'Segoe Script','Brush Script MT','Pretendard',cursive"
};

var TYPES = [
  { id: 'matchup', label: '대진표' },
  { id: 'stats', label: '선수 전적' },
  { id: 'score', label: '쉬는 시간 (스코어)' },
  { id: 'winner', label: '경기 결과' },
  { id: 'next', label: '다음 경기' }
];

/* ── 화면 배치 (1920x1080 기준) ─────────────────────────────── */
var L = {
  topBarY: 46, topBarH: 92,
  // 선수 사진은 방송처럼 화면 좌우 끝까지 꽉 채웁니다.
  photo: { w: 620, h: 1080, y: 0 },
  center: { x: 512, w: 896 }
};

/* ── 상태 ──────────────────────────────────────────────────── */
function defaults() {
  return {
    type: 'matchup',
    title: '끝장전',
    sponsorText: '',
    bgLeft: '#8c1f2a',
    bgRight: '#123a78',
    logoSponsor: null,
    logoBroadcast: null,
    liveBadge: '',
    players: [
      { nick: 'RoyaL', name: '김지성', race: 'T', photo: null, photoFrom: null,
        season: '', zoom: 1, ox: 0, oy: 0,
        prize: 'KRW 25,900,000', score: '0', delta: '',
        vs: 'VS 장윤철(P) 3 : 6 패\nVS 박상현(Z) 4 : 5 패\nVS 김민철(Z) 4 : 5 패\nVS 조일장(Z) 6 : 3 승\n[VS 이제동(Z) 6 : 3 승]' },
      { nick: 'Bisu', name: '김택용', race: 'P', photo: null, photoFrom: null,
        season: '', zoom: 1, ox: 0, oy: 0,
        prize: 'KRW 4,000,000', score: '0', delta: '',
        vs: 'VS 김명운(Z) 6 : 3 승\nVS 이재호(T) 3 : 6 패\nVS 이제동(Z) 5 : 4 승\nVS 이영한(Z) 8 : 1 승\n[VS 이영호(T) 5 : 3 승]' }
    ],
    boxes: [
      { title: '경기 방식', body: '두 선수가 9세트 풀세트 진행\n( 8대 0 상황에서도 마지막 9세트 진행 )' },
      { title: '상금',
        body: '매 세트 승리시 10만원\n[더블 찬스]\n세트 시작 전 선수당 1일 1회 더블 찬스 사용 가능\n' +
          '더블 찬스가 적용된 세트의 승자는 두배의 상금 획득 (20만원)\n* ※ 중복 사용 불가\n' +
          '[올킬 상금 30만원 (총 상금 140만원)]' },
      { title: '사용맵',
        body: '오디세이, 컬러리스 페이트, 녹아웃, 애티튜드,\n아이올로스, 백룸, 옥타곤 (ASL 시즌22 공식맵)\n' +
          '* 경기 시작 전 선수당 한 개씩 총 두 개 맵 제거' }
    ],
    stats: {
      heading: 'Player Stats',
      sub: '온라인 매치',
      prizeLabel: '누적상금',
      rows: [
        { label: '총 전적', a: '251', b: '302' },
        { label: '최근 한달 상대 전적', a: '1', b: '7' }
      ],
      period: '7월 11일 ~ 8월 11일 기록',
      muLabel: '최근 한달 상대 종족 전적',
      muA: 'vs P', muAVal: '16 : 17',
      muB: 'vs T', muBVal: '21 : 14',
      foot: '잠시 후 승부예측 마감!\nSOOP e스포츠\nesports.sooplive.co.kr',
      timer: '13:35'
    },
    winner: {
      side: 0,
      label: 'WINNER',
      ribbon: '3연승 중!',
      vsText: '5 VS 4'
    },
    next: {
      heading: 'NEXT MATCH',
      when: '2026년 8월 20일 목요일 오후 9시'
    },
    style: {
      title: { size: 58, color: '#4aa8ff', font: 'pretendard' },
      nick: { size: 46, color: '#e9edf5', font: 'pretendard' },
      pname: { size: 74, color: '#ffffff', font: 'pretendard' },
      boxTitle: { size: 38, color: '#ffd166', font: 'pretendard' },
      boxLine: { size: 26, color: '#ffffff', font: 'pretendard' },
      boxNote: { size: 20, color: '#b9c2d0', font: 'pretendard' },
      heading: { size: 62, color: '#ffffff', font: 'script' },
      sub: { size: 30, color: '#ffffff', font: 'pretendard' },
      rowLabel: { size: 26, color: '#ffffff', font: 'pretendard' },
      rowValue: { size: 62, color: '#ffffff', font: 'pretendard' },
      period: { size: 22, color: '#e8ecf3', font: 'pretendard' },
      prize: { size: 30, color: '#ffffff', font: 'pretendard' },
      vsList: { size: 23, color: '#e8ecf3', font: 'pretendard' },
      foot: { size: 22, color: '#0b0d11', font: 'pretendard' },
      timer: { size: 74, color: '#ffffff', font: 'black' },
      score: { size: 96, color: '#ffffff', font: 'pretendard' },
      winnerLabel: { size: 78, color: '#ffd166', font: 'black' },
      ribbon: { size: 26, color: '#ffffff', font: 'pretendard' },
      vsBig: { size: 74, color: '#ffffff', font: 'pretendard' },
      nextHead: { size: 150, color: '#ff4d5a', font: 'black' },
      when: { size: 46, color: '#ffffff', font: 'pretendard' }
    }
  };
}

var S = defaults();
var imgCache = {};

function loadImage(src, cb) {
  if (!src) { cb(null); return; }
  if (imgCache[src] && imgCache[src].complete) { cb(imgCache[src]); return; }
  var im = new Image();
  im.onload = function () { imgCache[src] = im; cb(im); };
  im.onerror = function () { cb(null); };
  im.src = src;
  imgCache[src] = im;
}

/* ── 그리기 도구 ───────────────────────────────────────────── */
function roundRect(c, x, y, w, h, r) {
  c.beginPath();
  c.moveTo(x + r, y);
  c.arcTo(x + w, y, x + w, y + h, r);
  c.arcTo(x + w, y + h, x, y + h, r);
  c.arcTo(x, y + h, x, y, r);
  c.arcTo(x, y, x + w, y, r);
  c.closePath();
}

/** 글자 모양을 정합니다. st 는 S.style 의 한 칸입니다. */
function use(st, sizeOverride, weight) {
  var f = FONTS[st.font] || FONTS.pretendard;
  ctx.font = (weight || 800) + ' ' + (sizeOverride || st.size) + 'px ' + f;
  ctx.fillStyle = st.color;
}

function setFont(size, weight, fontKey) {
  ctx.font = (weight || 700) + ' ' + size + 'px ' + (FONTS[fontKey] || FONTS.pretendard);
}

/** 글자가 칸을 넘치면 자동으로 줄여 그립니다. */
function fitSize(text, st, maxW, weight) {
  var s = st.size;
  use(st, s, weight);
  while (s > 10 && ctx.measureText(text).width > maxW) {
    s -= 1;
    use(st, s, weight);
  }
  return s;
}

function text(str, x, y, st, opt) {
  opt = opt || {};
  var size = opt.maxW ? fitSize(str, st, opt.maxW, opt.weight) : st.size;
  use(st, size, opt.weight);
  if (opt.color) ctx.fillStyle = opt.color;
  ctx.textAlign = opt.align || 'left';
  ctx.textBaseline = opt.baseline || 'alphabetic';
  if (opt.shadow) { ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = opt.shadow; }
  ctx.fillText(str, x, y);
  ctx.shadowBlur = 0;
  return size;
}

function drawCover(im, x, y, w, h, zoom, ox, oy, radius) {
  ctx.save();
  if (radius) { roundRect(ctx, x, y, w, h, radius); ctx.clip(); }
  else { ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip(); }
  var scale = Math.max(w / im.width, h / im.height) * (zoom || 1);
  var dw = im.width * scale, dh = im.height * scale;
  ctx.drawImage(im, x + (w - dw) / 2 + (ox || 0), y + (h - dh) / 2 + (oy || 0), dw, dh);
  ctx.restore();
}

function drawContain(im, cx, cy, maxW, maxH) {
  var scale = Math.min(maxW / im.width, maxH / im.height);
  var w = im.width * scale, h = im.height * scale;
  ctx.drawImage(im, cx - w / 2, cy - h / 2, w, h);
  return w;
}

/* ── 본문 줄 해석 ──────────────────────────────────────────────
   [글자]  → 테두리 강조 칩
   * 글자  → 작게, 흐린 색
   그 외   → 보통 글자                                           */
function parseLine(raw) {
  var t = raw.trim();
  if (!t) return { kind: 'gap', text: '' };
  if (t[0] === '[' && t[t.length - 1] === ']') return { kind: 'chip', text: t.slice(1, -1).trim() };
  if (t[0] === '*') return { kind: 'note', text: t.slice(1).trim() };
  return { kind: 'line', text: t };
}

function lines(s) { return String(s || '').split('\n').map(parseLine); }

/* ── 공통 영역 ─────────────────────────────────────────────── */
function drawBackground() {
  ctx.fillStyle = '#15171c';
  ctx.fillRect(0, 0, W, H);
  var side = 760;
  [[0, S.bgLeft, 0], [W - side, S.bgRight, 1]].forEach(function (p) {
    var x = p[0], i = p[2];
    var g = ctx.createLinearGradient(i === 0 ? 0 : W, 0, i === 0 ? side : W - side, 0);
    g.addColorStop(0, p[1]);
    g.addColorStop(1, 'rgba(21,23,28,0)');
    ctx.fillStyle = g;
    ctx.fillRect(x, 0, side, H);
  });
}

function drawTopBar(imgs) {
  var y = L.topBarY, h = L.topBarH, cx = W / 2;
  var st = S.style.title;
  use(st, st.size, 900);
  var titleW = ctx.measureText(S.title).width;

  var sponsorW = 0;
  if (imgs.sponsor) {
    sponsorW = Math.min(imgs.sponsor.width * (h / imgs.sponsor.height), 460);
  } else if (S.sponsorText) {
    setFont(42, 800, st.font);
    sponsorW = ctx.measureText(S.sponsorText).width;
  }
  var divW = sponsorW ? 46 : 0;
  var startX = cx - (sponsorW + divW + titleW) / 2;

  if (imgs.sponsor) {
    drawContain(imgs.sponsor, startX + sponsorW / 2, y + h / 2, sponsorW, h);
  } else if (S.sponsorText) {
    setFont(42, 800, st.font);
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillText(S.sponsorText, startX, y + h / 2);
  }
  if (divW) {
    ctx.strokeStyle = 'rgba(255,255,255,.4)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(startX + sponsorW + divW / 2, y + 14);
    ctx.lineTo(startX + sponsorW + divW / 2, y + h - 14);
    ctx.stroke();
  }
  text(S.title, startX + sponsorW + divW, y + h / 2 + 2, st,
    { weight: 900, baseline: 'middle' });

  if (imgs.broadcast) {
    var bw = Math.min(imgs.broadcast.width * (78 / imgs.broadcast.height), 260);
    drawContain(imgs.broadcast, W - 44 - bw / 2, y + h / 2 - 4, bw, 78);
  }
  if (S.liveBadge) {
    setFont(30, 900, 'pretendard');
    var lw = ctx.measureText(S.liveBadge).width + 40;
    ctx.fillStyle = '#1c8cff';
    roundRect(ctx, W - 44 - lw, y + h + 12, lw, 50, 8);
    ctx.fill();
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(S.liveBadge, W - 44 - lw / 2, y + h + 38);
  }
}

function photoRect(side) {
  var p = L.photo;
  return { x: side === 0 ? 0 : W - p.w, y: p.y, w: p.w, h: p.h };
}

/** 선수 사진. dim 이 true 면 어둡게 (진 선수). */
function drawPhoto(side, im, dim) {
  var pl = S.players[side], r = photoRect(side);
  if (im) {
    drawCover(im, r.x, r.y, r.w, r.h, pl.zoom, pl.ox, pl.oy, 0);
    if (dim) {
      ctx.save();
      ctx.beginPath(); ctx.rect(r.x, r.y, r.w, r.h); ctx.clip();
      ctx.fillStyle = 'rgba(6,8,12,.62)';
      ctx.fillRect(r.x, r.y, r.w, r.h);
      ctx.restore();
    }
  } else {
    ctx.save();
    ctx.setLineDash([12, 9]);
    ctx.strokeStyle = 'rgba(255,255,255,.30)';
    ctx.lineWidth = 3;
    roundRect(ctx, r.x + 26, r.y + 150, r.w - 52, r.h - 300, 14);
    ctx.stroke();
    ctx.setLineDash([]);
    setFont(28, 700);
    ctx.fillStyle = 'rgba(255,255,255,.55)';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('선수 사진을 올려 주세요', r.x + r.w / 2, r.y + r.h / 2 - 18);
    setFont(21, 500);
    ctx.fillText('여기로 끌어다 놓아도 됩니다', r.x + r.w / 2, r.y + r.h / 2 + 24);
    ctx.restore();
  }
}

/** 닉네임 + 이름 + 종족 한 덩어리. align 은 'left' | 'right' | 'center'. */
function drawNamePlate(side, x, y, align, maxW) {
  var pl = S.players[side];
  var sn = S.style.nick, sp = S.style.pname;
  if (pl.nick) {
    text(pl.nick, x, y, sn, { align: align, maxW: maxW, weight: 500, shadow: 10 });
  }
  var label = pl.name + (pl.race ? ' ' + pl.race : '');
  var size = fitSize(label, sp, maxW || 460, 900);
  use(sp, size, 900);
  var full = ctx.measureText(label).width;
  var nameW = ctx.measureText(pl.name).width;
  var sx = align === 'right' ? x - full : (align === 'center' ? x - full / 2 : x);
  ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
  ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = 14;
  ctx.fillStyle = sp.color;
  ctx.fillText(pl.name, sx, y + size + 12);
  if (pl.race) {
    ctx.fillStyle = RACE_COLOR[pl.race] || sp.color;
    ctx.fillText(' ' + pl.race, sx + nameW, y + size + 12);
  }
  ctx.shadowBlur = 0;
  return y + size + 12;
}

/* ── ① 대진표 ──────────────────────────────────────────────── */
function boxHeight(box) {
  var sT = S.style.boxTitle, sL = S.style.boxLine, sN = S.style.boxNote;
  var h = 20 + sT.size + 18 + 20;
  lines(box.body).forEach(function (ln) {
    if (ln.kind === 'gap') h += 14;
    else if (ln.kind === 'note') h += sN.size + 12;
    else if (ln.kind === 'chip') h += sL.size + 22;
    else h += sL.size + 14;
  });
  return h;
}

function drawMatchup() {
  var sT = S.style.boxTitle, sL = S.style.boxLine, sN = S.style.boxNote;
  var x = L.center.x, w = L.center.w, cx = x + w / 2;
  var hs = S.boxes.map(boxHeight);
  var total = hs.reduce(function (a, b) { return a + b; }, 0) + 22 * (S.boxes.length - 1);
  var y = Math.max(L.topBarY + L.topBarH + 40, (H - total) / 2);

  S.boxes.forEach(function (box, i) {
    var bh = hs[i];
    ctx.fillStyle = 'rgba(28,32,40,.92)';
    ctx.fillRect(x, y, w, bh);
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 3;
    ctx.strokeRect(x + 1.5, y + 1.5, w - 3, bh - 3);

    var ty = y + 20 + sT.size;
    text(box.title, cx, ty, sT, { align: 'center', maxW: w - 60, weight: 900 });
    var tw = ctx.measureText(box.title).width;
    ctx.strokeStyle = sT.color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(cx - tw / 2, ty + 10);
    ctx.lineTo(cx + tw / 2, ty + 10);
    ctx.stroke();

    var ly = ty + 18;
    lines(box.body).forEach(function (ln) {
      if (ln.kind === 'gap') { ly += 14; return; }
      if (ln.kind === 'note') {
        ly += sN.size + 12;
        text(ln.text, cx, ly, sN, { align: 'center', maxW: w - 60, weight: 500 });
        return;
      }
      if (ln.kind === 'chip') {
        ly += sL.size + 22;
        var s = fitSize(ln.text, sL, w - 140, 900);
        use(sL, s, 900);
        var cw = ctx.measureText(ln.text).width + 44;
        ctx.strokeStyle = sT.color;
        ctx.lineWidth = 2.5;
        ctx.strokeRect(cx - cw / 2, ly - s - 8, cw, s + 20);
        text(ln.text, cx, ly, sL, { align: 'center', maxW: w - 140, weight: 900 });
        return;
      }
      ly += sL.size + 14;
      text(ln.text, cx, ly, sL, { align: 'center', maxW: w - 60, weight: 700 });
    });
    y += bh + 22;
  });
}

/* ── ② 선수 전적 / ③ 쉬는 시간 ─────────────────────────────── */
function drawSidePanel(side, withScore) {
  var pl = S.players[side], st = S.stats;
  var panelW = 430;
  var x = side === 0 ? 300 : W - 300 - panelW;
  var y = 268;
  // 이름 판
  var g = ctx.createLinearGradient(x, y, x + panelW, y);
  g.addColorStop(0, side === 0 ? '#c0212f' : '#12419c');
  g.addColorStop(1, side === 0 ? '#8c1f2a' : '#0d2f75');
  ctx.fillStyle = g;
  roundRect(ctx, x, y, panelW, 150, 14);
  ctx.fill();
  var tx = side === 0 ? x + panelW - 22 : x + 22;
  var align = side === 0 ? 'right' : 'left';
  drawNamePlate(side, tx, y + 46, align, panelW - 44);

  if (withScore) {
    var ss = S.style.score;
    var sx = side === 0 ? x + panelW + 60 : x - 60;
    text(pl.score || '0', sx, y + 122, ss, { align: 'center', weight: 900, shadow: 16 });
  }

  // 누적상금
  var py = y + 168;
  ctx.fillStyle = 'rgba(226,232,240,.92)';
  roundRect(ctx, x, py, panelW, 46, 8);
  ctx.fill();
  text(st.prizeLabel, x + panelW / 2, py + 33, S.style.prize,
    { align: 'center', color: '#0b0d11', maxW: panelW - 30, weight: 800 });
  ctx.fillStyle = 'rgba(18,22,30,.55)';
  roundRect(ctx, x, py + 52, panelW, 56, 8);
  ctx.fill();
  text(pl.prize || '', x + panelW / 2, py + 90, S.style.prize,
    { align: 'center', color: side === 0 ? '#ff6b6b' : '#7cb6ff',
      maxW: panelW - 30, weight: 900 });

  // VS 목록
  var vy = py + 128;
  ctx.fillStyle = 'rgba(18,22,30,.5)';
  var vs = lines(pl.vs);
  var vh = vs.length * (S.style.vsList.size + 18) + 20;
  roundRect(ctx, x, vy, panelW, vh, 8);
  ctx.fill();
  var ly = vy + 10;
  vs.forEach(function (ln) {
    ly += S.style.vsList.size + 18;
    text(ln.text, x + panelW / 2, ly - 6, S.style.vsList,
      { align: 'center', maxW: panelW - 30, weight: ln.kind === 'chip' ? 900 : 600 });
  });
}

function drawStatsCenter() {
  var st = S.stats, cx = W / 2;
  var y = 250;
  text(st.heading, cx, y, S.style.heading, { align: 'center', maxW: 420, weight: 700 });
  y += 46;
  text(st.sub, cx, y, S.style.sub, { align: 'center', maxW: 420, weight: 800 });
  y += 30;

  var bw = 360, bx = cx - bw / 2;
  st.rows.forEach(function (row) {
    ctx.fillStyle = 'rgba(28,32,40,.95)';
    roundRect(ctx, bx, y, bw, 44, 6); ctx.fill();
    text(row.label, cx, y + 31, S.style.rowLabel, { align: 'center', maxW: bw - 20, weight: 800 });
    y += 52;
    ctx.fillStyle = 'rgba(226,232,240,.94)';
    roundRect(ctx, bx, y, bw, 84, 6); ctx.fill();
    ctx.strokeStyle = 'rgba(90,100,120,.5)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(cx, y + 12); ctx.lineTo(cx, y + 72); ctx.stroke();
    text(row.a, cx - bw / 4, y + 62, S.style.rowValue,
      { align: 'center', color: '#d92d3c', maxW: bw / 2 - 20, weight: 900 });
    text(row.b, cx + bw / 4, y + 62, S.style.rowValue,
      { align: 'center', color: '#1552d0', maxW: bw / 2 - 20, weight: 900 });
    y += 96;
  });

  ctx.fillStyle = 'rgba(28,32,40,.95)';
  roundRect(ctx, bx, y, bw, 40, 6); ctx.fill();
  text(st.period, cx, y + 28, S.style.period, { align: 'center', maxW: bw - 20, weight: 700 });
  y += 48;

  ctx.fillStyle = 'rgba(28,32,40,.95)';
  roundRect(ctx, bx, y, bw, 42, 6); ctx.fill();
  text(st.muLabel, cx, y + 29, S.style.rowLabel, { align: 'center', maxW: bw - 20, weight: 800 });
  y += 50;
  ctx.fillStyle = 'rgba(226,232,240,.94)';
  roundRect(ctx, bx, y, bw, 94, 6); ctx.fill();
  ctx.strokeStyle = 'rgba(90,100,120,.5)'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(cx, y + 12); ctx.lineTo(cx, y + 82); ctx.stroke();
  text(st.muA, cx - bw / 4, y + 40, S.style.rowLabel,
    { align: 'center', color: '#d92d3c', maxW: bw / 2 - 20, weight: 900 });
  text(st.muAVal, cx - bw / 4, y + 82, S.style.rowValue,
    { align: 'center', color: '#d92d3c', maxW: bw / 2 - 20, weight: 900 });
  text(st.muB, cx + bw / 4, y + 40, S.style.rowLabel,
    { align: 'center', color: '#1552d0', maxW: bw / 2 - 20, weight: 900 });
  text(st.muBVal, cx + bw / 4, y + 82, S.style.rowValue,
    { align: 'center', color: '#1552d0', maxW: bw / 2 - 20, weight: 900 });
  y += 106;

  var foot = lines(st.foot).filter(function (l) { return l.kind !== 'gap'; });
  if (foot.length) {
    var fh = foot.length * (S.style.foot.size + 12) + 18;
    ctx.fillStyle = 'rgba(226,232,240,.94)';
    roundRect(ctx, bx, y, bw, fh, 6); ctx.fill();
    var fy = y + 8;
    foot.forEach(function (ln, i) {
      fy += S.style.foot.size + 12;
      text(ln.text, cx, fy - 4, S.style.foot,
        { align: 'center', maxW: bw - 24, weight: i === 0 ? 900 : 700 });
    });
    y += fh + 16;
  }
  if (st.timer) {
    text(st.timer, cx, Math.min(y + S.style.timer.size, H - 40), S.style.timer,
      { align: 'center', weight: 900, shadow: 14 });
  }
}

/* ── ④ 경기 결과 ───────────────────────────────────────────── */
function drawWinner() {
  var w = S.winner, cx = W / 2;
  text(w.vsText, cx, 560, S.style.vsBig, { align: 'center', weight: 800, shadow: 16 });

  [0, 1].forEach(function (side) {
    var pl = S.players[side];
    var plateW = 520;
    var x = side === 0 ? 120 : W - 120 - plateW;
    var y = 690;
    ctx.fillStyle = 'rgba(226,232,240,.86)';
    ctx.fillRect(x, y, plateW, 96);
    var inner = side === 0 ? x + 24 : x + plateW - 24;
    var align = side === 0 ? 'left' : 'right';
    // 닉네임 + 이름을 한 줄로
    var label = pl.nick + '  ' + pl.name + (pl.race ? ' ' + pl.race : '');
    text(label, inner, y + 46, S.style.pname,
      { align: align, color: '#12161d', maxW: plateW - 48, weight: 900 });
    text(pl.prize || '', inner, y + 84, S.style.prize,
      { align: align, color: side === 0 ? '#d92d3c' : '#1552d0',
        maxW: plateW - 48, weight: 900 });
    if (pl.delta) {
      text(pl.delta, x + plateW / 2, y + 190, S.style.vsBig,
        { align: 'center', maxW: plateW, weight: 800, shadow: 14 });
    }
    if (side === w.side) {
      var by = 420;
      if (w.ribbon) {
        setFont(S.style.ribbon.size, 800, S.style.ribbon.font);
        var rw = ctx.measureText(w.ribbon).width + 34;
        ctx.fillStyle = '#e0392b';
        roundRect(ctx, x + 8, by - 40, rw, 44, 8); ctx.fill();
        text(w.ribbon, x + 8 + rw / 2, by - 10, S.style.ribbon,
          { align: 'center', weight: 800 });
      }
      text(w.label, x + 12, by + S.style.winnerLabel.size, S.style.winnerLabel,
        { align: 'left', maxW: plateW, weight: 900, shadow: 18 });
    }
  });
}

/* ── ⑤ 다음 경기 ───────────────────────────────────────────── */
function drawNext() {
  var n = S.next, cx = W / 2;
  text(n.heading, cx, 470, S.style.nextHead,
    { align: 'center', maxW: 900, weight: 900, shadow: 20 });

  [0, 1].forEach(function (side) {
    var plateW = 520;
    var x = side === 0 ? 100 : W - 100 - plateW;
    var y = 640;
    ctx.fillStyle = 'rgba(226,232,240,.86)';
    ctx.fillRect(x, y, plateW, 118);
    var inner = side === 0 ? x + 26 : x + plateW - 26;
    var align = side === 0 ? 'left' : 'right';
    text(S.players[side].nick, inner, y + 44, S.style.nick,
      { align: align, color: '#3b4450', maxW: plateW - 52, weight: 500 });
    var pl = S.players[side];
    var label = pl.name + (pl.race ? ' ' + pl.race : '');
    text(label, inner, y + 100, S.style.pname,
      { align: align, color: '#12161d', maxW: plateW - 52, weight: 900 });
  });

  if (n.when) {
    ctx.fillStyle = 'rgba(10,13,19,.72)';
    ctx.fillRect(0, H - 190, W, 120);
    text(n.when, cx, H - 108, S.style.when, { align: 'center', maxW: W - 200, weight: 800 });
  }
}

/* ── 그리기 ────────────────────────────────────────────────── */
function draw() {
  var need = [S.logoSponsor, S.logoBroadcast, S.players[0].photo, S.players[1].photo];
  var got = [null, null, null, null];
  var left = need.length;
  need.forEach(function (src, i) {
    loadImage(src, function (im) { got[i] = im; if (--left === 0) paint(got); });
  });
}

function paint(g) {
  ctx.clearRect(0, 0, W, H);
  drawBackground();
  var dim = [false, false];
  if (S.type === 'winner') { dim[1 - S.winner.side] = true; }
  drawPhoto(0, g[2], dim[0]);
  drawPhoto(1, g[3], dim[1]);
  drawTopBar({ sponsor: g[0], broadcast: g[1] });

  if (S.type === 'matchup') {
    drawNamePlate(0, 310, 830, 'center', 520);
    drawNamePlate(1, W - 310, 830, 'center', 520);
    drawMatchup();
  } else if (S.type === 'stats' || S.type === 'score') {
    drawSidePanel(0, S.type === 'score');
    drawSidePanel(1, S.type === 'score');
    drawStatsCenter();
  } else if (S.type === 'winner') {
    drawWinner();
  } else if (S.type === 'next') {
    drawNext();
  }
  save();
}

/* ── 시즌 프로필 사진 ──────────────────────────────────────────
   같은 선수라도 시즌마다 사진이 다릅니다. ASL S19 김명운과 S20 김명운을
   따로 고를 수 있게, 있는 시즌만 목록에 올려 둡니다. */
function $(id) { return document.getElementById(id); }

function seasonPath(slug, season) {
  var nn = (season < 10 ? '0' : '') + season;
  return '../img/players/seasons/' + slug + '-s' + nn + '.webp';
}

function playerInfo(name) {
  return PLAYERS.find(function (p) { return p.name === name; });
}

/** 그 선수에게 있는 시즌만 목록에 채웁니다. 최근 시즌이 위로 옵니다. */
function fillSeasons(i) {
  var sel = $('season' + (i + 1));
  if (!sel) return;
  var info = playerInfo(S.players[i].name);
  var list = (info && info.seasons) || [];
  sel.innerHTML = '<option value="">사진 없음</option>' +
    list.slice().reverse().map(function (v) {
      return '<option value="' + v + '">ASL S' + v + '</option>';
    }).join('');
  sel.value = S.players[i].season === '' ? '' : String(S.players[i].season);
  sel.disabled = list.length === 0;
}

/** 고른 시즌 사진을 실제로 붙입니다. */
function applySeason(i, season) {
  var pl = S.players[i], info = playerInfo(pl.name);
  pl.season = season;
  if (season !== '' && info) {
    pl.photo = seasonPath(info.slug, parseInt(season, 10));
    pl.photoFrom = 'season';
  } else if (pl.photoFrom === 'season') {
    pl.photo = null;
    pl.photoFrom = null;
  }
  pl.zoom = 1; pl.ox = 0; pl.oy = 0;
  var z = $('zoom' + (i + 1)); if (z) z.value = 1;
}

function bind(id, get, set) {
  var el = $(id);
  if (!el) return;
  el.value = get();
  el.addEventListener('input', function () { set(el.value); draw(); });
}

function bindPhoto(id, onLoad) {
  var el = $(id);
  if (!el) return;
  el.addEventListener('change', function () {
    var f = el.files && el.files[0];
    if (!f) return;
    var fr = new FileReader();
    fr.onload = function () { onLoad(fr.result); draw(); };
    fr.readAsDataURL(f);
  });
}

/** 글자 모양(크기·색·폰트) 조절칸을 붙입니다. */
function bindStyle(key) {
  var st = S.style[key];
  if (!st) return;
  bind('st_' + key + '_size', function () { return st.size; },
    function (v) { st.size = parseInt(v, 10) || st.size; });
  bind('st_' + key + '_color', function () { return st.color; },
    function (v) { st.color = v; });
  bind('st_' + key + '_font', function () { return st.font; },
    function (v) { st.font = v; });
}

/** 지금 고른 CG 종류에 필요한 칸만 보여 줍니다. */
function showTypeFields() {
  document.querySelectorAll('[data-for]').forEach(function (el) {
    el.hidden = el.getAttribute('data-for').split(' ').indexOf(S.type) < 0;
  });
  document.querySelectorAll('[data-type]').forEach(function (b) {
    b.classList.toggle('on', b.getAttribute('data-type') === S.type);
  });
}

function setupControls() {
  document.querySelectorAll('[data-type]').forEach(function (b) {
    b.addEventListener('click', function () {
      S.type = b.getAttribute('data-type');
      showTypeFields();
      draw();
    });
  });

  bind('title', function () { return S.title; }, function (v) { S.title = v; });
  bind('sponsorText', function () { return S.sponsorText; }, function (v) { S.sponsorText = v; });
  bind('liveBadge', function () { return S.liveBadge; }, function (v) { S.liveBadge = v; });
  bind('bgLeft', function () { return S.bgLeft; }, function (v) { S.bgLeft = v; });
  bind('bgRight', function () { return S.bgRight; }, function (v) { S.bgRight = v; });

  bindPhoto('logoSponsor', function (d) { S.logoSponsor = d; });
  bindPhoto('logoBroadcast', function (d) { S.logoBroadcast = d; });
  $('logoSponsorClear').addEventListener('click', function () { S.logoSponsor = null; draw(); });
  $('logoBroadcastClear').addEventListener('click', function () { S.logoBroadcast = null; draw(); });

  [0, 1].forEach(function (i) {
    var n = i + 1;
    bind('nick' + n, function () { return S.players[i].nick; },
      function (v) { S.players[i].nick = v; });
    bind('name' + n, function () { return S.players[i].name; },
      function (v) {
        S.players[i].name = v;
        var hit = PLAYERS.find(function (p) { return p.name === v; });
        if (hit) { S.players[i].race = hit.race; $('race' + n).value = hit.race; }
        // 직접 올린 사진은 건드리지 않습니다 — 등록 사진일 때만 바꿉니다.
        if (S.players[i].photoFrom !== 'upload') {
          var ss = (hit && hit.seasons) || [];
          if (ss.length) {
            applySeason(i, String(ss[ss.length - 1]));   // 가장 최근 시즌
          } else if (hit && hit.photo) {
            S.players[i].photo = '../img/players/' + encodeURIComponent(hit.photo);
            S.players[i].photoFrom = 'lib';
            S.players[i].season = '';
            S.players[i].zoom = 1; S.players[i].ox = 0; S.players[i].oy = 0;
            var z = $('zoom' + n); if (z) z.value = 1;
          } else if (S.players[i].photoFrom === 'lib' ||
                     S.players[i].photoFrom === 'season') {
            S.players[i].photo = null;
            S.players[i].photoFrom = null;
            S.players[i].season = '';
          }
        }
        fillSeasons(i);
      });
    bind('race' + n, function () { return S.players[i].race; },
      function (v) { S.players[i].race = v; });
    bind('zoom' + n, function () { return S.players[i].zoom; },
      function (v) { S.players[i].zoom = parseFloat(v); });
    var sel = $('season' + n);
    if (sel) sel.addEventListener('change', function () { applySeason(i, sel.value); draw(); });
    bind('prize' + n, function () { return S.players[i].prize; },
      function (v) { S.players[i].prize = v; });
    bind('score' + n, function () { return S.players[i].score; },
      function (v) { S.players[i].score = v; });
    bind('delta' + n, function () { return S.players[i].delta; },
      function (v) { S.players[i].delta = v; });
    bind('vs' + n, function () { return S.players[i].vs; },
      function (v) { S.players[i].vs = v; });
    bindPhoto('photo' + n, function (d) {
      S.players[i].photo = d;
      S.players[i].photoFrom = 'upload';
      S.players[i].season = '';
      var sv = $('season' + n); if (sv) sv.value = '';
      S.players[i].zoom = 1; S.players[i].ox = 0; S.players[i].oy = 0;
      $('zoom' + n).value = 1;
    });
    $('photo' + n + 'Clear').addEventListener('click', function () {
      S.players[i].photo = null; S.players[i].photoFrom = null; draw();
    });
  });

  S.boxes.forEach(function (box, i) {
    bind('boxTitle' + i, function () { return box.title; }, function (v) { box.title = v; });
    bind('boxBody' + i, function () { return box.body; }, function (v) { box.body = v; });
  });

  var st = S.stats;
  bind('stHeading', function () { return st.heading; }, function (v) { st.heading = v; });
  bind('stSub', function () { return st.sub; }, function (v) { st.sub = v; });
  bind('stPrizeLabel', function () { return st.prizeLabel; }, function (v) { st.prizeLabel = v; });
  bind('stPeriod', function () { return st.period; }, function (v) { st.period = v; });
  bind('stMuLabel', function () { return st.muLabel; }, function (v) { st.muLabel = v; });
  bind('stMuA', function () { return st.muA; }, function (v) { st.muA = v; });
  bind('stMuAVal', function () { return st.muAVal; }, function (v) { st.muAVal = v; });
  bind('stMuB', function () { return st.muB; }, function (v) { st.muB = v; });
  bind('stMuBVal', function () { return st.muBVal; }, function (v) { st.muBVal = v; });
  bind('stFoot', function () { return st.foot; }, function (v) { st.foot = v; });
  bind('stTimer', function () { return st.timer; }, function (v) { st.timer = v; });
  st.rows.forEach(function (row, i) {
    bind('stRowLabel' + i, function () { return row.label; }, function (v) { row.label = v; });
    bind('stRowA' + i, function () { return row.a; }, function (v) { row.a = v; });
    bind('stRowB' + i, function () { return row.b; }, function (v) { row.b = v; });
  });

  bind('winVs', function () { return S.winner.vsText; }, function (v) { S.winner.vsText = v; });
  bind('winLabel', function () { return S.winner.label; }, function (v) { S.winner.label = v; });
  bind('winRibbon', function () { return S.winner.ribbon; }, function (v) { S.winner.ribbon = v; });
  bind('winSide', function () { return String(S.winner.side); },
    function (v) { S.winner.side = parseInt(v, 10) || 0; });
  bind('nextHeading', function () { return S.next.heading; }, function (v) { S.next.heading = v; });
  bind('nextWhen', function () { return S.next.when; }, function (v) { S.next.when = v; });

  Object.keys(S.style).forEach(bindStyle);

  $('swap').addEventListener('click', function () {
    S.players.reverse();
    S.winner.side = 1 - S.winner.side;
    fillForm(); draw();
  });
  $('reset').addEventListener('click', function () {
    if (!confirm('처음 상태로 되돌립니다. 올린 사진도 지워집니다.')) return;
    localStorage.removeItem(KEY);
    location.reload();
  });
  $('download').addEventListener('click', download);
  $('exportJson').addEventListener('click', exportJson);
  $('importJson').addEventListener('change', importJson);
}

function fillForm() {
  [0, 1].forEach(function (i) {
    var n = i + 1, p = S.players[i];
    ['nick', 'name', 'race', 'zoom', 'prize', 'score', 'delta', 'vs'].forEach(function (k) {
      var el = $(k + n); if (el) el.value = p[k];
    });
    fillSeasons(i);
  });
  ['title', 'sponsorText', 'liveBadge', 'bgLeft', 'bgRight'].forEach(function (k) {
    var el = $(k); if (el) el.value = S[k];
  });
  S.boxes.forEach(function (b, i) {
    if ($('boxTitle' + i)) $('boxTitle' + i).value = b.title;
    if ($('boxBody' + i)) $('boxBody' + i).value = b.body;
  });
  var st = S.stats;
  [['stHeading', 'heading'], ['stSub', 'sub'], ['stPrizeLabel', 'prizeLabel'],
   ['stPeriod', 'period'], ['stMuLabel', 'muLabel'], ['stMuA', 'muA'],
   ['stMuAVal', 'muAVal'], ['stMuB', 'muB'], ['stMuBVal', 'muBVal'],
   ['stFoot', 'foot'], ['stTimer', 'timer']].forEach(function (p) {
    if ($(p[0])) $(p[0]).value = st[p[1]];
  });
  st.rows.forEach(function (row, i) {
    if ($('stRowLabel' + i)) $('stRowLabel' + i).value = row.label;
    if ($('stRowA' + i)) $('stRowA' + i).value = row.a;
    if ($('stRowB' + i)) $('stRowB' + i).value = row.b;
  });
  if ($('winVs')) $('winVs').value = S.winner.vsText;
  if ($('winLabel')) $('winLabel').value = S.winner.label;
  if ($('winRibbon')) $('winRibbon').value = S.winner.ribbon;
  if ($('winSide')) $('winSide').value = String(S.winner.side);
  if ($('nextHeading')) $('nextHeading').value = S.next.heading;
  if ($('nextWhen')) $('nextWhen').value = S.next.when;
  Object.keys(S.style).forEach(function (k) {
    var s2 = S.style[k];
    if ($('st_' + k + '_size')) $('st_' + k + '_size').value = s2.size;
    if ($('st_' + k + '_color')) $('st_' + k + '_color').value = s2.color;
    if ($('st_' + k + '_font')) $('st_' + k + '_font').value = s2.font;
  });
}

/* 캔버스에서 사진을 끌어 옮기고, 휠로 키우고 줄입니다. */
function canvasPos(ev) {
  var r = cv.getBoundingClientRect();
  return { x: (ev.clientX - r.left) * (W / r.width), y: (ev.clientY - r.top) * (H / r.height) };
}

function hitPhoto(pos) {
  for (var i = 0; i < 2; i++) {
    var r = photoRect(i);
    if (pos.x >= r.x && pos.x <= r.x + r.w && pos.y >= r.y && pos.y <= r.y + r.h) return i;
  }
  return -1;
}

function setupCanvasDrag() {
  var dragging = -1, last = null;
  cv.addEventListener('mousedown', function (e) {
    var pos = canvasPos(e);
    dragging = hitPhoto(pos);
    last = pos;
    if (dragging >= 0) cv.style.cursor = 'grabbing';
  });
  window.addEventListener('mousemove', function (e) {
    if (dragging < 0) return;
    var pos = canvasPos(e);
    S.players[dragging].ox += pos.x - last.x;
    S.players[dragging].oy += pos.y - last.y;
    last = pos;
    draw();
  });
  window.addEventListener('mouseup', function () {
    dragging = -1; cv.style.cursor = '';
  });
  cv.addEventListener('wheel', function (e) {
    var i = hitPhoto(canvasPos(e));
    if (i < 0) return;
    e.preventDefault();
    var p = S.players[i];
    p.zoom = Math.min(4, Math.max(0.4, p.zoom * (e.deltaY < 0 ? 1.06 : 0.94)));
    var z = $('zoom' + (i + 1)); if (z) z.value = p.zoom;
    draw();
  }, { passive: false });

  // 사진 파일을 미리보기에 바로 끌어다 놓기
  cv.addEventListener('dragover', function (e) { e.preventDefault(); });
  cv.addEventListener('drop', function (e) {
    e.preventDefault();
    var f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (!f) return;
    var i = hitPhoto(canvasPos(e));
    if (i < 0) return;
    var fr = new FileReader();
    fr.onload = function () {
      S.players[i].photo = fr.result;
      S.players[i].photoFrom = 'upload';
      S.players[i].zoom = 1; S.players[i].ox = 0; S.players[i].oy = 0;
      var z = $('zoom' + (i + 1)); if (z) z.value = 1;
      draw();
    };
    fr.readAsDataURL(f);
  });
}

function stamp() {
  var d = new Date();
  function p(n) { return (n < 10 ? '0' : '') + n; }
  return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + '-' +
    p(d.getHours()) + p(d.getMinutes());
}

function download() {
  var a = document.createElement('a');
  a.download = 'cg-' + S.type + '-' + S.players[0].name + '-vs-' +
    S.players[1].name + '-' + stamp() + '.png';
  a.href = cv.toDataURL('image/png');
  a.click();
}

function exportJson() {
  var a = document.createElement('a');
  a.download = 'cg-setting-' + stamp() + '.json';
  a.href = 'data:application/json;charset=utf-8,' +
    encodeURIComponent(JSON.stringify(S, null, 1));
  a.click();
}

function importJson(ev) {
  var f = ev.target.files && ev.target.files[0];
  if (!f) return;
  var fr = new FileReader();
  fr.onload = function () {
    try {
      var got = JSON.parse(fr.result), base = defaults();
      S = Object.assign(base, got);
      S.style = Object.assign(base.style, got.style || {});
      fillForm(); showTypeFields(); draw();
    } catch (e) { alert('설정 파일을 읽지 못했습니다.'); }
  };
  fr.readAsText(f);
}

/* ── 저장 ──────────────────────────────────────────────────── */
var KEY = 'sc-cg-v2';

function save() {
  try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { /* 용량 초과는 무시 */ }
}

function load() {
  try {
    var raw = localStorage.getItem(KEY);
    if (!raw) return;
    var got = JSON.parse(raw), base = defaults();
    S = Object.assign(base, got);
    S.style = Object.assign(base.style, got.style || {});
    S.stats = Object.assign(base.stats, got.stats || {});
    S.winner = Object.assign(base.winner, got.winner || {});
    S.next = Object.assign(base.next, got.next || {});
  } catch (e) { /* 깨진 값이면 기본값으로 */ }
}

load();
setupControls();
fillForm();
showTypeFields();
setupCanvasDrag();
draw();
