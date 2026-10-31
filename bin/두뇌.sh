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

HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/project-root.sh" 2>/dev/null || NF_HOME="${NIGHTFLIGHT_HOME:-$HOME/.nightflight}"

BRAIN="${NF_BRAIN_URL:-$NF_BRAIN_BASE/functions/v1/cheobang}"
DOORKEY="$NF_DOORKEY"

STAGE="${1:-}"
KIND="${2:-}"
LISTONLY=""
if [ "$KIND" = "--목록" ]; then LISTONLY=1; KIND="목록"; fi
if ! [[ "$STAGE" =~ ^[0-8]$ ]] || [ -z "$KIND" ]; then
  echo "쓰는 법: 두뇌.sh <단계 0~8> <갈래>" >&2
  exit 2
fi

PERSONID="$(nf_personid | tr -d '[:space:]')"
MACPRINT="$(nf_macprint 2>/dev/null | tr -d '[:space:]')"
BUNDLEID="$(nf_productid 2>/dev/null | tr -d '[:space:]')"

BODY="$(NF_B_PID="$PERSONID" NF_B_STAGE="$STAGE" NF_B_KIND="$KIND" NF_B_MAC="$MACPRINT" NF_B_BUNDLE="$BUNDLEID" python3 -I -c 'import json,os; e=os.environ; print(json.dumps({"사람id":e["NF_B_PID"],"어느단계":int(e["NF_B_STAGE"]),"무엇을물었나":e["NF_B_KIND"][:40],"맥지문":e["NF_B_MAC"],"번들id":e["NF_B_BUNDLE"]}, ensure_ascii=False))')"

if nf_dev 2>/dev/null && [ -n "${NF_TRACE:-}" ]; then :; else NF_TRACE="${NF_STATE:-$NF_HOME}/처방받음.tsv"; fi
export NF_TRACE NF_STAGE_ARG="$STAGE" NF_KIND_ARG="$KIND"
trace() {
  mkdir -p "$(dirname "$NF_TRACE")" 2>/dev/null
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$(date '+%Y-%m-%d %H:%M')" "$STAGE" "$KIND" "$1" "${2:-}" "${3:-}" \
    >> "$NF_TRACE" 2>/dev/null || true
}

KEYLINE_DEFAULT="$(nf_keyline)"
KEYLINE_EXPIRED="$(nf_keyline 만료)"
NF_LANG_NOW="$(nf_lang)"
export KEYLINE_DEFAULT KEYLINE_EXPIRED NF_LANG_NOW

ANSWER="$(nf_post "$BRAIN" "$BODY" -H "Authorization: Bearer $DOORKEY" 2>/dev/null)" || ANSWER=""

if [ -n "$LISTONLY" ]; then
  [ -n "$ANSWER" ] || { echo "  (이 단계의 안내 목록을 서버에서 못 받았습니다 — 아는 것만으로 진행합니다)"; exit 0; }
  ANSWER="$ANSWER" python3 -I -c 'import json,os
try: d=json.loads(os.environ["ANSWER"])
except Exception: d={}
g=d.get("이_단계에_있는_갈래") or []
print(" · ".join(g) if g else "")'
  exit 0
fi

if [ -z "$ANSWER" ]; then
  trace "못받음"
  echo "야간비행에서 못 받았습니다. 이 단계는 아는 것만으로 진행하고, 받지 못했다고 적어 둡니다."
  exit 0
fi

printf '%s' "$ANSWER" | python3 -I "$NF_PYDIR/두뇌표만들기.py" -
