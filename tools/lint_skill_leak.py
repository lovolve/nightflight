#!/usr/bin/env python3
"""공개 쪽에 **노하우가 샜나** — `skills/*/SKILL.md` 를 본다.

🔴 왜 (기획 §43-6 · 창업자 구술 2026-09-23):
   **본체는 서버에서 내려온다**
   손발(`~/nightflight`)은 **공개**이고 두뇌는 **비공개·유료**다. 그래서 단계 지침을
   공개 쪽에 적으면 **파는 것을 공짜로 주는 것**이 된다.

🔴 **그리고 2026-10-04 에 내가 실제로 그랬다.** 껍데기 여덟을 채웠는데,
   §43-6 이 *「7줄 8개는 아직 비어 있어 «샐 것이 없다»… **채우는 작업이 곧 노하우를
   공개하는 작업**이 된다」* 고 **미리 적어 뒀다.** 나는 그 절을 안 읽었다.
   ⭐ 그래서 문서가 아니라 **검사**로 만든다 — §43-6 이 그렇게 적어 뒀다.

§43-6 이 그은 선 그대로 본다.

| 공개 쪽에 둬도 되는 것 | 두뇌 서버에만 |
|---|---|
| 단계 이름 · 서버에 묻는 껍데기 | **단계의 실제 절차** |
| 「무엇을 검사하는지」 | **사고 이력에서 나온 증상 표** |
| 훅 배선 · 기록 형식 | 판정 기준 · 반려 대응법 · 레드팀 브리프 |

⛔ **못 둘**
 1. **길이로 재지 않는다.** 긴 글이 아니라 **«무엇이 적혀 있나»**가 문제다
 2. **⛔ 못 목록은 샘이 아니다** — 그건 제품의 성격이고 화면에 어차피 드러난다.
    ⭐ 가르는 기준: **「이것만 보고 남이 따라 할 수 있나」.**

보는 것 셋
 ① **사고 이력** — 앱 이름 + 날짜가 같이 있는 줄(= 남의 값으로 산 경험)
 ② **증상 표** — 「증상 / 원인」처럼 두 칸이 짝으로 선 표
 ③ **실측 수치** — 「실측 N」·「N건」·「N개 중」 같은 측정값

사용:  python3 lint_skill_leak.py
종료:  1 = 샜다 · 0 = 깨끗하다
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_history_leak import APPS as _APPS
APPS = "|".join(re.escape(a) for a in _APPS) if _APPS else r"(?!)"
_앱이름있나 = bool(_APPS)
DATE = r"20\d\d-\d\d-\d\d"
SYMPTOM = r"(증상|원인)\s*\|.*\|"
MEASURED = r"(실측|전수)\s*[0-9]|[0-9]+\s*건(?!수)|[0-9]+\s*개\s*중"


def main() -> int:
    bad = []
    for f in sorted((HERE / "skills").glob("*/SKILL.md")):
        rel = f.relative_to(HERE)
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, raw in enumerate(lines, 1):
            if "§43-6" in raw or "lint_skill_leak" in raw or raw.lstrip().startswith(">"):
                continue
            why = []
            if re.search(APPS, raw) and re.search(DATE, raw):
                why.append("사고 이력(앱 이름 + 날짜)")
            elif re.search(APPS, raw):
                why.append("사고 이력(앱 이름)")
            if re.search(SYMPTOM, raw):
                why.append("증상 표")
            if re.search(MEASURED, raw):
                why.append("실측 수치")
            if why:
                bad.append((rel, i, raw.strip()[:64], why))

    if not bad:
        if not _앱이름있나:
            print("  ⚠️ 남의 앱 이름 목록이 없어 **그 갈래는 재지 못했습니다**(「없다」가 아닙니다).")
            print("     ⭐ 그 목록은 **받는 분에게 안 갑니다** — 남의 앱 이름을 보낼 일이 없습니다.")
        print("  ✅ 공개 쪽 단계 지침에 노하우가 없다")
        print("     ⚠️ 이 검사는 «세 모양»만 본다(사고 이력·증상 표·실측 수치) —")
        print("        0 이 「전부 안전」은 아니다. 가르는 기준은 «남이 따라 할 수 있나»다")
        return 0

    print("── 공개 쪽에 노하우가 샜다 ──────────────────────")
    for rel, i, txt, why in bad[:12]:
        print(f"  🔴 {rel}:{i}  {' · '.join(why)}")
        print(f"     「{txt}」")
    if len(bad) > 12:
        print(f"  … {len(bad) - 12}곳 더")
    print()
    print("  ⛔ 이것은 **파는 것**이다 — 공개 쪽에 두면 복사된다(창업자 구술).")
    print("     코어의 `catalog/<단계>-처방.md` 로 옮기고, 공개 쪽에는")
    print("     **단계 이름 · 결정 번호 · ⛔ 못 · 「코어에 묻는다」**만 남긴다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
