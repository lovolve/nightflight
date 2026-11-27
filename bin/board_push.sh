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
. "$HERE/python_ok.sh" 2>/dev/null && { nf_python_ok || exit 0; }

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
  mkdir -p "$ST/internal" 2>/dev/null
  shasum "$HERE/../board/cockpit.html" 2>/dev/null | cut -d' ' -f1 > "$ST/internal/board.page"
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
  mkdir -p "$ST/internal" 2>/dev/null
  nf_sums "$B" > "$ST/internal/board.sent"
  rm -f "$ST/board.막음" "$ST/board.막음.told"
  python3 -I "$HERE/other_cockpits.py" --올렸다 "$ST" "$B/machine.json" 2>/dev/null || true
  echo "  · 조종석에 올린 것으로 적었습니다 — $(basename "$ROOT") ($(ls "$B"/*.json 2>/dev/null | wc -l | tr -d ' ')칸)"
  exit 0
fi

nf_page_title() {
  local l; l="$(bash -c '. "$1" >/dev/null 2>&1; nf_lang' _ "$HERE/project-root.sh" 2>/dev/null)"
  python3 -I -c '
import sys, re, os, json, html
p, en = sys.argv[1], sys.argv[2] == "en"
s = open(p, encoding="utf-8").read()
이름 = ""
try:
    이름 = (json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(p))), "board", "now.json"), encoding="utf-8")).get("앱이름") or "").strip()
except Exception:
    pass
if 이름:
    제목 = html.escape(이름[:40]) + (" cockpit" if en else " 조종석")
elif en:
    제목 = "Nightflight cockpit"
else:
    sys.exit(0)
open(p, "w", encoding="utf-8").write(re.sub(r"<title>[^<]*</title>", "<title>" + 제목 + "</title>", s, count=1))
' "$1" "$l" 2>/dev/null || true
}

nf_place_page() {
  local d="$1" t="$1.tmp.$$"
  cp "$HERE/../board/cockpit.html" "$t" 2>/dev/null && nf_page_title "$t" && mv -f "$t" "$d" && return 0
  rm -f "$t" 2>/dev/null; return 1
}

