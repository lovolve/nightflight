#!/usr/bin/env python3
"""답에서 «재고 말할 사실»(data/facts.tsv)을 단정했을 때 **잰 흔적이 있는지** 본다."""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import facts

TAIL = 2 * 1024 * 1024
바로잡힘_사용자 = re.compile(r"이미 (했|해 ?놨|해 ?뒀|있|출시|만들|받|올렸|넣었|켜|연결|등록|끝났)|벌써 (했|있|출시)|했잖아|있잖아|틀렸어|잘못 알고")
바로잡힘_AI = re.compile(r"바로잡습니다|제가 틀렸|잘못 말씀|잘못 알려|잘못 보고")
태그덩어리 = re.compile(r"<([A-Za-z][\w-]*)[^>]*>.*?</\1>", re.S)
더한흔적 = re.compile(r"facts\.py[\"']?\s+더하기")
ADMITTED = ("확인 못 했", "확인하지 않았", "재지 않았", "재 보지 않았", "안 재", "모릅니다", "모름", "추정입니다")


def 읽기(path: Path) -> tuple[list[str], list[str], str, list[str]]:
    with path.open("rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - TAIL))
        blob = f.read().decode("utf-8", errors="replace")
    말, 부름, 사용자, 이번부름 = [], [], "", []
    for line in blob.splitlines():
        try:
            d = json.loads(line)
        except Exception:
            continue
        content = (d.get("message") or {}).get("content") or []
        if d.get("type") == "user":
            if d.get("isCompactSummary"):
                continue
            글 = content if isinstance(content, str) else " ".join(
                p.get("text") or "" for p in content if isinstance(p, dict) and p.get("type") == "text")
            글 = 태그덩어리.sub(" ", 글).strip()
            if 글 and not 글.startswith("<"):
                사용자, 이번부름 = 글, []
            continue
        if d.get("type") != "assistant":
            continue
        if isinstance(content, str):
            말.append(content)
            continue
        for p in content:
            if not isinstance(p, dict):
                continue
            if p.get("type") == "text":
                말.append(p.get("text") or "")
            elif p.get("type") == "tool_use":
                inp = p.get("input") or {}
                b = str(p.get("name") or "") + " " + json.dumps(inp, ensure_ascii=False)
                부름.append(b)
                이번부름.append(b)
    return 말, 부름, 사용자, 이번부름


def 사고(사용자: str, 마지막말: str, 이번부름: list[str]) -> str | None:
    if any(더한흔적.search(b) for b in 이번부름):
        return None
    m = 바로잡힘_사용자.search(사용자 or "") or 바로잡힘_AI.search(re.sub(r"```.*?```", " ", 마지막말 or "", flags=re.S))
    return m.group(0) if m else None


def 짚을것(text: str, 부름: list[str], 잰값: dict, 표: list[dict]) -> list[dict]:
    본문 = re.sub(r"```.*?```", " ", text, flags=re.S)
    if any(a in 본문 for a in ADMITTED):
        return []
    out = []
    for f in 표:
        try:
            m = re.search(f["단정말"], 본문, re.I)
            흔적 = re.compile(f["흔적"], re.I)
        except re.error:
            continue
        if not m:
            continue
        if any(흔적.search(b) for b in 부름):
            continue
        v = 잰값.get(f["이름"])
        if v and not v[4]:
            continue
        out.append(dict(f, 말=m.group(0), 잰값=v))
    return out


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("NF_TRANSCRIPT", "")
    path = Path(arg) if arg else None
    if not path or not path.is_file():
        print("⛔ 이번 턴 기록을 못 받았습니다 — **검사하지 않았습니다.** ⚠️ 이건 「깨끗하다」가 아닙니다.")
        return 0
    try:
        말, 부름, 사용자, 이번부름 = 읽기(path)
    except Exception as e:
        print(f"⛔ 기록을 못 읽었습니다({type(e).__name__}) — **검사하지 않았습니다.**")
        return 0
    if not 말:
        return 0
    hits = 짚을것(말[-1], 부름, facts.잰값들(), facts.표())
    잡힘 = 사고(사용자, 말[-1], 이번부름)
    if not hits and not 잡힘:
        return 0
    if 잡힘:
        print(f"🟡 「{잡힘}」 — 이번 턴에 사실이 바로잡혔습니다. 같은 일이 다시 안 나게 이 앱의 사실 표에 한 줄 더하십시오.")
        print(f"   {Path(__file__).resolve().parent / 'facts.py'} 더하기 <이름> <단정하는 말> <재는 명령의 흔적> <재는 법> [며칠이면 다시 잴지]")
        print("   이미 표에 있는 사실이면 더하지 말고, 이번에 왜 재지 않았는지만 짚으십시오.")
        print("   [모델] 여러 앱에서 같은 사실이 나오면 대화 시작 때 «공용 표로 옮길 후보»로 보입니다.")
        if not hits:
            return 1
        print()
    for h in hits:
        print(f"🔴 「{h['말']}」 — **{h['이름']}**을(를) 단정했는데 이번 대화에서 잰 흔적이 없습니다.")
        if h["잰값"]:
            날, 값, 근거, 지남, _ = h["잰값"]
            print(f"   마지막으로 잰 값은 «{값}»({날} · {지남}일 전)이라 오래됐습니다.")
        print(f"   재는 법: {h['재는법']}")
    print()
    print("   ① 재고 나서 다시 말하십시오. 잰 결과가 앞의 말과 다르면 바로잡으십시오.")
    print("   ② 잴 수 없으면 «확인 못 했습니다»라고 쓰십시오. 기억이나 적어 둔 기록으로 단정하지 마십시오.")
    print("   ⭐ 이 사실이 틀리면 사용자가 안 해도 될 일을 합니다(이미 받은 열쇠를 다시 만드는 것처럼).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
