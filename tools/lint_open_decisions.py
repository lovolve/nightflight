#!/usr/bin/env python3
"""코드·문서에 표시된 «대표 자리»가 조종석에 올라가 있는지 본다.

왜 있나 (

  🔴 실측(어느 앱 2026-09-30): 결정 **45건 중 40건이 대표의 말**에서 나왔는데,
     도구가 「지금 결정하실 것」으로 띄운 것은 **1건**이었다.
     나머지 39건은 **모델이 대화 중에 알아서 물어서** 나왔다 — 도구가 아니라 모델이.
     **모델이 물을 줄 알아야만 결정이 나온다.** 안 물으면 39개가 모델 판단으로 굳었을 것이다.

  ⭐ 그런데 표지는 **이미 일하는 자리에 붙어 있다** — 코드 주석과 규칙 문서에
     「아직 안 정했다」·「창업자 판단이 필요하다」가 11곳 있었다(2026-09-30 실측).
     **도구가 그걸 안 볼 뿐이다.** 그래서 새 표지를 만들지 않고 «있는 것»을 긁는다.

이 검사가 보는 것 둘:
  ① **표시됐는데 기록에 없다** → 대표에게 안 보이는 결정 지점
  ② **정해졌는데 표지가 남아 있다** → 낡은 표지.
     (카드가 답이 나와도 안 내려가던 것과 **같은 병**이다 — 2026-09-29에 고쳤다)

⚠️ 짝짓기는 **낱말 겹침**이라 거칠다 — 그래서 **올렸다고 «적을» 수 있게** 했다.
   기록에 올린 표지에는 `(기록에 있음)` 을 붙인다. 그러면 이 검사는 넘어간다.
   ⛔ 낱말 겹침만으로 버티게 두면 **항상 같은 넷이 떠서 잡음이 된다** — 그럼 아무도 안 본다
   (2026-09-30 실측: 넷을 기록에 올렸는데 낱말이 안 겹쳐 그대로 떴다).

  사용:  python3 lint_open_decisions.py [저장소]
"""
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
