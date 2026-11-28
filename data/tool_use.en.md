# How to use Claude Code features

Use these only when the tool exists in Claude Code. If it does not, skip it and continue the way you were working. Do not explain feature names to the user. Tell the user only the result they will experience.

## Show a plan first

- When: a big change that is not in the design table, a data structure change, a fix that spans several features.
- How: use `EnterPlanMode` to write the plan and show it, and make the changes after the user approves.
- When not: while building the design table's sub-features in order. Do not interrupt the user during the Build stage.

## Progress display

- When: a task with three or more steps, or one that takes a long time.
- How: list the steps with the to-do tool, and mark each one the moment you finish it.
- Why: the user can tell whether the work is running or has stopped.

## Check the screen directly

- When: after you build or change a web screen. Only if the desktop app's browser tool is available.
- How:
  1. Add the dev server to `.claude/launch.json`. Do not write secrets in it.
  2. Start the server with `preview_start`.
  3. Read the content and the errors with `read_page` and `read_console_messages`.
  4. Click the buttons. If something is wrong, fix it and look again.
- Take a screenshot only when the user tells you to. For anything you could not see, write "not checked visually".

## Code review

- When: before leaving the Build stage for the Test stage, and before entering the Launch stage.
- ⛔ Ask the user first and run it only after they approve. When you ask, mention that it uses more of their quota. Ask as `data/asking.en.md` says.
- How: after approval, call the `code-review` skill. If that skill does not exist, hand the review to the `code-reviewer` agent.
- If the findings come with a grade (Important, Pre-existing or Nit; Claude Code 2.1.327 or later): fix only the Important ones before moving to the next stage. Group Pre-existing and Nit as "can be fixed later", show them, and fix them only when the user asks. If there are no grades (an older version, or the `code-reviewer` agent), show everything and let the user choose.
- If the user declines, do not ask again; move on. Ask only once at the same point.

## Independent check

- When: the end-of-turn notice reports an independent check is waiting. It appears when any development or fix sub-feature is marked done.
- Meaning: a "check" is an agent separate from the AI that built the feature finding it works. The building AI's own tests passing is not a check. The user trying it themselves is a "test".
- How:
  1. Run the `independent_check.py 설명 <feature> <sub-feature>` command from the notice. It writes a brief file.
  2. Start the `feature-verifier` agent with the Agent tool. Give it only that brief file path. Do not add your own explanation or say it is done.
- `importer`: Takes over the import. It runs on the Sonnet model and uses less AI usage. Give it the guide, the records command and the product folder paths.
  3. The agent records the result. A pass marks it done. A fail, or a verdict that a person must check, leaves it marked "needs review".
- It does not block. On a fail, tell the user and continue.
- If this tool cannot start agents, tell the user the independent check could not run. Do not record the result yourself.
- If the user says a feature is also important, run `ledger.sh 중요기능 <feature>`. If they say it is not, run `ledger.sh 중요기능뺌 <feature>`.

## Dedicated agents

- `code-explorer`: use it when the answer needs wide reading of the code. It keeps the main conversation from filling up with file contents.
- `code-reviewer`: use it for a code review the user has approved.
- `feature-verifier`: use it for the independent check. Give it only the brief file path.
- Do not pass an agent's judgment on as it is. Open the files yourself and check before you relay it.

## Introduce AI tools at the moment they are needed

This reduces the cases where the user cannot use a tool simply because they did not know it existed. Tell the user it exists; the user does the choosing.

- When: the user needs an app icon, store images, an intro video or narration and has no material, or the user has decided to put an AI feature in the app.
- How: get the list with `brain.sh <current stage> 도구/이미지디자인` (or `도구/영상음성`, `도구/모델`) and introduce the tools as that guidance says. Take the answer as options, the way `data/asking.en.md` says.
- Introduce a tool only once for the same task. If the user has said "stop these suggestions", do not introduce any.
- Do not state prices. Do not sign up or pay on the user's behalf.

## When the permission check blocks a command

- If the permission check blocks a command, do not tell the user to run it in the terminal themselves.
- Say in one sentence what was blocked. Ask in the chat whether they want it done.
- If they say yes, try again. If it is blocked again, say so and stop.

## Work that takes more than a minute (research, import, diagnosis)

If one line sits unchanged for minutes, the user just waits. Show what you find as you find it, and let them leave.

1. At the start, give the expected time as a range. Example: "This takes about 3–5 minutes. You can do something else. I will let you know when it is done."
2. Record it with `ledger.sh 하는중 "<task>" --화면 "<a «~하는 중» phrase in the user's language — e.g. checking this computer>" --예상 "3–5 min"` (a full sentence ending in «~습니다» is rejected).
3. Each time you find or finish one item, write one line in the chat. Example: "App 2/5 — X: $9/month · in-app payment."
4. Record the same line with `ledger.sh 찾음 "<that line>"`. It stacks under "Current task" in the cockpit.
5. If the result is not what was expected, say so right away. Do not save it for the end.
6. When a big step ends, run `ledger.sh 하는중끝` to mark it done, then `ledger.sh 조종석지금` to update the cockpit.
7. When done, if the `PushNotification` tool exists, send one line. Example: "App research done — 3/5 paid · one decision needed." The tool skips it if the user is watching.

- Do not promise remaining time. Give only the range at the start.
- Do not stretch time to look busy. If nothing is found yet, say what you are actually doing: "Still searching — reading X."
