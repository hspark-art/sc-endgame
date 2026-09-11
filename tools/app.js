/* 스타크래프트 끝장전 기록실 — 허브 페이지 앱.
   데이터(const D)는 빌드할 때 이 스크립트 위에 그대로 박아 넣습니다.
   서버가 없어도 파일만 열면 동작합니다. */

var RACE_LABEL = { T: '테란', P: '프로토스', Z: '저그' };
var RACE_ORDER = ['T', 'P', 'Z'];
var MU_KEYS = ['PvT', 'TvZ', 'PvZ'];
var RACE_COLOR = { T: 'var(--t)', P: 'var(--p)', Z: 'var(--z)' };

function $(sel, el) { return (el || document).querySelector(sel); }
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
  });
}
function pct(w, l) { var t = w + l; return t ? (w / t * 100).toFixed(1) + '%' : '-'; }
function pctNum(w, l) { var t = w + l; return t ? w / t * 100 : 0; }
function raceBadge(r) { return '<span class="race ' + (r || '') + '">' + (r || '?') + '</span>'; }
function pageOf(slug) { return 'p/' + encodeURIComponent(slug) + '.html'; }
function hrefOf(name) {
  var s = D.slugs[name];
  return s ? pageOf(s) : null;
}
function nameLink(name, race, extraClass) {
  var href = hrefOf(name);
  var inner = (race ? raceBadge(race) : '') +
    '<span class="nm-link' + (extraClass ? ' ' + extraClass : '') + '">' + esc(name) + '</span>';
  return href ? '<a href="' + href + '">' + inner + '</a>' : inner;
}

var view = $('#view');
var tabsEl = $('#tabs');

/* ── 상단 요약 ─────────────────────────────────────────────── */
$('#strip').innerHTML = [
  ['총 매치', D.global.totalMatches.toLocaleString()],
  ['총 세트', D.global.totalSets.toLocaleString()],
  ['참가 선수', D.global.totalPlayers + '명'],
  ['기간', D.global.firstDate + ' ~ ' + D.global.lastDate]
].map(function (kv) {
  return '<div class="item">' + kv[0] + '<b>' + kv[1] + '</b></div>';
}).join('');

/* ── 라이브 방송 배너 ──────────────────────────────────────────
   SOOP(구 아프리카TV)의 공개 station API 로 지금 방송 중인지 확인합니다.
   방송 번호(broad_no)는 방송할 때마다 바뀌므로 하드코딩하지 않고 매번 받아옵니다.
   그래서 "방송 시작 → 페이지 새로고침 없이 자동 반영" 이 됩니다. */
var SOOP_BJID = 'talent';
var SOOP_STATION_URL = 'https://www.sooplive.com/station/talent';
var liveBannerEl = $('#liveBanner');

function renderLiveOffline() {
  liveBannerEl.innerHTML = '<div class="livecard"><div class="live-head">' +
    '<span class="live-dot" style="background:#4b5565;animation:none"></span>' +
    '<span class="live-badge" style="color:var(--dim)">OFF AIR</span>' +
    '</div><div class="live-off">지금은 방송 중이 아닙니다 — ' +
    '<a href="' + SOOP_STATION_URL + '" target="_blank" rel="noopener">SOOP 방송국에서 방송 알림 받기</a>' +
    '</div></div>';
}

function renderLiveOnline(broadNo, title, viewers) {
  var liveUrl = 'https://play.sooplive.com/' + SOOP_BJID + '/' + broadNo;
  var thumb = 'https://liveimg.sooplive.com/h/' + broadNo + '.webp?t=' + Date.now();
  liveBannerEl.innerHTML = '<div class="livecard live">' +
    '<div class="live-head"><span class="live-dot"></span><span class="live-badge">LIVE</span>' +
    '<span class="live-title">' + esc(title || '끝장전 생방송 중') + '</span>' +
    (viewers ? '<span class="live-viewer">👁 ' + Number(viewers).toLocaleString() + '명 시청 중</span>' : '') +
    '</div>' +
    '<a class="live-thumb-link" href="' + liveUrl + '" target="_blank" rel="noopener">' +
    '<img class="live-thumb" src="' + thumb + '" alt="방송 미리보기" loading="eager">' +
    '<div class="live-play">▶ SOOP에서 바로 시청하기</div>' +
    '</a></div>';
}

function checkLiveStatus() {
  fetch('https://bjapi.afreecatv.com/api/' + SOOP_BJID + '/station', { cache: 'no-store' })
    .then(function (res) {
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.json();
    })
    .then(function (d) {
      var broadNo = d && d.broad && Number(d.broad.broad_no);
      if (broadNo) renderLiveOnline(broadNo, d.broad.broad_title, d.broad.current_sum_viewer);
      else renderLiveOffline();
    })
    .catch(function () {
      // 조회에 실패하면 배너를 숨깁니다 (틀린 정보를 보여주지 않기 위해).
      liveBannerEl.innerHTML = '';
    });
}
checkLiveStatus();
setInterval(checkLiveStatus, 60000);

/* ── 영상 바로재생 모달 ────────────────────────────────────────
   유튜브로 이탈시키지 않고 그 자리에서 바로 재생합니다. */
function extractYoutubeId(url) {
  var m = String(url || '').match(/(?:v=|youtu\.be\/|embed\/|shorts\/)([A-Za-z0-9_-]{11})/);
  return m ? m[1] : null;
}
var vmodalEl = $('#vmodal');
var vmodalFrameEl = $('#vmodalFrame');
function openVideoModal(url) {
  var id = extractYoutubeId(url);
  if (!id) { window.open(url, '_blank', 'noopener'); return; }
  vmodalFrameEl.innerHTML = '<iframe src="https://www.youtube.com/embed/' + id +
    '?autoplay=1&rel=0" title="다시보기" ' +
    'allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>';
  vmodalEl.classList.add('on');
}
function closeVideoModal() {
  vmodalEl.classList.remove('on');
  vmodalFrameEl.innerHTML = '';   // iframe 제거 — 닫으면 재생도 바로 멈춥니다
}
$('#vmodalClose').addEventListener('click', closeVideoModal);
vmodalEl.addEventListener('click', function (e) { if (e.target === vmodalEl) closeVideoModal(); });
window.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeVideoModal(); });

