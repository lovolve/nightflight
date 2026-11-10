#!/usr/bin/env python3
"""서버의 표·함수 모양을 읽어 «무엇이 있나»를 적는다 — `brain.sh` 의 몸."""
import json
from pathlib import Path
import re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import product_name


def 흔적(결과, 남은="", 하루=""):
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

def 새이름(글):
    if not isinstance(글, str) or not 글:
        return 글
    try:
        쌍 = []
        for 줄 in (Path(__file__).resolve().parent.parent / "data" / "legacy_names.tsv").read_text(encoding="utf-8").splitlines():
            if "\t" in 줄 and not 줄.startswith("#"):
                a, b = 줄.split("\t", 1)
                쌍.append((a, b))
                쌍.append((a.rsplit("/", 1)[-1], b.rsplit("/", 1)[-1]))
    except OSError:
        return 글
    for a, b in sorted(set(쌍), key=lambda x: -len(x[0])):
        글 = re.sub(r"(?<![가-힣A-Za-z0-9_])" + re.escape(a) + r"(?![가-힣A-Za-z0-9_])", b, 글)
    return 글


if d.get("내려줌"):
    print(새이름(d.get("본문", "")))
    남은 = d.get("남은몫")
    흔적("내려옴", "" if 남은 is None else 남은,
         "" if d.get("하루몫") is None else d.get("하루몫"))
    if 남은 is not None:
        print()
        print(f"— 오늘 남은 몫 {남은}번")
    if d.get("무료앱등록"):
        print()
        print("— 이 제품이 이 컴퓨터의 무료 제품으로 등록됐습니다. 이 컴퓨터의 무료 1년 동안 쓰실 수 있습니다.")
elif d.get("이_단계에_있는_갈래"):
    흔적("없는갈래")
    print("그 갈래는 없습니다. 이 단계에서 물을 수 있는 것:")
    for g in d["이_단계에_있는_갈래"]:
        print(f"  · {g}")
else:
    기본 = "We cannot provide this right now." if os.environ.get("NF_LANG_NOW") == "en" else "지금은 받을 수 없습니다."
    말 = (d.get("왜_en") or d.get("왜")) if os.environ.get("NF_LANG_NOW") == "en" else d.get("왜")
    print(새이름(말 or 기본))
    print()
    코드 = d.get("거절코드")
    if not 코드:
        흔적("서버오류")
        print("[모델] 서버 문제입니다. 사용자 잘못이나 결제 문제로 말하지 말고, 안내 없이 작업을 이어 가십시오.")
        raise SystemExit(0)
    흔적("거절:" + 코드)
    if 코드 == "앱칸참":
        _표 = product_name.목록()
        print("유료 제품등록: " + " · ".join(product_name.보임(a, _표) for a in (d.get("앱들") or [])))
        플러스 = d.get("등급") == "헤비"
        if 플러스:
            print("다른 제품의 제품등록을 푸시면 그 자리가 바로 돌아옵니다(같은 제품을 다시 넣는 것은 30일 뒤입니다).")
        else:
            print("플러스 플랜으로 바꾸시거나, 다른 제품의 제품등록을 푸시면 그 자리가 바로 돌아옵니다(같은 제품을 다시 넣는 것은 30일 뒤입니다).")
        print("[모델] 괄호 안이 제품 번호입니다. 빼려면 사용자가 고른 제품으로 license_key.sh 앱빼기 <제품 번호> (사용자 답을 들은 뒤에만)")
        if not 플러스:
            print("플러스 플랜(제품등록 15개 — 무료 1 + 유료 14)으로 바꾸시면 이 제품에도 바로 적용됩니다.")
            print("[모델] 바꾸려면 license_key.sh 등급 플러스 (라이선스 키는 필요 없습니다 · 결제한 메일로 확인 링크가 갑니다) · 플랜 안내 주소를 사용자에게 전하십시오: https://www.lovolve.app/nightflight/#price")
    elif 코드 == "다시넣기기다림":
        날 = str(d.get("다시넣는날") or "")[:10]
        바로 = str(d.get("바로다시되는날") or "")[:10]
        if 날:
            print("이 제품을 다시 넣으실 수 있는 날: " + 날)
        if 바로:
            print("한 달 한 번 바로 다시 넣기를 다시 쓰실 수 있는 날: " + 바로)
    elif 코드 in ("새컴퓨터몰림", "컴퓨터확인못함"):
        pass
    elif 코드 == "다시켜기":
        print("[모델] 사용자가 결제한 메일 주소를 말하면 printf '%s\\n' <메일> | license_key.sh 무료메일 로 보내고, 메일로 받은 여섯 자리 코드를 말하면 printf '%s\\n' <코드> | license_key.sh 무료코드 로 넣으십시오.")
    elif 코드 in ("무료기간끝", "무료끝유료필요"):
        print("[모델] 플랜 안내 주소를 사용자에게 전하십시오: https://www.lovolve.app/nightflight/#price")
    elif 코드 == "메일확인필요":
        print("[모델] 사용자가 메일 주소를 말하면 printf '%s\\n' <메일> | license_key.sh 무료메일 로 보내고 돌아온 말을 그대로 전하십시오. 사용자가 메일로 받은 여섯 자리 코드를 말하면 printf '%s\\n' <코드> | license_key.sh 무료코드 로 넣으십시오. 결제한 메일이면 그 플랜이 켜집니다.")
    elif 코드 in ("너무잦음", "하루한도"):
        pass
    else:
        if 코드 == "미결제" and d.get("무료앱"):
            print("이 컴퓨터의 무료 제품: " + str(d.get("무료앱")))
        if 코드 in ("미결제", "만료"):
            print("[모델] 플랜 안내 주소를 사용자에게 전하십시오: https://www.lovolve.app/nightflight/#price")
        print(os.environ.get("KEYLINE_EXPIRED" if 코드 == "만료" else "KEYLINE_DEFAULT", ""))
        print("[모델] 사용자가 결제한 메일 주소를 말하면 printf '%s\\n' <메일> | license_key.sh 무료메일 로 보내고, 메일로 받은 여섯 자리 코드를 말하면 printf '%s\\n' <코드> | license_key.sh 무료코드 로 넣으십시오. 돌아온 말을 그대로 전하십시오.")
