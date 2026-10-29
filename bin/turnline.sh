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
. "$(dirname "$0")/project-root.sh"
T="$NF_STATE/turns.tsv"
L="$NF_STATE/ledger.tsv"
nf_state_make || exit 0

NOW=$(date +%s)
printf '%s\t%s\n' "$NOW" "$(date +'%F %T')" >> "$T" 2>/dev/null || exit 0

FIRST=$(head -1 "$T" 2>/dev/null | cut -f1)
PREV=$(tail -2 "$T" 2>/dev/null | head -1 | cut -f1)
[ -n "${FIRST:-}" ] || exit 0

human() {
  local s=$1 d h m
  d=$((s/86400)); h=$(((s%86400)/3600)); m=$(((s%3600)/60))
  if [ "$d" -gt 0 ]; then printf '%d일 %d시간째' "$d" "$h"
  elif [ "$h" -gt 0 ]; then printf '%d시간 %d분째' "$h" "$m"
  else printf '%d분째' "$m"; fi
}
OUT="$(human $((NOW - FIRST)))"

if [ -n "${PREV:-}" ] && [ "$PREV" != "$NOW" ] && [ "$PREV" != "$FIRST" ]; then
  GAP=$((NOW - PREV))
  if [ "$GAP" -ge 72000 ]; then OUT="$OUT · $((GAP/86400))일 만에 이어서"
  elif [ "$GAP" -ge 7200 ]; then OUT="$OUT · $((GAP/3600))시간 만에 이어서"
  fi
fi

cnt() { [ -f "$L" ] && awk -F'\t' -v k="$1" '$2==k' "$L" 2>/dev/null | wc -l | tr -d ' ' || echo 0; }
:

if [ -f "$L" ]; then
  WAIT=$(awk -F'\t' -v now="$NOW" '
    $2=="기다림끝" { done[$3]=1; next }
    $2=="기다림"   { what[NR]=$3; day[NR]=$1; max[NR]=$5 }
    END{
      n=0; oldest=""; oldwhat=""; over=0; overwhat=""; overmax=0
      for (i in what) {
        skip=0
        for (k in done) if (index(what[i], k) || index(k, what[i])) skip=1
        if (skip) continue
        n++
        if (oldest=="" || day[i] < oldest) { oldest=day[i]; oldwhat=what[i]; oldmax=max[i] }
      }
      print n "\t" oldest "\t" oldwhat "\t" oldmax
    }' "$L" 2>/dev/null)
  W=$(printf '%s' "$WAIT" | cut -f1); OLD=$(printf '%s' "$WAIT" | cut -f2)
  WW=$(printf '%s' "$WAIT" | cut -f3); WMAX=$(printf '%s' "$WAIT" | cut -f4)
  if [ "${W:-0}" -gt 0 ] && [ -n "$OLD" ]; then
    OD=$(( (NOW - $(date -j -f '%Y-%m-%d' "$OLD" +%s 2>/dev/null || echo "$NOW")) / 86400 ))
    OUT="$OUT · 기다리는 것 $W(가장 오래된 것 ${OD}일째)"
    case "$WMAX" in ''|*[!0-9]*) ;; *)
      [ "$OD" -gt "$WMAX" ] && OUT="$OUT · ⛔ 최대 ${WMAX}일을 넘겼습니다(${WW}) — 문의하실 때입니다" ;;
    esac
  fi
fi

if [ -f "$L" ]; then
  ST=$(awk -F'\t' '$2=="단계"{s=$3} END{print s}' "$L" 2>/dev/null)
  :
fi

if [ -f "$L" ] && [ -n "${GAP:-}" ] && [ "${GAP:-0}" -ge 86400 ]; then
  _STG=$(awk -F'\t' '$2=="단계"{s=$3} END{print s}' "$L" 2>/dev/null)
  case "$_STG" in
    6*|7*|8*|*출시*|*수정*)
      _MARK="$(dirname "$L")/규정-말한달"
      _THIS=$(date +%Y-%m)
      if [ "$(cat "$_MARK" 2>/dev/null)" != "$_THIS" ]; then
        _OLD=$(awk -F'\t' '!/^#/ && NF>3 && $4!=""{if (o=="" || $4<o) o=$4} END{print o}' \
               "$(dirname "$0")/../../nightflight-server/catalog/관문-기준값.tsv" 2>/dev/null)
        if [ -n "${_OLD:-}" ]; then
          _D=$(( (NOW - $(date -j -f '%Y-%m-%d' "$_OLD" +%s 2>/dev/null || echo "$NOW")) / 86400 ))
          OUT="$OUT · 규정을 마지막으로 읽은 것이 ${_D}일 전입니다(바뀌었는지는 모릅니다)"
          printf '%s\n' "$_THIS" > "$_MARK" 2>/dev/null
        fi
      fi ;;
  esac
fi

printf '  ─ %s\n' "$OUT"
