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
        elif n == "piled.json" and isinstance(d, dict):
            d = {k: v for k, v in d.items() if k != "dict"}
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
  python3 -I "$HERE/other_cockpits.py" --올렸다 "$ST" "$B/machine.json" 2>/dev/null || true
  echo "  · 조종석에 올린 것으로 적었습니다 — $(basename "$ROOT") ($(ls "$B"/*.json 2>/dev/null | wc -l | tr -d ' ')칸)"
  exit 0
fi

nf_page_title() {
  local l; l="$(bash -c '. "$1" >/dev/null 2>&1; nf_lang' _ "$HERE/project-root.sh" 2>/dev/null)"
  [ "$l" = en ] || return 0
  python3 -I -c 'import sys,re; p=sys.argv[1]; s=open(p,encoding="utf-8").read(); open(p,"w",encoding="utf-8").write(re.sub(r"<title>[^<]*</title>","<title>Nightflight cockpit</title>",s,count=1))' "$1" 2>/dev/null || true
}

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
_nf_next_of() {
  local _f
  _f="$(NIGHTFLIGHT_PROJECT_DIR="$1" bash -c '. "$1" >/dev/null 2>&1; nf_next_file' _ "$HERE/project-root.sh")"
  mkdir -p "$(dirname "$_f")" 2>/dev/null
  printf '%s' "$_f"
}
ST="$(nf_state_of "$ROOT")"
URL="$(python3 -I "$HERE/trusted_text.py" 주소 "$ST" 2>/dev/null || true)"
CONSENT="$(head -1 "${NIGHTFLIGHT_HOME:-$HOME/.nightflight}/cockpit_consent" 2>/dev/null || true)"
if [ -n "$URL" ]; then
  NF_SESSION="$SID" NIGHTFLIGHT_PROJECT_DIR="$ROOT" CLAUDE_PROJECT_DIR="$ROOT" bash -c '. "$1" >/dev/null 2>&1 && nf_registered' _ "$HERE/project-root.sh" || exit 0
  if [ "$CONSENT" = "아니오" ]; then
    python3 "$HERE/../tools/cockpit_file.py" "$(dirname "$ST")" >/dev/null 2>&1 || true
    exit 0
  fi
fi

if [ -z "$URL" ]; then
  _NF_TRK="$(python3 -I "$HERE/trusted_text.py" 저장소안내 "$ST" 2>/dev/null || true)"
  if [ -n "$_NF_TRK" ]; then _nf_nx="$(_nf_next_of "$ROOT")"; printf '%s\n' "$_NF_TRK" > "$_nf_nx" 2>/dev/null; exit 0; fi
  PROOT="${CLAUDE_PROJECT_DIR:-$CWD}"
  [ -n "$PROOT" ] && [ -d "$PROOT" ] || exit 0
  PROOT="$(cd "$PROOT" && pwd)"
  [ "$PROOT" = "$(cd "$HOME" && pwd)" ] && exit 0
  [ "$PROOT" = "$(cd "$HERE/.." && pwd)" ] && exit 0
  PST="$(nf_state_of "$PROOT")"
  NF_SESSION="$SID" NIGHTFLIGHT_PROJECT_DIR="$PROOT" CLAUDE_PROJECT_DIR="$PROOT" bash -c '. "$1" >/dev/null 2>&1 && nf_registered' _ "$HERE/project-root.sh" || exit 0
  if [ -d "$PST" ]; then
    ( cd "$PROOT" && CLAUDE_PROJECT_DIR="$PROOT" "$HERE/ledger.sh" 조종석준비 >/dev/null 2>&1 ) || true
    python3 "$HERE/../tools/cockpit_file.py" "$PROOT" >/dev/null 2>&1 || true
  fi
  [ "$AGAIN" = "1" ] && exit 0
  [ "$CONSENT" = "아니오" ] && exit 0
  ASKED="$PST/board.create_asked"
  if [ -f "$ASKED" ]; then
    [ "$(grep -c . "$ASKED" 2>/dev/null || echo 0)" -ge 3 ] && exit 0
    [ -n "$SID" ] && grep -qxF "$SID" "$ASKED" 2>/dev/null && exit 0
  fi
  mkdir -p "$PST" 2>/dev/null || exit 0
  cp "$HERE/../board/cockpit.html" "$PST/board_page.html" 2>/dev/null || exit 0
  nf_page_title "$PST/board_page.html"
  ( cd "$PROOT" && CLAUDE_PROJECT_DIR="$PROOT" "$HERE/ledger.sh" 조종석준비 >/dev/null 2>&1 ) || true
  printf '%s\n' "${SID:-대화id없음-$(date +%s)}" >> "$ASKED"
  NFL="$(bash -c '. "$1" >/dev/null 2>&1; nf_lang' _ "$HERE/project-root.sh" 2>/dev/null)" python3 -I "$HERE/cockpit_create_guide.py" "$PROOT" "$HERE" "$PST" "$CONSENT"
  exit 0
