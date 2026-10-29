LC_ALL=C; export LC_ALL
case "$KIND" in

  피함|대신)
    echo "  ⛔ [$KIND] 은 없앴습니다 — 손으로만 적히던 칸이라 기록이 광고가 되는 자리였습니다." >&2
    echo "     실제로 막힌 것은 '막음' 으로 적고, '대신' 은 카드가 막음 줄에서 스스로 뽑습니다." >&2
    exit 1
    ;;

  막음)
    LINE="${2:?제품 언어로 한 줄이 필요하다}"
    WHY="${3:?근거가 필요하다 — 실제로 돌아간 검사만 적는다}"
    IF_NOT="${4:?안 막았으면 어떻게 될 뻔했나 — 숫자가 아니라 «일어날 일»을 한 줄로}"
    if [ -f "$STATE" ] && awk -F'\t' -v d="$(date +%F)" -v k="$KIND" -v l="$LINE" \
         '$1==d && $2==k && $3==l{found=1} END{exit !found}' "$STATE"; then
      exit 0
    fi
    feed_need "$LINE" 0
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$(date +%F)" "$KIND" "$LINE" "$WHY" "$IF_NOT" "${5:-}" >> "$STATE"
    feed_save "$LINE"
    echo "  · 기록에 남김 [$KIND] $LINE"
    ;;

  됐다)
    LINE="${2:?무엇이 됐나 — 제품 언어로 한 줄}"
    HOW="${3:?무엇이 이걸 확인했나. 확인 안 했으면 그대로: 안 함 / 눈으로 안 봄 / 빌드만 통과}"
    case "$LINE" in
      *"적는 칸"*|*"칸을 만들"*|*"검사를 만들"*|*"시험을 만들"*|*"스크립트"*|*"리팩"*|*"파싱"*)
        echo "  ⛔ 부품 이름으로 적혀 있습니다: 「$LINE」" >&2
        echo "     조종석이 이 글을 **그대로 사용자에게 보여 줍니다.**" >&2
        echo "     ⭐ «사용자가 겪는 일»로 적으십시오." >&2
        echo "        전: 표준 방식을 적는 칸" >&2
        echo "        후: 어제 정한 방식을 적어 두고 새 창에서도 그대로 씁니다" >&2
        echo "     ⚠️ 사용자에게 보이는 것이 정말 없으면 그렇게 적으십시오:" >&2
        echo "        「사용자에게 보이는 변화는 없습니다 — <무엇을 했나>」" >&2
        exit 1 ;;
    esac
    screen_need 1 "$LINE" 됐다
    _PLT="$NF_STATE/plan.tsv"; SUBS=""
    if [ -s "$_PLT" ] && [ ${#FSUB[@]} -eq 0 ]; then
      echo "  ⛔ 어느 세부기능의 일인지가 없습니다 — 조종석의 세부기능 상자와 이 기록을 맞대 볼 수 없습니다." >&2
      echo "     [모델] --세부 \"<기능> › <세부기능>\" 를 붙이십시오(여럿이면 --세부 를 여러 번)." >&2
      echo "     [모델] 세부기능의 일이 아니면: --세부 없음" >&2
      exit 1
    fi
    for _x in ${FSUB[@]+"${FSUB[@]}"}; do
      [ "$_x" = "없음" ] && continue
      _f="${_x%% › *}"; _z="${_x#* › }"
      if [ "$_f" = "$_x" ] || ! awk -F'\t' -v f="$_f" -v z="$_z" '$2==f && $3==z{h=1} END{exit !h}' "$_PLT" 2>/dev/null; then
        echo "  ⛔ 설계표에 「$_x」 자리가 없습니다 — 「기능 › 세부기능」 꼴로, 설계표에 있는 이름 그대로 적으십시오." >&2
        echo "     [모델] 설계표에 있는 이름은 같은 도구의 「설계표」로 보십시오" >&2
        exit 1
      fi
      SUBS="${SUBS:+$SUBS · }$_x"
    done
    ST=$(awk -F'\t' '$2=="단계"{v=$3} END{print v}' "$STATE" 2>/dev/null)
    printf '%s\t됐다\t%s\t%s\t%s\t%s\t%s\n' "$(date +%F)" "$LINE" "$HOW" "$ST" "${4:-}" "$SUBS" >> "$STATE"
    screen_save "$LINE"
    echo "  · 기록에 남김 [됐다] $LINE"
    if unverified "$HOW"; then
      echo "    ⚠️ 확인 안 됨 — 「$HOW」. 조종석에 그대로 그렇게 보입니다."
    else
      echo "    ✅ 확인: $HOW"
    fi
    ;;

  못함)
    WHAT="${2:?무슨 검사가 못 돌았나 — 제품 언어로}"
    LACK="${3:?무엇이 없어서}"
    TODO="${4:?사용자가 하실 일 — 한 줄로, 개발 용어 없이}"
    ST=$(awk -F'\t' '$2=="단계"{v=$3} END{print v}' "$STATE" 2>/dev/null)
    if [ -f "$STATE" ] && awk -F'\t' -v d="$(date +%F)" -v w="$WHAT" \
         '$1==d && $2=="못함" && $3==w{f=1} END{exit !f}' "$STATE"; then exit 0; fi
    printf '%s\t못함\t%s\t%s\t%s\n' "$(date +%F)" "$WHAT" "$LACK" "$TODO" >> "$STATE"
    echo "  ⚠️ 못함 적음 — $WHAT" >&2
    ;;

  이어받기)
    if [ ! -f "${NF_PERSON:-/nonexistent}" ]; then
      echo "  이어받을 것이 없습니다 — 이 컴퓨터에서 처음 쓰십니다."
      echo "  (이건 고장이 아닙니다. 「앱설정묻기」부터 하면 됩니다.)"
      exit 0
    fi
    echo
    echo "── 지난 앱에서 이미 말씀해 주신 것 ───────────────"
    echo
    PERSON="$NF_PERSON" python3 -I "$NF_PYDIR/사람자리.py"
    ;;

  시도)
    WHAT="${2:?무엇을 해 봤나 — 한 줄로}"
    WHY="${3:?어떻게 됐나 — 안 된 이유를 한 줄로}"
    VERDICT="${4:?판정 — \"막혔다: <무엇이 막나>\" 또는 \"못했다: <무엇이 바뀌면 다시 가나>\"}"
    case "$VERDICT" in
      막혔다:*|못했다:*) ;;
      막혔다|못했다)
        echo "  ⛔ 뒤에 설명이 필요합니다." >&2
        echo "     막혔다 → 「막혔다: 무엇이 막나」 (도구·플랫폼·법)" >&2
        echo "     못했다 → 「못했다: 무엇이 바뀌면 다시 가나」" >&2
        exit 1 ;;
      *) echo "  ⛔ 판정은 «막혔다» 또는 «못했다» 로 시작해야 합니다: $VERDICT" >&2
         echo "     ⭐ 이 둘을 가르지 않으면 다음에 «다시 가도 되는지»를 알 수 없습니다." >&2
         exit 1 ;;
    esac
    screen_need 1 "$WHAT" 시도
    printf '%s\t시도\t%s\t%s\t%s\t%s\t\n' "$(date +%F)" "$WHAT" "$WHY" "$VERDICT" "${5:-}" >> "$STATE"
    screen_save "$WHAT"
    echo "  · 기록에 남김 [시도] $WHAT"
    echo "      안 된 이유: $WHY"
    case "$VERDICT" in
      막혔다:*) echo "      ⛔ **다시 가지 않습니다** — ${VERDICT#막혔다:}" ;;
      못했다:*) echo "      ⭐ 이것이 바뀌면 다시 갑니다 — ${VERDICT#못했다:}" ;;
    esac
    board_nudge 시도
    ;;

  시도목록)
    echo
    echo "── 해 봤는데 안 된 것 ───────────────────────────"
    echo
    TOOLS="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)" python3 -I - <<'PYEOF'
