#!/usr/bin/env python3
"""조종석 자료를 올리라는 턴 끝 안내를 만든다. bin/board_push.sh 가 부른다."""
import json, sys
url, changed, root, here, st, pagenew = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
others = sys.argv[7] if len(sys.argv) > 7 else ""
page = ("⓪ 화면 판이 새것: Artifact publish(url " + url + ", file_path \"" + st + "/internal/board_page.html\") — 처음엔 거절되고 지금 판을 보여 주니 그대로 다시 올림 → "
        "`" + here + "/board_push.sh --화면올렸다 " + root + "`\n") if pagenew == "1" else ""
import os
if os.environ.get("NF_GUIDE_SHORT") == "1":
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext":
        "조종석이 멈춰 있습니다 — 달라진 칸: " + changed + "\n"
        "올릴 수 있으면: ArtifactData list(url " + url + ", collection \"state\")로 version 을 받고, "
        "batch 로 달라진 칸마다 set(file_path \"" + st + "/board/<칸이름>.json\", if_version) 한 뒤 "
        "`" + here + "/board_push.sh --올렸다 " + root + "` 를 돌리십시오. 올릴 도구가 없으면 이 글은 넘기십시오."}}, ensure_ascii=False))
    sys.exit(0)
print(json.dumps({"hookSpecificOutput": {
  "hookEventName": "Stop",
  "additionalContext": page + (
    "조종석에 안 올라간 칸: " + changed + " — 다른 도구를 부를 때 같은 메시지에 얹어 올리십시오.\n"
    "① ArtifactData list(url " + url + ", collection \"state\")로 칸마다 version 을 받습니다.\n"
    "  목록에 marked 가 있으면: get → items 마다 `" + here + "/ledger.sh 조종석표시 <기능> <세부> <상태>` → `" + here + "/ledger.sh 조종석준비` → ②에 features 와 marked delete 를 함께 넣습니다.\n"
    "② batch: 달라진 칸마다 set(doc_id <칸이름>, file_path \"" + st + "/board/<칸이름>.json\", if_version — 새 칸이면 빼기).\n"
    "  목록에 pressed 가 있으면: get → 값마다 `" + here + "/ledger.sh 앱설정 이미한것 <값> 화면` → pressed 를 delete.\n"
    "③ `" + here + "/board_push.sh --올렸다 " + root + "`\n"
    + "" +
    "올릴 도구가 없으면 사용자에게 파일 조종석 " + st + "/cockpit.html 을 알리고 넘어가십시오(실시간이 아닌 그때 판)."
  )}}, ensure_ascii=False))
