/* 끝장전 대진표 CG 제작 툴.
   1920x1080 캔버스에 직접 그립니다 — 바깥 라이브러리를 쓰지 않아서
   인터넷이 끊겨도 되고, 내보낸 PNG 가 화면에 보이는 것과 정확히 같습니다. */

var W = 1920, H = 1080;
var cv = document.getElementById('cv');
var ctx = cv.getContext('2d');
cv.width = W; cv.height = H;

var RACE_LABEL = { T: '테란', P: '프로토스', Z: '저그', '': '' };
var RACE_COLOR = { T: '#4a9eff', P: '#f5c518', Z: '#ff6b6b' };
var FONT = "'Pretendard','Malgun Gothic','맑은 고딕',system-ui,sans-serif";

/* ── 화면 배치 (1920x1080 기준) ─────────────────────────────── */
var L = {
  panelW: 470,                       // 좌우 선수 칸 너비
  topBarY: 52, topBarH: 92,
  photo: { x: 34, y: 176, w: 402, h: 604, r: 16 },
  namePlateY: 812,
  boxX: 512, boxW: 896, boxTop: 196, boxGap: 22,
  boxPad: 20, titleSize: 38, lineSize: 25, noteSize: 20
};

/* ── 상태 ──────────────────────────────────────────────────── */
var S = {
  title: '끝장전',
  titleColor: '#4aa8ff',
  sponsorText: '',
  bgLeft: '#8c1f2a',
  bgRight: '#123a78',
  players: [
    { nick: 'RoyaL', name: '김지성', race: 'T', photo: null, photoFrom: null,
      zoom: 1, ox: 0, oy: 0 },
    { nick: 'Bisu', name: '김택용', race: 'P', photo: null, photoFrom: null,
      zoom: 1, ox: 0, oy: 0 }
  ],
  logoSponsor: null,
  logoBroadcast: null,
  boxes: [
    { title: '경기 방식', body: '두 선수가 9세트 풀세트 진행\n( 8대 0 상황에서도 마지막 9세트 진행 )' },
    {
      title: '상금',
      body: '매 세트 승리시 10만원\n[더블 찬스]\n세트 시작 전 선수당 1일 1회 더블 찬스 사용 가능\n' +
        '더블 찬스가 적용된 세트의 승자는 두배의 상금 획득 (20만원)\n* ※ 중복 사용 불가\n' +
        '[올킬 상금 30만원 (총 상금 140만원)]'
    },
    {
      title: '사용맵',
      body: '오디세이, 컬러리스 페이트, 녹아웃, 애티튜드,\n아이올로스, 백룸, 옥타곤 (ASL 시즌22 공식맵)\n' +
        '* 경기 시작 전 선수당 한 개씩 총 두 개 맵 제거'
    }
  ]
};

var imgCache = {};      // dataURL → Image

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

function setFont(size, weight) {
  ctx.font = (weight || 700) + ' ' + size + 'px ' + FONT;
}

/** 글자가 칸을 넘치면 자동으로 줄여 그립니다. */
function fitText(text, size, weight, maxW) {
  var s = size;
  setFont(s, weight);
  while (s > 10 && ctx.measureText(text).width > maxW) {
    s -= 1;
    setFont(s, weight);
  }
  return s;
}

