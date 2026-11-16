#!/usr/bin/env python3
"""개인정보 처리방침 «초안» — 기록(고른 기능 · 돈 받기 · 앱 이름)과 코드(쓰는 바깥 서비스)에서 짓는다. 게시는 사람이 한다."""
import os, re, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _root

if len(sys.argv) < 2 or not Path(sys.argv[1]).is_dir():
    print("쓰는 법: privacy_draft.py <프로젝트 폴더>")
    sys.exit(0)
뿌리 = Path(sys.argv[1]).resolve()
lp = _root.ledger()
설정 = {}
try:
    for l in lp.read_text(encoding="utf-8").splitlines():
        c = l.split("\t")
        if len(c) > 3 and c[1] == "앱설정" and c[3].strip():
            설정.setdefault(c[2], []).append(c[3].strip())
except OSError:
    pass
마지막 = {k: v[-1] for k, v in 설정.items()}
기능들 = set()
for v in 설정.get("기능", []):
    기능들.update(x.strip() for x in v.split("·") if x.strip())

서비스표 = [
    ("Supabase", "회원 정보와 앱 데이터 저장", r"supabase"),
    ("Firebase(Google)", "회원 정보 · 데이터 저장 · 알림 보내기", r"firebase"),
    ("RevenueCat", "결제 · 구독 상태 관리", r"revenuecat"),
    ("Stripe", "결제 처리", r"stripe"),
    ("Paddle", "결제 처리", r"paddle"),
    ("OpenAI", "AI 답 만들기(입력한 글을 보냄)", r"openai"),
    ("Anthropic", "AI 답 만들기(입력한 글을 보냄)", r"anthropic"),
    ("Google Gemini", "AI 답 만들기(입력한 글을 보냄)", r"generativeai|google-genai|gemini"),
    ("Sentry", "오류 기록 수집", r"sentry"),
    ("Amplitude", "사용 통계 수집", r"amplitude"),
    ("Mixpanel", "사용 통계 수집", r"mixpanel"),
    ("OneSignal", "알림 보내기", r"onesignal"),
    ("LiveKit", "음성 · 영상 통화 중계", r"livekit"),
]
안봄 = {".git", "node_modules", "Pods", "DerivedData", "build", ".build", "dist", ".next", ".venv", "venv", ".nightflight", ".claude"}
글 = ""
for dp, dn, fn in os.walk(뿌리):
    dn[:] = [d for d in dn if d not in 안봄]
    if dp[len(str(뿌리)):].count(os.sep) >= 4:
        dn[:] = []
    for f in fn:
        if f in ("package.json", "Package.swift", "Package.resolved", "Podfile", "pubspec.yaml", "build.gradle",
                 "requirements.txt", "pyproject.toml", "project.pbxproj"):
            try:
                글 += Path(dp, f).read_text(encoding="utf-8", errors="replace").lower()[:400000]
            except OSError:
                pass
쓰는서비스 = [(n, 일) for n, 일, 패 in 서비스표 if re.search(패, 글)]

앱 = 마지막.get("앱이름") or "[확인 필요: 앱 이름]"
항목 = ["앱을 쓰는 동안 생기는 기록(오류 기록 · 기기 종류 · 운영체제 판)"]
if "전화기를 바꿔도 그대로 쓰기" in 기능들 or "다른 사람과 같이 쓰기" in 기능들 or any(n in ("Supabase", "Firebase(Google)") for n, _ in 쓰는서비스):
    항목.append("회원 가입 정보(이메일 주소 또는 애플 · 구글 로그인 식별 값)")
if "다른 사람이 쓴 글이나 사진 보기" in 기능들 or "사진이나 파일 올리기" in 기능들:
    항목.append("이용자가 올린 글 · 사진 · 파일")
if "내 위치 쓰기" in 기능들:
    항목.append("위치 정보(기능을 쓸 때만 · 이용자가 허락한 경우)")
if "사진이나 동영상 찍기" in 기능들:
    항목.append("카메라로 찍은 사진 · 동영상(이용자가 저장하거나 올린 것만)")
