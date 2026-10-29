#!/usr/bin/env python3
"""공개 쪽 관문 표에 **기준값이 샜나**.

🔴 왜 (기획 §43-6 · 창업자 2026-10-05 승인):
   §43-6 의 표가 「검사가 대조하는 **기준값**(관문 표 · 규정 최신본)」을
   **두뇌 서버에만** 두라고 적었다. 그런데 **2026-10-04 에 내가 공개 쪽에 만들었다** —
   날수·조항 원문·확인 등급·읽은 날까지 전부.

⭐ 가른 선 (.**

| 공개(`data/관문.tsv`) | 두뇌(`catalog/관문-기준값.tsv`) |
|---|---|
| 번호 · 이름 · **조건식** · 시작 · 받으면 | **최대 날수** · **조항 원문** · 확인 등급 · **읽은 날** |

⛔ 조건식은 베껴도 쓸모가 적다 — **값이 있는 것은 원문으로 확인한 날짜와 조항**이고
   그것을 **최신으로 유지하는 일**이 파는 것이다.

⛔ **주석은 세지 않는다** — 머리에 가른 날짜(2026-10-05)가 적혀 있고 그건 값이 아니다.
   이 저장소가 이미 적어 둔 오탐이다(사고 기록이 옛 문장을 인용한다).

사용:  python3 lint_gate_leak.py
종료:  1 = 샜다 · 0 = 깨끗하다
"""
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
PUB = Path(os.environ.get("NF_GATE_TABLE") or (HERE / "data" / "관문.tsv"))
LEAK = (
    (r"20\d\d-\d\d-\d\d", "우리가 읽은 날"),
    (r"[0-9]\.[0-9](\.[0-9])?\s*(원문|지침|조)", "조항 번호"),
    (r"(공식 안내|공식\)|원문 확인|지침|원문:)", "조항 원문"),
)


def main() -> int:
    if not PUB.exists():
        print("  ⚠️ 공개 출시 절차 표를 못 찾아 **재지 못했습니다**")
        return 0
    bad = []
    for i, raw in enumerate(PUB.read_text(encoding="utf-8").splitlines(), 1):
        if raw.lstrip().startswith("#") or "\t" not in raw:
            continue
        cols = raw.split("\t")
        rest = "\t".join(cols[5:]) if len(cols) > 5 else ""
        for pat, why in LEAK:
            if re.search(pat, rest):
                bad.append((i, raw.strip()[:60], why))
                break
    if not bad:
        print("  ✅ 공개 출시 절차 표에 셈만 있다 — 날짜·조항은 코어에 있다")
        print("     ⚠️ 이 검사는 «값의 모양»만 본다 — 0 이 「전부 안전」은 아니다")
        return 0
    print("── 공개 출시 절차 표에 기준값이 샜다 ──────────────────")
    _어디 = "data/관문.tsv" if PUB == HERE / "data" / "관문.tsv" else str(PUB)
    for i, txt, why in bad[:10]:
        print(f"  🔴 {_어디}:{i}  {why}")
        print(f"     「{txt}」")
    print()
    print("  ⛔ 이것이 **파는 것**이다(기획 §43-6) — 코어의")
    print("     `catalog/관문-기준값.tsv` 로 옮기고 공개 쪽에는 **조건식만** 남긴다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
