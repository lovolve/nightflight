# 5 Test

This file says only what this stage is for. The symptom tables, the actual procedure, the pass/fail criteria and the incident history come from the brain server (plan §43-6). Do not write them here. The body is served from the server. `tools/lint_skill_leak.py` enforces this.

## What this stage does

Decision 4: check the screens.

## How to ask the user, and tools

When you need to ask the user something, follow `${CLAUDE_PLUGIN_ROOT}/data/asking.en.md`. For showing a plan first, progress display, checking the screen directly and code review, follow `${CLAUDE_PLUGIN_ROOT}/data/tool_use.en.md`.

## What to ask the brain server

The list of what must be checked on a phone comes from the brain server.

On entering this stage, query the brain server first:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/brain.sh" 5 <topic>
```

If you do not know the topic, pass any word. The reply lists the topics you can ask about.

- Do not save what you receive to a file. Saving it ships the know-how out to every install (plan §43-6).
- If you receive nothing, do not stop. Proceed with what you know and record that the brain server did not answer.

## Do not do these in this stage

1. Take a screenshot only when the user tells you to. One screenshot takes 1 to 2 minutes, and the user waits that whole time.
2. Do every check that needs no screenshot. For anything you could not see, write "not checked visually".
3. Stop after two simulator failures. Report what you tried to do and what the error was.
4. Use `${CLAUDE_PLUGIN_ROOT}/tools/shot.sh`. Do not assemble the commands yourself.
