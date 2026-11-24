---
description: 야간비행 조종석을 엽니다 / Open the Nightflight cockpit
allowed-tools: ["Bash", "mcp__Claude_Browser__preview_start", "Artifact", "mcp__ccd_view__show_pane"]
---

# 조종석 열기 / Open the cockpit

- 안내: !`"${CLAUDE_PLUGIN_ROOT}/bin/board_push.sh" --지금만들기 "${CLAUDE_PROJECT_DIR:-$PWD}"`

위 「안내」에 적힌 것을 **그대로 한 번만** 하십시오. 안내가 비어 있거나 경로를 찾지 못했다고 하면,
돌고 있는 야간비행 플러그인의 `bin/board_push.sh` 를 찾아 같은 인자로 다시 부르십시오.

- 브라우저 칸 주소(`http://127.0.0.1:…`)를 주면 → `mcp__Claude_Browser__preview_start` 를 그 url 로 한 번
- 아티팩트 주소를 주면 → `Artifact` action `open` 으로 그 url
- 등록되지 않은 폴더라고 하면 → 그 말을 사용자에게 그대로 전하고 멈추십시오

⛔ 조종석 화면을 스크린샷으로 찍지 마십시오 — 보는 것은 사용자입니다.
⛔ 안내에 없는 길로 열지 마십시오(다른 창 · 크롬 · 직접 띄우기). 로그인을 다시 하게 됩니다.
⛔ 조종석을 열고 나서 다른 일을 덧붙이지 마십시오. 이 명령은 여는 것까지입니다.

Do exactly what the "안내" line above says, once. Do not take a screenshot of the cockpit.
