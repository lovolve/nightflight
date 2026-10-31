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
HERE="$(cd "$(dirname "$0")" && pwd)"
_nf_py="$(command -v python3 2>/dev/null || true)"
_nf_py_ok=""
if [ -n "$_nf_py" ]; then
  if [ "$_nf_py" = /usr/bin/python3 ] && [ "$(uname -s 2>/dev/null)" = Darwin ]; then
    _nf_dev="$(xcode-select -p 2>/dev/null || true)"
    [ -n "$_nf_dev" ] && [ -x "$_nf_dev/usr/bin/python3" ] && _nf_py_ok=1
    unset _nf_dev
  else
    "$_nf_py" -I -c 'import json' >/dev/null 2>&1 && _nf_py_ok=1
  fi
fi
if [ -z "$_nf_py_ok" ]; then
  cat >/dev/null 2>&1 || true
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"야간비행: 이 컴퓨터에서 파이썬 3을 찾지 못해 이번 대화에서는 기록 이어받기·진단·조종석·검사·라이선스 키 확인이 돌지 않습니다. 사용자에게 한 번 알리고, 원하시면 맥 개발자 도구를 깔아 드리겠다고(xcode-select --install) 물으십시오."}}'
  exit 0
fi
unset _nf_py _nf_py_ok
IN="$(python3 -I "$HERE/hook_in.py" 2>/dev/null)" || IN="$(cat 2>/dev/null || true)"

. "$HERE/project-root.sh" 2>/dev/null || exit 0
nf_registered || { printf '%s' "$IN" >/dev/null; exit 0; }
_nf_kan="$NF_HOME/이용권.json"
if [ ! -f "$_nf_kan" ] || [ -n "$(find "$_nf_kan" -mmin +60 2>/dev/null)" ]; then
  if nf_dev 2>/dev/null && [ -n "${NF_KAN_ANSWER+x}" ]; then printf '%s\n' "$NF_KAN_ANSWER" > "$_nf_kan" 2>/dev/null
  else
  ( _a="$(bash "$HERE/열쇠.sh" 칸읽기 2>/dev/null)" && [ -n "$_a" ] && printf '%s\n' "$_a" > "$_nf_kan.$$" && mv -f "$_nf_kan.$$" "$_nf_kan" ) >/dev/null 2>&1 &
  fi
fi
unset _nf_kan

if [ -d "$NF_STATE/tools" ]; then
  for _nf_l in "$NF_STATE/tools/"*; do
    [ -L "$_nf_l" ] && [ ! -e "$_nf_l" ] || continue
    _nf_b="$(basename "$_nf_l")"
    if [ -e "$HERE/../tools/$_nf_b" ]; then ln -sfn "$(cd "$HERE/../tools" && pwd -P)/$_nf_b" "$_nf_l" 2>/dev/null
    elif [ -e "$HERE/$_nf_b" ]; then ln -sfn "$HERE/$_nf_b" "$_nf_l" 2>/dev/null
    else rm -f "$_nf_l" 2>/dev/null; fi
  done
  unset _nf_l _nf_b
fi

bash "$HERE/ledger.sh" 조종석준비 >/dev/null 2>&1 || true

if ! { nf_dev 2>/dev/null && [ -n "${NF_PID:-}" ]; }; then NF_PID="$(nf_personid 2>/dev/null | tr -d "[:space:]")"; fi
NF_MPRINT="$(nf_macprint 2>/dev/null | tr -d "[:space:]")"
NF_BID="$(nf_productid 2>/dev/null | tr -d "[:space:]")"
NF_DEV="$(nf_dev 2>/dev/null && printf 1 || printf 0)"
NF_CALL="$(awk -F'\t' '$2=="호칭"{v=$3; s=1} END{if (s) print v}' "$NF_PERSON" 2>/dev/null | tr -d '\000-\037\177')"
printf '%s' "$IN" | NF_STATE="$NF_STATE" HERE="$HERE" NF_PID="$NF_PID" NF_DOORKEY="${NF_DOORKEY:-}" NF_KEYFILE="$NF_HOME/열쇠상태" \
  NF_MPRINT="$NF_MPRINT" NF_BID="$NF_BID" NF_DEV="$NF_DEV" NF_CALL="$NF_CALL" \
  NF_HOME="$NF_HOME" NF_CARRY_URL="${NF_CARRY_URL:-${NF_BRAIN_BASE:-}/rest/v1/rpc/들고오기}" python3 -I "$HERE/session_start.py" 2>/dev/null || true
if [ -f "$NF_HOME/이용권.새로" ]; then
  rm -f "$NF_HOME/이용권.새로"
  if ! { nf_dev 2>/dev/null && [ -n "${NF_KAN_ANSWER+x}" ]; }; then
    ( _a="$(bash "$HERE/열쇠.sh" 칸읽기 2>/dev/null)" && [ -n "$_a" ] && printf '%s\n' "$_a" > "$NF_HOME/이용권.json.$$" && mv -f "$NF_HOME/이용권.json.$$" "$NF_HOME/이용권.json" ) >/dev/null 2>&1 &
  fi
fi
exit 0
