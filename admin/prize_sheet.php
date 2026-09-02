<?php require __DIR__ . '/auth.php'; admin_require_login(); ?>
<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>당첨자 시트 — 끝장전</title><style>
*{box-sizing:border-box}body{margin:0;background:#0a0d13;color:#e8ecf3;
font-family:'Pretendard','Malgun Gothic',sans-serif;font-size:14px}
.wrap{margin:0 auto;padding:14px 18px 320px}
h1{font-size:18px;margin:4px 0 10px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
a.top{color:#8a93a6;font-size:12.5px;text-decoration:none}a.top:hover{color:#e8ecf3}
.card{background:#141821;border:1px solid #232a38;border-radius:12px;padding:12px}
button{background:#1c8cff;border:0;color:#fff;border-radius:8px;padding:8px 13px;
font-weight:700;cursor:pointer;font-family:inherit}
button.gray{background:#232a38}button.red{background:#e0392b}button.green{background:#1f9d55}
input,select,textarea{background:#1b202b;color:#e8ecf3;border:1px solid #232a38;
border-radius:8px;padding:7px 9px;font-family:inherit;font-size:13px}
.row{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin:6px 0}
.pill{background:#1b202b;border:1px solid #232a38;border-radius:999px;
padding:2px 9px;font-size:11.5px;color:#8a93a6}
.chip{cursor:pointer;user-select:none}.chip.on{border-color:#1c8cff;color:#cfe6ff}
.warn{color:#ffb020;font-weight:700}.ok{color:#4ade80;font-weight:700}
.hint{color:#8a93a6;font-size:11.5px;line-height:1.6;margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{padding:6px 8px;text-align:left;border-bottom:1px solid #171c25;white-space:nowrap}
th{color:#8a93a6;font-size:11px;position:sticky;top:0;background:#141821;z-index:2}
.scroll{overflow:auto;max-height:calc(100vh - 390px);min-height:260px}
td[contenteditable]{cursor:text;min-width:56px}
td[contenteditable]:hover{background:#181d28}
td[contenteditable]:focus{outline:2px solid #1c8cff;background:#181d28;border-radius:4px}
td.saved{outline:2px solid #1f9d55;border-radius:4px}
td.c-nick{font-weight:700}td.c-sid{color:#7cb6ff;font-size:12px}
.dupbanner{background:#3a1520;border:1px solid #ff4d5a;border-radius:10px;padding:9px 13px;margin:0 0 10px;font-size:13px;line-height:2}
.dupbanner.ok{background:#12251a;border-color:#2c6b3f;color:#9fe0b4}
body.maskacc td.c-sid,body.maskacc #selIds{filter:blur(6px);user-select:none}
td.c-how{color:#8a93a6;font-size:12px}
#notebar{position:fixed;left:0;right:0;bottom:0;background:#10141c;
border-top:1px solid #232a38;box-shadow:0 -8px 30px rgba(0,0,0,.45);padding:10px 16px;z-index:5}
#notebar .inner{margin:0 auto;padding:0 2px}
#noteTxt{width:100%;min-height:110px;resize:vertical;line-height:1.55}
#selIds{color:#7cb6ff;font-size:12px;flex:1;min-width:140px;overflow:hidden;
text-overflow:ellipsis;white-space:nowrap}
</style></head><body><div class="wrap">
<h1>&#128210; 당첨자 시트
 <span class="pill" id="sumline">불러오는 중…</span>
 <a class="top" href="prize.php">&#127873; 추첨 관제 →</a>
 <a class="top" href="cg.php">CG 제작 →</a>
</h1>
<div class="row" id="chips"></div>
<div id="dupBanner" class="dupbanner" style="display:none"></div>
<div class="card">
 <div class="row">
  <input id="fQ" placeholder="닉네임·계정 검색" style="width:190px">
  <select id="fDate"><option value="">날짜 전체</option></select>
  <select id="fPrize"><option value="">상품 전체</option></select>
  <select id="fSent"><option value="">쪽지 전체</option>
   <option value="no">안 보낸 사람</option><option value="yes">보낸 사람</option></select>
  <span style="flex:1"></span>
  <button class="gray" onclick="addRow()">＋ 행 추가</button>
  <button class="green" onclick="openGoogleSheet()">📗 구글 시트로 열기</button>
  <button class="gray" onclick="toggleMask()" id="maskBtn">🙈 계정 가리기</button>
  <button class="gray" onclick="copyLedger()">&#128203; 복사</button>
  <button class="gray" onclick="downloadLedger()">⬇ CSV</button>
 </div>
 <div class="scroll"><table id="sheet"><thead><tr>
  <th><input type="checkbox" id="selAll" title="보이는 줄 전체 선택"></th>
  <th>날짜</th><th>방식</th><th>닉네임</th><th>SOOP계정</th><th>상품</th><th>쪽지</th><th>메모</th><th></th>
 </tr></thead><tbody></tbody></table></div>
 <div class="hint">칸을 누르면 바로 고칠 수 있습니다 — 다른 곳을 누르면 저장됩니다(잠깐 초록 테두리 = 저장 완료).
 SOOP계정은 쪽지를 보낼 본계정 아이디입니다. 채팅·별풍선을 친 시청자는 추첨 때 자동으로 채워지고,
 비어 있으면 여기서 직접 넣어 주세요. 복사·CSV 는 지금 걸러져 보이는 줄만 내보냅니다.</div>
</div>
</div>
<div id="notebar"><div class="inner">
 <div class="row" style="margin:0 0 6px">
  <b>✉ 숲 쪽지 보내기</b>
  <span class="pill">선택 <b id="selN">0</b>명</span>
  <span id="selIds"></span>
  <span class="ok" id="flash"></span>
  <span style="flex:1"></span>
  <select id="tplSel">
   <option value="auto">문안 자동 (선택한 상품에 맞춰)</option>
   <option value="tax">제세공과금 — 마우스·패드 (동의서 폼)</option>
   <option value="free">비과세 — 유니폼·안경 (동의서 폼)</option>
   <option value="code">구글플레이 코드 전달</option>
   <option value="blank">직접 쓰기</option>
  </select>
 </div>
 <textarea id="noteTxt" spellcheck="false"></textarea>
 <div class="row" style="margin:6px 0 0">
  <button class="green" onclick="serverSend()">🚀 서버로 바로 보내기</button>
  <span class="pill" id="sessStat" title="talent 로그인 세션 상태">세션 확인 중…</span>
  <button class="gray" onclick="registerSession()">🔑 세션 등록</button>
  <button class="gray" onclick="testNote()">✉ 테스트</button>
  <span style="flex:1"></span>
  <span class="hint" style="margin:0">막혔을 때 수동 →</span>
  <button class="gray" onclick="copyIds()">받는사람 복사</button>
  <button class="gray" onclick="copyNote()">내용 복사</button>
  <button class="gray" onclick="window.open('https://note.sooplive.com/app/index.php','_blank','noopener')">쪽지함 ↗</button>
  <button class="gray" onclick="markSent()">✅ 보냄 처리</button>
 </div>
 <div class="row" style="margin:2px 0 0"><span class="warn" id="noteWarn"></span></div>
 <div class="hint"><b>🚀 서버로 바로 보내기</b> — talent 계정으로 이 서버가 직접 보냅니다.
 성공하면 쪽지 칸에 오늘 날짜가, 실패하면 메모에 사유가 남습니다. 처음 한 번
 <b>🔑 세션 등록</b>이 필요하고(만료되면 다시), 계정이 있는 사람만 대상입니다.
 오른쪽 수동 경로는 세션이 막혔을 때의 대비책입니다.</div>
</div></div>
<script>
const NL=String.fromCharCode(10),TAB=String.fromCharCode(9);
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function today(){const d=new Date(),p=n=>(n<10?'0':'')+n;
  return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate());}
let ST=null,tplTouched=false;const SEL=new Set();
const F={q:'',date:'',prize:'',sent:''};
async function api(act,body){
  try{const r=await fetch('prize_api.php',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(Object.assign({act:act},body||{}))});
    return await r.json();}
  catch(e){return{error:String(e)};}}
async function refresh(){
  try{ST=await (await fetch('prize_api.php?act=state')).json();}
  catch(e){ST={winners:{list:[]},prizes:{items:[]}};}
  if(!ST.winners)ST.winners={list:[]};
  for(const id of Array.from(SEL))if(!ST.winners.list.some(w=>w.id===id))SEL.delete(id);
  paint();}
function rows(){
  const l=ST?ST.winners.list.slice():[];
  l.sort((a,b)=>{const da=a.date||'0000',db=b.date||'0000';
    if(da!==db)return db<da?-1:1;
    const pa=a.prize||'',pb=b.prize||'';
    if(pa!==pb)return pa<pb?-1:1;
    return (a.nick||'')<(b.nick||'')?-1:1;});
  return l;}
function visible(){
  const q=F.q.toLowerCase();
  return rows().filter(w=>{
    if(q&&!((w.nick||'').toLowerCase().includes(q)||(w.sid||'').toLowerCase().includes(q)))return false;
    if(F.date&&(w.date||'(없음)')!==F.date)return false;
    if(F.prize&&(w.prize||'(비어 있음)')!==F.prize)return false;
    if(F.sent==='no'&&(w.sent||''))return false;
    if(F.sent==='yes'&&!(w.sent||''))return false;
    return true;});}
function ed(w,f,cls){
  return '<td contenteditable spellcheck="false" data-f="'+f+'" class="c-'+f+
    (cls?' '+cls:'')+'">'+esc(w[f]||'')+'</td>';}
function fillSel(id,arr,cur){
  const el=document.getElementById(id),first=el.options[0].outerHTML;
  el.innerHTML=first+arr.map(v=>'<option'+(v===cur?' selected':'')+'>'+esc(v)+'</option>').join('');
  el.value=cur||'';}
function dupNorm(x){return String(x||'').replace(/\s+/g,'').toLowerCase();}
function findDups(){
  if(!ST)return [];
  const map={};
  (ST.winners.list||[]).forEach(w=>{
    if(/연습/.test(w.how||'')||!w.prize)return;
    const person=(w.sid||'').toLowerCase()||dupNorm(w.nick);
    const key=person+'|'+dupNorm(w.prize);
    const m=map[key]||(map[key]={nick:w.nick,sid:w.sid||'',prize:w.prize,n:0});
    m.n++; m.nick=w.nick; if(w.sid)m.sid=w.sid;
  });
  return Object.values(map).filter(x=>x.n>=2).sort((a,b)=>b.n-a.n);
}
let dupDismissed='';
function dupSig(dups){return dups.map(d=>d.nick+'|'+d.prize+'|'+d.n).join(',');}
function dismissDup(){dupDismissed=dupSig(findDups())||'_none_';const el=document.getElementById('dupBanner');if(el)el.style.display='none';}
function renderDupBanner(){
  const el=document.getElementById('dupBanner'); if(!el)return;
  const dups=findDups();
  const sig=dupSig(dups)||'_none_';
  if(sig===dupDismissed){el.style.display='none';return;}
  const X='<button class="px" style="float:right;margin:-2px -4px 0 0;color:#ff8fa3" onclick="dismissDup()" title="배너 닫기">✕</button>';
  if(!dups.length){el.className='dupbanner ok';el.style.display='';el.innerHTML=X+'✓ 같은 상품 중복 당첨 없음';return;}
  el.className='dupbanner';el.style.display='';
  el.innerHTML=X+'🚨 <b>같은 상품 중복 당첨 '+dups.length+'건</b> — 확인 필요<br>'+
    dups.slice(0,40).map(d=>'<span class="pill" style="border-color:#ff4d5a;color:#ff8fa3;margin:2px 0;display:inline-block">'+
      esc(d.nick)+(d.sid?' <span style="color:#8a93a6">('+esc(d.sid)+')</span>':'')+' × '+esc(d.prize)+' <b>'+d.n+'회</b></span>').join(' ');
}
function paint(){
  const l=rows(),vis=visible();
  renderDupBanner();
  document.getElementById('sumline').textContent='전체 '+l.length+'건 · 보이는 중 '+vis.length+'건';
  const cnt={};l.forEach(w=>{const k=w.prize||'(비어 있음)';cnt[k]=(cnt[k]||0)+1;});
  document.getElementById('chips').innerHTML=Object.keys(cnt).sort().map(k=>
    '<span class="pill chip'+(F.prize===k?' on':'')+'" data-chip="'+esc(k)+'">'+
    esc(k)+' <b>'+cnt[k]+'</b></span>').join('');
  document.querySelectorAll('[data-chip]').forEach(c=>c.onclick=()=>{
    F.prize=F.prize===c.dataset.chip?'':c.dataset.chip;paint();});
  fillSel('fDate',Array.from(new Set(l.map(w=>w.date||'(없음)'))).sort().reverse(),F.date);
  fillSel('fPrize',Object.keys(cnt).sort(),F.prize);
  document.querySelector('#sheet tbody').innerHTML=vis.map(w=>{
    const bad=(w.memo||'').includes('수신거부');
    return '<tr data-id="'+esc(w.id)+'">'+
      '<td><input type="checkbox" data-sel'+(SEL.has(w.id)?' checked':'')+'></td>'+
      ed(w,'date')+ed(w,'how')+ed(w,'nick')+ed(w,'sid')+ed(w,'prize')+
      ed(w,'sent',w.sent?'ok':'')+ed(w,'memo',bad?'warn':'')+
      '<td><button class="red" style="padding:1px 7px" data-del title="삭제">×</button></td></tr>';
  }).join('');
  document.getElementById('selAll').checked=vis.length>0&&vis.every(w=>SEL.has(w.id));
  notePanel();}
const TB=document.querySelector('#sheet tbody');
TB.addEventListener('change',e=>{
  if(!e.target.matches('[data-sel]'))return;
  const id=e.target.closest('tr').dataset.id;
  if(e.target.checked)SEL.add(id);else SEL.delete(id);
  const vis=visible();
  document.getElementById('selAll').checked=vis.length>0&&vis.every(w=>SEL.has(w.id));
  notePanel();});
TB.addEventListener('click',async e=>{
  if(!e.target.matches('[data-del]'))return;
  const tr=e.target.closest('tr'),w=ST.winners.list.find(x=>x.id===tr.dataset.id);
  if(!confirm(((w&&w.nick)||'이')+' 줄을 지울까요?'))return;
  await api('winner_del',{id:tr.dataset.id});SEL.delete(tr.dataset.id);refresh();});
TB.addEventListener('focusin',e=>{
  const td=e.target.closest('td[contenteditable]');
  if(td)td.dataset.orig=td.textContent;});
TB.addEventListener('keydown',e=>{
  if(e.key==='Enter'&&e.target.closest('td[contenteditable]')){
    e.preventDefault();e.target.blur();}});
TB.addEventListener('focusout',async e=>{
  const td=e.target.closest('td[contenteditable]');if(!td)return;
  const val=td.textContent.trim();
  if(val===(td.dataset.orig||'').trim())return;
  const id=td.closest('tr').dataset.id,f=td.dataset.f,body={id:id};
  body[f]=val;
  const r=await api('winner_update',body);
  if(r&&r.ok){
    td.classList.add('saved');setTimeout(()=>td.classList.remove('saved'),900);
    const w=ST.winners.list.find(x=>x.id===id);if(w)w[f]=val;
    if(f==='date'||f==='prize'||f==='sent')paint();}
  else alert('저장에 실패했습니다: '+((r&&r.error)||'서버 응답 없음'));});
document.getElementById('selAll').onchange=e=>{
  visible().forEach(w=>{if(e.target.checked)SEL.add(w.id);else SEL.delete(w.id);});
  paint();};
document.getElementById('fQ').oninput=e=>{F.q=e.target.value.trim();paint();};
document.getElementById('fDate').onchange=e=>{F.date=e.target.value;paint();};
document.getElementById('fPrize').onchange=e=>{F.prize=e.target.value;paint();};
document.getElementById('fSent').onchange=e=>{F.sent=e.target.value;paint();};
const TPL={
 tax:['안녕하세요.','','구글 플레이 x 스타 끝장전 시청자 이벤트 안내 드립니다.','',
  '아래 링크의 폼을 작성해주세요.','','스타 끝장전 시청자 이벤트 개인정보 수집·이용에 관한 동의서',
  '링크 : https://forms.gle/AhPLwkWZwuNhkHn6A','','위에 첨부된 구글폼 링크에 접속, 작성해주시면 됩니다.','',
  '기타 문의 사항은 숲 중계진 계정으로 쪽지 혹은 help@etalent.co.kr 로 보내주시면 됩니다','',
  '앞으로도 저희 스타 끝장전에 많은 시청과 사랑, 관심 부탁드립니다.','감사합니다!'].join(NL),
 free:['안녕하세요.','','구글 플레이 x 스타 끝장전 시청자 이벤트 안내 드립니다.','',
  '아래 링크의 폼을 작성해주세요.','','스타 끝장전 시청자 이벤트 개인정보 수집·이용에 관한 동의서',
  '링크 : https://forms.gle/VLEkozjSJRVZije26','','위에 첨부된 구글폼 링크에 접속, 작성해주시면 됩니다.','',
  '기타 문의 사항은 숲 중계진 계정으로 쪽지 혹은 help@etalent.co.kr 로 보내주시면 됩니다','',
  '앞으로도 저희 스타 끝장전에 많은 시청과 사랑, 관심 부탁드립니다.','감사합니다!'].join(NL),
 code:['안녕하세요. 님! 주식회사 중계진입니다.','',
  '금일 중계진 분들께서 전달 주신 구글 플레이 5000 포인트 코드 전달 드립니다','','코드 번호 : ','',
  '코드는 Google play 앱 -> 결제 및 정기 결제 -> 기프트 코드 사용 메뉴에서 등록할 수 있습니다.','',
  '2026년 12월 31일 23:59에 만료되니 참고 부탁드립니다.','',
  '항상 저희 끝장전 및 주식회사 중계진 콘텐츠에 관심과 성원 보내주셔서 감사합니다!'].join(NL),
 blank:''};
function selWinners(){return ST?ST.winners.list.filter(w=>SEL.has(w.id)):[];}
function idsOf(ws){const s=new Set();
  ws.forEach(w=>{const v=(w.sid||'').trim();if(v)s.add(v);});
  return Array.from(s);}
function pickTpl(){
  const sel=document.getElementById('tplSel').value;
  if(sel!=='auto')return TPL[sel]||'';
  const ws=selWinners();
  if(ws.length&&ws.every(w=>/안경|유니폼/.test(w.prize||'')))return TPL.free;
  if(ws.length&&ws.every(w=>/코드|쿠폰/.test(w.prize||'')))return TPL.code;
  return TPL.tax;}
function notePanel(){
  const ws=selWinners(),ids=idsOf(ws);
  document.getElementById('selN').textContent=ws.length;
  document.getElementById('selIds').textContent=ids.join(', ');
  if(!tplTouched)document.getElementById('noteTxt').value=pickTpl();
  const warn=[];
  const noSid=ws.filter(w=>!(w.sid||'').trim()).length;
  if(noSid)warn.push('계정이 빈 사람 '+noSid+'명은 받는사람에서 빠집니다');
  if(ws.some(w=>(w.memo||'').includes('수신거부')))warn.push('쪽지 수신거부 표시가 있는 사람이 있습니다');
  document.getElementById('noteWarn').textContent=warn.join(' · ');}
document.getElementById('tplSel').onchange=()=>{tplTouched=false;notePanel();};
document.getElementById('noteTxt').oninput=()=>{tplTouched=true;};
function flash(m){const el=document.getElementById('flash');
  el.textContent=m;setTimeout(()=>{if(el.textContent===m)el.textContent='';},2500);}
function copyToClip(t,msg){
  const done=()=>flash(msg);
  if(navigator.clipboard&&navigator.clipboard.writeText)
    navigator.clipboard.writeText(t).then(done,()=>fallbackCopy(t,done));
  else fallbackCopy(t,done);}
function fallbackCopy(t,done){
  const ta=document.createElement('textarea');ta.value=t;
  document.body.appendChild(ta);ta.select();
  try{document.execCommand('copy');}catch(e){}
  ta.remove();done();}
function copyIds(){
  const ws=selWinners();
  if(!ws.length)return alert('먼저 줄 앞의 체크박스로 보낼 사람을 선택하세요');
  const ids=idsOf(ws);
  if(!ids.length)return alert('선택한 사람들에게 SOOP 계정이 없습니다 — 시트에서 계정을 채워 주세요');
  copyToClip(ids.join(','),'받는사람 '+ids.length+'명 복사됨 ✓');}
function copyNote(){copyToClip(document.getElementById('noteTxt').value,'쪽지 내용 복사됨 ✓');}
async function markSent(){
  const ws=selWinners();
  if(!ws.length)return alert('먼저 보낸 사람들을 선택하세요');
  if(!confirm(ws.length+'명을 오늘('+today()+') 쪽지 보냄으로 표시할까요?'))return;
  for(const w of ws)await api('winner_update',{id:w.id,sent:today()});
  flash(ws.length+'명 보냄 처리됨 ✓');refresh();}
async function testNote(){
  const st=await api('note_session_status');
  if(!st||!st.has){if(confirm('세션이 등록돼 있지 않습니다. 지금 등록할까요?'))registerSession();return;}
  const to=prompt('테스트 쪽지를 받을 SOOP 계정 아이디를 넣으세요.'+NL+'(보통 talent — 자기 자신에게 보내 확인)','talent');
  if(to===null||!to.trim())return;
  document.getElementById('flash').textContent='테스트 쪽지 보내는 중…';
  const r=await api('note_send',{to:to.trim(),
    content:'[테스트] 끝장전 쪽지 발송 점검입니다. 이 쪽지가 보이면 정상입니다 — 무시하셔도 됩니다.'});
  if(r&&r.ok)flash('✅ 테스트 쪽지 보냄 → '+to.trim()+' (SOOP 보낸 쪽지함에서 확인)');
  else alert('테스트 실패: '+((r&&r.reason)||'?')
    +(r&&r.expired?(NL+NL+'세션이 만료됐습니다 — 다시 등록하세요.'):'')
    +(r&&r.snippet?(NL+NL+'서버 응답: '+r.snippet):''));
}
async function noteSessionStatus(){
  try{
    const st=await api('note_session_status');
    const el=document.getElementById('sessStat');
    if(!el)return;
    if(st&&st.has){el.className='pill ok';
      el.innerHTML='🔑 세션 등록됨 <span style="color:#8a93a6">'+esc(st.savedAt||'')+'</span>';}
    else{el.className='pill warn';el.textContent='🔑 세션 미등록';}
  }catch(e){}
}
async function registerSession(){
  const c=prompt('talent 계정의 쪽지 세션 쿠키를 붙여넣으세요.\n\n'
    +'로그인된 Chrome 에서 note.sooplive.com 을 연 뒤\n'
    +'F12(개발자도구) → Application → Cookies → note.sooplive.com 의\n'
    +'쿠키들을  이름=값; 이름=값  형태로 붙여넣습니다.');
  if(c===null||!c.trim())return;
  const el=document.getElementById('sessStat');if(el)el.textContent='세션 확인 중…';
  const r=await api('note_session_set',{cookie:c.trim()});
  if(r&&r.valid){flash('세션 등록됨 — 유효합니다 ✓');}
  else{alert('등록은 했지만 로그인 세션으로 확인되지 않았습니다.\n'
    +'사유: '+((r&&r.reason)||'?')+'\n쿠키를 다시 복사해 주세요.');}
  noteSessionStatus();
}
async function serverSend(){
  const ws=selWinners().filter(w=>(w.sid||'').trim());
  const skipped=selWinners().length-ws.length;
  if(!ws.length)return alert('SOOP 계정이 있는 당첨자를 선택하세요'
    +(skipped?' ('+skipped+'명은 계정이 없어 제외됩니다)':''));
  const bodyTxt=document.getElementById('noteTxt').value.trim();
  if(!bodyTxt)return alert('보낼 내용이 비었습니다');
  const st=await api('note_session_status');
  if(!st||!st.has){if(confirm('talent 세션이 등록돼 있지 않습니다. 지금 등록할까요?'))registerSession();return;}
  if(!confirm(ws.length+'명에게 talent 계정으로 지금 쪽지를 보냅니다.'
    +(skipped?'\n(계정 없는 '+skipped+'명은 제외)':'')+'\n진행할까요?'))return;
  let ok=0,fail=0;
  const fl=document.getElementById('flash');
  for(let i=0;i<ws.length;i++){
    const w=ws[i];
    fl.textContent='보내는 중… '+(i+1)+'/'+ws.length+' — '+w.nick;
    const r=await api('note_send',{to:w.sid,content:bodyTxt});
    if(r&&r.ok){ok++;await api('winner_update',{id:w.id,sent:today()});}
    else{
      fail++;
      if(r&&r.expired){alert('talent 세션이 만료됐습니다. 다시 등록해 주세요.');noteSessionStatus();break;}
      const memo=((w.memo?w.memo+' · ':'')+'발송실패:'+((r&&r.reason)||'?')).slice(0,190);
      await api('winner_update',{id:w.id,memo:memo});
    }
    await new Promise(res=>setTimeout(res,900));
  }
  fl.textContent='';
  flash('완료 — 성공 '+ok+'명'+(fail?(' · 실패 '+fail+'명(메모 확인)'):'')+' ✓');
  refresh();
}
async function addRow(){
  const nick=prompt('닉네임을 입력하세요');
  if(!nick||!nick.trim())return;
  await api('pick',{nick:nick.trim(),prize:'',how:'수동',date:today()});
  refresh();}
function ledgerTsv(){
  const vis=visible();
  const head=['날짜','방식','닉네임','SOOP계정','상품','쪽지','메모'].join(TAB);
  const body=vis.map(w=>[w.date||'',w.how||'',w.nick||'',w.sid||'',w.prize||'',w.sent||'',w.memo||''].join(TAB)).join(NL);
  return {n:vis.length,txt:head+NL+body};}
function copyLedger(){
  const g=ledgerTsv();
  copyToClip(g.txt,'보이는 '+g.n+'줄 복사됨 ✓');}
/* 구글 시트로 열기 — 시청자 계정이 밖에 노출되지 않도록(개인정보) 서버에서
   공개 링크를 만들지 않고, 표 내용을 클립보드에 담아 새 구글 시트를 연 뒤
   붙여넣게 합니다. 붙여넣기는 Ctrl+V 한 번이면 셀에 자동 정렬됩니다. */
function openGoogleSheet(){
  const g=ledgerTsv();
  if(!g.n)return alert('열 줄이 없습니다');
  copyToClip(g.txt,'복사됨 — 새 구글 시트에서 Ctrl+V 로 붙여넣으세요');
  window.open('https://sheets.new','_blank','noopener');
  const el=document.getElementById('flash');
  el.innerHTML='📗 새 구글 시트가 열렸습니다 — <b>빈 칸(A1)을 클릭하고 Ctrl+V</b> 로 붙여넣으세요 ('+g.n+'줄)';
  setTimeout(()=>{if(el.textContent.startsWith('📗'))el.textContent='';},9000);}
function downloadLedger(){
  const vis=visible();
  if(!vis.length)return alert('내려받을 줄이 없습니다');
  const q=s=>'"'+String(s==null?'':s).replace(/"/g,'""')+'"';
  const lines=vis.map(w=>[q(w.date),q(w.how),q(w.nick),q(w.sid),q(w.prize),q(w.sent),q(w.memo)].join(','));
  const csv=String.fromCharCode(0xFEFF)+['날짜,방식,닉네임,SOOP계정,상품,쪽지,메모'].concat(lines).join(NL);
  const a=document.createElement('a');
  a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);
  a.download='끝장전-당첨자-'+today()+'.csv';a.click();}
function updateMaskBtn(){const b=document.getElementById('maskBtn');
  if(b)b.textContent=document.body.classList.contains('maskacc')?'👁 계정 보기':'🙈 계정 가리기';}
function toggleMask(){document.body.classList.toggle('maskacc');
  try{localStorage.setItem('pzMaskAcc',document.body.classList.contains('maskacc')?'1':'');}catch(e){}
  updateMaskBtn();}
if(localStorage.getItem('pzMaskAcc'))document.body.classList.add('maskacc');
updateMaskBtn();
refresh();noteSessionStatus();
</script></body></html>
