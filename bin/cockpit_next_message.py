#!/usr/bin/env python3
"""턴 끝에 적어 둔 조종석 안내를 다음 말을 받을 때 건넨다. bin/cockpit_next_message.sh 가 부른다."""
import json, os, sys

if sys.argv[1:] in (["--폴더"], ["--대화"]):
    try:
        print(str(json.load(sys.stdin).get("cwd" if sys.argv[1] == "--폴더" else "session_id") or "").replace("\n", ""))
    except (ValueError, AttributeError):
        pass
    sys.exit(0)
파일 = sys.stdin.read().strip()
try:
    with open(파일, encoding="utf-8") as f:
        글 = json.load(f)["hookSpecificOutput"]["additionalContext"]
    os.remove(파일)
except (OSError, ValueError, KeyError, TypeError):
    sys.exit(0)
if "board_push.sh --올렸다" in 글 and len(sys.argv) > 2 and sys.argv[1]:
    import subprocess
    _서버 = [sys.executable, "-I", os.path.join(sys.argv[2], "cockpit_server.py"), sys.argv[1]]
    _집 = os.path.realpath(os.path.expanduser("~"))
    _플러그인 = os.path.realpath(os.path.join(sys.argv[2], ".."))
    try:
        if subprocess.run(_서버 + ["--보이나"], capture_output=True, timeout=25).returncode == 0:
            sys.exit(0)
        if os.environ.get("CLAUDE_CODE_ENTRYPOINT") == "claude-desktop" and os.path.realpath(sys.argv[1]) not in (_집, _플러그인) \
                and subprocess.run(_서버 + ["--뒤에서"], capture_output=True, timeout=25).returncode == 0:
            sys.exit(0)
    except (OSError, subprocess.SubprocessError):
        pass
print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext":
                  글 + "\n같은 메시지에 얹을 수 있는 것은 같은 메시지에 얹으십시오."}}, ensure_ascii=False))
