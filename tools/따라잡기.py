#!/usr/bin/env python3
"""따라잡기 제안 — 진행 중인 프로젝트에서 지나간 단계에 빠진 일을 찾아 «하고 이어 갈까요»를 고르게 한다."""
import json, os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _root

단계들 = "진단 기획 검증 설계 개발 테스트 출시 수정 출시후".split()
차례 = ["표준", "실패", "검증", "기획"]


def _번호(이름):
    for i in range(len(단계들) - 1, -1, -1):
        if 단계들[i] in (이름 or "").replace("5. 확인", "5. 테스트").replace("5-확인", "5-테스트"):
            return i
    return None


def _줄들(lp):
    try:
        return [l.rstrip("\n").split("\t") for l in lp.read_text(encoding="utf-8").splitlines()]
    except OSError:
        return []


def compute(ledger=None):
    lp = Path(ledger) if ledger else _root.ledger()
    if not lp.is_file():
        return {"보일까": False}
    줄 = _줄들(lp)
    cur = None
    for c in 줄:
        if len(c) > 2 and c[1] == "단계":
            n = _번호(c[2])
            if n is not None:
                cur = n
    if cur is None or cur < 2:
        return {"보일까": False, "단계": cur}

    os.environ["NF_STATE"] = str(lp.parent)
    try:
        import standards, plan
        st = standards.compute(lp)
        pd = plan.compute()
    except Exception:
        return {"보일까": False, "못쟀다": True}
    표 = (pd or {}).get("단계") or {}

    def 기능들(최소):
        xs = []
        for k, p in 표.items():
            if str(k).isdigit() and int(k) >= 최소:
                for f in p.get("기능들") or []:
                    if f.get("기능") and f["기능"] not in xs:
                        xs.append(f["기능"])
        return xs

    개발 = [f.get("기능") for f in ((표.get("4") or {}).get("기능들") or []) if f.get("기능")]
    기능별 = st.get("기능별") or {}
    표준있음 = [f for f in 개발 if any(standards.완성(x) for x in 기능별.get(f, []))]
    실패있음 = [f for f in 개발 if any(standards.완성(x) and not str(x.get("실패", "")).startswith("없음")
                                    for x in 기능별.get(f, []))]
    검증수 = sum(1 for c in 줄 if len(c) > 1 and c[1] == "검증") + sum(
        1 for f in ((표.get("2") or {}).get("기능들") or []) for z in (f.get("세부") or []) if z.get("상태") == "완료")
    기획세부 = [z for f in ((표.get("1") or {}).get("기능들") or []) for z in (f.get("세부") or [])]
    기획끝 = sum(1 for z in 기획세부 if z.get("상태") == "완료")

    제안 = {
        "표준": {"이름": "표준방식 확인", "단계": 3, "안내": "3 설계-처방/표준조사", "권장": True,
                "까닭": "기능마다 만든 회사와 많은 앱이 하는 방식을 먼저 확인하면 시행착오가 줄고 기능이 안정됩니다",
                "지금": (f"개발 기능 {len(개발)}개 중 확인 {len(표준있음)}개" if 개발 else "설계표에 개발 기능이 아직 없습니다"),
                "끝": bool(개발) and len(표준있음) == len(개발),
                "남은것": [f for f in 개발 if f not in 표준있음]},
        "실패": {"이름": "실패경로 확인", "단계": 3, "안내": "3 설계-처방/실패설계", "권장": False,
                "까닭": "결제 · 로그인 · 서버처럼 바깥과 닿는 기능은 실패했을 때 사용자가 무엇을 보는지 정해 두지 않으면 출시 뒤에 터집니다",
                "지금": (f"실패경로를 확인한 기능 {len(실패있음)}/{len(개발)}" if 개발 else "설계표에 개발 기능이 아직 없습니다"),
                "끝": bool(개발) and len(실패있음) == len(개발),
                "남은것": [f for f in 개발 if f not in 실패있음]},
        "검증": {"이름": "비슷한 서비스 조사", "단계": 2, "안내": "2 검증-처방/조사-절차", "권장": False,
                "까닭": "같은 일을 하는 앱 3~5개가 지금 어떤지 보면 만들 가치와 빠진 기능이 보입니다",
                "지금": f"검증 기록 {검증수}개", "끝": 검증수 > 0, "남은것": []},
        "기획": {"이름": "기획 구체화 질문", "단계": 1, "안내": "1 기획-처방/질문-틀", "권장": False,
                "까닭": "누구를 위한 앱인지 · 첫 판에 무엇을 뺄지 · 무엇이 되면 성공인지를 정해 두면 범위가 흔들리지 않습니다",
                "지금": (f"기획 항목 {기획끝}/{len(기획세부)} 정함" if 기획세부 else "기획 표가 비어 있습니다"),
                "끝": bool(기획세부) and 기획끝 == len(기획세부), "남은것": []},
    }
    목록 = [dict(id=k, **제안[k]) for k in 차례 if 제안[k]["단계"] < cur and not 제안[k]["끝"]]
    고름, 건너뜀, 적힘 = [], False, False
    for c in 줄:
        if len(c) > 2 and c[1] == "따라잡기":
            적힘 = True
            if c[2] == "고름":
                for x in (c[3] if len(c) > 3 else "").split(","):
                    if x in 제안 and x not in 고름:
                        고름.append(x)
                건너뜀 = False
            elif c[2] == "건너뜀":
                고름, 건너뜀 = [], True
    for x in 목록:
        x["고름"] = x["id"] in 고름
    끝낸것 = [k for k in 고름 if 제안[k]["끝"]]
    return {"보일까": bool(목록) and not 건너뜀, "단계": 단계들[cur], "제안": 목록,
            "고름": (고름 if 적힘 else None), "건너뜀": 건너뜀, "끝낸것": 끝낸것}


