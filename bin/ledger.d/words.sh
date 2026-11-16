LC_ALL=C; export LC_ALL
case "$KIND" in

  호칭)
    CALL="$(printf '%s' "${2-}" | tr -d '\t\r\n' | cut -c1-60)"
    mkdir -p "$(dirname "$NF_PERSON")"
    printf '%s\t호칭\t%s\t\t\t\n' "$(date +%F)" "$CALL" >> "$NF_PERSON"
    if [ -n "$CALL" ]; then echo "  이제 «$CALL»(이)라고 부르겠습니다."; else echo "  이제 따로 부르는 말 없이 말씀드리겠습니다."; fi
    ;;

  낱말묻기)
    _LUF="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)/lint_user_facing.py"
    if [ ! -f "$_LUF" ]; then echo "  ⛔ 낱말 목록을 못 찾았습니다." >&2; exit 1; fi
    if { [ -f "${NF_PERSON:-/nonexistent}" ] && awk -F'\t' '$2=="아는낱말"{f=1} END{exit !f}' "$NF_PERSON"; } \
       || { [ -f "$STATE" ] && awk -F'\t' '$2=="아는낱말"{f=1} END{exit !f}' "$STATE"; }; then
      echo "  이미 한 번 물었습니다 — 설계상 «한 번만» 묻습니다(design/여정.md A-2)."
      echo "  지금 사전은 「풀어쓸말」로 봅니다."
      exit 0
    fi
    echo
    echo "── 사용자에게 이렇게 여쭙니다 ──────────────────────"
    echo
    echo "  아시는 낱말에 표시해 주세요. 하나도 몰라도 괜찮습니다 —"
    echo "  표시 안 하신 낱말은 나올 때마다 제가 풀어서 말하겠습니다."
    echo
    python3 "$_LUF" --낱말 | awk '{printf "    · %s\n", $0}'
    echo
    echo "  (답을 들으면 「아는낱말」로 적습니다 — 하나도 없으면 빈 채로 적습니다)"
    echo
    ;;

  아는낱말)
    _LUF="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)/lint_user_facing.py"
    ASKED=$(python3 "$_LUF" --낱말 | tr '\n' ' ')
    shift || true
    KNOWN=""
    for w in "$@"; do
      case " $ASKED " in
        *" $w "*) KNOWN="${KNOWN}${KNOWN:+ }$w" ;;
        *) echo "  ⛔ 물어본 낱말이 아닙니다: 「$w」" >&2
           echo "     물어본 것: $ASKED" >&2; exit 1 ;;
      esac
    done
    mkdir -p "$(dirname "$NF_PERSON")"
    printf '%s\t아는낱말\t%s\t%s\t\t\n' "$(date +%F)" "$KNOWN" "$ASKED" >> "$NF_PERSON"
    if [ -z "$KNOWN" ]; then
      echo "  알겠습니다. 나오는 낱말은 나올 때마다 풀어서 말씀드리겠습니다."
    else
      echo "  알겠습니다. 표시 안 하신 낱말은 나올 때마다 풀어서 말씀드리겠습니다."
    fi
    ;;

  아는말인가)
    W="${2:?어느 낱말인가}"
    if cat "${NF_PERSON:-/dev/null}" "$STATE" 2>/dev/null | awk -F'\t' -v w="$W" '
         $2=="아는낱말"{n=split($3,a," "); for(i=1;i<=n;i++) if(a[i]==w) f=1}
         $2=="낱말올림" && $3==w {f=1} END{exit !f}'; then
      exit 0
    fi
    exit 1
    ;;

  풀어쓸말)
    _LUF="$(cd "$NF_PYDIR/../tools" 2>/dev/null && pwd)/lint_user_facing.py"
    if ! cat "${NF_PERSON:-/dev/null}" "$STATE" 2>/dev/null | awk -F'\t' '$2=="아는낱말"{f=1} END{exit !f}'; then
      echo "  ⚠️ 아직 안 물어봤습니다 — 「낱말묻기」가 먼저입니다"
      echo "     (이건 「풀어 쓸 말이 없다」가 아니라 「안 물어봤다」입니다)"
      exit 0
    fi
    STATE="$STATE" PERSON="${NF_PERSON:-}" python3 -I - "$_LUF" <<'PYEOF'
