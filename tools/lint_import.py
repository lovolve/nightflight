#!/usr/bin/env python3
"""가져오기 점검 — 개발 중간에 야간비행을 깐 앱에서, 조종석의 칸마다 «가져왔음 · 이 앱엔 없음 · 아직»을 센다.



🔴 왜: 첫 대화 안내가 «단계와 기능 목록»만 가져오라고 했다. 조종석의 나머지 칸(화면 흐름 · 기능끼리 영향 · 기능마다 상태 ·
   정한 것 · 만드는 법 · 출시 절차 질문)은 조용히 빈 채로 남았고, 빈 칸은 «없다»로 읽힌다.
⭐ 가져오기를 «시작»한 앱(기록 폴더의 가져오기.tsv)에서만 본다. 칸마다 셋 중 하나여야 끝난다:
   가져왔음(기록에 그 줄이 있다) · 이 앱엔 없음(이유를 적었다) · 아직.
⚠️ 기계가 못 보는 것: 가져온 내용이 코드와 맞는지. 0 이 «맞다»는 뜻이 아니다.

쓰는 법 (ledger.sh 가 넘긴다)
  ledger.sh 가져오기 시작                 이 앱을 «개발 중간에 깔았다»로 적는다(첫 대화)
  ledger.sh 가져오기 없음 <칸> "<이유>"    이 앱에는 그 칸이 없다(예: 화면 · 서버만 있는 앱)
  ledger.sh 가져오기                      칸마다 지금 상태
  python3 tools/lint_import.py            대화 끝 검사 — 시작했는데 «아직»이 남았으면 알린다
"""
import re, sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _root

칸들 = [
    ("지금 단계",       ("기록", "단계"),          'ledger.sh 단계 "<번호>. <이름>"'),
    ("제품 이름",       ("앱설정", "앱이름"),       'ledger.sh 앱설정 앱이름 "<이름>" 코드'),
    ("기획 표",         ("설계표", "1"),           'ledger.sh 기능추가 1 "<묶음>" "<항목>" … → ledger.sh 세부상태 "<묶음>" "<항목>" 완료 "<정한 내용 (근거)>"'),
    ("검증 표",         ("설계표", "2"),           'ledger.sh 기능추가 2 "<묶음>" "<항목>" … → ledger.sh 세부상태 "<묶음>" "<항목>" 완료 "<확인한 것 (근거)>"'),
    ("설계 표",         ("설계표", "3"),           'ledger.sh 기능추가 3 "<묶음>" "<항목>" … → ledger.sh 세부상태 "<묶음>" "<항목>" 완료 "<정한 내용 (근거)>"'),
    ("기능 표",         ("설계표", "4+"),          'ledger.sh 기능추가 4 "<기능>" "<세부기능>" …'),
    ("만들어 둔 기능",   ("설치전", None),          'ledger.sh 설치전 "<기능>" "<세부기능>" "<근거 — 파일 · 시험>"'),
    ("화면 흐름",       ("화면", None),            'ledger.sh 화면 · 화면언제 · 화면하는일 · 화면요소 · 화면이동 (3-설계 스킬)'),
    ("기능끼리 영향",    ("기록", "영향|독립"),      'ledger.sh 영향 "<기능>" "<같이 바뀌는 기능>" "같은것을쓴다: <무엇>" 코드'),
    ("기능마다 상태",    ("기록", "상태"),          'ledger.sh 상태 "<기능>" "<상태>" "<갈 수 있는 곳>" 코드'),
    ("정한 것",         ("기록", "결정"),          'ledger.sh 결정 "<정한 것>" "<근거 — 문서 · 커밋>" "<다시 볼 조건>"'),
    ("만드는 법",       ("기록", "표준"),          'ledger.sh 표준 "<방식>" "<어느 파일>" 코드 "<기능>"'),
    ("출시 절차 질문",   ("앱설정", "플랫폼|돈받기|기능"), 'ledger.sh 앱설정 <플랫폼|돈받기|기능> "<값>" 코드'),
    ("출시 상태",       ("앱설정", "출시상태"),     'ledger.sh 앱설정 출시상태 "<출시 전 | 심사 중 | 출시함 — 근거: 스토어 주소 · 출시 커밋>" 코드'),
    ("읽은 문서",       ("앱설정", "읽은문서"),     'ledger.sh 앱설정 읽은문서 "<README · CLAUDE.md · docs/… — 문서마다 정한 것 n건>" 코드'),
]


def _파일():
    return _root.state_dir() / "가져오기.tsv"


