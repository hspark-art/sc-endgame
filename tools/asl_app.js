/* ASL 기록실 — 허브 페이지 앱.
   끝장전과는 별개 대회라 데이터도 화면도 따로 씁니다.
   ASL 기록에는 날짜가 없고 대회·라운드만 있어서, 축은 '연도' 가 아니라 '대회' 입니다. */

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
function nameLink(name, race, extraClass) {
  var s = D.slugs[name];
  var inner = (race ? raceBadge(race) : '') +
    '<span class="nm-link' + (extraClass ? ' ' + extraClass : '') + '">' + esc(name) + '</span>';
  return s ? '<a href="' + pageOf(s) + '">' + inner + '</a>' : inner;
}

var view = $('#view');
var tabsEl = $('#tabs');

$('#strip').innerHTML = [
  ['대회', D.global.totalTournaments + '개'],
  ['총 매치', D.global.totalMatches.toLocaleString()],
  ['총 세트', D.global.totalSets.toLocaleString()],
  ['참가 선수', D.global.totalPlayers + '명'],
  ['범위', D.global.firstTournament + ' ~ ' + D.global.lastTournament]
].map(function (kv) {
  return '<div class="item">' + kv[0] + '<b>' + kv[1] + '</b></div>';
}).join('');

var TABS = [
  { id: 'season', label: '대회' },
  { id: 'rank', label: '선수 랭킹' },
  { id: 'roster', label: '선수 명단' },
  { id: 'maps', label: '맵 통계' },
  { id: 'matches', label: '경기 기록' },
  { id: 'records', label: '기록실' }
];
var TAB_IDS = TABS.map(function (t) { return t.id; });

var state = {
  tab: 'season', tour: 'ALL', race: 'ALL', round: 'ALL', q: '', touchedTour: false,
  sort: { rank: { key: 'setWin', dir: -1 }, maps: { key: 'totalSets', dir: -1 } },
  open: {}
};
function sortState() { return state.sort[state.tab] || { key: '', dir: -1 }; }

