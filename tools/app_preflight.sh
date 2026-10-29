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

echo "── 기계 (질문 0개, 자동으로 읽음) ──────────────────"

chip=$(sysctl -n machdep.cpu.brand_string 2>/dev/null)
INTEL=0
echo "$chip" | grep -qi "apple" || INTEL=1
[ "$INTEL" = 0 ] && ok "칩" "$chip" || hm "칩" "$chip — 아래 「운영체제」를 같이 보십시오"

model=$(system_profiler SPHardwareDataType 2>/dev/null | awk -F': ' '/Model Identifier/{print $2}')
ok "모델" "${model:-불명}"

os=$(sw_vers -productVersion)
NEED=""
if [ -f /Applications/Xcode.app/Contents/Info.plist ]; then
  NEED=$(plutil -p /Applications/Xcode.app/Contents/Info.plist 2>/dev/null \
         | awk -F'"' '/LSMinimumSystemVersion/{print $4}')
fi
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
if [ -d /Applications/Xcode.app ]; then
  if   [ "$avail" -ge 30 ]; then ok "디스크 여유" "${avail}GB (Xcode 설치됨)"
  elif [ "$avail" -ge 10 ]; then hm "디스크 여유" "${avail}GB — 빌드 중간산물이 쌓이면 막힌다. 아래 «쌓인 것» 참고"
  else no "디스크 여유" "${avail}GB — 빌드가 곧 실패한다. 먼저 비워야 한다"; fi
else
  if   [ "$avail" -ge 60 ]; then ok "디스크 여유" "${avail}GB"
  elif [ "$avail" -ge 35 ]; then hm "디스크 여유" "${avail}GB — Xcode 설치에 빠듯하다"
  else no "디스크 여유" "${avail}GB — Xcode를 새로 깔 수 없다"; fi
fi

xp=$(xcode-select -p 2>/dev/null)
if [ -n "$xp" ] && [ -d "$xp" ]; then
  xv=$(xcodebuild -version 2>/dev/null | head -1)
  if [ -n "$xv" ]; then ok "Xcode" "$xv"
  else hm "Xcode" "CLT만 있다 ($xp) — 앱 빌드에는 Xcode 본체가 필요"; fi
else no "Xcode" "없다 — App Store에서 설치 (수십 GB)"; fi

if [ -d /Applications/Xcode.app ]; then
  sz=$(du -sg /Applications/Xcode.app 2>/dev/null | cut -f1)
  ok "Xcode 용량" "${sz}GB (실측)"
fi

dd=$(du -sg ~/Library/Developer/Xcode/DerivedData 2>/dev/null | cut -f1)
ar=$(du -sg ~/Library/Developer/Xcode/Archives   2>/dev/null | cut -f1)
sim=$(du -sg ~/Library/Developer/CoreSimulator   2>/dev/null | cut -f1)
tot=$(( ${dd:-0} + ${ar:-0} + ${sim:-0} ))
if [ "$tot" -ge 20 ]; then hm "쌓인 것" "${tot}GB (DerivedData ${dd:-0} / Archives ${ar:-0} / 시뮬레이터 ${sim:-0}) — 지울 수 있다"
else ok "쌓인 것" "${tot}GB (DerivedData ${dd:-0} / Archives ${ar:-0} / 시뮬레이터 ${sim:-0})"; fi

rt=$(xcrun simctl list runtimes 2>/dev/null | grep -c "iOS.*(.*)" )
if [ "${rt:-0}" -gt 0 ]; then ok "시뮬레이터" "iOS 런타임 ${rt}개"
else no "시뮬레이터" "iOS 런타임 없다 — 화면 확인(5단계) 불가"; fi

dev=$(system_profiler SPUSBDataType 2>/dev/null | grep -ci "iPhone")
if [ "${dev:-0}" -gt 0 ]; then ok "iPhone" "USB 연결됨"
else hm "iPhone" "지금은 연결 안 됨 — 5단계에서 필요(이유 코드 ⑥)"; fi

if command -v git >/dev/null; then ok "git" "$(git --version | awk '{print $3}')"
else no "git" "없다"; fi

echo
echo "── 사람만 아는 것 (기계가 못 읽는다) ─────────────────"
pre "Claude 요금제" "API로 확인 불가 → 4단계 사용량 한도와 직결"
pre "Apple 개발자 계정" "키가 있어야 확인 → 개인은 구입 후 24시간 안에 확인 메일(애플 공식) · 조직은 D-U-N-S 발급 최대 5영업일 + 애플에 넘어가기까지 최대 2영업일(애플 공식), 그 뒤 애플 확인 기간은 발표 없음"
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
  echo "  ㉮ **안드로이드 앱** — 맥이 필요 없습니다. 구글에 1회 3만원"
  echo "  ㉯ **웹사이트** — 심사가 없습니다. 가장 빠릅니다"
  echo "  ㉰ **iPhone 도 내고 싶으시면** — 운영체제를 올릴 수 있으면 올리고,"
  echo "       못 올리면 그때는 컴퓨터 이야기가 됩니다. 그건 돈이 드는 일이라 직접 정하실 일입니다"
  echo
  echo "  ⭐ 먼저 ㉮나 ㉯로 하나 내 보고, iPhone 은 뒤에 붙이는 길도 있습니다."
  echo "  ⚠️ 저희가 인텔 맥에서 직접 돌려 본 적은 없습니다 — 위 판정은 이 컴퓨터가"
  echo "     스스로 밝힌 요구 버전으로 셌습니다."
  echo
fi
