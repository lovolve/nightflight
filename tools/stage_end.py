#!/usr/bin/env python3
"""단계 끝 조건 — 단계마다 «언제 끝나나»를 한 곳에서 센다. 다음 단계 제안과 단계 넘기 확인이 같은 셈을 쓴다."""
import json, os, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _root

단계들 = "진단 기획 검증 설계 개발 테스트 출시 수정 출시후".split()


def _기록():
    v = os.environ.get("NF_LEDGER")
    return Path(v) if v else _root.ledger()


def _줄들(lp):
    try:
        return [l.split("\t") for l in Path(lp).read_text(encoding="utf-8").splitlines()]
    except OSError:
        return []


def 번호(이름, lp=None):
    t = (이름 or "").strip()
    m = re.match(r"^([0-8])(\s|\.|-|$)", t)
    if m:
        return int(m.group(1))
    for i in range(len(단계들) - 1, -1, -1):
        if t == 단계들[i] or t.endswith(" " + 단계들[i]) or (i == 5 and (t == "확인" or t.endswith(" 확인"))):
            return i
    lp = Path(lp) if lp else _기록()
    mp = lp.parent / "stage-map.tsv"
    try:
        for l in mp.read_text(encoding="utf-8").splitlines():
            c = l.split("\t")
            if len(c) > 1 and c[0] == t and c[1].strip().isdigit():
                return int(c[1])
    except OSError:
        pass
    return None


def 지금(lp=None):
    lp = Path(lp) if lp else _기록()
    cur = None
    for c in _줄들(lp):
        if len(c) > 2 and c[1] == "단계":
            n = 번호(c[2], lp)
            if n is not None:
                cur = n
    return cur


앱설정칸 = {"플랫폼": "어디에 낼지", "만드는법": "만드는 방식", "돈받기": "돈 받기"}


def 앱설정빈것(lp=None):
    lp = Path(lp) if lp else _기록()
    있음 = {c[2] for c in _줄들(lp) if len(c) > 3 and c[1] == "앱설정" and c[3].strip()}
    return [v for k, v in 앱설정칸.items() if k not in 있음]


def 조건(idx, lp=None):
    lp = Path(lp) if lp else _기록()
    os.environ["NF_STATE"] = str(lp.parent)
    줄 = _줄들(lp)
    out = []
    try:
        import plan
        표줄 = plan.읽기()
    except Exception:
        표줄 = []
    내것 = [r for r in 표줄 if str(r["단계"]).strip() == str(idx)]
    if 내것:
        끝 = sum(1 for r in 내것 if r["상태"] == "완료")
        넘 = sum(1 for r in 내것 if r["상태"] == "넘어감")
        out.append({"이름": "%s 표의 항목" % 단계들[idx], "됨": 끝 + 넘 == len(내것),
                    "지금": "%d/%d 완료" % (끝, len(내것) - 넘) + (" · 넘어감 %d" % 넘 if 넘 else "")})
    if idx == 1:
        빈 = [k for k in ("한줄", "누구", "문제")
             if not any(len(c) > 3 and c[1] == "제품소개" and c[2] == k and c[3].strip() for c in 줄)]
        out.append({"이름": "제품 소개(한 줄 · 누구 · 문제)", "됨": not 빈, "지금": "다 적음" if not 빈 else "아직: " + " · ".join(빈)})
        빈2 = 앱설정빈것(lp)
        out.append({"이름": "앱 설정(어디에 낼지 · 만드는 방식 · 돈 받기)", "됨": not 빈2, "지금": "다 정함" if not 빈2 else "아직: " + " · ".join(빈2)})
    if idx == 2:
        n = sum(1 for c in 줄 if len(c) > 1 and c[1] == "검증")
        out.append({"이름": "검증 기록", "됨": n > 0, "지금": "%d개" % n})
    if idx == 5:
        n = sum(1 for c in 줄 if len(c) > 5 and c[1] == "단계확인" and c[5].strip() == "5" and c[4].strip() == "봤음")
        n += sum(1 for r in 내것 if r["상태"] == "완료" and str(r.get("이름표") or "").startswith(("직접 확인", "직접 테스트")))
        out.append({"이름": "직접 써 보고 확인한 것", "됨": n > 0, "지금": "%d개" % n})
    if idx == 3:
        scr = lp.parent / "screens.tsv"
        화면 = (scr.is_file() and any(l.startswith("화면\t") for l in scr.read_text(encoding="utf-8").splitlines())) \
            or any(len(c) > 2 and c[1] == "화면없음" and c[2].strip() for c in 줄)
        out.append({"이름": "화면 설계서", "됨": bool(화면), "지금": "있음" if 화면 else "없음"})
        개발 = sorted({r["기능"] for r in 표줄 if str(r["단계"]).strip() == "4"})
        if 개발:
            try:
                import dependencies, standards
                연결 = set(dependencies.연결된기능(lp))
                st = standards.compute(lp).get("기능별") or {}
                표준 = [f for f in 개발 if any(standards.완성(x) for x in st.get(f, []))]
                out.append({"이름": "기능마다 표준방식 확인", "됨": len(표준) == len(개발), "지금": "%d/%d" % (len(표준), len(개발))})
                out.append({"이름": "기능 사이 연결", "됨": not (set(개발) - 연결), "지금": "%d/%d" % (len(set(개발) & 연결), len(개발))})
            except Exception:
                pass
        try:
            import states
            sd = states.compute(str(lp))
            if not sd.get("못쟀다"):
                없음 = [(f, k) for f, v in (sd.get("기능별본것") or {}).items() for k in v.get("실패출구없음", [])]
                out.append({"이름": "진행 중인 상태의 실패 출구", "됨": not 없음,
                            "지금": "다 있음" if not 없음 else "없음: " + " · ".join("%s의 %s" % x for x in 없음[:4])})
        except Exception:
            pass
    return out