function drawCover(im, x, y, w, h, zoom, ox, oy, radius) {
  ctx.save();
  roundRect(ctx, x, y, w, h, radius || 0);
  ctx.clip();
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
   [글자]  → 노란 테두리 강조 칩
   * 글자  → 작게, 흐린 색
   그 외   → 보통 흰 글자                                        */
function parseLine(raw) {
  var t = raw.trim();
  if (!t) return { kind: 'gap', text: '' };
  if (t[0] === '[' && t[t.length - 1] === ']') {
    return { kind: 'chip', text: t.slice(1, -1).trim() };
  }
  if (t[0] === '*') return { kind: 'note', text: t.slice(1).trim() };
  return { kind: 'line', text: t };
}

function boxLines(box) {
  return String(box.body || '').split('\n').map(parseLine);
}

function boxHeight(box) {
  var h = L.boxPad + L.titleSize + 16 + L.boxPad;   // 제목 + 밑줄 여백
  boxLines(box).forEach(function (ln) {
    if (ln.kind === 'gap') h += 14;
    else if (ln.kind === 'note') h += L.noteSize + 12;
    else if (ln.kind === 'chip') h += L.lineSize + 22;
    else h += L.lineSize + 12;
  });
  return h;
}

/* ── 각 영역 ───────────────────────────────────────────────── */
function drawBackground() {
  ctx.fillStyle = '#15171c';
  ctx.fillRect(0, 0, W, H);

  // 좌우 선수 칸 뒤로 깔리는 색
  [[0, S.bgLeft], [W - L.panelW, S.bgRight]].forEach(function (pair, i) {
    var x = pair[0];
    var g = ctx.createLinearGradient(x, 0, x + L.panelW, H);
    g.addColorStop(0, pair[1]);
    g.addColorStop(1, i === 0 ? '#2a1013' : '#0d1b33');
    ctx.fillStyle = g;
    ctx.fillRect(x, 0, L.panelW, H);
    // 가운데 쪽으로 자연스럽게 어두워지게
    var f = ctx.createLinearGradient(
      i === 0 ? x + L.panelW - 150 : x + 150, 0,
      i === 0 ? x + L.panelW : x, 0);
    f.addColorStop(0, 'rgba(21,23,28,0)');
    f.addColorStop(1, 'rgba(21,23,28,1)');
    ctx.fillStyle = f;
    ctx.fillRect(i === 0 ? x + L.panelW - 150 : x, 0, 150, H);
  });

  // 가운데 은은한 사선 무늬
  ctx.save();
  ctx.globalAlpha = 0.045;
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 2;
  for (var gx = L.panelW - 200; gx < W - L.panelW + 200; gx += 34) {
    ctx.beginPath();
    ctx.moveTo(gx, 0);
    ctx.lineTo(gx - 260, H);
    ctx.stroke();
  }
  ctx.restore();
}

function drawTopBar(imgs) {
  var y = L.topBarY, h = L.topBarH;
  var cx = W / 2;
  var titleSize = 58;
  setFont(titleSize, 900);
  var titleW = ctx.measureText(S.title).width;

  var sponsorW = 0;
  if (imgs.sponsor) {
    sponsorW = imgs.sponsor.width * (h / imgs.sponsor.height);
    sponsorW = Math.min(sponsorW, 420);
  } else if (S.sponsorText) {
    setFont(42, 800);
    sponsorW = ctx.measureText(S.sponsorText).width;
  }

  var divW = sponsorW ? 46 : 0;
  var total = sponsorW + divW + titleW;
  var startX = cx - total / 2;

  if (imgs.sponsor) {
    drawContain(imgs.sponsor, startX + sponsorW / 2, y + h / 2, sponsorW, h);
  } else if (S.sponsorText) {
    setFont(42, 800);
    ctx.fillStyle = '#e8ecf3';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(S.sponsorText, startX, y + h / 2);
  }

  if (divW) {
    ctx.strokeStyle = 'rgba(255,255,255,.35)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(startX + sponsorW + divW / 2, y + 12);
    ctx.lineTo(startX + sponsorW + divW / 2, y + h - 12);
    ctx.stroke();
  }

  setFont(titleSize, 900);
  ctx.fillStyle = S.titleColor;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(S.title, startX + sponsorW + divW, y + h / 2 + 2);

  if (imgs.broadcast) {
    var bw = Math.min(imgs.broadcast.width * (72 / imgs.broadcast.height), 240);
    drawContain(imgs.broadcast, W - 40 - bw / 2, y + h / 2, bw, 72);
  }
}

function photoRect(side) {
  var p = L.photo;
  var x = side === 0 ? p.x : W - L.panelW + p.x;
  return { x: x, y: p.y, w: p.w, h: p.h, r: p.r };
}

function drawPlayer(side, im) {
  var pl = S.players[side];
  var r = photoRect(side);

  // 사진 자리 (없으면 안내 문구)
  ctx.save();
  roundRect(ctx, r.x, r.y, r.w, r.h, r.r);
  ctx.fillStyle = 'rgba(0,0,0,.30)';
  ctx.fill();
  ctx.restore();

  if (im) {
    drawCover(im, r.x, r.y, r.w, r.h, pl.zoom, pl.ox, pl.oy, r.r);
    // 아래쪽을 어둡게 깔아 이름이 잘 보이게
    ctx.save();
    roundRect(ctx, r.x, r.y, r.w, r.h, r.r);
    ctx.clip();
    var g = ctx.createLinearGradient(0, r.y + r.h - 220, 0, r.y + r.h);
    g.addColorStop(0, 'rgba(0,0,0,0)');
    g.addColorStop(1, 'rgba(0,0,0,.72)');
    ctx.fillStyle = g;
    ctx.fillRect(r.x, r.y + r.h - 220, r.w, 220);
    ctx.restore();
  } else {
    ctx.save();
    ctx.setLineDash([10, 8]);
    ctx.strokeStyle = 'rgba(255,255,255,.32)';
    ctx.lineWidth = 3;
    roundRect(ctx, r.x, r.y, r.w, r.h, r.r);
    ctx.stroke();
    ctx.setLineDash([]);
    setFont(26, 700);
    ctx.fillStyle = 'rgba(255,255,255,.55)';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('선수 사진을 올려 주세요', r.x + r.w / 2, r.y + r.h / 2 - 16);
    setFont(20, 500);
    ctx.fillText('여기로 끌어다 놓아도 됩니다', r.x + r.w / 2, r.y + r.h / 2 + 22);
    ctx.restore();
  }

  var cx = r.x + r.w / 2;

  // 닉네임
  if (pl.nick) {
    var ns = fitText(pl.nick, 44, 500, r.w - 20);
    ctx.fillStyle = 'rgba(255,255,255,.88)';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'alphabetic';
    setFont(ns, 500);
    ctx.fillText(pl.nick, cx, L.namePlateY);
  }

  // 이름 + 종족
  var label = pl.name + (pl.race ? ' ' + pl.race : '');
  var size = fitText(label, 70, 900, r.w + 26);
  setFont(size, 900);
  var full = ctx.measureText(label).width;
  var nameOnlyW = ctx.measureText(pl.name).width;
  var startX = cx - full / 2;
  ctx.textAlign = 'left';
  ctx.shadowColor = 'rgba(0,0,0,.55)';
  ctx.shadowBlur = 12;
  ctx.fillStyle = '#ffffff';
  ctx.fillText(pl.name, startX, L.namePlateY + 76);
  if (pl.race) {
    ctx.fillStyle = RACE_COLOR[pl.race] || '#ffffff';
    ctx.fillText(' ' + pl.race, startX + nameOnlyW, L.namePlateY + 76);
  }
  ctx.shadowBlur = 0;
}

function drawBoxes() {
  var heights = S.boxes.map(boxHeight);
  var totalH = heights.reduce(function (a, b) { return a + b; }, 0) +
    L.boxGap * (S.boxes.length - 1);
  var avail = H - L.boxTop - 60;
  var y = L.boxTop + Math.max(0, (avail - totalH) / 2);

  S.boxes.forEach(function (box, i) {
    var h = heights[i];
    var x = L.boxX, w = L.boxW;

    ctx.fillStyle = 'rgba(38,40,46,.94)';
    roundRect(ctx, x, y, w, h, 4);
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,.85)';
    ctx.lineWidth = 3;
    ctx.beginPath();                       // 위쪽에만 밝은 선
    ctx.moveTo(x, y + 1.5);
    ctx.lineTo(x + w, y + 1.5);
    ctx.stroke();
    ctx.strokeStyle = 'rgba(255,255,255,.14)';
    ctx.lineWidth = 1.5;
    roundRect(ctx, x, y, w, h, 4);
    ctx.stroke();

    var cx = x + w / 2;
    var ty = y + L.boxPad + L.titleSize * 0.8;

    setFont(L.titleSize, 900);
    ctx.fillStyle = '#ffd24a';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'alphabetic';
    ctx.fillText(box.title, cx, ty);
    var tw = ctx.measureText(box.title).width;
    ctx.strokeStyle = '#ffd24a';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(cx - tw / 2, ty + 10);
    ctx.lineTo(cx + tw / 2, ty + 10);
    ctx.stroke();

    var ly = ty + 26;
    boxLines(box).forEach(function (ln) {
      if (ln.kind === 'gap') { ly += 14; return; }
      if (ln.kind === 'note') {
        ly += L.noteSize + 12;
        setFont(L.noteSize, 500);
        ctx.fillStyle = 'rgba(232,236,243,.62)';
        ctx.fillText(ln.text, cx, ly);
        return;
      }
      if (ln.kind === 'chip') {
        ly += L.lineSize + 22;
        setFont(L.lineSize, 800);
        var cw = ctx.measureText(ln.text).width + 34;
        var ch = L.lineSize + 16;
        ctx.fillStyle = 'rgba(255,210,74,.14)';
        roundRect(ctx, cx - cw / 2, ly - ch + 8, cw, ch, 3);
        ctx.fill();
        ctx.strokeStyle = '#ffd24a';
        ctx.lineWidth = 2;
        roundRect(ctx, cx - cw / 2, ly - ch + 8, cw, ch, 3);
        ctx.stroke();
        ctx.fillStyle = '#ffe9a8';
        ctx.fillText(ln.text, cx, ly);
        return;
      }
      ly += L.lineSize + 12;
      var s = fitText(ln.text, L.lineSize, 600, L.boxW - L.boxPad * 2 - 20);
      setFont(s, 600);
      ctx.fillStyle = '#ffffff';
      ctx.fillText(ln.text, cx, ly);
    });

    y += h + L.boxGap;
  });
}

