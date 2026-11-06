# Nightflight

Nightflight is a plugin for Claude Code.
It helps people who build apps alone, without a developer, get to launch.

- If the AI changes the same file many times in one conversation (8 by default), Nightflight tells the AI to stop and review its approach.
- It records decisions, dead ends, and standard methods. The AI picks up these records in the next conversation.
- The cockpit screen shows which stage you are in and what is left.
- It gives guidance for each of nine stages, from Diagnose to After launch.

Nightflight does not decide for you. It organizes what you need to make each decision.

## What you need

| What | Notes |
|---|---|
| Mac (macOS) | Nightflight runs on Mac. Windows and Linux are not supported. |
| Claude Code | Requires a paid Claude plan (Pro or higher). The free plan does not work. |
| Python 3 | Included with the Mac developer tools (run `xcode-select --install` in Terminal). Without it, most of Nightflight does not run. |

## Install

1. Open Claude Code (the Code tab in the Claude app, or Terminal).
2. Copy all of the text below and paste it into the conversation.

   ```
   Please install the Nightflight plugin.
   Run claude plugin marketplace add lovolve/nightflight in Terminal,
   then run claude plugin install nightflight@lovolve.
   If the claude command is not found, find and use the claude program inside the Claude app.
   ```

3. If the AI asks for permission to install, answer "yes". This adds outside code to your computer, so one question is normal.
4. When the install finishes, reopen Claude Code.

### Install in Codex

These steps were checked against the official Codex source. They have not been run in Codex.

1. Run this command in Terminal.

   ```bash
   codex plugin marketplace add lovolve/nightflight
   ```

2. Run this command.

   ```bash
   codex plugin add nightflight@lovolve
   ```

3. Reopen Codex.
4. Open `/hooks` in Codex.
5. Approve the Nightflight automatic checks. Without approval, record pickup and end-of-conversation checks do not run.
6. For planning and design, turn on plan mode with `/plan`. The choice screen appears only in that mode.

You may need to approve again in `/hooks` after a plugin update.

Differences from Claude Code:

- The cockpit cannot be published as a live web page. Open the file `.nightflight/조종석.html` instead.
- Screen layout previews do not appear.
- Records are not written in plan mode. They are written after you approve the plan.

## First use

1. Open a new conversation. You do not need a product folder yet.
2. Say "Let's start Nightflight".
   - If you are not in a product folder (for example, your home folder), the AI asks for the product name and creates and registers a folder with that name.
   - If you opened the folder of a product you are already building, the AI registers that folder.
3. In the first conversation, the AI checks this computer and asks a few questions.
4. After that, records and the cockpit update each time this conversation finishes a turn.
5. To continue in a new conversation, make "Let's start Nightflight" your first message. Nightflight stays out of conversations that do not ask for it. To turn it on for every conversation in the folder, say so.

## Where records are kept

- Automatic checks add guidance for the AI to each conversation: progress records, writing rules, and commands for cleanup requests. You do not see this text.
- Automatic checks save development words you use yourself on this computer (`~/.nightflight/`), so the AI does not explain them again. No notice appears when a word is saved.
- To turn off automatic checks, run `claude plugin disable nightflight@lovolve`. This turns off the whole plugin.
- Records stay in the product folder (`.nightflight/`). Record contents are not sent to the Nightflight server.
- The product folder also holds `.nightflight-product`, which contains the product number. Keep this file with your product. It lets the same product use one product slot on different computers.
- The cockpit asks once before its first upload. If you agree, a copy of your records goes to a private page (artifact) in your Claude account.
  - Uploaded: decisions, dead ends, feature progress, this computer's chip, operating system, memory and storage status, and the names and stages of other products registered on this computer.
  - Not uploaded: the values of secrets.
  - If you decline, you use only the cockpit file (`.nightflight/조종석.html`). To change your mind, say "update the cockpit".
- The Nightflight server receives only what it needs for stage guidance and license checks: the stage number, the guidance requested, a number identifying this computer (a random number made at install and a one-way value derived from the hardware number), the product number, your license key (when you enter it), your email address and confirmation code (when you confirm with your payment email), the plan you are changing to, your language, and a random request number that stops a request from counting twice. The server also briefly uses an irreversible value derived from your connection address.
- To check for a new version, Nightflight reads a public GitHub file once every 6 hours. It sends no records.
- The full list of values and how long they are kept is in the privacy policy on the sales page.

## Price

Prices and plans are on the sales page: https://lovolve.app/nightflight

- Automatic checks, warnings, the cockpit, and records are included in every plan.
- Your Claude subscription is separate. You pay Anthropic directly.

## License

This repository is public but not open source. You may install it, read the code, and build your own products with it. You may not redistribute it. See `LICENSE`.

## Contact

support@lovolve.app
