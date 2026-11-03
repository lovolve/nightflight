LC_ALL=C; export LC_ALL
case "$KIND" in

  등록)
    if nf_not_product_root; then
      echo "  지금 열린 곳($(basename "$NF_ROOT"))은 제품 폴더가 아니라서 여기에는 등록하지 않습니다. 제품 폴더를 새로 만들어 거기에 등록합니다."
      echo "  [모델] 이 순서로 하십시오:"
      echo "  [모델]  1) 만들 제품의 이름을 묻습니다. 그 이름이 폴더 이름이 됩니다(영문 소문자 · 숫자 · 하이픈). 등록은 폴더 자리로 묶여 나중에 이름을 바꾸기 어렵다고 한 줄 덧붙입니다."
      echo "  [모델]  2) 홈 폴더 아래에 그 이름으로 폴더를 만듭니다. 이미 있고 비어 있지 않으면, 이미 만들던 제품인지 묻고 아니면 다른 이름을 받습니다."
      echo "  [모델]  3) 그 폴더를 등록합니다: NIGHTFLIGHT_PROJECT_DIR=<새 폴더의 절대 경로> \"\${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh\" 등록"
      echo "  [모델]  4) 대화를 그 폴더로 옮깁니다. 작업 폴더를 옮기는 도구(change_directory)가 있으면(클로드 앱) 그것으로 옮기고,"
      echo "  [모델]     «폴더를 옮겼습니다. 한마디 더 하시면 그 폴더에서 이 컴퓨터 점검부터 시작합니다» 한 줄로 끝냅니다 — 정해진 작업은 옮겨진 다음 턴에 합니다."
      echo "  [모델]     그 도구가 없으면(터미널) 그 폴더로 클로드를 다시 열라고 알리고, 붙여 넣을 한 줄 cd <새 폴더> && claude 를 줍니다 — 다시 열면 첫 대화로 점검이 시작됩니다."
      exit 0
    fi
    _nf_again=""
    if awk -F'\t' -v r="$NF_ROOT" '$2=="프로젝트"&&$3==r{f=1} END{exit !f}' "$NF_PERSON" 2>/dev/null; then
      _nf_again=1
      echo "  이 폴더는 이미 야간비행에 등록돼 있습니다. 이용권과 제품등록 상태만 새로 읽습니다."
      if [ "$(nf_conv_scope "$NF_ROOT")" = 대화 ] && [ -n "$(nf_conv_id)" ] && ! nf_conv_ok_at "$NF_ROOT"; then
        nf_conv_add "$NF_ROOT" "$(nf_conv_id)" && echo "  이 대화도 야간비행 대화로 붙였습니다 — 기록과 조종석은 그대로 이어집니다."
      fi
    else
      grep -q $'\t등록\t' "$STATE" 2>/dev/null || printf '%s\t등록\t%s\t\t\t\n' "$(date +%F)" "$(basename "$NF_ROOT" | tr -d '\t\r\n')" >> "$STATE"
      mkdir -p "$(dirname "$NF_PERSON")" 2>/dev/null
      printf '%s\t프로젝트\t%s\t\t\t\n' "$(date +%F)" "$(printf '%s' "$NF_ROOT" | tr -d '\t\r\n')" >> "$NF_PERSON" 2>/dev/null
      echo "  이 폴더를 야간비행 프로젝트로 등록했습니다."
      if [ -n "$(nf_conv_id)" ]; then
        nf_conv_add "$NF_ROOT" "$(nf_conv_id)" 2>/dev/null || true
        echo "  야간비행은 이 대화에서만 움직입니다. 같은 폴더의 다른 대화(메일 · 조사 같은 것)에는 끼어들지 않습니다."
        echo "  [모델] 진단 전에 사용자에게 한 번만 물으십시오: «이 폴더에서 여는 모든 대화에도 야간비행을 켤까요? 기본은 이 대화만입니다.» 켜자고 하시면 ledger.sh 등록범위 폴더."
      else
        nf_conv_add "$NF_ROOT" '*' 2>/dev/null || true
      fi
    fi
    if nf_dev 2>/dev/null && [ -n "${NF_KAN_ANSWER+x}" ]; then _KAN="$NF_KAN_ANSWER"
    else _KAN="$(bash "$NF_PYDIR/열쇠.sh" 칸읽기 2>/dev/null || true)"
      [ -n "$_KAN" ] && printf '%s\n' "$_KAN" > "$NF_HOME/이용권.json" 2>/dev/null; fi
    _BID="$(nf_productid 2>/dev/null | tr -d '[:space:]')"
    KAN="$_KAN" BID="$_BID" KEYSH="$NF_PYDIR/열쇠.sh" PERSON="$NF_PERSON" python3 -I "$NF_PYDIR/등록칸.py"
    [ -n "$_nf_again" ] && exit 0
    _NAME="$(python3 -I "$NF_PYDIR/이름후보.py" "$NF_ROOT" 2>/dev/null | head -1 | tr -d '\t\r')"
    [ -n "$_NAME" ] && echo "  [모델] 앱 설정에서 찾은 제품 이름 후보: «$_NAME» — 사용자에게 «제품 이름을 «$_NAME»(으)로 할까요?» 묻고, 그렇다고 하시면 ledger.sh 앱설정 앱이름 \"<이름>\" 사용자 로 적으십시오."
    echo "  [모델] 지금 바로 이 순서로 하십시오(사용자에게는 등록했다는 것과 칸 안내만 한 줄씩 전합니다):"
    echo "  [모델]  1) 0-진단 스킬로 이 컴퓨터를 점검하고(질문 없이), 본 것을 한 줄로 말한 뒤 ledger.sh 단계 \"0. 진단\" 으로 적습니다."
    echo "  [모델]  2) 이미 만들던 제품이면(커밋·화면 파일·기획 메모가 있으면) 가져오기 스킬로 조종석 칸을 코드에서 채웁니다."
    echo "  [모델]  3) 아직 아무것도 안 만든 제품이면 진단 뒤 «기획부터 하자»고 제안하고, 받아들이면 1-기획 스킬로 갑니다."
    echo "  [모델]  4) 이 턴이 끝나면 조종석을 만들라는 안내가 뜹니다 — 그대로 따르십시오."
    echo "  [모델]  ⭐ 큰 단계(진단 · 가져오기 · 단계 하나)마다 과정을 보이십시오:"
    echo "  [모델]     시작할 때 대화창에 «지금 ~하고 있습니다» 한 줄 + ledger.sh 하는중 \"<그 말>\" --화면 \"<그 말>\" (조종석의 «지금 하는 일» 줄이 됩니다)"
    echo "  [모델]     끝나면 대화창에 «~이 끝났습니다» 한 줄 + ledger.sh 조종석지금 (조종석이 있으면 그 칸을 바로 올립니다 · 작은 걸음마다는 부르지 않습니다)"
    ;;

  등록범위)
    _nf_cf="$NF_HOME/대화.tsv"
    case "${2:-}" in
      폴더) nf_conv_add "$NF_ROOT" '*' && echo "  이 폴더에서 여는 모든 대화에서 야간비행이 움직입니다." ;;
      대화) [ -n "$(nf_conv_id)" ] && nf_conv_add "$NF_ROOT" "$(nf_conv_id)"
            awk -F'\t' -v r="$NF_ROOT" '!($1==r&&$2=="*")' "$_nf_cf" > "$_nf_cf.$$" 2>/dev/null && mv -f "$_nf_cf.$$" "$_nf_cf"
            echo "  야간비행은 「야간비행」이라고 하신 대화에서만 움직입니다." ;;
      *) echo "  지금: $( [ "$(nf_conv_scope "$NF_ROOT")" = 폴더 ] && echo '이 폴더의 모든 대화' || echo '야간비행이라고 하신 대화만')"
         echo "  [모델] 바꾸려면 ledger.sh 등록범위 폴더 또는 ledger.sh 등록범위 대화" ;;
    esac
    ;;

esac
