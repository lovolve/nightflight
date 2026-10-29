#!/usr/bin/env python3
"""묶임 — **정하기 전에** 「이걸 정하면 뒤에 무엇에 묶이나」를 보인다.

설계: nightflight-server design/비개발자와-개발자의-차이.md 축 ③

🔴 왜 (
   설계가 「만들 것: **「지금 이걸 정하면 뒤에 이것들이 묶입니다」를 «정하기 전에» 보여준다.**
   기록의 전제가 이미 그 자리인데 **사후**다. 사전으로 뒤집는다」고 적어 뒀다.

🔴 **그런데 사후였다** (실측 2026-10-08): 기록의 「묶임」 칸은 결정을 적을 때 받고,
   그 문장을 **내가 지어낸다.** 표가 없었다 — 손으로만 적히는 칸은 반드시 부풀고,
   **빠진 것은 아무도 모른다.**


| | 어디서 | 언제 아나 |
|---|---|---|
| **기능에서** | `data/기능.tsv` 다섯째 칸 | **B-3 에서 이미 안다** — 만들기 전이다 |
| **결정에서** | `data/묶임.tsv` 방아쇠 | 만들다가 생긴다 |

⛔ **기능 쪽 문구를 새로 쓰지 않는다.** 기능 표의 「바로 말하는 것」이 원본이고
   다섯째 칸은 **분류일 뿐**이다(두 곳에 문구를 두면 한 곳이 낡는다 — 기능 표의 못).

⛔ **「못되돌림」을 기능 표의 묶임 칸에서 읽지 않는다.** 넷째 칸(「껍데기로는 안 되나」)이
   이미 그것이라 거기서 **유도한다** — 그 기능을 고르셨고 만드는 법이 「웹을 껍데기에」면
   **나중에 못 붙인다**(손해 147건 ⑥ 이 그것이다).

⛔ **막지 않는다. 보이게 한다.** 무엇에 묶일지 알고 정하는 것은 대표님 몫이다.

쓰기:  binding_ahead.py
       binding_ahead.py --결정 "<문장>"
       binding_ahead.py --json
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _root as _root_mod

KINDS = ("돈", "시간", "법", "못되돌림")


def _state():
    v = os.environ.get("NF_STATE")
    return Path(v) if v else _root_mod.state_dir()


def _rows(p):
    if not p.exists():
        return []
    return [l.rstrip("\n").split("\t") for l in p.read_text(encoding="utf-8").splitlines()
            if "\t" in l and not l.startswith("#")]


def _기능표():
    out = {}
    for c in _rows(HERE.parent / "data" / "기능.tsv"):
        out[c[0]] = {"말": c[1] if len(c) > 1 else "",
                     "껍데기": c[3] if len(c) > 3 else "",
                     "묶임": [k for k in (c[4] if len(c) > 4 else "").split(",") if k.strip()]}
    return out


def _방아쇠표():
    out = []
    for c in _rows(HERE.parent / "data" / "묶임.tsv"):
        if len(c) < 4:
            continue
        out.append({"방아쇠": [t.strip() for t in c[0].split(",") if t.strip()],
                    "묶임": [k.strip() for k in c[1].split(",") if k.strip()],
                    "말": c[2], "확인": c[3], "설명키": c[4] if len(c) > 4 else ""})
    return out


def _앱설정():
    """마지막 줄이 이긴다 — 앱설정과 같은 규칙."""
    out = {}
    for c in _rows(_state() / "ledger.tsv"):
        if len(c) > 3 and c[1] == "앱설정":
            out[c[2]] = c[3]
    return out


def 기능에서():
    """고르신 기능에서 걸리는 묶임. ⛔ 안 들었으면 «못 봤다»고 한다."""
    설정, 표 = _앱설정(), _기능표()
    if "기능" not in 설정:
        return None, []
    만드는법 = 설정.get("만드는법", "")
    hits = []
    for v in [x.strip() for x in 설정["기능"].split("·") if x.strip()]:
        if v in ("모름", ""):
            continue
        f = 표.get(v)
        if not f:
            continue
        종류 = list(f["묶임"])
        덧 = ""
        if f["껍데기"] in ("안됨", "어려움") and 만드는법 == "웹을껍데기에":
            종류.append("못되돌림")
            덧 = ("이 기능은 **나중에 붙이기 어렵습니다** — 지금 고르신 만드는 법으로는 "
                  + ("못 붙입니다" if f["껍데기"] == "안됨" else "어렵습니다"))
        if 종류:
            hits.append({"기능": v, "묶임": 종류, "말": f["말"], "덧": 덧})
    return 만드는법, hits


def 결정에서(문장):
    out = []
    for r in _방아쇠표():
        for t in r["방아쇠"]:
            if t in 문장:
                out.append({**r, "걸린말": t})
                break
    return out


def 종류모으기(기능hits, 결정hits):
    s = []
    for h in 기능hits:
        s += h["묶임"]
    for h in 결정hits:
        s += h["묶임"]
    return [k for k in KINDS if k in s]


def 화면(문장=""):
    만드는법, fh = 기능에서()
    dh = 결정에서(문장) if 문장 else []
    print()
    print("── 이걸 정하면 뒤에 무엇에 묶이나 ──────────────")
    if 만드는법 is None:
        print("   ⚠️ 어떤 기능을 넣으실지 아직 안 들었습니다 — **「없다」가 아니라 「못 봤다」**입니다.")
    if not fh and 만드는법 is not None:
        print("   고르신 기능에서는 해야 하는 것이 없습니다.")
    for h in fh:
        print()
        print(f"   [{' · '.join(h['묶임'])}]  {h['기능']}")
        print(f"        {h['말']}")
        if h["덧"]:
            print(f"        🔴 {h['덧']}")
    if 문장:
        print()
        if not dh:
            print(f"   「{문장[:40]}」에서 해야 하는 것은 표에 없습니다.")
            print("      ⚠️ 이건 「묶이는 것이 없다」가 아니라 **표에 아직 없다**는 뜻입니다.")
        for h in dh:
            print(f"   [{' · '.join(h['묶임'])}]  「{h['걸린말']}」 때문에 여쭙니다")
            print(f"        {h['말']}")
            print(f"        (어디서 알았나: {h['확인']})")
    종류 = 종류모으기(fh, dh)
    print()
    if 종류:
        print(f"   ⭐ 묶이는 것: **{' · '.join(종류)}**")
        print("   ⚠️ 넷 다 **만드는 동안에는 비용이 0**이고 **내시는 순간부터** 시작됩니다.")
        print("      그래서 알고 정하시는 것과 모르고 정하시는 것이 다릅니다.")
    print("   ⛔ 막는 것이 아닙니다 — 아는 채로 정하시면 됩니다.")
    print()


def 빠진것(문장, 적은것):
    """적은 묶임에 **표가 걸리는데 없는 종류**를 돌려준다.

    ⛔ 막지 않는다 — 돌려주는 것은 «할 말»이고, 적을지는 대표님이 정한다.
    ⛔ 표에 없는 묶임을 적은 것은 **틀린 것이 아니다**(표가 모르는 것이 있다). 그건 말하지 않는다.
    """
    fh = []
    dh = 결정에서(문장)
    걸린 = 종류모으기(fh, dh)
    적힌 = [k for k in KINDS if 적은것.startswith(k)]
    없음이라했나 = 적은것.startswith("없음")
    빠진 = [k for k in 걸린 if k not in 적힌]
    if not 빠진:
        return []
    out = []
    if 없음이라했나:
        out.append("      ⛔ **「없음」이라고 적으셨는데 표에는 해야 하는 것이 있습니다.**")
    else:
        out.append("      ⚠️ 표에 걸리는데 **안 적힌 묶임**이 있습니다:")
    for k in 빠진:
        왜 = [f"{h['기능']} — {h['말']}" for h in fh if k in h["묶임"]]
        왜 += [f"「{h['걸린말']}」 — {h['말']}" for h in dh if k in h["묶임"]]
        for w in 왜[:2]:
            out.append(f"        [{k}] {w}")
    out.append("      → 다시 적으실지는 직접 정하십니다. 표가 모르는 것도 있습니다.")
    return out


def main(argv):
    문장 = ""
    if "--결정" in argv:
        i = argv.index("--결정")
        문장 = argv[i + 1] if i + 1 < len(argv) else ""
    if "--빠진것" in argv:
        j = argv.index("--빠진것")
        적은것 = argv[j + 1] if j + 1 < len(argv) else ""
        for l in 빠진것(문장, 적은것):
            print(l)
        return 0
    만드는법, fh = 기능에서()
    dh = 결정에서(문장) if 문장 else []
    if "--json" in argv:
        print(json.dumps({"기능에서": fh, "결정에서": dh,
                          "종류": 종류모으기(fh, dh),
                          "기능들었나": 만드는법 is not None}, ensure_ascii=False))
        return 0
    화면(문장)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
