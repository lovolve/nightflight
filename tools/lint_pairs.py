#!/usr/bin/env python3
"""야간비행 도구"""
from __future__ import annotations
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import file_pairs as P

GAP = 6 * 3600


def main() -> int:
    lp = Path(os.environ.get("NF_LEDGER") or (Path(os.environ.get("NF_STATE", ".claude")) / "ledger.tsv"))
    root = Path(os.environ.get("NF_ROOT") or os.getcwd())
    state = Path(os.environ.get("NF_STATE") or (root / ".claude"))
    sess = os.environ.get("NF_SESSION") or os.environ.get("CLAUDE_CODE_SESSION_ID") or ""
    pairs = P.짝들(lp, root)
    if not pairs:
        return 0
    touched = set()
    try:
        for line in (state / "internal" / "repeat-guard.tsv").read_text(encoding="utf-8").splitlines():
            c = line.split("\t")
            if len(c) >= 2 and (not sess or c[0] == sess):
                touched.add(str(Path(c[1]).resolve()))
    except OSError:
        pass
    hits = []
    for a, b, at, bt, why in pairs:
        for x, y, xt, yt in ((a, b, at, bt), (b, a, bt, at)):
            if str(x.resolve()) not in touched:
                continue
            if str(y.resolve()) in touched or P._mtime(y) >= P._mtime(x) - GAP:
                continue
            if P.확인됨(lp, root, x):
                continue
            hits.append((xt, yt, why))
    if not hits:
        return 0
    print(f"🔴 짝 파일 중 한쪽만 고쳤습니다 — {len(hits)}곳")
    for xt, yt, why in hits:
        print(f"   · {xt} 를 고쳤는데 {yt} 는 그대로입니다 — {why}")
    print('   [모델] 다른 쪽도 고치거나, 바꿀 것이 없으면 ledger.sh 짝확인 "<고친 파일>" "<까닭>" 을 적으십시오.')
    return 1


if __name__ == "__main__":
    sys.exit(main())
