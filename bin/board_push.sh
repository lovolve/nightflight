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

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

nf_state_of() {
  NIGHTFLIGHT_PROJECT_DIR="$1" bash -c '. "$1" >/dev/null 2>&1; printf "%s" "$NF_STATE"' _ "$HERE/project-root.sh"
}
nf_sums() {
  python3 -I - "$1" <<'PY' 2>/dev/null
import glob, hashlib, json, os, sys
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.json"))):
    n = os.path.basename(f)
    try:
        d = json.load(open(f, encoding="utf-8"))
        if n == "machine.json":
            d = {"걸리나짝": d.get("걸리나짝"), "걸리나": d.get("걸리나"), "못쟀다": d.get("못쟀다")}
        elif n == "now.json" and isinstance(d, dict):
            d = {k: v for k, v in d.items() if k != "updatedAt"}
        b = json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")
    except Exception:
        b = open(f, "rb").read()
    print(hashlib.sha256(b).hexdigest() + "  ./" + n)
PY
}

if [ "${1:-}" = "--화면올렸다" ]; then
  ROOT="${2:-${CLAUDE_PROJECT_DIR:-}}"
  ST=""; [ -n "$ROOT" ] && [ -d "$ROOT" ] && ST="$(nf_state_of "$ROOT")"
  if [ -z "$ST" ] || [ ! -d "$ST" ]; then
    echo "  ⛔ 어느 제품인지 알 수 없어 **아무것도 적지 않았습니다.**" >&2
    echo "     [모델] 폴더를 함께 주십시오: $HERE/board_push.sh --화면올렸다 <제품 폴더>" >&2
    exit 0
  fi
  shasum "$HERE/../board/cockpit.html" 2>/dev/null | cut -d' ' -f1 > "$ST/board.page"
  echo "  · 조종석 화면을 새 판으로 올린 것으로 적었습니다 — $(basename "$ROOT")"
  exit 0
fi

if [ "${1:-}" = "--올렸다" ]; then
  ROOT="${2:-${CLAUDE_PROJECT_DIR:-}}"
  if [ -z "$ROOT" ]; then
    _D="$PWD"
    while [ "$_D" != "/" ] && [ -n "$_D" ]; do
      if [ -d "$_D/.nightflight/board" ] || [ -d "$_D/.claude/board" ]; then ROOT="$_D"; break; fi
      _D="$(dirname "$_D")"
    done
  fi
  ST=""; [ -n "$ROOT" ] && [ -d "$ROOT" ] && ST="$(nf_state_of "$ROOT")"
  if [ -z "$ROOT" ] || [ -z "$ST" ] || [ ! -d "$ST/board" ]; then
    echo "  ⛔ 어느 제품인지 알 수 없어 **아무것도 적지 않았습니다.**" >&2
    echo "     [모델] 그 제품 폴더에서 부르거나 폴더를 함께 주십시오: $HERE/board_push.sh --올렸다 <제품 폴더>" >&2
    exit 0
  fi
  B="$ST/board"
  nf_sums "$B" > "$ST/board.sent"
  rm -f "$ST/board.막음"
  python3 -I "$HERE/다른조종석.py" --올렸다 "$ST" "$B/machine.json" 2>/dev/null || true
  echo "  · 조종석에 올린 것으로 적었습니다 — $(basename "$ROOT") ($(ls "$B"/*.json 2>/dev/null | wc -l | tr -d ' ')칸)"
  exit 0
fi

HOOK_IN=""
if [ ! -t 0 ]; then
  HOOK_IN="$(python3 -I -c '
import os, sys, selectors
try:
    sel = selectors.DefaultSelector(); sel.register(sys.stdin, selectors.EVENT_READ)
except Exception:
    sys.exit(0)
buf = []
while True:
    if not sel.select(1.0):
        break
    try:
        c = os.read(sys.stdin.fileno(), 65536)
    except Exception:
        break
    if not c:
        break
    buf.append(c)
sys.stdout.buffer.write(b"".join(buf))
' 2>/dev/null || true)"
fi

CWD=""; AGAIN="0"; SID=""
if [ -n "$HOOK_IN" ]; then
  export HOOK_IN
  eval "$(python3 -I -c '
import json, os, shlex
try:
    d = json.loads(os.environ.get("HOOK_IN") or "{}")
except Exception:
    d = {}
print("CWD=" + shlex.quote(str(d.get("cwd") or "")))
print("SID=" + shlex.quote(str(d.get("session_id") or "")))
print("AGAIN=" + ("1" if d.get("stop_hook_active") else "0"))
' 2>/dev/null || true)"
fi

