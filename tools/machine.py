#!/usr/bin/env python3
"""이 맥이 개발을 버티고 있나 — 한 곳에서 재서 두 화면에 같은 값을 준다."""
import json
import os
import pathlib
import re
import time as _t
import subprocess
import sys
import time

상태집 = pathlib.Path(os.environ.get("NIGHTFLIGHT_HOME") or (pathlib.Path.home() / ".nightflight"))
느린값적은곳 = 상태집 / "느린값.json"
하루 = 24 * 60 * 60


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def _n(s: str, 기본=None):
    m = re.search(r"-?\d+", s or "")
    return int(m.group(0)) if m else 기본


_시뮬바탕 = ("simdiskimaged", "CoreSimulatorService", "SimLaunchHost", "SimulatorTrampoline")
_유령기준MB = 200


def _유령():
    줄 = _run(["ps", "-axo", "rss=,command="])
    if not 줄:
        return None, None
    수, kb = 0, 0
    for l in 줄.splitlines():
        l = l.strip()
        if "/CoreSimulator.framework/" not in l:
            continue
        if any(b in l for b in _시뮬바탕):
            continue
        p = l.split(None, 1)
        try:
            kb += int(p[0]); 수 += 1
        except (ValueError, IndexError):
            continue
    mb = round(kb / 1024)
    return (수 if mb >= _유령기준MB else 0), mb


def 느린값(새로=False) -> dict:
    if not 새로 and 느린값적은곳.is_file():
        try:
            d = json.loads(느린값적은곳.read_text(encoding="utf-8"))
            if time.time() - d.get("잰때", 0) < 하루:
                return d
        except Exception:
            pass
    집 = pathlib.Path.home()
    잼 = {"잰때": time.time()}
    for 키, 길 in (("만들다남은것", 집 / "Library/Developer/Xcode/DerivedData"),
                   ("시뮬기기", 집 / "Library/Developer/CoreSimulator/Devices")):
        잼[키] = _n(_run(["du", "-sk", str(길)])) if 길.is_dir() else None
    try:
        느린값적은곳.parent.mkdir(parents=True, exist_ok=True)
        느린값적은곳.write_text(json.dumps(잼), encoding="utf-8")
    except OSError:
        pass
    return 잼


def 잰다(느린것도=True) -> dict:
    압박 = _n(_run(["sysctl", "-n", "kern.memorystatus_vm_pressure_level"]))
    스왑글 = _run(["sysctl", "-n", "vm.swapusage"])
    m = re.search(r"used\s*=\s*([\d.]+)M", 스왑글)
    스왑쓴 = float(m.group(1)) if m else None
    디스크 = "/System/Volumes/Data" if os.path.isdir("/System/Volumes/Data") else "/"
    def _df줄(*옵션):
        줄 = _run(["df", *옵션, 디스크]).splitlines()
        return 줄[1].split() if len(줄) > 1 else []
    _g = _df줄("-g")
    빈GB = _n(_g[3]) if len(_g) > 3 else None
    쓴비율 = _n(next((c for c in _df줄("-H") if c.endswith("%")), ""))
    if 빈GB is None or 쓴비율 is None:
        try:
            import shutil
            _du = shutil.disk_usage(디스크)
            빈GB = 빈GB if 빈GB is not None else int(_du.free / 1024 ** 3)
            쓴비율 = 쓴비율 if 쓴비율 is not None else (int(round(_du.used * 100 / (_du.used + _du.free))) if (_du.used + _du.free) else None)
        except Exception:
            pass
    유령수, 유령MB = _유령()
    d = {
        "압박": 압박,
        "압박말": {1: "양호", 2: "주의", 4: "위험"}.get(압박, "모름"),
        "스왑쓴M": 스왑쓴,
        "빈용량GB": 빈GB,
        "디스크쓴%": 쓴비율,
        "시뮬부팅": len([l for l in _run(["pgrep", "-x", "launchd_sim"]).splitlines() if l]),
        "시뮬창": bool(_run(["pgrep", "-x", "Simulator"])),
        "유령": 유령수,
        "유령MB": 유령MB,
        "할말": {"시뮬레이터": "시뮬레이터 정리해줘", "저장공간": "저장공간 정리해줘", "메모리": "메모리 정리해줘"},
        "잰때": _t.time(),
    }
    if 느린것도:
        c = 느린값()
        d["만들다남은것GB"] = round(c["만들다남은것"] / 1024 / 1024, 1) if c.get("만들다남은것") else None
        d["시뮬기기GB"] = round(c["시뮬기기"] / 1024 / 1024, 1) if c.get("시뮬기기") else None
        d["느린값잰때"] = c.get("잰때")
    return d


