#!/usr/bin/env python3
"""단계마다 며칠 걸렸는지 센다 — 조종석의 진행경과가 그 값을 쓴다."""
import os, unicodedata
W  = int(os.environ["W"]); IND = "  "
HB, HW, MM, RR = (os.environ[k] for k in ("HB","HW","MM","RR"))

def cols(t):
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in t)

def wrap(text, limit):
    out, line = [], ""
    for word in text.split():
        cand = (line + " " + word).strip()
        if cols(cand) > limit and line:
            out.append(line); line = word
        else:
            line = cand
    if line: out.append(line)
    return out or [""]

def block(label, color, lines):
    print(f"{IND}{color}{label}{RR}")
    for raw in lines:
        for l in wrap(raw, W - len(IND) * 2):
            print(f"{IND}{l}")
    print()

print()
block("지금 결정하실 것", HB, [os.environ["WHAT"]])
block("왜 여쭙나", HW, os.environ["WHY"].split(" · "))
block("이것만 정하시면 됩니다", HB, [os.environ["ONLY"]])
block("그 다음은 제가 맡습니다", MM, [os.environ["MINE"]])
block("지금 정하면 / 나중에 정하면", HW, [
    "지금 정하시면 그대로 만듭니다 \u2014 다시 만드는 일이 없습니다.",
    "나중에 정하시면 " + os.environ["LATER"],
])
BULLET = chr(0xB7) + " "
done = [d for d in os.environ["DONE"].splitlines() if d.strip()]
print(f"{IND}{MM}안 여쭙고 처리한 것{RR}")
if done:
    for d in done:
        for i, l in enumerate(wrap(d, W - len(IND)*2 - 2)):
            mark = BULLET if i == 0 else "  "
            print(f"{IND}{MM}{mark}{l}{RR}")
else:
    print(f"{IND}{MM}(없습니다){RR}")
print()
