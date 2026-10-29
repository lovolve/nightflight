#!/usr/bin/env python3
"""표준 — 「이 기능은 어떤 방식이 표준인가 · 출처는 무엇인가」

설계: nightflight-server design/들고-있는-것.md ⓐ
      ()

⭐⭐ **왜 이 칸이 있나.** 
   그리고 2026-10-10: 「**새 대화가 열리면 표준이 무엇이었는지를 모른다**」 —
   그래서 **같은 기능을 다른 방식으로 또 짠다.** 그것이 삽질의 큰 이유 중 하나다.

🔴 **실측으로 드러난 구멍이다**(2026-10-10): `bin/ledger.sh` 전체에 `표준` 이라는
   낱말이 **칸 0개 · 언급 0번**이었다. ⛔ **파는 것에 적어 두고 적을 자리가 없었다.**


4-개발 처방이 이미 못 박아 둔 것이다 — 「**「표준이다」를 내 기억으로 판정하지 않는다.**
출처는 설계 단계가 적어 둔 것이고, 없으면 **그 자리에서 다시 리서치한다**」.
⭐ 그래서 확인 칸은 **통제된 네 낱말**이고, 그중 하나는 **「출처가 없다」를 뜻한다.**
⛔ 「내기억」을 **막지 않는다** — 막으면 **거짓 출처를 적게** 된다. 대신 **따로 세고
   화면에서 「아직 표준이 아니다」라고 말한다**(「됐다 ≠ 확인했다」와 같은 꼴).
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

CONFIRM = {
    "돌려봄":   "우리가 그렇게 만들어 돌려 봤습니다",
    "코드":     "설치 전부터 이 앱이 쓰던 방식입니다 — 표준인지는 아직 안 봤습니다",
    "공식문서": "공식 문서에서 읽었습니다",
    "남이한것": "이미 돌아가는 앱·저장소에서 확인했습니다",
    "내기억":   "🔴 출처가 없습니다 — 아직 표준이라고 부를 수 없습니다",
}
SOURCED = ("돌려봄", "공식문서", "남이한것")


import _labels as _lb


def compute(ledger: Path = None) -> dict:
    """ledger.sh 와 조종석이 **같이 쓰는** 하나의 셈.

    ⛔ 세는 곳을 둘로 만들지 않는다 — 이 저장소가 「확인했다」 판정으로 값을 치렀다.
    """
    p = Path(ledger) if ledger else _root.ledger()
    _표 = _lb.항목표(p.parent)
    if not p.is_file():
        return {"못쟀다": True, "기능별": {}, "출처있음": 0, "출처없음": 0, "모른낱말": []}

    per, sourced, unsourced, badword = {}, 0, 0, []
    for line in p.read_text(encoding="utf-8").splitlines():
        c = line.rstrip("\n").split("\t")
        if len(c) < 4 or c[1] != "표준":
            continue
        d, what, why = c[0], c[2], c[3]
        conf = c[4].strip() if len(c) > 4 else ""
        topic = (c[5].strip() if len(c) > 5 else "") or "그 밖에"
        if conf not in CONFIRM:
            badword.append({"기능": topic, "낱말": conf, "무엇": what})
            conf = ""
        row = {"무엇": what, "출처": why, "확인": conf, "날": d,
               "뜻": CONFIRM.get(conf, "")}
        row["이름표"] = _표.get(what, (None, None))[0]
        row["구분"] = _lb.종류(_표, what)
        per.setdefault(topic, []).append(row)
        if conf in SOURCED:
            sourced += 1
        else:
            unsourced += 1

    for k in per:
        per[k].sort(key=lambda r: r["날"], reverse=True)

    return {"못쟀다": False, "기능별": (_uw.바꾼다(per) if _uw else per), "출처있음": sourced,
            "출처없음": unsourced, "모른낱말": badword}


def 사람말(d: dict) -> list:
    out = []
    if d["못쟀다"]:
        out.append("  아직 기록이 없습니다 — 적어 둔 표준이 없습니다.")
        out.append("  (이건 「표준이 없다」가 아니라 **「아직 안 적었다」**입니다.)")
        return out
    if not d["기능별"]:
        out.append("  적어 둔 표준이 없습니다.")
        out.append("  ⚠️ 기능마다 **어떤 방식이 표준인지**를 적어 두지 않으면,")
        out.append("     다음에 같은 기능을 **다른 방식으로 또 만듭니다**.")
        return out
    for feat, rows in sorted(d["기능별"].items()):
        out.append(f"  ▸ {feat}")
        for r in rows:
            out.append(f"   · {r['무엇']}")
            if r["확인"] in SOURCED:
                out.append(f"       출처: {r['출처']}  ({CONFIRM[r['확인']]}, {r['날']})")
            elif r["확인"] == "내기억":
                out.append(f"       {CONFIRM['내기억']}")
                out.append(f"          적힌 것: {r['출처']}  ({r['날']})")
            else:
                out.append(f"       🔴 확인 칸이 비었거나 모르는 말입니다 — 「{r['출처']}」")
    out.append("")
    out.append(f"  출처가 있는 것 {d['출처있음']}가지 · "
               f"🔴 아직 표준이라 부를 수 없는 것 {d['출처없음']}가지")
    if d["모른낱말"]:
        out.append(f"  ⚠️ 확인 칸에 모르는 말이 쓰인 것 {len(d['모른낱말'])}가지 — "
                   f"쓸 수 있는 말: {' · '.join(CONFIRM)}")
    return out


if __name__ == "__main__":
    import json
    r = compute()
    if "--json" in sys.argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print()
        print("── 이 앱의 표준 방식 ─────────────────────────────")
        print()
        for line in 사람말(r):
            print(line)
        print()
        print("  ⚠️ 저희가 적어 둔 것만 보입니다 — 「이것이 업계 표준 전부」가 아닙니다.")
        print()
