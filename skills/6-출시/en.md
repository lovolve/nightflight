# 6 Launch

This file says only what this stage is for. The symptom tables, the actual procedure, the pass/fail criteria and the incident history come from the brain server (plan §43-6). Do not write them here. The body is served from the server. `tools/lint_skill_leak.py` enforces this.

## What this stage does

Decision 5: submit.

## How to ask the user, and tools

When you need to ask the user something, follow `${CLAUDE_PLUGIN_ROOT}/data/asking.en.md`. For showing a plan first, progress display, checking the screen directly and code review, follow `${CLAUDE_PLUGIN_ROOT}/data/tool_use.en.md`.

## What to ask the brain server

The checklist of the most common rejection reasons and the App Review durations come from the brain server.

On entering this stage, query the brain server first:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/brain.sh" 6 <topic>
```

If you do not know the topic, pass any word. The reply lists the topics you can ask about.

- Do not save what you receive to a file. Saving it ships the know-how out to every install (plan §43-6).
- If you receive nothing, do not stop. Proceed with what you know and record that the brain server did not answer.

## The first time you use the app store tools

Run `"${CLAUDE_PLUGIN_ROOT}/tools/asc.py" 준비` first (`준비` means set up). Use the one in the Nightflight plugin folder, not the `tools/` of the repository you are working in. If the downloaded repository has a file with the same name, that one would run. If no key exists, the command prints which steps the user has to do. If a key exists, it creates the configuration and checks that the connection works.

The user's part is only: create a key and download it, and tell you the issuer ID.

Google Play works the same way: `"${CLAUDE_PLUGIN_ROOT}/tools/gplay.py" 준비`. It guides the key steps, and when the user places the key file, it checks the connection. Store information is handled by `gplay.py meta`.

## What the AI makes for the user

- Privacy policy draft: `ledger.sh 개인정보초안`. It writes the draft from the records and the code, and leaves the fields it cannot know as `확인 필요` (needs checking). The user publishes it.
- Screenshots for the store: `SHOT_STORE=1 "${CLAUDE_PLUGIN_ROOT}/tools/shot.sh" <screens…>`. It shoots on the mid-size iPhone that Apple always accepts and cleans up the status bar. If the large size is also needed, set `SHOT_STORE_DEVICE="Pro Max"`.
- Entering store information: `"${CLAUDE_PLUGIN_ROOT}/tools/asc.py" meta`, `review-notes` and `screenshots`. Viewing needs no flag. For changing, use `set` or `upload`: they show a preview first, and you add `--confirm` only after the user says it is fine.
  - Use these only on a version that has not been submitted yet.
  - The user presses the submit button (sending to App Review) on the web.

## Do not do these in this stage

1. "Upload" and "it arrived" are two steps. Combine them and a false success slips through.
2. The user presses every action that leaves this computer for the outside.
3. Do not show the rejection text as it is. Explain what the problem is and what to fix.
4. Do not invent day counts. State a review duration only from what the gate has confirmed against the original source.
