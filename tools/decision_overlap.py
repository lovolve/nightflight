#!/usr/bin/env python3
"""야간비행 도구"""
from __future__ import annotations
import os
import re
import sys
from pathlib import Path

보일수 = 8
최소점수 = 3
흔한말 = {"있다", "없다", "한다", "것을", "것이", "에서", "으로", "하고", "그리고", "다음", "새로",
         "결정", "2026", "다시", "본다", "그대로", "모두", "하나", "않는다", "는다"}


def 낱말(s: str) -> set[str]:
    out = set()
    for w in re.findall(r"[가-힣A-Za-z0-9]{2,}", s or ""):
        if w in 흔한말 or w.startswith("대표"):
            continue
        out.add(w)
        if len(w) > 2 and re.match(r"[가-힣]", w):
            out.add(w[:2])
    return out


def 항목표(state_dir: Path) -> dict[str, str]:
    p = state_dir / "feed-labels.tsv"
    out = {}
    if p.is_file():
        for l in p.read_text(encoding="utf-8", errors="replace").splitlines():
            c = l.split("\t")
            if len(c) >= 3 and not c[0].startswith("#"):
                out[c[0]] = c[1]
    return out


def main() -> int:
    if len(sys.argv) < 3:
        return 0
    ledger = Path(sys.argv[1])
    새글, 주제 = sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else "")
    항목 = sys.argv[4] if len(sys.argv) > 4 else ""
    if not ledger.is_file():
        return 0
    rows = [l.split("\t") for l in ledger.read_text(encoding="utf-8", errors="replace").splitlines()]
    되돌림 = [c[2] for c in rows if len(c) > 2 and c[1] == "되돌림" and c[2].strip()]
    표 = 항목표(ledger.parent)
    새 = 낱말(새글) | 낱말(항목)
    후보 = []
    for c in rows:
        if len(c) < 3 or c[1] != "결정" or c[2] == 새글:
            continue
        글 = c[2]
        if any(k in 글 or 글 in k for k in 되돌림):
            continue
        점 = len(새 & (낱말(글) | 낱말(표.get(글, ""))))
        if 주제 and len(c) > 5 and c[5] == 주제:
            점 += 2
        if 점 >= 최소점수:
            후보.append((점, c[0], 글))
    if not 후보:
        return 0
    후보.sort(key=lambda x: -x[0])
    print("  🟡 이 결정이 바꾸는 앞 결정이 있나 보십시오 — 비슷한 살아 있는 결정(점수 순):")
    for 점, 날, 글 in 후보[:보일수]:
        print(f"     · [{날}] {글[:90]}  (점수 {점})")
    print("     [모델] 새 결정이 앞 결정을 바꾸면: ledger.sh 되돌림 \"<앞 결정 글 앞부분>\" — 일부만 바뀌면 되돌린 뒤 맞는 부분만 결정으로 다시 적으십시오")
    print("     [모델] 이 목록은 후보입니다 — 다른 말로 적힌 앞 결정은 여기 안 나올 수 있습니다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