/* ── 탭 / 상태 ─────────────────────────────────────────────── */
var TABS = [
  { id: 'rank', label: '선수 랭킹' },
  { id: 'prize', label: '상금 랭킹' },
  { id: 'predict', label: '중계진 예측' },
  { id: 'roster', label: '선수 명단' },
  { id: 'maps', label: '맵 통계' },
  { id: 'recent', label: '경기 기록' },
  { id: 'records', label: '기록실' },
  { id: 'season', label: '시즌' }
];
var TAB_IDS = TABS.map(function (t) { return t.id; });

// 기간(연도 범위) 필터: 시작~끝 연도. 기본은 전체 기간.
var YEARS_ASC = (D.years || []).slice().sort();
var Y_MIN = YEARS_ASC[0] || '', Y_MAX = YEARS_ASC[YEARS_ASC.length - 1] || '';
// 정렬 상태는 탭마다 따로 둡니다 — 랭킹의 '매치승' 정렬이 맵 탭으로 새면 안 되니까요.
var state = {
  tab: 'rank', yFrom: Y_MIN, yTo: Y_MAX, race: 'ALL', q: '',
  sort: { rank: { key: 'matchWin', dir: -1 }, maps: { key: 'totalSets', dir: -1 }, prize: { key: 'prizeTotal', dir: -1 } }
};
function sortState() { return state.sort[state.tab] || { key: '', dir: -1 }; }
function isFullRange() { return state.yFrom <= Y_MIN && state.yTo >= Y_MAX; }
function yrsInRange() { return YEARS_ASC.filter(function (y) { return y >= state.yFrom && y <= state.yTo; }); }
function rangeLabel() { return isFullRange() ? '통산' : (state.yFrom === state.yTo ? state.yFrom + '년' : state.yFrom + '~' + state.yTo + '년'); }

