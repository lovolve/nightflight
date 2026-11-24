#!/usr/bin/env python3
"""사용자가 허락하면 대화 용량 · 한도를 표시한다 — 터미널은 상태줄, 앱은 입력창 위."""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nf_paths



def _마켓() -> "str | None":
    판 = Path(__file__).resolve().parent.parent
    이름 = None
    if 판.parent.name == "nightflight" and 판.parent.parent.parent.name == "cache":
        이름 = 판.parent.parent.name
    else:
        try:
            이름 = json.loads((판 / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")).get("name")
        except (OSError, ValueError, AttributeError):
            이름 = None
    return 이름 if isinstance(이름, str) and re.fullmatch(r"[A-Za-z0-9._-]{1,80}", 이름) else None


마켓 = _마켓()
집 = nf_paths.사람집()
설정길 = 집 / ".claude" / "settings.json"
다리길 = nf_paths.집() / "statusline_bridge.sh"
우리명령 = f'"{다리길}"'
우리명령들 = {우리명령, f'"{집 / ".nightflight" / "statusline_bridge.sh"}"'}
옛명령 = f'"{집 / ".nightflight" / "상태줄.sh"}"'
앱표시길 = nf_paths.집() / "app_display_on"
다리글 = f"""#!/bin/sh
f=$(ls -d "$HOME"/.claude/plugins/cache/{마켓}/nightflight/*/bin/statusline.sh 2>/dev/null | sort -V | tail -1)
[ -n "$f" ] && exec "$f"
exit 0
"""


def 적기(값: dict) -> None:
    대상 = Path(os.path.realpath(설정길))
    대상.parent.mkdir(parents=True, exist_ok=True)
    try:
        권한 = 대상.stat().st_mode & 0o7777
    except OSError:
        권한 = None
    with tempfile.TemporaryDirectory(dir=대상.parent) as 임시터:
        임시 = os.path.join(임시터, "new_version")
        with open(임시, "w", encoding="utf-8") as f:
            json.dump(값, f, ensure_ascii=False, indent=2)
            f.write("\n")
        if 권한 is not None:
            os.chmod(임시, 권한)
        os.replace(임시, 대상)


명령 = sys.argv[1] if len(sys.argv) > 1 else "상태"
try:
    설정 = json.loads(설정길.read_text(encoding="utf-8")) if 설정길.exists() else {}
    if not isinstance(설정, dict):
        raise ValueError
except (OSError, ValueError):
    print("설정 파일을 읽지 못해 아무것도 바꾸지 않았습니다.")
    sys.exit(1)
지금 = 설정.get("statusLine")
우리것 = isinstance(지금, dict) and 지금.get("command") in (우리명령들 | {옛명령})

if 명령 == "켜기" and 마켓 is None:
    print("야간비행이 깔린 자리를 알 수 없어 아무것도 바꾸지 않았습니다.")
    sys.exit(1)
if 명령 == "켜기":
    앱표시길.parent.mkdir(parents=True, exist_ok=True)
    앱표시길.touch()
    if 지금 and not 우리것:
        print("앱 표시를 켰습니다. 명령어 창에서는 이미 다른 상태줄을 쓰고 계셔서 바꾸지 않았습니다. 끄려면 «상태줄 꺼줘»라고 말씀해 주십시오.")
        sys.exit(0)
    다리길.parent.mkdir(parents=True, exist_ok=True)
    다리길.write_text(다리글, encoding="utf-8")
    다리길.chmod(0o755)
    설정["statusLine"] = {"type": "command", "command": 우리명령, "padding": 0}
    적기(설정)
    print("켰습니다. 앱에서는 입력창 위, 명령어 창에서는 화면 아래에 표시됩니다. 앱은 다음 응답부터, 명령어 창은 다음 실행부터 적용됩니다. 끄려면 «상태줄 꺼줘»라고 말씀해 주십시오.")
elif 명령 == "끄기":
    앱켜짐 = 앱표시길.exists()
    if 앱켜짐:
        앱표시길.unlink()
    if not 우리것:
        print("앱 표시를 껐습니다." if 앱켜짐 else "야간비행 표시가 켜져 있지 않습니다.")
        sys.exit(0)
    del 설정["statusLine"]
    적기(설정)
    print("껐습니다. 앱과 명령어 창 모두 표시하지 않습니다.")
else:
    print("켜짐" if 우리것 else ("다른 상태줄" if 지금 else "꺼짐"))
