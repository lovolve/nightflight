#!/usr/bin/env python3
"""셸 계산에 들어가는 값이 파일에서 왔으면, 계산 전에 숫자인지 거르는지 본다."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CALC = re.compile(r"\$\(\((.*?)\)\)")
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
READ = re.compile(r"(?:^|[;&|]\s*|\bthen\s+|\bdo\s+)read\s+(?:-[a-zA-Z]+\s+)*([A-Za-z_][A-Za-z0-9_ ]*?)\s*(?:<|$|;)")
FROM_FILE = re.compile(r"\$\([^)]*\b(?:cat|head|tail|cut|sed|grep|awk)\b")
SAFE = re.compile(r"wc -l|date \+%s|\+0\}|\bdu -|\bsysctl\b|\bcksum\b")


def code_of(line):
    return "" if line.lstrip().startswith("#") else line


def check(path):
    lines = [code_of(x) for x in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    used = {}
    for n, line in enumerate(lines, 1):
        for body in CALC.findall(line):
            for name in NAME.findall(re.sub(r"\"[^\"]*\"|'[^']*'", " ", body)):
                used.setdefault(name, []).append(n)
    bad = []
    for name, uses in used.items():
        assign = re.compile(rf"(?:^|[\s;&(]){name}=(.*)")
        for n, line in enumerate(lines, 1):
            m = assign.search(line)
            outside = False
            if m:
                rhs = m.group(1).split(f"; ")[0]
                outside = bool(FROM_FILE.search(rhs)) and not SAFE.search(rhs)
            for r in READ.finditer(line):
                outside = outside or name in r.group(1).split()
            if not outside:
                continue
            later = [u for u in uses if u > n]
            if not later:
                continue
            guard = re.compile(rf"""case "\${name}" in\s*''\|\*\[!0-9\]\*""")
            between = "\n".join(lines[n - 1:later[0] - 1])
            if not guard.search(between):
                bad.append((n, name))
    return bad


def main():
    if len(sys.argv) > 1:
        files = [Path(x) for x in sys.argv[1:]]
    else:
        out = subprocess.run(
            ["git", "-c", "core.quotepath=off", "ls-files", "*.sh"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout
        files = [ROOT / x for x in out.splitlines() if not x.startswith("tests/")]
    count = 0
    for f in files:
        if not f.is_file():
            continue
        for n, name in check(f):
            count += 1
            print(f"  ⛔ {f.name}:{n}  파일에서 읽은 {name} 을(를) 숫자인지 거르지 않고 계산에 넣습니다.")
    if count:
        print(f"  ⛔ 거르지 않은 자리 {count}곳: 받은 저장소의 파일 한 줄로 명령이 실행될 수 있습니다.")
        return 1
    print("  ✓ 파일에서 읽은 값은 모두 숫자인지 거른 뒤 계산합니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
