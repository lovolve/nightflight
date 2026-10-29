#!/usr/bin/env python3
"""꼭 봐야 할 순간에 레드팀(개발팀 + 보안팀)을 «권하는» 글을 찍는다 — 막지 않는다.

🔴 2026-10-28 — 설계 안정성과 보안만큼은 허술하지 않게 채운다. 설계 중 꼭 봐야 할 순간과 개발에 들어가기 전에
  개발팀 + 보안팀 레드팀을 권한다. 권하기만 한다 — 까닭을 말하고, 사용자는 안 돌리고 넘어갈 수 있다.

받는 것: argv[1] = 기록 파일(ledger.tsv) · argv[2] = 때(개발 · 출시 · 기능) · argv[3] = 기능 이름(때가 «기능»일 때).
  «기능»이면 이름으로 분야(결제 · 로그인 · 개인정보 · 서버권한)를 가리고, 어느 분야도 아니면 아무것도 안 찍는다.
찍는 것: 까닭 한 줄 + 모델에게 묻는 법과 적는 법. 같은 때는 한 번만 권한다 —
  이미 답(ledger 의 «레드팀» 줄)이 있거나 권한 적이 있으면(기록 자리의 레드팀권함.tsv) 조용히 둔다.
"""
import os, sys, time

기록 = sys.argv[1] if len(sys.argv) > 1 else ""
때 = sys.argv[2] if len(sys.argv) > 2 else ""
기능 = (sys.argv[3] if len(sys.argv) > 3 else "").lower()

분야말 = {
    "결제": ("결제", "구독", "환불", "인앱", "돈받기", "payment", "billing", "subscription"),
    "로그인": ("로그인", "회원", "가입", "계정", "인증", "login", "auth", "account"),
    "개인정보": ("개인정보", "위치", "연락처", "건강", "전화번호", "주소", "생년", "location", "contact", "health"),
    "서버권한": ("서버", "권한", "관리자", "데이터베이스", "server", "admin", "permission", "database"),
}
까닭 = {
    "개발": "설계가 굳는 마지막 자리입니다. 개발에 들어가면 기능 사이 연결 · 데이터 구조를 바꾸는 값이 몇 배로 커집니다",
    "출시": "출시 뒤에는 사용자 기록과 돈이 걸려 고치기 어렵고, 보안 구멍은 그대로 사용자 피해가 됩니다",
    "결제": "돈이 오가는 기능은 한 번 틀리면 두 번 결제 · 돈 안 내고 쓰기 · 환불 다툼이 됩니다",
    "로그인": "로그인은 남의 계정에 들어가는 길이 생기기 쉬운 자리입니다",
    "개인정보": "개인정보는 한 번 새면 되돌릴 수 없고 법적 책임이 따릅니다",
    "서버권한": "서버 권한을 잘못 열면 아무나 남의 데이터를 읽거나 지울 수 있습니다",
}
if 때 == "기능":
    때 = next((k for k, ws in 분야말.items() if any(w in 기능 for w in ws)), "")
if 때 not in 까닭 or not 기록:
    sys.exit(0)

이미 = set()
for 파일, 칸번호 in ((기록, 2), (os.path.join(os.path.dirname(기록), "레드팀권함.tsv"), 1)):
    try:
        for 줄 in open(파일, encoding="utf-8", errors="replace"):
            칸 = 줄.rstrip("\n").split("\t")
            if 파일 == 기록 and (len(칸) < 3 or 칸[1] != "레드팀"):
                continue
            if len(칸) > 칸번호:
                이미.add(칸[칸번호])
    except OSError:
        pass
if 때 in 이미:
    sys.exit(0)
try:
    with open(os.path.join(os.path.dirname(기록), "레드팀권함.tsv"), "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d") + "\t" + 때 + "\n")
except OSError:
    pass

이름 = {"개발": "개발에 들어가기 전", "출시": "출시하기 전"}.get(때, "처음 " + 때 + " 기능을 넣을 때")
print("  · 레드팀 권함 — " + 이름 + ": " + 까닭[때] + ".")
print("    [모델] 사용자에게 위 까닭을 한두 줄로 말하고 «개발팀과 보안팀으로 레드팀을 돌려 볼까요? 건너뛰셔도 됩니다»라고 물으십시오. 막지 않습니다.")
print("    [모델] 돌리자고 하시면 «레드팀» 스킬대로 하고 ledger.sh 레드팀 돌림 " + 때 + " \"<찾은 것 요약>\" · 건너뛰자고 하시면 ledger.sh 레드팀 넘김 " + 때 + " 으로 적으십시오.")
