#!/usr/bin/env python3
"""사용자 집 폴더 · 서버 주소의 주인 — 파이썬 쪽은 여기 하나에서 읽는다."""
from __future__ import annotations

import os
import re
from pathlib import Path

서버 = "https://tmrivrgrtgsjevikwagr.supabase.co"
유료열림 = False
결제주소 = "https://nightflight.lovolve.app/account/"
대기주소 = "https://nightflight.lovolve.app/wait/?for=paid"


def 결제말(en: bool = False) -> str:
    if 유료열림:
        return ("Buy on your account page: " + 결제주소) if en else ("결제하는 곳(내 계정 화면): " + 결제주소)
    return ("Paid plans are coming soon. Get notified when they open: " + 대기주소 + "&lang=en") if en else ("유료 플랜은 준비 중입니다. 열리면 알림 받기: " + 대기주소)


def 결제지시(en: bool = False) -> str:
    if 유료열림:
        return "[모델] 결제는 내 계정 화면에서 합니다 — 이 주소를 사용자에게 전하십시오: " + 결제주소 + ("?lang=en" if en else "")
    return "[모델] 유료 플랜은 준비 중이라고 알리고, 열리면 알림을 받는 대기 명단 주소를 전하십시오: " + 대기주소 + ("&lang=en" if en else "") + " — 결제 주소는 전하지 마십시오."

_플러그인 = Path(__file__).resolve().parent.parent


def 사람집() -> Path:
    return Path(os.environ.get("HOME") or Path.home())


def 집() -> Path:
    기본 = 사람집() / ".nightflight"
    v = os.environ.get("NIGHTFLIGHT_HOME") or ""
    if not v or not v.startswith("/"):
        return 기본
    p = Path(v)
    try:
        if p.exists() and p.stat().st_uid != os.getuid():
            return 기본
    except OSError:
        return 기본
    return p


def 개발() -> bool:
    return (_플러그인 / ".nightflight-dev").is_file()


def 주소허용(u: str) -> bool:
    if not isinstance(u, str):
        return False
    if u.startswith("https://"):
        pass
    elif u.startswith("http://"):
        if not 개발():
            return False
    else:
        return False
    h = u.split("://", 1)[1]
    for 끝 in ("/", "?", "#"):
        h = h.split(끝, 1)[0]
    h = h.lower()
    if not h or re.search(r"[^a-z0-9.:-]", h):
        return False
    if h in ("127.0.0.1", "localhost") or h.startswith(("127.0.0.1:", "localhost:")):
        return 개발()
    if h == 서버.split("://", 1)[1].lower():
        return True
    if h.endswith(".supabase.co"):
        return 개발()
    return False


def 서버주소() -> str:
    v = os.environ.get("NF_BRAIN_BASE") or ""
    return v.rstrip("/") if v and 주소허용(v) else 서버
