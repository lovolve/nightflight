LC_ALL=C; export LC_ALL
case "$KIND" in

  결정)
    LINE="${2:?무엇을 정했나}"
    WHY="${3:?근거 — 사용자 말씀을 그대로 인용한다(인용이 없으면 그건 내 판단이다)}"
    PREMISE="${4:?전제가 필요하다 — 「이것이 바뀌면 이 결정을 다시 본다」를 한 줄로}"
    BOUND="${6:?출시하면 무엇에 묶이나 — 돈|시간|법|못되돌림|없음 중 하나로 시작해서 한 줄. 예: \"돈: 저장소가 사용자 수만큼 계속 는다\"}"
    case "$BOUND" in
      돈*|시간*|법*|못되돌림*|없음*) ;;
      *) echo "  ⛔ 묶임은 «돈·시간·법·못되돌림·없음» 중 하나로 시작해야 합니다: $BOUND" >&2; exit 1 ;;
    esac
    feed_need "$LINE" 1 결정
    printf '%s\t결정\t%s\t%s\t%s\t%s\t%s\n' "$(date +%F)" "$LINE" "$WHY" "$PREMISE" "${5:-}" "$BOUND" >> "$STATE"
    feed_save "$LINE"
    echo "  · 기록에 남김 [결정] $LINE"
    echo "      전제: $PREMISE"
    _BA="$NF_PYDIR/../tools/binding_ahead.py"
    if [ -f "$_BA" ]; then
      _MISS=$(python3 "$_BA" --결정 "$LINE" --빠진것 "$BOUND" 2>/dev/null) || _MISS=""
      [ -n "$_MISS" ] && printf '%s\n' "$_MISS"
    fi
    _AT="$NF_PYDIR/../tools/attempts.py"
    if [ -f "$_AT" ] && [ -n "${5:-}" ]; then
      _BLK=$(python3 "$_AT" --막힌길 "${5}" 2>/dev/null) || _BLK=""
      if [ -n "$_BLK" ]; then
        echo "      ──"
        printf '%s\n' "$_BLK"
      fi
    fi
    board_nudge 결정
    ;;

  결정목록)
    echo
    echo "── 지금까지의 결정과 «그 전제» ───────────────────"
    if [ ! -f "$STATE" ] || [ "$(awk -F'\t' '$2=="결정"' "$STATE" | wc -l | tr -d ' ')" -eq 0 ]; then
      echo "   아직 없습니다."
    else
      awk -F'\t' '$2=="결정"{n++; print "   "n". ["$1"] "$3; print "        근거: "$4; print "        전제: "$5"  ← 이것이 바뀌면 다시 본다"}' "$STATE"
    fi
    echo
    echo "   ⚠️ 이 목록은 **처음에 정해진 것이 아니라 늘어난다.**"
    echo "      만들다 보면 정할 것이 «생기고», 정했던 것을 «되돌릴» 일도 생깁니다."
    echo
    ;;

  되돌림)
    KEY="${2:?되돌릴 결정의 일부 글자}"
    echo
    echo "── 되돌리기 ─────────────────────────────────────"
    if [ ! -f "$STATE" ]; then echo "   기록이 비어 있습니다."; exit 0; fi
    HIT=$(awk -F'\t' -v k="$KEY" '$2=="결정" && index($3,k){print NR"\t"$1"\t"$3"\t"$5; exit}' "$STATE")
    [ -n "$HIT" ] || { echo "   「$KEY」이 들어간 결정을 못 찾았습니다."; exit 0; }
    RN=$(echo "$HIT" | cut -f1); RD=$(echo "$HIT" | cut -f2)
    echo "   되돌릴 결정: $(echo "$HIT" | cut -f3)   [$RD]"
    echo "   그때의 전제: $(echo "$HIT" | cut -f4)"
    echo
    echo "   그 뒤에 쌓인 것 (이 중 무엇이 이 결정 «위에» 서 있는지는 사람이 가른다):"
    awk -F'\t' -v n="$RN" 'NR>n{print "     · ["$2"] "$3}' "$STATE" | tail -12
    [ "$(awk -F'\t' -v n="$RN" 'NR>n' "$STATE" | wc -l | tr -d ' ')" -eq 0 ] && echo "     (없습니다 — 되돌리기가 싸다)"
    echo
    echo "   ⛔ **다 버리지 않는다.** 셋으로 가릅니다:"
    echo "      ① 이 결정 때문에 생긴 것        → 버린다"
    echo "      ② 이 결정과 무관하게 옳았던 것  → **남긴다**"
    echo "      ③ 판단이 안 서는 것            → 사용자에게 묻는다"
    echo "   (어느 앱이 배경 8번을 되돌릴 때 «지운 것 / 되돌린 것 / **남긴 것**»을"
    echo "    손으로 갈랐다. 남긴 것이 있었다 — 버튼 기준선 통일은 배경과 무관하게 옳았다)"
    echo
    RP=$(echo "$HIT" | cut -f4)
    printf '%s\t되돌림\t%s\t%s에 정했던 것\t%s\n' "$(date +%F)" "$(echo "$HIT" | cut -f3)" "$RD" "$RP" >> "$STATE"
    echo "   · 기록에 남겼습니다 (틀린 전제: $RP)"
    echo
    ;;

  틀린전제)
    [ -f "$STATE" ] || { echo "   아직 되돌린 것이 없습니다."; exit 0; }
    N=$(awk -F'\t' '$2=="되돌림"' "$STATE" | wc -l | tr -d ' ')
    [ "$N" -eq 0 ] && { echo "   아직 되돌린 것이 없습니다. (0 은 0 이라고 씁니다)"; exit 0; }
    echo
    echo "── 되돌린 $N 건과, 그때 틀렸던 전제 ──────────────"
    echo
    awk -F'\t' '$2=="되돌림"{print "   · " $3; print "       틀렸던 전제: " $5; print "       " $4 " \xe2\x86\x92 " $1 " 되돌림"; print ""}' "$STATE"
    ;;

  전제점검)
    [ -f "$STATE" ] || { echo "   아직 결정이 없습니다."; exit 0; }
    N=$(awk -F'\t' '$2=="결정"' "$STATE" | wc -l | tr -d ' ')
    [ "$N" -eq 0 ] && { echo "   아직 결정이 없습니다."; exit 0; }
    echo
    echo "── 이 전제들, 아직 맞나요? ───────────────────────"
    echo
    awk -F'\t' '
      NR==FNR { if ($2=="전제바뀜") broken[$3]=$5
                if ($2=="전제해소") { for (bk in broken) if (index(bk,$3) || index($3,bk)) delete broken[bk] }
                if ($2=="되돌림")   undone[$3]=1
                next }
      $2=="결정"{
        for (k in undone) if (index($3, k) || index(k, $3)) { u++; next }
        n++
        mark = ""
        for (k in broken) if (index($3, k)) mark = "  ⛔ 깨졌다고 표시됨: " broken[k]
        print "   " n ". " $3
        print "        전제: " $5 mark
        print "        정한 날: " $1
        print ""
      }
      END { if (u) printf "   (되돌린 결정 %d건은 빼고 보였습니다 — 「되돌린 것들을 보여줘」라고 말씀하시면 보여드립니다)\n\n", u }
      ' "$STATE" "$STATE"
    echo "   ⚠️ **결정이 틀린 게 아니라 전제가 틀리는 일이 훨씬 많습니다.**"
    echo "      바뀐 것이 있으면 저에게 말씀해 주세요 — 어느 결정의 무엇이 바뀌었는지만"
    echo "      알려 주시면 기록하고, 다시 볼 것까지 만들어 두겠습니다."
    echo
    ;;

  전제바뀜)
    KEY="${2:?어느 결정인가 — 일부 글자}"
    WHAT="${3:?무엇이 바뀌었나}"
    [ -f "$STATE" ] && awk -F'\t' -v k="$KEY" '$2=="결정" && index($3,k){f=1} END{exit !f}' "$STATE" \
      || { echo "  「$KEY」이 들어간 결정을 못 찾았습니다."; exit 0; }
    NEXT="${4:?다시 볼 것 — 이 전제가 깨져서 무엇을 다시 보나. 정말 없으면 그대로: 없음}"
    printf '%s\t전제바뀜\t%s\t\t%s\t%s\n' "$(date +%F)" "$KEY" "$WHAT" "$NEXT" >> "$STATE"
    echo "  · 전제가 깨졌다고 표시했습니다: $KEY"
    echo "    바뀐 것: $WHAT"
    if [ "$NEXT" = "없음" ]; then
      echo "    ⚠️ 다시 볼 것 없음 — 남은것을 만들지 않았습니다."
    else
      ST=$(awk -F'\t' -v k="$KEY" '$2=="단계"{v=$3} $2=="결정" && index($3,k){out=v} END{print out}' "$STATE" 2>/dev/null)
      [ -z "$ST" ] && ST=$(awk -F'\t' '$2=="단계"{v=$3} END{print v}' "$STATE" 2>/dev/null)
      printf '%s\t남은것\t%s\t%s\t%s\t\n' "$(date +%F)" "$NEXT" "$ST" "$KEY" >> "$STATE"
      echo "    · 남은 것이 생겼습니다 [${ST:-단계 없음}] $NEXT"
      echo "      ↳ 그 결정이 있던 단계입니다. 다른 단계에서 보실 것이면 말씀해 주세요."
    fi
    echo "    → 되돌리실지 보시려면 「$KEY — 되돌릴까」라고 말씀해 주세요."
    ;;

  전제해소)
    KEY="${2:?어느 결정인가 — 일부 글자}"
    HOW="${3:?어떻게 해소됐나 — 무엇을 바꿔서 전제가 다시 섰나}"
    [ -f "$STATE" ] && awk -F'\t' -v k="$KEY" '$2=="전제바뀜" && index($3,k){f=1} END{exit !f}' "$STATE" \
      || { echo "  「$KEY」이 들어간 «전제바뀜»을 못 찾았습니다." >&2
           echo "     결정 자체를 접으시려면 「$KEY — 접는다」고 말씀해 주세요." >&2; exit 1; }
    printf '%s\t전제해소\t%s\t%s\t\t\t\n' "$(date +%F)" "$KEY" "$HOW" >> "$STATE"
    echo "  · 전제가 다시 섰습니다: $KEY"
    echo "    어떻게: $HOW"
    ;;

  묶임)
    _BA="$NF_PYDIR/../tools/binding_ahead.py"
    if [ ! -f "$_BA" ]; then
      echo "  ⛔ 설치가 덜 끝났습니다 — 같이 와야 하는 파일이 빠져 있습니다." >&2
      echo "     설치를 한 번 더 돌리면 됩니다. 기록은 지워지지 않습니다." >&2
      echo "     [모델] 빠진 파일: $_BA" >&2
      exit 1
    fi
    if [ -n "${2:-}" ]; then exec python3 "$_BA" --결정 "$2"; else exec python3 "$_BA"; fi
    ;;
esac
