#!/usr/bin/env python3
"""
  · 안 정한 것이 남은 채 설계 → 개발로 넘어가면 «넘어갈 때 한 번 물음»
  · 기준이 없으면 AI의 개발 시작을 «일단 막지만, 표준 방식이나 기준이 없을 때도 사용자가 선택해서 진행시킬 수는 있게»

파일(제품 기록 폴더):
  acceptance.tsv  기능 ⇥ 세부기능 ⇥ 기준(«하면 → 된다») ⇥ 초안|확인됨 ⇥ 날     마지막 줄이 이긴다
  undecided.tsv   번호 ⇥ 날 ⇥ 무엇 ⇥ 추측했다면 ⇥ 열림|정함|나중 ⇥ 정한 것    마지막 줄이 이긴다

사용:  acceptance.py                                   개발 세부기능에 기준이 없거나 안 정한 것이 있으면 모델 안내(턴 끝 검사, 끝값 1)
       acceptance.py 기준 <기능> <세부기능> "<하면 → 된다>"
       acceptance.py 없이진행 <기능> 표준|기준 "<사용자가 고른 말>"
       acceptance.py 안정함 "<무엇>" "<추측했다면 무엇을 골랐을지>"
       acceptance.py 정함 <번호> "<정한 것>"  |  나중 <번호>  |  안정함목록
"""
import sys
from datetime import date
from pathlib import Path

여기 = Path(__file__).resolve().parent
sys.path.insert(0, str(여기))
sys.path.insert(0, str(여기.parent / "bin"))
import plan
from important import 분야

대상단계 = {"4", "7"}


def _폴더() -> Path:
    return plan._file().parent


def _기록() -> Path:
    return _폴더() / "ledger.tsv"


def _덧쓰기(이름, 머리, 칸):
    p = _폴더() / 이름
    p.parent.mkdir(parents=True, exist_ok=True)
    새 = not p.exists()
    with open(p, "a", encoding="utf-8") as f:
        if 새:
            f.write(머리 + "\n")
        f.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in 칸) + "\n")


def _줄들(이름, n):
    p = _폴더() / 이름
    if not p.exists():
        return []
    return [(l.split("\t") + [""] * n)[:n] for l in p.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]


def 기준표() -> dict:
    return {(c[0], c[1]): {"기준": c[2], "확인": c[3], "날": c[4]} for c in _줄들("acceptance.tsv", 5)}


def 기준(기능, 세부):
    return 기준표().get((기능, 세부))


def 기준적기(기능, 세부, 글, 확인="초안"):
    글 = (글 or "").strip()
    if "→" not in 글 or min(len(x.strip()) for x in 글.split("→", 1)) < 2:
        sys.exit("  ⛔ 합격 기준은 «무엇을 하면 → 무엇이 된다» 한 줄입니다. 예: «환불하면 → 그 이용권 키가 막힌다»")
    if not any(r["기능"] == 기능 and r["세부기능"] == 세부 for r in plan.읽기()):
        sys.exit(f"  ⛔ 설계표에 「{기능} / {세부}」 자리가 없습니다")
    _덧쓰기("acceptance.tsv", "# 합격 기준 — 기능 ⇥ 세부기능 ⇥ 기준 ⇥ 초안|확인됨 ⇥ 날 (tools/acceptance.py)", (기능, 세부, 글, 확인, date.today().isoformat()))
    print(f"  · 합격 기준 — {기능} / {세부}: {글}" + (" (사용자 확인)" if 확인 == "확인됨" else ""))
    if 확인 == "초안" and 분야(기능, str(_기록())):
        print("  [모델] 중요한 기능이라 사용자 확인이 필요합니다. 선택지로 물으십시오: «이 기준이 맞습니까?» — 맞음(권장) · 고침. "
              f"맞다고 하시면 ledger.sh 합격기준확인 \"{기능}\" \"{세부}\", 고치면 고친 글로 ledger.sh 합격기준 을 다시 부르십시오.")


def 기준확인(기능, 세부):
    v = 기준(기능, 세부)
    if not v:
        sys.exit(f"  ⛔ 「{기능} / {세부}」에 합격 기준이 없습니다 — 먼저 적으십시오")
    기준적기(기능, 세부, v["기준"], "확인됨")


def 우회있나(기능, 종류) -> bool:
    try:
        for l in _기록().read_text(encoding="utf-8").splitlines():
            c = l.split("\t")
            if len(c) > 3 and c[1] == "기준없이진행" and c[2] == 기능 and c[3] == 종류:
                return True
    except OSError:
        pass
    return False


def 우회적기(기능, 종류, 말):
    if 종류 not in ("표준", "기준"):
        sys.exit("  ⛔ 표준 · 기준 중 하나입니다")
    if len((말 or "").strip()) < 2:
        sys.exit("  ⛔ 사용자가 고르신 말을 그대로 적으십시오 — 선택지에서 «없이 진행»을 고르셨을 때만 씁니다")
    with open(_기록(), "a", encoding="utf-8") as f:
        f.write("\t".join([date.today().isoformat(), "기준없이진행", 기능, 종류, 말.strip().replace("\t", " "), "", ""]) + "\n")
    print(f"  · 「{기능}」 — 사용자 선택으로 {'표준 방식' if 종류 == '표준' else '합격 기준'} 없이 진행합니다: {말.strip()}")


