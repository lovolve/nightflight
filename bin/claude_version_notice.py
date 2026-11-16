#!/usr/bin/env python3
"""대화가 시작될 때, 지금 도는 클로드 코드가 야간비행 기능에 필요한 판보다 낮으면 사람에게 한 번 알린다(SessionStart)."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

뿌리 = Path(__file__).resolve().parent.parent


def 판(글):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", 글 or "")
    return tuple(int(x) for x in m.groups()) if m else None


def 지금판():
    m = re.search(r"claude-code_(\d+)-(\d+)-(\d+)", os.environ.get("AI_AGENT", ""))
    if m:
        return tuple(int(x) for x in m.groups())
    길 = os.environ.get("CLAUDE_CODE_EXECPATH", "")
    if 길 and os.path.isfile(길):
        try:
            return 판(subprocess.run([길, "--version"], capture_output=True, text=True, timeout=5).stdout)
        except (OSError, subprocess.SubprocessError):
            return None
    return None


def 요구표():
    줄들 = []
    try:
        for 줄 in (뿌리 / "data" / "claude_min_version.tsv").read_text(encoding="utf-8").splitlines():
            if not 줄.strip() or 줄.startswith("#"):
                continue
            칸 = 줄.split("\t")
            if len(칸) >= 3 and 판(칸[2]):
                줄들.append((칸[0], 칸[1], 판(칸[2])))
    except OSError:
        pass
    return 줄들


def 영어인가():
    try:
        return subprocess.run(["bash", "-c", '. "$1" >/dev/null 2>&1; nf_lang', "_", str(뿌리 / "bin" / "project-root.sh")],
                              capture_output=True, text=True, timeout=5).stdout.strip() == "en"
    except (OSError, subprocess.SubprocessError):
        return False


def main():
    지금 = 지금판()
    if not 지금:
        return
    모자람 = [(ko, en, 최소) for ko, en, 최소 in 요구표() if 지금 < 최소]
    if not 모자람:
        return
    지금글 = ".".join(map(str, 지금))
    자리 = Path(os.environ.get("NIGHTFLIGHT_HOME") or (Path.home() / ".nightflight")) / "claude_version_told"
    try:
        if 자리.read_text(encoding="utf-8").strip() == 지금글:
            return
    except OSError:
        pass
    최소글 = ".".join(map(str, max(m for _, _, m in 모자람)))
    앱 = os.environ.get("CLAUDE_CODE_ENTRYPOINT", "") == "claude-desktop"
    if 영어인가():
        이름 = ", ".join(en for _, en, _ in 모자람)
        할일 = "Update the Claude desktop app." if 앱 else "Run `claude update` in the terminal."
        사람 = f"⚠️ Claude Code here is {지금글}, so Nightflight's {이름} does not work. It needs {최소글} or later. {할일}"
        모델 = f"Nightflight: this Claude Code is {지금글}; {이름} needs {최소글}+. If the user asks why it is missing, say this and how to update."
    else:
        이름 = " · ".join(ko for ko, _, _ in 모자람)
        할일 = "클로드 앱을 업데이트하십시오." if 앱 else "터미널에서 `claude update` 를 실행하십시오."
        사람 = f"⚠️ 이 클로드 코드는 {지금글} 판이라 야간비행 {이름}이 나오지 않습니다. {최소글} 판 이상이 필요합니다. {할일}"
        모델 = f"야간비행: 이 클로드 코드는 {지금글} 판이고 {이름}은 {최소글} 판 이상에서 돕니다. 사용자가 왜 안 나오는지 물으면 이 까닭과 업데이트 방법을 말하십시오."
    print(json.dumps({"systemMessage": 사람,
                      "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": 모델}},
                     ensure_ascii=False))
    try:
        자리.parent.mkdir(parents=True, exist_ok=True)
        자리.write_text(지금글 + "\n", encoding="utf-8")
    except OSError:
        pass


try:
    main()
except Exception:
    pass
sys.exit(0)
