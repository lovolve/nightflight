#!/usr/bin/env python3
"""컴퓨터 열쇠(계정 로그인으로 받은 것)를 화면에 찍는 줄이 없나 본다."""
import re
import sys
from pathlib import Path

뿌리 = Path(__file__).resolve().parent.parent
셸값 = re.compile(r'\$\{?CKEY\b|nf_ckey|account/key')
셸찍 = re.compile(r'^\s*(echo|printf)\b|[;&|]\s*(echo|printf)\b')
파값 = re.compile(r'열쇠\(\)|\[\s*["\']열쇠["\']\s*\]|\b_ck\b|컴퓨터열쇠\(\)|NF_B_CKEY')
파찍 = re.compile(r'\b(print|찍기|say|모델)\s*\(')


def 본다(p):
    걸림 = []
    try:
        줄들 = p.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return 걸림
    셸 = p.suffix == ".sh" or (줄들 and 줄들[0].startswith("#!") and "bash" in 줄들[0])
    for i, 줄 in enumerate(줄들, 1):
        글 = 줄.split("#", 1)[0] if 셸 else 줄
        if not 셸 and 글.lstrip().startswith("#"):
            continue
        if 셸 and 셸찍.search(글) and 셸값.search(글):
            걸림.append((i, 줄.strip()))
        if not 셸 and 파찍.search(글) and 파값.search(글):
            걸림.append((i, 줄.strip()))
    return 걸림


def main(a):
    파일들 = [Path(x) for x in a] or sorted(list((뿌리 / "bin").glob("*.sh")) + list((뿌리 / "bin").glob("*.py")))
    모두 = []
    for p in 파일들:
        for i, 줄 in 본다(p):
            모두.append("    · %s:%d  %s" % (p.name, i, 줄[:140]))
    if 모두:
        print("  ⛔ 컴퓨터 열쇠를 화면에 찍는 줄이 %d곳 있습니다 — 열쇠는 서버로 가는 몸에만 넣습니다:" % len(모두))
        print("\n".join(모두))
        return 1
    print("  ✅ 컴퓨터 열쇠를 화면에 찍는 줄이 없습니다")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