def 넘기(목표이름, 이유="", lp=None, 적기=False):
    lp = Path(lp) if lp else _기록()
    to = 번호(목표이름, lp)
    if to is None:
        print("  ⛔ 단계 이름을 읽지 못했습니다: 「%s」" % 목표이름, file=sys.stderr)
        print("     0. 진단 · 1. 기획 · 2. 검증 · 3. 설계 · 4. 개발 · 5. 확인 · 6. 출시 · 7. 수정 · 8. 출시후 중 하나로 적으십시오.", file=sys.stderr)
        print("     프로젝트가 따로 쓰는 이름이면 먼저 ledger.sh 단계연결 \"<이름>\" <0~8> 로 이으십시오.", file=sys.stderr)
        return 2
    cur = 지금(lp)
    if cur is None or to <= cur or (cur >= 6 and to >= 6):
        return 0
    안됨 = [(cur, x) for x in 조건(cur, lp) if not x["됨"]]
    for k in range(cur + 1, to):
        안됨 += [(k, x) for x in 조건(k, lp) if not x["됨"]]
        if not 조건(k, lp):
            안됨.append((k, {"이름": "%s 단계" % 단계들[k], "지금": "한 번도 거치지 않음"}))
    if not 안됨:
        return 0
    if 이유.strip():
        if not 적기:
            print("  · 끝나지 않은 것을 남기고 넘어갑니다(이유는 단계가 바뀔 때 기록합니다): " + " · ".join("%s %s" % (단계들[k], x["이름"]) for k, x in 안됨))
            return 0
        with open(lp, "a", encoding="utf-8") as f:
            f.write("\t".join([__import__("time").strftime("%Y-%m-%d"), "단계건너뜀", "%d→%d" % (cur, to),
                               이유.replace("\t", " ").replace("\n", " "), "", "", ""]) + "\n")
        print("  · 끝나지 않은 것을 남기고 넘어갑니다(이유를 기록했습니다): " + " · ".join("%s %s" % (단계들[k], x["이름"]) for k, x in 안됨))
        return 0
    print("  ⛔ %s 단계에서 %s 단계로 가기 전에 끝나지 않은 것이 있습니다:" % (단계들[cur], 단계들[to]), file=sys.stderr)
    for k, x in 안됨:
        print("     · %s — %s (%s)" % (단계들[k], x["이름"], x.get("지금", "")), file=sys.stderr)
    print("     [모델] 사용자에게 남은 것을 보이고 «마저 하고 넘어갈까요, 지금 넘어갈까요?»를 물으십시오.", file=sys.stderr)
    print("     [모델] 지금 넘어가기로 하시면 끝에 --이유 \"<사용자가 말한 까닭>\" 를 붙여 다시 부르십시오.", file=sys.stderr)
    return 1


def compute(lp=None):
    lp = Path(lp) if lp else _기록()
    if not lp.is_file():
        return {"단계": None}
    cur = 지금(lp)
    if cur is None:
        return {"단계": None}
    xs = 조건(cur, lp)
    다음 = cur + 1 if cur < 6 else None
    return {"단계": cur, "이름": 단계들[cur], "조건": xs, "다음": 다음, "다음이름": 단계들[다음] if 다음 is not None else "",
            "끝": bool(xs) and all(x["됨"] for x in xs)}


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["번호"]:
        n = 번호(a[1] if len(a) > 1 else "")
        print("" if n is None else n)
        sys.exit(0 if n is not None else 2)
    if a[:1] == ["앱설정빈것"]:
        print(" · ".join(앱설정빈것()))
        sys.exit(0)
    if a[:1] == ["넘기"]:
        sys.exit(넘기(a[1] if len(a) > 1 else "", a[2] if len(a) > 2 else ""))
    if a[:1] == ["건너뜀적기"]:
        sys.exit(넘기(a[1] if len(a) > 1 else "", a[2] if len(a) > 2 else "", 적기=True))
    print(json.dumps(compute(), ensure_ascii=False, indent=1))
