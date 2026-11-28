#!/usr/bin/env python3
"""실패 상황 — 기획에서 «실패 정책»을 묻고, 설계에서 기능마다 «실패 종류»를 빠짐없이 챙긴다.


기록 줄(ledger.tsv):
  날짜 ⇥ 실패정책 ⇥ 정책번호 ⇥ 고른 것 ⇥ 출처(사용자|내판단)
  날짜 ⇥ 실패점검 ⇥ 기능 ⇥ 종류번호 ⇥ 처리|해당없음 ⇥ 처리 방법과 보이는 화면, 또는 까닭 ⇥ 출처(사용자|내판단)
  ⭐ 같은 자리를 다시 적으면 마지막 줄이 이긴다.

사용:  failure_plan.py 정책목록               — 이 제품에 해당하는 질문과 답한 것
       failure_plan.py 정책 <번호> "<고른 것>" [사용자|내판단]
       failure_plan.py 점검목록               — 기능마다 빠진 실패 종류
       failure_plan.py 점검 <기능> <종류번호[,종류번호…]|전부> 처리|해당없음 "<방법과 화면 · 또는 까닭>" [사용자|내판단]
"""
import os
import sys
from datetime import date
from pathlib import Path

여기 = Path(__file__).resolve().parent
sys.path.insert(0, str(여기))
import plan

_표 = 여기.parent / "data" / "failure_kinds.tsv"


def _기록():
    v = os.environ.get("NF_LEDGER")
    return Path(v) if v else plan._file().with_name("ledger.tsv")


def _읽기표():
    정책, 종류 = [], []
    try:
        줄들 = _표.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 정책, 종류
    for l in 줄들:
        if not l or l.startswith("#"):
            continue
        c = l.split("\t") + [""] * 5
        if c[0] == "정책":
            정책.append({"번호": c[1], "질문": c[2], "고를것": [x.strip() for x in c[3].split("·") if x.strip()], "조건": c[4].strip()})
        elif c[0] == "종류":
            종류.append({"번호": c[1], "이름": c[2], "무엇": c[3]})
    return 정책, 종류


def _줄(lp=None):
    p = Path(lp) if lp else _기록()
    try:
        return [l.split("\t") for l in p.read_text(encoding="utf-8", errors="replace").splitlines()]
    except OSError:
        return []


def 해당정책(lp=None):
    정책, _ = _읽기표()
    try:
        맞나 = plan._앱조건()
    except Exception:
        맞나 = lambda 조건: "모름"
    return [p for p in 정책 if not p["조건"] or 맞나(p["조건"]) != "안걸림"]


def 정한정책(lp=None):
    out = {}
    for c in _줄(lp):
        if len(c) > 3 and c[1] == "실패정책" and c[3].strip():
            out[c[2]] = (c[3], c[4] if len(c) > 4 else "")
    return out


def 정책빈것(lp=None):
    정 = 정한정책(lp)
    return [p["번호"] for p in 해당정책(lp) if p["번호"] not in 정]


def 개발기능():
    return sorted({r["기능"] for r in plan.읽기() if str(r["단계"]).strip() == "4" and r.get("출처") != "단계 기본"})


def 적은점검(lp=None):
    out = {}
    for c in _줄(lp):
        if len(c) > 5 and c[1] == "실패점검" and c[5].strip():
            out[(c[2], c[3])] = (c[4], c[5], c[6] if len(c) > 6 else "")
    return out


def 점검빈것(lp=None):
    _, 종류 = _읽기표()
    적 = 적은점검(lp)
    return {f: 빈 for f in 개발기능() if (빈 := [k["번호"] for k in 종류 if (f, k["번호"]) not in 적])}


def _적기(칸들):
    p = _기록()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write("\t".join([date.today().isoformat()] + [str(x).replace("\t", " ").replace("\n", " ") for x in 칸들]) + "\n")


def 정책목록():
    해당, 정 = 해당정책(), 정한정책()
    if not 해당:
        print("  · 이 제품에 해당하는 실패 정책 질문이 없습니다.")
        return 0
    print("  ── 실패 정책 — 기획에서 여쭙니다(선택형 질문 도구로 하나씩 · «아직 모르겠다» 넣기) ──")
    for p in 해당:
        if p["번호"] in 정:
            값, 출처 = 정[p["번호"]]
            print(f"  ✓ [{p['번호']}] {p['질문']} → {값}" + (" (AI가 정함)" if 출처 == "내판단" else ""))
        else:
            print(f"  · [{p['번호']}] {p['질문']}  고를 것: {' / '.join(p['고를것'])} (첫째가 권장)")
    빈 = [p["번호"] for p in 해당 if p["번호"] not in 정]
    if 빈:
        print("  [모델] 답은 ledger.sh 실패정책 <번호> \"<고른 것>\" 으로 적습니다. «아직 모르겠다»면 \"모름\" 으로 적고, 설계에서 AI가 표준대로 정해 내판단으로 다시 적습니다.")
    return 0


