#!/usr/bin/env python3
"""기능별 진척 — **기록의 「됐다」·「남은 것」으로 센다.**

🔴 왜 (


이 저장소가 두 번 값을 치른 자리다 — 「**손으로만 적히는 칸을 두지 않는다. 반드시 부풀고,
부푼 기록은 신뢰를 더 빨리 잃는다**」(「피함」·「대신」이 그렇게 죽었다) ·
「**고정 분모를 쓰지 않는다 — 분모는 늘어난다**」.
⭐ 그래서 **이미 출처가 있는 칸**으로만 센다(창업자 결정 2026-10-05):
   **된 것 = 「됐다」 · 남은 것 = 「남은 것」.** 새 칸을 만들지 않는다.


⛔ 확인 안 된 「됐다」를 진척에 **그냥 더하면 그 숫자가 거짓이 된다.**
   경쟁 제품 5/8 이 「완료라고 말해도 실제로는 아무것도 안 됐다」로 걸린 자리다.
→ 그래서 **두 수를 같이 낸다**: 된 것 n 중 **눈으로 확인된 것 k**.


실측(2026-10-05): 주제 칸은 채워져 있는데(어느 앱 43/59 · 다른 앱 70/86)
**기능 이름이 아니다** — 「화면」·「사용성」·「금융연동」이고, 다른 앱은 「4. 개발」처럼
**단계 이름**이 들어와 있었다.
⛔ 「금융연동」이 「돈 받기」인지 「인터넷 없어도 쓰기」인지는 **제품 판단**이다.
⭐ `단계연결` 이 이미 같은 문제를 그렇게 풀었다 — **도구가 추측하지 않고,
   연결되지 않은 동안은 「미연결」이라고 쓴다.**


「놓치면 안 되는 것」은 **이미 있는 것만** 붙인다 —
`data/기능.tsv` 의 「바로 말하는 것」(딸려오는 돈·심사 요건) · 딸려오는 관문 ·
「껍데기로는 안 된다」. ⛔ 없는 기능은 **비어 있다고 말한다.** 채우지 않는다.

쓰기:  feature_progress.py
       feature_progress.py --json
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _root as _root_mod

UNVERIFIED = ("안함", "안봄", "못봄", "못봤", "못했", "못함", "못확인", "미확인")


def _state():
    v = os.environ.get("NF_STATE")
    return Path(v) if v else _root_mod.state_dir()


def _rows(p):
    if not p.exists():
        return []
    return [l.rstrip("\n").split("\t") for l in p.read_text(encoding="utf-8").splitlines()
            if "\t" in l]


def _unverified(how):
    h = (how or "").replace(" ", "")
    return any(t in h for t in UNVERIFIED)


def 기능표():
    out = {}
    p = HERE.parent / "data" / "기능.tsv"
    for c in _rows(p):
        if c[0].startswith("#"):
            continue
        out[c[0]] = {"따라오는것": c[1] if len(c) > 1 else "",
                     "관문": c[2] if len(c) > 2 else "",
                     "껍데기": c[3] if len(c) > 3 else ""}
    return out


def 연결():
    """주제 → (기능, 하위). 대표님이 연결한 것만 있다.

    🔴 2026-10-14: 전엔 **한 층**이었다(주제 → 기능). 그래서 조종석에 찍히는 이름이
      「검사」·「조종석」처럼 **저장소 폴더 이름**이 됐고, 고 했다.
      ⭐ 셋째 칸(하위)을 받는다. 없으면 빈 칸 — 옛 두 칸짜리 줄도 그대로 읽힌다.
    """
    out = {}
    for c in _rows(_state() / "feature-map.tsv"):
        if len(c) >= 2:
            out[c[0]] = (c[1], c[2] if len(c) > 2 else "")
    return out


def 이름표():
    """기록 원문 → (화면 문구, 종류) ( — 화면은 원문 대신 이 문구를 쓴다.
    「안 보이는 작업은 빼고」 — 종류가 «안 보이는 작업»인 줄은 진척에 안 넣는다.
    ⛔ 문구가 없는 줄은 None 이다 — 화면이 «화면 문구 없음» 표지를 단다(원문을 몰래 대신 쓰지 않는다).
    검사: tools/lint_screen_label.py · 적는 자리: bin/ledger.sh 됐다·남은것 의 --화면 --종류
    """
    out = {}
    for c in _rows(_state() / "item-labels.tsv"):
        if c[0].startswith("#") or len(c) < 2:
            continue
        out[c[0]] = (c[1], c[2] if len(c) > 2 and c[2] else None)
    return out


안보임 = "안 보이는 작업"


def _종류(표, what):
    if what.startswith("사용자에게 보이는 변화는 없습니다"):
        return 안보임
    return 표.get(what, (None, None))[1]


def compute():
    led = _rows(_state() / "ledger.tsv")
    표 = 이름표()
    fmap, ftable = 연결(), 기능표()

    끝낸키 = [c[2] for c in led if len(c) > 2 and c[1] == "끝냄"]
    없앤키 = [c[2] for c in led if len(c) > 2 and c[1] == "없어짐"]
    풀림 = [c[2] for c in led if len(c) > 2 and c[1] in ("풀림", "없어짐")]

    feats, 미연결, 주제없음 = {}, {}, {"된것": 0, "남은것": 0}

    def 칸(name):
        return feats.setdefault(name, {
            "기능": name, "된것": 0, "확인된것": 0, "확인칸없음": 0, "남은것": 0, "막힌것": [],
            "방금된것": "", "지금남은것": "", "지금남은것이름표": "",
            "하위": {},
            "놓치면안되는것": ftable.get(name, {}).get("따라오는것", ""),
            "관문": ftable.get(name, {}).get("관문", ""),
            "껍데기": ftable.get(name, {}).get("껍데기", ""),
        })

    def 어디(topic):
        """그 주제가 어느 기능인가. ⛔ 모르면 추측하지 않고 센다."""
        t = (topic or "").strip()
        if not t:
            return None, "주제없음", ""
        if t in fmap:
            기능, 하위 = fmap[t]
            return 기능, "", 하위
        return None, t, ""

    def 하위칸(f, 이름):
        """⛔ 하위 이름이 없으면 만들지 않는다 — 빈 칸을 지어내지 않는다."""
        if not 이름:
            return None
        return f["하위"].setdefault(이름, {"이름": 이름, "된것": 0, "확인된것": 0,
                                          "확인칸없음": 0, "남은것": 0, "줄들": [], "남은줄들": []})

    for c in led:
        kind = c[1] if len(c) > 1 else ""
        what = c[2] if len(c) > 2 else ""
        if kind in ("됐다", "남은것") and _종류(표, what) == 안보임:
            continue
        if kind == "됐다":
            how, topic = (c[3] if len(c) > 3 else ""), (c[5] if len(c) > 5 else "")
            name, miss, 하위 = 어디(topic)
            if name is None:
                if miss == "주제없음":
                    주제없음["된것"] += 1
                else:
                    미연결[miss] = 미연결.get(miss, 0) + 1
                continue
            f = 칸(name)
            f["된것"] += 1
            sub = 하위칸(f, 하위)
            if sub: sub["된것"] += 1
            확인됨 = not _unverified(how)
            if 확인됨:
                f["확인된것"] += 1
                if sub: sub["확인된것"] += 1
            if sub is not None:
                sub["줄들"].append({"무엇": what, "어떻게": (how or ""),
                                    "이름표": 표.get(what, (None, None))[0],
                                    "종류": _종류(표, what),
                                    "상태": "확인함" if 확인됨 else "기계가 못 봄"})
            f["방금된것"] = what
        elif kind == "남은것":
            if any(k in what for k in 없앤키):
                continue
            끝냈나 = any(k in what for k in 끝낸키)
            topic = c[5] if len(c) > 5 else ""
            name, miss, 하위 = 어디(topic)
            if name is None:
                if miss == "주제없음":
                    주제없음["된것" if 끝냈나 else "남은것"] += 1
                else:
                    미연결[miss] = 미연결.get(miss, 0) + 1
                continue
            f = 칸(name)
            sub = 하위칸(f, 하위)
            if 끝냈나:
                f["된것"] += 1
                f["확인칸없음"] += 1
                if sub: sub["된것"] += 1; sub["확인칸없음"] += 1
                f["방금된것"] = f["방금된것"] or what
            else:
                f["남은것"] += 1
                if sub: sub["남은것"] += 1
                f["지금남은것"] = what
                f["지금남은것이름표"] = 표.get(what, (None, None))[0]
                if sub is not None:
                    sub["남은줄들"].append({"무엇": what, "이름표": 표.get(what, (None, None))[0],
                                          "종류": _종류(표, what)})
        elif kind == "못함":
            if any(k in what for k in 풀림):
                continue
            주제없음.setdefault("막힌것", 0)
            주제없음["막힌것"] += 1

    for f in feats.values():
        분모 = f["된것"] + f["남은것"]
        f["분모"] = 분모
        for sub in f["하위"].values():
            sub["분모"] = sub["된것"] + sub["남은것"]
            sub["진척"] = round(sub["된것"] * 100 / sub["분모"]) if sub["분모"] else None
        f["하위"] = sorted(f["하위"].values(), key=lambda x: -x["분모"])
        f["진척"] = round(f["된것"] * 100 / 분모) if 분모 else None

    return {"기능들": sorted(feats.values(), key=lambda x: -x["분모"]),
            "미연결주제": 미연결, "주제없음": 주제없음}


def 화면(r):
    fs = r["기능들"]
    print()
    print("── 무엇이 얼마나 됐나 ───────────────────────────")
    if not fs:
        print("   아직 보여드릴 것이 없습니다.")
        print("   ⚠️ 이건 「아무것도 안 됐다」가 아니라 **어느 일이 어느 기능인지 아직")
        print("      연결이 안 됐다**는 뜻입니다.")
        _꼬리(r)
        return
    for f in fs:
        print()
        if f["남은것"]:
            print(f"   {f['기능']}  —  적어 둔 {f['분모']}가지 중 **{f['된것']}** 했습니다  ({f['진척']}%)")
        else:
            print(f"   {f['기능']}  —  적어 둔 {f['분모']}가지를 **다 했습니다**")
            print("        ⚠️ 「이 기능이 끝났다」는 뜻이 **아닙니다** — 적어 둔 것을 다 했다는 뜻이고,")
            print("           만들다 보면 또 생깁니다. 그때 이 숫자는 내려갑니다")
        if f["된것"] and f["확인된것"] < f["된것"]:
            print(f"        ⚠️ 그중 **눈으로 확인된 것은 {f['확인된것']}건**입니다 — 나머지는 됐다고만 적힌 것입니다")
            if f["확인칸없음"]:
                print(f"           그 {f['확인칸없음']}건은 **확인했다고 적을 칸이 없는** 종류입니다 — 모르는 것입니다")
        elif f["된것"]:
            print(f"        ✅ {f['된것']}건 다 확인됐습니다")
        for sub in f["하위"]:
            if sub["남은것"]:
                print(f"        └ {sub['이름']} — {sub['분모']}가지 중 {sub['된것']} ({sub['진척']}%)")
            else:
                print(f"        └ {sub['이름']} — 적어 둔 {sub['분모']}가지를 다 했습니다")
            if sub["된것"] and sub["확인된것"] < sub["된것"]:
                print(f"           그중 눈으로 확인된 것은 {sub['확인된것']}건입니다")
        if f["방금된것"]:
            print(f"        방금 된 것   {f['방금된것']}")
        if f["지금남은것"]:
            print(f"        지금 남은 것 {f['지금남은것']}")
        if f["놓치면안되는것"]:
            print(f"        🔴 놓치면 안 되는 것 — {f['놓치면안되는것']}")
        if f["껍데기"] == "안됨":
            print("        ⛔ 웹사이트를 그대로 앱에 넣는 방식으로는 **이 기능을 못 붙입니다**")
        elif f["껍데기"] == "어려움":
            print("        ⚠️ 웹사이트를 그대로 앱에 넣는 방식이면 이 기능이 **어렵습니다**")
        if not f["놓치면안되는것"]:
            print("        ⚠️ 이 기능에서 놓치기 쉬운 것은 **아직 모아 둔 것이 없습니다**")
    _꼬리(r)


def _꼬리(r):
    n, b = r["미연결주제"], r["주제없음"]
    print()
    if n:
        print(f"   ⚠️ **어느 기능인지 아직 안 정한 것이 {sum(n.values())}건** 있습니다:")
        for k, v in sorted(n.items(), key=lambda x: -x[1])[:8]:
            print(f"        「{k}」 {v}건")
        print("      이 말들이 어느 기능에 들어가는지 말씀해 주시면 그때부터 같이 봅니다.")
    if b["된것"] or b["남은것"]:
        print(f"   ⚠️ 아무 묶음도 없는 것이 {b['된것'] + b['남은것']}건 있습니다 — 이건 제가 적을 때 빠뜨린 것입니다.")
    if b.get("막힌것"):
        print(f"   ⚠️ 제가 못 해서 손이 가셔야 하는 것이 {b['막힌것']}건 있습니다(어느 기능인지는 안 적힙니다).")
    print()
    print("   ⚠️ **이 숫자가 세는 것은 «제가 적어 둔 일»입니다.** 「이 기능 전체」가 아닙니다 —")
    print("      만들다 보면 할 일이 늘어서 분모가 커지고, 그러면 비율이 **내려갑니다.**")
    print("      내려간 것이 나빠진 것은 아닙니다.")
    print()


def main(argv):
    r = compute()
    if "--json" in argv:
        print(json.dumps(r, ensure_ascii=False))
        return 0
    화면(r)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
