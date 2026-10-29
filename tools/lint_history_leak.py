#!/usr/bin/env python3
"""공개 쪽 **주석**에 사고 이력이 남아 있나

🔴 **왜 있나** — 두뇌 `README.md` 가 스스로 적어 뒀다(레드팀이 넓힌 선):
   「`SKILL.md` 하나가 아니라 **`tools/`·`bin/` 주석**이 13배 크다.
   그 주석은 아직 `~/nightflight` 에 있다. **다음 작업이다.**」
   ⛔ 창업자: **본체는 서버에서 내려온다**

🔴 그리고 **저장소를 공개로 바꾸려는 순간**에 이것이 걸림돌이다(). 공개하면 **이력까지 다 보인다.**


| | 공개에 남는다 | 두뇌로 간다 |
|---|---|---|
| **못 자체** — 「⛔ 0 을 「없었다」로 찍지 않는다」 | ✅ 남는다. 없으면 **코드를 읽을 수 없다** | |
| **남의 앱 이름** — 목록(`data/다른앱.tsv`)에 적은 것 | | 🔴 **간다.** 노하우와 별개로 **다른 앱의 사생활**이다 |
| **실측 수치·사고 서술** — 「하루에 아홉 건」·「15시간 동안 매 턴」 | | 🔴 **간다.** 그게 파는 것이다 |

⛔ **못까지 지우지 않는다.** 못이 사라지면 다음 사람이 같은 자리를 다시 밟는다 —
그건 노하우를 지키려고 **제품을 망가뜨리는** 것이다.


⛔ **「사고 서술」을 기계가 정확히 가를 수 없다.** 그래서 **하나만** 센다 — **앱 이름**.
🔴 처음엔 「날짜 + 실측」도 셌는데 **41곳이 전부 거짓 경보**였다(아래 주석).
⭐ 「0 이 전부 안전」이 아니다 — 사람이 한 번은 훑어야 한다.
"""
import re
import sys
from pathlib import Path

def _앱이름들():
    길 = Path(__file__).resolve().parent.parent / "data" / "다른앱.tsv"
    if not 길.is_file():
        return ()
    이름 = []
    for l in 길.read_text(encoding="utf-8").split("\n"):
        l = l.strip()
        if l and not l.startswith("#"):
            이름.append(l.split("\t")[-1].strip())
    return tuple(이름)


APPS = _앱이름들()


def _우리이름들():
    """「우리<탭>이름」으로 적힌 것 — 만드는 회사 자기 이름이다."""
    길 = Path(__file__).resolve().parent.parent / "data" / "다른앱.tsv"
    if not 길.is_file():
        return ()
    난것 = []
    for l in 길.read_text(encoding="utf-8").split("\n"):
        l = l.strip()
        if l and not l.startswith("#") and l.split("\t")[0].strip() == "우리":
            난것.append(l.split("\t")[-1].strip())
    return tuple(난것)


OURS = _우리이름들()
_주소꼴 = (re.compile(r"(?<![A-Za-z0-9@.])(" + "|".join(OURS) + r")/[A-Za-z0-9._-]")
           if OURS else re.compile(r"(?!)"))
DATE = re.compile(r"20\d\d-\d\d-\d\d")
SKIP_FILES = {"lint_history_leak.py", "다른앱.tsv"}
LOOK = ("*.md", "tools/*.py", "tools/*.sh", "bin/*.sh", "bin/ledger.d/*.sh", "tests/*.sh", "tests/*.js",
        "hooks/*.json", "skills/*/SKILL.md", "board/*.html", "data/*.tsv")


NAMES_OK = re.compile(r"유출검사:\s*이름을 말하는 자리")
SAID = []


def _본다(line: str, path: Path) -> bool:
    """⛔ 「주석이냐」로 가르지 않는다. 표지를 단 줄만 넘긴다."""
    return not NAMES_OK.search(line)


_ENG = tuple(a for a in APPS if a.isascii())
_KOR = tuple(a for a in APPS if not a.isascii())
_ENG_RE = (re.compile(r"(?<![A-Za-z0-9@.])(" + "|".join(_ENG) + r")(?![A-Za-z0-9.]*\.[a-z])")
           if _ENG else re.compile(r"(?!)"))


