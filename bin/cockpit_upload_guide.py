#!/usr/bin/env python3
"""조종석 자료를 올리라는 턴 끝 안내를 만든다. bin/board_push.sh 가 부른다."""
import json, sys
url, changed, root, here, st, pagenew = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
others = sys.argv[7] if len(sys.argv) > 7 else ""
page = ("  ⓪ 조종석 «화면 판»이 새것입니다 — Artifact publish · url " + url + " · file_path \"" + st + "/cockpit.html\" "
        "(그 대화에서 처음 올리면 거절되고 지금 판을 보여 줍니다 — 같은 플러그인의 옛 판이면 그대로 다시 올리면 됩니다) → "
        "`" + here + "/board_push.sh --화면올렸다 " + root + "`\n") if pagenew == "1" else ""
print(json.dumps({"hookSpecificOutput": {
  "hookEventName": "Stop",
  "additionalContext": page + (
    "조종석 자료가 바뀌었는데 아직 안 올라갔습니다 — 달라진 칸: " + changed + "\n"
    "이번 답에서 다른 도구를 부를 때 같은 메시지에 얹어 올리십시오. 따로 호출을 늘리지 않습니다. 다른 도구를 안 부르면 이 차례만 하십시오.\n"
    "  ① ArtifactData list · url " + url + " · collection \"state\" "
    "— 칸마다 version 을 받습니다(없는 칸은 새로 만드는 것이라 version 을 안 붙입니다)\n"
    "  ①-1 ①의 목록에 \"marked\" 칸이 있으면 — 사용자가 테스트 단계에서 누른 표시입니다. ArtifactData get 으로 열어 items 마다 "
    "`" + here + "/ledger.sh 조종석표시 <기능> <세부> <상태>` 를 돌리고 `" + here + "/ledger.sh 조종석준비` 를 돌리십시오. "
    "②에 features 칸을 더하고, 같은 묶음에 {op:\"delete\", collection:\"state\", doc_id:\"marked\"} 를 넣으십시오(화면이 옛 상태로 돌아가지 않게 함께 처리합니다).\n"
    "  ② ArtifactData batch · 같은 url · 달라진 칸마다 "
    "{op:\"set\", collection:\"state\", doc_id:<칸이름>, "
    "file_path:\"" + st + "/board/<칸이름>.json\", if_version:<①에서 받은 값>}\n"
    "  ③ ①의 목록에 \"pressed\" 칸이 있으면 — 사용자가 조종석에서 「이미 했어요」를 "
    "누르신 것입니다. ArtifactData get 으로 열어 값마다 "
    "`" + here + "/ledger.sh 앱설정 이미한것 <값> 화면` 을 돌리고, 끝나면 그 칸을 "
    "ArtifactData delete 로 지우십시오(지워야 다음에 또 안 옮깁니다).\n"
    "  ④ 올라갔으면 `" + here + "/board_push.sh --올렸다 " + root + "` 를 돌리십시오. "
    "올리시면 다음에 바뀔 때 또 알려 드립니다 — 조종석이 실시간으로 따라옵니다.\n"
    + "" +
    "⛔ 올릴 수 없는 자리(그 도구가 없음)라면 — 클로드가 아닌 도구에서는 흔합니다 — "
    "사용자에게 **파일로 된 조종석**을 알려 드리고 넘어가십시오: " + st + "/cockpit.html "
    "(턴 끝마다 다시 지어집니다. 실시간이 아니라 «그때 적은 판»입니다). 올리지 않으면 이 대화에서는 다시 안 막습니다."
  )}}, ensure_ascii=False))
