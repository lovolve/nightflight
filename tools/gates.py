#!/usr/bin/env python3
"""관문 — 「몇 개 걸리나 · 며칠인가」"""
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PLUGIN = _HERE.parent
_GATES = _PLUGIN / "data" / "관문.tsv"


def _할일표():
    out = {}
    try:
        for l in (_PLUGIN / "data" / "관문할일.tsv").read_text(encoding="utf-8").splitlines():
            c = l.split("\t")
            if l.startswith("#") or len(c) < 2:
                continue
            주소 = c[2].strip() if len(c) > 2 else ""
            out[c[0]] = (c[1].strip(), 주소 if 주소.startswith("https://") else "")
    except OSError:
        pass
    return out


할일표 = _할일표()
import sys as _s; _s.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import 관문기준값 as _기준값
    _BRAIN = _기준값.자리()
except ImportError:
    _BRAIN = _PLUGIN.parent / "nightflight-server" / "catalog" / "관문-기준값.tsv"


쌓이는축 = {"이미한것"}



def _이미한것값():
    f = Path(__file__).resolve().parent.parent / "data" / "이미한것.tsv"
    if not f.is_file():
        return ()
    줄 = []
    for l in f.read_text(encoding="utf-8").splitlines():
        if l.startswith("#") or "\t" not in l:
            continue
        c = l.split("\t")
        if len(c) >= 2 and c[0].strip():
            줄.append((c[0].strip(), c[1].strip()))
    return tuple(줄)


이미한것값 = _이미한것값()


def _load(axes, when, path, kind_col, ax_col, val_col, day_col):
    if not path or not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        c = line.rstrip("\n").split("\t")
        if len(c) <= max(ax_col, val_col):
            continue
        if kind_col is not None and (len(c) <= kind_col or c[kind_col] != "앱설정"):
            continue
        축, 값 = c[ax_col], c[val_col]
        if 축 in 쌓이는축 and 값.strip() == "없음":
            pass
        elif 축 in 쌓이는축 and axes.get(축) and axes[축] != "없음":
            있던 = [x.strip() for x in axes[축].split("·") if x.strip()]
            새것 = [x.strip() for x in 값.split("·") if x.strip()]
            값 = "·".join(있던 + [x for x in 새것 if x not in 있던])
        axes[축] = 값
        when[축] = c[day_col]


def _judger(axes, asked):
    def vals(ax):
        return [x.strip() for x in axes.get(ax, "").split("·") if x.strip()]

    def one(cond):
        m = re.match(r"^\s*([가-힣]+)\s*(has|!=|>=|<=|=|>|<)\s*(.+?)\s*$", cond)
        if not m:
            return "모름"
        ax, op, want = m.group(1), m.group(2), m.group(3)
        if ax not in asked:
            return "모름"
        got = vals(ax)
        if got == ["모름"] or not got:
            return "모름"
        if op in ("has", "="):
            return "걸림" if want in got else "안걸림"
        if op == "!=":
            return "걸림" if want not in got else "안걸림"
        g = got[0]
        if g.replace(" ", "") in ("아직없음", "아직안만듦", "없음"):
            import datetime as _dt
            g = _dt.date.today().isoformat()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", g):
            return "모름"
        if op == ">":  return "걸림" if g > want else "안걸림"
        if op == "<":  return "걸림" if g < want else "안걸림"
        if op == ">=": return "걸림" if g >= want else "안걸림"
        if op == "<=": return "걸림" if g <= want else "안걸림"
        return "모름"

    def judge_or(clause):
        parts = [p for p in clause.split("|") if p.strip()]
        if len(parts) == 1:
            return one(clause)
        sub = [one(p) for p in parts]
        if "걸림" in sub:
            return "걸림"
        if all(x == "안걸림" for x in sub):
            return "안걸림"
        return "모름"

    def judge(expr):
        outs = [judge_or(c) for c in expr.split("&")]
        if "안걸림" in outs:
            return "안걸림"
        if "모름" in outs:
            return "모름"
        return "걸림"

    return judge


범위밖 = "사업자 신고 · 개인정보 보호법 · 게임 등급분류처럼 나라마다 다른 법은 이 도구가 다루지 않습니다(스토어의 연령 등급 설문은 AI가 대신 넣습니다)"


