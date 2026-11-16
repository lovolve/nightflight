#!/usr/bin/env python3
"""같은 증상의 **N번째**를 센다 — 기둥 A."""
import collections
import os
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

DECL = re.compile(r"^\+\s*case\s+(?!let\b)([A-Za-z_]\w*)")
ELEM = re.compile(r'^\+\s*"[^"]+"\s*,?\s*$')
SRC = (".swift", ".ts", ".tsx", ".py", ".kt", ".java")
HUNK = re.compile(r"^@@[^@]*@@\s*(.*)$")
WHERE = re.compile(r"\b(enum|struct|class|interface|extension|protocol|object|type|def|func|function)\s+([A-Za-z_]\w*)")
SKIP = ("Tests", "test", "__pycache__", ".build", "node_modules")

SPEAK_TO_FOUNDER = 3
TELL_THE_MODEL = 2


def allowlist(repo):
    p = os.environ.get("NF_SYMPTOM_ALLOW") or (Path(repo) / "NF_SYMPTOM_ALLOW")
    out = {}
    if p and Path(p).exists():
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "|" in line:
                k, why = line.split("|", 1)
                out[k.strip()] = why.strip()
    return out


def history(repo):
    out = subprocess.run(
        ["git", "-C", repo, "log", "--reverse", "--no-merges", "--unified=0",
         "--date=short", "--pretty=format:\x1e%H\x1f%ad\x1f%s", "-p"],
        capture_output=True, text=True, errors="replace")
    per = collections.defaultdict(list)
    처음 = {}
    for chunk in out.stdout.split("\x1e")[1:]:
        head, _, body = chunk.partition("\n")
        try:
            h, d, s = head.split("\x1f")
        except ValueError:
            continue
        f, 자리, found = None, "", collections.defaultdict(list)
        for ln in body.split("\n"):
            if ln.startswith("+++ b/"):
                f = ln[6:]
                자리 = ""
                if not f.endswith(SRC) or any(x in f for x in SKIP):
                    f = None
                continue
            if not f:
                continue
            m = HUNK.match(ln)
            if m:
                w = WHERE.search(m.group(1) or "")
                자리 = f"{w.group(1)} {w.group(2)}" if w else ""
                continue
            m = DECL.match(ln)
            if m:
                found[(f, 자리)].append(m.group(1))
            elif ELEM.match(ln):
                found[(f, 자리)].append(ln.strip().strip(",").strip('"')[:20])
        for (f, 자리), names in found.items():
            per[(f, 자리)].append((d, h[:7], s, names))
            처음.setdefault(f, h[:7])
    return per, 처음


def 이름(키):
    f, 자리 = 키
    return f"{f} 의 `{자리}`" if 자리 else f


def 빼뒀나(키, allowed):
    f, 자리 = 키
    for k in (f"{f}::{자리}" if 자리 else f, f):
        if k in allowed:
            return allowed[k]
    return None


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    repo = args[0] if args else os.environ.get("CLAUDE_PROJECT_DIR", ".")
    window = 14
    if "--창" in argv:
        window = int(argv[argv.index("--창") + 1])
    show_all = "--전부" in argv

    if subprocess.run(["git", "-C", repo, "rev-parse", "--git-dir"],
                      capture_output=True).returncode != 0:
        print("⛔ git 저장소가 아닙니다 — **세지 않았습니다.**")
        return 0

    per, 처음 = history(repo)
    allowed = allowlist(repo)
    cutoff = date.today() - timedelta(days=window)

    rows = []
    for f, v in per.items():
        after = len(v) - (1 if v[0][1] == 처음.get(f[0]) else 0)
        if after < 1:
            continue
        last = date.fromisoformat(v[-1][0])
        rows.append((after, last, f, v))
    rows.sort(reverse=True)

    if show_all:
        print(f"=== 설계 뒤로 원소가 붙은 커밋 수 (자리 {len(per)}곳 봤습니다) ===\n")
        for after, last, f, v in rows:
            tag = "🔴" if after >= SPEAK_TO_FOUNDER else ("⚠️ " if after == TELL_THE_MODEL else "  ")
            why = 빼뒀나(f, allowed)
            note = f"  ← 빼 둠: {why}" if why else ""
            print(f"{tag} {after:>2}회  마지막 {last}  {이름(f)}{note}")
        return 0

    spoke = 0
    for after, last, f, v in rows:
        if 빼뒀나(f, allowed) or last < cutoff:
            continue
        if after >= SPEAK_TO_FOUNDER:
            spoke += 1
            print(f"\n🔴 **같은 자리를 {after}번째 늘렸습니다** — {이름(f)}")
            print(f"   설계한 커밋 뒤로 {after}번, 원소가 {sum(len(n) for _, _, _, n in v[1:])}개 붙었습니다.\n")
            for d, h, s, names in v[1:]:
                print(f"     {d} {h} +{len(names)}  {s[:56]}")
            print("\n   ⭐ 이 제목들이 이미 진단입니다 — 매번 «고친 뒤에» 적혔습니다.")
            print("   ⛔ 「하나 더 넣을까요?」는 물을 일이 아닙니다(기술 질문입니다).")
            print("   → 물을 것은 **그 «종류»를 통째로 어떻게 할지**입니다.")
            print("      한 줄로 적고 사용자에게 제품 언어로 여쭙십시오 —")
            print("      「무엇이 N번 일어났고, 그 방식 자체를 정하시겠습니까?」")
        elif after == TELL_THE_MODEL:
            spoke += 1
            print(f"\n⚠️ {Path(f[0]).name}{(' 의 `' + f[1] + '`') if f[1] else ''} — 설계 뒤로 **두 번째**입니다(아직 여쭙지 않습니다)."
                  f" 세 번째면 «종류»를 여쭙니다.")
    return 1 if spoke else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
