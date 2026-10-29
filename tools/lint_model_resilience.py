#!/usr/bin/env python3
"""모델 호출이 끊기지 않게 버티나 — 저장소를 훑어 넷을 본다.



⭐ **「폴백」이 두 종류다.** 섞어 세면 둘 다 없는 곳을 못 찾는다.
   ① **모델 폴백** — 그 모델이 죽었을 때 «다른 모델»로 다시 부른다
   ② **답 폴백** — 다 실패했을 때 사용자에게 «무엇을 보이나». 500 을 던지면 화면이 빈다
   어느 앱의 `analyze-message` 는 ②가 있고 ①이 없다. 다른 앱의 `dog-ask` 는 둘 다 있다.

🔴 **실측된 사고: 과거 모델로 폴백하면 그것도 없어진 모델이다.**
   `gemini-2.5-flash-lite` 는 **신규 API 키에서 404** 다(어느 앱 Phase 0 스파이크 확인).
   그래서 폴백은 **항상 후속 모델로** 간다. 이 검사가 버전이 내려가는 폴백을 오류로 잡는다.

⚠️ 종료일 표는 **손으로 유지한다.** 구글 공지가 출처이고 기계가 알 길이 없다.
   적혀 있지 않은 모델은 「모른다」로 나온다 — 모르는 것을 안전으로 읽지 않는다.
"""
import re, sys, pathlib, datetime

SUNSET = {
    "gemini-3.1-flash-lite": ("2027-05-07", "구글 공식 deprecations 페이지 · 후속 gemini-3.5-flash-lite"),
    "gemini-2.0-flash-lite":  ("2026-06-01", "구글 공식 deprecations 페이지"),
    "gemini-2.0-flash":       ("2026-06-01", "구글 공식 deprecations 페이지"),
}

NOT_ANNOUNCED = {
    "gemini-3.5-flash-lite": "2026-09-27",
}
STALE_CHECK_DAYS = 180

DEAD = {
    "gemini-2.5-flash-lite":
        "신규 프로젝트에서 접근 제한(구글 모델 문서) · 신규 API 키에서 404(어느 앱 Phase 0 실측)",
}
WARN_DAYS = 180

MODEL = re.compile(r"\b(gemini|claude|gpt)-[0-9]+(?:\.[0-9]+)?[a-z0-9.\-]*", re.I)
FROM_ENV = re.compile(r"env\.get\(\s*['\"](?:[A-Z_]*MODEL[A-Z_]*)['\"]|ProcessInfo[^\n]*MODEL")
FAIL_RETURN = re.compile(r"(return|throw)[^\n]*[가-힣]{2,}")
MODEL_LOOP = re.compile(r"for\s*\(\s*const\s+\w*model|MODELS\b|for\s+model\s+in|models\.forEach")
LIST_DECL = re.compile(r"(?:let|const|var)\s+([A-Za-z_]\w*)\s*(?::[^=]*)?=\s*\[")
def loops_over(name, text):
    return re.search(rf"for\s+\w+\s+in\s+[\w.]*\b{re.escape(name)}\b"
                     rf"|\b{re.escape(name)}\s*\.\s*(forEach|map)\b"
                     rf"|for\s*\([^)]*\bof\s+[\w.]*\b{re.escape(name)}\b", text)


def code_lines(path):
    """주석을 뺀 줄만. 주석에 적힌 옛 모델 이름을 사용으로 세지 않는다."""
    out, block = [], False
    for i, ln in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        s = ln.strip()
        if block:
            if "*/" in s:
                block = False
            continue
        if s.startswith("/*"):
            block = "*/" not in s
            continue
        if s.startswith("//") or s.startswith("#"):
            continue
        out.append((i, ln))
    return out


def version(m):
    g = re.search(r"([0-9]+)(?:\.([0-9]+))?", m)
    return (int(g.group(1)), int(g.group(2) or 0)) if g else (0, 0)