if [ "${1:-}" = "--지금만들기" ]; then
  ROOT="${2:-${CLAUDE_PROJECT_DIR:-}}"
  if [ -z "$ROOT" ] || [ ! -d "$ROOT" ]; then
    echo "  ⛔ 어느 제품인지 알 수 없어 조종석을 만들지 않았습니다." >&2
    echo "     [모델] 폴더를 함께 주십시오: $HERE/board_push.sh --지금만들기 <제품 폴더>" >&2
    exit 0
  fi
  ROOT="$(cd "$ROOT" && pwd)"; ST="$(nf_state_of "$ROOT")"
  if [ -z "$ST" ] || ! NIGHTFLIGHT_PROJECT_DIR="$ROOT" CLAUDE_PROJECT_DIR="$ROOT" bash -c '. "$1" >/dev/null 2>&1 && nf_registered' _ "$HERE/project-root.sh"; then
    echo "  이 폴더는 아직 야간비행에 등록되지 않았습니다. 조종석을 만들지 않았습니다."; exit 0
  fi
  [ -d "$ST/board" ] || ( cd "$ROOT" && CLAUDE_PROJECT_DIR="$ROOT" "$HERE/ledger.sh" 조종석준비 >/dev/null 2>&1 ) || true
  if [ "${CLAUDE_CODE_ENTRYPOINT:-}" = "claude-desktop" ]; then
    NF_ADDR=""
    for _nf_try in 1 2; do
      [ -d "$ST/board" ] || ( cd "$ROOT" && CLAUDE_PROJECT_DIR="$ROOT" "$HERE/ledger.sh" 조종석준비 >/dev/null 2>&1 ) || true
      [ -d "$ST/board" ] && NF_ADDR="$(python3 -I "$HERE/cockpit_server.py" "$ROOT" --뒤에서 2>/dev/null | head -1 || true)"
      case "${NF_ADDR:-}" in http://127.0.0.1:*) break ;; esac
      NF_ADDR=""; sleep 1
    done
    if [ -n "$NF_ADDR" ]; then
      mkdir -p "$ST/internal" 2>/dev/null && printf '%s\t%s\n' "$(date +%s)" "${CLAUDE_CODE_SESSION_ID:-}" > "$ST/internal/pane_asked" 2>/dev/null
      echo "  [모델] 지금 바로 mcp__Claude_Browser__preview_start 를 url «$NF_ADDR» 로 한 번 부르십시오 — 진단보다 먼저 부릅니다. 그다음 mcp__ccd_view__show_pane 을 pane «preview» 로 부르십시오 — 안 부르면 칸이 숨은 채 «열기» 카드만 떠서 사용자가 눌러야 보입니다(도구 목록에 이름만 있고 아직 안 불러온 도구면 ToolSearch 를 query «select:mcp__ccd_view__show_pane» 로 먼저 부릅니다 · 이름이 아예 없을 때만 건너뜁니다). 오른쪽 브라우저 칸에 «조종석 준비» 화면이 열리고, 진단·가져오기가 채워지는 모습이 보입니다. 화면을 찍지는 마십시오. 아티팩트로 만들지 마십시오."
      exit 0
    fi
    echo "  조종석을 켜지 못했습니다. 대화창에 /cockpit 을 입력하시면 다시 켭니다."
    echo "  [모델] 위 한 줄을 사용자에게 그대로 전하고 진단으로 넘어가십시오. 아티팩트로 만들지 마십시오."
    exit 0
  fi
  URL="$(python3 -I "$HERE/trusted_text.py" 주소 "$ST" 2>/dev/null || true)"
  if [ -n "$URL" ]; then
    echo "  [모델] 이 제품에는 조종석이 이미 있습니다 — Artifact open · url $URL 로 띄우고, 그 «다음에» mcp__ccd_view__show_pane(pane \"artifact\") 도구가 있으면 부르십시오(먼저 부르면 다른 페이지가 열립니다)."
    exit 0
  fi
  CONSENT="$(head -1 "${NIGHTFLIGHT_HOME:-$HOME/.nightflight}/cockpit_consent" 2>/dev/null || true)"
  ( cd "$ROOT" && CLAUDE_PROJECT_DIR="$ROOT" "$HERE/ledger.sh" 조종석준비 >/dev/null 2>&1 ) || true
  python3 "$HERE/../tools/cockpit_file.py" "$ROOT" >/dev/null 2>&1 || true
  if [ "$CONSENT" = "아니오" ]; then
    echo "  조종석에 올리지 않기로 하셨습니다. 파일로 된 조종석을 씁니다: $ST/cockpit.html"
    exit 0
  fi
  mkdir -p "$ST/internal" 2>/dev/null
  nf_place_page "$ST/internal/board_page.html" || { echo "  조종석 화면 판을 놓지 못했습니다. 이번 턴이 끝나면 다시 안내합니다."; exit 0; }
  printf '%s\n' "${CLAUDE_CODE_SESSION_ID:-지금만들기-$(date +%s)}" >> "$ST/internal/board.create_asked"
  NF_PLAIN=1 NFL="$(bash -c '. "$1" >/dev/null 2>&1; nf_lang' _ "$HERE/project-root.sh" 2>/dev/null)" python3 -I "$HERE/cockpit_create_guide.py" "$ROOT" "$HERE" "$ST" "$CONSENT"
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
_nf_next_of() {
  local _f
  _f="$(NIGHTFLIGHT_PROJECT_DIR="$1" bash -c '. "$1" >/dev/null 2>&1; nf_next_file' _ "$HERE/project-root.sh")"
  mkdir -p "$(dirname "$_f")" 2>/dev/null
  printf '%s' "$_f"
}
ST="$(nf_state_of "$ROOT")"
URL="$(python3 -I "$HERE/trusted_text.py" 주소 "$ST" 2>/dev/null || true)"
CONSENT="$(head -1 "${NIGHTFLIGHT_HOME:-$HOME/.nightflight}/cockpit_consent" 2>/dev/null || true)"

NF_PANE=0
if [ -n "$ST" ] && [ -d "$ST/board" ]; then
  if python3 -I "$HERE/cockpit_server.py" "$ROOT" --살아있나 >/dev/null 2>&1; then
    NF_PANE=1
  elif [ "${CLAUDE_CODE_ENTRYPOINT:-}" = "claude-desktop" ] \
       && [ "$ROOT" != "$(cd "$HOME" && pwd)" ] && [ "$ROOT" != "$(cd "$HERE/.." && pwd)" ]; then
    python3 -I "$HERE/cockpit_server.py" "$ROOT" --뒤에서 >/dev/null 2>&1 && NF_PANE=1
  fi
  [ "$NF_PANE" = "1" ] || { python3 -I "$HERE/cockpit_server.py" "$ROOT" --보이나 >/dev/null 2>&1 && NF_PANE=1; }
