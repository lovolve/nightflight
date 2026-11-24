# 5 Test


## What this stage does

Decision 4: check the screens.

**Do every check you can do yourself first.** Test slots come in two groups.
- `AI가 하는 확인` (AI checks): one full run from launch to finish · automated tests pass · no buttons that do nothing or screens with no way in · screens shown on failure · other screen sizes
- `직접 하실 확인` (checks for the user): a real phone · real account sign-in and live payment · finding what feels awkward. They show right away under "test it yourself" in the cockpit.
Do not hand AI checks to the user. Only when you tried and got stuck, hand it over with `ledger.sh 세부상태 <feature> <sub> "확인 필요" "직접 — <why it is blocked>"`.
A stage ends when nothing is left that AI can do now. Checks for the user and waits for an outside answer (`ledger.sh 세부언제`) do not hold the stage; they carry over to the next stage.

## How to ask the user, and tools

When you need to ask the user something, follow `${CLAUDE_PLUGIN_ROOT}/data/asking.en.md`. For showing a plan first, progress display, checking the screen directly and code review, follow `${CLAUDE_PLUGIN_ROOT}/data/tool_use.en.md`.

## What to ask the brain server

The list of what must be checked on a phone comes from the brain server.

On entering this stage, query the brain server first:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/brain.sh" 5 <topic>
```

If you do not know the topic, pass any word. The reply lists the topics you can ask about.

- Do not save what you receive to a file. Saving it ships the know-how out to every install.
- If you receive nothing, do not stop. Proceed with what you know and record that the brain server did not answer.

## Do not do these in this stage

1. Take a screenshot only when the user tells you to. One screenshot takes 1 to 2 minutes, and the user waits that whole time.
2. Do every check that needs no screenshot. For anything you could not see, write "not checked visually".
3. Stop after two simulator failures. Report what you tried to do and what the error was.
4. Use `${CLAUDE_PLUGIN_ROOT}/tools/shot.sh`. Do not assemble the commands yourself. For an Android app it hands over to the emulator tool (`tools/shot_android.sh`) by itself. For an app that ships on both iPhone and Android, add `SHOT_PLATFORM=android` to shoot the Android side.
