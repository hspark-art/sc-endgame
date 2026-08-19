# -*- coding: utf-8 -*-
"""상품 추첨 — 웹 판 (관리자 로그인 뒤 PHP 페이지 3개).

  admin/prize.php          관제 — 브라우저가 SOOP 채팅에 직접 붙습니다
  admin/prize_overlay.php  자막 — 방송 화면에 띄우는 창 (핀볼·당첨 배너)
  admin/prize_api.php      저장 — 상품·당첨자·자막 상태를 서버 파일로

왜 이렇게 나뉘나
  채팅 수신은 실시간이라 서버(공유호스팅 PHP)가 오래 붙어 있을 수 없습니다.
  대신 '관제 화면을 열어 둔 브라우저'가 시청자처럼 채팅 서버에 붙습니다.
  관제 창을 켜 둔 동안만 집계가 돌고, 45초마다 서버에 눈금을 남깁니다.

데이터는 서버의 admin/pz/ 에 쌓이고, 그 폴더는 .htaccess 로 바깥에서
직접 내려받지 못하게 막습니다 (시청자 닉네임 보호).
"""

PRIZE_API = r'''<?php
// 상품 추첨 저장소 API — 로그인한 관리자만 쓸 수 있습니다.
declare(strict_types=1);
require __DIR__ . '/auth.php';
admin_boot();
if (!admin_logged_in()) {
    http_response_code(401);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['error' => '로그인이 필요합니다']);
    exit;
}

const PZ = __DIR__ . '/pz';

function pz_boot(): void
{
    if (!is_dir(PZ)) {
        mkdir(PZ, 0755, true);
    }
    $ht = PZ . '/.htaccess';
    if (!file_exists($ht)) {                       // 폴더 직접 접근 차단
        file_put_contents($ht, "Require all denied\nDeny from all\n");
    }
    if (!is_dir(PZ . '/img')) {
        mkdir(PZ . '/img', 0755, true);
    }
}

function jread(string $name, $default)
{
    $p = PZ . '/' . $name;
    if (!file_exists($p)) {
        return $default;
    }
    $j = json_decode((string)file_get_contents($p), true);
    return $j === null ? $default : $j;
}

function jwrite(string $name, $doc): void
{
    file_put_contents(PZ . '/' . $name,
        json_encode($doc, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT),
        LOCK_EX);
}

function out($doc, int $code = 200): void
{
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($doc, JSON_UNESCAPED_UNICODE);
    exit;
}

pz_boot();
$act = $_GET['act'] ?? '';
$body = [];
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $body = json_decode((string)file_get_contents('php://input'), true) ?: [];
    $act = $body['act'] ?? $act;
}

// ── 방송 정보 (SOOP) — 브라우저는 CORS 로 막혀서 서버가 대신 물어봅니다 ──
if ($act === 'live') {
    // 기본은 우리 채널(talent). 시험용으로 ?bj=다른아이디 를 받을 수 있습니다.
    $bj = preg_replace('/[^a-z0-9_]/', '', strtolower((string)($_GET['bj'] ?? 'talent')));
    if ($bj === '') { $bj = 'talent'; }
    $ch = curl_init('https://live.sooplive.com/afreeca/player_live_api.php?bjid=' . $bj);
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => http_build_query([
            'bid' => $bj, 'type' => 'live', 'confirm_adult' => 'false',
            'player_type' => 'html5', 'mode' => 'landing', 'from_api' => '0',
            'pwd' => '', 'stream_type' => 'common', 'quality' => 'HD']),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 12,
        CURLOPT_HTTPHEADER => ['User-Agent: Mozilla/5.0'],
    ]);
    $res = curl_exec($ch);
    if ($res === false) {
        out(['error' => 'SOOP 접속 실패: ' . curl_error($ch)], 502);
    }
    $j = json_decode($res, true);
    out($j['CHANNEL'] ?? ['RESULT' => 0]);
}

// ── 상태 묶음 ──
if ($act === 'state') {
    out([
        'prizes' => jread('prizes.json', ['items' => []]),
        'winners' => jread('winners.json', ['list' => []]),
        'settings' => jread('settings.json', new stdClass()),
        'overlay' => jread('overlay.json', ['seq' => 0, 'kind' => 'none']),
    ]);
}
if ($act === 'overlay') {
    out(jread('overlay.json', ['seq' => 0, 'kind' => 'none']));
}
if ($act === 'overlay_set') {
    $ov = $body['overlay'] ?? [];
    $cur = jread('overlay.json', ['seq' => 0]);
    $ov['seq'] = (int)($cur['seq'] ?? 0) + 1;
    jwrite('overlay.json', $ov);
    out(['ok' => true, 'seq' => $ov['seq']]);
}

// ── 당첨자 장부 ──
if ($act === 'pick') {
    $nick = trim((string)($body['nick'] ?? ''));
    if ($nick === '') {
        out(['error' => '닉네임이 없습니다'], 400);
    }
    $w = jread('winners.json', ['list' => []]);
    $w['list'][] = [
        'id' => uniqid('w'),
        'date' => $body['date'] ?? date('Y-m-d'),
        'nick' => $nick,
        'prize' => (string)($body['prize'] ?? ''),
        'how' => (string)($body['how'] ?? '지명'),
        'at' => date('H:i'),
    ];
    jwrite('winners.json', $w);
    out(['ok' => true]);
}
if ($act === 'winner_del') {
    $w = jread('winners.json', ['list' => []]);
    $w['list'] = array_values(array_filter($w['list'],
        fn($x) => ($x['id'] ?? '') !== ($body['id'] ?? '-')));
    jwrite('winners.json', $w);
    out(['ok' => true]);
}

// ── 상품 ──
if ($act === 'prize_add') {
    $name = trim((string)($body['name'] ?? ''));
    if ($name === '') {
        out(['error' => '상품 이름이 없습니다'], 400);
    }
    $id = uniqid('p');
    $photo = '';
    if (!empty($body['photo']) && preg_match('/^data:image\/(\w+);base64,(.+)$/s',
            $body['photo'], $m)) {
        $ext = $m[1] === 'jpeg' ? 'jpg' : preg_replace('/[^a-z0-9]/', '', $m[1]);
        $raw = base64_decode($m[2]);
        if ($raw !== false && strlen($raw) < 8 * 1024 * 1024) {
            file_put_contents(PZ . '/img/' . $id . '.' . $ext, $raw);
            $photo = 'prize_api.php?act=img&f=' . $id . '.' . $ext;
        }
    }
    $p = jread('prizes.json', ['items' => []]);
    $p['items'][] = ['id' => $id, 'name' => $name,
                     'note' => (string)($body['note'] ?? ''), 'photo' => $photo];
    jwrite('prizes.json', $p);
    out(['ok' => true]);
}
if ($act === 'prize_del') {
    $p = jread('prizes.json', ['items' => []]);
    $p['items'] = array_values(array_filter($p['items'],
        fn($x) => ($x['id'] ?? '') !== ($body['id'] ?? '-')));
    jwrite('prizes.json', $p);
    out(['ok' => true]);
}
if ($act === 'img') {
    $f = basename((string)($_GET['f'] ?? ''));
    $p = PZ . '/img/' . $f;
    if ($f === '' || !file_exists($p)) {
        out(['error' => 'no image'], 404);
    }
    $ext = strtolower(pathinfo($p, PATHINFO_EXTENSION));
    header('Content-Type: ' . ($ext === 'png' ? 'image/png'
        : ($ext === 'webp' ? 'image/webp' : 'image/jpeg')));
    header('Cache-Control: private, max-age=3600');
    readfile($p);
    exit;
}

// ── 설정 ──
if ($act === 'settings_set') {
    jwrite('settings.json', $body['settings'] ?? new stdClass());
    out(['ok' => true]);
}

// ── 방송별 활약 눈금 (관제 창이 45초마다 남깁니다) ──
if ($act === 'stats_save') {
    $date = preg_replace('/[^0-9-]/', '', (string)($body['date'] ?? date('Y-m-d')));
    jwrite('stats-' . $date . '.json', [
        'date' => $date,
        'title' => (string)($body['title'] ?? ''),
        'savedAt' => date('H:i:s'),
        'users' => $body['users'] ?? new stdClass(),
        'rawUnknown' => array_slice($body['rawUnknown'] ?? [], -200),
    ]);
    out(['ok' => true]);
}
if ($act === 'stats_list') {
    $rows = [];
    foreach (glob(PZ . '/stats-*.json') ?: [] as $f) {
        $j = json_decode((string)file_get_contents($f), true) ?: [];
        $u = $j['users'] ?? [];
        $chats = 0; $bal = 0;
        foreach ($u as $x) { $chats += $x['c'] ?? 0; $bal += $x['b'] ?? 0; }
        $rows[] = ['date' => $j['date'] ?? basename($f),
                   'title' => $j['title'] ?? '',
                   'users' => count($u), 'chats' => $chats, 'balloons' => $bal];
    }
    usort($rows, fn($a, $b) => strcmp($b['date'], $a['date']));
    out(['list' => $rows]);
}
if ($act === 'stats_get') {
    $date = preg_replace('/[^0-9-]/', '', (string)($_GET['date'] ?? ''));
    out(jread('stats-' . $date . '.json', ['users' => new stdClass()]));
}

out(['error' => '모르는 요청: ' . $act], 404);
'''


