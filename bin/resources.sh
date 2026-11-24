#!/bin/bash
if [ -z "${NF_LC_WAS:-}" ]; then
  for _nf_lcv in "${LC_ALL:-}" "${LC_MESSAGES:-}" "${LANG:-}"; do
    case "$_nf_lcv" in C|POSIX|C.*|"") : ;; *) NF_LC_WAS="$_nf_lcv"; break ;; esac
  done
  unset _nf_lcv
fi
export NF_LC_WAS
LC_ALL=C; export LC_ALL
set -u
AUTO="${1:-}"

FREE=$(df -g / 2>/dev/null | awk 'NR==2{print $4}')
SWAP_USED=$(sysctl -n vm.swapusage 2>/dev/null | awk '{gsub(/M/,"",$6); print int($6)}')
SWAP_TOT=$(sysctl -n vm.swapusage 2>/dev/null | awk '{gsub(/M/,"",$3); print int($3)}')
RAM_MB=$(sysctl -n hw.memsize 2>/dev/null | awk '{print int($1/1048576)}')
BOOTED=$(pgrep -x launchd_sim 2>/dev/null | wc -l | tr -d ' ')
GHOSTS=$(pgrep -f CoreSimulator 2>/dev/null | wc -l | tr -d ' ')
UI=$(pgrep -x Simulator >/dev/null 2>&1 && echo 1 || echo 0)
BUSY=$(pgrep -f 'xcodebuild|xctest|simctl (spawn|launch|install)|GradleWrapperMain|gradlew' >/dev/null 2>&1 && echo 1 || echo 0)

SAY=""
KINDS=""
add() {
  SAY="${SAY}${SAY:+
}  $1"
  KINDS="${KINDS}${KINDS:+,}${2:-기타}"
}

if [ "${BOOTED:-0}" -eq 0 ] && [ "${GHOSTS:-0}" -ge 20 ]; then
  if [ "$AUTO" = "--정리" ]; then
    xcrun simctl shutdown all >/dev/null 2>&1
    if [ "${BUSY:-0}" -eq 0 ]; then
      pkill -f KotlinCompileDaemon >/dev/null 2>&1
      pkill -f GradleDaemon >/dev/null 2>&1
    fi
    add "⭐ 안 쓰는 채로 돌던 것을 정리했습니다. 컴퓨터가 다시 빨라집니다." 정리함
  else
    add "⚠️ 쓰지 않는데 돌고 있는 것이 있습니다 — 정리하면 빨라집니다." 유령
  fi
fi

if [ "${BOOTED:-0}" -ge 1 ] && [ "${UI:-0}" -eq 0 ] && [ "${BUSY:-0}" -eq 1 ] && [ "$AUTO" = "--정리" ]; then
  add "⏸ 지금 빌드나 시험이 돌고 있어 시뮬레이터를 끄지 않았습니다. 끝난 뒤 다시 말씀해 주세요." 빌드중
elif [ "${BOOTED:-0}" -ge 1 ] && [ "${UI:-0}" -eq 0 ] && [ "${BUSY:-0}" -eq 0 ]; then
  if [ "$AUTO" = "--정리" ]; then
    xcrun simctl shutdown all >/dev/null 2>&1
    LEFT="$(pgrep -x launchd_sim 2>/dev/null | grep -c . || :)"
    if [ "${LEFT:-0}" -eq 0 ]; then
      add "⭐ 보이지 않는 채로 돌던 시뮬레이터 ${BOOTED}대를 껐습니다. 메모리가 돌아옵니다." 정리함
    else
      add "⚠️ 시뮬레이터를 끄려 했는데 ${LEFT}대가 남아 있습니다 — 쓰고 있는 것일 수 있습니다." 못끔
    fi
  else
    add "⚠️ 시뮬레이터 화면은 닫혀 있는데 ${BOOTED}대가 계속 돌고 있습니다. 안 쓰시면 「정리해줘」라고 말씀해 주세요." 켜둔것
  fi
fi

