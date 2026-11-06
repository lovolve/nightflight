#!/usr/bin/env python3
"""야간비행 도구"""
import json, os, sys, time
import datetime as _dt


def _한국날(v):
    try:
        t = _dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return (t + _dt.timedelta(hours=9)).strftime("%Y-%m-%d") if t.tzinfo else str(v)[:10]
    except (ValueError, TypeError):
        return None

집 = os.environ.get("NF_HOME") or os.path.expanduser("~/.nightflight")
지금 = os.path.realpath(sys.argv[1]) if len(sys.argv) > 1 else ""

def 기록자리(root):
    if os.path.isdir(os.path.join(root, ".nightflight")):
        return os.path.join(root, ".nightflight")
    if os.path.isfile(os.path.join(root, ".claude", "ledger.tsv")):
        return os.path.join(root, ".claude")
    return None

def 단계(root):
    st = 기록자리(root)
    v = None
    try:
        for 줄 in open(os.path.join(st, "ledger.tsv"), encoding="utf-8", errors="replace"):
            칸 = 줄.rstrip("\n").split("\t")
            if len(칸) > 2 and 칸[1] == "단계":
                v = 칸[2]
    except (OSError, TypeError):
        pass
    return v

단계들 = "진단 기획 검증 설계 개발 테스트 출시 수정 출시후".split()
def 단계번호(v):
    for i in range(len(단계들) - 1, -1, -1):
        if v and 단계들[i] in v.replace("5. 확인", "5. 테스트").replace("5-확인", "5-테스트"):
            return i
    return None

def 앱이름(root):
    try:
        n = json.load(open(os.path.join(기록자리(root), "board", "now.json"), encoding="utf-8")).get("앱이름")
        if isinstance(n, str) and n.strip():
            return n.strip()
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return os.path.basename(root)

권, 받은때 = None, None
try:
    p = os.path.join(집, "이용권.json")
    권 = json.load(open(p, encoding="utf-8"))
    받은때 = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(p)))
except (OSError, ValueError):
    pass
if not isinstance(권, dict):
    권 = None

목록 = {}
try:
    for 줄 in open(os.path.join(집, "사람.tsv"), encoding="utf-8", errors="replace"):
        칸 = 줄.rstrip("\n").split("\t")
        if len(칸) > 3 and 칸[1] == "프로젝트" and 칸[2] and os.path.isdir(칸[2]) and 기록자리(칸[2]):
            목록[os.path.realpath(칸[2])] = 칸[3]
except OSError:
    pass

있나 = bool(권 and 권.get("있나"))
앱들 = [str(x) for x in (권.get("앱들") or [])] if 있나 else []
접은 = [str(x) for x in (권.get("접은제품") or [])] if 있나 else []
무료 = 권.get("무료앱") if 권 else None
번호없음 = ("(번호없음)", "no-bundle-id")
프로젝트 = []
for root, 번들 in 목록.items():
    n = 단계번호(단계(root))
    키 = 번들 or ("(번호없음)" if 무료 in 번호없음 or any(x in 앱들 + 접은 for x in 번호없음) else "")
    if 키 and (키 == 무료 or (not 번들 and 무료 in 번호없음)):
        구분 = "무료"
    elif 키 and (키 in 앱들 or (not 번들 and any(x in 앱들 for x in 번호없음))):
        구분 = "플랜"
    elif 키 and (키 in 접은 or (not 번들 and any(x in 접은 for x in 번호없음))):
        구분 = "접음"
    elif n is not None and n >= 3:
        구분 = "등록 전"
    else:
        구분 = "아이디어"
    프로젝트.append({"이름": 앱이름(root), "단계": 단계들[n] if n is not None else None, "구분": 구분,
                   "제품수에듦": 구분 in ("무료", "플랜", "접음"), "지금": root == 지금})
프로젝트.sort(key=lambda x: (not x["지금"], not x["제품수에듦"], x["이름"]))
무료이름 = next((앱이름(r) for r, b in 목록.items() if 무료 and (b == 무료 or (not b and 무료 in 번호없음))), None)
칸 = 권.get("칸수") if 있나 else None
보임 = {"헤비": "플러스"}
print(json.dumps({
    "플랜": (보임.get(권.get("등급"), 권.get("등급")) if 있나 else None),
    "제품수": len(앱들) + len(접은) + (1 if 무료 else 0),
    "한도": ((int(칸) + 1) if 칸 is not None else None) if 있나 else 1,
    "무료제품": (무료이름 or ("앱 번호를 못 읽은 제품" if 무료 in 번호없음 else ("A product registered on another computer" if os.environ.get("NF_UI_LANG") == "en" else "다른 컴퓨터에서 등록한 제품"))) if 무료 else None,
    "등록수": len(목록), "프로젝트": 프로젝트, "받은때": 받은때,
    "무료끝": _한국날(권.get("무료끝")) if 권.get("무료끝") else None,
}, ensure_ascii=False))