def main(argv):
    roots = [pathlib.Path(p) for p in (argv[1:] or ["."])]
    files = []
    for r in roots:
        for pat in ("**/*.ts", "**/*.swift", "**/*.tsx"):
            files += [f for f in r.glob(pat)
                      if not {"node_modules", ".build", "build", "dist", "__pycache__",
                              "Tests", "tests", "__tests__"} & set(f.parts)
                      and not f.name.endswith(("Tests.swift", ".test.ts", ".spec.ts"))]

    today = datetime.date.today()

    seen, texts = [], {}
    for f in sorted(set(files)):
        lines = code_lines(f)
        text = "\n".join(ln for _, ln in lines)
        texts[f] = text
        models = []
        for _, ln in lines:
            for m in MODEL.finditer(ln):
                if m.group(0).lower() not in models:
                    models.append(m.group(0).lower())
        if not models:
            continue
        list_names = [d.group(1) for _, ln in lines for d in LIST_DECL.finditer(ln)
                      if len(set(x.group(0).lower() for x in MODEL.finditer(ln))) >= 2]
        seen.append((f, lines, text, models, list_names))

    everything = "\n".join(texts.values())

    rows, problems = [], 0
    for f, lines, text, models, list_names in seen:
        has_loop = bool(MODEL_LOOP.search(text)) or any(
            loops_over(n, everything) for n in list_names)

        issues = []
        notes = []
        if len(models) < 2 or not has_loop:
            issues.append("모델 폴백①이 없다 — 그 모델이 죽으면 이 기능이 멈춘다")
        if not FAIL_RETURN.search(text):
            issues.append("답 폴백②이 없다 — 다 실패했을 때 사용자가 읽을 문구가 없다")
        if not FROM_ENV.search(text):
            notes.append("모델이 코드에 박혔다 — 바꾸려면 배포해야 한다(폴백①이 있으면 급하지 않다)")
        for m in models:
            if m in DEAD:
                issues.append(f"{m} 은 쓰면 안 된다 — {DEAD[m]}")
        if len(models) >= 2 and has_loop:
            vs = [version(m) for m in models]
            if vs != sorted(vs):
                issues.append(f"폴백이 «과거» 모델로 간다 ({' → '.join(models)}) — 그것도 없어진 모델이다")
        for m in models:
            if m in SUNSET:
                d = datetime.date.fromisoformat(SUNSET[m][0])
                left = (d - today).days
                if left <= WARN_DAYS:
                    issues.append(f"{m} 종료 {left}일 남았다 ({d}) — {SUNSET[m][1]}")
            elif m in NOT_ANNOUNCED:
                checked = datetime.date.fromisoformat(NOT_ANNOUNCED[m])
                age = (today - checked).days
                if age > STALE_CHECK_DAYS:
                    issues.append(f"{m} 종료 미공지 확인이 {age}일 전이다 ({checked}) — 다시 확인할 것")
            elif m not in DEAD:
                issues.append(f"{m} 의 종료일을 모른다 — 표에 적어 둘 것(모르는 것은 안전이 아니다)")

        rows.append((f, models, issues, notes))
        problems += bool(issues)

    print(f"=== 모델 호출 {len(rows)}곳 · 손볼 곳 {problems}곳 ===")
    for f, models, issues, notes in rows:
        mark = "⚠️ " if issues else "✅ "
        print(f"\n  {mark}{f}\n      모델: {' → '.join(models)}")
        for i in issues:
            print(f"      · {i}")
        for n in notes:
            print(f"      📌 {n}")
    if problems:
        print("""
  ⭐ 지켜야 하는 넷
     ① 모델 폴백을 **둘 이상**, **항상 후속 버전으로** 둔다 — 과거로 가면 404 를 만난다
     ② 다 실패해도 **사용자가 읽을 문구**를 준다 — 빈 화면이 가장 나쁘다
     ③ 새 모델을 쓰면 **종료일을 이 표에 적는다** — 사람의 기억에 맡기면 언젠가 섞인다
     📌 모델 id 를 환경변수로 빼면 배포 없이 바꿀 수 있다(①이 있으면 급하지 않다)""")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