import os, subprocess, sys
rows = []
for _p in [os.environ.get("PERSON"), os.environ.get("STATE")]:
    if _p and os.path.exists(_p):
        rows += [l.rstrip("\n").split("\t") for l in open(_p, encoding="utf-8") if "\t" in l]
known = set()
asked = []
for r in rows:
    if r[1] == "아는낱말":
        known |= set(r[2].split())
        asked = r[3].split()
    elif r[1] == "낱말올림":
        known.add(r[2])
pairs = [l.split("\t") for l in subprocess.run(
    [sys.executable, sys.argv[1], "--낱말전부"], capture_output=True, text=True).stdout.splitlines() if l]
need = [show for _m, show in pairs if show not in known]
print("  풀어 쓸 말 %d개 (아시는 것 %d개는 그대로 씁니다)" % (len(need), len(known)))
print("  " + " · ".join(need))
PYEOF
    ;;

  낱말올림)
    W="${2:?어떤 낱말을 쓰셨나}"
    if cat "${NF_PERSON:-/dev/null}" "$STATE" 2>/dev/null | awk -F'\t' -v w="$W" '
         $2=="아는낱말"{n=split($3,a," "); for(i=1;i<=n;i++) if(a[i]==w) f=1} END{exit !f}'; then exit 0; fi
    mkdir -p "$(dirname "$NF_PERSON")"
    printf '%s\t낱말올림\t%s\t%s\t\t\n' "$(date +%F)" "$W" "${3:-}" >> "$NF_PERSON"
    echo "$W"
    exit 0
    ;;

  사전예방)
    PREP="${2:?다음 단계에서 사용자가 하실 일 — 미리 아시면 준비가 되는 것}"
    APPLY="${3:?지금 신청해 두면 좋은 것 — 정말 없으면 그대로: 없음}"

    NINE_N="진단 기획 검증 설계 개발 확인 출시 수정 출시후"
    CUR=$(awk -F'\t' '$2=="단계"{v=$3} END{print v}' "$STATE" 2>/dev/null)
    IDX=""
    if [ -n "$CUR" ]; then
      IDX=$(awk -F'\t' -v l="$CUR" '$1==l{print $2; exit}' "$(dirname "$STATE")/stage-map.tsv" 2>/dev/null)
      [ -n "$IDX" ] || IDX=$(printf '%s' "$CUR" | awk '{ if (match($0,/^[ ]*[0-9]/)) { gsub(/[^0-9].*$/,""); print } }')
    fi
    NEXT=""
    case "$IDX" in
      ''|*[!0-9]*) ;;
      *) [ "$IDX" -lt 8 ] && NEXT=$(echo "$NINE_N" | cut -d' ' -f$((IDX+2))) ;;
    esac

    printf '%s\t사전예방\t%s\t%s\t%s\t\n' "$(date +%F)" "${NEXT:-}" "$PREP" "$APPLY" >> "$STATE"
    if [ "$APPLY" != "없음" ]; then
      X="지금 신청해 두면 좋은 것 — $APPLY"
      awk -F'\t' -v x="$X" '$2=="남은것" && $3==x{f=1} END{exit !f}' "$STATE" 2>/dev/null \
        || printf '%s\t남은것\t%s\t%s\t\t절차\n' "$(date +%F)" "$X" "${CUR:-}" >> "$STATE"
    fi

    echo
    if [ -n "$NEXT" ]; then echo "  다음은 「$NEXT」입니다"
    else echo "  다음 단계가 아직 정해지지 않았습니다 — 지금 단계를 9단계에 연결해 주시면 말씀드립니다"; fi
    echo "  거기서 $PREP"
    if [ "$APPLY" = "없음" ]; then
      echo "  지금 미리 신청해 둘 것은 없습니다."
    else
      echo "  그리고 지금 신청해 두면 좋은 것이 있습니다: $APPLY"
      echo "  ⭐ 신청하는 것과 만드는 것은 «같이» 굴러갑니다 — 기다리는 동안 개발이 멈추지 않습니다."
    fi
    echo
    ;;
esac
