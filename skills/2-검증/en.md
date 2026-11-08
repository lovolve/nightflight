# 2 Validate

This file says only what this stage is for. The symptom tables, the actual procedure, the pass/fail criteria and the incident history come from the brain server (plan §43-6). Do not write them here. The body is served from the server. `tools/lint_skill_leak.py` enforces this.

## What this stage does

Decision 2: proceed, revise or drop. The user makes it.

## How to ask the user, and tools

When you need to ask the user something, follow `${CLAUDE_PLUGIN_ROOT}/data/asking.en.md`. For showing a plan first, progress display, checking the screen directly and code review, follow `${CLAUDE_PLUGIN_ROOT}/data/tool_use.en.md`.

## What to ask the brain server

The red team brief and the criteria for checking against store policies come from the brain server.

On entering this stage, query the brain server first:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/brain.sh" 2 <topic>
```

If you do not know the topic, pass any word. The reply lists the topics you can ask about.

- Do not save what you receive to a file. Saving it ships the know-how out to every install (plan §43-6).
- If you receive nothing, do not stop. Proceed with what you know and record that the brain server did not answer.

## Do not do these in this stage

1. Do not issue a verdict. Supply the material; the user reaches the conclusion.
2. Do not flatter. Never describe a weak point as a good one.
3. Do not raise a concern from reading a policy alone. First look at apps that do the same thing (the same action, not just the same category).
4. If you could not check something, say "not checked" and then continue.

## How to record a checked item

When you confirm one row of the validation table, record it in this form. The cockpit draws the conclusion in the box on top and the evidence as name-value pairs.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 세부상태 "<group>" "<item>" 완료 "<conclusion> — <evidence name>: <value> · <evidence name>: <value> (source)"
```

`세부상태` sets the status of a sub-feature, and `완료` means done.

- The conclusion is a fact you found, for example "the top complaint about the #1 app is ads". Do not write a verdict such as proceed or drop (rule 1 above).
- Write the group, item, conclusion, evidence names and values in English. The Korean words in the command are what the tool reads. Never show them to the user.
- Keep the " — " separator. Without it, the cockpit shows the evidence with no conclusion box.
