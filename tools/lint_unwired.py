#!/usr/bin/env python3
"""«만든 것이 이어졌는가»를 본다 — 조각은 멀쩡하고 «사이»가 빈 고장을 잡는다.

왜 (어느 앱, 2026-09-27 하루에 «아홉» 건):
  ① 대기 화면 초시계를 «올리는 코드가 없어» 영원히 0초였다.
     주석에는 「올라가는 숫자가 멈추지 않았다는 증거」라고 적혀 있었다 — 증거가 안 움직였다
  ② 「같은 성별과만」 토글이 서버에 안 갔다 — Flow 가 `false` 를 박아 넘겼다.
     **안전 장치가 조용히 아무것도 안 하고 있었다**
  ③ `[CallEffect]` 를 아무도 안 받아서 **마이크가 안 켜지고**(음성 앱인데 목소리가 안 갔다) ·
     3분 전환·6분 종료가 없고 · **이용권이 한 번도 차감되지 않았다**
  ④ 「그만 찾기」가 화면 초시계만 멈추고 서버 큐에는 남았다 — **그만뒀는데 나중에 전화가 왔다**
  ⑤ 신고해야만 차단됐다. 화면 이름은 「신고 · 차단」인데 `block()` 이 죽어 있었다
  ⑥ 잔액 0이어도 통화가 시도됐다 — 막는 화면은 «있는데 거기로 가는 길이 없었다»

  ⭐ 왜 못 봤나: 코어를 순수하게 둬서 테스트가 0.08초에 도는 «대신»
     **경계에는 테스트가 없다.** 코어 205개가 다 통과해도
     「앱이 그걸 **부르는가**」는 아무도 안 본다. 그리고 **화면에 버튼이 있으면 된다고 믿는다.**

  ⭐ 고치는 순서: **① 타입 > ② 검사 > ③ 문서.** 위로 갈수록 사람이 잊을 수 없다.
     `onStart: () -> Void` → `(Bool) -> Void` 로 바꾸니 **떨어뜨리면 컴파일이 잡는다.**
     타입으로 못 막는 것만 이 검사로 내려온다.

⚠️ **가장 흔한 오탐은 «프로토콜 구현»이다** — 이름만 보면 아무도 안 부르는데
   프레임워크가 부른다(`render(pcmBuffer:)` · `path(in:)` · 델리게이트).
   아는 이름은 빼 뒀고, 새로 나오면 **이유를 적어** 빼면 된다.

⛔ **막지 않는다. 보이게 한다.** 앱마다 구조가 달라 오탐이 난다
   (프로토콜 구현 · SwiftUI 수명주기 · 트리거가 부르는 SQL).
   그래서 종료 코드는 언제나 0이고, **사람이 판단한다.**
   앱 안에 이미 맞춰 둔 검사가 있으면(그 앱의 `tools/lint_unwired.py`) 그쪽을 «엄격하게» 쓴다.

⚠️ 이 검사가 «2단 사슬»을 놓쳤던 적이 있다 — `Server.shared.leaveQueue` 는 «있는데»
   그걸 부르는 `Flow.stopLooking()` 이 죽어 있었다. 그래서 ③ 검사를 나중에 더했다.
   **한 단계만 보면 통과한다.**

  사용:  python3 lint_unwired.py [경로 ...]        기본: 현재 폴더
         NF_UNWIRED_ALLOW=<파일>  한 줄에 「이름|이유» — 이유 없이는 못 지운다
"""
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
    """이름이 `...Wiring` 인 묶음의 필드를 «만드는 곳»이 다 채우는가.

    🔵 인자를 여러 개 늘어놓는 대신 한 덩어리로 묶는 것이 이 부류의 «타입 해법»이다.
       묶어 두면 이렇게 기계로 셀 수 있다.
    """
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