import os, sys
sys.path.insert(0, os.environ.get("TOOLS", ""))
import attempts
for line in attempts.사람말(attempts.compute()):
    print(line)
PYEOF
    echo
    echo "  ⚠️ 저희가 적어 둔 것만 보입니다 — 「이것 말고는 다 된다」가 아닙니다."
    echo
    ;;

  하는중)
    LINE="${2:?지금 무엇을 하고 있나 — 동사로 한 줄. 예: 「적립 버튼이 두 번 눌리는 것을 고치는 중」}"
    LAST=$(awk -F'\t' '$2=="하는중"{v=$3} END{print v}' "$STATE" 2>/dev/null)
    if [ "$LAST" = "$LINE" ]; then
      echo "  · 같은 것을 하고 계십니다 — 또 적지 않습니다."
      exit 0
    fi
    screen_need 0 "$LINE"
    printf '%s\t하는중\t%s\t%s\t\t\n' "$(date '+%Y-%m-%d %H:%M')" "$LINE" "${3:-}" >> "$STATE"
    screen_save "$LINE"
    echo "  · 지금 하는 것으로 적었습니다: $LINE"
    ;;

  다음)
    LINE="${2:?사용자가 다음에 하실 한 가지 — 직접 하실 수 있는 것으로. 「애플 심사」 같은 기다리는 일은 안 받습니다}"
    WHY="${3:?왜 지금 하셔야 하나 — 한 줄. 없으면 미루게 됩니다}"
    screen_need 0 "$LINE"
    printf '%s\t다음\t%s\t%s\t\t\n' "$(date +%F)" "$LINE" "$WHY" >> "$STATE"
    screen_save "$LINE"
    echo "  · 다음에 하실 것으로 적었습니다: $LINE"
    ;;

  표준)
    WHAT="${2:?어떤 방식이 표준인가 — 한 줄로}"
    SRC="${3:?출처 — 어느 앱에서 봤나 · 어느 공식 문서인가. 없으면 그 자리에서 다시 리서치한다}"
    CONF="${4:?어떻게 확인했나 — 돌려봄|공식문서|남이한것|내기억 중 하나}"
    case "$CONF" in
      돌려봄|공식문서|남이한것|내기억|코드) ;;
      *) echo "  ⛔ 확인은 «돌려봄·공식문서·남이한것·내기억·코드» 중 하나여야 합니다: $CONF" >&2
         echo "     ⭐ 「내기억」도 적을 수 있습니다 — 그러면 「아직 표준이 아니다」로 보입니다." >&2
         exit 1 ;;
    esac
    _FEATS="$(NF_STATE="$NF_STATE" python3 "$NF_PYDIR/../tools/plan.py" json 2>/dev/null | python3 -I -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for p in (d.get("단계") or {}).values():
    for f in p.get("기능들") or []:
        print(f["기능"])
