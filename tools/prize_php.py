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
        'session' => jread('session.json', ['on' => false, 'date' => '', 'startedAt' => '']),
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
        'sid' => (string)($body['sid'] ?? ''),   // SOOP 아이디 (있으면 정확한 대조 키)
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
if ($act === 'winner_update') {
    $w = jread('winners.json', ['list' => []]);
    foreach ($w['list'] as &$x) {
        if (($x['id'] ?? '') === ($body['id'] ?? '')) {
            foreach (['date', 'nick', 'sid', 'prize', 'how', 'sent', 'memo'] as $k) {
                if (array_key_exists($k, $body)) { $x[$k] = (string)$body[$k]; }
            }
            break;
        }
    }
    unset($x);
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
if ($act === 'prize_move') {
    $p = jread('prizes.json', ['items' => []]);
    $items = $p['items'];
    $i = -1;
    foreach ($items as $k => $x) { if (($x['id'] ?? '') === ($body['id'] ?? '')) { $i = $k; break; } }
    $j = $i + ((($body['dir'] ?? '') === 'up') ? -1 : 1);
    if ($i >= 0 && $j >= 0 && $j < count($items)) {
        $tmp = $items[$i]; $items[$i] = $items[$j]; $items[$j] = $tmp;
        $p['items'] = $items; jwrite('prizes.json', $p);
    }
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
        'uid' => $body['uid'] ?? new stdClass(),
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

// ── 집계 켜짐/꺼짐 (스타트·종료 버튼 상태 — 창을 껐다 켜도 이어받게) ──
if ($act === 'session_set') {
    $s = $body['session'] ?? [];
    jwrite('session.json', [
        'on' => !empty($s['on']),
        'date' => preg_replace('/[^0-9-]/', '', (string)($s['date'] ?? '')),
        'startedAt' => (string)($s['startedAt'] ?? ''),
    ]);
    out(['ok' => true]);
}

// ── 채팅 로그 — 방송 날짜별 파일에 이어 붙입니다 (초기화 전까지 보존) ──
if ($act === 'chat_log') {
    $date = preg_replace('/[^0-9-]/', '', (string)($body['date'] ?? date('Y-m-d')));
    $lines = array_slice(is_array($body['lines'] ?? null) ? $body['lines'] : [], 0, 2000);
    if ($lines && $date !== '') {
        $txt = '';
        foreach ($lines as $l) {
            $txt .= json_encode($l, JSON_UNESCAPED_UNICODE) . "\n";
        }
        file_put_contents(PZ . '/chatlog-' . $date . '.jsonl', $txt, FILE_APPEND | LOCK_EX);
    }
    out(['ok' => true]);
}
if ($act === 'chat_tail') {
    $date = preg_replace('/[^0-9-]/', '', (string)($_GET['date'] ?? ''));
    $p = PZ . '/chatlog-' . $date . '.jsonl';
    $rows = [];
    if ($date !== '' && file_exists($p)) {
        $all = explode("\n", trim((string)file_get_contents($p)));
        foreach (array_slice($all, -300) as $ln) {
            $j = json_decode($ln, true);
            if ($j) { $rows[] = $j; }
        }
    }
    out(['lines' => $rows]);
}
if ($act === 'chat_clear') {
    $date = preg_replace('/[^0-9-]/', '', (string)($body['date'] ?? ''));
    if ($date !== '') { @unlink(PZ . '/chatlog-' . $date . '.jsonl'); }
    out(['ok' => true]);
}

// ── 별풍선 큰 알림(토스트) ──
if ($act === 'toast_add') {
    $t = jread('toasts.json', ['list' => []]);
    $t['list'][] = ['seq' => (int)(($t['list'][count($t['list']) - 1]['seq'] ?? 0) + 1),
                    'nick' => (string)($body['nick'] ?? ''),
                    'count' => (int)($body['count'] ?? 0), 'ts' => time()];
    $t['list'] = array_slice($t['list'], -30);
    jwrite('toasts.json', $t);
    out(['ok' => true]);
}
if ($act === 'toasts') {
    out(jread('toasts.json', ['list' => []]));
}

// ── 구글 문서 당첨자 대조 ──
if ($act === 'gdoc') {
    $st = jread('settings.json', []);
    $docId = preg_replace('/[^A-Za-z0-9_-]/', '', (string)($st['gdocId'] ?? ''));
    if ($docId === '') { out(['names' => [], 'ids' => [], 'note' => '문서 없음']); }
    $cache = jread('gdoc-cache.json', []);
    if (($cache['id'] ?? '') === $docId && (time() - ($cache['ts'] ?? 0)) < 300) {
        out($cache['data']);              // 5분 캐시
    }
    $ch = curl_init('https://docs.google.com/document/d/' . $docId . '/export?format=txt');
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 15,
        CURLOPT_FOLLOWLOCATION => true, CURLOPT_HTTPHEADER => ['User-Agent: Mozilla/5.0']]);
    $txt = curl_exec($ch);
    if ($txt === false) { out(['names' => [], 'ids' => [], 'note' => '문서 접근 실패']); }
    // '닉네임 / 아이디' 형태를 뽑습니다. 아이디는 소문자 영숫자.
    $ids = []; $names = [];
    foreach (preg_split('/
?
/', $txt) as $line) {
        if (preg_match('#^\s*([^/]{1,30})/\s*([A-Za-z0-9_]{3,30})#', $line, $m)) {
            $names[] = trim($m[1]);
            $ids[] = strtolower(trim($m[2]));
        }
    }
    $data = ['names' => array_values(array_unique($names)),
             'ids' => array_values(array_unique($ids)),
             'note' => count($ids) . '명'];
    jwrite('gdoc-cache.json', ['id' => $docId, 'ts' => time(), 'data' => $data]);
    out($data);
}

// ── 슬랙으로 요약 보내기 ──
if ($act === 'slack_report') {
    $st = jread('settings.json', []);
    $hook = (string)($st['slackWebhook'] ?? '');
    if (strpos($hook, 'hooks.slack.com') === false) {
        out(['error' => '슬랙 웹훅 주소를 설정에 먼저 넣어 주세요'], 400);
    }
    $text = (string)($body['text'] ?? '끝장전 상품 추첨 요약');
    $payload = json_encode(['text' => $text], JSON_UNESCAPED_UNICODE);
    $ch = curl_init($hook);
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_POSTFIELDS => $payload,
        CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 12,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json']]);
    $res = curl_exec($ch);
    out(['ok' => trim((string)$res) === 'ok', 'resp' => substr((string)$res, 0, 60)]);
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
.chatline{padding:3px 0;border-bottom:1px solid #12161e;font-size:13px;
overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
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
<div class="grid">

<div class="card"><div class="ct">실시간 채팅 <span class="n" id="totline"></span>
<button class="gray" style="margin-left:auto;padding:4px 10px" onclick="clearChat()" title="화면만 비웁니다 — 저장된 로그는 그대로 남습니다">채팅 지우기</button></div>
<div class="scroll" id="chat" style="max-height:560px"></div></div>

<div class="card"><div class="ct">시청자 활약 <span class="n">별풍선·채팅 순</span>
<button class="gray" style="margin-left:auto;padding:4px 10px" onclick="clearStats()">집계 초기화</button></div>
<div class="scroll"><table id="users"><thead><tr><th class="num">#</th><th>닉네임</th>
<th>SOOP계정</th><th class="num">채팅</th><th class="num">별풍선</th><th class="num">확률↑</th>
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
<div class="ct">당첨자 시트 <span class="n" id="wcount"></span>
<a class="top" href="prize_sheet.php">전체 화면 ↗</a>
<button class="gray" style="margin-left:auto;padding:4px 10px" onclick="copyLedger()">📋 복사</button>
<button class="gray" style="padding:4px 10px" onclick="downloadLedger()">⬇ CSV</button></div>
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
const IS_DEMO = location.search.includes('demo');
const IS_TEST_CH = BJ!=='talent' || IS_DEMO;   // 연습 모드도 진짜 기록에 안 섞음
const F='\x0c', users={}, recent=[], rawUnknown=[];
const sess={on:false,date:'',startedAt:''};   // 스타트/종료 상태
const logBuf=[];                              // 서버로 보낼 채팅 로그 대기줄
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
const seenBalloons=new Set();   // 재전송 별풍선 중복 방지 (메시지ID [3])
function parseBalloon(f){
  // 별풍선 svc 109 — 실측(2026-08): [3]메시지ID [4]개수 [6]보낸이ID [7]보낸이닉
  if(f.length<8)return null;
  const cnt=(f[4]||'').trim();
  if(!/^\d+$/.test(cnt)||+cnt<=0)return null;
  const mid=(f[3]||'').trim();
  if(mid&&seenBalloons.has(mid))return null;   // 이미 센 별풍선
  if(mid){seenBalloons.add(mid);
    if(seenBalloons.size>4000)seenBalloons=new Set([...seenBalloons].slice(-2000));}
  const nick=cleanNick(f[7]);
  return nick?{t:'balloon',nick,count:+cnt,id:cleanNick(f[6])}:null;
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
    slackWebhook:document.getElementById('sSlack').value.trim()});
  await api('settings_set',{settings});loadGdoc();
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
  recent.length=0;logBuf.length=0;
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
document.getElementById('pickNick').addEventListener('keydown',function(e){if(e.key==='Enter')manualPick();});

/* ── 화면 그리기 + 서버 상태 ── */
async function refresh(){
  try{ST=await (await fetch('prize_api.php?act=state')).json();}catch(e){return}
  if(ST.settings&&ST.settings.chatFull)settings=Object.assign(settings,ST.settings);
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
    '<td>'+(acc?'<span class="pill" style="font-size:11px">'+esc(acc)+'</span>'
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
  const medal=['🥇','🥈','🥉'];
  const maxAct=Math.max(1,...rows.map(u=>u.b*3+u.c));
  document.querySelector('#users tbody').innerHTML=rows.slice(0,200).map((u,i)=>{
    const pct=Math.round((u.b*3+u.c)/maxAct*100);
    return '<tr><td class="num" style="color:#8a93a6">'+(medal[i]||(i+1))+'</td>'+
    '<td><div class="actbar" style="width:'+pct+'%"></div>'+esc(u.nick)+'</td>'+
    '<td class="pill" style="font-size:11px">'+esc(uid[u.nick]||'-')+'</td><td class="num">'+u.c+'</td>'+
    '<td class="num balloon">'+(u.b||'')+'</td><td class="num">x'+u.w.toFixed(2)+
    '</td><td>'+(u.wins?'<span class="warn">'+u.wins+'회</span>':'')+'</td>'+
    '<td><button class="gray" style="padding:2px 8px" data-pick="'
    +esc(u.nick)+'">지명</button></td></tr>';}).join('');
  document.querySelectorAll('[data-pick]').forEach(b=>
    b.onclick=()=>pickThis(b.dataset.pick));
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
async function restoreSession(){
  if(IS_TEST_CH)return;
  try{
    const st=await (await fetch('prize_api.php?act=state')).json();
    const sv=(st&&st.session)||{};
    sess.on=!!sv.on;sess.date=sv.date||'';sess.startedAt=sv.startedAt||'';
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
function show(id){['idleBox','prizeBox','winBox','kingBox'].forEach(function(b){
  document.getElementById(b).classList.toggle('show',b===id);});
  document.getElementById('board').classList.remove('show');
  document.getElementById('lineup').classList.remove('show');
  if(anim){cancelAnimationFrame(anim);anim=null;}
}
let allPrizes=[];
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
      else idle();
    }
  }catch(e){}
  setTimeout(poll,900);
}
loadPrizes();setInterval(loadPrizes,30000);idle();poll();
</script></body></html>
'''


# ── 당첨자 시트 — 정리·편집·숲 쪽지 일괄 발송 ─────────────────
#
# 관제(prize.php)의 작은 장부를 전체 화면 시트로 키운 페이지입니다.
#   · 칸을 눌러 바로 고치는 표 (날짜·방식·닉네임·SOOP계정·상품·쪽지·메모)
#   · 날짜·상품·쪽지 여부로 거르고, 상품별 개수 칩으로 요약
#   · 줄을 골라 숲 쪽지 받는사람(계정 아이디)을 한 번에 복사
#     — 쪽지 문안은 구글 문서에 있던 실제 문안 3종을 그대로 넣어 둠
#   · 보낸 뒤 '보냄 처리'를 누르면 쪽지 칸에 오늘 날짜가 남음

def prize_sheet():
    return r'''<?php require __DIR__ . '/auth.php'; admin_require_login(); ?>
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
<div class="card">
 <div class="row">
  <input id="fQ" placeholder="닉네임·계정 검색" style="width:190px">
  <select id="fDate"><option value="">날짜 전체</option></select>
  <select id="fPrize"><option value="">상품 전체</option></select>
  <select id="fSent"><option value="">쪽지 전체</option>
   <option value="no">안 보낸 사람</option><option value="yes">보낸 사람</option></select>
  <span style="flex:1"></span>
  <button class="gray" onclick="addRow()">＋ 행 추가</button>
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
  <button onclick="copyIds()">① 받는사람 복사</button>
  <button onclick="copyNote()">② 내용 복사</button>
  <button class="gray" onclick="window.open('https://note.sooplive.com/','_blank','noopener')">③ 숲 쪽지함 열기 ↗</button>
  <button class="green" onclick="markSent()">✅ 선택 보냄 처리</button>
  <span class="warn" id="noteWarn"></span>
 </div>
 <div class="hint">숲 쪽지함에서 [쪽지 보내기]를 누른 뒤 — 받는사람 칸에 ①을 붙여넣고(여러 명이 쉼표로 들어갑니다),
 내용 칸에 ②를 붙여넣어 보내면 됩니다. 받는사람 수 제한에 걸리면 나눠서 보내세요.
 보낸 뒤 ✅ 를 누르면 쪽지 칸에 오늘 날짜가 남아 누구에게 보냈는지 시트에 남습니다.</div>
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
function paint(){
  const l=rows(),vis=visible();
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
async function addRow(){
  const nick=prompt('닉네임을 입력하세요');
  if(!nick||!nick.trim())return;
  await api('pick',{nick:nick.trim(),prize:'',how:'수동',date:today()});
  refresh();}
function copyLedger(){
  const vis=visible();
  const txt=vis.map(w=>[w.date||'',w.how||'',w.nick||'',w.sid||'',w.prize||'',w.sent||'',w.memo||''].join(TAB)).join(NL);
  copyToClip(['날짜','방식','닉네임','SOOP계정','상품','쪽지','메모'].join(TAB)+NL+txt,
    '보이는 '+vis.length+'줄 복사됨 ✓');}
function downloadLedger(){
  const vis=visible();
  if(!vis.length)return alert('내려받을 줄이 없습니다');
  const q=s=>'"'+String(s==null?'':s).replace(/"/g,'""')+'"';
  const lines=vis.map(w=>[q(w.date),q(w.how),q(w.nick),q(w.sid),q(w.prize),q(w.sent),q(w.memo)].join(','));
  const csv=String.fromCharCode(0xFEFF)+['날짜,방식,닉네임,SOOP계정,상품,쪽지,메모'].concat(lines).join(NL);
  const a=document.createElement('a');
  a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);
  a.download='끝장전-당첨자-'+today()+'.csv';a.click();}
refresh();
</script></body></html>
'''
