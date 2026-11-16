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

IN="$(python3 -I "$(cd "$(dirname "$0")" && pwd -P)/hook_in.py" 2>/dev/null)" || IN="$(cat 2>/dev/null || true)"
IFS=$'\t' read -r DIR PCT COST SID F5 R5 F7 <<EOF
$(printf '%s' "$IN" | python3 -I -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: d={}
w=(d.get("workspace") or {}); c=(d.get("context_window") or {}); m=(d.get("cost") or {}); r=(d.get("rate_limits") or {})
import time
def 한도(이름):
    k=(r.get(이름) or {}); p=k.get("used_percentage"); t=k.get("resets_at")
    남=max(0, int((t-time.time())//60)) if isinstance(t,(int,float)) else -1
    return (round(p) if isinstance(p,(int,float)) else -1), 남
f5,r5=한도("five_hour"); f7,_=한도("seven_day")
print(str(w.get("project_dir") or w.get("current_dir") or ".").replace("\t", " "),
      round(c.get("used_percentage") or 0),
      round(m.get("total_cost_usd") or 0, 2),
      "".join(ch for ch in str(d.get("session_id") or "none")[:16] if ch.isalnum() or ch in "-_") or "none", f5, r5, f7, sep="\t")
' 2>/dev/null)
EOF
printf '%s' "$IN" | python3 -I "$(dirname "$0")/quota_record.py" 2>/dev/null || true
[ -n "${DIR:-}" ] || exit 0

if [ -n "${NO_COLOR:-}" ]; then
  M=""; F=""; B=""; R=""; HI=""; HIW=""; HIC=""
else
  M=$'\033[38;5;245m'; F=$'\033[38;5;238m'; B=$'\033[1m'; R=$'\033[0m'
  HI=$'\033[48;5;29m\033[38;5;231m'
  HIW=$'\033[48;5;130m\033[38;5;231m'
  HIC=$'\033[48;5;124m\033[38;5;231m'
fi

L="$DIR/.nightflight/ledger.tsv"; [ -f "$L" ] || L="$DIR/.claude/ledger.tsv"
ST="$(dirname "$L")"
if [ -d "$DIR/.nightflight" ]; then ST="$DIR/.nightflight"; fi
CACHE_OK=""; grep -qF "야간비행이 더한 줄" "$ST/.gitignore" 2>/dev/null && CACHE_OK=1
n() { [ -f "$L" ] && awk -F'\t' -v k="$1" '$2==k' "$L" 2>/dev/null | wc -l | tr -d ' ' || echo 0; }
BLK=$(n 막음); DEC=$(n 결정)
W_BLOCK="막음"; W_DEC="결정"; W_NONE="아직 기록 없음"; W_CONV="이 대화"; W_SOON="곧 새로 시작해야 해요"; W_5="5시간"; W_7="7일"; W_NAME="야간비행"
W_H="시간 뒤 초기화"; W_M="분 뒤 초기화"
W_UNSHOWN="안 보여드림"; W_BROKEN1="전제"; W_BROKEN2="건 다시 봐야 함"; W_UNLOG1="커밋"; W_UNLOG2="건이 «됐다» 없이 지나갔어요"; W_UNLOG3="기록 없는 커밋"
LANG_UI="$(head -c 2 "${NIGHTFLIGHT_HOME:-$HOME/.nightflight}/language" 2>/dev/null)"
[ -n "$LANG_UI" ] || LANG_UI="$(bash -c '. "$1" >/dev/null 2>&1; nf_lang' _ "$(dirname "$0")/project-root.sh" 2>/dev/null)"
if [ "$LANG_UI" = "en" ]; then
  W_BLOCK="Blocked"; W_DEC="Decisions"; W_NONE="no records yet"; W_CONV="This conversation"; W_SOON="start a new one soon"; W_5="5-hour"; W_7="7-day"; W_NAME="Nightflight"
  W_H="h to reset"; W_M="m to reset"
  W_UNSHOWN="not shown yet"; W_BROKEN1="Premises to recheck:"; W_BROKEN2=""; W_UNLOG1="Commits without a done record:"; W_UNLOG2=""; W_UNLOG3="unrecorded commits"
fi

UNSHOWN=0
[ -f "$L" ] && UNSHOWN=$(awk -F'\t' '$2=="카드"{c=0; next} $2=="막음"{c++} END{print c+0}' "$L" 2>/dev/null)
[ -n "$UNSHOWN" ] || UNSHOWN=0

STAGE=""
[ -f "$L" ] && STAGE=$(awk -F'\t' '$2=="단계"{v=$3} END{print v}' "$L" 2>/dev/null | tr -d '\000-\037\177' | sed $'s/\xc2[\x80-\x9f]//g; s/\xe2\x80[\xaa-\xae]//g; s/\xe2\x81[\xa6-\xa9]//g')
if [ "$LANG_UI" = "en" ]; then
  case "$STAGE" in
    "0. 진단") STAGE="0. Diagnose" ;; "1. 기획") STAGE="1. Plan" ;; "2. 검증") STAGE="2. Validate" ;;
    "3. 설계") STAGE="3. Design" ;; "4. 개발") STAGE="4. Build" ;; "5. 테스트") STAGE="5. Test" ;;
    "6. 출시") STAGE="6. Launch" ;; "7. 수정") STAGE="7. Fix" ;; "8. 출시후"|"8. 출시 후") STAGE="8. After launch" ;;
  esac
