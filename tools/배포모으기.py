#!/usr/bin/env python3
"""받는 사람에게 나갈 것만 **한 폴더로 모은다** — 새 저장소에 올릴 몸이다.

⭐ .
   🔴 왜 고치는 게 아니라 새로 만드나: 지난 커밋 231개 중 **68개가 대표님 기록**을,
     **54개가 이 컴퓨터 상태**를 담고 있다. **지금 지워도 지난 커밋에 그대로 남아 읽힌다.**
   ⛔ 그날 손으로 고르면 섞인다 — 그래서 **목록**(`data/배포.tsv`)과 **이 도구**로 둔다.


1. **검사를 먼저 돌리고, 울면 멈춘다.** 분류 안 된 파일이 하나라도 있으면 안 모은다 —
   분류가 빈 채로 나가는 것이 이 사고의 모양이었다.
2. **덮어쓰지 않는다.** 나갈 폴더에 이미 무엇이 있으면 멈춘다(`--덮어쓰기` 로만 넘긴다).
   전역 규칙: 「지우거나 덮어쓰는 도구는 돌리기 전에 눈으로 확인한다」.
3. **옮긴 뒤 다시 센다.** 센 수와 실제로 생긴 파일 수가 다르면 **실패라고 말한다**
   (`tools/clean_disk.sh` 머리의 사고 이력 3 과 같은 못 — 실패를 성공으로 찍은 적이 있다).
4. **기본은 «보여만» 준다.** 실제로 모으려면 `--모아` 를 준다.
5. **마켓플레이스가 가리키는 자리가 이 폴더 안에 있나 본다.** 없으면 **깔리지 않는데**
   올리는 날까지 아무도 모른다(2026-10-25 에 더했다 — 공식 44개를 재 보고 알았다).
6. **`.gitignore` 에서 「기록을 다시 여는 줄」을 꼴로 걷는다.** 이 저장소에서는 그것이
   내용이라 일부러 담지만, 받는 분에게는 **그분의 기록**이다(2026-10-25).
   ⛔ 낱개 이름이 아니라 꼴이다 — 줄이 늘어도 따라온다.

사용:  python3 배포모으기.py <나갈 폴더>
       python3 배포모으기.py <나갈 폴더> --모아
끝값:  1 = 못 했다 · 0 = 했다
"""
import json
import re
import shutil
import sys
from pathlib import Path

여기 = Path(__file__).resolve().parent
sys.path.insert(0, str(여기))
import lint_distribution as 검사


걷을꼴 = re.compile(r"^\s*!\s*\.claude/")


def 기록여는줄걷는다(나갈곳: Path, 뿌리: Path) -> int:
    """나가는 `.gitignore` 에서 **기록을 다시 여는 줄을 꼴로 걷는다.**"""
    글길 = 나갈곳 / ".gitignore"
    원글 = 뿌리 / ".gitignore"
    if not 글길.exists():
        return 0
    있던수 = 0
    if 원글.exists():
        있던수 = sum(1 for 줄 in 원글.read_text(encoding="utf-8").split("\n")
                     if 걷을꼴.match(줄))
    줄들 = 글길.read_text(encoding="utf-8").split("\n")
    남길 = [줄 for 줄 in 줄들 if not 걷을꼴.match(줄)]
    걷은 = [줄.strip() for 줄 in 줄들 if 걷을꼴.match(줄)]
    if 있던수 and not 걷은:
        print("\n  🔴 **기록을 여는 줄이 원본에는 %d줄 있는데 나가는 몸에는 0줄입니다.**" % 있던수)
        print("     ⛔ 둘이 다르면 무엇을 본 것인지 모릅니다 — 성공이라고 말하지 않습니다.")
        return 1
    머리 = ["# ⛔ 야간비행의 기록 자리는 **커밋에 안 들어갑니다.**",
            "#   거기에는 정하신 것 · 이 컴퓨터의 상태 · 화면 주소가 쌓입니다.",
            "#   누구나 볼 수 있는 곳에 올리시면 그것이 같이 올라갑니다."]
    글길.write_text("\n".join(머리 + 남길), encoding="utf-8")
    남음 = [줄.strip() for 줄 in 글길.read_text(encoding="utf-8").split("\n")
            if 걷을꼴.match(줄)]
    if 남음:
        print("\n  🔴 **걷었다는데 아직 남아 있습니다** — 성공이라고 말하지 않습니다.")
        for 줄 in 남음:
            print("       · " + 줄)
        return 1
    print("  ✅ 기록을 다시 여는 %d줄을 걷었습니다 — 받는 분의 기록은 올라가지 않습니다."
          % len(걷은))
    for 줄 in 걷은:
        print("       · " + 줄)
    return 0


