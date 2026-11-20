#!/usr/bin/env python3
"""야간비행 도구"""
from __future__ import annotations
import datetime
import os
import sys
from pathlib import Path


def _ledger() -> Path:
    return Path(os.environ.get("NF_LEDGER") or "")


def _root() -> Path:
    return Path(os.environ.get("NF_ROOT") or os.getcwd())


def 자리(p: str, root: Path) -> Path:
    q = Path(os.path.expanduser(p.strip()))
    return q if q.is_absolute() else (root / q)


def _rows(lp: Path):
    try:
        for line in lp.read_text(encoding="utf-8").splitlines():
            c = line.split("\t")
            if len(c) >= 4:
                yield c
    except OSError:
        return


def 짝들(lp: Path, root: Path):
    seen = {}
    for c in _rows(lp):
        if c[1] == "짝파일" and len(c) >= 5:
            seen[(c[2], c[3])] = (자리(c[2], root), 자리(c[3], root), c[2], c[3], c[4] if len(c) > 4 else "")
    return list(seen.values())


def _mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def 확인됨(lp: Path, root: Path, f: Path) -> bool:
    mt = _mtime(f)
    for c in _rows(lp):
        if c[1] == "짝확인" and 자리(c[2], root).resolve() == f.resolve():
            try:
                if abs(float(c[3]) - mt) < 1.0:
                    return True
            except ValueError:
                pass
    return False


def 같이볼곳(lp: Path, root: Path, f: Path):
    out = []
    fr = f.resolve() if f.exists() else f
    for a, b, at, bt, why in 짝들(lp, root):
        if a.resolve() == fr:
            out.append((bt, why))
        elif b.resolve() == fr:
            out.append((at, why))
    return out


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "짝목록"
    lp, root = _ledger(), _root()
    today = datetime.date.today().isoformat()
    if cmd == "짝파일":
        if len(argv) < 5 or not all(x.strip() for x in argv[2:5]):
            print('  ⛔ 쓰는 법: ledger.sh 짝파일 "<파일 A>" "<파일 B>" "<무엇을 같이 쓰나>"', file=sys.stderr)
            return 1
        a, b, why = argv[2].strip(), argv[3].strip(), argv[4].strip().replace("\t", " ")
        for p in (a, b):
            if not 자리(p, root).exists():
                print(f"  ⛔ 파일이 없습니다: {p} — 자리를 확인하십시오(프로젝트 기준 상대 · 절대 · ~/…)", file=sys.stderr)
                return 1
        with lp.open("a", encoding="utf-8") as fh:
            fh.write(f"{today}\t짝파일\t{a}\t{b}\t{why}\t\n")
        print(f"  · 짝을 적었습니다 — {a} ↔ {b}")
        print("    이제 한쪽을 고치면 고치는 순간과 턴 끝에 다른 쪽을 같이 보라고 알립니다.")
        return 0
    if cmd == "짝확인":
        if len(argv) < 4 or not argv[3].strip():
            print('  ⛔ 쓰는 법: ledger.sh 짝확인 "<파일>" "<왜 다른 쪽은 안 바꿔도 되나>"', file=sys.stderr)
            return 1
        f = 자리(argv[2], root)
        if not f.exists():
            print(f"  ⛔ 파일이 없습니다: {argv[2]}", file=sys.stderr)
            return 1
        with lp.open("a", encoding="utf-8") as fh:
            fh.write(f"{today}\t짝확인\t{argv[2].strip()}\t{_mtime(f):.0f}\t{argv[3].strip().replace(chr(9), ' ')}\t\n")
        print(f"  · 적었습니다 — {argv[2].strip()} 은 다시 고치기 전까지 짝 알림을 하지 않습니다.")
        return 0
    if cmd == "짝목록":
        ps = 짝들(lp, root)
        if not ps:
            print("  적힌 짝 파일이 없습니다.")
            return 0
        for a, b, at, bt, why in ps:
            print(f"  · {at} ↔ {bt} — {why}")
        return 0
    if cmd == "알림":
        sess = argv[2] if len(argv) > 2 else ""
        said = Path(os.environ.get("NF_STATE") or (root / ".claude")) / "internal" / "pairs-said.tsv"
        try:
            done = set(said.read_text(encoding="utf-8").splitlines())
        except OSError:
            done = set()
        out, new = [], []
        for line in sys.stdin.read().splitlines():
            if not line.strip():
                continue
            f = Path(line.strip())
            key = f"{sess}\t{f}"
            if key in done:
                continue
            for other, why in 같이볼곳(lp, root, f):
                out.append(f"· {f.name} 를 고쳤습니다 — 짝 파일 {other} 도 같이 봐야 합니다: {why}")
            if out:
                new.append(key)
        if out:
            try:
                said.parent.mkdir(parents=True, exist_ok=True)
                with said.open("a", encoding="utf-8") as fh:
                    fh.write("".join(k + "\n" for k in new))
            except OSError:
                pass
            print("야간비행 — 짝 파일 알림(고친 그 순간):")
            print("\n".join(out))
            print('바꿀 것이 없으면 ledger.sh 짝확인 "<고친 파일>" "<까닭>" 을 적으십시오. 안 적고 턴을 끝내면 턴 끝 검사가 짚습니다.')
        return 0
    print(f"  ⛔ 모르는 명령: {cmd}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