def 정책(번호, 값, 출처="사용자"):
    if 번호 not in {p["번호"] for p in _읽기표()[0]}:
        sys.exit(f"  ⛔ 모르는 정책 번호입니다: {번호} — 쓸 수 있는 것: " + " · ".join(p["번호"] for p in _읽기표()[0]))
    값 = (값 or "").strip()
    if not 값:
        sys.exit("  ⛔ 고른 것이 비어 있습니다 — 모르시면 «모름»으로 적으십시오.")
    if 출처 not in ("사용자", "내판단"):
        sys.exit("  ⛔ 출처는 사용자 · 내판단 중 하나입니다")
    _적기(["실패정책", 번호, 값, 출처])
    print(f"  · 실패 정책을 적었습니다 — {번호}: {값}" + (" (AI가 정함)" if 출처 == "내판단" else ""))
    return 0


def 점검목록():
    _, 종류 = _읽기표()
    기능들 = 개발기능()
    if not 기능들:
        print("  · 개발할 기능이 설계표에 아직 없습니다 — 기능을 먼저 적으면 기능마다 실패 종류를 챙깁니다.")
        return 0
    정 = 정한정책()
    if 정:
        print("  · 기획에서 정한 실패 정책: " + " · ".join(f"{k}={v[0]}" for k, v in 정.items()))
    빈 = 점검빈것()
    적 = 적은점검()
    print(f"  ── 기능마다 실패 상황 점검 — {len(기능들) - len(빈)}/{len(기능들)} 기능 끝 ──")
    for f in 기능들:
        if f not in 빈:
            n = sum(1 for k in 종류 if 적.get((f, k["번호"]), ("",))[0] == "처리")
            print(f"  ✓ {f} — 처리 {n} · 해당없음 {len(종류) - n}")
        else:
            print(f"  · {f} — 아직: " + " · ".join(k["이름"] for k in 종류 if k["번호"] in 빈[f]))
    if 빈:
        print("  종류: " + " · ".join(f"{k['번호']}({k['무엇']})" for k in 종류))
        print("  [모델] 기능마다 종류별로 적으십시오: ledger.sh 실패점검 \"<기능>\" <종류번호[,…]|전부> 처리|해당없음 \"<처리 방법과 보이는 화면 · 또는 까닭>\" [사용자|내판단]. 기획 정책을 따르고, 묻지 않은 것은 표준대로 정해 내판단으로 적은 뒤 사용자에게 한 번에 요약해 보이십시오.")
    return 0


def 점검(기능, 종류들, 판, 글, 출처="내판단"):
    _, 종류 = _읽기표()
    번호들 = [k["번호"] for k in 종류]
    고른 = 번호들 if 종류들 == "전부" else [x.strip() for x in 종류들.split(",") if x.strip()]
    모름 = [x for x in 고른 if x not in 번호들]
    if 모름 or not 고른:
        sys.exit("  ⛔ 모르는 종류입니다: " + " · ".join(모름 or ["(비어 있음)"]) + " — 쓸 수 있는 것: " + " · ".join(번호들) + " · 전부")
    if 판 not in ("처리", "해당없음"):
        sys.exit("  ⛔ 셋째 칸은 처리 · 해당없음 중 하나입니다")
    글 = (글 or "").strip()
    if len(글) < 4:
        sys.exit("  ⛔ " + ("처리 방법과 사용자에게 보이는 화면을" if 판 == "처리" else "해당없는 까닭을") + " 한 줄로 적으십시오.")
    if 출처 not in ("사용자", "내판단"):
        sys.exit("  ⛔ 출처는 사용자 · 내판단 중 하나입니다")
    if 기능 not in 개발기능():
        sys.exit(f"  ⛔ 설계표의 개발 기능에 「{기능}」이 없습니다 — 쓸 수 있는 것: " + " · ".join(개발기능() or ["(없음)"]))
    for k in 고른:
        _적기(["실패점검", 기능, k, 판, 글, 출처])
    print(f"  · {기능} — {' · '.join(고른)}: {판}" + (" (AI가 정함)" if 출처 == "내판단" else ""))
    return 0


def main(a):
    if not a or a[0] == "정책목록":
        return 정책목록()
    if a[0] == "정책" and len(a) >= 3:
        return 정책(a[1], a[2], a[3] if len(a) > 3 else "사용자")
    if a[0] == "점검목록":
        return 점검목록()
    if a[0] == "점검" and len(a) >= 5:
        return 점검(a[1], a[2], a[3], a[4], a[5] if len(a) > 5 else "내판단")
    print(__doc__.split("사용:")[1] if "사용:" in __doc__ else __doc__)
    return 1


if __name__ == "__main__":
    plan.잠그기()
    sys.exit(main(sys.argv[1:]))
