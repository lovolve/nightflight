#!/usr/bin/env python3
"""사용자에게 보이는 글이 «쓰기 규칙»을 지키나 — ASD-STE100(항공 정비 설명서용 통제 영어)을 한국어로 옮긴 것."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARK = re.compile(r"[⭐⛔🔴✅❌]|⚠️?")
절차끝 = re.compile(r"(십시오|세요|주세요|주시면 됩니다|하면 됩니다|하기)\s*[.!]?\s*$")
연결동작 = re.compile(r"[가-힣]*(하|켜|넣|두|열|받|쓰|누르|바꾸|지우|만들|고르|붙이|올리|내리|닫|끄|찾|읽|적|보내|확인하)고\s(?!(싶|있|보|나|말|계|싶)[가-힣]*)")
문장끝 = re.compile(r"(?<=[다요]\.)\s+|(?<=[.?!])\s+(?=[가-힣A-Z「«(])")


def 기록자리(뿌리: Path) -> Path:
    for d in (".nightflight", ".claude"):
        if (뿌리 / d).is_dir() and (d != ".claude" or (뿌리 / d / "ledger.tsv").is_file()):
            return 뿌리 / d
    return 뿌리 / ".nightflight"


def 용어표():
    p = ROOT / "data" / "용어.tsv"
    out = []
    if not p.is_file():
        return out
    for l in p.read_text(encoding="utf-8").splitlines():
        if not l.strip() or l.startswith("#"):
            continue
        c = l.split("\t")
        if len(c) >= 2:
            for bad in c[1].split(";"):
                if bad.strip():
                    out.append((bad.strip(), c[0].strip()))
    return out


def 사전바꿈():
    p = ROOT / "data" / "낱말사전.tsv"
    out = []
    if not p.is_file():
        return out
    for l in p.read_text(encoding="utf-8").splitlines():
        c = l.split("\t")
        if l.startswith("#") or len(c) < 3 or c[1] != "다" or "두 뜻" in c[2] or c[0] == "배치":
            continue
        out.append((c[0], re.sub(r"\(이름 하나\)|\(.*헷갈림\)", "", c[2]).strip()))
    return out


def 화면글():
    for rel in ("board/cockpit.html",):
        f = ROOT / rel
        if not f.is_file():
            continue
        html = rel.endswith(".html")
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            s = line.strip()
            if s.startswith(("//", "#", "/*", "*", "<!--")):
                continue
            if "자료값" in line:
                continue
            code = line.split("//")[0] if html else re.split(r"\s#\s", line)[0]
            for m in re.finditer(r"'([^'\n]*[가-힣][^'\n]*)'|\"([^\"\n]*[가-힣][^\"\n]*)\"", code):
                앞, 뒤 = code[:m.start()].rstrip(), code[m.end():].lstrip()
                if 앞.endswith("[") and 뒤.startswith("]"):
                    continue
                if 뒤.startswith(":") or re.search(r"(===|!==|==|!=)\s*$", 앞) or re.match(r"(===|!==|==|!=)", 뒤):
                    continue
                t = re.sub(r"<[^>]+>", " ", m.group(1) or m.group(2))
                yield ("화면", f"{rel}:{n}", t)


def 기록표글():
    cols = {"feed-labels.tsv": (1, 2, 3), "item-labels.tsv": (1,), "screens.tsv": (2,),
            "plan-notes.tsv": (1,), "plan-when.tsv": (2, 3, 4)}
    for name, cs in cols.items():
        f = 기록자리(ROOT) / name
        if not f.is_file():
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("#"):
                continue
            c = line.split("\t")
            for i in cs:
                if i < len(c) and re.search(r"[가-힣]", c[i]):
                    yield ("기록표", f"{기록자리(ROOT).name}/{name}:{n}", c[i])


def 알림글():
    for f in sorted(list((ROOT / "bin").glob("*.sh")) + list((ROOT / "bin").glob("*.py"))):
        for n, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            s = line.strip()
            if s.startswith("#") or not ("systemMessage" in line or re.search(r"\bsayu\s+[\"']", line)):
                continue
            for m in re.finditer(r"'([^'\n]*[가-힣][^'\n]*)'|\"([^\"\n]*[가-힣][^\"\n]*)\"", line):
                yield ("알림", f"bin/{f.name}:{n}", m.group(1) or m.group(2))


def 안내글있나():
    return (ROOT.parent / "nightflight-server" / "catalog").is_dir()


def 안내글():
    d = ROOT.parent / "nightflight-server" / "catalog"
    if not d.is_dir():
        return
    for f in sorted(d.glob("*.md")):
        속 = False
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip().startswith("```"):
                속 = not 속
                continue
            if 속 or not re.search(r"[가-힣]", line) or line.startswith("---"):
                continue
            yield ("안내", f"catalog/{f.name}:{n}", line)


def 문장들(t):
    return [s.strip() for s in 문장끝.split(t) if s.strip()]


def 잰다(자리, 곳, t, 용어):
    hits = []
    쓸 = sorted({g for _, g in 용어}, key=len, reverse=True)
    깨끗 = re.sub(r"«[^»]*»|「[^」]*」|`[^`]*`", " ", t)
    for g in 쓸:
        깨끗 = 깨끗.replace(g, " ")
    for bad, good in 용어:
        if re.search(r"(?<![가-힣])" + re.escape(bad), 깨끗):
            hits.append(("용어", f"«{bad}» → «{good}»"))
    for s in 문장들(t):
        어절 = len(s.split())
        절차 = bool(절차끝.search(s))
        한도 = 20 if 절차 else 25
        if 어절 > 한도:
            hits.append(("길이", f"{어절}어절(>{한도}) — {s[:50]}"))
        if 절차 and 연결동작.search(s):
            hits.append(("동작", f"한 줄에 동작 둘 이상 — {s[:50]}"))
        if len(MARK.findall(s)) > 1 or (re.search(r"[«»]", s) and re.search(r"[「」]", s)):
            hits.append(("기호", f"기호 겹침 — {s[:50]}"))
    return [(자리, 곳, k, v) for k, v in hits]


def 안내못쟀다():
    if 안내글있나():
        return
    print("  ⚠️ 단계 안내는 **재지 못했습니다** — 그 글은 야간비행이 내려줍니다.")
    print("     (「안내 칸이 0」은 「안 어겼다」가 아니라 **「볼 글이 없었다」**입니다.)")


def main(argv):
    용어 = 용어표() + 사전바꿈()
    목록 = "--목록" in argv
    한자리 = argv[argv.index("--자리") + 1] if "--자리" in argv else None
    for x in argv:
        if x.startswith("--자리="):
            한자리 = x.split("=", 1)[1]
    모두 = []
    for gen in (화면글, 기록표글, 알림글, 안내글):
        for 자리, 곳, t in gen():
            if 한자리 and 자리 not in 한자리.split(","):
                continue
            모두 += 잰다(자리, 곳, t, 용어)
    if not 모두:
        print("  ✅ 쓰기 규칙 — 어긴 곳 없음 (용어 · 길이 · 동작 · 기호)")
        안내못쟀다()
        return 0
    from collections import Counter
    c = Counter((a, k) for a, _, k, _ in 모두)
    print(f"  ⛔ 쓰기 규칙을 어긴 곳 {len(모두)}곳 — 한 이름(data/용어.tsv) · 짧은 문장 · 한 동작 · 기호 겹침 없이")
    for 자리 in ("화면", "기록표", "알림", "안내"):
        줄 = " · ".join(f"{k} {c[(자리, k)]}" for k in ("용어", "길이", "동작", "기호") if c[(자리, k)])
        if 줄:
            print(f"     {자리}: {줄}")
    if 목록:
        for 자리, 곳, k, v in 모두:
            print(f"     [{k}] {곳}  {v}")
    else:
        print("     전부 보기: lint_writing.py --목록")
    안내못쟀다()
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
