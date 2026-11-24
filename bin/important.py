#!/usr/bin/env python3
"""야간비행 도구"""
import sys

분야말 = {
    "결제": ("결제", "구독", "환불", "인앱", "돈받기", "이용권", "payment", "billing", "subscription", "refund", "purchase"),
    "로그인": ("로그인", "회원", "가입", "계정", "인증", "login", "auth", "account"),
    "개인정보": ("개인정보", "위치", "연락처", "건강", "전화번호", "주소", "생년", "location", "contact", "health", "privacy"),
    "서버권한": ("서버", "권한", "관리자", "데이터베이스", "server", "admin", "permission", "database"),
}


def 이름분야(기능: str) -> str:
    t = (기능 or "").lower()
    return next((k for k, ws in 분야말.items() if any(w in t for w in ws)), "")


def 지정목록(기록: str) -> set:
    out = set()
    try:
        for 줄 in open(기록, encoding="utf-8", errors="replace"):
            c = 줄.rstrip("\n").split("\t")
            if len(c) > 2 and c[1] == "중요기능":
                out.add(c[2])
            elif len(c) > 2 and c[1] == "중요기능뺌":
                out.discard(c[2])
    except OSError:
        pass
    return out


def 분야(기능: str, 기록: str = "") -> str:
    if 기록 and 기능 in 지정목록(기록):
        return "지정"
    return 이름분야(기능)


if __name__ == "__main__":
    v = 분야(sys.argv[1] if len(sys.argv) > 1 else "", sys.argv[2] if len(sys.argv) > 2 else "")
    if v:
        print(v)
    sys.exit(0 if v else 1)