def compute(state=None, person=None, gates=None, brain=None, 플랫폼필요=True) -> dict:
    gp = Path(gates) if gates else _GATES
    if not gp.is_file():
        return {"못쟀다": "판정표없음", "총": 0, "걸림": [], "안걸림": 0,
                "모름": [], "두뇌있음": False,
                "이미한것": [], "이미한것고를것": [list(x) for x in 이미한것값], "범위밖": 범위밖}

    axes, when = {}, {}
    _load(axes, when, state, 1, 2, 3, 0)
    _load(axes, when, person, None, 1, 2, 0)
    asked = set(axes)
    if not asked or (플랫폼필요 and "플랫폼" not in asked):
        return {"못쟀다": "안물어봤음", "총": 0, "걸림": [], "안걸림": 0,
                "모름": [], "두뇌있음": False,
                "오늘신청": [], "제출뒤": [], "날짜없음": [], "막힘": [],
                "이미한것": [x.strip() for x in axes.get("이미한것", "").split("·")
                           if x.strip() and x.strip() != "없음"],
                "이미한것고를것": [list(x) for x in 이미한것값], "범위밖": 범위밖}

    bp = Path(brain) if brain else _BRAIN
    val = {}
    if bp.is_file():
        for line in bp.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or "\t" not in line:
                continue
            c = line.split("\t")
            if len(c) >= 3:
                val[c[0]] = {"src": c[2]}

    judge = _judger(axes, asked)
    hit, miss, unknown = [], [], []
    for line in gp.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or "\t" not in line:
            continue
        c = line.split("\t")
        if len(c) < 3:
            continue
        g = {"번호": c[0], "이름": c[1], "조건": c[2],
             "최대": c[3] if len(c) > 3 else "",
             "확인": c[4] if len(c) > 4 else "",
             "시작": c[5] if len(c) > 5 else "지금",
             "받으면": c[6] if len(c) > 6 else "",
             "할일": 할일표.get(c[0], ("", ""))[0], "주소": 할일표.get(c[0], ("", ""))[1],
             "덧붙임": c[7] if len(c) > 7 else "",
             "덧붙임이름표": c[8] if len(c) > 8 else "",
             "출처": val.get(c[0], {}).get("src", "")}
        r = judge(g["조건"])
        if r == "걸림":
            hit.append(g)
        elif r == "안걸림":
            miss.append(g)
        else:
            g["못들은것"] = sorted(
                {m.group(1) for m in re.finditer(r"([가-힣]+)\s*(?:has|!=|>=|<=|=|>|<)",
                                                 g["조건"])} - asked)
            unknown.append(g)

    return {
        "못쟀다": "", "총": len(hit) + len(miss) + len(unknown),
        "걸림": hit, "안걸림": len(miss), "모름": unknown,
        "두뇌있음": bool(val),
        "오늘신청": [g for g in hit if g["최대"].isdigit() and g["시작"] == "지금"],
        "제출뒤": [g for g in hit if g["시작"] == "제출뒤"],
        "날짜없음": [g for g in hit if g["최대"] == "모름" and g["시작"] == "지금"],
        "막힘": [g for g in hit if g["최대"] == "막힘"],
        "이미한것": [x.strip() for x in axes.get("이미한것", "").split("·")
                   if x.strip() and x.strip() != "없음"],
        "이미한것고를것": [list(x) for x in 이미한것값],
        "범위밖": 범위밖,
    }


def 날수말(g, 짧게=False) -> str:
    if not g["최대"]:
        return "날짜는 야간비행이 내려줍니다"
    if g["최대"] == "모름":
        if g.get("덧붙임"):
            return ("최대가 발표되지 않았습니다 — " + g["덧붙임"] if 짧게 else
                    "최대가 발표되지 않았습니다 (다만 " + g["덧붙임"] + ")")
        return "최대가 발표되지 않았습니다"
    if g["최대"] == "해당없음":
        return "날짜로 끝나는 일이 아니라 계속 지켜야 하는 것입니다"
    if g["최대"] == "막힘":
        return ("⛔ 이 방식으로는 출시가 안 됩니다" if 짧게 else
                "⛔ **이 방식으로는 출시가 안 됩니다** — 기다려서 풀리는 일이 아니라 만드는 방식을 바꾸셔야 합니다")
    if g.get("덧붙임"):
        return (f"최대 {g['최대']}일 · {g['덧붙임']}" if 짧게 else
                f"최대 {g['최대']}일 (다만 {g['덧붙임']})")
    return f"최대 {g['최대']}일"


