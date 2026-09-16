/**
 * 구글시트를 고치면 곧바로 사이트에 반영시키는 구글 앱스 스크립트. (2026-09-16)
 *
 * 왜 필요한가
 *   GitHub 예약 실행(15분마다)만으로도 반영은 됩니다. 다만 GitHub 의 예약은
 *   서버가 붐비면 수십 분~몇 시간씩 늦는 일이 실제로 있었습니다(2026-09-15
 *   기록: 예정보다 40분·2.5시간·4.5시간 늦음). 이 스크립트를 넣어 두면 시트를
 *   고치는 순간 GitHub 을 직접 두드려서, 대개 1분 안에 사이트가 바뀝니다.
 *   예약 실행은 그대로 두고 '못 받았을 때의 보험'으로 남겨 둡니다.
 *
 * 어느 시트에 넣나
 *   끝장전 시트(Results 탭이 있는 것)와 ASL 연동본, 둘 다에 넣으면 좋습니다.
 *   하나만 넣어도 그 시트의 수정은 즉시 반영됩니다.
 *
 * 넣는 법 (시트마다 한 번씩)
 *   1. 깃허브에서 토큰을 만듭니다
 *        github.com → 우측 위 프로필 → Settings → Developer settings
 *        → Personal access tokens → Fine-grained tokens → Generate new token
 *        · Repository access : Only select repositories → hspark-art/sc-endgame
 *        · Permissions       : Repository permissions → Contents → Read and write
 *        · Expiration        : 1년 정도 (만료되면 다시 만들어 4번만 다시 하면 됩니다)
 *      만들고 나온 토큰 문자열(github_pat_... )을 복사해 둡니다.
 *   2. 시트 상단 메뉴 [확장 프로그램] → [Apps Script]
 *   3. 편집기 내용을 지우고 이 파일 전체를 붙여넣고 저장(💾)
 *   4. 왼쪽 [프로젝트 설정 ⚙] → 맨 아래 [스크립트 속성] → [속성 추가]
 *        속성 : GITHUB_TOKEN     값 : 1번에서 복사한 토큰
 *      (토큰은 여기에만 둡니다. 스크립트 본문이나 저장소에 적지 마세요.)
 *   5. 편집기로 돌아와 함수 목록에서 setup 을 고르고 ▶ 실행 → 권한 승인
 *   6. 확인하려면 pushNow 를 ▶ 실행 → 실행 로그에 '보냈습니다 (204)' 가 나오면 성공.
 *      GitHub 저장소 Actions 탭에 「기록 자동 갱신」이 바로 돌기 시작합니다.
 *
 * 그다음부터
 *   시트를 고치면 알아서 갑니다. 손볼 것 없습니다.
 *   끄고 싶으면 편집기에서 teardown 을 ▶ 실행하세요.
 */

var REPO = 'hspark-art/sc-endgame';
var EVENT = 'sheet-changed';        // .github/workflows/update.yml 의 repository_dispatch types
var MIN_GAP_MS = 60 * 1000;         // 연속 수정 때 1분에 한 번만 보냅니다


/** 5번에서 한 번 실행 — 수정 감지 + 5분마다 밀린 것 보내기, 두 가지를 겁니다. */
function setup() {
  teardown();
  var ss = SpreadsheetApp.getActive();
  ScriptApp.newTrigger('onSheetChange').forSpreadsheet(ss).onChange().create();
  ScriptApp.newTrigger('flushPending').timeBased().everyMinutes(5).create();
  Logger.log('설치했습니다. 이제 시트를 고치면 자동으로 사이트가 갱신됩니다.');
}


/** 자동 실행을 모두 걷어냅니다. */
function teardown() {
  ScriptApp.getProjectTriggers().forEach(function (t) { ScriptApp.deleteTrigger(t); });
  Logger.log('자동 실행을 껐습니다.');
}


/** 시트가 바뀔 때마다 구글이 부릅니다. 너무 잦으면 미뤄 두고 flushPending 이 처리합니다. */
function onSheetChange() {
  var props = PropertiesService.getScriptProperties();
  var last = Number(props.getProperty('lastPushAt') || 0);
  if (Date.now() - last < MIN_GAP_MS) {
    props.setProperty('pending', '1');   // 방금 보냈음 — 잠시 뒤에 몰아서
    return;
  }
  pushNow();
}


/** 5분마다 — 위에서 미뤄 둔 수정이 있으면 그때 보냅니다. */
function flushPending() {
  var props = PropertiesService.getScriptProperties();
  if (props.getProperty('pending') === '1') {
    pushNow();
  }
}


/** 지금 바로 GitHub 에 '시트가 바뀌었다'고 알립니다. 시험 실행용으로도 씁니다. */
function pushNow() {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty('GITHUB_TOKEN');
  if (!token) {
    throw new Error('스크립트 속성에 GITHUB_TOKEN 이 없습니다 — 설명 4번을 봐 주세요.');
  }

  var res = UrlFetchApp.fetch('https://api.github.com/repos/' + REPO + '/dispatches', {
    method: 'post',
    contentType: 'application/json',
    headers: {
      Authorization: 'Bearer ' + token,
      Accept: 'application/vnd.github+json'
    },
    payload: JSON.stringify({ event_type: EVENT }),
    muteHttpExceptions: true
  });

  var code = res.getResponseCode();
  props.setProperty('lastPushAt', String(Date.now()));
  props.deleteProperty('pending');

  if (code === 204) {
    Logger.log('보냈습니다 (204) — 곧 사이트가 갱신됩니다.');
  } else {
    // 토큰 만료·권한 부족이 대부분입니다. 401/403 이면 토큰을 다시 만들어 주세요.
    Logger.log('보내지 못했습니다 (' + code + ') ' + res.getContentText());
    throw new Error('GitHub 이 ' + code + ' 를 돌려줬습니다 — 토큰과 권한을 확인해 주세요.');
  }
}
