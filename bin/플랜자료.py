#!/usr/bin/env python3
"""조종석 머리 «플랜» 단추가 펼칠 자료를 만든다(2026-10-27·28).

플랜에 등록한 프로젝트를 보는 자리 — 담는 것은 프로젝트 수 · 제품등록 수 · 제품 이름. 앱 이름이 있는 맨 위의 단추를 누르면 그 자리에서 열린다.
  ⛔ 다른 화면으로 옮겨 가지 않는다 — 조종석(아티팩트)은 나가면 큰 창으로 떠서 못 돌아온다(대시보드·프로젝트 이동을 없앤 까닭).

받는 것: argv[1] = 지금 프로젝트 폴더 · 환경값 NF_HOME(사람 자리 — 이용권.json · 사람.tsv).
찍는 것: JSON 한 덩이(조종석자료.py 가 board/plan.json 으로 적는다).
  {"플랜": "라이트"|"플러스"|null, "제품수": 제품등록 수(무료 제품 포함), "한도": 3|15|1|null, "무료제품": 이름|null,
   "등록수": N, "프로젝트": [{"이름", "단계", "구분", "제품수에듦", "지금"}], "받은때": "YYYY-MM-DD HH:MM"|null}
  구분: «등록 전»(설계를 넘었는데 서버에 아직 제품등록이 없다) · «무료»(무료 제품 — 2026-10-28 «평생»이라는 말을 뺐다) · «플랜»(유료 제품등록) · «접음»(설계를 시작하고 7일이 지나 접은 제품 — 제품등록은 그대로 센다) ·
        «아이디어»(아이디어 · 검증 — 제품등록 아님). 제품수에듦 = 구분이 아이디어가 아님(옛 이름 · 조종석이 읽는다).
⭐ 2026-10-28 플랜 개편: 라이트 = 무료 1 + 유료 2(모두 3) · 플러스 = 무료 1 + 유료 14(모두 15) ·
  구독이 끝나도 무료 제품 1개는 계속. 서버의 «칸수»는 유료 몫(2 · 14)이라 한도는 칸수 + 1 이다.
⛔ 서버를 부르지 않는다 — 이용권.json 은 대화 시작 훅이 뒤에서 채운다(못 받았으면 null 칸으로 둔다).
"""
import json, os, sys, time

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

단계들 = "진단 기획 검증 설계 개발 확인 출시 수정 출시후".split()
def 단계번호(v):
    for i in range(len(단계들) - 1, -1, -1):
        if v and 단계들[i] in v:
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
    "무료제품": (무료이름 or ("앱 번호를 못 읽은 제품" if 무료 in 번호없음 else 무료)) if 무료 else None,
    "등록수": len(목록), "프로젝트": 프로젝트, "받은때": 받은때,
}, ensure_ascii=False))