# ── 관제 화면 ────────────────────────────────────────────────

def prize_page():
    return r'''<?php require __DIR__ . '/auth.php'; admin_require_login(); ?>
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
<div class="scroll"><table id="users"><thead><tr><th>닉네임</th>
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
<button onclick="manualPick()">지명 → 자막 내보내기</button>
<button class="gray" onclick="plinko()">🎯 핀볼 추첨</button>
<button class="gray" onclick="clearOverlay()">자막 지우기</button></div>
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
<div class="ct">확률 설정</div>
<div class="row hint">채팅 <input id="sChatFull" style="width:56px"> 개에
+<input id="sChatMax" style="width:50px"> · 별풍선
<input id="sBalFull" style="width:64px"> 개에 +<input id="sBalMax" style="width:50px">
<label><input type="checkbox" id="sExcl"> 이전 당첨자 제외</label>
<button class="gray" onclick="saveSettings()">저장</button></div>
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
let settings={chatFull:50,chatBonusMax:0.3,balloonFull:1000,balloonBonusMax:0.5,excludeWinners:false};

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
  if(ev.t==='chat'){bump(ev.nick,'c');recent.push(ev);}
  else if(ev.t==='balloon'){bump(ev.nick,'b',ev.count);recent.push(ev);}
  recent.splice(0,Math.max(0,recent.length-200));
}
/* SOOP 채팅 프로토콜 — 시청자용 접속과 같은 방식입니다 */
function pkt(svc,body){
  const b=new TextEncoder().encode(body);
  const head=new TextEncoder().encode('\x1b\t'+String(svc).padStart(4,'0')
    +String(b.length).padStart(6,'0')+'00');
  const u=new Uint8Array(head.length+b.length);u.set(head);u.set(b,head.length);return u;
}
function parseBalloon(f){
  for(const i of [4,5,3]){
    const v=f[i]??'';
    if(/^\d+$/.test(v)&&+v>0){
      const nick=cleanNick(f[i-1]??'');
      if(nick)return{t:'balloon',nick,count:+v};
      break;
    }
  }
  return null;
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
    }else if(svc===18||svc===33){
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
  const n=norm(nick),h=ST.winners.list.filter(w=>norm(w.nick)===n);
  return[h.length,h.length?h[h.length-1].date:''];
}
function pickWeighted(){
  let pool=Object.keys(users).filter(n=>users[n].c+users[n].b>0);
  if(settings.excludeWinners)pool=pool.filter(n=>winCount(n)[0]===0);
  if(!pool.length)return null;
  const ws2=pool.map(weight), tot=ws2.reduce((a,b)=>a+b,0);
  let r=Math.random()*tot;
  for(let i=0;i<pool.length;i++){r-=ws2[i];if(r<=0)return pool[i];}
  return pool[pool.length-1];
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
  await api('pick',{nick,prize:pz.name||'',how:'지명'});
  await api('overlay_set',{overlay:{kind:'winner',nick,prize:pz.name||'',
    photo:pz.photo||'',how:'지명'}});
  refresh();
}
async function plinko(){
  const win=pickWeighted();
  if(!win)return alert('추첨할 시청자가 없습니다 (채팅한 사람이 있어야 합니다)');
  const others=Object.keys(users).filter(n=>n!==win&&users[n].c+users[n].b>0);
  others.sort(()=>Math.random()-.5);
  const slots=others.slice(0,8).concat([win]).sort(()=>Math.random()-.5);
  const pz=prizeOf(document.getElementById('prizeSel').value)||{};
  await api('pick',{nick:win,prize:pz.name||'',how:'핀볼'});
  await api('overlay_set',{overlay:{kind:'plinko',winner:win,slots,
    prize:pz.name||'',photo:pz.photo||''}});
  refresh();
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
  settings={chatFull:+document.getElementById('sChatFull').value||50,
    chatBonusMax:+document.getElementById('sChatMax').value||0.3,
    balloonFull:+document.getElementById('sBalFull').value||1000,
    balloonBonusMax:+document.getElementById('sBalMax').value||0.5,
    excludeWinners:document.getElementById('sExcl').checked};
  await api('settings_set',{settings});
}
function pickThis(n){document.getElementById('pickNick').value=n;dupCheck()}
function dupCheck(){
  const n=document.getElementById('pickNick').value.trim();
  const [cnt,last]=winCount(n);
  document.getElementById('dupwarn').innerHTML=!n?'':cnt
    ?'<span class="warn">⚠ 이미 '+cnt+'회 당첨 (마지막 '+esc(last)+')</span>'
    :'<span class="ok">✓ 당첨 기록 없음</span>';
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
    ['sBalFull',settings.balloonFull],['sBalMax',settings.balloonBonusMax]]){
    const el=document.getElementById(id);
    if(document.activeElement!==el)el.value=v;
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
  document.getElementById('chat').innerHTML=recent.slice().reverse().slice(0,60).map(e=>
    e.t==='balloon'
    ?'<div class="chatline">🎈 <b>'+esc(e.nick)+'</b> <span class="balloon">별풍선 '
      +e.count+'개</span> <span class="pill">'+e.at+'</span></div>'
    :'<div class="chatline"><b>'+esc(e.nick)+'</b> '+esc(e.msg)+'</div>').join('');
  const rows=Object.entries(users).map(([nick,u])=>({nick,c:u.c,b:u.b,
    w:weight(nick),wins:winCount(nick)[0]}));
  rows.sort((a,b)=>b.b-a.b||b.c-a.c);
  document.querySelector('#users tbody').innerHTML=rows.slice(0,200).map(u=>
    '<tr><td>'+esc(u.nick)+'</td><td class="num">'+u.c+'</td>'+
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
'''