fi
if [ "$NF_PANE" = "1" ] && [ "$AGAIN" != "1" ] && [ -n "$SID" ] && [ "${CLAUDE_CODE_ENTRYPOINT:-}" = "claude-desktop" ] && [ -f "$ST/internal/pane_asked" ]; then
  _pa="$(cat "$ST/internal/pane_asked" 2>/dev/null)"; _pt="${_pa%%	*}"; _ps="${_pa#*	}"
  _seen="$(head -1 "$ST/internal/pane_seen" 2>/dev/null | tr -cd '0-9')"
  if [ "$_ps" = "$SID" ] && [ "${_seen:-0}" -lt "${_pt:-0}" ] && ! grep -qxF "$SID" "$ST/internal/pane_reminded" 2>/dev/null; then
    printf '%s\n' "$SID" >> "$ST/internal/pane_reminded" 2>/dev/null
    _addr="$(python3 -I "$HERE/cockpit_server.py" "$ROOT" --뒤에서 2>/dev/null | head -1 || true)"
    case "$_addr" in
      http://127.0.0.1:*) _msg="조종석 화면이 아직 한 번도 열리지 않았습니다. mcp__Claude_Browser__preview_start 를 url «$_addr» 로 지금 한 번 부르십시오. 그다음 mcp__ccd_view__show_pane 을 pane «preview» 로 부르십시오 — 안 부르면 칸이 숨은 채 «열기» 카드만 떠서 사용자가 눌러야 보입니다(도구 목록에 이름만 있고 아직 안 불러온 도구면 ToolSearch 를 query «select:mcp__ccd_view__show_pane» 로 먼저 부릅니다 · 이름이 아예 없을 때만 건너뜁니다). 아티팩트로 만들지 마십시오. 화면을 찍지 마십시오." ;;
      *) _msg="조종석 화면이 아직 열리지 않았습니다. 사용자에게 «조종석을 켜지 못했습니다. 대화창에 /cockpit 을 입력하시면 다시 켭니다.»라고 한 줄 전하십시오. 아티팩트로 만들지 마십시오." ;;
    esac
    _NFM="$_msg" python3 -I -c 'import json,os; print(json.dumps({"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"[모델] "+os.environ["_NFM"]}}, ensure_ascii=False))'
    exit 0
  fi
fi
if [ -n "$URL" ]; then
  NF_SESSION="$SID" NIGHTFLIGHT_PROJECT_DIR="$ROOT" CLAUDE_PROJECT_DIR="$ROOT" bash -c '. "$1" >/dev/null 2>&1 && nf_registered' _ "$HERE/project-root.sh" || exit 0
  if [ "$CONSENT" = "아니오" ]; then
    python3 "$HERE/../tools/cockpit_file.py" "$(dirname "$ST")" >/dev/null 2>&1 || true
    exit 0
  fi
fi

if [ -z "$URL" ]; then
  [ "$NF_PANE" = "1" ] && exit 0
  _NF_TRK="$(python3 -I "$HERE/trusted_text.py" 저장소안내 "$ST" 2>/dev/null || true)"
  if [ -n "$_NF_TRK" ]; then _nf_nx="$(_nf_next_of "$ROOT")"; printf '%s\n' "$_NF_TRK" > "$_nf_nx" 2>/dev/null; exit 0; fi
  PROOT="${CLAUDE_PROJECT_DIR:-$CWD}"
  [ -n "$PROOT" ] && [ -d "$PROOT" ] || exit 0
  PROOT="$(cd "$PROOT" && pwd)"
  if [ "$PROOT" = "$(cd "$HOME" && pwd)" ] && [ -n "$CWD" ] && [ -d "$CWD" ]; then PROOT="$(cd "$CWD" && pwd)"; fi
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
  ASKED="$PST/internal/board.create_asked"
  if [ -f "$ASKED" ]; then
    [ "$(grep -c . "$ASKED" 2>/dev/null || echo 0)" -ge 3 ] && exit 0
    [ -n "$SID" ] && grep -qxF "$SID" "$ASKED" 2>/dev/null && exit 0
  fi
  mkdir -p "$PST/internal" 2>/dev/null || exit 0
  nf_place_page "$PST/internal/board_page.html" || exit 0
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
[ "$NF_PANE" = "1" ] && exit 0
WAS="$(cat "$ST/internal/board.sent" 2>/dev/null || true)"
PAGENOW="$(shasum "$HERE/../board/cockpit.html" 2>/dev/null | cut -d' ' -f1)"
PAGEWAS="$(cat "$ST/internal/board.page" 2>/dev/null || true)"
PAGENEW=0; [ -n "$PAGENOW" ] && [ "$PAGENOW" != "$PAGEWAS" ] && PAGENEW=1
[ "$PAGENEW" = "1" ] && mkdir -p "$ST/internal" 2>/dev/null && nf_place_page "$ST/internal/board_page.html"
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
TOLD="$ST/internal/board.notified"
RECEIPT="$(shasum "$ST/internal/board.sent" 2>/dev/null | cut -d' ' -f1)"; RECEIPT="${RECEIPT:-없음}"
nf_told_set() {
  { awk -F'\t' -v s="$1" '$1!=s' "$TOLD" 2>/dev/null | tail -n 49; printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "${4:-}"; } > "$TOLD.$$" \
    && mv -f "$TOLD.$$" "$TOLD"
}
PROG="$(python3 -I - "$B" <<'PY' 2>/dev/null
import glob, hashlib, json, os, sys
h = hashlib.sha256()
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.json"))):
    n = os.path.basename(f)
    if n == "machine.json":
        continue
    try:
        d = json.load(open(f, encoding="utf-8"))
        if isinstance(d, dict):
            빼기 = {"now.json": ("updatedAt", "repeat"), "piled.json": ("dict",)}.get(n, ())
            d = {k: v for k, v in d.items() if k not in 빼기}
        b = json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")
    except Exception:
        b = open(f, "rb").read()
    h.update(n.encode("utf-8") + b"\0" + b + b"\0")