def 가리키는곳확인(나갈곳: Path) -> int:
    """모은 폴더에서 **마켓플레이스 글이 가리키는 자리가 실제로 있나.**

    🔴 왜 (2026-10-25, 제가 재 보고 알았다):
      공식 마켓플레이스 44개를 받아서 재 봤다 — `source` 는 **`./plugins/<이름>` 꼴이 열여덟 개**이고
      `"."` 은 **하나도 없다.** 우리 것은 `"."` 다(저장소 전체가 플러그인이라는 뜻).
      ⭐ 모은 폴더에서는 `"."` 이 **맞다** — 거기는 나갈 것만 들어 있다.
      ⛔ 그런데 누군가 `source` 를 하위 폴더로 바꾸고 이 도구는 **뿌리에 그대로 펴면**,
        가리키는 자리가 **없는 채로 올라간다.** 깔리지 않고, 올리는 날까지 아무도 모른다.
    ⛔ 그래서 여기서 **무는 검사로** 둔다 — 짓는 쪽에서 재는 것이 올리는 쪽에서 아는 것보다 싸다.
    ⚠️ 복제 자체는 못 막는다 — 마켓플레이스를 더하면 **저장소가 통째로** 온다(`.git` 까지).
      그래서 이 폴더가 **새 저장소**가 되어야 한다(창업자 2026-10-24 결정).
    """
    글 = 나갈곳 / ".claude-plugin" / "marketplace.json"
    if not 글.exists():
        print("\n  🔴 **모은 폴더에 마켓플레이스 글이 없습니다** — 플러그인으로 안 깔립니다.")
        print("     ⛔ `data/배포.tsv` 가 `.claude-plugin/*.json` 을 「꼭」으로 적어 뒀는데 안 왔습니다.")
        return 1
    try:
        판 = json.loads(글.read_text(encoding="utf-8"))
    except Exception as e:
        print("\n  🔴 **마켓플레이스 글을 읽지 못했습니다** — %s" % e)
        return 1
    아픔 = 0
    for 칸 in 판.get("plugins", []):
        원 = 칸.get("source")
        if not isinstance(원, str):
            continue
        터 = (나갈곳 / 원).resolve()
        if not 터.is_dir():
            print("\n  🔴 **가리키는 자리가 없습니다** — %s → source \"%s\"" % (칸.get("name", "?"), 원))
            print("     ⛔ 이대로 올리면 **깔리지 않습니다.** 올리는 날까지 아무도 모릅니다.")
            아픔 = 1
            continue
        if not (터 / ".claude-plugin" / "plugin.json").exists():
            print("\n  🔴 **가리키는 자리에 플러그인 글이 없습니다** — %s → \"%s\"" % (칸.get("name", "?"), 원))
            print("     ⛔ 폴더는 있는데 그 안이 플러그인이 아닙니다 — 깔리지 않습니다.")
            아픔 = 1
    if not 아픔:
        print("  ✅ 마켓플레이스가 가리키는 자리가 이 폴더 안에 다 있습니다.")
    return 아픔


_안건드림 = (".md", ".json", ".txt", ".webp", ".png")


def _따옴표밖(줄, 기호들):
    """`줄` 에서 주석이 시작하는 자리. 따옴표 안이면 주석이 아니다. 없으면 -1."""
    따옴 = None
    i = 0
    while i < len(줄):
        c = 줄[i]
        if 따옴:
            if c == "\\":
                i += 2; continue
            if c == 따옴:
                따옴 = None
        elif c in "\"'`":
            따옴 = c
        else:
            for 기호 in 기호들:
                if not 줄.startswith(기호, i):
                    continue
                앞글자 = 줄[i - 1] if i else ""
                if 기호 == "#" and 앞글자 and not 앞글자.isspace():
                    continue
                if 기호 == "//" and 앞글자 == ":":
                    continue
                return i
        i += 1
    return -1


