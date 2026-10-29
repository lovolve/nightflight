LC_ALL=C; export LC_ALL
case "$KIND" in

  한국절차)
    ST=$(awk -F'\t' '$2=="단계"{v=$3} END{print v}' "$STATE" 2>/dev/null)
    N=0
    add() {
      awk -F'\t' -v x="$1" '$2=="남은것" && $3==x{f=1} END{exit !f}' "$STATE" 2>/dev/null && return 0
      printf '%s\t남은것\t%s\t%s\t%s\t절차\n' "$(date +%F)" "$1" "$ST" "$2" >> "$STATE"; N=$((N+1))
    }
    add "회원 정보를 받기 전에 — 남이 볼 수 없어야 할 것을 실제로 못 보는지 확인한다" "권한"
    add "출시 전에 — 개발자 계정·심사 대행 같은 «숨은 비용»을 먼저 알아 둔다" "숨은비용"
    add "출시 전에 — 심사에 며칠 걸리는지 「출시 절차」로 확인하고 일정을 잡는다" "심사기간"
    echo "  · 한국에서만 해야 하는 것 ${N}건을 「남은 것」에 넣었습니다 [${ST:-단계 없음}]"
    [ "$N" -eq 0 ] && echo "    (이미 다 들어가 있습니다)"
    echo "    ⚠️ 이건 «해당되는지 확인하라»는 것이지 «해야 한다»가 아닙니다 — 판단은 사용자 몫입니다."
    ;;

  사람확인)
    mkdir -p "$(dirname "$NF_PERSON")"
    printf '%s\t사람확인\t%s\t%s\t\t\n' "$(date +%F)" "$(basename "${NF_ROOT:-?}")" "${2:-그대로}" >> "$NF_PERSON"
    echo "  · 확인하셨다고 적었습니다 — 이 앱에서는 다시 여쭙지 않습니다."
    ;;

  앱설정묻기)
    _KNOWN=""
    if [ -f "${NF_PERSON:-/nonexistent}" ]; then
      _KNOWN=$(awk -F'\t' '$2=="계정종류"||$2=="이미한것"||$2=="계정만든날"||$2=="전에만든것"{k[$2]=1}
                 END{for(x in k) printf "%s ", x}' "$NF_PERSON")
    fi
    echo
    if [ -n "$_KNOWN" ]; then
      echo "  ⭐ 지난 앱에서 들은 것이 있어 **그만큼은 여쭙지 않습니다** — 「이어받기」로 보십시오."
      echo
    fi
    echo "── 사용자에게 이렇게 여쭙니다 (한 번에 다 묻지 않습니다) ──"
    echo
    echo "  ① 어디에 내실 건가요?  iPhone 앱 · 안드로이드 앱 · 웹사이트 — 여럿도 됩니다"
    echo "       iPhone 이면 맥과 개발 도구가 필요하고 애플에 연 14만원이 듭니다"
    echo "       안드로이드는 컴퓨터 종류를 안 가리고 구글에 1회 3만원입니다"
    echo "       웹은 심사가 없어 가장 빠릅니다 · 둘 이상이면 첫 출시는 하나만 권합니다"
    echo
    echo "  ② (①에서 앱을 고르셨으면) 그 계정이 개인 이름인가요, 회사 이름인가요?"
    echo "       아직 안 만드셨으면 그렇게 말씀해 주세요. 모르셔도 괜찮습니다"
    echo "       계정을 만든 날도 알려 주시면 좋습니다 — 날짜 하나로 14일이 사라지거나 생깁니다"
    echo
    echo "  ③ 무엇을 만들고 싶으신가요? 한 줄로 말씀해 주세요"
    echo
    echo "  ③-1 그 앱을 뭐라고 부르실 건가요?  아직 안 정하셨으면 「없음」이라고 해 주세요"
    echo "       나중에 기록을 저희에게 보내실 때, **그 이름이 든 줄을 제가 빼 드립니다**"
    echo
    echo "  ③-2 (앱을 고르셨으면) 만드는 길이 둘입니다. 어느 쪽이 좋으신가요?"
    if bash "$0" 아는말인가 네이티브 2>/dev/null; then
      echo "       ㉮ **네이티브** — 사진 찍기·알림·위치를 다 쓸 수 있습니다. 더 오래 걸립니다"
    else
      echo "       ㉮ **전화기에 맞게 새로 만든다**(이것을 «네이티브»라고 부릅니다)"
      echo "            사진 찍기·알림·위치를 다 쓸 수 있습니다. 더 오래 걸립니다"
    fi
    if bash "$0" 아는말인가 웹뷰 2>/dev/null; then
      echo "       ㉯ **웹뷰** — 빠르고, 웹과 앱이 한 벌입니다"
    else
      echo "       ㉯ **웹사이트를 만들어 그대로 앱에 넣는다**(이것을 «웹뷰»라고 부릅니다)"
      echo "            빠르고, 웹과 앱이 한 벌입니다"
    fi
    echo "            ⛔ 대신 사진 찍기·알림 같은 것을 **못 붙입니다**"
    echo "            ⛔ 그리고 애플이 「웹사이트를 그대로 넣은 앱」을 돌려보낼 수 있습니다"
    echo "       🔴 **나중에 바꾸면 거의 새로 만듭니다.** 그래서 지금 여쭙니다"
    echo
    echo "  ④ 돈을 받으실 건가요?  앱 안에서 받는다 · 밖에서 받는다 · 안 받는다"
    echo
    case " $_KNOWN " in
      *" 이미한것 "*)
        echo "  ⑤ (이미 들었습니다 — 「이어받기」에서 확인만 하시면 됩니다)"; echo ;;
      *)
        echo "  ⑤ 전에 앱을 내 보신 적이 있나요? 있으면 그 계정과 번호를 그대로 이어 씁니다"
        echo "       그리고 이미 해 두신 것이 있나요?  애플 가입 · 회사 번호 · 조직 계정"
        echo "       🔴 이걸 모르면 **이미 해 두신 것까지 「걸린다」고 말하게 됩니다**"
        echo ;;
    esac
    echo "  ⛔ 모르시는 것은 「모름」으로 두셔도 됩니다 — 그러면 그 출시 절차를 「확인 필요」로 남깁니다."
    echo "  (답을 들으면 「앱설정」으로 한 축씩 적습니다)"
    echo
    ;;

  앱설정)
    AX="${2:?어느 축인가 — 플랫폼·계정종류·계정만든날(구글 플레이 계정)·돈받기·기능·만들것·앱이름·이미한것·전에만든것·만드는법}"
    VAL="${3:?값 — 모르시면 그대로: 모름}"
    case "$AX" in
      플랫폼|계정종류|계정만든날|돈받기|기능|만들것|앱이름|이미한것|전에만든것|만드는법) ;;
      *) echo "  ⛔ 모르는 축입니다: 「$AX」" >&2
         echo "     쓸 수 있는 것: 플랫폼 · 계정종류 · 계정만든날 · 돈받기 · 기능 · 만들것 · 앱이름 · 이미한것 · 전에만든것 · 만드는법" >&2
         exit 1 ;;
    esac
    _DATA="$(cd "$NF_PYDIR/../data" 2>/dev/null && pwd)"
    _bad() { echo "  ⛔ $AX 에 쓸 수 없는 값입니다: 「$1」" >&2; echo "     쓸 수 있는 것: $2" >&2; exit 1; }
    _DID=""
    if [ "$AX" = "이미한것" ]; then
      _DIDF="$_DATA/이미한것.tsv"
      [ -f "$_DIDF" ] && _DID="$(awk -F'\t' '!/^#/ && NF>1 && $1!=""{printf "%s·", $1}' "$_DIDF")"
      [ -n "$_DID" ] || { echo "  ⛔ 고를 수 있는 값을 못 읽어 확인하지 못했습니다." >&2; exit 1; }
    fi
    printf '%s\n' "$VAL" | sed 's/·/\n/g' | while IFS= read -r v; do
      v="$(printf '%s' "$v" | sed 's/^ *//; s/ *$//')"
      [ -z "$v" ] && continue
      [ "$v" = "모름" ] && continue
      case "$AX" in
        플랫폼)   case "$v" in iPhone|안드로이드|웹|"스토어에 안 낸다") ;;
                  *) _bad "$v" "iPhone · 안드로이드 · 웹 · 스토어에 안 낸다 · 모름" ;; esac ;;
        계정종류) case "$v" in 개인|조직|아직없음) ;; *) _bad "$v" "개인 · 조직 · 아직없음 · 모름" ;; esac ;;
        돈받기)   case "$v" in 앱안에서|밖에서|안받는다) ;; *) _bad "$v" "앱안에서 · 밖에서 · 안받는다 · 모름" ;; esac ;;
        이미한것) case "·$_DID" in *"·$v·"*) ;; *) [ "$v" = "없음" ] ||
                     _bad "$v" "$(printf %s "${_DID%·}" | sed 's/·/ · /g') · 없음 · 모름" ;; esac ;;
        만드는법) case "$v" in 전화기에맞게|웹을껍데기에) ;;
                     *) _bad "$v" "전화기에맞게 · 웹을껍데기에 · 모름" ;; esac ;;
        계정만든날) case "$v" in 아직없음) ;; [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) ;;
                     *) _bad "$v" "구글 플레이 개발자 계정을 만든 날(2025-01-31 꼴) · 아직없음 · 모름" ;; esac ;;
        기능)     if [ ! -f "$_DATA/기능.tsv" ]; then
                    echo "  ⛔ 기능 목록 파일을 못 찾아 확인하지 못했습니다." >&2
                    exit 1
                  elif ! awk -F'\t' -v v="$v" '!/^#/ && $1==v{f=1} END{exit !f}' "$_DATA/기능.tsv"; then
                    echo "  ⛔ 기능 목록에 없습니다: 「$v」" >&2
                    echo "     목록:" >&2
                    awk -F'\t' '!/^#/ && NF>1{printf "       · %s\n", $1}' "$_DATA/기능.tsv" >&2
                    exit 1
                  fi ;;
      esac
    done || exit 1
    case "$AX" in
      계정종류|계정만든날|이미한것|전에만든것) WHERE="사람" ;;
      *)                                      WHERE="앱" ;;
    esac
    if [ "$WHERE" = "사람" ]; then
      mkdir -p "$(dirname "$NF_PERSON")"
      printf '%s\t%s\t%s\t%s\t\n' "$(date +%F)" "$AX" "$VAL" "${4:-대표님}" >> "$NF_PERSON"
      echo "  · 적었습니다 — $AX: $VAL   (앱이 바뀌어도 따라옵니다)"
    else
      printf '%s\t앱설정\t%s\t%s\t%s\t\n' "$(date +%F)" "$AX" "$VAL" "${4:-대표님}" >> "$STATE"
      echo "  · 적었습니다 — $AX: $VAL   (이 앱에만)"
    if [ "$AX" = "기능" ]; then
      _BA2="$NF_PYDIR/../tools/binding_ahead.py"
      [ -f "$_BA2" ] && python3 "$_BA2" 2>/dev/null | sed -n '/묶이나/,$p' || true
    fi
    fi
    if [ "$AX" = "기능" ] && [ -f "$_DATA/기능.tsv" ]; then
      printf '%s\n' "$VAL" | sed 's/·/\n/g' | while IFS= read -r v; do
        v="$(printf '%s' "$v" | sed 's/^ *//; s/ *$//')"
        [ -z "$v" ] && continue
        awk -F'\t' -v v="$v" '!/^#/ && $1==v && $2!=""{printf "    %s → %s\n", $1, $2}' "$_DATA/기능.tsv"
      done
      HOW=$({ [ -f "$STATE" ] && awk -F'\t' '$2=="앱설정" && $3=="만드는법"{v=$4} END{print v}' "$STATE"; } 2>/dev/null)
      if [ "${HOW:-}" = "웹을껍데기에" ]; then
        printf '%s\n' "$VAL" | sed 's/·/\n/g' | while IFS= read -r v; do
          v="$(printf '%s' "$v" | sed 's/^ *//; s/ *$//')"
          [ -z "$v" ] && continue
          awk -F'\t' -v v="$v" '!/^#/ && $1==v && $4!=""{
            if ($4=="안됨") printf "    ⛔ %s — 웹사이트를 그대로 앱에 넣는 방법으로는 **못 붙입니다**\n", $1
            else            printf "    ⚠️ %s — 웹사이트를 그대로 앱에 넣는 방법으로는 **붙이기 어렵습니다**\n", $1
          }' "$_DATA/기능.tsv"
        done
        echo "       (이걸 나중에 아시면 만든 것을 거의 새로 만듭니다 — 실제로 그런 사례가 있습니다)"
      fi
    fi
    ;;

  앱설정보기)
    HAS_APP=0; HAS_PERSON=0
    [ -f "$STATE" ] && awk -F'\t' '$2=="앱설정"{f=1} END{exit !f}' "$STATE" && HAS_APP=1
    [ -f "${NF_PERSON:-/nonexistent}" ] && HAS_PERSON=1
    if [ "$HAS_APP" = 0 ] && [ "$HAS_PERSON" = 0 ]; then
      echo "  ⚠️ 아직 안 물어봤습니다 — 「앱설정묻기」가 먼저입니다"
      echo "     (이건 「설정이 없다」가 아니라 「안 물어봤다」입니다)"
      exit 0
    fi
    echo
    echo "── 지금 설정 (마지막에 말씀하신 것) ──────────────"
    { [ -f "$STATE" ] && awk -F'\t' '$2=="앱설정"{printf "앱\t%s\t%s\t%s\t%s\n", $3, $4, $5, $1}' "$STATE"
      [ -f "${NF_PERSON:-/nonexistent}" ] && awk -F'\t' 'NF>=3{printf "사람\t%s\t%s\t%s\t%s\n", $2, $3, $4, $1}' "$NF_PERSON"
    } | awk -F'\t' '{src[$2]=$1; v[$2]=$3; w[$2]=$4; d[$2]=$5}
      END{ n=split("플랫폼 만드는법 만들것 앱이름 기능 돈받기 계정종류 계정만든날 이미한것 전에만든것", k, " ")
           for(i=1;i<=n;i++) if(k[i] in v)
             printf "   [%s] %s: %s   (%s · %s)\n", src[k[i]], k[i], v[k[i]], w[k[i]], d[k[i]]
           for(i=1;i<=n;i++) if(!(k[i] in v)) printf "   %s: 아직 안 들었습니다\n", k[i] }'
    echo
    ;;

  규정나이)
    echo
    echo "── 규정을 마지막으로 읽은 날 ─────────────────────"
    echo
    TOOLS="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)" python3 -I - <<'PYEOF'
