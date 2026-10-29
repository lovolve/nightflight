#!/usr/bin/env python3
"""상태 — 「이 기능이 가질 수 있는 상태와 다음에 갈 수 있는 곳」




`dependencies.py`(영향)는 **기능 ↔ 기능**을 본다 — 「둘이 같은 것을 들고 있다」·
「이것이 먼저다」·「한 화면에 있다」. 그건 **짝**이다.
상태는 **기능 하나 안**의 일이다 — 짝이 아니라 **자기 안의 길**이다.

⭐ 둘은 같은 집안이다: 영향의 「순서가있다」는 대개 **상태 조건**이다
  (「A가 먼저」 = 「A가 «끝남» 이어야」). 그래서 쓰는 칸 모양을 같게 맞췄고,
  이름도 **같은 자리**(기록의 «주제» 낱말)에서 받는다.
⛔ 그런데 **한 모듈에 합치지 않았다** — 영향은 짝이라 두 이름이 필요하고
  상태는 하나로 충분하다. 합치면 한쪽 칸이 늘 비어서 「안 적었다」와 구별이 안 된다.


| 그 기능에 적힌 상태가 | |
|---|---|
| **있다** | ⭐ 막다른 곳·못 닿는 곳을 **말할 수 있다** |
| **없다** | ⛔ 「상태가 없는 기능」이 **아니다.** 「**아직 안 적었다**」다 |

🔴 이 저장소가 **다섯 번** 겪은 「0 이 안전처럼 보이는」 병이고, 영향 지도가
   같은 자리에 같은 못을 박아 뒀다. 그래서 여기서도 **「상태가 단순합니다」 같은 말을
   아예 만들지 않는다.**


이걸 안 잡으면 적어 둘 이유가 없다. 넷 다 **비개발자가 실제로 당하는** 모양이다.

| 잡는 것 | 사람 말 | 왜 나쁜가 |
|---|---|---|
| **막다른 상태** | 「여기 가면 나올 길이 없습니다」 | 결제가 실패했는데 **다시 해 볼 길이 없다** |
| **못 닿는 상태** | 「여기로 들어오는 길이 없습니다」 | 적어 뒀지만 **아무도 그 상태가 안 된다** |
| **없는 곳으로 간다** | 「적지 않은 곳으로 갑니다」 | 오타이거나 **빠뜨린 상태**다 |
| **처음이 여럿** | 「시작하는 자리가 둘 이상입니다」 | 어디서 시작하는지 **아무도 모른다** |

⛔ 「막다른 상태」와 「끝」을 **가른다** — 끝나는 것이 맞는 자리는 갈 곳에 «끝»을
  적게 했다(`ledger.sh 상태`가 빈 칸을 거절한다). 빈 칸을 「끝」으로 읽으면
  **안 적은 것이 괜찮은 것으로** 보인다.

사용:  STATE=<장부> [NFONE=<기능>] python3 states.py
       python3 states.py  (장부는 _root 가 찾는다)
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _root

끝말 = "끝"
미정말 = "아직안정함"


def 읽는다(ledger=None) -> dict:
    """장부에서 상태 줄을 모은다.

    칸: 날짜 · 상태 · 상태이름 · 출처 · 갈수있는곳(쉼표) · 기능
    ⛔ `영향` 과 **같은 칸 수**다 — 한쪽만 바뀌면 둘 다 낡는다.
    """
    p = Path(ledger) if ledger else _root.ledger()
    if not p.is_file():
        return {"못쟀다": True, "기능별": {}, "적힌줄": 0, "내판단": 0}

    기능별, 줄수, 내판단 = {}, 0, 0
    for line in p.read_text(encoding="utf-8").splitlines():
        c = line.rstrip("\n").split("\t")
        if len(c) < 6 or c[1] != "상태":
            continue
        날, 이름, 출처, 갈곳, 기능 = c[0], c[2].strip(), c[3].strip(), c[4].strip(), c[5].strip()
        if not 이름 or not 기능:
            continue
        줄수 += 1
        if 출처 == "내판단":
            내판단 += 1
        갈 = [x.strip() for x in 갈곳.split(",") if x.strip()]
        기능별.setdefault(기능, {})[이름] = {"갈곳": 갈, "출처": 출처, "날": 날}
    return {"못쟀다": False, "기능별": 기능별, "적힌줄": 줄수, "내판단": 내판단}


def 본다(기능별: dict) -> dict:
    """기능마다 네 가지를 찾는다. ⛔ 넷 다 **못 찾았으면 「없다」가 아니다**(머리글)."""
    out = {}
    for 기능, 상태들 in 기능별.items():
        이름들 = set(상태들)
        막다른, 없는곳, 닿는곳 = [], [], set()
        for 이름, v in 상태들.items():
            갈 = v["갈곳"]
            if 갈 == [끝말] or 갈 == [미정말]:
                pass
            elif not [x for x in 갈 if x not in (끝말, 미정말)]:
                막다른.append(이름)
            for x in 갈:
                if x in (끝말, 미정말):
                    continue
                if x not in 이름들:
                    없는곳.append([이름, x])
                else:
                    닿는곳.add(x)
        처음 = sorted(이름들 - 닿는곳)
        out[기능] = {
            "상태수": len(이름들),
            "막다른": sorted(막다른),
            "없는곳": 없는곳,
            "처음": 처음,
            "끝있나": any(끝말 in v["갈곳"] for v in 상태들.values()),
            "아직안정함": sorted(k for k, v in 상태들.items() if 미정말 in v["갈곳"]),
            "상태들": {k: v["갈곳"] for k, v in 상태들.items()},
            "내판단": sorted(k for k, v in 상태들.items() if v["출처"] == "내판단"),
        }
    return out


def compute(ledger=None) -> dict:
    d = 읽는다(ledger)
    if d["못쟀다"]:
        return d
    d["기능별본것"] = 본다(d["기능별"])
    d["걸림수"] = sum(len(v["막다른"]) + len(v["없는곳"]) + (1 if len(v["처음"]) > 1 else 0)
                    for v in d["기능별본것"].values())
    return d


def main() -> int:
    d = compute(os.environ.get("STATE") or None)
    하나 = (os.environ.get("NFONE") or "").strip()
    if d["못쟀다"]:
        print("   아직 기록이 없습니다 — 적힌 상태가 없습니다.")
        print("   (고장이 아닙니다. 상태를 적으면 여기가 채워집니다.)")
        return 0
    본것 = d["기능별본것"]
    if 하나:
        본것 = {k: v for k, v in 본것.items() if k == 하나}
        if not 본것:
            print(f"   「{하나}」에 적힌 상태가 없습니다.")
            print("   ⚠️ 이건 「상태가 없다」가 아니라 «아직 안 적었다»입니다.")
            return 0
    if not 본것:
        print("   적힌 상태가 없습니다.")
        print("   ⚠️ 이건 「상태가 없다」가 아니라 «아직 안 적었다»입니다.")
        return 0

    print()
    print("── 기능마다 갈 수 있는 곳 ──────────────────────")
    print("   (지금 어느 상태인지와 다음에 갈 수 있는 곳을 정해 둔 것)")
    print()
    걸림 = 0
    for 기능 in sorted(본것):
        v = 본것[기능]
        print(f"  ■ {기능}  — 상태 {v['상태수']}가지")
        for 이름 in sorted(v["상태들"]):
            갈 = v["상태들"][이름]
            꼬리 = " · ".join(갈) if 갈 else "(안 적음)"
            표 = "  ⛔" if 이름 in v["막다른"] else "    "
            print(f"{표}   {이름} → {꼬리}")
        if v["처음"]:
            if len(v["처음"]) == 1:
                print(f"       시작하는 자리: {v['처음'][0]}")
            else:
                걸림 += 1
                print(f"  ⛔   시작하는 자리가 {len(v['처음'])}곳입니다: {' · '.join(v['처음'])}")
                print("         어디서 시작하는지 알 수 없습니다 — 하나로 정해 주십시오.")
        for 이름 in v["막다른"]:
            걸림 += 1
            print(f"  ⛔   「{이름}」에 가면 나올 길이 없습니다.")
            print("         여기서 끝나는 것이 맞으면 갈 곳에 «끝»을 적어 주십시오.")
        for 이름, x in v["없는곳"]:
            걸림 += 1
            print(f"  ⛔   「{이름}」이 적지 않은 곳(「{x}」)으로 갑니다.")
            print("         오타이거나 빠뜨린 상태입니다.")
        for 이름 in v["아직안정함"]:
            print(f"  ⚠️   「{이름}」 다음은 **아직 안 정했습니다** — 직접 정하실 자리입니다.")
            print("         ⛔ 빠뜨린 것이 아닙니다. 정하시면 그때 적습니다.")
        if v["내판단"]:
            print(f"       ⚠️ 제가 정한 상태 {len(v['내판단'])}가지: {' · '.join(v['내판단'])}")
        print()

    미정 = sum(len(v["아직안정함"]) for v in 본것.values())
    print(f"  적힌 줄 {d['적힌줄']} · 봐야 할 곳 {걸림}"
          + (f" · 아직 안 정한 곳 {미정}" if 미정 else ""))
    if not 걸림:
        print("  ⚠️ 봐야 할 곳이 0 이라는 것은 «적힌 것 안에서» 0 입니다 —")
        print("     「상태가 괜찮다」가 아니라 「적힌 것에는 걸리는 데가 없다」입니다.")
    if d["내판단"]:
        print(f"  ⚠️ 그중 {d['내판단']}줄은 **제가 정한 것**입니다 — 확인이 필요합니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