def 메모리쓴곳(n=8) -> list[dict]:
    out = _run(["ps", "-axo", "rss=,command="])
    묶 = {}
    for l in out.splitlines():
        l = l.strip()
        if not l or " " not in l:
            continue
        kb, cmd = l.split(" ", 1)
        try:
            mb = int(kb) / 1024
        except ValueError:
            continue
        경 = cmd.split(" --")[0]
        if "/claude-code/" in 경:
            이름, 닫기 = "클로드 앱 안의 대화", "대화"
        elif 경 == "claude" or 경.endswith("/claude"):
            이름, 닫기 = "터미널에서 연 클로드 대화", "대화"
        elif ".app/" in 경:
            이름, 닫기 = os.path.basename(경.split(".app/")[0]), "앱"
            if 경.startswith("/System/"):
                닫기 = ""
            if 이름 == "Claude":
                이름, 닫기 = "클로드 앱 (지금 쓰는 앱)", ""
        else:
            이름, 닫기 = "운영체제 기본 프로그램", ""
        g = 묶.setdefault(이름, {"이름": 이름, "MB": 0.0, "개수": 0, "닫기": 닫기})
        g["MB"] += mb
        g["개수"] += 1
    xs = sorted(묶.values(), key=lambda g: -g["MB"])[:n]
    for g in xs:
        g["MB"] = round(g["MB"])
    return xs


def _쓴양MB():
    out = _run(["top", "-l", "1", "-stats", "pid,mem", "-n", "2000"])
    xs = {}
    for l in out.splitlines():
        a = l.split()
        if len(a) != 2 or not a[0].isdigit():
            continue
        m = re.match(r"([\d.]+)([BKMG])", a[1])
        if not m:
            continue
        v = float(m.group(1)) * {"B": 1 / 1048576, "K": 1 / 1024, "M": 1, "G": 1024}[m.group(2)]
        xs[int(a[0])] = v
    return xs


def _대화이름(args: str) -> str:
    m = re.search(r"--name (.+?)(?: --|$)", args)
    return m.group(1).strip() if m else ""


def _폴더(pid: int) -> str:
    out = _run(["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"])
    for l in out.splitlines():
        if l.startswith("n"):
            p = l[1:]
            h = os.path.expanduser("~")
            return "집 폴더" if p == h else (p.replace(h + "/", "") if p.startswith(h) else p)
    return ""


def _켠날(pid: int) -> str:
    out = _run(["ps", "-o", "lstart=", "-p", str(pid)]).split()
    return f"{out[1]} {out[2]}" if len(out) >= 3 else ""


