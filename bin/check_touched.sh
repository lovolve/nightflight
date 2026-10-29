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
TOOLS="$(cd "$(dirname "$0")/../tools" && pwd)"
ALL="${1:-}"

NF_HOOK_IN=""
if [ ! -t 0 ]; then
  NF_HOOK_IN="$(python3 -I "$(cd "$(dirname "$0")" && pwd)/hook_in.py" 2>/dev/null)" || NF_HOOK_IN="$(cat 2>/dev/null || true)"
fi
if [ -n "$NF_HOOK_IN" ]; then
  export NF_HOOK_IN
  eval "$(python3 -I - <<'EOPY' 2>/dev/null || true
import json, os, shlex
try: d = json.loads(os.environ.get("NF_HOOK_IN") or "{}")
except Exception: d = {}
if not isinstance(d, dict): d = {}
sid = str(d.get("session_id") or "")
cwd = str(d.get("cwd") or "")
tr = str(d.get("transcript_path") or "")
if sid: print("export NF_SESSION=" + shlex.quote(sid))
if cwd: print("export NIGHTFLIGHT_PROJECT_DIR=" + shlex.quote(cwd))
if tr: print("export NF_TRANSCRIPT=" + shlex.quote(tr))
EOPY
)"
fi

. "$(dirname "$0")/project-root.sh"
REPO="$NF_ROOT"
[ -f "$NF_STATE/ledger.tsv" ] || exit 0

TOUCHED="$NF_STATE/repeat-guard.tsv"
RUN_LINTS=1
if [ "$ALL" != "--전부" ]; then
  S="${NF_SESSION:-${CLAUDE_CODE_SESSION_ID:-$(date +%Y%m%d)}}"
  if [ -f "$TOUCHED" ]; then
    awk -F'\t' -v s="$S" '$1==s{n++} END{exit !n}' "$TOUCHED" 2>/dev/null || RUN_LINTS=0
  else
    RUN_LINTS=0
  fi
fi

