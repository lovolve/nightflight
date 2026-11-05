#!/usr/bin/env python3
"""새 제품 폴더에 둘 설정·기록 자리를 만든다 — `setup_new_app.sh` 의 몸."""
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
