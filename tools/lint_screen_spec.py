#!/usr/bin/env python3
"""화면 흐름 검사 — 조종석 «화면 흐름»의 화면마다 «언제 보나» · «사용자가 여기서 하는 일»이 적혀 있나.


  「키메일, 등급바꾸기 확인 같은 말은 너무 축약해서 무슨 말인지를 모르겠어 · 들어오는길, 나가는길도 개념도 이상해」
  → 화면마다 «언제 보나» · «하는 일»을 적고, 줄인 이름에는 풀어 쓴 이름을 단다. 빠지면 이 검사가 알린다.

규칙
  ① 화면마다 «언제 보나»(plan.py 화면언제)와 «하는 일»(plan.py 화면하는일)이 있다.
  ③ 화면에 나가는 글(풀어 쓴 이름 · 언제 · 하는 일 · 보이는 것 · 이동 조건 · 갈림 · 상태)이 용어집 · 낱말 사전을 지키나 —
     «단추» · «사기»가 코드에서 채운 화면 기록에 들어왔다(2026-10-25). 쓰기 검사(lint_writing)의 같은 함수로 잰다.
  ② 메일인데 이름이 여섯 글자 이하이고 풀어 쓴 이름(plan.py 화면이름)이 없으면 알린다 — «키 메일»은 무엇의 메일인지 모른다.
⚠️ 기계가 못 보는 것: 적은 문장이 맞는지. 화면이 없는 제품은 볼 것이 없어 통과한다.

쓰는 법
  python3 tools/lint_screen_spec.py
"""
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
    """⭐ 2026-10-27 «하는 일» 줄(plan.py 화면일) — 화면과 어긋나면 조종석에서 빈 자리가 생긴다.
    하는 일이 하나도 없으면 묻지 않는다(조종석이 적은 차례대로 한 줄로 보인다). 있으면: 없는 화면을 가리키나 · 어느 일에도 안 든 화면이 있나."""
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
