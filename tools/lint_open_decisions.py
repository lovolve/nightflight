#!/usr/bin/env python3
"""코드·문서에 표시된 «대표 자리»가 조종석에 올라가 있는지 본다."""
import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
import _root
import re
import sys
from pathlib import Path

MARKS = ("안 정했다", "안정했다", "창업자 판단", "대표님 판단",
         "창업자가 정할", "대표님이 정할", "창업자 결정이 필요", "사람만의 판단")
LOOK = (".swift", ".md", ".ts", ".py", ".yml")
SKIP_DIRS = {".git", "build", "DerivedData", ".claude", ".nightflight", "node_modules", "design"}
SKIP_FILES = {"lint_open_decisions.py"}

WORD = re.compile(r"[가-힣]{2,}")
STOP = {"안다", "있다", "없다", "한다", "된다", "그것", "이것", "하는", "아직", "정했다",
        "창업자", "대표님", "판단", "필요", "무엇", "어떤", "그리고", "그런데", "이다"}


def words(text: str) -> set[str]:
    return {w for w in WORD.findall(text) if w not in STOP and len(w) >= 2}


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else _root.root()
    ledger = _root.ledger()
    if not ledger.exists():
        print("✅ 기록이 아직 없습니다")
        return 0

    open_rows, decided = [], []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        c = line.split("\t")
        if len(c) < 3:
            continue
        if c[1] in ("남은것", "카드"):
            open_rows.append(words(" ".join(c[2:])))
        elif c[1] == "결정":
            decided.append((c[2], words(" ".join(c[2:5]))))

    unseen, stale = [], []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in LOOK or path.name in SKIP_FILES:
            continue
        if any(p in SKIP_DIRS for p in path.parts):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(lines, 1):
            if not any(m in line for m in MARKS):
                continue
            if "기록에 있음" in line:
                continue
            if sum(line.count(c) for c in "①②③④⑤⑥⑦⑧") >= 2:
                continue
            w = words(line)
            if not w:
                continue
            rel = path.relative_to(root)
            hit_dec = next((d for d, dw in decided if len(w & dw) >= 3), None)
            if hit_dec:
                stale.append((rel, n, line.strip()[:66], hit_dec[:52]))
            elif not any(len(w & ow) >= 2 for ow in open_rows):
                unseen.append((rel, n, line.strip()[:76]))

    if not unseen and not stale:
        print("✅ 표시된 대표 자리가 전부 조종석에 있습니다")
        return 0

    if unseen:
        print(f"⚠️  조종석에 «없는» 대표 자리 {len(unseen)}곳 — 사용자는 이걸 못 보십니다\n")
        for rel, n, txt in unseen:
            print(f"  {rel}:{n}\n     {txt}")
        print()
    if stale:
        print(f"🔴 이미 «정해졌는데» 표지가 남아 있는 곳 {len(stale)}곳 — 두 번 묻게 됩니다\n")
        for rel, n, txt, dec in stale:
            print(f"  {rel}:{n}\n     {txt}\n     ↳ 정해짐: {dec}")
        print()
    print("  ⚠️ 짝짓기는 낱말 겹침이라 거칩니다 — 다른 말로 기록에 있을 수 있습니다.")
    print("     이 검사는 «눈이 갈 자리»를 만드는 것이지 판정이 아닙니다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
