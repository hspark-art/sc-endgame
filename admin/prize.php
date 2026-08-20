<?php require __DIR__ . '/auth.php'; admin_require_login(); ?>
<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>상품 추첨 관제 — 끝장전</title><style>
*{box-sizing:border-box}body{margin:0;background:#0a0d13;color:#e8ecf3;
font-family:'Pretendard','Malgun Gothic',sans-serif;font-size:14px}
.wrap{margin:0 auto;padding:14px 18px}
h1{font-size:18px;margin:4px 0 12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.grid{display:grid;gap:12px;grid-template-columns:1.1fr .9fr 1fr}
@media(max-width:1100px){.grid{grid-template-columns:1fr}}
.card{background:#141821;border:1px solid #232a38;border-radius:12px;padding:12px;min-width:0}
.ct{font-weight:800;margin-bottom:8px;display:flex;gap:8px;align-items:center}
.ct .n{color:#8a93a6;font-weight:500;font-size:11.5px}
.scroll{overflow:auto;max-height:520px}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{padding:5px 7px;text-align:left;border-bottom:1px solid #171c25;white-space:nowrap}
th{color:#8a93a6;font-size:11px}
.num{text-align:right;font-variant-numeric:tabular-nums}
.chatline{padding:3px 4px;border-bottom:1px solid #12161e;font-size:13px;
overflow:hidden;text-overflow:ellipsis;white-space:nowrap;cursor:pointer;border-radius:5px}
.chatline:hover{background:#1a2130}
.chatline b{color:#7cb6ff;font-weight:600}.balloon{color:#ffb020;font-weight:700}
button{background:#1c8cff;border:0;color:#fff;border-radius:8px;padding:8px 13px;
font-weight:700;cursor:pointer;font-family:inherit}
button.gray{background:#232a38}button.red{background:#e0392b}
button.green{background:#1f9d55}
button:disabled{opacity:.35;cursor:default}
input,select{background:#1b202b;color:#e8ecf3;border:1px solid #232a38;
border-radius:8px;padding:7px 9px;font-family:inherit;font-size:13px}
.row{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin:6px 0}
.warn{color:#ffb020;font-weight:700}.ok{color:#4ade80}
.pill{background:#1b202b;border:1px solid #232a38;border-radius:999px;
padding:2px 9px;font-size:11.5px;color:#8a93a6}
#users td:nth-child(2){position:relative;z-index:0}
.actbar{position:absolute;left:0;top:2px;bottom:2px;z-index:-1;border-radius:5px;
background:linear-gradient(90deg,rgba(28,140,255,.30),rgba(255,176,32,.14));min-width:2px}
.live{color:#ff4d5a;font-weight:900}
img.thumb{width:44px;height:44px;object-fit:cover;border-radius:8px;
vertical-align:middle;margin-right:6px;background:#0a0d13}
.hint{color:#8a93a6;font-size:11.5px;line-height:1.6;margin-top:6px}
hr{border-color:#232a38}
a.top{color:#8a93a6;font-size:12.5px;text-decoration:none}
a.top:hover{color:#e8ecf3}
.modal{position:fixed;inset:0;background:rgba(4,6,10,.66);z-index:50;display:flex;
align-items:flex-start;justify-content:center;padding:40px 16px;overflow:auto}
.modalbox{background:#141821;border:1px solid #2a3446;border-radius:14px;
padding:16px 18px;max-width:620px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.5)}
.chip{cursor:pointer;user-select:none;background:#1b202b}
.chip.on{border-color:#1c8cff;color:#cfe6ff;background:#12283f}
.rwrow{padding:3px 3px;border-bottom:1px solid #171c25;font-size:12.5px;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
body.maskacc .acc{filter:blur(6px);user-select:none;pointer-events:none}
.px{background:transparent;color:#8a93a6;border:0;padding:2px 8px;font-weight:900;font-size:15px;cursor:pointer;line-height:1}
.px:hover{color:#f87171}
@media(max-width:760px){
  .wrap{padding:10px 10px}
  body{font-size:15px}
  h1{font-size:16px}
  .card{padding:11px}
  #chat{max-height:40vh !important}
  .scroll{max-height:48vh}
  input,select{font-size:16px;padding:10px 11px}
  #pickNick,#prizeSel{flex:1 1 100% !important}
  .row>button{min-height:46px;padding:12px 14px;font-size:15px}
  #users td,#users th{padding:9px 5px;font-size:14.5px}
  /* 좁은 화면에선 SOOP계정·확률 열을 숨겨 깔끔하게 */
  #users th:nth-child(3),#users td:nth-child(3),
  #users th:nth-child(6),#users td:nth-child(6){display:none}
  #users button{padding:9px 14px;font-size:14px}
  .chatline{padding:9px 5px;font-size:14.5px}
  .rwrow{padding:8px 4px;font-size:14px}
  #winners td,#winners th{padding:8px 5px}
  #settingsModal .modalbox{padding:13px}
}
</style></head><body><div class="wrap">
<h1>🎁 상품 추첨 관제
<button id="btnStart" class="green" onclick="startSession()">▶ 스타트</button>
<button id="btnStop" class="red" onclick="stopSession()" disabled>⏹ 종료</button>
<span id="liveflag" class="pill">상태 확인 중…</span></h1>
<div class="row" style="margin:0 0 10px">
<span class="n">채널</span>
<input id="bjInput" placeholder="talent (우리 방송)" style="width:180px">
<button class="gray" onclick="goCh(document.getElementById('bjInput').value.trim())">붙기</button>
<button class="gray" onclick="goCh('')">우리 채널(talent)</button>
<button class="gray" onclick="goCh('__demo')">연습(가짜 채팅)</button>
<a class="top" href="prize_overlay.php" target="_blank">📺 방송 장면 열기 ↗</a>
<button class="gray" style="padding:4px 10px" onclick="openSettings()">⚙ 확률·규칙 설정</button>
<a class="top" href="cg.php">CG 제작 →</a>
<span class="n">이 창을 켜 둔 동안만 채팅이 집계됩니다</span></div>
<a href="prize_sheet.php" style="display:flex;align-items:center;gap:10px;margin:0 0 12px;
padding:12px 16px;border-radius:12px;border:1px solid #2e3a52;text-decoration:none;
background:linear-gradient(90deg,rgba(28,140,255,.16),rgba(255,198,61,.10));
color:#e8ecf3;font-weight:800">&#128210; 당첨자 시트
<span style="color:#8a93a6;font-weight:500;font-size:12.5px">날짜·상품별 정리 · SOOP계정 채우기 · 숲 쪽지 일괄 발송 →</span></a>
<script>
function goCh(v){
  if(v==='__demo'){location.href='prize.php?demo';return;}
  location.href = v ? ('prize.php?bj='+encodeURIComponent(v)) : 'prize.php';
}
</script>
<div class="row" id="panelBar" style="margin:0 0 10px;gap:5px;flex-wrap:wrap"></div>
<div class="grid">

<div class="card" data-panel="chat"><div class="ct">실시간 채팅 <span class="n" id="totline"></span>
<button class="gray" style="margin-left:auto;padding:4px 10px" onclick="clearChat()" title="화면만 비웁니다 — 저장된 로그는 그대로 남습니다">채팅 지우기</button><button class="px" onclick="togglePanel('chat')" title="이 창 닫기">✕</button></div>
<div class="scroll" id="chat" style="max-height:560px"></div></div>

<div class="card"><div class="ct" data-panel="users">시청자 활약 <span class="n">별풍선·채팅 순</span>
<button class="gray" style="margin-left:auto;padding:4px 10px" onclick="toggleMask()" id="maskBtn">🙈 계정 가리기</button>
<button class="gray" style="padding:4px 10px" onclick="downloadActivity()">⬇ 활약 CSV</button>
<button class="gray" style="padding:4px 10px" onclick="clearStats()">집계 초기화</button><button class="px" onclick="togglePanel('users')" title="이 창 닫기">✕</button></div>
<div class="scroll"><table id="users"><thead><tr><th class="num">#</th><th>닉네임</th>
<th>SOOP계정</th><th class="num">채팅</th><th class="num">별풍선</th><th class="num">확률↑</th>
<th>당첨</th><th></th></tr></thead><tbody></tbody></table></div>
<hr><div class="ct" data-panel="pastdays">지난 방송 <span class="n">저절로 저장됩니다</span><button class="px" style="margin-left:auto" onclick="togglePanel('pastdays')" title="이 창 닫기">✕</button></div>
<div class="scroll" style="max-height:150px"><table id="pastdays"><tbody></tbody></table></div></div>

<div class="card">
<div class="ct" data-panel="pick">당첨 만들기<button class="px" style="margin-left:auto" onclick="togglePanel('pick')" title="이 창 닫기">✕</button></div>
<div class="row"><input id="pickNick" placeholder="닉네임 — 채팅을 눌러도 들어갑니다" style="flex:1">
<select id="prizeSel" style="flex:1"></select></div>
<div id="dupwarn" class="hint"></div>
<div class="row">
<button onclick="manualPick()">지명 → 방송 장면</button>
<button class="gray" onclick="plinko()">🎯 핀볼</button>
<button class="gray" onclick="roulette()">🎡 룰렛</button>
<button class="gray" onclick="kings()">👑 오늘의 왕</button>
<button class="gray" onclick="clearOverlay()">장면 지우기</button></div>
<div class="hint">자막은 <b>자막 창</b>(위 링크)에 나옵니다 — 방송 프로그램에서 그 창을
잡으면 됩니다. 핀볼은 채팅·별풍선에 따라 확률이 조금 올라갑니다.</div>
<hr>
<div class="ct" data-panel="prizes">상품 <span class="n">사진도 넣을 수 있습니다</span><button class="px" style="margin-left:auto" onclick="togglePanel('prizes')" title="이 창 닫기">✕</button></div>
<div id="prizes"></div>
<div class="row"><input id="pName" placeholder="상품 이름" style="flex:1">
<input type="file" id="pPhoto" accept="image/*" style="display:none">
<button class="gray" onclick="document.getElementById('pPhoto').click()">사진</button>
<button onclick="addPrize()">추가</button></div>
<span id="pPhotoName" class="hint"></span>
<hr>
<div class="ct" data-panel="winners">당첨자 시트 <span class="n" id="wcount"></span>
<a class="top" href="prize_sheet.php">전체 화면 ↗</a>
<button class="gray" style="margin-left:auto;padding:4px 10px" onclick="copyLedger()">📋 복사</button>
<button class="gray" style="padding:4px 10px" onclick="downloadLedger()">⬇ CSV</button><button class="px" onclick="togglePanel('winners')" title="이 창 닫기">✕</button></div>
<div class="scroll" style="max-height:260px"><table id="winners"><thead><tr>
<th>날짜</th><th>닉네임</th><th>SOOP계정</th><th>상품</th><th>방식</th><th></th>
</tr></thead><tbody></tbody></table></div>
<div class="hint">쪽지 ✉ 는 그 계정의 SOOP 방송국을 새 탭으로 엽니다(거기서 쪽지). 계정이
비었으면 ✏로 넣으세요 — 채팅·별풍선을 친 시청자는 자동으로 채워집니다.</div>
<div class="row"><input id="wDate" placeholder="2026-08-13" style="width:104px">
<input id="wNick" placeholder="닉네임" style="flex:1">
<input id="wPrize" placeholder="상품" style="flex:1">
<button class="gray" onclick="addWinner()">지난 기록 넣기</button></div>
<hr>
<div class="ct" data-panel="recent">최근 당첨자 <span class="n">중복 방지</span>
<span style="flex:1"></span>
<button class="pill chip" onclick="setDupM(1)">1개월</button>
<button class="pill chip" onclick="setDupM(2)">2개월</button>
<button class="pill chip" onclick="setDupM(3)">3개월</button><button class="px" onclick="togglePanel('recent')" title="이 창 닫기">✕</button></div>
<div id="dupLegend" class="hint" style="margin:2px 0"></div>
<div class="scroll" style="max-height:230px"><div id="recentWinners"></div></div>
</div>

</div></div>
<div id="settingsModal" class="modal" style="display:none" onclick="if(event.target===this)closeSettings()">
 <div class="modalbox">
  <div class="ct">⚙ 확률·규칙 설정 <span style="flex:1"></span>
   <button class="gray" style="padding:4px 10px" onclick="closeSettings()">✕ 닫기</button></div>
  <div class="row hint">채팅 <input id="sChatFull" style="width:52px"> 개에
  +<input id="sChatMax" style="width:46px"> · 별풍선
  <input id="sBalFull" style="width:60px"> 개에 +<input id="sBalMax" style="width:46px"></div>
  <div class="row hint">
  <label><input type="checkbox" id="sExcl"> 이전 당첨자 전체 제외</label>
  · 최근 <input id="sWeeks" style="width:40px"> 주 당첨자 제외(0=끄기)
  · 별풍선 <input id="sAlert" style="width:52px"> 개 이상이면 감사 배너</div>
  <div class="row hint">집계 제외 계정 <input id="sExclAcc" style="flex:1;min-width:220px"
   placeholder="매크로·스태프 아이디/닉 (스페이스나 쉼표로 여러 개)"></div>
  <div class="row hint">우리 채널 (데이터 저장) <input id="sRealCh" style="flex:1;min-width:200px"
   placeholder="talent (기본) — 다른 방송도 저장하려면 아이디 추가"></div>
  <div class="hint" style="margin:-2px 0 6px">여기 적은 채널만 채팅·활약·당첨 데이터를 저장합니다.
  나머지 채널(테스트용)은 저장하지 않고 창을 닫으면 사라집니다.</div>
  <div class="hint" style="margin:-2px 0 6px">우리 방송 계정(<b id="bjName"></b>)은 자동 제외됩니다.
  자동 매크로 채팅·매니저 계정을 여기 넣으면 시청자 활약 집계에서 빠집니다.</div>
  <div class="row hint">구글 문서 ID <input id="sGdoc" style="flex:1;min-width:180px" placeholder="당첨자 문서 주소의 /d/ 다음 부분">
  <span id="gdocInfo" class="pill"></span></div>
  <div class="row hint">슬랙 웹훅 <input id="sSlack" style="flex:1;min-width:180px" placeholder="https://hooks.slack.com/..."></div>
  <div class="row"><button onclick="saveSettings()">설정 저장</button>
  <button class="gray" onclick="copyLedger()">📋 당첨 기록 복사</button>
  <button class="gray" onclick="slackReport()">📨 슬랙으로 요약</button></div>
 </div>
</div>
<script>
/* ── 채팅 집계 (이 브라우저 안에서) ─────────────────────────── */
/* 주소 뒤에 ?bj=아이디 를 붙이면 그 채널에 붙습니다 — 우리 방송이 없을 때
   다른 라이브에서 수신을 시험하는 용도입니다. 시험 채널일 때는
   방송별 눈금(stats)을 저장하지 않아 진짜 기록과 섞이지 않습니다. */
const BJ=(new URLSearchParams(location.search).get('bj')||'talent')
  .toLowerCase().replace(/[^a-z0-9_]/g,'')||'talent';
const IS_DEMO = location.search.includes('demo');
function realChSet(){
  let list=['talent'];
  try{const j=JSON.parse(localStorage.getItem('pzRealCh')||'null');if(Array.isArray(j)&&j.length)list=j;}catch(e){}
  return new Set(list.map(x=>String(x).toLowerCase()).concat('talent'));
}
/* 우리 채널(기록 저장 대상)이 아니면 휘발성(테스트)으로 봅니다.
   기본은 talent, 설정에서 다른 채널도 추가할 수 있습니다. */
let IS_TEST_CH = !realChSet().has(BJ) || IS_DEMO;
const F='\x0c', users={}, recent=[], rawUnknown=[];
const sess={on:false,date:'',startedAt:''};   // 스타트/종료 상태
const logBuf=[];                              // 서버로 보낼 채팅 로그 대기줄
const LSKEY='pzLive_'+BJ;   // 이 브라우저에 로그·집계 임시 보관 (창을 나가도 유지)
let liveOn=false, liveTitle='', ws=null, pingT=null, ST=null;
let settings={chatFull:50,chatBonusMax:0.3,balloonFull:1000,balloonBonusMax:0.5,
  excludeWinners:false,excludeWeeks:0,balloonAlert:100,gdocId:'',slackWebhook:''};
let gdoc={names:[],ids:[]};   // 구글 문서에서 읽어 온 당첨자
let exclSet=new Set(), macroCount=0;   // 집계 제외 계정, 제외한 채팅 수
let dupMonths=+(localStorage.getItem('pzDupM')||1)||1;   // 최근 당첨자 표시 기간(개월)

function esc(s){return String(s??'').replace(/[&<>"]/g,
  c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function cleanNick(s){s=(s||'').trim();
  if(s.endsWith(')')&&s.includes('(')) s=s.slice(0,s.lastIndexOf('('));return s.trim()}
function rebuildExcl(){
  exclSet=new Set([BJ]);   // 우리 방송 계정은 항상 제외
  (settings.excludeAccounts||'').toLowerCase().split(/[\s,]+/).filter(Boolean)
    .forEach(x=>exclSet.add(x));
}
function isExcluded(id,nick){
  const i=(id||'').toLowerCase().trim();
  if(i&&exclSet.has(i))return true;
  return exclSet.has((nick||'').replace(/\s+/g,'').toLowerCase());
}
function bump(nick,kind,n){
  if(!nick)return;
  const u=users[nick]??(users[nick]={c:0,b:0});
  if(kind==='c')u.c++; else u.b+=n;
}
function onEvent(ev){
  // 우리 방송 계정(매크로)·제외 계정은 시청자 활약에 넣지 않습니다
  if(isExcluded(ev.id,ev.nick)){macroCount++;return;}
  if(ev.t==='chat'){bump(ev.nick,'c');if(ev.id)uid[ev.nick]=ev.id;recent.push(ev);}
  else if(ev.t==='balloon'){
    bump(ev.nick,'b',ev.count);if(ev.id)uid[ev.nick]=ev.id;recent.push(ev);
    // 큰 별풍선이면 방송 장면에 감사 배너를 자동으로 띄웁니다
    if(!IS_TEST_CH && ev.count>=(settings.balloonAlert||100))
      api('toast_add',{nick:ev.nick,count:ev.count});
  }
  if(sess.on&&!IS_TEST_CH&&(ev.t==='chat'||ev.t==='balloon'))logBuf.push(ev);
  recent.splice(0,Math.max(0,recent.length-200));
}
const uid={};   // 닉네임 → SOOP 아이디 (지금 방송에서 본 것)
/* SOOP 채팅 프로토콜 — 시청자용 접속과 같은 방식입니다 */
function pkt(svc,body){
  const b=new TextEncoder().encode(body);
  const head=new TextEncoder().encode('\x1b\t'+String(svc).padStart(4,'0')
    +String(b.length).padStart(6,'0')+'00');
  const u=new Uint8Array(head.length+b.length);u.set(head);u.set(b,head.length);return u;
}
/* 별풍선 중복제거 — svc109 의 [3]은 별풍선 '종류' 해시라 여러 사람이
   공유합니다(실측: 서로 다른 3명이 같은 mid). 그래서 mid 만으로 지우면
   다른 사람·다른 개수 선물까지 버려 절반 이상을 놓쳤습니다. 이제
   (종류+보낸사람+개수)가 똑같고 8초 안에 다시 온 것만 재전송으로 보고
   건너뜁니다. 다른 사람·다른 개수·시간차 큰 같은 선물은 각각 셉니다. */
let seenBalloons=new Map();   // (보낸사람|개수) -> 마지막 시각(ms)
const BAL_WINDOW=8000;
/* 별풍선 중복제거 — 같은 사람이 같은 개수를 8초 안에 다시 보내면 재전송으로 봄.
   svc109·svc18 을 한 표에서 함께 보므로, 한 선물이 두 svc 로 겹쳐 와도 한 번만 셈. */
function dedupBalloon(who,cnt){
  const key=who+'|'+cnt, t=Date.now(), last=seenBalloons.get(key);
  seenBalloons.set(key,t);
  if(seenBalloons.size>5000){for(const [k,v] of seenBalloons)if(t-v>=BAL_WINDOW)seenBalloons.delete(k);}
  return last==null || t-last>=BAL_WINDOW;   // true = 새 별풍선
}
/* 이모티콘·시그니처 선물의 아이템ID (별풍선으로 사지만 별풍선 집계엔 안 넣음).
   실측으로 확인되는 대로 계속 추가합니다 (같은 사람이 같은 아이템ID 를
   개수만 바꿔 반복 발송하면 이모티콘 신호). */
const EMOTE_ITEMS=new Set(['537477152','2684436480']);
function parseBalloon(f){   // svc 109 — [4]개수 [6]보낸이ID [7]보낸이닉 [8]아이템ID
  if(f.length<8)return null;
  const cnt=(f[4]||'').trim();
  if(!/^\d+$/.test(cnt)||+cnt<=0)return null;
  const item=(f[8]||'').split('|')[0];
  if(EMOTE_ITEMS.has(item))return null;   // 이모티콘/시그니처 — 별풍선 아님
  const nick=cleanNick(f[7]); if(!nick)return null;
  const id=cleanNick(f[6]);
  return dedupBalloon(id||nick,cnt)?{t:'balloon',nick,count:+cnt,id}:null;
}
function parseBalloon18(f){  // svc 18 별풍선 — [1]채널 [2]보낸이ID [3]보낸이닉 [4]개수 (talent 실측 2026-08)
  if(f.length<5)return null;
  const cnt=(f[4]||'').trim();
  if(!/^\d+$/.test(cnt)||+cnt<=0||+cnt>100000)return null;
  const id=cleanNick(f[2]), nick=cleanNick(f[3]);
  if(!id||!nick||norm(id)===norm(nick))return null;   // id==닉 은 누적·순위 이벤트라 제외
  if((f[1]||'').toLowerCase()!==BJ)return null;        // 이 채널로 온 선물만
  return dedupBalloon(id,cnt)?{t:'balloon',nick,count:+cnt,id}:null;
}
async function connectChat(){
  if(!sess.on){setStatus('⏹ 종료 상태 — ▶ 스타트를 누르면 집계를 시작합니다');sessBtns();return;}
  if(IS_DEMO)return;                        // 연습 모드는 진짜 채팅 서버에 안 붙습니다
  let info;
  try{info=await (await fetch('prize_api.php?act=live&bj='+BJ)).json();}
  catch(e){setStatus('서버 오류');return setTimeout(connectChat,20000);}
  if(String(info.RESULT)!=='1'){
    liveOn=false;setStatus('방송 대기 중 — 시작되면 자동으로 붙습니다');
    return setTimeout(connectChat,20000);
  }
  liveOn=true;liveTitle=info.TITLE||'';
  setStatus('<span class="live">● LIVE</span> '+esc(liveTitle)+(IS_TEST_CH?' <span class="warn">['+BJ+' 채널 시험 중 — 기록 저장 안 함]</span>':''));
  try{
    ws=new WebSocket('wss://'+info.CHDOMAIN+':'+(+info.CHPT+1)+'/Websocket/'+BJ,['chat']);
  }catch(e){setStatus('채팅 연결 실패');return setTimeout(connectChat,15000);}
  ws.binaryType='arraybuffer';
  let joined=false;
  ws.onopen=()=>{ws.send(pkt(1,F+F+F+'16'+F));
    pingT=setInterval(()=>{try{ws.send(pkt(0,F))}catch(e){}},50000);};
  ws.onmessage=(m)=>{
    const s=new TextDecoder().decode(m.data);
    if(!s.startsWith('\x1b\t'))return;
    const svc=+s.slice(2,6), f=s.slice(14).split(F);
    if(!joined){joined=true;ws.send(pkt(2,F+String(info.CHATNO)+F+F+F+F));}
    if(svc===5&&f.length>6){
      const nick=cleanNick(f[6]);
      if(nick)onEvent({t:'chat',nick,id:cleanNick(f[2]),msg:f[1],at:now()});
    }else if(svc===109){
      const ev=parseBalloon(f);
      if(ev){ev.at=now();onEvent(ev);}   // null 이면 재전송 — 조용히 건너뜀
    }else if(svc===18){
      const ev=parseBalloon18(f);        // 별풍선이 svc18 로도 옵니다 (낭만헌터 100개 건)
      if(ev){ev.at=now();onEvent(ev);}

    }else if(![0,1,2,4].includes(svc)){
      rawUnknown.push({svc,f:f.slice(0,10),at:now()});
      rawUnknown.splice(0,Math.max(0,rawUnknown.length-200));
    }
  };
  ws.onclose=()=>{clearInterval(pingT);
    setStatus(liveOn?'연결 끊김 — 다시 붙는 중…':'방송 대기 중');
    setTimeout(connectChat,8000);};
  ws.onerror=()=>{try{ws.close()}catch(e){}};
}
function now(){return new Date().toTimeString().slice(0,8)}
function setStatus(html){document.getElementById('liveflag').innerHTML=html}

/* ── 가중치와 추첨 ── */
function weight(nick){
  const u=users[nick]||{c:0,b:0}, s=settings;
  return 1+Math.min(1,u.c/Math.max(1,s.chatFull))*s.chatBonusMax
          +Math.min(1,u.b/Math.max(1,s.balloonFull))*s.balloonBonusMax;
}
function norm(s){return String(s||'').replace(/\s+/g,'').toLowerCase()}
function winCount(nick){
  if(!ST)return[0,''];
  const n=norm(nick),sid=(uid[nick]||'').toLowerCase();
  const h=ST.winners.list.filter(w=>norm(w.nick)===n||(sid&&(w.sid||'').toLowerCase()===sid));
  return[h.length,h.length?h[h.length-1].date:''];
}
function recentWin(nick){
  // 최근 N주 안에 받은 적 있나 (0 이면 제한 없음)
  const wk=settings.excludeWeeks||0; if(!wk||!ST)return false;
  const cut=new Date(Date.now()-wk*7*864e5).toISOString().slice(0,10);
  const n=norm(nick),sid=(uid[nick]||'').toLowerCase();
  return ST.winners.list.some(w=>(norm(w.nick)===n||(sid&&(w.sid||'').toLowerCase()===sid))
    && (w.date||'')>=cut);
}
function inGdoc(nick){
  const sid=(uid[nick]||'').toLowerCase();
  if(sid&&gdoc.ids.includes(sid))return true;
  const n=norm(nick);
  return gdoc.names.some(x=>norm(x)===n)||gdoc.names.some(x=>norm(x).includes(n)&&n.length>=2);
}
function drawPool(){
  let pool=Object.keys(users).filter(n=>users[n].c+users[n].b>0);
  if(settings.excludeWinners)pool=pool.filter(n=>winCount(n)[0]===0);
  if(settings.excludeWeeks)pool=pool.filter(n=>!recentWin(n));
  return pool;
}
function pickFrom(pool){
  if(!pool.length)return null;
  const ws2=pool.map(weight), tot=ws2.reduce((a,b)=>a+b,0);
  let r=Math.random()*tot;
  for(let i=0;i<pool.length;i++){r-=ws2[i];if(r<=0)return pool[i];}
  return pool[pool.length-1];
}
// 핀볼·룰렛 후보 슬롯 — 확률 높은 사람 위주로 채웁니다(당첨자 포함).
function slotsFor(win,pool,k){
  const others=pool.filter(n=>n!==win).sort((a,b)=>weight(b)-weight(a));
  const top=others.slice(0,Math.max(0,k-1));
  const slots=top.concat([win]);
  for(let i=slots.length-1;i>0;i--){const j=(Math.random()*(i+1))|0;[slots[i],slots[j]]=[slots[j],slots[i]];}
  return slots;
}

/* ── 서버 통신 ── */
async function api(act,body){
  const r=await fetch('prize_api.php',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(Object.assign({act},body||{}))});
  const j=await r.json();if(j.error)alert(j.error);return j;
}
function prizeOf(id){return (ST?.prizes.items||[]).find(x=>x.id===id)}
async function manualPick(){
  const nick=document.getElementById('pickNick').value.trim();
  if(!nick)return alert('닉네임을 넣어 주세요');
  const pz=prizeOf(document.getElementById('prizeSel').value)||{};
  await api('pick',{nick,sid:uid[nick]||'',prize:pz.name||'',how:'지명'+(IS_TEST_CH?'(연습)':'')});
  await api('overlay_set',{overlay:{kind:'winner',nick,prize:pz.name||'',
    photo:pz.photo||'',how:'지명'}});
  refresh();
}
async function draw(kind){
  const pool=drawPool();
  const win=pickFrom(pool);
  if(!win)return alert('추첨할 시청자가 없습니다 (조건에 맞는 참가자가 없음)');
  const slots=slotsFor(win,pool,kind==='roulette'?10:9);
  const pz=prizeOf(document.getElementById('prizeSel').value)||{};
  await api('pick',{nick:win,sid:uid[win]||'',prize:pz.name||'',how:(kind==='roulette'?'룰렛':'핀볼')+(IS_TEST_CH?'(연습)':'')});
  await api('overlay_set',{overlay:{kind,winner:win,slots,prize:pz.name||'',photo:pz.photo||''}});
  refresh();
}
const plinko=()=>draw('plinko');
const roulette=()=>draw('roulette');
async function kings(){
  const arr=Object.entries(users);
  if(!arr.length)return alert('아직 참가자가 없습니다');
  const chatKing=arr.slice().sort((a,b)=>b[1].c-a[1].c)[0];
  const balKing=arr.slice().sort((a,b)=>b[1].b-a[1].b)[0];
  await api('overlay_set',{overlay:{kind:'kings',
    chatNick:chatKing[0],chatN:chatKing[1].c,
    balNick:balKing[0],balN:balKing[1].b}});
}
async function clearOverlay(){await api('overlay_set',{overlay:{kind:'none'}})}
let photoData='';
document.getElementById('pPhoto').addEventListener('change',e=>{
  const f=e.target.files[0];if(!f)return;
  const r=new FileReader();
  r.onload=()=>{photoData=r.result;
    document.getElementById('pPhotoName').innerHTML='<img src="'+r.result+'" style="width:38px;height:38px;object-fit:cover;border-radius:6px;vertical-align:middle;margin-right:6px">'+f.name;};
  r.readAsDataURL(f);
});
async function addPrize(){
  const name=document.getElementById('pName').value.trim();
  if(!name)return alert('상품 이름을 넣어 주세요');
  await api('prize_add',{name,photo:photoData});
  photoData='';document.getElementById('pName').value='';
  document.getElementById('pPhotoName').textContent='';refresh();
}
async function addWinner(){
  await api('pick',{date:document.getElementById('wDate').value.trim()||undefined,
    nick:document.getElementById('wNick').value.trim(),
    prize:document.getElementById('wPrize').value.trim(),how:'기록'});
  document.getElementById('wNick').value='';refresh();
}
async function saveSettings(){
  settings=Object.assign(settings,{
    chatFull:+document.getElementById('sChatFull').value||50,
    chatBonusMax:+document.getElementById('sChatMax').value||0.3,
    balloonFull:+document.getElementById('sBalFull').value||1000,
    balloonBonusMax:+document.getElementById('sBalMax').value||0.5,
    excludeWinners:document.getElementById('sExcl').checked,
    excludeWeeks:+document.getElementById('sWeeks').value||0,
    balloonAlert:+document.getElementById('sAlert').value||100,
    gdocId:(document.getElementById('sGdoc').value.trim().match(/[-\w]{25,}/)||[document.getElementById('sGdoc').value.trim()])[0],
    slackWebhook:document.getElementById('sSlack').value.trim(),
    excludeAccounts:document.getElementById('sExclAcc').value.trim(),
    realChannels:document.getElementById('sRealCh').value.trim()});
  await api('settings_set',{settings});loadGdoc();rebuildExcl();applyRealCh();closeSettings();
}
function openSettings(){var b=document.getElementById('bjName');if(b)b.textContent=BJ;
  document.getElementById('settingsModal').style.display='flex';}
function closeSettings(){document.getElementById('settingsModal').style.display='none';}
function applyRealCh(){
  const raw=(settings.realChannels||'').toLowerCase().split(/[\s,]+/).filter(Boolean);
  if(!raw.includes('talent'))raw.push('talent');
  try{localStorage.setItem('pzRealCh',JSON.stringify(raw));}catch(e){}
  IS_TEST_CH = !new Set(raw).has(BJ) || IS_DEMO;
}
function updateMaskBtn(){
  const b=document.getElementById('maskBtn');if(!b)return;
  b.textContent=document.body.classList.contains('maskacc')?'👁 계정 보기':'🙈 계정 가리기';
}
function toggleMask(){
  document.body.classList.toggle('maskacc');
  try{localStorage.setItem('pzMaskAcc',document.body.classList.contains('maskacc')?'1':'');}catch(e){}
  updateMaskBtn();
}
function downloadActivity(){
  const rows=Object.entries(users).map(([nick,u])=>({nick,acc:uid[nick]||'',c:u.c,b:u.b,w:winCount(nick)[0]}));
  if(!rows.length)return alert('활약 데이터가 없습니다');
  rows.sort((a,b)=>b.b-a.b||b.c-a.c);
  const NL=String.fromCharCode(10);
  const q=x=>'"'+String(x==null?'':x).replace(/"/g,'""')+'"';
  const lines=rows.map(r=>[q(r.nick),q(r.acc),r.c,r.b,r.w].join(','));
  const csv=String.fromCharCode(0xFEFF)+['닉네임,SOOP계정,채팅수,별풍선수,당첨횟수'].concat(lines).join(NL);
  const a=document.createElement('a');
  a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);
  a.download='끝장전-활약-'+(sess.date||todayStr())+'.csv';a.click();
}
const PANELS=[['chat','실시간 채팅'],['users','시청자 활약'],['pastdays','지난 방송'],
  ['pick','당첨 만들기'],['prizes','상품'],['winners','당첨자 시트'],['recent','최근 당첨자']];
const panelState={};   // key -> 숨김 여부(true=닫힘)
function panelNodes(key){
  // data-panel 이 카드면 카드 통째로, 섹션이면 헤더~다음 헤더/구분선 앞까지(앞 <hr> 포함)
  const el=document.querySelector('[data-panel="'+key+'"]');
  if(!el)return [];
  if(el.classList.contains('card'))return [el];
  const nodes=[]; const prev=el.previousElementSibling;
  if(prev&&prev.tagName==='HR')nodes.push(prev);
  nodes.push(el);
  let n=el.nextElementSibling;
  while(n&&!(n.classList&&n.classList.contains('ct'))&&n.tagName!=='HR'){nodes.push(n);n=n.nextElementSibling;}
  return nodes;
}
function applyPanel(key){
  const hide=!!panelState[key];
  panelNodes(key).forEach(n=>{n.style.display=hide?'none':'';});
}
function renderPanelBar(){
  const bar=document.getElementById('panelBar');if(!bar)return;
  bar.innerHTML='<span class="n" style="margin-right:2px">창 켜기·끄기:</span>'+PANELS.map(function(pr){
    return '<button class="pill chip'+(panelState[pr[0]]?'':' on')+'" data-pk="'+pr[0]+'">'+
      (panelState[pr[0]]?'＋ ':'✓ ')+esc(pr[1])+'</button>';}).join('');
  bar.querySelectorAll('[data-pk]').forEach(b=>b.onclick=()=>togglePanel(b.dataset.pk));
}
function togglePanel(key){
  panelState[key]=!panelState[key];
  try{localStorage.setItem('pzPanels',JSON.stringify(panelState));}catch(e){}
  applyPanel(key);renderPanelBar();
}
function initPanels(){
  try{Object.assign(panelState,JSON.parse(localStorage.getItem('pzPanels')||'{}'));}catch(e){}
  PANELS.forEach(pr=>applyPanel(pr[0]));
  renderPanelBar();
}
function setDupM(m){dupMonths=m;try{localStorage.setItem('pzDupM',m);}catch(e){}renderRecentWinners();}
const PCATS=[
  {k:'마우스패드',re:/마우스\s*패드|패드|gigantus|mousepad/i,c:'#a78bfa'},
  {k:'마우스',re:/마우스|viper|razer|mouse/i,c:'#4aa3ff'},
  {k:'유니폼',re:/유니폼|uniform|jamie/i,c:'#f87171'},
  {k:'안경',re:/안경|wearwhere|glass/i,c:'#4ade80'},
  {k:'쿠폰·코드',re:/쿠폰|포인트|코드|coupon|point|code/i,c:'#ffb020'}];
function prizeCat(p){for(const x of PCATS)if(x.re.test(p||''))return x;return{k:'기타',c:'#8a93a6'};}
let _rwSig='';
function renderRecentWinners(){
  const host=document.getElementById('recentWinners');if(!host||!ST)return;
  const list=ST.winners.list||[];
  const sig=dupMonths+'|'+list.length+'|'+list.map(w=>w.date+w.prize).join(',');
  if(sig===_rwSig)return; _rwSig=sig;
  const cut=new Date(Date.now()-dupMonths*31*864e5).toISOString().slice(0,10);
  const byp={};
  list.forEach(w=>{
    if(!w.date||w.date<cut)return;
    if(/연습/.test(w.how||''))return;
    const key=(w.sid||'').toLowerCase()||norm(w.nick);
    const pp=byp[key]||(byp[key]={nick:w.nick,sid:w.sid||'',date:w.date,cats:{},prizes:[]});
    if(w.date>=pp.date){pp.date=w.date;pp.nick=w.nick;}
    if(w.sid&&!pp.sid)pp.sid=w.sid;
    const c=prizeCat(w.prize);pp.cats[c.k]=c.c;pp.prizes.push({d:w.date,prize:w.prize,c:c.c});
  });
  const arr=Object.values(byp).sort((a,b)=>b.date<a.date?-1:(b.date>a.date?1:0));
  document.querySelectorAll('[data-dupm],[onclick^=\"setDupM\"]').forEach(()=>{});
  document.querySelectorAll('.chip').forEach(b=>{
    const m=(b.getAttribute('onclick')||'').match(/setDupM\((\d)/);
    if(m)b.classList.toggle('on',+m[1]===dupMonths);});
  const lg=document.getElementById('dupLegend');
  if(lg)lg.innerHTML='상품 색 — '+PCATS.map(x=>'<span style=\"color:'+x.c+';font-weight:700\">●</span>'+x.k).join(' &nbsp;');
  if(!arr.length){host.innerHTML='<div class=\"hint\">최근 '+dupMonths+'개월 당첨자가 없습니다.</div>';return;}
  host.innerHTML='<div class=\"hint\" style=\"margin:0 0 4px\">최근 '+dupMonths+'개월 '+arr.length+'명 — 다시 뽑지 않는 게 좋습니다</div>'+
    arr.map(pp=>{
      const primary=pp.prizes[pp.prizes.length-1].c;
      const badges=Object.entries(pp.cats).map(([k,c])=>'<span title=\"'+esc(k)+'\" style=\"display:inline-block;width:10px;height:10px;border-radius:3px;background:'+c+';margin-right:2px;vertical-align:middle\"></span>').join('');
      const names=[...new Set(pp.prizes.map(x=>x.prize))].join(', ');
      return '<div class=\"rwrow\" title=\"'+esc(names)+'\">'+badges+' <b style=\"color:'+primary+'\">'+esc(pp.nick)+'</b>'+
        (pp.sid?' <span class=\"pill acc\" style=\"font-size:10px\">'+esc(pp.sid)+'</span>':'')+
        ' <span class=\"n\" style=\"font-size:10.5px\">'+esc(pp.date)+'</span></div>';
    }).join('');
}
async function loadGdoc(){
  try{const g=await (await fetch('prize_api.php?act=gdoc')).json();
    gdoc={names:g.names||[],ids:g.ids||[]};
    document.getElementById('gdocInfo').textContent=g.note||'';}catch(e){}
}
function clearChat(){recent.length=0;
  document.getElementById('chat').innerHTML='';}
function clearStats(){
  if(!confirm('집계·계정·채팅 로그를 모두 초기화할까요? 당첨자 시트는 그대로 둡니다.'))return;
  for(const k in users)delete users[k];
  for(const k in uid)delete uid[k];
  recent.length=0;logBuf.length=0;macroCount=0;
  try{localStorage.removeItem(LSKEY);}catch(e){}
  if(!IS_TEST_CH&&sess.date){
    api('stats_save',{date:sess.date,title:liveTitle,users:{},rawUnknown:[],uid:{}});
    api('chat_clear',{date:sess.date});
  }
  sess.date=sess.on?todayStr():'';
  if(!IS_TEST_CH)api('session_set',{session:sess});
  document.getElementById('chat').innerHTML='';paint();}
function downloadLedger(){
  if(!ST||!ST.winners.list.length)return alert('당첨 기록이 없습니다');
  const NL=String.fromCharCode(10);
  const rows=ST.winners.list.map(w=>['"'+(w.date||'')+'"','"'+(w.nick||'').replace(/"/g,'""')+'"',
    '"'+(w.sid||'')+'"','"'+(w.prize||'').replace(/"/g,'""')+'"','"'+(w.how||'')+'"'].join(','));
  const csv=String.fromCharCode(0xFEFF)+['날짜,닉네임,SOOP계정,상품,방식'].concat(rows).join(NL);
  const a=document.createElement('a');
  a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);
  a.download='끝장전-당첨자-'+new Date().toISOString().slice(0,10)+'.csv';
  a.click();}
function copyLedger(){
  if(!ST||!ST.winners.list.length)return alert('당첨 기록이 없습니다');
  const TAB=String.fromCharCode(9),NL=String.fromCharCode(10);
  const txt=ST.winners.list.map(w=>[w.date,w.nick,w.sid||'',w.prize,w.how].join(TAB)).join(NL);
  navigator.clipboard.writeText(['날짜','닉네임','아이디','상품','방식'].join(TAB)+NL+txt)
    .then(()=>alert('당첨 기록 '+ST.winners.list.length+'건을 복사했습니다 (엑셀·문서에 붙여넣기)'));
}
async function slackReport(){
  const tot=Object.values(users).reduce((a,u)=>({c:a.c+u.c,b:a.b+u.b}),{c:0,b:0});
  const todays=(ST?ST.winners.list:[]).filter(w=>w.date===new Date().toISOString().slice(0,10));
  const NL=String.fromCharCode(10);
  const text='🎁 끝장전 상품 추첨 요약'+NL+'시청자 '+Object.keys(users).length+'명 · 채팅 '+tot.c+' · 별풍선 '+tot.b+NL+'오늘 당첨 '+todays.length+'명'+(todays.length?': '+todays.map(w=>w.nick+'('+w.prize+')').join(', '):'');
  const r=await api('slack_report',{text});
  if(r.ok)alert('슬랙으로 보냈습니다');else alert('슬랙 전송 실패 — 웹훅 주소를 확인하세요');
}
function pickThis(n){
  const el=document.getElementById('pickNick');
  el.value=n;dupCheck();
  el.style.background='#12283f';setTimeout(function(){el.style.background='';},450);
  if(window.innerWidth<=760)el.scrollIntoView({block:'center',behavior:'smooth'});
}
function dupCheck(){
  const n=document.getElementById('pickNick').value.trim();
  if(!n){document.getElementById('dupwarn').innerHTML='';return;}
  const [cnt,last]=winCount(n);
  const msgs=[];
  if(cnt)msgs.push('<span class="warn">⚠ 이미 '+cnt+'회 당첨 (마지막 '+esc(last)+')</span>');
  if(settings.excludeWeeks&&recentWin(n))msgs.push('<span class="warn">⚠ 최근 '+settings.excludeWeeks+'주 내 당첨</span>');
  if(inGdoc(n))msgs.push('<span class="warn">⚠ 구글 문서 당첨자 명단에 있음</span>');
  document.getElementById('dupwarn').innerHTML=msgs.length?msgs.join(' '):'<span class="ok">✓ 당첨 기록 없음</span>';
}
document.getElementById('pickNick').addEventListener('input',dupCheck);
document.getElementById('pickNick').addEventListener('keydown',function(e){if(e.key==='Enter')manualPick();});
document.getElementById('chat').addEventListener('click',function(ev){
  const line=ev.target.closest('.chatline[data-nick]');
  if(line&&line.dataset.nick)pickThis(line.dataset.nick);
});

/* ── 화면 그리기 + 서버 상태 ── */
async function refresh(){
  try{ST=await (await fetch('prize_api.php?act=state')).json();}catch(e){return}
  if(ST.settings&&ST.settings.chatFull)settings=Object.assign(settings,ST.settings);
  rebuildExcl();
  const sel=document.getElementById('prizeSel'),cur=sel.value;
  sel.innerHTML='<option value="">상품 없이</option>'+ST.prizes.items.map(x=>
    '<option value="'+x.id+'">'+esc(x.name)+'</option>').join('');
  if([...sel.options].some(o=>o.value===cur))sel.value=cur;
  const givenCount={};
  (ST.winners.list||[]).forEach(w=>{if(w.prize)givenCount[w.prize]=(givenCount[w.prize]||0)+1;});
  document.getElementById('prizes').innerHTML=ST.prizes.items.map((x,i)=>{
    const g=givenCount[x.name]||0;
    return '<div class="row">'+(x.photo?'<img class="thumb" src="'+x.photo+'">':'')+
    '<span style="flex:1">'+esc(x.name)+(g?' <span class="pill" style="color:#4ade80;border-color:#2c6b3f">✓ '+g+'회 지급</span>':'')+'</span>'+
    '<button class="gray" style="padding:3px 7px" data-mv="up" data-id="'+x.id+'"'+(i===0?' disabled':'')+'>▲</button>'+
    '<button class="gray" style="padding:3px 7px" data-mv="down" data-id="'+x.id+'"'+(i===ST.prizes.items.length-1?' disabled':'')+'>▼</button>'+
    '<button class="gray" style="padding:3px 9px" data-show="'+x.id+'">📺 보여주기</button>'+
    '<button class="red" style="padding:3px 9px" data-del="'+x.id+'">지우기</button></div>';})
    .join('')||'<div class="hint">아직 상품이 없습니다.</div>';
  document.querySelectorAll('[data-del]').forEach(b=>b.onclick=async()=>{
    await api('prize_del',{id:b.dataset.del});refresh();});
  document.querySelectorAll('[data-mv]').forEach(b=>b.onclick=async()=>{
    await api('prize_move',{id:b.dataset.id,dir:b.dataset.mv});refresh();});
  document.querySelectorAll('[data-show]').forEach(b=>b.onclick=async()=>{
    const pz=prizeOf(b.dataset.show)||{};
    await api('overlay_set',{overlay:{kind:'prize',prize:pz.name||'',photo:pz.photo||''}});});
  const wl=ST.winners.list;
  document.getElementById('wcount').textContent=wl.length+'건';
  document.querySelector('#winners tbody').innerHTML=wl.slice().reverse().map(w=>{
    const acc=w.sid||'';
    return '<tr><td>'+esc(w.date)+'</td><td><b>'+esc(w.nick)+'</b></td>'+
    '<td>'+(acc?'<span class="pill acc" style="font-size:11px">'+esc(acc)+'</span>'
      :'<span class="warn" style="font-size:11px">없음</span>')+'</td>'+
    '<td>'+esc(w.prize)+'</td><td class="pill">'+esc(w.how||'')+'</td>'+
    '<td style="white-space:nowrap">'+
    (acc?'<button class="gray" style="padding:1px 6px" data-note="'+esc(acc)+'" title="쪽지">✉</button>':'')+
    '<button class="gray" style="padding:1px 6px" data-wedit="'+w.id+'" title="편집">✏</button>'+
    '<button class="red" style="padding:1px 6px" data-wdel="'+w.id+'" title="삭제">×</button></td></tr>';
  }).join('');
  document.querySelectorAll('[data-wdel]').forEach(b=>b.onclick=async()=>{
    if(!confirm('이 당첨 기록을 지울까요?'))return;
    await api('winner_del',{id:b.dataset.wdel});refresh();});
  document.querySelectorAll('[data-note]').forEach(b=>b.onclick=()=>{
    const id=b.dataset.note;
    navigator.clipboard&&navigator.clipboard.writeText(id);
    window.open('https://www.sooplive.com/station/'+encodeURIComponent(id),'_blank','noopener');});
  document.querySelectorAll('[data-wedit]').forEach(b=>b.onclick=async()=>{
    const w=wl.find(x=>x.id===b.dataset.wedit); if(!w)return;
    const nick=prompt('닉네임',w.nick); if(nick===null)return;
    const sid=prompt('SOOP 계정 아이디 (쪽지 보낼 본계정)',w.sid||''); if(sid===null)return;
    const prize=prompt('상품',w.prize||''); if(prize===null)return;
    await api('winner_update',{id:w.id,nick:nick.trim(),sid:sid.trim(),prize:prize.trim()});refresh();});
  for(const [id,v] of [['sChatFull',settings.chatFull],['sChatMax',settings.chatBonusMax],
    ['sBalFull',settings.balloonFull],['sBalMax',settings.balloonBonusMax],
    ['sWeeks',settings.excludeWeeks||0],['sAlert',settings.balloonAlert||100],
    ['sGdoc',settings.gdocId||''],['sSlack',settings.slackWebhook||''],
    ['sExclAcc',settings.excludeAccounts||''],
    ['sRealCh',settings.realChannels||'']]){
    const el=document.getElementById(id);
    if(el&&document.activeElement!==el)el.value=v;
  }
  const ex=document.getElementById('sExcl');if(ex)ex.checked=!!settings.excludeWinners;
  rebuildExcl();applyRealCh();
  try{
    const pl=await (await fetch('prize_api.php?act=stats_list')).json();
    document.getElementById('pastdays').innerHTML='<tbody>'+pl.list.map(r=>
      '<tr><td>'+esc(r.date)+'</td><td class="num">'+r.users+'명</td>'+
      '<td class="num">'+r.chats+'</td><td class="num balloon">'+r.balloons+
      '</td></tr>').join('')+'</tbody>';
  }catch(e){}
}
function paint(){
  document.getElementById('totline').textContent='시청자 '
    +Object.keys(users).length+' · 채팅 '
    +Object.values(users).reduce((a,u)=>a+u.c,0)+' · 별풍선 '
    +Object.values(users).reduce((a,u)=>a+u.b,0)+(macroCount?' · 방송채팅 '+macroCount+' 제외':'');
  const chatEl=document.getElementById('chat');
  // 이미 맨 아래를 보고 있으면 새 글에 맞춰 따라 내려갑니다 (위로 올려 읽는 중이면 안 건드림)
  const atBottom=chatEl.scrollHeight-chatEl.scrollTop-chatEl.clientHeight<40;
  chatEl.innerHTML=recent.slice(-80).map(e=>
    e.t==='balloon'
    ?'<div class="chatline" data-nick="'+esc(e.nick)+'" title="눌러서 당첨 만들기에 넣기">🎈 <b>'+esc(e.nick)+'</b> <span class="balloon">별풍선 '
      +e.count+'개</span> <span class="pill">'+e.at+'</span></div>'
    :'<div class="chatline" data-nick="'+esc(e.nick)+'" title="눌러서 당첨 만들기에 넣기"><span class="pill" style="margin-right:5px">'+e.at
      +'</span><b>'+esc(e.nick)+'</b> '+esc(e.msg)+'</div>').join('');
  if(atBottom)chatEl.scrollTop=chatEl.scrollHeight;
  const rows=Object.entries(users).map(([nick,u])=>({nick,c:u.c,b:u.b,
    w:weight(nick),wins:winCount(nick)[0]}));
  // 당첨 확률(가중치) 높은 순 — 같으면 별풍선·채팅 순
  rows.sort((a,b)=>b.w-a.w||b.b-a.b||b.c-a.c);
  const medal=['🥇','🥈','🥉'];
  const maxAct=Math.max(1,...rows.map(u=>u.b*3+u.c));
  document.querySelector('#users tbody').innerHTML=rows.slice(0,200).map((u,i)=>{
    const pct=Math.round((u.b*3+u.c)/maxAct*100);
    return '<tr><td class="num" style="color:#8a93a6">'+(medal[i]||(i+1))+'</td>'+
    '<td><div class="actbar" style="width:'+pct+'%"></div>'+esc(u.nick)+'</td>'+
    '<td class="pill acc" style="font-size:11px">'+esc(uid[u.nick]||'-')+'</td><td class="num">'+u.c+'</td>'+
    '<td class="num balloon">'+(u.b||'')+'</td><td class="num">x'+u.w.toFixed(2)+
    '</td><td>'+(u.wins?'<span class="warn">'+u.wins+'회</span>':'')+'</td>'+
    '<td><button class="gray" style="padding:2px 8px" data-pick="'
    +esc(u.nick)+'">지명</button></td></tr>';}).join('');
  document.querySelectorAll('[data-pick]').forEach(b=>
    b.onclick=()=>pickThis(b.dataset.pick));
  renderRecentWinners();
}
/* 45초마다 오늘 집계를 서버에 남깁니다 — 지난 방송 기록이 됩니다 */
async function snapshot(){
  if(IS_TEST_CH||!sess.on)return;          // 시험 채널·종료 상태에선 저장 안 함
  if(Object.keys(users).length===0)return;
  await api('stats_save',{date:sess.date,title:liveTitle,users,rawUnknown,uid});
  api('session_set',{session:sess});
}
function todayStr(){return new Date().toISOString().slice(0,10)}
function sessBtns(){
  const s=document.getElementById('btnStart'),e=document.getElementById('btnStop');
  if(s)s.disabled=sess.on;
  if(e)e.disabled=!sess.on;
}
/* 채팅 로그를 서버에 이어 붙입니다 — 초기화 전까지 보존 */
async function flushLog(){
  if(IS_TEST_CH||!logBuf.length)return;
  const lines=logBuf.splice(0);
  const r=await api('chat_log',{date:sess.date,lines});
  if(!r||!r.ok)logBuf.unshift(...lines.slice(-500));
}
setInterval(flushLog,20000);
window.addEventListener('beforeunload',()=>{
  saveLive();   // 이 브라우저에 즉시 저장 (창을 나가도 안 사라지게 — 가장 확실)
  if(IS_TEST_CH||!navigator.sendBeacon)return;
  if(logBuf.length)navigator.sendBeacon('prize_api.php',new Blob([JSON.stringify(
    {act:'chat_log',date:sess.date,lines:logBuf.splice(0,2000)})],{type:'application/json'}));
  if(sess.on&&Object.keys(users).length)navigator.sendBeacon('prize_api.php',new Blob([JSON.stringify(
    {act:'stats_save',date:sess.date,title:liveTitle,users,rawUnknown:[],uid})],{type:'application/json'}));
});
async function startSession(){
  if(sess.on)return;
  sess.on=true;
  if(!sess.date)sess.date=todayStr();       // 이어서 할 땐 기존 날짜 유지
  if(sess.date!==todayStr()&&!confirm('저장돼 있는 '+sess.date+' 집계에 이어서 셉니다. 계속할까요?\n(새로 시작하려면 취소 후 집계 초기화를 먼저 누르세요)')){
    sess.on=false;return;
  }
  sess.startedAt=now().slice(0,5);
  if(!IS_TEST_CH)await api('session_set',{session:sess});
  sessBtns();
  if(IS_DEMO){setStatus('<span class="live">● 연습 모드</span> 가짜 채팅이 흐릅니다');return;}
  connectChat();
}
async function stopSession(){
  if(!sess.on)return;
  if(!confirm('집계를 종료할까요? 지금까지의 채팅·집계·계정은 그대로 저장돼 있습니다.'))return;
  sess.on=false;
  await flushLog();
  if(!IS_TEST_CH){
    if(Object.keys(users).length)
      await api('stats_save',{date:sess.date,title:liveTitle,users,rawUnknown,uid});
    await api('session_set',{session:sess});
  }
  try{if(ws)ws.close();}catch(e){}
  sessBtns();
  setStatus('⏹ 종료 상태 — 데이터는 저장돼 있습니다. ▶ 스타트로 다시 시작');
}
/* 창을 껐다 켜면 지난 상태(집계·계정·채팅창)를 통째로 이어받습니다 */
/* 창을 나가도(뒤로가기·닫기) 채팅창·집계가 사라지지 않게 이 브라우저에 저장합니다.
   집계 초기화 전까지 유지하고, 이틀 지난 것은 버립니다
   (서버의 날짜별 stats/chatlog 파일이 원본 보관 = 파일화). */
function saveLive(){
  if(IS_TEST_CH)return;
  try{localStorage.setItem(LSKEY,JSON.stringify({
    v:1,sess:sess,users:users,uid:uid,macroCount:macroCount,
    recent:recent.slice(-200),savedEpoch:Date.now()}));}catch(e){}
}
function loadLive(){
  if(IS_TEST_CH)return false;
  try{
    const d=JSON.parse(localStorage.getItem(LSKEY)||'null');
    if(!d)return false;
    if(Date.now()-(d.savedEpoch||0)>2*24*60*60*1000){localStorage.removeItem(LSKEY);return false;}
    if(d.sess){sess.on=!!d.sess.on;sess.date=d.sess.date||'';sess.startedAt=d.sess.startedAt||'';}
    const u=d.users||{};for(const k in u)users[k]=u[k];
    const iu=d.uid||{};for(const k in iu)uid[k]=iu[k];
    if(typeof d.macroCount==='number')macroCount=d.macroCount;
    if(Array.isArray(d.recent)&&recent.length===0)recent.push(...d.recent);
    return true;
  }catch(e){return false;}
}
setInterval(saveLive,3000);
addEventListener('pagehide',saveLive);
async function restoreSession(){
  if(IS_TEST_CH)return;
  const hadLocal=loadLive();   // 이 브라우저에 남은 채팅·집계를 즉시 복원
  sessBtns();paint();
  try{
    const st=await (await fetch('prize_api.php?act=state')).json();
    const sv=(st&&st.session)||{};
    if(!hadLocal){sess.on=!!sv.on;sess.date=sv.date||'';sess.startedAt=sv.startedAt||'';}
    else if(!sess.date&&sv.date){sess.date=sv.date;sess.on=!!sv.on;sess.startedAt=sv.startedAt||'';}
  }catch(e){}
  sessBtns();
  if(!sess.date)return;
  try{
    const j=await (await fetch('prize_api.php?act=stats_get&date='+sess.date)).json();
    const u=j.users||{};
    for(const k in u)if(!users[k])users[k]={c:u[k].c||0,b:u[k].b||0};
    const iu=j.uid||{};
    for(const k in iu)if(!uid[k])uid[k]=iu[k];
  }catch(e){}
  try{
    const t=await (await fetch('prize_api.php?act=chat_tail&date='+sess.date)).json();
    const lines=(t&&t.lines)||[];
    if(lines.length&&recent.length===0)recent.push(...lines.slice(-200));
  }catch(e){}
  paint();
}
setInterval(paint,1500);
setInterval(snapshot,45000);
refresh();setInterval(refresh,6000);
loadGdoc();setInterval(loadGdoc,300000);
applyRealCh();
if(localStorage.getItem('pzMaskAcc'))document.body.classList.add('maskacc');
updateMaskBtn();
initPanels();
restoreSession().finally(connectChat);
/* 연습: 주소 뒤에 ?demo 를 붙이면 가짜 채팅이 흐릅니다 */
if(location.search.includes('demo')){
  const NICKS=['별사탕요정','테란만세','저글링1000','프로브혁명','캐리어가요',
    'GG치지마','빌드깎는노인','더블넥좋아','뮤탈짤짤이','벙커링장인'];
  const MSGS=['ㅋㅋㅋㅋ','이걸 막네','오늘 폼 미쳤다','9세트 가자','GG','역전각','지리네요'];
  liveOn=true;liveTitle='(연습)';
  setStatus('<span class="live">● 연습 모드</span> 가짜 채팅 (기록 저장 안 함)');
  sess.on=true;sess.date=todayStr();sessBtns();
  const DIDS=['byeolst4r','terranzzang','zergrun1000','probe1017','carrier4u',
    'ggnooo','buildgm88','doublenex','mutalking','bunkerman'];
  setInterval(()=>{
    if(!sess.on)return;
    const i=Math.floor(Math.random()*NICKS.length), n=NICKS[i];
    if(Math.random()<0.12)onEvent({t:'balloon',nick:n,id:DIDS[i],at:now(),
      count:[1,5,10,50,100,500][Math.floor(Math.random()*6)]});
    else onEvent({t:'chat',nick:n,id:DIDS[i],at:now(),
      msg:MSGS[Math.floor(Math.random()*MSGS.length)]});
  },500);
}
</script></body></html>
