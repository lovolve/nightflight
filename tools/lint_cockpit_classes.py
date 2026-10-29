#!/usr/bin/env python3
"""조종석에서 «막대 전용 이름»을 다른 자리에 쓰지 않는다.

🔴 두 번 밟았다: 2026-10-24 세부기능 상태 글자 · 2026-10-25 상태 흐름 칩 — 둘 다 이름을 `st` 로 지었고,
   아홉 단계 막대의 `.st`(앞에 동그라미 · 세로 선)가 따라붙어 칩마다 동그라미가 박혔다().
⭐ 사람 기억에 맡기지 않는다 — 막대가 쓰는 이름을 여기 적어 두고, 화면 코드에서 그 이름이 class 로 쓰이면 울린다.

🔴 세 번째(2026-10-25): 설계서 틀을 `sv-scr` 로 지었는데 그 이름이 «화면별 진행» 칸에 이미 있었다 —
   새 규칙의 세로 쌓기·최대 폭 340 이 화면별 진행에 걸려 화면 일곱 개가 세로 한 줄로 섰다().
   예약 이름 표로는 못 막는다(새 이름이 겹친 것이다). ⭐ 그래서 둘째 검사: 같은 이름의 맨 바깥 규칙이 뒤에서
   «놓는 방식»(세로·가로 쌓기 · 칸 나눔 · 최대 폭 · 줄바꿈)을 처음 정하면 울린다 — 이름이 겹쳤다는 표시다.
"""
import re
import sys
from pathlib import Path

RESERVED = {"st": "아홉 단계 막대의 줄(앞 동그라미·세로 선이 붙는다)"}

_놓는방식 = ("flex-direction", "grid-template-columns", "max-width", "flex-wrap")


def 겹친이름(text):
    """같은 이름(.이름{…})의 맨 바깥 규칙이 뒤에서 놓는 방식을 새로 정하는 자리. @media 안 줄은 안 본다."""
    try:
        css = text[text.index("<style"):text.index("</style>")]
    except ValueError:
        return []
    본 = {}
    hits = []
    for n, l in enumerate(css.split("\n"), 1):
        if l.lstrip().startswith("@media"):
            continue
        for m in re.finditer(r'(?:^|\}\s*)(\.[\w가-힣-]+)\{([^}]*)\}', l):
            sel, body = m.group(1), m.group(2)
            props = {k.strip() for k, _ in (q.split(":", 1) for q in body.split(";") if ":" in q)}
            새 = {k for k in props if k in _놓는방식}
            if sel in 본 and 새 - 본[sel][1]:
                hits.append((sel, 본[sel][0], n, sorted(새 - 본[sel][1])))
            앞 = 본.get(sel, (n, set()))
            본[sel] = (앞[0], 앞[1] | props)
    return hits


def main():
    root = Path(__file__).resolve().parent.parent
    p = root / "board" / "cockpit.html"
    if not p.is_file():
        print("  ⚠️ 조종석 파일을 못 찾았습니다 — 재지 못했습니다")
        return 0
    hits = []
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        for m in re.finditer(r'class=\\?["\']([^"\'\\]*)', line):
            for tok in m.group(1).split():
                if tok in RESERVED:
                    hits.append((n, tok))
    겹 = 겹친이름(p.read_text(encoding="utf-8"))
    if not hits and not 겹:
        print("  ✅ 조종석 — 막대 전용 이름을 다른 자리에 쓰지 않았고, 겹친 이름도 없습니다")
        return 0
    if hits:
        print(f"  ⛔ 조종석 — 막대 전용 이름을 다른 자리에 썼습니다 {len(hits)}곳 (그 꾸밈이 따라붙습니다)")
        for n, tok in hits:
            print(f"     board/cockpit.html:{n} 「{tok}」 — {RESERVED[tok]}")
    if 겹:
        print(f"  ⛔ 조종석 — 같은 이름이 두 자리에 쓰인 것 같습니다 {len(겹)}곳 (뒤 규칙의 놓는 방식이 앞 자리에도 걸립니다)")
        for sel, a, b, ks in 겹:
            print(f"     「{sel}」 스타일 {a}째 줄과 {b}째 줄 — 뒤에서 새로 정함: {', '.join(ks)} · 새 자리의 이름을 바꾸십시오")
    return 1

if __name__ == "__main__":
    sys.exit(main())
