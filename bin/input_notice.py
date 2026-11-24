#!/usr/bin/env python3
"""AI가 답을 기다리거나 승인을 물을 때 컴퓨터 알림을 띄운다(Notification 훅)."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

글들 = {"permission_prompt": "승인을 기다립니다", "idle_prompt": "답을 기다립니다"}
글들_영어 = {"permission_prompt": "Waiting for your approval", "idle_prompt": "Waiting for your reply"}
try:
    입력 = json.load(sys.stdin) or {}
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from registered import 등록된_대화인가
    if not 등록된_대화인가(입력):
        sys.exit(0)
    영어 = subprocess.run(["bash", "-c", '. "$1" >/dev/null 2>&1; nf_lang', "_", str(Path(__file__).resolve().parent / "project-root.sh")],
                        capture_output=True, text=True, timeout=5).stdout.strip() == "en"
    글 = (글들_영어 if 영어 else 글들).get(str(입력.get("notification_type") or ""))
    제목 = "Nightflight" if 영어 else "야간비행"
    상태 = {}
    import nf_paths
    try:
        상태 = json.loads((nf_paths.집() / "feature_tips.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    if 글 and not 상태.get("입력알림끔") and os.environ.get("CLAUDE_CODE_ENTRYPOINT") != "claude-desktop":
        if sys.platform == "darwin":
            subprocess.run(["osascript", "-e", f'display notification "{글}" with title "{제목}"'], capture_output=True, timeout=5)
        elif shutil.which("notify-send"):
            subprocess.run(["notify-send", 제목, 글], capture_output=True, timeout=5)
except Exception:
    pass
sys.exit(0)
