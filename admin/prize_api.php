<?php
// 상품 추첨 저장소 API — 로그인한 관리자만 쓸 수 있습니다.
declare(strict_types=1);
require __DIR__ . '/auth.php';
admin_boot();

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


// ── 숲 쪽지 서버 발송 헬퍼 ────────────────────────────────────
// SOOP 은 자기 도메인 밖 요청의 응답을 막아 브라우저가 직접 못 보냅니다.
// talent 로그인 쿠키를 한 번 등록해 두고, 이 서버가 대신 POST 합니다.
const NOTE_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    . '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36';

function note_write(string $cookie, string $to, string $content): array
{
    // 실제 전송은 note_api.php 로 갑니다 (작성 폼 action 은 ?page=write 이지만
    // doWrite 가 note_api.php 로 POST 합니다 — 실측 2026-08-21).
    // recv_id·txt_to 둘 다 받는 아이디, szWork=WRITE.
    $ch = curl_init('https://note.sooplive.com/api/note_api.php');
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => http_build_query([
            'szWork' => 'WRITE', 'recv_id' => $to, 'txt_to' => $to,
            'file_key' => '', 'file_size' => '', 'content' => $content]),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 15,
        CURLOPT_ENCODING => '',
        CURLOPT_HTTPHEADER => [
            'User-Agent: ' . NOTE_UA,
            'Origin: https://note.sooplive.com',
            'Referer: https://note.sooplive.com/app/index.php?page=write',
            'X-Requested-With: XMLHttpRequest',
            'Cookie: ' . $cookie],
    ]);
    $res = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err = curl_error($ch);
    curl_close($ch);
    if ($res === false || $code === 0) {
        return ['ok' => false, 'reason' => 'SOOP 접속 실패: ' . $err, 'http' => $code];
    }
    // 로그인 풀림
    if ((stripos($res, 'login') !== false && stripos($res, 'member') !== false)
        || mb_strpos($res, '로그인이 필요') !== false) {
        return ['ok' => false, 'expired' => true, 'http' => $code,
                'reason' => 'talent 세션이 만료됐습니다 — 세션을 다시 등록하세요'];
    }
    // note_api.php 는 JSON 을 돌려줍니다:
    //   {"RESULT":1,"user_nick":"...","all_reject":false,"sender_balck":false,"MSG":"..."}
    $j = json_decode(trim($res), true);
    if (is_array($j) && array_key_exists('RESULT', $j)) {
        $rok = ((string)$j['RESULT'] === '1' || $j['RESULT'] === true);
        $msg = (string)($j['MSG'] ?? $j['MESSAGE'] ?? $j['message'] ?? '');
        // 상대가 쪽지 수신을 막았으면 도달하지 않습니다
        if (!empty($j['all_reject']) || !empty($j['sender_balck'])) {
            return ['ok' => false, 'http' => $code,
                    'reason' => '상대가 쪽지 수신을 거부한 계정입니다',
                    'nick' => (string)($j['user_nick'] ?? '')];
        }
        return ['ok' => $rok, 'http' => $code,
                'reason' => $rok ? '' : ($msg ?: '전송에 실패했습니다'),
                'nick' => (string)($j['user_nick'] ?? '')];
    }
    // JSON 이 아니면(로그인 페이지·오류 HTML 등) 실패로 봅니다 —
    // 성공은 반드시 RESULT:1 로만 인정합니다 (거짓 성공 방지).
    return ['ok' => false, 'http' => $code,
            'reason' => '예상치 못한 응답 (세션 만료이거나 SOOP 변경일 수 있음)',
            'snippet' => mb_substr(trim(preg_replace('/\s+/', ' ',
                strip_tags((string)$res))), 0, 140)];
}

function note_check(string $cookie): array
{
    $ch = curl_init('https://note.sooplive.com/app/index.php?page=recv_list');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 12, CURLOPT_ENCODING => '',
        CURLOPT_HTTPHEADER => ['User-Agent: ' . NOTE_UA, 'Cookie: ' . $cookie]]);
    $res = (string)curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    $valid = ($code === 200
        && (mb_strpos($res, '받은 쪽지') !== false || mb_strpos($res, '쪽지함') !== false)
        && mb_strpos($res, '로그인이 필요') === false);
    return ['ok' => true, 'valid' => $valid,
            'reason' => $valid ? '세션이 유효합니다 ✓'
                               : '로그인 세션이 아닙니다 — 쿠키를 다시 확인하세요'];
}

