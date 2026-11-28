# 3 Design


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
- When you enter planning or design, a checklist of features most apps have but plans often miss arrives. Propose the rows that apply **before the user asks**, and record each answer: `ledger.sh 빠진기능 "<item>" 넣음|해당없음|다음번 "<why>"`. Without these records, the missing-features check shows as unfinished when you close the Design stage.
- The cockpit's progress shows how far these slots are filled. Never report progress from the log of finished work.

## Screen flow: the cockpit's "screen flow" is drawn from these commands

A flow diagram carries good information but looks unfamiliar. Being understood at once comes before good information. So the cockpit shows one line per thing the user does, and opens only the clicked line as a phone-screen drawing. Clicking a screen opens its screen spec below.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면 <short name> "<one-line description>"
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면이름 <screen> "<full name>"
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면언제 <screen> "<when the user sees this screen>"
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면하는일 <screen> "<what the user does here>"
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면요소 <screen> "<what is visible>" <feature> [sub-feature]
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 화면그림 <screen> <element number> 글|제목|버튼|입력|목록|사진|그래프|숫자판|탭|비움 "<the exact words shown on screen>"   # right after each element
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
- `화면그림` records how that element looks and the exact words on screen. Kinds: `글` text, `제목` title, `버튼` button, `입력` input, `목록` list, `사진` photo, `그래프` chart, `숫자판` keypad, `탭` tabs, `비움` blank. Record it right after each element. The cockpit draws the screen picture from these words; without them it shows only a list of what the screen contains. Do not ask the user to write the words: write them from the plan and the task, and let the user correct them on the picture.
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
- Every screen must belong to some task. The end-of-conversation check reports screens that belong to no task, and tasks that point to a screen that does not exist.

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

- Do not save the guidance you receive to a file. Always use the latest version from the server.
- If you receive nothing, do not stop. Proceed with what you know and record that the brain server did not answer.

## After the features are confirmed: record the map between features

"I know every place to change" does not mean you analyze the code to find them when the user asks for a fix. It means you build the map during design, and when a fix comes, you check against that map. So the design must include the map of parts: how features connect, where they collide, and in what order they run.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 영향 <feature being changed> <feature to check with it> "<kind>: <what>" 리서치 --화면 "<what the user experiences>" --종류 "사용자에게 보이는 것"   # if not visible: --종류 "안 보이는 작업"
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

## Failure situations — cover every feature

The state diagram check only finds dead ends in what was written down. If a failure state was never written, it cannot see it. So go through a fixed list of failure kinds for each feature.
1. Run `ledger.sh 실패점검목록` (failure check list). For each feature to build, it shows the failure kinds not yet covered (lost connection, server error, permission denied, bad input, double taps and simultaneous use, reopening the app, an outside service refusing, storage).
2. For each feature and kind, record `ledger.sh 실패점검 "<feature>" <kind id[,…]|전부> 처리|해당없음 "<how it is handled and what the user sees · or why it does not apply>" [사용자|내판단]` (`처리` = handled, `해당없음` = does not apply, `내판단` = decided by the AI).
3. Follow the failure policies decided in planning. Anything not asked, or answered `모름`, is decided with the standard approach and recorded as `내판단`.
4. When done, show the user a summary in one go — show the "decided by AI" group first and ask whether they want to change anything.
5. Anything recorded as `처리` also goes into the state diagram (`ledger.sh 상태`) as a failure state and where it leads.
Do not move on to development until every kind is recorded for every feature. In the test stage, the "no freezes or lost data in bad situations" item runs each `처리` line for real.

## How to ask the user

When you need to ask the user something, first read `${CLAUDE_PLUGIN_ROOT}/data/asking.en.md` and ask exactly as it says: options per item, the recommended option on top, and "Not sure yet".

Ask in groups: page structure, interactions, tech stack, data storage, failure screens.

Never ask about the tech stack by tool name. Ask by the result the user gets, and put the tool name in parentheses at the end of the option description.

Write the text in quotes in these commands in English. The Korean words in the commands are what the tool reads. Never show them to the user.

## Undecided items and pass checks

- Do not fill in what the user has not decided with a guess. Record it with `ledger.sh 안정함 "<what>" "<what you would have guessed>"`. It shows at the top of the cockpit decisions.
- When the user decides, run `ledger.sh 안정함 정함 <number> "<decision>"` and also record the decision.
- For each sub-feature to build, write one pass check: `ledger.sh 합격기준 "<feature>" "<sub-feature>" "<when this is done → this happens>"`. You write the draft. Only for important features (payment, login, personal data, server permissions), confirm it with the user using choices.
- Without a pass check, development on that sub-feature is blocked. If the user chooses "proceed without a check", run `ledger.sh 기준없이진행 "<feature>" 기준 "<their words>"` and continue (use `표준` the same way when there is no standard method).

## Do not do these in this stage

1. Do not draw from your own taste right away. Collect references first.
2. "It feels like X" is reference language. It means bring that reference, not remake it.
3. For the first release, the minimum is the default.
4. Do not show the technical design. Give only the result: "I can build it" or "It is hard, because …".
5. Do not turn the user's words into a finished product by your own interpretation. Offer two or three directions for the user to choose from or combine.
6. Do not stop at a feature list. If you record the points and not the lines between them, "fixing one thing breaks another" stays exactly as it is.
