# 5 Test


## What this stage does

Decision 4: check the screens.

**Do every test you can do yourself first.** Do not call these "checks" — a check is only what an agent separate from the building AI verified. Test slots come in two groups.
- `AI가 하는 테스트` (AI tests): one full run from launch to finish · automated tests pass · no buttons that do nothing or screens with no way in · screens shown on failure · other screen sizes · on-screen guidance matches what the app does · no freezes or lost data in bad situations · state combination tests, riskiest features first · AI answers stay consistent across three runs (only for products with an AI feature) · independent check by a separate AI
- `직접 하실 테스트` (tests for the user): a real phone · real account sign-in and live payment · finding what feels awkward. They show right away under "test it yourself" in the cockpit.
Do not hand AI tests to the user. Only when you tried and got stuck, hand it over with `ledger.sh 세부상태 <feature> <sub> "확인 필요" "직접 — <why it is blocked>"`.
A stage ends when nothing is left that AI can do now. Checks for the user and waits for an outside answer (`ledger.sh 세부언제`) do not hold the stage; they carry over to the next stage.

## Make AI tests visible

Do not test silently in the background. The user should see what is being tested, why, and how far along it is, in the cockpit and in the conversation.

1. At the start, show the AI test list once — one line per item: what and why. Say the why like this:
   - One full run from launch to finish — checks that the path a user actually takes connects all the way (catches breaks between features that each work alone)
   - On-screen guidance matches what the app does — checks that what screens, descriptions, and the sales page promise actually works
   - No buttons that do nothing or screens with no way in — finds spots where nothing happens or the user can never move on
   - No freezes or lost data in bad situations — trigger each failure situation recorded as `처리` in design (`ledger.sh 실패점검목록`) for real, and check that what the user sees matches what was recorded
   - State combination tests, riskiest features first — starting with features tied to money, law, or things that cannot be undone, walk every path in the design's state diagram (`ledger.sh 상태목록`) once (catches cases where each feature works alone but some order of steps gets stuck)
   - AI answers stay consistent across three runs — ask the app's AI feature the same question three times and check that the form and meaning of the answers match (one correct answer can be luck)
   - Independent check by a separate AI — an AI that did not build the app uses it like a first-time user and looks for breakage
2. When you start an item, record `ledger.sh 하는중 "<item name> (<n>/<total>)" --화면 "<item name> 테스트하는 중 (<n>/<total>)"`. It shows right away under "Now" in the cockpit.
3. Record each finding as you go with `ledger.sh 찾음 "<one line>"`. If it is a defect, fix it and run that item again.
4. When an item is done, record `ledger.sh 세부상태 "AI가 하는 테스트" "<item name>" 완료 "<what you ran and what you saw>"` and `ledger.sh 하는중끝`, and tell the user in one line: "Done — N findings."
5. "Independent check by a separate AI" comes last. Use the Agent tool to start two separate agents: (1) use the app from start to finish, (2) bad situations over several days of use. Do not pass on the building AI's judgment that it is "done". It is complete when both report zero high-severity findings. If your tool cannot start agents, tell the user "I could not run the independent check" and leave it as `확인 필요`.
6. When all AI tests are done, give the user the "tests to do yourself" as to-dos — for each, what to do, how, and about how many minutes. These stay as remaining work even after moving to the next stage.

## How to ask the user, and tools

When you need to ask the user something, follow `${CLAUDE_PLUGIN_ROOT}/data/asking.en.md`. For showing a plan first, progress display, checking the screen directly and code review, follow `${CLAUDE_PLUGIN_ROOT}/data/tool_use.en.md`.

## What to ask the brain server

The list of what must be checked on a phone comes from the brain server.

On entering this stage, query the brain server first:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/brain.sh" 5 <topic>
```

If you do not know the topic, pass any word. The reply lists the topics you can ask about.

- Do not save the guidance you receive to a file. Always use the latest version from the server.
- If you receive nothing, do not stop. Proceed with what you know and record that the brain server did not answer.

## Do not do these in this stage

1. Take a screenshot only when the user tells you to. One screenshot takes 1 to 2 minutes, and the user waits that whole time.
2. Do every check that needs no screenshot. For anything you could not see, write "not checked visually".
3. Stop after two simulator failures. Report what you tried to do and what the error was.
4. Use `${CLAUDE_PLUGIN_ROOT}/tools/shot.sh`. Do not assemble the commands yourself. For an Android app it hands over to the emulator tool (`tools/shot_android.sh`) by itself. For an app that ships on both iPhone and Android, add `SHOT_PLATFORM=android` to shoot the Android side.
