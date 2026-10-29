LC_ALL=C; export LC_ALL
case "$KIND" in

  기능연결)
    TOPIC="${2:?기록에 적힌 «주제» 낱말 — 그대로}"
    FEAT="${3:?기능 이름 — 아무 이름이나 됩니다}"
    SUB="${4:-}"
    _FT="$NF_PYDIR/../data/기능.tsv"
    if [ -f "$_FT" ] && awk -F'\t' -v f="$FEAT" '$1==f{ok=1} END{exit !ok}' "$_FT"; then
      _GATEY="예"
    else
      _GATEY="아니오"
      if [ -f "$_FT" ]; then
        _NEAR="$(awk -F'\t' -v f="$FEAT" '
          !/^#/ && NF>1 {
            a=$1; b=f; gsub(/[ \t]/,"",a); gsub(/[ \t]/,"",b)
            if (a==b || index(a,b) || index(b,a)) print $1
          }' "$_FT" | head -2)"
      fi
    fi
    FMAP="$(dirname "$STATE")/feature-map.tsv"
    touch "$FMAP"
    awk -F'\t' -v k="$TOPIC" '$1!=k' "$FMAP" > "$FMAP.tmp" 2>/dev/null || true
    printf '%s\t%s\t%s\n' "$TOPIC" "$FEAT" "$SUB" >> "$FMAP.tmp"
    mv "$FMAP.tmp" "$FMAP"
    if [ -n "$SUB" ]; then echo "  · 「$TOPIC」 → $FEAT / $SUB"
    else echo "  · 「$TOPIC」 → $FEAT"; fi
    echo "    이제 그 말이 붙은 일들을 이 기능으로 봅니다. 지난 것까지 같이 봅니다."
    if [ "$_GATEY" = "예" ]; then
      echo "    이 기능은 출시 전에 걸리는 일을 끌고 옵니다 — 그 셈에 들어갑니다."
    else
      echo "    이 기능은 출시 전에 걸리는 일을 끌고 오지 않습니다. 진척만 봅니다."
      if [ -n "${_NEAR:-}" ]; then
        echo "    ⚠️ 비슷한 이름이 목록에 있습니다 — 이걸 뜻하셨다면 그 이름으로 적으십시오:"
        printf '%s\n' "$_NEAR" | while IFS= read -r _n; do [ -n "$_n" ] && echo "       · $_n"; done
      fi
    fi
    ;;

  기능추가|세부기능|세부빼기|세부상태|설계표|화면|화면요소|화면이동|화면종류|화면이름|화면언제|화면하는일|화면갈림|화면상태|화면상태비움|화면일|화면일빼기|화면빼기|기능빼기|화면문제|설치전|설치전확인|기능설명|세부언제)
    _PL="$NF_PYDIR/../tools/plan.py"
    [ "$1" = "설계표" ] && set -- 보기 "${@:2}"
    if [ "$1" = "기능추가" ]; then
      NF_STATE="$NF_STATE" python3 "$_PL" "$@" || exit $?
      python3 -I "$NF_PYDIR/레드팀권함.py" "$STATE" 기능 "${3-}" 2>/dev/null || true
      exit 0
    fi
    NF_STATE="$NF_STATE" exec python3 "$_PL" "$@"
    ;;

  가져오기)
    _IM="$NF_PYDIR/../tools/lint_import.py"
    [ "$#" -le 1 ] && set -- 가져오기 보기
    if [ "${2-}" = "시작" ]; then
      NF_STATE="$NF_STATE" python3 "$_IM" "${@:2}" || exit $?
      python3 -I "$NF_PYDIR/모델권함.py" "" 가져오기 2>/dev/null || true
      exit 0
    fi
    NF_STATE="$NF_STATE" exec python3 "$_IM" "${@:2}"
    ;;

  기능진척)
    _FP="$NF_PYDIR/../tools/feature_progress.py"
    if [ ! -f "$_FP" ]; then
      echo "  ⛔ 설치가 덜 끝났습니다 — 같이 와야 하는 파일이 빠져 있습니다." >&2
      echo "     설치를 한 번 더 돌리면 됩니다. 기록은 지워지지 않습니다." >&2
      echo "     [모델] 빠진 파일: $_FP" >&2
      exit 1
    fi
    exec python3 "$_FP"
    ;;

  영향)
    MINE="${2:?고치는 쪽 — 기록에 쓰인 «주제» 낱말}"
    OTHER="${3:?같이 봐야 하는 쪽 — 기록에 쓰인 «주제» 낱말}"
    KIND="${4:?종류 — \"같은것을쓴다: <무엇을 같이 쓰나>\" | \"순서가있다: <무엇이 먼저>\" | \"같은화면: <어느 화면>\"}"
    SRC="${5:?어떻게 알았나 — 깨졌다|리서치|표준|내판단}"
    case "$KIND" in
      같은것을쓴다:*|순서가있다:*|같은화면:*) ;;
      같은것을쓴다|순서가있다|같은화면)
        echo "  ⛔ 뒤에 설명이 필요합니다 — 「$KIND: 무엇을」" >&2; exit 1 ;;
      *) echo "  ⛔ 종류는 «같은것을쓴다·순서가있다·같은화면» 중 하나로 시작해야 합니다: $KIND" >&2
         echo "     ⭐ 종류를 가르지 않으면 「같이 보라」만 나오고 «무엇을 할지»가 안 나옵니다." >&2
         exit 1 ;;
    esac
    case "$SRC" in
      깨졌다|리서치|표준|내판단|코드) ;;
      *) echo "  ⛔ 출처는 «깨졌다·리서치·표준·내판단·코드» 중 하나여야 합니다: $SRC" >&2; exit 1 ;;
    esac
    _TOOLS="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)"
    if [ ! -f "$_TOOLS/dependencies.py" ]; then
      echo "  ⛔ 설치가 덜 끝났습니다 — 같이 와야 하는 파일이 빠져 있습니다." >&2
      echo "     설치를 한 번 더 돌리면 됩니다. 기록은 지워지지 않습니다." >&2
      echo "     [모델] 빠진 파일: $_TOOLS/dependencies.py" >&2
      exit 1
    fi
    if true; then
      _BAD=$(NFMINE="$MINE" NFOTHER="$OTHER" NFTOOLS="$_TOOLS" python3 -I -c '
import os, sys
sys.path.insert(0, os.environ["NFTOOLS"])
import dependencies as D
have = D.쓸수있는이름()
miss = [x for x in (os.environ["NFMINE"], os.environ["NFOTHER"]) if x not in have]
print(" · ".join(miss))')
      _RC=$?
      if [ "$_RC" -ne 0 ]; then
        echo "  ⛔ 이름을 확인하지 못했습니다 — **적지 않았습니다.**" >&2
        echo "     ⚠️ 이건 「이름이 맞다」가 아니라 「못 쟀다」입니다." >&2
        exit 1
      fi
      if [ -n "$_BAD" ]; then
        echo "  ⛔ 기록에 없는 이름입니다: $_BAD" >&2
        echo "     ⭐ 지도는 **이미 적어 둔 기능 사이**에만 그립니다 —" >&2
        echo "        그 기능으로 무엇이 됐거나 남았는지를 먼저 적어 주십시오." >&2
        exit 1
      fi
    fi
    _NOTE="${KIND#*:}"; _NOTE="${_NOTE# }"
    screen_need 1 "$_NOTE" 영향
    printf '%s\t영향\t%s\t%s\t%s\t%s\t\n' "$(date +%F)" "$OTHER" "$SRC" "$KIND" "$MINE" >> "$STATE"
    screen_save "$_NOTE"
    echo "  · 기록에 남김 [영향] 「$MINE」을 고치면 「$OTHER」도 봐야 합니다"
    case "$KIND" in
      같은것을쓴다:*) echo "      ⛔ 한쪽을 바꾸면 **다른 쪽이 깨집니다** — 고치기 전에 멈춥니다" ;;
      순서가있다:*)   echo "      ⚠️ 앞을 바꾸면 뒤가 못 돕니다" ;;
      같은화면:*)     echo "      ⚠️ 모양을 바꾸면 다른 쪽 자리가 밀립니다" ;;
    esac
    [ "$SRC" = "내판단" ] && echo "      🔴 출처가 없습니다 — **아직 확인된 영향이 아닙니다.**"
    board_nudge 영향
    ;;

  제품소개)
    _K="${2:?칸 — 한줄|누구|문제|해결|수익}"
    _V="${3:?내용 — 사용자가 읽는 말로 한두 문장}"
    case "$_K" in 한줄|누구|문제|해결|수익) ;; *) echo "  ⛔ 칸은 «한줄 · 누구 · 문제 · 해결 · 수익» 중 하나입니다" >&2; exit 1 ;; esac
    python3 "$_SL" --한줄 -- "$_V" >/dev/null 2>&1 || true
    printf '%s\t제품소개\t%s\t%s\t\t\t\n' "$(date +%F)" "$_K" "$_V" >> "$STATE"
    echo "  · 기록에 남김 [제품소개 · $_K] $_V"
    [ "$_K" = 한줄 ] && { python3 -I "$NF_PYDIR/새제품안내.py" "$STATE" 소개 2>/dev/null || true; }
    board_nudge 결정
    ;;

  화면없음)
    _WHY="${2:?왜 화면이 없나 — 한 줄}"
    printf '%s\t화면없음\t%s\t\t\t\t\n' "$(date +%F)" "$_WHY" >> "$STATE"
    echo "  · 기록에 남김 [화면없음] $_WHY"
    ;;

  독립)
    _F="${2:?기능 — 설계표의 기능 이름}"
    _WHY="${3:?왜 다른 기능과 안 엮이나 — 한 줄}"
    _TOOLS="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)"
    if ! NFF="$_F" NFTOOLS="$_TOOLS" python3 -I -c '
