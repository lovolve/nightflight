#!/usr/bin/env python3
"""받은 글 가운데 AI 지시나 사용자 말로 써도 되는 것만 골라 준다."""
import hashlib
import json, os
import re
import secrets
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


def _주소파일(기록폴더: str) -> str:
    for 후보 in (os.path.join(기록폴더, "internal", "board.url"), os.path.join(기록폴더, "board.url")):
        if os.path.isfile(후보):
            return 후보
    return os.path.join(기록폴더, "internal", "board.url")


def _집() -> str:
    if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import nf_paths
    return str(nf_paths.집())


def _비밀(만들기: bool) -> str:
    길 = os.path.join(_집(), "owner.key")
    try:
        with open(길, encoding="utf-8") as f:
            v = f.read(200).strip()
        if re.fullmatch(r"[0-9a-f]{64}", v):
            return v
    except OSError:
        pass
    if not 만들기:
        return ""
    v = secrets.token_hex(32)
    try:
        os.makedirs(_집(), exist_ok=True)
        fd = os.open(길, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(v + "\n")
        return v
    except FileExistsError:
        return _비밀(False)
    except OSError:
        return ""


def _도장값(비밀: str, 주소: str) -> str:
    return hashlib.sha256((비밀 + "\n" + 주소).encode("utf-8")).hexdigest()


def _도장파일(주소파일: str) -> str:
    return os.path.join(os.path.dirname(주소파일), "board.owner")


def 도장찍기(기록폴더: str, 주소: str) -> bool:
    return _도장찍기_파일(_주소파일(기록폴더), 주소)


def _도장찍기_파일(파일: str, 주소: str) -> bool:
    비밀 = _비밀(True)
    if not 비밀 or not 꼴맞는주소(주소):
        return False
    try:
        os.makedirs(os.path.dirname(파일), exist_ok=True)
        with open(_도장파일(파일), "w", encoding="utf-8") as f:
            f.write(_도장값(비밀, 주소) + "\n")
        return True
    except OSError:
        return False


def _도장맞나(파일: str, 글: str) -> bool:
    비밀 = _비밀(False)
    도장 = _도장파일(파일)
    if 비밀:
        try:
            with open(도장, encoding="utf-8") as f:
                return f.read(200).strip() == _도장값(비밀, 글)
        except OSError:
            pass
    if os.path.islink(파일) or os.path.exists(도장):
        return False
    try:
        주소때 = os.stat(파일).st_mtime
        비밀때 = os.stat(os.path.join(_집(), "owner.key")).st_mtime if 비밀 else float("inf")
    except OSError:
        return False
    return 주소때 < 비밀때


def 조종석주소(기록폴더: str) -> str:
    파일 = _주소파일(기록폴더)
    try:
        with open(파일, encoding="utf-8", errors="replace") as f:
            글 = f.read(300).strip()
    except OSError:
        return ""
    if not 꼴맞는주소(글) or _저장소에_들어_있나(파일):
        return ""
    if not _도장맞나(파일, 글):
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
    elif 명령 == "저장소안내":
        파일 = _주소파일(값)
        if os.path.isfile(파일) and _저장소에_들어_있나(파일):
            말 = "야간비행: 조종석 주소 파일이 저장소에 들어 있어 쓰지 않았습니다. 새 조종석을 만들지 말고, `git rm --cached -- " + 파일 + "` 로 저장소에서만 빼고 무시 목록에 넣은 뒤 사용자에게 보고하십시오."
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": 말}}, ensure_ascii=False))
    elif 명령 == "꼴":
        sys.exit(0 if 꼴맞는주소(값) else 1)
    elif 명령 == "도장":
        sys.exit(0 if 도장찍기(값, sys.argv[3] if len(sys.argv) > 3 else "") else 1)
    elif 명령 == "열쇠준비":
        sys.exit(0 if _비밀(True) else 1)
    else:
        sys.exit(2)
