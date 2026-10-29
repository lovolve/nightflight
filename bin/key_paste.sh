#!/bin/bash
set -u
[ -n "${HOME:-}" ] || { HOME="$(cd ~ 2>/dev/null && pwd -P)" || HOME="/tmp"; export HOME; }
_nf_p=""; _nf_ifs="$IFS"; IFS=:
for _nf_d in ${PATH:-}; do case "$_nf_d" in /*) _nf_p="${_nf_p:+$_nf_p:}$_nf_d" ;; esac; done
IFS="$_nf_ifs"; PATH="$_nf_p"; unset _nf_p _nf_d _nf_ifs
PATH="${PATH:+$PATH:}/usr/bin:/bin:/usr/sbin"
set +exv 2>/dev/null || true
_nf_lc_set="${LC_ALL+1}"; _nf_lc_old="${LC_ALL-}"
LC_ALL=C
if [ -n "$_nf_lc_set" ]; then _nf_env=(env -u SHELLOPTS -u BASHOPTS "LC_ALL=$_nf_lc_old"); else _nf_env=(env -u SHELLOPTS -u BASHOPTS -u LC_ALL); fi
_nf_claude="${CLAUDE_PROJECT_DIR:+1}"
nf_suppress() {
  local l; IFS= read -r l
  if [ -n "$_nf_claude" ]; then printf '%s\n' "${l%\}\}},\"suppressOriginalPrompt\":true}}"; else printf '%s\n' "$l"; fi
}
_nf_me="${BASH_SOURCE[0]:-$0}"; _nf_i=0
while [ -L "$_nf_me" ] && [ "$_nf_i" -lt 20 ]; do
  _nf_t="$(readlink "$_nf_me" 2>/dev/null)" || break
  case "$_nf_t" in /*) _nf_me="$_nf_t" ;; *) _nf_me="$(cd "$(dirname "$_nf_me")" 2>/dev/null && pwd -P)/$_nf_t" ;; esac
  _nf_i=$((_nf_i + 1))
done
HERE="$(cd "$(dirname "$_nf_me")" 2>/dev/null && pwd -P)"
unset _nf_me _nf_i _nf_t
KEYSH="$HERE/열쇠.sh"
NFL="en"
if . "$HERE/project-root.sh" >/dev/null 2>&1; then
  NFL="$(LC_ALL="$_nf_lc_old" nf_lang 2>/dev/null || echo en)"
  if nf_dev 2>/dev/null && [ -n "${NF_KEY_SH:-}" ]; then KEYSH="$NF_KEY_SH"; fi
fi
HOOKIN="$("${_nf_env[@]}" python3 -I "$HERE/hook_in.py" --끝까지 2>/dev/null)"; _nf_rc=$?
case "$_nf_rc" in
  0) OUT="$(printf '%s' "$HOOKIN" | "${_nf_env[@]}" KEYSH="$KEYSH" NFL="$NFL" NF_BASH="${BASH:-bash}" NF_HOST_CLAUDE="$_nf_claude" python3 -I "$HERE/key_paste.py" 2>/dev/null || true)" ;;
  3|127) HOOKIN="$(cat 2>/dev/null || true)"
         OUT="$(printf '%s' "$HOOKIN" | "${_nf_env[@]}" KEYSH="$KEYSH" NFL="$NFL" NF_BASH="${BASH:-bash}" NF_HOST_CLAUDE="$_nf_claude" python3 -I "$HERE/key_paste.py" 2>/dev/null || true)" ;;
  4) OUT="못읽음" ;;
  *)
     HOOKIN="$(cat 2>/dev/null || true)"
     case "$HOOKIN" in
       "{"*) OUT="$(printf '%s' "$HOOKIN" | "${_nf_env[@]}" KEYSH="$KEYSH" NFL="$NFL" NF_BASH="${BASH:-bash}" NF_HOST_CLAUDE="$_nf_claude" python3 -I "$HERE/key_paste.py" 2>/dev/null || true)" ;;
       *) OUT="못읽음" ;;
     esac ;;
esac
nf_block_unread() {
  if [ "$NFL" = "en" ]; then
    printf '%s\n' '{"decision":"block","reason":"Nightflight could not check this message, so it was not sent to the AI because it may contain your license key. Please try again in a moment.","hookSpecificOutput":{"hookEventName":"UserPromptSubmit"}}' | nf_suppress
  else
    printf '%s\n' '{"decision":"block","reason":"야간비행이 이 메시지를 확인하지 못해서, 라이선스 키가 들어 있을 수 있어 AI에게 보내지 않았습니다. 잠시 뒤에 다시 보내 주십시오.","hookSpecificOutput":{"hookEventName":"UserPromptSubmit"}}' | nf_suppress
  fi
}
case "$OUT" in
  못읽음) nf_block_unread ;;
  PASS) ;;
  "")
    if printf '%s' "$HOOKIN" | grep -qE '[Nn][^A-Za-z0-9]{0,6}[Ff][^A-Za-z0-9]{0,8}[A-HJKMNP-Za-hjkmnp-z2-9]{6}'; then
      if ! "${_nf_env[@]}" python3 -I -c 'import json' >/dev/null 2>&1; then
        if [ "$NFL" = "en" ]; then
          printf '%s\n' '{"decision":"block","reason":"Nightflight needs Python 3 to check your license key, and it isn'"'"'t available on this computer. Install Python 3 (on a Mac, run xcode-select --install in Terminal), then paste the key again. Your message was not sent to the AI.","hookSpecificOutput":{"hookEventName":"UserPromptSubmit"}}' | nf_suppress
        else
          printf '%s\n' '{"decision":"block","reason":"이 컴퓨터에 파이썬 3 이 없어 야간비행이 라이선스 키를 확인하지 못했습니다. 파이썬 3 을 깐 뒤(맥은 터미널에서 xcode-select --install) 다시 붙여 넣어 주십시오. 보내신 말은 AI에게 가지 않았습니다.","hookSpecificOutput":{"hookEventName":"UserPromptSubmit"}}' | nf_suppress
        fi
      else
        nf_block_unread
      fi
    fi ;;
  *) printf '%s\n' "$OUT" ;;
esac
exit 0
