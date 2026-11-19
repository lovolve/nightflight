#!/bin/bash
if [ -z "${NF_LC_WAS:-}" ]; then
  for _nf_lcv in "${LC_ALL:-}" "${LC_MESSAGES:-}" "${LANG:-}"; do
    case "$_nf_lcv" in C|POSIX|C.*|"") : ;; *) NF_LC_WAS="$_nf_lcv"; break ;; esac
  done
  unset _nf_lcv
fi
export NF_LC_WAS
LC_ALL=C; export LC_ALL

WRITE=0
for a in "$@"; do [ "$a" = "--적어" ] && WRITE=1; done
LEDGER="$(cd "$(dirname "${BASH_SOURCE[0]}")/../bin" 2>/dev/null && pwd)/ledger.sh"
_적어(){
  [ "$WRITE" = 1 ] || return 0
  [ -x "$LEDGER" ] || return 0
  "$LEDGER" 단계확인 0 "$2" "$1" "$3" >/dev/null 2>&1 || true
}
ok(){ printf "  ✅ %-22s %s\n" "$1" "$2"; _적어 됨   "$1" "$2"; }
no(){ printf "  ⛔ %-22s %s\n" "$1" "$2"; _적어 안됨 "$1" "$2"; }
hm(){ printf "  ⚠️  %-22s %s\n" "$1" "$2"; _적어 예고 "$1" "$2"; }
pre(){ printf "  · %-22s %s\n" "$1" "$2"; _적어 예고 "$1" "$2"; }

PROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
PLATS=""
_prev=""
for a in "$@"; do
  [ "$_prev" = "--플랫폼" ] && PLATS="$PLATS·$a"
  _prev="$a"
done
if [ -z "$PLATS" ]; then
  for _lg in "$PROOT/.nightflight/ledger.tsv" "$PROOT/.claude/ledger.tsv"; do
    [ -f "$_lg" ] || continue
    PLATS=$(awk -F'\t' '$2=="앱설정" && $3=="플랫폼"{v=$4} END{print v}' "$_lg")
    break
  done
fi
WANT_IOS="?"; WANT_AND="?"
if [ -n "$PLATS" ]; then
  WANT_IOS=0; WANT_AND=0
  case "$PLATS" in *iPhone*) WANT_IOS=1 ;; esac
  case "$PLATS" in *안드로이드*) WANT_AND=1 ;; esac
else
  _has(){ [ -n "$(find "$PROOT" -maxdepth 3 \( "$@" \) -not -path '*/node_modules/*' -not -path '*/.*' -print -quit 2>/dev/null)" ]; }
  _ios=0; _and=0
  _has -name '*.xcodeproj' -o -name 'project.yml' -o -name 'Package.swift' && _ios=1
  _has -name 'build.gradle' -o -name 'build.gradle.kts' -o -name 'AndroidManifest.xml' && _and=1
  if [ "$_ios" = 1 ] || [ "$_and" = 1 ]; then
    WANT_IOS=$_ios; WANT_AND=$_and
    [ -f "$PROOT/pubspec.yaml" ] || [ -f "$PROOT/app.json" ] && { [ "$_ios" = 0 ] && WANT_IOS="?"; [ "$_and" = 0 ] && WANT_AND="?"; }
  fi
fi
need(){
  if [ "$1" = 1 ]; then no "$2" "$3"; else hm "$2" "$3 (그 앱을 만들 때 필요합니다)"; fi
}

echo "── 기계 (질문 0개, 자동으로 읽음) ──────────────────"

chip=$(sysctl -n machdep.cpu.brand_string 2>/dev/null)
INTEL=0
echo "$chip" | grep -qi "apple" || INTEL=1
[ "$INTEL" = 0 ] && ok "칩" "$chip" || hm "칩" "$chip — 아래 「운영체제」를 같이 보십시오"

model=$(system_profiler SPHardwareDataType 2>/dev/null | awk -F': ' '/Model Identifier/{print $2}')
ok "모델" "${model:-불명}"

