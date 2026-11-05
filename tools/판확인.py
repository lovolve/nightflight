#!/usr/bin/env python3
"""깔린 야간비행 판과 공개된 최신 판을 견준다 — 조종석 맨 위 «업데이트» 칸의 자료다."""
import json, os, re, subprocess, sys, time, urllib.request
from pathlib import Path

_PLUGIN = Path(__file__).resolve().parent.parent
_주소 = "https://raw.githubusercontent.com/lovolve/nightflight/main/.claude-plugin/plugin.json"
_주기 = 6 * 3600
할말 = "야간비행 업데이트해줘"
_프록시막음 = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _받은자리() -> Path:
    return Path(os.environ.get("NIGHTFLIGHT_HOME") or (Path.home() / ".nightflight")) / "최신판.txt"


def _판(글) -> tuple:
    return tuple(int(x) for x in str(글).split("."))


def 지금판():
    try:
        v = json.loads((_PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")).get("version")
        _판(v)
        return v
    except (OSError, ValueError, TypeError):
        return None


def 낡았나() -> bool:
    p = _받은자리()
    return not p.is_file() or time.time() - p.stat().st_mtime >= _주기


def 받기() -> int:
    if os.environ.get("NF_VER_NO_NET") or not 낡았나():
        return 0
    try:
        with _프록시막음.open(_주소, timeout=3) as r:
            v = json.loads(r.read(65536).decode("utf-8")).get("version")
        if not re.fullmatch(r"\d+(\.\d+){1,3}", str(v)):
            return 1
    except (OSError, ValueError):
        return 1
    p = _받은자리()
    p.parent.mkdir(parents=True, exist_ok=True)
    t = p.with_name("%s.%d.tmp" % (p.name, os.getpid()))
    t.write_text(v + "\n", encoding="utf-8")
    t.replace(p)
    return 0


def 뒤에서받기():
    if os.environ.get("NF_VER_NO_NET") or not 낡았나():
        return
    try:
        subprocess.Popen([sys.executable, "-I", str(Path(__file__).resolve()), "받기"],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
    except OSError:
        pass


def 상태() -> dict:
    지금 = 지금판()
    try:
        최신 = _받은자리().read_text(encoding="utf-8").strip()
        _판(최신)
    except (OSError, ValueError):
        최신 = None
    if not 지금 or not 최신:
        칸 = "못잼"
    elif _판(지금) < _판(최신):
        칸 = "필요"
    elif _판(지금) > _판(최신):
        칸 = "앞섬"
    else:
        칸 = "최신"
    return {"지금": 지금, "최신": 최신, "상태": 칸, "할말": 할말}


if __name__ == "__main__":
    명령 = sys.argv[1] if len(sys.argv) > 1 else "상태"
    if 명령 == "받기":
        sys.exit(받기())
    print(json.dumps(상태(), ensure_ascii=False))