/* ── 전체 그리기 ───────────────────────────────────────────── */
var pending = 0;
function draw() {
  var need = [S.logoSponsor, S.logoBroadcast, S.players[0].photo, S.players[1].photo];
  var got = [null, null, null, null];
  var left = need.length;
  need.forEach(function (src, i) {
    loadImage(src, function (im) {
      got[i] = im;
      if (--left === 0) paint(got);
    });
  });
}

function paint(g) {
  ctx.clearRect(0, 0, W, H);
  drawBackground();
  drawTopBar({ sponsor: g[0], broadcast: g[1] });
  drawPlayer(0, g[2]);
  drawPlayer(1, g[3]);
  drawBoxes();
  save();
}

/* ── 조작 ──────────────────────────────────────────────────── */
function $(id) { return document.getElementById(id); }

function bind(id, get, set) {
  var el = $(id);
  if (!el) return;
  el.value = get();
  var ev = (el.type === 'range' || el.type === 'color') ? 'input' : 'input';
  el.addEventListener(ev, function () { set(el.value); draw(); });
}

function bindPhoto(id, onLoad) {
  var el = $(id);
  el.addEventListener('change', function () {
    var f = el.files && el.files[0];
    if (!f) return;
    var fr = new FileReader();
    fr.onload = function () { onLoad(fr.result); draw(); };
    fr.readAsDataURL(f);
  });
}