# ── 자막 창 ──────────────────────────────────────────────────


# ── 방송 장면 (자막 아닌 '한 장면') ──────────────────────────
#
# 방송 위에 얹는 투명 자막이 아니라, 그 자체로 방송에 보여 주는 한 장면입니다.
#   · 꽉 찬 배경 + 상품 사진 + 당첨자 + 핀볼이 페이지 안에서 다 보입니다
#   · 왼쪽 아래에 '중계진' 자리(PIP) 를 비워 둡니다 — 그 칸을 눌러
#     테두리 / 초록(크로마키) / 카메라 / 없음 으로 바꿉니다

def prize_overlay():
    return r'''<?php require __DIR__ . '/auth.php'; admin_require_login(); ?>
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
</style></head><body>
<div id="scene"></div>
<div id="hint">화면 클릭 = 배경 초록/어둠 · PIP 클릭 = 중계진 자리 바꾸기</div>
<div id="title">&#127873; <b>&#45001;&#51109;&#51204;</b> &#49345;&#54408; &#52628;&#52628;&#52628;</div>
<div id="stage">
  <div class="box" id="idleBox"><div class="idle" id="idleText"></div></div>
  <div class="box" id="prizeBox"><div class="plabel" id="prizeLbl"></div>
    <img class="pimg" id="prizeImg" hidden><div class="pname" id="prizeName"></div></div>
  <div class="box" id="winBox"><div class="wcap" id="winCap"></div>
    <img class="pimg" id="winImg" hidden style="max-height:300px">
    <div class="wnick" id="winNick"></div><div class="wprize" id="winPrize"></div></div>
  <canvas id="board" width="1200" height="820"></canvas>
</div>
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
let seq=-1, anim=null;
function show(id){['idleBox','prizeBox','winBox'].forEach(function(b){
  document.getElementById(b).classList.toggle('show',b===id);});
  document.getElementById('board').classList.remove('show');
  if(anim){cancelAnimationFrame(anim);anim=null;}
}
function idle(){show('idleBox');}
function prize(st){
  show('prizeBox');
  const im=document.getElementById('prizeImg');
  if(st.photo){im.src=st.photo;im.hidden=false;}else im.hidden=true;
  document.getElementById('prizeName').textContent=st.prize||'';
}
function winner(st){
  show('winBox');
  document.getElementById('winCap').textContent=st.how==='핀볼'?'🎯 핀볼 추첨 당첨':'🎉 축하합니다';
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
  cv.classList.add('show');
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
async function poll(){
  try{
    const st=await (await fetch('prize_api.php?act=overlay')).json();
    if(st.seq!==seq){
      seq=st.seq;
      if(st.kind==='winner')winner(st);
      else if(st.kind==='plinko')plinko(st);
      else if(st.kind==='prize')prize(st);
      else idle();
    }
  }catch(e){}
  setTimeout(poll,900);
}
idle();poll();
</script></body></html>
'''