ROOT="${CLAUDE_PROJECT_DIR:-${CWD:-$(cd "$HERE/.." && pwd)}}"
ST="$(nf_state_of "$ROOT")"
URL="$(cat "$ST/board.url" 2>/dev/null || true)"

if [ -z "$URL" ]; then
  PROOT="${CLAUDE_PROJECT_DIR:-$CWD}"
  [ -n "$PROOT" ] && [ -d "$PROOT" ] || exit 0
  PROOT="$(cd "$PROOT" && pwd)"
  [ "$PROOT" = "$(cd "$HOME" && pwd)" ] && exit 0
  [ "$PROOT" = "$(cd "$HERE/.." && pwd)" ] && exit 0
  PST="$(nf_state_of "$PROOT")"
  NIGHTFLIGHT_PROJECT_DIR="$PROOT" CLAUDE_PROJECT_DIR="$PROOT" bash -c '. "$1" >/dev/null 2>&1 && nf_registered' _ "$HERE/project-root.sh" || exit 0
  if [ -d "$PST" ]; then
    ( cd "$PROOT" && CLAUDE_PROJECT_DIR="$PROOT" "$HERE/ledger.sh" 조종석준비 >/dev/null 2>&1 ) || true
    python3 "$HERE/../tools/조종석파일.py" "$PROOT" >/dev/null 2>&1 || true
  fi
  [ "$AGAIN" = "1" ] && exit 0
  ASKED="$PST/board.만들기"
  if [ -f "$ASKED" ]; then
    [ "$(grep -c . "$ASKED" 2>/dev/null || echo 0)" -ge 3 ] && exit 0
    [ -n "$SID" ] && grep -qxF "$SID" "$ASKED" 2>/dev/null && exit 0
  fi
  mkdir -p "$PST" 2>/dev/null || exit 0
  cp "$HERE/../board/cockpit.html" "$PST/cockpit.html" 2>/dev/null || exit 0
  ( cd "$PROOT" && CLAUDE_PROJECT_DIR="$PROOT" "$HERE/ledger.sh" 조종석준비 >/dev/null 2>&1 ) || true
  printf '%s\n' "${SID:-대화id없음-$(date +%s)}" >> "$ASKED"
  python3 -I -c '
import json, sys
root, here, st = sys.argv[1], sys.argv[2], sys.argv[3]
print(json.dumps({
  "decision": "block",
  "reason": (
    "이 프로젝트에는 아직 조종석이 없습니다 — 지금 만들어 주십시오(첫 대화에서 한 번).\n"
    "  ① Artifact publish · file_path \"" + st + "/cockpit.html\" · icon \"gauge\" · "
    "capabilities {\"db\":{}} · description \"이 제품의 단계와 남은 일을 보여 주는 조종석\"\n"
    "  ② 받은 주소를 등록합니다: `" + here + "/ledger.sh 조종석 \"<받은 주소>\"` → `" + here + "/board_push.sh --화면올렸다 " + root + "`\n"
    "  ③ " + st + "/board/ 에 칸(*.json)이 있으면 ArtifactData batch · 같은 주소 · 칸마다 "
    "{op:\"set\", collection:\"state\", doc_id:<칸이름>, file_path:<그 json 의 절대경로>} "
    "(새로 만드는 칸이라 version 을 안 붙입니다) → 끝나면 "
    "`" + here + "/board_push.sh --올렸다 " + root + "`. "
    "칸이 없으면 건너뜁니다 — 조종석이 「아직 기록 없음 · 첫 대화를 하면 채워집니다」로 보입니다.\n"
    "  ④ 사용자께 한 줄로 알려 드립니다: 조종석을 만들었고 그 주소 — 옆 창에 열어 두면 진행이 보입니다.\n"
    "⛔ 만들 수 없는 자리(그 도구가 없음 · 로그인 안 됨)라면 — 클로드가 아닌 도구에서는 흔합니다 — "
    "사용자께 **파일로 된 조종석**을 알려 드리십시오: " + st + "/조종석.html "
    "(턴 끝마다 다시 지어집니다. 실시간은 아니고 «그때 적은 판»입니다). "
    "그리고 이 대화에서는 다시 안 막습니다."
  )}, ensure_ascii=False))
' "$PROOT" "$HERE" "$PST"
  exit 0
fi

[ -x "$HERE/ledger.sh" ] && "$HERE/ledger.sh" 조종석준비 >/dev/null 2>&1
python3 "$HERE/../tools/조종석파일.py" "$(dirname "$ST")" >/dev/null 2>&1 || true

B="$ST/board"
[ -d "$B" ] || exit 0