def _다시여는장치() -> list[dict]:
    d = os.path.expanduser("~/Library/LaunchAgents")
    out = []
    try:
        names = sorted(os.listdir(d))
    except OSError:
        return out
    for f in names:
        if not f.endswith(".plist"):
            continue
        try:
            t = open(os.path.join(d, f), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        글 = t
        for sc in re.findall(r"<string>(/[^<]+\.sh)</string>", t):
            try:
                글 += open(sc, encoding="utf-8", errors="replace").read()
            except OSError:
                pass
        if re.search(r"--remote-control|cc on |claude[^\n]*--(continue|resume)|tmux[^\n]*claude", 글):
            간격 = re.search(r"<key>StartInterval</key>\s*<integer>(\d+)</integer>", t)
            out.append({"파일": f, "간격분": int(간격.group(1)) // 60 if 간격 else None})
    return out


def 메모리자세히() -> dict:
    쓴 = _쓴양MB()
    ps = _run(["ps", "-axo", "pid=,args="])
    대화, 앱창, 앱 = [], [], {"합MB": 0.0}
    for l in ps.splitlines():
        l = l.strip()
        if " " not in l:
            continue
        pid, args = l.split(" ", 1)
        if not pid.isdigit():
            continue
        pid = int(pid)
        mb = 쓴.get(pid, 0.0)
        경 = args.split(" --")[0]
        if "/claude-code/" in 경 or re.match(r"(\S*/)?claude(\.exe)?( |$)", args):
            대화.append({"MB": round(mb), "이름": _대화이름(args), "폴더": _폴더(pid), "켠날": _켠날(pid),
                       "어디": "앱 안" if "/claude-code/" in 경 else "터미널"})
        elif "/Claude.app/" in 경:
            앱["합MB"] += mb
            if "--type=renderer" in args:
                앱창.append({"MB": round(mb), "켠날": _켠날(pid)})
    앱창.sort(key=lambda x: -x["MB"])
    합 = sum(쓴.values())
    m = re.search(r"used = ([\d.]+)M", _run(["sysctl", "vm.swapusage"]))
    램 = _n(_run(["sysctl", "-n", "hw.memsize"]), 0)
    return {"합GB": round(합 / 1024, 1), "램GB": round(램 / 1073741824) if 램 else None,
            "스왑GB": round(float(m.group(1)) / 1024, 1) if m else None,
            "대화": sorted(대화, key=lambda x: -x["MB"]), "앱MB": round(앱["합MB"]),
            "큰창": 앱창[0] if 앱창 else None, "작은창": len(앱창) - 1 if 앱창 else 0,
            "장치": _다시여는장치()}


def 걸리나짝(d: dict) -> list[list[str]]:
    짝 = []
    if (d.get("압박") or 1) >= 2:
        짝.append(["메모리", f"{d['압박말']}"])
    if (d.get("빈용량GB") or 999) < 20:
        짝.append(["빈 용량", f"{d['빈용량GB']}GB"])
    if (d.get("디스크쓴%") or 0) >= 85:
        짝.append(["디스크", f"{d['디스크쓴%']}% 참"])
    if (d.get("유령") or 0) > 0 and (d.get("시뮬부팅") or 0) == 0:
        짝.append(["닫힌 뒤에도 남은 시뮬레이터 프로그램", f"{d['유령']}개"])
    return 짝


def 걸리나(d: dict) -> list[str]:
    return [f"{a} {b}" for a, b in 걸리나짝(d)]


def main() -> int:
    if "--메모리" in sys.argv:
        x = 메모리자세히()
        print("=== 메모리를 누가 얼마나 쓰나 (닫으면 그만큼 빕니다) ===")
        print(f"  모든 프로그램 합계 {x['합GB']}GB · 램 {x['램GB']}GB · 디스크로 밀어 둔 것(스왑) {x['스왑GB']}GB")
        print("  ⚠️ 합계는 램 · 압축 · 스왑을 다 더한 값입니다. 램을 넘는 몫이 스왑으로 갑니다.")
        if x["장치"]:
            print()
            print("  🔴 클로드 대화를 자동으로 다시 여는 장치가 있습니다 — 먼저 끄지 않으면 닫아도 다시 열립니다")
            for a in x["장치"]:
                print(f"     · {a['파일']}" + (f" ({a['간격분']}분마다)" if a["간격분"] else ""))
        print()
        print("  클로드 대화 (쉬는 대화는 닫을 수 있습니다 — 기록은 남고 다시 이어 열 수 있습니다)")
        for c in x["대화"]:
            이름 = c["이름"] or "(이름 없음)"
            print(f"  {c['MB']:>6,}MB  {이름} · {c['어디']} · {c['폴더']} · {c['켠날']}에 켬")
        print()
        큰 = x["큰창"]
        print(f"  클로드 앱(창 · 화면 그리기 · 내장 브라우저) {x['앱MB']:,}MB — 앱을 닫으면 모든 대화가 멈춥니다")
        if 큰:
            print(f"     · 가장 큰 창 {큰['MB']:,}MB · {큰['켠날']}부터 켜져 있음"
                  + (" — 앱을 한 번 껐다 켜면 처음 크기로 돌아갑니다(한가할 때)" if 큰["MB"] >= 1500 else ""))
        if x["작은창"]:
            print(f"     · 작은 화면 칸 {x['작은창']}개 — 대화 옆 창 · 내장 브라우저 탭 · 미리보기. 안 보이는데 열린 것이 있을 수 있습니다")
        print()
        print("  그 밖의 앱")
        for g in 메모리쓴곳():
            if g["이름"].startswith("클로드") or g["이름"].startswith("터미널에서 연 클로드"):
                continue
            뒤 = {"대화": "", "앱": "앱을 닫을 수 있습니다", "": "닫지 않습니다"}[g["닫기"]]
            print(f"  {g['MB']:>6,}MB  {g['이름']} · {뒤}")
        return 0
    d = 잰다()
    if "--판" in sys.argv:
        print(json.dumps(d, ensure_ascii=False))
        return 0
    걸림 = 걸리나(d)
    print("=== 이 컴퓨터가 개발을 버티고 있나 ===")
    print(f"  메모리      {d['압박말']} · 스왑 {(d['스왑쓴M'] or 0)/1024:.1f}GB 쓰는 중")
    print("              ⚠️ 스왑은 %로 안 적습니다 — 컴퓨터가 필요할 때 총량을 늘립니다")
    print(f"  빈 용량     {d['빈용량GB']}GB 남음 ({d['디스크쓴%']}% 씀)")
    print(f"  시뮬레이터  부팅 {d['시뮬부팅']}대"
          f" · 창 {'열림' if d['시뮬창'] else '닫힘'} · 남은 프로그램 {d['유령']}개")
    느 = [x for x in (d.get("만들다남은것GB"), d.get("시뮬기기GB")) if x]
    if 느:
        지난 = (time.time() - (d.get("느린값잰때") or 0)) / 3600
        print(f"  치울 수 있는 것  {round(sum(느), 1)}GB · "
              f"시뮬레이터 기기 {d.get('시뮬기기GB') or 0}GB 포함  ({int(지난)}시간 전에 쟀습니다)")
    print()
    if 걸림:
        print("  🔴 지금 상태 — 주의: " + " · ".join(걸림))
    else:
        print("  ✅ 지금 상태 — 모두 괜찮음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
