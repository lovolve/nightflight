LC_ALL=C; export LC_ALL
case "$KIND" in

  바로잡기)
    python3 -I "$NF_PYDIR/바로잡기.py" "$(dirname "$STATE")" "${2:-}" "${3:-}" "${4:-}"
    ;;

esac