def 주석걷기(f: Path) -> None:
    """옮겨 놓은 파일 하나에서 코드 주석을 건다."""
    if f.suffix in _안건드림:
        return
    try:
        글 = f.read_text(encoding="utf-8")
    except Exception:
        return
    def _조각걷기(m):
        return _인용꼴.sub("", m.group(0))
    글 = re.sub(r'\"\"\".*?\"\"\"', _조각걷기, 글, flags=re.S)
    머리 = 글.split("\n", 1)[0] if 글 else ""
    셸인가 = f.suffix == ".sh" or (not f.suffix and 머리.startswith("#!") and "sh" in 머리)
    if f.suffix == ".tsv":
        def _주석줄(l):
            return l.lstrip().startswith("#")
        난것, 묶음 = [], []
        def _묶음비우기():
            if not 묶음:
                return
            난것.extend(l.rstrip() for l in _인용꼴.sub("", "\n".join(묶음)).split("\n"))
            묶음.clear()
        for l in 글.splitlines():
            if _주석줄(l):
                묶음.append(l)
            else:
                _묶음비우기()
                난것.append(_인용꼴.sub("", l).rstrip(" "))
        _묶음비우기()
        f.write_text("\n".join(난것).rstrip("\n") + "\n", encoding="utf-8")
        return
    if f.suffix == ".py" or 셸인가:
        기호 = ("#",)
    elif f.suffix in (".ts", ".js"):
        기호 = ("//",)
    elif f.suffix in (".html",):
        기호 = ("//",)
    else:
        return

    if f.suffix == ".html":
        글 = re.sub(r"<!--.*?-->", "", 글, flags=re.S)
        글 = re.sub(r"/\*.*?\*/", "", 글, flags=re.S)

    난것 = []
    for n, 줄 in enumerate(글.splitlines()):
        벗 = 줄.rstrip()
        if n < 2 and (벗.startswith("#!") or "coding" in 벗):
            난것.append(줄); continue
        i = _따옴표밖(줄, 기호)
        if i < 0:
            난것.append(줄); continue
        앞 = 줄[:i].rstrip()
        if not 앞.strip():
            continue
        난것.append(앞)
    f.write_text("\n".join(난것).rstrip("\n") + "\n", encoding="utf-8")


_이름 = r"(창업자|대표님)"
_가까운틈 = r"[^\t\u300d]{0,20}"
_먼틈 = r"[^\n\t\u300d]{0,60}"
_이음 = r"(?:[^\n\t\u300c\u300d]{0,8}\u300c[^\u300d]{1,400}\u300d)*"
_인용꼴 = re.compile(
    _이름 + r"(?:" + _가까운틈 + r"\u300c[^\u300d]{4,400}\u300d"
          + r"|" + _먼틈 + r"\u300c[^\u300d]{12,400}\u300d)" + _이음)


def 인용남았나(나갈곳: Path) -> bool:
    """나가는 몸에 사용자 말씀 인용이 남았으면 True(그러면 모으기가 멈춘다)."""
    걸림 = []
    for f in sorted(나갈곳.rglob("*")):
        if not f.is_file() or f.suffix in (".webp", ".png"):
            continue
        try:
            글 = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in _인용꼴.finditer(글):
            n = 글.count("\n", 0, m.start()) + 1
            걸림.append((str(f.relative_to(나갈곳)), n,
                        " / ".join(m.group(0).split("\n"))[:110]))
    if not 걸림:
        return False
    print()
    print("  🔴 **나가는 몸에 사용자 말씀 인용이 %d곳 남았습니다.**" % len(걸림))
    print("     공개 저장소로 나가면 그 말이 그대로 읽힙니다 — 한 번 나가면 지워도 지난 판에 남습니다.")
    for 파일, n, 줄 in 걸림[:12]:
        print("       · %s:%d  %s" % (파일, n, 줄))
    if len(걸림) > 12:
        print("       … 외 %d곳" % (len(걸림) - 12))
    print()
    print("  ⭐ 고치는 법: **원본 저장소의 그 글 파일**에서 인용을 «사실»로 다시 쓰십시오.")
    print("     말은 남기고 누가 말했는지만 뺍니다 — 보기 낱말을 빼면 규칙이 약해집니다.")
    print("     ⛔ 여기(모은 폴더)에서 고치지 마십시오. 다시 모으면 되돌아갑니다.")
    return True


