#!/usr/bin/env python3
"""야간비행 도구"""
from __future__ import annotations
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _root

겹침최소 = 6
커밋최대 = 20
흔한말 = {"있다", "없다", "한다", "것을", "것이", "에서", "으로", "하고", "그리고", "다음", "새로",
         "확인", "확인한다", "고친다", "만든다", "있는", "없는", "하는", "되는", "Co-Authored-By", "Claude",
         "noreply@anthropic.com", "Opus"}


def 낱말(s: str) -> set[str]:
    return {w for w in re.findall(r"[가-힣A-Za-z0-9/._-]{2,}", s) if w not in 흔한말 and not w.startswith("대표")}


def 열린일(ledger: Path) -> list[tuple[str, str]]:
    rows = []
    with ledger.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) > 2:
                rows.append(c)
    닫힘 = [r[2] for r in rows if r[1] in ("끝냄", "없어짐") and r[2]]
    return [(r[0], r[2]) for r in rows
            if r[1] == "남은것" and r[2] and not any(k in r[2] for k in 닫힘)]


_GIT안전 = ["-c", "core.fsmonitor=false", "-c", "log.showSignature=false"]


def git(repo: Path, *args: str) -> str:
    try:
        return subprocess.run(["git", *_GIT안전, "-C", str(repo), *args], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return ""


def main() -> int:
    try:
        st = _root.state_dir()
        ledger = st / "ledger.tsv"
    except Exception:
        return 0
    if not ledger.is_file():
        return 0
    repo = Path(git(st, "rev-parse", "--show-toplevel").strip() or ".")
    head = git(repo, "rev-parse", "HEAD").strip()
    if not head:
        return 0
    표 = _root.sys_path(st, "done_unclosed_seen")
    try:
        본곳 = 표.read_text(encoding="utf-8").strip()
    except Exception:
        본곳 = ""
    if 본곳 == head:
        return 0
    if not 본곳 or not git(repo, "cat-file", "-t", 본곳).strip():
        새것 = []
    else:
        새것 = [h for h in git(repo, "rev-list", f"--max-count={커밋최대}", f"{본곳}..HEAD").split() if h]
    try:
        표.parent.mkdir(parents=True, exist_ok=True)
        표.write_text(head + "\n", encoding="utf-8")
    except Exception:
        pass
    if not 새것:
        return 0
    열린 = 열린일(ledger)
    찾음 = []
    for h in 새것:
        글 = git(repo, "show", "-s", "--format=%h\t%B", h)
        if "\t" not in 글:
            continue
        짧은, 본문 = 글.split("\t", 1)
        커밋낱말 = 낱말(본문[:2000])
        for 날, 일 in 열린:
            겹 = 낱말(일) & 커밋낱말
            if len(겹) >= 겹침최소:
                찾음.append((len(겹), 짧은.strip(), 일, sorted(겹)[:6]))
    if not 찾음:
        return 0
    찾음.sort(reverse=True)
    print("  🟡 새 커밋이 끝낸 하던 일일 수 있습니다 — 열어 보고, 끝났으면 닫으십시오")
    for n, h, 일, 겹 in 찾음[:6]:
        print(f"     · 커밋 {h} ↔ 「{일[:90]}」")
        print(f"       겹친 말 {n}개: {' · '.join(겹)}")
    print("     [모델] 끝났으면: ledger.sh 됐다 \"<무엇이>\" \"<무엇이 확인했나>\" 다음 ledger.sh 끝냄 \"<하던 일 글 일부>\"")
    print("     [모델] 일부만 끝났으면: 남은 부분만 ledger.sh 남은것 으로 다시 적고 옛 줄을 끝냄 으로 닫으십시오")
    return 1


if __name__ == "__main__":
    sys.exit(main())
