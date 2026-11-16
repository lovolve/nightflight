#!/usr/bin/env python3
"""상태 — 「이 기능이 가질 수 있는 상태와 다음에 갈 수 있는 곳」"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _root

끝말 = "끝"
미정말 = "아직안정함"


def 읽는다(ledger=None) -> dict:
    p = Path(ledger) if ledger else _root.ledger()
    if not p.is_file():
        return {"못쟀다": True, "기능별": {}, "적힌줄": 0, "내판단": 0}

    기능별, 줄수, 내판단, 설명들 = {}, 0, 0, {}
    for line in p.read_text(encoding="utf-8").splitlines():
        c = line.rstrip("\n").split("\t")
        if len(c) > 3 and c[1] == "상태설명":
            설명들[c[2].strip()] = c[3].strip()
            continue
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
    return {"못쟀다": False, "기능별": 기능별, "적힌줄": 줄수, "내판단": 내판단, "설명들": 설명들}


def 본다(기능별: dict) -> dict:
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
        실패출구없음 = sorted(이름 for 이름, v in 상태들.items()
                         if (이름.rstrip().endswith("중") or "기다" in 이름 or 이름.rstrip().endswith(" 대기"))
                         and not 이름.startswith("쉬는")
                         and 미정말 not in v["갈곳"]
                         and 끝말 not in v["갈곳"] and len([x for x in v["갈곳"] if x not in (끝말, 미정말)]) == 1)
        out[기능] = {
            "실패출구없음": 실패출구없음,
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
    for 기능, 글 in (d.get("설명들") or {}).items():
        if 기능 in d["기능별본것"]:
            d["기능별본것"][기능]["설명"] = 글
    d["걸림수"] = sum(len(v["막다른"]) + len(v["없는곳"]) + len(v["실패출구없음"]) + (1 if len(v["처음"]) > 1 else 0)
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
        for 이름 in v["실패출구없음"]:
            걸림 += 1
            print(f"  ⛔   「{이름}」에서 나가는 길이 하나뿐입니다 — 실패하거나 취소할 때 갈 곳이 없습니다.")
            print("         실패 · 취소 · 다시 시도 중 맞는 것을 갈 곳에 더해 주십시오. 실패할 일이 없는 상태면 갈 곳에 «끝»도 적어 머무는 자리로 밝혀 주십시오.")
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
