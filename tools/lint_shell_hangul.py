#!/usr/bin/env python3
"""셸 파일에 **한글 변수 이름**이 있나 — 배시가 조용히 실패하는 자리다.

🔴 왜 (2026-10-14, 하루에 **세 번**):
   배시는 한글 식별자를 못 읽는다. `여기="가"` 를 **명령으로 보고** 이렇게 끝난다:

       여기=가: command not found

   ⛔ 그런데 **끝값이 0 이다**(실측). 스크립트는 그대로 이어 돌고 `$여기` 는 **빈 값**이다.
   ⛔ 그리고 **`bash -n` 이 통과한다** — 문법은 맞기 때문이다.
   ⭐ 그래서 **아무도 못 본다.** 이 저장소가 아는 모양 그대로다 — 「조용히 틀렸다」.

   같은 사람이 하루에 세 번 밟았고(`bin/두뇌.sh` 머리에 적어 두고 그 다음 파일에서 또),
   파일 머리에 적는 것으로는 안 멈췄다. ⭐ 그래서 검사로 내린다
   (전역 규칙 0: 「누군가 그걸 한다 → 규칙이다 → **검사로 옮긴다**」).


- **헤러독 속**(`<<'PY' … PY`)은 파이썬·파이썬은 **한글 이름이 된다**(실측).
  이 저장소는 셸 안에 파이썬을 자주 넣는다 — 거기까지 잡으면 매번 울고 아무도 안 본다.
- **주석**과 **따옴표 안의 글**.
- 일부러 그 꼴을 쓰는 자리는 **선언**한다: `한글이름검사: 말하는 자리다`. 조용히 안 뺀다.

사용:  python3 lint_shell_hangul.py [저장소]
끝값:  1 = 있다 · 0 = 없다
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _root import root as _repo_root

LOOK = ("bin/*.sh", "bin/ledger.d/*.sh", "tools/*.sh", "tests/*.sh", "probe/*.sh")
ASSIGN = re.compile(r"^\s*(?:local\s+|export\s+|declare\s+(?:-\w+\s+)?)?"
                    r"([A-Za-z0-9_]*[가-힣][A-Za-z0-9_가-힣]*)=")
DECLARE = re.compile(r"\b(?:local|declare|export|readonly|typeset)\s+(?:-\w+\s+)*"
                     r"([A-Za-z0-9_]*[가-힣][A-Za-z0-9_가-힣]*)\b")
ASSIGN2 = re.compile(r"(?:;|&&|\|\|)\s*([A-Za-z0-9_]*[가-힣][A-Za-z0-9_가-힣]*)=")
OPEN = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1\s*$")
OK = re.compile(r"한글이름검사:\s*말하는 자리다")
SAID = []


def 본다(path: Path):
    """헤러독 속과 주석을 뺀 (줄번호, 줄) 만 돌려준다.

    ⚠️ `python3 -c "` 로 **여러 줄에 걸친 따옴표** 속 파이썬은 못 가린다 —
       거기는 셸이 아닌데 셸로 읽어 **헛울린다.** 표지를 붙여 넘긴다(위 주석 참고).
    """
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    tag = None
    for i, raw in enumerate(lines, 1):
        if tag is not None:
            if raw.strip() == tag:
                tag = None
            continue
        s = raw.lstrip()
        if s.startswith("#"):
            continue
        m = OPEN.search(raw)
        if m:
            tag = m.group(2)
            continue
        yield i, raw


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else _repo_root()
    seen, bad, looked = set(), [], 0
    for pat in LOOK:
        for f in sorted(root.glob(pat)):
            if f.resolve() in seen:
                continue
            seen.add(f.resolve())
            for i, line in 본다(f):
                looked += 1
                m = ASSIGN.match(line) or DECLARE.search(line) or ASSIGN2.search(line)
                if not m:
                    continue
                if OK.search(line):
                    SAID.append(f"{f.name}:{i}")
                    continue
                bad.append((f.relative_to(root), i, m.group(1), line.strip()[:62]))

    if not seen:
        print("  ⚠️ 셸 파일을 못 찾아 **재지 못했습니다** — 「없다」가 아닙니다.")
        return 0

    if bad:
        print(f"=== 셸 파일의 **한글 변수 이름** {len(bad)}곳 ===")
        for rel, i, name, txt in bad:
            print(f"  🔴 {rel}:{i}  「{name}=」")
            print(f"     {txt}")
        print()
        print("  ⛔ 배시는 이 이름을 **명령으로 봅니다** — 「command not found」가 나고")
        print("     **끝값은 0 이라 그대로 이어 돌며** 그 변수는 **빈 값**이 됩니다.")
        print("     `bash -n` 도 통과합니다. 그래서 아무도 못 봅니다.")
        print("  ⭐ 고치는 길: 이름을 로마자로 바꾸십시오(`여기` → `HERE`).")
        print("     헤러독 속 파이썬은 한글 이름을 써도 됩니다 — 거기는 안 봅니다.")
        return 1

    print(f"  ✅ 셸 파일 {len(seen)}개에 한글 변수 이름이 없습니다 ({looked:,}줄 봤습니다)")
    print("     ⚠️ 헤러독 속과 주석은 **일부러 안 봅니다** — 거기는 셸이 아닙니다.")
    if SAID:
        print(f"     ⚠️ {len(SAID)}곳은 「말하는 자리다」라고 **선언해서** 넘겼습니다 — "
              + " · ".join(SAID[:5]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
