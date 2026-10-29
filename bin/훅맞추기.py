#!/usr/bin/env python3
"""플러그인을 깔지 않고 저장소 설정(.claude/settings.json)에 야간비행 자동 점검을 손으로 적어 쓰는 프로젝트를 hooks/hooks.json 에 맞춘다.

🔴 2026-10-28 대표님 «34분 전 새로 고침 — 이 대화를 진행하고 있는데 업데이트가 안 되는 것 같아»:
  야간비행 저장소의 설정에 턴 끝 «조종석 올리기»(board_push.sh)가 빠져 있어 이 대화 내내 조종석 자료가 안 올라갔다.
  가계부 · 그런 어른도 빠져 있었고(가계부 조종석 «1일 전»), 그런 어른은 대화 시작 점검도 없었다.
  ⛔ hooks.json 이 바뀌어도 손으로 적은 설정은 따라오지 않는다 — 사람 기억에 안 맡기고 이 도구가 맞춘다.

받는 것: argv[1] = 프로젝트 폴더 · [--보기] (바꾸지 않고 빠진 것만 말한다).
하는 것: hooks.json 의 사건마다 명령을 이 플러그인의 진짜 경로로 바꿔, 설정에 없으면 더한다.
  ⛔ 설정에 이미 있는 다른 점검(다른 도구의 것)은 그대로 둔다 · 지우지 않는다 · 순서는 hooks.json 대로 뒤에 붙인다.
  ⛔ 야간비행 점검이 하나도 없는 설정(플러그인으로 깐 프로젝트)은 건드리지 않는다 — 플러그인이 이미 붙인다.
"""
import json, os, sys

여기 = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
root = sys.argv[1] if len(sys.argv) > 1 else ""
보기만 = "--보기" in sys.argv
설정 = os.path.join(root, ".claude", "settings.json")
if not root or not os.path.isfile(설정):
    sys.exit(0)

틀 = json.load(open(os.path.join(여기, "hooks", "hooks.json"), encoding="utf-8")).get("hooks", {})
try:
    d = json.load(open(설정, encoding="utf-8"))
except (OSError, ValueError):
    print("  ⚠️ 설정 파일을 읽지 못했습니다 — 바꾸지 않았습니다: " + 설정)
    sys.exit(0)
훅 = d.get("hooks") if isinstance(d.get("hooks"), dict) else {}
있는것 = [h.get("command", "") for v in 훅.values() for x in (v or []) for h in (x.get("hooks") or [])]
if not any(os.path.join(여기, "bin") in c for c in 있는것):
    sys.exit(0)


def 진짜(c):
    return c.replace("${CLAUDE_PLUGIN_ROOT}", 여기).replace('"' + 여기 + '"', 여기)


빠짐 = []
for 사건, 묶음 in 틀.items():
    for x in 묶음:
        for h in x.get("hooks") or []:
            c = 진짜(h.get("command", ""))
            이름 = os.path.basename(c.split()[-1])
            줄들 = [g.get("command", "") for y in 훅.get(사건, []) or [] for g in (y.get("hooks") or [])]
            if any(이름 in g for g in 줄들):
                continue
            빠짐.append((사건, c))
            if not 보기만:
                칸 = 훅.setdefault(사건, [])
                if not 칸:
                    칸.append({"matcher": ".*", "hooks": []})
                칸[-1].setdefault("hooks", []).append({"type": "command", "command": c})

if not 빠짐:
    sys.exit(0)
if 보기만:
    for 사건, c in 빠짐:
        print("  · 빠짐 [" + 사건 + "] " + os.path.basename(c.split()[-1]))
    sys.exit(0)
d["hooks"] = 훅
tmp = 설정 + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write("\n")
os.replace(tmp, 설정)
print("  · 자동 점검을 플러그인 목록에 맞췄습니다(" + os.path.basename(os.path.realpath(root)) + "): "
      + " · ".join("[" + 사건 + "] " + os.path.basename(c.split()[-1]) for 사건, c in 빠짐))
