#!/usr/bin/env python3
"""야간비행 도구"""
import glob
import json
import os
import plistlib
import re
import shlex
import shutil
import subprocess
import sys

HOME = os.path.expanduser("~")
BREW = [x for x in os.environ.get("NF_FIND_PREFIXES", "/opt/homebrew:/usr/local").split(":") if x]
APPDIRS = [x for x in os.environ.get("NF_FIND_APPDIRS", "/Applications:" + HOME + "/Applications").split(":") if x]


def _props(path, key):
    try:
        for line in open(path, encoding="utf-8", errors="replace"):
            if line.strip().startswith(key + "="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


def _run(*a):
    try:
        return subprocess.run(a, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def _first(cands, ok):
    seen, looked = set(), []
    for p, src in cands:
        if not p or p in seen:
            continue
        seen.add(p)
        looked.append(p)
        if ok(p):
            return {"자리": p, "출처": src, "본자리": looked}
    return {"자리": "", "출처": "", "본자리": looked}


def find(root):
    root = os.path.abspath(root)
    out = {}

    sdk_props = _props(os.path.join(root, "local.properties"), "sdk.dir") or _props(os.path.join(root, "android", "local.properties"), "sdk.dir")
    cands = [(os.environ.get("ANDROID_HOME", ""), "환경 설정 ANDROID_HOME"),
             (os.environ.get("ANDROID_SDK_ROOT", ""), "환경 설정 ANDROID_SDK_ROOT"),
             (sdk_props, "프로젝트 local.properties"),
             (os.path.join(HOME, "Library/Android/sdk"), "Android Studio 기본 자리")]
    cands += [(b + "/share/android-commandlinetools", "Homebrew 명령줄 도구") for b in BREW]
    sdk = _first(cands, lambda p: os.path.isdir(os.path.join(p, "platform-tools")))
    if sdk["자리"]:
        plats = [re.sub(r".*android-", "", x) for x in glob.glob(sdk["자리"] + "/platforms/android-*")]
        sdk["가장높은판"] = max(plats, key=lambda v: int(v) if v.isdigit() else -1) if plats else ""
        sdk["기기이미지"] = sorted(os.path.basename(x) for x in glob.glob(sdk["자리"] + "/system-images/*"))
        sdk["adb"] = sdk["자리"] + "/platform-tools/adb" if os.access(sdk["자리"] + "/platform-tools/adb", os.X_OK) else ""
        emu = sdk["자리"] + "/emulator/emulator"
        sdk["emulator"] = emu if os.access(emu, os.X_OK) else ""
        avdm = sorted(glob.glob(sdk["자리"] + "/cmdline-tools/*/bin/avdmanager"))
        sdk["avdmanager"] = avdm[-1] if avdm else ""
    out["안드로이드SDK"] = sdk

    cands = [(p, "응용 프로그램 폴더") for d in APPDIRS for p in sorted(glob.glob(d + "/Android Studio*.app"))]
    if not cands:
        cands = [(d + "/Android Studio.app", "응용 프로그램 폴더") for d in APPDIRS]
    out["AndroidStudio"] = _first(cands, os.path.isdir)

    jh_sys = "" if os.environ.get("NF_FIND_NO_SELECT") == "1" else _run("/usr/libexec/java_home")
    gp = [os.path.join(root, "gradle.properties"), os.path.join(root, "android", "gradle.properties"), HOME + "/.gradle/gradle.properties"]
    cands = [(os.environ.get("JAVA_HOME", ""), "환경 설정 JAVA_HOME"), (jh_sys, "시스템 Java")]
    cands += [(_props(g, "org.gradle.java.home"), "gradle.properties") for g in gp]
    for b in BREW:
        cands += [(p, "Homebrew Java") for p in sorted(glob.glob(b + "/opt/openjdk*/libexec/openjdk.jdk/Contents/Home"))]
    if os.environ.get("NF_FIND_NO_SELECT") != "1":
        cands += [(p, "설치된 Java") for p in sorted(glob.glob("/Library/Java/JavaVirtualMachines/*/Contents/Home"))]
    if out["AndroidStudio"]["자리"]:
        cands.append((out["AndroidStudio"]["자리"] + "/Contents/jbr/Contents/Home", "Android Studio 안의 Java"))
    out["Java"] = _first(cands, lambda p: os.access(os.path.join(p, "bin/java"), os.X_OK))

    avd_home = os.environ.get("ANDROID_AVD_HOME") or os.path.join(HOME, ".android/avd")
    out["가상기기"] = {"자리": avd_home, "목록": sorted(os.path.basename(x)[:-4] for x in glob.glob(avd_home + "/*.avd")), "본자리": [avd_home]}

    sel = "" if os.environ.get("NF_FIND_NO_SELECT") == "1" else _run("xcode-select", "-p")
    app_from_sel = sel[: -len("/Contents/Developer")] if sel.endswith("/Contents/Developer") else ""
    cands = [(app_from_sel, "지금 선택된 개발 도구")]
    cands += [(p, "응용 프로그램 폴더") for d in APPDIRS for p in sorted(glob.glob(d + "/Xcode*.app"))]
    if len(cands) == 1 and not app_from_sel:
        cands += [(d + "/Xcode.app", "응용 프로그램 폴더") for d in APPDIRS]
    xc = _first(cands, lambda p: os.path.isfile(os.path.join(p, "Contents/Info.plist")))
    xc["선택된자리"] = sel
    if xc["자리"]:
        for f, k, name in (("Contents/version.plist", "CFBundleShortVersionString", "판"), ("Contents/Info.plist", "LSMinimumSystemVersion", "요구운영체제")):
            try:
                with open(os.path.join(xc["자리"], f), "rb") as fh:
                    xc[name] = str(plistlib.load(fh).get(k, ""))
            except Exception:
                xc[name] = ""
    out["Xcode"] = xc

    path_extra = os.pathsep.join([b + "/bin" for b in BREW] + [HOME + "/flutter/bin", HOME + "/development/flutter/bin", HOME + "/fvm/default/bin"])
    w = shutil.which("flutter", path=os.environ.get("PATH", "") + os.pathsep + path_extra)
    cands = [(os.path.join(os.environ["FLUTTER_ROOT"], "bin/flutter") if os.environ.get("FLUTTER_ROOT") else "", "환경 설정 FLUTTER_ROOT"),
             (w or "", "PATH")]
    cands += [(p + "/flutter", "알려진 자리") for p in path_extra.split(os.pathsep)]
    out["Flutter"] = _first(cands, lambda p: os.access(p, os.X_OK))
    return out


def 못찾음말(item):
    return "못 찾았습니다 — 본 자리: " + " · ".join(item.get("본자리") or ["(볼 자리를 정하지 못함)"])


def sh(out):
    s = out["안드로이드SDK"]; j = out["Java"]; a = out["AndroidStudio"]; x = out["Xcode"]; f = out["Flutter"]; v = out["가상기기"]
    kv = {
        "NF_SDK": s["자리"], "NF_SDK_SRC": s["출처"], "NF_SDK_LOOKED": " · ".join(s["본자리"]),
        "NF_SDK_TOP": s.get("가장높은판", ""), "NF_SYSIMG": " ".join(s.get("기기이미지", [])),
        "NF_ADB": s.get("adb", ""), "NF_EMU": s.get("emulator", ""), "NF_AVDMANAGER": s.get("avdmanager", ""),
        "NF_JAVA": j["자리"], "NF_JAVA_SRC": j["출처"], "NF_JAVA_LOOKED": " · ".join(j["본자리"]),
        "NF_AS": a["자리"], "NF_AS_LOOKED": " · ".join(a["본자리"]),
        "NF_AVD_N": str(len(v["목록"])), "NF_AVDS": " ".join(v["목록"]), "NF_AVD_HOME": v["자리"],
        "NF_XCODE": x["자리"], "NF_XCODE_SRC": x["출처"], "NF_XCODE_VER": x.get("판", ""), "NF_XCODE_MINOS": x.get("요구운영체제", ""),
        "NF_XCODE_LOOKED": " · ".join(x["본자리"]), "NF_XCODE_SELECTED": x.get("선택된자리", ""),
        "NF_FLUTTER": f["자리"], "NF_FLUTTER_LOOKED": " · ".join(f["본자리"]),
    }
    return "\n".join(f"{k}={shlex.quote(v)}" for k, v in kv.items())


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    out = find(args[0] if args else ".")
    if "--sh" in argv:
        print(sh(out))
    elif "--json" in argv:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        for name, item in out.items():
            if name == "가상기기":
                print(f"  {name:14} {len(item['목록'])}개 ({item['자리']})")
            elif item["자리"]:
                print(f"  {name:14} {item['자리']}  ← {item['출처']}")
            else:
                print(f"  {name:14} {못찾음말(item)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
