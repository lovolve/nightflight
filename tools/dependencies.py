#!/usr/bin/env python3
"""영향 — 「이걸 고치면 무엇도 봐야 하나」"""
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

KIND = {
    "같은것을쓴다": ("둘이 같은 것을 들고 있습니다", "한쪽을 바꾸면 다른 쪽이 깨집니다"),
    "순서가있다":   ("이것이 먼저 돼야 저것이 됩니다", "앞을 바꾸면 뒤가 못 돕니다"),
    "같은화면":     ("한 화면에 같이 있습니다", "모양을 바꾸면 다른 쪽 자리가 밀립니다"),
}
STOP_KINDS = ("같은것을쓴다",)

SOURCE = {
    "깨졌다":  "⭐ 실제로 고쳤더니 깨졌습니다 — 재어 본 것입니다",
    "리서치":  "비슷한 앱들에서 둘이 같이 온다고 확인했습니다",
    "코드":    "설치 전부터 있던 코드에서 읽었습니다 — 실제로 고쳐서 깨지는지는 아직 안 재었습니다",
    "표준":    "적어 둔 표준 방식이 그 둘을 함께 요구합니다",
    "내판단":  "🔴 출처가 없습니다 — 아직 확인된 영향이 아닙니다",
}
CONFIRMED = ("깨졌다", "리서치", "표준", "코드")


def 설계표기능(ledger: Path = None) -> set:
    p = Path(ledger) if ledger else _root.ledger()
    t = p.parent / "plan.tsv"
    if t.is_file():
        out = set()
        for line in t.read_text(encoding="utf-8").splitlines():
            c = line.split("\t")
            if len(c) > 1 and not line.startswith("#") and c[1].strip():
                out.add(c[1].strip())
        return out
    j = p.parent / "board" / "features.json"
    if not j.is_file():
        return set()
    try:
        import json
        d = json.loads(j.read_text(encoding="utf-8"))
    except Exception:
        raise
    out = set()
    for _, pp in ((d.get("설계표") or {}).get("단계") or {}).items():
        for f in (pp.get("기능들") or []):
            if (f.get("기능") or "").strip():
                out.add(f["기능"].strip())
    return out


def 쓸수있는이름(ledger: Path = None) -> set:
    return 설계표기능(ledger) | 주제들(ledger)


def 주제들(ledger: Path = None) -> set:
    p = Path(ledger) if ledger else _root.ledger()
    if not p.is_file():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        c = line.rstrip("\n").split("\t")
        if len(c) > 5 and c[5].strip():
            out.add(c[5].strip())
    return out


import _labels as _lb


def 연결된기능(ledger: Path = None) -> dict:
    p = Path(ledger) if ledger else _root.ledger()
    out = {}
    if not p.is_file():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        c = line.rstrip("\n").split("\t")
        if len(c) > 5 and c[1] == "영향" and c[3].strip() in CONFIRMED:
            for x in (c[2].strip(), c[5].strip()):
                if x:
                    out[x] = "연결"
        elif len(c) > 3 and c[1] == "독립" and c[2].strip() and c[3].strip():
            out.setdefault(c[2].strip(), "독립")
    return out


def compute(ledger: Path = None) -> dict:
    p = Path(ledger) if ledger else _root.ledger()
    _표 = _lb.항목표(p.parent)
    if not p.is_file():
        return {"못쟀다": True, "고치는쪽별": {}, "확인된것": 0,
                "확인안된것": 0, "모른낱말": []}

    per, ok_n, unk_n, badword = {}, 0, 0, []
    for line in p.read_text(encoding="utf-8").splitlines():
        c = line.rstrip("\n").split("\t")
        if len(c) < 6 or c[1] != "영향":
            continue
        d, other, src, pre, mine = c[0], c[2], c[3].strip(), c[4].strip(), c[5].strip()
        kind, _, note = pre.partition(":")
        kind = kind.strip()
        if kind not in KIND:
            badword.append({"고치는쪽": mine, "낱말": kind, "같이볼쪽": other})
            kind = ""
        if src not in SOURCE:
            badword.append({"고치는쪽": mine, "낱말": src, "같이볼쪽": other})
            src = ""
        row = {"같이볼쪽": other, "종류": kind, "영향받는말": note.strip(), "출처": src,
               "날": d, "뜻": KIND.get(kind, ("", ""))[0],
               "할일": KIND.get(kind, ("", ""))[1],
               "출처뜻": SOURCE.get(src, "")}
        row["이름표"] = _표.get(note.strip(), (None, None))[0]
        row["구분"] = _lb.종류(_표, note.strip())
        per.setdefault(mine, []).append(row)
        if src in CONFIRMED:
            ok_n += 1
        else:
            unk_n += 1

    for k in per:
        per[k].sort(key=lambda r: (0 if r["종류"] in STOP_KINDS else 1, r["날"]))

    return {"못쟀다": False, "고치는쪽별": (_uw.바꾼다(per) if _uw else per), "확인된것": ok_n,
            "확인안된것": unk_n, "모른낱말": badword, "따져본기능": 연결된기능(p)}