if "AI가 답해주기" in 기능들:
    항목.append("AI 기능에 입력한 글(답을 만들기 위해 AI 서비스로 보냄)")
돈 = 마지막.get("돈받기", "")
if 돈 and 돈 not in ("없음", "안받음"):
    항목.append("구매 기록(결제 자체는 애플 · 구글이 처리하며 카드 정보는 받지 않음)")

확인 = []
def 칸(x):
    확인.append(x)
    return "[확인 필요: %s]" % x

오늘 = time.strftime("%Y년 %m월 %d일")
줄 = [
    "<!-- 야간비행이 기록과 코드에서 지은 «초안»입니다. 법률 검토가 아닙니다. [확인 필요] 칸을 채우고, 서비스 내용과 맞는지 확인한 뒤 게시하십시오. -->",
    "",
    "# %s 개인정보 처리방침" % 앱,
    "",
    "%s(이하 «운영자»)는 %s(이하 «서비스»)를 이용하는 분의 개인정보를 소중히 다루며, 관련 법령을 지킵니다." % (칸("운영자 이름 또는 회사 이름"), 앱),
    "",
    "## 1. 모으는 개인정보",
    "",
] + ["- " + x for x in 항목] + [
    "",
    "## 2. 쓰는 목적",
    "",
    "- 서비스 제공과 회원 관리",
    "- 오류를 고치고 서비스를 나아지게 하기",
] + (["- 결제 확인과 환불 처리"] if 돈 and 돈 not in ("없음", "안받음") else []) + [
    "",
    "## 3. 보관 기간",
    "",
    "회원 탈퇴 또는 이용 목적을 이룬 뒤 바로 지웁니다. 법령이 보관을 요구하는 기록은 그 기간 동안만 보관합니다. %s" % 칸("법령상 따로 보관하는 기록과 기간이 있는지"),
    "",
    "## 4. 처리를 맡기는 곳(바깥 서비스)",
    "",
]
if 쓰는서비스:
    줄 += ["| 맡기는 곳 | 맡기는 일 |", "|---|---|"] + ["| %s | %s |" % x for x in 쓰는서비스]
    줄 += ["", "위 목록은 앱 코드에서 찾은 것입니다. %s" % 칸("빠진 서비스 · 쓰지 않는 서비스가 있는지")]
else:
    줄 += ["%s" % 칸("개인정보를 맡기는 바깥 서비스(저장 · 로그인 · 결제 · AI · 통계)")]
줄 += [
    "",
    "## 5. 이용자의 권리",
    "",
    "이용자는 언제든지 자기 개인정보를 보거나, 고치거나, 지우라고 요청할 수 있습니다.",
]
if any("회원 가입" in x for x in 항목):
    줄 += ["앱 안의 «계정 삭제»에서 바로 탈퇴하고 정보를 지울 수 있습니다. %s" % 칸("앱 안에 계정 삭제 기능이 있는지(애플 심사 요건)")]
줄 += [
    "",
    "## 6. 아동의 개인정보",
    "",
    "서비스는 만 14세 미만 아동을 대상으로 하지 않습니다. %s" % 칸("대상 나이"),
    "",
    "## 7. 문의",
    "",
    "개인정보 관련 문의: %s" % 칸("문의 메일 주소"),
    "",
    "## 8. 시행일",
    "",
    "이 방침은 %s부터 시행합니다." % 칸("시행일 — 예: %s" % 오늘),
    "",
]

대상 = 뿌리 / "privacy-policy-draft.md"
if 대상.exists():
    대상 = 뿌리 / ("개인정보처리방침-초안-%s.md" % time.strftime("%Y%m%d-%H%M%S"))
대상.write_text("\n".join(줄), encoding="utf-8")
print("  · 개인정보 처리방침 초안을 만들었습니다: " + 대상.name)
print("    채워야 할 칸 %d개: %s" % (len(확인), " · ".join(확인)))
print("    [모델] 사용자에게 채울 칸을 하나씩 여쭈어 채우고, 게시할 곳(웹 페이지 주소)을 정해 앱스토어 «개인정보 처리방침 URL»에 넣게 안내하십시오. 법률 검토가 아니라고 함께 말씀드리십시오.")
