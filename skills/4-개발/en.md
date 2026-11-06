# 4 Build

This file says only what this stage is for. The symptom tables, causes and the order of countermeasures come from the brain server (plan §43-6 names this file directly). Do not write them here. `tools/lint_skill_leak.py` enforces this.

## What this stage does

This is the longest stretch, and you do not talk to the user during it. Collect everything that needs a human hand and ask it once, in one batch.

Fill in the design table's slots. Each time you finish one sub-feature, change the status of its slot:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 세부상태 <feature> <sub-feature> 완료 "<how it was verified>"
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 세부상태 <feature> <sub-feature> "확인 필요" "<short label>"
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 세부상태 <feature> <sub-feature> "방법 찾는 중" "<short label>"
```

There are five statuses. Use these exact words:

- `시작 전`: not started
- `진행 중`: in progress
- `완료`: done
- `확인 필요`: needs checking
- `방법 찾는 중`: looking for a way
- A sixth mark, `넘어감` (skipped), is chosen by the user in the Test stage. Never set it yourself.

Rules:

- Attach how it was verified to every `완료`, for example "tapped it on a phone". If it is missing or says "not done", the slot is recorded as `확인 필요` with the reason "not verified".
- You cannot mark `완료` on a sub-feature that is not in the design table. When a new one comes up, get the user's confirmation and create the slot first.
- When you record finished work (`ledger.sh 됐다`), attach which sub-feature it belongs to: `--세부 "<feature> › <sub-feature>"` (repeat the option for several; use `--세부 없음` when the work belongs to no sub-feature). If that record says the work was not verified, the cockpit shows that sub-feature as `확인 필요`.
- Write the verification text and the labels in English. The Korean words in the commands are what the tool reads. Never show them to the user.

## The failure particular to this stage, in one line

"Built" and "connected" are different. Every piece works, and the gaps between them are empty. The symptom table and the order of countermeasures come from the brain server.

## How to ask the user, and tools

When you need to ask the user something, follow `${CLAUDE_PLUGIN_ROOT}/data/묻는법.en.md`. For showing a plan first, progress display, checking the screen directly and code review, follow `${CLAUDE_PLUGIN_ROOT}/data/도구쓰는법.en.md`.

## What to ask the brain server

Remedies by symptom, the module catalog, and the notice "this feature is the third one" (the third time the same kind of feature is built).

On entering this stage, query the brain server first:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/두뇌.sh" 4 <topic>
```

If you do not know the topic, pass any word. The reply lists the topics you can ask about.

- Do not save what you receive to a file. Saving it ships the know-how out to every install (plan §43-6).
- If you receive nothing, do not stop. Proceed with what you know and record that the brain server did not answer.

## Do not do these in this stage

1. Do not talk to the user. The only places to ask are decision points designed in advance.
2. Do not ask "Shall I cut or change it?". Both options shrink the product.
3. Do not go down the same path three times and then say "it can't be done".
4. If a value lives in two places, fix it by structure, not by a check. If it lives in one place, there is nothing to check.
5. Watch the disk during development too. It fills up as you work, and then work stops.
