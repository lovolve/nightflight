nf_python_ok() {
  local _p _d
  _p="$(command -v python3 2>/dev/null)" || return 1
  [ -n "$_p" ] || return 1
  if [ "$_p" = /usr/bin/python3 ] && [ "$(uname -s 2>/dev/null)" = Darwin ]; then
    _d="$(xcode-select -p 2>/dev/null)" || return 1
    [ -n "$_d" ] && [ -x "$_d/usr/bin/python3" ]
    return
  fi
  "$_p" -I -c 'import json' >/dev/null 2>&1
}