def main() -> int:
    인자 = [a for a in sys.argv[1:] if not a.startswith("--")]
    모아 = "--모아" in sys.argv
    덮 = "--덮어쓰기" in sys.argv
    if not 인자:
        print("  ⛔ 어디로 모을지 폴더를 주십시오:  배포모으기.py <나갈 폴더> [--모아]")
        return 1
    뿌리 = Path(__file__).resolve().parent.parent
    나갈곳 = Path(인자[0]).resolve()

    칸들 = 검사.표읽기(뿌리 / "data" / "배포.tsv")
    파일들 = 검사.추적목록(뿌리)
    나감, 안나감, 모름 = 검사.가른다(파일들, 칸들)
    빠짐 = [k for k in 칸들 if k["꼭"] and not any(검사.맞나(f, k["꼴"]) for f in 파일들)]
    if 모름 or 빠짐:
        print("  🔴 **모으지 않았습니다** — 먼저 배포 목록을 맞추십시오.")
        print("     무엇이 빠졌는지는 배포 검사가 말해 줍니다.")
        if 모름:
            print("     · 분류 안 된 파일 %d개" % len(모름))
        if 빠짐:
            print("     · 「꼭」인데 없는 것 %d개" % len(빠짐))
        return 1

    갈것 = sorted(f for f, _ in 나감)
    print("=== 받는 사람에게 갈 것 %d개 · 여기 남을 것 %d개 ===" % (len(갈것), len(안나감)))
    남는이유 = {}
    for f, k in 안나감:
        남는이유.setdefault(k["꼴"], [k["왜"], 0])[1] += 1
    for 꼴, (왜, n) in sorted(남는이유.items()):
        print("  여기 남음  %-28s %2d개  %s" % (꼴, n, 왜[:52]))

    if not 모아:
        print("\n  ⚠️ **보여만 줬습니다.** 실제로 모으려면 끝에 `--모아` 를 붙이십시오.")
        return 0

    if 나갈곳.exists() and any(나갈곳.iterdir()) and not 덮:
        print("\n  ⛔ **모으지 않았습니다** — 그 폴더에 이미 무엇이 있습니다: %s" % 나갈곳)
        print("     비우시거나 다른 폴더를 주십시오. 꼭 덮어쓰시려면 `--덮어쓰기` 를 붙이십시오.")
        return 1

    for f in 갈것:
        왼, 오 = 뿌리 / f, 나갈곳 / f
        오.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(왼, 오)
        주석걷기(오)

    생김 = [f for f in 갈것 if (나갈곳 / f).exists()]
    새것 = sorted(str(p.relative_to(나갈곳)) for p in 나갈곳.rglob("*") if p.is_file())
    더간것 = [f for f in 새것 if f not in 갈것]
    if len(생김) != len(갈것) or 더간것:
        print("\n  🔴 **모았는데 수가 안 맞습니다** — 성공이라고 말하지 않습니다.")
        print("     셌던 것 %d개 · 실제로 생긴 것 %d개" % (len(갈것), len(생김)))
        for f in [f for f in 갈것 if f not in 생김][:5]:
            print("       · 안 갔음: " + f)
        for f in 더간것[:5]:
            print("       · 더 갔음: " + f)
        return 1

    if 가리키는곳확인(나갈곳) or 기록여는줄걷는다(나갈곳, 뿌리) or 인용남았나(나갈곳):
        print("\n  🔴 **모으기는 했지만 올리면 안 됩니다** — 위를 고친 뒤 다시 모으십시오.")
        return 1

    print("\n  ✅ %d개를 모았습니다: %s" % (len(생김), 나갈곳))
    print("  ⛔ 여기는 **새로 시작하는 곳**입니다 — 여태까지의 기록이 안 따라옵니다.")
    print("     지금 만드는 곳은 **비공개 그대로** 두십시오(창업자 2026-10-24 결정).")
    print("  ⚠️ 올리기 전에 한 번 더 보십시오 — 이 도구는 «목록대로» 옮길 뿐,")
    print("     목록이 틀렸는지는 모릅니다.")
    import subprocess
    메일 = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True, cwd=str(나갈곳)).stdout.strip()
    if 메일 and not re.search(r"(^support@|noreply|no-reply)", 메일):
        print("\n  🔴 이 자리에서 커밋하면 작성자 메일이 «%s…» 입니다 — 받아 가는 사람 모두가 커밋 기록에서 봅니다." % 메일[:6])
        print("     첫 커밋 전에 그 폴더에서 작성자를 회사 주소로 정하십시오(그 저장소에만 듣습니다):")
        print("     [모델] git -C %s config user.email support@<도메인>" % 나갈곳)
    return 0


if __name__ == "__main__":
    sys.exit(main())
