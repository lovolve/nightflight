#!/usr/bin/env python3
"""조종석 화면 글에 «앱»을 쓰지 않는다 · 낯선 순우리말 대신 사람들이 쓰는 말을 쓴다 — 사용자가 만드는 것은 앱·웹·도구로 여럿이고, 야간비행도 앱이 아니다.

🔴 2026-10-25  — 그 자리에 «제품»을 쓴다.
⭐ 실제 앱을 가리키는 고유 표현(「앱빌더」)은 넘긴다. 주석(//)은 안 본다 — 화면에 나가는 따옴표 안 글만 본다.
"""
import re, sys
from pathlib import Path

ALLOW = ("앱빌더", "앱스토어")
바꿀말 = {"단추": "버튼",
          "대표님": "(빼고 하는 일 그대로)"}
_표 = {".claude/screens.tsv": (2,), ".claude/feed-labels.tsv": (1, 2, 3), ".claude/item-labels.tsv": (1,)}

def main():
    p = Path(__file__).resolve().parent.parent / "board" / "cockpit.html"
    hits = []
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        code = line.split("//")[0] if "'" in line else ""
        for m in re.finditer(r"'([^'\n]*)'", code):
            t = m.group(1)
            if "앱" in t and not any(a in t for a in ALLOW) and not re.search(r"[A-Za-z_]앱|앱이름|앱설정|앱칸", t):
                hits.append((n, t[:60]))
        for 말, 대신 in 바꿀말.items():
            for m in re.finditer(r"'([^'\n]*)'", code):
                if 말 in m.group(1):
                    hits.append((n, f"«{말}» → «{대신}»: " + m.group(1)[:50]))
    root = p.parent.parent
    for rel, cols in _표.items():
        f = root / rel
        if not f.is_file():
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("#"):
                continue
            c = line.split("\t")
            for i in cols:
                for 말, 대신 in 바꿀말.items():
                    if i < len(c) and 말 in c[i]:
                        hits.append((f"{rel}:{n}", f"«{말}» → «{대신}»: " + c[i][:50]))
    if not hits:
        print("  ✅ 조종석 화면 글 — «앱» 대신 «제품», 낯선 말 없음")
        return 0
    print(f"  ⛔ 조종석 화면 글에 바꿀 말이 {len(hits)}곳 — «앱»은 «제품»으로(사용자가 만드는 것은 앱만이 아닙니다) · «단추»는 «버튼»으로")
    for n, t in hits:
        print(f"     {n if isinstance(n, str) else 'board/cockpit.html:' + str(n)} 「{t}」")
    return 1

if __name__ == "__main__":
    sys.exit(main())
