# -*- coding: utf-8 -*-
"""관리자 로그인 (PHP). 카페24처럼 PHP 가 도는 곳에서 CG 툴을 가려 줍니다.

자바스크립트로 비밀번호를 확인하는 방식은 소스 보기 한 번이면 뚫리므로
쓰지 않았습니다. 여기서는 서버가 세션으로 판단합니다.

비밀번호는 저장소에 넣지 않습니다. 처음 접속하면 아이디·비밀번호를 정하는
화면이 뜨고, 그때 서버에 admin/config.php 가 만들어집니다 (bcrypt 해시).
"""

AUTH_PHP = r'''<?php
// 관리자 인증 공통 — 로그인 여부 판단과 세션 설정만 합니다.
declare(strict_types=1);

const ADMIN_CONFIG = __DIR__ . '/config.php';
const LOGIN_WINDOW = 600;    // 10분 동안
const LOGIN_TRIES  = 8;      // 8번 틀리면 잠급니다

function admin_boot(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }
    $https = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
        || (($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https');
    session_set_cookie_params([
        'lifetime' => 0,
        'path' => rtrim(dirname($_SERVER['SCRIPT_NAME'] ?? '/'), '/') . '/',
        'httponly' => true,
        'samesite' => 'Lax',
        'secure' => $https,
    ]);
    session_name('SCADMIN');
    session_start();
}

/** 설정 파일이 있으면 배열로, 없으면 null. */
function admin_config(): ?array
{
    if (!is_file(ADMIN_CONFIG)) {
        return null;
    }
    $cfg = include ADMIN_CONFIG;
    return (is_array($cfg) && isset($cfg['user'], $cfg['hash'])) ? $cfg : null;
}

function admin_save_config(string $user, string $password): bool
{
    $php = "<?php\n// 관리자 계정. 이 파일은 저장소에 올리지 마세요.\nreturn "
        . var_export(['user' => $user,
                      'hash' => password_hash($password, PASSWORD_DEFAULT)], true)
        . ";\n";
    $ok = @file_put_contents(ADMIN_CONFIG, $php, LOCK_EX) !== false;
    if ($ok) {
        @chmod(ADMIN_CONFIG, 0600);
    }
    return $ok;
}

function admin_logged_in(): bool
{
    admin_boot();
    return !empty($_SESSION['admin_user']);
}

/** 로그인 안 했으면 로그인 화면으로 보냅니다. */
function admin_require_login(): void
{
    if (admin_logged_in()) {
        return;
    }
    $to = basename($_SERVER['SCRIPT_NAME'] ?? '');
    header('Location: index.php' . ($to ? '?next=' . rawurlencode($to) : ''));
    exit;
}

function admin_user(): string
{
    admin_boot();
    return (string)($_SESSION['admin_user'] ?? '');
}

/** 남은 시도 횟수. 0 이면 잠긴 상태입니다. */
function admin_tries_left(): int
{
    admin_boot();
    $f = $_SESSION['fail'] ?? null;
    if (!$f || (time() - $f['at']) > LOGIN_WINDOW) {
        return LOGIN_TRIES;
    }
    return max(0, LOGIN_TRIES - $f['n']);
}

function admin_note_fail(): void
{
    admin_boot();
    $f = $_SESSION['fail'] ?? null;
    if (!$f || (time() - $f['at']) > LOGIN_WINDOW) {
        $f = ['n' => 0, 'at' => time()];
    }
    $f['n']++;
    $f['at'] = time();
    $_SESSION['fail'] = $f;
}

function admin_login(string $user, string $password): bool
{
    admin_boot();
    if (admin_tries_left() <= 0) {
        return false;
    }
    $cfg = admin_config();
    if (!$cfg) {
        return false;
    }
    // 아이디가 틀려도 같은 시간이 걸리도록 항상 검증을 돌립니다.
    $userOk = hash_equals((string)$cfg['user'], $user);
    $passOk = password_verify($password, (string)$cfg['hash']);
    if (!($userOk && $passOk)) {
        admin_note_fail();
        return false;
    }
    session_regenerate_id(true);          // 세션 고정 공격 방어
    $_SESSION['admin_user'] = $cfg['user'];
    unset($_SESSION['fail']);
    return true;
}

function admin_logout(): void
{
    admin_boot();
    $_SESSION = [];
    if (ini_get('session.use_cookies')) {
        $p = session_get_cookie_params();
        setcookie(session_name(), '', time() - 42000,
                  $p['path'], $p['domain'], $p['secure'], $p['httponly']);
    }
    session_destroy();
}

function admin_csrf(): string
{
    admin_boot();
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(16));
    }
    return $_SESSION['csrf'];
}

function admin_csrf_ok(?string $token): bool
{
    admin_boot();
    return !empty($_SESSION['csrf']) && is_string($token)
        && hash_equals($_SESSION['csrf'], $token);
}
'''

LOGOUT_PHP = r'''<?php
require __DIR__ . '/auth.php';
admin_logout();
header('Location: index.php');
'''

HTACCESS = r'''# 설정 파일과 인증 코드는 직접 열 수 없게 막습니다.
<FilesMatch "^(config\.php|config\.sample\.php|auth\.php)$">
  <IfModule mod_authz_core.c>
    Require all denied
  </IfModule>
  <IfModule !mod_authz_core.c>
    Order allow,deny
    Deny from all
  </IfModule>
</FilesMatch>

# 폴더 목록이 그대로 보이지 않게 합니다.
Options -Indexes

DirectoryIndex index.php index.html
'''

