#!/usr/bin/env python3
"""서버의 표·함수 모양을 읽어 «무엇이 있나»를 적는다 — `두뇌.sh` 의 몸.

⭐ `bin/두뇌.sh` 가 부른다. 받는 것은 그 셸이 넘기는 환경변수(와 선 글)다.
⛔ **`-I` 로 부른다** — 받는 분 폴더에 `json.py` 가 심겨 있어도 파이썬의 것을 읽는다
  (`tools/lint_python_isolated.py` 가 그것을 본다).

🔴 **왜 파일로 빼냈나** (2026-10-25, ):
   전에는 이 90줄이 셸 파일 안에 들어 있었다.
   ⛔ 그 자리에는 **아무 도구도 닿지 않는다** — 린터·형식 검사·시험이 다 비껴간다.
   ⛔ 어디서 틀렸는지도 셸 줄 번호로만 나와, 수천 줄 파일에서 사람이 찾지 못한다.
   ⛔ `-c` 꼴이면 **파이썬 코드에 홑따옴표를 한 글자도 쓸 수 없다**(셸이 그것으로 감싼다).
   ⭐ 파일로 빼면 그 뒤로는 **도구가 대신 잡는다.**
"""
import json, os, sys


def 흔적(결과, 남은="", 하루=""):
    """⛔ 가지가 셋이라 **가른 자리에서** 적는다 — 셸에서 또 가르면 한쪽이 낡는다."""
    길 = os.environ.get("NF_TRACE", "")
    if not 길:
        return
    try:
        os.makedirs(os.path.dirname(길), exist_ok=True)
        with open(길, "a", encoding="utf-8") as f:
            from datetime import datetime
            f.write("\t".join([datetime.now().strftime("%Y-%m-%d %H:%M"),
                               os.environ.get("NF_STAGE_ARG", ""),
                               os.environ.get("NF_KIND_ARG", ""),
                               결과, str(남은), str(하루)]) + "\n")
    except OSError:
        pass


try:
    d = json.loads(sys.stdin.read() if sys.argv[1:] in ([], ["-"]) else sys.argv[1])
except Exception:
    print("야간비행의 답을 읽지 못했습니다. 받지 못한 것으로 적어 둡니다.")
    흔적("못읽음")
    raise SystemExit(0)

if d.get("내려줌"):
    print(d.get("본문", ""))
    남은 = d.get("남은몫")
    흔적("내려옴", "" if 남은 is None else 남은,
         "" if d.get("하루몫") is None else d.get("하루몫"))
    if 남은 is not None:
        print()
        print(f"— 오늘 남은 몫 {남은}번")
    if d.get("무료앱등록"):
        print()
        print("— 이 제품이 이 컴퓨터의 무료 제품으로 등록됐습니다. 플랜이 없거나 구독이 끝나도 이 제품은 계속 쓰실 수 있습니다.")
elif d.get("이_단계에_있는_갈래"):
    흔적("없는갈래")
    print("그 갈래는 없습니다. 이 단계에서 물을 수 있는 것:")
    for g in d["이_단계에_있는_갈래"]:
        print(f"  · {g}")
else:
    기본 = "We cannot provide this right now." if os.environ.get("NF_LANG_NOW") == "en" else "지금은 받을 수 없습니다."
    말 = (d.get("왜_en") or d.get("왜")) if os.environ.get("NF_LANG_NOW") == "en" else d.get("왜")
    print(말 or 기본)
    print()
    코드 = d.get("거절코드")
    흔적("거절:" + (코드 or "모름"))
    if d.get("메일확인필요") is True and 코드 != "메일확인필요":
        print("[모델] 먼저 권하십시오: «아직 메일 확인을 안 하셔서 무료 제품 1개가 비어 있습니다. 메일 주소를 알려 주시면 확인 코드를 보내 드립니다. 확인하시면 이 제품을 무료로 쓰실 수 있습니다.» 사용자가 메일 주소를 말하면 printf '%s\\n' <메일> | 열쇠.sh 무료메일 로 보내고 돌아온 말을 그대로 전하십시오. 사용자가 메일로 받은 여섯 자리 코드를 말하면 printf '%s\\n' <코드> | 열쇠.sh 무료코드 로 넣으십시오.")
    if 코드 == "앱칸참":
        print("유료 제품등록: " + " · ".join(a + ("(앱 번호를 못 읽은 프로젝트들)" if a == "no-bundle-id" else "") for a in (d.get("앱들") or [])))
        print("플러스 플랜으로 바꾸시거나, 설계를 시작하고 7일이 안 된 제품의 제품등록을 푸시면 이 제품에도 적용됩니다(7일이 지난 제품은 풀어도 제품등록이 돌아오지 않습니다).")
        print("[모델] 빼려면 사용자가 고른 제품으로 열쇠.sh 앱빼기 <제품 번호> (사용자 답을 들은 뒤에만)")
        print("플러스 플랜(제품등록 15개 — 무료 1 + 유료 14)으로 바꾸시면 이 제품에도 바로 적용됩니다.")
        print("[모델] 바꾸려면 printf '%s\\n' <키> | 열쇠.sh 등급 플러스 - (결제한 메일로 확인 링크가 갑니다) · 플랜 안내 주소를 사용자에게 전하십시오: https://www.lovolve.app/nightflight/#price")
    elif 코드 == "다시넣기기다림":
        날 = str(d.get("다시넣는날") or "")[:10]
        바로 = str(d.get("바로다시되는날") or "")[:10]
        if 날:
            print("이 제품을 다시 넣으실 수 있는 날: " + 날)
        if 바로:
            print("한 달 한 번 바로 다시 넣기를 다시 쓰실 수 있는 날: " + 바로)
    elif 코드 == "메일확인필요":
        print("[모델] 사용자가 메일 주소를 말하면 printf '%s\\n' <메일> | 열쇠.sh 무료메일 로 보내고 돌아온 말을 그대로 전하십시오. 사용자가 메일로 받은 여섯 자리 코드를 말하면 printf '%s\\n' <코드> | 열쇠.sh 무료코드 로 넣으십시오. 결제한 메일이면 그 플랜이 켜집니다.")
    elif 코드 == "너무잦음":
        pass
    else:
        if 코드 == "미결제" and d.get("무료앱"):
            print("이 컴퓨터의 무료 제품: " + str(d.get("무료앱")))
        if 코드 in ("미결제", "만료"):
            print("[모델] 플랜 안내 주소를 사용자에게 전하십시오: https://www.lovolve.app/nightflight/#price")
        print(os.environ.get("KEYLINE_EXPIRED" if 코드 == "만료" else "KEYLINE_DEFAULT", ""))
        print("[모델] 사용자가 결제한 메일 주소를 말하면 printf '%s\\n' <메일> | 열쇠.sh 무료메일 로 보내고, 메일로 받은 여섯 자리 코드를 말하면 printf '%s\\n' <코드> | 열쇠.sh 무료코드 로 넣으십시오. 돌아온 말을 그대로 전하십시오.")
