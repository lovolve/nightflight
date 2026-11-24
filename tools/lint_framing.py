#!/usr/bin/env python3
"""금지된 «틀 씌우기»를 찾는다 — 제품 개념에 사용자가 원하지 않은 방향을 붙이는 말을 기계가 잡는다."""
import os, re, subprocess, sys
from pathlib import Path

DEFAULT = []
SKIP_LINE = re.compile(r"~~|⛔|🔴|환상|폐기|금지")
SKIP_HEAD = re.compile(r"환상|폐기|방향이 없다|쓰지 말|잘못|고침|바로잡|정정")
HEADING   = re.compile(r"^#{1,6}\s")

def repo_root() -> Path:
    try:
        return Path(subprocess.check_output(["git","rev-parse","--show-toplevel"],
                    text=True, stderr=subprocess.DEVNULL).strip())
    except Exception:
        return Path.cwd()

def load_words():
    f = os.environ.get("NF_FRAMING")
    if f and os.path.exists(f):
        out = []
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "|" in line:
                w, why = line.split("|", 1); out.append((w.strip(), why.strip()))
        if out: return out
    return DEFAULT

def main():
    roots = [Path(a).expanduser() for a in sys.argv[1:]] or [repo_root()]
    words = load_words()
    if not words:
        print("=== 제품 개념에 «방향»을 붙이는 말 (보고 전용) ===")
        print("  이 앱에는 쓰지 않기로 한 낱말 목록이 없어 보지 않았다(NF_FRAMING)")
        return 0
    files = []
    for r in roots:
        files += sorted(r.rglob("*.md")) if r.is_dir() else [r]
    hits = []
    for p in files:
        if any(x in p.parts for x in (".git", "node_modules", ".build", "board")): continue
        try: lines = p.read_text(encoding="utf-8", errors="ignore").split("\n")
        except OSError: continue
        in_fix = False
        for i, line in enumerate(lines):
            if HEADING.match(line):
                in_fix = bool(SKIP_HEAD.search(line))
            if in_fix or SKIP_LINE.search(line): continue
            for w, why in words:
                if w in line:
                    hits.append((p, i+1, w, why, line.strip()[:76]))

    print("=== 제품 개념에 «방향»을 붙이는 말 (보고 전용) ===")
    if not hits:
        print("  ✅ 없다"); return 0
    print(f"  {len(hits)}곳. ⚠️ 정당한 자리도 있다 — 경쟁사 서술이면 그대로 두고,")
    print("  우리 제품을 그렇게 «정의»하고 있으면 고친다.\n")
    led = Path(__file__).resolve().parent.parent / "bin" / "ledger.sh"
    for p, n, w, why, txt in hits:
        try: rel = p.relative_to(repo_root())
        except ValueError: rel = p
        print(f"  {rel}:{n}  「{w}」\n      {txt}\n      ↳ {why}")
    if os.access(led, os.X_OK):
        try:
            subprocess.run([str(led), "막음",
                "제품에 없는 성격을 붙여 쓰고 있던 것",
                f"틀 검사 — {len(hits)}곳",
                "그 위에 화면과 문구를 쌓은 뒤에 알게 되면, 고치는 범위가 제품 전체가 됩니다",
                ], check=False, capture_output=True)
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
