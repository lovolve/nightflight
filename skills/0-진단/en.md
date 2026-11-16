# 0 Diagnose

This file says only what this stage is for. The symptom tables, the actual procedure, the pass/fail criteria and the incident history come from the brain server (plan §43-6). Do not write them here. The body is served from the server. `tools/lint_skill_leak.py` enforces this.

## What this stage does

Read the chip, operating system, disk, accumulated files, development tools, simulators and phone. Ask the user zero questions.

## How to ask the user, and tools

When you need to ask the user something, follow `${CLAUDE_PLUGIN_ROOT}/data/asking.en.md`. For showing a plan first, progress display, checking the screen directly and code review, follow `${CLAUDE_PLUGIN_ROOT}/data/tool_use.en.md`.

## What to ask the brain server

`${CLAUDE_PLUGIN_ROOT}/tools/app_preflight.sh` runs the checks. The thresholds and the remedies come from the brain server.

On entering this stage, query the brain server first:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/brain.sh" 0 <topic>
```

If you do not know the topic, pass any word. The reply lists the topics you can ask about.

- Do not save what you receive to a file. Saving it ships the know-how out to every install (plan §43-6).
- If you receive nothing, do not stop. Proceed with what you know and record that the brain server did not answer.

## Do not do these in this stage

1. Do not end with "not enough". For each blocked item, give one action that undoes the block.
2. Do not ask about anything a machine can read.
3. For what you cannot read, do not ask a question. Give a notice that says only when it will be needed.
4. Do not end with "this won't work". Give the path that does work (Android, web) alongside.
