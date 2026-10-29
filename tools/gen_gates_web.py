#!/usr/bin/env python3
"""설치 전 관문 셈 — 웹이 쓸 **미리 계산한 표**를 만든다

설계: nightflight-server design/설치전-관문셈.md (창업자 결정 2026-10-11: 질문 넷)


설계 §4 가 🔴 **「판정 규칙이 두 곳이 된다」**를 걸림돌로 꼽았다.
⛔ 이 저장소가 「**두 곳에 두면 한 곳이 반드시 낡는다**」로 값을 치렀다(2026-09-30).

⭐⭐ 그런데 4-개발 처방이 답을 적어 뒀다:
   「**값이 두 곳에 있으면 검사가 아니라 «구조»로 푼다** — 한 곳이면 볼 필요가 없다」

⭐ 그래서 **판정 규칙을 웹에 보내지 않는다.** 네 축이 가질 수 있는 답을 **전부 돌려
   미리 계산**하고, 웹은 **표를 찾아보기만** 한다.
   → **규칙은 `gates.py` 한 곳에만 있다.** 어긋날 길이 **구조적으로 없다.**

⛔ **그래도 검사는 필요하다** — 만들어 둔 표가 **낡을 수 있다**
   (`관문.tsv` 나 `gates.py` 가 바뀌면). 그건 `lint_gates_web.py` 가 본다.


- **네 축만 쓴다**(창업자 결정: 플랫폼·만드는법·계정종류·기능). 다섯째를 넣지 않는다.
- **「이미한것」은 「없음」으로 둔다** — 랜딩에 온 사람은 거의 전부 아직 안 한 사람이다.
  ⛔ 그 **가정을 표에 적어** 화면이 반드시 말하게 한다(설계 §1).
- **조항 원문·읽은 날은 안 넣는다** — 두뇌 것이다(`lint_gate_leak.py` 가 지키는 선).
"""
import hashlib
import itertools
import datetime as _dt
import json
import os
import sys
import atexit
import shutil
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gates as G

_PLUGIN = Path(__file__).resolve().parent.parent
OUT = _PLUGIN / "board" / "관문셈.json"

ASK = {
    "플랫폼":   ["iPhone", "안드로이드", "웹", "스토어에 안 낸다"],
    "만드는법": ["전화기에맞게", "웹을껍데기에", "모름"],
    "계정종류": ["개인", "조직", "아직없음"],
}
ASK["기능"] = None


def _기능값(path=None):
    """🔴 **손으로 적은 목록이 낡았다** (2026-10-12 실측).

    ⚠️ 인용검사: 찾는 말이다 — 아래의 「개인정보보호법」은 **조항을 인용한 것이 아니라**
       그 관문이 왜 안 걸렸는지 «설명하는» 것이다. 조항 원문은 두뇌가 들고 있다.

    여기에 네 개가 박혀 있었다. 바로 위 줄이 ⛔ 「값 목록을 여기 지어내지 않는다」고
    적어 뒀는데 **코드가 그 주석을 어기고 있었다.** 관문 7 의 조건을 세 갈래로 고친 날
    (2026-10-12) 이 목록은 그대로여서, **설치 전 화면에서 「다른 사람과 같이 쓰기」를
    고를 수가 없었다** — 채팅·게시판 앱을 만드시는 분께 화면이 「개인정보보호법 안 걸림」을
    보냈다. 실측: 768경우 중 384가 「안 걸린다」였고 그 안에 채팅이 전부 들어 있었다.

    ⭐ **뽑는 자리는 관문 조건이다** — `data/관문.tsv` 가 「기능 has …」로 «실제로 쓰는» 값만.
       안 쓰는 기능은 답을 바꿀 수 없으므로 안 물어도 셈이 똑같다(그래서 정직하다).
    ⛔ `data/기능.tsv` 전부(11개)를 쓰지 않는다 — 경우가 86,016가지가 되고
       그중 답이 달라지는 것은 하나도 없다.
    """
    import re as _re
    src = path or (_PLUGIN / "data" / "관문.tsv")
    vals = set()
    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        col = line.split("\t")
        if len(col) < 3:
            continue
        for m in _re.finditer(r"기능 has ([^|&]+)", col[2]):
            vals.add(m.group(1).strip())
    if not vals:
        raise SystemExit("🔴 출시 절차 조건에 「기능 has …」가 하나도 없습니다 — 표를 보십시오.")
    return sorted(vals)


ASK["기능"] = _기능값()
MULTI = ("플랫폼", "기능")
ASSUMED = {"이미한것": "없음"}