def 고치기전(topic: str, ledger: Path = None) -> dict:
    d = compute(ledger)
    _t = (topic or "").strip()
    if _uw: _t = _uw.사용자말(_t)
    rows = [] if d["못쟀다"] else d["고치는쪽별"].get(_t, [])
    stop = [r for r in rows if r["종류"] in STOP_KINDS]
    tell = [r for r in rows if r["종류"] not in STOP_KINDS]
    if stop:
        verdict = "멈춤"
    elif tell:
        verdict = "알림"
    else:
        verdict = "안적힘"
    return {"판정": verdict, "멈출것": stop, "알릴것": tell,
            "못쟀다": d["못쟀다"], "주제": (topic or "").strip()}


def 고치기전_사람말(r: dict) -> list:
    out = []
    if r["판정"] == "안적힘":
        out.append(f"  ⚠️ 「{r['주제']}」에 영향받는 것이 **지도에 안 적혀 있습니다.**")
        out.append("     ⛔ 이건 **「따로 떨어져 있다」는 뜻이 아닙니다** — 아직 안 적었다는 뜻입니다.")
        return out
    if r["멈출것"]:
        out.append("  ⛔ **고치기 전에 멈춥니다** — 같이 깨질 수 있는 것이 있습니다.")
        for x in r["멈출것"]:
            out.append(f"     · {x['같이볼쪽']} — {x['할일']}")
            if x["영향받는말"]:
                out.append(f"       무엇을 같이 쓰나: {x['영향받는말']}")
            out.append(f"       {x['출처뜻']}  ({x['날']})")
    if r["알릴것"]:
        out.append("  ⚠️ 같이 봐야 하는 것 (멈추지는 않습니다):")
        for x in r["알릴것"]:
            out.append(f"     · {x['같이볼쪽']} — {x['할일']}")
    out.append("     ⚠️ 지도에 적힌 것만 보입니다 — **이게 전부라는 뜻이 아닙니다.**")
    return out


def 사람말(d: dict) -> list:
    out = []
    if d["못쟀다"]:
        out.append("  아직 기록이 없습니다 — 적어 둔 영향이 없습니다.")
        out.append("  (이건 **「영향받는 것이 없다」가 아니라 「아직 안 적었다」**입니다.)")
        return out
    if not d["고치는쪽별"]:
        out.append("  적어 둔 영향이 없습니다.")
        out.append("  (이건 **「영향받는 것이 없다」가 아니라 「아직 안 적었다」**입니다.)")
        out.append("  ⛔ **「기능들이 서로 따로 있다」는 뜻이 아닙니다.**")
        out.append("  ⭐ 지도는 **자랍니다** — 리서치에서, 표준에서, 그리고 깨질 때 들어옵니다.")
        return out
    for mine, rows in sorted(d["고치는쪽별"].items()):
        out.append(f"  ▸ 「{mine}」을 고치면")
        for r in rows:
            head = "⛔" if r["종류"] in STOP_KINDS else ("⚠️" if r["종류"] else "🔴")
            out.append(f"   {head} {r['같이볼쪽']} 도 봐야 합니다")
            if r["종류"]:
                out.append(f"       왜: {r['뜻']} → {r['할일']}")
                if r["영향받는말"]:
                    out.append(f"       무엇을: {r['영향받는말']}")
            else:
                out.append("       🔴 종류가 비었거나 모르는 말입니다 — **할 일을 알 수 없습니다**")
            out.append(f"       {r['출처뜻'] or '🔴 출처를 읽을 수 없습니다'}  ({r['날']})")
    out.append("")
    out.append(f"  출처 있는 영향 {d['확인된것']}가지(깨졌다 · 리서치 · 표준 · 코드) · "
               f"🔴 아직 확인 안 된 영향 {d['확인안된것']}가지")
    if d["모른낱말"]:
        out.append(f"  🔴 읽을 수 없는 칸이 있는 것 {len(d['모른낱말'])}가지")
    return out


if __name__ == "__main__":
    import json
    if "--고치기전" in sys.argv:
        i = sys.argv.index("--고치기전")
        r = 고치기전(sys.argv[i + 1] if len(sys.argv) > i + 1 else "")
        if "--json" in sys.argv:
            print(json.dumps(r, ensure_ascii=False))
        else:
            for line in 고치기전_사람말(r):
                print(line)
        sys.exit(1 if r["판정"] == "멈춤" else 0)
    d = compute()
    if "--json" in sys.argv:
        print(json.dumps(d, ensure_ascii=False, indent=1))
    else:
        print()
        print("── 이걸 고치면 무엇도 봐야 하나 ─────────────────")
        print()
        for line in 사람말(d):
            print(line)
        print()
