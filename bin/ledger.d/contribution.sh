LC_ALL=C; export LC_ALL
case "$KIND" in

  기여동의|기여후보|기여|기여목록|기여취소)
    _PICK="$NF_PYDIR/../tools/pick_contribution.py"
    if [ ! -f "$_PICK" ]; then
      echo "  ⛔ 설치가 덜 끝났습니다 — 같이 와야 하는 파일이 빠져 있습니다." >&2
      echo "     설치를 한 번 더 돌리면 됩니다. 기록은 지워지지 않습니다." >&2
      echo "     [모델] 빠진 파일: $_PICK" >&2
      exit 1
    fi
    case "$KIND" in
      기여동의) exec python3 "$_PICK" 동의 ${2+"$2"} ;;
      기여후보) exec python3 "$_PICK" 후보 ;;
      기여)     exec python3 "$_PICK" 담기 "${2:?무엇을 보낼지 일부 글자로}" ;;
      기여목록) exec python3 "$_PICK" 목록 ;;
      기여취소) exec python3 "$_PICK" 취소 "${2:?지울 것의 이름표}" ;;
    esac
    ;;
esac
