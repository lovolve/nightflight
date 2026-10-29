#!/usr/bin/env python3
"""사람 자리(여러 제품에 걸쳐 따라오는 것)를 읽고 적는다.

⭐ `bin/ledger.sh` 가 부른다. 받는 것은 그 셸이 넘기는 환경변수(와 선 글)다.
⛔ **`-I` 로 부른다** — 받는 분 폴더에 `json.py` 가 심겨 있어도 파이썬의 것을 읽는다
  (`tools/lint_python_isolated.py` 가 그것을 본다).

🔴 **왜 파일로 빼냈나** (2026-10-25, ):
   전에는 이 40줄이 셸 파일 안에 들어 있었다.
   ⛔ 그 자리에는 **아무 도구도 닿지 않는다** — 린터·형식 검사·시험이 다 비껴간다.
   ⛔ 어디서 틀렸는지도 셸 줄 번호로만 나와, 수천 줄 파일에서 사람이 찾지 못한다.
   ⛔ `-c` 꼴이면 **파이썬 코드에 홑따옴표를 한 글자도 쓸 수 없다**(셸이 그것으로 감싼다).
   ⭐ 파일로 빼면 그 뒤로는 **도구가 대신 잡는다.**
"""
import os
rows = [l.rstrip("\n").split("\t") for l in open(os.environ["PERSON"], encoding="utf-8") if "\t" in l]
last = {}
for c in rows:
    if len(c) >= 3: last[c[1]] = (c[2], c[0])
CHANGES = {"계정종류", "이미한것"}
NAMES = {"계정종류": "계정이 개인 이름인지 회사 이름인지",
         "계정만든날": "그 계정을 만든 날",
         "이미한것": "이미 해 두신 것",
         "전에만든것": "전에 만드신 앱",
         "아는낱말": "아는 낱말 체크"}
order = ["계정종류", "계정만든날", "이미한것", "전에만든것", "아는낱말"]
shown = 0
for k in order:
    if k not in last: continue
    v, d = last[k]
    shown += 1
    label = NAMES.get(k, k)
    if k == "아는낱말":
        print(f"  · {label} — 이미 하셨습니다 ({d})")
        continue
    print(f"  · {label} — {v}   ({d})")
if not shown:
    print("  (아직 아무것도 없습니다)")
print()
ask = [k for k in order if k in last and k in CHANGES]
if ask:
    print("  바뀐 것이 있으면 말씀해 주세요. 그대로면 이대로 씁니다.")
    for k in ask:
        print(f"    - {NAMES[k]}")
    print()
    print("  ⚠️ 이 둘은 바뀔 수 있어서 여쭙니다 — 계정 종류가 바뀌거나,")
    print("     신청하신 것이 와서 늘어났을 수 있습니다.")
else:
    print("  바뀔 수 있는 것은 아직 들은 것이 없습니다.")
print()
miss = [k for k in order if k not in last]
if miss:
    print("  아직 안 들은 것: " + " · ".join(NAMES.get(k, k) for k in miss))
    print()
