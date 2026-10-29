#!/usr/bin/env python3
"""기록 칸의 정의(`data/기록칸.tsv`)가 **적는 쪽과 맞나.**

🔴 왜 (2026-10-25,  → 옆 대화 품질 레드팀 ③):
   기록은 탭으로 가른 줄인데 **칸의 뜻이 둘째 칸(종류)마다 다르다.** 그래서 머리글을 둘 수
   없고, 무엇이 무엇인지 적힌 곳이 **저장소 어디에도 없었다.** 읽는 곳은 넷이고 넷이 각자
   «칸 번호»로 집는다.
   🔴 그것이 실제로 아팠다: 조종석 검사를 고칠 때 **어느 칸이 사람이 쓴 글이고 어느 칸이
     수인지 코드만 봐서는 못 가려서** 눕혀야 할지 말지 몰랐다. 결국 다 눕히는 쪽으로 정했다.

⭐ 그래서 `data/기록칸.tsv` 를 뒀다. ⛔ **그런데 손으로만 두면 반드시 낡는다** —
  이 저장소가 여러 번 치른 값이다. 그래서 이 검사가 **적는 쪽과 견준다.**


1. **적는 쪽에 있는데 표에 없는 종류** → 운다. 새 종류를 더하면 그날 잡힌다.
2. **칸 수가 다르다** → 운다. 적는 쪽이 칸을 하나 늘렸는데 표가 모르면, 읽는 쪽이
   엉뚱한 칸을 집는다.
3. **표에 있는데 적는 쪽에 없는 종류** → ⚠️ **적기만 한다.** 옛 판에서 적힌 줄이
   기록에 남아 있을 수 있어서, 지우라고 하지 않는다.
4. **꼴이 아는 말인가**(사람글·코드값·수·날·빈칸) → 모르는 말이면 운다.
   ⛔ 「사람글」이 이 표의 **쓸모**다 — 화면이 눕혀야 하는 칸을 그것으로 가린다.


- **기록 파일을 안 읽는다.** 거기에는 대표님 기록이 있고, 이 검사는 «꼴»만 본다.
  ⭐ 그래서 기록이 없는 컴퓨터에서도 돈다.
- **표를 고치지 않는다.** 보여만 준다 — 검사가 조용히 고치면 사람이 안 본다.

사용:  python3 lint_ledger_schema.py [저장소]
끝값:  1 = 어긋났다 · 0 = 맞는다
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

아는꼴 = ("사람글", "코드값", "수", "날", "빈칸")

_적는꼴 = re.compile(r"printf\s+'([^']*)'.*?>>\s*\"\$(STATE|NF_PERSON)\"")
_가지꼴 = re.compile(r"\s{0,4}([가-힣]+)\)\s*$")


def _문장들(원: str):
    """줄 끝이 `\\` 면 다음 줄과 **이어 붙인다.**

    🔴 2026-10-25: 처음엔 줄 단위로 봤다가 여러 줄에 걸친 `printf` 를 **1칸**으로 셌다
      (여덟 자리가 그랬다). 이어 붙이지 않으면 칸 수를 못 센다.
    """
    L = 원.split("\n")
    모음, 시작 = "", 0
    for i, l in enumerate(L, 1):
        if not 모음:
            시작 = i
        모음 += l.rstrip().rstrip("\\") if l.rstrip().endswith("\\") else l
        if l.rstrip().endswith("\\"):
            continue
        yield 시작, 모음, L
        모음 = ""


def 적는쪽(뿌리: Path):
    """종류 → 적는 **칸 수**들.

    ⭐ 종류가 `%s` 면 그 위 `case` 가지 이름이 종류다.
    ⛔ 기록 파일(`$STATE`)과 사람 자리(`$NF_PERSON`) **둘 다** 본다 — 꼴이 같다.
      ⚠️ `앱설정` 만 둘에 있고 칸 수가 다르다(기록 6칸 · 사람 자리 5칸) — 표는
        **둘을 다 적는다**(큰 쪽에 맞춘다).
    ⛔ 어느 `case` 가지인지 **모르면 짐작하지 않는다** — 그 자리는 그냥 넘긴다.
      🔴 처음엔 마지막 가지를 집었다가 `기능연결`(기록에 안 적고 기능 지도에 적는다)을
        잘못 집었다(2026-10-25 실측).
    """
    것들: dict = {}
    for q in sorted((뿌리 / "bin").rglob("*")):
        if not q.is_file() or q.suffix not in (".sh", ""):
            continue
        try:
            원 = q.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if q.suffix == "" and not 원.startswith("#!"):
            continue
        for n, 문장, L in _문장들(원):
            m = _적는꼴.search(문장)
            if not m:
                continue
            칸 = m.group(1).rstrip("\\n").split("\\t")
            if len(칸) < 2:
                continue
            종 = 칸[1]
            if 종 == "%s":
                가지 = [x.strip().rstrip(")") for x in L[:n - 1] if _가지꼴.match(x)]
                if not 가지:
                    continue
                종 = 가지[-1]
            것들.setdefault(종, set()).add(len(칸))
    return 것들


def 표읽기(길: Path):
    """종류 → {칸번호: (이름, 꼴)}. ⛔ 머리줄과 주석은 건너뛴다."""
    표: dict[str, dict] = {}
    나쁜꼴 = []
    if not 길.exists():
        return None, 나쁜꼴
    for n, 줄 in enumerate(길.read_text(encoding="utf-8").splitlines(), 1):
        if not 줄.strip() or 줄.startswith("#"):
            continue
        c = 줄.split("\t")
        if len(c) < 5 or c[0] == "종류":
            continue
        종류, 칸, 이름, 꼴 = c[0].strip(), c[1].strip(), c[2].strip(), c[3].strip()
        if 꼴 not in 아는꼴:
            나쁜꼴.append((n, 종류, 꼴))
        if not 칸.isdigit():
            나쁜꼴.append((n, 종류, "칸이 수가 아니다: %s" % 칸))
            continue
        표.setdefault(종류, {})[int(칸)] = (이름, 꼴)
    return 표, 나쁜꼴


def main() -> int:
    뿌리 = Path(sys.argv[1] if len(sys.argv) > 1 else
                Path(__file__).resolve().parent.parent).resolve()
    표길 = 뿌리 / "data" / "기록칸.tsv"
    표, 나쁜꼴 = 표읽기(표길)
    if 표 is None:
        print("  ⛔ 칸 정의 표가 없어 **재지 못했습니다**: %s" % 표길.relative_to(뿌리))
        return 1

    적는것 = 적는쪽(뿌리)

    아픔 = 0
    공통 = 표.get("*", {})
    print("=== 기록 칸 정의 — 종류 %d가지 · 적는 쪽에 %d가지 ==="
          % (len([k for k in 표 if k != "*"]), len(적는것)))

    없는것 = sorted(k for k in 적는것 if k not in 표)
    if 없는것:
        아픔 = 1
        print("\n  🔴 **적는데 정의가 없는 종류 %d가지** — 읽는 쪽이 칸을 짐작하게 됩니다."
              % len(없는것))
        print("     ⛔ 이 표가 «무엇이 무엇인지» 적힌 **하나뿐인 자리**입니다.")
        for k in 없는것:
            print("       · %s  (적는 칸 수: %s)" % (k, sorted(적는것[k])))

    어긋남 = []
    for 종류, 칸수들 in sorted(적는것.items()):
        if 종류 not in 표 or not 칸수들:
            continue
        정의칸 = set(표[종류]) | set(공통)
        가장큰 = max(정의칸) if 정의칸 else 0
        if 가장큰 not in 칸수들:
            어긋남.append((종류, sorted(칸수들), 가장큰))
    if 어긋남:
        아픔 = 1
        print("\n  🔴 **칸 수가 다릅니다 %d가지** — 읽는 쪽이 엉뚱한 칸을 집습니다." % len(어긋남))
        for 종류, 적는수, 정의수 in 어긋남:
            print("       · %-10s 적는 쪽 %s · 정의 %d칸" % (종류, 적는수, 정의수))

    if 나쁜꼴:
        아픔 = 1
        print("\n  🔴 **모르는 꼴 %d곳** — 아는 꼴: %s" % (len(나쁜꼴), " · ".join(아는꼴)))
        print("     ⛔ 「사람글」이 이 표의 쓸모입니다 — 화면이 눕혀야 하는 칸을 그것으로 가립니다.")
        for n, 종류, 꼴 in 나쁜꼴[:8]:
            print("       · %d줄  %s → %s" % (n, 종류, 꼴))

    if not 아픔:
        사람글 = sum(1 for v in 표.values() for _, (_, 꼴) in v.items() if 꼴 == "사람글")
        print("\n  ✅ 적는 쪽과 맞습니다. 칸 정의 %d개 중 **사람이 쓴 글이 %d개**입니다."
              % (sum(len(v) for v in 표.values()), 사람글))
        print("     ⭐ 화면은 그 %d개를 **반드시 눕혀야** 합니다(남의 폴더를 여실 수 있습니다)." % 사람글)

    남는것 = sorted(k for k in 표 if k != "*" and k not in 적는것)
    if 남는것:
        print("\n  ⚠️ 정의는 있는데 **지금 적는 곳이 없는 종류 %d가지**: %s"
              % (len(남는것), " · ".join(남는것)))
        print("     ⛔ 지우라고 하지 않습니다 — 옛 판에서 적힌 줄이 기록에 남아 있을 수 있고,")
        print("        그러면 읽는 쪽이 그 줄의 칸을 알아야 합니다.")
    print("\n  ⚠️ 이 검사는 **기록 파일을 읽지 않습니다** — 거기에는 사용자 기록이 있습니다.")
    print("     꼴만 봅니다. 그래서 기록이 없는 컴퓨터에서도 돕니다.")
    print("  ⚠️ 그리고 **적는 쪽만** 봅니다 — «읽는 쪽이 맞는 칸을 집나»는 안 봅니다.")
    print("     ⛔ 안 적으면 「다 막았다」로 읽힙니다. 읽는 쪽은 종류마다 다른 칸을 집어서,")
    print("        글만 보고 «그 줄이 어느 종류인가»를 알 수 없습니다(실측: 읽는 곳 둘이")
    print("        1~6칸을 번호로만 집습니다). 그 자리는 사람이 보셔야 합니다.")
    return 아픔


if __name__ == "__main__":
    sys.exit(main())
