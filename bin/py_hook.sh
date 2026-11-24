#!/bin/bash
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/python_ok.sh" 2>/dev/null || exit 0
nf_python_ok || exit 0
case "${1:-}" in
  ""|*/*|..*) exit 0 ;;
esac
exec python3 "$HERE/$1"