import os, sys
sys.path.insert(0, os.environ["NFTOOLS"])
import dependencies as D
sys.exit(0 if os.environ["NFF"] in D.설계표기능() else 1)'; then
      echo "  ⛔ 설계표에 없는 기능입니다: $_F" >&2; exit 1
    fi
    printf '%s\t독립\t%s\t%s\t\t\t\n' "$(date +%F)" "$_F" "$_WHY" >> "$STATE"
    echo "  · 기록에 남김 [독립] 「$_F」은 다른 기능과 엮이지 않습니다 — $_WHY"
    board_nudge 영향
    ;;

  상태)
    FEAT="${2:?어느 기능 — 기록에 쓰인 «주제» 낱말}"
    ST="${3:?상태 이름 — 예: 결제됨}"
    GO="${4:?갈 수 있는 곳 — 쉼표로 여럿. 더 갈 곳이 없으면: 끝}"
    SRC="${5:-내판단}"
    case "$SRC" in
      대표님|리서치|표준|깨졌다|내판단|코드) ;;
      *) echo "  ⛔ 출처는 «대표님·리서치·표준·깨졌다·내판단·코드» 중 하나여야 합니다: $SRC" >&2; exit 1 ;;
    esac
    _TOOLS="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)"
    if [ ! -f "$_TOOLS/dependencies.py" ]; then
      echo "  ⛔ 설치가 덜 끝났습니다 — 같이 와야 하는 파일이 빠져 있습니다." >&2
      echo "     설치를 한 번 더 돌리면 됩니다. 기록은 지워지지 않습니다." >&2
      exit 1
    fi
    _SBAD=$(NFF="$FEAT" NFTOOLS="$_TOOLS" python3 -I -c '
import os, sys
sys.path.insert(0, os.environ["NFTOOLS"])
import dependencies as D
print("" if os.environ["NFF"] in D.쓸수있는이름() else os.environ["NFF"])')
    if [ $? -ne 0 ]; then
      echo "  ⛔ 이름을 확인하지 못했습니다 — **적지 않았습니다.**" >&2
      echo "     ⚠️ 이건 「이름이 맞다」가 아니라 「못 쟀다」입니다." >&2
      exit 1
    fi
    if [ -n "$_SBAD" ]; then
      echo "  ⛔ 기록에 없는 기능입니다: 「$_SBAD」" >&2
      echo "     그 기능으로 무엇이 됐거나 남았는지를 **먼저 적어** 주십시오." >&2
      exit 1
    fi
    printf '%s\t상태\t%s\t%s\t%s\t%s\n' "$(date +%F)" "$ST" "$SRC" "$GO" "$FEAT" >> "$STATE"
    echo "  · 적었습니다 — $FEAT: 「$ST」 → $GO"
    [ "$SRC" = "내판단" ] && echo "     ⚠️ 출처가 «내판단»입니다 — 사용자가 정하신 것이 아닙니다."
    exec "$0" 상태목록 "$FEAT"
    ;;

  상태목록)
    _TOOLS="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)"
    if [ ! -f "$_TOOLS/states.py" ]; then
      echo "  ⛔ 설치가 덜 끝났습니다 — 같이 와야 하는 파일이 빠져 있습니다." >&2
      exit 1
    fi
    STATE="$STATE" NFONE="${2:-}" python3 "$_TOOLS/states.py"
    ;;

  영향목록)
    echo
    echo "── 이걸 고치면 무엇도 봐야 하나 ─────────────────"
    echo
    TOOLS="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)" python3 -I - <<'PYEOF'
import os, sys
sys.path.insert(0, os.environ.get("TOOLS", ""))
import dependencies
for line in dependencies.사람말(dependencies.compute()):
    print(line)
PYEOF
    echo
    ;;

  고치기전)
    TOPIC="${2:?어느 기능을 고치나 — 기록에 쓰인 «주제» 낱말}"
    TOOLS="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)" \
      python3 "$NF_PYDIR/../tools/dependencies.py" --고치기전 "$TOPIC"
    exit $?
    ;;
esac
