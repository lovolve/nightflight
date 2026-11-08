#!/usr/bin/env python3
"""야간비행 도구"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

BAN = {
    "세어": "알려 드립니다 · 봅니다",
    "셈을": "알려 드리는 것", "셈은": "알려 드리는 것", "셈이": "알려 드리는 것",
    "셉니다": "봅니다", "센다": "본다", "센 것": "모르는 것",
    "걸리는 것": "해야 하는 것", "안 걸립니다": "안 하셔도 됩니다",
    "안 걸린다": "안 하셔도 된다", "걸리는 것이 없": "해야 할 일이 없",
    "막히는 것": "이 방식으로는 안 되는 것", "돌려보냅니다": "출시가 안 됩니다",
    "껍데기": "웹사이트를 그대로 앱에 넣는다",
    "장부": "기록",
    "바닥": "어디까지인지", "살아 있는 척": "표지 없이",
    "죽어 있": "없어졌", "못 박혀": "정해져", "못을 박": "정해 둔",
}
SAID = []
AXIS_VALUES = set()
OK = re.compile(r"모호어검사:\s*말하는 자리다")
LOOK = (".claude/feature-map.tsv",
        "board/*.html", "landing/*.html", "tools/*.py", "tools/*.sh", "bin/*.sh", "bin/ledger.d/*.sh",
        "data/*.tsv", "*.md", "catalog/*.md")
SKIP_FILES = {"lint_vague_words.py"}


def _찍히는_글만(text: str, suffix: str, 처방본문: bool = False) -> list:
    lines = text.splitlines()
    out = []
    in_doc = False
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        q = raw.count('"' * 3) + raw.count("'" * 3)
        was = in_doc
        if q % 2 == 1:
            in_doc = not in_doc
        if was or q % 2 == 1 or q >= 2:
            out.append((i, ""))
            continue
        if s.startswith(("//", "<!--") if 처방본문 else ("//", "#", "*", "<!--")):
            out.append((i, ""))
            continue
        line = re.sub(r"\s//.*$", "", raw)
        if not 처방본문:
            line = re.sub(r"\s#(?!\s*모호어검사).*$", "", line)
        out.append((i, line))
    return out


def _사용자칸(f: Path) -> list:
    head = "\n".join(f.read_text(encoding="utf-8").splitlines()[:30])
    m = re.search(r"RULE-0:\s*사용자 문구 칸\s*=\s*(\d+(?:\s*,\s*\d+)*)", head)
    if not m:
        return []
    return [int(x) for x in re.split(r"\s*,\s*", m.group(1)) if int(x) > 0]


아직고친말 = {
    "관문": "출시 절차",
    "야간비행": None,
    "조종석": None,
    "두뇌": "코어",
    "처방": "가이드",
    "기다림": "일정 안내",
}


아직센것 = None
_기록칸 = None


_요소이름 = re.compile(r'(?:\bid|\bclass|\bname|\bfor|\bhref|\bsrc|\bdata-[\w-]+)'
                       r'\s*=\s*["\']([^"\']*)["\']')


def _자료냐(q: str, line: str = "") -> bool:
    s = q.strip()
    if re.search(r"\.(tsv|json|md|sh|py|html|js|txt|svg)$", s):
        return True
    if s in (_기록칸 or ()):
        return True
    if line:
        for v in _요소이름.findall(line):
            if s == v or s in v.split():
                return True
    return False


def _기록칸읽기(root) -> frozenset:
    f = root / "bin" / "ledger.sh"
    if not f.is_file():
        return frozenset()
    try:
        글 = "\n".join(x.read_text(encoding="utf-8") for x in [f] + sorted((root / "bin" / "ledger.d").glob("*.sh")))
    except OSError:
        return frozenset()
    이름 = set(re.findall(r"^  ([가-힣]+)\)$", 글, re.M))
    이름 |= {n + "끝" for n in 이름}
    return frozenset(이름)


def _아직(root) -> None:
    센것 = 아직센것
    if 센것 is None:
        print("  ⚠️ 아직 안 고친 말을 **재지 못했습니다** — 「0곳」이 아닙니다.")
        return
    총 = sum(센것.values())
    if not 총:
        return
    print(f"  ⚠️ **제가 지어냈는데 아직 안 고친 말 {총:,}곳** — 「0곳」이 아닙니다.")
    print("     " + " · ".join(f"{w} {n}" for w, n in 센것.most_common() if n))
    print("     ⛔ 전에 이 자리에 「창업자가 쓰시는 말이라 안 봅니다」라고 찍었습니다. "
          "재 보니 **일곱 개 전부 제가 먼저 쓴 말**이었습니다(2026-10-14).")
    print("     ⚠️ 「야간비행」·「조종석」은 제품 이름이라 **창업자가 정하실 일**입니다.")


def main() -> int:
    HOME_REPO = Path(__file__).resolve().parent.parent
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HOME_REPO
    gp = root / "data" / "gates.tsv"
    if gp.is_file():
        for ln in gp.read_text(encoding="utf-8").splitlines():
            if ln.startswith("#") or "\t" not in ln:
                continue
            c = ln.split("\t")
            if len(c) > 2:
                AXIS_VALUES.update(m.strip() for m in
                                   re.findall(r"(?:=|has|!=)\s*([^|&]+)", c[2]))
    global 아직센것, _기록칸
    import collections
    아직센것 = collections.Counter()
    _기록칸 = _기록칸읽기(root)
    bad, seen = [], 0
    files = []
    for pat in LOOK:
        files += sorted(root.glob(pat))
    for f in files:
        if f.name in SKIP_FILES:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = f.relative_to(root)
        처방본문 = (rel.parts[0] == "catalog" and f.suffix == ".md")
        울타리 = False
        내부메모 = 처방본문 and "두뇌에서만 내려간다" in text.splitlines()[0]
        for i, line in _찍히는_글만(text, f.suffix, 처방본문):
            if not line.strip():
                continue
            if OK.search(line):
                SAID.append(f"{rel}:{i}")
                continue
            code_free = re.sub(r"\[\s*['\"][^'\"]*['\"]\s*\]", "[]", line)
            code_free = re.sub(r"\.get\(\s*['\"][^'\"]*['\"]", ".get(", code_free)
            code_free = re.sub(r"['\"][^'\"]*['\"]\s*:", '"":', code_free)
            quoted = (re.findall(r"'([^']{2,})'", code_free)
                      + re.findall(r'"([^"]{2,})"', code_free))
            quoted += re.findall(r">([^<>]{2,})<", code_free)
            quoted = list(dict.fromkeys(quoted))
            if 내부메모:
                if line.strip() == "---":
                    내부메모 = False
                continue
            if 처방본문:
                if line.lstrip().startswith("```"):
                    울타리 = not 울타리
                    continue
                if 울타리:
                    continue
                quoted = [re.sub(r"`[^`]*`", "", line)]
            if f.suffix == ".tsv":
                quoted = [line.split("\t")[c - 1] for c in _사용자칸(f)
                          if c - 1 < len(line.split("\t"))]
            seen += 1
            for q in quoted:
                if not _자료냐(q, line):
                    for _w in 아직고친말:
                        if _w in q:
                            아직센것[_w] += q.count(_w)
                if q in AXIS_VALUES:
                    continue
                for w, instead in BAN.items():
                    if w in q:
                        bad.append((rel, i, w, instead, q.strip()[:60]))
                        break
    print(f"=== 사용자에게 보이는 글의 «불명확한 말·비유» — {len(bad)}곳 ({seen:,}줄 봤습니다) ===")
    if SAID:
        print(f"  ⚠️ {len(SAID)}곳은 「말하는 자리다」라고 **선언해서** 넘겼습니다 — "
              + " · ".join(SAID[:6]))
    if not bad:
        print("  ✅ 제가 지어낸 말이 사용자 쪽에 없습니다.")
        print("  ⚠️ 이 검사는 **적어 둔 말 목록**만 봅니다 — 0 이 「전부 또렷하다」는 뜻은 아닙니다.")
        _아직(root)
        return 0
    _아직(root)
    for rel, i, w, instead, q in bad[:14]:
        print(f"  🔴 {rel}:{i} — 「{w}」")
        print(f"       「{q}」")
        print(f"       ⭐ 대신: {instead}")
    if len(bad) > 14:
        print(f"  … 그리고 {len(bad) - 14}곳 더")
    print("\n  ⛔ 새 낱말을 지어내지 마십시오 — **무엇을 하는지 그대로** 말합니다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
