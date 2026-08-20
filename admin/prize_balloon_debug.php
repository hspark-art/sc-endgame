<?php require __DIR__ . '/auth.php'; admin_require_login(); ?>
<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>별풍선 실시간 확인 — 끝장전</title><style>
*{box-sizing:border-box}body{margin:0;background:#0a0d13;color:#e8ecf3;
font-family:'Pretendard','Malgun Gothic',sans-serif;font-size:14px}
.wrap{max-width:1200px;margin:0 auto;padding:14px 16px}
h1{font-size:18px;margin:4px 0 10px}
a.top{color:#8a93a6;font-size:12.5px;text-decoration:none}a.top:hover{color:#e8ecf3}
.row{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin:6px 0}
input,button{font-family:inherit;font-size:13px;border-radius:8px}
input{background:#1b202b;color:#e8ecf3;border:1px solid #232a38;padding:7px 9px}
button{background:#1c8cff;border:0;color:#fff;padding:8px 13px;font-weight:700;cursor:pointer}
button.gray{background:#232a38}
.pill{background:#1b202b;border:1px solid #232a38;border-radius:999px;padding:2px 9px;font-size:11.5px;color:#8a93a6}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
td,th{padding:6px 8px;text-align:left;border-bottom:1px solid #171c25;white-space:nowrap}
th{color:#8a93a6;font-size:11px;position:sticky;top:0;background:#0a0d13}
.b109{color:#ffd24a}.b18{color:#4ade80}.ad{color:#7cb6ff}.sub{color:#a78bfa}.etc{color:#8a93a6}
.item{font-variant-numeric:tabular-nums}
.hint{color:#8a93a6;font-size:12px;line-height:1.7;margin-top:8px}
.big{background:#12283f}
.live{color:#ff4d5a;font-weight:900}
mark{background:#3a2b12;color:#ffd24a;padding:0 3px;border-radius:4px}
</style></head><body><div class="wrap">
<h1>🔎 별풍선 실시간 확인 <span id="flag" class="pill">연결 준비…</span></h1>
<div class="row">
<span class="pill">채널</span>
<input id="bj" placeholder="talent" style="width:150px">
<button class="gray" onclick="go()">붙기</button>
<a class="top" href="prize.php">← 관제로</a>
<span style="flex:1"></span>
<button class="gray" onclick="rows.length=0;document.querySelector('#t tbody').innerHTML=''">지우기</button>
</div>
<div class="hint">들어오는 <b>선물 후보</b> 이벤트를 원본 그대로 보여줍니다. 방송의 실제 별풍선/이모티콘과 맞춰 보세요.
<b class="b109">노랑=svc109</b> · <b class="b18">초록=svc18(큰 별풍선)</b> · <b class="ad">파랑=애드벌룬</b> · <b class="sub">보라=구독</b>.
같은 사람이 <b>아이템ID가 계속 같으면 이모티콘/시그니처</b>(예: 가포 537477152), <b>제각각이면 진짜 별풍선</b>입니다.</div>
<table id="t"><thead><tr><th>시각</th><th>svc</th><th>종류</th><th>닉네임</th><th>계정</th>
<th class="num">개수</th><th>아이템ID</th><th>원본 필드</th></tr></thead><tbody></tbody></table>
<script>
const BJ=(new URLSearchParams(location.search).get('bj')||'talent').toLowerCase().replace(/[^a-z0-9_]/g,'')||'talent';
document.getElementById('bj').value=BJ;
function go(){const v=document.getElementById('bj').value.trim();location.href=v?('prize_balloon_debug.php?bj='+encodeURIComponent(v)):'prize_balloon_debug.php';}
const F='\x0c', rows=[];
function esc(s){return String(s==null?'':s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function clean(s){s=(s||'').trim();if(s.endsWith(')')&&s.includes('('))s=s.slice(0,s.lastIndexOf('('));return s.trim()}
function pkt(svc,body){const b=new TextEncoder().encode(body);
  const h=new TextEncoder().encode('\x1b\t'+String(svc).padStart(4,'0')+String(b.length).padStart(6,'0')+'00');
  const u=new Uint8Array(h.length+b.length);u.set(h);u.set(b,h.length);return u;}
function setFlag(h){document.getElementById('flag').innerHTML=h}
// 같은 사람이 같은 아이템ID 를 몇 번 보냈는지 (이모티콘 반복 표시용)
const itemSeen={};
const EMOTE_ITEMS=new Set(['537477152','2684436480']);
function classify(svc,f){
  if(svc===109){const it=(f[8]||'').split('|')[0];
    return {k:EMOTE_ITEMS.has(it)?'이모티콘(제외)':'별풍선(svc109)',cls:EMOTE_ITEMS.has(it)?'etc':'b109',nick:clean(f[7]),id:clean(f[6]),cnt:f[4],item:it};}
  if(svc===18)  return {k:'별풍선(svc18)', cls:'b18', nick:clean(f[3]),id:clean(f[2]),cnt:f[4],item:'(svc18)'};
  if(svc===87)  return {k:'애드벌룬',       cls:'ad',  nick:clean(f[4]||f[3]),id:clean(f[3]),cnt:(f[5]||'').replace(/[^0-9]/g,'')||'?',item:'ad'};
  if(svc===54)  return {k:'구독',           cls:'sub', nick:clean(f[2]),id:'',cnt:'',item:'sub'};
  return {k:'기타 svc'+svc,cls:'etc',nick:'',id:'',cnt:'',item:''};
}
function add(svc,f){
  const c=classify(svc,f);
  let repeat='';
  if((svc===109||svc===18)&&c.id&&c.item){
    const key=c.id+'|'+c.item; itemSeen[key]=(itemSeen[key]||0)+1;
    if(itemSeen[key]>=2) repeat=' <mark>같은아이템 '+itemSeen[key]+'회</mark>';
  }
  const t=new Date().toTimeString().slice(0,8);
  rows.unshift('<tr class="'+(+c.cnt>=50?'big':'')+'"><td class="pill">'+t+'</td>'+
    '<td class="'+c.cls+'">'+svc+'</td><td class="'+c.cls+'">'+esc(c.k)+'</td>'+
    '<td><b>'+esc(c.nick)+'</b></td><td class="pill">'+esc(c.id)+'</td>'+
    '<td class="num">'+esc(c.cnt)+'</td><td class="item">'+esc(c.item)+repeat+'</td>'+
    '<td class="pill" style="font-size:10.5px;color:#5a6376">'+esc(JSON.stringify(f.slice(0,11)))+'</td></tr>');
  rows.splice(300);
  document.querySelector('#t tbody').innerHTML=rows.join('');
}
let ws=null,pingT=null;
async function connect(){
  let info;
  try{info=await (await fetch('prize_api.php?act=live&bj='+BJ)).json();}
  catch(e){setFlag('서버 오류');return setTimeout(connect,15000);}
  if(String(info.RESULT)!=='1'){setFlag('방송 대기 중…');return setTimeout(connect,15000);}
  setFlag('<span class="live">● LIVE</span> '+esc(info.TITLE||''));
  try{ws=new WebSocket('wss://'+info.CHDOMAIN+':'+(+info.CHPT+1)+'/Websocket/'+BJ,['chat']);}
  catch(e){setFlag('연결 실패');return setTimeout(connect,15000);}
  ws.binaryType='arraybuffer';let joined=false;
  ws.onopen=()=>{ws.send(pkt(1,F+F+F+'16'+F));pingT=setInterval(()=>{try{ws.send(pkt(0,F))}catch(e){}},50000);};
  ws.onmessage=(m)=>{const s=new TextDecoder().decode(m.data);
    if(!s.startsWith('\x1b\t'))return;const svc=+s.slice(2,6),f=s.slice(14).split(F);
    if(!joined){joined=true;ws.send(pkt(2,F+String(info.CHATNO)+F+F+F+F));}
    if([18,54,87,106,107,108,109].includes(svc))add(svc,f);
  };
  ws.onclose=()=>{clearInterval(pingT);setFlag('연결 끊김 — 다시 붙는 중…');setTimeout(connect,6000);};
  ws.onerror=()=>{try{ws.close()}catch(e){}};
}
connect();
</script></body></html>
