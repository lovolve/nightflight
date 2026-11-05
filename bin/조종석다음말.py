#!/usr/bin/env python3
"""턴 끝에 적어 둔 조종석 안내를 다음 말을 받을 때 건넨다. bin/조종석다음말.sh 가 부른다."""
import json, os, sys

if sys.argv[1:] == ["--폴더"]:
    try:
        print(str(json.load(sys.stdin).get("cwd") or ""))
    except (ValueError, AttributeError):
        pass
    sys.exit(0)
자리 = sys.stdin.read().strip()
파일 = os.path.join(자리, "board.다음말")
try:
    with open(파일, encoding="utf-8") as f:
        글 = json.load(f)["hookSpecificOutput"]["additionalContext"]
    os.remove(파일)
except (OSError, ValueError, KeyError, TypeError):
    sys.exit(0)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext":
                  글 + "\n같은 메시지에 얹을 수 있는 것은 같은 메시지에 얹으십시오."}}, ensure_ascii=False))