CONFIG_SAMPLE = r'''<?php
// admin/config.php 예시입니다. 실제 파일은 처음 접속했을 때 자동으로 만들어집니다.
// 손으로 만들 때는 아래처럼 쓰고 파일 이름을 config.php 로 바꾸세요.
// hash 는 password_hash('원하는비밀번호', PASSWORD_DEFAULT) 결과입니다.
return [
    'user' => 'admin',
    'hash' => '$2y$10$여기에비크립트해시를넣으세요..............................',
];
'''


def index_php(css, site_name):
    """로그인 화면. 설정 파일이 없으면 최초 설정 화면이 됩니다."""
    return (
        '''<?php
require __DIR__ . '/auth.php';
admin_boot();

$cfg      = admin_config();
$setup    = ($cfg === null);          // 아직 계정이 없으면 최초 설정
$error    = '';
$notice   = '';
$next     = preg_replace('/[^A-Za-z0-9._-]/', '', $_GET['next'] ?? '');
$nextUrl  = $next !== '' ? $next : 'cg.php';

if (admin_logged_in() && !$setup) {
    header('Location: ' . $nextUrl);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!admin_csrf_ok($_POST['csrf'] ?? null)) {
        $error = '입력 시간이 너무 오래되었습니다. 다시 시도해 주세요.';
    } elseif ($setup) {
        $u  = trim((string)($_POST['user'] ?? ''));
        $p1 = (string)($_POST['pw'] ?? '');
        $p2 = (string)($_POST['pw2'] ?? '');
        if ($u === '' || !preg_match('/^[A-Za-z0-9._-]{3,32}$/', $u)) {
            $error = '아이디는 영문·숫자·. _ - 로 3~32자로 지어 주세요.';
        } elseif (mb_strlen($p1) < 8) {
            $error = '비밀번호는 8자 이상으로 정해 주세요.';
        } elseif ($p1 !== $p2) {
            $error = '두 비밀번호가 서로 다릅니다.';
        } elseif (!admin_save_config($u, $p1)) {
            $error = 'admin 폴더에 쓸 수 없습니다. FTP 에서 admin 폴더 권한을 707 로 바꾼 뒤 다시 해 주세요.';
        } else {
            admin_login($u, $p1);
            header('Location: ' . $nextUrl);
            exit;
        }
    } else {
        if (admin_tries_left() <= 0) {
            $error = '로그인을 여러 번 실패했습니다. 10분 뒤에 다시 시도해 주세요.';
        } elseif (admin_login((string)($_POST['user'] ?? ''), (string)($_POST['pw'] ?? ''))) {
            header('Location: ' . $nextUrl);
            exit;
        } else {
            $left  = admin_tries_left();
            $error = '아이디 또는 비밀번호가 맞지 않습니다.'
                   . ($left > 0 && $left <= 3 ? ' (남은 시도 ' . $left . '번)' : '');
            usleep(400000);          // 무차별 대입을 조금이라도 늦춥니다
        }
    }
}
$csrf = admin_csrf();
?>
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>관리자 로그인 — ''' + site_name + '''</title>
<link rel="stylesheet" as="style"
  href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
<style>
''' + css + '''
.loginwrap{max-width:400px;margin:0 auto;padding:70px 20px 60px}
.loginwrap h1{font-size:22px;margin-bottom:6px}
.loginwrap .sub{margin-bottom:22px}
.loginwrap .fld{margin-bottom:13px}
.loginwrap input[type=text],.loginwrap input[type=password]{width:100%;padding:11px 12px;
  border-radius:9px;background:var(--panel2);border:1px solid var(--line);
  color:var(--txt);font-size:14px;font-family:inherit}
.loginwrap input:focus{outline:none;border-color:var(--accent)}
.loginwrap .btn{width:100%;padding:12px;margin-top:6px;font-size:14px}
.msg{padding:10px 12px;border-radius:9px;font-size:12.5px;margin-bottom:14px;line-height:1.6}
.msg.err{background:rgba(248,113,113,.10);border:1px solid var(--lose);color:var(--lose)}
.msg.info{background:rgba(28,140,255,.10);border:1px solid var(--accent);color:#cfe6ff}
</style>
</head>
<body>
<div class="brandbar"></div>
<div class="loginwrap">
  <h1><?= $setup ? '관리자 계정 만들기' : '관리자 로그인' ?></h1>
  <div class="sub">CG 제작 툴은 관리자만 쓸 수 있습니다.</div>

<?php if ($error !== ''): ?>
  <div class="msg err"><?= htmlspecialchars($error, ENT_QUOTES) ?></div>
<?php endif; ?>
<?php if ($setup): ?>
  <div class="msg info">아직 계정이 없습니다. 지금 바로 아이디와 비밀번호를 정해 주세요.
  이 화면은 계정을 만들면 다시 나오지 않습니다.</div>
<?php endif; ?>

  <form method="post" autocomplete="off">
    <input type="hidden" name="csrf" value="<?= htmlspecialchars($csrf, ENT_QUOTES) ?>">
    <div class="fld"><label>아이디</label>
      <input type="text" name="user" autofocus required
             autocomplete="<?= $setup ? 'off' : 'username' ?>"></div>
    <div class="fld"><label>비밀번호</label>
      <input type="password" name="pw" required
             autocomplete="<?= $setup ? 'new-password' : 'current-password' ?>"></div>
<?php if ($setup): ?>
    <div class="fld"><label>비밀번호 확인</label>
      <input type="password" name="pw2" required autocomplete="new-password"></div>
<?php endif; ?>
    <button class="btn primary" type="submit"><?= $setup ? '계정 만들고 시작하기' : '로그인' ?></button>
  </form>

  <div class="helptxt" style="margin-top:18px">
    <a href="../index.html" style="color:var(--accent)">← 기록실로 돌아가기</a>
  </div>
</div>
</body>
</html>
''')
