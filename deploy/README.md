# 서버에서 직접 운영하기 — starendgame.com (2026-09-24)

starendgame.com 이 도는 단독 서버(`175.118.124.225`, Ubuntu 24.04, nginx) **안에서**
갱신까지 전부 돌립니다. pubgin.com 이 2026-09-23 에 한 것과 같은 방식이고,
설치 꾸러미 모양도 맞췄습니다(pubg-meta-src 의 `deploy/`).

| | 전 (GitHub Actions) | 후 (이 서버) |
|---|---|---|
| 도는 곳 | 해외 GitHub 러너 | 이 서버 (systemd `starendgame.timer`) |
| 주기 | '15분마다' 라지만 **실제 3~5시간** (GitHub 이 흘림) | **5분마다, 적힌 대로** |
| 배포 | SSH 로 337개 전송 | **같은 기계 안 폴더 복사** — 네트워크 없음 |
| 비밀번호 | GitHub 시크릿에 root 비밀번호 | **필요 없음** |
| GitHub | 운영의 중심 | 코드 창고 (서버가 5분마다 새 코드를 받아 감) |

**pubgin 과 다른 점 두 가지**

- **상시 서비스가 아니라 타이머입니다.** pubgin 은 PUBG API 를 실시간으로 따라가야 해서
  계속 켜 두는 프로그램이지만, 이쪽은 구글시트가 원본이라 5분마다 한 번 돌고 끝나면 됩니다.
- **토큰이 필요 없습니다.** 이 저장소는 공개라 받아오는 데 열쇠가 없습니다.

> 🔒 유튜브 키·슬랙 웹훅은 **채팅·메신저에 붙여넣지 마세요.** 서버의 편집기(nano)에만 넣습니다.

---

## 1. 지금 상태 확인 (읽기만 — 아무것도 안 바뀝니다)

```bash
echo "### 1. starendgame 을 서비스하는 nginx 설정"
sudo nginx -T 2>/dev/null | grep -B2 -A16 "server_name.*starendgame" | head -50
echo; echo "### 2. 웹 폴더"
ls -la /var/www/
echo; echo "### 3. 파이썬·git·PHP"
python3 -V; git --version; php -v 2>/dev/null | head -1
echo; echo "### 4. 지금 도는 자동 작업"
systemctl list-timers --all --no-pager | head -12
echo; echo "### 5. 당첨자 명단이 웹에서 열리나 (200 이면 열림, 403·404 면 막힘)"
curl -s -o /dev/null -w "winners.json → %{http_code}\n" https://starendgame.com/admin/pz/winners.json
```

나온 내용을 그대로 Claude 에게 주세요. 5번이 **200** 이면 당첨자 명단(시청자 SOOP 아이디)이
지금 누구나 받을 수 있는 상태입니다 — 9단계에서 막습니다.

---

## 2. 필요한 프로그램 (한 번)

```bash
sudo apt-get update -q && sudo apt-get install -y git python3-openpyxl
python3 -V && git --version
```

`Python 3.12…` 와 `git version …` 이 나오면 됩니다. (`python3-openpyxl` 은 엑셀 파일을 만드는 데 씁니다.)

---

## 3. 프로그램 받기

```bash
sudo mkdir -p /opt/starendgame
sudo chown www-data:www-data /opt/starendgame
sudo -u www-data env HOME=/opt/starendgame git clone https://github.com/hspark-art/sc-endgame.git /opt/starendgame
sudo -u www-data git -C /opt/starendgame branch --show-current
```

마지막 줄이 `claude/starcraft-endgame-site-049jip` 이면 맞습니다. (받는 양은 50MB 쯤입니다. 1분 안쪽입니다.)

---

## 4. 설정 파일 만들기

```bash
sudo -u www-data cp /opt/starendgame/deploy/env.example /opt/starendgame/.env
sudo chmod 600 /opt/starendgame/.env
sudo nano /opt/starendgame/.env
```

편집기가 열리면 두 줄을 채웁니다. `DEPLOY_LOCAL_DIR=/var/www/starendgame` 은 이미 적혀 있습니다 —
**이 한 줄이 「서버 안 폴더 복사」를 켭니다.**

- `YOUTUBE_API_KEY=` 뒤에 유튜브 API 키 — 회사 PC 의 `data/youtube.json` 안 `apiKey` 값과 같습니다.
  지금 없으면 **비워 둬도 됩니다.** 사이트는 그대로 갱신되고, 새 영상 자동 연결만 쉽니다.
- `SLACK_WEBHOOK_URL=` 뒤에 슬랙 웹훅 — **새로 발급받은 주소**를 넣어 주세요
  (옛 주소는 옮겨 오던 판에 섞여 웹에 노출됐었습니다).

