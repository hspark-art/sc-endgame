<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>승부토토 — 끝장전</title><style>
*{box-sizing:border-box}body{margin:0;background:#0a0d13;color:#e8ecf3;
font-family:'Pretendard','Malgun Gothic','Apple SD Gothic Neo',sans-serif;font-size:15px}
.wrap{max-width:880px;margin:0 auto;padding:18px 14px 60px}
h1{font-size:22px;margin:6px 0 2px}
.sub{color:#8a93a6;font-size:13px;margin-bottom:14px}
a{color:#7cb6ff;text-decoration:none}
.card{background:#11151d;border:1px solid #1d2431;border-radius:14px;padding:14px 16px;margin:12px 0}
.live{border-color:#2b4a76;background:#0f1a2b}
.lt{font-weight:800;font-size:15px;margin-bottom:8px}
.vs{display:flex;align-items:center;gap:10px;font-weight:800;font-size:17px;flex-wrap:wrap}
.aName{color:#7cb6ff}.bName{color:#ff8fa3}
.bar{height:14px;background:#33202a;border-radius:7px;overflow:hidden;display:flex;margin:8px 0 4px}
.bar>div:first-child{background:#1c8cff;transition:width .5s}
.bar>div:last-child{background:#ff4d5a;flex:1}
.pill{background:#1b202b;border:1px solid #232a38;border-radius:999px;padding:2px 10px;font-size:12px;color:#8a93a6}
.rule{color:#aab3c5;font-size:13px;line-height:1.95}
input{background:#1b202b;color:#e8ecf3;border:1px solid #232a38;border-radius:9px;
padding:9px 12px;font-size:14px;width:100%;font-family:inherit}
table{width:100%;border-collapse:collapse;font-size:14px}
td,th{padding:8px 8px;text-align:left;border-bottom:1px solid #171c25;white-space:nowrap}
th{color:#8a93a6;font-size:11.5px}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tr.me{background:#12283f}
.rank{width:44px;color:#8a93a6;font-weight:800}.medal{font-size:17px}
.pts{color:#ffd24a;font-weight:800}.st{color:#4ade80;font-weight:700}
.bust{color:#f87171;font-size:11px}
.small{font-size:12px;color:#8a93a6}
.feed{font-size:13px;line-height:2;max-height:230px;overflow:auto}
.feed .ok{color:#4ade80}.feed .no{color:#f87171}.feed .in{color:#7cb6ff}.feed .se{color:#ffd24a}
.empty{color:#8a93a6;text-align:center;padding:22px 0;line-height:1.9}
.tabs{display:flex;gap:6px;margin:10px 0 2px}
.tab{background:#1b202b;border:1px solid #232a38;border-radius:999px;padding:6px 14px;
font-size:13px;color:#8a93a6;cursor:pointer;font-weight:700}
.tab.on{background:#1c8cff;border-color:#1c8cff;color:#fff}
@media(max-width:560px){td,th{padding:7px 5px;font-size:13px}.hidem{display:none}}
</style></head><body><div class="wrap">
<h1>🎰 끝장전 승부토토</h1>
<div class="sub">채팅으로 참여하는 가상 포인트 배팅 · <span id="upd" class="pill">불러오는 중…</span>
 · <a href="index.html">← 끝장전 기록실</a></div>

<div class="card live" id="liveCard" style="display:none">
  <div class="lt" id="liveState"></div>
  <div class="vs" id="liveVs" style="display:none"><span class="aName" id="lvA"></span><span id="lvACnt" class="pill"></span>
    <span style="color:#8a93a6">vs</span>
    <span id="lvBCnt" class="pill"></span><span class="bName" id="lvB"></span></div>
  <div class="bar" id="liveBar" style="display:none"><div id="lvBarA" style="width:50%"></div><div></div></div>
  <div class="small" id="liveHint"></div>
</div>

<div class="card">
  <div class="lt">참여 방법 · 규칙</div>
  <div class="rule">
  ① 방송 중 채팅에 <b>도전</b> 이라고 치면 참여 — 그날의 가상 <b class="pts">10,000P</b> 지급 (1인 1회)<br>
  ② 세트마다 베팅이 열리면 채팅에 <b>"선수이름 금액"</b> (예: 김지성 3000) 또는 <b>"선수이름 올인"</b><br>
  ③ <b>첫 베팅만 인정</b> — 바꿀 수 없어요. 오탈자·형식이 다르면 접수되지 않습니다 (아래 접수 확인 참고)<br>
  ④ 배당은 <b>총 풀 ÷ 이긴 쪽 풀</b> — 소수 쪽에 걸수록 크게 법니다. 적중자가 없으면 전원 환불<br>
  ⑤ <b class="bust">포인트를 다 잃으면 그날은 끝</b> (관전만) · 하루가 끝나면 <b>최종 포인트 1위가 우승</b>!</div>
</div>

<div class="tabs">
 <button class="tab on" data-tab="today">오늘</button>
 <button class="tab" data-tab="season">시즌 랭킹</button>
</div>

<div id="tabToday">
<div class="card">
  <div class="lt">📋 접수 확인 (실시간) <span class="small">— 내 베팅이 들어갔는지 여기서 확인!</span></div>
  <input id="qf" placeholder="내 닉네임 검색" oninput="paint()">
  <div class="feed" id="feed" style="margin-top:8px"></div>
  <div class="empty" id="noFeed" style="display:none">아직 소식이 없습니다.</div>
</div>
<div class="card">
  <div class="lt">🏆 오늘의 순위 <span class="small" id="cnt"></span></div>
  <div style="overflow-x:auto"><table id="t"><thead><tr>
  <th class="rank">순위</th><th>닉네임</th><th class="num">포인트</th>
  <th class="num">베팅 승패</th><th class="hidem"></th>
  </tr></thead><tbody></tbody></table></div>
  <div class="empty" id="noRows" style="display:none">아직 참가자가 없습니다 — 방송에서 채팅에 <b>도전</b>!</div>
</div>
<div class="card">
  <div class="lt">최근 베팅 결과</div>
  <div style="overflow-x:auto"><table id="r"><thead><tr>
  <th>매치</th><th>결과</th><th class="num">배당</th><th class="num">풀</th><th class="num">적중</th>
  </tr></thead><tbody></tbody></table></div>
  <div class="empty" id="noRounds" style="display:none">아직 진행된 베팅이 없습니다.</div>
</div>
</div>

<div id="tabSeason" style="display:none">
<div class="card">
  <div class="lt">👑 시즌 종합 랭킹 <span class="small">우승 → 누적 포인트 순</span></div>
  <input id="qs" placeholder="내 닉네임 검색" oninput="paint()">
  <div style="overflow-x:auto;margin-top:8px"><table id="ts"><thead><tr>
  <th class="rank">순위</th><th>닉네임</th><th class="num">우승</th><th class="num">승률</th>
  <th class="num">누적P</th><th class="num hidem">최고P</th><th class="num hidem">참여일</th>
  </tr></thead><tbody></tbody></table></div>
  <div class="empty" id="noSeason" style="display:none">아직 시즌 기록이 없습니다.</div>
</div>
<div class="card">
  <div class="lt">지난 날들의 우승자</div>
  <div id="daysList" class="rule"></div>
</div>
</div>
<div class="small" style="text-align:center;margin-top:16px">
가상 포인트입니다 (현금 아님) · <a href="index.html">끝장전 기록실</a></div>

<script>
let data=null;
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
document.querySelectorAll('.tab').forEach(function(b){
  b.addEventListener('click',function(){
    document.querySelectorAll('.tab').forEach(function(x){x.classList.toggle('on',x===b)});
    document.getElementById('tabToday').style.display=b.getAttribute('data-tab')==='today'?'':'none';
    document.getElementById('tabSeason').style.display=b.getAttribute('data-tab')==='season'?'':'none';
  });
});
function paint(){
  if(!data)return;
  const d=data.day, lc=document.getElementById('liveCard');
  const qf=(document.getElementById('qf').value||'').trim().toLowerCase();
  if(d){
    lc.style.display='';
    const r=d.round;
    if(r){
      document.getElementById('liveVs').style.display='';
      document.getElementById('liveBar').style.display='';
      const tot=r.poolA+r.poolB, pa=tot?Math.round(r.poolA*100/tot):50;
      const oa=r.poolA>0?(tot/r.poolA).toFixed(2):'-', ob=r.poolB>0?(tot/r.poolB).toFixed(2):'-';
      document.getElementById('liveState').textContent=(r.state==='locked')?'⏸ 베팅 마감 — 결과 대기 중':'💰 베팅 접수 중!';
      document.getElementById('lvA').textContent=r.a;
      document.getElementById('lvB').textContent=r.b;
      document.getElementById('lvACnt').textContent=r.poolA.toLocaleString()+'P · '+oa+'배';
      document.getElementById('lvBCnt').textContent=r.poolB.toLocaleString()+'P · '+ob+'배';
      document.getElementById('lvBarA').style.width=(tot?pa:50)+'%';
      document.getElementById('liveHint').textContent='베팅 '+r.bets+'건 · 채팅에 "선수이름 금액" (첫 베팅 고정)';
    }else{
      document.getElementById('liveVs').style.display='none';
      document.getElementById('liveBar').style.display='none';
      document.getElementById('liveState').textContent=d.open?'🟢 참여 접수 중 — 채팅에 "도전"!':'오늘 판 진행 중';
      document.getElementById('liveHint').textContent='참여 '+d.entries+'명';
    }
    const fd=(d.feed||[]).filter(function(f){return !qf||String(f.msg).toLowerCase().indexOf(qf)>=0;});
    document.getElementById('feed').innerHTML=fd.map(function(f){
      const cls=f.type==='bet'?'ok':(f.type==='fail'?'no':(f.type==='join'?'in':'se'));
      return '<div class="'+cls+'">'+esc(f.at+'  '+f.msg)+'</div>';}).join('');
    document.getElementById('noFeed').style.display=(d.feed||[]).length?'none':'';
    const rows=(d.rows||[]).map(function(p,i){p._r=i+1;return p;})
      .filter(function(p){return !qf||String(p.n).toLowerCase().indexOf(qf)>=0;});
    const medals=['🥇','🥈','🥉'];
    document.querySelector('#t tbody').innerHTML=rows.slice(0,100).map(function(p){
      return '<tr'+(qf&&String(p.n).toLowerCase()===qf?' class="me"':'')+'>'
        +'<td class="rank">'+(p._r<=3?'<span class="medal">'+medals[p._r-1]+'</span>':p._r)+'</td>'
        +'<td><b>'+esc(p.n)+'</b>'+(p.bust?' <span class="bust">파산</span>':'')+'</td>'
        +'<td class="num pts">'+p.bal.toLocaleString()+'P</td>'
        +'<td class="num">'+p.betW+'승 '+p.betL+'패</td><td class="hidem"></td></tr>';}).join('');
    document.getElementById('noRows').style.display=(d.rows||[]).length?'none':'';
    document.getElementById('cnt').textContent=(d.rows||[]).length?'· 참여 '+d.entries+'명':'';
    document.querySelector('#r tbody').innerHTML=(d.rounds||[]).map(function(x){
      const wn=x.winner==='a'?x.a:x.b;
      return '<tr><td>'+esc(x.a)+' <span class="small">vs</span> '+esc(x.b)+'</td>'
        +'<td class="st">'+(x.refund?'환불':esc(wn)+' 승')+'</td>'
        +'<td class="num">'+(x.refund?'-':x.odds.toFixed(2)+'배')+'</td>'
        +'<td class="num">'+(x.poolA+x.poolB).toLocaleString()+'</td>'
        +'<td class="num">'+x.hit+'/'+x.bets+'</td></tr>';}).join('');
    document.getElementById('noRounds').style.display=(d.rounds||[]).length?'none':'';
  }else{
    lc.style.display='none';
    document.getElementById('feed').innerHTML='';
    document.getElementById('noFeed').style.display='';
    document.querySelector('#t tbody').innerHTML='';
    document.getElementById('noRows').style.display='';
    document.querySelector('#r tbody').innerHTML='';
    document.getElementById('noRounds').style.display='';
    document.getElementById('cnt').textContent='';
  }
  const qs=(document.getElementById('qs').value||'').trim().toLowerCase();
  const sp=((data.season||{}).players||[]).map(function(p,i){p._r=i+1;return p;})
    .filter(function(p){return !qs||String(p.n).toLowerCase().indexOf(qs)>=0;});
  document.querySelector('#ts tbody').innerHTML=sp.slice(0,100).map(function(p){
    return '<tr'+(qs&&String(p.n).toLowerCase()===qs?' class="me"':'')+'>'
      +'<td class="rank">'+p._r+'</td><td><b>'+esc(p.n)+'</b></td>'
      +'<td class="num">'+(p.champ?'👑 '+p.champ:'-')+'</td>'
      +'<td class="num">'+p.rate+'% <span class="small">('+p.betW+'승'+p.betL+'패)</span></td>'
      +'<td class="num pts">'+p.totalFinal.toLocaleString()+'</td>'
      +'<td class="num hidem">'+p.bestBal.toLocaleString()+'</td>'
      +'<td class="num hidem">'+p.days+'</td></tr>';}).join('');
  document.getElementById('noSeason').style.display=sp.length?'none':'';
  document.getElementById('daysList').innerHTML=(((data.season||{}).days)||[]).map(function(dd){
    return '<div>'+esc(dd.date)+' — 👑 <b>'+esc((dd.champ||{}).n||'')+'</b> '
      +(((dd.champ||{}).bal)||0).toLocaleString()+'P <span class="small">(참여 '+dd.entries+'명)</span></div>';
  }).join('')||'<div class="small">아직 없음</div>';
  document.getElementById('upd').textContent=new Date().toTimeString().slice(0,8)+' 갱신';
}
async function load(){
  try{data=await (await fetch('admin/prize_api.php?act=toto_public')).json();paint();}
  catch(e){document.getElementById('upd').textContent='불러오기 실패 — 잠시 후 다시';}
}
load();setInterval(load,8000);
</script></body></html>
