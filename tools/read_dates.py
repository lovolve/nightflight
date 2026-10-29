#!/usr/bin/env python3
"""규정을 마지막으로 읽은 날 — **세는 곳은 여기 하나다**

설계: nightflight-server design/랜딩-설계-초안.md
      「조종석이 「읽은 날」을 보여야 한다」 ()

⭐⭐ **이 칸이 구독이 살아 있는 이유다.**  — 맞다.
   그래서 파는 것은 「해결」이 아니라 **「그 값이 오늘 맞다고 말할 수 있는 근거」**다.
   클로드는 자기가 **언제** 읽었는지 모르고, ⛔ **모른다고 말하지 않는다.**
   .

⛔ **「못 쟀다」와 「오래되지 않았다」를 섞지 않는다.** 두뇌가 없으면 **날짜를 모르는 것**이고
   그건 「최신이다」가 아니다. 이 저장소가 세 번 값을 치른 병이다.
⛔ **읽은 날이 빈 칸을 「오래되지 않음」으로 세지 않는다** — 그건 **안 읽은 것**이다.
⛔ **문턱을 지어내지 않는다.** 「며칠이면 낡았다」를 애플·구글이 공개하지 않는다.
   날수를 **그대로 보이고** 판단은 사람에게 둔다 (CLAUDE.md: 인용이 없으면 내 판단이라고 쓴다).

🔴 **세는 곳이 둘이면 갈린다 — 실제로 갈려 있었다.**
   `ledger.sh 규정나이` 가 자기 안에서 셌고, 그 안에서 확인 등급이 **늘 빈 문자열**
   (`"conf": ""`)이어서 「⚠️ 요약만 보았습니다」 경고가 **한 번도 안 울렸다.**
   등급은 **공개** 표(`data/관문.tsv` 다섯째 칸)에 있고 거기를 안 읽었다.
   ⭐ 여기서 **번호로 합친다** — 두뇌(읽은 날)와 공개(확인 등급)를 한 줄로 만든다.

⛔ **셈·조건 판정을 여기서 다시 하지 않는다.** 「이 앱에 몇 개 걸리나」는 `ledger.sh 관문`
   한 곳이 센다. 이 칸이 답하는 것은 **「우리가 최신으로 맞춰 두는 값이 얼마나 됐나」**다.
"""
import datetime
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PLUGIN = _HERE.parent
_BRAIN = _PLUGIN.parent / "nightflight-server" / "catalog" / "관문-기준값.tsv"
_PUBLIC = _PLUGIN / "data" / "관문.tsv"


def _today():
    """오늘. ⭐ 시험이 날짜를 옮길 수 있게 환경변수를 먼저 본다
    (기여를 담는 도구와 같은 이음매 — 그게 없어서 변이를 못 잡은 적이 있다)."""
    v = os.environ.get("NF_TODAY")
    if v:
        try:
            return datetime.date.fromisoformat(v)
        except ValueError:
            pass
    return datetime.date.today()


def _rows(p: Path):
    """주석과 빈 줄을 뺀 칸 목록."""
    if not p.is_file():
        return None
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or "\t" not in line:
            continue
        out.append(line.split("\t"))
    return out


def compute(brain_path: Path = None, public_path: Path = None) -> dict:
    """조종석과 터미널이 **같이 쓰는** 하나의 셈.

    ⚠️ 두 길은 **도구 기준**이다. 시험이 바꿔 넣을 수 있게 인자로도 받는다."""
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
    """터미널에 찍는 줄들. ⭐ 조종석과 **같은 셈**에서 나온다."""
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