def 적기(종류, 값=""):
    lp = _root.ledger()
    if not lp.is_file():
        sys.exit("  ⛔ 기록이 없습니다 — 등록된 프로젝트에서만 적습니다.")
    if 종류 == "고름":
        ids = [x.strip() for x in 값.replace("·", ",").split(",") if x.strip()]
        틀림 = [x for x in ids if x not in 차례]
        if not ids or 틀림:
            sys.exit("  ⛔ 고를 수 있는 것: " + " · ".join(차례) + (" — 모르는 것: " + " · ".join(틀림) if 틀림 else ""))
        값 = ",".join(k for k in 차례 if k in ids)
    with open(lp, "a", encoding="utf-8") as f:
        f.write("\t".join([time.strftime("%Y-%m-%d"), "따라잡기", 종류, 값, "", "", ""]) + "\n")
    d = compute(lp)
    if 종류 == "건너뜀":
        print("  · 따라잡기 제안을 건너뛰었습니다 — 지금 단계 일을 이어 가십시오.")
        return
    print("  · 따라잡기 — 하는 중: " + " · ".join(x["이름"] for x in d.get("제안", []) if x.get("고름")))
    for x in d.get("제안", []):
        if not x.get("고름"):
            continue
        덧 = (" — 남은 기능: " + " · ".join(x["남은것"][:12])) if x.get("남은것") else ""
        print(f"    [모델] {x['이름']}: {x['지금']}{덧} — 먼저 두뇌.sh {x['안내']} 를 받아 그 차례대로 하십시오")
    print("    [모델] 고른 차례대로 하고, 다 끝나면 지금 단계 일로 돌아가십시오. 조종석 카드는 끝날 때마다 줄어듭니다.")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["고름"]:
        적기("고름", " ".join(a[1:]))
    elif a[:1] == ["건너뜀"]:
        적기("건너뜀")
    else:
        print(json.dumps(compute(), ensure_ascii=False, indent=1))
