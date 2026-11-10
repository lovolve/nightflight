#!/usr/bin/env python3
"""중요한 기능의 독립 확인 — 코딩한 AI가 아니라 따로 띄운 확인 에이전트가 «정말 되나»를 본다.

  「야간비행에서 코드를 검증하거나 기능이 제대로 됐는지 확인하는 과정이 충분히 있어? … 독립된 에이전트로」
  → 「중요한 기능에만 돌리는 걸로 설계해」 · 실패하면 «알리기만 함» · 이미 완료된 것은 «새 판 첫 대화에서 한 번 확인».
  따로 실제로 돌려 본 대화가 찾았다. 완료를 정하는 것이 코딩한 AI 자신이면 이 빈 곳은 안 메워진다.

흐름:
  ① 중요한 기능(bin/important.py)의 개발 · 수정 단계 세부기능을 «완료»로 적으면 plan.py 가 «확인 필요 · 독립 확인 대기»로 적고
     여기 «대기» 줄을 남긴다. 이미 완료였던 것은 처음 한 번(소급) «대기» 줄만 남기고 완료는 그대로 둔다.
  ② 턴 끝(check_touched.sh)이 이 파일을 인자 없이 부른다 — 대기가 있으면 확인 에이전트를 띄우라고 모델에게 알린다.
  ③ 모델은 «설명» 이 만든 파일 경로 하나만 에이전트에게 준다. 설명은 기록(정한 것 · 표준 · 실패 경우)에서 짓는다 —
     코딩한 AI의 «다 됐다»는 판단은 넣지 않는다.
  ④ 에이전트가 결과 파일을 남기고 «기록» 으로 판정을 적는다 — 통과면 완료, 실패 · 사람이면 «확인 필요»(막지 않는다).
⚠️ 한계: 코딩한 AI가 결과 파일을 직접 써서 «기록»을 부르는 것은 완전히 막지 못한다 — 설명에만 있는 열쇠를 요구해 어렵게 할 뿐이다.

사용:  independent_check.py                         대기가 있으면 모델 안내를 찍고 끝값 1(턴 끝 검사)
       independent_check.py 목록
       independent_check.py 설명 <기능> <세부기능>    확인 에이전트에게 줄 설명 파일을 짓고 경로를 찍는다
       independent_check.py 기록 <기능> <세부기능> 통과|실패|사람 "<근거 한 줄>" <결과 파일>
       independent_check.py 중요 <기능> | 중요뺌 <기능>   사람이 «이것도 중요해» · «이건 아니야»라고 한 것
"""
import hashlib
import secrets
import sys
from datetime import date
from pathlib import Path

여기 = Path(__file__).resolve().parent
sys.path.insert(0, str(여기))
sys.path.insert(0, str(여기.parent / "bin"))
import plan
from important import 분야

판정말 = {"통과": ("완료", "독립 확인: "), "실패": ("확인 필요", "독립 확인 실패"), "사람": ("확인 필요", "사람 확인 필요")}
대상단계 = {"4", "7"}


def _상태폴더() -> Path:
    return plan._file().parent


def _기록() -> Path:
    return _상태폴더() / "ledger.tsv"


def _파일() -> Path:
    return _상태폴더() / "internal" / "independent_checks.tsv"


def 읽기() -> dict:
    out = {}
    p = _파일()
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            if not l or l.startswith("#"):
                continue
            c = (l.split("\t") + [""] * 7)[:7]
            out[(c[1], c[2])] = {"날": c[0], "기능": c[1], "세부": c[2], "상태": c[3], "근거": c[4], "열쇠": c[5], "확인말": c[6]}
    return out


