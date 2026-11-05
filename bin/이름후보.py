#!/usr/bin/env python3
"""등록할 때 앱 설정에서 «제품 이름» 후보를 찾아 한 줄로 찍는다 — 적지는 않는다."""
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