def _사람말(t: str) -> str:
    """터미널 꾸밈을 걷어낸다.

    🔴 **2026-10-11, 화면을 «눈으로 보고» 알았다.** `gates.py` 의 `날수말()` 은
       터미널용이라 `**굵게**` 를 쓴다. 그것을 그대로 웹에 보냈더니 화면에
       **별표가 그대로 찍혔다** — 「`**이 방식으로는 돌려보냅니다**`」.
    ⛔ 검사도 시험도 못 잡았다. **돌려봐야 보이는 것**이었다.
    ⭐ 그래서 «보내는 자리»에서 걷어낸다 — 터미널 쪽 글은 그대로 둔다.
    """
    return t.replace("**", "").replace("⛔ ", "").strip()


홀로 = {"스토어에 안 낸다"}


def _subsets(xs):
    """여럿 고르는 축의 모든 고름. ⛔ 빈 것도 넣는다 — 「하나도 안 고름」이 있다."""
    for k in range(len(xs) + 1):
        for c in itertools.combinations(xs, k):
            골 = list(c)
            if 홀로 & set(골) and len(골) > 1:
                continue
            yield 골


def _키(ans: dict) -> str:
    """찾아보기 열쇠. ⭐ 웹이 같은 꼴로 만들 수 있게 **정렬**해 둔다."""
    parts = []
    for ax in sorted(ASK):
        v = ans[ax]
        parts.append(ax + "=" + ("·".join(sorted(v)) if isinstance(v, list) else v))
    return "|".join(parts)


_작업터 = None


def _한번쓰는_작업터() -> str:
    """경우마다 임시 폴더를 만들지 않는다 — **하나를 만들고 다시 쓴다.**

    🔴🔴 **실측 2026-10-13: 맥에 빈 임시 폴더 2,138,367개.**
       .
       전에는 이 아래 네 겹 반복문이 **경우마다** `mkdtemp()` 를 불러
       **한 번에 4,608개**를 만들고 **하나도 안 지웠다**(실측).
       그리고 턴 끝(`bin/check_touched.sh`)이 `lint_gates_web.py` 를 **매 턴** 돌리고
       그것이 `build()` 를 부른다 — **턴마다 4,608개**가 쌓였다.
    ⛔ 경우마다 **새 폴더가 필요한 이유가 없었다.** 같은 파일을 덮어 쓰면 된다.
    ⭐ 한 번 만들고 다시 쓰고, 프로그램이 끝날 때 지운다.
    ⚠️ 빈 폴더라 **크기로는 안 보인다** — 그래서 디스크를 봐도 못 찾는다. 수로만 보인다.
    """
    global _작업터
    if _작업터 is None:
        _작업터 = tempfile.mkdtemp()
        atexit.register(shutil.rmtree, _작업터, True)
    return _작업터


def build() -> dict:
    rows, n = {}, 0
    gate_list, gate_ix = [], {}
    p = os.path.join(_한번쓰는_작업터(), "l.tsv")
    축들 = sorted(ASK)
    갈래들 = [list(_subsets(ASK[a])) if a in MULTI else list(ASK[a]) for a in 축들]
    for 고름 in itertools.product(*갈래들):
                    ans = dict(zip(축들, 고름))
                    with open(p, "w", encoding="utf-8") as f:
                        for ax, v in list(ans.items()) + list(ASSUMED.items()):
                            val = "·".join(v) if isinstance(v, list) else v
                            if not val:
                                continue
                            f.write(f"2026-10-11\t앱설정\t{ax}\t{val}\t\t\n")
                    r = G.compute(p, None, 플랫폼필요=False)
                    for g in r["걸림"] + r["오늘신청"] + r["날짜없음"] + r["막힘"]:
                        if g["번호"] not in gate_ix:
                            gate_ix[g["번호"]] = len(gate_list)
                            gate_list.append({
                                "번호": g["번호"], "이름": g["이름"],
                                "최대": g["최대"], "확인": g["확인"],
                                "시작": g["시작"], "말": _사람말(G.날수말(g)),
                            })
                    rows[_키(ans)] = {
                        "안걸림": r["안걸림"],
                        "총": r["총"],
                        "걸림": [gate_ix[g["번호"]] for g in r["걸림"]],
                        "오늘신청": [gate_ix[g["번호"]] for g in
                                   r["오늘신청"] + [x for x in r["날짜없음"]
                                                 if x not in r["오늘신청"]]],
                        "막힘": [gate_ix[g["번호"]] for g in r["막힘"]],
                        "못센것": len(r["모름"]),
                    }
                    n += 1
    return {
        "이것은": "미리 계산해 둔 표입니다. 사람이 읽거나 고치는 파일이 아닙니다.",
        "고치지마십시오": "손으로 고치면 다음에 다시 만들 때 지워지고, 그 사이에는 "
                          "화면이 틀린 답을 보입니다. 검사(tools/lint_gates_web.py)가 "
                          "지문을 견주어 낡은 것을 잡습니다.",
        "짓는법": "python3 tools/gen_gates_web.py",
        "무엇에서": ["data/관문.tsv", "tools/gates.py"],
        "왜미리계산하나": "판정 규칙을 웹에 보내면 규칙이 두 곳이 되고, 한 곳이 반드시 "
                          "낡습니다. 그래서 네 축이 가질 수 있는 답을 전부 돌려 미리 "
                          "계산하고, 화면은 표를 찾아보기만 합니다 — 규칙은 "
                          "tools/gates.py 한 곳에만 있습니다.",
        "관문들": gate_list,
        "만든날": _dt.date.today().isoformat(),
        "묻는축": sorted(ASK),
        "고를수있는값": ASK,
        "여럿고르는축": list(MULTI),
        "홀로고르는값": sorted(홀로),
        "가정": {"이미한것": "없음",
                 "화면에할말": "아직 아무것도 안 하신 것으로 보고 알려 드렸습니다. "
                              "이미 하신 것이 있으면 그만큼 줄어듭니다 — "
                              "깔면 정확히 알려 드립니다."},
        "범위밖": G.범위밖,
        "경우수": n,
        "표": rows,
    }


