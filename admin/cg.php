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
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(320px,100%),1fr));gap:14px}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(260px,100%),1fr));gap:14px}

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
.row3{display:grid;grid-template-columns:1.3fr 1fr 1fr;gap:9px}
/* CG 종류 고르기 */
.cgtypes{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:9px}
.cgtype{display:flex;flex-direction:column;gap:2px;padding:9px 10px;border-radius:9px;
  background:var(--panel2);border:1px solid var(--line);color:var(--dim);
  cursor:pointer;text-align:left;font-family:inherit}
.cgtype b{color:var(--txt);font-size:13px}
.cgtype span{font-size:10.5px;line-height:1.35}
.cgtype:hover{border-color:var(--accent)}
.cgtype.on{background:linear-gradient(135deg,var(--accent),#0d5fc4);border-color:var(--accent)}
.cgtype.on b,.cgtype.on span{color:#fff}
/* 글자 모양 한 줄 — 이름 / 크기 / 색 / 폰트 */
.strow{display:grid;grid-template-columns:1fr 66px 44px 104px;gap:6px;align-items:center;
  margin-bottom:6px}
.stname{color:var(--dim);font-size:11.5px;font-weight:600;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.strow input[type=number],.strow select{width:100%;padding:6px 7px;border-radius:7px;
  background:var(--panel2);color:var(--txt);border:1px solid var(--line);
  font-family:inherit;font-size:12px}
.strow input[type=color]{width:100%;height:30px;padding:2px;border-radius:7px;
  background:var(--panel2);border:1px solid var(--line);cursor:pointer}
.strow select:focus,.strow input:focus{border-color:var(--accent);outline:none}
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
.pphoto{width:104px;height:104px;border-radius:50%;object-fit:cover;object-position:center top;
  border:3px solid var(--line);background:var(--panel2);flex:0 0 auto;
  box-shadow:0 4px 16px rgba(0,0,0,.35)}
.rphoto{width:38px;height:38px;border-radius:50%;object-fit:cover;object-position:center top;
  border:1px solid var(--line);background:var(--panel2);vertical-align:middle;margin-right:8px}

/* ── 모바일 터치 크기 ─────────────────────────────────
   손가락으로 누르는 화면입니다. 글자만 한 크기로 두면 잘 안 눌립니다.
   누르는 것들이 40px 안팎이 되도록 위아래 여백을 넉넉히 줍니다.

   이 블록은 **반드시 파일 맨 끝**에 있어야 합니다. 위쪽 @media 안에 두면
   그 뒤에 나오는 .navlink · .h2hsel 같은 규칙이 같은 우선순위로 다시
   덮어써서 효과가 사라집니다 (실제로 그렇게 겪었습니다).
   톱니바퀴(.gear)는 일부러 눈에 안 띄게 둔 것이라 건드리지 않습니다. */
@media (max-width:640px){
  .navlink{padding:11px 16px}
  .tab{padding:10px 14px}
  .chip{padding:9px 13px}
  .dlbtn{padding:9px 13px}
  .yt-mini{display:inline-block;padding:9px 4px}
  .backlink{padding:8px 2px}
  .nm-link{display:inline-block;padding:5px 0}
  .h2hsel{padding-top:11px;padding-bottom:11px}
  .h2hopt{padding:12px 10px}
  .h2hclear{width:34px;height:34px;font-size:19px}
  .h2hdrop{max-height:min(300px,46vh)}
}

/* 선수 사진은 얼굴이 보여야 하므로 큼직하게. 좁은 화면에서만 조금 줄입니다. */
@media (max-width:640px){
  .pphoto{width:78px;height:78px;border-width:2px}
  .rphoto{width:32px;height:32px}
}
</style>
</head>
<body>
<div class="brandbar"></div>
<div class="wrap cgwrap">
<nav class="sitenav"><a class="navlink" href="../index.html">← 사이트로 돌아가기</a></nav>
<header style="border-bottom:none;padding-bottom:6px"><div class="headrow"><div><h1>CG 제작 툴</h1><div class="sub">대진표 이미지를 만들어 PNG(1920×1080)로 내려받습니다. 입력한 내용은 이 브라우저에 자동 저장됩니다.</div></div><div style="margin-left:auto;text-align:right"><div class="helptxt" style="margin:0"><?= htmlspecialchars(admin_user(), ENT_QUOTES) ?> 님</div><a class="dlbtn" href="logout.php" style="margin-top:6px;display:inline-block">로그아웃</a></div></div></header>
<div class="cglayout">
<div class="cgpanel">
<div class="card"><div class="cardtitle">CG 종류</div>
<div class="cgtypes"><button class="cgtype" type="button" data-type="matchup"><b>대진표</b><span>경기 방식·상금·사용맵</span></button><button class="cgtype" type="button" data-type="stats"><b>선수 전적</b><span>총 전적·누적상금·상대 전적</span></button><button class="cgtype" type="button" data-type="score"><b>쉬는 시간</b><span>전적 + 양쪽 스코어</span></button><button class="cgtype" type="button" data-type="winner"><b>경기 결과</b><span>승자 강조·패자 어둡게</span></button><button class="cgtype" type="button" data-type="next"><b>다음 경기</b><span>NEXT MATCH 안내</span></button></div>
<div class="helptxt">고른 종류에 필요한 칸만 아래에 나옵니다. 선수·사진·상단 설정은 다섯 종류가 함께 씁니다.</div></div>
<div class="card"><div class="cardtitle">상단</div>
<div class="fld"><label>타이틀</label><input type="text" id="title"></div>
<div class="fld"><label>스폰서 글자 (로고를 올리면 로고가 우선입니다)</label><input type="text" id="sponsorText" placeholder="예: Google Play"></div>
<div class="fld"><label>스폰서 로고</label><div class="row-inline"><label class="filebtn">파일 선택<input type="file" id="logoSponsor" accept="image/*"></label><button class="btn danger" id="logoSponsorClear" type="button">지우기</button></div></div>
<div class="fld"><label>방송국 로고 (오른쪽 위)</label><div class="row-inline"><label class="filebtn">파일 선택<input type="file" id="logoBroadcast" accept="image/*"></label><button class="btn danger" id="logoBroadcastClear" type="button">지우기</button></div></div>
<div class="fld"><label>LIVE 배지 (비우면 안 나옵니다)</label><input type="text" id="liveBadge" placeholder="예: LIVE"></div>
</div>
<div class="card"><div class="cardtitle">선수 1 <span class="note">왼쪽</span></div>
<div class="fld"><label>이름 (기록실에 있는 선수는 종족이 자동으로 채워집니다)</label><input type="text" id="name1" list="playerList"></div>
<div class="row2"><div class="fld"><label>닉네임</label><input type="text" id="nick1" placeholder="예: RoyaL"></div>
<div class="fld"><label>종족</label><select id="race1"><option value="T">테란 (T)</option><option value="P">프로토스 (P)</option><option value="Z">저그 (Z)</option><option value="">없음</option></select></div>
</div>
<div class="fld"><label>사진</label><div class="row-inline"><label class="filebtn">파일 선택<input type="file" id="photo1" accept="image/*"></label><button class="btn danger" id="photo1Clear" type="button">지우기</button></div></div>
<div class="fld"><label>시즌 사진 (같은 선수의 다른 시즌 사진을 고를 수 있습니다)</label><select id="season1"><option value="">사진 없음</option></select></div>
<div class="fld"><label>사진 크기</label><input type="range" id="zoom1" min="0.4" max="4" step="0.02"></div>
<div class="helptxt">사진은 미리보기 위에서 <b>끌어서 위치</b>를 잡고 <b>휠로 크기</b>를 맞출 수 있습니다. 이미지 파일을 미리보기에 끌어다 놓아도 바로 들어갑니다.</div>
<div data-for="stats score winner"><div class="fld"><label>누적상금</label><input type="text" id="prize1" placeholder="KRW 25,900,000"></div>
</div>
<div data-for="score"><div class="fld"><label>스코어</label><input type="text" id="score1" placeholder="4"></div>
</div>
<div data-for="winner"><div class="fld"><label>상금 증감 (사진 아래 큰 글자)</label><input type="text" id="delta1" placeholder="₩700,000"></div>
</div>
<div data-for="stats score"><div class="fld"><label>최근 전적 목록 (한 줄에 하나씩 · [줄] 은 굵게)</label><textarea id="vs1" rows="5"></textarea></div>
</div>
</div>
<div class="card"><div class="cardtitle">선수 2 <span class="note">오른쪽</span></div>
<div class="fld"><label>이름 (기록실에 있는 선수는 종족이 자동으로 채워집니다)</label><input type="text" id="name2" list="playerList"></div>
<div class="row2"><div class="fld"><label>닉네임</label><input type="text" id="nick2" placeholder="예: RoyaL"></div>
<div class="fld"><label>종족</label><select id="race2"><option value="T">테란 (T)</option><option value="P">프로토스 (P)</option><option value="Z">저그 (Z)</option><option value="">없음</option></select></div>
</div>
<div class="fld"><label>사진</label><div class="row-inline"><label class="filebtn">파일 선택<input type="file" id="photo2" accept="image/*"></label><button class="btn danger" id="photo2Clear" type="button">지우기</button></div></div>
<div class="fld"><label>시즌 사진 (같은 선수의 다른 시즌 사진을 고를 수 있습니다)</label><select id="season2"><option value="">사진 없음</option></select></div>
<div class="fld"><label>사진 크기</label><input type="range" id="zoom2" min="0.4" max="4" step="0.02"></div>
<div class="helptxt">사진은 미리보기 위에서 <b>끌어서 위치</b>를 잡고 <b>휠로 크기</b>를 맞출 수 있습니다. 이미지 파일을 미리보기에 끌어다 놓아도 바로 들어갑니다.</div>
<div data-for="stats score winner"><div class="fld"><label>누적상금</label><input type="text" id="prize2" placeholder="KRW 25,900,000"></div>
</div>
<div data-for="score"><div class="fld"><label>스코어</label><input type="text" id="score2" placeholder="4"></div>
</div>
<div data-for="winner"><div class="fld"><label>상금 증감 (사진 아래 큰 글자)</label><input type="text" id="delta2" placeholder="₩700,000"></div>
</div>
<div data-for="stats score"><div class="fld"><label>최근 전적 목록 (한 줄에 하나씩 · [줄] 은 굵게)</label><textarea id="vs2" rows="5"></textarea></div>
</div>
</div>
<div class="card"><div class="cardtitle">배경색</div>
<div class="row2"><div class="fld"><label>왼쪽</label><input type="color" id="bgLeft"></div>
<div class="fld"><label>오른쪽</label><input type="color" id="bgRight"></div>
</div>
<button class="btn" id="swap" type="button">좌우 선수 바꾸기</button>
</div>
<div class="card" data-for="matchup"><div class="cardtitle">상자 1</div>
<div class="fld"><label>제목</label><input type="text" id="boxTitle0"></div>
<div class="fld"><label>내용 (한 줄에 하나씩)</label><textarea id="boxBody0" rows="5"></textarea></div>
<div class="helptxt"><code>[글자]</code> 는 테두리 강조 칸, <code>* 글자</code> 는 작은 주석, 빈 줄은 한 칸 띄우기입니다. 상자 높이는 내용에 맞춰 알아서 늘어납니다.</div>
</div>
<div class="card" data-for="matchup"><div class="cardtitle">상자 2</div>
<div class="fld"><label>제목</label><input type="text" id="boxTitle1"></div>
<div class="fld"><label>내용 (한 줄에 하나씩)</label><textarea id="boxBody1" rows="5"></textarea></div>
<div class="helptxt"><code>[글자]</code> 는 테두리 강조 칸, <code>* 글자</code> 는 작은 주석, 빈 줄은 한 칸 띄우기입니다. 상자 높이는 내용에 맞춰 알아서 늘어납니다.</div>
</div>
<div class="card" data-for="matchup"><div class="cardtitle">상자 3</div>
<div class="fld"><label>제목</label><input type="text" id="boxTitle2"></div>
<div class="fld"><label>내용 (한 줄에 하나씩)</label><textarea id="boxBody2" rows="5"></textarea></div>
<div class="helptxt"><code>[글자]</code> 는 테두리 강조 칸, <code>* 글자</code> 는 작은 주석, 빈 줄은 한 칸 띄우기입니다. 상자 높이는 내용에 맞춰 알아서 늘어납니다.</div>
</div>
<div class="card" data-for="stats score"><div class="cardtitle">가운데 전적판</div>
<div class="row2"><div class="fld"><label>큰 제목</label><input type="text" id="stHeading"></div>
<div class="fld"><label>작은 제목</label><input type="text" id="stSub"></div>
</div>
<div class="fld"><label>상금 칸 제목</label><input type="text" id="stPrizeLabel"></div>
<div class="row3"><div class="fld"><label>1번째 줄 이름</label><input type="text" id="stRowLabel0"></div>
<div class="fld"><label>왼쪽</label><input type="text" id="stRowA0"></div>
<div class="fld"><label>오른쪽</label><input type="text" id="stRowB0"></div>
</div>
<div class="row3"><div class="fld"><label>2번째 줄 이름</label><input type="text" id="stRowLabel1"></div>
<div class="fld"><label>왼쪽</label><input type="text" id="stRowA1"></div>
<div class="fld"><label>오른쪽</label><input type="text" id="stRowB1"></div>
</div>
<div class="fld"><label>기간 안내</label><input type="text" id="stPeriod"></div>
<div class="fld"><label>종족 전적 제목</label><input type="text" id="stMuLabel"></div>
<div class="row2"><div class="fld"><label>왼쪽 이름</label><input type="text" id="stMuA"></div>
<div class="fld"><label>왼쪽 값</label><input type="text" id="stMuAVal"></div>
</div>
<div class="row2"><div class="fld"><label>오른쪽 이름</label><input type="text" id="stMuB"></div>
<div class="fld"><label>오른쪽 값</label><input type="text" id="stMuBVal"></div>
</div>
<div class="fld"><label>아래 안내 (한 줄에 하나씩)</label><textarea id="stFoot" rows="3"></textarea></div>
<div class="fld"><label>타이머 (비우면 안 나옵니다)</label><input type="text" id="stTimer"></div>
</div>
<div class="card" data-for="winner"><div class="cardtitle">경기 결과</div>
<div class="fld"><label>이긴 선수</label><select id="winSide"><option value="0">왼쪽 선수</option><option value="1">오른쪽 선수</option></select></div>
<div class="row2"><div class="fld"><label>가운데 스코어</label><input type="text" id="winVs" placeholder="5 VS 4"></div>
<div class="fld"><label>승자 글자</label><input type="text" id="winLabel" placeholder="WINNER"></div>
</div>
<div class="fld"><label>승자 위 리본 (비우면 안 나옵니다)</label><input type="text" id="winRibbon" placeholder="3연승 중!"></div>
<div class="helptxt">진 선수 사진은 자동으로 어두워집니다. 선수별 누적상금·상금 증감은 위 선수 칸에서 넣습니다.</div>
</div>
<div class="card" data-for="next"><div class="cardtitle">다음 경기</div>
<div class="fld"><label>큰 글자</label><input type="text" id="nextHeading" placeholder="NEXT MATCH"></div>
<div class="fld"><label>날짜·시간</label><input type="text" id="nextWhen"></div>
</div>
<div class="card"><div class="cardtitle">글자 모양<span class="note">크기 · 색 · 폰트</span></div>
<div class="strow"><span class="stname">타이틀</span><input type="number" id="st_title_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_title_color" title="색"><select id="st_title_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow"><span class="stname">닉네임</span><input type="number" id="st_nick_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_nick_color" title="색"><select id="st_nick_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow"><span class="stname">선수 이름</span><input type="number" id="st_pname_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_pname_color" title="색"><select id="st_pname_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="matchup"><span class="stname">상자 제목</span><input type="number" id="st_boxTitle_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_boxTitle_color" title="색"><select id="st_boxTitle_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="matchup"><span class="stname">상자 본문</span><input type="number" id="st_boxLine_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_boxLine_color" title="색"><select id="st_boxLine_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="matchup"><span class="stname">상자 주석</span><input type="number" id="st_boxNote_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_boxNote_color" title="색"><select id="st_boxNote_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="stats score"><span class="stname">큰 제목</span><input type="number" id="st_heading_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_heading_color" title="색"><select id="st_heading_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="stats score"><span class="stname">작은 제목</span><input type="number" id="st_sub_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_sub_color" title="색"><select id="st_sub_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="stats score"><span class="stname">줄 이름</span><input type="number" id="st_rowLabel_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_rowLabel_color" title="색"><select id="st_rowLabel_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="stats score"><span class="stname">줄 숫자</span><input type="number" id="st_rowValue_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_rowValue_color" title="색"><select id="st_rowValue_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="stats score"><span class="stname">기간 안내</span><input type="number" id="st_period_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_period_color" title="색"><select id="st_period_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="stats score winner"><span class="stname">누적상금</span><input type="number" id="st_prize_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_prize_color" title="색"><select id="st_prize_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="stats score"><span class="stname">최근 전적 목록</span><input type="number" id="st_vsList_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_vsList_color" title="색"><select id="st_vsList_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="stats score"><span class="stname">아래 안내</span><input type="number" id="st_foot_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_foot_color" title="색"><select id="st_foot_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="stats score"><span class="stname">타이머</span><input type="number" id="st_timer_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_timer_color" title="색"><select id="st_timer_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="score"><span class="stname">스코어</span><input type="number" id="st_score_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_score_color" title="색"><select id="st_score_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="winner"><span class="stname">승자 글자</span><input type="number" id="st_winnerLabel_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_winnerLabel_color" title="색"><select id="st_winnerLabel_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="winner"><span class="stname">리본</span><input type="number" id="st_ribbon_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_ribbon_color" title="색"><select id="st_ribbon_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="winner"><span class="stname">가운데 스코어 · 상금 증감</span><input type="number" id="st_vsBig_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_vsBig_color" title="색"><select id="st_vsBig_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="next"><span class="stname">NEXT MATCH</span><input type="number" id="st_nextHead_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_nextHead_color" title="색"><select id="st_nextHead_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="strow" data-for="next"><span class="stname">날짜·시간</span><input type="number" id="st_when_size" min="8" max="400" step="1" title="크기"><input type="color" id="st_when_color" title="색"><select id="st_when_font" title="폰트"><option value="pretendard">기본 (Pretendard)</option><option value="gothic">맑은 고딕</option><option value="nanum">나눔고딕</option><option value="black">굵은 영문 (Arial Black)</option><option value="serif">바탕</option><option value="script">흘림체 (Script)</option></select></div>
<div class="helptxt">숫자는 1920×1080 기준 픽셀입니다. 칸을 넘치는 글자는 알아서 조금씩 줄여 그립니다.</div>
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
const PLAYERS = [{"name":"강정우","race":"T","from":"ASL","slug":"kang-jeongu","photo":"","seasons":[]},{"name":"강태완","race":"T","from":"ASL","slug":"kang-taewan","photo":"","seasons":[]},{"name":"고석현","race":"Z","from":"ASL","slug":"ko-seokhyeon","photo":"","seasons":[]},{"name":"구성훈","race":"T","from":"ASL","slug":"koo-seonghun","photo":"","seasons":[]},{"name":"김건욱","race":"Z","from":"ASL","slug":"kim-geonuk","photo":"","seasons":[]},{"name":"김경모","race":"Z","from":"ASL","slug":"kim-gyeongmo","photo":"","seasons":[]},{"name":"김규회","race":"P","from":"ASL","slug":"kim-gyuhoe","photo":"","seasons":[]},{"name":"김기훈","race":"P","from":"ASL","slug":"kim-gihun","photo":"","seasons":[]},{"name":"김명운","race":"Z","from":"끝장전","slug":"kim-myeongun","photo":"kim-myeongun.webp","seasons":[9,14,15,19,20]},{"name":"김민철","race":"Z","from":"끝장전","slug":"kim-mincheol","photo":"kim-mincheol.webp","seasons":[9,14,15,19,20]},{"name":"김범성","race":"Z","from":"ASL","slug":"kim-beomseong","photo":"","seasons":[]},{"name":"김범수","race":"P","from":"ASL","slug":"kim-beomsu","photo":"","seasons":[]},{"name":"김봉준","race":"P","from":"ASL","slug":"kim-bongjun","photo":"","seasons":[]},{"name":"김상곤","race":"Z","from":"ASL","slug":"kim-sanggon","photo":"","seasons":[]},{"name":"김성대","race":"Z","from":"끝장전","slug":"kim-seongdae","photo":"kim-seongdae.webp","seasons":[9,14,15,19]},{"name":"김성현","race":"T","from":"끝장전","slug":"kim-seonghyeon","photo":"","seasons":[]},{"name":"김승현","race":"P","from":"끝장전","slug":"kim-seunghyeon","photo":"","seasons":[]},{"name":"김영진","race":"T","from":"ASL","slug":"kim-yeongjin","photo":"","seasons":[]},{"name":"김윤중","race":"P","from":"끝장전","slug":"kim-yunjung","photo":"","seasons":[]},{"name":"김윤환","race":"Z","from":"끝장전","slug":"kim-yunhwan","photo":"","seasons":[]},{"name":"김재현","race":"T","from":"ASL","slug":"kim-jaehyeon","photo":"","seasons":[]},{"name":"김재훈","race":"P","from":"ASL","slug":"kim-jaehun","photo":"","seasons":[]},{"name":"김정우","race":"Z","from":"끝장전","slug":"kim-jeongu","photo":"kim-jeongu.webp","seasons":[20]},{"name":"김지성","race":"T","from":"끝장전","slug":"kim-jiseong","photo":"kim-jiseong.webp","seasons":[14,15,21]},{"name":"김태영","race":"T","from":"ASL","slug":"kim-taeyeong","photo":"kim-taeyeong.webp","seasons":[21]},{"name":"김택용","race":"P","from":"끝장전","slug":"kim-taekyong","photo":"kim-taekyong.webp","seasons":[9,14,15,19,20,21]},{"name":"김현우","race":"Z","from":"ASL","slug":"kim-hyeonu","photo":"","seasons":[]},{"name":"도재욱","race":"P","from":"끝장전","slug":"do-jaeuk","photo":"do-jaeuk.webp","seasons":[9,14,15,19,20]},{"name":"문기호","race":"Z","from":"ASL","slug":"moon-giho","photo":"","seasons":[]},{"name":"문태호","race":"T","from":"ASL","slug":"moon-taeho","photo":"","seasons":[]},{"name":"박상현","race":"Z","from":"끝장전","slug":"park-sanghyeon","photo":"park-sanghyeon.webp","seasons":[9,14,20,21]},{"name":"박성균","race":"T","from":"끝장전","slug":"park-seonggyun","photo":"park-seonggyun.webp","seasons":[15]},{"name":"박성준","race":"Z","from":"ASL","slug":"park-seongjun","photo":"","seasons":[]},{"name":"박세정","race":"P","from":"ASL","slug":"park-sejeong","photo":"","seasons":[]},{"name":"박재혁","race":"Z","from":"ASL","slug":"park-jaehyeok","photo":"","seasons":[]},{"name":"박재현","race":"P","from":"ASL","slug":"park-jaehyeon","photo":"","seasons":[]},{"name":"박준오","race":"Z","from":"끝장전","slug":"park-juno","photo":"park-juno.webp","seasons":[16]},{"name":"박지수","race":"T","from":"ASL","slug":"park-jisu","photo":"","seasons":[]},{"name":"박지호","race":"P","from":"ASL","slug":"park-jiho","photo":"","seasons":[]},{"name":"박지훈","race":"P","from":"ASL","slug":"park-jihun","photo":"","seasons":[]},{"name":"방태수","race":"Z","from":"ASL","slug":"bang-taesu","photo":"bang-taesu.webp","seasons":[20]},{"name":"배병우","race":"Z","from":"ASL","slug":"bae-byeongu","photo":"","seasons":[]},{"name":"배성흠","race":"Z","from":"ASL","slug":"bae-seongheum","photo":"","seasons":[]},{"name":"배호연","race":"T","from":"ASL","slug":"bae-hoyeon","photo":"","seasons":[]},{"name":"변현제","race":"P","from":"끝장전","slug":"byun-hyeonje","photo":"byun-hyeonje.webp","seasons":[14,19,20]},{"name":"변형태","race":"T","from":"ASL","slug":"byun-hyeongtae","photo":"","seasons":[]},{"name":"서문지훈","race":"Z","from":"ASL","slug":"seo-munjihun","photo":"","seasons":[]},{"name":"손경훈","race":"P","from":"ASL","slug":"son-gyeonghun","photo":"son-gyeonghun.webp","seasons":[9]},{"name":"송병구","race":"P","from":"끝장전","slug":"song-byeonggu","photo":"song-byeonggu.webp","seasons":[9]},{"name":"신상문","race":"T","from":"ASL","slug":"shin-sangmun","photo":"shin-sangmun.webp","seasons":[21]},{"name":"심대성","race":"Z","from":"ASL","slug":"shim-daeseong","photo":"","seasons":[]},{"name":"염보성","race":"T","from":"끝장전","slug":"yeom-boseong","photo":"","seasons":[]},{"name":"오진식","race":"Z","from":"ASL","slug":"oh-jinsik","photo":"","seasons":[]},{"name":"원선재","race":"P","from":"ASL","slug":"won-seonjae","photo":"","seasons":[]},{"name":"원지훈","race":"P","from":"ASL","slug":"won-jihun","photo":"","seasons":[]},{"name":"유승곤","race":"T","from":"ASL","slug":"yoo-seunggon","photo":"yoo-seunggon.webp","seasons":[19]},{"name":"유영진","race":"T","from":"끝장전","slug":"yoo-yeongjin","photo":"yoo-yeongjin.webp","seasons":[14,15,19,20]},{"name":"유진우","race":"Z","from":"ASL","slug":"yoo-jinu","photo":"","seasons":[]},{"name":"윤수철","race":"P","from":"ASL","slug":"yoon-sucheol","photo":"yoon-sucheol.webp","seasons":[21]},{"name":"윤용태","race":"P","from":"끝장전","slug":"yoon-yongtae","photo":"","seasons":[]},{"name":"윤종현","race":"T","from":"ASL","slug":"yoon-jonghyeon","photo":"","seasons":[]},{"name":"윤진규","race":"Z","from":"ASL","slug":"yoon-jingyu","photo":"","seasons":[]},{"name":"윤찬희","race":"T","from":"끝장전","slug":"yoon-chanhui","photo":"yoon-chanhui.webp","seasons":[9,14]},{"name":"이경민","race":"T","from":"끝장전","slug":"lee-gyeongmin","photo":"lee-gyeongmin.webp","seasons":[9]},{"name":"이성은","race":"T","from":"ASL","slug":"lee-seongeun","photo":"","seasons":[]},{"name":"이영웅","race":"T","from":"끝장전","slug":"lee-yeongung","photo":"lee-yeongung.webp","seasons":[19,20]},{"name":"이영한","race":"Z","from":"끝장전","slug":"lee-yeonghan","photo":"lee-yeonghan.webp","seasons":[14,15]},{"name":"이영호","race":"T","from":"끝장전","slug":"lee-yeongho","photo":"lee-yeongho.webp","seasons":[9,21]},{"name":"이예준","race":"Z","from":"ASL","slug":"lee-yejun","photo":"","seasons":[]},{"name":"이예훈","race":"Z","from":"ASL","slug":"lee-yehun","photo":"","seasons":[]},{"name":"이윤열","race":"T","from":"ASL","slug":"lee-yunyeol","photo":"","seasons":[]},{"name":"이재호","race":"T","from":"끝장전","slug":"lee-jaeho","photo":"lee-jaeho.webp","seasons":[9,14,15,19,20,21]},{"name":"이제동","race":"Z","from":"끝장전","slug":"lee-jedong","photo":"lee-jedong.webp","seasons":[15,19,20,21]},{"name":"이창우","race":"Z","from":"ASL","slug":"lee-changu","photo":"","seasons":[]},{"name":"인치호","race":"Z","from":"ASL","slug":"in-chiho","photo":"","seasons":[]},{"name":"임진묵","race":"T","from":"끝장전","slug":"lim-jinmuk","photo":"lim-jinmuk.webp","seasons":[21]},{"name":"임홍규","race":"Z","from":"끝장전","slug":"lim-honggyu","photo":"lim-honggyu.webp","seasons":[9,20]},{"name":"장윤철","race":"P","from":"끝장전","slug":"jang-yuncheol","photo":"jang-yuncheol.webp","seasons":[9,14,15,19,20,21]},{"name":"전태양","race":"T","from":"끝장전","slug":"jeon-taeyang","photo":"","seasons":[]},{"name":"정경두","race":"P","from":"ASL","slug":"jung-gyeongdu","photo":"","seasons":[]},{"name":"정민기","race":"T","from":"ASL","slug":"jung-mingi","photo":"","seasons":[]},{"name":"정영재","race":"T","from":"끝장전","slug":"jung-yeongjae","photo":"jung-yeongjae.webp","seasons":[15]},{"name":"정윤성","race":"P","from":"ASL","slug":"jung-yunseong","photo":"","seasons":[]},{"name":"정윤종","race":"P","from":"ASL","slug":"jung-yunjong","photo":"jung-yunjong.webp","seasons":[19,21]},{"name":"조기석","race":"T","from":"끝장전","slug":"cho-giseok","photo":"cho-giseok.webp","seasons":[9,19,20,21]},{"name":"조일장","race":"Z","from":"끝장전","slug":"cho-iljang","photo":"cho-iljang.webp","seasons":[14,15,19,21]},{"name":"진영화","race":"P","from":"ASL","slug":"jin-yeonghwa","photo":"","seasons":[]},{"name":"최영현","race":"P","from":"ASL","slug":"choi-yeonghyeon","photo":"","seasons":[]},{"name":"최호선","race":"T","from":"끝장전","slug":"choi-hoseon","photo":"choi-hoseon.webp","seasons":[14,15,21]},{"name":"하늘","race":"P","from":"ASL","slug":"ha-neul","photo":"","seasons":[]},{"name":"한두열","race":"Z","from":"ASL","slug":"han-duyeol","photo":"","seasons":[]},{"name":"한상봉","race":"Z","from":"ASL","slug":"han-sangbong","photo":"","seasons":[]},{"name":"현지섭","race":"T","from":"ASL","slug":"hyun-jiseop","photo":"","seasons":[]},{"name":"홍덕","race":"P","from":"ASL","slug":"hong-deok","photo":"","seasons":[]},{"name":"황병영","race":"T","from":"끝장전","slug":"hwang-byeongyeong","photo":"hwang-byeongyeong.webp","seasons":[9,14,15,19,20,21]}];
/* 끝장전 방송 CG 제작 툴.
   1920x1080 캔버스에 직접 그립니다 — 바깥 라이브러리를 쓰지 않아서
   인터넷이 끊겨도 되고, 내보낸 PNG 가 화면에 보이는 것과 정확히 같습니다.

   CG 다섯 종류를 한 툴에서 만듭니다.
     matchup  대진표 (경기 방식·상금·사용맵)
     stats    선수 전적
     score    쉬는 시간 (전적 + 스코어)
     winner   경기 결과 (승자 강조·패자 어둡게)
     next     다음 경기 안내

   배치는 방송 포맷 그대로 고정입니다. 대신 글자마다 내용·크기·색·폰트를
   바꿀 수 있고, 사진은 끌어서 위치를, 휠이나 슬라이더로 크기를 맞춥니다. */

var W = 1920, H = 1080;
var cv = document.getElementById('cv');
var ctx = cv.getContext('2d');
cv.width = W; cv.height = H;

var RACE_COLOR = { T: '#4a9eff', P: '#f5c518', Z: '#ff6b6b' };

var FONTS = {
  pretendard: "'Pretendard','Malgun Gothic','맑은 고딕',system-ui,sans-serif",
  gothic: "'Malgun Gothic','맑은 고딕',sans-serif",
  nanum: "'NanumGothic','나눔고딕','Malgun Gothic',sans-serif",
  black: "'Arial Black','Pretendard','Malgun Gothic',sans-serif",
  serif: "'Batang','바탕',serif",
  script: "'Segoe Script','Brush Script MT','Pretendard',cursive"
};

var TYPES = [
  { id: 'matchup', label: '대진표' },
  { id: 'stats', label: '선수 전적' },
  { id: 'score', label: '쉬는 시간 (스코어)' },
  { id: 'winner', label: '경기 결과' },
  { id: 'next', label: '다음 경기' }
];

/* ── 화면 배치 (1920x1080 기준) ─────────────────────────────── */
var L = {
  topBarY: 46, topBarH: 92,
  // 선수 사진은 방송처럼 화면 좌우 끝까지 꽉 채웁니다.
  photo: { w: 620, h: 1080, y: 0 },
  center: { x: 512, w: 896 }
};

/* ── 상태 ──────────────────────────────────────────────────── */
function defaults() {
  return {
    type: 'matchup',
    title: '끝장전',
    sponsorText: '',
    bgLeft: '#8c1f2a',
    bgRight: '#123a78',
    logoSponsor: null,
    logoBroadcast: null,
    liveBadge: '',
    players: [
      { nick: 'RoyaL', name: '김지성', race: 'T', photo: null, photoFrom: null,
        season: '', zoom: 1, ox: 0, oy: 0,
        prize: 'KRW 25,900,000', score: '0', delta: '',
        vs: 'VS 장윤철(P) 3 : 6 패\nVS 박상현(Z) 4 : 5 패\nVS 김민철(Z) 4 : 5 패\nVS 조일장(Z) 6 : 3 승\n[VS 이제동(Z) 6 : 3 승]' },
      { nick: 'Bisu', name: '김택용', race: 'P', photo: null, photoFrom: null,
        season: '', zoom: 1, ox: 0, oy: 0,
        prize: 'KRW 4,000,000', score: '0', delta: '',
        vs: 'VS 김명운(Z) 6 : 3 승\nVS 이재호(T) 3 : 6 패\nVS 이제동(Z) 5 : 4 승\nVS 이영한(Z) 8 : 1 승\n[VS 이영호(T) 5 : 3 승]' }
    ],
    boxes: [
      { title: '경기 방식', body: '두 선수가 9세트 풀세트 진행\n( 8대 0 상황에서도 마지막 9세트 진행 )' },
      { title: '상금',
        body: '매 세트 승리시 10만원\n[더블 찬스]\n세트 시작 전 선수당 1일 1회 더블 찬스 사용 가능\n' +
          '더블 찬스가 적용된 세트의 승자는 두배의 상금 획득 (20만원)\n* ※ 중복 사용 불가\n' +
          '[올킬 상금 30만원 (총 상금 140만원)]' },
      { title: '사용맵',
        body: '오디세이, 컬러리스 페이트, 녹아웃, 애티튜드,\n아이올로스, 백룸, 옥타곤 (ASL 시즌22 공식맵)\n' +
          '* 경기 시작 전 선수당 한 개씩 총 두 개 맵 제거' }
    ],
    stats: {
      heading: 'Player Stats',
      sub: '온라인 매치',
      prizeLabel: '누적상금',
      rows: [
        { label: '총 전적', a: '251', b: '302' },
        { label: '최근 한달 상대 전적', a: '1', b: '7' }
      ],
      period: '7월 11일 ~ 8월 11일 기록',
      muLabel: '최근 한달 상대 종족 전적',
      muA: 'vs P', muAVal: '16 : 17',
      muB: 'vs T', muBVal: '21 : 14',
      foot: '잠시 후 승부예측 마감!\nSOOP e스포츠\nesports.sooplive.co.kr',
      timer: '13:35'
    },
    winner: {
      side: 0,
      label: 'WINNER',
      ribbon: '3연승 중!',
      vsText: '5 VS 4'
    },
    next: {
      heading: 'NEXT MATCH',
      when: '2026년 8월 20일 목요일 오후 9시'
    },
    style: {
      title: { size: 58, color: '#4aa8ff', font: 'pretendard' },
      nick: { size: 46, color: '#e9edf5', font: 'pretendard' },
      pname: { size: 74, color: '#ffffff', font: 'pretendard' },
      boxTitle: { size: 38, color: '#ffd166', font: 'pretendard' },
      boxLine: { size: 26, color: '#ffffff', font: 'pretendard' },
      boxNote: { size: 20, color: '#b9c2d0', font: 'pretendard' },
      heading: { size: 62, color: '#ffffff', font: 'script' },
      sub: { size: 30, color: '#ffffff', font: 'pretendard' },
      rowLabel: { size: 26, color: '#ffffff', font: 'pretendard' },
      rowValue: { size: 62, color: '#ffffff', font: 'pretendard' },
      period: { size: 22, color: '#e8ecf3', font: 'pretendard' },
      prize: { size: 30, color: '#ffffff', font: 'pretendard' },
      vsList: { size: 23, color: '#e8ecf3', font: 'pretendard' },
      foot: { size: 22, color: '#0b0d11', font: 'pretendard' },
      timer: { size: 74, color: '#ffffff', font: 'black' },
      score: { size: 96, color: '#ffffff', font: 'pretendard' },
      winnerLabel: { size: 78, color: '#ffd166', font: 'black' },
      ribbon: { size: 26, color: '#ffffff', font: 'pretendard' },
      vsBig: { size: 74, color: '#ffffff', font: 'pretendard' },
      nextHead: { size: 150, color: '#ff4d5a', font: 'black' },
      when: { size: 46, color: '#ffffff', font: 'pretendard' }
    }
  };
}

var S = defaults();
var imgCache = {};

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

/** 글자 모양을 정합니다. st 는 S.style 의 한 칸입니다. */
function use(st, sizeOverride, weight) {
  var f = FONTS[st.font] || FONTS.pretendard;
  ctx.font = (weight || 800) + ' ' + (sizeOverride || st.size) + 'px ' + f;
  ctx.fillStyle = st.color;
}

function setFont(size, weight, fontKey) {
  ctx.font = (weight || 700) + ' ' + size + 'px ' + (FONTS[fontKey] || FONTS.pretendard);
}

/** 글자가 칸을 넘치면 자동으로 줄여 그립니다. */
function fitSize(text, st, maxW, weight) {
  var s = st.size;
  use(st, s, weight);
  while (s > 10 && ctx.measureText(text).width > maxW) {
    s -= 1;
    use(st, s, weight);
  }
  return s;
}

function text(str, x, y, st, opt) {
  opt = opt || {};
  var size = opt.maxW ? fitSize(str, st, opt.maxW, opt.weight) : st.size;
  use(st, size, opt.weight);
  if (opt.color) ctx.fillStyle = opt.color;
  ctx.textAlign = opt.align || 'left';
  ctx.textBaseline = opt.baseline || 'alphabetic';
  if (opt.shadow) { ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = opt.shadow; }
  ctx.fillText(str, x, y);
  ctx.shadowBlur = 0;
  return size;
}

function drawCover(im, x, y, w, h, zoom, ox, oy, radius) {
  ctx.save();
  if (radius) { roundRect(ctx, x, y, w, h, radius); ctx.clip(); }
  else { ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip(); }
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
   [글자]  → 테두리 강조 칩
   * 글자  → 작게, 흐린 색
   그 외   → 보통 글자                                           */
function parseLine(raw) {
  var t = raw.trim();
  if (!t) return { kind: 'gap', text: '' };
  if (t[0] === '[' && t[t.length - 1] === ']') return { kind: 'chip', text: t.slice(1, -1).trim() };
  if (t[0] === '*') return { kind: 'note', text: t.slice(1).trim() };
  return { kind: 'line', text: t };
}

function lines(s) { return String(s || '').split('\n').map(parseLine); }

/* ── 공통 영역 ─────────────────────────────────────────────── */
function drawBackground() {
  ctx.fillStyle = '#15171c';
  ctx.fillRect(0, 0, W, H);
  var side = 760;
  [[0, S.bgLeft, 0], [W - side, S.bgRight, 1]].forEach(function (p) {
    var x = p[0], i = p[2];
    var g = ctx.createLinearGradient(i === 0 ? 0 : W, 0, i === 0 ? side : W - side, 0);
    g.addColorStop(0, p[1]);
    g.addColorStop(1, 'rgba(21,23,28,0)');
    ctx.fillStyle = g;
    ctx.fillRect(x, 0, side, H);
  });
}

function drawTopBar(imgs) {
  var y = L.topBarY, h = L.topBarH, cx = W / 2;
  var st = S.style.title;
  use(st, st.size, 900);
  var titleW = ctx.measureText(S.title).width;

  var sponsorW = 0;
  if (imgs.sponsor) {
    sponsorW = Math.min(imgs.sponsor.width * (h / imgs.sponsor.height), 460);
  } else if (S.sponsorText) {
    setFont(42, 800, st.font);
    sponsorW = ctx.measureText(S.sponsorText).width;
  }
  var divW = sponsorW ? 46 : 0;
  var startX = cx - (sponsorW + divW + titleW) / 2;

  if (imgs.sponsor) {
    drawContain(imgs.sponsor, startX + sponsorW / 2, y + h / 2, sponsorW, h);
  } else if (S.sponsorText) {
    setFont(42, 800, st.font);
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillText(S.sponsorText, startX, y + h / 2);
  }
  if (divW) {
    ctx.strokeStyle = 'rgba(255,255,255,.4)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(startX + sponsorW + divW / 2, y + 14);
    ctx.lineTo(startX + sponsorW + divW / 2, y + h - 14);
    ctx.stroke();
  }
  text(S.title, startX + sponsorW + divW, y + h / 2 + 2, st,
    { weight: 900, baseline: 'middle' });

  if (imgs.broadcast) {
    var bw = Math.min(imgs.broadcast.width * (78 / imgs.broadcast.height), 260);
    drawContain(imgs.broadcast, W - 44 - bw / 2, y + h / 2 - 4, bw, 78);
  }
  if (S.liveBadge) {
    setFont(30, 900, 'pretendard');
    var lw = ctx.measureText(S.liveBadge).width + 40;
    ctx.fillStyle = '#1c8cff';
    roundRect(ctx, W - 44 - lw, y + h + 12, lw, 50, 8);
    ctx.fill();
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(S.liveBadge, W - 44 - lw / 2, y + h + 38);
  }
}

function photoRect(side) {
  var p = L.photo;
  return { x: side === 0 ? 0 : W - p.w, y: p.y, w: p.w, h: p.h };
}

/** 선수 사진. dim 이 true 면 어둡게 (진 선수). */
function drawPhoto(side, im, dim) {
  var pl = S.players[side], r = photoRect(side);
  if (im) {
    drawCover(im, r.x, r.y, r.w, r.h, pl.zoom, pl.ox, pl.oy, 0);
    if (dim) {
      ctx.save();
      ctx.beginPath(); ctx.rect(r.x, r.y, r.w, r.h); ctx.clip();
      ctx.fillStyle = 'rgba(6,8,12,.62)';
      ctx.fillRect(r.x, r.y, r.w, r.h);
      ctx.restore();
    }
  } else {
    ctx.save();
    ctx.setLineDash([12, 9]);
    ctx.strokeStyle = 'rgba(255,255,255,.30)';
    ctx.lineWidth = 3;
    roundRect(ctx, r.x + 26, r.y + 150, r.w - 52, r.h - 300, 14);
    ctx.stroke();
    ctx.setLineDash([]);
    setFont(28, 700);
    ctx.fillStyle = 'rgba(255,255,255,.55)';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('선수 사진을 올려 주세요', r.x + r.w / 2, r.y + r.h / 2 - 18);
    setFont(21, 500);
    ctx.fillText('여기로 끌어다 놓아도 됩니다', r.x + r.w / 2, r.y + r.h / 2 + 24);
    ctx.restore();
  }
}

/** 닉네임 + 이름 + 종족 한 덩어리. align 은 'left' | 'right' | 'center'. */
function drawNamePlate(side, x, y, align, maxW) {
  var pl = S.players[side];
  var sn = S.style.nick, sp = S.style.pname;
  if (pl.nick) {
    text(pl.nick, x, y, sn, { align: align, maxW: maxW, weight: 500, shadow: 10 });
  }
  var label = pl.name + (pl.race ? ' ' + pl.race : '');
  var size = fitSize(label, sp, maxW || 460, 900);
  use(sp, size, 900);
  var full = ctx.measureText(label).width;
  var nameW = ctx.measureText(pl.name).width;
  var sx = align === 'right' ? x - full : (align === 'center' ? x - full / 2 : x);
  ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
  ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = 14;
  ctx.fillStyle = sp.color;
  ctx.fillText(pl.name, sx, y + size + 12);
  if (pl.race) {
    ctx.fillStyle = RACE_COLOR[pl.race] || sp.color;
    ctx.fillText(' ' + pl.race, sx + nameW, y + size + 12);
  }
  ctx.shadowBlur = 0;
  return y + size + 12;
}

/* ── ① 대진표 ──────────────────────────────────────────────── */
function boxHeight(box) {
  var sT = S.style.boxTitle, sL = S.style.boxLine, sN = S.style.boxNote;
  var h = 20 + sT.size + 18 + 20;
  lines(box.body).forEach(function (ln) {
    if (ln.kind === 'gap') h += 14;
    else if (ln.kind === 'note') h += sN.size + 12;
    else if (ln.kind === 'chip') h += sL.size + 22;
    else h += sL.size + 14;
  });
  return h;
}

function drawMatchup() {
  var sT = S.style.boxTitle, sL = S.style.boxLine, sN = S.style.boxNote;
  var x = L.center.x, w = L.center.w, cx = x + w / 2;
  var hs = S.boxes.map(boxHeight);
  var total = hs.reduce(function (a, b) { return a + b; }, 0) + 22 * (S.boxes.length - 1);
  var y = Math.max(L.topBarY + L.topBarH + 40, (H - total) / 2);

  S.boxes.forEach(function (box, i) {
    var bh = hs[i];
    ctx.fillStyle = 'rgba(28,32,40,.92)';
    ctx.fillRect(x, y, w, bh);
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 3;
    ctx.strokeRect(x + 1.5, y + 1.5, w - 3, bh - 3);

    var ty = y + 20 + sT.size;
    text(box.title, cx, ty, sT, { align: 'center', maxW: w - 60, weight: 900 });
    var tw = ctx.measureText(box.title).width;
    ctx.strokeStyle = sT.color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(cx - tw / 2, ty + 10);
    ctx.lineTo(cx + tw / 2, ty + 10);
    ctx.stroke();

    var ly = ty + 18;
    lines(box.body).forEach(function (ln) {
      if (ln.kind === 'gap') { ly += 14; return; }
      if (ln.kind === 'note') {
        ly += sN.size + 12;
        text(ln.text, cx, ly, sN, { align: 'center', maxW: w - 60, weight: 500 });
        return;
      }
      if (ln.kind === 'chip') {
        ly += sL.size + 22;
        var s = fitSize(ln.text, sL, w - 140, 900);
        use(sL, s, 900);
        var cw = ctx.measureText(ln.text).width + 44;
        ctx.strokeStyle = sT.color;
        ctx.lineWidth = 2.5;
        ctx.strokeRect(cx - cw / 2, ly - s - 8, cw, s + 20);
        text(ln.text, cx, ly, sL, { align: 'center', maxW: w - 140, weight: 900 });
        return;
      }
      ly += sL.size + 14;
      text(ln.text, cx, ly, sL, { align: 'center', maxW: w - 60, weight: 700 });
    });
    y += bh + 22;
  });
}

/* ── ② 선수 전적 / ③ 쉬는 시간 ─────────────────────────────── */
function drawSidePanel(side, withScore) {
  var pl = S.players[side], st = S.stats;
  var panelW = 430;
  var x = side === 0 ? 300 : W - 300 - panelW;
  var y = 268;
  // 이름 판
  var g = ctx.createLinearGradient(x, y, x + panelW, y);
  g.addColorStop(0, side === 0 ? '#c0212f' : '#12419c');
  g.addColorStop(1, side === 0 ? '#8c1f2a' : '#0d2f75');
  ctx.fillStyle = g;
  roundRect(ctx, x, y, panelW, 150, 14);
  ctx.fill();
  var tx = side === 0 ? x + panelW - 22 : x + 22;
  var align = side === 0 ? 'right' : 'left';
  drawNamePlate(side, tx, y + 46, align, panelW - 44);

  if (withScore) {
    var ss = S.style.score;
    var sx = side === 0 ? x + panelW + 60 : x - 60;
    text(pl.score || '0', sx, y + 122, ss, { align: 'center', weight: 900, shadow: 16 });
  }

  // 누적상금
  var py = y + 168;
  ctx.fillStyle = 'rgba(226,232,240,.92)';
  roundRect(ctx, x, py, panelW, 46, 8);
  ctx.fill();
  text(st.prizeLabel, x + panelW / 2, py + 33, S.style.prize,
    { align: 'center', color: '#0b0d11', maxW: panelW - 30, weight: 800 });
  ctx.fillStyle = 'rgba(18,22,30,.55)';
  roundRect(ctx, x, py + 52, panelW, 56, 8);
  ctx.fill();
  text(pl.prize || '', x + panelW / 2, py + 90, S.style.prize,
    { align: 'center', color: side === 0 ? '#ff6b6b' : '#7cb6ff',
      maxW: panelW - 30, weight: 900 });

  // VS 목록
  var vy = py + 128;
  ctx.fillStyle = 'rgba(18,22,30,.5)';
  var vs = lines(pl.vs);
  var vh = vs.length * (S.style.vsList.size + 18) + 20;
  roundRect(ctx, x, vy, panelW, vh, 8);
  ctx.fill();
  var ly = vy + 10;
  vs.forEach(function (ln) {
    ly += S.style.vsList.size + 18;
    text(ln.text, x + panelW / 2, ly - 6, S.style.vsList,
      { align: 'center', maxW: panelW - 30, weight: ln.kind === 'chip' ? 900 : 600 });
  });
}

function drawStatsCenter() {
  var st = S.stats, cx = W / 2;
  var y = 250;
  text(st.heading, cx, y, S.style.heading, { align: 'center', maxW: 420, weight: 700 });
  y += 46;
  text(st.sub, cx, y, S.style.sub, { align: 'center', maxW: 420, weight: 800 });
  y += 30;

  var bw = 360, bx = cx - bw / 2;
  st.rows.forEach(function (row) {
    ctx.fillStyle = 'rgba(28,32,40,.95)';
    roundRect(ctx, bx, y, bw, 44, 6); ctx.fill();
    text(row.label, cx, y + 31, S.style.rowLabel, { align: 'center', maxW: bw - 20, weight: 800 });
    y += 52;
    ctx.fillStyle = 'rgba(226,232,240,.94)';
    roundRect(ctx, bx, y, bw, 84, 6); ctx.fill();
    ctx.strokeStyle = 'rgba(90,100,120,.5)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(cx, y + 12); ctx.lineTo(cx, y + 72); ctx.stroke();
    text(row.a, cx - bw / 4, y + 62, S.style.rowValue,
      { align: 'center', color: '#d92d3c', maxW: bw / 2 - 20, weight: 900 });
    text(row.b, cx + bw / 4, y + 62, S.style.rowValue,
      { align: 'center', color: '#1552d0', maxW: bw / 2 - 20, weight: 900 });
    y += 96;
  });

  ctx.fillStyle = 'rgba(28,32,40,.95)';
  roundRect(ctx, bx, y, bw, 40, 6); ctx.fill();
  text(st.period, cx, y + 28, S.style.period, { align: 'center', maxW: bw - 20, weight: 700 });
  y += 48;

  ctx.fillStyle = 'rgba(28,32,40,.95)';
  roundRect(ctx, bx, y, bw, 42, 6); ctx.fill();
  text(st.muLabel, cx, y + 29, S.style.rowLabel, { align: 'center', maxW: bw - 20, weight: 800 });
  y += 50;
  ctx.fillStyle = 'rgba(226,232,240,.94)';
  roundRect(ctx, bx, y, bw, 94, 6); ctx.fill();
  ctx.strokeStyle = 'rgba(90,100,120,.5)'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(cx, y + 12); ctx.lineTo(cx, y + 82); ctx.stroke();
  text(st.muA, cx - bw / 4, y + 40, S.style.rowLabel,
    { align: 'center', color: '#d92d3c', maxW: bw / 2 - 20, weight: 900 });
  text(st.muAVal, cx - bw / 4, y + 82, S.style.rowValue,
    { align: 'center', color: '#d92d3c', maxW: bw / 2 - 20, weight: 900 });
  text(st.muB, cx + bw / 4, y + 40, S.style.rowLabel,
    { align: 'center', color: '#1552d0', maxW: bw / 2 - 20, weight: 900 });
  text(st.muBVal, cx + bw / 4, y + 82, S.style.rowValue,
    { align: 'center', color: '#1552d0', maxW: bw / 2 - 20, weight: 900 });
  y += 106;

  var foot = lines(st.foot).filter(function (l) { return l.kind !== 'gap'; });
  if (foot.length) {
    var fh = foot.length * (S.style.foot.size + 12) + 18;
    ctx.fillStyle = 'rgba(226,232,240,.94)';
    roundRect(ctx, bx, y, bw, fh, 6); ctx.fill();
    var fy = y + 8;
    foot.forEach(function (ln, i) {
      fy += S.style.foot.size + 12;
      text(ln.text, cx, fy - 4, S.style.foot,
        { align: 'center', maxW: bw - 24, weight: i === 0 ? 900 : 700 });
    });
    y += fh + 16;
  }
  if (st.timer) {
    text(st.timer, cx, Math.min(y + S.style.timer.size, H - 40), S.style.timer,
      { align: 'center', weight: 900, shadow: 14 });
  }
}

/* ── ④ 경기 결과 ───────────────────────────────────────────── */
function drawWinner() {
  var w = S.winner, cx = W / 2;
  text(w.vsText, cx, 560, S.style.vsBig, { align: 'center', weight: 800, shadow: 16 });

  [0, 1].forEach(function (side) {
    var pl = S.players[side];
    var plateW = 520;
    var x = side === 0 ? 120 : W - 120 - plateW;
    var y = 690;
    ctx.fillStyle = 'rgba(226,232,240,.86)';
    ctx.fillRect(x, y, plateW, 96);
    var inner = side === 0 ? x + 24 : x + plateW - 24;
    var align = side === 0 ? 'left' : 'right';
    // 닉네임 + 이름을 한 줄로
    var label = pl.nick + '  ' + pl.name + (pl.race ? ' ' + pl.race : '');
    text(label, inner, y + 46, S.style.pname,
      { align: align, color: '#12161d', maxW: plateW - 48, weight: 900 });
    text(pl.prize || '', inner, y + 84, S.style.prize,
      { align: align, color: side === 0 ? '#d92d3c' : '#1552d0',
        maxW: plateW - 48, weight: 900 });
    if (pl.delta) {
      text(pl.delta, x + plateW / 2, y + 190, S.style.vsBig,
        { align: 'center', maxW: plateW, weight: 800, shadow: 14 });
    }
    if (side === w.side) {
      var by = 420;
      if (w.ribbon) {
        setFont(S.style.ribbon.size, 800, S.style.ribbon.font);
        var rw = ctx.measureText(w.ribbon).width + 34;
        ctx.fillStyle = '#e0392b';
        roundRect(ctx, x + 8, by - 40, rw, 44, 8); ctx.fill();
        text(w.ribbon, x + 8 + rw / 2, by - 10, S.style.ribbon,
          { align: 'center', weight: 800 });
      }
      text(w.label, x + 12, by + S.style.winnerLabel.size, S.style.winnerLabel,
        { align: 'left', maxW: plateW, weight: 900, shadow: 18 });
    }
  });
}

/* ── ⑤ 다음 경기 ───────────────────────────────────────────── */
function drawNext() {
  var n = S.next, cx = W / 2;
  text(n.heading, cx, 470, S.style.nextHead,
    { align: 'center', maxW: 900, weight: 900, shadow: 20 });

  [0, 1].forEach(function (side) {
    var plateW = 520;
    var x = side === 0 ? 100 : W - 100 - plateW;
    var y = 640;
    ctx.fillStyle = 'rgba(226,232,240,.86)';
    ctx.fillRect(x, y, plateW, 118);
    var inner = side === 0 ? x + 26 : x + plateW - 26;
    var align = side === 0 ? 'left' : 'right';
    text(S.players[side].nick, inner, y + 44, S.style.nick,
      { align: align, color: '#3b4450', maxW: plateW - 52, weight: 500 });
    var pl = S.players[side];
    var label = pl.name + (pl.race ? ' ' + pl.race : '');
    text(label, inner, y + 100, S.style.pname,
      { align: align, color: '#12161d', maxW: plateW - 52, weight: 900 });
  });

  if (n.when) {
    ctx.fillStyle = 'rgba(10,13,19,.72)';
    ctx.fillRect(0, H - 190, W, 120);
    text(n.when, cx, H - 108, S.style.when, { align: 'center', maxW: W - 200, weight: 800 });
  }
}

/* ── 그리기 ────────────────────────────────────────────────── */
function draw() {
  var need = [S.logoSponsor, S.logoBroadcast, S.players[0].photo, S.players[1].photo];
  var got = [null, null, null, null];
  var left = need.length;
  need.forEach(function (src, i) {
    loadImage(src, function (im) { got[i] = im; if (--left === 0) paint(got); });
  });
}

function paint(g) {
  ctx.clearRect(0, 0, W, H);
  drawBackground();
  var dim = [false, false];
  if (S.type === 'winner') { dim[1 - S.winner.side] = true; }
  drawPhoto(0, g[2], dim[0]);
  drawPhoto(1, g[3], dim[1]);
  drawTopBar({ sponsor: g[0], broadcast: g[1] });

  if (S.type === 'matchup') {
    drawNamePlate(0, 310, 830, 'center', 520);
    drawNamePlate(1, W - 310, 830, 'center', 520);
    drawMatchup();
  } else if (S.type === 'stats' || S.type === 'score') {
    drawSidePanel(0, S.type === 'score');
    drawSidePanel(1, S.type === 'score');
    drawStatsCenter();
  } else if (S.type === 'winner') {
    drawWinner();
  } else if (S.type === 'next') {
    drawNext();
  }
  save();
}

/* ── 시즌 프로필 사진 ──────────────────────────────────────────
   같은 선수라도 시즌마다 사진이 다릅니다. ASL S19 김명운과 S20 김명운을
   따로 고를 수 있게, 있는 시즌만 목록에 올려 둡니다. */
function $(id) { return document.getElementById(id); }

function seasonPath(slug, season) {
  var nn = (season < 10 ? '0' : '') + season;
  return '../img/players/seasons/' + slug + '-s' + nn + '.webp';
}

function playerInfo(name) {
  return PLAYERS.find(function (p) { return p.name === name; });
}

/** 그 선수에게 있는 시즌만 목록에 채웁니다. 최근 시즌이 위로 옵니다. */
function fillSeasons(i) {
  var sel = $('season' + (i + 1));
  if (!sel) return;
  var info = playerInfo(S.players[i].name);
  var list = (info && info.seasons) || [];
  sel.innerHTML = '<option value="">사진 없음</option>' +
    list.slice().reverse().map(function (v) {
      return '<option value="' + v + '">ASL S' + v + '</option>';
    }).join('');
  sel.value = S.players[i].season === '' ? '' : String(S.players[i].season);
  sel.disabled = list.length === 0;
}

/** 고른 시즌 사진을 실제로 붙입니다. */
function applySeason(i, season) {
  var pl = S.players[i], info = playerInfo(pl.name);
  pl.season = season;
  if (season !== '' && info) {
    pl.photo = seasonPath(info.slug, parseInt(season, 10));
    pl.photoFrom = 'season';
  } else if (pl.photoFrom === 'season') {
    pl.photo = null;
    pl.photoFrom = null;
  }
  pl.zoom = 1; pl.ox = 0; pl.oy = 0;
  var z = $('zoom' + (i + 1)); if (z) z.value = 1;
}

function bind(id, get, set) {
  var el = $(id);
  if (!el) return;
  el.value = get();
  el.addEventListener('input', function () { set(el.value); draw(); });
}

function bindPhoto(id, onLoad) {
  var el = $(id);
  if (!el) return;
  el.addEventListener('change', function () {
    var f = el.files && el.files[0];
    if (!f) return;
    var fr = new FileReader();
    fr.onload = function () { onLoad(fr.result); draw(); };
    fr.readAsDataURL(f);
  });
}

/** 글자 모양(크기·색·폰트) 조절칸을 붙입니다. */
function bindStyle(key) {
  var st = S.style[key];
  if (!st) return;
  bind('st_' + key + '_size', function () { return st.size; },
    function (v) { st.size = parseInt(v, 10) || st.size; });
  bind('st_' + key + '_color', function () { return st.color; },
    function (v) { st.color = v; });
  bind('st_' + key + '_font', function () { return st.font; },
    function (v) { st.font = v; });
}

/** 지금 고른 CG 종류에 필요한 칸만 보여 줍니다. */
function showTypeFields() {
  document.querySelectorAll('[data-for]').forEach(function (el) {
    el.hidden = el.getAttribute('data-for').split(' ').indexOf(S.type) < 0;
  });
  document.querySelectorAll('[data-type]').forEach(function (b) {
    b.classList.toggle('on', b.getAttribute('data-type') === S.type);
  });
}

function setupControls() {
  document.querySelectorAll('[data-type]').forEach(function (b) {
    b.addEventListener('click', function () {
      S.type = b.getAttribute('data-type');
      showTypeFields();
      draw();
    });
  });

  bind('title', function () { return S.title; }, function (v) { S.title = v; });
  bind('sponsorText', function () { return S.sponsorText; }, function (v) { S.sponsorText = v; });
  bind('liveBadge', function () { return S.liveBadge; }, function (v) { S.liveBadge = v; });
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
        // 직접 올린 사진은 건드리지 않습니다 — 등록 사진일 때만 바꿉니다.
        if (S.players[i].photoFrom !== 'upload') {
          var ss = (hit && hit.seasons) || [];
          if (ss.length) {
            applySeason(i, String(ss[ss.length - 1]));   // 가장 최근 시즌
          } else if (hit && hit.photo) {
            S.players[i].photo = '../img/players/' + encodeURIComponent(hit.photo);
            S.players[i].photoFrom = 'lib';
            S.players[i].season = '';
            S.players[i].zoom = 1; S.players[i].ox = 0; S.players[i].oy = 0;
            var z = $('zoom' + n); if (z) z.value = 1;
          } else if (S.players[i].photoFrom === 'lib' ||
                     S.players[i].photoFrom === 'season') {
            S.players[i].photo = null;
            S.players[i].photoFrom = null;
            S.players[i].season = '';
          }
        }
        fillSeasons(i);
      });
    bind('race' + n, function () { return S.players[i].race; },
      function (v) { S.players[i].race = v; });
    bind('zoom' + n, function () { return S.players[i].zoom; },
      function (v) { S.players[i].zoom = parseFloat(v); });
    var sel = $('season' + n);
    if (sel) sel.addEventListener('change', function () { applySeason(i, sel.value); draw(); });
    bind('prize' + n, function () { return S.players[i].prize; },
      function (v) { S.players[i].prize = v; });
    bind('score' + n, function () { return S.players[i].score; },
      function (v) { S.players[i].score = v; });
    bind('delta' + n, function () { return S.players[i].delta; },
      function (v) { S.players[i].delta = v; });
    bind('vs' + n, function () { return S.players[i].vs; },
      function (v) { S.players[i].vs = v; });
    bindPhoto('photo' + n, function (d) {
      S.players[i].photo = d;
      S.players[i].photoFrom = 'upload';
      S.players[i].season = '';
      var sv = $('season' + n); if (sv) sv.value = '';
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

  var st = S.stats;
  bind('stHeading', function () { return st.heading; }, function (v) { st.heading = v; });
  bind('stSub', function () { return st.sub; }, function (v) { st.sub = v; });
  bind('stPrizeLabel', function () { return st.prizeLabel; }, function (v) { st.prizeLabel = v; });
  bind('stPeriod', function () { return st.period; }, function (v) { st.period = v; });
  bind('stMuLabel', function () { return st.muLabel; }, function (v) { st.muLabel = v; });
  bind('stMuA', function () { return st.muA; }, function (v) { st.muA = v; });
  bind('stMuAVal', function () { return st.muAVal; }, function (v) { st.muAVal = v; });
  bind('stMuB', function () { return st.muB; }, function (v) { st.muB = v; });
  bind('stMuBVal', function () { return st.muBVal; }, function (v) { st.muBVal = v; });
  bind('stFoot', function () { return st.foot; }, function (v) { st.foot = v; });
  bind('stTimer', function () { return st.timer; }, function (v) { st.timer = v; });
  st.rows.forEach(function (row, i) {
    bind('stRowLabel' + i, function () { return row.label; }, function (v) { row.label = v; });
    bind('stRowA' + i, function () { return row.a; }, function (v) { row.a = v; });
    bind('stRowB' + i, function () { return row.b; }, function (v) { row.b = v; });
  });

  bind('winVs', function () { return S.winner.vsText; }, function (v) { S.winner.vsText = v; });
  bind('winLabel', function () { return S.winner.label; }, function (v) { S.winner.label = v; });
  bind('winRibbon', function () { return S.winner.ribbon; }, function (v) { S.winner.ribbon = v; });
  bind('winSide', function () { return String(S.winner.side); },
    function (v) { S.winner.side = parseInt(v, 10) || 0; });
  bind('nextHeading', function () { return S.next.heading; }, function (v) { S.next.heading = v; });
  bind('nextWhen', function () { return S.next.when; }, function (v) { S.next.when = v; });

  Object.keys(S.style).forEach(bindStyle);

  $('swap').addEventListener('click', function () {
    S.players.reverse();
    S.winner.side = 1 - S.winner.side;
    fillForm(); draw();
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
    ['nick', 'name', 'race', 'zoom', 'prize', 'score', 'delta', 'vs'].forEach(function (k) {
      var el = $(k + n); if (el) el.value = p[k];
    });
    fillSeasons(i);
  });
  ['title', 'sponsorText', 'liveBadge', 'bgLeft', 'bgRight'].forEach(function (k) {
    var el = $(k); if (el) el.value = S[k];
  });
  S.boxes.forEach(function (b, i) {
    if ($('boxTitle' + i)) $('boxTitle' + i).value = b.title;
    if ($('boxBody' + i)) $('boxBody' + i).value = b.body;
  });
  var st = S.stats;
  [['stHeading', 'heading'], ['stSub', 'sub'], ['stPrizeLabel', 'prizeLabel'],
   ['stPeriod', 'period'], ['stMuLabel', 'muLabel'], ['stMuA', 'muA'],
   ['stMuAVal', 'muAVal'], ['stMuB', 'muB'], ['stMuBVal', 'muBVal'],
   ['stFoot', 'foot'], ['stTimer', 'timer']].forEach(function (p) {
    if ($(p[0])) $(p[0]).value = st[p[1]];
  });
  st.rows.forEach(function (row, i) {
    if ($('stRowLabel' + i)) $('stRowLabel' + i).value = row.label;
    if ($('stRowA' + i)) $('stRowA' + i).value = row.a;
    if ($('stRowB' + i)) $('stRowB' + i).value = row.b;
  });
  if ($('winVs')) $('winVs').value = S.winner.vsText;
  if ($('winLabel')) $('winLabel').value = S.winner.label;
  if ($('winRibbon')) $('winRibbon').value = S.winner.ribbon;
  if ($('winSide')) $('winSide').value = String(S.winner.side);
  if ($('nextHeading')) $('nextHeading').value = S.next.heading;
  if ($('nextWhen')) $('nextWhen').value = S.next.when;
  Object.keys(S.style).forEach(function (k) {
    var s2 = S.style[k];
    if ($('st_' + k + '_size')) $('st_' + k + '_size').value = s2.size;
    if ($('st_' + k + '_color')) $('st_' + k + '_color').value = s2.color;
    if ($('st_' + k + '_font')) $('st_' + k + '_font').value = s2.font;
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
  var dragging = -1, last = null;
  cv.addEventListener('mousedown', function (e) {
    var pos = canvasPos(e);
    dragging = hitPhoto(pos);
    last = pos;
    if (dragging >= 0) cv.style.cursor = 'grabbing';
  });
  window.addEventListener('mousemove', function (e) {
    if (dragging < 0) return;
    var pos = canvasPos(e);
    S.players[dragging].ox += pos.x - last.x;
    S.players[dragging].oy += pos.y - last.y;
    last = pos;
    draw();
  });
  window.addEventListener('mouseup', function () {
    dragging = -1; cv.style.cursor = '';
  });
  cv.addEventListener('wheel', function (e) {
    var i = hitPhoto(canvasPos(e));
    if (i < 0) return;
    e.preventDefault();
    var p = S.players[i];
    p.zoom = Math.min(4, Math.max(0.4, p.zoom * (e.deltaY < 0 ? 1.06 : 0.94)));
    var z = $('zoom' + (i + 1)); if (z) z.value = p.zoom;
    draw();
  }, { passive: false });

  // 사진 파일을 미리보기에 바로 끌어다 놓기
  cv.addEventListener('dragover', function (e) { e.preventDefault(); });
  cv.addEventListener('drop', function (e) {
    e.preventDefault();
    var f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (!f) return;
    var i = hitPhoto(canvasPos(e));
    if (i < 0) return;
    var fr = new FileReader();
    fr.onload = function () {
      S.players[i].photo = fr.result;
      S.players[i].photoFrom = 'upload';
      S.players[i].zoom = 1; S.players[i].ox = 0; S.players[i].oy = 0;
      var z = $('zoom' + (i + 1)); if (z) z.value = 1;
      draw();
    };
    fr.readAsDataURL(f);
  });
}

function stamp() {
  var d = new Date();
  function p(n) { return (n < 10 ? '0' : '') + n; }
  return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + '-' +
    p(d.getHours()) + p(d.getMinutes());
}

function download() {
  var a = document.createElement('a');
  a.download = 'cg-' + S.type + '-' + S.players[0].name + '-vs-' +
    S.players[1].name + '-' + stamp() + '.png';
  a.href = cv.toDataURL('image/png');
  a.click();
}

function exportJson() {
  var a = document.createElement('a');
  a.download = 'cg-setting-' + stamp() + '.json';
  a.href = 'data:application/json;charset=utf-8,' +
    encodeURIComponent(JSON.stringify(S, null, 1));
  a.click();
}

function importJson(ev) {
  var f = ev.target.files && ev.target.files[0];
  if (!f) return;
  var fr = new FileReader();
  fr.onload = function () {
    try {
      var got = JSON.parse(fr.result), base = defaults();
      S = Object.assign(base, got);
      S.style = Object.assign(base.style, got.style || {});
      fillForm(); showTypeFields(); draw();
    } catch (e) { alert('설정 파일을 읽지 못했습니다.'); }
  };
  fr.readAsText(f);
}

/* ── 저장 ──────────────────────────────────────────────────── */
var KEY = 'sc-cg-v2';

function save() {
  try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { /* 용량 초과는 무시 */ }
}

function load() {
  try {
    var raw = localStorage.getItem(KEY);
    if (!raw) return;
    var got = JSON.parse(raw), base = defaults();
    S = Object.assign(base, got);
    S.style = Object.assign(base.style, got.style || {});
    S.stats = Object.assign(base.stats, got.stats || {});
    S.winner = Object.assign(base.winner, got.winner || {});
    S.next = Object.assign(base.next, got.next || {});
  } catch (e) { /* 깨진 값이면 기본값으로 */ }
}

load();
setupControls();
fillForm();
showTypeFields();
setupCanvasDrag();
draw();
</script>
</body>
</html>
