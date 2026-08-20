<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>승부예측 리더보드 — 끝장전</title><style>
*{box-sizing:border-box}body{margin:0;background:#0a0d13;color:#e8ecf3;
font-family:'Pretendard','Malgun Gothic','Apple SD Gothic Neo',sans-serif;font-size:15px}
.wrap{max-width:860px;margin:0 auto;padding:18px 14px 60px}
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
.rule{color:#aab3c5;font-size:13px;line-height:1.9}
input{background:#1b202b;color:#e8ecf3;border:1px solid #232a38;border-radius:9px;
padding:9px 12px;font-size:14px;width:100%;font-family:inherit}
table{width:100%;border-collapse:collapse;font-size:14px}
td,th{padding:8px 8px;text-align:left;border-bottom:1px solid #171c25;white-space:nowrap}
th{color:#8a93a6;font-size:11.5px}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tr.me{background:#12283f}
.rank{width:44px;color:#8a93a6;font-weight:800}
.medal{font-size:17px}
.pts{color:#ffd24a;font-weight:800}
.st{color:#4ade80;font-weight:700}
.small{font-size:12px;color:#8a93a6}
.empty{color:#8a93a6;text-align:center;padding:26px 0;line-height:1.9}
.win{color:#4ade80;font-weight:700}
@media(max-width:560px){td,th{padding:7px 5px;font-size:13px}.hidem{display:none}}
</style></head><body><div class="wrap">
<h1>🔮 끝장전 승부예측</h1>
<div class="sub">채팅으로 세트 승자를 맞히면 포인트! · <span id="upd" class="pill">불러오는 중…</span>
 · <a href="index.html">← 끝장전 기록실</a></div>

<div class="card live" id="liveCard" style="display:none">
  <div class="lt" id="liveState">🟢 지금 예측 진행 중!</div>
  <div class="vs"><span class="aName" id="lvA"></span><span id="lvACnt" class="pill"></span>
    <span style="color:#8a93a6">vs</span>
    <span id="lvBCnt" class="pill"></span><span class="bName" id="lvB"></span></div>
  <div class="bar"><div id="lvBarA" style="width:50%"></div><div></div></div>
  <div class="small">방송 채팅에 <b>선수 이름</b>을 치면 참여됩니다 (첫 입력만 인정)</div>
</div>

<div class="card">
  <div class="lt">참여 방법 · 포인트</div>
  <div class="rule">
  ① 방송에서 <b>예측 시작</b>이 뜨면, 채팅에 <b>이길 것 같은 선수 이름</b>을 치세요 (정확히 이름만!)<br>
  ② <b>첫 입력만 인정</b>됩니다 — 한번 고르면 바꿀 수 없어요<br>
  ③ 맞히면 <b class="pts">+100P</b>, 연속으로 맞히면 <b class="st">연승 보너스 +20P씩</b> (최대 +100P)</div>
</div>

<div class="card">
  <div class="lt">🏆 포인트 순위 <span class="small" id="cnt"></span></div>
  <input id="q" placeholder="내 닉네임 검색" oninput="paint()">
  <div style="overflow-x:auto;margin-top:8px"><table id="t"><thead><tr>
  <th class="rank">순위</th><th>닉네임</th><th class="num">포인트</th>
  <th class="num">적중</th><th class="num">연승</th><th class="num hidem">최고연승</th>
  </tr></thead><tbody></tbody></table></div>
  <div class="empty" id="noRows" style="display:none">아직 기록이 없습니다 — 다음 방송의 승부예측에 참여해 보세요!</div>
</div>

<div class="card">
  <div class="lt">최근 예측 결과</div>
  <div style="overflow-x:auto"><table id="r"><thead><tr>
  <th>매치</th><th>결과</th><th class="num">표</th><th class="num">적중</th><th class="hidem">시각</th>
  </tr></thead><tbody></tbody></table></div>
  <div class="empty" id="noRounds" style="display:none">아직 진행된 예측이 없습니다.</div>
</div>
<div class="small" style="text-align:center;margin-top:16px">
스타크래프트 끝장전 · <a href="index.html">기록실 보기</a></div>

<script>
let data=null;
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function paint(){
  if(!data)return;
  const q=(document.getElementById('q').value||'').trim().toLowerCase();
  const rows=(data.players||[]).map(function(p,i){p._rank=i+1;return p;})
    .filter(function(p){return !q||String(p.n).toLowerCase().indexOf(q)>=0;});
  const medals=['🥇','🥈','🥉'];
  document.querySelector('#t tbody').innerHTML=rows.slice(0,100).map(function(p){
    const acc=(p.w+p.l)?Math.round(p.w*100/(p.w+p.l)):0;
    return '<tr'+(q&&String(p.n).toLowerCase()===q?' class="me"':'')+'>'
      +'<td class="rank">'+(p._rank<=3?'<span class="medal">'+medals[p._rank-1]+'</span>':p._rank)+'</td>'
      +'<td><b>'+esc(p.n)+'</b></td>'
      +'<td class="num pts">'+p.pts.toLocaleString()+'P</td>'
      +'<td class="num">'+p.w+'/'+(p.w+p.l)+' <span class="small">('+acc+'%)</span></td>'
      +'<td class="num st">'+(p.st?p.st+'연승':'-')+'</td>'
      +'<td class="num hidem">'+(p.best||0)+'</td></tr>';
  }).join('');
  document.getElementById('noRows').style.display=(data.players||[]).length?'none':'';
  document.getElementById('cnt').textContent=(data.players||[]).length
    ?'· 참여자 '+(data.players||[]).length+'명':'';
  const rd=data.rounds||[];
  document.querySelector('#r tbody').innerHTML=rd.map(function(x){
    const tot=x.ca+x.cb, wn=x.winner==='a'?x.a:x.b;
    return '<tr><td>'+esc(x.a)+' <span class="small">vs</span> '+esc(x.b)+'</td>'
      +'<td class="win">'+esc(wn)+' 승</td>'
      +'<td class="num">'+tot+'</td>'
      +'<td class="num">'+x.hit+(tot?' <span class="small">('+Math.round(x.hit*100/tot)+'%)</span>':'')+'</td>'
      +'<td class="small hidem">'+esc(x.at||'')+'</td></tr>';
  }).join('');
  document.getElementById('noRounds').style.display=rd.length?'none':'';
  const c=data.cur, lc=document.getElementById('liveCard');
  if(c&&c.a){
    lc.style.display='';
    const tot=c.ca+c.cb, pa=tot?Math.round(c.ca*100/tot):50;
    document.getElementById('liveState').textContent=(c.state==='locked')
      ?'⏸ 예측 마감 — 결과 기다리는 중':'🟢 지금 예측 진행 중! 채팅에 선수 이름을 치세요';
    document.getElementById('lvA').textContent=c.a;
    document.getElementById('lvB').textContent=c.b;
    document.getElementById('lvACnt').textContent=c.ca+'표'+(tot?' · '+pa+'%':'');
    document.getElementById('lvBCnt').textContent=c.cb+'표'+(tot?' · '+(100-pa)+'%':'');
    document.getElementById('lvBarA').style.width=(tot?pa:50)+'%';
  }else lc.style.display='none';
  document.getElementById('upd').textContent=data.updatedAt?('갱신 '+data.updatedAt):'집계 대기 중';
}
async function load(){
  try{data=await (await fetch('admin/prize_api.php?act=predict_public')).json();paint();}
  catch(e){document.getElementById('upd').textContent='불러오기 실패 — 잠시 후 다시';}
}
load();setInterval(load,10000);
</script></body></html>