fi

BROKEN=0
[ -f "$L" ] && BROKEN=$(awk -F'\t' '
  NR==FNR { if ($2=="되돌림") done[$3]=1; next }
  $2=="전제바뀜" { open=1; for (d in done) if (index(d,$3)) open=0; if (open) k[$3]=1 }
  END { n=0; for (x in k) n++; print n }' "$L" "$L" 2>/dev/null)
[ -n "$BROKEN" ] || BROKEN=0

SEEN="$ST/.ledger-seen-$SID"
if [ -f "$SEEN" ]; then read -r B0 D0 < "$SEEN"; else
  B0=$BLK; D0=$DEC
  [ -n "$CACHE_OK" ] && printf '%s %s\n' "$BLK" "$DEC" 2>/dev/null > "$SEEN"
  find "$(dirname "$SEEN")" -name '.ledger-seen-*' -mtime +2 -delete 2>/dev/null
fi
case "$B0" in ''|*[!0-9]*|0[0-9]*) B0=$BLK ;; esac
case "$D0" in ''|*[!0-9]*|0[0-9]*) D0=$DEC ;; esac
d() { [ "$1" -gt "$2" ] && printf ' %s(+%s)%s' "$B" "$(($1 - $2))" "$R"; }

UNLOGGED=0
LASTDONE=$([ -f "$L" ] && awk -F'\t' '$2=="됐다"{d=$1} END{print d}' "$L" 2>/dev/null)
case "$LASTDONE" in [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) ;; *) LASTDONE="" ;; esac
if [ -n "$LASTDONE" ] && [ -d "$DIR/.git" ]; then
  UC="$ST/.unlogged-$(git -C "$DIR" rev-parse --short HEAD 2>/dev/null)-$LASTDONE"
  if [ -f "$UC" ]; then read -r UNLOGGED < "$UC"; else
    UNLOGGED=$(git -C "$DIR" log --since="$LASTDONE 23:59:59" --oneline 2>/dev/null | wc -l | tr -d ' ')
    [ -n "$CACHE_OK" ] && printf '%s\n' "${UNLOGGED:-0}" 2>/dev/null > "$UC"
    find "$ST" -name '.unlogged-*' -mtime +2 -delete 2>/dev/null
  fi
fi
[ -n "$UNLOGGED" ] || UNLOGGED=0

PAINT=""
if [ "${PCT:-0}" -ge 85 ]; then PAINT=ctx
elif [ "$BROKEN" -gt 0 ]; then PAINT=broken
elif [ $((BLK - B0)) -gt 0 ]; then PAINT=gate
elif [ "$UNLOGGED" -gt 0 ]; then PAINT=unlogged
elif [ "${PCT:-0}" -ge 60 ]; then PAINT=ctx
fi