import os, sys
sys.path.insert(0, os.environ.get("TOOLS", ""))
import read_dates
for line in read_dates.사람말(read_dates.compute()):
    print(line)
PYEOF
    echo
    echo "  ⚠️ 저희는 **바뀌었는지는 보지 않습니다** — 「우리가 읽은 날」만 말합니다."
    echo
    ;;

  관문)
    _GT="$NF_PYDIR/../tools/gates.py"
    if [ ! -f "$_GT" ]; then
      echo "  ⛔ 설치가 덜 끝났습니다 — 같이 와야 하는 파일이 빠져 있습니다." >&2
      echo "     설치를 한 번 더 돌리면 됩니다. 기록은 지워지지 않습니다." >&2
      echo "     ⚠️ 이건 「해야 할 일이 없다」가 아니라 **알려 드릴 수 없다**입니다." >&2
      echo "     [모델] 빠진 파일: $_GT" >&2
      exit 1
    fi
    STATE="$STATE" PERSON="${NF_PERSON:-}" python3 "$_GT"
    ;;

  기다림)
    WHAT="${2:?무엇을 신청했나 — 제품 언어로}"
    USUAL="${3:?보통 걸리는 기간 — 발표된 값만. 모르면 그대로: 모름}"
    MAXD="${4:?최대 며칠 — 숫자만. 이 날을 넘기면 문의를 권한다}"
    case "$MAXD" in
      ''|*[!0-9]*)
        echo "  ⛔ 최대는 «숫자»로 적습니다: 「$MAXD」" >&2
        echo "     이 칸은 추정이 아니라 애플·구글이 발표한 값입니다 — 모르면 적지 않습니다." >&2
        exit 1 ;;
    esac
    printf '%s\t기다림\t%s\t%s\t%s\t\n' "$(date +%F)" "$WHAT" "$USUAL" "$MAXD" >> "$STATE"
    echo "  · 기다리기 시작했습니다: $WHAT"
    echo "    보통 $USUAL · 최대 ${MAXD}일 — 넘기면 문의를 권해 드립니다"
    ;;

  문의권함)
    KEY="${2:?어느 기다리는 일 — 일부 글자}"
    DRAFT="${3:?초안을 둔 자리 — 사용자가 열어 볼 곳}"
    FILLED="${4:?제가 넣어 둔 것 — 예: 신청 번호·신청한 날}"
    [ -f "$STATE" ] && awk -F'\t' -v k="$KEY" '$2=="기다림" && index($3,k){f=1} END{exit !f}' "$STATE" \
      || { echo "  「$KEY」이 들어간 «기다리는 일»을 못 찾았습니다 — 먼저 그 일을 적습니다." >&2; exit 1; }
    if awk -F'\t' -v d="$(date +%F)" -v k="$KEY" \
         '$1==d && $2=="문의권함" && $3==k{f=1} END{exit !f}' "$STATE" 2>/dev/null; then exit 0; fi
    printf '%s\t문의권함\t%s\t%s\t%s\t\n' "$(date +%F)" "$KEY" "$DRAFT" "$FILLED" >> "$STATE"
    W=$(awk -F'\t' -v k="$KEY" '$2=="기다림" && index($3,k){print $3; exit}' "$STATE")
    M=$(awk -F'\t' -v k="$KEY" '$2=="기다림" && index($3,k){print $5; exit}' "$STATE")
    U=$(awk -F'\t' -v k="$KEY" '$2=="기다림" && index($3,k){print $4; exit}' "$STATE")
    echo
    echo "  최대 ${M}일을 넘겼습니다($W)"
    echo "  보통 ${U}에 오는데 아직 소식이 없습니다."
    echo
    echo "  문의하실 때가 됐습니다. 영어로 쓰실 필요 없습니다 —"
    echo "  초안을 써서 여기에 뒀습니다: $DRAFT"
    echo "  읽어 보시고 보내시면 됩니다."
    echo "  제가 넣어 둔 것: $FILLED"
    echo
    echo "  ⛔ 보내는 것은 사용자가 하십니다 — 제가 누르지 않습니다."
    echo
    ;;

  기다림끝)
    KEY="${2:?무엇이 왔나 — «기다리는 일»의 일부 글자}"
    [ -f "$STATE" ] && awk -F'\t' -v k="$KEY" '$2=="기다림" && index($3,k){f=1} END{exit !f}' "$STATE" \
      || { echo "  「$KEY」이 들어간 «기다리는 일»을 못 찾았습니다." >&2; exit 1; }
    printf '%s\t기다림끝\t%s\t\t\t\n' "$(date +%F)" "$KEY" >> "$STATE"
    echo "  · 왔습니다: $KEY"
    ;;

  풀림)
    KEY="${2:?어느 검사 — 일부 글자}"
    printf '%s\t풀림\t%s\t\t\n' "$(date +%F)" "$KEY" >> "$STATE"
    echo "  · 이제 돕니다: $KEY"
    ;;

  없어짐)
    KEY="${2:?무엇을 치우나 — «못함»·«남은것»·«시도»의 일부 글자}"
    WHY="${3:?왜 더 이상 필요 없나 — 한 줄로}"
    KIND=$(awk -F'\t' -v k="$KEY" '($2=="못함"||$2=="남은것"||$2=="시도") && index($3,k){print $2; exit}' \
             "$STATE" 2>/dev/null)
    [ -n "$KIND" ] || {
      echo "  「$KEY」이 들어간 «못함»·«남은것»·«시도»를 못 찾았습니다." >&2
      echo "     끝낸 일이면 「끝냄」으로 적습니다:      $KEY" >&2
      echo "     이제 도는 검사면 「풀림」으로 적습니다:  $KEY" >&2
      exit 1; }
    printf '%s\t없어짐\t%s\t%s\t%s\t\t\n' "$(date +%F)" "$KEY" "$WHY" "$KIND" >> "$STATE"
    echo "  · 치웠습니다 [$KIND] $KEY"
    echo "    이유: $WHY"
    ;;
esac
