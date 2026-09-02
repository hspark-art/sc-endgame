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
if (!admin_logged_in() && $act !== 'toto_public') {
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

// ── 승부토토 — 하루 가상 포인트 배팅 (합동배당) ──────────────────
// toto_day.json    오늘 상태 {date,open,players:{계정:{n,bal,betW,betL,bust}},round,rounds,feed}
// toto_season.json 시즌 누적 {players:{계정:{n,days,champ,betW,betL,totalFinal,bestBal}},days:[]}
// 규칙: '도전'=참여(10,000P) · '이름 금액' 첫 베팅 고정 · 배당=총풀/승자풀 ·
//       승자 없으면 전원 환불 · 파산=그날 끝 · 하루 마감 때 시즌 누적
if ($act === 'toto_get') {
    out(['day' => jread('toto_day.json', null),
         'season' => jread('toto_season.json', ['players' => [], 'days' => []])]);
}
if ($act === 'toto_save') {
    jwrite('toto_day.json', $body['day'] ?? null);
    out(['ok' => true]);
}
if ($act === 'toto_settle') {
    // 정산은 서버가 단독 수행 — 서버에 같은 라운드가 있을 때만 (이중 정산 방지)
    $day = $body['day'] ?? null;
    $srv = jread('toto_day.json', null);
    if (!$day || !$srv || !is_array($day['round'] ?? null)
        || (string)(($srv['round']['id'] ?? '')) !== (string)($day['round']['id'] ?? '')) {
        out(['error' => '정산할 베팅 라운드가 없습니다 (이미 정산됐을 수 있어요)'], 400);
    }
    $winner = (($body['winner'] ?? 'a') === 'b') ? 'b' : 'a';
    $round = (array)$day['round'];
    $bets = (array)($round['bets'] ?? []);
    $pl = (array)($day['players'] ?? []);
    $poolA = 0; $poolB = 0;
    foreach ($bets as $v) { $v = (array)$v;
        if ((($v['p'] ?? 'a')) === 'b') $poolB += (int)($v['amt'] ?? 0);
        else $poolA += (int)($v['amt'] ?? 0); }
    $total = $poolA + $poolB;
    $pw = ($winner === 'a') ? $poolA : $poolB;
    $refund = ($pw <= 0);                    // 승자 쪽에 아무도 없음 → 전원 환불
    $odds = $refund ? 0 : round($total / max(1, $pw), 2);
    $hit = 0; $top = [];
    foreach ($bets as $bid => $v) {
        $v = (array)$v; $amt = (int)($v['amt'] ?? 0);
        $pick = (($v['p'] ?? 'a') === 'b') ? 'b' : 'a';
        $p = (array)($pl[$bid] ?? ['n' => $v['n'] ?? '', 'bal' => 0, 'betW' => 0, 'betL' => 0, 'bust' => false]);
        if ($refund) { $p['bal'] = (int)$p['bal'] + $amt; }
        elseif ($pick === $winner) {
            $gain = (int)floor($amt * $total / $pw);
            $p['bal'] = (int)$p['bal'] + $gain;
            $p['betW'] = (int)($p['betW'] ?? 0) + 1; $hit++;
            $top[] = ['n' => (string)($p['n'] ?? ''), 'gain' => $gain - $amt];
        } else { $p['betL'] = (int)($p['betL'] ?? 0) + 1; }
        if ((int)$p['bal'] <= 0) { $p['bal'] = 0; $p['bust'] = true; }   // 파산 — 오늘 끝
        $pl[$bid] = $p;
    }
    usort($top, function ($x, $y) { return $y['gain'] <=> $x['gain']; });
    $day['players'] = $pl;
    $rl = (array)($day['rounds'] ?? []);
    array_unshift($rl, ['a' => (string)($round['a'] ?? ''), 'b' => (string)($round['b'] ?? ''),
        'winner' => $winner, 'poolA' => $poolA, 'poolB' => $poolB, 'odds' => $odds,
        'hit' => $hit, 'bets' => count($bets), 'refund' => $refund, 'at' => date('H:i')]);
    $day['rounds'] = array_slice($rl, 0, 40);
    $day['round'] = null;
    $fd = (array)($day['feed'] ?? []);
    $wname = ($winner === 'a') ? (string)($round['a'] ?? '') : (string)($round['b'] ?? '');
    array_unshift($fd, ['type' => 'settle', 'at' => date('H:i:s'),
        'msg' => $refund ? '⚖ 적중자 없음 — 전원 환불'
                         : ('🏆 ' . $wname . ' 승 · 배당 ' . number_format($odds, 2) . '배 · 적중 ' . $hit . '명')]);
    $day['feed'] = array_slice($fd, 0, 80);
    jwrite('toto_day.json', $day);
    out(['ok' => true, 'refund' => $refund, 'odds' => $odds, 'hit' => $hit, 'bets' => count($bets),
         'poolA' => $poolA, 'poolB' => $poolB, 'wname' => $wname, 'top' => array_slice($top, 0, 5)]);
}
if ($act === 'toto_closeday') {
    $day = $body['day'] ?? jread('toto_day.json', null);
    if (!$day || !is_array($day['players'] ?? null) || !count((array)$day['players'])) {
        out(['error' => '마감할 참가자가 없습니다'], 400);
    }
    $rows = [];
    foreach ((array)$day['players'] as $pid => $p) { $p = (array)$p;
        $rows[] = ['id' => (string)$pid, 'n' => (string)($p['n'] ?? ''), 'bal' => (int)($p['bal'] ?? 0),
                   'betW' => (int)($p['betW'] ?? 0), 'betL' => (int)($p['betL'] ?? 0)]; }
    usort($rows, function ($x, $y) { return $y['bal'] <=> $x['bal']; });
    $season = jread('toto_season.json', ['players' => [], 'days' => []]);
    $sp = (array)($season['players'] ?? []);
    foreach ($rows as $i => $r) {
        $s2 = (array)($sp[$r['id']] ?? ['n' => '', 'days' => 0, 'champ' => 0, 'betW' => 0,
                                        'betL' => 0, 'totalFinal' => 0, 'bestBal' => 0]);
        if ($r['n'] !== '') $s2['n'] = $r['n'];
        $s2['days'] = (int)$s2['days'] + 1;
        if ($i === 0) $s2['champ'] = (int)$s2['champ'] + 1;
        $s2['betW'] = (int)$s2['betW'] + $r['betW'];
        $s2['betL'] = (int)$s2['betL'] + $r['betL'];
        $s2['totalFinal'] = (int)$s2['totalFinal'] + $r['bal'];
        if ($r['bal'] > (int)$s2['bestBal']) $s2['bestBal'] = $r['bal'];
        $sp[$r['id']] = $s2;
    }
    $season['players'] = $sp;
    $days = (array)($season['days'] ?? []);
    array_unshift($days, ['date' => (string)($day['date'] ?? date('Y-m-d')), 'entries' => count($rows),
        'champ' => ['n' => $rows[0]['n'], 'bal' => $rows[0]['bal']],
        'top' => array_map(function ($r) { return ['n' => $r['n'], 'bal' => $r['bal']]; }, array_slice($rows, 0, 5))]);
    $season['days'] = array_slice($days, 0, 120);
    jwrite('toto_season.json', $season);
    jwrite('toto_day.json', null);
    out(['ok' => true, 'entries' => count($rows),
         'rank' => array_map(function ($r) { return ['n' => $r['n'], 'bal' => $r['bal']]; }, array_slice($rows, 0, 10))]);
}
if ($act === 'toto_public') {
    // 공개 리더보드 — 로그인 불필요, 닉네임만 (계정 비공개)
    $day = jread('toto_day.json', null);
    $dayOut = null;
    if (is_array($day)) {
        $rows = [];
        foreach ((array)($day['players'] ?? []) as $p) { $p = (array)$p;
            $rows[] = ['n' => (string)($p['n'] ?? ''), 'bal' => (int)($p['bal'] ?? 0),
                       'betW' => (int)($p['betW'] ?? 0), 'betL' => (int)($p['betL'] ?? 0),
                       'bust' => !empty($p['bust'])]; }
        usort($rows, function ($x, $y) { return $y['bal'] <=> $x['bal']; });
        $roundPub = null;
        if (is_array($day['round'] ?? null)) {
            $r = (array)$day['round']; $pa = 0; $pb = 0; $nb = 0;
            foreach ((array)($r['bets'] ?? []) as $v) { $v = (array)$v; $nb++;
                if ((($v['p'] ?? 'a')) === 'b') $pb += (int)($v['amt'] ?? 0);
                else $pa += (int)($v['amt'] ?? 0); }
            $roundPub = ['a' => (string)($r['a'] ?? ''), 'b' => (string)($r['b'] ?? ''),
                         'state' => (string)($r['state'] ?? ''), 'poolA' => $pa, 'poolB' => $pb, 'bets' => $nb];
        }
        $dayOut = ['date' => (string)($day['date'] ?? ''), 'open' => !empty($day['open']),
            'entries' => count($rows), 'rows' => array_slice($rows, 0, 200), 'round' => $roundPub,
            'rounds' => array_slice((array)($day['rounds'] ?? []), 0, 20),
            'feed' => array_slice((array)($day['feed'] ?? []), 0, 40)];
    }
    $season = jread('toto_season.json', ['players' => [], 'days' => []]);
    $sr = [];
    foreach ((array)($season['players'] ?? []) as $p) { $p = (array)$p;
        $w = (int)($p['betW'] ?? 0); $l = (int)($p['betL'] ?? 0);
        $sr[] = ['n' => (string)($p['n'] ?? ''), 'days' => (int)($p['days'] ?? 0),
                 'champ' => (int)($p['champ'] ?? 0), 'betW' => $w, 'betL' => $l,
                 'rate' => ($w + $l) ? round($w * 100 / ($w + $l)) : 0,
                 'totalFinal' => (int)($p['totalFinal'] ?? 0), 'bestBal' => (int)($p['bestBal'] ?? 0)]; }
    usort($sr, function ($x, $y) {
        return [$y['champ'], $y['totalFinal']] <=> [$x['champ'], $x['totalFinal']]; });
    out(['day' => $dayOut,
         'season' => ['players' => array_slice($sr, 0, 200),
                      'days' => array_slice((array)($season['days'] ?? []), 0, 30)]]);
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
if ($act === 'toto_chatlog') {
    // 승부예측 진행 중 전 채팅 원본 + 운영 이벤트 마커 (검증·분쟁 근거)
    $date = preg_replace('/[^0-9-]/', '', (string)($body['date'] ?? date('Y-m-d')));
    $lines = array_slice(is_array($body['lines'] ?? null) ? $body['lines'] : [], 0, 2000);
    if ($lines && $date !== '') {
        $txt = '';
        foreach ($lines as $l) {
            $txt .= json_encode($l, JSON_UNESCAPED_UNICODE) . "
";
        }
        file_put_contents(PZ . '/toto_chatlog-' . $date . '.jsonl', $txt, FILE_APPEND | LOCK_EX);
    }
    out(['ok' => true]);
}
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
<title>끝장전 상품 추첨</title><style>
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
#chat{resize:vertical;max-height:none;min-height:160px}   /* 아래 모서리 드래그로 높이 조절 */
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{padding:5px 7px;text-align:left;border-bottom:1px solid #171c25;white-space:nowrap}
th{color:#8a93a6;font-size:11px}
.num{text-align:right;font-variant-numeric:tabular-nums}
.chatline{padding:3px 4px;border-bottom:1px solid #12161e;font-size:13px;
overflow:hidden;text-overflow:ellipsis;white-space:nowrap;cursor:pointer;border-radius:5px}
.chatline:hover{background:#1a2130}
.chatline b{color:#7cb6ff;font-weight:600}.balloon{color:#ffb020;font-weight:700}
.wtag{color:#ffd166;font-size:11px;font-weight:600;margin-left:1px}
.wicon{font-size:12px;margin-left:2px;vertical-align:middle}
.chatlegend{border-top:1px solid #1d2431;margin-top:8px;padding-top:7px}
.chatlegend .lgrow{line-height:2;font-size:11.5px}
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
#kingChat td:nth-child(2),#kingBal td:nth-child(2){position:relative;z-index:0}
.subhead{font-weight:800;font-size:13px;margin:10px 0 4px;color:#e8ecf3;display:flex;gap:7px;align-items:center}
.subhead .n{color:#8a93a6;font-weight:500;font-size:11px}
.actbar{position:absolute;left:0;top:2px;bottom:2px;z-index:-1;border-radius:5px;
background:linear-gradient(90deg,rgba(28,140,255,.30),rgba(255,176,32,.14));min-width:2px}
.live{color:#ff4d5a;font-weight:900}
img.thumb{width:44px;height:44px;object-fit:cover;border-radius:8px;
vertical-align:middle;margin-right:6px;background:#0a0d13}
.hint{color:#8a93a6;font-size:11.5px;line-height:1.6;margin-top:6px}
hr{border-color:#232a38}
a.top{color:#8a93a6;font-size:12.5px;text-decoration:none}
a.top:hover{color:#e8ecf3}
.modal{position:fixed;inset:0;background:rgba(4,6,10,.66);z-index:50;display:flex;
align-items:flex-start;justify-content:center;padding:40px 16px;overflow:auto}
.dupbanner{background:#3a1520;border:1px solid #ff4d5a;border-radius:10px;padding:8px 12px;margin:8px 0;font-size:12.5px;line-height:2}
.dupbanner.ok{background:#12251a;border-color:#2c6b3f;color:#9fe0b4}
#pastdays tr{cursor:pointer}#pastdays tr:hover{background:#1a2030}
.modalbox{background:#141821;border:1px solid #2a3446;border-radius:14px;
padding:16px 18px;max-width:620px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.5)}
.chip{cursor:pointer;user-select:none;background:#1b202b}
.chip.on{border-color:#1c8cff;color:#cfe6ff;background:#12283f}
.rwrow{padding:3px 3px;border-bottom:1px solid #171c25;font-size:12.5px;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
body.maskacc .acc{filter:blur(6px);user-select:none;pointer-events:none}
.px{background:transparent;color:#8a93a6;border:0;padding:2px 8px;font-weight:900;font-size:15px;cursor:pointer;line-height:1}
.px:hover{color:#f87171}
@media(max-width:760px){
  .wrap{padding:10px 10px}
  body{font-size:15px}
  h1{font-size:16px}
  .card{padding:11px}
  #chat{max-height:40vh !important}
  .scroll{max-height:48vh}
  #chat{height:auto;max-height:48vh;resize:none}
  input,select{font-size:16px;padding:10px 11px}
  #pickNick,#prizeSel{flex:1 1 100% !important}
  .row>button{min-height:46px;padding:12px 14px;font-size:15px}
  #kingChat td,#kingChat th,#kingBal td,#kingBal th{padding:9px 5px;font-size:14.5px}
  /* 좁은 화면에선 SOOP계정 열을 숨겨 깔끔하게 */
  #kingChat th:nth-child(3),#kingChat td:nth-child(3),
  #kingBal th:nth-child(3),#kingBal td:nth-child(3){display:none}
  #kingChat button,#kingBal button{padding:9px 14px;font-size:14px}
  .chatline{padding:9px 5px;font-size:14.5px}
  .rwrow{padding:8px 4px;font-size:14px}
  #winners td,#winners th{padding:8px 5px}
  #settingsModal .modalbox{padding:13px}
}
</style></head><body><div class="wrap">
<h1>🎁 끝장전 상품 추첨
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
<button class="gray" style="padding:4px 10px" onclick="openSettings()">⚙ 규칙 설정</button>
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
<div class="row" id="panelBar" style="margin:0 0 10px;gap:5px;flex-wrap:wrap"></div>
<div class="grid">

<div class="card" data-panel="chat"><div class="ct">실시간 채팅 <span class="n" id="totline"></span>
<button class="gray" style="margin-left:auto;padding:4px 10px" onclick="clearChat()" title="화면만 비웁니다 — 저장된 로그는 그대로 남습니다">채팅 지우기</button><button class="px" onclick="togglePanel('chat')" title="이 창 닫기">✕</button></div>
<div class="scroll" id="chat" style="height:520px"></div>
<div id="chatLegend" class="chatlegend" style="display:none"></div></div>

<div class="card"><div class="ct" data-panel="users">시청자 활약 <span class="n">채팅왕 · 후원왕</span>
<button class="gray" style="margin-left:auto;padding:4px 10px" onclick="toggleMask()" id="maskBtn">🙈 계정 가리기</button>
<button class="gray" style="padding:4px 10px" onclick="downloadActivity()">⬇ 활약 CSV</button>
<button class="gray" style="padding:4px 10px" onclick="clearStats()">집계 초기화</button><button class="px" onclick="togglePanel('users')" title="이 창 닫기">✕</button></div>
<div class="subhead">💬 채팅왕 <span class="n">채팅 많은 순</span></div>
<div class="scroll" style="max-height:300px"><table id="kingChat"><thead><tr>
<th class="num">#</th><th>닉네임</th><th>SOOP계정</th><th class="num">채팅</th><th class="num">당첨</th><th></th>
</tr></thead><tbody></tbody></table></div>
<div class="subhead">👑 후원왕 <span class="n">별풍선·애드벌룬 많은 순</span></div>
<div class="scroll" style="max-height:300px"><table id="kingBal"><thead><tr>
<th class="num">#</th><th>닉네임</th><th>SOOP계정</th><th class="num">별풍선</th><th class="num">당첨</th><th></th>
</tr></thead><tbody></tbody></table></div>
<hr><div class="ct" data-panel="pastdays">지난 방송 <span class="n">저절로 저장됩니다</span><button class="px" style="margin-left:auto" onclick="togglePanel('pastdays')" title="이 창 닫기">✕</button></div>
<div class="scroll" style="max-height:150px"><table id="pastdays"><tbody></tbody></table></div></div>

<div class="card">
<div class="ct" data-panel="predict">🔮 시청자 승부예측 <span class="n">채팅 '도전' → 포인트 베팅</span><button class="px" style="margin-left:auto" onclick="togglePanel('predict')" title="이 창 닫기">✕</button></div>
<div class="row">
<button onclick="ttOpenDay()" id="ttOpenBtn">🔮 오늘 시작</button>
<span class="pill" id="ttEntry" style="font-size:12px">-</span>
<button class="gray" onclick="ttCloseDay()" id="ttCloseBtn" disabled>🏁 하루 마감</button>
<a class="top" href="../predict.php" target="_blank">리더보드 ↗</a></div>
<div class="row"><input id="ttA" placeholder="선수 A 이름" style="flex:1;min-width:80px">
<span class="n">vs</span><input id="ttB" placeholder="선수 B 이름" style="flex:1;min-width:80px"></div>
<div class="row">
<button onclick="ttRoundStart()" id="ttStartBtn" disabled>💰 베팅 오픈</button>
<button class="gray" onclick="ttLock()" id="ttLockBtn" disabled>⏸ 마감</button>
<button class="gray" onclick="ttSettle('a')" id="ttWinA" disabled>A 승</button>
<button class="gray" onclick="ttSettle('b')" id="ttWinB" disabled>B 승</button>
<button class="gray" onclick="ttCancelRound()" id="ttCancelBtn" disabled>취소</button></div>
<div id="ttBar" style="display:none">
<div style="display:flex;justify-content:space-between;font-size:12.5px;margin:2px 0">
<b id="ttCntA" style="color:#7cb6ff"></b><b id="ttCntB" style="color:#ff8fa3"></b></div>
<div style="height:12px;background:#33202a;border-radius:6px;overflow:hidden;display:flex">
<div id="ttFillA" style="background:#1c8cff;width:50%;transition:width .4s"></div>
<div style="background:#ff4d5a;flex:1"></div></div>
</div>
<div id="ttStatus" class="hint"></div>
<div id="ttFeed" style="max-height:108px;overflow:auto;font-size:12px;line-height:1.9;color:#aab3c5"></div>
<hr>
<div class="ct" data-panel="pick">당첨 만들기<button class="px" style="margin-left:auto" onclick="togglePanel('pick')" title="이 창 닫기">✕</button></div>
<div class="row"><input id="pickNick" placeholder="닉네임 — 채팅을 눌러도 들어갑니다" style="flex:1">
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
<div class="ct" data-panel="prizes">상품 <span class="n">사진도 넣을 수 있습니다</span><button class="px" style="margin-left:auto" onclick="togglePanel('prizes')" title="이 창 닫기">✕</button></div>
<div id="prizes"></div>
<div class="row"><input id="pName" placeholder="상품 이름" style="flex:1">
<input type="file" id="pPhoto" accept="image/*" style="display:none">
<button class="gray" onclick="document.getElementById('pPhoto').click()">사진</button>
<button onclick="addPrize()">추가</button></div>
<span id="pPhotoName" class="hint"></span>
<hr>
<div class="ct" data-panel="winners">당첨자 시트 <span class="n" id="wcount"></span>
<a class="top" href="prize_sheet.php">전체 화면 ↗</a>
<button class="gray" style="margin-left:auto;padding:4px 10px" onclick="copyLedger()">📋 복사</button>
<button class="gray" style="padding:4px 10px" onclick="downloadLedger()">⬇ CSV</button><button class="px" onclick="togglePanel('winners')" title="이 창 닫기">✕</button></div>
<div id="dupBanner" class="dupbanner" style="display:none"></div>
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
<div class="ct" data-panel="recent">최근 당첨자 <span class="n">중복 방지</span>
<span style="flex:1"></span>
<button class="pill chip" onclick="setDupM(1)">1개월</button>
<button class="pill chip" onclick="setDupM(2)">2개월</button>
<button class="pill chip" onclick="setDupM(3)">3개월</button><button class="px" onclick="togglePanel('recent')" title="이 창 닫기">✕</button></div>
<div id="dupLegend" class="hint" style="margin:2px 0"></div>
<div class="scroll" style="max-height:230px"><div id="recentWinners"></div></div>
</div>

</div></div>
<div id="pastModal" class="modal" style="display:none" onclick="if(event.target===this)closePast()">
 <div class="modalbox">
  <div class="ct"><span id="pastTitle">지난 방송</span><span style="flex:1"></span>
   <button class="gray" style="padding:4px 10px" onclick="closePast()">✕ 닫기</button></div>
  <div id="pastBody"></div>
 </div>
</div>
<div id="settingsModal" class="modal" style="display:none" onclick="if(event.target===this)closeSettings()">
 <div class="modalbox">
  <div class="ct">⚙ 규칙 설정 <span style="flex:1"></span>
   <button class="gray" style="padding:4px 10px" onclick="closeSettings()">✕ 닫기</button></div>
  <div class="row hint">채팅 <input id="sChatFull" style="width:52px"> 개에
  +<input id="sChatMax" style="width:46px"> · 별풍선
  <input id="sBalFull" style="width:60px"> 개에 +<input id="sBalMax" style="width:46px"></div>
  <div class="row hint">
  <label><input type="checkbox" id="sExcl"> 이전 당첨자 전체 제외</label>
  · 최근 <input id="sWeeks" style="width:40px"> 주 당첨자 제외(0=끄기)
  · 별풍선 <input id="sAlert" style="width:52px"> 개 이상이면 감사 배너</div>
  <div class="row hint">집계 제외 계정 <input id="sExclAcc" style="flex:1;min-width:220px"
   placeholder="매크로·스태프 아이디/닉 (스페이스나 쉼표로 여러 개)"></div>
  <div class="row hint">우리 채널 (데이터 저장) <input id="sRealCh" style="flex:1;min-width:200px"
   placeholder="talent (기본) — 다른 방송도 저장하려면 아이디 추가"></div>
  <div class="hint" style="margin:-2px 0 6px">여기 적은 채널만 채팅·활약·당첨 데이터를 저장합니다.
  나머지 채널(테스트용)은 저장하지 않고 창을 닫으면 사라집니다.</div>
  <div class="hint" style="margin:-2px 0 6px">우리 방송 계정(<b id="bjName"></b>)은 자동 제외됩니다.
  자동 매크로 채팅·매니저 계정을 여기 넣으면 시청자 활약 집계에서 빠집니다.</div>
  <div class="row hint">구글 문서 ID <input id="sGdoc" style="flex:1;min-width:180px" placeholder="당첨자 문서 주소의 /d/ 다음 부분">
  <span id="gdocInfo" class="pill"></span></div>
  <div class="row hint">슬랙 웹훅 <input id="sSlack" style="flex:1;min-width:180px" placeholder="https://hooks.slack.com/..."></div>
  <div class="row"><button onclick="saveSettings()">설정 저장</button>
  <button class="gray" onclick="copyLedger()">📋 당첨 기록 복사</button>
  <button class="gray" onclick="slackReport()">📨 슬랙으로 요약</button></div>
 </div>
</div>
<script>
/* ── 채팅 집계 (이 브라우저 안에서) ─────────────────────────── */
/* 주소 뒤에 ?bj=아이디 를 붙이면 그 채널에 붙습니다 — 우리 방송이 없을 때
   다른 라이브에서 수신을 시험하는 용도입니다. 시험 채널일 때는
   방송별 눈금(stats)을 저장하지 않아 진짜 기록과 섞이지 않습니다. */
const BJ=(new URLSearchParams(location.search).get('bj')||'talent')
  .toLowerCase().replace(/[^a-z0-9_]/g,'')||'talent';
const IS_DEMO = location.search.includes('demo');
function realChSet(){
  let list=['talent'];
  try{const j=JSON.parse(localStorage.getItem('pzRealCh')||'null');if(Array.isArray(j)&&j.length)list=j;}catch(e){}
  return new Set(list.map(x=>String(x).toLowerCase()).concat('talent'));
}
/* 우리 채널(기록 저장 대상)이 아니면 휘발성(테스트)으로 봅니다.
   기본은 talent, 설정에서 다른 채널도 추가할 수 있습니다. */
let IS_TEST_CH = !realChSet().has(BJ) || IS_DEMO;
const F='\x0c', users={}, recent=[], rawUnknown=[];
const sess={on:false,date:'',startedAt:''};   // 스타트/종료 상태
const logBuf=[];                              // 서버로 보낼 채팅 로그 대기줄
const LSKEY='pzLive_'+BJ;   // 이 브라우저에 로그·집계 임시 보관 (창을 나가도 유지)
let liveOn=false, liveTitle='', ws=null, pingT=null, ST=null;
let settings={chatFull:50,chatBonusMax:0.3,balloonFull:1000,balloonBonusMax:0.5,
  excludeWinners:false,excludeWeeks:0,balloonAlert:100,gdocId:'',slackWebhook:''};
let gdoc={names:[],ids:[]};   // 구글 문서에서 읽어 온 당첨자
let exclSet=new Set(), macroCount=0;   // 집계 제외 계정, 제외한 채팅 수
let dupMonths=+(localStorage.getItem('pzDupM')||1)||1;   // 최근 당첨자 표시 기간(개월)

function esc(s){return String(s??'').replace(/[&<>"]/g,
  c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function cleanNick(s){s=(s||'').trim();
  if(s.endsWith(')')&&s.includes('(')) s=s.slice(0,s.lastIndexOf('('));return s.trim()}
function rebuildExcl(){
  exclSet=new Set([BJ]);   // 우리 방송 계정은 항상 제외
  (settings.excludeAccounts||'').toLowerCase().split(/[\s,]+/).filter(Boolean)
    .forEach(x=>exclSet.add(x));
}
function isExcluded(id,nick){
  const i=(id||'').toLowerCase().trim();
  if(i&&exclSet.has(i))return true;
  return exclSet.has((nick||'').replace(/\s+/g,'').toLowerCase());
}
function bump(nick,kind,n){
  if(!nick)return;
  const u=users[nick]??(users[nick]={c:0,b:0});
  if(kind==='c')u.c++; else u.b+=n;
}
function onEvent(ev){
  // 우리 방송 계정(매크로)·제외 계정은 시청자 활약에 넣지 않습니다
  if(isExcluded(ev.id,ev.nick)){macroCount++;return;}
  if(ev.t==='chat'){bump(ev.nick,'c');if(ev.id)uid[ev.nick]=ev.id;recent.push(ev);ttOnChat(ev);}
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
/* 별풍선 중복제거 — svc109 의 [3]은 별풍선 '종류' 해시라 여러 사람이
   공유합니다(실측: 서로 다른 3명이 같은 mid). 그래서 mid 만으로 지우면
   다른 사람·다른 개수 선물까지 버려 절반 이상을 놓쳤습니다. 이제
   (종류+보낸사람+개수)가 똑같고 8초 안에 다시 온 것만 재전송으로 보고
   건너뜁니다. 다른 사람·다른 개수·시간차 큰 같은 선물은 각각 셉니다. */
let seenBalloons=new Map();   // (보낸사람|개수) -> 마지막 시각(ms)
const BAL_WINDOW=8000;
/* 별풍선 — SOOP 플레이어 공식 코드에서 확인한 레이아웃 그대로 (2026-08-21).
     svc 18 = SVC_SENDBALLOON      [1]채널 [2]보낸이ID [3]닉 [4]개수 [8]시그니처 이미지 파일명
     svc 33 = SVC_SENDBALLOONSUB   [2]채널 [4]보낸이ID [5]닉 [6]개수 (중계방)
     svc109 = SVC_OGQ_EMOTICON     이모티콘 스티커 — 별풍선이 아니므로 세지 않음
   닉==ID 인 시청자도 진짜 별풍선입니다(공식 파서에 제외 규칙 없음).
   순위·누적은 svc 30/39(TOPFAN/TOPCLAN)로 따로 오므로 여기 안 섞입니다.
   중복제거: 같은 사람·같은 개수가 8초 안에 다시 오면 재전송으로 봄. */
function dedupBalloon(who,cnt,kind){
  const key=who+'|'+cnt+'|'+(kind||'star'), t=Date.now(), last=seenBalloons.get(key);
  seenBalloons.set(key,t);
  if(seenBalloons.size>5000){for(const [k,v] of seenBalloons)if(t-v>=BAL_WINDOW)seenBalloons.delete(k);}
  return last==null || t-last>=BAL_WINDOW;   // true = 새(중복 아닌) 것
}
function parseBalloon18(f){  // svc 18 — 공식 SVC_SENDBALLOON
  if(f.length<5)return null;
  const cnt=(f[4]||'').trim();
  if(!/^\d+$/.test(cnt)||+cnt<=0||+cnt>1000000)return null;
  const id=cleanNick(f[2]), nick=cleanNick(f[3]);
  if(!id||!nick)return null;
  if((f[1]||'').toLowerCase()!==BJ)return null;        // 이 채널로 온 선물만
  return dedupBalloon(id,cnt)?{t:'balloon',nick,count:+cnt,id}:null;
}
function parseBalloon33(f){  // svc 33 — 공식 SVC_SENDBALLOONSUB (중계방 별풍선)
  if(f.length<7)return null;
  const cnt=(f[6]||'').trim();
  if(!/^\d+$/.test(cnt)||+cnt<=0||+cnt>1000000)return null;
  const id=cleanNick(f[4]), nick=cleanNick(f[5]);
  if(!id||!nick)return null;
  if((f[2]||'').toLowerCase()!==BJ)return null;
  return dedupBalloon(id,cnt,'star')?{t:'balloon',nick,count:+cnt,id}:null;
}
function parseBalloon87(f){  // 애드벌룬 (SVC_ADCON_EFFECT) — 채널f[2] 아이디f[3] 닉f[4] 개수f[10]. 사장님 방침으로 별풍선 합산.
  if(f.length<11)return null;
  const cnt=(f[10]||'').trim();
  if(!/^\d+$/.test(cnt)||+cnt<=0||+cnt>1000000)return null;
  const id=cleanNick(f[3]), nick=cleanNick(f[4]);
  if(!id||!nick)return null;
  if((f[2]||'').toLowerCase()!==BJ)return null;
  return dedupBalloon(id,cnt,'ad')?{t:'balloon',nick,count:+cnt,id,ad:1}:null;
}
function parseBalloon107(f){ // 방송국 애드벌룬 (SVC_STATION_ADCON) — 채널f[1] 아이디f[2] 닉f[3] 개수f[4]
  if(f.length<5)return null;
  const cnt=(f[4]||'').trim();
  if(!/^\d+$/.test(cnt)||+cnt<=0||+cnt>1000000)return null;
  const id=cleanNick(f[2]), nick=cleanNick(f[3]);
  if(!id||!nick)return null;
  if((f[1]||'').toLowerCase()!==BJ)return null;
  return dedupBalloon(id,cnt,'ad')?{t:'balloon',nick,count:+cnt,id,ad:1}:null;
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
  ttGapCheck();
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
    }else if(svc===18){
      const ev=parseBalloon18(f);        // 별풍선 (공식 SVC_SENDBALLOON)
      if(ev){ev.at=now();onEvent(ev);}
    }else if(svc===33){
      const ev=parseBalloon33(f);        // 중계방 별풍선 (공식 SVC_SENDBALLOONSUB)
      if(ev){ev.at=now();onEvent(ev);}
    }else if(svc===87){
      const ev=parseBalloon87(f);        // 애드벌룬 — 별풍선에 합산
      if(ev){ev.at=now();onEvent(ev);}
    }else if(svc===107){
      const ev=parseBalloon107(f);       // 방송국 애드벌룬 — 별풍선에 합산
      if(ev){ev.at=now();onEvent(ev);}
    }else if(svc===109){
      // OGQ 이모티콘(공식 SVC_OGQ_EMOTICON) — 별풍선 아님, 집계 안 함

    }else if(![0,1,2,4].includes(svc)){
      rawUnknown.push({svc,f:f.slice(0,10),at:now()});
      rawUnknown.splice(0,Math.max(0,rawUnknown.length-200));
    }
  };
  ws.onclose=()=>{clearInterval(pingT);
    if(tt&&!window.ttDropAt)window.ttDropAt=Date.now();   // 예측 중 끊김 시각 기록
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
function curPrize(){return (prizeOf(document.getElementById('prizeSel').value)||{}).name||'';}
function hasWonPrize(nick,prize){
  // 이 사람이 '이 상품'을 이미 받았는지 (닉 또는 SOOP계정 일치)
  if(!ST||!prize)return false;
  const n=norm(nick), sid=(uid[nick]||'').toLowerCase(), pn=norm(prize);
  return ST.winners.list.some(w=>norm(w.prize)===pn &&
    (norm(w.nick)===n || (sid&&(w.sid||'').toLowerCase()===sid)));
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
  const prize=curPrize();
  let pool=Object.keys(users).filter(n=>users[n].c+users[n].b>0);
  if(prize)pool=pool.filter(n=>!hasWonPrize(n,prize));   // 같은 상품 중복 당첨 방지 (항상)
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
  if(hasWonPrize(nick,pz.name)&&!confirm(nick+' 님은 이미 "'+(pz.name||'')+'" 상품에 당첨된 적이 있습니다. 같은 상품에 또 당첨시킬까요?'))return;
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
    slackWebhook:document.getElementById('sSlack').value.trim(),
    excludeAccounts:document.getElementById('sExclAcc').value.trim(),
    realChannels:document.getElementById('sRealCh').value.trim()});
  await api('settings_set',{settings});loadGdoc();rebuildExcl();applyRealCh();closeSettings();
}
function openSettings(){var b=document.getElementById('bjName');if(b)b.textContent=BJ;
  document.getElementById('settingsModal').style.display='flex';}
function closeSettings(){document.getElementById('settingsModal').style.display='none';}
function applyRealCh(){
  const raw=(settings.realChannels||'').toLowerCase().split(/[\s,]+/).filter(Boolean);
  if(!raw.includes('talent'))raw.push('talent');
  try{localStorage.setItem('pzRealCh',JSON.stringify(raw));}catch(e){}
  IS_TEST_CH = !new Set(raw).has(BJ) || IS_DEMO;
}
function updateMaskBtn(){
  const b=document.getElementById('maskBtn');if(!b)return;
  b.textContent=document.body.classList.contains('maskacc')?'👁 계정 보기':'🙈 계정 가리기';
}
function toggleMask(){
  document.body.classList.toggle('maskacc');
  try{localStorage.setItem('pzMaskAcc',document.body.classList.contains('maskacc')?'1':'');}catch(e){}
  updateMaskBtn();
}
function downloadActivity(){
  const rows=Object.entries(users).map(([nick,u])=>({nick,acc:uid[nick]||'',c:u.c,b:u.b,w:winCount(nick)[0]}));
  if(!rows.length)return alert('활약 데이터가 없습니다');
  rows.sort((a,b)=>b.b-a.b||b.c-a.c);
  const NL=String.fromCharCode(10);
  const q=x=>'"'+String(x==null?'':x).replace(/"/g,'""')+'"';
  const lines=rows.map(r=>[q(r.nick),q(r.acc),r.c,r.b,r.w].join(','));
  const csv=String.fromCharCode(0xFEFF)+['닉네임,SOOP계정,채팅수,별풍선수,당첨횟수'].concat(lines).join(NL);
  const a=document.createElement('a');
  a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(csv);
  a.download='끝장전-활약-'+(sess.date||todayStr())+'.csv';a.click();
}
/* ── 시청자 승부예측 — 하루 가상 포인트 베팅 (내부 코드명 toto 유지) ──
   '도전' → 10,000P 지급(계정당 1회). '이름 금액'/'이름 올인' — 첫 베팅 고정.
   배당 = 총풀/승자풀(합동배당), 승자 없으면 전원 환불. 파산 = 그날 끝.
   접수/실패는 피드로 안내(관제·방송 장면·공개 페이지). 정산·하루마감은
   서버가 단독 수행(이중 방지). 연습 채널이면 전부 이 창 안에서만. */
const TT_START=10000, TT_MIN=100;
let tt=null;            // {date,open,players,round,rounds,feed}
let ttLogBuf=[];        // 예측 중 전 채팅 원본 (서버 기록 대기)
function ttLog(o){ if(tt&&!IS_TEST_CH)ttLogBuf.push(Object.assign({at:Date.now()},o)); }
function ttLogFlush(){
  if(!ttLogBuf.length||IS_TEST_CH||!tt)return;
  api('toto_chatlog',{date:tt.date,lines:ttLogBuf.splice(0,2000)});
}
function ttGapCheck(){
  // 채팅이 끊겼다 다시 붙었을 때 — 그 사이 채팅은 못 받았으니 크게 알립니다.
  if(!window.ttDropAt)return;
  const gap=Math.round((Date.now()-window.ttDropAt)/1000);
  window.ttDropAt=null;
  if(tt&&gap>=3){
    ttFeed('info','⚠ 채팅 연결이 '+gap+'초 끊겼습니다 — 그 사이 도전·베팅은 못 받았을 수 있어요. 방송에서 안내해 주세요!');
    ttLog({ctl:'gap',sec:gap});
    ttPaint();
  }
}
let ttSyncT=null, ttLocalSeason={players:{},days:[]};
function ttNorm(s){return String(s||'').replace(/\s+/g,'').replace(/[!~.?]+$/,'').toLowerCase()}
function ttFeed(type,msg){
  if(!tt)return;
  tt.feed=tt.feed||[];
  tt.feed.unshift({type:type,msg:msg,at:new Date().toTimeString().slice(0,8)});
  tt.feed.splice(80);
}
function ttOnChat(ev){
  if(!tt)return;
  ttLog({id:ev.id||'',n:ev.nick,m:ev.msg});     // 전 채팅 원본 기록
  const key=ev.id||('nick:'+ev.nick);
  const raw=String(ev.msg||'').trim();
  if(ttNorm(raw)==='도전'){                     // ① 참여
    if(!tt.open)return;
    const p0=tt.players[key];
    if(p0){if(p0.bust)ttFeed('fail','❌ '+ev.nick+' — 오늘은 파산! 내일 다시 도전하세요');return;}
    tt.players[key]={n:ev.nick,bal:TT_START,betW:0,betL:0,bust:false};
    ttFeed('join','🙋 '+ev.nick+' 참여! ('+TT_START.toLocaleString()+'P 지급)');
    ttPaint();return;
  }
  if(!tt.round)return;                          // ② 베팅 — '이름 금액'
  const m=raw.split(/\s+/);
  if(m.length!==2)return;
  const amtRaw=m[1].replace(/,/g,'');
  const allin=(amtRaw==='올인');
  if(!allin&&!/^[0-9]+$/.test(amtRaw))return;   // 베팅 형태 아님 → 조용히 무시
  const nm=ttNorm(m[0]);
  let pick=null;
  if(nm===ttNorm(tt.round.a))pick='a'; else if(nm===ttNorm(tt.round.b))pick='b';
  if(tt.round.state!=='open'){const pl0=tt.players[key];if(pick&&pl0&&!pl0.bust)ttFeed('fail','❌ '+ev.nick+' — 베팅 마감! 다음 세트에 참여하세요');return;}
  const p=tt.players[key];
  if(!pick){if(p&&!p.bust)ttFeed('fail','❌ '+ev.nick+' — 선수 이름을 정확히! ('+tt.round.a+' / '+tt.round.b+')');return;}
  if(!p){ttFeed('fail','❌ '+ev.nick+' — 먼저 채팅에 "도전"을 쳐서 참여하세요');return;}
  if(p.bust){ttFeed('fail','❌ '+ev.nick+' — 파산! 오늘은 관전만');return;}
  if(tt.round.bets[key]){ttFeed('fail','❌ '+ev.nick+' — 이미 베팅했어요 (변경 불가)');return;}
  const amt=allin?p.bal:parseInt(amtRaw,10);
  if(!allin&&amt>p.bal){ttFeed('fail','❌ '+ev.nick+' — 잔액 부족 (보유 '+p.bal.toLocaleString()+'P)');return;}
  if(amt<TT_MIN){ttFeed('fail','❌ '+ev.nick+' — 최소 '+TT_MIN+'P부터');return;}
  p.bal-=amt;
  tt.round.bets[key]={p:pick,amt:amt,n:ev.nick};
  ttFeed('bet','✅ '+ev.nick+' '+amt.toLocaleString()+'P → '+(pick==='a'?tt.round.a:tt.round.b)+(allin?' (올인!)':''));
  ttPaint();
}
function ttPools(){
  let a=0,b=0,n=0;
  if(tt&&tt.round)for(const k in tt.round.bets){const v=tt.round.bets[k];n++;if(v.p==='a')a+=v.amt;else b+=v.amt;}
  return{a:a,b:b,n:n};
}
function ttOdds(pool,total){return pool>0?(total/pool).toFixed(2):'-';}
function ttPaint(){
  const st=document.getElementById('ttStatus');if(!st)return;
  const bar=document.getElementById('ttBar'),fd=document.getElementById('ttFeed');
  const oBtn=document.getElementById('ttOpenBtn'),cBtn=document.getElementById('ttCloseBtn');
  const sBtn=document.getElementById('ttStartBtn'),lBtn=document.getElementById('ttLockBtn');
  const aBtn=document.getElementById('ttWinA'),bBtn=document.getElementById('ttWinB'),xBtn=document.getElementById('ttCancelBtn');
  const en=document.getElementById('ttEntry');
  if(!tt){
    oBtn.disabled=false;cBtn.disabled=true;sBtn.disabled=true;lBtn.disabled=true;
    aBtn.disabled=true;bBtn.disabled=true;xBtn.disabled=true;
    en.textContent='시작 전';bar.style.display='none';
    if(!st.dataset.keep)st.innerHTML='<b>🔮 오늘 시작</b>을 누르면 시청자가 채팅에 <b>도전</b>을 쳐서 참여합니다 (1인 '+TT_START.toLocaleString()+'P).';
    fd.innerHTML='';return;
  }
  st.dataset.keep='';
  let np=0,nb=0;for(const k in tt.players){np++;if(tt.players[k].bust)nb++;}
  en.textContent='참여 '+np+'명'+(nb?' · 파산 '+nb:'');
  oBtn.disabled=true;cBtn.disabled=false;
  const r=tt.round;
  sBtn.disabled=!!r;lBtn.disabled=!r||r.state!=='open';
  aBtn.disabled=!r;bBtn.disabled=!r;xBtn.disabled=!r;
  if(r){
    aBtn.textContent=r.a+' 승';bBtn.textContent=r.b+' 승';
    document.getElementById('ttA').value=r.a;document.getElementById('ttB').value=r.b;
    const c=ttPools(),tot=c.a+c.b,pa=tot?Math.round(c.a*100/tot):50;
    bar.style.display='';
    document.getElementById('ttCntA').textContent=r.a+' '+c.a.toLocaleString()+'P (배당 '+ttOdds(c.a,tot)+')';
    document.getElementById('ttCntB').textContent='(배당 '+ttOdds(c.b,tot)+') '+c.b.toLocaleString()+'P '+r.b;
    document.getElementById('ttFillA').style.width=(tot?pa:50)+'%';
    st.innerHTML=(r.state==='open'?'🟢 <b>베팅 접수 중</b> — 채팅에 "이름 금액" 또는 "이름 올인". ':'⏸ <b>마감</b> — 결과 버튼으로 정산. ')
      +'베팅 '+c.n+'건 · 총 '+tot.toLocaleString()+'P'+(IS_TEST_CH?' <span class="warn">(연습)</span>':'');
  }else{
    aBtn.textContent='A 승';bBtn.textContent='B 승';bar.style.display='none';
    st.innerHTML='참여 접수 중 — 세트 전에 선수 두 명을 넣고 <b>베팅 오픈</b>.'+(IS_TEST_CH?' <span class="warn">(연습 — 저장 안 됨)</span>':'');
  }
  fd.innerHTML=(tt.feed||[]).slice(0,10).map(function(f){
    return '<div>'+esc(f.at+' '+f.msg)+'</div>';}).join('');
}
function ttSyncStart(){if(ttSyncT||IS_TEST_CH)return;ttSyncT=setInterval(function(){if(tt){api('toto_save',{day:tt});ttLogFlush();}},4000);}
function ttSyncStop(){if(ttSyncT){clearInterval(ttSyncT);ttSyncT=null;}}
async function ttOpenDay(){
  if(tt)return;
  tt={date:todayStr(),open:true,players:{},round:null,rounds:[],feed:[]};
  ttFeed('info','🔮 시청자 승부예측 시작! 채팅에 "도전"');
  ttLog({ctl:'open_day'});
  const st=document.getElementById('ttStatus');if(st)delete st.dataset.keep;
  ttPaint();
  if(!IS_TEST_CH){await api('toto_save',{day:tt});ttSyncStart();}
}
async function ttRoundStart(){
  if(!tt||tt.round)return;
  const a=document.getElementById('ttA').value.trim(),b=document.getElementById('ttB').value.trim();
  if(!a||!b)return alert('선수 두 명의 이름을 넣어주세요');
  if(ttNorm(a)===ttNorm(b))return alert('두 이름이 같습니다');
  tt.round={id:String(Date.now()),a:a,b:b,state:'open',bets:{}};
  ttFeed('info','💰 베팅 오픈 — '+a+' vs '+b);
  ttLog({ctl:'round_open',a:a,b:b});
  ttPaint();
  if(!IS_TEST_CH){await api('toto_save',{day:tt});await api('overlay_set',{overlay:{kind:'toto'}});}
}
async function ttLock(){
  if(!tt||!tt.round||tt.round.state!=='open')return;
  tt.round.state='locked';
  ttFeed('info','⏸ 베팅 마감 ('+ttPools().n+'건)');
  ttLog({ctl:'lock'});
  ttPaint();
  if(!IS_TEST_CH)await api('toto_save',{day:tt});
}
async function ttCancelRound(){
  if(!tt||!tt.round)return;
  if(!confirm('이 베팅 라운드를 취소할까요? 건 포인트는 전부 돌려줍니다.'))return;
  for(const k in tt.round.bets){const v=tt.round.bets[k];const p=tt.players[k];if(p){p.bal+=v.amt;p.bust=false;}}
  ttFeed('info','↩ 라운드 취소 — 전원 환불');
  ttLog({ctl:'cancel'});
  tt.round=null;ttPaint();
  if(!IS_TEST_CH){await api('toto_save',{day:tt});await api('overlay_set',{overlay:{kind:'none'}});}
}
function ttSettleLocal(day,winner){
  const r=day.round,bets=r.bets;let pa=0,pb=0;
  for(const k in bets){if(bets[k].p==='a')pa+=bets[k].amt;else pb+=bets[k].amt;}
  const tot=pa+pb,pw=winner==='a'?pa:pb,refund=pw<=0;
  const odds=refund?0:+(tot/pw).toFixed(2);let hit=0;const top=[];
  for(const k in bets){const v=bets[k],p=day.players[k];
    if(refund)p.bal+=v.amt;
    else if(v.p===winner){const gain=Math.floor(v.amt*tot/pw);p.bal+=gain;p.betW++;hit++;top.push({n:v.n,gain:gain-v.amt});}
    else p.betL++;
    if(p.bal<=0){p.bal=0;p.bust=true;}}
  top.sort(function(x,y){return y.gain-x.gain});
  const wname=winner==='a'?r.a:r.b;
  day.rounds.unshift({a:r.a,b:r.b,winner:winner,poolA:pa,poolB:pb,odds:odds,hit:hit,bets:Object.keys(bets).length,refund:refund,at:new Date().toTimeString().slice(0,5)});
  day.round=null;
  return{ok:true,refund:refund,odds:odds,hit:hit,poolA:pa,poolB:pb,wname:wname,top:top.slice(0,5)};
}
async function ttSettle(w){
  if(!tt||!tt.round)return;
  const wname=(w==='a'?tt.round.a:tt.round.b);
  if(!confirm(wname+' 승으로 정산할까요?'))return;
  ttLog({ctl:'settle',winner:w,wname:wname});ttLogFlush();
  let res;
  if(IS_TEST_CH){res=ttSettleLocal(tt,w);ttFeed('settle',res.refund?'⚖ 적중자 없음 — 전원 환불':'🏆 '+wname+' 승 · 배당 '+res.odds.toFixed(2)+'배 · 적중 '+res.hit+'명');}
  else{
    res=await api('toto_settle',{winner:w,day:tt});
    if(!res||!res.ok)return alert('정산 실패: '+((res&&res.error)||'서버 오류'));
    const g=await api('toto_get',{});if(g&&g.day)tt=g.day;   // 서버 정산 결과로 동기화
  }
  ttPaint();
  if(!IS_TEST_CH)await api('overlay_set',{overlay:{kind:'toto_result',
    wname:res.wname||wname,odds:res.odds,hit:res.hit,refund:res.refund,poolA:res.poolA,poolB:res.poolB,top:res.top||[]}});
}
async function ttCloseDay(){
  if(!tt)return;
  if(tt.round)return alert('진행 중인 베팅 라운드를 먼저 정산하거나 취소해 주세요');
  if(!confirm('오늘 승부예측을 마감하고 순위를 확정할까요?'))return;
  ttLog({ctl:'close_day'});ttLogFlush();
  let res;
  if(IS_TEST_CH){
    const rows=Object.keys(tt.players).map(function(k){const p=tt.players[k];return{n:p.n,bal:p.bal};});
    rows.sort(function(x,y){return y.bal-x.bal});
    res={ok:true,entries:rows.length,rank:rows.slice(0,10)};
  }else{
    res=await api('toto_closeday',{day:tt});
    if(!res||!res.ok)return alert('마감 실패: '+((res&&res.error)||'서버 오류'));
  }
  const champ=res.rank&&res.rank[0];
  tt=null;ttSyncStop();
  const st=document.getElementById('ttStatus');
  st.dataset.keep='1';
  st.innerHTML='🏁 오늘 마감 — 참여 '+res.entries+'명'+(champ?' · 🥇 <b>'+esc(champ.n)+'</b> '+champ.bal.toLocaleString()+'P':'')+(IS_TEST_CH?' <span class="warn">(연습)</span>':'');
  ttPaint();
  if(!IS_TEST_CH&&champ)await api('overlay_set',{overlay:{kind:'toto_champ',n:champ.n,bal:champ.bal,entries:res.entries,rank:res.rank||[]}});
}
async function ttRestore(){
  if(IS_TEST_CH)return;
  try{const g=await api('toto_get',{});
    if(g&&g.day&&g.day.players){tt=g.day;ttSyncStart();ttPaint();}}catch(e){}
}
const PANELS=[['chat','실시간 채팅'],['users','시청자 활약'],['pastdays','지난 방송'],
  ['predict','승부예측'],['pick','당첨 만들기'],['prizes','상품'],['winners','당첨자 시트'],['recent','최근 당첨자']];
const panelState={};   // key -> 숨김 여부(true=닫힘)
function panelNodes(key){
  // data-panel 이 카드면 카드 통째로, 섹션이면 헤더~다음 헤더/구분선 앞까지(앞 <hr> 포함)
  const el=document.querySelector('[data-panel="'+key+'"]');
  if(!el)return [];
  if(el.classList.contains('card'))return [el];
  const nodes=[]; const prev=el.previousElementSibling;
  if(prev&&prev.tagName==='HR')nodes.push(prev);
  nodes.push(el);
  let n=el.nextElementSibling;
  while(n&&!(n.classList&&n.classList.contains('ct'))&&n.tagName!=='HR'){nodes.push(n);n=n.nextElementSibling;}
  return nodes;
}
function applyPanel(key){
  const hide=!!panelState[key];
  panelNodes(key).forEach(n=>{n.style.display=hide?'none':'';});
}
function renderPanelBar(){
  const bar=document.getElementById('panelBar');if(!bar)return;
  bar.innerHTML='<span class="n" style="margin-right:2px">창 켜기·끄기:</span>'+PANELS.map(function(pr){
    return '<button class="pill chip'+(panelState[pr[0]]?'':' on')+'" data-pk="'+pr[0]+'">'+
      (panelState[pr[0]]?'＋ ':'✓ ')+esc(pr[1])+'</button>';}).join('');
  bar.querySelectorAll('[data-pk]').forEach(b=>b.onclick=()=>togglePanel(b.dataset.pk));
}
/* 카드(열) 전체가 닫히면 숨기고, 남은 카드 수에 맞춰 그리드를 좁혀 채팅을 넓힘 */
function reflowGrid(){
  const grid=document.querySelector('.grid'); if(!grid)return;
  const cards=[...grid.children].filter(c=>c.classList&&c.classList.contains('card'));
  cards.forEach(function(card){
    const own=card.getAttribute('data-panel');
    let empty;
    if(own){empty=!!panelState[own];}   // 채팅 카드(카드 자체가 한 패널)
    else{const pk=[...card.querySelectorAll('[data-panel]')].map(e=>e.getAttribute('data-panel'));
      empty=pk.length>0 && pk.every(k=>panelState[k]);}   // 나머지 카드는 안쪽 패널이 모두 닫혔을 때
    card.style.display=empty?'none':'';
  });
  const vis=cards.filter(c=>c.style.display!=='none').length;
  // 넓은 화면에서만 열 재배치 (좁은 화면은 CSS 미디어쿼리로 1열)
  grid.style.gridTemplateColumns=(window.innerWidth>1100)
    ? (vis<=1?'1fr':vis===2?'1.5fr 1fr':'1.1fr .9fr 1fr') : '';
}
function togglePanel(key){
  panelState[key]=!panelState[key];
  try{localStorage.setItem('pzPanels',JSON.stringify(panelState));}catch(e){}
  applyPanel(key);reflowGrid();renderPanelBar();
}
function initPanels(){
  try{Object.assign(panelState,JSON.parse(localStorage.getItem('pzPanels')||'{}'));}catch(e){}
  PANELS.forEach(pr=>applyPanel(pr[0]));
  reflowGrid();renderPanelBar();
}
/* 채팅창 높이 — 드래그한 값을 이 브라우저에 기억 */
function initChatResize(){
  const el=document.getElementById('chat'); if(!el)return;
  try{const h=localStorage.getItem('pzChatH'); if(h&&+h>=160)el.style.height=h+'px';}catch(e){}
  if(window.ResizeObserver){
    let t; new ResizeObserver(function(){clearTimeout(t);t=setTimeout(function(){
      try{localStorage.setItem('pzChatH',Math.round(el.offsetHeight));}catch(e){}
    },400);}).observe(el);
  }
  window.addEventListener('resize',function(){clearTimeout(window._rgT);window._rgT=setTimeout(reflowGrid,200);});
}
function setDupM(m){dupMonths=m;try{localStorage.setItem('pzDupM',m);}catch(e){}renderRecentWinners();}
const PCATS=[
  {k:'마우스패드',re:/마우스\s*패드|패드|gigantus|mousepad/i,c:'#a78bfa',i:'🟪'},
  {k:'마우스',re:/마우스|viper|razer|mouse/i,c:'#4aa3ff',i:'🖱️'},
  {k:'유니폼',re:/유니폼|uniform|jamie/i,c:'#f87171',i:'👕'},
  {k:'안경',re:/안경|wearwhere|glass/i,c:'#4ade80',i:'👓'},
  {k:'쿠폰·코드',re:/쿠폰|포인트|코드|coupon|point|code/i,c:'#ffb020',i:'🎟️'}];
function prizeCat(p){for(const x of PCATS)if(x.re.test(p||''))return x;return{k:'기타',c:'#8a93a6',i:'🎁'};}
let _rwSig='';
async function showPastDay(date){
  document.getElementById('pastTitle').textContent=date+' — 최종 시청자 활약';
  document.getElementById('pastBody').innerHTML='<div class="hint">불러오는 중…</div>';
  document.getElementById('pastModal').style.display='flex';
  let j;
  try{j=await (await fetch('prize_api.php?act=stats_get&date='+encodeURIComponent(date))).json();}
  catch(e){document.getElementById('pastBody').innerHTML='<div class="warn">불러오기 실패</div>';return;}
  const u=j.users||{}, ud=j.uid||{};
  const arr=Object.entries(u).map(([nick,x])=>({nick:nick,c:(x&&x.c)||0,b:(x&&x.b)||0}));
  const medal=['🥇','🥈','🥉'];
  function tbl(valKey,label,cls){
    const rows=arr.filter(x=>x[valKey]>0).sort((a,b)=>b[valKey]-a[valKey]).slice(0,50);
    return '<div class="subhead">'+label+'</div><div class="scroll" style="max-height:230px"><table><thead><tr>'+
      '<th class="num">#</th><th>닉네임</th><th>SOOP계정</th><th class="num">'+(valKey==='c'?'채팅':'별풍선')+'</th></tr></thead><tbody>'+
      (rows.length?rows.map((x,i)=>'<tr><td class="num" style="color:#8a93a6">'+(medal[i]||(i+1))+
        '</td><td><b>'+esc(x.nick)+'</b></td><td class="pill acc" style="font-size:11px">'+esc(ud[x.nick]||'-')+
        '</td><td class="num '+cls+'">'+x[valKey]+'</td></tr>').join(''):'<tr><td colspan="4" style="color:#8a93a6;padding:12px">없음</td></tr>')+
      '</tbody></table></div>';
  }
  document.getElementById('pastBody').innerHTML=
    '<div class="hint">저장 시각 '+esc(j.savedAt||'-')+' · 시청자 '+arr.length+'명'+(j.title?' · '+esc(j.title):'')+'</div>'+
    tbl('c','💬 채팅왕','')+tbl('b','👑 후원왕','balloon');
}
function closePast(){document.getElementById('pastModal').style.display='none';}

/* 중복 당첨 — 같은 사람(닉/계정)이 같은 상품을 2번 이상 받은 것 */
function findDups(){
  if(!ST)return [];
  const map={};
  (ST.winners.list||[]).forEach(w=>{
    if(/연습/.test(w.how||'')||!w.prize)return;
    const person=(w.sid||'').toLowerCase()||norm(w.nick);
    const key=person+'|'+norm(w.prize);
    const m=map[key]||(map[key]={nick:w.nick,sid:w.sid||'',prize:w.prize,n:0,dates:[]});
    m.n++; m.nick=w.nick; if(w.sid)m.sid=w.sid; if(w.date)m.dates.push(w.date);
  });
  return Object.values(map).filter(x=>x.n>=2).sort((a,b)=>b.n-a.n);
}
function dupPersonKeys(){
  const set=new Set();
  findDups().forEach(d=>set.add((d.sid||'').toLowerCase()||norm(d.nick)));
  return set;
}
let dupDismissed='';
function dupSig(dups){return dups.map(d=>d.nick+'|'+d.prize+'|'+d.n).join(',');}
function dismissDup(){dupDismissed=dupSig(findDups())||'_none_';const el=document.getElementById('dupBanner');if(el)el.style.display='none';}
function renderDupBanner(){
  const el=document.getElementById('dupBanner'); if(!el)return;
  // 당첨자 시트 패널을 X로 닫았으면 배너도 숨김
  if(typeof panelState!=='undefined'&&panelState['winners']){el.style.display='none';return;}
  const dups=findDups();
  const sig=dupSig(dups)||'_none_';
  if(sig===dupDismissed){el.style.display='none';return;}   // 사용자가 배너 X로 끈 상태 (내용 바뀌면 다시 뜸)
  const X='<button class="px" style="float:right;margin:-2px -4px 0 0;color:#ff8fa3" onclick="dismissDup()" title="배너 닫기">✕</button>';
  if(!dups.length){el.className='dupbanner ok';el.style.display='';el.innerHTML=X+'✓ 같은 상품 중복 당첨 없음';return;}
  el.className='dupbanner';el.style.display='';
  el.innerHTML=X+'🚨 <b>같은 상품 중복 당첨 '+dups.length+'건</b> — 확인 필요<br>'+
    dups.slice(0,30).map(d=>'<span class="pill" style="border-color:#ff4d5a;color:#ff8fa3;margin:2px 0;display:inline-block">'+
      esc(d.nick)+(d.sid?' <span style="color:#8a93a6">('+esc(d.sid)+')</span>':'')+' × '+esc(d.prize)+' <b>'+d.n+'회</b></span>').join(' ');
}
function renderChatLegend(){
  const el=document.getElementById('chatLegend'); if(!el||!ST)return;
  const byCat={};
  const add=(name)=>{if(!name)return;const c=prizeCat(name);const b=byCat[c.k]||(byCat[c.k]={i:c.i,c:c.c,names:[]});if(!b.names.includes(name))b.names.push(name);};
  (ST.prizes.items||[]).forEach(x=>add(x.name));
  (ST.winners.list||[]).forEach(w=>add(w.prize));
  const keys=Object.keys(byCat);
  if(!keys.length){el.style.display='none';return;}
  el.style.display='';
  el.innerHTML='<div class="hint" style="margin:0 0 3px">🎁 당첨 상품 아이콘 — 채팅 이름 옆에 뜹니다</div>'+
    keys.map(k=>{const b=byCat[k];
      return '<div class="lgrow"><span class="wicon">'+b.i+'</span> <b style="color:'+b.c+'">'+esc(k)+'</b> '+
        '<span class="n" style="font-size:11px">'+esc(b.names.join(', '))+'</span></div>';}).join('');
}
function renderRecentWinners(){
  const host=document.getElementById('recentWinners');if(!host||!ST)return;
  const list=ST.winners.list||[];
  const sig=dupMonths+'|'+list.length+'|'+list.map(w=>w.date+w.prize).join(',');
  if(sig===_rwSig)return; _rwSig=sig;
  const cut=new Date(Date.now()-dupMonths*31*864e5).toISOString().slice(0,10);
  const byp={};
  list.forEach(w=>{
    if(!w.date||w.date<cut)return;
    if(/연습/.test(w.how||''))return;
    const key=(w.sid||'').toLowerCase()||norm(w.nick);
    const pp=byp[key]||(byp[key]={nick:w.nick,sid:w.sid||'',date:w.date,cats:{},prizes:[]});
    if(w.date>=pp.date){pp.date=w.date;pp.nick=w.nick;}
    if(w.sid&&!pp.sid)pp.sid=w.sid;
    const c=prizeCat(w.prize);pp.cats[c.k]=c.c;pp.prizes.push({d:w.date,prize:w.prize,c:c.c});
  });
  const arr=Object.values(byp).sort((a,b)=>b.date<a.date?-1:(b.date>a.date?1:0));
  document.querySelectorAll('[data-dupm],[onclick^=\"setDupM\"]').forEach(()=>{});
  document.querySelectorAll('.chip').forEach(b=>{
    const m=(b.getAttribute('onclick')||'').match(/setDupM\((\d)/);
    if(m)b.classList.toggle('on',+m[1]===dupMonths);});
  const lg=document.getElementById('dupLegend');
  if(lg)lg.innerHTML='상품 색 — '+PCATS.map(x=>'<span style=\"color:'+x.c+';font-weight:700\">●</span>'+x.k).join(' &nbsp;');
  if(!arr.length){host.innerHTML='<div class=\"hint\">최근 '+dupMonths+'개월 당첨자가 없습니다.</div>';return;}
  const dk=dupPersonKeys();
  host.innerHTML='<div class=\"hint\" style=\"margin:0 0 4px\">최근 '+dupMonths+'개월 '+arr.length+'명 — 다시 뽑지 않는 게 좋습니다</div>'+
    arr.map(pp=>{
      const isDup=dk.has((pp.sid||'').toLowerCase()||norm(pp.nick));
      const primary=isDup?'#ff4d5a':pp.prizes[pp.prizes.length-1].c;
      const badges=Object.entries(pp.cats).map(([k,c])=>'<span title=\"'+esc(k)+'\" style=\"display:inline-block;width:10px;height:10px;border-radius:3px;background:'+c+';margin-right:2px;vertical-align:middle\"></span>').join('');
      const names=[...new Set(pp.prizes.map(x=>x.prize))].join(', ');
      return '<div class=\"rwrow\" title=\"'+esc(names)+(isDup?' — 같은 상품 중복 당첨!':'')+'\">'+(isDup?'🚨':badges)+' <b style=\"color:'+primary+'\">'+esc(pp.nick)+'</b>'+
        (pp.sid?' <span class=\"pill acc\" style=\"font-size:10px\">'+esc(pp.sid)+'</span>':'')+
        ' <span class=\"n\" style=\"font-size:10.5px\">'+esc(pp.date)+'</span></div>';
    }).join('');
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
  recent.length=0;logBuf.length=0;macroCount=0;
  try{localStorage.removeItem(LSKEY);}catch(e){}
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
function pickThis(n){
  const el=document.getElementById('pickNick');
  el.value=n;dupCheck();
  el.style.background='#12283f';setTimeout(function(){el.style.background='';},450);
  if(window.innerWidth<=760)el.scrollIntoView({block:'center',behavior:'smooth'});
}
function dupCheck(){
  const n=document.getElementById('pickNick').value.trim();
  if(!n){document.getElementById('dupwarn').innerHTML='';return;}
  const [cnt,last]=winCount(n);
  const pz=curPrize();
  const msgs=[];
  if(pz&&hasWonPrize(n,pz))msgs.push('<span class="warn" style="font-weight:800">🚫 이미 이 상품('+esc(pz)+')에 당첨 — 중복!</span>');
  if(cnt)msgs.push('<span class="warn">⚠ 다른 상품 포함 '+cnt+'회 당첨 (마지막 '+esc(last)+')</span>');
  if(settings.excludeWeeks&&recentWin(n))msgs.push('<span class="warn">⚠ 최근 '+settings.excludeWeeks+'주 내 당첨</span>');
  if(inGdoc(n))msgs.push('<span class="warn">⚠ 구글 문서 당첨자 명단에 있음</span>');
  document.getElementById('dupwarn').innerHTML=msgs.length?msgs.join(' '):'<span class="ok">✓ 당첨 기록 없음</span>';
}
document.getElementById('pickNick').addEventListener('input',dupCheck);
document.getElementById('prizeSel').addEventListener('change',dupCheck);
document.getElementById('pickNick').addEventListener('keydown',function(e){if(e.key==='Enter')manualPick();});
document.getElementById('chat').addEventListener('click',function(ev){
  const line=ev.target.closest('.chatline[data-nick]');
  if(line&&line.dataset.nick)pickThis(line.dataset.nick);
});

/* ── 화면 그리기 + 서버 상태 ── */
async function refresh(){
  try{ST=await (await fetch('prize_api.php?act=state')).json();}catch(e){return}
  if(ST.settings&&ST.settings.chatFull)settings=Object.assign(settings,ST.settings);
  rebuildExcl();
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
  renderDupBanner();
  renderChatLegend();
  document.querySelector('#winners tbody').innerHTML=wl.slice().reverse().map(w=>{
    const acc=w.sid||'';
    return '<tr><td>'+esc(w.date)+'</td><td><b>'+esc(w.nick)+'</b></td>'+
    '<td>'+(acc?'<span class="pill acc" style="font-size:11px">'+esc(acc)+'</span>'
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
    ['sGdoc',settings.gdocId||''],['sSlack',settings.slackWebhook||''],
    ['sExclAcc',settings.excludeAccounts||''],
    ['sRealCh',settings.realChannels||'']]){
    const el=document.getElementById(id);
    if(el&&document.activeElement!==el)el.value=v;
  }
  const ex=document.getElementById('sExcl');if(ex)ex.checked=!!settings.excludeWinners;
  rebuildExcl();applyRealCh();
  try{
    const pl=await (await fetch('prize_api.php?act=stats_list')).json();
    document.getElementById('pastdays').innerHTML='<tbody>'+pl.list.map(r=>
      '<tr data-date="'+esc(r.date)+'" title="클릭하면 그날 최종 활약을 봅니다"><td>'+esc(r.date)+' ↗</td><td class="num">'+r.users+'명</td>'+
      '<td class="num">'+r.chats+'</td><td class="num balloon">'+r.balloons+
      '</td></tr>').join('')+'</tbody>';
    document.querySelectorAll('#pastdays [data-date]').forEach(tr=>
      tr.onclick=()=>showPastDay(tr.dataset.date));
  }catch(e){}
}
function paint(){
  document.getElementById('totline').textContent='시청자 '
    +Object.keys(users).length+' · 채팅 '
    +Object.values(users).reduce((a,u)=>a+u.c,0)+' · 별풍선 '
    +Object.values(users).reduce((a,u)=>a+u.b,0)+(macroCount?' · 방송채팅 '+macroCount+' 제외':'');
  const chatEl=document.getElementById('chat');
  // 이미 맨 아래를 보고 있으면 새 글에 맞춰 따라 내려갑니다 (위로 올려 읽는 중이면 안 건드림)
  const atBottom=chatEl.scrollHeight-chatEl.scrollTop-chatEl.clientHeight<40;
  const _wc={};   // 이 렌더 동안 닉별 당첨 정보 캐시 {n, icons}
  function winInfo(nick){
    if(nick in _wc)return _wc[nick];
    const nn=norm(nick), sid=(uid[nick]||'').toLowerCase();
    const wins=(ST?ST.winners.list:[]).filter(w=>norm(w.nick)===nn||(sid&&(w.sid||'').toLowerCase()===sid));
    const cats={};
    wins.forEach(w=>{const c=prizeCat(w.prize);(cats[c.k]||(cats[c.k]={i:c.i,names:[]})).names.push(w.prize);});
    const icons=Object.values(cats).map(x=>'<span class="wicon" title="'+esc([...new Set(x.names)].join(', '))+'">'+x.i+'</span>').join('');
    return (_wc[nick]={n:wins.length, icons:icons});
  }
  function wtitle(nick){
    const w=winInfo(nick);
    return (w.n?'🏆 당첨 '+w.n+'회':'당첨 없음')+' · 눌러서 당첨 만들기에 넣기';
  }
  function wtag(nick){
    const w=winInfo(nick);
    return w.n?' <span class="wtag">(당첨 '+w.n+'회)</span>'+w.icons:'';
  }
  chatEl.innerHTML=recent.slice(-80).map(e=>
    e.t==='balloon'
    ?'<div class="chatline" data-nick="'+esc(e.nick)+'" title="'+esc(wtitle(e.nick))+'">🎈 <b>'+esc(e.nick)+'</b>'+wtag(e.nick)+' <span class="balloon">별풍선 '
      +e.count+'개</span> <span class="pill">'+e.at+'</span></div>'
    :'<div class="chatline" data-nick="'+esc(e.nick)+'" title="'+esc(wtitle(e.nick))+'"><span class="pill" style="margin-right:5px">'+e.at
      +'</span><b>'+esc(e.nick)+'</b>'+wtag(e.nick)+' '+esc(e.msg)+'</div>').join('');
  if(atBottom)chatEl.scrollTop=chatEl.scrollHeight;
  const arr=Object.entries(users).map(([nick,u])=>({nick,c:u.c,b:u.b,wins:winCount(nick)[0]}));
  const medal=['🥇','🥈','🥉'];
  function kingRows(list,valKey,cls,maxv){
    if(!list.length)return '<tr><td colspan="6" style="color:#8a93a6;padding:14px 4px">아직 없습니다</td></tr>';
    return list.slice(0,100).map((u,i)=>{
      const val=u[valKey], pct=Math.round(val/maxv*100);
      return '<tr><td class="num" style="color:#8a93a6">'+(medal[i]||(i+1))+'</td>'+
      '<td><div class="actbar" style="width:'+pct+'%"></div>'+esc(u.nick)+'</td>'+
      '<td class="pill acc" style="font-size:11px">'+esc(uid[u.nick]||'-')+'</td>'+
      '<td class="num '+cls+'">'+val+'</td>'+
      '<td class="num">'+(u.wins?'<span class="warn">'+u.wins+'회</span>':'')+'</td>'+
      '<td><button class="gray" style="padding:2px 8px" data-pick="'+esc(u.nick)+'">지명</button></td></tr>';
    }).join('');
  }
  const byChat=arr.filter(u=>u.c>0).sort((a,b)=>b.c-a.c||b.b-a.b);
  const byBal=arr.filter(u=>u.b>0).sort((a,b)=>b.b-a.b||b.c-a.c);
  document.querySelector('#kingChat tbody').innerHTML=kingRows(byChat,'c','',Math.max(1,...byChat.map(u=>u.c)));
  document.querySelector('#kingBal tbody').innerHTML=kingRows(byBal,'b','balloon',Math.max(1,...byBal.map(u=>u.b)));
  document.querySelectorAll('[data-pick]').forEach(b=>
    b.onclick=()=>pickThis(b.dataset.pick));
  renderRecentWinners();
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
  saveLive();   // 이 브라우저에 즉시 저장 (창을 나가도 안 사라지게 — 가장 확실)
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
/* 창을 나가도(뒤로가기·닫기) 채팅창·집계가 사라지지 않게 이 브라우저에 저장합니다.
   집계 초기화 전까지 유지하고, 이틀 지난 것은 버립니다
   (서버의 날짜별 stats/chatlog 파일이 원본 보관 = 파일화). */
function saveLive(){
  if(IS_TEST_CH)return;
  try{localStorage.setItem(LSKEY,JSON.stringify({
    v:1,sess:sess,users:users,uid:uid,macroCount:macroCount,
    recent:recent.slice(-200),savedEpoch:Date.now()}));}catch(e){}
}
function loadLive(){
  if(IS_TEST_CH)return false;
  try{
    const d=JSON.parse(localStorage.getItem(LSKEY)||'null');
    if(!d)return false;
    if(Date.now()-(d.savedEpoch||0)>2*24*60*60*1000){localStorage.removeItem(LSKEY);return false;}
    if(d.sess){sess.on=!!d.sess.on;sess.date=d.sess.date||'';sess.startedAt=d.sess.startedAt||'';}
    const u=d.users||{};for(const k in u)users[k]=u[k];
    const iu=d.uid||{};for(const k in iu)uid[k]=iu[k];
    if(typeof d.macroCount==='number')macroCount=d.macroCount;
    if(Array.isArray(d.recent)&&recent.length===0)recent.push(...d.recent);
    return true;
  }catch(e){return false;}
}
setInterval(saveLive,3000);
addEventListener('pagehide',saveLive);
async function restoreSession(){
  if(IS_TEST_CH)return;
  const hadLocal=loadLive();   // 이 브라우저에 남은 채팅·집계를 즉시 복원
  sessBtns();paint();
  try{
    const st=await (await fetch('prize_api.php?act=state')).json();
    const sv=(st&&st.session)||{};
    if(!hadLocal){sess.on=!!sv.on;sess.date=sv.date||'';sess.startedAt=sv.startedAt||'';}
    else if(!sess.date&&sv.date){sess.date=sv.date;sess.on=!!sv.on;sess.startedAt=sv.startedAt||'';}
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
applyRealCh();
if(localStorage.getItem('pzMaskAcc'))document.body.classList.add('maskacc');
updateMaskBtn();
initPanels();
initChatResize();
ttPaint();ttRestore();
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
'''


# ── 별풍선 실시간 확인(디버그) 창 ─────────────────────────────
# 관제와 별개로, 들어오는 '선물 후보' 이벤트를 원본 그대로 실시간 표로
# 보여줍니다. 아이템ID 까지 보이므로 '이모티콘/시그니처 별풍선'(같은
# 아이템ID 반복)과 '진짜 별풍선'(아이템ID 제각각)을 눈으로 가릴 수 있습니다.

def prize_balloon_debug():
    return r'''<?php require __DIR__ . '/auth.php'; admin_require_login(); ?>
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
<b class="b18">초록 = 별풍선</b> (svc18 · 중계33 · <b>애드벌룬87 · 방송국애드107</b> — 모두 집계) ·
<b class="etc">회색 = OGQ 이모티콘</b> (집계 안 함) ·
<b class="ad">파랑 = 영상풍선·초콜릿</b> · <b class="sub">보라 = 구독·미션</b>.
별풍선의 아이템 칸은 시그니처 이미지 파일명입니다 (기본 별풍선은 '기본').</div>
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
function classify(svc,f){
  // SOOP 플레이어 공식 상수 기준 (2026-08-21 확인)
  if(svc===18)  return {k:'별풍선', cls:'b18', nick:clean(f[3]),id:clean(f[2]),cnt:f[4],item:(f[8]||'')||'기본'};
  if(svc===33)  return {k:'별풍선(중계)', cls:'b18', nick:clean(f[5]),id:clean(f[4]),cnt:f[6],item:(f[9]||'')||'기본'};
  if(svc===109) return {k:'OGQ 이모티콘(집계 안함)', cls:'etc', nick:clean(f[7]),id:clean(f[6]),cnt:f[4],item:(f[8]||'').split('|')[0]};
  if(svc===87)  return {k:'별풍선(애드벌룬)', cls:'b18', nick:clean(f[4]),id:clean(f[3]),cnt:f[10],item:'애드'};
  if(svc===107) return {k:'별풍선(방송국애드)', cls:'b18', nick:clean(f[3]),id:clean(f[2]),cnt:f[4],item:'방송국애드'};
  if(svc===105) return {k:'영상풍선', cls:'ad', nick:'',id:'',cnt:'',item:'video'};
  if(svc===37)  return {k:'초콜릿', cls:'ad', nick:'',id:'',cnt:'',item:'choco'};
  if(svc===108) return {k:'구독', cls:'sub', nick:clean(f[3]||f[2]),id:clean(f[2]),cnt:'',item:'sub'};
  if(svc===121) return {k:'도전미션', cls:'sub', nick:'',id:'',cnt:'',item:'mission'};
  return {k:'svc '+svc,cls:'etc',nick:'',id:'',cnt:'',item:''};
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
    if([18,33,37,87,105,107,108,109,121].includes(svc))add(svc,f);
  };
  ws.onclose=()=>{clearInterval(pingT);setFlag('연결 끊김 — 다시 붙는 중…');setTimeout(connect,6000);};
  ws.onerror=()=>{try{ws.close()}catch(e){}};
}
connect();
</script></body></html>
'''


# ── 승부토토 공개 리더보드 (predict.php, 사이트 루트·로그인 불필요) ──────
# 오늘의 순위·실시간 배당·접수/실패 피드·시즌 종합 랭킹.

def prize_predict_board():
    return r'''<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>시청자 승부예측 — 끝장전</title><style>
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
<h1>🔮 끝장전 시청자 승부예측</h1>
<div class="sub">채팅으로 참여하는 가상 포인트 승부예측 · <span id="upd" class="pill">불러오는 중…</span>
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
'''
