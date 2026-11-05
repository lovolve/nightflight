#!/usr/bin/env python3
"""사용자가 허락하면 터미널 상태줄을 켠다 — 대화 용량 · 비용 · 한도."""
import json
import os
import sys
import tempfile
from pathlib import Path

집 = Path(os.environ.get("HOME") or Path.home())
설정길 = 집 / ".claude" / "settings.json"
다리길 = 집 / ".nightflight" / "상태줄.sh"
우리명령 = f'"{다리길}"'
다리글 = """#!/bin/sh
f=$(ls -d "$HOME"/.claude/plugins/cache/*/nightflight/*/bin/statusline.sh 2>/dev/null | sort -V | tail -1)
[ -n "$f" ] && exec "$f"
exit 0
"""


def 적기(값: dict) -> None:
    설정길.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=설정길.parent) as 임시터:
        임시 = os.path.join(임시터, "새판")
        with open(임시, "w", encoding="utf-8") as f:
            json.dump(값, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(임시, 설정길)


명령 = sys.argv[1] if len(sys.argv) > 1 else "상태"
try:
    설정 = json.loads(설정길.read_text(encoding="utf-8")) if 설정길.exists() else {}
    if not isinstance(설정, dict):
        raise ValueError
except (OSError, ValueError):
    print("설정 파일을 읽지 못해 아무것도 바꾸지 않았습니다.")
    sys.exit(1)
지금 = 설정.get("statusLine")
우리것 = isinstance(지금, dict) and 지금.get("command") == 우리명령

if 명령 == "켜기":
    if 지금 and not 우리것:
        print("이미 다른 상태줄을 쓰고 계셔서 바꾸지 않았습니다.")
        sys.exit(0)
    다리길.parent.mkdir(parents=True, exist_ok=True)
    다리길.write_text(다리글, encoding="utf-8")
    다리길.chmod(0o755)
    설정["statusLine"] = {"type": "command", "command": 우리명령, "padding": 0}
    적기(설정)
    print("상태줄을 켰습니다. 다음 응답부터 화면 아래에 보입니다. 끄려면 «상태줄 꺼줘»라고 말씀해 주십시오.")
elif 명령 == "끄기":
    if not 우리것:
        print("야간비행 상태줄이 켜져 있지 않습니다.")
        sys.exit(0)
    del 설정["statusLine"]
    적기(설정)
    print("상태줄을 껐습니다.")
else:
    print("켜짐" if 우리것 else ("다른 상태줄" if 지금 else "꺼짐"))