NOWSUM="$(nf_sums "$B")"
[ -n "$NOWSUM" ] || exit 0
WAS="$(cat "$ST/board.sent" 2>/dev/null || true)"
PAGENOW="$(shasum "$HERE/../board/cockpit.html" 2>/dev/null | cut -d' ' -f1)"
PAGEWAS="$(cat "$ST/board.page" 2>/dev/null || true)"
PAGENEW=0; [ -n "$PAGENOW" ] && [ "$PAGENOW" != "$PAGEWAS" ] && PAGENEW=1
[ "$PAGENEW" = "1" ] && cp "$HERE/../board/cockpit.html" "$ST/cockpit.html" 2>/dev/null
[ "$NOWSUM" = "$WAS" ] && [ "$PAGENEW" = "0" ] && exit 0

CHANGED="$(python3 -I -c '
import sys
def table(t):
    out = {}
    for line in t.splitlines():
        p = line.split()
        if len(p) >= 2:
            out[p[1].rsplit("/", 1)[-1][:-5]] = p[0]
    return out
a, b = table(sys.argv[1]), table(sys.argv[2])
names = [k for k in sorted(a) if a[k] != b.get(k)]
print(" · ".join(names))
' "$NOWSUM" "$WAS" 2>/dev/null || true)"
[ "$NOWSUM" = "$WAS" ] && CHANGED="(없음 — 화면 판만 새것)"
[ -n "$CHANGED" ] || CHANGED="(전부)"

MARK="$ST/board.막음"
if [ "$AGAIN" = "1" ] || [ -f "$MARK" ]; then
  rm -f "$MARK"
  python3 -I -c '
import json, sys
print(json.dumps({"systemMessage":
  "  ⚠️ 조종석이 기록보다 오래됐습니다 — 이번에는 못 올렸습니다. 「조종석 올려」라고 말씀해 주시면 올립니다."},
  ensure_ascii=False))
' "$CHANGED"
  exit 0
fi
: > "$MARK"

python3 -I -c '
import json, sys
url, changed, root, here, st, pagenew = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
others = sys.argv[7] if len(sys.argv) > 7 else ""
page = ("  ⓪ 조종석 «화면 판»이 새것입니다 — Artifact publish · url " + url + " · file_path \"" + st + "/cockpit.html\" "
        "(그 대화에서 처음 올리면 거절되고 지금 판을 보여 줍니다 — 같은 플러그인의 옛 판이면 그대로 다시 올리면 됩니다) → "
        "`" + here + "/board_push.sh --화면올렸다 " + root + "`\n") if pagenew == "1" else ""
print(json.dumps({
  "decision": "block",
  "reason": page + (
    "조종석 자료가 바뀌었는데 아직 안 올라갔습니다 — 달라진 칸: " + changed + "\n"
    "지금 올리십시오. 창업자가 조종석을 열면 이 자료를 봅니다.\n"
    "  ① ArtifactData list · url " + url + " · collection \"state\" "
    "— 칸마다 version 을 받습니다(없는 칸은 새로 만드는 것이라 version 을 안 붙입니다)\n"
    "  ② ArtifactData batch · 같은 url · 달라진 칸마다 "
    "{op:\"set\", collection:\"state\", doc_id:<칸이름>, "
    "file_path:\"" + st + "/board/<칸이름>.json\", if_version:<①에서 받은 값>}\n"
    "  ③ ①의 목록에 \"pressed\" 칸이 있으면 — 사용자가 조종석에서 「이미 했어요」를 "
    "누르신 것입니다. ArtifactData get 으로 열어 값마다 "
    "`bin/ledger.sh 앱설정 이미한것 <값> 화면` 을 돌리고, 끝나면 그 칸을 "
    "ArtifactData delete 로 지우십시오(지워야 다음에 또 안 옮깁니다).\n"
    "  ④ 올라갔으면 `" + here + "/board_push.sh --올렸다 " + root + "` 를 돌리십시오. "
    "그래야 다음 턴에 또 안 멈춥니다.\n"
    + others +
    "⛔ 올릴 수 없는 자리(그 도구가 없음)라면 — 클로드가 아닌 도구에서는 흔합니다 — "
    "창업자께 **파일로 된 조종석**을 알려 드리고 넘어가십시오: " + st + "/조종석.html "
    "(턴 끝마다 다시 지어집니다. 실시간이 아니라 «그때 적은 판»입니다). 다음 턴에는 안 막습니다."
  )}, ensure_ascii=False))
' "$URL" "$CHANGED" "$ROOT" "$HERE" "$ST" "$PAGENEW" "$(python3 -I "$HERE/다른조종석.py" --안내 "$ST" "$HERE" 2>/dev/null || true)"
exit 0
