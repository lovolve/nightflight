#!/usr/bin/env python3
"""대화가 시작될 때 클로드 코드 기능 쓰는 법을 가리킨다 — 등록한 프로젝트에서만(SessionStart)."""
import json
import os
import subprocess
import sys
from pathlib import Path

폴더 = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
if (폴더 / ".nightflight").exists() or (폴더 / ".claude" / "ledger.tsv").exists():
    뿌리 = Path(__file__).resolve().parent.parent
    try:
        끔 = json.loads((Path(os.environ.get("HOME") or Path.home()) / ".nightflight" / "feature_tips.json").read_text(encoding="utf-8")).get("끔") is True
    except (OSError, ValueError, AttributeError):
        끔 = False
    try:
        영어 = subprocess.run(["bash", "-c", '. "$1" >/dev/null 2>&1; nf_lang', "_", str(뿌리 / "bin" / "project-root.sh")],
                            capture_output=True, text=True, timeout=5).stdout.strip() == "en"
    except (OSError, subprocess.SubprocessError):
        영어 = False
    if 영어:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext":
            "LANGUAGE: English. This user reads English. Write every reply, question, and summary in English, "
            "and address the user as \"you\" (no titles). For every Nightflight skill, read the en.md next to its SKILL.md "
            "and follow it instead of the Korean SKILL.md. Command output and guidance may be in Korean: read it, "
            "but never show Korean to the user unless they wrote it. "
            f"Nightflight: when asking the user a question, follow {뿌리}/data/asking.en.md. "
            f"For planning large changes, showing progress on long work, checking screens, and code review, follow {뿌리}/data/tool_use.en.md. "
            "Run code review only after the user approves it."
            + (" The user turned off these notices. Do not introduce AI tools." if 끔 else "")}}, ensure_ascii=False))
        sys.exit(0)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext":
        f"야간비행: 사용자에게 물을 때는 {뿌리}/data/asking.md 를 따르십시오. "
        f"큰 변경 전 계획 · 긴 작업의 진행 표시 · 화면 직접 확인 · 코드 검토는 {뿌리}/data/tool_use.md 를 따르십시오. "
        "코드 검토는 사용자 승인을 받은 뒤에만 돌립니다."
        + (" 사용자가 안내를 꺼 두었으니 AI 도구를 소개하지 마십시오." if 끔 else "")}}, ensure_ascii=False))
sys.exit(0)
