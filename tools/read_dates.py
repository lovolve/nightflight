#!/usr/bin/env python3
"""규정을 마지막으로 읽은 날 — **세는 곳은 여기 하나다**"""
import datetime
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PLUGIN = _HERE.parent
import sys as _s; _s.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import gate_thresholds as _기준값
    _BRAIN = _기준값.자리()
except ImportError:
    _BRAIN = _PLUGIN.parent / "nightflight-server" / "catalog" / "관문-기준값.tsv"
_PUBLIC = _PLUGIN / "data" / "gates.tsv"


def _today():
    v = os.environ.get("NF_TODAY")
    if v:
        try:
            return datetime.date.fromisoformat(v)
        except ValueError:
            pass
    return datetime.date.today()


def _rows(p: Path):
    if not p.is_file():
        return None
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or "\t" not in line:
            continue
        out.append(line.split("\t"))
    return out


def compute(brain_path: Path = None, public_path: Path = None) -> dict:
    bp = Path(brain_path) if brain_path else _BRAIN
    pp = Path(public_path) if public_path else _PUBLIC
    brain = _rows(bp)
    today = _today()

    if brain is None:
        return {"못쟀다": True, "줄들": [], "안읽은것": [], "가장오래된": None,
                "요약만": 0, "센날": today.isoformat()}

    pub = _rows(pp) or []
    grade = {c[0].strip(): (c[4].strip() if len(c) > 4 else "")
             for c in pub if c and c[0].strip().isdigit()}

    dated, never = [], []
    for c in brain:
        if len(c) < 4:
            continue
        no, name, read = c[0].strip(), c[1].strip(), c[3].strip()
        g = grade.get(no, "")
        try:
            age = (today - datetime.date.fromisoformat(read)).days
        except ValueError:
            never.append({"번호": no, "이름": name, "확인": g})
            continue
        dated.append({"번호": no, "이름": name, "읽은날": read, "며칠전": age, "확인": g})

    have = {c[0].strip() for c in brain if c and c[0].strip()}
    for c in pub:
        if c and c[0].strip().isdigit() and c[0].strip() not in have and len(c) > 1:
            never.append({"번호": c[0].strip(), "이름": c[1].strip(), "확인": grade.get(c[0].strip(), "")})

    dated.sort(key=lambda x: -x["며칠전"])
    return {
        "못쟀다": False,
        "줄들": dated,
        "안읽은것": never,
        "가장오래된": dated[0]["며칠전"] if dated else None,
        "요약만": sum(1 for x in dated if x["확인"] == "요약"),
        "센날": today.isoformat(),
    }


def 사람말(d: dict) -> list:
    out = []
    if d["못쟀다"]:
        out.append("  ⚠️ 규정을 읽은 날은 **야간비행이 내려줍니다** — 여기서는 **재지 못했습니다.**")
        out.append("     (이건 「오래되지 않았다」가 아니라 **「못 쟀다」**입니다.)")
        return out
    if d["줄들"]:
        out.append(f"  가장 오래된 것이 **{d['가장오래된']}일 전**입니다.")
        out.append("")
        for x in d["줄들"]:
            mark = "⚠️ " if x["확인"] == "요약" else "   "
            tail = "  ⚠️ 저희는 요약만 보았습니다" if x["확인"] == "요약" else ""
            out.append(f"  {mark}{x['이름']} — {x['읽은날']} ({x['며칠전']}일 전){tail}")
    else:
        out.append("  읽은 날이 적힌 것이 없습니다.")
    if d["안읽은것"]:
        out.append("")
        out.append(f"  🔴 아직 읽은 적이 없는 것 {len(d['안읽은것'])}개 — "
                   "「오래되지 않음」이 아니라 **안 읽었음**입니다")
        for x in d["안읽은것"]:
            out.append(f"     · {x['이름']}")
    return out


if __name__ == "__main__":
    import json
    d = compute()
    if "--json" in sys.argv:
        print(json.dumps(d, ensure_ascii=False, indent=1))
    else:
        print()
        print("── 규정을 마지막으로 읽은 날 ─────────────────────")
        print()
        for line in 사람말(d):
            print(line)
        print()