' 2>/dev/null)"
    if [ -n "$_FEATS" ]; then
      if [ -z "${5:-}" ] || { [ "${5}" != "공통" ] && ! printf '%s\n' "$_FEATS" | grep -Fxq -- "${5}"; }; then
        echo "  ⛔ 표준은 설계표의 기능 하나에 묶습니다 — 다섯째 칸에 기능 이름을 적으십시오(여러 기능에 걸치면 「공통」)." >&2
        echo "     지금 적은 것: 「${5:-비어 있음}」" >&2
        echo "     설계표의 기능: $(printf '%s\n' "$_FEATS" | paste -sd'|' - | sed 's/|/ · /g')" >&2
        exit 1
      fi
    fi
    screen_need 1 "$WHAT" 표준
    printf '%s\t표준\t%s\t%s\t%s\t%s\t\n' "$(date +%F)" "$WHAT" "$SRC" "$CONF" "${5:-}" >> "$STATE"
    screen_save "$WHAT"
    echo "  · 기록에 남김 [표준] $WHAT"
    echo "      출처: $SRC"
    if [ "$CONF" = "내기억" ]; then
      echo "      🔴 출처가 없습니다 — **아직 표준이라고 부를 수 없습니다.**"
      echo "         공식 문서나 돌아가는 앱에서 확인하면 다시 적어 주십시오."
    fi
    _AT="$NF_PYDIR/../tools/attempts.py"
    if [ -f "$_AT" ] && [ -n "${5:-}" ]; then
      _BLK=$(python3 "$_AT" --막힌길 "${5}" 2>/dev/null) || _BLK=""
      if [ -n "$_BLK" ]; then
        echo "      ──"
        printf '%s\n' "$_BLK"
      fi
    fi
    board_nudge 표준
    ;;

  표준목록)
    echo
    echo "── 이 앱의 표준 방식 ─────────────────────────────"
    echo
    TOOLS="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)" python3 -I - <<'PYEOF'
