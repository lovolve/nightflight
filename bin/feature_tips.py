#!/usr/bin/env python3
"""막히는 순간에 클로드 코드 기능을 짚어 드린다 — 사용자 말이 들어올 때 돈다(UserPromptSubmit)."""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

여기 = Path(__file__).resolve().parent
sys.path.insert(0, str(여기))
from trusted_text import 사용자가_쓴_말

최대횟수 = 2
끄는말 = re.compile(r"(이런|기능) ?안내 ?(그만|꺼|끄|하지 ?마)")
켜는말 = re.compile(r"(이런|기능) ?안내 ?(다시 ?)?켜")
알림끄는말 = re.compile(r"입력 ?알림 ?(그만|꺼|끄)")
알림켜는말 = re.compile(r"입력 ?알림 ?(다시 ?)?켜")


def 상태길() -> Path:
    return Path(os.environ.get("HOME") or Path.home()) / ".nightflight" / "feature_tips.json"


def 읽기() -> dict:
    try:
        d = json.loads(상태길().read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def 적기(d: dict) -> None:
    길 = 상태길()
    길.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=길.parent) as 임시터:
        임시 = os.path.join(임시터, "new_version")
        with open(임시, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(임시, 길)


def 표():
    for 줄 in (여기.parent / "data" / "feature_tips.tsv").read_text(encoding="utf-8").splitlines():
        if not 줄.strip() or 줄.startswith("#"):
            continue
        칸 = 줄.split("\t")
        if len(칸) == 4:
            yield 칸


def 등록한_프로젝트인가() -> bool:
    폴더 = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    return (폴더 / ".nightflight").exists() or (폴더 / ".claude" / "ledger.tsv").exists()


def 답(글: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": 글}}, ensure_ascii=False))


def 처리(입력: dict) -> None:
    말 = 사용자가_쓴_말(str(입력.get("prompt") or "")).strip()
    if not 말:
        return
    상태 = 읽기()
    기능 = 상태.setdefault("기능", {})
    대화 = str(입력.get("session_id") or "")

    for 규칙, 칸, 값, 글 in ((끄는말, "끔", True, "이런 안내를 껐습니다. «이런 안내 켜줘»로 다시 켤 수 있습니다."),
                         (켜는말, "끔", False, "이런 안내를 다시 켰습니다."),
                         (알림끄는말, "입력알림끔", True, "입력 알림을 껐습니다. «입력 알림 켜줘»로 다시 켤 수 있습니다."),
                         (알림켜는말, "입력알림끔", False, "입력 알림을 다시 켰습니다.")):
        if 규칙.search(말):
            상태[칸] = 값
            적기(상태)
            답(f"야간비행: 사용자에게 한 문장으로 전하십시오: {글}")
            return

    바뀜 = False
    줄들 = list(표())
    for id_, _, 쓴말, _ in 줄들:
        if re.search(쓴말, 말):
            기능.setdefault(id_, {})["썼음"] = True
            바뀜 = True

    글들 = []
    if not 상태.get("제안함") and 등록한_프로젝트인가():
        상태["제안함"] = True
        바뀜 = True
        글들.append(
            "야간비행: 사용자의 요청을 먼저 처리하십시오. 그 답 끝에 data/asking.md 대로 두 가지를 한 번만 물으십시오. "
            "① 첫머리에 «야간비행은 비개발자가 이해할 수 있는 용어로 개발하실 수 있도록 언어를 제공하고 있습니다.»라고 쓰고, 선택지를 "
            "«쓰기: 이 대화부터 야간비행의 언어를 사용합니다» «안 쓰기: 기존에 대화하던 언어를 그대로 사용합니다»로 보여 드리십시오. "
            "쓰겠다고 하면 앱에서는 대화 제목 메뉴의 출력 스타일, 터미널에서는 `/config` 의 출력 스타일에서 «야간비행 언어»를 고르는 법을 알려 드리십시오. 같은 자리에서 언제든 끌 수 있다고 말하십시오. "
            f"② 대화 용량과 사용 한도를 늘 표시할까요? 앱에서는 입력창 위, 터미널에서는 화면 아래에 표시됩니다. 쓰겠다고 하면 `{여기}/statusline_enable.py 켜기` 를 돌리십시오. 끄는 법은 같은 명령의 `끄기` 입니다. "
            "터미널에 이미 다른 상태줄이 있으면 덮어쓰지 않습니다."
        )

    if not 상태.get("끔") and not (대화 and 상태.get("안내한대화") == 대화):
        for id_, 알아듣는, _, 전할말 in 줄들:
            칸 = 기능.get(id_, {})
            if 칸.get("썼음") or int(칸.get("횟수") or 0) >= 최대횟수:
                continue
            if re.search(알아듣는, 말):
                기능.setdefault(id_, {})["횟수"] = int(칸.get("횟수") or 0) + 1
                상태["안내한대화"] = 대화
                바뀜 = True
                글들.append(
                    "야간비행: 사용자의 요청을 먼저 처리하십시오. 답 끝에 이 내용을 한 번만 짧게 덧붙이십시오. "
                    f"«{전할말}» 사용자가 원하지 않으면 «이런 안내 그만»이라고 하시면 된다고 함께 말하십시오."
                    if int(칸.get("횟수") or 0) == 0 else
                    f"야간비행: 사용자의 요청을 먼저 처리하십시오. 답 끝에 이 내용을 한 번만 짧게 덧붙이십시오. «{전할말}»"
                )
                break
    if 바뀜:
        적기(상태)
    if 글들:
        답("\n".join(글들))


if __name__ == "__main__":
    try:
        처리(json.load(sys.stdin) or {})
    except Exception:
        pass