fi

[ -x "$HERE/ledger.sh" ] && "$HERE/ledger.sh" 조종석준비 >/dev/null 2>&1
python3 "$HERE/../tools/cockpit_file.py" "$(dirname "$ST")" >/dev/null 2>&1 || true

B="$ST/board"
[ -d "$B" ] || exit 0

NOWSUM="$(nf_sums "$B")"
[ -n "$NOWSUM" ] || exit 0
WAS="$(cat "$ST/board.sent" 2>/dev/null || true)"
PAGENOW="$(shasum "$HERE/../board/cockpit.html" 2>/dev/null | cut -d' ' -f1)"
PAGEWAS="$(cat "$ST/board.page" 2>/dev/null || true)"
PAGENEW=0; [ -n "$PAGENOW" ] && [ "$PAGENOW" != "$PAGEWAS" ] && PAGENEW=1
[ "$PAGENEW" = "1" ] && cp "$HERE/../board/cockpit.html" "$ST/board_page.html" 2>/dev/null && nf_page_title "$ST/board_page.html"
[ "$NOWSUM" = "$WAS" ] && [ "$PAGENEW" = "0" ] && exit 0

CHANGED="$(python3 -I -c '
import re, sys
def table(t):
    out = {}
    for line in t.splitlines():
        p = line.split()
        if len(p) >= 2:
            이름 = p[1].rsplit("/", 1)[-1][:-5]
            if re.fullmatch(r"[A-Za-z0-9가-힣_-]{1,40}", 이름):
                out[이름] = p[0]
    return out
a, b = table(sys.argv[1]), table(sys.argv[2])
names = [k for k in sorted(a) if a[k] != b.get(k)]
print(" · ".join(names))
' "$NOWSUM" "$WAS" 2>/dev/null || true)"
[ "$NOWSUM" = "$WAS" ] && CHANGED="(없음 — 화면 판만 새것)"
[ -n "$CHANGED" ] || CHANGED="(전부)"

MARK="$ST/board.막음"
TOLD="$ST/board.notified"
RECEIPT="$(shasum "$ST/board.sent" 2>/dev/null | cut -d' ' -f1)"; RECEIPT="${RECEIPT:-없음}"
nf_told_set() {
  { awk -F'\t' -v s="$1" '$1!=s' "$TOLD" 2>/dev/null | tail -n 49; printf '%s\t%s\t%s\n' "$1" "$2" "$3"; } > "$TOLD.$$" \
    && mv -f "$TOLD.$$" "$TOLD"
}
nf_warn_once() {
  if [ "$(head -c 2 "${NIGHTFLIGHT_HOME:-$HOME/.nightflight}/language" 2>/dev/null)" = "en" ]; then
    printf '%s\n' '{"systemMessage": "  ⚠️ The cockpit is older than your records and was not updated this time. Say \"update the cockpit\" to update it."}'
  else
    printf '%s\n' '{"systemMessage": "  ⚠️ 조종석이 기록보다 오래됐습니다 — 이번에는 못 올렸습니다. 「조종석 올려」라고 말씀해 주시면 올립니다."}'
  fi
}
if [ -n "$SID" ]; then
  _nf_line="$(awk -F'\t' -v s="$SID" '$1==s{l=$0} END{print l}' "$TOLD" 2>/dev/null)"
  TSTATE=""; THASH=""
  if [ -n "$_nf_line" ]; then
    TSTATE="$(printf '%s' "$_nf_line" | cut -f2 -s)"; THASH="$(printf '%s' "$_nf_line" | cut -f3 -s)"
    [ -n "$TSTATE" ] || TSTATE="조용"
  fi
  [ "$TSTATE" = "조용" ] && exit 0
  if [ "$AGAIN" = "1" ]; then
    [ "$TSTATE" = "막음" ] || exit 0
    [ "$THASH" != "$RECEIPT" ] && exit 0
    nf_told_set "$SID" 조용 "$RECEIPT"; nf_warn_once; exit 0
  fi
  if [ "$TSTATE" = "막음" ] && [ "$THASH" = "$RECEIPT" ]; then
    nf_told_set "$SID" 조용 "$RECEIPT"; exit 0
  fi
  nf_told_set "$SID" 막음 "$RECEIPT"
else
  if [ "$AGAIN" = "1" ]; then nf_warn_once; exit 0; fi
  [ -f "$MARK" ] && exit 0
  : > "$MARK"
fi

_nf_nx="$(_nf_next_of "$ROOT")"
python3 -I "$HERE/cockpit_upload_guide.py" "$URL" "$CHANGED" "$ROOT" "$HERE" "$ST" "$PAGENEW" "$(python3 -I "$HERE/other_cockpits.py" --안내 "$ST" "$HERE" 2>/dev/null || true)" > "$_nf_nx.tmp" 2>/dev/null && mv -f "$_nf_nx.tmp" "$_nf_nx"
exit 0
