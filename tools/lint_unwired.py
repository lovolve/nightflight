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
라벨 = {}
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


SKIP_DIRS = {".build", "DerivedData", "build", "node_modules", ".next", "dist", "out", ".git", "Pods", ".gradle", "Tests", "test", "tests", "__tests__"}


def _파일(roots, exts):
    for r in roots:
        for ext in exts:
            for p in Path(r).rglob("*" + ext):
                if any(x in SKIP_DIRS for x in p.parts) or ".test." in p.name or ".spec." in p.name:
                    continue
                yield p


_빈몸 = r"\{\s*(?:(?://[^\n]*|/\*.*?\*/)\s*)*\}"
_찍기만 = r"\{\s*(?:print|console\.log|debugPrint|NSLog|Log\.\w)\s*\([^()]*\)\s*;?\s*\}"
빈버튼 = {
    ".swift": [re.compile(r"Button\s*(?:\([^()\n]*(?:\([^()\n]*\)[^()\n]*)*\))?\s*" + _빈몸, re.S),
               re.compile(r"Button\s*\(\s*action:\s*" + _빈몸, re.S),
               re.compile(r"\.onTapGesture\s*(?:\([^()]*\))?\s*" + _빈몸, re.S),
               re.compile(r"Button\s*(?:\([^()\n]*\))?\s*" + _찍기만, re.S)],
    ".kt": [re.compile(r"onClick\s*=\s*" + _빈몸, re.S),
            re.compile(r"setOnClickListener\s*" + _빈몸, re.S),
            re.compile(r"\.clickable\s*" + _빈몸, re.S),
            re.compile(r"onClick\s*=\s*" + _찍기만, re.S)],
    "web": [re.compile(r"on(?:Click|Press|Submit)=\{\s*\(\s*\w*\s*\)\s*=>\s*" + _빈몸 + r"\s*\}", re.S),
            re.compile(r"on(?:Click|Press|Submit)=\{\s*\(\s*\w*\s*\)\s*=>\s*(?:" + _찍기만 + r"|(?:console\.log|alert)\([^()]*\))\s*\}", re.S),
            re.compile(r"on(?:Click|Press)=\{\s*(?:undefined|null)\s*\}"),
            re.compile(r"@click(?:\.\w+)*=\"\s*\""),
            re.compile(r"<a\b(?![^>]*\bon[Cc]lick)[^>]*\bhref=\"#\"[^>]*>")],
}
WEB = (".tsx", ".jsx", ".vue", ".svelte", ".html")


def 빈_버튼(roots, allow):
    for ext, rxs in (( ".swift", 빈버튼[".swift"]), (".kt", 빈버튼[".kt"])) + tuple((e, 빈버튼["web"]) for e in WEB):
        for p in _파일(roots, (ext,)):
            if ".stories." in p.name:
                continue
            src = p.read_text(errors="ignore")
            미리 = [m.start() for m in re.finditer(r"#Preview\b|:\s*PreviewProvider\b|@Preview\b", src)]
            for rx in rxs:
                for m in rx.finditer(src):
                    if any(0 <= m.start() - k < 4000 for k in 미리):
                        continue
                    if ext == ".swift" and ("role: .cancel" in m.group(0)
                                            or re.search(r"\.(alert|confirmationDialog)\s*\(", src[max(0, m.start() - 400):m.start()])):
                        continue
                    줄 = src.count("\n", 0, m.start()) + 1
                    키 = f"{p.name}:{줄}"
                    if 키 in allow:
                        skipped.append(f"{키} — {allow[키]}")
                        continue
                    found.append(("눌러도 반응 없는 버튼", 키,
                                  "누르는 자리는 있는데 하는 일이 비었거나 찍기만 한다"))
                    라벨[키] = _라벨(m.group(0) + src[m.end():m.end() + 300])


