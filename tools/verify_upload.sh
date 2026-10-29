#!/bin/bash
if [ -z "${NF_LC_WAS:-}" ]; then
  for _nf_lcv in "${LC_ALL:-}" "${LC_MESSAGES:-}" "${LANG:-}"; do
    case "$_nf_lcv" in C|POSIX|C.*|"") : ;; *) NF_LC_WAS="$_nf_lcv"; break ;; esac
  done
  unset _nf_lcv
fi
export NF_LC_WAS
LC_ALL=C; export LC_ALL
set -uo pipefail

BUNDLE="${1:?번들 id 가 필요하다 — 예: com.example.MyApp}"
BUILD="${2:?빌드 번호가 필요하다}"
MAX_MIN="${3:-10}"
ASC="$(dirname "$0")/asc.py"

[ -f "$ASC" ] || { echo "⚠️  $ASC 가 없다 — 도착 확인을 못 한다. 업로드 성공은 «도착»이 아니다."; exit 0; }

RAW=$(python3 "$ASC" raw GET "/v1/apps?filter[bundleId]=$BUNDLE&fields[apps]=name,bundleId" 2>&1)
APP_JSON=$(printf '%s\n' "$RAW" | grep -v '^\[asc\]')
if ! printf '%s' "$APP_JSON" | python3 -I -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
  printf '%s\n' "$APP_JSON" >&2
  echo "❌ App Store Connect 에 물어보지 못해 «도착 확인»을 못 했다." >&2
  echo "   애플에 물어볼 열쇠를 못 찾았습니다 — 제가 자리를 확인합니다." >&2
  echo "   [모델] ~/.appstoreconnect/asc.env 또는 이 앱의 tools/asc.env" >&2
  exit 1
fi
APP_ID=$(printf '%s' "$APP_JSON" | python3 -I -c "
import sys, json
try: d = json.load(sys.stdin)
except Exception: sys.exit()
for a in d.get('data', []):
    if a['attributes'].get('bundleId') == sys.argv[1]:
        print(a['id'], a['attributes'].get('name', '')); break
" "$BUNDLE")
[ -n "$APP_ID" ] || { echo "❌ 번들 id '$BUNDLE' 로 앱을 못 찾았다 — 상수를 확인한다"; exit 1; }

echo "▸ 도착 확인: ${APP_ID%% *}  「${APP_ID#* }」  빌드(앱을 실행할 수 있는 파일로 만든 것) $BUILD  (최대 ${MAX_MIN}분)"
ID="${APP_ID%% *}"

TRIES=$(( MAX_MIN * 2 ))
for i in $(seq 1 "$TRIES"); do
  STATE=$(python3 "$ASC" raw GET \
    "/v1/builds?filter[app]=$ID&limit=50&fields[builds]=version,processingState" 2>/dev/null \
    | python3 -I -c "
import sys, json
try: d = json.load(sys.stdin)
except Exception: sys.exit()
for b in d.get('data', []):
    if b['attributes'].get('version') == sys.argv[1]:
        print(b['attributes'].get('processingState')); break
" "$BUILD")
  case "$STATE" in
    VALID)          echo "   ✅ $BUILD 번 도착 · 처리 완료(VALID)"; exit 0 ;;
    PROCESSING)     echo "   … 처리 중 ($((i*30))초)" ;;
    INVALID|FAILED) echo "   ❌ 애플이 $BUILD 번을 거절했다 ($STATE)"
                    echo "      no_reply@email.apple.com 메일에서 ITMS-#### 코드를 확인한다"; exit 1 ;;
    *)              echo "   … 아직 목록에 없다 ($((i*30))초)" ;;
  esac
  [ "$i" = "$TRIES" ] && {
    echo "   ❌ ${MAX_MIN}분이 지나도 $BUILD 번이 안 보인다."
    echo "      전송은 됐지만 **처리 단계에서 버려졌을** 가능성이 높다 —"
    echo "      no_reply@email.apple.com 메일에서 ITMS-#### 코드를 확인한다"
    exit 1
  }
  sleep 30
done
