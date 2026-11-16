#!/bin/bash
if [ -z "${BASH_VERSION:-}" ] || [ -n "${POSIXLY_CORRECT:-}" ] || case ":${SHELLOPTS:-}:" in *:posix:*) true ;; *) false ;; esac; then exec env -u POSIXLY_CORRECT -u SHELLOPTS -u BASHOPTS bash "$0" "$@"; fi
set -uo pipefail
_nf_lc_old="${LC_ALL-}"
LC_ALL=C
umask 077
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/project-root.sh" 2>/dev/null || {
  echo "야간비행을 찾지 못했습니다. 다시 깔아 주십시오." >&2; exit 1; }

STATEFILE="$NF_HOME/license_state"
[ -f "$STATEFILE" ] && chmod 600 "$STATEFILE" 2>/dev/null
NFL="$(LC_ALL="$_nf_lc_old" nf_lang)"
두말() { if [ "$NFL" = "en" ]; then printf '%s' "$2"; else printf '%s' "$1"; fi; }
GARBLED="$(두말 "서버가 뜻 모를 답을 보냈습니다. 잠시 뒤에 다시 해 주십시오." "Got an unexpected response from the server. Please try again in a moment.")"
서버말() { local t; t="$(nf_say "$1")"; printf '  %s\n' "${t:-$GARBLED}"; }

보여준다() {
  if [ -n "$(nf_ckey)" ]; then
    _m="$(head -c 120 "$NF_HOME/account/mail" 2>/dev/null | tr -d '\n')"
    echo "  $(두말 "이 컴퓨터는 ${_m:-계정}에 연결돼 있습니다." "This computer is connected to ${_m:-your account}.")"
  else
    echo "  $(두말 "이 컴퓨터는 아직 계정에 연결되지 않았습니다. 이용권을 사셨으면 «야간비행 로그인»이라고 말씀해 주십시오." "This computer isn't connected to an account yet. If you bought a plan, say “Nightflight login”.")"   # 2026-11-10 계정 로그인으로 바꿈
  fi
}

정상답() { NF_ANS="$1" python3 -I -c 'import json,os,sys
try: d=json.loads(os.environ["NF_ANS"])
except Exception: sys.exit(1)
sys.exit(0 if isinstance(d, dict) and "있나" in d else 1)' 2>/dev/null; }
CODE="${1-}"
case "$CODE" in
  ""|상태)
    echo "쓰는 법: license_key.sh 로그인                     이 컴퓨터를 구글 · 애플 계정에 연결합니다(주소와 확인 문자를 보이고 브라우저를 엽니다)"
    echo "         license_key.sh 로그인대기                 승인을 기다립니다(끝값 0 연결 · 3 아직 — 다시 부릅니다 · 1 실패)"
    echo "         license_key.sh 계정                       이 컴퓨터가 어느 계정에 붙어 있나 봅니다"
    echo "         license_key.sh 해제 [확인]                이 컴퓨터만 계정에서 뗍니다(「확인」 없이는 무엇을 할지만 말합니다)"
    echo "         license_key.sh 보기                       이 컴퓨터의 이용권 · 제품등록을 봅니다"
    echo "         license_key.sh 앱빼기 <제품 번호> [확인]   다 만든 제품의 칸을 비웁니다(「확인」 없이는 무엇을 비울지만 말합니다)"
    echo "         license_key.sh 등급                       플랜 바꾸기 · 다시 사기 · 다른 컴퓨터 해제를 하는 내 계정 화면 주소를 보입니다"
    echo
    보여준다
    exit 0 ;;
esac

PERSONID="$(nf_personid | tr -d '[:space:]')"
if [ -z "$PERSONID" ]; then
  echo "$(두말 "이 컴퓨터에 자리를 만들지 못했습니다. 야간비행을 다시 깔아 주십시오." "Nightflight couldn't set itself up on this computer. Please reinstall it.")" >&2
  exit 1
fi
MACPRINT="$(nf_macprint | tr -d '[:space:]')"
if [ -z "$MACPRINT" ]; then
  echo "$(두말 "이 컴퓨터를 알아보지 못했습니다. 야간비행을 다시 깔아 주십시오." "Nightflight couldn't recognize this computer. Please reinstall it.")" >&2
  exit 1
fi

CKEY="$(nf_ckey)"

서버() {
  nf_post "$NF_BRAIN_BASE/rest/v1/rpc/$1" "$2" -H "apikey: $NF_DOORKEY" 2>/dev/null
}
몸() { local v; for v in "$@"; do case "$v" in *$'\x1f'*) echo "{}"; return 1 ;; esac; done
  local IFS=$'\x1f'; NF_PAIRS="$*" python3 -I -c 'import json,os; a=os.environ["NF_PAIRS"].split("\x1f"); print(json.dumps(dict(zip(a[::2], a[1::2])), ensure_ascii=False))'; }
못닿음() {
  echo "$(두말 "지금 서버에 닿지 못했습니다. 라이선스 키가 틀린 것이 아닙니다 — 잠시 뒤에 다시 해 주십시오." "Couldn't reach the Nightflight server. Your key is fine — please try again in a moment.")" >&2
  exit 1
}

