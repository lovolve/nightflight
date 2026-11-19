#!/usr/bin/env python3
"""대화가 시작될 때 조종석 서버를 켜고, AI에게 «첫 답에서 오른쪽 브라우저 칸에 조종석을 열라»고 알린다(SessionStart)."""
import json
import os
import subprocess
import sys
from pathlib import Path

여기 = Path(__file__).resolve().parent
try:
    _입력 = json.load(sys.stdin) or {}
except Exception:
    _입력 = {}
sys.path.insert(0, str(여기))
sys.path.insert(0, str(여기.parent / "tools"))


def main() -> int:
    if os.environ.get("CLAUDE_CODE_ENTRYPOINT") != "claude-desktop":
        return 0
    if _입력.get("source") == "compact":
        return 0
    from registered import 등록된_대화인가
    if not 등록된_대화인가(_입력):
        return 0
    import _root
    뿌리 = _root.root()
    import cockpit_file
    if not (cockpit_file.기록집(뿌리) / "board").is_dir():
        return 0
    try:
        r = subprocess.run([sys.executable, "-I", str(여기 / "cockpit_server.py"), str(뿌리), "--뒤에서"],
                           capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return 0
    주소 = (r.stdout or "").strip().splitlines()[:1]
    if r.returncode != 0 or not 주소 or not 주소[0].startswith("http://127.0.0.1:"):
        return 0
    try:
        영어 = subprocess.run(["bash", "-c", '. "$1" >/dev/null 2>&1; nf_lang', "_", str(여기 / "project-root.sh")],
                            capture_output=True, text=True, timeout=5).stdout.strip() == "en"
    except (OSError, subprocess.SubprocessError):
        영어 = False
    if 영어:
        글 = ("Nightflight cockpit: in your first reply of this conversation, call mcp__Claude_Browser__preview_start once with "
             f'url "{주소[0]}" to open the cockpit in the right-hand browser pane. It updates itself every few seconds. '
             "Do not take a screenshot of it. If it fails, tell the user they can type /cockpit to open it.")
    else:
        글 = (f"야간비행 조종석: 이 대화의 첫 답에서 mcp__Claude_Browser__preview_start 를 url «{주소[0]}» 로 한 번 부르십시오 — "
             "오른쪽 브라우저 칸에 조종석이 열리고 몇 초마다 저절로 바뀝니다. 화면을 찍지는 마십시오. "
             "열리지 않으면 사용자에게 입력창에 /cockpit 을 입력하면 열린다고 알려 주십시오.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": 글}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