if [ $((BLK + DEC)) -eq 0 ]; then
  if [ -n "$STAGE" ]; then LEFT="${M}${STAGE} · ${W_NONE}${R}"
  else LEFT="${M}${W_NAME} · ${W_NONE}${R}"; fi
else
  if [ "$PAINT" = gate ]; then
    LEFT="${HI} ${W_BLOCK} ${BLK} (+$((BLK - B0))) ${R}"
  else
    LEFT="${M}${W_BLOCK} ${BLK}${R}$(d "$BLK" "$B0")"
  fi
  [ "$UNSHOWN" -gt 0 ] && LEFT="${LEFT} ${M}(${W_UNSHOWN} ${UNSHOWN})${R}"
  DECPART="${M}${W_DEC} ${DEC}${R}$(d "$DEC" "$D0")"
  [ "$PAINT" = broken ] && DECPART="${HIW} ${W_BROKEN1} ${BROKEN}${W_BROKEN2} ${R}"
  if [ "$PAINT" = unlogged ]; then DECPART="${HIW} ${W_UNLOG1} ${UNLOGGED}${W_UNLOG2} ${R}"
  elif [ "$UNLOGGED" -gt 0 ]; then DECPART="${DECPART}  ${M}${W_UNLOG3} ${UNLOGGED}${R}"; fi
  HEAD="${M}${W_NAME}${R}"
  [ -n "$STAGE" ] && HEAD="${M}${STAGE}${R}"
  LEFT="${HEAD}  ${LEFT}  ${DECPART}"
fi

bar() {
  local p=$1 n=10 i f out=""
  for i in $(seq 1 $n); do
    f=$(( i * 100 / n ))
    if [ "$f" -le "$p" ]; then out="$out█"; else out="$out░"; fi
  done
  printf '%s' "$out"
}
CTX="${W_CONV} $(bar "${PCT:-0}") ${PCT:-0}%"
[ "${PCT:-0}" -ge 85 ] && CTX="$CTX — ${W_SOON}"
case "$PAINT" in
  ctx) [ "${PCT:-0}" -ge 85 ] && RIGHT="${HIC} ${CTX} ${R}" || RIGHT="${HIW} ${CTX} ${R}" ;;
  *)   RIGHT="${M}${W_CONV}${R} ${F}$(bar "${PCT:-0}")${R} ${M}${PCT:-0}%${R}" ;;
esac
if [ "${F5:--1}" -ge 0 ] 2>/dev/null; then
  LIM="${W_5} ${F5}%"
  if [ "${R5:--1}" -ge 0 ] 2>/dev/null; then
    if [ "$R5" -ge 60 ]; then LIM="$LIM · $((R5 / 60))${W_H}"; else LIM="$LIM · ${R5}${W_M}"; fi
  fi
  [ "${F7:--1}" -ge 0 ] 2>/dev/null && LIM="$LIM · ${W_7} ${F7}%"
  RIGHT="$RIGHT  ${M}${LIM}${R}"
fi

plain() { printf '%s' "$1" | sed $'s/\033\\[[0-9;]*m//g'; }
W=${COLUMNS:-$(tput cols 2>/dev/null || echo 0)}
NF_CELLS='import sys, unicodedata as u; s = sys.stdin.buffer.read().decode("utf-8", "replace").rstrip("\n"); print(sum(0 if u.combining(c) else 2 if u.east_asian_width(c) in "WF" else 1 for c in s))'
LW=$(plain "$LEFT" | python3 -I -c "$NF_CELLS" 2>/dev/null || plain "$LEFT" | wc -m | tr -d ' ')
RW=$(plain "$RIGHT" | python3 -I -c "$NF_CELLS" 2>/dev/null || plain "$RIGHT" | wc -m | tr -d ' ')
GAP=$(( W - LW - RW - 2 ))
if [ "$W" -gt 0 ] && [ "$GAP" -gt 2 ]; then
  printf '%s%*s%s\n' "$LEFT" "$GAP" "" "$RIGHT"
else
  printf '%s   %s\n' "$LEFT" "$RIGHT"
fi
