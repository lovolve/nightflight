#!/usr/bin/env python3
"""조종석이 **기록 글을 화면에 끼울 때 눕혀서** 넣나 — 안 눕히면 그 글이 화면을 바꾼다.

🔴 왜 (2026-10-25 보안 레드팀 3회차 ④):
   `board/cockpit.html` 의 `날()` 이 기록의 날짜 칸을 **그대로** 돌려주고, 그 값이
   다섯 곳에서 `innerHTML` 로 들어갔다(:2219·:2222·:2320·:2342·:2378).
   ⛔ 기록은 **그 폴더의 파일**이다 — 받은 사람이 남이 만든 폴더를 열면 그 안의 값이 들어온다.
     `slice(5)` 가 앞 다섯 글자를 버리므로 앞을 채워 둔 글자는 살아서 들어간다.
   ⭐ 고침은 함수 한 곳이었다(`날()` 안에서 `esc`). 쓰는 곳마다 붙이면 새 자리를 놓친다.


   HTML 글자 안에서 `'+ 식 +'` 로 끼우는 자리 중, 식이 **기록 값을 가리키는 꼴**
   (`x['칸']` · `x.이름`)인데 `esc(` 나 이미 눕히는 도움 함수를 거치지 않은 것.


   **수를 내는 식**은 안 잡는다: `.length` · `.toFixed(` · `Math.` · `parseInt(` ·
   `Number(` · 괄호 안의 셈. 실측(2026-10-25): 그것들을 안 빼면 멀쩡한 12곳이 걸린다.
   ⭐ 이미 눕히는 도움 함수(`esc` · `칩` · `줄` · `표` · `문구` · `날` · `원문표지` · `일`)도 통과.
   주석 줄도 안 본다.

사용:  python3 lint_cockpit_escape.py [저장소]
끝값:  1 = 눕히지 않은 자리가 있다 · 0 = 없다
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _root import root as _repo_root

끼움 = re.compile(
    r"\+\s*([A-Za-z_$\uac00-\ud7a3][\w$\uac00-\ud7a3]*"
    r"""(?:\[\s*(?:'[^']*'|"[^"]*")\s*\]|\.[\w$\uac00-\ud7a3]+)+(?:\([^()]*\))?)\s*\+""")
기록값 = re.compile(r"""\[\s*(?:'[^']+'|"[^"]+")\s*\]|\.[\w\uac00-\ud7a3]+""")
수를냄 = re.compile(r"\.length\b|\.toFixed\(|\bMath\.|\bparseInt\(|\bNumber\(|\.size\b")
덩이잇기 = re.compile(r"\.join\s*\(")
눕히는것 = ("esc(", "칩(", "줄(", "표(", "문구(", "날(", "원문표지(", "일(")

칸함수 = re.compile(r"\b(줄|표)\s*\(")


def _인자떠내기(글: str, 열린자리: int):
    """`(` 자리부터 짝이 맞는 `)` 까지. 글자열 안의 괄호는 안 센다."""
    깊이, i, 따옴 = 0, 열린자리, ""
    while i < len(글):
        c = 글[i]
        if 따옴:
            if c == "\\":
                i += 2; continue
            if c == 따옴:
                따옴 = ""
        elif c in "'\"`":
            따옴 = c
        elif c == "(":
            깊이 += 1
        elif c == ")":
            깊이 -= 1
            if 깊이 == 0:
                return 글[열린자리 + 1:i], i
        i += 1
    return None, i


def _맨위쉼표로가른다(글: str):
    칸, 깊이, 따옴, 앞 = [], 0, "", 0
    for i, c in enumerate(글):
        if 따옴:
            if c == "\\":
                continue
            if c == 따옴:
                따옴 = ""
        elif c in "'\"`":
            따옴 = c
        elif c in "([{":
            깊이 += 1
        elif c in ")]}":
            깊이 -= 1
        elif c == "," and 깊이 == 0:
            칸.append(글[앞:i]); 앞 = i + 1
    칸.append(글[앞:])
    return [x.strip() for x in 칸 if x.strip()]


def _눕힌범위(글: str):
    범위 = []
    for 이름 in 눕히는것:
        자리 = 0
        while True:
            i = 글.find(이름, 자리)
            if i < 0:
                break
            _, 끝 = _인자떠내기(글, i + len(이름) - 1)
            범위.append((i, 끝))
            자리 = i + len(이름)
    return 범위


안찍히는뒤 = re.compile(r"\s*(\?|&&|\|\||!==|===|!=|==|>=|<=|>|<|\)\s*\?)")


def _안눕힌기록값(칸: str):
    """이 칸에서 **눕히지 않고 찍히는** 기록값을 돌려준다(없으면 빈 목록)."""
    if 수를냄.search(칸):
        return []
    범위 = _눕힌범위(칸)
    샌것 = []
    for m in 기록값.finditer(칸):
        if any(a <= m.start() and m.end() <= b for a, b in 범위):
            continue
        if 안찍히는뒤.match(칸, m.end()):
            continue
        if 칸[m.end():m.end() + 1] == "(" or 칸[m.end():].lstrip()[:1] == "(":
            continue
        샌것.append(m.group(0))
    return 샌것


def 칸을본다(글: str):
    """`줄([…])`·`표(…)` 에 **안 눕힌 기록값을 인자로** 넘기는 자리.

    ⭐ 한 칸이 괜찮다고 보는 조건: 눕히는 함수를 거쳤거나 · 수를 내거나 ·
      이미 만든 덩이를 이었거나(`join`) · 글자열 토막뿐이거나 · 변수 이름 하나뿐이다.
      ⛔ **변수 이름 하나(`x`·`줄들2`)는 통과시킨다** — 그 값이 어디서 왔는지는
        이 검사가 모른다. 그것까지 걸면 멀쩡한 자리가 잔뜩 걸리고 사람이 검사를 끈다.
        ⚠️ 그래서 이 검사는 **기록 칸을 직접 따는 꼴**(`x['이름']`·`w.what`)만 잡는다.
    """
    걸린것 = []
    for m in 칸함수.finditer(글):
        안, 끝 = _인자떠내기(글, m.end() - 1)
        if 안 is None:
            continue
        몸 = 안.strip()
        if 몸.startswith("[") and 몸.endswith("]"):
            몸 = 몸[1:-1]
        for 칸 in _맨위쉼표로가른다(몸):
            if 덩이잇기.search(칸):
                continue
            for 샌것 in _안눕힌기록값(칸):
                걸린것.append((m.group(1), 칸[:70], 샌것))
    return 걸린것


def 눕히는함수가따옴표도바꾸나(뿌리: Path):
    """`esc()` 가 **`"` 와 `'` 까지** 바꾸나.

    🔴 왜 (2026-10-25 보안 레드팀 8회차 ④ · 옆 대화가 짚고 제가 쟀다):
      `esc()` 는 `textContent` → `innerHTML` 로 눕혔다. 그것은 `&`·`<`·`>` 만 바꾸고
      **`"` 와 `'` 는 그대로 둔다.** 그런데 조종석은 그 함수를 **속성 값**에도 쓴다
      (`data-say="…"`·`data-scr="…"` 다섯 자리).
      ⛔ 실측: 화면 이름이 `내 화면" onmouseover=…` 이면 따옴표가 셋이 되어
        **속성이 끊기고 그 뒤가 새 속성이 된다.** 기록은 받는 분이 쓰신 글이다.
    ⭐ 그래서 이 검사가 **되돌아가는 것**을 막는다. 위의 끼움 검사는 「눕혔나」만 보고
      「무엇까지 눕혔나」는 안 봐서, 이 자리가 비어 있었다.
    """
    f = 뿌리 / "board" / "cockpit.html"
    if not f.is_file():
        return []
    글 = f.read_text(encoding="utf-8")
    자리 = 글.find("function esc(")
    if 자리 < 0:
        return []
    몸 = 글[자리:자리 + 400]
    끝 = 몸.find("\n  function ")
    if 끝 > 0:
        몸 = 몸[:끝]
    빠짐 = []
    if "&quot;" not in 몸:
        빠짐.append(('겹따옴표', "속성 값이 끊긴다"))
    if "&#39;" not in 몸 and "&apos;" not in 몸:
        빠짐.append(("홑따옴표", "홑따옴표로 묶은 속성이 끊긴다"))
    return 빠짐


def 본다(뿌리: Path):
    걸린것 = []
    볼것 = ["cockpit.html"]
    for f in [뿌리 / "board" / n for n in 볼것]:
        if not f.is_file():
            continue
        try:
            줄들 = f.read_text(encoding="utf-8").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        for n, l in enumerate(줄들, 1):
            if "<" not in l or l.lstrip().startswith("//"):
                continue
            for m in 끼움.finditer(l):
                식 = m.group(1).strip()
                if "esc(" in 식 or 식.startswith(눕히는것):
                    continue
                if 수를냄.search(식) or 덩이잇기.search(식):
                    continue
                if 기록값.search(식):
                    걸린것.append((f.relative_to(뿌리), n, 식[:70]))
            for 누구, 칸, 샌것 in 칸을본다(l):
                걸린것.append((f.relative_to(뿌리), n,
                               "%s( 안의 칸에서 %s — %s" % (누구, 샌것, 칸)))
    return 걸린것


if __name__ == "__main__":
    뿌리 = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else _repo_root()
    빠짐 = 눕히는함수가따옴표도바꾸나(뿌리)
    if 빠짐:
        print("  ⛔ 눕히는 함수(`esc`)가 **따옴표를 안 바꿉니다** — 속성 값에도 쓰는 함수입니다.")
        for 무엇, 왜 in 빠짐:
            print("     · %s 를 안 바꿉니다 — %s" % (무엇, 왜))
        print("     🔴 실측(2026-10-25): 화면 이름에 따옴표 하나면 속성이 끊기고")
        print("        그 뒤가 **새 속성**이 됩니다. 기록은 받는 분이 쓰신 글입니다.")
        sys.exit(1)
    걸린것 = 본다(뿌리)
    if not 걸린것:
        sys.exit(0)
    print("  ⛔ 기록 글을 안 눕히고 화면에 끼우는 곳이 %d 곳입니다." % len(걸린것))
    print("     그 자리는 **기록 파일의 글이 화면을 바꿉니다**(받은 사람이 남의 폴더를 열면).")
    print("     고침: 그 식을 `esc(…)` 로 감싸거나, 돌려주는 함수 안에서 한 번에 눕히십시오.")
    for p, n, 식 in 걸린것:
        print("     · %s:%d  %s" % (p, n, 식))
    sys.exit(1)