def 표지():
    """가져오기.tsv → {"시작": 날짜 | None, "없음": {칸: 이유}}"""
    p = _파일()
    out = {"시작": None, "없음": {}}
    if not p.is_file():
        return out
    for l in p.read_text(encoding="utf-8").splitlines():
        c = (l.split("\t") + ["", "", ""])[:3]
        if c[1] == "시작":
            out["시작"] = c[0]
        elif c[1] == "없음" and c[2]:
            칸, _, 이유 = c[2].partition(" — ")
            out["없음"][칸] = 이유
    return out


def _기록줄():
    p = _root.ledger()
    if not p.is_file():
        return []
    return [l.split("\t") for l in p.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]


def 센다():
    """칸마다 (이름, 상태, 수 또는 이유, 명령). 상태: 가져왔음 · 없음 · 아직"""
    줄 = _기록줄()
    st = _root.state_dir()
    plan = st / "plan.tsv"
    plan줄 = [l.split("\t") for l in plan.read_text(encoding="utf-8").splitlines()
              if l and not l.startswith("#")] if plan.is_file() else []
    scr = st / "screens.tsv"
    화면수 = sum(1 for l in scr.read_text(encoding="utf-8").splitlines() if l.startswith("화면\t")) if scr.is_file() else 0
    화면없음 = any(len(c) > 2 and c[1] == "화면없음" and c[2].strip() for c in 줄)
    없음 = 표지()["없음"]
    out = []
    for 이름, (어디, 무엇), 명령 in 칸들:
        if 어디 == "기록":
            n = sum(1 for c in 줄 if len(c) > 1 and c[1] in 무엇.split("|"))
            if 이름 == "지금 단계":
                n = sum(1 for c in 줄 if len(c) > 2 and c[1] == "단계" and "진단" not in c[2])
        elif 어디 == "앱설정":
            n = sum(1 for c in 줄 if len(c) > 2 and c[1] == "앱설정" and c[2] in 무엇.split("|"))
            if 이름 == "제품 이름" and not n:
                n = sum(1 for c in 줄 if len(c) > 2 and c[1] == "결정" and "제품 이름" in c[2])
        elif 어디 == "설계표":
            n = sum(1 for c in plan줄 if c and (c[0] == 무엇 if 무엇 != "4+" else c[0].isdigit() and int(c[0]) >= 4))
        elif 어디 == "설치전":
            n = sum(1 for c in plan줄 if len(c) > 5 and c[5].startswith("설치 전"))
        else:
            n = 화면수 or (1 if 화면없음 else 0)
        if n and 이름 == "화면 흐름" and not 화면없음:
            후보 = _화면파일수()
            out.append((이름, "일부만" if 후보 and n * 2 < 후보 else "가져왔음", n, 명령))
        elif n:
            out.append((이름, "가져왔음", n, 명령))
        elif 이름 in 없음:
            out.append((이름, "없음", 없음[이름], 명령))
        else:
            out.append((이름, "아직", 0, 명령))
    return out


def 시작():
    p = _파일()
    p.parent.mkdir(parents=True, exist_ok=True)
    if 표지()["시작"]:
        print(f"  · 이미 가져오기를 시작했습니다 ({표지()['시작']})")
        return
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"{date.today().isoformat()}\t시작\t\n")
    print("  · 이 앱을 «개발 중간에 깔았다»로 적었습니다 — 칸마다 코드에서 찾아 채우십시오(가져오기 스킬)")


def 없음(칸, 이유):
    if 칸 not in [c[0] for c in 칸들]:
        sys.exit("  ⛔ 칸 이름은 다음 중 하나입니다: " + " · ".join(c[0] for c in 칸들))
    이유 = (이유 or "").strip()
    if not 이유:
        sys.exit("  ⛔ 이유가 필요합니다 — 왜 이 앱에는 그 칸이 없나")
    with open(_파일(), "a", encoding="utf-8") as f:
        f.write(f"{date.today().isoformat()}\t없음\t{칸} — {이유}\n")
    print(f"  · «{칸}» — 이 앱엔 없음 ({이유})")


def 보기():
    t = 표지()
    if not t["시작"]:
        print("  · 이 앱은 가져오기를 시작하지 않았습니다 — 개발 중간에 깔았으면: ledger.sh 가져오기 시작")
        return
    for 이름, 상태, 값, 명령 in 센다():
        표 = {"가져왔음": "●", "없음": "–", "아직": "○"}[상태]
        말 = {"가져왔음": f"가져왔음 {값}줄", "없음": f"이 앱엔 없음 — {값}", "아직": "아직"}[상태]
        print(f"  {표} {이름:<10} {말}")


커밋문턱 = 10