eval "$(python3 -I "$(dirname "${BASH_SOURCE[0]}")/find_dev.py" "$PROOT" --sh 2>/dev/null)"

os=$(sw_vers -productVersion)
NEED="${NF_XCODE_MINOS:-}"
_num() { printf '%s' "$1" | awk -F. '{printf "%d%03d", $1, $2+0}'; }
if [ -n "$NEED" ]; then
  if [ "$(_num "$os")" -ge "$(_num "$NEED")" ] 2>/dev/null; then
    ok "운영체제" "$os (이 컴퓨터의 개발 도구는 $NEED 이상을 요구합니다 — 맞습니다)"
  else
    no "운영체제" "$os — 이 컴퓨터의 개발 도구는 **$NEED 이상**을 요구합니다"
    echo "     운영체제를 올릴 수 있으면 올리면 됩니다. 못 올리면 아래를 보십시오."
    NEED_ALT=1
  fi
else
  hm "운영체제" "$os (개발 도구가 아직 없어 요구 버전을 못 읽었습니다)"
  [ "$INTEL" = 1 ] && NEED_ALT=1
fi

avail=$(df -g / | awk 'NR==2{print $4}')
if [ -n "${NF_XCODE:-}" ]; then
  if   [ "$avail" -ge 30 ]; then ok "디스크 여유" "${avail}GB (Xcode 설치됨)"
  elif [ "$avail" -ge 10 ]; then hm "디스크 여유" "${avail}GB — 빌드 중간산물이 쌓이면 막힌다. 아래 «쌓인 것» 참고"
  else no "디스크 여유" "${avail}GB — 빌드가 곧 실패한다. 먼저 비워야 한다"; fi
elif [ "$WANT_IOS" = 0 ]; then
  if   [ "$avail" -ge 30 ]; then ok "디스크 여유" "${avail}GB"
  elif [ "$avail" -ge 10 ]; then hm "디스크 여유" "${avail}GB — 에뮬레이터와 빌드 중간 파일이 쌓이면 막힌다"
  else no "디스크 여유" "${avail}GB — 빌드가 곧 실패한다. 먼저 비워야 한다"; fi
else
  if   [ "$avail" -ge 60 ]; then ok "디스크 여유" "${avail}GB"
  elif [ "$avail" -ge 35 ]; then hm "디스크 여유" "${avail}GB — Xcode 설치에 빠듯하다"
  elif [ "$WANT_IOS" = 1 ]; then no "디스크 여유" "${avail}GB — Xcode를 새로 깔 수 없다"
  else hm "디스크 여유" "${avail}GB — iPhone 앱을 만들면 Xcode를 새로 깔 자리가 모자랍니다"; fi
fi

xp=$(xcode-select -p 2>/dev/null)
if [ "$WANT_IOS" = 0 ]; then :
elif [ -n "$xp" ] && [ -d "$xp" ]; then
  xv=$(xcodebuild -version 2>/dev/null | head -1)
  if [ -n "$xv" ]; then ok "Xcode" "$xv"
  else hm "Xcode" "CLT만 있다 ($xp) — iPhone 앱 빌드에는 Xcode 본체가 필요"; fi
else need "$WANT_IOS" "Xcode" "못 찾았습니다(본 자리: ${NF_XCODE_LOOKED:-지금 선택된 개발 도구}) — 없으면 App Store에서 설치 (수십 GB)"; fi

if [ -n "${NF_XCODE:-}" ]; then
  sz=$(du -sg "$NF_XCODE" 2>/dev/null | cut -f1)
  ok "Xcode 용량" "${sz}GB (실측)"
fi

