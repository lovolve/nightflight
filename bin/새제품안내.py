#!/usr/bin/env python3
"""제품등록 하나로 다른 제품을 시작하는 것 같을 때 «새 제품은 제품등록이 필요합니다»를 «안내»한다 — 막지 않는다.

🔴 2026-10-28 — 등록한 제품 하나로 여러 제품을 만드는 것은 막는 장치를 만들지 않는다(정직한 사용자가 걸릴 위험이 더 크다).
  대신 새 제품을 시작하는 것 같으면 안내만 띄운다. 그렇게 쓰는 사람이 많이 보이면 출시 때 앱 이름표 묶기를 다시 본다.

받는 것: argv[1] = 기록 파일(ledger.tsv) · argv[2] = 때(단계 · 소개). 기록에 새 줄을 «적은 뒤에» 부른다.
  단계: 설계(3) 이상까지 갔던 제품이 진단 · 기획 · 검증(0~2)으로 돌아왔다.
  소개: 설계 이상까지 갔던 제품의 «한줄» 소개가 바뀌었다.
찍는 것: 사용자에게 옮길 안내 한 줄 + 모델에게 묻는 법. 같은 날 같은 때는 한 번만(기록 자리의 새제품안내.tsv).
⛔ 같은 제품을 다듬는 중일 수 있다 — 단정하지 않고 묻는다. 막지 않는다.
"""
import os, sys, time

기록 = sys.argv[1] if len(sys.argv) > 1 else ""
때 = sys.argv[2] if len(sys.argv) > 2 else ""
if 때 not in ("단계", "소개") or not 기록:
    sys.exit(0)

단계들 = "진단 기획 검증 설계 개발 확인 출시 수정 출시후".split()


def 번호(이름):
    for i in range(len(단계들) - 1, -1, -1):
        if 단계들[i] in 이름:
            return i
    return None


단계줄, 한줄들 = [], []
try:
    for 줄 in open(기록, encoding="utf-8", errors="replace"):
        칸 = 줄.rstrip("\n").split("\t")
        if len(칸) > 2 and 칸[1] == "단계":
            n = 번호(칸[2])
            if n is not None:
                단계줄.append(n)
        elif len(칸) > 3 and 칸[1] == "제품소개" and 칸[2] == "한줄":
            한줄들.append((칸[3].strip(), 단계줄[-1] if 단계줄 else None))
except OSError:
    sys.exit(0)

if 때 == "단계":
    if len(단계줄) < 2 or 단계줄[-1] > 2 or max(단계줄[:-1]) < 3:
        sys.exit(0)
    무엇 = "설계까지 갔던 제품이 " + 단계들[단계줄[-1]] + " 단계로 돌아왔습니다"
else:
    if len(한줄들) < 2 or 한줄들[-1][0] == 한줄들[-2][0] or not 단계줄 or max(단계줄) < 3:
        sys.exit(0)
    무엇 = "설계까지 갔던 제품의 한 줄 소개가 바뀌었습니다"

오늘 = time.strftime("%Y-%m-%d")
자리 = os.path.join(os.path.dirname(기록), "새제품안내.tsv")
try:
    for 줄 in open(자리, encoding="utf-8", errors="replace"):
        if 줄.rstrip("\n").split("\t")[:2] == [오늘, 때]:
            sys.exit(0)
except OSError:
    pass
try:
    with open(자리, "a", encoding="utf-8") as f:
        f.write(오늘 + "\t" + 때 + "\n")
except OSError:
    pass

print("  · 새 제품 안내 — " + 무엇 + ".")
print("    [모델] 사용자에게 이렇게 물으십시오: «같은 제품을 다듬고 계신 건가요, 다른 제품을 새로 시작하시는 건가요?» 단정하지 않습니다. 막지 않습니다.")
print("    [모델] 같은 제품이면 그대로 이어 가십시오. 다른 제품이면 «새 제품은 새 폴더에서 시작하고, 설계를 시작할 때 제품등록이 하나 더 필요합니다. 아이디어와 검증은 몇 개든 무료입니다»라고 알리십시오.")
