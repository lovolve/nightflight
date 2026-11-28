#!/usr/bin/env python3
"""개발 폴더의 앱 아이콘을 찾아 조종석 이름 카드에 넣을 작은 그림으로 만든다."""
import shutil
import base64
import json
import os
import subprocess
import sys
import time

뺄폴더 = {"node_modules", "DerivedData", ".git", "build", "Build", "Pods", ".build", "dist", ".next", "worktrees",
         ".nightflight", ".claude", "Carthage", "vendor", ".gradle", "intermediates", "generated"}
최대깊이 = 7
최대크기 = 40 * 1024
줄인폭 = 96
웹이름 = ("apple-touch-icon.png", "icon.png", "favicon.png", "favicon.svg", "icon.svg", "logo.png")


def _걷기(뿌리):
    뿌리 = os.path.abspath(뿌리)
    깊이0 = 뿌리.rstrip(os.sep).count(os.sep)
    for 자리, 폴더들, 파일들 in os.walk(뿌리):
        폴더들[:] = sorted(d for d in 폴더들 if d not in 뺄폴더 and not d.startswith("."))
        if 자리.count(os.sep) - 깊이0 >= 최대깊이:
            폴더들[:] = []
        yield 자리, 폴더들, 파일들


def _가장큰png(폴더):
    best, 크기 = "", -1
    try:
        for f in os.listdir(폴더):
            if f.lower().endswith(".png"):
                p = os.path.join(폴더, f)
                s = os.path.getsize(p)
                if s > 크기:
                    best, 크기 = p, s
    except OSError:
        pass
    return best


def 후보들(뿌리):
    ios, android, web = [], [], []
    for 자리, 폴더들, 파일들 in _걷기(뿌리):
        이름 = os.path.basename(자리)
        if 이름 == "AppIcon.appiconset":
            p = _가장큰png(자리)
            if p:
                ios.append(p)
            폴더들[:] = []
            continue
        if 이름.startswith("mipmap-") and "xxxhdpi" in 이름:
            for f in ("ic_launcher.png", "ic_launcher_round.png"):
                if f in 파일들:
                    android.append(os.path.join(자리, f))
                    break
        for f in 웹이름:
            if f in 파일들:
                web.append(os.path.join(자리, f))
                break
    out = []
    for 무리 in (ios, android, web):
        out += sorted(무리, key=lambda p: (p.count(os.sep), p))
    return out


def 찾기(뿌리):
    h = 후보들(뿌리)
    return h[0] if h else ""


def _줄이기(원본, 놓을곳):
    try:
        r = subprocess.run(["sips", "-s", "format", "png", "-Z", str(줄인폭), 원본, "--out", 놓을곳],
                           capture_output=True, timeout=15)
        return r.returncode == 0 and os.path.getsize(놓을곳) > 0
    except (OSError, subprocess.SubprocessError):
        return False


class _잠금:
    def __init__(self, 기록):
        self.길 = os.path.join(기록, "internal", "app_icon.lock")

    def __enter__(self):
        self.f = None
        try:
            import fcntl
            os.makedirs(os.path.dirname(self.길), exist_ok=True)
            self.f = open(self.길, "a")
            fcntl.flock(self.f, fcntl.LOCK_EX)
        except Exception:
            pass
        return self

    def __exit__(self, *a):
        if self.f is not None:
            self.f.close()


def _표저장(표자리, 표):
    t = "%s.tmp%d" % (표자리, os.getpid())
    with open(t, "w", encoding="utf-8") as f:
        json.dump(표, f, ensure_ascii=False)
    os.replace(t, 표자리)


def 주소(뿌리, 기록):
    with _잠금(기록):
        return _주소(뿌리, 기록)


