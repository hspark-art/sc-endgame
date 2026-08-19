<?php require __DIR__ . '/auth.php'; admin_require_login(); ?>
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CG 제작 툴 — 스타크래프트 끝장전 기록실</title>
<meta name="description" content="끝장전 대진표 CG(1920×1080)를 만들어 PNG 로 내려받는 방송용 도구.">
<link rel="canonical" href="https://pubgin.com/endgame/admin/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="스타크래프트 끝장전 기록실">
<meta property="og:title" content="CG 제작 툴 — 스타크래프트 끝장전 기록실">
<meta property="og:description" content="끝장전 대진표 CG(1920×1080)를 만들어 PNG 로 내려받는 방송용 도구.">
<meta property="og:url" content="https://pubgin.com/endgame/admin/">
<meta property="og:image" content="https://stimg.sooplive.com/LOGO/ta/talent/m/talent.webp">
<meta name="twitter:card" content="summary">
<meta name="robots" content="noindex, nofollow">
<link rel="icon" href="https://stimg.sooplive.com/LOGO/ta/talent/m/talent.webp">
<link rel="stylesheet" as="style" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
<style>
:root{
  --bg:#0a0d13; --panel:#141821; --panel2:#1b202b; --line:#232a38; --line2:#171c25;
  --txt:#e8ecf3; --dim:#8a93a6; --accent:#1c8cff; --gold:#ffb020;
  --win:#4ade80; --lose:#f87171;
  --t:#4a9eff; --p:#f5c518; --z:#ff6b6b;
}
*{box-sizing:border-box}
/* hidden 속성이 항상 이기도록. display 를 지정한 요소에 hidden 을 걸면
   작성자 규칙이 브라우저 기본값을 눌러 버려서 계속 보입니다. */
[hidden]{display:none !important}
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

/* ── 상대 전적 ─────────────────────────────────────────────── */
.h2hpanel{display:flex;flex-wrap:wrap;align-items:flex-end;gap:8px;
  border:1px solid var(--line);border-radius:12px;background:var(--panel);
  padding:12px;margin-bottom:12px}
