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
IFS=$'\t' read -r DIR PCT COST SID <<EOF
$(printf '%s' "$IN" | python3 -I -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: d={}
w=(d.get("workspace") or {}); c=(d.get("context_window") or {}); m=(d.get("cost") or {})
print(str(w.get("project_dir") or w.get("current_dir") or ".").replace("\t", " "),
      round(c.get("used_percentage") or 0),
      round(m.get("total_cost_usd") or 0, 2),
      "".join(ch for ch in str(d.get("session_id") or "none")[:16] if ch.isalnum() or ch in "-_") or "none", sep="\t")
' 2>/dev/null)
EOF
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

UNSHOWN=0
[ -f "$L" ] && UNSHOWN=$(awk -F'\t' '$2=="카드"{c=0; next} $2=="막음"{c++} END{print c+0}' "$L" 2>/dev/null)
[ -n "$UNSHOWN" ] || UNSHOWN=0

STAGE=""
[ -f "$L" ] && STAGE=$(awk -F'\t' '$2=="단계"{v=$3} END{print v}' "$L" 2>/dev/null | tr -d '\000-\037\177' | sed $'s/\xc2[\x80-\x9f]//g; s/\xe2\x80[\xaa-\xae]//g; s/\xe2\x81[\xa6-\xa9]//g')

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
  if [ -n "$STAGE" ]; then LEFT="${M}${STAGE} · 아직 기록 없음${R}"
  else LEFT="${M}야간비행 · 아직 기록 없음${R}"; fi
else
  if [ "$PAINT" = gate ]; then
    LEFT="${HI} 막음 ${BLK} (+$((BLK - B0))) ${R}"
  else
    LEFT="${M}막음 ${BLK}${R}$(d "$BLK" "$B0")"
  fi
  [ "$UNSHOWN" -gt 0 ] && LEFT="${LEFT} ${M}(안 보여드림 ${UNSHOWN})${R}"
  DECPART="${M}결정 ${DEC}${R}$(d "$DEC" "$D0")"
  [ "$PAINT" = broken ] && DECPART="${HIW} 전제 ${BROKEN}건 다시 봐야 함 ${R}"
  if [ "$PAINT" = unlogged ]; then DECPART="${HIW} 커밋 ${UNLOGGED}건이 «됐다» 없이 지나갔어요 ${R}"
  elif [ "$UNLOGGED" -gt 0 ]; then DECPART="${DECPART}  ${M}기록 없는 커밋 ${UNLOGGED}${R}"; fi
  HEAD="${M}야간비행${R}"
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
CTX="이 대화 $(bar "${PCT:-0}") ${PCT:-0}%"
[ "${PCT:-0}" -ge 85 ] && CTX="$CTX — 곧 새로 시작해야 해요"
case "$PAINT" in
  ctx) [ "${PCT:-0}" -ge 85 ] && RIGHT="${HIC} ${CTX} ${R}" || RIGHT="${HIW} ${CTX} ${R}" ;;
  *)   RIGHT="${M}이 대화${R} ${F}$(bar "${PCT:-0}")${R} ${M}${PCT:-0}%${R}" ;;
esac
[ "${COST:-0}" != "0" ] && [ "${COST:-0}" != "0.0" ] && RIGHT="$RIGHT  ${M}\$${COST}${R}"

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
