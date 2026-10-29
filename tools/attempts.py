#!/usr/bin/env python3
"""시도 — 「이걸 해 봤고 안 됐다 · 왜 안 됐나」

설계: nightflight-server design/들고-있는-것.md ⓑ
      ()

⭐⭐ **왜**: 새 대화는 **전에 뭘 해 봤고 안 됐는지 모른다** → **같은 막힌 길을 다시 간다.**
   비개발자는 그게 막힌 길인지 모르고, **매번 처음부터** 간다.

🔴 **실측 구멍이었다**(2026-10-10): `ledger.sh` 전체에 `시도` 가 **칸 0개 · 언급 0번**.


| | 뜻 | 다음 세션이 할 일 |
|---|---|---|
| **막혔다** | 그 방법으로는 **안 된다** — 도구·플랫폼·법이 막는다 | ⛔ **다시 가지 않는다** |
| **못했다** | **우리가** 못 했다 — 시간·지식·설정 | ⭐ **무엇이 바뀌면** 다시 갈 수 있다 |

⛔ **둘을 섞으면 이 칸이 해롭다.** 전부 「막혔다」로 읽으면 **포기가 쌓이고**,
전부 「못했다」로 읽으면 **같은 막힌 길을 또 간다.** 그래서 **판정을 강제한다.**

⛔ **「못했다」에는 「무엇이 바뀌면 다시 가나」가 필요하다** — 없으면 영원히 「나중에」다.
   (`결정` 에 **전제**를 강제한 것과 같은 이유다.)


| | |
|---|---|
| `못함` | **지금** 못 하고 있다 — 대표님이 풀어 주셔야 한다(현재 상태) |
| `시도` | **해 봤고** 안 됐다 — 다시 가지 말라는 **이력** |
| `되돌림` | **결정**을 뒤집었다 |
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _root

try:
    import importlib.util as _ilu, os as _os
    _p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "user_words.py")
    _s = _ilu.spec_from_file_location("_uw", _p)
    _uw = _ilu.module_from_spec(_s); _s.loader.exec_module(_uw)
except Exception:
    _uw = None

VERDICT = {
    "막혔다": "그 방법으로는 안 됩니다 — 다시 가지 마십시오",
    "못했다": "우리가 못 했습니다 — 아래가 바뀌면 다시 갈 수 있습니다",
}


import _labels as _lb


def compute(ledger: Path = None) -> dict:
    """ledger.sh 와 조종석이 **같이 쓰는** 하나의 셈."""
    p = Path(ledger) if ledger else _root.ledger()
    _표 = _lb.항목표(p.parent)
    if not p.is_file():
        return {"못쟀다": True, "기능별": {}, "막힌것": 0, "못한것": 0, "모른낱말": []}

    gone = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        c = line.rstrip("\n").split("\t")
        if len(c) >= 4 and c[1] == "없어짐":
            gone[c[2]] = c[3]

    def _치움(what):
        for k, why in gone.items():
            if k and k in what:
                return why
        return ""

    per, blocked, failed, badword = {}, 0, 0, []
    for line in p.read_text(encoding="utf-8").splitlines():
        c = line.rstrip("\n").split("\t")
        if len(c) < 5 or c[1] != "시도":
            continue
        d, what, why, pre = c[0], c[2], c[3], c[4].strip()
        topic = (c[5].strip() if len(c) > 5 else "") or "그 밖에"
        verdict, _, detail = pre.partition(":")
        verdict = verdict.strip()
        if verdict not in VERDICT:
            badword.append({"기능": topic, "낱말": verdict, "무엇": what})
            verdict = ""
        치움 = _치움(what)
        row = {"무엇": what, "왜": why, "판정": verdict,
               "자세히": detail.strip(), "날": d, "뜻": VERDICT.get(verdict, ""),
               "치움": 치움}
        row["이름표"] = _표.get(what, (None, None))[0]
        row["구분"] = _lb.종류(_표, what)
        per.setdefault(topic, []).append(row)
        if 치움:
            pass
        elif verdict == "막혔다":
            blocked += 1
        elif verdict == "못했다":
            failed += 1

    for k in per:
        per[k].sort(key=lambda r: (2 if r["치움"] else (0 if r["판정"] == "막혔다" else 1),
                                   r["날"]))

    return {"못쟀다": False, "기능별": (_uw.바꾼다(per) if _uw else per), "막힌것": blocked,
            "못한것": failed, "모른낱말": badword}


def 막힌길(topic: str, ledger: Path = None) -> list:
    """⭐⭐ **이 기능에서 이미 막힌 길.** `표준`·`결정` 을 적을 때 **먼저 보여 준다** —
    그것이 「같은 막힌 길을 다시 간다」를 막는 자리다.

    ⛔ 막지 않는다. 표가 모르는 것도 있고, 결정은 대표님 것이다. **말하고 지나간다.**
    """
    d = compute(ledger)
    if d["못쟀다"] or not topic:
        return []
    rows = d["기능별"].get(topic.strip(), [])
    return [r for r in rows if r["판정"] == "막혔다" and not r["치움"]]


def 사람말(d: dict) -> list:
    out = []
    if d["못쟀다"]:
        out.append("  아직 기록이 없습니다 — 적어 둔 시도가 없습니다.")
        out.append("  (이건 「막힌 길이 없다」가 아니라 **「아직 안 적었다」**입니다.)")
        return out
    if not d["기능별"]:
        out.append("  적어 둔 시도가 없습니다.")
        out.append("  ⚠️ **해 봤는데 안 된 것**을 적어 두지 않으면,")
        out.append("     다음에 **같은 막힌 길을 또 갑니다**.")
        return out
    for feat, rows in sorted(d["기능별"].items()):
        out.append(f"  ▸ {feat}")
        for r in rows:
            if r["치움"]:
                out.append(f"   ✔ {r['무엇']}  ← 치웠습니다")
                out.append(f"       왜 치웠나: {r['치움']}")
                continue
            head = "⛔" if r["판정"] == "막혔다" else ("⭐" if r["판정"] == "못했다" else "🔴")
            out.append(f"   {head} {r['무엇']}")
            out.append(f"       안 된 이유: {r['왜']}  ({r['날']})")
            if r["판정"] == "막혔다":
                out.append(f"       막는 것: {r['자세히'] or '— (안 적혀 있습니다)'}")
            elif r["판정"] == "못했다":
                out.append(f"       이것이 바뀌면 다시 갑니다: {r['자세히']}")
            else:
                out.append("       🔴 판정이 비었거나 모르는 말입니다 — "
                           "**다시 가도 되는지 알 수 없습니다**")
    out.append("")
    out.append(f"  ⛔ 다시 가지 말 것 {d['막힌것']}가지 · "
               f"⭐ 조건이 바뀌면 갈 수 있는 것 {d['못한것']}가지")
    if d["모른낱말"]:
        out.append(f"  🔴 판정을 읽을 수 없는 것 {len(d['모른낱말'])}가지 — "
                   f"쓸 수 있는 말: {' · '.join(VERDICT)}")
    return out


if __name__ == "__main__":
    import json
    r = compute()
    if "--json" in sys.argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    elif "--막힌길" in sys.argv:
        i = sys.argv.index("--막힌길")
        for x in 막힌길(sys.argv[i + 1] if len(sys.argv) > i + 1 else ""):
            print(f"  ⛔ 전에 해 봤고 막혔습니다: {x['무엇']}")
            print(f"     안 된 이유: {x['왜']}  ({x['날']})")
            print(f"     막는 것: {x['자세히'] or '— (안 적혀 있습니다)'}")
    else:
        print()
        print("── 해 봤는데 안 된 것 ───────────────────────────")
        print()
        for line in 사람말(r):
            print(line)
        print()
        print("  ⚠️ 저희가 적어 둔 것만 보입니다 — 「이것 말고는 다 된다」가 아닙니다.")
        print()
