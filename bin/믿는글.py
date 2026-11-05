#!/usr/bin/env python3
"""받은 글 가운데 AI 지시나 사용자 말로 써도 되는 것만 골라 준다."""
import os
import re
import subprocess
import sys

_주소꼴 = re.compile(r"https://claude\.ai/(?:code/)?artifact/[A-Za-z0-9_-]{1,80}")

_남의글 = re.compile(
    r"<(agent-message|cross-session-message|task-notification|system-reminder|pasted_content)\b[^>]*>"
    r".*?(?:</\1>|\Z)",
    re.S,
)


def 꼴맞는주소(글: str) -> bool:
    return bool(_주소꼴.fullmatch(글))


def _저장소에_들어_있나(파일: str) -> bool:
    try:
        r = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-C", os.path.dirname(파일),
             "ls-files", "--error-unmatch", "--", os.path.basename(파일)],
            capture_output=True, timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0


def 조종석주소(기록폴더: str) -> str:
    파일 = os.path.join(기록폴더, "board.url")
    try:
        with open(파일, encoding="utf-8", errors="replace") as f:
            글 = f.read(300).strip()
    except OSError:
        return ""
    if not 꼴맞는주소(글) or _저장소에_들어_있나(파일):
        return ""
    return 글


def 사용자가_쓴_말(입력: str) -> str:
    return _남의글.sub(" ", 입력)


if __name__ == "__main__":
    명령 = sys.argv[1] if len(sys.argv) > 1 else ""
    값 = sys.argv[2] if len(sys.argv) > 2 else ""
    if 명령 == "주소":
        주소 = 조종석주소(값)
        if 주소:
            print(주소)
    elif 명령 == "꼴":
        sys.exit(0 if 꼴맞는주소(값) else 1)
    else:
        sys.exit(2)
