#!/usr/bin/env python3
"""규정을 인용한 자리마다 «확인 표지»가 붙어 있는지 본다.

왜 있나 — 2026-09-27 하루에 규정을 잘못 읽은 것이 여섯 번이다:
  ① 모델 제공자 「therapy, mental health」 → 「제품이 성립하지 않는다」(해당 아니었다)
  ② 애플 「random or anonymous chat」 → 「랜덤을 버려야 한다」(같은 기능 앱 다섯이 살아 있었다)
  ③ 닉네임을 「필터 대상이 하나 는다」고 비용처럼 말함(모든 소셜 앱에 닉네임이 있다)
  ④ 애플 1.2(UGC 규정)를 **앱이 낸 말**에 붙임(UGC 가 아니다)
  ⑤ 제타 고소 사건을 퍼블리시티권 근거로 씀(그건 이미지·설정 복제이고 우리는 둘 다 안 한다)
  ⑥ §7(사용자 신원)을 **조언자 이름**에 붙여 필드를 빼자고 함(캐릭터 이름은 개인정보가 아니다)

⭐ 여섯 번 다 같은 모양이다 — **조항 번호를 보고, 원문과 적용 대상을 확인하지 않고 단정했다.**
   그래서 이 검사는 「맞게 읽었나」를 판정하지 않는다(그건 기계가 못 한다).
   **인용 옆에 「확인했는지」가 적혀 있는지만** 본다. 안 적혀 있으면 그게 곧 안 한 것이다.

⛔ 표지를 지어내지 말 것. 「원문 확인」은 실제로 원문을 받아 읽었을 때만 쓴다.
"""
import re, sys, pathlib

CITE = re.compile(
    r"(애플|Apple|가이드라인|guideline|App Review)\s*\**\s*\d+\.\d+(\.\d+)?"
    r"|제\s*\d+\s*조(\s*의\s*\d+)?"
    r"|(부정경쟁방지법|청소년보호법|의료법|자살예방법|정신건강복지법|개인정보보호법"
    r"|전자상거래법|정보통신망법|저작권법|AI기본법|COPPA|GDPR|DSA|NO FAKES)"
)

MARKERS = ("원문 확인", "원문 미확인", "해당 아니다", "적용 불확실")

SKIP = re.compile(r"lint_citations|확인 표지|MARKERS|통제된 어휘")


def blocks(path: pathlib.Path):
    """(시작줄, 줄목록) — swift 는 이어진 주석 덩어리, md 는 제목부터 다음 제목까지."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if path.suffix == ".md":
        start, buf = 1, []
        for i, ln in enumerate(lines, 1):
            if re.match(r"^#{1,6}\s", ln) and buf:
                yield start, buf
                start, buf = i, [ln]
            else:
                if not buf:
                    start = i
                buf.append(ln)
        if buf:
            yield start, buf
        return
    if path.suffix in (".py", ".sh", ".tsv"):
        _DOC = ('"""', "'''")
        in_doc = False
        start, buf = None, []
        for i, ln in enumerate(lines, 1):
            t = ln.strip()
            opens = path.suffix == ".py" and t.startswith(_DOC)
            if in_doc:
                buf.append(ln)
                if t.endswith(_DOC) or (len(t) > 3 and t.count(_DOC[0]) + t.count(_DOC[1]) >= 1):
                    in_doc = False
                continue
            if opens:
                if start is None:
                    start = i
                buf.append(ln)
                if not (t.count(_DOC[0]) >= 2 or t.count(_DOC[1]) >= 2):
                    in_doc = True
            elif t.startswith("#"):
                if start is None:
                    start = i
                buf.append(ln)
            else:
                if buf:
                    yield start, buf
                start, buf = None, []
        if buf:
            yield start, buf
        return
    start, buf = None, []
    for i, ln in enumerate(lines, 1):
        if re.match(r"\s*(//|///)", ln):
            if start is None:
                start = i
            buf.append(ln)
        else:
            if buf:
                yield start, buf
            start, buf = None, []
    if buf:
        yield start, buf


SAID_CITE = []


def main(argv):
    root = pathlib.Path(argv[1] if len(argv) > 1 else ".")
    pats = ("*.swift", "*.md", "*.py", "*.sh", "*.tsv")
    targets = []
    for g in pats:
        targets += list(root.rglob(g))
    SELF = {"lint_citations.py", "run.sh"}
    targets = sorted({t for t in targets
                      if ".build" not in t.parts and ".git" not in t.parts
                      and "__pycache__" not in t.parts
                      and t.name not in SELF})

    total, bare = 0, []
    for path in targets:
        for start, buf in blocks(path):
            text = "\n".join(buf)
            hits = {m.group(0).strip() for m in CITE.finditer(text)}
            if not hits:
                continue
            total += len(hits)
            if any(m in text for m in MARKERS) or SKIP.search(text):
                continue
            if "인용검사: 찾는 말이다" in text:
                SAID_CITE.append(f"{path}:{start}")
                continue
            bare.append((path, start, sorted(hits), buf[0].strip()[:70]))

    rel = lambda p: p.relative_to(root) if root in p.parents or p.parent == root else p
    print(f"=== 규정 인용 {total}건 · 확인 표지 없는 자리 {len(bare)}곳 ===")
    if not bare:
        print("  ✅ 인용마다 확인 표지가 있다")
        return 0
    for path, line, hits, head in bare:
        print(f"\n  {rel(path)}:{line}  {' · '.join(hits)}")
        print(f"      {head}")
    print(f"""
  ⛔ 인용한 자리에 다음 넷 중 하나를 적을 것 — {' / '.join(MARKERS)}
     「원문 확인」은 실제로 원문을 받아 읽었을 때만 쓴다.
  ⭐ 그리고 적기 전에 물을 것: 「그 조항이 «무엇에» 적용되나 · 우리가 그걸 하나」
     둘째 답이 「아니다」면 그 조항은 근거가 아니다 — 「해당 아니다」로 적고 끝낸다.""")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