def 도달_못하는_웹안드로이드화면(roots, allow):
    kt = [p for p in _파일(roots, (".kt",))]
    if kt:
        blob = "\n".join(p.read_text(errors="ignore") for p in kt)
        for r in sorted(set(re.findall(r'composable\(\s*(?:route\s*=\s*)?"([^"{]+)', blob))):
            if r in allow:
                skipped.append(f"{r} — {allow[r]}"); continue
            if not re.search(rf'navigate\(\s*"{re.escape(r)}|startDestination\s*=\s*"{re.escape(r)}"', blob):
                found.append(("도달 못 하는 화면", f'composable("{r}")', "그 화면으로 «가는 길»이 없다 — 만들어 두고 못 간다"))
    web = [p for p in _파일(roots, (".tsx", ".jsx", ".ts", ".js", ".vue"))]
    if web:
        blob = "\n".join(p.read_text(errors="ignore") for p in web)
        for r in sorted(set(re.findall(r'<Route\b[^>]*\bpath=["\'](/[^"\':*]*)["\']|\bpath:\s*["\'](/[^"\':*]*)["\']', blob))):
            r = next(x for x in r if x)
            if r in ("/", "") or r in allow:
                continue
            if not re.search(rf'(?:to|href)=\{{?["\'`]{re.escape(r)}["\'`?#/]|navigate\(\s*["\'`]{re.escape(r)}|push\(\s*["\'`]{re.escape(r)}|redirect\(\s*["\'`]{re.escape(r)}', blob):
                found.append(("도달 못 하는 화면", f"길 {r}", "그 화면으로 «가는 길»(링크 · 이동)이 없다 — 만들어 두고 못 간다"))


def _라벨(t):
    for rx in (r'(?:Button|Text|Label)\(\s*"([^"\n]{1,40})"', r'>\s*([^<>{}\n]{1,40}?)\s*<', r'(?:title|label|aria-label)=["\']([^"\'\n]{1,40})'):
        m = re.search(rx, t)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def 작동안함(roots=None):
    global found
    roots = roots or [str(_root.root())]
    saved, found = found, []
    try:
        allow = allowlist()
        빈_버튼(roots, allow)
        도달_못하는_웹안드로이드화면(roots, allow)
        도달_못하는_화면(roots, allow)
        줄 = []
        for 분류, 무엇, _ in found:
            if 분류 == "눌러도 반응 없는 버튼":
                줄.append({"갈래": "버튼", "이름": 라벨.get(무엇, ""), "자리": 무엇})
            elif 분류 == "도달 못 하는 화면":
                줄.append({"갈래": "화면", "이름": 무엇.split(": ")[-1].replace('composable("', "").rstrip('")').replace("길 ", ""), "자리": 무엇})
        return {"보일까": bool(줄), "수": len(줄), "줄": 줄[:30]}
    except Exception:
        return None
    finally:
        found = saved


def main():
    roots = sys.argv[1:] or ["."]
    allow = allowlist()
    for check in (안_부르는_swift_함수, 안_부르는_sql_함수, 도달_못하는_화면, 안_채운_배선, 빈_버튼, 도달_못하는_웹안드로이드화면):
        try:
            check(roots, allow)
        except Exception as e:
            print(f"⚠️ {check.__name__} 를 못 돌렸다: {e}")

    if skipped:
        print(f"· 이유를 적어 뺀 것 {len(skipped)}개")
    if not found:
        print("✅ 배선 점검 — 눈에 띄는 «안 이어진 것»이 없다")
        print("   ⚠️ 이 검사는 **여섯 모양**만 본다 — 0 이 「전부 이어졌다」는 뜻은 아니다.")
        return 0
    print(f"⚠️ «있는데 안 이어진» 것으로 보이는 것 {len(found)}건 — **사람이 판단한다**")
    for 분류, 무엇, 왜 in found:
        print(f"   [{분류}] {무엇}")
        print(f"       {왜}")
    print("\n정당한 것은 NF_UNWIRED_ALLOW 파일에 「이름|이유」로 적는다. 이유 없이는 못 뺀다.")
    return 1


import sys as _sys
if __name__ == "__main__":
    _sys.exit(main())