def 확인말(g) -> str:
    if g["확인"] == "요약":
        return "⚠️ 저희는 요약만 보았습니다 — 직접 확인하셔야 합니다"
    if g["확인"] == "미확인":
        return "⚠️ 저희가 확인하지 않았습니다"
    return ""


def 사람말(d: dict) -> list:
    out = []
    if d["못쟀다"] == "판정표없음":
        out.append("  ⛔ 기준 표를 못 찾아 **알려 드릴 수 없습니다**.")
        out.append("     (이건 「해야 할 일이 없다」가 아니라 「확인하지 못했다」입니다.)")
        return out
    if d["못쟀다"] == "안물어봤음":
        out.append("  ⚠️ 아직 안 물어봤습니다 — 앱 설정을 먼저 여쭙습니다")
        out.append("     (이건 「해야 할 일이 없다」가 아니라 「물어보지 않았다」입니다)")
        return out
    out.append("")
    out.append(f"── 출시 준비 — 모두 {d['총']}개 가운데 ──────────────────")
    out.append("")
    오늘 = d["오늘신청"] + [g for g in d["날짜없음"] if g not in d["오늘신청"]]
    if 오늘:
        out.append("  오늘 할 것 — 만드는 동안 같이 진행됩니다.")
        for g in 오늘:
            if g["최대"].isdigit():
                out.append(f"    「기다림」으로 적을 것: {g['이름']} · 최대 {g['최대']}일")
            else:
                out.append(f"    「기다림」으로 적을 것: {g['이름']} · ⚠️ {날수말(g, 짧게=True)}")
                out.append("       **언제쯤 안 오면 물어볼까요?** 그 날을 최대로 적습니다"
                           " — 제가 추정하지 않습니다")
        for g in 오늘:
            if g["받으면"]:
                out.append(f"    받으시면 「이미한것」에 적을 것: {g['받으면']}")
        out.append("")
    else:
        out.append("  오늘 할 것 — 오늘 하실 일은 없습니다. 만드는 데만 집중하시면 됩니다.")
        out.append("")
    if d["걸림"]:
        out.append(f"  해야 하는 것 {len(d['걸림'])}개")
        for g in d["걸림"]:
            out.append(f"    · {g['이름']} — {날수말(g)}")
            c = 확인말(g)
            if c:
                out.append(f"      {c}")
        out.append("")
    if d["모름"]:
        out.append(f"  아직 모르는 것 {len(d['모름'])}개 — 답을 못 들어서 판정을 못 했습니다")
        for g in d["모름"]:
            need = g.get("못들은것") or []
            out.append(f"    · {g['이름']}" + (f" — 아직 못 들은 것: {' · '.join(need)}" if need else ""))
        out.append("")
    if not d["두뇌있음"]:
        out.append("  ⚠️ 조항 원문과 「저희가 언제 읽었나」는 야간비행이 내려줍니다.")
        out.append("")
    if d["제출뒤"]:
        out.append("  아래는 제출한 «뒤»에 시작됩니다.")
        for g in d["제출뒤"]:
            out.append(f"    · {g['이름']} — {날수말(g, 짧게=True)}")
        out.append("")
    out.append(f"  모두 {d['총']}개 가운데 {d['안걸림']}개는 이 경우에 안 하셔도 됩니다."
               if d["안걸림"] else "  안 하셔도 되는 것이 아직 없습니다.")
    out.append("")
    out.append("  ⛔ 그 일들을 «실제로 하는 것»은 여기서 하지 않습니다 — 알려 드리는 데까지가 이 화면입니다.")
    out.append(f"  ⚠️ {범위밖}.")
    out.append("")
    return out


if __name__ == "__main__":
    import json
    d = compute(os.environ.get("STATE"), os.environ.get("PERSON"))
    if "--json" in sys.argv:
        print(json.dumps(d, ensure_ascii=False, indent=1))
    else:
        for line in 사람말(d):
            print(line)
