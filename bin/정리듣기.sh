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
_nf_me="${BASH_SOURCE[0]:-$0}"; _nf_i=0
while [ -L "$_nf_me" ] && [ "$_nf_i" -lt 20 ]; do
  _nf_t="$(readlink "$_nf_me" 2>/dev/null)" || break
  case "$_nf_t" in /*) _nf_me="$_nf_t" ;; *) _nf_me="$(cd "$(dirname "$_nf_me")" 2>/dev/null && pwd -P)/$_nf_t" ;; esac
  _nf_i=$((_nf_i + 1))
done
if [ -L "$_nf_me" ]; then NF_PYDIR=""; else NF_PYDIR="$(cd "$(dirname "$_nf_me")" 2>/dev/null && pwd -P)"; fi
unset _nf_me _nf_i _nf_t
HERE="${NF_PYDIR:-$(cd "$(dirname "$0")" && pwd)}"
TOOLNAME="클로드"
while [ $# -gt 0 ]; do
  case "$1" in
    --도구) TOOLNAME="${2:-클로드}"; shift 2 ;;
    *) shift ;;
  esac
done
IN="$(python3 -I "$HERE/hook_in.py" 2>/dev/null)" || IN="$(cat 2>/dev/null || true)"

if [ "$TOOLNAME" = "커서" ]; then
  printf '%s' "$IN" | HERE="$HERE" python3 -I -c '
import json, os, re, subprocess, sys
try:
    prompt = (json.load(sys.stdin) or {}).get("prompt", "") or ""
except Exception:
    prompt = ""
here = os.environ["HERE"]
tools = os.path.join(os.path.dirname(here), "tools")
정리말 = re.search(r"(정리|치워|치우|비워|지워)", prompt)
시뮬 = re.search(r"(시뮬레이터|시뮬|가짜 ?전화기)", prompt)
공간 = re.search(r"(저장공간|저장 ?공간|디스크|용량|빈 ?용량)", prompt)
맨말 = bool(re.fullmatch(r"\s*(컴퓨터\s*)?(좀\s*)?(정리|치워)\s*(해\s*줘|해줘|줘|해|해주세요|해 주세요)?\s*", prompt))
말 = []
if 정리말 and (시뮬 or 맨말):
    try:
        r = subprocess.run(["bash", os.path.join(here, "resources.sh"), "--정리"],
                           capture_output=True, text=True, timeout=30)
        말.append((r.stdout or "").strip() or "정리할 것이 없었습니다.")
    except Exception:
        말.append("정리하지 못했습니다. 잠시 뒤에 다시 말씀해 주십시오.")
if 정리말 and (공간 or 맨말):
    말.append("저장공간은 지우기 전에 무엇을 지울지 보셔야 합니다. 아래 줄을 터미널에 넣어 보시고, "
             "지우실 것이면 끝에 --apply 를 붙여 다시 넣으십시오:  " + os.path.join(tools, "clean_disk.sh"))
if 말:
    print(json.dumps({"continue": False, "user_message": "\n\n".join(말)}, ensure_ascii=False))
' 2>/dev/null || true
  exit 0
fi

printf '%s' "$IN" | HERE="$HERE" python3 -I "$NF_PYDIR/정리말듣기.py" 2>/dev/null || true
exit 0
