LC_ALL=C; export LC_ALL
case "$KIND" in

  등록)
    if [ -n "${_nf_was_reg:-}" ]; then
      echo "  이 폴더는 이미 야간비행에 등록돼 있습니다."
      echo "  [모델] 다시 등록하지 않습니다. 지금 단계와 남은 일은 ledger.sh show 와 조종석에서 보십시오."
      exit 0
    fi
    printf '%s\t등록\t%s\t\t\t\n' "$(date +%F)" "$(basename "$NF_ROOT" | tr -d '\t\r\n')" >> "$STATE"
    mkdir -p "$(dirname "$NF_PERSON")" 2>/dev/null
    printf '%s\t프로젝트\t%s\t%s\t\t\n' "$(date +%F)" "$(printf '%s' "$NF_ROOT" | tr -d '\t\r\n')" "$(nf_bundleid 2>/dev/null | tr -d '[:space:]')" >> "$NF_PERSON" 2>/dev/null
    echo "  이 폴더를 야간비행 프로젝트로 등록했습니다."
    if nf_dev 2>/dev/null && [ -n "${NF_KAN_ANSWER+x}" ]; then _KAN="$NF_KAN_ANSWER"
    else _KAN="$(bash "$NF_PYDIR/열쇠.sh" 칸읽기 2>/dev/null || true)"
      [ -n "$_KAN" ] && printf '%s\n' "$_KAN" > "$NF_HOME/이용권.json" 2>/dev/null; fi
    _BID="$(nf_bundleid 2>/dev/null | tr -d '[:space:]')"
    KAN="$_KAN" BID="$_BID" KEYSH="$NF_PYDIR/열쇠.sh" PERSON="$NF_PERSON" python3 -I "$NF_PYDIR/등록칸.py"
    echo "  [모델] 지금 바로 이 순서로 하십시오(사용자에게는 등록했다는 것과 칸 안내만 한 줄씩 전합니다):"
    echo "  [모델]  1) 0-진단 스킬로 이 컴퓨터를 점검하고(질문 없이), 본 것을 한 줄로 말한 뒤 ledger.sh 단계 \"0. 진단\" 으로 적습니다."
    echo "  [모델]  2) 이미 만들던 제품이면(커밋·화면 파일·기획 메모가 있으면) 가져오기 스킬로 조종석 칸을 코드에서 채웁니다."
    echo "  [모델]  3) 아직 아무것도 안 만든 제품이면 진단 뒤 «기획부터 하자»고 제안하고, 받아들이면 1-기획 스킬로 갑니다."
    echo "  [모델]  4) 이 턴이 끝나면 조종석을 만들라는 안내가 뜹니다 — 그대로 따르십시오."
    echo "  [모델]  ⭐ 큰 단계(진단 · 가져오기 · 단계 하나)마다 과정을 보이십시오:"
    echo "  [모델]     시작할 때 대화창에 «지금 ~하고 있습니다» 한 줄 + ledger.sh 하는중 \"<그 말>\" --화면 \"<그 말>\" (조종석의 «지금 하는 일» 줄이 됩니다)"
    echo "  [모델]     끝나면 대화창에 «~이 끝났습니다» 한 줄 + ledger.sh 조종석지금 (조종석이 있으면 그 칸을 바로 올립니다 · 작은 걸음마다는 부르지 않습니다)"
    ;;

esac
