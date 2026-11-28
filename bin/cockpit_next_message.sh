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
. "$HERE/python_ok.sh" 2>/dev/null && { nf_python_ok || exit 0; }
IN="$(python3 -I "$HERE/hook_in.py" 2>/dev/null)" || IN=""
_nf_cwd="$(printf '%s' "$IN" | python3 -I "$HERE/cockpit_next_message.py" --폴더 2>/dev/null)"
[ -n "$_nf_cwd" ] && export NIGHTFLIGHT_PROJECT_DIR="$_nf_cwd"
_nf_sid="$(printf '%s' "$IN" | python3 -I "$HERE/cockpit_next_message.py" --대화 2>/dev/null)"
[ -n "$_nf_sid" ] && export NF_SESSION="$_nf_sid"
. "$HERE/project-root.sh" 2>/dev/null || exit 0
nf_registered 2>/dev/null || exit 0
_nf_f="$(nf_next_file)"
NF_PANE_ADDR=""
_nf_pd="${NIGHTFLIGHT_HOME:-$HOME/.nightflight}/cockpit_pending/$(printf '%s' "${NF_SESSION:-}" | tr -cd '[:alnum:]_-' | cut -c1-80)"
_nf_first=""
if [ -n "${NF_SESSION:-}" ] && { [ -e "$_nf_pd" ] || [ -e "$_nf_pd.done" ]; }; then
  _nf_first=1; rm -f "$_nf_pd.done" 2>/dev/null
fi
if [ -z "$_nf_first" ] && [ "${CLAUDE_CODE_ENTRYPOINT:-}" = "claude-desktop" ] && [ -n "${NF_SESSION:-}" ]; then
  _nf_pg="$(python3 -I "$HERE/cockpit_server.py" "$NF_ROOT" --안보인지 2>/dev/null)" && [ -n "$_nf_pg" ] && {
    _nf_pm="$(nf_state_of "$NF_ROOT")/internal/pane_gone"
    _nf_pk="$NF_SESSION	${_nf_pg#*	}"
    if ! grep -qxF "$_nf_pk" "$_nf_pm" 2>/dev/null; then
      mkdir -p "$(dirname "$_nf_pm")" 2>/dev/null
      printf '%s\n' "$_nf_pk" >> "$_nf_pm" 2>/dev/null
      NF_PANE_ADDR="${_nf_pg%%	*}"
    fi
  }
fi
export NF_PANE_ADDR
[ -f "$_nf_f" ] || [ -n "$NF_PANE_ADDR" ] || exit 0
printf '%s' "$_nf_f" | python3 -I "$HERE/cockpit_next_message.py" "$NF_ROOT" "$HERE" 2>/dev/null || true
exit 0