def _주소(뿌리, 기록):
    안 = os.path.join(기록, "internal")
    표자리, 그림자리 = os.path.join(안, "app_icon.src"), os.path.join(안, "app_icon.png")
    오늘 = time.strftime("%Y-%m-%d")
    try:
        표 = json.load(open(표자리, encoding="utf-8"))
    except (OSError, ValueError):
        표 = {}
    if 표.get("끔"):
        return ""
    if 표.get("지정"):
        try:
            b = open(그림자리, "rb").read()
        except OSError:
            return ""
        return 표.get("꼴", "data:image/png;base64,") + base64.b64encode(b).decode() if 0 < len(b) <= 최대크기 else ""
    원본 = os.path.join(뿌리, 표["원본"]) if 표.get("원본") else ""
    if 표.get("찾은날") != 오늘 or (원본 and not os.path.isfile(원본)):
        원본 = 찾기(뿌리)
        표 = {"원본": os.path.relpath(원본, 뿌리) if 원본 else "", "찾은날": 오늘}
        try:
            os.makedirs(안, exist_ok=True)
            _표저장(표자리, 표)
        except OSError:
            pass
    if not 원본 or not os.path.isfile(원본):
        return ""
    if 원본.lower().endswith(".svg"):
        try:
            b = open(원본, "rb").read()
        except OSError:
            return ""
        return "data:image/svg+xml;base64," + base64.b64encode(b).decode() if len(b) <= 최대크기 else ""
    try:
        낡음 = not os.path.isfile(그림자리) or os.path.getmtime(그림자리) < os.path.getmtime(원본) or 표.get("만든원본") != 표.get("원본")
    except OSError:
        낡음 = True
    if 낡음:
        os.makedirs(안, exist_ok=True)
        if not _줄이기(원본, 그림자리):
            return ""
        표["만든원본"] = 표.get("원본")
        try:
            _표저장(표자리, 표)
        except OSError:
            pass
    try:
        b = open(그림자리, "rb").read()
    except OSError:
        return ""
    return "data:image/png;base64," + base64.b64encode(b).decode() if 0 < len(b) <= 최대크기 else ""


def _표쓰기(기록, 표):
    안 = os.path.join(기록, "internal")
    os.makedirs(안, exist_ok=True)
    _표저장(os.path.join(안, "app_icon.src"), 표)


def 명령(말, 인자):
    기록 = os.environ.get("NF_STATE") or ""
    if not 기록 or not os.path.isdir(기록):
        sys.exit("  ⛔ 기록 폴더를 찾지 못했습니다 — 야간비행에 등록한 폴더에서 부르십시오.")
    with _잠금(기록):
        return _명령(말, 인자, 기록)


def _명령(말, 인자, 기록):
    뿌리 = os.path.dirname(os.path.abspath(기록))
    그림자리 = os.path.join(기록, "internal", "app_icon.png")
    if 말 == "후보":
        h = 후보들(뿌리)
        if not h:
            print("  개발 폴더에서 찾은 아이콘이 없습니다.")
        for i, p in enumerate(h, 1):
            print(f"  {i}. {os.path.relpath(p, 뿌리)}")
        return 0
    if 말 == "끄기":
        _표쓰기(기록, {"끔": True})
        print("  · 조종석 이름 카드를 아이콘 없이 두 글자로 둡니다.")
        return 0
    if 말 == "자동":
        _표쓰기(기록, {})
        print("  · 개발 폴더에서 아이콘을 다시 찾습니다(다음 조종석 갱신 때).")
        return 0
    if 말 == "바꾸기":
        if not 인자:
            sys.exit("  ⛔ 바꿀 그림 파일을 적어 주십시오: app_icon.py 바꾸기 <그림 파일>")
        p = os.path.abspath(os.path.expanduser(인자[0]))
        if not os.path.isfile(p):
            sys.exit(f"  ⛔ 그림 파일을 찾지 못했습니다: {인자[0]}")
        os.makedirs(os.path.dirname(그림자리), exist_ok=True)
        if p.lower().endswith(".svg"):
            if os.path.getsize(p) > 최대크기:
                sys.exit("  ⛔ SVG 그림이 너무 큽니다(40KB 넘음). PNG 로 주시면 줄여서 넣습니다.")
            shutil.copyfile(p, 그림자리)
            꼴 = "data:image/svg+xml;base64,"
        else:
            if not _줄이기(p, 그림자리):
                sys.exit("  ⛔ 그 파일을 그림으로 읽지 못했습니다. PNG · JPG 파일을 주십시오.")
            if os.path.getsize(그림자리) > 최대크기:
                sys.exit("  ⛔ 줄였는데도 그림이 너무 큽니다(40KB 넘음). 더 단순한 그림을 주십시오.")
            꼴 = "data:image/png;base64,"
        _표쓰기(기록, {"지정": True, "꼴": 꼴, "고른날": time.strftime("%Y-%m-%d")})
        print("  · 조종석 이름 카드의 아이콘을 고르신 그림으로 바꿨습니다(다음 조종석 갱신 때 보입니다).")
        return 0
    sys.exit("  ⛔ 모르는 말입니다: 후보 · 바꾸기 <그림 파일> · 끄기 · 자동")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] in ("후보", "바꾸기", "끄기", "자동"):
        sys.exit(명령(sys.argv[1], sys.argv[2:]))
    if len(sys.argv) < 3:
        sys.exit("사용: app_icon.py <제품 폴더> <기록 폴더>")
    print(주소(sys.argv[1], sys.argv[2]))