MSG_USER=""; MSG_MODEL=""
sayu() { if [ "$ALL" = "--전부" ]; then printf '%s\n' "$1"; else MSG_MODEL="${MSG_MODEL}${1}
"; fi; }
saym() { if [ "$ALL" = "--전부" ]; then printf '%s\n' "$1"; else MSG_MODEL="${MSG_MODEL}${1}
"; fi; }
MSG_NOTE=""
sayn() { if [ "$ALL" = "--전부" ]; then printf '%s\n' "$1"; else MSG_NOTE="${MSG_NOTE}${1}
"; fi; }

run_one() {
  [ "$RUN_LINTS" = 1 ] || return 0
  CHECKED=$((CHECKED+1))
  local out rc tgt="${3-.}"
  if [ "$tgt" = "-" ]; then out=$(cd "$REPO" && python3 "$TOOLS/$1" 2>&1); rc=$?
  else                      out=$(cd "$REPO" && python3 "$TOOLS/$1" "$tgt" 2>&1); rc=$?; fi
  if [ "$ALL" = "--전부" ]; then
    printf '  ── %s — %s\n' "$1" "$2"
    printf '%s\n' "$out" | sed 's/^/     /'
    return 0
  fi
  [ "$rc" -eq 0 ] && return 0
  HITS=$((HITS+1))

  local sig memo prev_sig prev_at now age
  sig=$(printf '%s' "$out" | shasum 2>/dev/null | cut -c1-12)
  memo="$NF_STATE/.said-$1"
  now=$(date +%s)
  if [ -n "$sig" ] && [ -f "$memo" ]; then
    prev_sig=$(cut -d' ' -f1 "$memo" 2>/dev/null)
    prev_at=$(cut -d' ' -f2 "$memo" 2>/dev/null)
    if [ "$prev_sig" = "$sig" ]; then
      age=$(( now - ${prev_at:-0} ))
      if [ "$age" -lt 86400 ]; then
        QUIET=$((QUIET+1))
        return 0
      fi
      printf '%s %s' "$sig" "$now" > "$memo" 2>/dev/null
      saym ""
      HIT_NAMES="${HIT_NAMES}${HIT_NAMES:+ · }$2"
      saym "  ⚠️ $2 — 하루째 그대로입니다. 자세히: 「검사 전부 보여줘」"
      return 0
    fi
  fi
  [ -n "$sig" ] && printf '%s %s' "$sig" "$now" > "$memo" 2>/dev/null
  saym ""
  HIT_NAMES="${HIT_NAMES}${HIT_NAMES:+ · }$2"
  saym "  ⚠️ $2 — $1"
  saym "$(printf '%s\n' "$out" | grep -v '^$' | head -12 | sed 's/^/     /')"
}

run_dev() { nf_dev 2>/dev/null || return 0; run_one "$@"; }

HITS=0; CHECKED=0; HIT_NAMES=""; QUIET=0
run_one lint_model_resilience.py "모델이 종료되면 그 기능이 멈추나"
run_one lint_unwired.py          "버튼은 있는데 아무것도 안 하나"                    -
run_one lint_supabase_grants.py  "서버 권한이 열려 있나"                            -
run_one lint_table_grants.py     "새 표에 누가 읽고 쓸 수 있는지 적었나"            -
run_one lint_citations.py        "규정을 인용한 자리에 확인 표지가 있나"            -
run_one lint_user_facing.py     "사용자에게 보이는 문구에 개발 용어가 있나"
run_one lint_handoff_claim.py    "「사용자가 하셔야」라고 하면서 눌러는 봤나"   -
run_dev lint_board_wiring.py     "계산은 되는데 화면에 안 가는 것이 있나"       -
run_dev lint_cockpit_classes.py  "조종석에서 막대 전용 이름을 다른 자리에 썼나"   -
run_dev lint_cockpit_scale.py    "조종석 글자 크기·굵기·간격이 정한 단계 안인가"   -
run_dev lint_cockpit_shape.py    "조종석 꼴 표가 지금 기록 자료를 다 덮나"   -
run_dev lint_cockpit_words.py    "조종석 화면 글에 «앱»을 썼나(«제품»으로)"      -
run_one lint_writing.py          "사용자에게 보이는 글이 쓰기 규칙을 지키나(한 이름 · 짧은 문장 · 한 동작)"  --자리=화면,기록표,알림
run_one lint_outbound.py         "밖으로 보내면서 봉투를 빼먹었나"              -
run_dev lint_webfont.py          "나가는 화면이 글꼴을 바깥에서 받나"            -
run_dev lint_skill_leak.py       "공개 쪽에 노하우가 샜나"                      -
run_dev lint_gate_leak.py        "공개 출시 절차 표에 기준값이 샜나"                 -
run_dev lint_deprecated.py       "폐기된 결론이 표지 없이 남아 있나"           -
run_dev lint_pinned_count.py   "지금을 말하는 검사 수가 실제와 다르나" -
run_dev lint_gate_bias.py      "공개 출시 절차 표가 원문보다 쉽게 적혀 있나" -
run_dev lint_vague_words.py    "제가 지어낸 불명확한 말이 사용자 쪽에 있나" -
run_one lint_screen_label.py   "조종석에 나가는 줄에 화면 문구·종류가 있나"   -
run_one lint_screen_spec.py    "화면 흐름의 화면마다 «언제 보나»·«하는 일»이 적혀 있나"   -
run_one lint_import.py         "개발 중간에 깐 앱이면 조종석 칸을 다 가져왔나(가져왔음 · 이 앱엔 없음 · 아직)"   -
run_dev lint_screen_words.py   "화면에 목록에 없는 새 말이 생겼나" -
run_dev lint_shell_hangul.py   "셸에 한글 변수 이름이 있나"                   -
run_dev lint_python_isolated.py "파이썬을 글로 넘길 때 열린 폴더를 끊었나"      -
run_dev lint_shell_backtick.py  "찍는 글 안에 백틱이 있나(배시가 돌린다)"      -
run_dev lint_old_python.py      "맥 기본 파이썬에서 돌 때 죽지 않나"            -
run_dev lint_shell_python.py    "셸 안에 파이썬이 늘지 않았나(도구가 안 닿는다)"  -
run_dev lint_ledger_schema.py   "기록 칸의 정의가 적는 쪽과 맞나"              -
run_dev lint_shell_locale.py    "한국어 지역 설정에서 멈추지 않나"             -
run_dev lint_cockpit_escape.py  "조종석이 기록 글을 눕혀서 끼우나"             -
run_dev lint_distribution.py     "받는 사람에게 나갈 것만 나가나"                   -
run_dev lint_history_leak.py     "공개 쪽 주석에 남의 앱 이름이 남았나"        -
run_dev lint_gates_web.py        "웹이 쓸 출시 절차 표가 낡았나"                     -

run_one lint_number_source.py    "돈·기간·비율에 출처가 붙어 있나"            -
run_one count_same_symptom.py    "같은 자리를 몇 번째 늘리는 중인가"

if [ "$ALL" = "--전부" ]; then
  echo
  echo "  ── 여기부터는 «보고 전용» — 판정이 서지 않아 턴 끝에는 말하지 않는다"
  run_one lint_framing.py        "개념에 «방향»을 붙였나"
  run_one check_attribution.py   "「창업자 결정」이라고 쓴 자리에 출처가 있나"
  run_one lint_open_decisions.py "안 정한 채 지나간 것이 있나"
  exit 0
fi

SPOKE=$((HITS - QUIET))
if [ "$SPOKE" -gt 0 ]; then
  sayu "  ⚠️ 해당될 수 있는 것 ${SPOKE} — ${HIT_NAMES}"
  sayu "     «고치라»는 말이 아닙니다. 해당되는지만 보시면 됩니다."
  sayu "     나머지까지 보시려면 「전부 보여줘」라고 말씀해 주세요."
fi

RS="$("$(dirname "$0")/resources.sh" 2>/dev/null || true)"
[ -n "${RS:-}" ] && sayn "$RS"

"$(dirname "$0")/turnline.sh" >/dev/null 2>&1 || true


if [ "$ALL" != "--전부" ]; then
  if [ -n "$MSG_MODEL" ]; then MSG_MODEL="${MSG_MODEL}${MSG_NOTE}"
  elif [ -n "$MSG_NOTE" ]; then
    _nf_nh="${NIGHTFLIGHT_HOME:-$HOME/.nightflight}"
    case "$_nf_nh" in /*) mkdir -p "$_nf_nh" 2>/dev/null && printf '%s' "$MSG_NOTE" >> "$_nf_nh/다음알림" 2>/dev/null ;; esac
  fi
  python3 -I - "$MSG_USER" "$MSG_MODEL" <<'EOPY'
import json, sys
u = sys.argv[1].strip("\n"); m = sys.argv[2].strip("\n")
o = {}
if u: o["systemMessage"] = u
if m: o["hookSpecificOutput"] = {"hookEventName": "Stop", "additionalContext": m}
if o: print(json.dumps(o, ensure_ascii=False))
EOPY
fi
exit 0
