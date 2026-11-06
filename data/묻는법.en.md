# How to ask the user

Follow this order whenever you ask the user a question, in every stage. In the Build stage, collect everything that needs a human hand and ask it once, in one batch.

Write every on-screen sentence in plain words. Do not use development names; describe what the user will experience. Plain means the level of ordinary workplace language. Do not go simpler than that: it sounds childish and reads like a translation.

## 1. Look first

- Do not ask for anything you can learn from the code, the records, what the user already said, or research.
- Show what you found as "Here is what I understood", and accept only corrections.
- Ask only what needs the user's judgment: product direction, taste, and choices whose gains and losses differ.

## 2. Check that the question deserves to be asked

Ask only when the question is one of these three:

- The answer changes what you build.
- It pins down an important assumption.
- It chooses one of several paths with different gains and losses.

Do not ask these:

- "Shall I proceed?" Show the plan and the user approves it.
- A question padded with an obviously wrong option.
- A question whose options all remove something.

## 3. Ask with a choice screen

Use the tool available:

| Tool | Question tool | Per turn | Options |
|---|---|---|---|
| Claude Code | `AskUserQuestion` | up to 4 questions | 2 to 4 |
| Codex | `request_user_input` (on only in plan mode) | up to 3 questions | 2 to 3 |
| Any other tool, or no tool | numbered list | up to 3 questions | 2 to 3 |

- Give each question a short label of at most 12 characters (this holds for both Claude Code and Codex).
- Write the question as one sentence.
- Put the recommended option on top and add "(Recommended)" at the end of its name.
- For each option, write one sentence on what changes if the user picks it.
- Do not add an "Other" option. The screen adds its own free-text field.
- If the user may not be able to answer, include "Not sure yet" as an option.
- Use multi-select only for options that can be chosen together.
- For a question that chooses a screen layout, attach a preview. This works only in Claude Code.

Codex default mode has no choice screen. Tell the user to turn on plan mode with `/plan`. If the user does not, ask one question at a time in plain text.

## 4. After the answer

- Record the answer as soon as you receive it. If you cannot record in plan mode, list it in the plan under "To record" and record it after approval.
- Record what the user wrote themselves in their own words.
- If there is no answer, or the answer is "Not sure yet", do not stop. Proceed with the recommended option, record it as an "assumption", and show it to the user.
- Before moving to the next group, remove any question the answer made unnecessary.

## 5. When to stop

Do not fix the total number of questions in advance. Stop when no product decision is left that the AI would have to make alone during development.

Plan is complete when all of these are decided:

- One-line pitch, who it is for, problem, current alternative, why now, solution, what to cut from the first release, success criteria, where to meet the first users, revenue.

Design is complete when all of these are decided:

- Page structure, interactions, tech stack, data storage, the screen shown when something fails, how to check that it is finished.

When you finish, show the user everything decided and every assumption in one place.
