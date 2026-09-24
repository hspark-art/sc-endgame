#!/bin/sh
# starendgame.com 자동 갱신 — 서버 안에서 한 번 돌고 끝납니다 (2026-09-24)
# systemd 타이머(starendgame.timer)가 5분마다 부릅니다.
#
# 하는 일 — GitHub Actions 의 .github/workflows/update.yml 과 같은 순서입니다.
#   0. 새 코드 받기   저장소 기본 브랜치를 그대로 따라갑니다 (공개 저장소라 토큰이 필요 없습니다)
#   1. 갱신           구글시트 → 데이터 → 사이트 빌드 → 웹루트로 폴더 복사   (tools/update.py)
#   2. 확인           사이트를 직접 열어 방금 만든 것과 같은지 대조          (tools/verify_live.py)
#   3. 당첨자 명단    구글 문서 → admin/pz/winners.json  (방송 시간대 KST 21~02시에만)
#
# 손으로 한 번 돌리기:  sudo systemctl start starendgame && journalctl -u starendgame -n 60 --no-pager
set -u
cd /opt/starendgame || exit 1

BRANCH=claude/starcraft-endgame-site-049jip

# 0) 새 코드. 받아지면 그대로 맞추고, GitHub 에 못 닿으면 있던 코드로 계속합니다.
#    reset --hard 는 '저장소가 추적하는 파일'만 되돌립니다 — 빌드 결과물(index.php …)은
#    어차피 곧 다시 만들고, 상태 파일(data/.deploy-state.json 등)과 .env 는 추적 밖이라 그대로입니다.
#    🔴 git clean 은 쓰지 마세요. 상태 파일이 지워져 매번 전부 다시 복사하고 '마지막 갱신'도 흔들립니다.
if git fetch -q origin "$BRANCH" 2>/dev/null; then
  git reset -q --hard FETCH_HEAD
  echo "코드: $(git log -1 --format='%h %s' | cut -c1-72)"
else
  echo "코드: GitHub 에 닿지 못해 있던 코드로 돕니다"
fi

python3 tools/update.py --auto-apply-deletes
rc=$?
# 갱신이 성공했을 때만 사이트를 대조합니다 — 실패했으면 옛것인 게 당연해 알림만 두 번 갑니다.
if [ "$rc" -eq 0 ]; then
  python3 tools/verify_live.py || rc=$?
fi

H=$(TZ=Asia/Seoul date +%-H)
if [ "$H" -ge 21 ] || [ "$H" -le 2 ]; then
  python3 tools/gdoc_import.py || echo "(당첨자 명단 단계는 실패했지만 사이트 갱신과는 별개입니다)"
fi
exit "$rc"
