#!/usr/bin/env python3
"""조종석을 처음 만들라는 턴 끝 안내를 만든다. bin/board_push.sh 가 부른다."""
import json, os, sys
root, here, st = sys.argv[1], sys.argv[2], sys.argv[3]
동의 = sys.argv[4] if len(sys.argv) > 4 else ""
영어 = os.environ.get("NFL") == "en"
묻는글 = ("«If you use the cockpit page, a copy of your records is uploaded to a private page in your Claude account. "
         "It includes your decisions, dead ends, feature progress, this computer's chip, operating system, memory and storage status, "
         "the names and stages of other products registered on this computer, the names of files kept out of GitHub, "
         "and the key names in your secrets file. Secret values are never uploaded. Upload it?» "
         "(Ask in English. Options: Upload / Don't upload.)\n") if 영어 else (
    "«조종석 화면을 쓰면 기록 사본이 클로드 계정의 비공개 페이지에 올라갑니다. "
    "올라가는 것은 정한 것, 막힌 길, 기능 진척, 이 컴퓨터의 칩·운영체제·메모리·저장공간 상태, "
    "이 컴퓨터에 등록한 다른 제품의 이름과 단계, 깃허브에 안 올리는 파일 이름, 비밀값 파일의 키 이름입니다. "
    "비밀값의 값은 올리지 않습니다. 올릴까요?»\n")
물음 = "" if 동의 == "네" else (
    "먼저 사용자에게 선택지로 한 번 물으십시오. 한 번 답하면 다시 묻지 않습니다.\n"
    + 묻는글 +
    "  · 올립니다 → `" + here + "/ledger.sh 조종석동의 네` 를 돌리고 아래 차례를 하십시오.\n"
    "  · 올리지 않습니다 → `" + here + "/ledger.sh 조종석동의 아니오` 를 돌리고, 파일로 된 조종석 "
    + st + "/cockpit.html 을 알려 드리십시오. 아래 차례는 하지 않습니다.\n\n")
print(json.dumps({"hookSpecificOutput": {
  "hookEventName": "Stop",
  "additionalContext": 물음 + (
    "이 프로젝트에는 아직 조종석이 없습니다 — " + ("올려도 된다고 하면 " if 물음 else "지금 ") + "만들어 주십시오(첫 대화에서 한 번).\n"
    "  ① Artifact publish · file_path \"" + st + "/internal/board_page.html\" · icon \"gauge\" · "
    "capabilities {\"db\":{}} · description \"" + ("Cockpit showing this product's stage and remaining work" if 영어 else "이 제품의 단계와 남은 일을 보여 주는 조종석") + "\"\n"
    "  ② 받은 주소를 등록합니다: `" + here + "/ledger.sh 조종석 \"<받은 주소>\"` → `" + here + "/board_push.sh --화면올렸다 " + root + "`\n"
    "  ③ " + st + "/board/ 에 칸(*.json)이 있으면 ArtifactData batch · 같은 주소 · 칸마다 "
    "{op:\"set\", collection:\"state\", doc_id:<칸이름>, file_path:<그 json 의 절대경로>} "
    "(새로 만드는 칸이라 version 을 안 붙입니다) → 끝나면 "
    "`" + here + "/board_push.sh --올렸다 " + root + "`. "
    "칸이 없으면 건너뜁니다 — 조종석이 「아직 기록 없음 · 첫 대화를 하면 채워집니다」로 보입니다.\n"
    "  ④ 조종석을 띄웁니다: Artifact open · url <받은 주소> (칸을 다 올린 뒤에 — 빈 판이 먼저 보이지 않게). "
    "열 수 없는 자리면 건너뜁니다.\n"
    "  ⑤ 사용자께 한 줄로 알려 드립니다: 조종석을 만들어 열었고 그 주소 — 옆 창에 두면 진행이 보입니다.\n"
    "⛔ 만들 수 없는 자리(그 도구가 없음 · 로그인 안 됨)라면 — 클로드가 아닌 도구에서는 흔합니다 — "
    "사용자께 **파일로 된 조종석**을 알려 드리십시오: " + st + "/cockpit.html "
    "(턴 끝마다 다시 지어집니다. 실시간은 아니고 «그때 적은 판»입니다). "
    "그리고 이 대화에서는 다시 안 막습니다."
  )}}, ensure_ascii=False))