def _커밋수():
    import subprocess
    try:
        r = subprocess.run(["git", "-C", str(_root.state_dir().parent), "rev-list", "--count", "HEAD"],
                           capture_output=True, text=True, timeout=3)
        return int(r.stdout.strip()) if r.returncode == 0 else 0
    except Exception:
        return 0


코드파일문턱 = 5
_코드끝 = (".swift", ".kt", ".java", ".ts", ".tsx", ".js", ".jsx", ".dart", ".py", ".vue", ".svelte")
_안봄 = {".git", "node_modules", "Pods", "DerivedData", "build", ".build", "dist", ".next", ".venv", "venv", ".nightflight", ".claude"}


def _코드파일수():
    import os
    뿌리 = str(_root.state_dir().parent)
    n = 0
    for dp, dn, fn in os.walk(뿌리):
        dn[:] = [d for d in dn if d not in _안봄]
        if dp[len(뿌리):].count(os.sep) >= 4:
            dn[:] = []
        n += sum(1 for f in fn if f.endswith(_코드끝))
        if n >= 코드파일문턱:
            break
    return n


_화면끝 = re.compile(r"(View|Screen|Page)\.(swift|kt|tsx|jsx|dart|vue)$|^page\.(tsx|jsx)$")


def _화면파일수():
    """코드에서 «화면»으로 보이는 파일 수 — 이름이 …View · …Screen · …Page 이거나 page.tsx 인 것(대략이다 · 못 세면 0)."""
    import os
    try:
        뿌리 = str(_root.state_dir().parent)
    except Exception:
        return 0
    n = 0
    for dp, dn, fn in os.walk(뿌리):
        dn[:] = [d for d in dn if d not in _안봄]
        if dp[len(뿌리):].count(os.sep) >= 6:
            dn[:] = []
        n += sum(1 for f in fn if _화면끝.search(f) and not f.startswith(("Preview", "Base")))
    return n


def 진행():
    """조종석 «가져오기» 줄이 그릴 것 — 같은 셈을 두 곳에서 하지 않게 이 함수 하나가 준다(bin/조종석자료.py 가 받아 싣는다).
    보일까: 가져오기를 시작했거나 코드가 쌓인 앱이고, 아직 · 일부만인 칸이 남았을 때만(다 끝나면 줄이 사라진다)."""
    시작함 = bool(표지()["시작"])
    대상 = 시작함 or _커밋수() >= 커밋문턱 or _코드파일수() >= 코드파일문턱
    칸 = []
    for 이름, 상태, 값, _ in 센다():
        칸.append({"이름": 이름, "상태": 상태, "수": 값 if isinstance(값, int) else None,
                  "이유": 값 if 상태 == "없음" else "",
                  "후보": _화면파일수() if 이름 == "화면 흐름" and 상태 in ("가져왔음", "일부만") else None})
    남 = sum(1 for c in 칸 if c["상태"] in ("아직", "일부만"))
    return {"보일까": bool(대상 and 남), "전체": len(칸), "끝": sum(1 for c in 칸 if c["상태"] in ("가져왔음", "없음")),
            "남": 남, "칸": 칸}


def main():
    시작함 = bool(표지()["시작"])
    if not 시작함 and _커밋수() < 커밋문턱 and _코드파일수() < 코드파일문턱:
        return 0
    남 = [x for x in 센다() if x[1] in ("아직", "일부만")]
    if not 남:
        return 0
    if 시작함:
        print(f"  🔴 개발 중간에 깐 앱인데 조종석 칸 {len(남)}개를 아직 가져오지 않았습니다 — 코드에서 찾아 채우거나, 없으면 «없음»을 이유와 함께 적으십시오")
    else:
        print(f"  🔴 코드가 쌓인 앱인데 조종석 칸 {len(남)}개가 비어 있습니다 — «가져오기» 스킬대로 `ledger.sh 가져오기 시작` 으로 적고 코드에서 찾아 채우거나, 없으면 «없음»을 이유와 함께 적으십시오")
    for 이름, 상태, n, 명령 in 남:
        덧 = f" (일부만 — {n}개 적힘 · 코드의 화면 파일 {_화면파일수()}개)" if 상태 == "일부만" else ""
        print(f"     · {이름}{덧} → {명령}  |  없으면: ledger.sh 가져오기 없음 \"{이름}\" \"<이유>\"")
    return 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["시작"]:
        시작()
    elif a[:1] == ["없음"] and len(a) == 3:
        없음(a[1], a[2])
    elif a[:1] == ["보기"] or a == []:
        if a == []:
            sys.exit(main())
        보기()
    else:
        sys.exit(__doc__.split("쓰는 법")[1])
