# 스타크래프트 기록실 — 작업 안내

이 폴더에서 일하는 Claude 를 위한 메모입니다. 휴대폰에서 짧게 시켜도
바로 알아듣도록 필요한 것만 적었습니다.

## 이게 뭔가

정적 사이트 세 개가 한 폴더에 있습니다.

| | 주소 | 내용 |
| --- | --- | --- |
| 끝장전 | `pubgin.com/endgame/` | 296매치 · 2,656세트 · 선수 35명 |
| ASL | `pubgin.com/endgame/asl/` | 23개 대회 · 1,299매치 · 2,177세트 · 선수 95명 |
| CG 제작 툴 | `pubgin.com/endgame/admin/` | 대진표 이미지 만들기 (관리자 로그인) |

**실제 사이트는 카페24의 pubgin.com 입니다.** GitHub 은 백업일 뿐이고,
거기 올린다고 사이트가 바뀌지 않습니다.

## 자주 쓰는 명령

새 PC 에서 **처음 한 번만** — FTP 정보를 넣고 전부 잘 되는지 확인합니다.

```bash
python3 tools/setup.py
```

그다음부터는 이것만 씁니다.

```bash
python3 tools/update.py              # 구글시트 → 데이터 → 사이트 → 업로드 (제일 많이 씀)
python3 tools/update.py --dry-run    # 아무것도 바꾸지 않고 무엇이 달라지는지만
python3 tools/build.py               # 사이트만 다시 만들기
python3 tools/deploy.py              # 만든 것을 FTP 로 올리기 (바뀐 파일만)
```

슬래시 명령으로도 됩니다 — `/갱신` `/확인` `/배포` `/상태`

## 꼭 지킬 것

- **`index.html`, `p/`, `asl/`, `admin/`, `csv/`, `xlsx/`, `sheets.html` 은 빌드 결과물입니다.**
  직접 고치지 마세요. 고칠 곳은 `tools/` 와 `data/` 입니다.
- 화면을 바꾸려면 `tools/site.css`, `tools/app.js`, `tools/asl_app.js`,
  `tools/cg_app.js`, `tools/render.py` 를 고치고 `build.py` 를 돌립니다.
- `tools/build.py` 의 `if __name__ == '__main__'` 블록은 **항상 파일 맨 끝**에
  있어야 합니다. 그 뒤에 함수를 덧붙이면 NameError 가 납니다.
- **`data/deploy.json` 과 `admin/config.php` 는 저장소에 올리지 않습니다.**
  각각 FTP 비밀번호와 관리자 계정이 들어 있습니다.
- `update.py` 는 기록이 줄면 멈춥니다. 시트에서 줄이 지워지는 사고를 막기
  위해서입니다. 사용자가 의도한 삭제라고 확인해 주기 전에는 `--force` 를
  붙이지 마세요.

## 데이터가 어디서 오나

```
data/asl.json       ASL 정본  ← 구글시트에서 받아옴 (data/asl-source.json 에 주소)
data/endgame.json   끝장전 정본  ← 방송팀 시트에서 뽑아 둔 것 (아직 수동)
data/videos.json    경기 → 유튜브 다시보기 매핑 (비어 있음)
data/site.json      사이트 주소 (baseUrl)
```

빌드는 원본을 절대 고치지 않습니다. 나머지는 전부 다시 계산해서 만듭니다.

## 알아 둘 사실

- 끝장전은 사실상 9세트 고정입니다 (296경기 중 294경기).
- ASL 은 경기 날짜가 없어 대회·라운드 순서로만 정리합니다.
- ASL 동족전 549세트는 종족 상성 집계에서 빠집니다.
- ASL 시트에서 이영호가 9줄만 P·Z 로 적혀 있어 빌드 때 T 로 맞춥니다.
  원본 시트는 건드리지 않고, 실행할 때마다 알려 줍니다.
- 끝장전 296경기 전부 `youtubeUrl` 이 비어 있습니다. 영상을 붙이려면
  `tools/fetch_videos.py` 에 YouTube Data API 키가 필요합니다.

## 자세한 내용

`README.md` 에 전부 있습니다. 빌드 구조, 도메인 옮기기, 관리자 로그인,
데이터 확보 방안까지 정리돼 있습니다.
