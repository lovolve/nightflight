# 1 Plan


## What this stage does

Decision 1: confirm the plan. Confirm the target user in the same step.

## Tools

For showing a plan before a big change, progress display, checking the screen directly and code review, follow `${CLAUDE_PLUGIN_ROOT}/data/tool_use.en.md`.

## What to ask the brain server

The framework for narrowing the target user and the method for choosing benchmarks come from the brain server.

On entering this stage, query the brain server first:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/brain.sh" 1 <topic>
```

If you do not know the topic, pass any word. The reply lists the topics you can ask about.

- Do not save the guidance you receive to a file. Always use the latest version from the server.
- If you receive nothing, do not stop. Proceed with what you know and record that the brain server did not answer.

## How to ask the user

When you need to ask the user something, first read `${CLAUDE_PLUGIN_ROOT}/data/asking.en.md` and ask exactly as it says: options per item, the recommended option on top, and "Not sure yet".

Record each decision in its own field:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 제품소개 <한줄|누구|문제|대안|왜지금|해결|뺄것|성공기준|첫사용자|수익> "<the user's words, in English>"
```

The fields are: `한줄` one-line pitch, `누구` who it is for, `문제` problem, `대안` current alternative, `왜지금` why now, `해결` solution, `뺄것` what to cut from the first release, `성공기준` success criteria, `첫사용자` where to meet the first users, `수익` revenue.

Write the text in quotes in English. The Korean words in the command are what the tool reads. Never show them to the user.

## Failure policies — decide them in planning

What happens when things fail is a product question for planning, not something to leave for design. The more the user decides, the more accurate the design.
1. Run `ledger.sh 실패정책목록` (failure policy list). It shows only the questions that apply to this product (lost connection, failed payment, new phone, editing at the same time, AI failure, undoing deletes, and so on).
2. Ask them one at a time with the choice question tool — use the listed options as they are, mark the first as recommended, and include "Not sure yet".
3. Record each answer with `ledger.sh 실패정책 <id> "<chosen option>"`. If the user is not sure, record `"모름"` — the AI decides it in design using the standard approach.
Do not move on to validation until every question is recorded (`모름` counts as an answer).

## Undecided items and pass checks

- Do not fill in what the user has not decided with a guess. Record it with `ledger.sh 안정함 "<what>" "<what you would have guessed>"`. It shows at the top of the cockpit decisions.
- When the user decides, run `ledger.sh 안정함 정함 <number> "<decision>"` and also record the decision.

## Do not do these in this stage

1. Do not ask for what you can find. Fill it in by research and show a draft first.
2. Do not choose benchmarks by rating.
3. State the limit of personas whenever you use them: they are imitations. Pair them with checks against real users.
