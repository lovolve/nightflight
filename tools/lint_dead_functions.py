#!/usr/bin/env python3
"""웹 화면 파일(.html · .js)에서 «만들어 놓고 아무도 부르지 않는 함수»를 찾는다."""
import os
import collections
import re
import sys
from pathlib import Path

SKIP = {"node_modules", ".next", "dist", "build", "out", ".git", ".claude", ".nightflight", "vendor"}
EXT = (".html", ".js", ".jsx", ".tsx", ".ts", ".vue", ".svelte")
DECL = re.compile(r"\bfunction\s+([A-Za-z_$가-힣][\w$가-힣]*)\s*\(")


def 허용():
    p = Path(os.environ.get("NF_UNWIRED_ALLOW") or (Path.cwd() / "NF_UNWIRED_ALLOW"))
    out = {}
    if p.is_file():
        for l in p.read_text(encoding="utf-8").splitlines():
            if "|" in l and not l.lstrip().startswith("#"):
                n, why = l.split("|", 1)
                out[n.strip()] = why.strip()
    return out


def 파일들(roots):
    for r in roots:
        r = Path(r)
        if r.is_file():
            yield r
            continue
        for p in r.rglob("*"):
            if p.suffix in EXT and not any(x in SKIP for x in p.parts) and ".min." not in p.name:
                yield p


def 찾기(roots):
    files = list(파일들(roots))
    글 = {p: p.read_text(encoding="utf-8", errors="ignore") for p in files}
    전체 = "\n".join(글.values())
    allow = 허용()
    낱말수 = collections.Counter(re.findall(r"[\w$가-힣]+", 전체))
    out = []
    for p, s in 글.items():
        for m in DECL.finditer(s):
            n = m.group(1)
            if n in allow:
                continue
            쓰임 = 낱말수[n] - 1
            if 쓰임 <= 0:
                줄 = s.count("\n", 0, m.start()) + 1
                out.append((p.name, 줄, n))
    return out


def main():
    roots = sys.argv[1:]
    if not roots:
        roots = ["board"] if Path("board/cockpit.html").is_file() else ["."]
    hits = 찾기(roots)
    if not hits:
        return 0
    print("⚠️ 만들어 놓고 아무도 부르지 않는 함수 %d개 — 고쳐도 화면이 안 바뀝니다:" % len(hits))
    for f, n, name in hits[:12]:
        print("   · %s:%d %s()" % (f, n, name))
    print("   지우거나, 부르는 곳을 잇거나, 일부러 남기면 NF_UNWIRED_ALLOW 에 «이름|이유»를 적으십시오.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