def _이름찾기(line: str):
    """이 줄에 있는 앱 이름들. ⛔ 긴 이름을 짧은 이름으로 두 번 세지 않는다.

    🔴 **띄어쓰기가 있으면 못 잡았다** (2026-10-12). 화면에 보이는 이름은
      사람은 **띄어서** 쓰고 목록에는 붙여 적혀 있었다.
      ⛔ 조종석 제목이 바로 그 꼴이었다 — 가장 눈에 띄는 자리를 못 봤다.
      ⭐ 그래서 **띈 것을 붙여서** 견준다. 목록에 꼴을 두 벌 적지 않는다(한 곳이다).
    """
    out = []
    flat = line.replace(" ", "")
    rest = flat
    for a in _KOR:
        if a in rest:
            out.append(a)
            rest = rest.replace(a, " ")
    주소든것 = {m.group(1) for m in _주소꼴.finditer(line)}
    out += sorted({m.group(1) for m in _ENG_RE.finditer(line)} - 주소든것)
    return out


HOME = Path(__file__).resolve().parent.parent


def _뿌리() -> Path:
    return Path(sys.argv[1]) if len(sys.argv) > 1 else HOME


def main() -> int:
    root = _뿌리()
    apps, meas, seen = [], [], 0
    for g in LOOK:
        for f in sorted(root.glob(g)):
            if f.name in SKIP_FILES or not f.is_file():
                continue
            try:
                lines = f.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, OSError):
                continue
            rel = f.relative_to(root)
            for i, ln in enumerate(lines, 1):
                if not _본다(ln, f):
                    SAID.append(f"{f.relative_to(root)}:{i}")
                    continue
                seen += 1
                hit = _이름찾기(ln)
                if hit:
                    apps.append((rel, i, " · ".join(hit), ln.strip()[:60]))


    def _표지도_말한다():
        if SAID:
            print(f"     ⚠️ {len(SAID)}곳은 「이름을 말하는 자리」라고 **선언해서** 넘겼습니다 —")
            print("        " + " · ".join(SAID[:8]))

    if not apps and not meas:
        if not APPS:
            print(f"  ⚠️ 볼 앱 이름이 없어 **재지 못했습니다** ({seen:,}줄 봤지만 견줄 이름이 0개).")
            print("     ⭐ 그 목록(`data/다른앱.tsv`)은 **받는 분에게 안 갑니다** —")
            print("        남의 앱 이름을 보낼 일이 없습니다. 그래서 받는 분 쪽에서는 늘 비어 있습니다.")
        else:
            print(f"  ✅ 공개 쪽에 남의 앱 이름이 없습니다 ({seen:,}줄 봤습니다)")
        print("     ⚠️ 이 검사는 **앱 이름만** 봅니다 — 「사고 서술」은 기계가 못 가릅니다.")
        print("        0 이 「전부 안전」은 아닙니다. 공개 전에 사람이 한 번은 훑어야 합니다.")
        _표지도_말한다()
        return 0

    print("── 공개 쪽 주석에 사고 이력이 남아 있다 ──────────")
    print()
    if apps:
        print(f"  🔴 **남의 앱 이름 {len(apps)}곳** — 공개하면 그 앱들의 사고가 같이 나갑니다")
        for rel, i, who, txt in apps[:14]:
            print(f"     {rel}:{i}  [{who}]")
            print(f"        「{txt}」")
        if len(apps) > 14:
            print(f"     … 그리고 {len(apps) - 14}곳 더")
        print()
    if meas:
        print(f"  ⚠️ **날짜 + 실측이 같은 줄에 있는 것 {len(meas)}곳** — 그게 파는 것입니다")
        for rel, i, txt in meas[:8]:
            print(f"     {rel}:{i}  「{txt}」")
        if len(meas) > 8:
            print(f"     … 그리고 {len(meas) - 8}곳 더")
        print()
    print("  ⭐ 고치는 길: **못은 남기고 «이야기»만 야간비행 서버로 옮깁니다.**")
    print("     ⛔ 못까지 지우지 마십시오 — 못이 사라지면 다음 사람이 같은 자리를 다시 밟습니다.")
    print(f"     ⚠️ {seen:,}줄을 봤고, 이 검사는 **이름만** 봅니다(0 이 전부 안전은 아닙니다).")
    _표지도_말한다()
    return 1


if __name__ == "__main__":
    sys.exit(main())
