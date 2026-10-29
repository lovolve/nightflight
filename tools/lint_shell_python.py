#!/usr/bin/env python3
"""셸 파일 안에 **파이썬이 얼마나 남았나** — 도구가 닿지 않는 자리를 센다.

🔴 왜 (2026-10-25, ):
   배포물 109개·33,185줄 중 **셸 파일 안에 든 파이썬이 2,019줄**이었다(실측).
   ⛔ 그 자리에는 **아무 도구도 닿지 않는다** — 린터·형식 검사·시험이 다 비껴간다.
     하루에 그 안에서 셋이 났다: 한글 변수 이름(zsh 가 못 읽는데 `bash -n` 은 통과) ·
     겹따옴표 속 백틱이 실제로 명령을 돌린 것 · `BASH_SOURCE` 가 비어 조용히 되돌림 값으로 간 것.
   ⛔ `-c '…'` 꼴이면 **파이썬 코드에 홑따옴표를 한 글자도 쓸 수 없다**(셸이 그것으로 감싼다).
     실측: 빼낸 345줄에 `'` 가 0개였다. 코드가 그 제약에 맞춰 비틀려 있었다.
   ⛔ 그리고 파이썬 경고가 `2>/dev/null` 에 **삼켜진다**. 빼내는 순간 하나가 드러났다
     (`"\\["` 잘못된 탈출 — 지금은 우연히 돌지만 다음 판에서 깨진다).
   ⭐ 2026-10-25 에 아홉 토막 **1,645줄을 파일로 뺐다**(2,019 → 374줄).


1. **늘어나면 운다.** 지금 남은 줄 수를 적어 두고, 그보다 늘면 실패한다.
   ⛔ 「0 으로 만들라」가 아니다 — 열 줄 토막은 한눈에 읽히고, 빼면 파일만 늘어난다.
   ⭐ 막는 것은 **되돌아가는 것**이다. 큰 토막이 새로 생기면 그날 잡는다.
2. **한 토막이 문턱보다 크면 운다.** 큰 것 하나가 수백 줄짜리 눈먼 자리를 만든다.
3. **센 수를 찍는다.** 안 보이면 늘어난다(이 저장소가 아는 못이다).

사용:  python3 lint_shell_python.py [저장소]
끝값:  1 = 늘었거나 큰 토막이 있다 · 0 = 괜찮다
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

남은줄_한도 = 374
한토막_한도 = 35

_여는c = re.compile(r"python3\s+(?:-\w+\s+)*-c\s+'")
_헤러독 = re.compile(r"<<\s*'?([A-Za-z_]\w*)'?\s*$")


def 토막들(뿌리: Path):
    """셸 파일 안의 파이썬 토막. ⭐ POSIX 홑따옴표 안에는 탈출이 없다 —
    여는 `'` 다음 첫 `'` 가 닫는 것이라 **글자 자리로 정확히** 집을 수 있다.
    ⛔ 줄 단위로 어림하면 틀린다(실제로 두 번 틀렸다 — 426줄로 셌는데 5줄이었다)."""
    것들 = []
    for p in sorted((뿌리 / "bin").rglob("*")):
        if not p.is_file():
            continue
        try:
            s = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if p.suffix not in (".sh", "") or (p.suffix == "" and not s.startswith("#!")):
            continue
        이름 = str(p.relative_to(뿌리))
        for m in _여는c.finditer(s):
            닫 = s.find("'", m.end())
            if 닫 < 0:
                continue
            것들.append((s[m.end():닫].count("\n"), 이름, "-c", s.count("\n", 0, m.end()) + 1))
        L = s.split("\n")
        i = 0
        while i < len(L):
            h = _헤러독.search(L[i])
            if h and "python3" in L[i]:
                태그 = h.group(1)
                j = next((k for k in range(i + 1, len(L)) if L[k].strip() == 태그), None)
                if j:
                    것들.append((j - i - 1, 이름, "헤러독", i + 1))
                    i = j
            i += 1
    return 것들


def main() -> int:
    뿌리 = Path(sys.argv[1] if len(sys.argv) > 1 else
                Path(__file__).resolve().parent.parent).resolve()
    것들 = 토막들(뿌리)
    합 = sum(n for n, *_ in 것들)
    큰것 = sorted((x for x in 것들 if x[0] > 한토막_한도), reverse=True)

    print("=== 셸 안에 든 파이썬 — %s줄 · 토막 %d개 (도구가 닿지 않는 자리) ==="
          % (f"{합:,}", len(것들)))
    아픔 = 0
    if 합 > 남은줄_한도:
        아픔 = 1
        print("\n  🔴 **늘었습니다** — 적어 둔 %s줄보다 %s줄 많습니다."
              % (f"{남은줄_한도:,}", f"{합 - 남은줄_한도:,}"))
        print("     ⛔ 그 자리에는 린터도 형식 검사도 시험도 닿지 않습니다.")
        print("     ⭐ 파일로 빼십시오 — 빼면 그 뒤로는 도구가 대신 잡습니다.")
    if 큰것:
        아픔 = 1
        print("\n  🔴 **한 토막이 %d줄보다 큽니다 %d개** — 큰 것 하나가 눈먼 자리를 만듭니다."
              % (한토막_한도, len(큰것)))
        for n, f, 꼴, 줄 in 큰것[:6]:
            print("       · %4d줄  %s:%d (%s)" % (n, f, 줄, 꼴))
    if not 아픔:
        print("\n  ✅ 늘지 않았고, %d줄보다 큰 토막이 없습니다." % 한토막_한도)
        만드는쪽 = (뿌리 / "tests" / "run.sh").is_file()
        if 합 < 남은줄_한도 and 만드는쪽:
            print("     ⭐ %s줄 줄었습니다 — 이 파일의 `남은줄_한도` 를 %s 로 낮춰 두십시오."
                  % (f"{남은줄_한도 - 합:,}", f"{합:,}"))

    print("\n  ⚠️ 이 검사는 **`bin/` 만** 봅니다 — 거기가 받는 분에게 나가는 몸입니다.")
    print("  ⚠️ 그리고 **0 을 요구하지 않습니다.** 열 줄 토막은 한눈에 읽히고,")
    print("     빼면 파일만 늘어납니다. 막는 것은 «되돌아가는 것»입니다.")
    return 아픔


if __name__ == "__main__":
    sys.exit(main())
