/**
 * ASL 연동본에 '보기용' 시트를 만들어 주는 구글 앱스 스크립트.
 *
 * 왜 스크립트인가
 *   연동본의 첫 번째 시트는 A1 의 =IMPORTRANGE(...) 결과가 A1:N 으로 펼쳐진
 *   것입니다. 그 범위에 값을 하나라도 쓰면 IMPORTRANGE 가 #REF! 로 깨집니다.
 *   그래서 원본 시트는 손대지 않고, 옆에 '보기용' 시트를 따로 만들어 씁니다.
 *
 * 쓰는 법 (한 번만)
 *   1. 연동본 시트를 엽니다
 *   2. 상단 메뉴 [확장 프로그램] → [Apps Script]
 *   3. 열린 편집기의 내용을 지우고 이 파일 전체를 붙여넣습니다
 *   4. 저장(💾) 후 ▶ 실행 → 권한 승인 (본인 시트라 안전합니다)
 *   5. 연동본 시트로 돌아오면 아래에 '보기용' 탭이 생겨 있습니다
 *
 * 그다음부터
 *   시트를 열 때마다 자동으로 새로 그립니다. 직접 하시려면 상단 메뉴
 *   [🔄 보기용] → [지금 새로고침] 을 누르시면 됩니다.
 */

var VIEW_NAME = '보기용';

// 대회명과 라운드를 가르는 규칙 — 사이트의 asl_import.py 와 같게 맞췄습니다.
var TOURNEY_RE = /^(대국민\s*스타리그|ASL\s*Season\s*\d+)\s*(.*)$/;
var ROUND_ALIAS = { 'WILD CARD': '와일드카드', '결승': '결승전', 'FINALS': '결승전' };

var RACE_BG = { 'T': '#dbeafe', 'P': '#fef3c7', 'Z': '#ede9fe' };
var RACE_LABEL = { 'T': '테란', 'P': '토스', 'Z': '저그' };

var HEAD = ['경기번호', '대회', '라운드', '승자', '종족', '맵', '종족', '패자'];
var WIDTHS = [80, 150, 90, 110, 60, 150, 60, 110];


function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🔄 보기용')
    .addItem('지금 새로고침', 'buildView')
    .addToUi();
  try {
    buildView();
  } catch (e) {
    // 열 때 실패해도 시트 자체는 열려야 하므로 조용히 넘어갑니다.
  }
}


/** 줄바꿈·겹공백을 한 칸으로 눌러 줍니다. */
function norm(v) {
  return String(v == null ? '' : v).replace(/\s+/g, ' ').trim();
}


/** '대국민 스타리그 32강' → ['대국민 스타리그', '32강'] */
function splitGroup(text) {
  var t = norm(text);
  var m = TOURNEY_RE.exec(t);
  var tour, rnd;
  if (m) {
    tour = norm(m[1]);
    rnd = norm(m[2]);
  } else {
    var i = t.lastIndexOf(' ');
    tour = i > 0 ? t.slice(0, i) : t;
    rnd = i > 0 ? t.slice(i + 1) : '';
  }
  return [tour, ROUND_ALIAS[rnd] || rnd];
}


function buildView() {
  var ss = SpreadsheetApp.getActive();
  var src = ss.getSheets()[0];              // 연동본(IMPORTRANGE) 시트 — 읽기만 합니다
  var last = src.getLastRow();
  if (last < 3) return;

  var vals = src.getRange(3, 1, last - 2, 9).getValues();

  var rows = [];
  var group = '';
  for (var i = 0; i < vals.length; i++) {
    var r = vals[i];
    var no = r[0], grp = r[1], a = norm(r[2]), ar = norm(r[3]).toUpperCase();
    var wa = norm(r[4]), mp = norm(r[5]), wb = norm(r[6]);
    var br = norm(r[7]).toUpperCase(), b = norm(r[8]);

    if (norm(grp)) group = grp;             // 병합 칸은 첫 줄에만 값이 있어 이어받습니다
    if (!a || !b || !group) continue;
    if (!(wa === '승' || wb === '승')) continue;

    var g = splitGroup(group);
    var aWon = (wa === '승');
    rows.push([
      no,
      g[0], g[1],
      aWon ? a : b, aWon ? ar : br,
      mp,
      aWon ? br : ar, aWon ? b : a
    ]);
  }
  if (!rows.length) return;

  // ── 보기용 시트 다시 그리기 ─────────────────────────────
  var out = ss.getSheetByName(VIEW_NAME);
  if (!out) out = ss.insertSheet(VIEW_NAME);
  out.clear();
  out.clearConditionalFormatRules();
  if (out.getMaxColumns() > HEAD.length) {
    out.deleteColumns(HEAD.length + 1, out.getMaxColumns() - HEAD.length);
  }

  out.getRange(1, 1, 1, HEAD.length).setValues([HEAD]);
  out.getRange(2, 1, rows.length, HEAD.length).setValues(rows);

  // 머리글
  var head = out.getRange(1, 1, 1, HEAD.length);
  head.setBackground('#1f2937').setFontColor('#ffffff')
      .setFontWeight('bold').setHorizontalAlignment('center')
      .setVerticalAlignment('middle');
  out.setRowHeight(1, 34);
  out.setFrozenRows(1);

  var body = out.getRange(2, 1, rows.length, HEAD.length);
  body.setVerticalAlignment('middle').setFontSize(10);
  out.getRange(2, 1, rows.length, 1).setHorizontalAlignment('center');   // 경기번호
  out.getRange(2, 3, rows.length, 1).setHorizontalAlignment('center');   // 라운드
  out.getRange(2, 5, rows.length, 1).setHorizontalAlignment('center');   // 종족
  out.getRange(2, 7, rows.length, 1).setHorizontalAlignment('center');   // 종족
  out.getRange(2, 4, rows.length, 1).setFontWeight('bold');              // 승자

  for (var c = 0; c < WIDTHS.length; c++) out.setColumnWidth(c + 1, WIDTHS[c]);

  // 줄무늬 — 눈이 줄을 따라가기 쉽게
  body.applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY, false, false);

  // 종족 칸에 색 (T 파랑 · P 노랑 · Z 보라)
  var rules = [];
  ['T', 'P', 'Z'].forEach(function (race) {
    [5, 7].forEach(function (col) {
      rules.push(SpreadsheetApp.newConditionalFormatRule()
        .whenTextEqualTo(race)
        .setBackground(RACE_BG[race])
        .setRanges([out.getRange(2, col, rows.length, 1)])
        .build());
    });
  });
  out.setConditionalFormatRules(rules);

  // 대회가 바뀌는 줄에 윗선을 그어 구간을 나눕니다
  for (var j = 1; j < rows.length; j++) {
    if (rows[j][1] !== rows[j - 1][1]) {
      out.getRange(j + 2, 1, 1, HEAD.length)
         .setBorder(true, null, null, null, null, null, '#9ca3af',
                    SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
    }
  }

  out.getRange(1, 1, rows.length + 1, HEAD.length).createFilter();

  // 맨 아래에 언제 만든 것인지 남깁니다
  var stamp = Utilities.formatDate(new Date(),
    Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm');
  out.getRange(rows.length + 3, 1)
     .setValue('세트 ' + rows.length + '줄 · ' + stamp + ' 기준 (연동본에서 자동으로 만듭니다)')
     .setFontColor('#6b7280').setFontSize(9);

  ss.setActiveSheet(out);
}
