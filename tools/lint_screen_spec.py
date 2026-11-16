#!/usr/bin/env python3
"""화면 흐름 검사 — 조종석 «화면 흐름»의 화면마다 «언제 보나» · «사용자가 여기서 하는 일»이 적혀 있나."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plan
import lint_writing as _W

짧은이름 = 6


def 빠진칸(화면들):
    out = []
    for g in 화면들:
        이름 = g["이름"]
        if not g.get("언제"):
            out.append((이름, "언제 보나", f'ledger.sh 화면언제 "{이름}" "<사용자가 언제 이 화면을 보나>"'))
        if not g.get("하는일"):
            out.append((이름, "사용자가 여기서 하는 일", f'ledger.sh 화면하는일 "{이름}" "<사용자가 여기서 하는 일>"'))
        if len(이름.replace(" ", "")) <= 짧은이름 and not g.get("풀이름") and g.get("종류") == "메일":
            out.append((이름, "풀어 쓴 이름", f'ledger.sh 화면이름 "{이름}" "<무엇의 메일인지 풀어 쓴 이름>"'))
    return out


def 용어어김(화면들):
    표 = _W.용어표() + _W.사전바꿈()
    out = []
    for g in 화면들:
        글들 = [g.get("풀이름") or g["이름"], g.get("언제", ""), g.get("하는일", ""), g.get("갈림", "")]
        글들 += [e.get("설명", "") for e in g.get("요소", [])] + [m.get("조건", "") for m in g.get("이동", [])]
        글들 += [z.get("상태", "") + " " + z.get("때", "") for z in g.get("상태", [])]
        for t in filter(None, 글들):
            for h in _W.잰다("화면", g["이름"], t, 표):
                if h[2] == "용어":
                    out.append((g["이름"], f"용어 — {h[3]}", f"«{t[:30]}»"))
    return out


def 일어긋남(화면들, 일들):
    if not 일들:
        return []
    names = {g["이름"] for g in 화면들}
    든 = {n for j in 일들 for s in j["차례"] for n in s}
    out = []
    for j in 일들:
        for n in sorted({n for s in j["차례"] for n in s} - names):
            out.append((j["이름"], f"없는 화면 «{n}»", f'ledger.sh 화면일 "{j["이름"]}" "<언제>" <화면> … 로 다시 적거나 ledger.sh 화면일빼기 "{j["이름"]}"'))
    for g in 화면들:
        if g["이름"] not in 든:
            out.append((g["이름"], "어느 하는 일에도 안 듦", f'ledger.sh 화면일 "<하는 일>" "<언제>" … "{g["이름"]}" …'))
    return out


def main():
    화면들 = plan.화면읽기()
    빠 = 빠진칸(화면들) + 용어어김(화면들) + 일어긋남(화면들, plan.화면일읽기())
    if not 빠:
        return 0
    print(f"  🔴 화면 흐름에 고칠 곳 {len(빠)}개 — 빈 칸은 조종석에 «아직 적지 않았습니다»로 나갑니다")
    for 이름, 칸, 명령 in 빠[:12]:
        print(f"     · «{이름}» {칸} → {명령}")
    if len(빠) > 12:
        print(f"     … 외 {len(빠) - 12}개")
    return 1


if __name__ == "__main__":
    sys.exit(main())
