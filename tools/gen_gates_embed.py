#!/usr/bin/env python3
"""랜딩에 **심을 조각**을 만든다 — `board/관문셈.html` 에서 «뽑아서».

🔴 왜 (레드팀 3/3 의 1순위, 2026-10-12): 관문 셈이 랜딩에서 **「예시」로만** 있어서
   「**처음으로 하고 싶어졌습니다. 그리고 처음으로 할 데가 없습니다.**」가 나왔다 —
   설득은 됐고 전환은 0 이었다.

⭐⭐ **베끼지 않는다.** 화면 파일을 읽어서 조각을 «뽑는다» —
   `tests/열쇠맞나.js` 가 열쇠 함수를 뽑아 쓰는 것과 같은 방식이다.
   ⛔ 베끼면 두 벌이 되고 한 벌이 낡는다(이 저장소가 반복해서 치른 값).

무엇을 바꾸나
| 바꾸는 것 | 왜 |
|---|---|
| `fetch('관문셈.json')` → **표를 박아 넣는다** | 조각은 **한 덩어리로 자족적**이어야 한다(랜딩 요청) |
| `:root{…}` 토큰 정의 | ⛔ 걷어낸다 — 랜딩의 토큰을 쓴다. 우리 이름은 **기본값**으로만 남는다 |
| 우리 토큰 이름 → 랜딩 이름 | `var(--ink)` → `var(--ink, #13161B)` 꼴. ⚠️ 없으면 안 보이게 되니 **기본값을 같이** |
| `body{…}` · `.wrap{max-width}` | ⛔ 걷어낸다 — **바깥 폭은 랜딩이 정한다** |
| 선택자 전부 | `#관문셈` 아래로 **묶는다** — 랜딩의 다른 글에 새지 않게 |
| `<h1>` · 리드 문장 | ⛔ 걷어낸다 — **제목은 랜딩 것**이다 |
| 아이디 `q`·`go`·`out`·`foot` | 접두사를 붙인다 — 랜딩 쪽 아이디와 부딪히지 않게 |

사용:  python3 gen_gates_embed.py
나오는 것:  board/관문셈-조각.html
"""
import json
import re
import sys
from pathlib import Path

_PLUGIN = Path(__file__).resolve().parent.parent
SRC = _PLUGIN / "board" / "관문셈.html"
TBL = _PLUGIN / "board" / "관문셈.json"
OUT = _PLUGIN / "board" / "관문셈-조각.html"

ROOT_ID = "관문셈"

MAP = {
    "ground": "base", "panel": "raised", "ink": "ink", "ink-2": "ink-dim",
    "muted": "ink-dim", "faint": "ink-dim", "rule": "line", "rule-2": "line",
    "now": "signal", "alert": "signal", "open": "signal", "ok": "signal",
}


def _기본값(css: str) -> dict:
    """`:root{…}` 에서 우리 기본값을 읽는다. ⛔ 여기 적지 않는다 — 화면이 들고 있다."""
    vals = {}
    for m in re.finditer(r"--([a-z0-9-]+)\s*:\s*([^;}]+)", css):
        vals.setdefault(m.group(1), m.group(2).strip())
    return vals


def main() -> int:
    if not SRC.is_file() or not TBL.is_file():
        print("  ⚠️ 화면이나 표가 없어 **조각을 못 만들었습니다.**", file=sys.stderr)
        return 1
    html = SRC.read_text(encoding="utf-8")
    table = json.loads(TBL.read_text(encoding="utf-8"))

    css = html[html.index("<style>") + 7:html.index("</style>")]
    기본 = _기본값(css)

    css = re.sub(r"@media[^{]*\{\s*:root[^}]*\{[^}]*\}\s*\}", "", css, flags=re.S)
    css = re.sub(r":root(\[[^\]]*\])?\s*\{[^}]*\}", "", css, flags=re.S)
    css = re.sub(r"(?m)^\s*body\s*\{[^}]*\}", "", css)
    css = re.sub(r"\.wrap\s*\{[^}]*\}", "", css, flags=re.S)

    def _tok(m):
        name = m.group(1)
        우리값 = 기본.get(name, "")
        랜딩 = MAP.get(name)
        if 랜딩:
            return f"var(--{랜딩}, var(--{name}, {우리값}))" if 우리값 else f"var(--{랜딩})"
        return f"var(--{name}, {우리값})" if 우리값 else m.group(0)
    css = re.sub(r"var\(--([a-z0-9-]+)\)", _tok, css)

    def _scope(block):
        sels, body = block.group(1), block.group(2)
        out = []
        for s in sels.split(","):
            s = s.strip()
            if not s or s.startswith("@"):
                out.append(s)
            else:
                out.append(f"#{ROOT_ID} {s}")
        return ", ".join(out) + "{" + body + "}"
    css = re.sub(r"(?m)^([^{@}/][^{}]*?)\{([^{}]*)\}", _scope, css)

    body = html[html.index('<div class="wrap">'):html.index("</div>\n\n<script>")]
    body = re.sub(r"<h1>.*?</h1>", "", body, flags=re.S)
    body = re.sub(r'<p class="lede">.*?</p>', "", body, flags=re.S)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    body = body.replace('<div class="wrap">', "").strip()
    for i in ("q", "go", "out", "foot"):
        body = body.replace(f'id="{i}"', f'id="{ROOT_ID}-{i}"')

    js = html[html.index("<script>") + 8:html.rindex("</script>")]
    js = js.replace("""  var $ = function(id){ return document.getElementById(id); };""",
                    f"""  // ⭐ 조각은 아이디에 접두사를 쓴다 — 랜딩 쪽 아이디와 부딪히지 않게
  var $ = function(id){{ return document.getElementById('{ROOT_ID}-' + id); }};""")
    표박음 = "Promise.resolve(" + json.dumps(table, ensure_ascii=False,
                                            separators=(",", ":")) + ")"
    옛호출 = "fetch('관문셈.json').then(function(res){ return res.json(); })"
    if 옛호출 not in js:
        print("  🔴 표를 불러오는 자리를 못 찾았습니다 — 화면이 바뀌었습니다.", file=sys.stderr)
        return 1
    js = js.replace(옛호출, 표박음)

    frag = (f"""<!-- 설치 전 관문 셈 — 랜딩에 심는 조각.
     ⛔ **이 파일을 손으로 고치지 마십시오.** `tools/gen_gates_embed.py` 가
        `board/관문셈.html` 에서 «뽑아» 만듭니다 — 고치실 곳은 그 화면입니다.
     ⭐ 바깥 폭·여백·제목은 **랜딩이 정합니다.** 이 조각은 폭을 안 정합니다.
     ⭐ 색은 랜딩 토큰을 먼저 보고, 없으면 우리 기본값으로 보입니다. -->
<section id="{ROOT_ID}">
<style>{css}</style>
{body}
</section>
<script>{js}</script>
""")
    if "--찍기" in sys.argv:
        sys.stdout.write(frag)
        return 0
    OUT.write_text(frag, encoding="utf-8")
    kb = len(frag.encode("utf-8")) / 1024
    import gzip
    gz = len(gzip.compress(frag.encode("utf-8"))) / 1024
    print(f"  · 만들었다: {kb:,.0f}KB (눌러서 보내면 **{gz:,.1f}KB**)")
    print(f"    {OUT}")
    print("  ⭐ 화면에서 «뽑아» 만들었습니다 — 베낀 것이 아니라 두 곳이 안 생깁니다.")
    print("  ⛔ 이 조각이 낡으면 턴 끝 검사가 울립니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
