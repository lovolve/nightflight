LC_ALL=C; export LC_ALL
case "$KIND" in

  단계)
    NAME="${2:?단계 이름 — 0. 진단 · 1. 기획 · 2. 검증 · 3. 설계 · 4. 개발 · 5. 확인 · 6. 출시 · 7. 수정 · 8. 출시후 (가져오기 시험 2026-10-25: 이름 목록이 없어 짐작했다)}"
    if printf '%s' "$NAME" | grep -q '검증'; then
      _MISSI=""
      for _k in 한줄 누구 문제; do awk -F'\t' -v k="$_k" '$2=="제품소개"&&$3==k&&$4!=""{f=1} END{exit !f}' "$STATE" 2>/dev/null || _MISSI="$_MISSI $_k"; done
      if [ -n "$_MISSI" ]; then
        echo "  ⛔ 검증에 들어가기 전에 이 제품을 간단히 적어야 합니다 — 아직:$_MISSI" >&2
        echo "     ledger.sh 제품소개 <한줄|누구|문제|해결|수익> \"<사용자가 읽는 말>\"" >&2
        exit 1
      fi
    fi
    if printf '%s' "$NAME" | grep -qE '개발|확인|출시|수정'; then
      _MISS="$(NFTOOLS="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)" python3 -I -c '
