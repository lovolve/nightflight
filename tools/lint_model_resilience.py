#!/usr/bin/env python3
"""모델 호출이 끊기지 않게 버티나 — 저장소를 훑어 넷을 본다."""
import os, re, sys, pathlib, datetime

SUNSET = {
    "gemini-3.1-flash-lite": ("2027-05-07", "구글 공식 deprecations 페이지 · 후속 gemini-3.5-flash-lite"),
    "gemini-2.0-flash-lite":  ("2026-06-01", "구글 공식 deprecations 페이지"),
    "gemini-2.0-flash":       ("2026-06-01", "구글 공식 deprecations 페이지"),
    "claude-sonnet-4-5":          ("2026-11-30", "앤트로픽 공식 model-deprecations 페이지 · 대체 claude-sonnet-5-5"),
    "claude-sonnet-4-5-20250929": ("2026-11-30", "앤트로픽 공식 model-deprecations 페이지 · 대체 claude-sonnet-5-5"),
    "claude-opus-4-1-20250805":   ("2026-08-05", "앤트로픽 공식 model-deprecations 페이지(Retired)"),
    "claude-opus-4-20250514":     ("2026-06-15", "앤트로픽 공식 model-deprecations 페이지(Retired)"),
    "claude-sonnet-4-20250514":   ("2026-06-15", "앤트로픽 공식 model-deprecations 페이지(Retired)"),
    "claude-3-7-sonnet-20250219": ("2026-02-19", "앤트로픽 공식 model-deprecations 페이지(Retired)"),
    "claude-3-5-haiku-20241022":  ("2026-02-19", "앤트로픽 공식 model-deprecations 페이지(Retired)"),
    "claude-3-haiku-20240307":    ("2026-04-20", "앤트로픽 공식 model-deprecations 페이지(Retired)"),
}

NOT_ANNOUNCED = {
    "gemini-3.5-flash-lite": "2026-11-23",
    "gemini-4-argon": "2026-11-23", "gemini-4-carbon": "2026-11-23",
    "gemini-4-hydrogen": "2026-11-23", "gemini-4-neon": "2026-11-23",
    "claude-opus-5-5": "2026-11-23", "claude-sonnet-5-5": "2026-11-23", "claude-haiku-5-5": "2026-11-23",
    "claude-opus-5": "2026-11-23", "claude-sonnet-5": "2026-11-23",
    "claude-fable-5": "2026-11-23", "claude-mythos-5-1": "2026-11-23", "claude-mythos-5": "2026-11-23",
    "claude-opus-4-8": "2026-11-23", "claude-opus-4-7": "2026-11-23", "claude-opus-4-6": "2026-11-23",
    "claude-sonnet-4-6": "2026-11-23",
    "claude-opus-4-5-20251101": "2026-11-23", "claude-haiku-4-5-20251001": "2026-11-23",
}
STALE_CHECK_DAYS = 180

DEAD = {
    "gemini-2.5-flash-lite":
        "신규 프로젝트에서 접근 제한(구글 모델 문서) · 신규 API 키에서 404",
}
WARN_DAYS = 180

MODEL = re.compile(r"\b(?:gemini|gpt)-[0-9]+(?:\.[0-9]+)?[a-z0-9.\-]*"
                   r"|\bclaude-(?:[0-9]|(?:opus|sonnet|haiku|fable|mythos)-[0-9a-z])[a-z0-9.\-]*", re.I)
FROM_ENV = re.compile(r"env\.get\(\s*['\"](?:[A-Z_]*MODEL[A-Z_]*)['\"]|ProcessInfo[^\n]*MODEL")
FAIL_RETURN = re.compile(r"(return|throw)[^\n]*[가-힣]{2,}")
MODEL_LOOP = re.compile(r"for\s*\(\s*const\s+\w*model|MODELS\b|for\s+model\s+in|models\.forEach")
LIST_DECL = re.compile(r"(?:let|const|var)\s+([A-Za-z_]\w*)\s*(?::[^=]*)?=\s*\[")
def loops_over(name, text):
    return re.search(rf"for\s+\w+\s+in\s+[\w.]*\b{re.escape(name)}\b"
                     rf"|\b{re.escape(name)}\s*\.\s*(forEach|map)\b"
                     rf"|for\s*\([^)]*\bof\s+[\w.]*\b{re.escape(name)}\b", text)


def code_lines(path):
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
    g = re.search(r"([0-9]+)(?:[.-]([0-9]+))?", m)
    return (int(g.group(1)), int(g.group(2) or 0)) if g else (0, 0)


def 종료모델글(모델, today=None):
    m = (모델 or "").strip().lower()
    if m not in SUNSET:
        return ""
    today = today or datetime.date.today()
    d = datetime.date.fromisoformat(SUNSET[m][0])
    g = re.search(r"대체 (\S+)", SUNSET[m][1])
    대체 = (" 대체 모델은 " + g.group(1) + " 입니다.") if g else ""
    언제 = "이미 종료됐습니다" if (d - today).days < 0 else f"{d.month}월 {d.day}일에 종료됩니다"
    return ("  [모델] 종료 모델 안내: 지금 모델(" + m + ")은 " + 언제 + ". 사용자에게 한 줄로 알리십시오: "
            "«지금 쓰시는 모델은 " + 언제 + ". 모델 고르는 곳(/model)에서 다른 모델로 바꿔 두시길 권합니다." + 대체 +
            " 바꾸지 않으면 그날부터 이 모델로는 대화가 열리지 않습니다.» 한 번만 말하고 막지 마십시오.")


def main(argv):
    roots = [pathlib.Path(p) for p in (argv[1:] or ["."])]
    files = []
    for r in roots:
        빼는폴더 = {"node_modules", ".build", "build", "dist", "__pycache__", "Tests", "tests", "__tests__",
                   "androidTest", "test", ".dart_tool", "Pods", ".gradle", ".git"}
        꼴 = (".ts", ".swift", ".tsx", ".kt", ".java", ".dart", ".js", ".jsx")
        for 폴더, 아래, 이름들 in os.walk(r):
            아래[:] = [d for d in 아래 if d not in 빼는폴더]
            for n in 이름들:
                if n.endswith(꼴) and not n.endswith(("Tests.swift", ".test.ts", ".spec.ts", "Test.kt", "Test.java", "_test.dart", ".test.js", ".spec.js", ".min.js")):
                    files.append(pathlib.Path(폴더) / n)

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
                if left < 0:
                    issues.append(f"{m} 은 이미 종료됐다 ({d}) — {SUNSET[m][1]}")
                elif left <= WARN_DAYS:
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
    if len(sys.argv) >= 3 and sys.argv[1] == "--모델":
        print(종료모델글(sys.argv[2]))
        sys.exit(0)
    sys.exit(main(sys.argv))
