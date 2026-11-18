#!/usr/bin/env python3
"""파이썬 자동 점검이 «이 대화가 야간비행에 등록한 대화인가»를 묻는 한 곳."""
import os
import subprocess
from pathlib import Path

_여기 = Path(__file__).resolve().parent


def 등록된_대화인가(입력: dict) -> bool:
    환경 = dict(os.environ)
    대화 = str((입력 or {}).get("session_id") or "").replace("\n", "")
    if 대화:
        환경["NF_SESSION"] = 대화
    폴더 = str((입력 or {}).get("cwd") or "")
    if not 환경.get("CLAUDE_PROJECT_DIR") and 폴더:
        환경["CLAUDE_PROJECT_DIR"] = 폴더
    try:
        r = subprocess.run(["bash", "-c", '. "$1" >/dev/null 2>&1 && nf_registered', "_", str(_여기 / "project-root.sh")],
                           env=환경, capture_output=True, timeout=5)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False
