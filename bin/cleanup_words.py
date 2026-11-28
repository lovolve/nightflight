#!/usr/bin/env python3
"""대화창에서 알아듣는 말을 보고 모델에게 무엇을 할지 알린다."""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trusted_text import 사용자가_쓴_말, 조종석주소

here = os.environ.get("HERE") or os.path.dirname(os.path.abspath(__file__))
플러그인 = os.path.dirname(here)
표자리 = os.path.join(플러그인, "data", "spoken_words.tsv")
마켓 = "lovolve"


def 표읽기(자리=표자리):
    낱말, 말 = {}, []
    try:
        줄들 = open(자리, encoding="utf-8").read().splitlines()
    except OSError:
        return 낱말, 말
    for 줄 in 줄들:
        if not 줄 or 줄.startswith("#"):
            continue
        c = 줄.split("\t")
        if c[0] == "낱말" and len(c) >= 3:
            전체 = c[2].startswith("=")
            try:
                낱말[c[1]] = (re.compile(c[2][1:] if 전체 else c[2]), 전체)
            except re.error:
                continue
        elif c[0] == "말" and len(c) >= 6:
            조각들 = []
            try:
                for 조각 in c[2].split(" && "):
                    조각들.append([x.strip() if x.strip().startswith("@") else re.compile(x.strip()) for x in 조각.split(" || ")])
            except re.error:
                continue
            말.append({"이름": c[1], "조각들": 조각들, "조건들": [x for x in c[3].split(",") if x.strip()],
                      "등록전": c[4].strip(), "안내": c[5]})
    return 낱말, 말


def _맞나(항, 낱말, 글):
    if isinstance(항, str):
        식, 전체 = 낱말.get(항[1:], (None, False))
        if 식 is None:
            return False
        return bool(식.fullmatch(글) if 전체 else 식.search(글))
    return bool(항.search(글))


def 알아듣나(줄, 낱말, 글):
    return all(any(_맞나(항, 낱말, 글) for 항 in 조각) for 조각 in 줄["조각들"])


def main():
    try:
        _in = json.load(sys.stdin) or {}
    except Exception:
        _in = {}
    if not isinstance(_in, dict):
        _in = {}
    prompt = 사용자가_쓴_말(_in.get("prompt", "") or "")
    글 = prompt.strip()
    등록전 = "--등록전" in sys.argv[1:]
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    낱말, 말들 = 표읽기()

    잰것 = {}

    def 조종석():
        if "주소" not in 잰것:
            잰것["주소"], 잰것["기록"] = "", ""
            for 폴더 in (".nightflight", ".claude"):
                자리 = os.path.join(root, 폴더)
                주소 = 조종석주소(자리)
                if 주소:
                    잰것["주소"], 잰것["기록"] = 주소, 자리
                    break
        return 잰것["주소"]

    def 동의():
        try:
            return open(os.path.join(os.environ.get("NIGHTFLIGHT_HOME") or os.path.expanduser("~/.nightflight"), "cockpit_consent"),
                        encoding="utf-8").read().strip()
        except OSError:
            return ""

    def 다른대화():
        if "다른대화" not in 잰것:
            잰것["다른대화"] = ""
            try:
                import others_editing as _oe
                from pathlib import Path as _P
                _뿌리 = os.environ.get("CLAUDE_PROJECT_DIR") or _in.get("cwd") or os.getcwd()
                _기록 = next((_P(_뿌리) / n for n in (".nightflight", ".claude") if (_P(_뿌리) / n / "internal" / "repeat-guard.tsv").exists()), None)
                if _기록 is not None:
                    잰것["다른대화"] = _oe.모델글(_oe.찾기(_P(_뿌리), _기록, str(_in.get("session_id") or ""))) or ""
            except Exception:
                pass
        return 잰것["다른대화"]

    데스크톱 = os.environ.get("CLAUDE_CODE_ENTRYPOINT") == "claude-desktop"

    def 칸주소():
        if "칸주소" not in 잰것:
            잰것["칸주소"] = ""
            if 데스크톱:
                try:
                    import cockpit_open as _co
                    잰것["칸주소"] = _co.서버주소(root, 7)
                except Exception:
                    pass
        return 잰것["칸주소"]

    def 칸서버삶():
        if "칸서버삶" not in 잰것:
            import subprocess
            try:
                잰것["칸서버삶"] = subprocess.run([sys.executable, "-I", os.path.join(here, "cockpit_server.py"), root, "--살아있나"],
                                              capture_output=True, timeout=3).returncode == 0
            except Exception:
                잰것["칸서버삶"] = False
        return 잰것["칸서버삶"]

    안함 = 낱말.get("안함", (None, False))[0]
    개발말 = 낱말.get("개발말", (None, False))[0]
    조건들 = {
        "짧음": lambda: len(prompt) <= 80,
        "안함아님": lambda: not (안함 and 안함.search(글)),
        "개발말아님": lambda: not (개발말 and 개발말.search(글)),
        "조종석있음": lambda: bool(조종석()),
        "조종석없음": lambda: not 조종석(),
        "올리지않기로함": lambda: 동의() == "아니오",
        "다른대화편집": lambda: bool(다른대화()),
        "앱아님": lambda: not 데스크톱,
        "브라우저칸": lambda: 데스크톱 and bool(칸주소()),
        "칸못켬": lambda: 데스크톱 and not 칸주소(),
        "칸서버없음": lambda: not 칸서버삶(),
        "앞말없음": lambda: not say,
    }
    say = []
    for 줄 in 말들:
        if (줄["등록전"] == "만") != 등록전:
            continue
        if not 알아듣나(줄, 낱말, 글):
            continue
        if not all(조건들.get(이름.strip(), lambda: False)() for 이름 in 줄["조건들"]):
            continue
        안내 = 줄["안내"]
        자리표 = {"{ledger}": os.path.join(here, "ledger.sh"), "{here}": here, "{tools}": os.path.join(플러그인, "tools"),
                "{plugin}": 플러그인, "{주소}": 잰것.get("주소", ""), "{기록}": 잰것.get("기록", ""), "{다른대화}": 잰것.get("다른대화", ""), "{칸주소}": 잰것.get("칸주소", ""),
                "{마켓}": 마켓}
        for k, v in 자리표.items():
            안내 = 안내.replace(k, v)
        say.append(안내)
    if say:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                                 "additionalContext": "\n".join(say)}},
                         ensure_ascii=False))


if __name__ == "__main__":
    main()
