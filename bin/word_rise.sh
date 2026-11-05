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
IN="$(python3 -I "$HERE/hook_in.py" 2>/dev/null)" || IN="$(cat 2>/dev/null || true)"

_nf_nh="${NIGHTFLIGHT_HOME:-$HOME/.nightflight}"; case "$_nf_nh" in /*) ;; *) _nf_nh="" ;; esac
printf '%s' "$IN" | HERE="$HERE" NF_NOTE_FILE="${_nf_nh:+$_nf_nh/다음알림}" python3 -I "$HERE/낱말듣기.py" 2>/dev/null || true
exit 0
