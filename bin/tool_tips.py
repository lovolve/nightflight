#!/usr/bin/env python3
"""서버에서 승인된 바깥 도구 목록을 받아 두고, 기능 안내(feature_tips.py)가 읽을 줄로 바꾼다."""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nf_paths

주기 = 24 * 3600
실패주기 = 3600
경로 = "/functions/v1/gyejeong/%EB%8F%84%EA%B5%AC%EC%A0%9C%EC%95%88"
식한도 = 300
글한도 = 600
반복한도 = 6
횟수한도 = 50


def 집() -> Path:
    return nf_paths.집()


def 저장길() -> Path:
    return 집() / "tool_tips.json"


def 읽기() -> dict:
    try:
        d = json.loads(저장길().read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _적기(d: dict) -> None:
    길 = 저장길()
    길.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=길.parent) as 임시터:
        임시 = os.path.join(임시터, "new_version")
        with open(임시, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(임시, 길)


def 주소() -> str:
    v = os.environ.get("NF_TOOL_TIPS_URL") or ""
    if v and nf_paths.주소허용(v):
        return v
    return nf_paths.서버주소() + 경로


def _수(x) -> float:
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def 받기(지금: bool = False) -> str:
    d = 읽기()
    if not 지금 and time.time() - _수(d.get("받은때")) < 주기:
        return "아직 하루가 안 지났습니다"
    if not 지금 and time.time() - _수(d.get("시도한때")) < 실패주기:
        return "조금 전에 받지 못했습니다 — 한 시간 뒤에 다시 받습니다"
    u = 주소()
    if not nf_paths.주소허용(u):
        return "주소가 맞지 않습니다"
    try:
        요청 = urllib.request.Request(u, headers={"Accept": "application/json"})
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(요청, timeout=8) as r:
            몸 = json.loads(r.read(512 * 1024).decode("utf-8"))
    except Exception:
        d["시도한때"] = time.time()
        _적기(d)
        return "받지 못했습니다 — 갖고 있던 목록을 씁니다"
    if not isinstance(몸, dict) or 몸.get("됐나") is not True or not isinstance(몸.get("도구"), list):
        d["시도한때"] = time.time()
        _적기(d)
        return "받지 못했습니다 — 갖고 있던 목록을 씁니다"
    _적기({"받은때": time.time(), "도구": 몸["도구"][:200]})
    return f"받았습니다 — {len(몸['도구'])}개"


_반복표 = re.compile(r"(?<!\\)(?:[*+]|\{\d*,?\d*\})")


def _무거운식(x: str) -> bool:
    if re.search(r"\\[1-9]|\\g|\(\?(?!:|i\))", x):
        return True
    for m in re.finditer(r"\{(\d*),?(\d*)\}", x):
        if any(v and int(v) > 횟수한도 for v in m.groups()):
            return True
    if len(re.findall(r"(?<!\\)[*+]|\{\d+,\}", x)) > 반복한도:
        return True
    열림 = []
    for i, ch in enumerate(x):
        if ch == "\\":
            continue
        if i > 0 and x[i - 1] == "\\":
            continue
        if ch == "(":
            열림.append(i)
        elif ch == ")" and 열림:
            처음 = 열림.pop()
            안 = x[처음 + 1:i]
            뒤 = x[i + 1:i + 2]
            if 뒤 in ("*", "+", "{") and (_반복표.search(안) or "|" in 안):
                return True
    return False


def _식(x) -> "re.Pattern | None":
    if not isinstance(x, str) or not x.strip() or len(x) > 식한도:
        return None
    if _무거운식(x):
        return None
    try:
        return re.compile(x)
    except re.error:
        return None


def 줄들(영어: bool = False) -> list[tuple]:
    out = []
    for x in 읽기().get("도구") or []:
        if not isinstance(x, dict):
            continue
        이름 = x.get("이름")
        알 = _식(x.get("알아듣는말"))
        썼 = x.get("썼는지")
        썼식 = _식(썼) if 썼 else None
        말 = x.get("전할말_en" if 영어 else "전할말") or x.get("전할말")
        if not isinstance(이름, str) or not 이름.strip() or 알 is None or (썼 and 썼식 is None):
            continue
        if not isinstance(말, str) or not 말.strip() or len(말) > 글한도:
            continue
        out.append(("도구:" + 이름.strip()[:60], 알, 썼식, 말.strip()))
    return out


효과경로 = "/functions/v1/gyejeong/%EB%8F%84%EA%B5%AC%ED%9A%A8%EA%B3%BC"


def 동의길() -> Path:
    return 집() / "tool_stats_consent"


def 동의() -> str:
    try:
        return 동의길().read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def 효과지금() -> dict:
    try:
        d = json.loads((집() / "feature_tips.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out = {}
    for id_, 칸 in ((d.get("기능") or {}) if isinstance(d, dict) else {}).items():
        if not isinstance(id_, str) or not id_.startswith("도구:") or not isinstance(칸, dict):
            continue
        out[id_[3:][:60]] = {"나감": int(칸.get("횟수") or 0), "그만": int(칸.get("그만") or 0), "씀": 1 if 칸.get("안내뒤씀") else 0}
    return out


def 효과보내기(지금보냄: bool = False) -> str:
    if 동의() != "네":
        return "동의하지 않아 보내지 않습니다"
    보낸길 = 집() / "tool_stats_sent.json"
    try:
        if not 지금보냄 and time.time() - 보낸길.stat().st_mtime < 주기:
            return "아직 하루가 안 지났습니다"
    except OSError:
        pass
    지금 = 효과지금()
    try:
        보낸 = json.loads(보낸길.read_text(encoding="utf-8"))
        보낸 = 보낸 if isinstance(보낸, dict) else {}
    except (OSError, ValueError):
        보낸 = {}
    줄 = []
    for 이름, 수 in 지금.items():
        전 = 보낸.get(이름) if isinstance(보낸.get(이름), dict) else {}
        늘 = {k: max(0, 수[k] - int(전.get(k) or 0)) for k in ("나감", "그만", "씀")}
        if any(늘.values()):
            줄.append({"이름": 이름, **늘})
    if not 줄:
        return "보낼 것이 없습니다"
    u = nf_paths.서버주소() + 효과경로 if not os.environ.get("NF_TOOL_STATS_URL") else os.environ["NF_TOOL_STATS_URL"]
    if not nf_paths.주소허용(u):
        return "주소가 맞지 않습니다"
    try:
        요청 = urllib.request.Request(u, data=json.dumps({"줄": 줄[:100]}, ensure_ascii=False).encode("utf-8"),
                                    headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(요청, timeout=8) as r:
            답 = json.loads(r.read(64 * 1024).decode("utf-8"))
        if not (isinstance(답, dict) and 답.get("됐나") is True):
            return "보내지 못했습니다 — 다음에 다시 보냅니다"
    except Exception:
        return "보내지 못했습니다 — 다음에 다시 보냅니다"
    보낸길.parent.mkdir(parents=True, exist_ok=True)
    보낸길.write_text(json.dumps(지금, ensure_ascii=False), encoding="utf-8")
    return f"보냈습니다 — {len(줄)}개"


def 단계줄들(영어: bool = False) -> list[tuple]:
    out = []
    for x in 읽기().get("도구") or []:
        if not isinstance(x, dict) or not isinstance(x.get("이름"), str) or not x["이름"].strip():
            continue
        단계 = x.get("단계")
        if not isinstance(단계, list):
            continue
        단계 = {int(n) for n in 단계 if isinstance(n, int) and not isinstance(n, bool) and 0 <= n <= 8}
        if not 단계:
            continue
        세부 = x.get("세부기능말")
        세부식 = _식(세부) if 세부 else None
        썼 = x.get("썼는지")
        썼식 = _식(썼) if 썼 else None
        말 = x.get("전할말_en" if 영어 else "전할말") or x.get("전할말")
        if (세부 and 세부식 is None) or (썼 and 썼식 is None) or not isinstance(말, str) or not 말.strip() or len(말) > 글한도:
            continue
        out.append(("도구:" + x["이름"].strip()[:60], 단계, 세부식, 썼식, 말.strip()))
    return out


def main(a: list[str]) -> int:
    if a[:1] == ["받기"]:
        print(받기("--지금" in a))
        return 0
    if a[:1] == ["동의"] and a[1:2] in (["네"], ["아니오"]):
        동의길().parent.mkdir(parents=True, exist_ok=True)
        동의길().write_text(a[1] + "\n", encoding="utf-8")
        print("안내 효과를 보내기로 했습니다." if a[1] == "네" else "안내 효과를 보내지 않기로 했습니다.")
        return 0
    if a[:1] == ["효과보내기"]:
        print(효과보내기("--지금" in a))
        return 0
    if a[:1] == ["보기"]:
        for id_, 알, _, 말 in 줄들():
            print(f"{id_}\t{알.pattern}\t{말}")
        return 0
    print("받기 · 보기 · 동의 네 · 동의 아니오 · 효과보내기 중 하나를 주십시오.")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
