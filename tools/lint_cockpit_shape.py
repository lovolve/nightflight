#!/usr/bin/env python3
"""조종석의 «꼴 표»가 지금 기록 자료를 다 덮나.

🔴 2026-10-27 15회차 레드팀: 기록 값 하나가 틀린 꼴이면 조종석이 통째로 멈췄다 → 꼴 표(어느 자리가 목록 · 묶음인가)를
   실제 자료에서 뽑아 cockpit.html 에 박고, 받을 때 그 표로 맞추게 했다(tools/조종석꼴.py).
⭐  — 꼴 표는 «뽑은 날의 자료»다. 기록에 새 목록 칸이 생기면 표가 그 자리를 모르고, 그 자리가 틀리면 다시 멈춘다.
   그래서 지금 자료에서 목록 · 묶음 자리를 다시 뽑아, 표에 없는 자리 · 표와 꼴이 다른 자리를 알린다.
⛔ 고치지 않는다 — 알리기만 한다. 고치는 것은 `python3 tools/조종석꼴.py --박기 <기록판 폴더…>` 다.

쓰는 법:  python3 tools/lint_cockpit_shape.py [<기록판 폴더> …]   (안 주면 이 저장소의 기록판)
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib.util as _u
_s = _u.spec_from_file_location("조종석꼴", str(Path(__file__).resolve().parent / "조종석꼴.py"))
꼴틀 = _u.module_from_spec(_s); _s.loader.exec_module(꼴틀)


def 박힌표(text):
    m = re.search(r"var 꼴표=(.*?);/\*꼴표끝\*/", text, re.S)
    return json.loads(m.group(1)) if m else None


def 빠진자리(표, 자료, 길):
    """자료(짧게 꼴)에 있는 목록·묶음 자리 가운데 표가 모르는 것 · 꼴이 다른 것"""
    out = []
    if 자료 in (0, None):
        return out
    자_목록 = 자료 == "A" or isinstance(자료, list)
    if 표 in (0, None):
        return [(길, "표에 없는 " + ("목록" if 자_목록 else "묶음") + " 자리")]
    표_목록 = 표 == "A" or isinstance(표, list)
    if 자_목록 != 표_목록:
        return [(길, "꼴이 다름 — 표는 " + ("목록" if 표_목록 else "묶음") + ", 자료는 " + ("목록" if 자_목록 else "묶음"))]
    if 자_목록:
        속자 = 자료[1] if isinstance(자료, list) else None
        속표 = 표[1] if isinstance(표, list) else None
        return 빠진자리(속표, 속자, 길 + "[]") if 속자 else []
    if isinstance(자료, dict):
        표d = 표 if isinstance(표, dict) else {}
        for k, v in 자료.items():
            out += 빠진자리(표d.get(k, 표d.get("*")), v, 길 + "." + k)
    return out


def main(argv):
    root = Path(__file__).resolve().parent.parent
    p = root / "board" / "cockpit.html"
    if not p.exists():
        return 0
    표 = 박힌표(p.read_text(encoding="utf-8"))
    if 표 is None:
        print("  ⛔ 조종석에 꼴 표(var 꼴표=…;/*꼴표끝*/)가 없습니다 — 틀린 꼴 자료에서 화면이 멈춥니다"); return 1
    폴더 = [Path(a) for a in argv] or [d for d in (root / ".nightflight" / "board", root / ".claude" / "board") if d.is_dir()][:1]
    자료표 = {}
    for d in 폴더:
        for f in sorted(Path(d).glob("*.json")):
            try: v = json.loads(f.read_text(encoding="utf-8"))
            except Exception: continue
            자료표[f.stem] = 꼴틀.합치기(자료표.get(f.stem), 꼴틀.꼴(v, f.stem))
    빠짐 = []
    for k, v in 자료표.items():
        if k == "pressed": continue
        빠짐 += 빠진자리(표.get(k), 꼴틀.짧게(v), k)
    if not 빠짐:
        print(f"  ✅ 조종석 꼴 표 — 지금 기록 자료({len(자료표)}칸)의 목록 · 묶음 자리를 다 덮습니다")
        return 0
    print(f"  ⛔ 조종석 꼴 표가 낡았습니다 — 모르는 자리 {len(빠짐)}곳 (그 자리 값이 틀리면 화면이 멈춥니다)")
    for 길, 왜 in 빠짐[:12]:
        print(f"     {길} — {왜}")
    print("     고치기: python3 tools/조종석꼴.py --박기 <기록판 폴더…>  (여러 제품의 기록판을 같이 주면 더 넓게 덮습니다)")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
