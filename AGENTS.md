# 야간비행 — 어느 AI 도구에서든 같은 규칙

> ⛔ **먼저 읽을 것**: [규칙 0 — 사용자는 비개발자다](RULE-0.md)

## 이 파일이 `AGENTS.md` 인 이유 (범용화, 2026-10-03)

⭐ 처음부터 **범용**으로 만든다.

⚠️ 아래 표는 **이 저장소(플러그인을 만드는 곳)를 열었을 때**의 이야기다. 플러그인으로 깔리면 이 파일은 도구의
   플러그인 보관 폴더 안에 놓여 **어느 도구도 프로젝트 규칙으로 읽지 않는다.** 받는 분이 `bin/setup_new_app.sh` 를 돌리면
   그 앱 맨 위에 `AGENTS.md` 를 따로 심는다(스킬·훅이 부르지 않는다 — 손으로 돌리는 도구다)(2026-10-25 코드 품질 레드팀 ⑥ — 표의 ✅ 가 어느 자리 기준인지 없었다).

| 도구 | 이 파일(`AGENTS.md`)을 읽나 |
|---|---|
| 클로드 코드 | ✅ `CLAUDE.md` 가 없으면 **`AGENTS.md` 를 직접 읽는다** |
| Codex CLI | ✅ 처음부터 `AGENTS.md` 다 |
| Gemini CLI | ✅ 설정으로 가리킨다 |
| Cursor | ✅ 프로젝트 뿌리의 `AGENTS.md` 를 읽는다 — *"an alternative to `.cursor/rules`"* (공식 문서, 2026-10-03 확인) |

⛔ **Windsurf 를 지웠다**(2026-10-03). 그 이름의 제품이 **없다** — `windsurf.com` 이 `devin.ai/desktop`
   으로 **308 영구 이전**된다(내가 직접 재서 확인). 후속 제품은 훅 이름 열두 개가 전부 다르고
   자리도 다르다. ⚠️ Cascade 종료일(2026-07-01)은 레드팀이 찾은 것이고 **내가 재확인하지 않았다.**
   ⭐ 「지원 목록」에 **없는 제품이 적혀 있는 것**이 범용화의 전형적 사고다 — 목록은 손으로 유지되고
      제품은 우리 허락 없이 사라진다.

⛔ **`CLAUDE.md` 를 따로 두지 않는다.** 두 벌이 되면 그게 「이식한 스크립트」 함정이다.

## 무엇이 도구와 «무관»한가 (실측 2026-10-03)

| 부품 | 범용 |
|---|---|
| **두뇌 서버**(원격 MCP — 유료·노하우·과금) | ✅ MCP 는 Linux Foundation 표준. 주요 클라이언트가 모두 받는다 |
| **검사**(`tools/lint_*.py` — 수는 폴더가 말한다) | ✅ 순수 파이썬. 루트·기록은 `tools/_root.py` 가 도구 없이 찾는다 |
| **훅 스크립트** | ✅ Codex 는 클로드와 **이벤트 이름·stdin JSON 모양이 같아 안 고치고 돈다**. Cursor 는 이름이 다르다 |
| 기록 · 조종석 · 턴 줄 · 자원 점검 | ✅ 셸·HTML. `bin/project-root.sh` 가 같은 일을 한다 |
| 🔴 스킬 형식 · 서브에이전트 | ⚠️ 도구별. **다만 노하우가 서버에 있어 틀만 다시 쓴다** |

## 기록은 어디 사나
`.nightflight/` 가 기본이고 **기존 앱의 `.claude/` 도 읽는다**(`tools/_root.py` · `bin/project-root.sh`).
⛔ **경로를 코드에 박지 않는다.**

## 훅 이벤트는 «공통 이름»만 쓴다
`SessionStart` · `UserPromptSubmit` · `PostToolUse` · `Stop` — 클로드와 Codex 가 같은 이름으로 받는다
(`hooks/hooks.json` 이 쓰는 넷 그대로 · Codex 쪽 근거는 아래 «플러그인으로 깔리는 것»의 `protocol/src/hooks.rs`).
Cursor 는 이름이 다르다 — 그래서 아래 표에서 «아직 모른다»다.
⛔ 한쪽에만 있는 이름을 쓰면 그 순간 범용성이 깨진다.

## 플러그인으로 깔리는 것 — 어디까지 되나 (2026-10-25 공식 소스로 확인)

⚠️ 맨 위 표(«이 파일을 읽나»)와 **다른 질문**이다 — 제미나이·커서는 규칙 파일은 읽지만, 플러그인 꼴로 깔리는 것은 아직 아니다/모른다.

| 도구 | 플러그인으로 깔리나 | 무엇으로 확인했나 |
|---|---|---|
| 클로드 코드 | ✅ | `claude plugin validate` 통과 |
| **Codex CLI** | ✅ **그대로 된다** | `openai/codex` 소스 넷(아래) |
| Gemini CLI | ⛔ **아직 아니다** | 사건 이름이 다르다(아래) |
| Cursor | ⛔ **아직 모른다** | 찾는 자리만 봤다 |

⭐ **Codex 가 되는 까닭 — 넷 다 공식 소스에서 읽었다.**
- `exec-server-protocol/src/protocol.rs` 의 `DISCOVERABLE_PLUGIN_MANIFEST_PATHS` 에
  `.codex-plugin/plugin.json` · **`.claude-plugin/plugin.json`** · `.cursor-plugin/plugin.json` 이 있다
- `hooks/src/declarations.rs` 가 `plugin_root.join("hooks/hooks.json")` 을 읽는다 — **우리와 같은 자리**
- `protocol/src/hooks.rs` 의 사건 이름이 `UserPromptSubmit`·`SessionStart`·`Stop`·`PostToolUse` — **같다**
- `hooks/src/engine/discovery.rs` 가 `CLAUDE_PLUGIN_ROOT` 를 **일부러** 넣어 준다
  (*"For OOTB compat with existing plugins that use this env var."*)

⛔⛔ **`hooks.json` 에 「`// 왜 …`」 열쇠를 두지 마라.** JSON 에 주석이 없어서 그렇게 적어 뒀었는데,
   Codex 의 `HooksFile` 에 `deny_unknown_fields` 가 걸려 있어 **맨 위의 그 열쇠 하나로 파일 전체가
   거절된다** — Codex 에서 훅이 **하나도** 안 붙을 상태였다(2026-10-25 발견).
   ⭐ 「왜」는 `hooks/왜.md` 에 있다. 글자를 줄이지 않고 **자리만** 옮겼다. 묶음 절 94 가 지킨다.

⛔ **Gemini CLI 는 사건 이름이 다르다** — `UserPromptSubmit` → `BeforeAgent` ·
   `Stop` → `SessionEnd` · `PostToolUse` → `AfterTool`. 훅 파일 자리는 같은 `hooks/hooks.json` 인데
   경로 변수가 `${extensionPath}` 라 **한 파일에 두 변수를 같이 적을 수 없다**
   (`docs/extensions/reference.md`: *"hooks are not defined in the `gemini-extension.json` manifest"*).
   내보내는 꼴은 같다(`additionalContext` · `decision: "deny"` · `continue: false`).
   ⭐ 2026-10-25 — **이 컴퓨터에 그 도구가 없어 돌려 볼 수 없으므로 안 넣는다.**
     깔아서 재 볼 수 있게 되면 그때 한다. ⛔ 안 돌려 본 등록 파일을 배포물에 넣지 않는다.
