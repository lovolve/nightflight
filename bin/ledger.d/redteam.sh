LC_ALL=C; export LC_ALL
case "$KIND" in

  레드팀)
    ANS="${2:?돌림 또는 넘김}"
    WHEN="${3:?때 — 개발 · 출시 · 결제 · 로그인 · 개인정보 · 서버권한}"
    case "$ANS" in 돌림|넘김) ;; *) echo "  답은 «돌림» 또는 «넘김»입니다." >&2; exit 1 ;; esac
    case "$WHEN" in 개발|출시|결제|로그인|개인정보|서버권한) ;; *) echo "  때는 개발 · 출시 · 결제 · 로그인 · 개인정보 · 서버권한 중 하나입니다." >&2; exit 1 ;; esac
    SUM="$(printf '%s' "${4-}" | tr '\t\r\n' '   ' | cut -c1-400)"
    if [ "$ANS" = "돌림" ] && [ -z "$SUM" ]; then
      echo "  돌렸으면 찾은 것을 한 줄로 적어 주십시오 — 없었으면 «찾은 것 없음»." >&2
      exit 1
    fi
    printf '%s\t레드팀\t%s\t%s\t%s\t\n' "$(date +%F)" "$WHEN" "$ANS" "$SUM" >> "$STATE"
    if [ "$ANS" = "돌림" ]; then echo "  · 레드팀($WHEN): 돌림 — $SUM"; else echo "  · 레드팀($WHEN): 이번에는 건너뜀"; fi
    ;;

esac
