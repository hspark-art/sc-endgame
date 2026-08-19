<?php require __DIR__ . '/auth.php'; admin_require_login(); ?>
<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="robots" content="noindex, nofollow">
<title>당첨 자막 — 방송 화면용</title><style>
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;
background:#00ff00;overflow:hidden;font-family:'Pretendard','Malgun Gothic',sans-serif}
body.dark{background:#0a0d13}
#hint{position:absolute;top:10px;left:14px;color:rgba(0,0,0,.55);font-size:13px;
font-weight:700}body.dark #hint{color:rgba(255,255,255,.4)}
#banner{position:absolute;left:50%;bottom:6%;transform:translateX(-50%) scale(0);
display:flex;align-items:center;gap:26px;padding:26px 44px;border-radius:22px;
background:linear-gradient(135deg,rgba(12,16,26,.96),rgba(20,26,40,.96));
border:3px solid #ffc63d;box-shadow:0 18px 60px rgba(0,0,0,.6);
transition:transform .45s cubic-bezier(.2,1.6,.4,1)}
#banner.show{transform:translateX(-50%) scale(1)}
#banner img{width:120px;height:120px;object-fit:cover;border-radius:16px}
#banner .cap{color:#ffc63d;font-weight:900;font-size:28px;letter-spacing:.12em}
#banner .nick{color:#fff;font-weight:900;font-size:58px;line-height:1.15}
#banner .prize{color:#cdd6e4;font-weight:700;font-size:32px}
#board{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);display:none}
#board.show{display:block}
</style></head><body>
<div id="hint">이 창을 방송 화면에 잡으세요 · 초록 배경은 크로마키용 — 화면을 누르면 어두운 배경으로 바뀝니다</div>
<div id="banner"><img id="bimg" hidden>
<div><div class="cap" id="bcap">🎁 상품 당첨</div>
<div class="nick" id="bnick"></div><div class="prize" id="bprize"></div></div></div>
<canvas id="board" width="1200" height="860"></canvas>
<script>
document.body.addEventListener('click',()=>document.body.classList.toggle('dark'));
let seq=-1,anim=null;
const cv=document.getElementById('board'),cx=cv.getContext('2d');
function showBanner(nick,prize,photo,cap){
  const b=document.getElementById('banner');
  document.getElementById('bnick').textContent=nick;
  document.getElementById('bprize').textContent=prize||'';
  document.getElementById('bcap').textContent=cap||'🎁 상품 당첨';
  const im=document.getElementById('bimg');
  if(photo){im.src=photo;im.hidden=false}else im.hidden=true;
  b.classList.add('show');
}
function hideAll(){
  document.getElementById('banner').classList.remove('show');
  cv.classList.remove('show');
  if(anim){cancelAnimationFrame(anim);anim=null}
}
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
  let t0=null;cv.classList.add('show');
  function frame(ts){
    if(!t0)t0=ts;
    const el=ts-t0,total=ROWS*T+700;
    cx.clearRect(0,0,cv.width,cv.height);
    cx.fillStyle='rgba(10,13,20,.92)';
    cx.beginPath();cx.roundRect(0,0,cv.width,cv.height,26);cx.fill();
    cx.strokeStyle='#ffc63d';cx.lineWidth=4;cx.stroke();
    cx.fillStyle='#ffc63d';cx.font='900 40px Pretendard';cx.textAlign='center';
    cx.fillText('🎯 행운의 핀볼 추첨',cv.width/2,62);
    cx.fillStyle='#8a93a6';
    for(let r=0;r<ROWS;r++)for(let c=0;c<=slots.length;c++){
      const px=c*slotW+(r%2?slotW/2:0);
      if(px>10&&px<cv.width-10){cx.beginPath();cx.arc(px,130+r*64,5,0,7);cx.fill()}
    }
    slots.forEach((s2,i2)=>{
      const hl=el>total-500&&i2===winIdx;
      cx.fillStyle=hl?'#ffc63d':'rgba(27,32,43,.95)';
      cx.beginPath();cx.roundRect(i2*slotW+5,cv.height-96,slotW-10,86,10);cx.fill();
      cx.fillStyle=hl?'#0b0d11':'#e8ecf3';
      cx.font=(hl?'900 ':'700 ')+Math.min(26,300/Math.max(4,s2.length)+10)+'px Pretendard';
      cx.fillText(s2,i2*slotW+slotW/2,cv.height-44);
    });
    const step=Math.min(ROWS-1,Math.floor(el/T)),f=Math.min(1,(el-step*T)/T);
    const c0=step?path[step-1]:Math.floor(slots.length/2),c1=path[step];
    const bx=(c0+(c1-c0)*f+0.5)*slotW;
    const by=96+step*64+f*64+Math.sin(f*3.14)*-26;
    const yy=el>ROWS*T?Math.min(cv.height-120,96+ROWS*64+(el-ROWS*T)*.9):by;
    cx.fillStyle='#ff4d5a';
    cx.beginPath();cx.arc(el>ROWS*T?(winIdx+0.5)*slotW:bx,yy,17,0,7);cx.fill();
    if(el<total)anim=requestAnimationFrame(frame);
    else{cv.classList.remove('show');
      showBanner(st.winner,st.prize,st.photo,'🎯 핀볼 추첨 당첨');}
  }
  anim=requestAnimationFrame(frame);
}
async function poll(){
  try{
    const st=await (await fetch('prize_api.php?act=overlay')).json();
    if(st.seq!==seq){
      seq=st.seq;hideAll();
      if(st.kind==='winner')showBanner(st.nick,st.prize,st.photo,
        st.how==='핀볼'?'🎯 핀볼 추첨 당첨':'🎁 상품 당첨');
      else if(st.kind==='plinko')plinko(st);
    }
  }catch(e){}
  setTimeout(poll,900);
}
poll();
</script></body></html>
