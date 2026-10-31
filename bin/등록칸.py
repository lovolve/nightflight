#!/usr/bin/env python3
"""`ledger.sh 등록` 이 부른다 — 서버에서 읽은 이용권 칸(JSON)을 보고 등록할 때 알려 드릴 말을 찍는다.

받는 것: 환경값 KAN(서버 답 · `열쇠.sh 칸읽기`) · BID(이 제품 번호) · KEYSH(열쇠.sh 자리).
2026-10-27: 제품등록은 설계 단계부터다(등록은 막지 않는다) · 모자라면 미리 알리고 플랜 안내 주소를 준다.
"""
import json, os
주소 = "https://www.lovolve.app/nightflight/#price"
열쇠 = os.environ["KEYSH"]
try:
    d = json.loads(os.environ.get("KAN") or "")
except ValueError:
    d = None
bid = os.environ.get("BID") or ""
번호없음 = ("(번호없음)", "no-bundle-id")
def 보임(b):
    return "앱 번호를 못 읽은 제품" if b in 번호없음 else b
if not isinstance(d, dict):
    print("  플랜의 제품등록은 지금 확인하지 못했습니다 — 아이디어 · 검증 단계는 그대로 쓰실 수 있습니다.")
else:
    무료 = d.get("무료앱")
    칸, 앱들 = (d.get("칸수"), d.get("앱들") or []) if d.get("있나") else (None, [])
    접은 = (d.get("접은제품") or []) if d.get("있나") else []
    if bid and (bid == 무료 or bid in 앱들):
        print("  이 제품은 이미 제품등록돼 있습니다(" + ("무료 제품" if bid == 무료 else "플랜") + ").")
    elif not 무료 and d.get("메일확인") is not True:
        print("  무료 제품을 쓰시려면 처음 한 번 메일 확인이 필요합니다(컴퓨터 한 대에 1개). 메일 주소를 알려 주시면 여섯 자리 확인 코드를 보내 드립니다.")
        print("  [모델] 사용자가 메일 주소를 말하면 printf '%s\\n' <메일> | " + 열쇠 + " 무료메일 · 메일로 받은 코드를 말하면 printf '%s\\n' <코드> | " + 열쇠 + " 무료코드")
    elif not 무료:
        print("  설계 단계에 들어가면 이 제품이 이 컴퓨터의 무료 제품으로 제품등록됩니다(컴퓨터 한 대에 1개 · 플랜과 상관없이 계속).")
    elif not d.get("있나"):
        print("  ⚠️ 이 컴퓨터의 무료 제품은 이미 «%s» 입니다(컴퓨터 한 대에 1개)." % 보임(무료))
        print("     아이디어 · 검증 단계는 그대로 쓰실 수 있고, 설계 단계부터는 이 제품에 이용권이 필요합니다. 플랜 안내: " + 주소)
    elif 칸 is not None and len(앱들) + len(접은) >= int(칸):
        print("  ⚠️ 플랜의 제품등록 %d개를 이미 다 쓰셨습니다(무료 제품 %s · 유료 %s)." % (int(칸) + 1, 보임(무료), ", ".join([보임(a) for a in 앱들] + [보임(a) + "(접음)" for a in 접은])))
        print("     아이디어 · 검증 단계는 그대로 쓰실 수 있습니다. 제품등록은 설계 단계부터라, 그때 이 제품도 1개가 됩니다.")
        print("     플러스 플랜으로 바꾸시거나, 다른 제품의 제품등록을 푸시면 그 자리가 바로 돌아옵니다(같은 제품을 다시 넣는 것은 30일 뒤입니다). 플랜 안내: " + 주소)
        print("  [모델] 풀려면 사용자가 고른 제품으로 " + 열쇠 + " 앱빼기 <제품 번호> 확인 · 플러스로 바꾸려면 " + 열쇠 + " 등급 플러스 (라이선스 키는 필요 없습니다 · 결제한 메일로 확인 링크가 갑니다)")
    else:
        남 = "제한 없음" if 칸 is None else "%d개 중 %d개 사용 중(무료 1 + 유료 %d/%d)" % (int(칸) + 1, len(앱들) + len(접은) + 1, len(앱들) + len(접은), int(칸))
        print("  플랜의 제품등록: " + 남 + " — 설계 단계에 들어가면 이 제품도 1개가 됩니다.")

목록 = {}
try:
    for 줄 in open(os.environ.get("PERSON") or "/nonexistent", encoding="utf-8", errors="replace"):
        칸들 = 줄.rstrip("\n").split("\t")
        if len(칸들) > 3 and 칸들[1] == "프로젝트" and os.path.isdir(칸들[2]):
            목록[칸들[2]] = 칸들[3]
except OSError:
    pass
if 목록:
    쓰는 = (set(d.get("앱들") or []) if d.get("있나") else set()) | ({d.get("무료앱")} if d.get("무료앱") else set()) if isinstance(d, dict) else set()
    칸씀 = [p for p, b in 목록.items() if b and b in 쓰는]
    print("  이 컴퓨터에 등록한 프로젝트 %d개 — 제품등록(설계 단계 이상) %d개 · 아이디어 · 검증 중 %d개." % (len(목록), len(칸씀), len(목록) - len(칸씀)))
