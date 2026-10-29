#!/bin/bash
if [ -z "${NF_LC_WAS:-}" ]; then
  for _nf_lcv in "${LC_ALL:-}" "${LC_MESSAGES:-}" "${LANG:-}"; do
    case "$_nf_lcv" in C|POSIX|C.*|"") : ;; *) NF_LC_WAS="$_nf_lcv"; break ;; esac
  done
  unset _nf_lcv
fi
export NF_LC_WAS
LC_ALL=C; export LC_ALL
set -eu
_nf_me="${BASH_SOURCE[0]:-$0}"; _nf_i=0
while [ -L "$_nf_me" ] && [ "$_nf_i" -lt 20 ]; do
  _nf_t="$(readlink "$_nf_me" 2>/dev/null)" || break
  case "$_nf_t" in /*) _nf_me="$_nf_t" ;; *) _nf_me="$(cd "$(dirname "$_nf_me")" 2>/dev/null && pwd -P)/$_nf_t" ;; esac
  _nf_i=$((_nf_i + 1))
done
if [ -L "$_nf_me" ]; then NF_PYDIR=""; else NF_PYDIR="$(cd "$(dirname "$_nf_me")" 2>/dev/null && pwd -P)"; fi
unset _nf_me _nf_i _nf_t

APP="${1:?앱 폴더 경로가 필요하다}"
APP=$(cd "$APP" && pwd)
ICTO="$(cd "${NF_PYDIR:-$(dirname "$0")}/.." && pwd)"
SHARED="$ICTO/tools"

if [ "$APP" = "$ICTO" ]; then
  echo "  🔴 여기는 야간비행 자신입니다 — 여기에 다시 깔면 **도구가 지워집니다.**" >&2
  echo "     (주는 쪽과 받는 쪽이 같은 폴더라, 링크가 원본을 덮습니다)" >&2
  echo "     만드시려는 앱 폴더를 적어 주세요." >&2
  exit 1
fi
VAULT="${NF_VAULT:-}"
if [ -z "$VAULT" ]; then
  for _v in "$HOME"/*/wiki; do
    if [ -f "$_v/작업환경/앱개발-교훈집.md" ]; then VAULT="$_v"; break; fi
  done
  unset _v
