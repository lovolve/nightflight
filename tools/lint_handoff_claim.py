#!/usr/bin/env python3
"""야간비행 도구"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

HANDOFF = (
    "해 주셔야", "하셔야 합니다", "하셔야 돼", "대표님만", "대표님이 직접",
    "제가 못 합니다", "제가 못 하는", "저는 못 합니다", "할 수 없습니다",
    "불가능합니다", "방법이 없습니다", "없이는 안 됩니다", "필요합니다만 제가",
)

TRIED = (
    "눌러 봤", "눌러보", "직접 해 봤", "해 봤는데", "돌려 봤", "시도했", "시도해 봤",
    "404", "403", "405", "오류였습니다", "거부당", "실패했습니다", "막혔습니다",
    "확인했습니다", "확인함", "실측", "두 번 시도", "두 번째도",
)

ADMITTED = ("확인 못 했", "확인하지 않았", "모릅니다", "모르겠습니다", "안 해 봤", "추정입니다")


TAIL = 512 * 1024


def 말들(path: Path) -> list[str]:
    out = []
    with path.open("rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - TAIL))
        blob = f.read()
    for line in blob.decode("utf-8", errors="replace").splitlines():
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") != "assistant":
            continue
        content = (d.get("message") or {}).get("content") or []
        if isinstance(content, str):
            out.append(content)
            continue
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                out.append(part.get("text") or "")
    return out


def 짚을것(text: str) -> str | None:
    hit = next((h for h in HANDOFF if h in text), None)
    if not hit:
        return None
    if any(t in text for t in TRIED) or any(a in text for a in ADMITTED):
        return None
    return hit


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("NF_TRANSCRIPT", "")
    if not arg:
        print("⛔ 이번 턴 기록을 못 받았습니다 — **검사하지 않았습니다.**")
        print("   ⚠️ 이건 「깨끗하다」가 아닙니다.")
        return 0
    path = Path(arg)
    if not path.exists():
        print("⛔ 기록 파일이 없습니다 — **검사하지 않았습니다.**")
        return 0
    if path.is_dir():
        print("⛔ 기록 자리가 아니라 폴더를 받았습니다 — **검사하지 않았습니다.**")
        print("   ⚠️ 이건 「깨끗하다」가 아닙니다.")
        return 0

    try:
        msgs = 말들(path)
    except Exception as e:
        print(f"⛔ 기록을 못 읽었습니다({type(e).__name__}) — **검사하지 않았습니다.**")
        print("   ⚠️ 이건 「깨끗하다」가 아닙니다.")
        return 0
    if not msgs:
        return 0
    last = msgs[-1]
    hit = 짚을것(last)
    if not hit:
        return 0

    print(f"🔴 「{hit}」라고 적으셨는데 **눌러 본 흔적이 없습니다.**")
    print()
    print("   물어야 할 것은 「되나 안 되나」가 아니라 **「내가 해 봤나」**입니다.")
    print("   ① 도구나 명령으로 **그 자리에서 해 보십시오.** 막히면 그 오류를 적으십시오.")
    print("   ② 안 해 봤으면 **「확인 못 했습니다」**라고 쓰십시오. 단정하지 마십시오.")
    print("   ③ 문서나 남의 글은 흔적이 아닙니다 — 같은 날 그걸 믿었다가 404 를 만났습니다.")
    print()
    print("   ⭐ 틀렸을 때 값을 치르는 쪽이 사용자입니다 —")
    print("      비개발자가 **안 해도 될 일**을 찾아 헤매게 됩니다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
