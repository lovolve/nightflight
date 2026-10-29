#!/bin/bash
if [ -z "${NF_LC_WAS:-}" ]; then
  for _nf_lcv in "${LC_ALL:-}" "${LC_MESSAGES:-}" "${LANG:-}"; do
    case "$_nf_lcv" in C|POSIX|C.*|"") : ;; *) NF_LC_WAS="$_nf_lcv"; break ;; esac
  done
  unset _nf_lcv
fi
export NF_LC_WAS
LC_ALL=C; export LC_ALL
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
IN="$(python3 -I "$HERE/hook_in.py" 2>/dev/null)" || IN="$(cat 2>/dev/null || true)"

_nf_nh="${NIGHTFLIGHT_HOME:-$HOME/.nightflight}"; case "$_nf_nh" in /*) ;; *) _nf_nh="" ;; esac
printf '%s' "$IN" | HERE="$HERE" NF_NOTE_FILE="${_nf_nh:+$_nf_nh/다음알림}" python3 -I -c '
import json, os, re, subprocess, sys

raw = sys.stdin.read()
try:
    prompt = (json.loads(raw) or {}).get("prompt", "") or ""
except Exception:
    sys.exit(0)
if not prompt.strip():
    sys.exit(0)

HERE = os.environ["HERE"]
led = os.path.join(HERE, "ledger.sh")
luf = os.path.join(os.path.dirname(HERE), "tools", "lint_user_facing.py")
if not (os.path.exists(led) and os.path.exists(luf)):
    sys.exit(0)

pairs = [l.split("\t") for l in subprocess.run(
    [sys.executable, luf, "--낱말전부"], capture_output=True, text=True).stdout.splitlines() if "\t" in l]

def 사용자가_쓴_것만(t: str) -> str:
    t = re.sub(r"<pasted_content[^>]*>.*?</pasted_content>", " ", t, flags=re.S)
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"`[^`]*`", " ", t)
    t = re.sub(r"[「\"'']([^「」\"'']{0,80})[」\"'']", " ", t)
    남김 = []
    for ln in t.splitlines():
        if re.search(r"(error|warning|Traceback|at line|\bE\d{3}\b|로그|붙여넣|붙여 넣)", ln, re.I):
            continue
        남김.append(ln)
    return "\n".join(남김)

prompt = 사용자가_쓴_것만(prompt)

ASKING = re.compile(r"(뭐(야|예요|니|냐|지)|뭔(가요|지)|무슨|무엇|뜻이|의미|"
                    r"란\s*\?|이란|이라는 게|설명(해|좀)|모르겠|어려워|어렵|풀어서|쉽게|"
                    r"네가|니가|당신이|아까|말한|말씀하신|했던|그게 맞|맞아\?)")

raised = []
for m, show in pairs:
    if not re.search(r"\b" + re.escape(m) + r"\b" if re.match(r"^[A-Za-z]", m)
                     else re.escape(m), prompt):
        continue
    i = prompt.find(m)
    near = prompt[max(0, i - 40): i + len(m) + 40]
    if ASKING.search(near):
        continue
    r = subprocess.run(["bash", led, "낱말올림", show, "사용자가 먼저 쓰셨습니다"],
                       capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip() == show:
        raised.append(show)

알림 = ""
nf = os.environ.get("NF_NOTE_FILE", "")
if nf and os.path.isfile(nf):
    try:
        알림 = open(nf, encoding="utf-8", errors="replace").read().strip()[:2000]; os.remove(nf)
    except OSError:
        알림 = ""
if not raised:
    if 알림:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "지난 턴 끝에 잰 이 컴퓨터 알림(필요할 때 한 줄로 전하십시오): " + 알림}}, ensure_ascii=False))
    sys.exit(0)

msg = ("적응형 사전: 사용자가 먼저 쓰신 낱말 — 「" + "」·「".join(raised) + "」. "
       "이제 이 말은 풀어 쓰지 않고 그대로 씁니다. "
       "⛔ 올렸다고 사용자에게 말하지 마십시오 — 되물으면 시험이 됩니다.")
if 알림:
    msg += "\n지난 턴 끝에 잰 이 컴퓨터 알림(필요할 때 한 줄로 전하십시오): " + 알림
print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                         "additionalContext": msg}}, ensure_ascii=False))
' 2>/dev/null || true
exit 0