[ "${BOOTED:-0}" -ge 2 ] && add "⚠️ 시뮬레이터가 ${BOOTED}대 겹쳐 돌고 있습니다 — 하나만 쓰면 훨씬 빠릅니다." 겹침

if [ -n "${RAM_MB:-}" ] && [ "${RAM_MB:-0}" -gt 0 ] && [ "${SWAP_USED:-0}" -gt 0 ]; then
  PCT=$(( SWAP_USED * 100 / RAM_MB ))
  if [ "$PCT" -ge 50 ]; then
    add "⚠️ 램 $(( RAM_MB / 1024 ))GB 로 모자라 **디스크에서 $(( SWAP_USED / 1024 )).$(( SWAP_USED % 1024 * 10 / 1024 ))GB 를 빌려 쓰는 중**입니다(램의 ${PCT}%). 빌린 것을 다시 꺼낼 때마다 멈칫합니다." 메모리
  fi
fi

if [ -n "${FREE:-}" ] && [ "${FREE:-999}" -lt 25 ]; then
  _nf_cc="${NIGHTFLIGHT_HOME:-$HOME/.nightflight}/resources_clean"; CLEAN=""
  if [ -f "$_nf_cc" ]; then
    _nf_ct=$(cut -d' ' -f1 "$_nf_cc" 2>/dev/null); _nf_cv=$(cut -d' ' -f2 "$_nf_cc" 2>/dev/null)
    case "$_nf_ct" in ''|*[!0-9]*|0[0-9]*) _nf_ct=0 ;; esac
    case "$_nf_cv" in ''|*[!0-9]*|0[0-9]*) _nf_cv="" ;; esac
    [ -n "$_nf_cv" ] && [ $(( $(date +%s) - _nf_ct )) -lt 21600 ] && CLEAN="$_nf_cv"
  fi
  if [ -z "$CLEAN" ]; then
    _nf_dd=$(du -sg ~/Library/Developer/Xcode/DerivedData 2>/dev/null | cut -f1); _nf_sd=$(du -sg ~/Library/Developer/CoreSimulator/Devices 2>/dev/null | cut -f1)
    CLEAN=$(( ${_nf_dd:-0} + ${_nf_sd:-0} ))
    case "${NIGHTFLIGHT_HOME:-$HOME/.nightflight}" in /*) mkdir -p "${NIGHTFLIGHT_HOME:-$HOME/.nightflight}" 2>/dev/null && printf '%s %s\n' "$(date +%s)" "$CLEAN" > "$_nf_cc" 2>/dev/null ;; esac
  fi
  if [ "${CLEAN:-0}" -gt 3 ]; then
    add "⚠️ 디스크가 ${FREE}GB 남았습니다. 그런데 **지울 수 있는 것이 ${CLEAN}GB** 있습니다 — 「정리해줘」라고 말씀해 주세요." 디스크
  else
    add "⚠️ 디스크가 ${FREE}GB 남았습니다. 더 만들려면 자리가 필요합니다." 디스크
  fi
fi

[ -n "$SAY" ] || exit 0
. "$(dirname "$0")/project-root.sh"
[ -z "$NF_STATE_UNSAFE" ] || exit 0
MARK="$NF_STATE/internal/resources-said"; mkdir -p "$NF_STATE/internal" 2>/dev/null
nf_state_make
NOW=$(date +%s)
KEY=$(printf '%s' "$KINDS" | cksum | cut -d' ' -f1)
if [ -f "$MARK" ]; then
  OLD_KEY=$(cut -f1 "$MARK" 2>/dev/null); OLD_AT=$(cut -f2 "$MARK" 2>/dev/null)
  case "$OLD_AT" in ''|*[!0-9]*|0[0-9]*) OLD_AT=0 ;; esac
  if [ "${OLD_KEY:-}" = "$KEY" ] && [ $(( NOW - ${OLD_AT:-0} )) -lt 21600 ]; then
    exit 0
  fi
fi
printf '%s\t%s\n' "$KEY" "$NOW" > "$MARK" 2>/dev/null
printf '%s\n' "$SAY"
exit 0