def _적기(기능, 세부, 상태, 근거="", 열쇠="", 확인말=""):
    p = _파일()
    p.parent.mkdir(parents=True, exist_ok=True)
    새 = not p.exists()
    with open(p, "a", encoding="utf-8") as f:
        if 새:
            f.write("# 독립 확인 — 날 ⇥ 기능 ⇥ 세부기능 ⇥ 대기|통과|실패|사람 ⇥ 근거 ⇥ 열쇠 ⇥ 코딩한 AI가 적은 확인 (tools/independent_check.py 가 쓴다)\n")
        f.write("\t".join(x.replace("\t", " ").replace("\n", " ") for x in
                          (date.today().isoformat(), 기능, 세부, 상태, 근거, 열쇠, 확인말)) + "\n")


def 중요한가(기능) -> bool:
    return bool(분야(기능, str(_기록())))


def 대상인가(기능, 세부) -> bool:
    단 = {r["단계"] for r in plan.읽기() if r["기능"] == 기능 and r["세부기능"] == 세부}
    return bool(단 & 대상단계) and 중요한가(기능)


def 대기적기(기능, 세부, 확인말=""):
    _적기(기능, 세부, "대기", "", "", 확인말)


def 소급():
    표 = _상태폴더() / "internal" / "independent_retro.done"
    if 표.exists() or not plan._file().exists():
        return 0
    있음, n = 읽기(), 0
    for r in plan.읽기():
        if r["단계"] in 대상단계 and r["상태"] == "완료" and (r["기능"], r["세부기능"]) not in 있음 and 중요한가(r["기능"]):
            대기적기(r["기능"], r["세부기능"], r["이름표"]); n += 1
    표.parent.mkdir(parents=True, exist_ok=True)
    표.write_text(date.today().isoformat() + f"\t{n}\n", encoding="utf-8")
    return n


def 대기목록():
    return [v for v in 읽기().values() if v["상태"] == "대기"]


def _기록줄(칸, 무엇):
    out = []
    try:
        for l in _기록().read_text(encoding="utf-8").splitlines():
            c = l.split("\t")
            if len(c) > 2 and c[1] == 칸 and 무엇 in l:
                out.append(c)
    except OSError:
        pass
    return out


