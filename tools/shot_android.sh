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

ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$ROOT"
NAME=$(basename "$ROOT")
OUT="${SHOT_DIR:-/tmp/${NAME}-shots}"
mkdir -p "$OUT"
ARGN="${SHOT_ARG:-screen}"
MIN="${SHOT_MIN:-30000}"

eval "$(python3 -I "$(dirname "${BASH_SOURCE[0]}")/find_dev.py" "$ROOT" --sh 2>/dev/null)"
ADB="${NF_ADB:-$(command -v adb || true)}"
EMU="${NF_EMU:-$(command -v emulator || true)}"
[ -n "$ADB" ] || die "안드로이드 SDK 를 못 찾았습니다 — 본 자리: ${NF_SDK_LOOKED:-없음}. 다른 자리에 있으면 ANDROID_HOME 으로 알려 주십시오. 없으면 Android Studio 를 깔고 한 번 실행하면 받습니다."
[ -n "${NF_JAVA:-}" ] && export JAVA_HOME="${JAVA_HOME:-$NF_JAVA}"

_t(){
  local s=$1; shift
  "$@" & local p=$!
  ( sleep "$s"; kill "$p" 2>/dev/null ) & local w=$!
  local r=0; wait "$p" || r=$?
  kill "$w" 2>/dev/null; wait "$w" 2>/dev/null
  return $r
}

STARTED=0
SERIAL=$("$ADB" devices 2>/dev/null | awk 'NR>1 && $2=="device"{print $1; exit}')
if [ -z "$SERIAL" ]; then
  [ -n "$EMU" ] || die "에뮬레이터 프로그램을 못 찾았습니다(본 SDK: ${NF_SDK:-없음}) — Android Studio 의 SDK Manager 에서 «Android Emulator» 를 받으십시오."
  AVD="${SHOT_AVD:-$("$EMU" -list-avds 2>/dev/null | head -1)}"
  [ -n "$AVD" ] || die "가상 기기가 없습니다 — Android Studio 의 Device Manager 에서 만들거나, 받아 둔 기기 이미지로 avdmanager create avd 를 돌리십시오(받아 둔 이미지: ${NF_SYSIMG:-없음})."
  echo "  가상 기기를 켭니다 — $AVD"
  "$EMU" -avd "$AVD" -no-snapshot-save -no-boot-anim >/dev/null 2>&1 &
  STARTED=1
  _t 90 "$ADB" wait-for-device || die "가상 기기가 90초 안에 안 켜졌습니다"
  n=0
  until [ "$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ]; do
    n=$((n+1)); [ "$n" -gt 90 ] && die "가상 기기가 90초 안에 다 켜지지 않았습니다"
    sleep 1
  done
  SERIAL=$("$ADB" devices | awk 'NR>1 && $2=="device"{print $1; exit}')
fi
A="$ADB -s $SERIAL"
stop_emu(){ [ "$STARTED" = 1 ] && $A emu kill >/dev/null 2>&1 || true; }
trap stop_emu EXIT

MOD="${SHOT_MODULE:-app}"
if [ -f pubspec.yaml ]; then
  [ -n "${NF_FLUTTER:-}" ] || die "이 앱은 Flutter 인데 flutter 를 못 찾았습니다 — 본 자리: $NF_FLUTTER_LOOKED"
  "$NF_FLUTTER" build apk --debug >/dev/null || die "빌드가 실패했습니다"
  APK=build/app/outputs/flutter-apk/app-debug.apk
  _t 30 $A install -r "$APK" >/dev/null || die "설치가 실패했습니다"
  GRADLE_DIR=android
elif [ -x ./gradlew ]; then
  ./gradlew -q ":$MOD:installDebug" || die "빌드나 설치가 실패했습니다"
  GRADLE_DIR=.
elif [ -x android/gradlew ]; then
  (cd android && ./gradlew -q ":$MOD:installDebug") || die "빌드나 설치가 실패했습니다"
  GRADLE_DIR=android
else
  die "gradlew 를 못 찾았습니다 — 안드로이드 프로젝트 맨 위에서 돌리십시오"
fi

PKG="${SHOT_PKG:-}"
if [ -z "$PKG" ]; then
  PKG=$(find "$GRADLE_DIR" -maxdepth 3 \( -name build.gradle -o -name build.gradle.kts \) -not -path '*/node_modules/*' 2>/dev/null \
        | xargs grep -h -E "^[[:space:]]*applicationId[[:space:]=]+[\"'][A-Za-z0-9_.]+[\"']" 2>/dev/null \
        | sed -E "s/.*[\"']([A-Za-z0-9_.]+)[\"'].*/\1/" | head -1)
fi
[ -n "$PKG" ] || die "앱 패키지 이름을 못 읽었습니다 — SHOT_PKG 로 알려 주십시오"
ACT=$($A shell cmd package resolve-activity --brief -c android.intent.category.LAUNCHER "$PKG" 2>/dev/null | tr -d '\r' | tail -1)
case "$ACT" in */*) ;; *) die "$PKG 의 시작 화면을 못 찾았습니다 — 설치가 안 됐을 수 있습니다";; esac

shot(){
  local f="$OUT/$1.png" try
  for try in 1 2; do
    $A shell am force-stop "$PKG" >/dev/null 2>&1 || true
    if [ -n "${2:-}" ]; then _t 30 $A shell am start -W -n "$ACT" --es "$ARGN" "$2" >/dev/null || continue
    else _t 30 $A shell am start -W -n "$ACT" >/dev/null || continue; fi
    $A exec-out screencap -p > "$f" 2>/dev/null || continue
    [ "$(wc -c < "$f" | tr -d ' ')" -ge "$MIN" ] && { echo "  · $1.png"; return 0; }
  done
  echo "  ⚠️ $1 — 두 번 찍었는데 빈 화면에 가깝습니다(앱이 그 화면 이름을 읽는지 보십시오)"
}
if [ $# -eq 0 ]; then shot "now"; else for s in "$@"; do shot "$s" "$s"; done; fi
echo "  사진은 $OUT 에 있습니다."
[ "$STARTED" = 1 ] && echo "끝. 이 도구가 켠 가상 기기는 끕니다." || echo "끝. 원래 켜져 있던 기기는 그대로 둡니다."
