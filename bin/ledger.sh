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

if [ "$#" -gt 0 ]; then
  _a=(); for _x in "$@"; do _a+=("$(printf '%s' "$_x" | tr '\t\n\r' '   ')"); done
  set -- "${_a[@]}"
fi

UNVERIFIED_TOKENS="안함 안봄 못봄 못봤 못했 못함 못확인 미확인 빌드만 코드에있 코드를읽 코드읽 기존코드 README에 적혀있"
unverified() {
  local h t; h=$(printf '%s' "${1:-}" | tr -d ' ')
  for t in $UNVERIFIED_TOKENS; do case "$h" in *"$t"*) return 0 ;; esac; done
  return 1
}

_nf_me="${BASH_SOURCE[0]:-$0}"; _nf_i=0
while [ -L "$_nf_me" ] && [ "$_nf_i" -lt 20 ]; do
  _nf_t="$(readlink "$_nf_me" 2>/dev/null)" || break
  case "$_nf_t" in /*) _nf_me="$_nf_t" ;; *) _nf_me="$(cd "$(dirname "$_nf_me")" 2>/dev/null && pwd -P)/$_nf_t" ;; esac
  _nf_i=$((_nf_i + 1))
done
if [ -L "$_nf_me" ]; then _PR=""; else _PR="$(cd "$(dirname "$_nf_me")" 2>/dev/null && pwd -P)/project-root.sh"; fi
unset _nf_me _nf_i _nf_t
if [ ! -f "$_PR" ]; then
  echo "  ⛔ 설치가 덜 끝났습니다 — 같이 와야 하는 파일이 빠져 있습니다." >&2
  echo "     설치를 한 번 더 돌리면 됩니다. 기록은 지워지지 않습니다." >&2
  echo "     [모델] 빠진 파일: $_PR" >&2
  exit 1
fi
. "$_PR"
STATE="$NF_STATE/ledger.tsv"
_nf_cmd="${1:-show}"
_nf_was_reg=""; nf_registered && _nf_was_reg=1
if [ -n "$_nf_was_reg" ] || [ "$_nf_cmd" = 등록 ]; then
  nf_state_make 2>/dev/null || mkdir -p "$(dirname "$STATE")"
else
  case "$_nf_cmd" in
    호칭|낱말묻기|아는낱말|아는말인가|풀어쓸말|낱말올림|사전예방|-h|--help|help|도움말) ;;
    show) echo "  이 폴더는 아직 야간비행에 등록되지 않았습니다 — 기록이 없습니다."
          echo "  [모델] 사용자가 «야간비행에 등록해» 같은 말을 하면 그때 ledger.sh 등록 을 부르십시오."
          exit 0 ;;
    *) echo "  이 폴더는 아직 야간비행에 등록되지 않아 기록하지 않았습니다." >&2
       echo "  [모델] 사용자가 등록해 달라고 하기 전에는 기록 명령을 쓰지 마십시오. 등록 요청이 있으면 ledger.sh 등록 을 먼저 부르십시오." >&2
       exit 3 ;;
  esac
fi

SCR=""; SCRK=""; FITEM=""; FVAL=""; FCOND=""; FSUB=(); _ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --화면) SCR="${2-}"; shift; [ $# -gt 0 ] && shift ;;
    --종류) SCRK="${2-}"; shift; [ $# -gt 0 ] && shift ;;
    --항목) FITEM="${2-}"; shift; [ $# -gt 0 ] && shift ;;
    --값)   FVAL="${2-}"; shift; [ $# -gt 0 ] && shift ;;
    --조건) FCOND="${2-}"; shift; [ $# -gt 0 ] && shift ;;
    --세부) FSUB+=("${2-}"); shift; [ $# -gt 0 ] && shift ;;
    *) _ARGS+=("$1"); shift ;;
  esac
done
set -- ${_ARGS[@]+"${_ARGS[@]}"}
_SL="$NF_PYDIR/../tools/lint_screen_label.py"
_LBL="$(dirname "$STATE")/item-labels.tsv"
_FLBL="$(dirname "$STATE")/feed-labels.tsv"
screen_need() {
  if [ -z "$SCR$SCRK" ] && [ -n "${2-}" ] && [ -f "$_LBL" ] \
     && awk -F'\t' -v x="$2" '$1==x{f=1} END{exit !f}' "$_LBL"; then SCR_OLD=1; return 0; fi
  SCR_OLD=0
  local kinds="새 기능|문제 고침|안 보이는 작업"
  case "${3-}" in 남은것) kinds="새 기능|문제 고침|대표님 결정 필요|안 보이는 작업" ;;
                  표준|시도|영향) kinds="사용자에게 보이는 것|안 보이는 작업" ;; esac
  local how='--화면 「사용자가 겪는 일을 정확히」'
  [ "$1" = 1 ] && how="$how --종류 「$kinds」"
  if [ "$1" = 1 ] && [ "$SCRK" = "안 보이는 작업" ] && [ -z "$SCR" ]; then
    python3 "$_SL" --한줄 --기록 "${3:-됐다}" --종류 "$SCRK" --숨김 || exit 1; return 0; fi
  if [ -z "$SCR" ] || { [ "$1" = 1 ] && [ -z "$SCRK" ]; }; then
    echo "  ⛔ 화면 문구가 없습니다 — 조종석은 원문 대신 이 문구를 보여 줍니다." >&2
    echo "     붙일 것: $how" >&2
    echo "     ⭐ 기능을 정확히 · 지어낸 말·비유 없이 · 길이 제한 없음 · «무엇이 어떻게» 명사구" >&2
    echo "        예: --화면 「질문에 다 답하지 않아도 출시 절차 결과 확인 가능」 --종류 「${kinds%%|*}」" >&2
    echo "     ⭐ 사용자가 화면·결과에서 아무 차이도 겪지 않는 일이면 --종류 「안 보이는 작업」만 붙입니다" >&2
    exit 1
  fi
  if [ "$1" = 1 ]; then python3 "$_SL" --한줄 --기록 "${3:-됐다}" --종류 "$SCRK" -- "$SCR" || exit 1
  else python3 "$_SL" --한줄 -- "$SCR" || exit 1; fi
}
screen_save() {
  [ "${SCR_OLD:-0}" = 1 ] && return 0
  printf '%s\t%s\t%s\n' "$1" "$SCR" "$SCRK" >> "$_LBL"
}
feed_need() {
  if [ -z "$FITEM$FVAL" ] && [ -n "${1-}" ] && [ -f "$_FLBL" ] \
     && awk -F'\t' -v x="$1" '$1==x{f=1} END{exit !f}' "$_FLBL"; then FEED_OLD=1; return 0; fi
  FEED_OLD=0
  if [ -z "$FITEM" ] || [ -z "$FVAL" ]; then
    if [ "${2:-1}" = 0 ]; then
      echo "  ⚠️ 조종석 «최근 기록» 칸이 없습니다 — 원문이 «화면 문구 없음» 표지와 나갑니다: $1" >&2
      FEED_OLD=1; return 0
    fi
    echo "  ⛔ 조종석 «최근 기록» 표의 칸이 없습니다 — 붙일 것: --항목 「무엇에 대한 것」 --값 「정한 것·막은 것」" >&2
    echo "     예: --항목 「앱 결제 처리」 --값 「세금 처리까지 대신하는 결제 대행사에 맡김」" >&2
    exit 1
  fi
  python3 "$_SL" --한줄 -- "$FITEM" || exit 1
  python3 "$_SL" --한줄 -- "$FVAL" || exit 1
  if [ "${3-}" = 결정 ]; then
    if [ -z "$FCOND" ]; then
      echo "  ⛔ 결정에는 «다시 볼 조건»의 화면 문구도 붙입니다 — --조건 「이것이 바뀌면」" >&2
      echo "     예: --조건 「글로벌 출시 계획이 바뀌면」" >&2
      exit 1
    fi
    python3 "$_SL" --한줄 -- "$FCOND" || exit 1
  fi
}
feed_save() {
  [ "${FEED_OLD:-0}" = 1 ] && return 0
  printf '%s\t%s\t%s\t%s\n' "$1" "$FITEM" "$FVAL" "$FCOND" >> "$_FLBL"
}
KIND="${1:-show}"

BOARD="$(dirname "$STATE")/board.url"
nf_part() {
  local f="$NF_PYDIR/ledger.d/$1.sh"
  if [ ! -f "$f" ]; then
    echo "  ⛔ 설치가 덜 끝났습니다 — 같이 와야 하는 파일이 빠져 있습니다." >&2
    echo "     설치를 한 번 더 돌리면 됩니다. 기록은 지워지지 않습니다." >&2
    echo "     [모델] 빠진 파일: $f" >&2
    exit 1
  fi
  printf '%s' "$f"
}
board_nudge() {
  [ -f "$BOARD" ] || return 0
  local url n seen
  url=$(head -1 "$BOARD")
  n=$(awk -F'\t' '$2=="결정"' "$STATE" 2>/dev/null | wc -l | tr -d ' ')
  seen=$(awk -F'\t' '$2=="조종석반영"{v=$3} END{print v+0}' "$STATE" 2>/dev/null)
  [ "$n" -gt "$seen" ] || return 0
  [ "$1" = "단계" ] || [ $((n - seen)) -ge 3 ] || return 0
  echo
  echo "  📋 **앱에서 보는 조종석을 갱신하십시오** — 결정 $((n - seen))건이 아직 조종석에 없습니다."
  echo "     $url"
  echo "     기록을 다시 읽어 그 주소로 다시 올리고, 끝나면 「조종석반영」으로 적습니다."
}

case "$KIND" in
  화면문구|조종석|조종석반영|조종석준비|조종석지금|카드|show) _NFP="$(nf_part 조종석)" || exit 1; . "$_NFP" ;;
  피함|대신|막음|됐다|못함|이어받기|시도|시도목록|하는중|다음|표준|표준목록|못함목록|남은것|남은것목록|끝냄) _NFP="$(nf_part 작업)" || exit 1; . "$_NFP" ;;
  결정|결정목록|되돌림|틀린전제|전제점검|전제바뀜|전제해소|묶임) _NFP="$(nf_part 결정)" || exit 1; . "$_NFP" ;;
  단계|단계연결|단계확인|검증|설계|갈래|단계옮김) _NFP="$(nf_part 단계)" || exit 1; . "$_NFP" ;;
  기능연결|기능추가|세부기능|세부빼기|세부상태|설계표|화면|화면요소|화면이동|화면종류|화면이름|화면언제|화면하는일|화면갈림|화면상태|화면상태비움|화면일|화면일빼기|화면빼기|기능빼기|화면문제|설치전|설치전확인|기능설명|세부언제|가져오기|기능진척|영향|제품소개|화면없음|독립|상태|상태목록|영향목록|고치기전) _NFP="$(nf_part 설계표)" || exit 1; . "$_NFP" ;;
  한국절차|사람확인|앱설정묻기|앱설정|앱설정보기|규정나이|관문|기다림|문의권함|기다림끝|풀림|없어짐) _NFP="$(nf_part 출시)" || exit 1; . "$_NFP" ;;
  낱말묻기|아는낱말|아는말인가|풀어쓸말|낱말올림|사전예방|호칭) _NFP="$(nf_part 낱말)" || exit 1; . "$_NFP" ;;
  등록) _NFP="$(nf_part 등록)" || exit 1; . "$_NFP" ;;
  바로잡기) _NFP="$(nf_part 바로잡기)" || exit 1; . "$_NFP" ;;
  레드팀) _NFP="$(nf_part 레드팀)" || exit 1; . "$_NFP" ;;
  기여동의|기여후보|기여|기여목록|기여취소) _NFP="$(nf_part 기여)" || exit 1; . "$_NFP" ;;

  *)
    case "${1:-}" in ""|-h|--help|help|도움말) _nf_rc=0 ;; *) echo "모르는 명령입니다: $1" >&2; _nf_rc=2 ;; esac
    awk '/^#   사용:/{f=1} f && !/^#/{exit} f && (/ledger\.sh / || /^# +--/ || /^#   [^ 🔴⭐⛔⚠(]/)' "$0" \
      | sed -e 's/^# \{0,1\}//' -e 's/ *([^()]*design\/[^()]*)//g'
    exit "$_nf_rc"
    ;;
esac