function writeHash() {
  var h = state.tab + (state.tour !== 'ALL' ? '/' + encodeURIComponent(state.tour) : '');
  if (location.hash.replace(/^#/, '') !== h) history.replaceState(null, '', '#' + h);
}
function readHash() {
  var raw = location.hash.replace(/^#/, '');
  if (!raw) return;
  var parts = raw.split('/');
  if (TAB_IDS.indexOf(parts[0]) >= 0) state.tab = parts[0];
  if (parts[1]) {
    var want = decodeURIComponent(parts[1]);
    if (D.tournaments.some(function (t) { return t.name === want; })) {
      state.tour = want;
      state.touchedTour = true;
    }
  }
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

function tourChips() {
  var el = document.createElement('div');
  el.className = 'chips';
  el.innerHTML = '<span class="chiplabel">대회</span>' +
    '<div class="chip' + (state.tour === 'ALL' ? ' on' : '') + '" data-tour="ALL">전체</div>' +
    D.tournaments.map(function (t) {
      return '<div class="chip' + (state.tour === t.name ? ' on' : '') +
        '" data-tour="' + esc(t.name) + '">' + esc(t.short) + '</div>';
    }).join('');
  el.querySelectorAll('[data-tour]').forEach(function (c) {
    c.addEventListener('click', function () {
      state.tour = c.dataset.tour;
      state.touchedTour = true;      // 직접 고른 뒤로는 자동으로 안 바꿉니다
      render();
    });
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

function mirrorNote(mirror, mirrorSets, totalSets) {
  if (!mirrorSets) return '';
  var parts = RACE_ORDER.filter(function (r) { return mirror[r]; })
    .map(function (r) { return RACE_LABEL[r] + ' ' + mirror[r]; });
  return '<div class="hint" style="margin-top:2px">위 막대는 서로 다른 종족끼리 붙은 ' +
    (totalSets - mirrorSets).toLocaleString() + '세트만 셉니다. ' +
    '동족전 ' + mirrorSets.toLocaleString() + '세트(' + parts.join(' · ') +
    ')는 이기고 지는 종족이 같아 상성에 넣지 않았습니다.</div>';
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

/* ── 대회 ──────────────────────────────────────────────────── */
function renderSeason() {
  var html = D.tournaments.map(function (t) {
    var isOpen = !!state.open[t.name];
    var champ = t.champion
      ? '🏆 ' + nameLink(t.champion, t.championRace) +
        ' <span class="dim">' + t.finalScore + '</span>'
      : '<span class="dim">진행 중</span>';
    var head = '<div class="srow' + (isOpen ? ' open' : '') + '" data-t="' + esc(t.name) + '">' +
      '<span class="nm">' + esc(t.name) + '</span>' +
      '<span class="num dim">' + t.matches + '매치</span>' +
      '<span class="num dim">' + t.sets + '세트</span>' +
      '<span class="num dim">' + t.players + '명</span>' +
      '<span class="ch">' + champ + '</span>' +
      '<span class="caret">▶</span></div>';

    var rounds = '<div class="stlabel">라운드</div>' +
      '<div class="tblwrap" style="border:none;background:transparent"><table><tbody>' +
      t.rounds.map(function (r) {
        return '<tr><td class="nm" style="padding-left:20px">' + esc(r.name) + '</td>' +
          '<td class="num dim">' + r.matches + '매치</td>' +
          '<td class="num dim">' + r.sets + '세트</td></tr>';
      }).join('') + '</tbody></table></div>';

    var runner = t.runnerUp
      ? '<div class="offbox"><span class="dim">준우승</span> ' +
        nameLink(t.runnerUp, t.runnerUpRace) + '</div>'
      : '';
    var mu = '<div class="stlabel">종족 상성 (세트)</div><div style="padding:4px 20px 14px">' +
      MU_KEYS.map(function (k) { return muBar(k, t.mu[k]); }).join('') +
      mirrorNote(t.mirror, t.mirrorSets, t.sets) + '</div>';
    var go = '<div style="padding:14px 20px 4px;display:flex;gap:8px;flex-wrap:wrap">' +
      '<a class="dlbtn on" href="t/' + encodeURIComponent(t.id) + '.html">' +
      '대회 상세 보기 →</a>' +
      '<span class="dlbtn" data-go="' + esc(t.name) + '">경기 기록에서 보기</span></div>';

    return head + '<div class="stages' + (isOpen ? ' open' : '') + '">' +
      go + runner + rounds + mu + '</div>';
  }).join('');

  view.innerHTML = '<div class="srow thead"><span>대회</span><span class="num">매치</span>' +
    '<span class="num">세트</span><span class="num">선수</span><span>우승</span><span></span></div>' +
    '<div class="tourlist">' + html + '</div>' +
    '<div class="hint">대회 줄을 누르면 펼쳐지고, 그 안의 <b>대회 상세 보기</b>를 누르면 ' +
    '진출 현황·라운드별 경기·선수 성적을 한 화면에서 볼 수 있습니다.<br>' +
    'ASL 기록에는 날짜가 없어 대회·라운드 순서로만 정리했습니다.</div>';

  view.querySelectorAll('[data-t]').forEach(function (el) {
    el.addEventListener('click', function (ev) {
      if (ev.target.closest('a') || ev.target.closest('[data-go]')) return;
      var n = el.dataset.t;
      state.open[n] = !state.open[n];
      render();
    });
  });
  view.querySelectorAll('[data-go]').forEach(function (el) {
    el.addEventListener('click', function (ev) {
      ev.stopPropagation();
      state.tour = el.dataset.go;
      state.touchedTour = true;
      state.tab = 'matches';
      render();
    });
  });
}

/* ── 선수 랭킹 ─────────────────────────────────────────────── */
function playerRows() {
  return D.players.map(function (p) {
    var src = state.tour === 'ALL' ? p : (p.byTour[state.tour] || null);
    if (!src) return null;
    return {
      name: p.name, slug: p.slug, race: p.race,
      titles: state.tour === 'ALL' ? p.titles : (D.champOf[state.tour] === p.name ? 1 : 0),
      setWin: src.setWin, setLoss: src.setLoss,
      matchWin: src.matchWin, matchLoss: src.matchLoss,
      tournaments: state.tour === 'ALL' ? p.tournaments : 1,
      best: state.tour === 'ALL' ? (p.bestRound || '') : (src.best || ''),
      setPct: pctNum(src.setWin, src.setLoss),
      matchPct: pctNum(src.matchWin, src.matchLoss)
    };
  }).filter(Boolean);
}

function renderRank() {
  view.appendChild(tourChips());
  view.appendChild(raceChips());
  var table = document.createElement('div');
  view.appendChild(searchBox('선수 이름 검색...', function () { draw(); }));
  view.appendChild(table);

  function draw() {
    var s = sortState();
    var rows = playerRows().filter(function (p) {
      return (state.race === 'ALL' || p.race === state.race) &&
        (!state.q || p.name.indexOf(state.q) >= 0);
    });
    rows = sortRows(rows, s.key, s.dir);
    var cols = [
      { key: 'name', label: '선수' },
      { key: 'titles', label: '우승', cls: 'num' },
      { key: 'matchWin', label: '매치', cls: 'num' },
      { key: 'matchPct', label: '매치 승률', cls: 'num' },
      { key: 'setWin', label: '세트', cls: 'num' },
      { key: 'setPct', label: '세트 승률', cls: 'num' },
      { key: 'tournaments', label: '출전 대회', cls: 'num hide-mobile' },
      { key: 'best', label: '최고 성적', cls: 'hide-mobile' }
    ];
    var body = rows.length ? rows.map(function (p, i) {
      return '<tr class="rowlink" data-href="' + pageOf(p.slug) + '">' +
        '<td><span class="rk">' + (i + 1) + '</span>' + raceBadge(p.race) +
        '<span class="nm">' + esc(p.name) + '</span></td>' +
        '<td class="num">' + (p.titles ? '🏆 ' + p.titles : '<span class="dim">-</span>') + '</td>' +
        '<td class="num">' + p.matchWin + '-' + p.matchLoss + '</td>' +
        '<td class="num">' + pct(p.matchWin, p.matchLoss) + '</td>' +
        '<td class="num">' + p.setWin + '-' + p.setLoss + '</td>' +
        '<td class="num">' + pct(p.setWin, p.setLoss) + '</td>' +
        '<td class="num hide-mobile">' + p.tournaments + '</td>' +
        '<td class="hide-mobile dim">' + esc(p.best || '-') + '</td></tr>';
    }).join('') : '<tr><td colspan="8"><div class="emptybox">해당 조건의 선수가 없습니다.</div></td></tr>';

    table.innerHTML = tableHTML(cols, body) +
      '<div class="hint">' +
      (state.tour === 'ALL' ? '통산 기록입니다. ' : esc(state.tour) + ' 기록만 보고 있습니다. ') +
      '"최고 성적"은 그 대회에서 올라간 가장 높은 라운드입니다.</div>';
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
      .sort(function (a, b) { return (b.titles - a.titles) || (b.setWin - a.setWin); });
    var card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = '<div class="cardtitle">' + raceBadge(race) + RACE_LABEL[race] +
      '<span class="note">' + list.length + '명</span></div>' +
      '<div class="tblwrap"><table><thead><tr><th class="static">선수</th>' +
      '<th class="static num">우승</th><th class="static num">세트</th></tr></thead><tbody>' +
      list.map(function (p) {
        return '<tr class="rowlink" data-href="' + pageOf(p.slug) + '">' +
          '<td class="nm">' + esc(p.name) + '</td>' +
          '<td class="num">' + (p.titles ? '🏆 ' + p.titles : '<span class="dim">-</span>') + '</td>' +
          '<td class="num">' + p.setWin + '-' + p.setLoss + '</td></tr>';
      }).join('') + '</tbody></table></div>';
    grid.appendChild(card);
  });
  view.appendChild(grid);
  grid.querySelectorAll('[data-href]').forEach(function (el) {
    el.addEventListener('click', function () { location.href = el.dataset.href; });
  });
}

/* ── 맵 통계 ───────────────────────────────────────────────── */
function renderMaps() {
  var table = document.createElement('div');
  view.appendChild(tourChips());
  view.appendChild(searchBox('맵 이름 검색...', function () { draw(); }));
  view.appendChild(table);

  function draw() {
    var s = sortState();
    var rows = D.maps;
    if (state.tour !== 'ALL') {
      rows = rows.filter(function (m) { return m.byTour[state.tour]; })
        .map(function (m) {
          var c = Object.assign({}, m);
          c.totalSets = m.byTour[state.tour];
          c.scoped = true;
          return c;
        });
    }
    if (state.q) {
      var q = state.q.toLowerCase();
      rows = rows.filter(function (m) { return m.name.toLowerCase().indexOf(q) >= 0; });
    }
    rows = sortRows(rows, s.key, s.dir);
    var scoped = state.tour !== 'ALL';
    var cols = [
      { key: 'name', label: '맵' },
      { key: 'totalSets', label: scoped ? '이 대회 세트' : '총 세트', cls: 'num' },
      { key: 'tournaments', label: '사용 대회', cls: 'num hide-mobile' },
      { key: 'mirrorSets', label: '동족전', cls: 'num hide-mobile' },
      { label: '프로토스 vs 테란', cls: 'num' },
      { label: '테란 vs 저그', cls: 'num' },
      { label: '프로토스 vs 저그', cls: 'num' }
    ];
    function cell(o, front) {
      if (!o || !(o.w + o.l)) return '<span class="dim">-</span>';
      return o.w + '-' + o.l + ' <span class="pct">(' + front + ' ' + pct(o.w, o.l) + ')</span>';
    }
    var body = rows.map(function (m) {
      return '<tr><td class="nm">' + esc(m.name) + '</td>' +
        '<td class="num">' + m.totalSets + '</td>' +
        '<td class="num hide-mobile">' + m.tournaments + '</td>' +
        '<td class="num hide-mobile dim">' + (m.mirrorSets || 0) + '</td>' +
        '<td class="num">' + cell(m.mu.PvT, 'P') + '</td>' +
        '<td class="num">' + cell(m.mu.TvZ, 'T') + '</td>' +
        '<td class="num">' + cell(m.mu.PvZ, 'P') + '</td></tr>';
    }).join('');
    table.innerHTML = tableHTML(cols, body) +
      '<div class="hint">괄호 안은 앞에 적힌 종족 기준 승률입니다. ' +
      '"동족전"은 같은 종족끼리 붙어 상성에 넣을 수 없는 세트 수입니다.' +
      (scoped ? ' 세트 수는 ' + esc(state.tour) + ' 것만 세지만, 승패는 통산 기준입니다.' : '') +
      '</div>';
    bindSort(table, draw);
  }
  draw();
}

/* ── 경기 기록 ─────────────────────────────────────────────── */
function renderMatches() {
  // 1,299매치를 한 번에 늘어놓으면 보기 어렵습니다. 처음 들어오면 최신 대회만 봅니다.
  if (!state.touchedTour && state.tour === 'ALL' && D.tournaments.length) {
    state.tour = D.tournaments[0].name;
  }
  view.appendChild(tourChips());
  var roundRow = document.createElement('div');
  roundRow.className = 'chips';
  view.appendChild(roundRow);
  var table = document.createElement('div');
  view.appendChild(searchBox('선수 이름으로 경기 찾기...', function () { draw(); }));
  view.appendChild(table);

  function drawRounds(list) {
    var seen = [];
    list.forEach(function (m) { if (seen.indexOf(m.round) < 0) seen.push(m.round); });
    seen.sort(function (a, b) {
      return D.roundOrder.indexOf(a) - D.roundOrder.indexOf(b);
    });
    if (seen.indexOf(state.round) < 0) state.round = 'ALL';
    roundRow.innerHTML = '<span class="chiplabel">라운드</span>' +
      [['ALL', '전체']].concat(seen.map(function (r) { return [r, r]; })).map(function (o) {
        return '<div class="chip' + (state.round === o[0] ? ' on' : '') +
          '" data-round="' + esc(o[0]) + '">' + esc(o[1]) + '</div>';
      }).join('');
    roundRow.querySelectorAll('[data-round]').forEach(function (c) {
      c.addEventListener('click', function () { state.round = c.dataset.round; draw(); });
    });
  }

  function draw() {
    var byTour = D.matches.filter(function (m) {
      return state.tour === 'ALL' || m.tournament === state.tour;
    });
    drawRounds(byTour);
    var rows = byTour.filter(function (m) {
      return (state.round === 'ALL' || m.round === state.round) &&
        (!state.q || m.players.some(function (n) { return n.indexOf(state.q) >= 0; }));
    });

    var body = rows.length ? rows.map(function (m) {
      var a = m.players[0], b = m.players[1];
      var aWin = m.winner === a;
      return '<tr>' +
        '<td class="muted hide-mobile">' + esc(m.tournament) + '</td>' +
        '<td class="muted">' + esc(m.round) + '</td>' +
        '<td>' + nameLink(a, m.race[a]) + ' <span class="muted">vs</span> ' +
        nameLink(b, m.race[b]) + '</td>' +
        '<td class="num score-cell" data-awin="' + (aWin ? 1 : 0) + '">' +
        '<span class="spoiler">결과 보기</span>' +
        '<span class="score-value" hidden>' + m.setWins[a] + ' - ' + m.setWins[b] + '</span></td>' +
        '<td class="hide-mobile muted" style="white-space:normal">' +
        esc((m.maps || []).filter(Boolean).join(', ')) + '</td></tr>';
    }).join('') : '<tr><td colspan="5"><div class="emptybox">해당 조건의 경기가 없습니다.</div></td></tr>';

    table.innerHTML = tableHTML([
      { label: '대회', cls: 'hide-mobile' }, { label: '라운드' }, { label: '대진' },
      { label: '결과', cls: 'num' }, { label: '맵', cls: 'hide-mobile' }
    ], body) +
      '<div class="hint">' + rows.length + '매치를 보고 있습니다. ' +
      '한 줄이 매치(시리즈) 하나이고, 맵은 그 시리즈에서 치른 순서대로입니다. ' +
      '"결과 보기"를 눌러야 스코어가 나옵니다.</div>';

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

function renderRecords() {
  var r = D.records;
  var html = '<div class="card"><div class="cardtitle">종족 상성 — 세트 기준' +
    '<span class="note">통산 ' + D.global.totalSets.toLocaleString() + '세트</span></div>' +
    MU_KEYS.map(function (k) { return muBar(k, D.mu[k]); }).join('') +
    mirrorNote(D.global.mirror, D.global.mirrorSets, D.global.totalSets) + '</div>';

  html += '<div class="card"><div class="cardtitle">역대 우승자</div>' +
    '<div class="tblwrap"><table><thead><tr><th class="static">대회</th>' +
    '<th class="static">우승</th><th class="static num">스코어</th>' +
    '<th class="static">준우승</th></tr></thead><tbody>' +
    D.tournaments.map(function (t) {
      if (!t.champion) {
        return '<tr><td class="nm">' + esc(t.name) + '</td>' +
          '<td class="dim" colspan="3">진행 중</td></tr>';
      }
      return '<tr><td class="nm">' + esc(t.name) + '</td>' +
        '<td>🏆 ' + nameLink(t.champion, t.championRace, 'win') + '</td>' +
        '<td class="num">' + esc(t.finalScore) + '</td>' +
        '<td>' + nameLink(t.runnerUp, t.runnerUpRace) + '</td></tr>';
    }).join('') + '</tbody></table></div></div>';

  html += '<div class="grid2">' +
    recordCard('최다 우승', '', r.titles) +
    recordCard('최다 세트 승', '', r.setWin) +
    recordCard('세트 승률', r.minSet + '세트 이상', r.setPct) +
    recordCard('최다 매치 승', '시리즈 기준', r.matchWin) +
    recordCard('매치 승률', r.minMatch + '매치 이상', r.matchPct) +
    recordCard('최다 출전 대회', '', r.tournaments) +
    '</div>';

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

/* ── 라우팅 ────────────────────────────────────────────────── */
function render() {
  renderTabs();
  writeHash();
  view.innerHTML = '';
  if (state.tab === 'season') renderSeason();
  else if (state.tab === 'rank') renderRank();
  else if (state.tab === 'roster') renderRoster();
  else if (state.tab === 'maps') renderMaps();
  else if (state.tab === 'matches') renderMatches();
  else if (state.tab === 'records') renderRecords();
}

window.addEventListener('hashchange', function () { readHash(); render(); });
readHash();
render();

$('#built').textContent = new Date(D.builtAt).toLocaleString('ko-KR');
