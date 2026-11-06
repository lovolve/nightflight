# Red team

Run this only after Nightflight recommended a red team and the user agreed to run it. Typical moments: before development starts, before launch, and the first time payment, login, personal data, or server-permission features go in. A development team and a security team review the design and the code separately and look for holes. If the user wants to skip, do not run it.

Design stability and security must not be left thin. The red team is only recommended. Explain why it is needed. The user may skip it.

## When

`ledger.sh` printed "red team recommended". You told the user why. Run the red team only if the user then asks to run it.
If the user skips, record it with `ledger.sh 레드팀 넘김 <때>` (red team, skipped, `<때>` = the trigger) and continue the earlier work. Do not recommend it again.

## How

Start the two teams separately and at the same time, so neither sees the other's answer. Give each team this project's records (decisions, feature table, screen design document) and the code.

1. Development team: where does the product break if it is built as planned?
   - Items in the feature table that are missing from the code. Things built against a decision (for example, decided "no server" but data is saved on a server).
   - Missing connections between features. Data structures that would break existing users' records if changed later.
   - Failures (network loss, canceled payment, app killed) that leave the user with an empty screen or half-saved data.
2. Security team: how can someone else abuse it?
   - Login: ways into someone else's account; where passwords and tokens are kept.
   - Secrets: keys placed in code, in the repository, or inside the app. A server secret key inside the app is the most urgent.
   - Permissions: do the server and the database restrict reads and writes to the logged-in owner's own data?
   - Personal data: what is collected, where it is sent, whether it can be deleted.
   - Payment: ways to use the product without paying, double charges, continued use after a refund.

Make each team report every finding in the form "what, where, and what happens to the user". Sort the findings by urgency.
Do not decide whether to fix a finding. The user decides. Do not assume a finding is "already fixed".

## Record it

When the run is finished, tell the user the findings in plain English, most urgent first. Then record the run:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 레드팀 돌림 <때> "<one line of what was found, or: nothing found>"
```

Allowed values for `<때>` (the trigger): `개발` (development), `출시` (launch), `결제` (payment), `로그인` (login), `개인정보` (personal data), `서버권한` (server permissions). The quoted finding text is written in English. Never show the Korean command words to the user.

## Prohibitions

1. Do not run the red team if the user did not ask to run it. If the user skips it, do not block them.
2. Do not fix anything the red team found before showing it to the user. Tell the user first.
