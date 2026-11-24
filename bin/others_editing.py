#!/usr/bin/env python3
"""다른 대화가 고치고 아직 커밋하지 않은 파일을 찾는다."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

TAIL = 4 * 1024 * 1024


def _git(뿌리: Path, *a: str) -> str:
    try:
        r = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(뿌리), *a],
                           capture_output=True, text=True, timeout=20)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def 바뀐파일(뿌리: Path) -> set[str]:
    맨위 = _git(뿌리, "rev-parse", "--show-toplevel").strip()
    if not 맨위:
        return set()
    맨위p = Path(맨위)
    위험 = r"^(filter\..*\.(clean|smudge|process)|diff\..*\.(textconv|command)|core\.fsmonitor|include\..*|includeif\..*)$"
    if _git(뿌리, "config", "--local", "--includes", "--get-regexp", 위험).strip() \
       or _git(뿌리, "config", "--worktree", "--includes", "--get-regexp", 위험).strip():
        return set()
    try:
        _속성 = [맨위p / ".gitattributes", Path(_git(뿌리, "rev-parse", "--git-path", "info/attributes").strip() or "/없음")]
        if not Path(_속성[1]).is_absolute():
            _속성[1] = 맨위p / _속성[1]
        if any(p.is_file() and "filter=" in p.read_text(encoding="utf-8", errors="replace") for p in _속성):
            return set()
    except OSError:
        return set()
    나온 = _git(뿌리, "status", "--porcelain", "-z", "--untracked-files=all")
    out = set()
    조각 = 나온.split("\0")
    i = 0
    while i < len(조각):
        x = 조각[i]
        i += 1
        if len(x) < 4:
            continue
        상태, 길 = x[:2], x[3:]
        if "R" in 상태 or "C" in 상태:
            i += 1
        out.add(str((맨위p / 길).resolve()))
    return out


def _마지막커밋때(뿌리: Path, 파일: str) -> int:
    t = _git(뿌리, "log", "-1", "--format=%ct", "--", 파일).strip()
    return int(t) if t.isdigit() else 0


def 대화이름(sid: str, 집: Path | None = None) -> str:
    집 = 집 or Path(os.environ.get("HOME") or Path.home())
    try:
        후보 = sorted((집 / ".claude" / "projects").glob(f"*/{sid}.jsonl"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        후보 = []
    for p in 후보[:2]:
        try:
            with open(p, "rb") as fh:
                크기 = p.stat().st_size
                fh.seek(max(0, 크기 - TAIL))
                글 = fh.read().decode("utf-8", "ignore")
        except OSError:
            continue
        자리 = 글.rfind('"customTitle":"')
        if 자리 >= 0:
            시작 = 자리 + len('"customTitle":"')
            끝 = 글.find('"', 시작)
            이름 = 글[시작:끝].strip()
            if 이름 and len(이름) <= 80:
                return 이름
    return f"다른 대화({sid[:8]})"


def 찾기(뿌리: Path, 기록: Path, 내대화: str = "", 집: Path | None = None) -> list[dict]:
    바뀐 = 바뀐파일(뿌리)
    if not 바뀐:
        return []
    고친: dict[str, dict[str, int]] = {}
    try:
        줄들 = (기록 / "internal" / "repeat-guard.tsv").read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for 줄 in 줄들:
        c = 줄.split("\t")
        if len(c) < 4 or not c[0] or not c[3].strip().isdigit():
            continue
        try:
            f = str(Path(c[1]).resolve())
        except OSError:
            continue
        if f not in 바뀐:
            continue
        t = int(c[3].strip())
        고친.setdefault(f, {})
        고친[f][c[0]] = max(고친[f].get(c[0], 0), t)
    out = []
    for f in sorted(고친):
        뒤 = _마지막커밋때(뿌리, f)
        대화들 = {s: t for s, t in 고친[f].items() if t >= 뒤}
        남 = {s: t for s, t in 대화들.items() if s != 내대화}
        if not 남:
            continue
        try:
            보임 = str(Path(f).relative_to(Path(_git(뿌리, "rev-parse", "--show-toplevel").strip()).resolve()))
        except ValueError:
            보임 = f
        out.append({"파일": 보임,
                    "대화들": [(대화이름(s, 집), t) for s, t in sorted(남.items(), key=lambda x: -x[1])],
                    "이대화도": 내대화 in 대화들})
    return out


def _때(t: int) -> str:
    import time
    return time.strftime("%m-%d %H:%M", time.localtime(t))


def 사람글(목록: list[dict]) -> str:
    if not 목록:
        return "다른 대화가 고치고 아직 커밋하지 않은 파일은 없습니다."
    줄 = [f"다른 대화가 고치고 아직 커밋하지 않은 파일이 {len(목록)}개 있습니다."]
    for x in 목록:
        누구 = " · ".join(f"{n}({_때(t)})" for n, t in x["대화들"])
        줄.append(f"  · {x['파일']} — {누구}" + (" · 이 대화도 고침" if x["이대화도"] else ""))
    return "\n".join(줄)


def 모델글(목록: list[dict]) -> str:
    if not 목록:
        return ""
    return ("야간비행: " + 사람글(목록) + "\n"
            "⛔ 커밋 · 공개본에 그 파일의 다른 대화 몫을 담지 마십시오. 같은 파일에 이 대화의 고침이 섞였으면 이 대화의 덩어리만 담으십시오. "
            "⭐ 그 파일 때문에 공개나 시험이 막히면, 그 대화에 메시지로 알리고 사용자께 무엇이 막혔는지 말하십시오. 그 대화의 커밋은 그 대화가 사용자 승인을 받아 합니다.")


def main(argv: list[str]) -> int:
    세션 = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    뿌리 = Path.cwd()
    기록 = None
    모델 = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--세션", "--뿌리", "--기록") and i + 1 < len(argv):
            v = argv[i + 1]
            if a == "--세션":
                세션 = v
            elif a == "--뿌리":
                뿌리 = Path(v)
            else:
                기록 = Path(v)
            i += 2
            continue
        if a == "--모델":
            모델 = True
        i += 1
    if 기록 is None:
        for 이름 in (".nightflight", ".claude"):
            if (뿌리 / 이름 / "internal" / "repeat-guard.tsv").exists():
                기록 = 뿌리 / 이름
                break
    if 기록 is None:
        if not 모델:
            print("고친 파일 기록을 찾지 못해 확인하지 않았습니다.")
        return 0
    목록 = 찾기(뿌리, 기록, 세션)
    글 = 모델글(목록) if 모델 else 사람글(목록)
    if 글:
        print(글)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
