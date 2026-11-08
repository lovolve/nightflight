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
IN="$(python3 -I "$HERE/hook_in.py" 2>/dev/null)" || IN=""
_nf_cwd="$(printf '%s' "$IN" | python3 -I "$HERE/cockpit_next_message.py" --폴더 2>/dev/null)"
[ -n "$_nf_cwd" ] && export NIGHTFLIGHT_PROJECT_DIR="$_nf_cwd"
. "$HERE/project-root.sh" 2>/dev/null || exit 0
nf_registered 2>/dev/null || exit 0
_nf_f="$(nf_next_file)"
[ -f "$_nf_f" ] || exit 0
printf '%s' "$_nf_f" | python3 -I "$HERE/cockpit_next_message.py" 2>/dev/null || true
exit 0
