<?php
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
<title>관리자 로그인 — 스타크래프트 끝장전 기록실</title>
<link rel="stylesheet" as="style"
  href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
<style>
:root{
  --bg:#0a0d13; --panel:#141821; --panel2:#1b202b; --line:#232a38; --line2:#171c25;
  --txt:#e8ecf3; --dim:#8a93a6; --accent:#1c8cff; --gold:#ffb020;
  --win:#4ade80; --lose:#f87171;
  --t:#4a9eff; --p:#f5c518; --z:#ff6b6b;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);
  font-family:'Pretendard','Malgun Gothic','맑은 고딕',system-ui,sans-serif;
  font-size:14px;-webkit-text-size-adjust:100%}
a{color:inherit;text-decoration:none}
/* 누르라고 만든 것들은 눌러도 글자가 잡히거나 커서가 깜빡이지 않게 합니다. */
.tab,.chip,th,.rowlink,.score-cell,.spoiler,.dlbtn,.backlink,.linkbtn,
.yt-mini,.vmodal-close,.navlink,.srow,.caret,.race,.rk{
  -webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
.rowlink,.score-cell,.tab,.chip,th[data-key]{cursor:pointer}
:focus{outline:none}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.brandbar{height:4px;background:linear-gradient(90deg,var(--t) 0%,var(--accent) 35%,var(--gold) 70%,var(--z) 100%)}
.wrap{max-width:1180px;margin:0 auto;padding:26px 20px 80px}

/* ── 헤더 ─────────────────────────────────────────── */
header{padding-bottom:18px;border-bottom:1px solid var(--line);position:relative;overflow:hidden}
header::before{content:'';position:absolute;inset:0;pointer-events:none;opacity:.06;
  background-image:repeating-linear-gradient(115deg,var(--accent) 0 2px,transparent 2px 26px);
  -webkit-mask-image:linear-gradient(180deg,#000,transparent);mask-image:linear-gradient(180deg,#000,transparent)}
.headrow{display:flex;align-items:center;gap:14px;position:relative}
.brandlogo{width:48px;height:48px;border-radius:50%;object-fit:cover;flex:none;
  border:2px solid var(--accent);box-shadow:0 0 0 4px rgba(28,140,255,.15)}
h1{margin:0;font-size:26px;letter-spacing:-.02em;
  background:linear-gradient(90deg,var(--accent),var(--gold));-webkit-background-clip:text;
  background-clip:text;color:transparent}
h1 a{color:transparent}
.sub{color:var(--dim);font-size:13px;margin-top:6px}
.stats-strip{display:flex;gap:22px;flex-wrap:wrap;margin-top:14px}
.stats-strip .item{color:var(--dim);font-size:12.5px}
.stats-strip b{color:var(--txt);font-size:15px;display:block;font-variant-numeric:tabular-nums}

/* ── 바로가기 배너 ────────────────────────────────── */
.linkbanner{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0 0}
.linkbtn{display:flex;flex-direction:column;gap:2px;padding:9px 14px;border-radius:9px;
  background:var(--panel);border:1px solid var(--line);font-weight:700;font-size:13px}
.linkbtn:hover{border-color:var(--accent)}
.linkbtn .sub2{color:var(--dim);font-weight:500;font-size:11px}
.linkbtn.yt:hover{border-color:#ff3d3d}
.yt-ico{color:#ff3d3d}

/* ── 라이브 배너 ──────────────────────────────────── */
.livecard{margin-top:14px;border:1px solid var(--line);border-radius:12px;
  background:var(--panel);overflow:hidden}
.livecard.live{border-color:#ff3d3d;box-shadow:0 0 0 3px rgba(255,61,61,.10)}
.live-head{display:flex;align-items:center;gap:9px;padding:11px 14px;flex-wrap:wrap}
.live-dot{width:9px;height:9px;border-radius:50%;background:#ff3d3d;flex:none;
  box-shadow:0 0 0 0 rgba(255,61,61,.7);animation:pulse 1.6s infinite}
@keyframes pulse{70%{box-shadow:0 0 0 9px rgba(255,61,61,0)}100%{box-shadow:0 0 0 0 rgba(255,61,61,0)}}
.live-badge{color:#ff3d3d;font-weight:900;font-size:12px;letter-spacing:.08em}
.live-title{font-weight:700;font-size:13.5px;flex:1;min-width:150px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.live-viewer{color:var(--dim);font-size:12px}
.live-off{padding:0 14px 12px;color:var(--dim);font-size:12.5px}
.live-off a{color:var(--accent);text-decoration:underline}
.live-thumb-link{display:block;position:relative}
.live-thumb{width:100%;display:block;aspect-ratio:16/9;object-fit:cover;background:#000}
.live-play{position:absolute;left:0;right:0;bottom:0;padding:10px 14px;font-weight:800;
  font-size:13px;background:linear-gradient(180deg,transparent,rgba(0,0,0,.82))}

/* ── 탭 / 칩 ──────────────────────────────────────── */
.tabs{display:flex;gap:6px;margin:20px 0 12px;flex-wrap:wrap}
.tab{padding:8px 15px;border-radius:8px;background:var(--panel);color:var(--dim);
  cursor:pointer;font-weight:600;font-size:13px;border:1px solid transparent}
.tab:hover{color:var(--txt)}
.tab.on{color:#fff;background:linear-gradient(135deg,var(--accent),#0d5fc4);
  box-shadow:0 2px 10px rgba(28,140,255,.35)}
.tab .n{opacity:.6;margin-left:6px;font-size:11px}

.chips{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap;align-items:center}
.chip{padding:5px 12px;border-radius:999px;background:var(--panel);color:var(--dim);
  cursor:pointer;font-weight:700;font-size:12px;border:1px solid var(--line)}
.chip:hover{color:var(--txt)}
.chip.on{color:#fff;background:var(--accent);border-color:var(--accent)}
.chiplabel{color:var(--dim);font-size:11.5px;letter-spacing:.05em;margin-right:2px}

input.search{width:100%;max-width:280px;padding:8px 12px;border-radius:8px;
  background:var(--panel);border:1px solid var(--line);color:var(--txt);
  font-size:13px;margin-bottom:12px}
input.search::placeholder{color:var(--dim)}
input.search:focus{outline:none;border-color:var(--accent)}

/* ── 표 ───────────────────────────────────────────── */
.tblwrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{padding:10px 12px;text-align:left;white-space:nowrap}
th{color:var(--dim);font-size:11px;font-weight:600;letter-spacing:.06em;
  border-bottom:1px solid var(--line);cursor:pointer;user-select:none}
th.static{cursor:default}
td{border-bottom:1px solid var(--line2)}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:#161b25}
.num{text-align:right;font-variant-numeric:tabular-nums}
.rowlink{cursor:pointer}
.rk{display:inline-block;min-width:22px;color:var(--dim);font-size:12px;
  font-variant-numeric:tabular-nums}
.nm{font-weight:700}
.nm-link{font-weight:700;cursor:pointer;border-bottom:1px dotted transparent}
.nm-link:hover{color:var(--accent);border-bottom-color:var(--accent)}
.pct{color:var(--dim);font-size:12px;margin-left:4px}
.muted,.dim{color:var(--dim)}
.win{color:var(--win)}
.lose{color:var(--lose)}
.race{display:inline-block;width:18px;height:18px;line-height:18px;text-align:center;
  border-radius:5px;font-size:10.5px;font-weight:900;color:#0b0d11;margin-right:6px;flex:none}
.race.T{background:var(--t)} .race.P{background:var(--p)} .race.Z{background:var(--z)}

/* ── 카드 ─────────────────────────────────────────── */
.card{border:1px solid var(--line);border-radius:12px;background:var(--panel);
  padding:14px;margin-bottom:14px}
.card > .tblwrap{border:none;border-radius:0;background:transparent}
.cardtitle{font-weight:800;font-size:14.5px;margin-bottom:10px;display:flex;
  align-items:center;gap:8px;flex-wrap:wrap}
.cardtitle .note{color:var(--dim);font-weight:500;font-size:11.5px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}

/* ── 상성 막대 ────────────────────────────────────── */
.mubar{display:flex;height:24px;border-radius:6px;overflow:hidden;margin:6px 0 4px;
  background:var(--panel2)}
.mubar span{display:flex;align-items:center;justify-content:center;font-size:11px;
  font-weight:800;color:#0b0d11;min-width:0;overflow:hidden;white-space:nowrap}
.murow{margin-bottom:12px}
.murow:last-child{margin-bottom:0}
.mulabel{display:flex;justify-content:space-between;font-size:12px;color:var(--dim)}
.mulabel b{color:var(--txt)}

/* ── 스파크라인(연도별 사용) ──────────────────────── */
.spark{display:inline-flex;align-items:flex-end;gap:2px;height:20px}
.spark i{display:block;width:5px;background:var(--accent);opacity:.55;border-radius:1px}
.spark i.on{opacity:1}

/* ── 내려받기 상자 (보조 기능이라 눈에 덜 띄게) ───── */
.dlbox{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-top:16px;
  padding:12px 14px;border:1px solid var(--line);border-radius:12px;
  background:var(--panel);font-size:12px;opacity:.78}
.dlbox:hover{opacity:1}
.dlbox .t{color:var(--dim);font-size:11.5px;letter-spacing:.02em;margin-right:2px}
.dlbtn{padding:4px 10px;border-radius:6px;background:transparent;color:var(--dim);
  border:1px solid var(--line);font-weight:600;font-size:11.5px}
.dlbtn:hover{color:var(--txt);border-color:var(--accent)}
.dlbtn.on{color:var(--txt);border-color:var(--accent)}

/* ── 영상 ─────────────────────────────────────────── */
.yt-mini{color:#ff6b6b;font-weight:700;font-size:12px;cursor:pointer;white-space:nowrap}
.yt-mini:hover{text-decoration:underline}
.yt-fallback{color:var(--dim);font-weight:600}
.vmodal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:60;
  align-items:center;justify-content:center;padding:20px}
.vmodal.on{display:flex}
.vmodal-box{width:100%;max-width:960px}
.vmodal-close{display:block;margin:0 0 10px auto;background:transparent;color:var(--txt);
  border:1px solid var(--line);border-radius:8px;padding:6px 12px;cursor:pointer;
  font-size:13px;font-family:inherit}
.vmodal-frame{position:relative;padding-top:56.25%;background:#000;border-radius:10px;overflow:hidden}
.vmodal-frame iframe{position:absolute;inset:0;width:100%;height:100%;border:0}

/* ── 스포일러 ─────────────────────────────────────── */
.score-cell{cursor:pointer}
.spoiler{display:inline-block;padding:3px 9px;border-radius:6px;background:var(--panel2);
  color:var(--dim);font-size:11.5px;font-weight:600;border:1px solid var(--line)}
.score-cell:hover .spoiler{color:var(--txt);border-color:var(--accent)}

/* ── 선수 페이지 ──────────────────────────────────── */
.backlink{color:var(--dim);font-size:13px;margin:16px 0 12px;display:inline-block;cursor:pointer}
.backlink:hover{color:var(--accent)}
.phead{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.phead .race{width:26px;height:26px;line-height:26px;font-size:13px;border-radius:7px}
.pname{font-size:22px;font-weight:900;letter-spacing:-.01em}
.ptag{padding:3px 9px;border-radius:999px;border:1px solid var(--line);
  color:var(--dim);font-size:11.5px;font-weight:700}
.streak-w{color:var(--win)} .streak-l{color:var(--lose)}

/* ── 푸터 ─────────────────────────────────────────── */
footer{margin-top:28px;padding-top:16px;border-top:1px solid var(--line);
  color:var(--dim);font-size:12px;line-height:1.8}
footer a{color:var(--accent);text-decoration:underline}
.legal{margin-top:8px;font-size:11px;opacity:.75;line-height:1.7}

/* ── 안내 문단 ────────────────────────────────────── */
.hint{color:var(--dim);font-size:12px;margin-top:8px;line-height:1.7}
.emptybox{padding:26px 14px;text-align:center;color:var(--dim);font-size:13px}

/* ── 코드 (시트 연동 안내) ────────────────────────── */
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
pre{background:var(--panel2);border:1px solid var(--line);border-radius:8px;
  padding:11px 13px;overflow-x:auto;font-size:12.5px;margin:8px 0;color:#cfe6ff}
code.inline{background:var(--panel2);border:1px solid var(--line);border-radius:5px;
  padding:1px 5px;font-size:12px;color:#cfe6ff}
ol.steps{padding-left:20px;line-height:2}
ol.steps li{margin-bottom:4px}

@media (max-width:640px){
  .wrap{padding:20px 13px 60px}
  h1{font-size:21px}
  .hide-mobile{display:none}
  th,td{padding:9px 9px}
  .stats-strip{gap:14px}
}

/* ── 사이트 전환 바 ───────────────────────────────── */
.sitenav{display:flex;gap:4px;margin:0 0 18px;flex-wrap:wrap}
.navlink{padding:7px 16px;border-radius:8px;background:var(--panel);color:var(--dim);
  font-weight:700;font-size:13px;border:1px solid var(--line)}
.navlink:hover{color:var(--txt);border-color:var(--accent)}
.navlink.on{color:#0b0d11;background:var(--gold);border-color:var(--gold)}

/* ── 펼쳐지는 대회 목록 (ASL) ─────────────────────── */
.tourlist{border:1px solid var(--line);border-radius:12px;background:var(--panel);overflow:hidden}
.srow{display:grid;grid-template-columns:1fr 78px 78px 62px 224px 22px;
  align-items:center;gap:10px;padding:13px 14px;cursor:pointer;
  border-top:1px solid var(--line2)}
.srow:first-child{border-top:none}
.srow:hover{background:#161b25}
.srow.thead{background:transparent;border:none;cursor:default;padding:0 14px 8px;
  color:var(--dim);font-size:11px;font-weight:600;letter-spacing:.06em}
.srow.thead:hover{background:none}
.srow .ch{font-size:12.5px;color:var(--dim);overflow:hidden;padding-left:14px;
  text-overflow:ellipsis;white-space:nowrap}
.caret{color:var(--dim);font-size:11px;text-align:center;transition:transform .15s}
.srow.open .caret{transform:rotate(90deg)}
.stages{display:none;background:#0f1319;border-top:1px solid var(--line2)}
.stages.open{display:block}
.stlabel{padding:13px 20px 2px;color:var(--dim);font-size:11.5px;letter-spacing:.06em}
.offbox{padding:12px 20px;border-bottom:1px solid var(--line2);font-size:12.5px}
.stages .tblwrap{border:none;background:transparent;border-radius:0}
.stages td{border-bottom:1px solid var(--line2)}

@media (max-width:760px){
  .srow{grid-template-columns:1fr 60px 60px 20px}
  .srow > :nth-child(4),.srow.thead > :nth-child(4){display:none}
  .srow .ch{display:none}
}

/* ── CG 제작 툴 ───────────────────────────────────── */
.cgwrap{max-width:none;padding:22px 22px 60px}
.cglayout{display:grid;grid-template-columns:380px minmax(0,1fr);gap:20px;align-items:start}
.cgpanel{position:sticky;top:16px;max-height:calc(100vh - 40px);overflow-y:auto;
  padding-right:6px}
.cgpanel::-webkit-scrollbar{width:8px}
.cgpanel::-webkit-scrollbar-thumb{background:var(--line);border-radius:4px}
.cgstage{border:1px solid var(--line);border-radius:12px;background:#0e1015;padding:12px}
#cv{width:100%;height:auto;display:block;border-radius:6px;background:#15171c;
  cursor:grab;box-shadow:0 8px 30px rgba(0,0,0,.5)}
#cv:active{cursor:grabbing}

.fld{margin-bottom:11px}
.fld > label{display:block;color:var(--dim);font-size:11.5px;font-weight:600;
  letter-spacing:.04em;margin-bottom:5px}
.fld input[type=text],.fld select,.fld textarea{width:100%;padding:8px 10px;border-radius:8px;
  background:var(--panel2);border:1px solid var(--line);color:var(--txt);
  font-size:13px;font-family:inherit}
.fld textarea{min-height:96px;resize:vertical;line-height:1.6}
.fld input[type=text]:focus,.fld select:focus,.fld textarea:focus{
  outline:none;border-color:var(--accent)}
.fld input[type=range]{width:100%;accent-color:var(--accent)}
.fld input[type=color]{width:46px;height:32px;padding:2px;border-radius:7px;
  background:var(--panel2);border:1px solid var(--line);cursor:pointer}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:9px}
.row-inline{display:flex;gap:9px;align-items:center}
.filebtn{display:inline-block;padding:7px 11px;border-radius:7px;background:var(--panel2);
  border:1px solid var(--line);color:var(--dim);font-size:12px;font-weight:600;cursor:pointer}
.filebtn:hover{color:var(--txt);border-color:var(--accent)}
.filebtn input{display:none}
.btn{padding:9px 14px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);
  color:var(--txt);font-family:inherit;font-size:13px;font-weight:700;cursor:pointer}
.btn:hover{border-color:var(--accent)}
.btn.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.btn.primary:hover{filter:brightness(1.08)}
.btn.danger:hover{border-color:var(--lose);color:var(--lose)}
.btnrow{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}
.note{color:var(--dim);font-size:11.5px;margin-top:8px;min-height:16px;line-height:1.6}
.note.bad{color:var(--gold)}
.helptxt{color:var(--dim);font-size:11.5px;line-height:1.75;margin-top:6px}
.helptxt code{background:var(--panel2);border:1px solid var(--line);border-radius:4px;
  padding:1px 5px;font-size:11px;color:#cfe6ff}

@media (max-width:1000px){
  .cglayout{grid-template-columns:1fr}
  .cgpanel{position:static;max-height:none}
}

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