저장: `Ctrl+O` → `Enter` → `Ctrl+X`

---

## 5. 사이트 폴더 권한

지금까지 GitHub 이 root 계정으로 올려서, 사이트 파일 주인이 root 입니다. 이 서버의 자동 작업은
웹서버와 같은 `www-data` 계정으로 돌기 때문에 주인을 맞춰 줍니다.

```bash
sudo chown -R www-data:www-data /var/www/starendgame
```

아무 말 없이 끝나면 정상입니다.

---

## 6. 한 번 돌려보기 (중요)

자동으로 켜기 전에 **보는 앞에서** 한 번 돌립니다. 1분쯤 걸립니다 — 끝날 때까지 기다려 주세요.

```bash
sudo cp /opt/starendgame/deploy/starendgame.service /opt/starendgame/deploy/starendgame.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start starendgame
journalctl -u starendgame -n 45 --no-pager
```

끝부분에 이렇게 나오면 성공입니다.

```
  올릴 곳 이 서버 안 /var/www/starendgame (폴더 복사)
  이 서버 안 폴더로 바로 복사합니다 (네트워크 없음).
사이트가 방금 만든 것과 같습니다 ✅
```

- `사이트 폴더에 쓸 권한이 없습니다` → 5단계를 다시 하세요.
- `SFTP`·`FTP` 라는 글자가 보이면 → 4단계의 `DEPLOY_LOCAL_DIR` 줄을 확인하세요.
- 그 밖이면 나온 내용을 Claude 에게 그대로 주세요.

---

## 7. 5분 자동 켜기

```bash
sudo systemctl enable --now starendgame.timer
systemctl list-timers starendgame.timer --no-pager
```

`NEXT` 칸에 5분 안쪽 시각이 보이면 끝입니다. 이제 시트를 고치면 **5분 안에** 사이트가 바뀝니다.

---

## 8. GitHub Actions 예약 끄기 (Claude 몫)

서버가 돌기 시작하면 GitHub 쪽 예약은 Claude 가 끕니다. 두 곳이 같이 돌면 GitHub 이 root 로
파일을 올려 5단계의 주인 맞추기가 다시 틀어지기 때문입니다. 수동 실행 버튼은 비상용으로 남깁니다.

---

## 9. 보안 — 당첨자 명단 막기 (1단계 5번이 200 이었을 때)

nginx 는 `.htaccess` 를 **읽지 않습니다.** 카페24(Apache) 시절 `admin/pz/.htaccess` 가 막던
당첨자 명단·채팅 기록이 지금은 웹에서 그대로 열릴 수 있습니다. 관제 화면은 이 폴더를 PHP 로만
읽으므로(`prize_api.php`), 웹에서 막아도 아무것도 안 깨집니다. 정확한 설정 파일 위치는 1단계
결과를 보고 Claude 가 알려 드립니다.

```nginx
location ^~ /admin/pz/ { deny all; return 404; }
```

(넣은 뒤 `sudo nginx -t && sudo systemctl reload nginx`)

---

## 평소에 쓰는 명령

| 하고 싶은 것 | 명령 |
|---|---|
| 방금 뭐 했나 | `journalctl -u starendgame -n 40 --no-pager` |
| 계속 지켜보기 | `journalctl -u starendgame -f` |
| 다음 실행 언제 | `systemctl list-timers starendgame.timer --no-pager` |
| 지금 바로 한 번 | `sudo systemctl start starendgame` |
| 잠깐 멈추기 | `sudo systemctl stop starendgame.timer` |
| 다시 켜기 | `sudo systemctl start starendgame.timer` |
| 새 코드 받기 | 자동입니다 — 매 회차 처음에 GitHub 기본 브랜치를 받아 맞춥니다 |

## 알아두실 것

- **코드는 매번 GitHub 에서 받습니다.** Claude 가 기본 브랜치에 올리면 다음 회차(5분 안)에
  서버가 그대로 씁니다. 서버에서 파일을 직접 고치면 다음 회차에 되돌아가니, 고칠 것은 저장소에서.
- **상태 파일은 서버에 남습니다** — `data/.deploy-state.json` 등. 그래서 기록이 그대로면
  복사가 0개로 끝나고 20초 안에 내려갑니다. `git clean` 은 쓰지 마세요(이것들이 지워집니다).
- **사이트가 만든 것과 다르면 슬랙이 옵니다** (`tools/verify_live.py`). 조용히 낡는 일이 없습니다.
- **당첨자 명단 자동 등록**도 같은 회차에서 KST 21~02시에만 돕니다. 서버 안이라 파일을 직접 고칩니다.