dd=$(du -sg ~/Library/Developer/Xcode/DerivedData 2>/dev/null | cut -f1)
ar=$(du -sg ~/Library/Developer/Xcode/Archives   2>/dev/null | cut -f1)
sim=$(du -sg ~/Library/Developer/CoreSimulator   2>/dev/null | cut -f1)
tot=$(( ${dd:-0} + ${ar:-0} + ${sim:-0} ))
if [ "$tot" -ge 20 ]; then hm "쌓인 것" "${tot}GB (DerivedData ${dd:-0} / Archives ${ar:-0} / 시뮬레이터 ${sim:-0}) — 지울 수 있다"
else ok "쌓인 것" "${tot}GB (DerivedData ${dd:-0} / Archives ${ar:-0} / 시뮬레이터 ${sim:-0})"; fi

if [ "$WANT_IOS" != 0 ]; then
  rt=$(xcrun simctl list runtimes 2>/dev/null | grep -c "iOS.*(.*)" )
  if [ "${rt:-0}" -gt 0 ]; then ok "시뮬레이터" "iOS 런타임 ${rt}개"
  else need "$WANT_IOS" "시뮬레이터" "iOS 런타임 없다 — iPhone 화면 확인(5단계) 불가"; fi

  dev=$(system_profiler SPUSBDataType 2>/dev/null | grep -ci "iPhone")
  if [ "${dev:-0}" -gt 0 ]; then ok "iPhone" "USB 연결됨"
  else hm "iPhone" "지금은 연결 안 됨 — 5단계에서 필요(이유 코드 ⑥)"; fi
fi

if [ "$WANT_AND" != 0 ]; then
  if [ -n "${NF_SDK:-}" ]; then ok "안드로이드 SDK" "있다 — $NF_SDK (가장 높은 판 ${NF_SDK_TOP:-없음} · ${NF_SDK_SRC})"
  else need "$WANT_AND" "안드로이드 SDK" "못 찾았습니다(본 자리: $NF_SDK_LOOKED) — 없으면 Android Studio 를 깔면 첫 실행 때 받습니다"; fi

  if [ -n "${NF_AS:-}" ]; then ok "Android Studio" "있다"
  elif [ -n "${NF_SDK:-}" ]; then ok "Android Studio" "못 찾았지만 명령줄 도구로 만들고 있어 없어도 됩니다"
  else need "$WANT_AND" "Android Studio" "못 찾았습니다(본 자리: $NF_AS_LOOKED) — 없으면 developer.android.com/studio 에서 설치"; fi

  if [ -n "${NF_JAVA:-}" ]; then ok "Java" "있다 — $NF_JAVA (${NF_JAVA_SRC})"
  else need "$WANT_AND" "Java" "못 찾았습니다(본 자리: ${NF_JAVA_LOOKED:-없음}) — 없으면 Android Studio 를 깔면 같이 들어옵니다"; fi

  if [ "${NF_AVD_N:-0}" -gt 0 ]; then ok "에뮬레이터" "가상 기기 ${NF_AVD_N}개"
  elif [ -n "${NF_SYSIMG:-}" ]; then
    need "$WANT_AND" "에뮬레이터" "가상 기기가 $NF_AVD_HOME 에 없습니다 — 받아 둔 기기 이미지(${NF_SYSIMG})로 AI가 만들 수 있습니다(avdmanager create avd)"
  else need "$WANT_AND" "에뮬레이터" "가상 기기가 $NF_AVD_HOME 에 없습니다 — 안드로이드 화면 확인(5단계) 불가. Android Studio 의 Device Manager 에서 만듭니다"; fi

  avgb=$(du -sg "$HOME/.android/avd" 2>/dev/null | cut -f1)
  grgb=$(du -sg "$HOME/.gradle" 2>/dev/null | cut -f1)
  atot=$(( ${avgb:-0} + ${grgb:-0} ))
  if [ "$atot" -ge 20 ]; then hm "쌓인 것(안드로이드)" "${atot}GB (가상 기기 ${avgb:-0} / Gradle ${grgb:-0}) — 지울 수 있다"
  elif [ "$atot" -gt 0 ]; then ok "쌓인 것(안드로이드)" "${atot}GB (가상 기기 ${avgb:-0} / Gradle ${grgb:-0})"; fi
fi

