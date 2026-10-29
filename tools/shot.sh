#!/bin/bash
if [ -z "${NF_LC_WAS:-}" ]; then
  for _nf_lcv in "${LC_ALL:-}" "${LC_MESSAGES:-}" "${LANG:-}"; do
    case "$_nf_lcv" in C|POSIX|C.*|"") : ;; *) NF_LC_WAS="$_nf_lcv"; break ;; esac
  done
  unset _nf_lcv
fi
export NF_LC_WAS
LC_ALL=C; export LC_ALL
set -e

die() { echo "⛔ $*" >&2; exit 1; }

rec() {
  local SELF="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")"
  local L="$(cd "$(dirname "$SELF")/../bin" 2>/dev/null && pwd)/ledger.sh"
  [ -x "$L" ] || return 0
  "$L" "$1" "$2" "$3" "${4:-}" >/dev/null 2>&1 || true
}


ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
PROJ="${SHOT_PROJ:-$(find "$ROOT" -maxdepth 3 -name "*.xcodeproj" -not -path "*/.*" | head -1)}"
[ -n "$PROJ" ] || die "*.xcodeproj 를 못 찾았다. SHOT_PROJ 로 지정할 것."
SCHEME=$(basename "$PROJ" .xcodeproj)
OUT="${SHOT_DIR:-/tmp/${SCHEME}-shots}"
ARG="${SHOT_ARG:--screen}"
SHOT_MIN="${SHOT_MIN:-150000}"
SHOT_TRIES="${SHOT_TRIES:-25}"
mkdir -p "$OUT"

[ -f "$(dirname "$PROJ")/project.yml" ] && command -v xcodegen >/dev/null && \
  (cd "$(dirname "$PROJ")" && xcodegen generate >/dev/null)

UDID=$(xcrun simctl list devices | grep Booted | head -1 | sed -E 's/.*\(([0-9A-F-]{36})\).*/\1/')
if [ -z "$UDID" ]; then
  UDID=$(xcrun simctl list devices available | grep -E "iPhone 1[6-9]|iPhone 2[0-9]" \
         | head -1 | sed -E 's/.*\(([0-9A-F-]{36})\).*/\1/')
  [ -n "$UDID" ] || die "쓸 수 있는 iPhone 시뮬레이터가 없다."
  echo "부팅: $UDID"
  xcrun simctl boot "$UDID"
  xcrun simctl bootstatus "$UDID" -b >/dev/null 2>&1 || true
fi

xcrun simctl spawn "$UDID" defaults write com.apple.Accessibility ReduceMotionEnabled -bool true 2>/dev/null || true

cd "$(dirname "$PROJ")"
xcodebuild -project "$(basename "$PROJ")" -scheme "$SCHEME" \
           -destination "id=$UDID" -configuration Debug -quiet build
read -r APP BUNDLE < <(xcodebuild -project "$(basename "$PROJ")" -scheme "$SCHEME" \
  -destination "id=$UDID" -configuration Debug -showBuildSettings 2>/dev/null \
  | awk -F' = ' '/ BUILT_PRODUCTS_DIR/{d=$2} / FULL_PRODUCT_NAME/{n=$2}
                 / PRODUCT_BUNDLE_IDENTIFIER/{b=$2} END{print d"/"n, b}')
[ -d "$APP" ] || die "빌드 산출물을 못 찾았다: $APP"
xcrun simctl install "$UDID" "$APP"

shoot() {
  local name=$1; shift
  xcrun simctl terminate "$UDID" "$BUNDLE" >/dev/null 2>&1 || true
  xcrun simctl launch "$UDID" "$BUNDLE" $SHOT_EXTRA "$@" >/dev/null
  local sz=0 waited=0
  for _ in $(seq 1 "$SHOT_TRIES"); do
    sleep 0.4; waited=$((waited+1))
    xcrun simctl io "$UDID" screenshot --type=png "$OUT/$name.png" >/dev/null 2>&1 || continue
    sz=$(stat -f%z "$OUT/$name.png" 2>/dev/null || echo 0)
    [ "$sz" -ge "$SHOT_MIN" ] && break
  done
  if [ "$sz" -lt "$SHOT_MIN" ]; then
    rec 막음 "화면이 안 그려진 채로 사진이 찍히던 것" "화면 크기 검사 — ${name} ${sz}B" \
        "빈 화면이 스토어 심사와 소개 자료로 나가, 심사가 반려되거나 첫 인상이 빈 화면이 됩니다"
    echo "  ⚠️  $name.png ${sz}B — $((waited*4/10))초 기다려도 빈 화면이다."
    echo "      화면이 느리면 SHOT_TRIES 를 올리고, 그래도면 앱이 «떴다» 마커를 쓰게 한다(규칙 3)."
  else
    echo "  ✓ $name.png ($((sz/1024))KB · $((waited*4/10))초 대기)"
  fi
}

echo "찍는 중 → $OUT"
if [ $# -eq 0 ]; then
  shoot "shot"
else
  i=0
  for s in "$@"; do i=$((i+1)); shoot "$(printf '%02d-%s' "$i" "$s")" "$ARG" "$s"; done
fi
xcrun simctl terminate "$UDID" "$BUNDLE" >/dev/null 2>&1 || true

_shot_root="$(python3 -I -c 'import os, sys; print(os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[1]))))' "${BASH_SOURCE[0]}" 2>/dev/null)"
if [ -f "${_shot_root:-/nonexistent}/.nightflight-dev" ]; then SHOT_KEEP_DAYS="${SHOT_KEEP_DAYS:-30}"; else SHOT_KEEP_DAYS="${SHOT_KEEP_DAYS:-0}"; fi
DEVDIR="$HOME/Library/Developer/CoreSimulator/Devices"
if [ "$SHOT_KEEP_DAYS" -gt 0 ] && [ -d "$DEVDIR" ]; then
  NOW=$(date +%s); WIPED=0; FREED=0
  for dir in "$DEVDIR"/*/; do
    [ -d "$dir" ] || continue
    id=$(basename "$dir")
    [ "$id" = "$UDID" ] && continue
    mt=$(stat -f %m "$dir" 2>/dev/null) || continue
    days=$(( (NOW - mt) / 86400 ))
    [ "$days" -lt "$SHOT_KEEP_DAYS" ] && continue
    nm=$(plutil -extract name raw "$dir/device.plist" 2>/dev/null || echo "$id")
    mb=$(du -sm "$dir" 2>/dev/null | cut -f1)
    if xcrun simctl delete "$id" >/dev/null 2>&1; then
      WIPED=$((WIPED+1)); FREED=$((FREED + ${mb:-0}))
      echo "  🧹 ${days}일 안 쓴 기기를 지웠습니다 — ${nm} (${mb}MB)"
    fi
  done
  [ "$WIPED" -gt 0 ] && {
    echo "  🧹 모두 ${WIPED}개 · ${FREED}MB 를 비웠습니다"
    rec 막음 "안 쓰는 시뮬레이터가 디스크를 계속 먹는 일" "${SHOT_KEEP_DAYS}일 넘게 안 쓴 기기 ${WIPED}개 · ${FREED}MB 를 실제로 지웠습니다"
  }
fi

echo "끝. 다 보시고 나면 제가 꺼 두겠습니다."
echo "[모델] 세션 끝에 simctl shutdown all (프로세스 ~170개가 남는다)" >&2