def 지문(d: dict) -> str:
    """⭐ 만들어 낸 것의 지문 — 낡았는지 검사가 이것으로 본다."""
    core = json.dumps({k: d[k] for k in ("묻는축", "고를수있는값", "가정", "범위밖", "관문들", "표")},
                      ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(core.encode("utf-8")).hexdigest()[:16]


def 적을글(d: dict) -> str:
    """머리말은 **사람이 읽게**, 몸통(`표` 648칸)은 **한 줄로** 적는다.

    🔴 왜 이렇게 갈랐나 (2026-10-25, 재서 정했다):
      세 꼴을 다 만들어 재 봤다 — 눌러서 보내는 크기가 **4,707 · 4,570 · 4,633바이트**다.
      ⛔ 즉 **크기는 고를 근거가 못 된다**(137바이트 차이다). 이 파일의 머리에 적힌
        「더 줄이지 않는다」는 결정도 그대로 둔다.
      ⭐ 그래서 **읽는 사람** 기준으로 정했다:
        · 머리말을 펼쳐 적으면 `head` 만으로 «무엇이고 어떻게 다시 짓나»를 안다.
        · 몸통을 한 줄로 적으면 **기계 자료임이 한눈에 보인다** — 고치려 들지 않는다.
          그리고 줄 수가 8,726 → 14 로 줄어, 저장소를 훑는 사람의 눈에서 사라진다.
      ⛔ 꼴을 바꾸고 **다시 읽어 같은 값인지 확인한다** — 글자를 손으로 이어 붙이는
        자리라, 확인을 빼면 깨진 JSON 이 조용히 나간다.
    """
    머리 = {k: v for k, v in d.items() if k != "표"}
    글 = json.dumps(머리, ensure_ascii=False, indent=1)
    닫는 = 글.rstrip().rfind("}")
    글 = (글[:닫는].rstrip().rstrip(",")
          + ',\n "표": '
          + json.dumps(d["표"], ensure_ascii=False, separators=(",", ":"))
          + "\n}\n")
    if json.loads(글) != d:
        raise SystemExit("  ⛔ 적을 글을 만들다 값이 달라졌습니다 — 적지 않았습니다.")
    return 글


def main() -> int:
    d = build()
    d["지문"] = 지문(d)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(적을글(d), encoding="utf-8")
    size = OUT.stat().st_size
    import gzip
    gz = len(gzip.compress(OUT.read_bytes()))
    print(f"  · 만들었다: 경우 {d['경우수']:,}가지 · {size:,}바이트"
          f"(눌러서 보내면 **{gz:,}바이트**) · 지문 {d['지문']}")
    print(f"    {OUT}")
    print("  ⭐ 판정 규칙은 **웹에 안 보낸다** — 미리 계산한 표만 보낸다.")
    print("  ⛔ 이 표가 낡으면 턴 끝 검사가 울린다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