fi
case "$ICTO" in */.claude/plugins/*) PLUGIN_SPOT=1 ;; *) PLUGIN_SPOT="" ;; esac
if [ -z "$PLUGIN_SPOT" ] && [ -f "$ICTO/.claude-plugin/plugin.json" ] && [ ! -e "$ICTO/.git" ] && [ ! -f "$ICTO/.nightflight-dev" ]; then PLUGIN_SPOT=1; fi
STATE_DIR="$(cd "$APP" && CLAUDE_PROJECT_DIR="$APP" . "$NF_PYDIR/project-root.sh" >/dev/null 2>&1 && nf_state_make >/dev/null 2>&1; printf '%s' "${NF_STATE:-}")" || STATE_DIR=""
[ -n "$STATE_DIR" ] || STATE_DIR="$APP/.nightflight"
if [ -n "$PLUGIN_SPOT" ]; then TOOLDIR="$STATE_DIR/tools"; else TOOLDIR="$APP/tools"; fi
TOOLREL="${TOOLDIR#"$APP"/}"
mkdir -p "$TOOLDIR"
[ -n "$PLUGIN_SPOT" ] && printf '# 야간비행 도구로 가는 이 컴퓨터만의 링크입니다 — 저장소에 올리지 않습니다.\n*\n' > "$TOOLDIR/.gitignore"
if [ -n "$PLUGIN_SPOT" ]; then
  NF_SEEN_ROW="자세히는 \`@@LEDGER@@ show\`"
  NF_TOOLS_NOTE=" — 이 컴퓨터에만 있는 링크라 같이 일하는 분 컴퓨터에는 없습니다(그분도 야간비행을 깔면 생깁니다)"
  NF_BROKEN_NOTE="깨진 전제는 조종석에 표시된다."
else
  NF_SEEN_ROW="**화면 아래 상태줄에 항상 보인다** · 자세히는 \`@@LEDGER@@ show\`"
  NF_TOOLS_NOTE=""
  NF_BROKEN_NOTE="깨진 전제가 있으면 상태줄이 그 자리를 칠한다."
fi
BAKDIR="${NIGHTFLIGHT_HOME:-$HOME/.nightflight}/설치백업/$(date +%Y%m%d-%H%M%S)-$$"

S="$APP/.claude/settings.json"
OFF="$APP/.claude/NF_OFF"
[ -f "$OFF" ] && grep -vE '^\s*(#|$)' "$OFF" | while read -r ev; do
  echo "  · 훅 $ev — 꺼 두셔서 안 얹습니다 (.claude/NF_OFF)"
done

MISSING=$(python3 -I - "$ICTO/hooks/hooks.json" "$ICTO" "$S" "$OFF" <<'PY'
import json, os, sys
want = json.load(open(sys.argv[1])); want = want.get("hooks", want)
root, s = sys.argv[2], sys.argv[3]
off = set()
if len(sys.argv) > 4 and os.path.exists(sys.argv[4]):
    off = {l.strip() for l in open(sys.argv[4]) if l.strip() and not l.startswith("#")}
need = {h["command"].replace("${CLAUDE_PLUGIN_ROOT}", root)
        for ev, es in want.items() if ev not in off
        for e in es for h in e.get("hooks", [])}
have = set()
if os.path.exists(s):
    try:
        cur = json.load(open(s))
        have = {h.get("command") for es in cur.get("hooks", {}).values()
                for e in es for h in e.get("hooks", [])}
    except Exception:
        have = set()
print(len(need - have))
PY
)
if [ -f "$S" ] && [ "${MISSING:-1}" = "0" ]; then
  echo "  · 훅 — 이미 전부 있음"
else
  [ -f "$S" ] && [ "${MISSING:-1}" != "0" ] && echo "  ⚠️ 훅 $MISSING 개가 빠져 있었습니다 — 얹습니다"
  if [ -z "$PLUGIN_SPOT" ] && [ -f "$S" ]; then
    mkdir -p "$BAKDIR" && cp -p "$S" "$BAKDIR/settings.json" && { echo "  ⚠️ 이 앱의 원래 설정을 저장소 밖에 따로 남겼습니다(되돌리실 수 있습니다)"; echo "    [모델] 백업 자리: ${BAKDIR/#$HOME/~}/settings.json"; }
  fi
  case "${PLUGIN_SPOT:+plugin}" in
    plugin) echo "  · 훅 — 플러그인으로 깔려 있어 이미 돕니다(앱 설정에 다시 적지 않았습니다)"
                         echo "  · 상태줄 — 플러그인 자리에서는 붙이지 않았습니다" ;;
    *) mkdir -p "$APP/.claude" && python3 -I "$NF_PYDIR/새앱채우기.py" "$ICTO/hooks/hooks.json" "$ICTO" "$S" "$OFF"
       echo "  ✅ 반복 감지 훅 — 같은 파일을 한 대화에서 8번 고치면 알린다"
       echo "  ✅ 턴 끝 검사 — 검사가 «사람이 기억할 때»가 아니라 자동으로 돈다"
       echo "  ✅ 상태줄 — 기록이 «명령 없이» 화면 아래에 항상 보인다" ;;
  esac
fi

PAIR_OWN=""
for t in ledger.sh project-root.sh; do
  if [ -e "$TOOLDIR/$t" ] && [ ! -L "$TOOLDIR/$t" ]; then PAIR_OWN="$PAIR_OWN $t"; fi
done
if [ -n "$PAIR_OWN" ]; then
  mkdir -p "$STATE_DIR" && ln -sfn "$ICTO/bin/ledger.sh" "$STATE_DIR/ledger.sh"
  LEDGER_CMD="${STATE_DIR#"$APP"/}/ledger.sh"
else
  LEDGER_CMD="$TOOLREL/ledger.sh"
fi
C="$APP/AGENTS.md"
[ -f "$APP/CLAUDE.md" ] && C="$APP/CLAUDE.md"
if [ -f "$C" ] && grep -qF "## 이 앱을 시작할 때 (자동으로 안 따라오는 것들이라 여기 적는다)" "$C"; then
  echo "  · $(basename "$C") — 이미 붙어 있음"
else
  IMPORTS=""
  for f in "작업환경/앱개발-교훈집.md" "rules/general-workflow-rules.md"; do
    [ -f "$VAULT/$f" ] && IMPORTS="$IMPORTS@$VAULT/$f
"
  done
  if [ -z "$IMPORTS" ]; then
    :
  fi
  if [ -s "$C" ]; then
    mkdir -p "$BAKDIR" && cp -p "$C" "$BAKDIR/$(basename "$C")" && { echo "  · 이 앱의 원래 규칙 문서를 저장소 밖에 따로 남겼습니다(되돌리실 수 있습니다)"; echo "    [모델] 백업 자리: ${BAKDIR/#$HOME/~}/$(basename "$C")"; }
  fi
  if [ -n "$IMPORTS" ]; then NF_FOLLOWS="전역 \`~/.claude/CLAUDE.md\` 와 위 두 문서만이 이 앱에 따라오는 전부다."
  else NF_FOLLOWS="전역 \`~/.claude/CLAUDE.md\` 만이 이 앱에 따라오는 전부다."; fi
  [ -s "$C" ] && printf '\n' >> "$C"
  cat >> "$C" <<MD
$IMPORTS## 이 앱을 시작할 때 (자동으로 안 따라오는 것들이라 여기 적는다)

**프로젝트 메모리는 폴더별로 갈린다** — 이전 앱의 메모리는 하나도 안 따라온다.
$NF_FOLLOWS

1. **UI 파일 안에 로직 타입을 두지 않는다.** 막는 것은 \`import UIKit\` 이 아니라 **위치**다
   (어느 앱에서 로직 타입 다섯이 SwiftUI 파일에 얹혀 있어 테스트가 100초→0.2초가 될 것을 막고 있었다)
2. **사용자에게 보이는 문장은 로직의 출력**이므로 코어에 둔다
3. **빠른 테스트 층을 1일차에 만든다** — 나중에 하면 타입을 꺼내는 공사가 된다
4. **벤치마크는 사용자·매출·수익이 높은 앱만.** 평점 좋은 망한 앱을 따라가지 않는다

| 쓸 때 | 명령 |
|---|---|
| 시작 전 기계 점검 (10초) | \`$TOOLREL/app_preflight.sh\` |
| 화면 확인 (20초) | \`$TOOLREL/shot.sh [화면이름 …]\` |
| 기록 — 무엇을 안 겪었나 | ${NF_SEEN_ROW//@@LEDGER@@/$LEDGER_CMD} |
| 검사가 무언가 막았을 때 | \`$LEDGER_CMD 막음 "<일어나던 일>" "<무슨 검사>" "<안 막았으면>" --항목 "<…>" --값 "<…>"\` |
| 멈췄을 때 결정 카드 | \`$LEDGER_CMD 카드 "<무엇을>" "<왜>" "<나중에 정하면>" "<이것만 정하시면>" "<제가 맡는 것>"\` |
| **단계를 넘을 때** | \`$LEDGER_CMD 단계 "<이름>"\` → **전제 점검이 자동으로 뜬다** |
| 전제가 깨졌을 때 | \`$LEDGER_CMD 전제바뀜 "<결정>" "<무엇이 바뀌었나>"\` |
| 되돌릴 때 | \`$LEDGER_CMD 되돌림 "<결정>"\` (기록에 남는다) |
| 내가 자주 틀리는 전제 | \`$LEDGER_CMD 틀린전제\` |
| Supabase 권한 검사 | \`$TOOLREL/lint_supabase_grants.py\` |
| 「창업자 결정」 인용 검사 | \`$TOOLREL/check_attribution.py\` |
| 개념에 «방향»을 붙였나 검사 | \`$TOOLREL/lint_framing.py\` |
| 규정 인용에 확인 표지가 있나 검사 | \`$TOOLREL/lint_citations.py\` |
| 모델 호출이 끊기지 않게 버티나 검사 | \`$TOOLREL/lint_model_resilience.py\` |
| 밖으로 보내며 봉투를 빼먹었나 검사 | \`$TOOLREL/lint_outbound.py\` |
| **처음 한 번** — 아는 낱말 체크 | \`$LEDGER_CMD 낱말묻기\` → 답을 \`아는낱말\` 로 |
| 풀어 써야 할 말 (모델이 본다) | \`$LEDGER_CMD 풀어쓸말\` |

조종석은 기록 원문 대신 이 문구를 보여 준다. **없으면 기록 명령이 거절한다.**
| 기록 | 붙이는 것 |
|---|---|
| \`됐다\` · \`남은것\` | \`--화면 "<기능을 정확히>" --종류 "새 기능|문제 고침|안 보이는 작업"\` |
| \`하는중\` · \`다음\` | \`--화면 "<기능을 정확히>"\` |
| \`결정\` · \`막음\` | \`--항목 "<무엇에 대한 것>" --값 "<정한 것·막은 것>"\` |
| 이미 적힌 줄 | \`$LEDGER_CMD 화면문구 "<원문 그대로>" --화면 … --종류 …\` |

⛔ 지어낸 말·비유 금지 · 길이 제한 없음 — **뜻이 그대로 전달될 때까지만** 줄인다 · «무엇이 · 어떻게» 명사구.
⛔ \`안 보이는 작업\`(사용자가 화면·결과에서 아무 차이도 겪지 않는 일)은 진척에 안 나간다.
⚠️ 문구가 기능을 «정확하게» 적었는지는 검사가 못 본다 — 쓰기 전에 그 기능이 실제로 무엇을 하는지 연다.

\`ledger.sh 결정\` 은 **전제 없이는 거부한다.** 앱 개발 초기의 결정은 전부 «그때 맞다고 본 것» 위에
서 있고, **틀리는 것은 결정이 아니라 그 전제**다 (어느 앱에서 되돌린 셋이 전부 그랬다).
전제를 안 적으면 나중에 **무엇이 바뀌어서 다시 봐야 하는지**를 알 길이 없다.

그래서 **단계를 넘을 때마다 「이 전제들 아직 맞나요?」를 한 번 띄운다.** 전제는 조용히 낡는다 —
묻는 자리가 없으면 아무도 안 본다. $NF_BROKEN_NOTE

⛔ **기록에는 실제로 돌아간 검사만 적는다.** 막은 게 없으면 0이라고 쓴다 —
숫자를 채우려 드는 순간 기록이 광고가 되고, 그때 신뢰를 잃는다.

⭐ **칸은 둘뿐이고 둘 다 출처가 있다** — **막음은 검사가 부르고, 결정은 대표님 인용이 필수**다.
「피함」·「대신」은 없앴다(2026-09-26): 손으로만 적히던 칸이라 **반드시 부푼다.**
카드의 「안 여쭙고 처리한 것」은 **지난 카드 이후 쌓인 막음 줄**을 기계가 뽑으므로 지어낼 수 없다.
MD
  if [ -n "$IMPORTS" ]; then echo "  ✅ $(basename "$C") — 교훈집·규칙 연결 + 새 앱 규칙 넷"
  else echo "  ✅ $(basename "$C") — 새 앱 규칙 넷"; fi
fi

OK=0; BAD=""
SKIP=""
for t in $(cd "$SHARED" && ls | grep -vE '^(__pycache__|.*\.md)$'); do
  if [ -e "$TOOLDIR/$t" ] && [ ! -L "$TOOLDIR/$t" ]; then SKIP="$SKIP $t"; continue; fi
  ln -sfn "$SHARED/$t" "$TOOLDIR/$t"
  if [ -e "$TOOLDIR/$t" ]; then OK=$((OK+1)); else BAD="$BAD $t"; rm -f "$TOOLDIR/$t"; fi
done
if [ -n "$PAIR_OWN" ]; then
  SKIP="$SKIP ledger.sh project-root.sh"
  echo "  · 이 앱에 기록 도구와 이름이 같은 파일이 있어 기록 도구를 붙이지 않았습니다 —"
  echo "    그 파일을 다른 이름으로 옮기신 뒤 설치를 한 번 더 돌리시면 붙습니다."
  echo "    [모델] 겹친 파일: $TOOLREL/$PAIR_OWN (짝 ledger.sh · project-root.sh 를 둘 다 안 걸었다)"
else
  for t in ledger.sh project-root.sh; do
    ln -sfn "$ICTO/bin/$t" "$TOOLDIR/$t"
    [ -e "$TOOLDIR/$t" ] && OK=$((OK+1)) || BAD="$BAD $t"
  done
fi
echo "  ✅ $TOOLREL/ — 도구 ${OK}개 연결(전부 «닿는지» 확인함)"

( cd "$APP" && CLAUDE_PROJECT_DIR="$APP" bash "$ICTO/bin/ledger.sh" 등록 >/dev/null 2>&1 ) || true
if [ -n "$PAIR_OWN" ]; then
  :
elif (cd "$APP" && bash "$TOOLREL/ledger.sh" >/dev/null 2>&1); then
  echo "  ✅ 실제로 한 번 돌려 봤습니다 — 기록이 돕니다"
else
  echo "  🔴 깔리긴 했는데 **돌지 않습니다.**" >&2
  echo "     설치를 한 번 더 돌려 보시고, 그래도 안 되면 말씀해 주십시오." >&2
  exit 1
fi
[ -n "$SKIP" ] && echo "  · 이 앱에 같은 이름 파일이 있어 건드리지 않았습니다:$SKIP"
[ -n "$BAD" ] && { echo "  🔴 닿지 않아 뺐습니다:$BAD"; echo "     저장소가 온전한지 보십시오 — 원래 자리는 $SHARED"; }

echo
echo "붙었습니다."
if [ -x "$ICTO/bin/resources.sh" ]; then
  ( cd "$APP" && NIGHTFLIGHT_PROJECT_DIR="$APP" "$ICTO/bin/resources.sh" ) || true
fi
echo "  이제 만들고 싶은 앱을 말씀해 주세요."