def 설명(기능, 세부) -> Path:
    if (기능, 세부) not in 읽기():
        sys.exit(f"  ⛔ 「{기능} / {세부}」은 독립 확인 대기 항목이 아닙니다 — independent_check.py 목록 을 보십시오")
    v = 읽기()[(기능, 세부)]
    폴더 = _상태폴더() / "internal" / "checks"
    폴더.mkdir(parents=True, exist_ok=True)
    이름 = hashlib.sha1(f"{기능}\t{세부}".encode("utf-8")).hexdigest()[:10]
    결과 = 폴더 / f"{이름}.result.md"
    이미 = 폴더 / f"{이름}.brief.md"
    if v["상태"] == "대기" and v["열쇠"] and 이미.exists():
        return 이미
    열쇠 = secrets.token_hex(8)
    _적기(기능, 세부, "대기", "", 열쇠, v["확인말"])
    결과.unlink(missing_ok=True)
    기능설명 = plan.설명읽기().get(기능, "")
    표준 = [c for c in _기록줄("표준", 기능) if len(c) > 5 and c[5] == 기능]
    결정 = [c for c in _기록줄("결정", 기능)][-8:]
    ledger = Path(__file__).resolve().parent.parent / "bin" / "ledger.sh"
    글 = [f"# 독립 확인 — {기능} / {세부}", "",
          "당신은 이 기능을 만든 대화와 따로 떠 있는 확인 담당입니다. 만든 대화의 설명은 받지 않았습니다.",
          "이 파일과 제품 코드 · 기록만 보고, 이 세부기능이 실제로 되는지 확인하십시오.", "",
          "## 지키는 것",
          "- 제품 파일을 고치지 않습니다. 쓰는 파일은 아래 결과 파일 하나뿐입니다.",
          "- 빌드 · 시험 · 실행할 수 있는 것은 실제로 돌립니다. 코드를 읽기만 하고 «된다»고 하지 않습니다.",
          "- 스크린샷은 찍지 않습니다. 시뮬레이터 · 에뮬레이터는 같은 목적으로 두 번 실패하면 멈춥니다.",
          "- 눈으로만 볼 수 있는 것(휴대폰 화면 · 결제 창)은 «사람» 판정으로 넘기고 볼 항목을 적습니다.",
          "- 돈이 실제로 나가는 결제 · 실제 계정 만들기 · 남에게 보내기는 하지 않습니다. 시험 환경이 있으면 그것만 씁니다.", "",
          "## 확인할 것", f"- 기능: {기능}", f"- 세부기능: {세부}"]
    if 기능설명:
        글.append(f"- 기능 설명(기록): {기능설명}")
    try:
        import acceptance as _ac
        _기 = _ac.기준(기능, 세부)
    except Exception:
        _기 = None
    if _기:
        글.append(f"- 합격 기준({'사용자 확인' if _기['확인'] == '확인됨' else 'AI 초안'}): {_기['기준']} — 이 기준대로 실제로 돌려 보고 판정하십시오")
    if 표준:
        글 += ["", "## 이 기능의 정한 방식과 실패 경우(기록) — 실패 경우마다 사용자가 무엇을 보는지 확인하십시오"]
        for c in 표준:
            글.append(f"- {c[2]}" + (f" · 도구: {c[7]}" if len(c) > 7 and c[7] else "") + (f" · 실패 경우: {c[8]}" if len(c) > 8 and c[8] else ""))
    if 결정:
        글 += ["", "## 이 기능에 걸린 정한 것(기록)"] + [f"- {c[2]}" for c in 결정]
    글 += ["", "## 끝나면 — 이 두 가지를 차례로 하십시오",
           f"1. 결과 파일을 씁니다: {결과}",
           f"   첫 줄에 `열쇠: {열쇠}` 를 적고, 그 아래에 돌린 명령 · 본 것 · 판정 까닭을 적습니다.",
           f"2. 판정을 적습니다(통과 · 실패 · 사람 중 하나):",
           f"   \"{ledger}\" 독립확인 기록 \"{기능}\" \"{세부}\" <통과|실패|사람> \"<근거 한 줄>\" \"{결과}\"",
           "", "판정 기준: 통과 = 실제로 돌려서 됨을 봤다 · 실패 = 돌려서 틀린 것을 봤다 · 사람 = 기계로는 볼 수 없어 사람이 봐야 한다.",
           "돌려 보지 못했으면 통과로 적지 않습니다."]
    p = 폴더 / f"{이름}.brief.md"
    p.write_text("\n".join(글) + "\n", encoding="utf-8")
    return p


def _기록경로(결과파일) -> str:
    try:
        return str(Path(결과파일).resolve().relative_to(_상태폴더().resolve()))
    except ValueError:
        return Path(결과파일).name