.h2hside{display:flex;flex-direction:column;gap:6px;flex:1 1 150px;min-width:0}
.h2hside.wide{flex:1 1 220px}
.h2hcap{font-size:11px;color:var(--dim)}
.h2hsel{width:100%;padding:8px 10px;border-radius:8px;font-size:13px;
  background:var(--panel2);color:var(--txt);border:1px solid var(--line);
  font-family:inherit;-webkit-appearance:none;appearance:none;
  background-image:url("data:image/svg+xml;charset=utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 8'%3E%3Cpath fill='%238a93a6' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 10px center;background-size:10px;
  padding-right:26px}
.h2hsel:focus{border-color:var(--accent)}
/* 경기 기록을 대회·라운드로 묶을 때 그 사이에 끼우는 제목줄 */
.grouphead td{background:var(--panel2);border-top:2px solid var(--line);
  padding:9px 10px !important}
.grouphead .gtour{font-weight:700;color:var(--txt);font-size:13px}
.grouphead .ground{margin-left:8px;padding:2px 8px;border-radius:999px;
  background:var(--panel);border:1px solid var(--line);
  color:var(--accent);font-size:11px;font-weight:700}
.grouphead .note{margin-left:8px;color:var(--dim);font-size:11px;font-weight:500}
tbody tr.grouphead:first-child td{border-top:none}
/* 선수 칸 — 직접 치면 아래로 목록이 펼쳐집니다 (목록을 직접 그립니다). */
.h2hpick{position:relative}
.h2hinput{padding-right:30px;
  background-image:url("data:image/svg+xml;charset=utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cg fill='none' stroke='%238a93a6' stroke-width='1.6'%3E%3Ccircle cx='7' cy='7' r='4.2'/%3E%3Cpath d='M10.2 10.2L14 14' stroke-linecap='round'/%3E%3C/g%3E%3C/svg%3E");
  background-size:13px}
.h2hclear{position:absolute;right:4px;top:50%;transform:translateY(-50%);
  width:22px;height:22px;line-height:1;border:0;border-radius:6px;cursor:pointer;
  background:transparent;color:var(--dim);font-size:16px;font-family:inherit}
.h2hclear:hover{background:var(--panel);color:var(--txt)}
.h2hdrop{position:absolute;left:0;right:0;top:calc(100% + 4px);z-index:40;
  max-height:264px;overflow-y:auto;border-radius:10px;
  background:var(--panel2);border:1px solid var(--line);
  box-shadow:0 12px 28px rgba(0,0,0,.45)}
.h2hopt{display:flex;align-items:center;gap:8px;padding:8px 10px;cursor:pointer;
  font-size:13px;border-bottom:1px solid rgba(255,255,255,.04)}
.h2hopt:last-child{border-bottom:0}
.h2hopt:hover,.h2hopt.on{background:var(--panel)}
.h2hoptname{font-weight:600;color:var(--txt)}
.h2hoptrace{flex:0 0 auto;width:17px;height:17px;line-height:17px;text-align:center;
  border-radius:5px;font-size:10px;font-weight:800;color:#0b0d11}
.h2hoptrace.r-T{background:#7cc0ff}
.h2hoptrace.r-P{background:#ffd166}
.h2hoptrace.r-Z{background:#ff8fa3}
.h2hoptnum{margin-left:auto;color:var(--dim);font-size:11px}
.h2hempty{padding:12px 10px;color:var(--dim);font-size:12px;text-align:center}
.h2hvs{flex:0 0 auto;color:var(--dim);font-size:12px;font-weight:700;
  padding:0 2px 10px;align-self:flex-end}
.h2hreset{margin-bottom:0}
.h2hhead{text-align:center}
.h2hnames{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;
  gap:8px;font-size:16px;font-weight:700}
.h2hvs2{color:var(--dim);font-size:12px;font-weight:400}
.h2hscore{display:flex;align-items:baseline;justify-content:center;gap:4px;
  margin-top:8px;font-size:26px;font-weight:800}
.h2hscore .dim{font-size:13px;font-weight:400}
.h2hdash{color:var(--dim);font-size:16px;margin:0 4px}
.h2hrate{margin-left:10px;font-size:15px;font-weight:700;color:var(--accent)}
.h2hbar{max-width:420px;margin:10px auto 4px}
.h2hbar span:first-child{background:var(--win)}
.h2hbar span:last-child{background:var(--lose)}
.h2hquick{justify-content:center;margin-top:8px}
@media (max-width:520px){
  .h2hvs{display:none}
  .h2hside{flex:1 1 100%}
  .h2hscore{font-size:22px}
}

/* 관리자(CG 제작) 입구 — 눈에 띄지 않게 맨 아래 구석에 둡니다. */
.gear{display:block;width:15px;height:15px;margin:14px auto 0;color:var(--line);
  opacity:.5;transition:opacity .15s,color .15s;-webkit-tap-highlight-color:transparent}
.gear:hover,.gear:focus-visible{opacity:1;color:var(--dim)}

/* 선수 사진 — img/players/<슬러그>.jpg 를 넣으면 자동으로 붙습니다. */
.pphoto{width:56px;height:56px;border-radius:50%;object-fit:cover;object-position:center top;
  border:2px solid var(--line);background:var(--panel2);flex:0 0 auto}
.rphoto{width:26px;height:26px;border-radius:50%;object-fit:cover;object-position:center top;
  border:1px solid var(--line);background:var(--panel2);vertical-align:middle;margin-right:6px}
</style>
</head>
<body>
<div class="brandbar"></div>
<div class="wrap cgwrap">
<nav class="sitenav"><a class="navlink" href="../index.html">← 사이트로 돌아가기</a></nav>
<header style="border-bottom:none;padding-bottom:6px"><div class="headrow"><div><h1>CG 제작 툴</h1><div class="sub">대진표 이미지를 만들어 PNG(1920×1080)로 내려받습니다. 입력한 내용은 이 브라우저에 자동 저장됩니다.</div></div><div style="margin-left:auto;text-align:right"><div class="helptxt" style="margin:0"><?= htmlspecialchars(admin_user(), ENT_QUOTES) ?> 님</div><a class="dlbtn" href="logout.php" style="margin-top:6px;display:inline-block">로그아웃</a></div></div></header>
<div class="cglayout">
<div class="cgpanel">
<div class="card"><div class="cardtitle">상단</div>
<div class="row2"><div class="fld"><label>타이틀</label><input type="text" id="title"></div>
<div class="fld"><label>타이틀 색</label><input type="color" id="titleColor"></div>
</div>
<div class="fld"><label>스폰서 글자 (로고를 올리면 로고가 우선입니다)</label><input type="text" id="sponsorText" placeholder="예: Google Play"></div>
<div class="fld"><label>스폰서 로고</label><div class="row-inline"><label class="filebtn">파일 선택<input type="file" id="logoSponsor" accept="image/*"></label><button class="btn danger" id="logoSponsorClear" type="button">지우기</button></div></div>
<div class="fld"><label>방송국 로고 (오른쪽 위)</label><div class="row-inline"><label class="filebtn">파일 선택<input type="file" id="logoBroadcast" accept="image/*"></label><button class="btn danger" id="logoBroadcastClear" type="button">지우기</button></div></div>
</div>
<div class="card"><div class="cardtitle">선수 1 <span class="note">왼쪽</span></div>
<div class="fld"><label>이름 (기록실에 있는 선수는 종족이 자동으로 채워집니다)</label><input type="text" id="name1" list="playerList" placeholder="예: 김지성"></div>
<div class="row2"><div class="fld"><label>닉네임</label><input type="text" id="nick1" placeholder="예: RoyaL"></div>
<div class="fld"><label>종족</label><select id="race1"><option value="T">테란 (T)</option><option value="P">프로토스 (P)</option><option value="Z">저그 (Z)</option><option value="">표시 안 함</option></select></div>
</div>
<div class="fld"><label>사진</label><div class="row-inline"><label class="filebtn">파일 선택<input type="file" id="photo1" accept="image/*"></label><button class="btn danger" id="photo1Clear" type="button">지우기</button></div></div>
<div class="fld"><label>사진 크기</label><input type="range" id="zoom1" min="0.4" max="4" step="0.02" value="1"></div>
<div class="helptxt">사진은 미리보기 위에서 <b>끌어서 위치</b>를 잡고 <b>휠로 크기</b>를 맞출 수 있습니다. 이미지 파일을 미리보기에 끌어다 놓아도 바로 들어갑니다.</div>
</div>
<div class="card"><div class="cardtitle">선수 2 <span class="note">오른쪽</span></div>
<div class="fld"><label>이름 (기록실에 있는 선수는 종족이 자동으로 채워집니다)</label><input type="text" id="name2" list="playerList" placeholder="예: 김지성"></div>
<div class="row2"><div class="fld"><label>닉네임</label><input type="text" id="nick2" placeholder="예: RoyaL"></div>
<div class="fld"><label>종족</label><select id="race2"><option value="T">테란 (T)</option><option value="P">프로토스 (P)</option><option value="Z">저그 (Z)</option><option value="">표시 안 함</option></select></div>
</div>
<div class="fld"><label>사진</label><div class="row-inline"><label class="filebtn">파일 선택<input type="file" id="photo2" accept="image/*"></label><button class="btn danger" id="photo2Clear" type="button">지우기</button></div></div>
<div class="fld"><label>사진 크기</label><input type="range" id="zoom2" min="0.4" max="4" step="0.02" value="1"></div>
<div class="helptxt">사진은 미리보기 위에서 <b>끌어서 위치</b>를 잡고 <b>휠로 크기</b>를 맞출 수 있습니다. 이미지 파일을 미리보기에 끌어다 놓아도 바로 들어갑니다.</div>
</div>
<div class="card"><div class="cardtitle">배경색</div>
<div class="row2"><div class="fld"><label>왼쪽</label><input type="color" id="bgLeft"></div>
<div class="fld"><label>오른쪽</label><input type="color" id="bgRight"></div>
</div>
<button class="btn" id="swap" type="button">좌우 선수 바꾸기</button>
</div>
<div class="card"><div class="cardtitle">상자 1</div>
<div class="fld"><label>제목</label><input type="text" id="boxTitle0"></div>
<div class="fld"><label>내용 (한 줄에 하나씩)</label><textarea id="boxBody0"></textarea></div>
<div class="helptxt"><code>[글자]</code> 는 노란 테두리 강조 칸, <code>* 글자</code> 는 작은 회색 주석, 빈 줄은 한 칸 띄우기입니다. 상자 높이는 내용에 맞춰 알아서 늘어납니다.</div>
</div>
<div class="card"><div class="cardtitle">상자 2</div>
<div class="fld"><label>제목</label><input type="text" id="boxTitle1"></div>
<div class="fld"><label>내용 (한 줄에 하나씩)</label><textarea id="boxBody1"></textarea></div>
<div class="helptxt"><code>[글자]</code> 는 노란 테두리 강조 칸, <code>* 글자</code> 는 작은 회색 주석, 빈 줄은 한 칸 띄우기입니다. 상자 높이는 내용에 맞춰 알아서 늘어납니다.</div>
</div>
<div class="card"><div class="cardtitle">상자 3</div>
<div class="fld"><label>제목</label><input type="text" id="boxTitle2"></div>
<div class="fld"><label>내용 (한 줄에 하나씩)</label><textarea id="boxBody2"></textarea></div>
<div class="helptxt"><code>[글자]</code> 는 노란 테두리 강조 칸, <code>* 글자</code> 는 작은 회색 주석, 빈 줄은 한 칸 띄우기입니다. 상자 높이는 내용에 맞춰 알아서 늘어납니다.</div>
</div>
<div class="card"><div class="cardtitle">내보내기</div>
<div class="btnrow"><button class="btn primary" id="download" type="button">PNG 내려받기</button><button class="btn" id="exportJson" type="button">설정 내보내기</button><label class="filebtn">설정 불러오기<input type="file" id="importJson" accept="application/json,.json"></label><button class="btn danger" id="reset" type="button">처음으로</button></div>
<div class="note" id="note"></div>
<div class="helptxt">사진까지 포함해 자동 저장하므로, 사진이 아주 크면 저장에 실패할 수 있습니다. 그럴 때는 "설정 내보내기"로 파일에 남겨 두세요.</div>
</div>
</div>
<div class="cgstage"><canvas id="cv"></canvas>
<div class="helptxt">미리보기는 실제 1920×1080 캔버스를 줄여 보여 주는 것이라 내려받은 PNG 와 똑같습니다.</div></div>
</div>
<datalist id="playerList"></datalist>
<footer>이 도구는 브라우저 안에서만 동작합니다 — 올린 사진은 어디에도 올라가지 않고 이 컴퓨터를 벗어나지 않습니다.<br>선수 자동완성 목록은 끝장전·ASL 기록실 데이터에서 가져온 95명입니다.</footer>
</div>
<script>
const PLAYERS = [{"name":"강정우","race":"T","from":"ASL","slug":"kang-jeongu","photo":""},{"name":"강태완","race":"T","from":"ASL","slug":"kang-taewan","photo":""},{"name":"고석현","race":"Z","from":"ASL","slug":"ko-seokhyeon","photo":""},{"name":"구성훈","race":"T","from":"ASL","slug":"koo-seonghun","photo":""},{"name":"김건욱","race":"Z","from":"ASL","slug":"kim-geonuk","photo":""},{"name":"김경모","race":"Z","from":"ASL","slug":"kim-gyeongmo","photo":""},{"name":"김규회","race":"P","from":"ASL","slug":"kim-gyuhoe","photo":""},{"name":"김기훈","race":"P","from":"ASL","slug":"kim-gihun","photo":""},{"name":"김명운","race":"Z","from":"끝장전","slug":"kim-myeongun","photo":""},{"name":"김민철","race":"Z","from":"끝장전","slug":"kim-mincheol","photo":""},{"name":"김범성","race":"Z","from":"ASL","slug":"kim-beomseong","photo":""},{"name":"김범수","race":"P","from":"ASL","slug":"kim-beomsu","photo":""},{"name":"김봉준","race":"P","from":"ASL","slug":"kim-bongjun","photo":""},{"name":"김상곤","race":"Z","from":"ASL","slug":"kim-sanggon","photo":""},{"name":"김성대","race":"Z","from":"끝장전","slug":"kim-seongdae","photo":""},{"name":"김성현","race":"T","from":"끝장전","slug":"kim-seonghyeon","photo":""},{"name":"김승현","race":"P","from":"끝장전","slug":"kim-seunghyeon","photo":""},{"name":"김영진","race":"T","from":"ASL","slug":"kim-yeongjin","photo":""},{"name":"김윤중","race":"P","from":"끝장전","slug":"kim-yunjung","photo":""},{"name":"김윤환","race":"Z","from":"끝장전","slug":"kim-yunhwan","photo":""},{"name":"김재현","race":"T","from":"ASL","slug":"kim-jaehyeon","photo":""},{"name":"김재훈","race":"P","from":"ASL","slug":"kim-jaehun","photo":""},{"name":"김정우","race":"Z","from":"끝장전","slug":"kim-jeongu","photo":""},{"name":"김지성","race":"T","from":"끝장전","slug":"kim-jiseong","photo":""},{"name":"김태영","race":"T","from":"ASL","slug":"kim-taeyeong","photo":""},{"name":"김택용","race":"P","from":"끝장전","slug":"kim-taekyong","photo":""},{"name":"김현우","race":"Z","from":"ASL","slug":"kim-hyeonu","photo":""},{"name":"도재욱","race":"P","from":"끝장전","slug":"do-jaeuk","photo":""},{"name":"문기호","race":"Z","from":"ASL","slug":"moon-giho","photo":""},{"name":"문태호","race":"T","from":"ASL","slug":"moon-taeho","photo":""},{"name":"박상현","race":"Z","from":"끝장전","slug":"park-sanghyeon","photo":""},{"name":"박성균","race":"T","from":"끝장전","slug":"park-seonggyun","photo":""},{"name":"박성준","race":"Z","from":"ASL","slug":"park-seongjun","photo":""},{"name":"박세정","race":"P","from":"ASL","slug":"park-sejeong","photo":""},{"name":"박재혁","race":"Z","from":"ASL","slug":"park-jaehyeok","photo":""},{"name":"박재현","race":"P","from":"ASL","slug":"park-jaehyeon","photo":""},{"name":"박준오","race":"Z","from":"끝장전","slug":"park-juno","photo":""},{"name":"박지수","race":"T","from":"ASL","slug":"park-jisu","photo":""},{"name":"박지호","race":"P","from":"ASL","slug":"park-jiho","photo":""},{"name":"박지훈","race":"P","from":"ASL","slug":"park-jihun","photo":""},{"name":"방태수","race":"Z","from":"ASL","slug":"bang-taesu","photo":""},{"name":"배병우","race":"Z","from":"ASL","slug":"bae-byeongu","photo":""},{"name":"배성흠","race":"Z","from":"ASL","slug":"bae-seongheum","photo":""},{"name":"배호연","race":"T","from":"ASL","slug":"bae-hoyeon","photo":""},{"name":"변현제","race":"P","from":"끝장전","slug":"byun-hyeonje","photo":""},{"name":"변형태","race":"T","from":"ASL","slug":"byun-hyeongtae","photo":""},{"name":"서문지훈","race":"Z","from":"ASL","slug":"seo-munjihun","photo":""},{"name":"손경훈","race":"P","from":"ASL","slug":"son-gyeonghun","photo":""},{"name":"송병구","race":"P","from":"끝장전","slug":"song-byeonggu","photo":""},{"name":"신상문","race":"T","from":"ASL","slug":"shin-sangmun","photo":""},{"name":"심대성","race":"Z","from":"ASL","slug":"shim-daeseong","photo":""},{"name":"염보성","race":"T","from":"끝장전","slug":"yeom-boseong","photo":""},{"name":"오진식","race":"Z","from":"ASL","slug":"oh-jinsik","photo":""},{"name":"원선재","race":"P","from":"ASL","slug":"won-seonjae","photo":""},{"name":"원지훈","race":"P","from":"ASL","slug":"won-jihun","photo":""},{"name":"유승곤","race":"T","from":"ASL","slug":"yoo-seunggon","photo":""},{"name":"유영진","race":"T","from":"끝장전","slug":"yoo-yeongjin","photo":""},{"name":"유진우","race":"Z","from":"ASL","slug":"yoo-jinu","photo":""},{"name":"윤수철","race":"P","from":"ASL","slug":"yoon-sucheol","photo":""},{"name":"윤용태","race":"P","from":"끝장전","slug":"yoon-yongtae","photo":""},{"name":"윤종현","race":"T","from":"ASL","slug":"yoon-jonghyeon","photo":""},{"name":"윤진규","race":"Z","from":"ASL","slug":"yoon-jingyu","photo":""},{"name":"윤찬희","race":"T","from":"끝장전","slug":"yoon-chanhui","photo":""},{"name":"이경민","race":"T","from":"끝장전","slug":"lee-gyeongmin","photo":""},{"name":"이성은","race":"T","from":"ASL","slug":"lee-seongeun","photo":""},{"name":"이영웅","race":"T","from":"끝장전","slug":"lee-yeongung","photo":""},{"name":"이영한","race":"Z","from":"끝장전","slug":"lee-yeonghan","photo":""},{"name":"이영호","race":"T","from":"끝장전","slug":"lee-yeongho","photo":""},{"name":"이예준","race":"Z","from":"ASL","slug":"lee-yejun","photo":""},{"name":"이예훈","race":"Z","from":"ASL","slug":"lee-yehun","photo":""},{"name":"이윤열","race":"T","from":"ASL","slug":"lee-yunyeol","photo":""},{"name":"이재호","race":"T","from":"끝장전","slug":"lee-jaeho","photo":""},{"name":"이제동","race":"Z","from":"끝장전","slug":"lee-jedong","photo":""},{"name":"이창우","race":"Z","from":"ASL","slug":"lee-changu","photo":""},{"name":"인치호","race":"Z","from":"ASL","slug":"in-chiho","photo":""},{"name":"임진묵","race":"T","from":"끝장전","slug":"lim-jinmuk","photo":""},{"name":"임홍규","race":"Z","from":"끝장전","slug":"lim-honggyu","photo":""},{"name":"장윤철","race":"P","from":"끝장전","slug":"jang-yuncheol","photo":""},{"name":"전태양","race":"T","from":"끝장전","slug":"jeon-taeyang","photo":""},{"name":"정경두","race":"P","from":"ASL","slug":"jung-gyeongdu","photo":""},{"name":"정민기","race":"T","from":"ASL","slug":"jung-mingi","photo":""},{"name":"정영재","race":"T","from":"끝장전","slug":"jung-yeongjae","photo":""},{"name":"정윤성","race":"P","from":"ASL","slug":"jung-yunseong","photo":""},{"name":"정윤종","race":"P","from":"ASL","slug":"jung-yunjong","photo":""},{"name":"조기석","race":"T","from":"끝장전","slug":"cho-giseok","photo":""},{"name":"조일장","race":"Z","from":"끝장전","slug":"cho-iljang","photo":""},{"name":"진영화","race":"P","from":"ASL","slug":"jin-yeonghwa","photo":""},{"name":"최영현","race":"P","from":"ASL","slug":"choi-yeonghyeon","photo":""},{"name":"최호선","race":"T","from":"끝장전","slug":"choi-hoseon","photo":""},{"name":"하늘","race":"P","from":"ASL","slug":"ha-neul","photo":""},{"name":"한두열","race":"Z","from":"ASL","slug":"han-duyeol","photo":""},{"name":"한상봉","race":"Z","from":"ASL","slug":"han-sangbong","photo":""},{"name":"현지섭","race":"T","from":"ASL","slug":"hyun-jiseop","photo":""},{"name":"홍덕","race":"P","from":"ASL","slug":"hong-deok","photo":""},{"name":"황병영","race":"T","from":"끝장전","slug":"hwang-byeongyeong","photo":""}];
/* 끝장전 대진표 CG 제작 툴.
   1920x1080 캔버스에 직접 그립니다 — 바깥 라이브러리를 쓰지 않아서
   인터넷이 끊겨도 되고, 내보낸 PNG 가 화면에 보이는 것과 정확히 같습니다. */

var W = 1920, H = 1080;
var cv = document.getElementById('cv');
var ctx = cv.getContext('2d');
cv.width = W; cv.height = H;

var RACE_LABEL = { T: '테란', P: '프로토스', Z: '저그', '': '' };
var RACE_COLOR = { T: '#4a9eff', P: '#f5c518', Z: '#ff6b6b' };
var FONT = "'Pretendard','Malgun Gothic','맑은 고딕',system-ui,sans-serif";

/* ── 화면 배치 (1920x1080 기준) ─────────────────────────────── */
var L = {
  panelW: 470,                       // 좌우 선수 칸 너비
  topBarY: 52, topBarH: 92,
  photo: { x: 34, y: 176, w: 402, h: 604, r: 16 },
  namePlateY: 812,
  boxX: 512, boxW: 896, boxTop: 196, boxGap: 22,
  boxPad: 20, titleSize: 38, lineSize: 25, noteSize: 20
};

/* ── 상태 ──────────────────────────────────────────────────── */
var S = {
  title: '끝장전',
  titleColor: '#4aa8ff',
  sponsorText: '',
  bgLeft: '#8c1f2a',
  bgRight: '#123a78',
  players: [
    { nick: 'RoyaL', name: '김지성', race: 'T', photo: null, photoFrom: null,
      zoom: 1, ox: 0, oy: 0 },
    { nick: 'Bisu', name: '김택용', race: 'P', photo: null, photoFrom: null,
      zoom: 1, ox: 0, oy: 0 }
  ],
  logoSponsor: null,
  logoBroadcast: null,
  boxes: [
    { title: '경기 방식', body: '두 선수가 9세트 풀세트 진행\n( 8대 0 상황에서도 마지막 9세트 진행 )' },
    {
      title: '상금',
      body: '매 세트 승리시 10만원\n[더블 찬스]\n세트 시작 전 선수당 1일 1회 더블 찬스 사용 가능\n' +
        '더블 찬스가 적용된 세트의 승자는 두배의 상금 획득 (20만원)\n* ※ 중복 사용 불가\n' +
        '[올킬 상금 30만원 (총 상금 140만원)]'
    },
    {
      title: '사용맵',
      body: '오디세이, 컬러리스 페이트, 녹아웃, 애티튜드,\n아이올로스, 백룸, 옥타곤 (ASL 시즌22 공식맵)\n' +
        '* 경기 시작 전 선수당 한 개씩 총 두 개 맵 제거'
    }
  ]
};

var imgCache = {};      // dataURL → Image

function loadImage(src, cb) {
  if (!src) { cb(null); return; }
  if (imgCache[src] && imgCache[src].complete) { cb(imgCache[src]); return; }
  var im = new Image();
  im.onload = function () { imgCache[src] = im; cb(im); };
  im.onerror = function () { cb(null); };
  im.src = src;
  imgCache[src] = im;
}

/* ── 그리기 도구 ───────────────────────────────────────────── */
function roundRect(c, x, y, w, h, r) {
  c.beginPath();
  c.moveTo(x + r, y);
  c.arcTo(x + w, y, x + w, y + h, r);
  c.arcTo(x + w, y + h, x, y + h, r);
  c.arcTo(x, y + h, x, y, r);
  c.arcTo(x, y, x + w, y, r);
  c.closePath();
}

function setFont(size, weight) {
  ctx.font = (weight || 700) + ' ' + size + 'px ' + FONT;
}

/** 글자가 칸을 넘치면 자동으로 줄여 그립니다. */
function fitText(text, size, weight, maxW) {
  var s = size;
  setFont(s, weight);
  while (s > 10 && ctx.measureText(text).width > maxW) {
    s -= 1;
    setFont(s, weight);
  }
  return s;
}

function drawCover(im, x, y, w, h, zoom, ox, oy, radius) {
  ctx.save();
  roundRect(ctx, x, y, w, h, radius || 0);
  ctx.clip();
  var scale = Math.max(w / im.width, h / im.height) * (zoom || 1);
  var dw = im.width * scale, dh = im.height * scale;
  ctx.drawImage(im, x + (w - dw) / 2 + (ox || 0), y + (h - dh) / 2 + (oy || 0), dw, dh);
  ctx.restore();
}

function drawContain(im, cx, cy, maxW, maxH) {
  var scale = Math.min(maxW / im.width, maxH / im.height);
  var w = im.width * scale, h = im.height * scale;
  ctx.drawImage(im, cx - w / 2, cy - h / 2, w, h);
  return w;
}

/* ── 본문 줄 해석 ──────────────────────────────────────────────
   [글자]  → 노란 테두리 강조 칩
   * 글자  → 작게, 흐린 색
   그 외   → 보통 흰 글자                                        */
function parseLine(raw) {
  var t = raw.trim();
  if (!t) return { kind: 'gap', text: '' };
  if (t[0] === '[' && t[t.length - 1] === ']') {
    return { kind: 'chip', text: t.slice(1, -1).trim() };
  }
  if (t[0] === '*') return { kind: 'note', text: t.slice(1).trim() };
  return { kind: 'line', text: t };
}

function boxLines(box) {
  return String(box.body || '').split('\n').map(parseLine);
}

function boxHeight(box) {
  var h = L.boxPad + L.titleSize + 16 + L.boxPad;   // 제목 + 밑줄 여백
  boxLines(box).forEach(function (ln) {
    if (ln.kind === 'gap') h += 14;
    else if (ln.kind === 'note') h += L.noteSize + 12;
    else if (ln.kind === 'chip') h += L.lineSize + 22;
    else h += L.lineSize + 12;
  });
  return h;
}

/* ── 각 영역 ───────────────────────────────────────────────── */
function drawBackground() {
  ctx.fillStyle = '#15171c';
  ctx.fillRect(0, 0, W, H);

  // 좌우 선수 칸 뒤로 깔리는 색
  [[0, S.bgLeft], [W - L.panelW, S.bgRight]].forEach(function (pair, i) {
    var x = pair[0];
    var g = ctx.createLinearGradient(x, 0, x + L.panelW, H);
    g.addColorStop(0, pair[1]);
    g.addColorStop(1, i === 0 ? '#2a1013' : '#0d1b33');
    ctx.fillStyle = g;
    ctx.fillRect(x, 0, L.panelW, H);
    // 가운데 쪽으로 자연스럽게 어두워지게
    var f = ctx.createLinearGradient(
      i === 0 ? x + L.panelW - 150 : x + 150, 0,
      i === 0 ? x + L.panelW : x, 0);
    f.addColorStop(0, 'rgba(21,23,28,0)');
    f.addColorStop(1, 'rgba(21,23,28,1)');
    ctx.fillStyle = f;
    ctx.fillRect(i === 0 ? x + L.panelW - 150 : x, 0, 150, H);
  });

  // 가운데 은은한 사선 무늬
  ctx.save();
  ctx.globalAlpha = 0.045;
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 2;
  for (var gx = L.panelW - 200; gx < W - L.panelW + 200; gx += 34) {
    ctx.beginPath();
    ctx.moveTo(gx, 0);
    ctx.lineTo(gx - 260, H);
    ctx.stroke();
  }
  ctx.restore();
}

function drawTopBar(imgs) {
  var y = L.topBarY, h = L.topBarH;
  var cx = W / 2;
  var titleSize = 58;
  setFont(titleSize, 900);
  var titleW = ctx.measureText(S.title).width;

  var sponsorW = 0;
  if (imgs.sponsor) {
    sponsorW = imgs.sponsor.width * (h / imgs.sponsor.height);
    sponsorW = Math.min(sponsorW, 420);
  } else if (S.sponsorText) {
    setFont(42, 800);
    sponsorW = ctx.measureText(S.sponsorText).width;
  }

  var divW = sponsorW ? 46 : 0;
  var total = sponsorW + divW + titleW;
  var startX = cx - total / 2;

  if (imgs.sponsor) {
    drawContain(imgs.sponsor, startX + sponsorW / 2, y + h / 2, sponsorW, h);
  } else if (S.sponsorText) {
    setFont(42, 800);
    ctx.fillStyle = '#e8ecf3';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(S.sponsorText, startX, y + h / 2);
  }

  if (divW) {
    ctx.strokeStyle = 'rgba(255,255,255,.35)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(startX + sponsorW + divW / 2, y + 12);
    ctx.lineTo(startX + sponsorW + divW / 2, y + h - 12);
    ctx.stroke();
  }

  setFont(titleSize, 900);
  ctx.fillStyle = S.titleColor;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(S.title, startX + sponsorW + divW, y + h / 2 + 2);

  if (imgs.broadcast) {
    var bw = Math.min(imgs.broadcast.width * (72 / imgs.broadcast.height), 240);
    drawContain(imgs.broadcast, W - 40 - bw / 2, y + h / 2, bw, 72);
  }
}

function photoRect(side) {
  var p = L.photo;
  var x = side === 0 ? p.x : W - L.panelW + p.x;
  return { x: x, y: p.y, w: p.w, h: p.h, r: p.r };
}

function drawPlayer(side, im) {
  var pl = S.players[side];
  var r = photoRect(side);

  // 사진 자리 (없으면 안내 문구)
  ctx.save();
  roundRect(ctx, r.x, r.y, r.w, r.h, r.r);
  ctx.fillStyle = 'rgba(0,0,0,.30)';
  ctx.fill();
  ctx.restore();

  if (im) {
    drawCover(im, r.x, r.y, r.w, r.h, pl.zoom, pl.ox, pl.oy, r.r);
    // 아래쪽을 어둡게 깔아 이름이 잘 보이게
    ctx.save();
    roundRect(ctx, r.x, r.y, r.w, r.h, r.r);
    ctx.clip();
    var g = ctx.createLinearGradient(0, r.y + r.h - 220, 0, r.y + r.h);
    g.addColorStop(0, 'rgba(0,0,0,0)');
    g.addColorStop(1, 'rgba(0,0,0,.72)');
    ctx.fillStyle = g;
    ctx.fillRect(r.x, r.y + r.h - 220, r.w, 220);
    ctx.restore();
  } else {
    ctx.save();
    ctx.setLineDash([10, 8]);
    ctx.strokeStyle = 'rgba(255,255,255,.32)';
    ctx.lineWidth = 3;
    roundRect(ctx, r.x, r.y, r.w, r.h, r.r);
    ctx.stroke();
    ctx.setLineDash([]);
    setFont(26, 700);
    ctx.fillStyle = 'rgba(255,255,255,.55)';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('선수 사진을 올려 주세요', r.x + r.w / 2, r.y + r.h / 2 - 16);
    setFont(20, 500);
    ctx.fillText('여기로 끌어다 놓아도 됩니다', r.x + r.w / 2, r.y + r.h / 2 + 22);
    ctx.restore();
  }

  var cx = r.x + r.w / 2;

  // 닉네임
  if (pl.nick) {
    var ns = fitText(pl.nick, 44, 500, r.w - 20);
    ctx.fillStyle = 'rgba(255,255,255,.88)';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'alphabetic';
    setFont(ns, 500);
    ctx.fillText(pl.nick, cx, L.namePlateY);
  }

  // 이름 + 종족
  var label = pl.name + (pl.race ? ' ' + pl.race : '');
  var size = fitText(label, 70, 900, r.w + 26);
  setFont(size, 900);
  var full = ctx.measureText(label).width;
  var nameOnlyW = ctx.measureText(pl.name).width;
  var startX = cx - full / 2;
  ctx.textAlign = 'left';
  ctx.shadowColor = 'rgba(0,0,0,.55)';
  ctx.shadowBlur = 12;
  ctx.fillStyle = '#ffffff';
  ctx.fillText(pl.name, startX, L.namePlateY + 76);
  if (pl.race) {
    ctx.fillStyle = RACE_COLOR[pl.race] || '#ffffff';
    ctx.fillText(' ' + pl.race, startX + nameOnlyW, L.namePlateY + 76);
  }
  ctx.shadowBlur = 0;
}

function drawBoxes() {
  var heights = S.boxes.map(boxHeight);
  var totalH = heights.reduce(function (a, b) { return a + b; }, 0) +
    L.boxGap * (S.boxes.length - 1);
  var avail = H - L.boxTop - 60;
  var y = L.boxTop + Math.max(0, (avail - totalH) / 2);

  S.boxes.forEach(function (box, i) {
    var h = heights[i];
    var x = L.boxX, w = L.boxW;

    ctx.fillStyle = 'rgba(38,40,46,.94)';
    roundRect(ctx, x, y, w, h, 4);
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,.85)';
    ctx.lineWidth = 3;
    ctx.beginPath();                       // 위쪽에만 밝은 선
    ctx.moveTo(x, y + 1.5);
    ctx.lineTo(x + w, y + 1.5);
    ctx.stroke();
    ctx.strokeStyle = 'rgba(255,255,255,.14)';
    ctx.lineWidth = 1.5;
    roundRect(ctx, x, y, w, h, 4);
    ctx.stroke();

    var cx = x + w / 2;
    var ty = y + L.boxPad + L.titleSize * 0.8;

    setFont(L.titleSize, 900);
    ctx.fillStyle = '#ffd24a';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'alphabetic';
    ctx.fillText(box.title, cx, ty);
    var tw = ctx.measureText(box.title).width;
    ctx.strokeStyle = '#ffd24a';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(cx - tw / 2, ty + 10);
    ctx.lineTo(cx + tw / 2, ty + 10);
    ctx.stroke();

    var ly = ty + 26;
    boxLines(box).forEach(function (ln) {
      if (ln.kind === 'gap') { ly += 14; return; }
      if (ln.kind === 'note') {
        ly += L.noteSize + 12;
        setFont(L.noteSize, 500);
        ctx.fillStyle = 'rgba(232,236,243,.62)';
        ctx.fillText(ln.text, cx, ly);
        return;
      }
      if (ln.kind === 'chip') {
        ly += L.lineSize + 22;
        setFont(L.lineSize, 800);
        var cw = ctx.measureText(ln.text).width + 34;
        var ch = L.lineSize + 16;
        ctx.fillStyle = 'rgba(255,210,74,.14)';
        roundRect(ctx, cx - cw / 2, ly - ch + 8, cw, ch, 3);
        ctx.fill();
        ctx.strokeStyle = '#ffd24a';
        ctx.lineWidth = 2;
        roundRect(ctx, cx - cw / 2, ly - ch + 8, cw, ch, 3);
        ctx.stroke();
        ctx.fillStyle = '#ffe9a8';
        ctx.fillText(ln.text, cx, ly);
        return;
      }
      ly += L.lineSize + 12;
      var s = fitText(ln.text, L.lineSize, 600, L.boxW - L.boxPad * 2 - 20);
      setFont(s, 600);
      ctx.fillStyle = '#ffffff';
      ctx.fillText(ln.text, cx, ly);
    });

    y += h + L.boxGap;
  });
}

/* ── 전체 그리기 ───────────────────────────────────────────── */
var pending = 0;
function draw() {
  var need = [S.logoSponsor, S.logoBroadcast, S.players[0].photo, S.players[1].photo];
  var got = [null, null, null, null];
  var left = need.length;
  need.forEach(function (src, i) {
    loadImage(src, function (im) {
      got[i] = im;
      if (--left === 0) paint(got);
    });
  });
}

function paint(g) {
  ctx.clearRect(0, 0, W, H);
  drawBackground();
  drawTopBar({ sponsor: g[0], broadcast: g[1] });
  drawPlayer(0, g[2]);
  drawPlayer(1, g[3]);
  drawBoxes();
  save();
}

/* ── 조작 ──────────────────────────────────────────────────── */
function $(id) { return document.getElementById(id); }

function bind(id, get, set) {
  var el = $(id);
  if (!el) return;
  el.value = get();
  var ev = (el.type === 'range' || el.type === 'color') ? 'input' : 'input';
  el.addEventListener(ev, function () { set(el.value); draw(); });
}

function bindPhoto(id, onLoad) {
  var el = $(id);
  el.addEventListener('change', function () {
    var f = el.files && el.files[0];
    if (!f) return;
    var fr = new FileReader();
    fr.onload = function () { onLoad(fr.result); draw(); };
    fr.readAsDataURL(f);
  });
}

function setupControls() {
  bind('title', function () { return S.title; }, function (v) { S.title = v; });
  bind('titleColor', function () { return S.titleColor; }, function (v) { S.titleColor = v; });
  bind('sponsorText', function () { return S.sponsorText; }, function (v) { S.sponsorText = v; });
  bind('bgLeft', function () { return S.bgLeft; }, function (v) { S.bgLeft = v; });
  bind('bgRight', function () { return S.bgRight; }, function (v) { S.bgRight = v; });

  bindPhoto('logoSponsor', function (d) { S.logoSponsor = d; });
  bindPhoto('logoBroadcast', function (d) { S.logoBroadcast = d; });
  $('logoSponsorClear').addEventListener('click', function () { S.logoSponsor = null; draw(); });
  $('logoBroadcastClear').addEventListener('click', function () { S.logoBroadcast = null; draw(); });

  [0, 1].forEach(function (i) {
    var n = i + 1;
    bind('nick' + n, function () { return S.players[i].nick; },
      function (v) { S.players[i].nick = v; });
    bind('name' + n, function () { return S.players[i].name; },
      function (v) {
        S.players[i].name = v;
        var hit = PLAYERS.find(function (p) { return p.name === v; });
        if (hit) { S.players[i].race = hit.race; $('race' + n).value = hit.race; }
        // 올려 둔 선수 사진이 있으면 바로 붙입니다.
        // 직접 올리신 사진은 건드리지 않습니다 — 등록 사진일 때만 바꿉니다.
        if (S.players[i].photoFrom !== 'upload') {
          if (hit && hit.photo) {
            S.players[i].photo = '../img/players/' + encodeURIComponent(hit.photo);
            S.players[i].photoFrom = 'lib';
            S.players[i].zoom = 1; S.players[i].ox = 0; S.players[i].oy = 0;
            var z = $('zoom' + n); if (z) z.value = 1;
          } else if (S.players[i].photoFrom === 'lib') {
            // 사진이 없는 선수로 바꿨는데 앞 선수 얼굴이 남아 있으면 안 됩니다.
            S.players[i].photo = null; S.players[i].photoFrom = null;
          }
        }
      });
    bind('race' + n, function () { return S.players[i].race; },
      function (v) { S.players[i].race = v; });
    bind('zoom' + n, function () { return S.players[i].zoom; },
      function (v) { S.players[i].zoom = parseFloat(v); });
    bindPhoto('photo' + n, function (d) {
      S.players[i].photo = d;
      S.players[i].photoFrom = 'upload';       // 직접 올린 사진이 항상 우선입니다
      S.players[i].zoom = 1; S.players[i].ox = 0; S.players[i].oy = 0;
      $('zoom' + n).value = 1;
    });
    $('photo' + n + 'Clear').addEventListener('click', function () {
      S.players[i].photo = null; S.players[i].photoFrom = null; draw();
    });
  });

  S.boxes.forEach(function (box, i) {
    bind('boxTitle' + i, function () { return box.title; }, function (v) { box.title = v; });
    bind('boxBody' + i, function () { return box.body; }, function (v) { box.body = v; });
  });

  $('swap').addEventListener('click', function () {
    S.players.reverse();
    fillForm();
    draw();
  });
  $('reset').addEventListener('click', function () {
    if (!confirm('처음 상태로 되돌립니다. 올린 사진도 지워집니다.')) return;
    localStorage.removeItem(KEY);
    location.reload();
  });
  $('download').addEventListener('click', download);
  $('exportJson').addEventListener('click', exportJson);
  $('importJson').addEventListener('change', importJson);
}

function fillForm() {
  [0, 1].forEach(function (i) {
    var n = i + 1, p = S.players[i];
    $('nick' + n).value = p.nick;
    $('name' + n).value = p.name;
    $('race' + n).value = p.race;
    $('zoom' + n).value = p.zoom;
  });
  $('title').value = S.title;
  $('titleColor').value = S.titleColor;
  $('sponsorText').value = S.sponsorText;
  $('bgLeft').value = S.bgLeft;
  $('bgRight').value = S.bgRight;
  S.boxes.forEach(function (b, i) {
    // 불러온 설정의 상자 개수가 화면보다 많을 수 있어 있는 칸만 채웁니다.
    if ($('boxTitle' + i)) $('boxTitle' + i).value = b.title;
    if ($('boxBody' + i)) $('boxBody' + i).value = b.body;
  });
}

/* 캔버스에서 사진을 끌어 옮기고, 휠로 키우고 줄입니다. */
function canvasPos(ev) {
  var r = cv.getBoundingClientRect();
  return { x: (ev.clientX - r.left) * (W / r.width), y: (ev.clientY - r.top) * (H / r.height) };
}
function hitPhoto(pos) {
  for (var i = 0; i < 2; i++) {
    var r = photoRect(i);
    if (pos.x >= r.x && pos.x <= r.x + r.w && pos.y >= r.y && pos.y <= r.y + r.h) return i;
  }
  return -1;
}
function setupCanvasDrag() {
  var drag = null;
  cv.addEventListener('mousedown', function (ev) {
    var pos = canvasPos(ev);
    var i = hitPhoto(pos);
    if (i < 0 || !S.players[i].photo) return;
    drag = { i: i, x: pos.x, y: pos.y, ox: S.players[i].ox, oy: S.players[i].oy };
    ev.preventDefault();
  });
  window.addEventListener('mousemove', function (ev) {
    if (!drag) return;
    var pos = canvasPos(ev);
    S.players[drag.i].ox = drag.ox + (pos.x - drag.x);
    S.players[drag.i].oy = drag.oy + (pos.y - drag.y);
    draw();
  });
  window.addEventListener('mouseup', function () { drag = null; });
  cv.addEventListener('wheel', function (ev) {
    var i = hitPhoto(canvasPos(ev));
    if (i < 0 || !S.players[i].photo) return;
    ev.preventDefault();
    var p = S.players[i];
    p.zoom = Math.min(4, Math.max(0.4, p.zoom * (ev.deltaY < 0 ? 1.06 : 1 / 1.06)));
    $('zoom' + (i + 1)).value = p.zoom;
    draw();
  }, { passive: false });

  // 캔버스에 파일을 끌어다 놓으면 가까운 쪽 선수 사진이 됩니다.
  cv.addEventListener('dragover', function (ev) { ev.preventDefault(); });
  cv.addEventListener('drop', function (ev) {
    ev.preventDefault();
    var f = ev.dataTransfer.files && ev.dataTransfer.files[0];
    if (!f || !/^image\//.test(f.type)) return;
    var pos = canvasPos(ev);
    var i = hitPhoto(pos);
    if (i < 0) i = pos.x < W / 2 ? 0 : 1;
    var fr = new FileReader();
    fr.onload = function () {
      S.players[i].photo = fr.result;
      S.players[i].zoom = 1; S.players[i].ox = 0; S.players[i].oy = 0;
      $('zoom' + (i + 1)).value = 1;
      draw();
    };
    fr.readAsDataURL(f);
  });
}

/* ── 내보내기 · 저장 ───────────────────────────────────────── */
function stamp() {
  var d = new Date();
  function p(n) { return (n < 10 ? '0' : '') + n; }
  return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) +
    '-' + p(d.getHours()) + p(d.getMinutes());
}

function download() {
  cv.toBlob(function (blob) {
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = '끝장전-' + S.players[0].name + '-vs-' + S.players[1].name +
      '-' + stamp() + '.png';
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }, 'image/png');
}

function exportJson() {
  var blob = new Blob([JSON.stringify(S, null, 1)], { type: 'application/json' });
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = '끝장전-CG-설정-' + stamp() + '.json';
  document.body.appendChild(a);
  a.click();
  setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}

function importJson(ev) {
  var f = ev.target.files && ev.target.files[0];
  if (!f) return;
  var fr = new FileReader();
  fr.onload = function () {
    try {
      var got = JSON.parse(fr.result);
      Object.keys(got).forEach(function (k) { S[k] = got[k]; });
      fillForm();
      draw();
      note('설정을 불러왔습니다.');
    } catch (e) {
      note('설정 파일을 읽지 못했습니다: ' + e.message, true);
    }
  };
  fr.readAsText(f);
  ev.target.value = '';
}

var KEY = 'sc-cg-v1';
var saveTimer = null;
function save() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(function () {
    try {
      localStorage.setItem(KEY, JSON.stringify(S));
      note('자동 저장됨 — 이 브라우저에서 새로고침해도 그대로 있습니다.');
    } catch (e) {
      note('사진이 커서 자동 저장을 못 했습니다. "설정 내보내기"로 파일에 저장하세요.', true);
    }
  }, 400);
}
function restore() {
  try {
    var raw = localStorage.getItem(KEY);
    if (!raw) return;
    var got = JSON.parse(raw);
    Object.keys(got).forEach(function (k) { S[k] = got[k]; });
  } catch (e) { /* 저장본이 깨졌으면 그냥 기본값으로 갑니다 */ }
}
function note(msg, bad) {
  var el = $('note');
  el.textContent = msg;
  el.className = 'note' + (bad ? ' bad' : '');
}

/* ── 선수 자동완성 ─────────────────────────────────────────── */
function setupDatalist() {
  var dl = document.getElementById('playerList');
  dl.innerHTML = PLAYERS.map(function (p) {
    return '<option value="' + p.name + '">' + RACE_LABEL[p.race] +
      (p.from ? ' · ' + p.from : '') + '</option>';
  }).join('');
}

/* ── 시작 ──────────────────────────────────────────────────── */
restore();
setupDatalist();
setupControls();
fillForm();
setupCanvasDrag();
draw();
if (document.fonts && document.fonts.ready) {
  document.fonts.ready.then(draw);   // 폰트가 늦게 오면 다시 그립니다
}
</script>
</body>
</html>
