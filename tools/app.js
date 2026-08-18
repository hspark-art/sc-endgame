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
  { id: 'roster', label: '선수 명단' },
  { id: 'maps', label: '맵 통계' },
  { id: 'recent', label: '경기 기록' },
  { id: 'records', label: '기록실' },
  { id: 'season', label: '시즌' }
];
var TAB_IDS = TABS.map(function (t) { return t.id; });

// 정렬 상태는 탭마다 따로 둡니다 — 랭킹의 '매치승' 정렬이 맵 탭으로 새면 안 되니까요.
var state = {
  tab: 'rank', year: 'ALL', race: 'ALL', q: '',
  sort: { rank: { key: 'matchWin', dir: -1 }, maps: { key: 'totalSets', dir: -1 } }
};
function sortState() { return state.sort[state.tab] || { key: '', dir: -1 }; }

function writeHash() {
  var h = state.tab + (state.year !== 'ALL' ? '/' + state.year : '');
  if (location.hash.replace(/^#/, '') !== h) {
    history.replaceState(null, '', '#' + h);
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
  var parts = raw.split('/');
  if (TAB_IDS.indexOf(parts[0]) >= 0) state.tab = parts[0];
  if (parts[1] && D.years.indexOf(parts[1]) >= 0) state.year = parts[1];
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
function yearChips() {
  var counts = {};
  D.yearly.forEach(function (y) { counts[y.year] = y.matches; });
  var opts = [['ALL', '전체', D.global.totalMatches]].concat(
    D.years.map(function (y) { return [y, y, counts[y] || 0]; }));
  var el = document.createElement('div');
  el.className = 'chips';
  el.innerHTML = '<span class="chiplabel">연도</span>' + opts.map(function (o) {
    return '<div class="chip' + (state.year === o[0] ? ' on' : '') + '" data-year="' + o[0] + '">' +
      o[1] + '<span class="n" style="opacity:.6;margin-left:5px;font-size:11px">' + o[2] + '</span></div>';
  }).join('');
  el.querySelectorAll('[data-year]').forEach(function (c) {
    c.addEventListener('click', function () { state.year = c.dataset.year; render(); });
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
  // 연도를 고르면 그 해 성적만, 전체면 통산 성적을 씁니다.
  return D.players.map(function (p) {
    var src = state.year === 'ALL' ? p : (p.yearly[state.year] || null);
    if (!src) return null;
    return {
      name: p.name, slug: p.slug, race: p.race,
      matchWin: src.matchWin, matchLoss: src.matchLoss,
      setWin: src.setWin, setLoss: src.setLoss,
      appearances: state.year === 'ALL' ? p.appearances : src.apps,
      lastDate: state.year === 'ALL' ? p.lastDate : (src.lastDate || ''),
      matchPct: pctNum(src.matchWin, src.matchLoss),
      setPct: pctNum(src.setWin, src.setLoss)
    };
  }).filter(Boolean);
}

function renderRank() {
  view.appendChild(yearChips());
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
      (state.year === 'ALL' ? '통산 기록입니다. ' : state.year + '년 기록만 보고 있습니다. ') +
      '표 머리글을 누르면 그 항목으로 정렬하고, 선수를 누르면 상세 기록으로 이동합니다.</div>';
    bindSort(table, draw);
    table.querySelectorAll('[data-href]').forEach(function (el) {
      el.addEventListener('click', function () { location.href = el.dataset.href; });
    });
  }
  draw();
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
  view.appendChild(yearChips());
  var table = document.createElement('div');
  var input = searchBox('선수 이름으로 경기 찾기...', function () { draw(); });
  view.appendChild(input);
  view.appendChild(table);

  function draw() {
    var rows = D.matches.filter(function (m) {
      return (state.year === 'ALL' || m.date.slice(0, 4) === state.year) &&
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
  return '<div class="murow">' +
    '<div class="mulabel"><span>' + raceBadge(front) + RACE_LABEL[front] +
    ' <b>' + o.w + '</b></span>' +
    '<span><b>' + o.l + '</b> ' + RACE_LABEL[back] + raceBadge(back) + '</span></div>' +
    '<div class="mubar">' +
    '<span style="width:' + wp + '%;background:' + RACE_COLOR[front] + '">' +
    (total ? pct(o.w, o.l) : '') + '</span>' +
    '<span style="width:' + (100 - wp) + '%;background:' + RACE_COLOR[back] + '">' +
    (total ? pct(o.l, o.w) : '') + '</span></div></div>';
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
    recordCard('최장 활동', '첫 출전 ~ 최근 출전', r.span) +
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
      state.year = el.dataset.year;
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
