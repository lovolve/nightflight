# Import

Use this skill when Nightflight was installed on an app that is already partway through development. Find each cockpit field in the existing code, documents, and commits, and fill it in. Write the evidence for everything you find. Enter features that already work as `완료` (done). Use it only in a project registered with Nightflight.

This file says what to do. The know-how (symptom tables, judging criteria) comes from the brain server.

The user does not always start with Nightflight. A product may already be under construction when it is installed. The cockpit must still end up with everything needed.

## When

Run it in the first conversation when the product already exists: there are commits, screen files, or planning notes. Run it after the computer check in phase `0-진단` (Diagnose).

Run it even if records already exist. When the end-of-conversation check (`lint_import`) reports that an app has accumulated code but its cockpit fields are empty, run it then.
Do not limit it to the first conversation. An app that had records before this feature would never be imported.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 가져오기 시작
```

## Rules for writing commands

Text values you pass to `ledger.sh` commands (names, notes, evidence, screen wording, decision text) are written in English. The Korean command words, field names, and status words in code spans are what the tool reads: keep them exactly. Never show those Korean words to the user. Describe results to the user in plain English, without commands.

## Field by field: find in the code, then fill

| Field | Where to find it | Command to record it |
|---|---|---|
| Current phase | Is it released? Are there tests? Are all screens present? | `ledger.sh 단계 "<number>. <name>"` (`단계` = phase) |
| Product name | Display name in the app, store settings | `ledger.sh 앱설정 앱이름 "<name>" 코드` (`앱설정` = app setting, `앱이름` = app name, `코드` = from code) |
| Plan table | README, CLAUDE.md, planning notes, store description, the decision records (who it is for; what it does and does not do; name; where it is sold; price) | `ledger.sh 기능추가 1 "<group>" "<item>" ...`, then for each item `ledger.sh 세부상태 "<group>" "<item>" 완료 "<what was decided (evidence)>"` (`기능추가` = add feature, `세부상태` = detail status) |
| Validate table | Research documents, competitor comparisons, the evidence behind decision records | `ledger.sh 기능추가 2 "<group>" "<item>" ...`, then `세부상태 ... 완료 "<conclusion> — <evidence name>: <value> · <evidence name>: <value> (source)"` |
| Design table | Design documents, screen list, features included and left out, decision records | `ledger.sh 기능추가 3 "<group>" "<item>" ...`, then `세부상태 ... 완료 "<what was decided (evidence)>"` |
| Feature table | Screen files, server functions, documents | `ledger.sh 기능추가 4 "<feature>" "<sub-feature>" ...` |
| Features already built | Features in the code that work | `ledger.sh 설치전 "<feature>" "<sub-feature>" "<evidence: file, passing test>"` (`설치전` = existed before install) |
| Screen flow | Screen files, navigation code | Use the "screen flow" commands of the `3-설계` (Design) skill. End with `화면일`, which records, for each task the user does, the order of screens it passes through. |
| How features affect each other | Code where two features use the same data or the same screen | `ledger.sh 영향 "<feature>" "<feature that changes with it>" "같은것을쓴다: <what is shared>" 코드` (`영향` = impact; `같은것을쓴다` = uses the same thing). If they are not linked: `ledger.sh 독립 "<feature>" "<reason>"` (`독립` = independent) |
| States per feature | State values such as paid, expired | `ledger.sh 상태 "<feature>" "<state>" "<states it can go to>" 코드` (`상태` = state) |
| Decisions | Decisions written in documents or commit messages | `ledger.sh 결정 ...`: use exactly the form in "A decision has five fields and three markers" below |
| How it is built | The way the code does things (payment, login, storage) | `ledger.sh 표준 "<method>" "<file>" 코드 "<feature>" "<tool combination>" "<failure cases the code handles>"` (`표준` = standard). If the code has no failure handling, write `없음: no handling in code`. A rule that spans several features goes to `ledger.sh 배운것` (`배운것` = lesson learned). |
| Launch procedure questions | Payment, login, platform code | `ledger.sh 앱설정 <platform, payments, or feature> "<value>" 코드` |
| Launch status | Store address, release commit, review email | `ledger.sh 앱설정 출시상태 "<not yet released, in review, or released — with evidence>" 코드` (`출시상태` = launch status) |
| Documents read | README, CLAUDE.md, AGENTS.md, docs/ | `ledger.sh 앱설정 읽은문서 "<document names — n decisions per document>" 코드` (`읽은문서` = documents read). Decisions found in the documents you read go into the Decisions field. |

### Shape of the commands: what to know before they are rejected

In an import test on a copy of an app with its records deleted, all twelve rejections came from the points below.

- Phase names: `0. 진단` (Diagnose), `1. 기획` (Plan), `2. 검증` (Validate), `3. 설계` (Design), `4. 개발` (Build), `5. 확인` (Test), `6. 출시` (Launch), `7. 수정` (Fix), `8. 출시후` (After launch).
  Record `0. 진단` first. Record the current phase last: the last line is the current phase.
  Do not record `4. 개발` or any later phase until the screen flow and the feature impact entries exist. The order is: feature table, features already built (`설치전`), screen flow, impact, phase.
- Screen wording (`--화면`) and a decision's `--값` are written as noun phrases. A clause ending in a verb is rejected (the tool checks Korean sentence endings). Example: "three screens sharing one distance value" (correct); "three screens use the same distance value" (wrong).
- The 4 in `기능추가 4` is the phase where the feature lives (4 = Build). Put the app's features at 4.
- The Plan, Validate, and Design tables (1, 2, 3) split the decisions into groups and items. Write an item's "what was decided" in the fourth field of `세부상태 ... 완료 "<text>"`. The cockpit shows this text when the user opens that phase. At the end of the text, put the evidence in parentheses (document name, file:line, decision date).
  Do not create items you did not find. If you found nothing for a whole phase, use `가져오기 없음 "<field>" "<reason>"` (`가져오기 없음` = import none).
  The Validate table has one more shape. Begin with a one-line conclusion; after " — ", join the evidence as "name: value" separated by " · ". The cockpit draws the conclusion in the box on top and the evidence as pairs. Without " — ", only the evidence shows as lines, with no conclusion box (do not make one up).
  Example: `No diary app sells monthly subscription only — apps measured: 12 Korean diary apps · monthly price: KRW 1,000 to 2,900`. The evidence is Korean-market data. Say that in the text.
- Do not use a middle dot (·) in names: feature, sub-feature, or screen names. Write "and" instead.
- Impact and standard entries need screen wording. End with `--화면 "<what the user experiences>" --종류 "사용자에게 보이는 것"` (`--종류` = kind; the value means "something the user sees"). If the user would notice no difference, use only `--종류 "안 보이는 작업"` (behind-the-scenes work).
- A decision has five fields and three markers:
  `ledger.sh 결정 "<what was decided>" "<evidence: document or commit>" "<premise: if this changes, look again>" "<one-word topic, or empty>" "<binding>" --항목 "<what>" --값 "<how>" --조건 "<condition to look again, as screen wording>"`
  The fifth field, binding, starts with one of `돈|시간|법|못되돌림|없음` (money, time, law, cannot be undone, none). If you see no cost evidence in the code or documents, write `없음: import — no cost evidence seen`.
- App setting values: platform is one of `iPhone`, `안드로이드` (Android), `웹` (web), `스토어에 안 낸다` (not published to a store), `모름` (unknown). Payments is one of `앱안에서` (inside the app), `밖에서` (outside the app), `안받는다` (no payments), `모름` (unknown). For features, enter any value and the command returns the list of allowed values.
- The next states of a state are an existing state name or `끝` (end). Separate several with commas (`"사용 중,만료"` is the form: in use, expired; in the real call the state names are in English). If there is nowhere further to go, use `끝`.
  Recording the same state again overwrites it. To change where it can go, write the whole list again. If a target state is not recorded yet, record that state first.
- An app setting takes one value per call. Calling the same axis several times accumulates values, for axes that hold several (like features).
- Evidence for a decision: a place in a document, commit message, or code comment that says why. Put that place (file:line) in the evidence field.
- If the README and the code disagree, follow the code. Do not record the disagreement as a decision; tell the user about the difference.
- A screen's short name need not be spaced words. The human-readable name goes in `화면이름` (screen name), recorded separately.
- If a screen state has no "when it moves on", leave it as an empty string (`""`).
- Things that are not app screens (the phone's default incoming call screen, email) are recorded as screens if the user passes through them. For email: `화면종류 ... 메일` (screen kind, email).

If the app has no such field (for example a server with no screens), record the reason:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 가져오기 없음 "<field>" "<reason>"
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 가져오기          # current state of every field
```

## Confirm with the user

1. When everything is filled, show the user a short summary: current phase, feature table, screen flow.
2. Sub-features that exist in the code and work become `완료` (done) through `설치전`. Do not enter them as "needs confirmation": that would cover the user's "what to do now" list with features of a product that already works.
3. Fix a sub-feature with `세부상태` only if the user said it is wrong.

## Prohibitions

1. Do not leave a field you could not find empty. An empty field reads as "none". Either you found it, or you record "none" with a reason. The end-of-conversation check (`lint_import`) reports the fields that remain.
2. Do not record "done" without evidence. Call `설치전` only with a place in the code (file:line) or a passing test. Do not include code that no screen uses.
3. Do not change the app's code. Import only reads.
4. Do not invent evidence for a decision. Use only what is written in documents or commits. If there is none, leave the decision empty and record "none" with the reason.
