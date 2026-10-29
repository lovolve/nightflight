#!/usr/bin/env python3
"""공개 관문 표가 **두뇌 원문보다 「쉽게」** 적혀 있나.

🔴 왜 (레드팀 2026-10-12): 하루에 찾은 어긋남 여섯 중 **넷이 한쪽**이었다 —
   「쉽게 3 · 안전하게 1」 대 「어렵게 2」. 레드팀 판정:
   「**한쪽으로 쏠리면 그건 실수가 아니라 «버릇»이다.**」

⭐⭐ 이 검사가 보는 것은 **방향**이다. 「수가 틀렸나」가 아니라
   **「원문에 있는데 공개 표에 없나」**를 본다 — 그게 쏠리는 꼴이다.

| 꼴 | 보는 법 |
|---|---|
| **원문이 「최대 N 이상」(하한)** | 공개 최대가 숫자면 🔴 — 하한을 상한으로 뒤집은 것이다 |
| **원문이 「… 도 최대 M」이라 더 붙는데** | 공개 표에 그 M 이 **덧붙임으로도** 없으면 🔴 |
| **원문에 최대가 없다** | 공개 최대가 숫자면 🔴 — 분위수를 최대로 부른 것이다 |

⛔ **두뇌가 없으면 「못 쟀다」고 말한다.** 사용자 맥에는 두뇌가 없다 —
   거기서 0 이 나오면 그건 「맞다」가 아니라 「대조할 바탕이 없다」다.
⛔ 그리고 **고치라고 하지 않는다** — 어느 쪽이 맞는지는 원문을 읽은 사람이 정한다.
   이 검사는 **방향이 쏠렸다는 것만** 말한다.

사용:  python3 lint_gate_bias.py [저장소]
종료:  1 = 「쉽게」 쪽으로 샌 자리가 있다 · 0 = 없거나 못 쟀다
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _root import root as _repo_root

import os


def _brain(root: Path):
    for c in (os.environ.get("NF_BRAIN"),
              root.parent / "nightflight-server" / "catalog" / "관문-기준값.tsv"):
        if c and Path(c).is_file():
            return Path(c)
    return None


LOWER = re.compile(r"up to [a-z]+ days? or longer|최대\s*\d+\s*일\s*이상|or longer")
NO_MAX = re.compile(r"처리 기간이? 원문에 없다|원문에 «?최대»?는 없다|알 수 없다|확인하지 않았다")
EXTRA = re.compile(r"(결제수단 확인|확인)은? ?(따로 )?최대\s*(\d+)\s*일")


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else _repo_root()
    gp = root / "data" / "관문.tsv"
    bp = _brain(root)
    if not gp.is_file():
        print("  ⚠️ 공개 출시 절차 표가 없어 **재지 못했습니다.**")
        return 0
    if bp is None:
        print("  ⚠️ 코어 원문이 없어 **대조하지 못했습니다** — 0 이 「맞다」가 아닙니다.")
        print("     (사용자 컴퓨터에는 코어가 없습니다. 이 검사는 만드는 쪽에서 돕니다.)")
        return 0

    pub = {}
    for line in gp.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or "\t" not in line:
            continue
        c = line.split("\t")
        if len(c) > 4:
            pub[c[0]] = {"이름": c[1], "최대": c[3], "확인": c[4],
                         "덧붙임": c[7] if len(c) > 7 else ""}
    bad = []
    for line in bp.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or "\t" not in line:
            continue
        c = line.split("\t")
        if len(c) < 3 or c[0] not in pub:
            continue
        src, g = c[2], pub[c[0]]
        if LOWER.search(src) and g["최대"].isdigit():
            bad.append((c[0], g["이름"], "원문은 «하한»(「이상」)인데 공개 표가 숫자를 «최대»로 적었다"))
        elif NO_MAX.search(src) and g["최대"].isdigit():
            bad.append((c[0], g["이름"], "원문에 최대가 없는데 공개 표가 숫자를 적었다"))
        m = EXTRA.search(src)
        if m and m.group(3) not in (g["최대"] + g["덧붙임"]):
            bad.append((c[0], g["이름"],
                        f"원문에 「{m.group(1)} 최대 {m.group(3)}일」이 더 있는데 공개 표가 말하지 않는다"))

    print(f"=== 공개 표가 코어 원문보다 «쉽게» 적힌 자리 — {len(bad)}곳 (출시 절차 {len(pub)}개 대조) ===")
    if not bad:
        print("  ✅ 「쉽게」 쪽으로 샌 자리가 없습니다.")
        print("  ⚠️ 이 검사는 **세 꼴**만 봅니다(하한을 상한으로 · 없는 최대 · 빠뜨린 지연) —")
        print("     0 이 「전부 맞다」는 뜻은 아닙니다. 조건이 좁은 쪽은 사람이 대조해야 합니다.")
        return 0
    for n, name, why in bad:
        print(f"  🔴 출시 절차 {n} {name}")
        print(f"       {why}")
    print("\n  ⛔ 어느 쪽이 맞는지는 **원문을 읽은 사람**이 정합니다 — 이 검사는 방향만 말합니다.")
    print("  ⭐ 「최대」가 아닌 값은 **덧붙임 칸**에 둡니다(그 칸이 그래서 있습니다).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