import os, sys
sys.path.insert(0, os.environ.get("TOOLS", ""))
import standards
for line in standards.사람말(standards.compute()):
    print(line)
PYEOF
    echo
    echo "  ⚠️ 저희가 적어 둔 것만 보입니다 — 「이것이 업계 표준 전부」가 아닙니다."
    echo
    ;;

  못함목록)
    [ -f "$STATE" ] || { echo "   없습니다."; exit 0; }
    awk -F'\t' '
      NR==FNR { if ($2=="풀림") ok[$3]=1; if ($2=="없어짐") gone[$3]=$4; next }
      $2=="못함" {
        for (k in ok)   if (index($3,k)) next
        for (k in gone) if (index($3,k)) { g++; gwhy[$3]=gone[k]; next }
        n++
        print "   ⚠️ " $3; print "      없는 것: " $4; print "      하실 일: " $5; print "" }
      END { if (!n) print "   지금 못 돌고 있는 검사는 없습니다."
            if (g) { printf "   · 필요 없어져 치운 것 %d건:\n", g
                     for (w in gwhy) print "      - " w "\n        이유: " gwhy[w] } }' "$STATE" "$STATE"
    ;;

  남은것)
    if [ "${2:-}" = "--단계" ]; then FORCED="${3:?단계 라벨 — 예: 2. 검증}"; shift 2; fi
    LINE="${2:?이 단계에서 아직 안 한 것 — 제품 언어로 한 줄}"
    ST=$(awk -F'\t' '$2=="단계"{v=$3} END{print v}' "$STATE" 2>/dev/null)
    [ -n "${FORCED:-}" ] && ST="$FORCED"
    screen_need 1 "$LINE" 남은것
    printf '%s\t남은것\t%s\t%s\t%s\t%s\n' "$(date +%F)" "$LINE" "$ST" "${3:-}" "${4:-}" >> "$STATE"
    screen_save "$LINE"
    echo "  · 남은 것 [${ST:-단계 없음}] $LINE"
    ;;

  남은것목록)
    bash "$0" 조종석준비 >/dev/null 2>&1 || true
    STAGES="$(dirname "$STATE")/board/stages.json"
    if [ ! -f "$STAGES" ]; then
      echo "  아직 기록이 없습니다 — 남은 것을 셀 수 없습니다."
      echo "  ⚠️ 이건 「남은 게 없다」가 아니라 **아직 아무것도 안 적혔다**는 뜻입니다."
      exit 0
    fi
    STAGES="$STAGES" python3 -I - <<'PYEOF'
import json, os
d = json.load(open(os.environ["STAGES"], encoding="utf-8"))
rows = []
for b in list((d.get("per") or {}).values()) + [d.get("loose") or {}]:
    for x in (b.get("open") or []):
        rows.append(((b.get("labels") or [""])[0], x))
print()
print("── 지금 남은 것 ─────────────────────────────────")
if not rows:
    print("   남은 것이 없습니다.")
    print("   ⚠️ 적은 것이 없으면 여기도 빕니다 — 「다 했다」와 구별되지 않습니다.")
else:
    for lbl, x in rows:
        print("   · %s%s" % (("[%s] " % lbl) if lbl else "", x["what"]))
    print()
    print("   ⭐ 끝내시면 그 줄을 「끝냄」으로, 안 하기로 하셨으면 「없어짐」으로 적습니다.")
print()
PYEOF
    ;;

  끝냄)
    KEY="${2:?끝낸 것 — 일부 글자}"
    [ -f "$STATE" ] && awk -F'\t' -v k="$KEY" '$2=="남은것" && index($3,k){f=1} END{exit !f}' "$STATE" \
      || { echo "  「$KEY」이 들어간 «남은 것»을 못 찾았습니다." >&2; exit 1; }
    printf '%s\t끝냄\t%s\t\t\n' "$(date +%F)" "$KEY" >> "$STATE"
    echo "  · 끝냈습니다: $KEY"
    ;;
esac