import os, sys
sys.path.insert(0, os.environ["NFTOOLS"])
import dependencies as D, plan as P
done = D.연결된기능()
print(" · ".join(sorted({r["기능"] for r in P.읽기() if str(r["단계"]).strip().isdigit() and int(r["단계"]) >= 4} - set(done))))' 2>/dev/null)" || _MISS="?"
      _SCR="$(dirname "$STATE")/screens.tsv"
      if ! { [ -f "$_SCR" ] && grep -q $'^화면\t' "$_SCR"; } && ! awk -F'\t' '$2=="화면없음"&&$3!=""{f=1} END{exit !f}' "$STATE" 2>/dev/null; then
        echo "  ⛔ 개발에 들어가기 전에 화면 설계서가 있어야 합니다 — 화면 목록 · 화면마다 들어갈 기능 · 화면 사이 이동." >&2
        echo "     화면이 없는 앱이면 이유를 밝혀 주십시오." >&2
        echo "     화면: ledger.sh 화면 <이름> <설명> · 화면요소 <화면> <설명> <기능> [세부기능] · 화면이동 <화면> <다음> <무엇을 하면> · 없으면: ledger.sh 화면없음 <이유>" >&2
        echo "     화면마다: 화면언제 <화면> <언제 보나> · 화면하는일 <화면> <하는 일> · 줄인 이름이면 화면이름 <화면> <풀어 쓴 이름> · 갈리면 화면갈림 <화면> <물음>(이동 조건은 «예» · «아니오 · …»)" >&2
        exit 1
      fi
      if [ "$_MISS" = "?" ]; then
        echo "  ⚠️ 기능 사이 연결을 따져 봤는지 재지 못했습니다 — 막지 않고 넘어갑니다." >&2
      elif [ -n "$_MISS" ]; then
        echo "  ⛔ 개발에 들어가기 전에 기능마다 다른 기능과 어떻게 엮이는지 적어야 합니다 — 아직: $_MISS" >&2
        echo "     엮이면 「ledger.sh 영향」, 안 엮이면 「ledger.sh 독립 <기능> <이유>」" >&2
        exit 1
      fi
    fi
    if printf '%s' "$NAME" | grep -q '설계'; then
      _P12="$(awk -F'\t' '$1=="1"||$1=="2"{n++} END{print n+0}' "$(dirname "$STATE")/plan.tsv" 2>/dev/null)"
      [ "${_P12:-0}" = 0 ] && echo "  ⚠️ 기획 · 검증 표가 비어 있습니다 — 설계로 넘어가지만, 무엇을 왜 만드는지가 조종석에 안 남습니다. 가져오는 앱이면 기획 · 검증에서 정한 것도 채워 주십시오." >&2
    fi
    printf '%s\t단계\t%s\t\t\n' "$(date +%F)" "$NAME" >> "$STATE"
    echo "  · 단계: $NAME"
    python3 -I "$NF_PYDIR/새제품안내.py" "$STATE" 단계 2>/dev/null || true
    board_nudge 단계
    _SN=$(printf '%s' "$NAME" | awk '{n=split("진단 기획 검증 설계 개발 확인 출시 수정 출시후",a," "); r=""; for(i=n;i>=1;i--) if(index($0,a[i])){r=i-1; break} print r}')
    _BR="$NF_PYDIR/두뇌.sh"
    if [ -n "$_SN" ] && [ -x "$_BR" ] && [ -n "${NF_BRAIN_BASE:-}" ] && [ -n "${NF_DOORKEY:-}" ] && [ -z "${NF_NO_BRAIN_LIST:-}" ]; then
      _GL="$(NF_BRAIN_TIMEOUT=4 "$_BR" "$_SN" --목록 2>/dev/null)"
      if [ -n "$_GL" ]; then
        echo "  · 이 단계에서 받을 수 있는 안내: $_GL"
        echo "    지금 하는 일에 맞는 것을 골라 바로 받으십시오: 두뇌.sh $_SN <갈래>"
      fi
    fi
    case "$_SN" in
      3) python3 -I "$NF_PYDIR/모델권함.py" "" 설계 2>/dev/null || true ;;
      4) python3 -I "$NF_PYDIR/레드팀권함.py" "$STATE" 개발 2>/dev/null || true ;;
      6) python3 -I "$NF_PYDIR/레드팀권함.py" "$STATE" 출시 2>/dev/null || true ;;
    esac
    exec "$0" 전제점검
    ;;

  단계연결)
    LBL="${2:?프로젝트의 단계 이름 — 기록에 적힌 그대로}"
    IDX="${3:?9단계 번호 0~8 (0진단 1기획 2검증 3설계 4개발 5확인 6출시 7수정 8출시후)}"
    case "$IDX" in [0-8]) ;; *) echo "  번호는 0~8 입니다." >&2; exit 1 ;; esac
    MAP="$(dirname "$STATE")/stage-map.tsv"
    touch "$MAP"
    awk -F'\t' -v k="$LBL" '$1!=k' "$MAP" > "$MAP.tmp" 2>/dev/null || true
    printf '%s\t%s\n' "$LBL" "$IDX" >> "$MAP.tmp"
    mv "$MAP.tmp" "$MAP"
    NAMES="진단 기획 검증 설계 개발 확인 출시 수정 출시후"
    echo "  · 「$LBL」 → $IDX-$(echo $NAMES | cut -d' ' -f$((IDX+1)))"
    ;;

  단계확인)
    SNUM="${2:?어느 단계 0~8}"
    WHAT="${3:?무엇을 확인했나 — 제품 언어로 한 줄}"
    HOW="${4:?상태 — 단계마다 받는 말이 다릅니다}"
    case "$SNUM" in
      0) OKS="됨 안됨 예고 모름" ;;
      1) OKS="정함 아직" ;;
      5) OKS="봤음 안됨 폰필요" ;;
      6) OKS="됨 남음 막힘" ;;
      7) OKS="고침 고치는중 모름" ;;
      8) OKS="읽음 답초안 올림" ;;
      2) echo "  ⛔ 2-검증은 「검증」으로 적습니다 — 확인됨·치명적과 틀을 같이 받습니다." >&2; exit 2 ;;
      3) echo "  ⛔ 3-설계는 「설계」·「갈래」로 적습니다." >&2; exit 2 ;;
      4) echo "  ⛔ 4-개발은 「됐다」·「기능연결」로 적습니다 — 상태 지도가 그걸 그립니다." >&2; exit 2 ;;
      *) echo "  ⛔ 단계는 0~8 입니다." >&2; exit 2 ;;
    esac
    case " $OKS " in
      *" $HOW "*) ;;
      *) echo "  ⛔ 「$HOW」는 $SNUM 단계에서 받을 수 없습니다 — 받는 말: $OKS" >&2; exit 2 ;;
    esac
    printf '%s\t단계확인\t%s\t%s\t%s\t%s\n' "$(date +%F)" "$WHAT" "${5:-}" "$HOW" "$SNUM" >> "$STATE"
    echo "  · 기록에 남김 [$SNUM단계·$HOW] $WHAT"
    ;;

  검증)
    WHAT="${2:?무엇을 봤나 — 한 줄로}"
    JUDGE="${3:?확인됨 또는 치명적}"
    WHY="${4:?근거 — 어디서 봤나. 출처가 없으면 그건 내 짐작이다}"
    FRAME="${5:-}"
    if [ -z "$FRAME" ]; then
      echo "  ⛔ 틀을 안 적으면 받지 않습니다." >&2
      echo "     조사 전에 넷을 적습니다 — **누구 말인가(모집단) · 몇 개(표본) ·" >&2
      echo "     무엇 대비(분모) · 무엇이 좋은 것인가(결과변수)**." >&2
      echo "     ⚠️ 첫째가 «누구 말인가»입니다. 나머지 셋을 정확히 지켜도" >&2
      echo "     엉뚱한 사람들을 조사하면 답이 통째로 틀립니다." >&2
      exit 2
    fi
    case "$JUDGE" in
      확인됨|치명적) ;;
      *) echo "  ⛔ 「$JUDGE」는 받을 수 없습니다 — «확인됨» 또는 «치명적»입니다." >&2
         echo "     진행·수정·접기는 **사용자가 내시는 결정**이라 「결정」으로 적습니다." >&2
         exit 2 ;;
    esac
    screen_need 0 "$WHAT" 검증
    printf '%s\t검증\t%s\t%s\t%s\t%s\n' "$(date +%F)" "$WHAT" "$WHY" "$JUDGE" "$FRAME" >> "$STATE"
    screen_save "$WHAT"
    echo "  · 기록에 남김 [검증·$JUDGE] $WHAT"
    ;;

  설계)
    WHAT="${2:?어느 기능}"
    WHERE="${3:?넣음 · 뺌 · 다음번}"
    WHY="${4:?왜 — 사용자 말씀을 그대로. 인용이 없으면 그건 내 판단이다}"
    case "$WHERE" in
      넣음|뺌|다음번) ;;
      *) echo "  ⛔ 「$WHERE」는 받을 수 없습니다 — «넣음»·«뺌»·«다음번» 셋입니다." >&2; exit 2 ;;
    esac
    printf '%s\t설계\t%s\t%s\t%s\t\n' "$(date +%F)" "$WHAT" "$WHY" "$WHERE" >> "$STATE"
    echo "  · 기록에 남김 [설계·$WHERE] $WHAT"
    ;;

  갈래)
    TOPIC="${2:?무엇을 고르나 — 배색·레이아웃 같은}"
    NAME="${3:?갈래 이름}"
    SRC="${4:?출처와 실측값 — 「모던하게」 같은 말은 안 받습니다}"
    PICK="${5:-}"
    if awk -F'\t' -v k="$TOPIC — $NAME" '$2=="갈래" && $3==k{f=1} END{exit !f}' "$STATE" 2>/dev/null; then
      if [ -n "$PICK" ]; then
        printf '%s\t갈래\t%s\t%s\t고름\t%s\n' "$(date +%F)" "$TOPIC — $NAME" "$SRC" "$NAME" >> "$STATE"
        echo "  · 고르신 것으로 적었습니다 — $TOPIC — $NAME"
      else
        echo "  ⚠️ 「$TOPIC — $NAME」은 이미 적혀 있습니다 — 또 적지 않습니다."
      fi
      exit 0
    fi
    printf '%s\t갈래\t%s\t%s\t%s\t%s\n' "$(date +%F)" "$TOPIC — $NAME" "$SRC" "${PICK:+고름}" "$NAME" >> "$STATE"
    N=$(awk -F'\t' -v k="$TOPIC — " '$2=="갈래" && index($3,k)==1{n++} END{print n+0}' "$STATE")
    echo "  · 기록에 남김 [갈래] $TOPIC — $NAME${PICK:+  (고르셨습니다)}"
    if [ "$N" -lt 2 ]; then
      echo "     ⚠️ 「$TOPIC」 갈래가 아직 **하나뿐**입니다 — 하나만 내면 고르시는 게 아닙니다."
    elif [ "$N" -gt 3 ]; then
      echo "     ⚠️ 「$TOPIC」 갈래가 **$N개**입니다 — 다섯을 넘으면 못 고르십니다."
    fi
    ;;

  단계옮김)
    KEY="${2:?어느 줄인가 — 일부 글자}"
    TO="${3:?옮길 단계 라벨 — 예: 2. 검증}"
    [ -f "$STATE" ] && awk -F'\t' -v k="$KEY" '($2=="남은것"||$2=="됐다") && index($3,k){f=1} END{exit !f}' "$STATE" \
      || { echo "  「$KEY」이 들어간 «남은것/됐다»를 못 찾았습니다." >&2; exit 1; }
    printf '%s\t단계옮김\t%s\t%s\t\t\n' "$(date +%F)" "$KEY" "$TO" >> "$STATE"
    echo "  · 단계를 옮겼습니다: 「$KEY」 → $TO"
    ;;
esac
