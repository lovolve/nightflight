#!/usr/bin/env python3
"""야간비행 도구"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

TAIL = 1024 * 1024

PENDING = (
    "아직 안 한 것", "아직 안 했", "아직 안 ", "안 한 것", "남은 일", "못 했습니다", "하지 못했습니다",
    "안 넣었", "안 만들었", "안 고쳤", "안 했습니다",
    "넣지 않았습니다", "만들지 않았습니다", "고치지 않았습니다", "추가하지 않았습니다",
    "나중에 하", "다음에 하", "따로 하겠습니다", "뒤로 미루",
)
WAITING = ("커밋", "깃허브", "푸시", "서버에 올리", "올릴까요", "승인", "정하실", "정해 주", "여쭙")
RECORDED = ("남은 것으로 기록", "남은 것에 적", "남은것", "기록에 적었", "기록했습니다")


def 이번턴(path: Path):
    with path.open("rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - TAIL))
        blob = f.read()
    rows = []
    for line in blob.decode("utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    start = 0
    for i, d in enumerate(rows):
        if d.get("type") != "user":
            continue
        c = (d.get("message") or {}).get("content")
        if isinstance(c, str) or (isinstance(c, list) and any(isinstance(p, dict) and p.get("type") == "text" for p in c)):
            start = i + 1
    texts, cmds = [], []
    for d in rows[start:]:
        if d.get("type") != "assistant":
            continue
        for p in (d.get("message") or {}).get("content") or []:
            if not isinstance(p, dict):
                continue
            if p.get("type") == "text":
                texts.append(p.get("text") or "")
            elif p.get("type") == "tool_use":
                cmds.append(json.dumps(p.get("input") or {}, ensure_ascii=False))
    return texts, cmds


def 짚을줄(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        if not any(k in line for k in PENDING):
            continue
        if any(k in line for k in WAITING) or any(k in line for k in RECORDED):
            continue
        out.append(line.strip()[:120])
    return out


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("NF_TRANSCRIPT", "")
    path = Path(arg) if arg else None
    if not path or not path.is_file():
        print("⛔ 이번 턴 기록을 못 받았습니다 — 검사하지 않았습니다(깨끗하다는 뜻이 아닙니다).")
        return 0
    try:
        texts, cmds = 이번턴(path)
    except Exception as e:
        print(f"⛔ 기록을 못 읽었습니다({type(e).__name__}) — 검사하지 않았습니다.")
        return 0
    if not texts:
        return 0
    lines = 짚을줄(texts[-1])
    if not lines:
        return 0
    if any("남은것" in c for c in cmds):
        return 0
    print(f"🔴 «안 한 일»을 말했는데 이번 턴에 기록의 «남은 것»에 안 적었습니다 — {len(lines)}줄")
    for l in lines[:5]:
        print(f"   「{l}」")
    print("   ⭐ 대화가 압축되면 요약 메모의 할 일은 묻힙니다. 기록에 적어야 다음 대화가 이어받습니다.")
    print('   [모델] ledger.sh 남은것 "<한 줄>" "" "<주제>" --화면 "<그 말>" --종류 "<사용자에게 보이는 것|안 보이는 작업>" 으로 적으십시오.')
    return 1


if __name__ == "__main__":
    sys.exit(main())