function writeHash() {
  var params = [];
  if (!isFullRange()) params.push('y=' + state.yFrom + '-' + state.yTo);
  if (state.q) params.push('q=' + encodeURIComponent(state.q));
  var h = state.tab + (params.length ? '?' + params.join('&') : '');
  if (location.hash.replace(/^#/, '') !== h) {
    history.replaceState(null, '', '#' + h);
  }
}

function applyYearToken(tok) {
  var rg = tok.split('-');
  if (rg.length === 2 && D.years.indexOf(rg[0]) >= 0 && D.years.indexOf(rg[1]) >= 0) {
    state.yFrom = rg[0] < rg[1] ? rg[0] : rg[1];
    state.yTo = rg[0] < rg[1] ? rg[1] : rg[0];
  } else if (D.years.indexOf(tok) >= 0) {          // 예전 단일 연도 호환
    state.yFrom = state.yTo = tok;
  }
}

function readHash() {
  var raw = location.hash.replace(/^#/, '');
  if (!raw) return false;
  // 예전 링크(#player/이름) 는 선수 페이지로 넘겨 줍니다.
  if (raw.indexOf('player/') === 0) {
    var name = decodeURIComponent(raw.slice('player/'.length));
    var href = hrefOf(name);
    if (href) { location.replace(href); return true; }
  }
  var qi = raw.indexOf('?');
  var head = qi >= 0 ? raw.slice(0, qi) : raw;
  var query = qi >= 0 ? raw.slice(qi + 1) : '';
  var parts = head.split('/');
  if (TAB_IDS.indexOf(parts[0]) >= 0) state.tab = parts[0];
  if (parts[1]) applyYearToken(parts[1]);           // 예전 형식 #탭/2019-2025
  if (query) {                                       // 새 형식 #탭?y=..&q=..
    query.split('&').forEach(function (kv) {
      var i = kv.indexOf('='); if (i < 0) return;
      var k = kv.slice(0, i), v = decodeURIComponent(kv.slice(i + 1));
      if (k === 'q') state.q = v;
      else if (k === 'y') applyYearToken(v);
    });
  }
  return false;
}

function renderTabs() {
  tabsEl.innerHTML = TABS.map(function (t) {
    return '<div class="tab' + (state.tab === t.id ? ' on' : '') + '" data-tab="' + t.id + '">' +
      t.label + '</div>';
  }).join('');
  tabsEl.querySelectorAll('.tab').forEach(function (el) {
    el.addEventListener('click', function () {
      state.tab = el.dataset.tab;
      state.q = '';
      render();
    });
  });
}

/* ── 필터 칩 ───────────────────────────────────────────────── */
function yearRange() {
  var el = document.createElement('div');
  el.className = 'chips yrrange';
  function opts(sel) {
    return YEARS_ASC.map(function (y) {
      return '<option value="' + y + '"' + (y === sel ? ' selected' : '') + '>' + y + '</option>';
    }).join('');
  }
  el.innerHTML = '<span class="chiplabel">기간</span>' +
    '<select class="yrsel" data-yr="from" aria-label="시작 연도">' + opts(state.yFrom) + '</select>' +
    '<span class="yrtilde">~</span>' +
    '<select class="yrsel" data-yr="to" aria-label="끝 연도">' + opts(state.yTo) + '</select>' +
    '<div class="chip' + (isFullRange() ? ' on' : '') + '" data-yall="1">전체</div>';
  el.querySelector('[data-yr="from"]').addEventListener('change', function () {
    state.yFrom = this.value; if (state.yFrom > state.yTo) state.yTo = state.yFrom; render();
  });
  el.querySelector('[data-yr="to"]').addEventListener('change', function () {
    state.yTo = this.value; if (state.yTo < state.yFrom) state.yFrom = state.yTo; render();
  });
  el.querySelector('[data-yall]').addEventListener('click', function () {
    state.yFrom = Y_MIN; state.yTo = Y_MAX; render();
  });
  return el;
}

function raceChips() {
  var el = document.createElement('div');
  el.className = 'chips';
  el.innerHTML = '<span class="chiplabel">종족</span>' +
    [['ALL', '전체']].concat(RACE_ORDER.map(function (r) { return [r, RACE_LABEL[r]]; }))
      .map(function (o) {
        return '<div class="chip' + (state.race === o[0] ? ' on' : '') +
          '" data-race="' + o[0] + '">' + o[1] + '</div>';
      }).join('');
  el.querySelectorAll('[data-race]').forEach(function (c) {
    c.addEventListener('click', function () { state.race = c.dataset.race; render(); });
  });
  return el;
}

function searchBox(placeholder, onInput) {
  var input = document.createElement('input');
  input.className = 'search';
  input.placeholder = placeholder;
  input.value = state.q;
  input.addEventListener('input', function () { state.q = input.value; onInput(); });
  return input;
}

/* ── 공통: 정렬 가능한 표 ──────────────────────────────────── */
function sortRows(rows, key, dir) {
  return rows.slice().sort(function (a, b) {
    var av = a[key], bv = b[key];
    if (typeof av === 'string' || typeof bv === 'string') {
      return String(av == null ? '' : av).localeCompare(String(bv == null ? '' : bv)) * dir;
    }
    return ((av || 0) - (bv || 0)) * dir;
  });
}

function tableHTML(cols, bodyHTML) {
  var s = sortState();
  return '<div class="tblwrap"><table><thead><tr>' + cols.map(function (c) {
    var arrow = c.key && s.key === c.key ? (s.dir > 0 ? ' ▲' : ' ▼') : '';
    return '<th class="' + (c.cls || '') + (c.key ? '' : ' static') + '"' +
      (c.key ? ' data-key="' + c.key + '"' : '') + '>' + c.label + arrow + '</th>';
  }).join('') + '</tr></thead><tbody>' + bodyHTML + '</tbody></table></div>';
}

function bindSort(container, rerender) {
  container.querySelectorAll('th[data-key]').forEach(function (el) {
    el.addEventListener('click', function () {
      var s = sortState(), k = el.dataset.key;
      if (s.key === k) s.dir *= -1;
      else { s.key = k; s.dir = k === 'name' ? 1 : -1; }
      rerender();
    });
  });
}

/* ── 선수 랭킹 ─────────────────────────────────────────────── */
function playerRowsForYear() {
  // 기간을 고르면 그 기간 성적을 연도별로 합산, 전체면 통산 성적을 그대로 씁니다.
  var full = isFullRange(), yrs = yrsInRange();
  return D.players.map(function (p) {
    if (full) {
      return {
        name: p.name, slug: p.slug, race: p.race,
        matchWin: p.matchWin, matchLoss: p.matchLoss,
        setWin: p.setWin, setLoss: p.setLoss,
        appearances: p.appearances, lastDate: p.lastDate,
        matchPct: pctNum(p.matchWin, p.matchLoss),
        setPct: pctNum(p.setWin, p.setLoss)
      };
    }
    var mw = 0, ml = 0, sw = 0, sl = 0, apps = 0, last = '';
    yrs.forEach(function (y) {
      var v = p.yearly[y];
      if (v) { mw += v.matchWin; ml += v.matchLoss; sw += v.setWin; sl += v.setLoss; apps += v.apps;
        if (v.lastDate && v.lastDate > last) last = v.lastDate; }
    });
    if (mw + ml === 0) return null;
    return {
      name: p.name, slug: p.slug, race: p.race,
      matchWin: mw, matchLoss: ml, setWin: sw, setLoss: sl,
      appearances: apps, lastDate: last,
      matchPct: pctNum(mw, ml), setPct: pctNum(sw, sl)
    };
  }).filter(Boolean);
}

function renderRank() {
  view.appendChild(yearRange());
  view.appendChild(raceChips());
  var table = document.createElement('div');
  var input = searchBox('선수 이름 검색...', function () { draw(); });
  view.appendChild(input);
  view.appendChild(table);

  function draw() {
    var s = sortState();
    var rows = playerRowsForYear().filter(function (p) {
      return (state.race === 'ALL' || p.race === state.race) &&
        (!state.q || p.name.indexOf(state.q) >= 0);
    });
    rows = sortRows(rows, s.key, s.dir);

    var cols = [
      { key: 'name', label: '선수' },
      { key: 'matchWin', label: '매치', cls: 'num' },
      { key: 'matchPct', label: '매치 승률', cls: 'num' },
      { key: 'setWin', label: '세트', cls: 'num' },
      { key: 'setPct', label: '세트 승률', cls: 'num' },
      { key: 'appearances', label: '출전', cls: 'num' },
      { key: 'lastDate', label: '최근 출전', cls: 'num hide-mobile' }
    ];
    var body = rows.length ? rows.map(function (p, i) {
      return '<tr class="rowlink" data-href="' + pageOf(p.slug) + '">' +
        '<td><span class="rk">' + (i + 1) + '</span>' + raceBadge(p.race) +
        '<span class="nm">' + esc(p.name) + '</span></td>' +
        '<td class="num">' + p.matchWin + '-' + p.matchLoss + '</td>' +
        '<td class="num">' + pct(p.matchWin, p.matchLoss) + '</td>' +
        '<td class="num">' + p.setWin + '-' + p.setLoss + '</td>' +
        '<td class="num">' + pct(p.setWin, p.setLoss) + '</td>' +
        '<td class="num">' + p.appearances + '</td>' +
        '<td class="num hide-mobile">' + (p.lastDate || '-') + '</td></tr>';
    }).join('') : '<tr><td colspan="7"><div class="emptybox">해당 조건의 선수가 없습니다.</div></td></tr>';

    table.innerHTML = tableHTML(cols, body) +
      '<div class="hint">' +
      (isFullRange() ? '통산 기록입니다. ' : rangeLabel() + ' 기록만 보고 있습니다. ') +
      '표 머리글을 누르면 그 항목으로 정렬하고, 선수를 누르면 상세 기록으로 이동합니다.</div>';
    bindSort(table, draw);
    table.querySelectorAll('[data-href]').forEach(function (el) {
      el.addEventListener('click', function () { location.href = el.dataset.href; });
    });
  }
  draw();
}

/* ── 상금 랭킹 ─────────────────────────────────────────────── */
function fmtWon(n) {
  n = Number(n || 0);
  if (n >= 100000000) {
    var eok = Math.floor(n / 100000000), man = Math.round((n % 100000000) / 10000);
    return eok + '억' + (man ? ' ' + man.toLocaleString() + '만' : '') + '원';
  }
  if (n >= 10000) return Math.round(n / 10000).toLocaleString() + '만원';
  return n.toLocaleString() + '원';
}
function renderPrize() {
  view.appendChild(yearRange());
  view.appendChild(raceChips());
  var table = document.createElement('div');
  view.appendChild(searchBox('선수 이름 검색...', function () { draw(); }));
  view.appendChild(table);

  function draw() {
    var s = sortState();
    var full = isFullRange(), yrs = yrsInRange();
    var rows = D.players.map(function (p) {
      var src;
      if (full) {
        src = { prizeTotal: p.prizeTotal || 0, prize: p.prize || 0, prizeBonus: p.prizeBonus || 0, prizeSets: p.prizeSets || 0 };
      } else {
        var tot = 0, pz = 0, bn = 0, st = 0;
        yrs.forEach(function (y) { var v = p.prizeYearly && p.prizeYearly[y]; if (v) { tot += v.total; pz += v.prize; bn += v.bonus; st += v.sets; } });
        src = { prizeTotal: tot, prize: pz, prizeBonus: bn, prizeSets: st };
      }
      return { name: p.name, slug: p.slug, race: p.race, prizeTotal: src.prizeTotal, prize: src.prize, prizeBonus: src.prizeBonus, prizeSets: src.prizeSets };
    }).filter(function (p) {
      return p && p.prizeTotal > 0 &&
        (state.race === 'ALL' || p.race === state.race) &&
        (!state.q || p.name.indexOf(state.q) >= 0);
    });
    rows = sortRows(rows, s.key || 'prizeTotal', s.dir);

    var cols = [
      { key: 'name', label: '선수' },
      { key: 'prizeTotal', label: '총 상금', cls: 'num' },
      { key: 'prize', label: '기본 상금', cls: 'num hide-mobile' },
      { key: 'prizeBonus', label: '더블찬스', cls: 'num hide-mobile' },
      { key: 'prizeSets', label: '이긴 세트', cls: 'num' }
    ];
    var body = rows.length ? rows.map(function (p, i) {
      return '<tr class="rowlink" data-href="' + pageOf(p.slug) + '">' +
        '<td><span class="rk">' + (i + 1) + '</span>' + raceBadge(p.race) +
        '<span class="nm">' + esc(p.name) + '</span></td>' +
        '<td class="num"><b>' + fmtWon(p.prizeTotal) + '</b></td>' +
        '<td class="num hide-mobile">' + fmtWon(p.prize) + '</td>' +
        '<td class="num hide-mobile">' + fmtWon(p.prizeBonus) + '</td>' +
        '<td class="num">' + p.prizeSets.toLocaleString() + '</td></tr>';
    }).join('') : '<tr><td colspan="5"><div class="emptybox">해당 조건의 선수가 없습니다.</div></td></tr>';

    var shownTotal = rows.reduce(function (a, p) { return a + p.prizeTotal; }, 0);
    table.innerHTML = tableHTML(cols, body) +
      '<div class="hint">끝장전은 <b>세트 승리마다 상금</b>을 받습니다(기본 상금 + 더블찬스). ' +
      (isFullRange() ? '통산 ' : rangeLabel() + ' ') + '배분 상금 <b>' + fmtWon(shownTotal) + '</b>. ' +
      '기간을 고르면 그 기간 상금만 봅니다. 표 머리글을 누르면 정렬, 선수를 누르면 상세로 이동합니다.</div>';
    bindSort(table, draw);
    table.querySelectorAll('[data-href]').forEach(function (el) {
      el.addEventListener('click', function () { location.href = el.dataset.href; });
    });
  }
  draw();
}

/* ── 재밌는 기록 (기록실 탭 하단에 이어 붙습니다) ───────────── */
function renderFun() {
  var P = D.players;
  function nameCell(p, i) {
    return '<td><span class="rk">' + (i + 1) + '</span>' + raceBadge(p.race) +
      '<span class="nm">' + esc(p.name) + '</span></td>';
  }
  function rows(list, valFn) {
    return list.length ? list.map(function (p, i) {
      return '<tr class="rowlink" data-href="' + pageOf(p.slug) + '">' + nameCell(p, i) +
        '<td class="num">' + valFn(p) + '</td></tr>';
    }).join('') : '<tr><td colspan="2"><div class="emptybox">없음</div></td></tr>';
  }
  function lbCard(title, note, headLabel, body) {
    return '<div class="card"><div class="cardtitle">' + title +
      (note ? '<span class="note">' + note + '</span>' : '') + '</div>' +
      '<div class="tblwrap"><table><thead><tr><th>선수</th><th class="num">' + headLabel +
      '</th></tr></thead><tbody>' + body + '</tbody></table></div></div>';
  }

  var winL = P.filter(function (p) { return p.streak.bestWin >= 2; })
    .sort(function (a, b) { return b.streak.bestWin - a.streak.bestWin; }).slice(0, 10);
  var lossL = P.filter(function (p) { return p.streak.bestLoss >= 2; })
    .sort(function (a, b) { return b.streak.bestLoss - a.streak.bestLoss; }).slice(0, 10);
  var curL = P.filter(function (p) { return Math.abs(p.streak.current) >= 2; })
    .sort(function (a, b) { return Math.abs(b.streak.current) - Math.abs(a.streak.current); }).slice(0, 12);

  var g1 = document.createElement('div');
  g1.className = 'grid3';
  g1.innerHTML =
    lbCard('💧 최다 연패', '매치 기준', '연패', rows(lossL, function (p) { return '<b>' + p.streak.bestLoss + '연패</b>'; })) +
    lbCard('📈 지금 연속 기록', '최근 경기 기준', '현재', rows(curL, function (p) {
      var c = p.streak.current;
      return '<b class="' + (c > 0 ? 'stw' : 'stl') + '">' + (c > 0 ? c + '연승 중' : (-c) + '연패 중') + '</b>';
    }));
  view.appendChild(g1);

  var g2 = document.createElement('div');
  g2.className = 'grid3';
  g2.innerHTML = RACE_ORDER.map(function (r) {
    var list = P.filter(function (p) { return p.race === r; })
      .sort(function (a, b) { return b.matchWin - a.matchWin || b.setWin - a.setWin; }).slice(0, 6);
    var body = list.map(function (p, i) {
      return '<tr class="rowlink" data-href="' + pageOf(p.slug) + '">' + nameCell(p, i) +
        '<td class="num">' + p.matchWin + '-' + p.matchLoss + '</td>' +
        '<td class="num hide-mobile">' + pct(p.matchWin, p.matchLoss) + '</td></tr>';
    }).join('');
    return '<div class="card"><div class="cardtitle">' + raceBadge(r) + RACE_LABEL[r] +
      ' 최강<span class="note">매치승 순</span></div>' +
      '<div class="tblwrap"><table><thead><tr><th>선수</th><th class="num">매치</th>' +
      '<th class="num hide-mobile">승률</th></tr></thead><tbody>' + body + '</tbody></table></div></div>';
  }).join('');
  view.appendChild(g2);

  var h2h = {}, pairs = [];
  D.matches.forEach(function (m) {
    var pr = m.players.slice().sort();
    var key = pr[0] + '|' + pr[1];
    var rec = h2h[key] || (h2h[key] = { a: pr[0], b: pr[1], aw: 0, bw: 0 });
    if (m.winner === pr[0]) rec.aw++; else rec.bw++;
  });
  Object.keys(h2h).forEach(function (key) {
    var r = h2h[key], g = r.aw + r.bw;
    if (g < 3) return;                            // 매치(경기) 3번 이상 맞대결
    var sN, wN, sw, sl;
    if (r.aw >= r.bw) { sN = r.a; wN = r.b; sw = r.aw; sl = r.bw; }
    else { sN = r.b; wN = r.a; sw = r.bw; sl = r.aw; }
    pairs.push({
      strong: { n: sN, r: D.raceOf[sN], s: D.slugs[sN] || '' },
      weak: { n: wN, r: D.raceOf[wN], s: D.slugs[wN] || '' },
      sw: sw, sl: sl, rate: sw / g
    });
  });
  pairs = pairs.filter(function (x) { return x.rate >= 0.7 && x.sw - x.sl >= 2; })
    .sort(function (a, b) { return b.rate - a.rate || (b.sw - b.sl) - (a.sw - a.sl); }).slice(0, 15);
  var tbody = pairs.length ? pairs.map(function (x, i) {
    return '<tr><td><span class="rk">' + (i + 1) + '</span>' + raceBadge(x.strong.r) +
      '<a class="nm-link" href="' + pageOf(x.strong.s) + '">' + esc(x.strong.n) + '</a></td>' +
      '<td class="num"><b>' + x.sw + '</b> - ' + x.sl + '</td>' +
      '<td>' + raceBadge(x.weak.r) + '<a class="nm-link" href="' + pageOf(x.weak.s) + '">' + esc(x.weak.n) + '</a></td>' +
      '<td class="num hide-mobile">' + Math.round(x.rate * 100) + '%</td></tr>';
  }).join('') : '<tr><td colspan="4"><div class="emptybox">없음</div></td></tr>';
  var c3 = document.createElement('div');
  c3.className = 'card';
  c3.innerHTML = '<div class="cardtitle">😈 천적 관계<span class="note">3경기 이상 맞대결 · 한쪽이 70%+ 우세</span></div>' +
    '<div class="tblwrap"><table><thead><tr><th>우세</th><th class="num">경기 전적</th><th>열세</th>' +
    '<th class="num hide-mobile">우세율</th></tr></thead><tbody>' + tbody + '</tbody></table></div>' +
    '<div class="hint">같은 두 선수가 여러 번 맞붙어 한쪽이 크게 앞선 매치업입니다. 이름을 누르면 상세로 갑니다.</div>';
  view.appendChild(c3);

  view.querySelectorAll('.rowlink[data-href]').forEach(function (el) {
    el.addEventListener('click', function () { location.href = el.dataset.href; });
  });
}

/* ── 중계진 예측 ───────────────────────────────────────────── */
function renderPredict() {
  var pr = D.predict;
  if (!pr || !pr.casters || !pr.casters.length) {
    view.innerHTML = '<div class="emptybox">중계진 예측 데이터가 아직 없습니다.</div>';
    return;
  }
  function signed(n, suffix) {
    if (n == null) return '-';
    return (n > 0 ? '+' : '') + (suffix === '%' ? n : n.toLocaleString()) + (suffix || '');
  }
  var cbody = pr.casters.map(function (c, i) {
    return '<tr><td><span class="rk">' + (i + 1) + '</span><span class="nm">' + esc(c.name) + '</span></td>' +
      '<td class="num"><b>' + c.pct + '%</b></td>' +
      '<td class="num">' + c.correct + ' / ' + c.total + '</td>' +
      '<td class="num hide-mobile ' + ((c.index || 0) >= 0 ? 'stw' : 'stl') + '">' + signed(c.index) + '</td>' +
      '<td class="num hide-mobile ' + ((c.roi || 0) >= 0 ? 'stw' : 'stl') + '">' + signed(c.roi, '%') + '</td></tr>';
  }).join('');
  var c1 = document.createElement('div'); c1.className = 'card';
  c1.innerHTML = '<div class="cardtitle">🎙️ 중계진 적중률<span class="note">전체 ' + pr.totalPredictions +
    '건 · 평균 ' + pr.overallPct + '%</span></div>' +
    '<div class="tblwrap"><table><thead><tr><th>캐스터</th><th class="num">적중률</th><th class="num">적중/전체</th>' +
    '<th class="num hide-mobile">지수</th><th class="num hide-mobile">수익률</th></tr></thead><tbody>' + cbody +
    '</tbody></table></div><div class="hint">세트마다 캐스터가 승자를 예측한 기록입니다. 지수·수익률은 방송 미션 점수(갯수를 걸어 맞히면 획득) 기준입니다.</div>';
  view.appendChild(c1);

  var pcts = pr.bySet.map(function (x) { return x.pct; });
  var lo = Math.min.apply(null, pcts), hi = Math.max.apply(null, pcts);
  var sbars = pr.bySet.map(function (s) {
    var cls = s.pct === lo ? ' hard' : (s.pct === hi ? ' easy' : '');
    return '<div class="prow"><span class="plab">SET ' + s.set + '</span>' +
      '<div class="pbar"><span class="' + cls.trim() + '" style="width:' + Math.max(s.pct, 8) + '%">' + s.pct + '%</span></div>' +
      '<span class="pnum">' + s.correct + '/' + s.total + '</span></div>';
  }).join('');
  var c2 = document.createElement('div'); c2.className = 'card';
  c2.innerHTML = '<div class="cardtitle">🎯 세트별 적중률<span class="note">초록=가장 잘맞힘 · 빨강=가장 어려움</span></div>' +
    sbars + '<div class="hint">몇 번째 세트를 캐스터들이 잘/못 맞혔는지. 승부가 갈리는 후반 세트가 대체로 더 어렵습니다.</div>';
  view.appendChild(c2);

  var pbody = pr.byPlayer.slice(0, 12).map(function (p, i) {
    var s = D.slugs[p.name];
    return '<tr' + (s ? ' class="rowlink" data-href="' + pageOf(s) + '"' : '') + '>' +
      '<td><span class="rk">' + (i + 1) + '</span>' + raceBadge(p.race) + '<span class="nm">' + esc(p.name) + '</span></td>' +
      '<td class="num"><b>' + p.missPct + '%</b></td>' +
      '<td class="num hide-mobile">' + p.miss + ' / ' + p.total + '</td></tr>';
  }).join('');
  var c3 = document.createElement('div'); c3.className = 'card';
  c3.innerHTML = '<div class="cardtitle">😱 예측 파괴자<span class="note">이 선수 경기에서 예측이 빗나간 비율</span></div>' +
    '<div class="tblwrap"><table><thead><tr><th>선수</th><th class="num">빗나감</th>' +
    '<th class="num hide-mobile">빗나감/예측</th></tr></thead><tbody>' + pbody + '</tbody></table></div>' +
    '<div class="hint">이 선수가 낀 세트에서 캐스터 예측이 얼마나 빗나갔는지(12예측 이상). 높을수록 이변이 잦습니다.</div>';
  view.appendChild(c3);

  var mbody = pr.byMatchup.map(function (m) {
    return '<tr><td>' + esc(m.label) + '</td><td class="num"><b>' + m.pct + '%</b></td>' +
      '<td class="num hide-mobile">' + m.correct + ' / ' + m.total + '</td></tr>';
  }).join('');
  var c4 = document.createElement('div'); c4.className = 'card';
  c4.innerHTML = '<div class="cardtitle">🧬 종족전별 예측 적중률</div>' +
    '<div class="tblwrap"><table><thead><tr><th>종족전</th><th class="num">적중률</th>' +
    '<th class="num hide-mobile">적중/예측</th></tr></thead><tbody>' + mbody + '</tbody></table></div>' +
    '<div class="hint">어느 종족 대결이 예측하기 쉬운지/어려운지. 낮을수록 변수가 많다는 뜻입니다.</div>';
  view.appendChild(c4);

  view.querySelectorAll('.rowlink[data-href]').forEach(function (el) {
    el.addEventListener('click', function () { location.href = el.dataset.href; });
  });
}

/* ── 선수 명단 ─────────────────────────────────────────────── */
function renderRoster() {
  var grid = document.createElement('div');
  grid.className = 'grid3';
  RACE_ORDER.forEach(function (race) {
    var list = D.players.filter(function (p) { return p.race === race; })
      .sort(function (a, b) { return b.appearances - a.appearances; });
    var card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = '<div class="cardtitle">' + raceBadge(race) + RACE_LABEL[race] +
      '<span class="note">' + list.length + '명</span></div>' +
      '<div class="tblwrap"><table><thead><tr><th class="static">선수</th>' +
      '<th class="static num">출전</th><th class="static num">매치</th></tr></thead><tbody>' +
      list.map(function (p) {
        return '<tr class="rowlink" data-href="' + pageOf(p.slug) + '">' +
          '<td class="nm">' + esc(p.name) + '</td>' +
          '<td class="num">' + p.appearances + '</td>' +
          '<td class="num">' + p.matchWin + '-' + p.matchLoss + '</td></tr>';
      }).join('') + '</tbody></table></div>';
    grid.appendChild(card);
  });
  view.appendChild(grid);
  grid.querySelectorAll('[data-href]').forEach(function (el) {
    el.addEventListener('click', function () { location.href = el.dataset.href; });
  });
}

/* ── 맵 통계 ───────────────────────────────────────────────── */
function sparkHTML(yearly) {
  var max = 0;
  D.years.forEach(function (y) { max = Math.max(max, yearly[y] || 0); });
  if (!max) return '';
  var asc = D.years.slice().reverse();      // 왼쪽이 과거
  return '<span class="spark" title="' + asc.map(function (y) {
    return y + ' ' + (yearly[y] || 0) + '세트';
  }).join(' / ') + '">' + asc.map(function (y) {
    var v = yearly[y] || 0;
    var h = v ? Math.max(3, Math.round(v / max * 20)) : 1;
    return '<i class="' + (v ? 'on' : '') + '" style="height:' + h + 'px"></i>';
  }).join('') + '</span>';
}

function renderMaps() {
  var table = document.createElement('div');
  view.appendChild(searchBox('맵 이름 검색...', function () { draw(); }));
  view.appendChild(table);

  function draw() {
    var s = sortState();
    var rows = sortRows(D.maps, s.key, s.dir);
    if (state.q) {
      var q = state.q.toLowerCase();
      rows = rows.filter(function (m) { return m.name.toLowerCase().indexOf(q) >= 0; });
    }
    var cols = [
      { key: 'name', label: '맵' },
      { key: 'totalSets', label: '총 세트', cls: 'num' },
      { key: 'daysUsed', label: '사용일수', cls: 'num hide-mobile' },
      { label: '연도별 사용', cls: 'hide-mobile' },
      { label: '저그 vs 프로토스', cls: 'num' },
      { label: '테란 vs 저그', cls: 'num' },
      { label: '프로토스 vs 테란', cls: 'num' }
    ];
    function cell(o, front) {
      if (!o || !(o.w + o.l)) return '<span class="dim">-</span>';
      return o.w + '-' + o.l + ' <span class="pct">(' + front + ' ' + pct(o.w, o.l) + ')</span>';
    }
    var body = rows.map(function (m) {
      return '<tr><td class="nm">' + esc(m.name) + '</td>' +
        '<td class="num">' + m.totalSets + '</td>' +
        '<td class="num hide-mobile">' + m.daysUsed + '</td>' +
        '<td class="hide-mobile">' + sparkHTML(m.yearly || {}) + '</td>' +
        '<td class="num">' + cell(m.matchup['Z-P'], 'Z') + '</td>' +
        '<td class="num">' + cell(m.matchup['T-Z'], 'T') + '</td>' +
        '<td class="num">' + cell(m.matchup['P-T'], 'P') + '</td></tr>';
    }).join('');

    table.innerHTML = tableHTML(cols, body) +
      '<div class="hint">괄호 안은 앞에 적힌 종족 기준 승률입니다. ' +
      '연도별 사용 막대는 왼쪽이 ' + D.years[D.years.length - 1] + '년, 오른쪽이 ' + D.years[0] + '년입니다.<br>' +
      '맵별 승패는 세트마다 어떤 맵을 썼는지 기록이 남은 세트만 집계합니다 — ' +
      '전체 ' + D.global.totalSets.toLocaleString() + '세트 가운데 ' +
      D.mapCoveredSets.toLocaleString() + '세트가 대상입니다.</div>';
    bindSort(table, draw);
  }
  draw();
}

/* ── 경기 기록 ─────────────────────────────────────────────── */
function renderRecent() {
  view.appendChild(yearRange());
  var table = document.createElement('div');
  var input = searchBox('선수 이름으로 경기 찾기...', function () { draw(); });
  view.appendChild(input);
  view.appendChild(table);

  function draw() {
    var rows = D.matches.filter(function (m) {
      var yr = m.date.slice(0, 4);
      return (isFullRange() || (yr >= state.yFrom && yr <= state.yTo)) &&
        (!state.q || m.players.some(function (n) { return n.indexOf(state.q) >= 0; }));
    });
    var withVideo = rows.filter(function (m) { return m.youtubeUrl; }).length;

    var body = rows.length ? rows.map(function (m) {
      var a = m.players[0], b = m.players[1];
      var aWin = m.winner === a;
      var search = 'https://www.youtube.com/@ETALENT-SC/search?query=' +
        encodeURIComponent(a + ' ' + b);
      var ytCell = m.youtubeUrl
        ? '<span class="yt-mini" data-yt="' + esc(m.youtubeUrl) + '">▶ 바로재생</span>'
        : '<a class="yt-mini yt-fallback" href="' + search + '" target="_blank" rel="noopener">🔍 채널에서 찾기</a>';
      return '<tr>' +
        '<td class="muted">' + m.date + '</td>' +
        '<td>' + nameLink(a, m.race[a]) + ' <span class="muted">vs</span> ' +
        nameLink(b, m.race[b]) + '</td>' +
        '<td class="num score-cell" data-a="' + esc(a) + '" data-awin="' + (aWin ? 1 : 0) + '">' +
        '<span class="spoiler">결과 보기</span>' +
        '<span class="score-value" hidden>' + m.setWins[a] + ' - ' + m.setWins[b] + '</span></td>' +
        '<td class="hide-mobile muted">' + esc((m.maps || []).filter(Boolean).slice(0, 3).join(', ')) +
        ((m.maps || []).filter(Boolean).length > 3 ? ' …' : '') + '</td>' +
        '<td>' + ytCell + '</td></tr>';
    }).join('') : '<tr><td colspan="5"><div class="emptybox">해당 조건의 경기가 없습니다.</div></td></tr>';

    table.innerHTML = tableHTML([
      { label: '날짜' }, { label: '대진' }, { label: '결과', cls: 'num' },
      { label: '맵', cls: 'hide-mobile' }, { label: '다시보기' }
    ], body) +
      '<div class="hint">' + rows.length + '경기를 보고 있습니다' +
      (withVideo ? ' (영상 ' + withVideo + '개 연결됨)' : '') + '. ' +
      '"결과 보기"를 눌러야 스코어가 나옵니다 — 다시보기 전에 결과가 새지 않게 가려 뒀습니다. ' +
      '"바로재생"은 페이지를 벗어나지 않고 그 자리에서 재생합니다.' +
      (withVideo < rows.length
        ? '<br>영상이 연결되지 않은 경기는 두 선수 이름으로 채널 검색 결과를 열어 줍니다.'
        : '') + '</div>';

    table.querySelectorAll('.score-cell').forEach(function (cellEl) {
      cellEl.addEventListener('click', function () {
        cellEl.querySelector('.spoiler').hidden = true;
        cellEl.querySelector('.score-value').hidden = false;
        var aWin = cellEl.dataset.awin === '1';
        var links = cellEl.closest('tr').querySelectorAll('.nm-link');
        if (links[0]) links[0].classList.add(aWin ? 'win' : 'lose');
        if (links[1]) links[1].classList.add(aWin ? 'lose' : 'win');
      });
    });
    table.querySelectorAll('[data-yt]').forEach(function (el) {
      el.addEventListener('click', function () { openVideoModal(el.dataset.yt); });
    });
  }
  draw();
}

/* ── 기록실 ────────────────────────────────────────────────── */
function recordCard(title, note, rows) {
  return '<div class="card"><div class="cardtitle">' + title +
    (note ? '<span class="note">' + note + '</span>' : '') + '</div>' +
    '<div class="tblwrap"><table><tbody>' + rows.map(function (r, i) {
      return '<tr><td style="width:34px" class="num dim">' + (i + 1) + '</td>' +
        '<td>' + nameLink(r.name, r.race) + '</td>' +
        '<td class="num"><b>' + esc(r.label) + '</b></td>' +
        '<td class="num dim hide-mobile" style="font-size:12px">' + esc(r.detail) + '</td></tr>';
    }).join('') + '</tbody></table></div></div>';
}

function muBar(key, o) {
  var front = key[0], back = key[2];
  var total = o.w + o.l;
  var wp = total ? o.w / total * 100 : 50;
  // 한쪽이 0이면 칸 너비가 0이라 글자가 밖으로 삐져나옵니다 — 좁으면 숨깁니다.
  var showL = total && wp >= 13, showR = total && (100 - wp) >= 13;
  return '<div class="murow">' +
    '<div class="mulabel"><span>' + raceBadge(front) + RACE_LABEL[front] +
    ' <b>' + o.w + '</b></span>' +
    '<span><b>' + o.l + '</b> ' + RACE_LABEL[back] + raceBadge(back) + '</span></div>' +
    '<div class="mubar">' +
    '<span style="width:' + wp + '%;background:' + RACE_COLOR[front] + '">' +
    (showL ? pct(o.w, o.l) : '') + '</span>' +
    '<span style="width:' + (100 - wp) + '%;background:' + RACE_COLOR[back] + '">' +
    (showR ? pct(o.l, o.w) : '') + '</span></div></div>';
}

function renderRecords() {
  var r = D.records;
  var html = '<div class="card"><div class="cardtitle">종족 상성 — 세트 기준' +
    '<span class="note">통산 ' + D.global.totalSets.toLocaleString() + '세트</span></div>' +
    MU_KEYS.map(function (k) { return muBar(k, D.mu[k]); }).join('') + '</div>';

  html += '<div class="grid2">' +
    recordCard('최다 출전', '매치 기준', r.apps) +
    recordCard('최다 매치 승', '', r.matchWin) +
    recordCard('매치 승률', r.minMatch + '경기 이상', r.matchPct) +
    recordCard('최다 세트 승', '', r.setWin) +
    recordCard('세트 승률', r.minSet + '세트 이상', r.setPct) +
    recordCard('최다 연승', '매치 기준', r.winStreak) +
    recordCard('5-4 접전 최다', '마지막 세트까지 간 경기', r.thriller) +
    '</div>';

  html += '<div class="grid2">';
  html += '<div class="card"><div class="cardtitle">최다 세트 차 완승</div>' +
    '<div class="tblwrap"><table><tbody>' + r.sweep.map(function (x, i) {
      return '<tr><td style="width:34px" class="num dim">' + (i + 1) + '</td>' +
        '<td class="muted" style="font-size:12.5px">' + x.date + '</td>' +
        '<td>' + nameLink(x.a, x.aRace, 'win') + ' <span class="dim">vs</span> ' +
        nameLink(x.b, x.bRace) + '</td>' +
        '<td class="num"><b>' + x.score + '</b></td></tr>';
    }).join('') + '</tbody></table></div></div>';

  html += '<div class="card"><div class="cardtitle">최다 사용 맵</div>' +
    '<div class="tblwrap"><table><tbody>' + r.topMaps.map(function (x, i) {
      return '<tr><td style="width:34px" class="num dim">' + (i + 1) + '</td>' +
        '<td class="nm">' + esc(x.name) + '</td>' +
        '<td class="num"><b>' + esc(x.label) + '</b></td>' +
        '<td class="num dim hide-mobile" style="font-size:12px">' + esc(x.detail) + '</td></tr>';
    }).join('') + '</tbody></table></div></div>';
  html += '</div>';

  html += '<div class="card"><div class="cardtitle">라이벌 — 맞대결이 많은 순서' +
    '<span class="note">상위 15쌍</span></div>' +
    '<div class="tblwrap"><table><thead><tr><th class="static">대진</th>' +
    '<th class="static num">매치</th><th class="static num">세트</th>' +
    '<th class="static num hide-mobile">앞 선수 세트 승률</th></tr></thead><tbody>' +
    D.rivalries.map(function (x) {
      return '<tr><td>' + nameLink(x.a, x.aRace) + ' <span class="dim">vs</span> ' +
        nameLink(x.b, x.bRace) + '</td>' +
        '<td class="num">' + x.matchW + '-' + x.matchL + '</td>' +
        '<td class="num">' + x.setW + '-' + x.setL + '</td>' +
        '<td class="num hide-mobile">' + pct(x.setW, x.setL) + '</td></tr>';
    }).join('') + '</tbody></table></div>' +
    '<div class="hint">전적은 왼쪽에 적힌 선수 기준입니다.</div></div>';

  view.innerHTML = html;
  renderFun();   // 재밌는 기록(연패·현재 연속·종족별 최강·천적)을 이어서 붙입니다
}

/* ── 시즌 ──────────────────────────────────────────────────── */
function renderSeason() {
  var rows = D.yearly.map(function (y) {
    return '<tr class="rowlink" data-year="' + y.year + '">' +
      '<td class="nm">' + y.year + '</td>' +
      '<td class="num">' + y.matches + '</td>' +
      '<td class="num">' + y.sets + '</td>' +
      '<td class="num">' + y.players + '</td>' +
      '<td>' + (y.topPlayer ? nameLink(y.topPlayer, (D.raceOf[y.topPlayer] || '')) +
        ' <span class="dim">' + y.topWins + '승 ' + y.topLosses + '패</span>' : '-') + '</td>' +
      MU_KEYS.map(function (k) {
        var o = y.mu[k];
        return '<td class="num hide-mobile">' + o.w + '-' + o.l + '</td>';
      }).join('') + '</tr>';
  }).join('');

  var html = '<div class="card"><div class="cardtitle">연도별 요약</div>' +
    '<div class="tblwrap"><table><thead><tr>' +
    '<th class="static">연도</th><th class="static num">매치</th><th class="static num">세트</th>' +
    '<th class="static num">선수</th><th class="static">최다승</th>' +
    MU_KEYS.map(function (k) {
      return '<th class="static num hide-mobile">' + k.replace('v', ' vs ') + '</th>';
    }).join('') + '</tr></thead><tbody>' + rows + '</tbody></table></div>' +
    '<div class="hint">연도를 누르면 그 해 랭킹으로 이동합니다. ' +
    '상성 칸은 세트 기준 승-패이고, 앞에 적힌 종족 기준입니다.</div></div>';

  html += '<div class="grid2">' + D.yearly.map(function (y) {
    return '<div class="card"><div class="cardtitle">' + y.year + ' 종족 상성' +
      '<span class="note">' + y.matches + '매치 · ' + y.sets + '세트</span></div>' +
      MU_KEYS.map(function (k) { return muBar(k, y.mu[k]); }).join('') + '</div>';
  }).join('') + '</div>';

  view.innerHTML = html;
  view.querySelectorAll('tr[data-year]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      // 행 안의 선수 이름은 선수 페이지로 가야 하므로 행 클릭을 가로채지 않습니다.
      if (e.target.closest('a')) return;
      state.yFrom = state.yTo = el.dataset.year;
      state.tab = 'rank';
      render();
    });
  });
}

/* ── 라우팅 ────────────────────────────────────────────────── */
function render() {
  renderTabs();
  writeHash();
  view.innerHTML = '';
  if (state.tab === 'rank') renderRank();
  else if (state.tab === 'prize') renderPrize();
  else if (state.tab === 'predict') renderPredict();
  else if (state.tab === 'roster') renderRoster();
  else if (state.tab === 'maps') renderMaps();
  else if (state.tab === 'recent') renderRecent();
  else if (state.tab === 'records') renderRecords();
  else if (state.tab === 'season') renderSeason();
}

window.addEventListener('hashchange', function () {
  if (readHash()) return;
  render();
});
if (!readHash()) render();

$('#built').textContent = new Date(D.builtAt).toLocaleString('ko-KR');
