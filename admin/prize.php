<?php require __DIR__ . '/auth.php'; admin_require_login(); ?>
<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>상품 추첨 관제 — 끝장전</title><style>
*{box-sizing:border-box}body{margin:0;background:#0a0d13;color:#e8ecf3;
font-family:'Pretendard','Malgun Gothic',sans-serif;font-size:14px}
.wrap{max-width:1520px;margin:0 auto;padding:14px}
h1{font-size:18px;margin:4px 0 12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.grid{display:grid;gap:12px;grid-template-columns:1.1fr .9fr 1fr}
@media(max-width:1100px){.grid{grid-template-columns:1fr}}
.card{background:#141821;border:1px solid #232a38;border-radius:12px;padding:12px;min-width:0}
.ct{font-weight:800;margin-bottom:8px;display:flex;gap:8px;align-items:center}
.ct .n{color:#8a93a6;font-weight:500;font-size:11.5px}
.scroll{overflow-y:auto;max-height:520px}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{padding:5px 7px;text-align:left;border-bottom:1px solid #171c25;white-space:nowrap}
th{color:#8a93a6;font-size:11px}
.num{text-align:right;font-variant-numeric:tabular-nums}
.chatline{padding:3px 0;border-bottom:1px solid #12161e;font-size:13px;
overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.chatline b{color:#7cb6ff;font-weight:600}.balloon{color:#ffb020;font-weight:700}
button{background:#1c8cff;border:0;color:#fff;border-radius:8px;padding:8px 13px;
font-weight:700;cursor:pointer;font-family:inherit}
button.gray{background:#232a38}button.red{background:#e0392b}
input,select{background:#1b202b;color:#e8ecf3;border:1px solid #232a38;
border-radius:8px;padding:7px 9px;font-family:inherit;font-size:13px}
.row{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin:6px 0}
.warn{color:#ffb020;font-weight:700}.ok{color:#4ade80}
.pill{background:#1b202b;border:1px solid #232a38;border-radius:999px;
padding:2px 9px;font-size:11.5px;color:#8a93a6}
.live{color:#ff4d5a;font-weight:900}
img.thumb{width:44px;height:44px;object-fit:cover;border-radius:8px;
vertical-align:middle;margin-right:6px;background:#0a0d13}
.hint{color:#8a93a6;font-size:11.5px;line-height:1.6;margin-top:6px}
hr{border-color:#232a38}
a.top{color:#8a93a6;font-size:12.5px;text-decoration:none}
a.top:hover{color:#e8ecf3}
</style></head><body><div class="wrap">
<h1>🎁 상품 추첨 관제 <span id="liveflag" class="pill">연결 준비…</span></h1>
<div class="row" style="margin:0 0 10px">
<span class="n">채널</span>
<input id="bjInput" placeholder="talent (우리 방송)" style="width:180px">
<button class="gray" onclick="goCh(document.getElementById('bjInput').value.trim())">붙기</button>
<button class="gray" onclick="goCh('')">우리 채널(talent)</button>
<button class="gray" onclick="goCh('__demo')">연습(가짜 채팅)</button>
<a class="top" href="prize_overlay.php" target="_blank">📺 방송 장면 열기 ↗</a>
<a class="top" href="cg.php">CG 제작 →</a>
<span class="n">이 창을 켜 둔 동안만 채팅이 집계됩니다</span></div>
<script>
function goCh(v){
  if(v==='__demo'){location.href='prize.php?demo';return;}
  location.href = v ? ('prize.php?bj='+encodeURIComponent(v)) : 'prize.php';
}
</script>
<div class="grid">

<div class="card"><div class="ct">실시간 채팅 <span class="n" id="totline"></span></div>
<div class="scroll" id="chat" style="max-height:560px"></div></div>

<div class="card"><div class="ct">시청자 활약 <span class="n">별풍선·채팅 순</span></div>
<div class="scroll"><table id="users"><thead><tr><th class="num">#</th><th>닉네임</th>
<th class="num">채팅</th><th class="num">별풍선</th><th class="num">확률↑</th>
<th>당첨</th><th></th></tr></thead><tbody></tbody></table></div>
<hr><div class="ct">지난 방송 <span class="n">저절로 저장됩니다</span></div>
<div class="scroll" style="max-height:150px"><table id="pastdays"><tbody></tbody></table></div></div>

<div class="card">
<div class="ct">당첨 만들기</div>
<div class="row"><input id="pickNick" placeholder="닉네임 (지명)" style="flex:1">
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
<div class="ct">상품 <span class="n">사진도 넣을 수 있습니다</span></div>
<div id="prizes"></div>
<div class="row"><input id="pName" placeholder="상품 이름" style="flex:1">
<input type="file" id="pPhoto" accept="image/*" style="display:none">
<button class="gray" onclick="document.getElementById('pPhoto').click()">사진</button>
<button onclick="addPrize()">추가</button></div>
<span id="pPhotoName" class="hint"></span>
<hr>
<div class="ct">당첨자 장부 <span class="n" id="wcount"></span></div>
<div class="scroll" style="max-height:200px"><table id="winners"><tbody></tbody></table></div>
<div class="row"><input id="wDate" placeholder="2026-08-13" style="width:104px">
<input id="wNick" placeholder="닉네임" style="flex:1">
<input id="wPrize" placeholder="상품" style="flex:1">
<button class="gray" onclick="addWinner()">지난 기록 넣기</button></div>
<hr>
<div class="ct">확률·규칙 설정</div>
<div class="row hint">채팅 <input id="sChatFull" style="width:52px"> 개에
+<input id="sChatMax" style="width:46px"> · 별풍선
<input id="sBalFull" style="width:60px"> 개에 +<input id="sBalMax" style="width:46px"></div>
<div class="row hint">
<label><input type="checkbox" id="sExcl"> 이전 당첨자 전체 제외</label>
· 최근 <input id="sWeeks" style="width:40px"> 주 당첨자 제외(0=끄기)
· 별풍선 <input id="sAlert" style="width:52px"> 개 이상이면 감사 배너</div>
<div class="row hint">구글 문서 ID <input id="sGdoc" style="flex:1;min-width:180px" placeholder="당첨자 문서 주소의 /d/ 다음 부분">
<span id="gdocInfo" class="pill"></span></div>
<div class="row hint">슬랙 웹훅 <input id="sSlack" style="flex:1;min-width:180px" placeholder="https://hooks.slack.com/...">
<button class="gray" onclick="saveSettings()">설정 저장</button></div>
<div class="row">
<button class="gray" onclick="copyLedger()">📋 당첨 기록 복사</button>
<button class="gray" onclick="slackReport()">📨 슬랙으로 요약</button></div>
</div>

</div></div>
<script>
/* ── 채팅 집계 (이 브라우저 안에서) ─────────────────────────── */
/* 주소 뒤에 ?bj=아이디 를 붙이면 그 채널에 붙습니다 — 우리 방송이 없을 때
   다른 라이브에서 수신을 시험하는 용도입니다. 시험 채널일 때는
   방송별 눈금(stats)을 저장하지 않아 진짜 기록과 섞이지 않습니다. */
const BJ=(new URLSearchParams(location.search).get('bj')||'talent')
  .toLowerCase().replace(/[^a-z0-9_]/g,'')||'talent';
const IS_TEST_CH = BJ!=='talent';
const F='\x0c', users={}, recent=[], rawUnknown=[];
let liveOn=false, liveTitle='', ws=null, pingT=null, ST=null;
let settings={chatFull:50,chatBonusMax:0.3,balloonFull:1000,balloonBonusMax:0.5,
  excludeWinners:false,excludeWeeks:0,balloonAlert:100,gdocId:'',slackWebhook:''};
let gdoc={names:[],ids:[]};   // 구글 문서에서 읽어 온 당첨자

function esc(s){return String(s??'').replace(/[&<>"]/g,
  c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function cleanNick(s){s=(s||'').trim();
  if(s.endsWith(')')&&s.includes('(')) s=s.slice(0,s.lastIndexOf('('));return s.trim()}
function bump(nick,kind,n){
  if(!nick)return;
  const u=users[nick]??(users[nick]={c:0,b:0});
  if(kind==='c')u.c++; else u.b+=n;
}
function onEvent(ev){
  if(ev.t==='chat'){bump(ev.nick,'c');if(ev.id)uid[ev.nick]=ev.id;recent.push(ev);}
  else if(ev.t==='balloon'){
    bump(ev.nick,'b',ev.count);if(ev.id)uid[ev.nick]=ev.id;recent.push(ev);
    // 큰 별풍선이면 방송 장면에 감사 배너를 자동으로 띄웁니다
    if(!IS_TEST_CH && ev.count>=(settings.balloonAlert||100))
      api('toast_add',{nick:ev.nick,count:ev.count});
  }
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
const seenBalloons=new Set();   // 재전송 별풍선 중복 방지 (메시지ID [3])
function parseBalloon(f){
  // 별풍선 svc 109 — 실측(2026-08): [3]메시지ID [4]개수 [6]보낸이ID [7]보낸이닉
  if(f.length<8)return null;
  const cnt=(f[4]||'').trim();
  if(!/^\d+$/.test(cnt)||+cnt<=0)return null;
  const mid=(f[3]||'').trim();
  if(mid&&seenBalloons.has(mid))return null;   // 이미 센 별풍선
  if(mid)seenBalloons.add(mid);
  const nick=cleanNick(f[7]);
  return nick?{t:'balloon',nick,count:+cnt,id:(f[6]||'').trim()}:null;
}
async function connectChat(){
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
      if(nick)onEvent({t:'chat',nick,msg:f[1],at:now()});
    }else if(svc===109){
      const ev=parseBalloon(f);
      if(ev){ev.at=now();onEvent(ev);}
      else rawUnknown.push({svc,f:f.slice(0,12),at:now()});
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
  await api('pick',{nick,sid:uid[nick]||'',prize:pz.name||'',how:'지명'});
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
  await api('pick',{nick:win,sid:uid[win]||'',prize:pz.name||'',how:kind==='roulette'?'룰렛':'핀볼'});
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
    document.getElementById('pPhotoName').textContent='사진: '+f.name;};
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
    slackWebhook:document.getElementById('sSlack').value.trim()});
  await api('settings_set',{settings});loadGdoc();
}
async function loadGdoc(){
  try{const g=await (await fetch('prize_api.php?act=gdoc')).json();
    gdoc={names:g.names||[],ids:g.ids||[]};
    document.getElementById('gdocInfo').textContent=g.note||'';}catch(e){}
}
function copyLedger(){
  if(!ST||!ST.winners.list.length)return alert('당첨 기록이 없습니다');
  const txt=ST.winners.list.map(w=>[w.date,w.nick,w.sid||'',w.prize,w.how].join('	')).join('
');
  navigator.clipboard.writeText('날짜	닉네임	아이디	상품	방식
'+txt)
    .then(()=>alert('당첨 기록 '+ST.winners.list.length+'건을 복사했습니다 (엑셀·문서에 붙여넣기)'));
}
async function slackReport(){
  const tot=Object.values(users).reduce((a,u)=>({c:a.c+u.c,b:a.b+u.b}),{c:0,b:0});
  const todays=(ST?ST.winners.list:[]).filter(w=>w.date===new Date().toISOString().slice(0,10));
  const text='🎁 끝장전 상품 추첨 요약
'+
    '시청자 '+Object.keys(users).length+'명 · 채팅 '+tot.c+' · 별풍선 '+tot.b+'
'+
    '오늘 당첨 '+todays.length+'명'+(todays.length?': '+todays.map(w=>w.nick+'('+w.prize+')').join(', '):'');
  const r=await api('slack_report',{text});
  if(r.ok)alert('슬랙으로 보냈습니다');else alert('슬랙 전송 실패 — 웹훅 주소를 확인하세요');
}
function pickThis(n){document.getElementById('pickNick').value=n;dupCheck()}
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

/* ── 화면 그리기 + 서버 상태 ── */
async function refresh(){
  try{ST=await (await fetch('prize_api.php?act=state')).json();}catch(e){return}
  if(ST.settings&&ST.settings.chatFull)settings=Object.assign(settings,ST.settings);
  const sel=document.getElementById('prizeSel'),cur=sel.value;
  sel.innerHTML='<option value="">상품 없이</option>'+ST.prizes.items.map(x=>
    '<option value="'+x.id+'">'+esc(x.name)+'</option>').join('');
  if([...sel.options].some(o=>o.value===cur))sel.value=cur;
  document.getElementById('prizes').innerHTML=ST.prizes.items.map(x=>
    '<div class="row">'+(x.photo?'<img class="thumb" src="'+x.photo+'">':'')+
    '<span style="flex:1">'+esc(x.name)+'</span>'+
    '<button class="gray" style="padding:3px 9px" data-show="'+x.id+'">📺 보여주기</button>'+
    '<button class="red" style="padding:3px 9px" data-del="'+x.id+'">지우기</button></div>')
    .join('')||'<div class="hint">아직 상품이 없습니다.</div>';
  document.querySelectorAll('[data-del]').forEach(b=>b.onclick=async()=>{
    await api('prize_del',{id:b.dataset.del});refresh();});
  document.querySelectorAll('[data-show]').forEach(b=>b.onclick=async()=>{
    const pz=prizeOf(b.dataset.show)||{};
    await api('overlay_set',{overlay:{kind:'prize',prize:pz.name||'',photo:pz.photo||''}});});
  const wl=ST.winners.list;
  document.getElementById('wcount').textContent=wl.length+'건';
  document.getElementById('winners').innerHTML='<tbody>'+wl.slice().reverse().map(w=>
    '<tr><td>'+esc(w.date)+'</td><td><b>'+esc(w.nick)+'</b></td><td>'+esc(w.prize)+
    '</td><td class="pill">'+esc(w.how||'')+'</td><td><button class="red" '+
    'style="padding:1px 7px" data-wdel="'+w.id+'">×</button></td></tr>').join('')+'</tbody>';
  document.querySelectorAll('[data-wdel]').forEach(b=>b.onclick=async()=>{
    await api('winner_del',{id:b.dataset.wdel});refresh();});
  for(const [id,v] of [['sChatFull',settings.chatFull],['sChatMax',settings.chatBonusMax],
    ['sBalFull',settings.balloonFull],['sBalMax',settings.balloonBonusMax],
    ['sWeeks',settings.excludeWeeks||0],['sAlert',settings.balloonAlert||100],
    ['sGdoc',settings.gdocId||''],['sSlack',settings.slackWebhook||'']]){
    const el=document.getElementById(id);
    if(el&&document.activeElement!==el)el.value=v;
  }
  document.getElementById('sExcl').checked=!!settings.excludeWinners;
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
    +Object.values(users).reduce((a,u)=>a+u.b,0);
  const chatEl=document.getElementById('chat');
  // 이미 맨 아래를 보고 있으면 새 글에 맞춰 따라 내려갑니다 (위로 올려 읽는 중이면 안 건드림)
  const atBottom=chatEl.scrollHeight-chatEl.scrollTop-chatEl.clientHeight<40;
  chatEl.innerHTML=recent.slice(-80).map(e=>
    e.t==='balloon'
    ?'<div class="chatline">🎈 <b>'+esc(e.nick)+'</b> <span class="balloon">별풍선 '
      +e.count+'개</span> <span class="pill">'+e.at+'</span></div>'
    :'<div class="chatline"><span class="pill" style="margin-right:5px">'+e.at
      +'</span><b>'+esc(e.nick)+'</b> '+esc(e.msg)+'</div>').join('');
  if(atBottom)chatEl.scrollTop=chatEl.scrollHeight;
  const rows=Object.entries(users).map(([nick,u])=>({nick,c:u.c,b:u.b,
    w:weight(nick),wins:winCount(nick)[0]}));
  // 당첨 확률(가중치) 높은 순 — 같으면 별풍선·채팅 순
  rows.sort((a,b)=>b.w-a.w||b.b-a.b||b.c-a.c);
  document.querySelector('#users tbody').innerHTML=rows.slice(0,200).map((u,i)=>
    '<tr><td class="num" style="color:#8a93a6">'+(i+1)+'</td>'+
    '<td>'+esc(u.nick)+'</td><td class="num">'+u.c+'</td>'+
    '<td class="num balloon">'+(u.b||'')+'</td><td class="num">x'+u.w.toFixed(2)+
    '</td><td>'+(u.wins?'<span class="warn">'+u.wins+'회</span>':'')+'</td>'+
    '<td><button class="gray" style="padding:2px 8px" data-pick="'
    +esc(u.nick)+'">지명</button></td></tr>').join('');
  document.querySelectorAll('[data-pick]').forEach(b=>
    b.onclick=()=>pickThis(b.dataset.pick));
}
/* 45초마다 오늘 집계를 서버에 남깁니다 — 지난 방송 기록이 됩니다 */
async function snapshot(){
  if(IS_TEST_CH)return;                    // 남의 채널 시험은 기록하지 않습니다
  if(Object.keys(users).length===0)return;
  await api('stats_save',{date:new Date().toISOString().slice(0,10),
    title:liveTitle,users,rawUnknown});
}
setInterval(paint,1500);
setInterval(snapshot,45000);
refresh();setInterval(refresh,6000);
loadGdoc();setInterval(loadGdoc,300000);
connectChat();
/* 연습: 주소 뒤에 ?demo 를 붙이면 가짜 채팅이 흐릅니다 */
if(location.search.includes('demo')){
  const NICKS=['별사탕요정','테란만세','저글링1000','프로브혁명','캐리어가요',
    'GG치지마','빌드깎는노인','더블넥좋아','뮤탈짤짤이','벙커링장인'];
  const MSGS=['ㅋㅋㅋㅋ','이걸 막네','오늘 폼 미쳤다','9세트 가자','GG','역전각','지리네요'];
  liveOn=true;liveTitle='(연습)';
  setStatus('<span class="live">● 연습 모드</span> 가짜 채팅 (기록 저장 안 함)');
  window.IS_TEST_CH=true;
  setInterval(()=>{
    const n=NICKS[Math.floor(Math.random()*NICKS.length)];
    if(Math.random()<0.12)onEvent({t:'balloon',nick:n,at:now(),
      count:[1,5,10,50,100,500][Math.floor(Math.random()*6)]});
    else onEvent({t:'chat',nick:n,at:now(),
      msg:MSGS[Math.floor(Math.random()*MSGS.length)]});
  },500);
}
</script></body></html>
