#!/usr/bin/env python3
"""AI가 답을 기다리거나 승인을 물을 때 컴퓨터 알림을 띄운다(Notification 훅)."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

글들 = {"permission_prompt": "승인을 기다립니다", "idle_prompt": "답을 기다립니다"}
try:
    입력 = json.load(sys.stdin) or {}
    글 = 글들.get(str(입력.get("notification_type") or ""))
    상태 = {}
    try:
        상태 = json.loads((Path(os.environ.get("HOME") or Path.home()) / ".nightflight" / "기능안내.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    if 글 and not 상태.get("입력알림끔") and os.environ.get("CLAUDE_CODE_ENTRYPOINT") != "claude-desktop":
        if sys.platform == "darwin":
            subprocess.run(["osascript", "-e", f'display notification "{글}" with title "야간비행"'], capture_output=True, timeout=5)
        elif shutil.which("notify-send"):
            subprocess.run(["notify-send", "야간비행", 글], capture_output=True, timeout=5)
except Exception:
    pass
sys.exit(0)