print(h.hexdigest())
PY
)"
nf_warn_once() {
  python3 -I - "$ST/internal/board.sent" "$(head -c 2 "${NIGHTFLIGHT_HOME:-$HOME/.nightflight}/language" 2>/dev/null)" <<'PY' 2>/dev/null || true
import json, os, sys, time
sent, lang = sys.argv[1], sys.argv[2]
try:
    t = time.localtime(os.path.getmtime(sent))
except OSError:
    t = None
if lang == "en":
    when = time.strftime("%b %-d %H:%M", t) if t else "never"
    msg = "  ⚠️ The cockpit has stopped updating (last updated: " + when + "). Say \"update the cockpit\"."
else:
    when = ("%d월 %d일 %s" % (t.tm_mon, t.tm_mday, time.strftime("%H:%M", t))) if t else "아직 없음"
    msg = "  ⚠️ 조종석이 멈춰 있습니다(마지막 반영: " + when + "). «조종석 올려»라고 말씀해 주십시오."
print(json.dumps({"systemMessage": msg}, ensure_ascii=False))
PY
}
if [ -n "$SID" ]; then
  _nf_line="$(awk -F'\t' -v s="$SID" '$1==s{l=$0} END{print l}' "$TOLD" 2>/dev/null)"
  TSTATE=""; THASH=""; TPROG=""
  if [ -n "$_nf_line" ]; then
    TSTATE="$(printf '%s' "$_nf_line" | cut -f2 -s)"; THASH="$(printf '%s' "$_nf_line" | cut -f3 -s)"; TPROG="$(printf '%s' "$_nf_line" | cut -f4 -s)"
    [ -n "$TSTATE" ] || TSTATE="조용"
  fi
  if [ "$TSTATE" = "조용" ] && [ -n "$THASH" ] && [ "$THASH" != "$RECEIPT" ]; then TSTATE=""; fi
  if [ "$TSTATE" = "조용" ]; then
    [ "$PROG" = "$TPROG" ] && exit 0
    nf_told_set "$SID" 조용 "$THASH" "$PROG"; nf_warn_once
    NF_REGUIDE=1
  fi
  if [ "${NF_REGUIDE:-0}" = "0" ]; then
  if [ "$AGAIN" = "1" ]; then
    [ "$TSTATE" = "막음" ] || exit 0
    [ "$THASH" != "$RECEIPT" ] && exit 0
    nf_told_set "$SID" 조용 "$RECEIPT" "$PROG"; nf_warn_once; exit 0
  fi
  if [ "$TSTATE" = "막음" ] && [ "$THASH" = "$RECEIPT" ]; then
    nf_told_set "$SID" 조용 "$RECEIPT" "$PROG"; nf_warn_once; exit 0
  fi
  nf_told_set "$SID" 막음 "$RECEIPT"
  fi
else
  if [ "$AGAIN" = "1" ] || [ -f "$MARK" ]; then
    [ -f "$MARK" ] || : > "$MARK"
    [ "$(cat "$MARK.told" 2>/dev/null)" = "$PROG" ] || { printf '%s\n' "$PROG" > "$MARK.told"; nf_warn_once; }
    exit 0
  fi
  : > "$MARK"; rm -f "$MARK.told"
fi

_nf_nx="$(_nf_next_of "$ROOT")"
NF_GUIDE_SHORT="${NF_REGUIDE:-0}" python3 -I "$HERE/cockpit_upload_guide.py" "$URL" "$CHANGED" "$ROOT" "$HERE" "$ST" "$PAGENEW" "$(python3 -I "$HERE/other_cockpits.py" --안내 "$ST" "$HERE" 2>/dev/null || true)" > "$_nf_nx.tmp" 2>/dev/null && mv -f "$_nf_nx.tmp" "$_nf_nx"
exit 0
