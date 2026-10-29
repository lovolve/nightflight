#!/usr/bin/env python3
"""새 제품 폴더에 둘 설정·기록 자리를 만든다 — `setup_new_app.sh` 의 몸.

⭐ `bin/setup_new_app.sh` 가 부른다. 받는 것은 그 셸이 넘기는 환경변수(와 선 글)다.
⛔ **`-I` 로 부른다** — 받는 분 폴더에 `json.py` 가 심겨 있어도 파이썬의 것을 읽는다
  (`tools/lint_python_isolated.py` 가 그것을 본다).

🔴 **왜 파일로 빼냈나** (2026-10-25, ):
   전에는 이 58줄이 셸 파일 안에 들어 있었다.
   ⛔ 그 자리에는 **아무 도구도 닿지 않는다** — 린터·형식 검사·시험이 다 비껴간다.
   ⛔ 어디서 틀렸는지도 셸 줄 번호로만 나와, 수천 줄 파일에서 사람이 찾지 못한다.
   ⛔ `-c` 꼴이면 **파이썬 코드에 홑따옴표를 한 글자도 쓸 수 없다**(셸이 그것으로 감싼다).
   ⭐ 파일로 빼면 그 뒤로는 **도구가 대신 잡는다.**
"""
import json, os, sys
want = json.load(open(sys.argv[1])); want = want.get("hooks", want)
root, out = sys.argv[2], sys.argv[3]

off = set()
if len(sys.argv) > 4 and os.path.exists(sys.argv[4]):
    off = {l.strip() for l in open(sys.argv[4]) if l.strip() and not l.startswith("#")}

cur = {}
if os.path.exists(out):
    try:
        cur = json.load(open(out))
    except Exception:
        cur = {}

_before = set((cur.get("hooks") or {}).keys())
_had_status = "statusLine" in cur

cur.setdefault("statusLine", {"type": "command",
                              "command": f"{root}/bin/statusline.sh", "padding": 0})
hooks = cur.setdefault("hooks", {})
added = 0
for event, entries in want.items():
    if event in off:
        continue
    for e in entries:
        e = {k: v for k, v in e.items() if not k.startswith("//")}
        for h in e.get("hooks", []):
            h["command"] = h["command"].replace("${CLAUDE_PLUGIN_ROOT}", root)
        mine = {h["command"] for h in e.get("hooks", [])}
        have = {h.get("command") for ee in hooks.get(event, [])
                for h in ee.get("hooks", [])}
        if mine & have:
            continue
        hooks.setdefault(event, []).append(e)
        added += 1

_after = set((cur.get("hooks") or {}).keys())
_lost = _before - _after
if _lost or (_had_status and "statusLine" not in cur):
    print("  ⛔ 기존 설정이 줄어들 뻔해서 **쓰지 않았습니다**.", file=sys.stderr)
    print("     없어질 뻔한 것: " + " · ".join(sorted(_lost) or ["상태줄"]), file=sys.stderr)
    print("     파일은 그대로 두었습니다. 다시 돌리시면 됩니다.", file=sys.stderr)
    raise SystemExit(1)
json.dump(cur, open(out, "w"), ensure_ascii=False, indent=2)
print(f"  · 훅 {added}개를 얹었습니다 (기존 설정은 그대로 둡니다)")