def 기록(기능, 세부, 판정, 근거, 결과파일):
    if 판정 not in 판정말:
        sys.exit("  ⛔ 판정은 통과 · 실패 · 사람 중 하나입니다")
    v = 읽기().get((기능, 세부))
    if not v or v["상태"] != "대기" or not v["열쇠"]:
        sys.exit(f"  ⛔ 「{기능} / {세부}」에 설명을 지은 확인 대기가 없습니다 — 먼저 independent_check.py 설명 으로 확인 담당 AI를 띄우십시오")
    try:
        첫 = Path(결과파일).read_text(encoding="utf-8").strip().splitlines()[0]
    except (OSError, IndexError):
        sys.exit("  ⛔ 결과 파일이 없습니다 — 확인 담당 AI가 남긴 결과 파일 경로를 주십시오")
    if v["열쇠"] not in 첫:
        sys.exit("  ⛔ 결과 파일의 첫 줄 열쇠가 설명의 열쇠와 다릅니다 — 확인 담당 AI가 이번 설명으로 쓴 결과가 아닙니다")
    if not (근거 or "").strip():
        sys.exit("  ⛔ 근거 한 줄이 필요합니다 — 무엇을 돌려서 무엇을 봤나")
    상태, 머리 = 판정말[판정]
    이름표 = (머리 + 근거.strip()) if 판정 == "통과" else 머리
    rows = plan.읽기()
    for r in rows:
        if r["기능"] == 기능 and r["세부기능"] == 세부:
            r["상태"], r["이름표"], r["바뀐날"] = 상태, 이름표, date.today().isoformat()
    plan.쓰기(rows)
    _적기(기능, 세부, 판정, 근거.strip(), v["열쇠"], v["확인말"])
    with open(_기록(), "a", encoding="utf-8") as f:
        f.write("\t".join([date.today().isoformat(), "독립확인", 판정, 근거.strip().replace("\t", " "), _기록경로(결과파일), "", f"{기능} › {세부}"]) + "\n")
    print(f"  · 독립 확인 {판정} — {기능} / {세부} → {상태}")
    if 판정 != "통과":
        print(f"  [모델] 사용자에게 알리십시오(막지 않습니다): 「{기능} / {세부}」 독립 확인 결과 «{판정}» — {근거.strip()}")


def 안내() -> int:
    소급()
    대기 = 대기목록()
    if not 대기:
        return 0
    here = Path(__file__).resolve()
    print(f"  · 중요한 기능 독립 확인 대기 {len(대기)}건 — 만든 대화가 아니라 따로 띄운 확인 담당 AI가 봅니다.")
    for v in 대기[:5]:
        print(f"    - {v['기능']} / {v['세부']}")
    지은 = [v for v in 대기 if v["열쇠"]]
    if 지은:
        print(f"  [모델] 설명을 이미 지은 {len(지은)}건은 확인 담당 AI가 돌고 있으면 결과를 기다리십시오. 같은 건을 또 띄우지 않습니다.")
    안지은 = [v for v in 대기 if not v["열쇠"]]
    if not 안지은:
        return 1
    v = 안지은[0]
    print("  [모델] 하나씩 하십시오. 설명 파일을 짓고, 그 경로만 확인 에이전트에게 주십시오(당신의 설명 · 판단은 덧붙이지 않습니다):")
    print(f"    python3 \"{here}\" 설명 \"{v['기능']}\" \"{v['세부']}\"")
    print("    → Agent 도구 · subagent_type \"nightflight:feature-verifier\" · prompt 「<설명 파일 경로> 를 읽고 그대로 하십시오」")
    print("    에이전트를 띄울 수 없는 도구면 사용자에게 «독립 확인을 못 했습니다»라고 알리고 넘어가십시오. 결과를 대신 적지 않습니다.")
    return 1


def 중요(기능, 뺌=False):
    with open(_기록(), "a", encoding="utf-8") as f:
        f.write("\t".join([date.today().isoformat(), "중요기능뺌" if 뺌 else "중요기능", 기능, "", "", "", ""]) + "\n")
    print(f"  · 「{기능}」 — " + ("중요한 기능에서 뺐습니다" if 뺌 else "중요한 기능으로 적었습니다. 이 기능의 개발 세부기능은 완료할 때 독립 확인을 거칩니다"))


def main(a):
    if not a:
        return 안내()
    k = a[0]
    if k == "목록":
        소급()
        for v in 읽기().values():
            print(f"  {v['상태']:<4} {v['기능']} / {v['세부']}" + (f" — {v['근거']}" if v["근거"] else ""))
        return 0
    if k == "설명" and len(a) >= 3:
        print(설명(a[1], a[2])); return 0
    if k == "기록" and len(a) >= 6:
        기록(a[1], a[2], a[3], a[4], a[5]); return 0
    if k in ("중요", "중요뺌") and len(a) >= 2:
        중요(a[1], 뺌=(k == "중요뺌")); return 0
    print(__doc__.split("사용:")[1].split("\n\n")[0])
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
