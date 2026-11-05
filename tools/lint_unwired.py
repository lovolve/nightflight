#!/usr/bin/env python3
"""«만든 것이 이어졌는가»를 본다 — 조각은 멀쩡하고 «사이»가 빈 고장을 잡는다."""
import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
import _root
import os
import re
import sys
from pathlib import Path

FRAMEWORK = re.compile(
    r"^(body|init|deinit|main|makeUIView|updateUIView|makeCoordinator|"
    r"application|scene|hash|encode|decode|description|"
    r"pushRegistry|provider|room|urlSession|tableView|collectionView|"
    r"path|animatableData|sizeThatFits|layoutSubviews|placeholder|render)"
)

found = []
skipped = []


def allowlist():
    p = os.environ.get("NF_UNWIRED_ALLOW")
    if not p:
        for r in (str(_root.root()), os.getcwd()):
            if r and (Path(r) / "NF_UNWIRED_ALLOW").exists():
                p = str(Path(r) / "NF_UNWIRED_ALLOW"); break
    out = {}
    if p and Path(p).exists():
        for line in Path(p).read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "|" not in line:
                continue
            name, why = line.split("|", 1)
            out[name.strip()] = why.strip()
    return out


def swift_files(roots):
    for r in roots:
        for p in Path(r).rglob("*.swift"):
            if any(x in p.parts for x in (".build", "DerivedData", "Tests", "build")):
                continue
            yield p


def 안_부르는_swift_함수(roots, allow):
    files = list(swift_files(roots))
    blob = "\n".join(p.read_text(errors="ignore") for p in files)
    for p in files:
        src = p.read_text(errors="ignore")
        for name in set(re.findall(r"\n\s{4}(?:@\w+\s+)?func (\w+)\(", src)):
            if FRAMEWORK.match(name):
                continue
            if name in allow:
                skipped.append(f"{name} — {allow[name]}")
                continue
            calls = len(re.findall(rf"[.\s]{name}\s*\(", blob)) - \
                    len(re.findall(rf"func {name}\s*\(", blob))
            if calls <= 0:
                found.append(("호출처 없음", f"{p.name}: {name}()",
                              "만들어만 두고 «아무도 안 부른다»"))


def 안_부르는_sql_함수(roots, allow):
    migr = [p for r in roots for p in Path(r).rglob("supabase/migrations/*.sql")]
    if not migr:
        return
    sql = "\n".join(p.read_text(errors="ignore") for p in migr)
    client = "\n".join(p.read_text(errors="ignore") for r in roots
                       for p in list(Path(r).rglob("*.swift")) + list(Path(r).rglob("*.ts"))
                       if ".build" not in p.parts)
    for name in sorted(set(re.findall(r"create (?:or replace )?function ([a-z_]+)\(", sql))):
        if name in allow:
            skipped.append(f"{name} — {allow[name]}")
            continue
        if f'"{name}"' in client or f"'{name}'" in client or f"/{name}" in client:
            continue
        inner = len(re.findall(rf"\b{name}\s*\(", sql)) - \
                len(re.findall(rf"function {name}\s*\(", sql))
        if inner <= 0:
            found.append(("안 부르는 RPC", f"{name}()",
                          "클라이언트·엣지함수·다른 SQL 어디서도 «안 부른다». "
                          "트리거·cron 이 부르면 이유를 적어 뺀다"))


def 도달_못하는_화면(roots, allow):
    for p in swift_files(roots):
        src = p.read_text(errors="ignore")
        for m in re.finditer(r"enum (Route|Screen|Step|Destination)\b([^{]*)\{(.*?)\n\s{4}\}",
                             src, re.S):
            if "CaseIterable" in m.group(2):
                continue
            for case in re.findall(r"case (\w+)", m.group(3)):
                if case in allow:
                    skipped.append(f"{case} — {allow[case]}")
                    continue
                if not re.search(rf"= \.{case}\b|return \.{case}\b|\.{case}\b\s*=", src):
                    found.append(("도달 못 하는 화면", f"{p.name}: {m.group(1)}.{case}",
                                  "그 화면으로 «가는 길»이 없다 — 만들어 두고 못 간다"))


def 안_채운_배선(roots, allow):
    files = list(swift_files(roots))
    blob = "\n".join(p.read_text(errors="ignore") for p in files)
    for p in files:
        for m in re.finditer(r"struct (\w*Wiring) \{(.*?)\n\}", p.read_text(errors="ignore"), re.S):
            name, body = m.group(1), m.group(2)
            sites = re.findall(rf"{name}\((.{{0,1200}}?)\n\s*\)", blob, re.S)
            if not sites:
                found.append(("배선 없음", name, "이 묶음을 «만드는 곳»이 없다"))
                continue
            for field in re.findall(r"var (\w+):", body):
                if field in allow:
                    continue
                if not any(f"{field}:" in s for s in sites):
                    found.append(("안 채운 배선", f"{name}.{field}",
                                  "만드는 곳이 «안 채운다» — 그 부분만 조용히 안 된다"))


def main():
    roots = sys.argv[1:] or ["."]
    allow = allowlist()
    for check in (안_부르는_swift_함수, 안_부르는_sql_함수, 도달_못하는_화면, 안_채운_배선):
        try:
            check(roots, allow)
        except Exception as e:
            print(f"⚠️ {check.__name__} 를 못 돌렸다: {e}")

    if skipped:
        print(f"· 이유를 적어 뺀 것 {len(skipped)}개")
    if not found:
        print("✅ 배선 점검 — 눈에 띄는 «안 이어진 것»이 없다")
        print("   ⚠️ 이 검사는 **네 모양**만 본다 — 0 이 「전부 이어졌다」는 뜻은 아니다.")
        return 0
    print(f"⚠️ «있는데 안 이어진» 것으로 보이는 것 {len(found)}건 — **사람이 판단한다**")
    for 분류, 무엇, 왜 in found:
        print(f"   [{분류}] {무엇}")
        print(f"       {왜}")
    print("\n정당한 것은 NF_UNWIRED_ALLOW 파일에 「이름|이유」로 적는다. 이유 없이는 못 뺀다.")
    return 1


import sys as _sys
_sys.exit(main())