case "$CODE" in
  로그인|로그인대기|계정|해제)
    case "$CODE" in 로그인) SUB=시작 ;; 로그인대기) SUB=대기 ;; 계정) SUB=상태 ;; *) SUB=해제 ;; esac
    NF_HOME="$NF_HOME" NF_BRAIN_BASE="$NF_BRAIN_BASE" NF_DOORKEY="$NF_DOORKEY" NF_PID="$PERSONID" NF_MPRINT="$MACPRINT" NFL="$NFL" \
      exec python3 -I "$HERE/account_login.py" "$SUB" "${@:2}" ;;
  칸읽기)
    ANSWER="$(서버 내이용권 "$(몸 p_사람id "$PERSONID" p_맥지문 "$MACPRINT" ${CKEY:+p_컴퓨터열쇠 "$CKEY"})")" || exit 4
    정상답 "$ANSWER" || exit 4
    printf '%s\n' "$ANSWER"
    exit 0 ;;
  보기)
    ANSWER="$(서버 내이용권 "$(몸 p_사람id "$PERSONID" p_맥지문 "$MACPRINT" ${CKEY:+p_컴퓨터열쇠 "$CKEY"})")" || 못닿음
    [ -n "$ANSWER" ] || 못닿음
    정상답 "$ANSWER" || 못닿음
    ANSWER="$ANSWER" NFL="$NFL" NF_PYDIR="$NF_PYDIR" NF_HOME="$NF_HOME" python3 -I - <<'PY'
import json, os, sys
sys.path.insert(0, os.environ["NF_PYDIR"]); import product_name; 표 = product_name.목록()
d = json.loads(os.environ["ANSWER"])
en = os.environ.get("NFL") == "en"
if not d.get("있나"):
    print("  No plan on this computer." if en else "  이 컴퓨터에는 이용권이 없습니다.")
    raise SystemExit(0)
칸 = d.get("칸수")
앱 = d.get("앱들") or []
무료 = d.get("무료앱")
접은 = d.get("접은제품") or []
수 = len(앱) + len(접은) + (1 if 무료 else 0)
if en:
    print(f"  Plan           {dict(라이트='Lite', 헤비='Plus').get(d.get('등급'), d.get('등급'))} plan")
    print(f"  Valid until    {str(d.get('만료') or '')[:10]}")
    print(f"  Computers      {d.get('맥수')}/3")
    print(f"  Products       {수}/{(칸 + 1) if 칸 else 'no limit'}" + (f"  (1 free + {칸} paid)" if 칸 else ""))
else:
    print(f"  플랜        {dict(라이트='라이트', 헤비='플러스').get(d.get('등급'), d.get('등급'))} 플랜")
    print(f"  쓸 수 있는 날  {str(d.get('만료') or '')[:10]} 까지")
    print(f"  등록된 컴퓨터  {d.get('맥수')}/3")
    print(f"  제품등록     {수}/{(칸 + 1) if 칸 else '제한 없음'}" + (f"  (무료 1 + 유료 {칸} · 설계 단계부터)" if 칸 else "  (설계 단계부터)"))
if 무료:
    print(f"    · {product_name.보임(무료, 표, en)}  " + ("(free product)" if en else "(무료 제품)"))
for a in 앱 + 접은:
    print(f"    · {product_name.보임(a, 표, en)}" + (("  (folded — still counts)" if en else "  (접음 — 제품등록은 그대로 남습니다)") if a in 접은 else ""))
PY
    exit 0 ;;
  등급)
    echo "  $(두말 "플랜 바꾸기 · 다시 사기 · 다른 컴퓨터 해제는 내 계정 화면에서 합니다. 이 컴퓨터를 연결한 계정으로 로그인해 주십시오:" "Change your plan, renew, or disconnect other computers on your account page. Sign in with the account this computer is connected to:")"
    echo "    https://account.lovolve.app"
    exit 0 ;;
  앱빼기)
    BID="${2:?비울 제품 번호를 적어 주십시오 — 「license_key.sh 보기」에 나옵니다}"
    if [ "${3-}" != "확인" ]; then
      _nf_name="$(NFL="$NFL" NF_HOME="$NF_HOME" python3 -I "$NF_PYDIR/product_name.py" "$BID" 2>/dev/null)"
      echo "  $(두말 "이 제품의 제품등록을 풀려고 합니다: ${_nf_name:-$BID}" "About to remove this product from your plan's product count: ${_nf_name:-$BID}")"
      echo "  $(두말 "풀면 그 자리가 바로 돌아옵니다. 같은 제품을 다시 넣는 것은 30일 뒤입니다(한 달에 한 번은 바로 됩니다). 무료 제품은 30일에 한 번 바꿀 수 있습니다. 푸시겠습니까?" "The slot comes back right away. Re-adding the same product waits 30 days (once a month it's immediate). The free product can be switched once every 30 days. Release it?")"
      echo "  [모델] 사람이 그러라고 하면: license_key.sh 앱빼기 $BID 확인 — 사람이 답하기 전에는 부르지 마십시오"
      exit 0
    fi
    ANSWER="$(서버 앱칸빼기 "$(몸 p_사람id "$PERSONID" p_맥지문 "$MACPRINT" p_번들id "$BID" ${CKEY:+p_컴퓨터열쇠 "$CKEY"})")" || 못닿음
    [ -n "$ANSWER" ] || 못닿음
    서버말 "$ANSWER"
    rm -f "$NF_HOME/license.json" 2>/dev/null
    exit 0 ;;
esac

echo "$(두말 "그 명령은 없습니다. 이용권은 «야간비행 로그인»으로 켭니다." "That command doesn't exist. Turn on your plan with “Nightflight login”.")" >&2
exit 2
