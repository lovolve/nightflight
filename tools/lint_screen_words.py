#!/usr/bin/env python3
"""화면에 **새 말이 생기면 막는다** — 

🔴 왜 문서가 아니라 검사인가:
  적어 두는 것으로는 세 번 다 못 막았다 —
    「관문」·「두뇌」·「처방」·「기다림」 (창업자가 2026-10-16 에 전부 바꾸라고 하셨다)
    「바닥」 (2026-10-19, 제 말 검사가 잡았다)
    「잰 때」 (2026-10-19, 창업자가 화면에서 보고 잡으셨다)
  ⛔ 전부 **제가 지어낸 말**이고, 전부 **화면의 짧은 이름표**로 샜다.
  ⭐ 그래서 그 자리를 **목록으로 못 박는다.** 목록에 없는 말이 화면에 나오면 **실패**다.

어떻게 가리나 (⚠️ 기계가 「지어낸 말인가」를 판단하지 못한다):
  · 화면 파일에서 **짧은 이름표**만 뽑는다(제목·칸이름·딱지 — 14자 이하).
  · `data/화면말.tsv` 에 없으면 실패한다. 새 말을 쓰려면 **거기에 먼저 적어야** 한다.
  · 적을 때 **누가 정했는지**를 같이 적는다 — 그래야 「제가 지어낸 것」이 드러난다.
⛔ 0 이 「지어낸 말이 없다」는 뜻은 아니다. 이 검사는 **짧은 이름표만** 본다.
   본문 속 낱말은 `lint_vague_words.py` 쪽이고, 그쪽도 **제가 쓴 것만** 안다.

  사용:  python3 lint_screen_words.py
         python3 lint_screen_words.py --새것
"""
import html
import pathlib
import re
import sys

여기 = pathlib.Path(__file__).resolve().parent.parent
목록길 = 여기 / "data" / "화면말.tsv"
볼것: list[str] = []
if "--볼것" in sys.argv:
    볼것 = [sys.argv[sys.argv.index("--볼것") + 1]]
못지킴 = {
    "board/cockpit.html": "화면을 글로 그린다 — 이름표가 글 속에 있다(2026-10-19)",
    "board/관문셈.html": "같다",
    "board/관문셈-조각.html": "같다(조종석에서 뽑아 만든다)",
}

딱지 = re.compile(
    r'<(?:p|h[1-6]|span|div|dt|th|summary|legend|b|li)[^>]*class="[^"]*'
    r'\b(?:cap|eye|lb|tt|k|sk|t|nm|fn|lt|when|sig|phk|fk|sgt|mnm|mk|mhead|stg|phn)\b[^"]*"[^>]*>([^<]{1,48})<')
이름표최대 = 20


def 자료뗀다(t: str) -> str:
    """이름표에서 **자료를 떼어** 말만 남긴다.

    🔴 처음에 「수가 들어 있으면 통째로 뺀다」로 했다가 **막으려던 바로 그 경우를 놓쳤다**
       (2026-10-19 변이로 확인): 「잰 때 2026-10-19 08:15」이 통째로 빠져 버렸다.
       ⛔ 이름표와 자료가 **같은 칸에 같이 들어 있다.** 그래서 자료만 떼야 한다.
    """
    t = re.sub(r"\d[\d:.\-/]*\s*"
               r"(?:(?:GB|MB|KB|TB|건|개|가지|일|분|시간|초|%|번|곳|줄|쪽|대|명|원|회)(?![가-힣]))?",
               " ", t)
    return re.sub(r"\s+", " ", t).strip(" ·—-")


def 목록() -> dict[str, str]:
    if not 목록길.is_file():
        return {}
    말 = {}
    for l in 목록길.read_text(encoding="utf-8").splitlines():
        if not l.strip() or l.startswith("#"):
            continue
        c = l.split("\t")
        말[c[0].strip()] = (c[1].strip() if len(c) > 1 else "")
    return 말


