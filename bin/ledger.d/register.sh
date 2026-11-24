LC_ALL=C; export LC_ALL
case "$KIND" in

  등록)
    if [ "$(nf_lang)" = en ]; then _nf_en=1; else _nf_en=""; fi
    _nf_t() { if [ -n "$_nf_en" ]; then printf '%s\n' "$2"; else printf '%s\n' "$1"; fi; }
    [ -n "$_nf_en" ] && echo "  [모델] LANGUAGE: This user reads English. Write every reply, question, and summary in English, and address the user as \"you\" (no titles). For every Nightflight skill, read the en.md next to its SKILL.md and follow it instead of the Korean SKILL.md. Command output and guidance may be in Korean: read it, but never show Korean to the user unless they wrote it."
    if nf_not_product_root; then
      _nf_t "  지금 열린 곳($(basename "$NF_ROOT"))은 제품 폴더가 아니라서 여기에는 등록하지 않습니다. 제품 폴더를 새로 만들어 거기에 등록합니다." \
            "  The folder open now ($(basename "$NF_ROOT")) is not a product folder, so Nightflight will not register it. It will create a new product folder and register that instead."
      echo "  [모델] 이 순서로 하십시오:"
      _nf_cands="$(for _d in "$HOME" "$HOME/Desktop" "$HOME/Documents" "$HOME/Developer" "$HOME/Projects" "$HOME/projects" "$HOME/code" "$HOME/dev" "$HOME/src" "$HOME/Library/Mobile Documents/com~apple~CloudDocs"; do
          [ -d "$_d" ] && find "$_d" -mindepth 2 -maxdepth 3 -name .git -prune -print 2>/dev/null; done \
        | while IFS= read -r _g; do _r="$(dirname "$_g")"; printf '%s\t%s\n' "$(stat -f %m "$_g" 2>/dev/null || stat -c %Y "$_g" 2>/dev/null || echo 0)" "$_r"; done \
        | sort -s -rn -k1,1 | cut -f2 | awk '!s[tolower($0)]++' | head -5)"
      echo "  [모델]  0) 먼저 이미 만들던 제품이 있는지 묻습니다(선택형 질문 도구가 있으면 그것으로). 있으면 그 폴더를 고르게 하고 2)를 건너뛰어 그 폴더를 3)처럼 등록합니다."
      [ -n "$_nf_cands" ] && printf '%s\n' "$_nf_cands" | sed 's/^/  [모델]     후보(최근에 고친 순): /'
      echo "  [모델]  1) 새로 만드는 제품이면 만들 제품의 이름을 묻습니다. 그 이름이 폴더 이름이 됩니다(영문 소문자 · 숫자 · 하이픈). 등록은 폴더 자리로 묶여 나중에 이름을 바꾸기 어렵다고 한 줄 덧붙입니다."
      echo "  [모델]  2) 홈 폴더 아래에 그 이름으로 폴더를 만듭니다. 이미 있고 비어 있지 않으면, 이미 만들던 제품인지 묻고 아니면 다른 이름을 받습니다."
      echo "  [모델]  3) 그 폴더를 등록합니다: NIGHTFLIGHT_PROJECT_DIR=<새 폴더의 절대 경로> \"\${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh\" 등록"
      echo "  [모델]  4) 대화를 그 폴더로 옮깁니다. 작업 폴더를 옮기는 도구(change_directory)가 있으면(클로드 앱) 그것으로 옮기고,"
      echo "  [모델]     «폴더를 옮겼습니다. 한마디 더 하시면 그 폴더에서 이 컴퓨터 점검부터 시작합니다» 한 줄로 끝냅니다 — 정해진 작업은 옮겨진 다음 턴에 합니다."
      echo "  [모델]     그 도구가 없으면(터미널) 그 폴더로 클로드를 다시 열라고 알리고, 붙여 넣을 한 줄 cd <새 폴더> && claude 를 줍니다 — 다시 열면 첫 대화로 점검이 시작됩니다."
      exit 0
    fi
    case "$NF_ROOT" in /var/folders/*|/private/var/folders/*)
      case "$(mkdir -p "$NF_HOME" 2>/dev/null; cd "$NF_HOME" 2>/dev/null && pwd -P)" in /var/folders/*|/private/var/folders/*) _nf_tmphome=1 ;; *) _nf_tmphome="" ;; esac
      if [ -z "$_nf_tmphome" ]; then
        _nf_t "  지금 열린 곳은 시스템 임시 폴더라서 야간비행에 등록하지 않았습니다. 제품 폴더에서 다시 말씀해 주십시오." \
              "  The folder open now is a system temporary folder, so Nightflight did not register it. Try again from a product folder."
        exit 0
      fi ;;
    esac
    _nf_again=""
    if awk -F'\t' -v r="$NF_ROOT" '$2=="프로젝트"&&$3==r{f=1} END{exit !f}' "$NF_PERSON" 2>/dev/null; then
      _nf_again=1
      _nf_t "  이 폴더는 이미 야간비행에 등록돼 있습니다. 이용권과 제품등록 상태만 새로 읽습니다." \
            "  This folder is already registered with Nightflight. Refreshing only your plan and product slot status."
      _nf_ss="$(printf '{"source":"startup","session_id":"%s"}' "${NF_SESSION:-${CLAUDE_CODE_SESSION_ID:-}}" | NIGHTFLIGHT_PROJECT_DIR="$NF_ROOT" bash "$NF_PYDIR/session_start.sh" 2>/dev/null \
        | python3 -I -c 'import json,sys
try: print(json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"])
except Exception: pass' 2>/dev/null)"
      if [ -n "$_nf_ss" ]; then
        echo "  [모델] 아래가 새 대화가 받는 시작 안내입니다 — 이것대로 일하십시오."
        printf '%s\n' "$_nf_ss" | sed 's/^/  [모델] /'
      else
        echo "  [모델] 일하기 전에 ledger.sh 결정목록 · ledger.sh 시도목록 · ledger.sh 영향목록 을 읽으십시오."
      fi
    else
      grep -q $'\t등록\t' "$STATE" 2>/dev/null || printf '%s\t등록\t%s\t\t\t\n' "$(date +%F)" "$(basename "$NF_ROOT" | tr -d '\t\r\n')" >> "$STATE"
      mkdir -p "$(dirname "$NF_PERSON")" 2>/dev/null
      printf '%s\t프로젝트\t%s\t\t\t\n' "$(date +%F)" "$(printf '%s' "$NF_ROOT" | tr -d '\t\r\n')" >> "$NF_PERSON" 2>/dev/null
      _nf_t "  이 폴더를 야간비행 프로젝트로 등록했습니다." "  This folder is now registered as a Nightflight project."
      _OLDB="$(dirname "$(dirname "$BOARD")")/board.url"
      if [ -f "$BOARD" ] || [ -f "$_OLDB" ]; then
        git -c core.fsmonitor=false -C "$NF_ROOT" rm --cached -q --ignore-unmatch -- "$BOARD" "$_OLDB" >/dev/null 2>&1 || true
        rm -f "$BOARD" "$_OLDB"
        _nf_t "  이 폴더에 들어 있던 조종석 주소를 지웠습니다. 이 제품의 조종석을 새로 만듭니다." \
              "  Removed the cockpit address that came with this folder. A new cockpit will be made for this product."
      fi
      mkdir -p "$NF_HOME" 2>/dev/null; nf_lang > "$NF_HOME/language" 2>/dev/null || true
      _nf_t "  야간비행은 이 폴더에서 여는 모든 대화에서 움직입니다." \
            "  Nightflight runs in every chat you open in this folder."
    fi
    if nf_dev 2>/dev/null && [ -n "${NF_KAN_ANSWER+x}" ]; then _KAN="$NF_KAN_ANSWER"
    else _KAN="$(bash "$NF_PYDIR/license_key.sh" 칸읽기 2>/dev/null || true)"
      [ -n "$_KAN" ] && printf '%s\n' "$_KAN" > "$NF_HOME/license.json" 2>/dev/null; fi
    _BID="$(nf_productid 2>/dev/null | tr -d '[:space:]')"
    NFL="$(nf_lang)" KAN="$_KAN" BID="$_BID" KEYSH="$NF_PYDIR/license_key.sh" PERSON="$NF_PERSON" python3 -I "$NF_PYDIR/register_slots.py"
    [ -n "$_nf_again" ] && exit 0
    _NAME="$(python3 -I "$NF_PYDIR/name_candidates.py" "$NF_ROOT" 2>/dev/null | head -1 | tr -d '\t\r')"
    [ -n "$_NAME" ] && echo "  [모델] 앱 설정에서 찾은 제품 이름 후보: «$_NAME» — 사용자에게 «제품 이름을 «$_NAME»(으)로 할까요?»(영어 사용자에게는 영어로) 묻고, 그렇다고 하시면 ledger.sh 앱설정 앱이름 \"<이름>\" 사용자 로 적으십시오."
    echo "  [모델] 지금 바로 이 순서로 하십시오(사용자에게는 등록했다는 것과 칸 안내만 한 줄씩 전합니다):"
    echo "  [모델]  1) 조종석을 먼저 만듭니다: $NF_PYDIR/board_push.sh --지금만들기 \"$NF_ROOT\" 를 돌려 나온 차례대로 하십시오(올릴지 묻는 것부터)."
    echo "  [모델]  2) 0-진단 스킬로 이 컴퓨터를 점검하고(질문 없이), 본 것을 한 줄로 말한 뒤 ledger.sh 단계 \"0. 진단\" 으로 적습니다."
    echo "  [모델]  3) 이미 만들던 제품이면(커밋·화면 파일·기획 메모가 있으면) 가져오기 스킬대로 nightflight:importer 에이전트(소넷 모델 · 사용량을 덜 씀)에게 맡겨 조종석 칸을 코드에서 채우고, 끝나면 ledger.sh 조종석지금 으로 올립니다."
    echo "  [모델]  4) 아직 아무것도 안 만든 제품이면 진단 뒤 «기획부터 하자»고 제안하고, 받아들이면 1-기획 스킬로 갑니다."
    echo "  [모델]  ⭐ 물을 것(대화 범위 · 제품 이름 · 기획 제안 · 조종석 올리기)은 한 번에 하나씩 묻습니다. 선택형 질문 도구가 있으면 그것으로 묻고 답을 받은 뒤 다음으로 갑니다. 답 끝에 질문을 여럿 늘어놓지 않습니다."
    echo "  [모델]  ⭐ 큰 단계(진단 · 가져오기 · 단계 하나)마다 과정을 보이십시오:"
    echo "  [모델]     시작할 때 대화창에 «지금 ~하고 있습니다» 한 줄 + ledger.sh 하는중 \"<그 말>\" --화면 \"<그 말>\" (조종석의 «지금 하는 일» 줄이 됩니다) — 1분 넘게 걸리면 --예상 \"3~5분\" 을 붙이고 «다른 일을 하셔도 됩니다»라고 말합니다"
    echo "  [모델]     하는 동안 찾거나 끝낸 것마다 대화창에 한 줄 + ledger.sh 찾음 \"<그 줄>\" (조종석 «지금 작업» 밑에 쌓입니다 · data/tool_use.md «1분 넘게 걸리는 일»)"
    echo "  [모델]     끝나면 대화창에 «~이 끝났습니다» 한 줄 + ledger.sh 조종석지금 (조종석이 있으면 그 칸을 바로 올립니다 · 작은 걸음마다는 부르지 않습니다)"
    _nf_rules="$(printf '{}' | NF_RULES_ONLY=1 NF_STATE="$NF_STATE" HERE="$NF_PYDIR" NF_CALL="$(awk -F'\t' '$2=="호칭"{v=$3; s=1} END{if (s) print v}' "$NF_PERSON" 2>/dev/null | tr -d '\000-\037\177')" python3 -I "$NF_PYDIR/session_start.py" 2>/dev/null)"
    [ -n "$_nf_rules" ] && printf '\n  [모델] 이 대화는 등록 전에 열려 대화 시작 안내를 받지 못했습니다. 아래를 이 대화에서 지키십시오.\n%s\n' "$_nf_rules" | sed '3,$s/^/  [모델] /'
    ;;

esac
