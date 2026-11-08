# 3 Design

This file says only what this stage is for. The symptom tables, the actual procedure, the pass/fail criteria and the incident history come from the brain server (plan §43-6). Do not write them here. The body is served from the server. `tools/lint_skill_leak.py` enforces this.

## What this stage does

Decision 3: confirm the features. Sort them into include, cut and next version.

Keep every confirmed feature in the design table. Create its slots now: stage, then feature, then sub-feature. During design, list all the features to build; later stages mark them finished.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 기능추가 4 <feature>
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 기능추가 4 <feature> <sub-feature> …
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 세부기능 4 <feature> <sub-feature>
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 설계표
```

- Line 1 adds a feature. A feature that has default sub-features gets its slots created with it.
- Line 2 adds a feature with sub-features, for a feature with no defaults or when the user's plan differs from the defaults.
- Line 3 adds one more sub-feature from the plan.
- Line 4 prints the list to get confirmed.

- Get the user to confirm the list you made. What goes in and what is cut is the user's decision.
- The cockpit's progress shows how far these slots are filled. Never report progress from the log of finished work.

## Screen flow: the cockpit's "screen flow" is drawn from these commands

A flow diagram carries good information but looks unfamiliar. Being understood at once comes before good information. So the cockpit shows one line per thing the user does, and opens only the clicked line as a phone-screen drawing. Clicking a screen opens its screen spec below.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면 <short name> "<one-line description>"
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면이름 <screen> "<full name>"
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면언제 <screen> "<when the user sees this screen>"
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면하는일 <screen> "<what the user does here>"
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면요소 <screen> "<what is visible>" <feature> [sub-feature]
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면이동 <screen> <next screen> "<what the user does to go there>"
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면갈림 <screen> "<the question that branches after this screen>"
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면상태 <screen> "<state>" ["<when it moves on>"] [나쁨]
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면종류 <screen> 폰|모니터|메일
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면일 "<task>" "<when; may be empty>" <screen> ["<screen|screen>"] …
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면빼기 <screen> "<why, for example the screen was removed>"
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 기능빼기 <feature> "<why, for example the feature was removed or merged>"
```

What each command does:

- `화면` creates a screen (short name plus one-line description).
- `화면이름` sets the full name. Always set it when the short name is abbreviated.
- `화면언제` records when the user sees the screen.
- `화면하는일` records what the user does on the screen.
- `화면요소` records one visible element and the feature (and sub-feature) it belongs to.
- `화면이동` records a transition and the user action that triggers it. Writing the transition between the same two screens again changes only its condition.
- `화면갈림` records the question that branches after a screen. Use it only when the flow branches. The conditions of the transitions out of that screen are "yes" and "no · …" (written in English as the user would see them).
- `화면상태` records a state of a screen. Use it only for screens that change by time, payment or server. `나쁨` marks a bad state.
- `화면종류` sets the screen kind: `폰` phone, `모니터` monitor, `메일` email.
- `화면일` records a task and the screens it covers. In the screen list, "|" means "or".
- `화면빼기` removes a screen. `기능빼기` removes a feature.

Removing:

- Record removed screens and features with the remove commands. A removed feature or screen has to change in design, in development and everywhere they connect.
- `화면빼기` also removes the transitions into that screen and removes it from the task order.
- `기능빼기` also removes the design-table rows in every stage, the screen elements that pointed to the feature, the links and the state drawings.
- Do not delete a screen element's description and do not delete log lines by hand. The record that it was removed must stay, so that later you can tell why it is gone.

Tasks:

- Write each task in the user's words, such as "Get started", "Log what I spent", "Review this month". A task is not a feature name.
- You derive tasks from the plan, from each screen's "when seen" and from the transitions. Do not add questions to the user for this.
- Every screen must belong to some task. The end-of-conversation check reports screens that are missing and tasks that have none.

Changing screens:

- When screens change (a new screen, a removed screen, a changed transition), fix them with the same commands, even during development.
- Writing the transition between the same two screens again changes only its condition.
- If "when seen" or "task" is missing, the end-of-conversation check (`lint_screen_spec`) reports it. The cockpit then shows "Not written yet".

## Tools

For showing a plan before a big change, progress display, checking the screen directly and code review, follow `${CLAUDE_PLUGIN_ROOT}/data/tool_use.en.md`.

## What to ask the brain server

The reference topics and the measured values come from the brain server.

On entering this stage, query the brain server first:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/brain.sh" 3 <topic>
```

If you do not know the topic, pass any word. The reply lists the topics you can ask about.

- Do not save what you receive to a file. Saving it ships the know-how out to every install (plan §43-6).
- If you receive nothing, do not stop. Proceed with what you know and record that the brain server did not answer.

## After the features are confirmed: record the map between features

"I know every place to change" does not mean you analyze the code to find them when the user asks for a fix. It means you build the map during design, and when a fix comes, you check against that map. So the design must include the map of parts: how features connect, where they collide, and in what order they run.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 영향 <feature being changed> <feature to check with it> "<kind>: <what>" 리서치
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 영향목록

"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 상태 <feature> <state> <reachable states, comma-separated> user
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 상태목록
```

Link map (`영향`): "if I fix this, what else do I have to look at?"

- The kind is one of three: `같은것을쓴다` (the two hold the same thing), `순서가있다` (this one comes first), `같은화면` (on the same screen).
- The last word of the command is the source. `리서치` means research.
- `영향목록` prints the links.
- Take only what research gives you. Do not add questions to the user during design. Record only the dependencies you can see while looking at similar apps.

State map (`상태`): "which state is this feature in now, and where can it go next?"

- If there is nowhere further to go, write `끝` (end) as the destination. An empty field means "not written", not "none".
- The user can decide these. "Where does the user go if payment fails?" is a product question.
- If you decided it yourself, write the source as `내판단` (my judgment) instead of `user`. The list reports that count separately.
- `상태목록` prints the states.

If either map is empty, never say "nothing depends on it". Say "it is not written on the map". Letting 0 read as safe is worse than having no map, because people trust it and stop checking.

## How to ask the user

When you need to ask the user something, first read `${CLAUDE_PLUGIN_ROOT}/data/asking.en.md` and ask exactly as it says: options per item, the recommended option on top, and "Not sure yet".

Ask in groups: page structure, interactions, tech stack, data storage, failure screens.

Never ask about the tech stack by tool name. Ask by the result the user gets, and put the tool name in parentheses at the end of the option description.

Write the text in quotes in these commands in English. The Korean words in the commands are what the tool reads. Never show them to the user.

## Do not do these in this stage

1. Do not draw from your own taste right away. Collect references first.
2. "It feels like X" is reference language. It means bring that reference, not remake it.
3. For the first release, the minimum is the default.
4. Do not show the technical design. Give only the result: "I can build it" or "It is hard, because …".
5. Do not turn the user's words into a finished product by your own interpretation. Offer topics to choose from.
6. Do not stop at a feature list. If you record the points and not the lines between them, "fixing one thing breaks another" stays exactly as it is. One chat product hit this almost 100 times.