pz_boot();
$act = $_GET['act'] ?? '';
$body = [];
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $body = json_decode((string)file_get_contents('php://input'), true) ?: [];
    $act = $body['act'] ?? $act;
}

// 로그인 확인 — 공개 리더보드 읽기(predict_public)만 로그인 없이 허용
if (!admin_logged_in() && $act !== 'predict_public') {
    http_response_code(401);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['error' => '로그인이 필요합니다']);
    exit;
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

// ── 승부예측 — 채팅으로 세트 승자 맞히기, 맞히면 포인트 ──────────
// predict_cur.json     진행 중 라운드 {id,a,b,state,startedAt,votes:{계정:{p,n,at}}}
// predict_points.json  누적 포인트 {players:{계정:{n,pts,w,l,st,best}}}
// predict_rounds.json  끝난 라운드 요약 (최근 60)
if ($act === 'predict_get') {
    out(['cur' => jread('predict_cur.json', null),
         'rounds' => jread('predict_rounds.json', ['list' => []])]);
}
if ($act === 'predict_save') {
    jwrite('predict_cur.json', $body['cur'] ?? null);
    out(['ok' => true]);
}
if ($act === 'predict_cancel') {
    jwrite('predict_cur.json', null);
    out(['ok' => true, 'cancelled' => true]);
}
if ($act === 'predict_settle') {
    // 정산은 서버가 합니다. 서버에 진행 라운드가 있고 같은 라운드일 때만
    // 처리해서, 버튼을 두 번 눌러도 포인트가 두 번 들어가지 않습니다.
    $srv = jread('predict_cur.json', null);
    $cur = $body['cur'] ?? $srv;
    if (!$srv || !$cur || (string)($srv['id'] ?? '') !== (string)($cur['id'] ?? '')) {
        out(['error' => '정산할 예측이 없습니다 (이미 정산됐을 수 있어요)'], 400);
    }
    $winner = (($body['winner'] ?? 'a') === 'b') ? 'b' : 'a';
    $votes = (array)($cur['votes'] ?? []);
    $led = jread('predict_points.json', ['players' => []]);
    $pl = (array)($led['players'] ?? []);
    $hit = 0; $ca = 0; $cb = 0; $top = [];
    foreach ($votes as $vid => $v) {
        $v = (array)$v;
        $pick = (($v['p'] ?? 'a') === 'b') ? 'b' : 'a';
        if ($pick === 'a') $ca++; else $cb++;
        $p = (array)($pl[$vid] ?? ['n' => '', 'pts' => 0, 'w' => 0, 'l' => 0, 'st' => 0, 'best' => 0]);
        if (($v['n'] ?? '') !== '') $p['n'] = $v['n'];
        if ($pick === $winner) {
            $hit++;
            $p['st'] = (int)($p['st'] ?? 0) + 1;
            $bonus = min(((int)$p['st'] - 1) * 20, 100);    // 연승 보너스 +20씩, 최대 +100
            $gain = 100 + $bonus;
            $p['pts'] = (int)($p['pts'] ?? 0) + $gain;
            $p['w'] = (int)($p['w'] ?? 0) + 1;
            if ((int)$p['st'] > (int)($p['best'] ?? 0)) $p['best'] = (int)$p['st'];
            $top[] = ['n' => (string)$p['n'], 'gain' => $gain, 'st' => (int)$p['st']];
        } else {
            $p['l'] = (int)($p['l'] ?? 0) + 1;
            $p['st'] = 0;
        }
        $pl[$vid] = $p;
    }
    usort($top, function ($x, $y) { return $y['gain'] <=> $x['gain']; });
    $led['players'] = $pl;
    $led['updatedAt'] = date('Y-m-d H:i:s');
    jwrite('predict_points.json', $led);
    $rounds = jread('predict_rounds.json', ['list' => []]);
    array_unshift($rounds['list'], [
        'id' => (string)($cur['id'] ?? ''), 'a' => (string)($cur['a'] ?? ''),
        'b' => (string)($cur['b'] ?? ''), 'winner' => $winner,
        'ca' => $ca, 'cb' => $cb, 'hit' => $hit, 'at' => date('Y-m-d H:i')]);
    $rounds['list'] = array_slice($rounds['list'], 0, 60);
    jwrite('predict_rounds.json', $rounds);
    jwrite('predict_cur.json', null);
    out(['ok' => true, 'hit' => $hit, 'total' => $ca + $cb, 'ca' => $ca, 'cb' => $cb,
         'top' => array_slice($top, 0, 5)]);
}
if ($act === 'predict_public') {
    // 공개 리더보드 — 읽기 전용, 닉네임만 내보냅니다 (SOOP 계정은 비공개)
    $led = jread('predict_points.json', ['players' => []]);
    $rows = [];
    foreach ((array)($led['players'] ?? []) as $pid => $p) {
        $p = (array)$p;
        $rows[] = ['n' => (string)($p['n'] ?? ''), 'pts' => (int)($p['pts'] ?? 0),
                   'w' => (int)($p['w'] ?? 0), 'l' => (int)($p['l'] ?? 0),
                   'st' => (int)($p['st'] ?? 0), 'best' => (int)($p['best'] ?? 0)];
    }
    usort($rows, function ($x, $y) { return $y['pts'] <=> $x['pts']; });
    $cur = jread('predict_cur.json', null);
    $curPub = null;
    if (is_array($cur)) {
        $ca = 0; $cb = 0;
        foreach ((array)($cur['votes'] ?? []) as $v) {
            $v = (array)$v;
            if ((($v['p'] ?? 'a')) === 'b') $cb++; else $ca++;
        }
        $curPub = ['a' => (string)($cur['a'] ?? ''), 'b' => (string)($cur['b'] ?? ''),
                   'state' => (string)($cur['state'] ?? ''), 'ca' => $ca, 'cb' => $cb];
    }
    $rl = jread('predict_rounds.json', ['list' => []]);
    out(['players' => array_slice($rows, 0, 200),
         'rounds' => array_slice((array)($rl['list'] ?? []), 0, 20),
         'cur' => $curPub, 'updatedAt' => (string)($led['updatedAt'] ?? '')]);
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

// ── 숲 쪽지 서버 발송 ────────────────────────────────────────
if ($act === 'note_session_set') {
    $cookie = trim((string)($body['cookie'] ?? ''));
    // 여러 줄로 붙여넣어도 한 줄로 정리
    $cookie = preg_replace('/\s*[\r\n]+\s*/', ' ', $cookie);
    jwrite('note_session.json', ['cookie' => $cookie, 'savedAt' => date('Y-m-d H:i')]);
    out($cookie === '' ? ['ok' => true, 'valid' => false, 'reason' => '쿠키가 비었습니다']
                       : note_check($cookie));
}
if ($act === 'note_session_status') {
    $sSess = jread('note_session.json', ['cookie' => '']);
    out(['has' => !empty($sSess['cookie']), 'savedAt' => $sSess['savedAt'] ?? '']);
}
if ($act === 'note_session_check') {
    $sSess = jread('note_session.json', ['cookie' => '']);
    out(empty($sSess['cookie']) ? ['ok' => true, 'valid' => false, 'reason' => '세션 미등록']
                                : note_check((string)$sSess['cookie']));
}
if ($act === 'note_send') {
    $sSess = jread('note_session.json', ['cookie' => '']);
    $cookie = (string)($sSess['cookie'] ?? '');
    if ($cookie === '') {
        out(['ok' => false, 'reason' => '세션이 없습니다 — 먼저 talent 세션을 등록하세요']);
    }
    $to = preg_replace('/[^A-Za-z0-9_]/', '', (string)($body['to'] ?? ''));
    $content = trim((string)($body['content'] ?? ''));
    if ($to === '' || $content === '') {
        out(['ok' => false, 'reason' => '받는사람 또는 내용이 비었습니다']);
    }
    out(note_write($cookie, $to, mb_substr($content, 0, 5000)));
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
