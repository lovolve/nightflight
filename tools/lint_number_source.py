#!/usr/bin/env python3
"""대표가 «행동할» 숫자에 **출처**가 붙어 있는지 본다 — 돈 · 기간 · 비율.

왜 있나 (

  ⭐ 가르는 자리는 **「세상이 정한 것」과 「우리가 정하는 것」**이다.
     · 세상이 정한 것 — 구글 「12명 × 14일 연속」, 애플 심사, 사업자등록.
       **정확히 예측되고 코드로 못 줄인다.**
     · 우리가 정하는 것 — 「이 기능 며칠」, 「원가 얼마」. **AI 도 모른다.**

  🔴 실측(어느 앱 2026-09-29~30): 원가를 **47원 → 79원 → 56원 → 73원**으로 네 번 고쳤다.
     그런데 화면에서 「구글 14일」과 「20턴 73원」이 **똑같이 생겼다.**
     비개발자에게 가장 위험한 것은 **둘이 구별 안 되는 것**이다.

⭐ 이 검사는 「숫자가 맞나」를 판정하지 않는다(그건 기계가 못 한다) —
   `lint_citations.py` 와 같은 원칙으로 **출처가 적혀 있는지만** 본다. 안 적혀 있으면 그게 곧 안 한 것이다.

⛔ **시험 개수·줄 수 같은 숫자는 안 본다.** 대표가 그걸로 계획을 세우지 않는다.
   전부 검사하면 잡음이 나고, 잡음이 나면 검사기를 아무도 안 본다.

  사용:  python3 lint_number_source.py [기록.tsv]
"""
from __future__ import annotations
import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
import _root
import re
import sys
from pathlib import Path

MONEY = re.compile(r"\d[\d,]*\s*(원|달러|\$|USD|만원)")
SPAN = re.compile(r"\d+\s*(일|주|개월|달|년|시간)(?!\s*(뒤|후|전|째|간의))")
RATIO = re.compile(r"\d+(\.\d+)?\s*%")

OFFICIAL = ("공식", "원문", "지침", "가이드라인", "약관", "고시", "법령")
MEASURED = ("실측", "측정", "쟀", "재 봤", "확인함", "확인했", "실제로 돌려", "로그")
GUESSED = ("추정", "어림", "대략", "예상", "내 판단", "제 판단", "가정", "짐작", "모른다", "못 했다", "안 했")
SECOND = ("보도", "기사", "발표", "공지", "문의 답변")
CHOSEN = ("정한 값", "예시")
MARKS = OFFICIAL + MEASURED + GUESSED + SECOND + CHOSEN

SINCE = "2026-09-30"

SKIP_NEAR = ("시험", "테스트", "개 통과", "줄", "커밋", "건 중", "표본")
SKIP_LINE = ("표본", "건 중", "/147", "/20")


def flagged(text: str) -> str | None:
    if not text.strip():
        return None
    hit = MONEY.search(text) or SPAN.search(text) or RATIO.search(text)
    if not hit:
        return None
    if any(m in text for m in MARKS):
        return None
    if RATIO.search(text) and any(s in text for s in SKIP_LINE):
        return None
    around = text[max(0, hit.start() - 12): hit.end() + 12]
    if any(s in around for s in SKIP_NEAR):
        return None
    return hit.group(0).strip()


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else _root.ledger()
    if path.is_dir():
        path = _root.ledger()
    if not path.exists():
        print("✅ 기록이 아직 없습니다")
        return 0

    bad = []
    looked = 0
    old = 0
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        cols = line.split("\t")
        if len(cols) < 3:
            continue
        if cols[0] < SINCE:
            old += 1
            continue
        looked += 1
        kind = cols[1]
        whole = " ".join(cols[2:])
        if any(m in whole for m in MARKS):
            continue
        for col in cols[2:]:
            num = flagged(col)
            if num:
                bad.append((n, kind, num, col.strip()[:70]))
                break

    tail = f" (옛 줄 {old}개는 안 봤습니다 — {SINCE} 이전)" if old else ""
    if looked == 0 and old == 0:
        print(f"⛔ {path.name} 은 기록 형식이 아닙니다(탭 3칸 이상인 줄이 없습니다)"
              " — **검사하지 않았습니다.**")
        print("   ⚠️ 이건 「깨끗하다」가 아닙니다. 기록이 아직 없습니다.")
        return 0

    if not bad:
        print(f"✅ 돈·기간·비율에 전부 출처가 붙어 있습니다 ({looked}줄 봤습니다){tail}")
        return 0

    print(f"⚠️  출처가 안 붙은 숫자 {len(bad)}곳{tail} — 「공식 / 실측 / 추정」 중 하나를 적으십시오\n")
    for n, kind, num, sample in bad:
        print(f"  {path.name}:{n} [{kind}] 「{num}」")
        print(f"     {sample}")
    print("\n  ⭐ 세상이 정한 것(구글 14일)과 우리가 정하는 것(원가 73원)은 «다른 숫자»입니다.")
    print("     사용자는 화면만 보고 그걸 구별할 수 없습니다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
