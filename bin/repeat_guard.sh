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

INPUT="$(python3 -I "$(cd "$(dirname "$0")" && pwd -P)/hook_in.py" 2>/dev/null)" || INPUT="$(cat 2>/dev/null || true)"
eval "$(NF_HOOK_IN="$INPUT" python3 -I - <<'EOPY' 2>/dev/null || true
import json, os, shlex
try: d = json.loads(os.environ.get("NF_HOOK_IN") or "{}")
except Exception: d = {}
if not isinstance(d, dict): d = {}
cwd = str(d.get("cwd") or "")
sid = str(d.get("session_id") or "")
if cwd: print("export NIGHTFLIGHT_PROJECT_DIR=" + shlex.quote(cwd))
if sid: print("export NF_SESSION=" + shlex.quote(sid))
EOPY
)"
. "$(dirname "$0")/project-root.sh"
nf_registered || exit 0

STATE="$NF_STATE/repeat-guard.tsv"
LIMIT="${REPEAT_LIMIT:-8}"
nf_state_make || true

ROOT="$NF_ROOT"
SESSION_KEY="$(printf '%s' "${NF_SESSION:-x}" | tr -cd 'A-Za-z0-9_-' | cut -c1-40)"
MARK="$NF_STATE/.repeat-guard-mark-${SESSION_KEY:-x}"

FILES=$(printf '%s' "$INPUT" | python3 -I -c '
import json,sys
try:
    d = json.load(sys.stdin)
    print((d.get("tool_input") or {}).get("file_path") or "")
except Exception:
    print("")
' 2>/dev/null)
CMD=$(printf '%s' "$INPUT" | python3 -I -c '
import json,sys
try: print(str((json.load(sys.stdin).get("tool_input") or {}).get("command") or ""))
except Exception: print("")
' 2>/dev/null)

if [ -z "$FILES" ]; then
  if [ -f "$MARK" ]; then NEWER=(-newer "$MARK"); else NEWER=(-newermt "-30 seconds"); fi
  FILES=$(find "$ROOT" \
      \( -name .git -o -name node_modules -o -name .build -o -name build \
         -o -name DerivedData -o -name dist -o -name .next -o -name __pycache__ \
         -o -name .claude -o -name .nightflight -o -name Pods -o -name .venv -o -name vendor \) -prune -o \
      -type f "${NEWER[@]}" -print 2>/dev/null | head -200 \
    | NF_CMD="$CMD" python3 -I "$NF_PYDIR/명령읽기.py" 2>/dev/null | head -20)
fi
touch "$MARK" 2>/dev/null
find "$NF_STATE" -maxdepth 1 -name ".repeat-guard-mark-*" -mtime +2 -delete 2>/dev/null
[ -n "$FILES" ] || exit 0

SESSION="${NF_SESSION:-${CLAUDE_CODE_SESSION_ID:-$(date +%Y%m%d)}}"
made() {
  head -20 "$1" 2>/dev/null | grep -qiE "만들어진.{0,4}것|생성된.{0,4}것|자동.{0,2}생성|손으로 ?고치지 ?마|DO NOT EDIT|auto-?generated|@generated" && return 0
  git -C "$(dirname "$1")" check-ignore -q "$1" 2>/dev/null && return 0
  return 1
}

HIT=""; N=0
DOING=""
[ -f "$NF_STATE/plan.tsv" ] && DOING="$(awk -F'\t' '$4=="진행 중"{n++; d=$2" › "$3} END{if(n==1) print d}' "$NF_STATE/plan.tsv" 2>/dev/null)"
while IFS= read -r f; do
  [ -n "$f" ] || continue
  made "$f" && continue
  printf '%s\t%s\t%s\n' "$SESSION" "$f" "$DOING" >> "$STATE"
  c=$(awk -F'\t' -v s="$SESSION" -v x="$f" '$1==s && $2==x' "$STATE" | wc -l | tr -d ' ')
  if [ "$c" -ge "$LIMIT" ] && [ $((c % LIMIT)) -eq 0 ] && [ "$c" -gt "$N" ]; then
    N=$c; HIT="$f"
  fi
done <<EOF
$FILES
EOF
[ -n "$HIT" ] || exit 0

BASE=$(basename "$HIT")

SAID="$NF_STATE/repeat-guard-said.tsv"
FIRST=1
if [ -f "$SAID" ] && awk -F'\t' -v s="$SESSION" -v x="$HIT" \
     '$1==s && $2==x{f=1} END{exit !f}' "$SAID"; then FIRST=0; fi
[ "$FIRST" = 1 ] && printf '%s\t%s\n' "$SESSION" "$HIT" >> "$SAID"

python3 -I "$NF_PYDIR/같은증상셈.py" "$BASE" "$N" "$FIRST"
exit 0
