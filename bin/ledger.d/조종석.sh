LC_ALL=C; export LC_ALL
case "$KIND" in
  화면문구)
    ORIG="${2:?원문 — 기록에 적힌 글자 그대로}"
    awk -F'\t' -v x="$ORIG" '$3==x || ($2=="영향" && index($5,x)){f=1} END{exit !f}' "$STATE" 2>/dev/null \
      || { echo "  ⛔ 기록에 그 원문이 없습니다: 「$ORIG」 — 글자 그대로 붙여 주십시오" >&2; exit 1; }
    if [ -n "$FITEM$FVAL" ]; then feed_need "" 1; feed_save "$ORIG"; echo "  · 최근 기록 칸을 붙였습니다: $FITEM · $FVAL"
    else
      _k=$(awk -F'\t' -v x="$ORIG" '$3==x || ($2=="영향" && index($5,x)){k=$2} END{print k}' "$STATE")
      case "$_k" in 됐다|남은것|표준|시도|영향) screen_need 1 "" "$_k" ;; *) screen_need 0 "" ;; esac
      screen_save "$ORIG"; echo "  · 화면 문구를 붙였습니다: $SCR${SCRK:+ ($SCRK)}"
    fi
    ;;

  조종석)
    if [ -n "${2:-}" ]; then
      printf '%s\n' "$2" > "$BOARD"; echo "  · 조종석 주소를 기억했습니다: $2"
    elif [ -f "$BOARD" ]; then
      echo "  조종석: $(head -1 "$BOARD")"
      board_nudge 단계 || true
    else
      echo "  아직 조종석이 없습니다.  「조종석」에 주소를 한 번 등록하면 됩니다."
    fi
    ;;

  조종석반영)
    if [ ! -f "$(dirname "$STATE")/board/now.json" ]; then
      echo "  ⛔ 먼저 「조종석준비」로 보낼 것을 만드십시오." >&2
      echo "     (조종석준비 없이 「반영됐다」고만 적으면 조종석이 조용히 낡습니다.)" >&2
      exit 1
    fi
    N=$(python3 -I -c 'import json,sys;print(json.load(open(sys.argv[1]))["decisions"])' \
          "$(dirname "$STATE")/board/now.json" 2>/dev/null) || N=""
    if [ -z "$N" ]; then echo "  ⛔ board/now.json 을 읽지 못했습니다 — 조종석준비를 다시 돌리십시오." >&2; exit 1; fi
    printf '%s\t조종석반영\t%s\t\t\n' "$(date +%F)" "$N" >> "$STATE"
    echo "  · 조종석이 결정 ${N}건까지 반영된 것으로 기록했습니다."
    ;;

  조종석지금)
    bash "$NF_PYDIR/ledger.sh" 조종석준비 >/dev/null 2>&1 || true
    _url="$(cat "$BOARD" 2>/dev/null || true)"
    _bd="$(dirname "$STATE")/board"
    if [ -z "$_url" ]; then
      echo "  조종석이 아직 없습니다 — 이번 턴이 끝나면 만들라는 안내가 뜹니다(그때 지금까지 채운 칸이 함께 올라갑니다)."
      exit 0
    fi
    _names="$(for _f in "$_bd"/*.json; do [ -f "$_f" ] && basename "$_f" .json; done | tr '\n' ' ')"
    echo "  [모델] 지금 조종석에 올리십시오 — ① ArtifactData list · url \"$_url\" · collection \"state\" 로 칸마다 version 을 받고"
    echo "  [모델]   ② ArtifactData batch · 같은 url · 칸마다 {op:\"set\", collection:\"state\", doc_id:<칸이름>, file_path:\"$_bd/<칸이름>.json\", if_version:<①의 값 — 없는 칸은 빼고>}"
    echo "  [모델]   칸: $_names"
    echo "  [모델] 올린 뒤: $NF_PYDIR/board_push.sh --올렸다 $(cd "$(dirname "$STATE")/.." && pwd)  — 그러면 턴 끝에 같은 것을 다시 올리라고 하지 않습니다."
    ;;

  조종석준비)
    [ "${2:-}" = "--자세히" ] && export NF_DETAIL=1
    REPO="${CLAUDE_PROJECT_DIR:-$PWD}"
    LASTDONE=$(awk -F'\t' '$2=="됐다"{d=$1} END{print d}' "$STATE" 2>/dev/null)
    if [ -n "$LASTDONE" ] && git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1; then
      BEHIND=$(git -C "$REPO" log --since="$LASTDONE 23:59:59" --oneline 2>/dev/null | wc -l | tr -d ' ')
      if [ "${BEHIND:-0}" -gt 0 ]; then
        echo "  ⚠️ 그 뒤로 $BEHIND 번 고쳤는데 «됐다»가 하나도 없습니다 (마지막 됐다: $LASTDONE)"
        echo "     그 단계가 비어 보이는 것은 «일이 없었다»가 아니라 «기록이 없었다»입니다."
        echo "     남기시려면 무엇을 만들었고 무엇이 그것을 확인했는지 말씀해 주세요."
      fi
    fi
    if [ ! -f "$STATE" ]; then
      echo "  아직 기록이 없습니다 — 보낼 것이 없습니다."
      echo "  (이건 고장이 아닙니다. 첫 단계를 적으면 여기가 채워집니다.)"
      exit 0
    fi
    OUT="$(dirname "$STATE")/board"; mkdir -p "$OUT"
    STATE="$STATE" OUT="$OUT" PERSON="${NF_PERSON:-}" UNVERIFIED_TOKENS="$UNVERIFIED_TOKENS" \
      NF_TRACE="${NF_TRACE:-${NF_STATE:-$NF_HOME}/처방받음.tsv}" \
      NF_KEYLINE="$(nf_keyline 2>/dev/null)" \
      NF_BRAIN_SET="$([ -n "${NF_BRAIN_BASE:-}" ] && [ -n "${NF_DOORKEY:-}" ] && echo 1)" \
      NF_PERSONFILE="${NF_PERSONFILE:-}" \
      TOOLS="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)" python3 -I "$NF_PYDIR/조종석자료.py"
    RC=$?
    if [ "$RC" -ne 0 ]; then
      echo "  ⛔ 조종석에 보낼 것을 만들지 못했습니다 — 계산이 $RC 로 끝났습니다." >&2
      echo "     ⚠️ 이건 «일이 없었다»가 아니라 «계산이 죽었다»입니다. 위 오류를 보십시오." >&2
      echo "     그 사이 조종석은 낡은 값을 그대로 들고 있습니다." >&2
      exit 1
    fi
    echo "  · JSON $(ls "$OUT"/*.json 2>/dev/null | wc -l | tr -d ' ')개 만듦$([ -f "$BOARD" ] && echo " → $(head -1 "$BOARD")") · 올린 뒤 「조종석반영」(통계: --자세히)"
    ;;

  카드)
    WHAT="${2:?무엇을 결정하실 것인가}"
    WHY="${3:?왜 여쭙나 — 「미리 설계된 지점」인지 「반복 감지」인지 밝힌다}"
    LATER="${4:?나중에 정하면 무엇을 다시 만들게 되나 — 시간이 아니라 «다시 만드는 것»으로 적는다}"
    ONLY="${5:?사용자가 «이것만» 정하시면 되는 것 — 제품 언어로 한 줄}"
    MINE="${6:?그 답 뒤에 제가 맡는 것 — 가운뎃점으로 나열, 최대 4개}"

    _LUF="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)/lint_user_facing.py"
    if [ -f "$_LUF" ] && ! python3 "$_LUF" --문구 "$ONLY" 2>&1; then
      echo "     ③번 칸은 «사용자가 정하실 것»입니다. 개발 낱말이 들어가면 그 질문은 아직 여쭐 수 없습니다." >&2
      exit 1
    fi

    _N=$(printf '%s' "$MINE" | awk -F'·' '{print NF}')
    if [ "${_N:-1}" -gt 4 ]; then
      echo "  ⛔ ④번 칸에 ${_N}개를 적었습니다 — 최대 4개입니다." >&2
      echo "     이 칸은 자랑이 아니라 «사용자 답의 범위»를 좁히는 자리입니다." >&2
      echo "     그 결정에서 «바로 따라오는 것»만 적습니다." >&2
      exit 1
    fi
    if printf '%s' "$MINE" | grep -qE '꼼꼼|알아서|완벽|빠짐없이|전부 다|철저'; then
      echo "  ⛔ ④번 칸에 자랑이 들어 있습니다: 「$MINE」" >&2
      echo "     무엇을 하는지만 적습니다 — 어떻게 하는지는 사용자가 보실 일입니다." >&2
      exit 1
    fi

    if printf '%s' "$LATER" | grep -qE '며칠|금방|거의 다|진행률|%|[0-9]+ *(일|주|주일|개월|달|시간|분|초)|하루|이틀|사흘|나흘|일주일'; then
      echo "  ⛔ ⑤번 칸에 시간이 들어 있습니다: 「$LATER」" >&2
      echo "     「며칠」은 틀린 답이 아니라 틀린 질문입니다 — 코드 쓰기는 시간을 거의 안 먹습니다." >&2
      echo "     대신 이렇게 적습니다:" >&2
      echo "       · 무엇을 다시 만드는지  — 「만든 화면을 거의 새로 만듭니다」" >&2
      echo "       · 사용자가 다시 하실 것이 몇 개인지 — 「다시 고르실 것이 3개 생깁니다」" >&2
      exit 1
    fi
    W=${COLUMNS:-$(tput cols 2>/dev/null || echo 76)}
    [ "$W" -gt 88 ] && W=88
    [ "$W" -lt 40 ] && W=40

    if [ -n "${NO_COLOR:-}" ]; then HB=""; HW=""; MM=""; RR=""
    else HB=$'\033[1m'; HW=$'\033[38;5;214m'; MM=$'\033[38;5;245m'; RR=$'\033[0m'; fi

    DONE=""
    [ -f "$STATE" ] && DONE=$(awk -F'\t' '
      $2=="카드"{ buf=""; next }
      $2=="막음"{ buf = buf $3 "\n" }
      END{ printf "%s", buf }' "$STATE" | tail -6)

    printf '%s\t카드\t%s\t%s\t%s\t%s\t%s\t%s\n' "$(date +%F)" "$WHAT" "$WHY" \
      "$(printf '%s' "$DONE" | tr '\n' '\036')" "$LATER" "$ONLY" "$MINE" >> "$STATE"

    WHAT="$WHAT" WHY="$WHY" DONE="$DONE" LATER="$LATER" ONLY="$ONLY" MINE="$MINE" W="$W" \
    HB="$HB" HW="$HW" MM="$MM" RR="$RR" python3 -I "$NF_PYDIR/단계날수.py"
    ;;

  show)
    STAGE="${2:-}"
    echo
    echo "── 기록${STAGE:+ · $STAGE} ──────────────────────────────"
    if [ ! -f "$STATE" ]; then
      echo "   아직 아무것도 없습니다."
      echo "   ⚠️ 이건 「잘 돌고 있다」는 뜻이 아니라 **아직 아무 검사도 안 돌았다**는 뜻입니다."
      echo; exit 0
    fi
    for k in 막음 결정; do
      n=$(awk -F'\t' -v k="$k" '$2==k' "$STATE" | wc -l | tr -d ' ')
      skip=0
      [ "$k" = "막음" ] && skip=$(awk -F'\t' '$2=="막음" && $4==""' "$STATE" | wc -l | tr -d ' ')
      case "$k" in
        막음) label="막았습니다     " ;;
        결정) label="직접 정한 것   " ;;
      esac
      printf "   %s  %s건\n" "$label" "$n"
      [ "${skip:-0}" -gt 0 ] && printf "        ⚠️ 그중 %s건은 근거가 없어 아래에 안 적었습니다 — 어느 검사가 막았는지 모릅니다.\n" "$skip"
      if [ "$n" -gt 0 ]; then
        if [ "$k" = "결정" ]; then
          awk -F'\t' '$2=="결정"{print "        · "$3"\n            근거: "$4"\n            전제: "$5}' "$STATE" | tail -9
        else
          awk -F'\t' -v k="$k" '$2==k && $4!=""{
              print "        · 막았습니다  "$3
              if ($5 != "") print "          안 막았으면  "$5
              print "          (근거: "$4")"
          }' "$STATE" | tail -9
        fi
      fi
    done
    echo
    echo "   ⚠️ 실제로 돌아간 검사만 적혀 있습니다. 0이면 0이라고 씁니다."
    echo
    ;;
esac