def 화면말():
    찾음 = []
    for pat in 볼것:
        for p in (sorted(여기.glob(pat)) if not pathlib.Path(pat).is_absolute() else [pathlib.Path(pat)]):
            s = p.read_text(encoding="utf-8", errors="ignore")
            s = re.sub(r'(?s)<!--.*?-->|<style[^>]*>.*?</style>|<script[^>]*>.*?</script>', " ", s)
            for m in 딱지.finditer(s):
                t = html.unescape(m.group(1)).strip()
                t = 자료뗀다(t)
                if t and len(t) <= 이름표최대 and re.search(r"[가-힣]", t):
                    찾음.append((p.name, t))
    return 찾음


def main() -> int:
    아는말 = 목록()
    찾음 = 화면말()
    새것 = sorted({t for _, t in 찾음 if t not in 아는말})

    if "--새것" in sys.argv:
        for t in 새것:
            print(f"{t}\t")
        return 0

    print(f"=== 화면에 쓰는 말 — 이름표 {len(찾음)}개 · 서로 다른 말 "
          f"{len({t for _, t in 찾음})}개 ===")

    눈감음 = []
    for pat in 볼것:
        for p in (sorted(여기.glob(pat)) if not pathlib.Path(pat).is_absolute() else [pathlib.Path(pat)]):
            크기 = p.stat().st_size
            본것 = sum(1 for f2, _ in 찾음 if f2 == p.name)
            if 크기 > 20_000 and 본것 < 3:
                눈감음.append(f"{p.name}({크기 // 1024}KB 인데 이름표 {본것}개)")
    if 눈감음:
        print("\n  🔴 **이 검사가 거의 안 보고 있습니다** — " + " · ".join(눈감음))
        print("     ⛔ 화면을 글(script)로 그리면 이름표가 글 속으로 들어가 안 보입니다.")
        print("        ✅ 가 「새 말이 없다」가 아니라 **「볼 것이 없었다」**가 됩니다.")
        print("     ⭐ 그 화면의 이름표는 사람이 봐야 합니다. 이 검사로는 못 막습니다.")
        return 1
    if not 목록길.is_file():
        print(f"  🔴 목록이 없습니다: {목록길.relative_to(여기)}")
        return 1
    if not 볼것:
        print("  ⚠️ 지금은 이 검사가 지키는 화면이 없습니다 — 남은 화면은 모두 글로 그려 이름표가 안 보입니다.")
    if not 새것:
        print(f"  ✅ 목록에 없는 말이 없습니다 (목록 {len(아는말)}개)")
        내가 = [t for t, who in 아는말.items() if who.startswith("제가")]
        if 내가:
            print(f"  ⚠️ 그중 **제가 지어낸 말 {len(내가)}개**가 아직 있습니다 — "
                  + " · ".join(내가[:6]))
            print("     ⛔ 0 이 「지어낸 말이 없다」는 뜻이 아닙니다. 목록에 적혀 있을 뿐입니다.")
        print("  ⚠️ 이 검사는 **짧은 이름표만** 봅니다. 본문 속 낱말은 못 봅니다.")
        print(f"  🔴 그리고 **못 지키는 화면이 {len(못지킴)}개** 있습니다 — 사람이 봐야 합니다:")
        for 길, 왜 in 못지킴.items():
            print(f"       {길} — {왜}")
        return 0

    print(f"\n  🔴 목록에 없는 말 {len(새것)}개 — 새 말을 만드셨습니다\n")
    어디 = {}
    for f, t in 찾음:
        어디.setdefault(t, set()).add(f)
    for t in 새것:
        print(f"   「{t}」   ({' · '.join(sorted(어디[t]))})")
    print(f"""
  ⛔ 
  ⭐ 쓰시려면 `{목록길.relative_to(여기)}` 에 **먼저 적으십시오.** 칸 둘입니다:
       <화면에 쓰는 말>\t<누가 정했나 — 창업자 / 설명함 / 보통말 / 제가 지어냄(날짜)>
  ⚠️ 「제가 지어냄」으로 적으셔도 통과합니다. 다만 **그렇게 적혀 남습니다** —
     이 검사의 뜻은 막는 것이 아니라 **지어낸 것을 드러내는 것**입니다.""")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