if [ -f "$PROOT/pubspec.yaml" ]; then
  if [ -n "${NF_FLUTTER:-}" ]; then ok "Flutter" "$("$NF_FLUTTER" --version 2>/dev/null | head -1 | awk '{print $2}') — $NF_FLUTTER"
  else no "Flutter" "못 찾았습니다(본 자리: $NF_FLUTTER_LOOKED) — 이 프로젝트는 Flutter 로 만들어져 있습니다"; fi
fi

if command -v git >/dev/null; then ok "git" "$(git --version | awk '{print $3}')"
else no "git" "없다"; fi

echo
echo "── 사람만 아는 것 (기계가 못 읽는다) ─────────────────"
pre "Claude 요금제" "API로 확인 불가 → 4단계 사용량 한도와 직결"
[ "$WANT_IOS" != 0 ] && pre "Apple 개발자 계정" "키가 있어야 확인 → 개인은 구입 후 24시간 안에 확인 메일(애플 공식) · 조직은 D-U-N-S 발급 최대 5영업일 + 애플에 넘어가기까지 최대 2영업일(애플 공식), 그 뒤 애플 확인 기간은 발표 없음"
[ "$WANT_AND" != 0 ] && pre "Google Play 개발자 계정" "등록비 1회 25달러 · 신분증 본인 확인 · 새 개인 계정은 실제 안드로이드 휴대폰 확인(구글 공식) — 확인에 걸리는 날은 구글이 밝히지 않음 · 개인 계정이면 출시 전 테스터 12명 14일 연속"
pre "어디에 팔 건가" "EU 포함? → DSA trader (주소 공개)"
pre "돈을 받을 건가" "Paid Apps 계약(Account Holder만) → 세금 → 은행 순서 강제"
pre "게임인가" "중국 판호 · 한국 GRAC · 일본 재무국 신고"

SCHEME="$(find app -maxdepth 4 -path '*/xcshareddata/xcschemes/*.xcscheme' 2>/dev/null | head -1)"
STOREKIT="$(find app -maxdepth 2 -name '*.storekit' 2>/dev/null | head -1)"
if [ -n "$SCHEME" ] && [ -n "$STOREKIT" ]; then
  if grep -q "StoreKitConfigurationFileReference" "$SCHEME"; then
    echo "  ✅ 결제를 시험하는 설정이 붙어 있습니다"
  else
    echo "  ⛔ 결제를 시험하는 설정이 사라졌습니다 — 설정을 만드는 도구가 덮어썼습니다"
    echo "     제가 다시 붙입니다. 따로 하실 것은 없습니다."
    echo "     [모델] Scheme 의 LaunchAction 에 StoreKitConfigurationFileReference 를 되돌린다" >&2
  fi
fi

if [ "${NEED_ALT:-0}" = 1 ]; then
  echo
  echo "── 이 컴퓨터로도 되는 길 ───────────────────────────"
  echo
  echo "  지금 안 되는 것은 **iPhone 앱** 하나입니다. 나머지는 됩니다."
  echo
  echo "  ㉮ **안드로이드 앱** — 맥이 필요 없습니다. 구글 등록비 1회 25달러(구글 공식 2026-11-19)"
  echo "  ㉯ **웹사이트** — 심사가 없습니다. 가장 빠릅니다"
  echo "  ㉰ **iPhone 도 내고 싶으시면** — 운영체제를 올릴 수 있으면 올리고,"
  echo "       못 올리면 그때는 컴퓨터 이야기가 됩니다. 그건 돈이 드는 일이라 직접 정하실 일입니다"
  echo
  echo "  ⭐ 먼저 ㉮나 ㉯로 하나 내 보고, iPhone 은 뒤에 붙이는 길도 있습니다."
  echo "  ⚠️ 저희가 인텔 맥에서 직접 돌려 본 적은 없습니다 — 위 판정은 이 컴퓨터가"
  echo "     스스로 밝힌 요구 버전으로 셌습니다."
  echo
fi
