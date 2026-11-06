#!/usr/bin/env python3
"""같은 증상이 몇 번째인지 세어 모델에게 알린다 — 되풀이를 끊는 자리."""
import json, os, sys
base, n, first = sys.argv[1], sys.argv[2], sys.argv[3] == "1"


seen = f"🔴 같은 자리를 {n}번째 고치고 있습니다."
try:
    with open(os.path.join(os.environ.get("NIGHTFLIGHT_HOME") or os.path.expanduser("~/.nightflight"), "언어"), encoding="utf-8") as _언어파일:
        if _언어파일.read(2) == "en":
            seen = f"🔴 The same place has now been changed {n} times."
except OSError:
    pass

_꼬리 = (
    "⭐ 사용자 화면에는 「같은 자리를 N번째 고치고 있습니다」 한 줄만 갔습니다.\n"
    "   그러니 「제가 알아서 하고 넘어가는」 선택지는 없습니다 — 멈춘 것을 이미 보셨습니다.\n"
) if first else (
    "🔴 **이미 한 번 멈추라고 했는데 계속 고쳤습니다.** 그래서 이번에는 사용자 화면에\n"
    "   **아무것도 안 갔습니다** — 같은 문장이 반복되면 옆의 다른 알림까지 묻히기 때문입니다.\n"
    "   사용자는 **처음 한 번 이미 보셨습니다.** 지금 멈추고 여쭙는 것 말고는 선택지가 없습니다.\n"
)

tell = (
    f"🔴 반복 감지 — 「{base}」를 이번 세션에 {n}번 고쳤습니다.\n"
    "오류가 안 났다고 해서 맞는 방향인 것은 아닙니다. 여기서 한 번 멈춥니다.\n"
    "\n"
    "1. 계속 고치지 말고 **무엇이 아닌지/무엇이어야 하는지**를 먼저 적어 보세요.\n"
    "2. 무엇이어야 하는지를 모르겠으면 **직접 만들지 말고 레퍼런스를 2~3갈래로 모아**\n"
    "   사용자에게 고르거나 섞게 하세요(화면은 레퍼런스부터 — 내 취향으로 바로 그리지 않습니다).\n"
    "3. 여쭐 때는 **번역**합니다 — 기술 사실이 아니라 **제품에서 무엇이 달라지는지**와\n"
    "   **왜 이것이 사용자 결정인지**를 말합니다. API·프레임워크 이름은 접어 둡니다.\n"
    "4. 선택지에 **빼기만 두지 않습니다**(다른 방법 / 작게 / 다음 버전 / 큰 공사 / 빼기는 맨 마지막).\n"
    "\n"
    + _꼬리 +
    "   이어서 결정 카드를 띄웁니다 — 무엇을 «안 여쭙고» 처리했는지가 거기서만 보입니다.\n"
    "   ⚠️ **막지 못했으므로 「막음」으로 적지 않습니다.** 적을 것이 있으면\n"
    "      실제로 바꾼 것을 «그 종류»로 적으십시오(「막음」은 막은 것만입니다).\n"
    "\n"
    "근거: 어느 앱에서 통화 카드 3번·배경 8번을 «오류 없이» 만들고 버렸습니다."
)

out = {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": tell}}
if first:
    out["systemMessage"] = seen
print(json.dumps(out, ensure_ascii=False))
