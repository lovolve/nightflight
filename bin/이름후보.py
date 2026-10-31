#!/usr/bin/env python3
"""등록할 때 앱 설정에서 «제품 이름» 후보를 찾아 한 줄로 찍는다 — 적지는 않는다.

🔴 2026-10-29 설치 점검 ⑦: 앱 설정 파일에 표시 이름(«돈기록»)이 있어도 조종석 앱이름이 비어 «제품 이름 아직 안 물어봄»으로 그렸다.
⭐ 후보만 찾아 모델에게 알린다 — 사용자에게 확인받은 뒤에만 `ledger.sh 앱설정 앱이름` 으로 적는다.
⛔ 받은 저장소의 값을 그대로 기록에 적지 않는다(저장소가 정하는 값이다). 변수로 적힌 값($(…) · {{…}})은 읽지 않는다.

받는 것: argv[1] = 프로젝트 폴더. 찍는 것: 후보가 있으면 이름 하나(없으면 아무것도 안 찍는다).
"""
import json, os, re, sys

뿌리 = sys.argv[1] if len(sys.argv) > 1 else "."
안봄 = {".git", "node_modules", "Pods", "DerivedData", "build", ".build", "dist", ".next", ".venv", "venv", ".nightflight", ".claude"}
기본이름 = {"my-app", "myapp", "app", "vite-project", "react-app", "expo-app", "untitled", "test"}


def 깨끗(v):
    v = (v or "").strip()
    if not v or "$" in v or "{{" in v or len(v) > 40 or "\n" in v:
        return ""
    return "" if v.lower() in 기본이름 else v


후보 = []
for dp, dn, fn in os.walk(뿌리):
    dn[:] = [d for d in dn if d not in 안봄 and not d.endswith((".xcassets", ".lproj"))]
    if dp[len(뿌리):].count(os.sep) >= 4:
        dn[:] = []
    for f in fn:
        p = os.path.join(dp, f)
        try:
            if f == "Info.plist":
                s = open(p, encoding="utf-8", errors="replace").read()
                for 열쇠 in ("CFBundleDisplayName", "CFBundleName"):
                    m = re.search(r"<key>" + 열쇠 + r"</key>\s*<string>([^<]*)</string>", s)
                    if m and 깨끗(m.group(1)):
                        후보.append((0, 깨끗(m.group(1))))
            elif f == "project.yml":
                m = re.search(r"CFBundleDisplayName:\s*[\"']?([^\"'\n]+)", open(p, encoding="utf-8", errors="replace").read())
                if m and 깨끗(m.group(1)):
                    후보.append((0, 깨끗(m.group(1))))
            elif f == "app.json":
                d = json.load(open(p, encoding="utf-8"))
                n = (d.get("expo") or {}).get("name") if isinstance(d.get("expo"), dict) else d.get("displayName") or d.get("name")
                if isinstance(n, str) and 깨끗(n):
                    후보.append((1, 깨끗(n)))
            elif f == "package.json" and dp == 뿌리:
                n = json.load(open(p, encoding="utf-8")).get("name")
                if isinstance(n, str) and 깨끗(n) and "/" not in n:
                    후보.append((2, 깨끗(n)))
        except (OSError, ValueError, AttributeError):
            continue
if 후보:
    print(sorted(후보)[0][1])