function setupControls() {
  bind('title', function () { return S.title; }, function (v) { S.title = v; });
  bind('titleColor', function () { return S.titleColor; }, function (v) { S.titleColor = v; });
  bind('sponsorText', function () { return S.sponsorText; }, function (v) { S.sponsorText = v; });
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
        // 올려 둔 선수 사진이 있으면 바로 붙입니다.
        // 직접 올리신 사진은 건드리지 않습니다 — 등록 사진일 때만 바꿉니다.
        if (S.players[i].photoFrom !== 'upload') {
          if (hit && hit.photo) {
            S.players[i].photo = '../img/players/' + encodeURIComponent(hit.photo);
            S.players[i].photoFrom = 'lib';
            S.players[i].zoom = 1; S.players[i].ox = 0; S.players[i].oy = 0;
            var z = $('zoom' + n); if (z) z.value = 1;
          } else if (S.players[i].photoFrom === 'lib') {
            // 사진이 없는 선수로 바꿨는데 앞 선수 얼굴이 남아 있으면 안 됩니다.
            S.players[i].photo = null; S.players[i].photoFrom = null;
          }
        }
      });
    bind('race' + n, function () { return S.players[i].race; },
      function (v) { S.players[i].race = v; });
    bind('zoom' + n, function () { return S.players[i].zoom; },
      function (v) { S.players[i].zoom = parseFloat(v); });
    bindPhoto('photo' + n, function (d) {
      S.players[i].photo = d;
      S.players[i].photoFrom = 'upload';       // 직접 올린 사진이 항상 우선입니다
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

  $('swap').addEventListener('click', function () {
    S.players.reverse();
    fillForm();
    draw();
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
    $('nick' + n).value = p.nick;
    $('name' + n).value = p.name;
    $('race' + n).value = p.race;
    $('zoom' + n).value = p.zoom;
  });
  $('title').value = S.title;
  $('titleColor').value = S.titleColor;
  $('sponsorText').value = S.sponsorText;
  $('bgLeft').value = S.bgLeft;
  $('bgRight').value = S.bgRight;
  S.boxes.forEach(function (b, i) {
    // 불러온 설정의 상자 개수가 화면보다 많을 수 있어 있는 칸만 채웁니다.
    if ($('boxTitle' + i)) $('boxTitle' + i).value = b.title;
    if ($('boxBody' + i)) $('boxBody' + i).value = b.body;
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
  var drag = null;
  cv.addEventListener('mousedown', function (ev) {
    var pos = canvasPos(ev);
    var i = hitPhoto(pos);
    if (i < 0 || !S.players[i].photo) return;
    drag = { i: i, x: pos.x, y: pos.y, ox: S.players[i].ox, oy: S.players[i].oy };
    ev.preventDefault();
  });
  window.addEventListener('mousemove', function (ev) {
    if (!drag) return;
    var pos = canvasPos(ev);
    S.players[drag.i].ox = drag.ox + (pos.x - drag.x);
    S.players[drag.i].oy = drag.oy + (pos.y - drag.y);
    draw();
  });
  window.addEventListener('mouseup', function () { drag = null; });
  cv.addEventListener('wheel', function (ev) {
    var i = hitPhoto(canvasPos(ev));
    if (i < 0 || !S.players[i].photo) return;
    ev.preventDefault();
    var p = S.players[i];
    p.zoom = Math.min(4, Math.max(0.4, p.zoom * (ev.deltaY < 0 ? 1.06 : 1 / 1.06)));
    $('zoom' + (i + 1)).value = p.zoom;
    draw();
  }, { passive: false });

  // 캔버스에 파일을 끌어다 놓으면 가까운 쪽 선수 사진이 됩니다.
  cv.addEventListener('dragover', function (ev) { ev.preventDefault(); });
  cv.addEventListener('drop', function (ev) {
    ev.preventDefault();
    var f = ev.dataTransfer.files && ev.dataTransfer.files[0];
    if (!f || !/^image\//.test(f.type)) return;
    var pos = canvasPos(ev);
    var i = hitPhoto(pos);
    if (i < 0) i = pos.x < W / 2 ? 0 : 1;
    var fr = new FileReader();
    fr.onload = function () {
      S.players[i].photo = fr.result;
      S.players[i].zoom = 1; S.players[i].ox = 0; S.players[i].oy = 0;
      $('zoom' + (i + 1)).value = 1;
      draw();
    };
    fr.readAsDataURL(f);
  });
}

/* ── 내보내기 · 저장 ───────────────────────────────────────── */
function stamp() {
  var d = new Date();
  function p(n) { return (n < 10 ? '0' : '') + n; }
  return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) +
    '-' + p(d.getHours()) + p(d.getMinutes());
}

function download() {
  cv.toBlob(function (blob) {
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = '끝장전-' + S.players[0].name + '-vs-' + S.players[1].name +
      '-' + stamp() + '.png';
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }, 'image/png');
}

function exportJson() {
  var blob = new Blob([JSON.stringify(S, null, 1)], { type: 'application/json' });
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = '끝장전-CG-설정-' + stamp() + '.json';
  document.body.appendChild(a);
  a.click();
  setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}

function importJson(ev) {
  var f = ev.target.files && ev.target.files[0];
  if (!f) return;
  var fr = new FileReader();
  fr.onload = function () {
    try {
      var got = JSON.parse(fr.result);
      Object.keys(got).forEach(function (k) { S[k] = got[k]; });
      fillForm();
      draw();
      note('설정을 불러왔습니다.');
    } catch (e) {
      note('설정 파일을 읽지 못했습니다: ' + e.message, true);
    }
  };
  fr.readAsText(f);
  ev.target.value = '';
}

var KEY = 'sc-cg-v1';
var saveTimer = null;
function save() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(function () {
    try {
      localStorage.setItem(KEY, JSON.stringify(S));
      note('자동 저장됨 — 이 브라우저에서 새로고침해도 그대로 있습니다.');
    } catch (e) {
      note('사진이 커서 자동 저장을 못 했습니다. "설정 내보내기"로 파일에 저장하세요.', true);
    }
  }, 400);
}
function restore() {
  try {
    var raw = localStorage.getItem(KEY);
    if (!raw) return;
    var got = JSON.parse(raw);
    Object.keys(got).forEach(function (k) { S[k] = got[k]; });
  } catch (e) { /* 저장본이 깨졌으면 그냥 기본값으로 갑니다 */ }
}
function note(msg, bad) {
  var el = $('note');
  el.textContent = msg;
  el.className = 'note' + (bad ? ' bad' : '');
}

/* ── 선수 자동완성 ─────────────────────────────────────────── */
function setupDatalist() {
  var dl = document.getElementById('playerList');
  dl.innerHTML = PLAYERS.map(function (p) {
    return '<option value="' + p.name + '">' + RACE_LABEL[p.race] +
      (p.from ? ' · ' + p.from : '') + '</option>';
  }).join('');
}

/* ── 시작 ──────────────────────────────────────────────────── */
restore();
setupDatalist();
setupControls();
fillForm();
setupCanvasDrag();
draw();
if (document.fonts && document.fonts.ready) {
  document.fonts.ready.then(draw);   // 폰트가 늦게 오면 다시 그립니다
}
