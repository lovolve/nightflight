#!/usr/bin/env python3
"""조종석 글자 크기 · 굵기 · 간격이 정한 단계 밖으로 나가지 않게 한다.

🔴 2026-10-27  — 재 보니 글자 크기 16가지(9~24px, 0.5px 차이까지) ·
   굵기 4가지 · 바깥 간격 95가지였다. 화면을 고칠 때마다 그 자리에서 값을 새로 정했기 때문이다.
⭐ 「㉠으로 해」: 애플 화면 지침 맥 글자 단계(Title 1 22 · Title 2 17 · Title 3 15 · Body 13 · Callout 12)로 옮겼다.
   글자 크기는 `var(--fs-1)`~`var(--fs-5)` 만 · 굵기는 400 · 600 만 · 간격(margin · padding · gap)은 4의 배수(3px 이하는 미세 조정이라 둔다)
   · 모서리 둥글기는 2 · 6 · 12 · 999px · 50% 만.
⛔ 사람 기억에 맡기지 않는다 — 단계는 :root 한 곳에만 숫자로 있고, 그 밖에서 숫자 크기를 쓰면 울린다.
"""
import re
import sys
from pathlib import Path

예외 = ("font:600 9.5px/12px",)


def 찾기(text):
    나쁨 = []
    for 번호, 줄 in enumerate(text.splitlines(), 1):
        if "--fs-1:" in 줄 or any(e in 줄 for e in 예외):
            continue
        for m in re.finditer(r"font-size\s*:\s*(-?[\d.]+(?:px|rem))", 줄):
            나쁨.append((번호, "글자 크기 " + m.group(1), "var(--fs-1)~var(--fs-5) 가운데 하나"))
        for m in re.finditer(r"font\s*:\s*\d{3}\s+([\d.]+(?:px|rem))", 줄):
            나쁨.append((번호, "글자 크기 " + m.group(1), "var(--fs-1)~var(--fs-5) 가운데 하나"))
        for m in re.finditer(r"font-weight\s*:\s*(\d{3})", 줄):
            if m.group(1) not in ("400", "600"):
                나쁨.append((번호, "굵기 " + m.group(1), "400 또는 600"))
        for m in re.finditer(r"(?<![-\w])(?:margin|padding|gap|row-gap|column-gap)(?:-[a-z]+)*\s*:\s*([^;}\"']+)", 줄):
            for v in re.findall(r"-?([\d.]+)px", m.group(1)):
                n = float(v)
                if n > 3 and n % 4:
                    나쁨.append((번호, "간격 " + v + "px", "4의 배수(4 · 8 · 12 · 16 · 24 …)"))
        for m in re.finditer(r"border-radius\s*:\s*([^;}\"'!]+)", 줄):
            if "jf-fr" in 줄:
                continue
            for v in m.group(1).split():
                if v not in ("0", "2px", "6px", "12px", "999px", "50%"):
                    나쁨.append((번호, "모서리 " + v, "2px · 6px · 12px · 999px · 50% 가운데 하나"))
    return 나쁨


def main():
    root = Path(__file__).resolve().parent.parent
    p = root / "board" / "cockpit.html"
    if not p.exists():
        return 0
    나쁨 = 찾기(p.read_text(encoding="utf-8"))
    if not 나쁨:
        print("  ✅ 조종석 — 글자 크기 다섯 · 굵기 둘 · 간격 4의 배수 · 모서리 다섯을 지킵니다")
        return 0
    print(f"  ⛔ 조종석 — 정한 단계 밖의 값 {len(나쁨)}곳 (다시 섞이면 위계가 흐려집니다)")
    for 번호, 무엇, 대신 in 나쁨[:12]:
        print(f"     board/cockpit.html:{번호} 「{무엇}」 → {대신}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
