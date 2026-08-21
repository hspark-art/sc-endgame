<?php require __DIR__ . '/auth.php'; admin_require_login(); ?>
<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="robots" content="noindex, nofollow">
<title>상품 추첨 방송 장면</title><style>
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;
font-family:'Pretendard','Malgun Gothic',sans-serif;background:#0a0d13}
#scene{position:absolute;inset:0;background:
radial-gradient(1200px 800px at 15% 20%,rgba(140,31,42,.55),transparent 60%),
radial-gradient(1200px 800px at 85% 20%,rgba(18,58,120,.55),transparent 60%),
linear-gradient(180deg,#0d1017,#080a0f)}
#scene::before{content:'';position:absolute;inset:0;opacity:.05;
background:repeating-linear-gradient(115deg,#fff 0 2px,transparent 2px 30px)}
.chroma #scene{background:#00d000}
.chroma #scene::before{display:none}
#title{position:absolute;top:54px;left:0;right:0;text-align:center;color:#fff;
font-weight:900;font-size:56px;letter-spacing:.02em;text-shadow:0 4px 18px rgba(0,0,0,.5)}
#title b{color:#ffc63d}
#hint{position:absolute;top:12px;right:16px;color:rgba(255,255,255,.35);font-size:13px}
#stage{position:absolute;left:0;right:0;top:150px;bottom:0;display:flex;
align-items:center;justify-content:center}
.box{display:none;flex-direction:column;align-items:center;gap:22px;text-align:center;padding:0 60px}
.box.show{display:flex;animation:pop .5s cubic-bezier(.2,1.5,.4,1)}
.plabel{color:#ffc63d;font-weight:900;font-size:34px;letter-spacing:.14em}
.pimg{max-width:620px;max-height:520px;border-radius:22px;object-fit:contain;
box-shadow:0 20px 60px rgba(0,0,0,.55);background:rgba(255,255,255,.03)}
.pname{color:#fff;font-weight:900;font-size:60px;line-height:1.15}
.wcap{color:#ffc63d;font-weight:900;font-size:40px;letter-spacing:.12em}
.wnick{color:#fff;font-weight:900;font-size:104px;line-height:1.1;text-shadow:0 6px 26px rgba(0,0,0,.6)}
.wprize{color:#cdd6e4;font-weight:700;font-size:40px}
.idle{color:rgba(255,255,255,.82);font-weight:800;font-size:48px}
#board{display:none}#board.show{display:block}
#drawPrize{position:absolute;left:50%;top:120px;transform:translateX(-50%);display:none;
align-items:center;gap:14px;padding:10px 22px;border-radius:999px;
background:rgba(20,26,40,.8);border:1px solid #ffc63d;z-index:4}
#drawPrize.show{display:flex}
#drawPrize img{width:44px;height:44px;object-fit:cover;border-radius:8px}
#drawPrize span{color:#ffc63d;font-weight:800;font-size:26px}
@keyframes pop{0%{transform:scale(.6);opacity:0}60%{transform:scale(1.06)}100%{transform:scale(1);opacity:1}}
#pip{position:absolute;left:44px;bottom:44px;width:560px;height:315px;border-radius:16px;
overflow:hidden;display:flex;align-items:center;justify-content:center;cursor:pointer}
#pip.frame{border:3px solid rgba(255,255,255,.5);background:rgba(0,0,0,.35)}
#pip.chroma{background:#00d000;border:0}
#pip.cam{background:#000;border:3px solid rgba(255,255,255,.35)}
#pip.off{display:none}
#pip .lab{color:rgba(255,255,255,.7);font-weight:800;font-size:22px;pointer-events:none}
#pip.chroma .lab{color:rgba(0,0,0,.35)}
#pip video{width:100%;height:100%;object-fit:cover}
#confetti{position:absolute;inset:0;pointer-events:none;z-index:5}
#lineup{position:absolute;left:0;right:0;bottom:0;top:150px;display:none;
flex-direction:column;align-items:center;justify-content:center;gap:22px}
#lineup.show{display:flex}
#lineup .llabel{color:#ffc63d;font-weight:900;font-size:34px;letter-spacing:.14em}
#lineup .cards{display:flex;gap:24px;flex-wrap:wrap;justify-content:center;max-width:1500px}
#lineup .pcard{width:230px;background:rgba(20,26,40,.72);border:1px solid rgba(255,255,255,.12);
border-radius:16px;padding:14px;text-align:center}
#lineup .pcard img{width:100%;height:180px;object-fit:contain;border-radius:10px;background:rgba(0,0,0,.2)}
#lineup .pcard .nm{color:#fff;font-weight:800;font-size:22px;margin-top:10px}
#toast{position:absolute;right:44px;top:150px;z-index:6;display:flex;flex-direction:column;gap:10px;align-items:flex-end}
.toastItem{padding:14px 24px;border-radius:14px;background:linear-gradient(135deg,#ffb020,#ff7a3d);
color:#1a1206;font-weight:900;font-size:30px;box-shadow:0 10px 30px rgba(0,0,0,.4);
animation:slideIn .4s ease, fadeOut .5s ease 5s forwards}
@keyframes slideIn{from{transform:translateX(120%);opacity:0}to{transform:translateX(0);opacity:1}}
@keyframes fadeOut{to{opacity:0;transform:translateX(120%)}}
</style></head><body>
<div id="scene"></div>
<canvas id="confetti"></canvas>
<div id="hint">화면 클릭 = 배경 초록/어둠 · PIP 클릭 = 중계진 자리 바꾸기</div>
<div id="title">&#127873; <b>&#45001;&#51109;&#51204;</b> &#49345;&#54408; &#52628;&#52628;&#52628;</div>
<div id="stage">
  <div class="box" id="idleBox"><div class="idle" id="idleText"></div></div>
  <div class="box" id="prizeBox"><div class="plabel" id="prizeLbl"></div>
    <img class="pimg" id="prizeImg" hidden><div class="pname" id="prizeName"></div></div>
  <div class="box" id="winBox"><div class="wcap" id="winCap"></div>
    <img class="pimg" id="winImg" hidden style="max-height:300px">
    <div class="wnick" id="winNick"></div><div class="wprize" id="winPrize"></div></div>
  <div class="box" id="kingBox">
    <div class="wcap">👑 오늘의 주인공</div>
    <div style="display:flex;gap:120px;margin-top:10px">
      <div><div class="plabel">채팅왕</div><div class="pname" id="ckNick"></div>
        <div class="wprize" id="ckN"></div></div>
      <div><div class="plabel" style="color:#ff8fa3">후원왕</div><div class="pname" id="bkNick"></div>
        <div class="wprize" id="bkN"></div></div></div></div>
  <div class="box" id="pdBox">
    <div class="wcap" id="pdCap">🔮 승부예측</div>
    <div style="display:flex;gap:60px;align-items:center;margin-top:6px">
      <div style="text-align:center"><div class="pname" id="pdAName" style="color:#7cb6ff"></div>
        <div class="wprize" id="pdACnt"></div></div>
      <div class="plabel" style="font-size:30px">VS</div>
      <div style="text-align:center"><div class="pname" id="pdBName" style="color:#ff8fa3"></div>
        <div class="wprize" id="pdBCnt"></div></div>
    </div>
    <div style="width:72%;height:26px;background:#1a2030;border-radius:13px;overflow:hidden;display:flex;margin-top:16px">
      <div id="pdBarA" style="background:#1c8cff;height:100%;width:50%;transition:width .5s"></div>
      <div style="background:#ff4d5a;height:100%;flex:1"></div>
    </div>
    <div class="wprize" id="pdHint" style="margin-top:12px"></div>
    <div class="wprize" id="pdTop" style="margin-top:6px;font-size:24px;color:#ffd24a"></div>
    <div id="pdFeed" style="margin-top:10px;font-size:19px;color:#aab3c5;line-height:1.6;text-align:center"></div>
  </div>
  <div id="drawPrize"></div>
  <canvas id="board" width="1200" height="820"></canvas>
  <div id="lineup"><div class="llabel">🎁 오늘의 상품</div><div class="cards" id="lineupCards"></div></div>
</div>
<div id="toast"></div>
<div id="pip" class="frame"><span class="lab" id="pipLab"></span>
  <video id="cam" autoplay muted playsinline hidden></video></div>
<script>
document.getElementById('title').innerHTML='🎁 <b>끝장전</b> 상품 추첨';
document.getElementById('idleText').textContent='잠시 후, 행운의 주인공을 뽑습니다 🎯';
document.getElementById('prizeLbl').textContent='이번 상품';
document.getElementById('winCap').textContent='🎉 축하합니다';
const PIP_MODES=['frame','chroma','cam','off'];
const PIP_LAB={frame:'중계진 화면',chroma:'',cam:'',off:''};
let pipI=0, camStream=null;
const pip=document.getElementById('pip'), camEl=document.getElementById('cam'), pipLab=document.getElementById('pipLab');
function setPip(){
  pip.className=PIP_MODES[pipI];
  pipLab.textContent=PIP_LAB[PIP_MODES[pipI]];
  if(PIP_MODES[pipI]==='cam'){
    camEl.hidden=false;
    if(!camStream){navigator.mediaDevices.getUserMedia({video:true,audio:false})
      .then(function(s){camStream=s;camEl.srcObject=s;})
      .catch(function(){pipLab.textContent='카메라 권한 거부';});}
  }else{camEl.hidden=true;}
}
pip.addEventListener('click',function(e){e.stopPropagation();pipI=(pipI+1)%PIP_MODES.length;setPip();});
setPip();
document.body.addEventListener('click',function(){document.body.classList.toggle('chroma');});
document.addEventListener('keydown',function(e){
  if(e.key==='m'||e.key==='M'){muted=!muted;
    document.getElementById('hint').textContent=muted?'🔇 소리 꺼짐 (M 키로 켜기)':'화면 클릭 = 배경 초록/어둠 · PIP 클릭 = 중계진 자리 · M = 소리';}});
let seq=-1, anim=null;
function show(id){['idleBox','prizeBox','winBox','kingBox','pdBox'].forEach(function(b){
  document.getElementById(b).classList.toggle('show',b===id);});
  document.getElementById('board').classList.remove('show');
  document.getElementById('lineup').classList.remove('show');
  if(anim){cancelAnimationFrame(anim);anim=null;}
  if(pdTimer){clearInterval(pdTimer);pdTimer=null;}
}
let allPrizes=[];
let pdTimer=null;
async function loadPrizes(){
  try{const st=await (await fetch('prize_api.php?act=state')).json();
    allPrizes=(st.prizes&&st.prizes.items)||[];}catch(e){}
}
function showDrawPrize(st){
  const d=document.getElementById('drawPrize');
  if(st.prize){d.innerHTML=(st.photo?'<img src="'+st.photo+'">':'')+
    '<span>'+String(st.prize).replace(/[&<>]/g,'')+' 추첨!</span>';d.classList.add('show');}
  else d.classList.remove('show');
}
function idle(){
  document.getElementById('drawPrize').classList.remove('show');
  const lu=document.getElementById('lineup');
  if(allPrizes.length){
    document.getElementById('lineupCards').innerHTML=allPrizes.slice(0,8).map(function(x){
      return '<div class="pcard">'+(x.photo?'<img src="'+x.photo+'">':'')+
        '<div class="nm">'+(x.name||'').replace(/[&<>]/g,'')+'</div></div>';}).join('');
    ['idleBox','prizeBox','winBox','kingBox'].forEach(function(b){document.getElementById(b).classList.remove('show');});
    document.getElementById('board').classList.remove('show');
    lu.classList.add('show');
  }else{lu.classList.remove('show');show('idleBox');}
}
function kings(st){
  ['idleBox','prizeBox','winBox'].forEach(function(b){document.getElementById(b).classList.remove('show');});
  document.getElementById('board').classList.remove('show');
  const k=document.getElementById('kingBox');k.classList.add('show');
  document.getElementById('ckNick').textContent=st.chatNick||'-';
  document.getElementById('ckN').textContent='채팅 '+(st.chatN||0)+'개';
  document.getElementById('bkNick').textContent=st.balNick||'-';
  document.getElementById('bkN').textContent='별풍선 '+(st.balN||0)+'개';
}
function hideKings(){document.getElementById('kingBox').classList.remove('show');}
/* 룰렛 — 돌아가는 원판이 당첨자 칸에서 멈춥니다 */
function roulette(st){
  const slots=st.slots,winIdx=slots.indexOf(st.winner),N=slots.length;
  ['idleBox','prizeBox','winBox','kingBox'].forEach(function(b){document.getElementById(b).classList.remove('show');});
  const cvr=document.getElementById('board');cvr.classList.add('show');showDrawPrize(st);
  const cxr=cvr.getContext('2d'),cx0=cvr.width/2,cy0=380,R=330;
  const seg=2*Math.PI/N, target=-(winIdx*seg)-seg/2+ -Math.PI/2;
  const spins=5, dur=4200; let t0=null;
  const cols=['#ff6a6a','#ffb020','#4ade80','#4a9eff','#c084fc','#f472b6'];
  function frame(ts){
    if(!t0)t0=ts;const el=ts-t0,f=Math.min(1,el/dur);
    const ease=1-Math.pow(1-f,3);
    const ang=ease*(spins*2*Math.PI+target);
    cxr.clearRect(0,0,cvr.width,cvr.height);
    cxr.font='900 40px Pretendard';cxr.textAlign='center';cxr.fillStyle='#ffc63d';
    cxr.fillText('🎡 행운의 룰렛',cx0,54);
    for(let i=0;i<N;i++){
      const a0=ang+i*seg,a1=a0+seg;
      cxr.beginPath();cxr.moveTo(cx0,cy0);cxr.arc(cx0,cy0,R,a0,a1);cxr.closePath();
      cxr.fillStyle=cols[i%cols.length];cxr.fill();
      cxr.save();cxr.translate(cx0,cy0);cxr.rotate(a0+seg/2);
      cxr.fillStyle='#0b0d11';cxr.textAlign='right';
      cxr.font='800 '+Math.min(26,220/Math.max(4,slots[i].length))+'px Pretendard';
      cxr.fillText(slots[i],R-16,7);cxr.restore();
    }
    cxr.beginPath();cxr.moveTo(cx0+R+8,cy0-20);cxr.lineTo(cx0+R-24,cy0);cxr.lineTo(cx0+R+8,cy0+20);
    cxr.closePath();cxr.fillStyle='#fff';cxr.fill();
    if(f<1)anim=requestAnimationFrame(frame);
    else{cvr.classList.remove('show');winner({nick:st.winner,prize:st.prize,photo:st.photo,how:'룰렛'});}
  }
  anim=requestAnimationFrame(frame);
}
/* 큰 별풍선 감사 토스트 */
let toastSeen=0;
async function pollToasts(){
  try{
    const t=await (await fetch('prize_api.php?act=toasts')).json();
    (t.list||[]).forEach(function(x){
      if(x.seq>toastSeen){toastSeen=x.seq;
        const d=document.createElement('div');d.className='toastItem';
        d.textContent='🎈 '+x.nick+'님 별풍선 '+x.count+'개 감사합니다!';
        document.getElementById('toast').appendChild(d);
        setTimeout(function(){d.remove();},5600);}
    });
  }catch(e){}
  setTimeout(pollToasts,1500);
}
pollToasts();
function prize(st){
  show('prizeBox');
  const im=document.getElementById('prizeImg');
  if(st.photo){im.src=st.photo;im.hidden=false;}else im.hidden=true;
  document.getElementById('prizeName').textContent=st.prize||'';
}
// 당첨 효과음 — 외부 파일 없이 만들어 냅니다 (밝은 3음 + 반짝임).
let audioCtx=null, muted=false;
function initAudio(){ if(!audioCtx){ try{audioCtx=new (window.AudioContext||window.webkitAudioContext)();}catch(e){} } }
document.body.addEventListener('click',initAudio,{once:true});
function winSound(){
  if(muted||!audioCtx)return;
  try{
    const t0=audioCtx.currentTime;
    [523.25,659.25,783.99,1046.5].forEach(function(f,i){
      const o=audioCtx.createOscillator(),g=audioCtx.createGain();
      o.type='triangle';o.frequency.value=f;
      const t=t0+i*0.12;
      g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(0.22,t+0.03);
      g.gain.exponentialRampToValueAtTime(0.001,t+0.45);
      o.connect(g);g.connect(audioCtx.destination);o.start(t);o.stop(t+0.5);
    });
  }catch(e){}
}
function fireConfetti(){
  const c=document.getElementById('confetti'),x=c.getContext('2d');
  c.width=window.innerWidth||1920;c.height=window.innerHeight||1080;
  const cols=['#ffc63d','#ff6a6a','#4ade80','#4a9eff','#c084fc','#ffffff'];
  const P=[];for(let i=0;i<160;i++)P.push({x:c.width/2+(Math.random()-.5)*400,
    y:c.height*0.3,vx:(Math.random()-.5)*14,vy:Math.random()*-16-4,
    g:0.4+Math.random()*0.3,r:Math.random()*8+4,c:cols[i%cols.length],
    rot:Math.random()*6,vr:(Math.random()-.5)*0.4});
  let f=0;
  (function frame(){
    x.clearRect(0,0,c.width,c.height);f++;
    P.forEach(function(p){p.vy+=p.g;p.x+=p.vx;p.y+=p.vy;p.rot+=p.vr;
      x.save();x.translate(p.x,p.y);x.rotate(p.rot);x.fillStyle=p.c;
      x.fillRect(-p.r/2,-p.r/2,p.r,p.r*0.6);x.restore();});
    if(f<140)requestAnimationFrame(frame);else x.clearRect(0,0,c.width,c.height);
  })();
}
function winner(st){
  document.getElementById('drawPrize').classList.remove('show');
  show('winBox');
  fireConfetti();
  winSound();
  document.getElementById('winCap').textContent={'핀볼':'🎯 핀볼 추첨 당첨','룰렛':'🎡 룰렛 당첨'}[st.how]||'🎉 축하합니다';
  const im=document.getElementById('winImg');
  if(st.photo){im.src=st.photo;im.hidden=false;}else im.hidden=true;
  document.getElementById('winNick').textContent=st.nick||st.winner||'';
  document.getElementById('winPrize').textContent=st.prize||'';
}
const cv=document.getElementById('board'),cx=cv.getContext('2d');
function plinko(st){
  const slots=st.slots,winIdx=slots.indexOf(st.winner);
  const ROWS=9,T=210,slotW=cv.width/slots.length;
  let col=Math.floor(slots.length/2),path=[];
  for(let r=0;r<ROWS;r++){
    const remain=ROWS-r,diff=winIdx-col;
    let step;
    if(Math.abs(diff)>=remain)step=Math.sign(diff);
    else step=Math.random()<0.5+diff*0.18?1:-1;
    col=Math.max(0,Math.min(slots.length-1,col+step));path.push(col);
  }
  path[ROWS-1]=winIdx;
  ['idleBox','prizeBox','winBox'].forEach(function(b){document.getElementById(b).classList.remove('show');});
  cv.classList.add('show');showDrawPrize(st);
  let t0=null;
  function frame(ts){
    if(!t0)t0=ts;const el=ts-t0,total=ROWS*T+700;
    cx.clearRect(0,0,cv.width,cv.height);
    cx.fillStyle='rgba(10,13,20,.6)';
    cx.beginPath();cx.roundRect(0,0,cv.width,cv.height,26);cx.fill();
    cx.strokeStyle='#ffc63d';cx.lineWidth=4;cx.stroke();
    cx.fillStyle='#ffc63d';cx.font='900 42px Pretendard';cx.textAlign='center';
    cx.fillText('🎯 행운의 핀볼 추첨',cv.width/2,60);
    cx.fillStyle='#8a93a6';
    for(let r=0;r<ROWS;r++)for(let c=0;c<=slots.length;c++){
      const px=c*slotW+(r%2?slotW/2:0);
      if(px>10&&px<cv.width-10){cx.beginPath();cx.arc(px,120+r*62,5,0,7);cx.fill();}
    }
    slots.forEach(function(s2,i2){
      const hl=el>total-500&&i2===winIdx;
      cx.fillStyle=hl?'#ffc63d':'rgba(27,32,43,.95)';
      cx.beginPath();cx.roundRect(i2*slotW+5,cv.height-92,slotW-10,82,10);cx.fill();
      cx.fillStyle=hl?'#0b0d11':'#e8ecf3';
      cx.font=(hl?'900 ':'700 ')+Math.min(26,300/Math.max(4,s2.length)+10)+'px Pretendard';
      cx.fillText(s2,i2*slotW+slotW/2,cv.height-42);
    });
    const step=Math.min(ROWS-1,Math.floor(el/T)),f=Math.min(1,(el-step*T)/T);
    const c0=step?path[step-1]:Math.floor(slots.length/2),c1=path[step];
    const bx=(c0+(c1-c0)*f+0.5)*slotW,by=88+step*62+f*62+Math.sin(f*3.14)*-24;
    const yy=el>ROWS*T?Math.min(cv.height-116,88+ROWS*62+(el-ROWS*T)*.9):by;
    cx.fillStyle='#ff4d5a';
    cx.beginPath();cx.arc(el>ROWS*T?(winIdx+0.5)*slotW:bx,yy,17,0,7);cx.fill();
    if(el<total)anim=requestAnimationFrame(frame);
    else{cv.classList.remove('show');winner({nick:st.winner,prize:st.prize,photo:st.photo,how:'핀볼'});}
  }
  anim=requestAnimationFrame(frame);
}
function totoLive(st){
  show('pdBox');
  document.getElementById('pdTop').textContent='';
  async function tick(){
    try{
      const d=(await (await fetch('prize_api.php?act=toto_public')).json()).day;
      if(!d)return;
      const fd=(d.feed||[]).slice(0,3).map(function(f){return f.msg;}).join('   ');
      document.getElementById('pdFeed').textContent=fd;
      const r=d.round;
      if(!r){
        document.getElementById('pdCap').textContent='🔮 시청자 승부예측 — 채팅에 "도전"을 치면 참여! (1인 10,000P)';
        document.getElementById('pdAName').textContent='참여 '+d.entries+'명';
        document.getElementById('pdBName').textContent='';
        document.getElementById('pdACnt').textContent='';
        document.getElementById('pdBCnt').textContent='';
        document.getElementById('pdBarA').style.width='50%';
        document.getElementById('pdHint').textContent='세트마다 "선수이름 금액" 으로 베팅 · 첫 베팅 고정 · 가상 포인트';
        return;
      }
      const tot=r.poolA+r.poolB, pa=tot?Math.round(r.poolA*100/tot):50;
      const oa=r.poolA>0?(tot/r.poolA).toFixed(2):'-', ob=r.poolB>0?(tot/r.poolB).toFixed(2):'-';
      document.getElementById('pdCap').textContent=(r.state==='locked')
        ?'⏸ 베팅 마감 — 결과를 기다립니다!':'💰 베팅 접수 중 — 채팅에 "선수이름 금액"!';
      document.getElementById('pdAName').textContent=r.a;
      document.getElementById('pdBName').textContent=r.b;
      document.getElementById('pdACnt').textContent=r.poolA.toLocaleString()+'P · 배당 '+oa;
      document.getElementById('pdBCnt').textContent=r.poolB.toLocaleString()+'P · 배당 '+ob;
      document.getElementById('pdBarA').style.width=(tot?pa:50)+'%';
      document.getElementById('pdHint').textContent='베팅 '+r.bets+'건 · 총 '+tot.toLocaleString()+'P · "이름 올인"도 가능 · 첫 베팅 고정';
    }catch(e){}
  }
  tick();pdTimer=setInterval(tick,2000);
}
function totoResult(st){
  show('pdBox');fireConfetti();winSound();
  const tot=(st.poolA||0)+(st.poolB||0);
  document.getElementById('pdCap').textContent=st.refund
    ?'⚖ 적중자 없음 — 전원 환불':'🏆 '+(st.wname||'')+' 승!';
  document.getElementById('pdAName').textContent=st.refund?'':(st.wname||'');
  document.getElementById('pdBName').textContent='';
  document.getElementById('pdACnt').textContent=st.refund?'':'배당 '+(st.odds||0).toFixed(2)+'배';
  document.getElementById('pdBCnt').textContent='';
  document.getElementById('pdBarA').style.width='50%';
  document.getElementById('pdHint').textContent=st.refund
    ?'건 포인트를 모두 돌려드렸습니다'
    :'적중 '+(st.hit||0)+'명 · 총 풀 '+tot.toLocaleString()+'P';
  document.getElementById('pdTop').textContent=(st.top&&st.top.length)
    ?('🔥 '+st.top.slice(0,3).map(function(t){return t.n+' +'+t.gain.toLocaleString()+'P'}).join('  ·  ')):'';
  document.getElementById('pdFeed').textContent='';
}
function totoChamp(st){
  show('pdBox');fireConfetti();winSound();
  document.getElementById('pdCap').textContent='👑 오늘의 승부예측 우승!';
  document.getElementById('pdAName').textContent=st.n||'';
  document.getElementById('pdBName').textContent='';
  document.getElementById('pdACnt').textContent=(st.bal||0).toLocaleString()+'P';
  document.getElementById('pdBCnt').textContent='';
  document.getElementById('pdBarA').style.width='50%';
  document.getElementById('pdHint').textContent='참여 '+(st.entries||0)+'명';
  document.getElementById('pdTop').textContent=(st.rank&&st.rank.length>1)
    ?st.rank.slice(1,4).map(function(r,i){return (i+2)+'위 '+r.n+' '+r.bal.toLocaleString()+'P'}).join('  ·  '):'';
  document.getElementById('pdFeed').textContent='';
}
async function poll(){
  try{
    const st=await (await fetch('prize_api.php?act=overlay')).json();
    if(st.seq!==seq){
      seq=st.seq;
      if(st.kind==='winner')winner(st);
      else if(st.kind==='plinko')plinko(st);
      else if(st.kind==='roulette')roulette(st);
      else if(st.kind==='kings')kings(st);
      else if(st.kind==='prize')prize(st);
      else if(st.kind==='toto')totoLive(st);
      else if(st.kind==='toto_result')totoResult(st);
      else if(st.kind==='toto_champ')totoChamp(st);
      else idle();
    }
  }catch(e){}
  setTimeout(poll,900);
}
loadPrizes();setInterval(loadPrizes,30000);idle();poll();
</script></body></html>
