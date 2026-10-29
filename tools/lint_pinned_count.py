#!/usr/bin/env python3
"""**지금을 말하는 검사 수**가 글에 박혀 있나 — 그리고 실제와 다르나.

🔴 왜 (2026-10-12): 「검사 8종」이 공개 쪽 `AGENTS.md` 에 적혀 있었고 실제는 **16**이었다.
   같은 수가 일곱 가지로 흩어져 있었다 — 7종·8종·8개·14종·14개·15개·16개·열일곱·열여덟.
   이 저장소의 표준이 답을 이미 적어 뒀다 — 「**세는 법을 적고 수는 안 박는다**」.

⭐⭐ **이력의 수는 «고치지 않는다»** (전역 규칙 0, 2026-10-12):
   · 누군가 그걸 한다 → 규칙 → 검사로
   · 아무것도 안 깨진다 → 상태 → 한 곳에만
   · **같은 사고를 다시 겪는다 → 이력 → 그대로 둔다**
   「검사가 14종인데 자동으로 도는 것이 0개였다(실측 2026-09-30)」는 **그날의 사실**이다.
   ⛔ 그걸 16으로 고치면 **사고 기록이 거짓**이 된다.
   ⭐ 그래서 **날짜가 붙은 줄은 세지 않는다.** 날짜가 「이건 이력이다」의 표지다.

⛔ 「수가 박혀 있다」를 다 잡지 않는다 — 상태 수백 곳이 울면 목록이 안 읽힌다.
   **지금을 말하면서 실제와 «다른» 것**만 잡는다. 좁고 전부 진짜다.

사용:  python3 lint_pinned_count.py [저장소]
종료:  1 = 틀린 수가 박혀 있다 · 0 = 없다
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _root import root as _repo_root

PIN = re.compile(r"검사[가는]?\s*\**\s*(\d+|[일이삼사오육칠팔구십열스]{1,4})\s*\**\s*([종개])")
DATED = re.compile(r"20\d\d[-./]\d{1,2}|20\d\d년")

NOW_PIN = re.compile(r"지금은.{0,40}?\*{0,2}(\d+)\*{0,2}\s*(건|곳|개)")
NOW_OK = re.compile(r"📌\s*이력|지금수검사:\s*찾는 말이다")
HAN = {"일": 1, "이": 2, "삼": 3, "사": 4, "오": 5, "육": 6, "칠": 7, "팔": 8, "구": 9,
       "십": 10, "열": 10, "열하나": 11, "열둘": 12, "열셋": 13, "열넷": 14, "열다섯": 15,
       "열여섯": 16, "열일곱": 17, "열여덟": 18, "스물": 20}
LOOK = ("*.md", "bin/*.sh", "bin/ledger.d/*.sh", "tools/*.py", "data/*.tsv", "skills/*/SKILL.md")


KINDS = ("lint_*.py", "check_*.py", "count_*.py")


def _센다(root: Path) -> int:
    """⭐ **폴더가 목록이다.** 수를 여기 적지 않는다."""
    got = set()
    for k in KINDS:
        got |= {f.name for f in (root / "tools").glob(k)}
    return len(got)


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--센다":
        rt = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else _repo_root()
        print(_센다(rt))
        return 0
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else _repo_root()
    real = _센다(root)
    if real == 0:
        print("  ⚠️ 검사 파일을 못 찾아 **재지 못했습니다** — 「박힌 수가 없다」가 아닙니다.")
        return 0
    bad, dated, now_pin, said_now = [], 0, [], []
    seen = set()
    for pat in LOOK:
        for f in sorted(root.glob(pat)):
            if ".git" in f.parts or f.resolve() in seen:
                continue
            seen.add(f.resolve())
            try:
                lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            for i, line in enumerate(lines, 1):
                for m in PIN.finditer(line):
                    raw = m.group(1)
                    n = int(raw) if raw.isdigit() else HAN.get(raw)
                    if n is None or n == real:
                        continue
                    if DATED.search(line):
                        dated += 1
                        continue
                    bad.append((f, i, n, line.strip()[:76]))
                if NOW_PIN.search(line):
                    if NOW_OK.search(line):
                        said_now.append(f"{f.name}:{i}")
                    else:
                        now_pin.append((f, i, line.strip()[:76]))
    if now_pin:
        print(f"=== 「지금은 … N건」이라고 **현재를 주장하며 수를 박은 자리** {len(now_pin)}곳 ===")
        for f, i, txt in now_pin:
            print(f"  🔴 {f}:{i}")
            print(f"     「{txt}」")
        print()
        print("  ⭐ 날짜가 붙어 있어도 **「지금은」이라고 하면 이력이 아닙니다** —")
        print("     날짜는 「언제 쟀나」이고 「지금은」은 「지금 그렇다」입니다.")
        print("  ⭐ 고치는 길: 지난 수는 **「📌 이력:」 밑으로** 옮기고, 현재는 **검사가 말하게** 둡니다.")
        print("     (일부러 그 말을 찾는 자리면 `지금수검사: 찾는 말이다` 라고 선언합니다.)")
        return 1
    if said_now:
        print(f"  ⚠️ 「지금은 … N건」 꼴 {len(said_now)}곳은 「찾는 말이다」라고 **선언해서** "
              f"넘겼습니다 — {' · '.join(said_now[:5])}")
    print(f"=== 지금을 말하면서 «실제와 다른» 검사 수 — {len(bad)}곳 (실제 {real}개) ===")
    if dated:
        print(f"  ⭐ 날짜가 붙은 {dated}곳은 **이력이라 안 잡았습니다** — 그날의 사실입니다.")
    if not bad:
        print("  ✅ 틀린 수가 박혀 있지 않습니다.")
        print("  ⚠️ 이 검사는 **꼴 둘**만 봅니다(「검사 N종|개」 · 「지금은 … N건」) — 0 이 「수가 전부 맞다」는 뜻은 아닙니다.")
        return 0
    for f, i, n, txt in bad[:12]:
        try:
            rel = f.relative_to(root)
        except ValueError:
            rel = f
        print(f"  🔴 {rel}:{i} — 「{n}」이라고 적혀 있고 실제는 {real}")
        print(f"       {txt}")
    print("\n  ⭐ 고치는 법: **세는 법을 적고 수는 안 박습니다**(README 선). 폴더가 목록입니다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