def 막는글(기능, 세부) -> str:
    return (f"  ⛔ 「{기능} / {세부}」에 합격 기준이 없습니다 — 기준 없이 개발을 시작하지 않습니다.\n"
            f"     먼저 초안을 적으십시오:  ledger.sh 합격기준 \"{기능}\" \"{세부}\" \"<무엇을 하면 → 무엇이 된다>\"\n"
            f"     사용자가 선택지에서 «기준 없이 진행»을 고르셨으면:  ledger.sh 기준없이진행 \"{기능}\" 기준 \"<사용자가 고른 말>\"")


def 안정함표() -> dict:
    return {c[0]: {"번호": c[0], "날": c[1], "무엇": c[2], "추측": c[3], "상태": c[4], "정한것": c[5]} for c in _줄들("undecided.tsv", 6)}


def 열린것():
    return [v for v in 안정함표().values() if v["상태"] == "열림"]


def 안정함(무엇, 추측):
    if len((무엇 or "").strip()) < 2:
        sys.exit("  ⛔ 무엇을 안 정했는지 적으십시오")
    번호 = str(max([int(k) for k in 안정함표() if k.isdigit()] or [0]) + 1)
    _덧쓰기("undecided.tsv", "# 아직 안 정함 — 번호 ⇥ 날 ⇥ 무엇 ⇥ 추측했다면 ⇥ 열림|정함|나중 ⇥ 정한 것 (tools/acceptance.py)",
           (번호, date.today().isoformat(), 무엇.strip(), (추측 or "").strip(), "열림", ""))
    print(f"  · 안 정함 {번호} — {무엇.strip()}" + (f" (추측했다면: {추측.strip()})" if 추측 else ""))


def 닫기(번호, 상태, 정한것=""):
    v = 안정함표().get(번호)
    if not v:
        sys.exit(f"  ⛔ 안 정함 {번호} 이 없습니다")
    if 상태 == "정함" and len((정한것 or "").strip()) < 2:
        sys.exit("  ⛔ 정한 것을 적으십시오")
    _덧쓰기("undecided.tsv", "", (번호, date.today().isoformat(), v["무엇"], v["추측"], 상태, (정한것 or "").strip()))
    print(f"  · 안 정함 {번호} → {상태}" + (f": {정한것.strip()}" if 정한것 else ""))
    if 상태 == "정함":
        print("  [모델] 정한 것을 결정 사항으로도 적으십시오(ledger.sh 결정 …).")


def 넘어가기전(새단계) -> str:
    if not str(새단계).startswith("4"):
        return ""
    열 = 열린것()
    if not 열:
        return ""
    줄 = "\n".join(f"     - {v['번호']}. {v['무엇']}" + (f" (추측했다면: {v['추측']})" if v["추측"] else "") for v in 열[:8])
    return (f"  ⛔ 아직 안 정한 것이 {len(열)}개 남아 있습니다 — 개발로 넘어가기 전에 사용자에게 한 번 물으십시오(막지 않습니다).\n{줄}\n"
            "     선택지로 항목마다 «지금 정함 · 나중에» 를 물으십시오. 정하시면 ledger.sh 안정함 정함 <번호> \"<정한 것>\", "
            "나중이면 ledger.sh 안정함 나중 <번호>.\n"
            "     물은 뒤 같은 단계 명령에 --물었음 을 붙여 다시 부르십시오.")


def 안내() -> int:
    표 = 기준표()
    없음 = [r for r in plan.읽기() if r["단계"] in 대상단계 and r["상태"] != "넘어감" and (r["기능"], r["세부기능"]) not in 표
           and not 우회있나(r["기능"], "기준")]
    열 = 열린것()
    if not 없음 and not 열:
        return 0
    if 없음:
        print(f"  · 합격 기준이 없는 개발 세부기능 {len(없음)}개 — 확인 담당 AI와 테스트가 대조할 기준이 없습니다.")
        for r in 없음[:5]:
            print(f"    - {r['기능']} / {r['세부기능']}")
        print("  [모델] 기록과 코드를 읽고 세부기능마다 «무엇을 하면 → 무엇이 된다» 초안을 적으십시오(사용자에게 묻지 않습니다 — 중요 기능만 적은 뒤 확인을 받습니다):")
        print(f"    ledger.sh 합격기준 \"{없음[0]['기능']}\" \"{없음[0]['세부기능']}\" \"<하면 → 된다>\"")
    if 열:
        print(f"  · 아직 안 정한 것 {len(열)}개 — 조종석 결정 사항 맨 위에 보입니다.")
    return 1


def main(a):
    if not a:
        return 안내()
    k = a[0]
    if k == "기준" and len(a) == 4:
        기준적기(a[1], a[2], a[3])
    elif k == "기준확인" and len(a) == 3:
        기준확인(a[1], a[2])
    elif k == "없이진행" and len(a) == 4:
        우회적기(a[1], a[2], a[3])
    elif k == "안정함" and len(a) in (2, 3):
        안정함(a[1], a[2] if len(a) == 3 else "")
    elif k == "정함" and len(a) == 3:
        닫기(a[1], "정함", a[2])
    elif k == "나중" and len(a) == 2:
        닫기(a[1], "나중")
    elif k == "넘어가기전" and len(a) == 2:
        t = 넘어가기전(a[1])
        if t:
            print(t)
    elif k == "안정함목록":
        for v in 안정함표().values():
            print(f"  {v['번호']}. [{v['상태']}] {v['무엇']}" + (f" → {v['정한것']}" if v["정한것"] else ""))
    else:
        print(__doc__.split("사용:")[1])
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
