#!/usr/bin/env python3
"""조종석이 받는 기록 자료의 «꼴 표»를 실제 자료에서 뽑는다 — 어느 자리가 목록([])이고 어느 자리가 묶음({})인가.

🔴 2026-10-27 15회차 레드팀 · : 기록 값 하나가 틀린 꼴이면 조종석이 통째로 멈췄다.
   시험 화면에서 틀린 값을 자리마다 넣어 보니 처음 11자리, 깊이 들어가니 31자리가 더 나왔다 — 한 자리씩 막으면 끝이 없다.
⭐ 그래서 꼴을 «자료에서» 뽑아 조종석에 박는다. 조종석은 받을 때 이 표로 맞춘다(cockpit.html 의 `꼴표`).
   이름이 자료마다 다른 묶음(기능 이름 · 단계 번호 · 상태 이름)은 `*` 로 적는다.

쓰는 법:  python3 tools/조종석꼴.py <기록판 폴더> [<기록판 폴더> …]   → 꼴 표 한 줄(JSON)을 찍는다
          python3 tools/조종석꼴.py --박기 <폴더…>                    → board/cockpit.html 의 꼴 표 자리를 바꾼다
"""
import json
import re
import sys
from pathlib import Path

이름묶음 = {"states.기능별본것", "states.기능별", "states.기능별.*", "states.기능별본것.*.상태들", "features.설계표.단계", "stages.per",
           "deps.고치는쪽별", "deps.따져본기능", "features.진단값", "machine.메모리쓴곳", "attempts.기능별", "standards.기능별"}


def 합치기(a, b):
    if a is None: return b
    if b is None: return a
    if a[0] != b[0]: return a
    if a[0] == "O":
        k = dict(a[1])
        for n, v in b[1].items(): k[n] = 합치기(k.get(n), v)
        return ("O", k)
    if a[0] == "A":
        return ("A", 합치기(a[1], b[1]))
    return a


def 꼴(v, 길):
    if isinstance(v, list):
        속 = None
        for x in v[:50]: 속 = 합치기(속, 꼴(x, 길 + ".[]"))
        return ("A", 속 if 속 and 속[0] in "AO" else None)
    if isinstance(v, dict):
        if 길 in 이름묶음:
            속 = None
            for x in v.values(): 속 = 합치기(속, 꼴(x, 길 + ".*"))
            return ("O", {"*": 속} if 속 and 속[0] in "AO" else {})
        k = {}
        for n, x in v.items():
            s = 꼴(x, 길 + "." + n)
            if s[0] in "AO": k[n] = s
        return ("O", k)
    return ("S", None)


def 짧게(s):
    if s is None: return 0
    if s[0] == "A": return ["A", 짧게(s[1])] if s[1] else "A"
    if s[0] == "O":
        return {n: 짧게(v) for n, v in s[1].items()} if s[1] else "O"
    return 0


def 짧은합(a, b):
    """짧은 꼴(0 · "A" · ["A", 속] · "O" · {…}) 둘을 합친다 — 어느 한쪽이 아는 자리는 남긴다."""
    if a in (0, None): return b
    if b in (0, None): return a
    a목 = a == "A" or isinstance(a, list)
    b목 = b == "A" or isinstance(b, list)
    if a목 != b목: return b
    if a목:
        속 = 짧은합(a[1] if isinstance(a, list) else None, b[1] if isinstance(b, list) else None)
        return ["A", 속] if 속 not in (0, None) else "A"
    ad = a if isinstance(a, dict) else {}
    bd = b if isinstance(b, dict) else {}
    합 = {k: 짧은합(ad.get(k), bd.get(k)) for k in sorted(set(ad) | set(bd))}
    return 합 if 합 else "O"


def main(argv):
    박기 = "--박기" in argv
    폴더 = [Path(a) for a in argv if a != "--박기"]
    표 = {}
    for d in 폴더:
        for f in sorted(d.glob("*.json")):
            try: v = json.loads(f.read_text(encoding="utf-8"))
            except Exception: continue
            표[f.stem] = 합치기(표.get(f.stem), 꼴(v, f.stem))
    글 = json.dumps({k: 짧게(v) for k, v in sorted(표.items()) if v and v[0] in "AO"}, ensure_ascii=False, separators=(",", ":"))
    if not 박기:
        print(글); return 0
    p = Path(__file__).resolve().parent.parent / "board" / "cockpit.html"
    s = p.read_text(encoding="utf-8")
    m = re.search(r"var 꼴표=(.*?);/\*꼴표끝\*/", s, re.S)
    if m:
        try:
            옛 = json.loads(m.group(1))
            새 = json.loads(글)
            글 = json.dumps({k: 짧은합(옛.get(k), 새.get(k)) for k in sorted(set(옛) | set(새))}, ensure_ascii=False, separators=(",", ":"))
        except ValueError:
            pass
    새 = re.sub(r"var 꼴표=.*?;/\*꼴표끝\*/", lambda m: "var 꼴표=" + 글 + ";/*꼴표끝*/", s, count=1, flags=re.S)
    if 새 == s and "var 꼴표=" not in s:
        print("  ⛔ cockpit.html 에 꼴 표 자리(var 꼴표=…;/*꼴표끝*/)가 없습니다"); return 1
    p.write_text(새, encoding="utf-8"); print(f"  ✓ 꼴 표를 박았습니다 ({len(글)}자)"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
