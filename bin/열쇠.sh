#!/bin/bash
if [ -z "${BASH_VERSION:-}" ] || [ -n "${POSIXLY_CORRECT:-}" ] || case ":${SHELLOPTS:-}:" in *:posix:*) true ;; *) false ;; esac; then exec env -u POSIXLY_CORRECT -u SHELLOPTS -u BASHOPTS bash "$0" "$@"; fi
set -uo pipefail
_nf_lc_old="${LC_ALL-}"
LC_ALL=C
umask 077
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/project-root.sh" 2>/dev/null || {
  echo "야간비행을 찾지 못했습니다. 다시 깔아 주십시오." >&2; exit 1; }

STATEFILE="$NF_HOME/열쇠상태"
[ -f "$STATEFILE" ] && chmod 600 "$STATEFILE" 2>/dev/null
NFL="$(LC_ALL="$_nf_lc_old" nf_lang)"
두말() { if [ "$NFL" = "en" ]; then printf '%s' "$2"; else printf '%s' "$1"; fi; }
GARBLED="$(두말 "서버가 뜻 모를 답을 보냈습니다. 잠시 뒤에 다시 해 주십시오." "Got an unexpected response from the server. Please try again in a moment.")"
서버말() { local t; t="$(nf_say "$1")"; printf '  %s\n' "${t:-$GARBLED}"; }

보여준다() {
  if [ -s "$STATEFILE" ]; then
    printf '  %s\n' "$(cat "$STATEFILE")"
    echo "  ⚠️ $(두말 "이건 마지막으로 넣었을 때 받은 말입니다. 지금 맞는지는 서버가 정합니다." "This is the status from when you last entered your key. Your current status may differ.")"
  else
    echo "  $(두말 "아직 이 컴퓨터를 켜지 않으셨습니다. 결제하셨으면 결제하신 메일 주소를 대화창에 알려 주십시오." "This computer isn't set up yet. If you've paid, tell this chat the email you paid with.")"
  fi
}

상태적기() { local t; t="$(nf_say "$1")"; [ -n "$t" ] || return 0
  [ -L "$STATEFILE" ] && rm -f "$STATEFILE"
  ( umask 077; printf '%s\n' "$t" > "$STATEFILE" ); chmod 600 "$STATEFILE" 2>/dev/null; }
맥목록() { NF_ANS="$1" NFL="$NFL" python3 -I -c '
import json, os
try: d = json.loads(os.environ["NF_ANS"])
except Exception: d = {}
en = os.environ.get("NFL") == "en"
for m in d.get("맥들") or []:
    if not isinstance(m, dict): continue
    번호, 등록, 마지막, mid = m.get("번호"), str(m.get("등록일") or "")[:10], str(m.get("마지막날") or "")[:10], str(m.get("id") or "")
    print(("    · Computer %s — added %s · last used %s  [%s]" if en else "    · %s번 컴퓨터 — 등록 %s · 마지막으로 쓴 날 %s  [%s]") % (번호, 등록 or "?", 마지막 or "?", mid))
' 2>/dev/null; }
정상답() { NF_ANS="$1" python3 -I -c 'import json,os,sys
try: d=json.loads(os.environ["NF_ANS"])
except Exception: sys.exit(1)
sys.exit(0 if isinstance(d, dict) and "있나" in d else 1)' 2>/dev/null; }
CODE="${1-}"
키읽기() { local v=""; IFS= read -r v || true; printf '%s' "$v" | tr -d '[:space:]'; }
[ "$CODE" = "-" ] && CODE="$(키읽기)"
case "$CODE" in
  ""|상태)
    echo "쓰는 법: 열쇠.sh -  (키는 표준입력 한 줄)   예: printf '%s\n' NF-ABCDEFGH-JKMNPQRSTU | 열쇠.sh -   (키 자리에 - 를 쓰면 키를 표준입력에서 읽어 명령 인자에 안 남긴다)"
    echo "         열쇠.sh - 풀기 <번호>             컴퓨터 자리를 바꾸는 확인 링크를 결제한 메일로 보냅니다(링크에서 고르고 확인해야 바뀝니다)"
    echo "         열쇠.sh 보기                       이 컴퓨터의 이용권 · 제품등록을 봅니다"
    echo "         열쇠.sh 무료메일                   메일로 확인 코드를 보냅니다 — 결제한 메일이면 플랜이, 아니면 무료 제품이 켜집니다(메일 주소는 표준입력 한 줄)"
    echo "         열쇠.sh 무료코드                   메일로 받은 여섯 자리 코드를 넣습니다(코드는 표준입력 한 줄)"
    echo "         열쇠.sh 컴퓨터바꾸기 <맥id>         컴퓨터 3대가 찼을 때, 사용자가 고른 한 대를 빼고 이 컴퓨터를 켭니다(고른 뒤에만)"
    echo "         열쇠.sh 앱빼기 <제품 번호> [확인]   다 만든 제품의 칸을 비웁니다(「확인」 없이는 무엇을 비울지만 말합니다)"
    echo "         열쇠.sh 등급 <라이트|플러스>         결제한 메일로 확인 링크를 보냅니다(링크에서 확인해야 바뀝니다 · 키는 없어도 됩니다)"
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

서버() {
  nf_post "$NF_BRAIN_BASE/rest/v1/rpc/$1" "$2" -H "apikey: $NF_DOORKEY" -H "Authorization: Bearer $NF_DOORKEY" 2>/dev/null
}
결제() { NF_BRAIN_TIMEOUT=20 nf_post "$NF_BRAIN_BASE/functions/v1/gyeolje/$1" "$2" -H "apikey: $NF_DOORKEY" 2>/dev/null; }
몸() { local v; for v in "$@"; do case "$v" in *$'\x1f'*) echo "{}"; return 1 ;; esac; done
  local IFS=$'\x1f'; NF_PAIRS="$*" python3 -I -c 'import json,os; a=os.environ["NF_PAIRS"].split("\x1f"); print(json.dumps(dict(zip(a[::2], a[1::2])), ensure_ascii=False))'; }
키꼴() { [[ "$1" =~ ^[Nn][Ff]-[A-HJKMNP-Za-hjkmnp-z2-9]{8}-[A-HJKMNP-Za-hjkmnp-z2-9]{10}$ ]]; }
꼴틀림() {
  echo "$(두말 "라이선스 키 꼴이 아닙니다. 메일로 받으신 NF- 로 시작하는 키를 그대로 붙여 넣어 주십시오." "That doesn't look like a Nightflight license key. Paste the key from your email exactly as it appears — it starts with NF-.")" >&2
  exit 1
}
못닿음() {
  echo "$(두말 "지금 서버에 닿지 못했습니다. 라이선스 키가 틀린 것이 아닙니다 — 잠시 뒤에 다시 해 주십시오." "Couldn't reach the Nightflight server. Your key is fine — please try again in a moment.")" >&2
  exit 1
}

case "$CODE" in
  무료메일)
    MAIL="$(키읽기)"
    case "$MAIL" in
      ?*@?*.?*) ;;
      *) echo "$(두말 "메일 주소 꼴이 아닙니다. 받으실 메일 주소를 그대로 적어 주십시오." "That doesn't look like an email address. Please type the address where you want the code.")" >&2; exit 1 ;;
    esac
    ANSWER="$(결제 %EB%AC%B4%EB%A3%8C%EB%A9%94%EC%9D%BC "$(몸 사람id "$PERSONID" 맥지문 "$MACPRINT" 메일 "$MAIL" 언어 "$NFL")")" || 못닿음
    [ -n "$ANSWER" ] || 못닿음
    if NF_ANS="$ANSWER" python3 -I -c '
import json, os, re, sys
try: d = json.loads(os.environ["NF_ANS"])
except Exception: sys.exit(1)
글 = " ".join(str(d.get(k) or "") for k in ("말", "말_en"))
sys.exit(0 if ("확인번호" in d or re.search(r"(?<!\d)\d{6}(?!\d)", 글)) else 1)' 2>/dev/null; then
      echo "  $(두말 "메일로 여섯 자리 확인 코드를 보냈습니다. 받으신 코드를 이 대화창에 알려 주십시오. 메일이 안 보이면 스팸함을 봐 주십시오." "We emailed you a six-digit code. Tell this chat the code. If you don't see the email, check your spam folder.")"
      echo "  [모델] 서버 답에 확인 코드가 실려 와서 보이지 않았습니다. 사용자에게 코드를 말하지 마십시오. 서버 대화(운영자)에 알릴 일입니다."
      exit 0
    fi
    서버말 "$ANSWER"
    exit 0 ;;
  무료코드)
    MCODE="$(키읽기)"
    case "$MCODE" in
      [0-9][0-9][0-9][0-9][0-9][0-9]) ;;
      *) echo "$(두말 "확인 코드는 메일로 받으신 숫자 여섯 자리입니다." "The code is the six digits from the email.")" >&2; exit 1 ;;
    esac
    ANSWER="$(결제 %EB%AC%B4%EB%A3%8C%EC%BD%94%EB%93%9C "$(몸 사람id "$PERSONID" 맥지문 "$MACPRINT" 코드 "$MCODE")")" || 못닿음
    [ -n "$ANSWER" ] || 못닿음
    서버말 "$ANSWER"
    if printf '%s' "$ANSWER" | grep -q '"컴퓨터가득"[[:space:]]*:[[:space:]]*true'; then
      맥목록 "$ANSWER"
      echo "  [모델] 위 목록을 사용자에게 보여 드리고 «뺄 컴퓨터 하나»를 고르시게 하십시오. 고르신 뒤에만: $0 컴퓨터바꾸기 <고른 컴퓨터의 맥id>"
      exit 1
    fi
    printf '%s' "$ANSWER" | grep -q '"된다"[[:space:]]*:[[:space:]]*true' || exit 1
    상태적기 "$ANSWER"
    exit 0 ;;
  컴퓨터바꾸기)
    MID="${2:?뺄 컴퓨터의 맥id를 적어 주십시오 — 무료코드가 보여 준 목록에 있습니다}"
    case "$MID" in *[!A-Za-z0-9_-]*|'') echo "$(두말 "컴퓨터 표시가 올바르지 않습니다. 목록에 나온 것을 그대로 써 주십시오." "That computer id doesn't look right. Use one from the list.")" >&2; exit 1 ;; esac
    ANSWER="$(결제 %EC%BB%B4%ED%93%A8%ED%84%B0%EB%B0%94%EA%BE%B8%EA%B8%B0 "$(몸 사람id "$PERSONID" 맥지문 "$MACPRINT" 맥id "$MID")")" || 못닿음
    [ -n "$ANSWER" ] || 못닿음
    서버말 "$ANSWER"
    printf '%s' "$ANSWER" | grep -q '"된다"[[:space:]]*:[[:space:]]*true' || exit 1
    상태적기 "$ANSWER"
    exit 0 ;;
  칸읽기)
    ANSWER="$(서버 내이용권 "$(몸 p_사람id "$PERSONID" p_맥지문 "$MACPRINT")")" || exit 4
    정상답 "$ANSWER" || exit 4
    printf '%s\n' "$ANSWER"
    exit 0 ;;
  보기)
    ANSWER="$(서버 내이용권 "$(몸 p_사람id "$PERSONID" p_맥지문 "$MACPRINT")")" || 못닿음
    [ -n "$ANSWER" ] || 못닿음
    정상답 "$ANSWER" || 못닿음
    ANSWER="$ANSWER" NFL="$NFL" python3 -I - <<'PY'
import json, os
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
    print(f"  Products       {수}/{(칸 + 1) if 칸 else 'no limit'}" + (f"  (1 free forever + {칸} paid)" if 칸 else ""))
else:
    print(f"  플랜        {dict(라이트='라이트', 헤비='플러스').get(d.get('등급'), d.get('등급'))} 플랜")
    print(f"  쓸 수 있는 날  {str(d.get('만료') or '')[:10]} 까지")
    print(f"  등록된 컴퓨터  {d.get('맥수')}/3")
    print(f"  제품등록     {수}/{(칸 + 1) if 칸 else '제한 없음'}" + (f"  (무료 1 + 유료 {칸} · 설계 단계부터)" if 칸 else "  (설계 단계부터)"))
if 무료:
    보임 = ("no app id" if en else "앱 번호를 못 읽은 제품") if 무료 in ("(번호없음)", "no-bundle-id") else 무료
    print(f"    · {보임}  " + ("(free product)" if en else "(무료 제품)"))
for a in 앱 + 접은:
    print(f"    · {a}" + (("  (번호 없는 프로젝트 — no app id)" if en else "  (앱 번호를 못 읽은 프로젝트들)") if a == "no-bundle-id" else ("  (folded — still counts)" if en else "  (접음 — 제품등록은 그대로 남습니다)") if a in 접은 else ""))
PY
    exit 0 ;;
  등급)
    NEW="${2:?라이트나 플러스 중 하나를 적어 주십시오}"; KEY="${3-}"; KEEP=""
    if [ "$KEY" = "남길" ]; then KEEP="${4:?남길 제품을 쉼표로 적어 주십시오}"; KEY=""
      case "$KEEP" in *[!a-z0-9.,-]*) echo "$(두말 "남길 제품은 목록에 나온 제품 번호를 쉼표로 이어 적어 주십시오." "List the products to keep, comma-separated, as shown.")" >&2; exit 1 ;; esac
    fi
    case "$NEW" in 라이트|헤비|플러스|lite|Lite|plus|Plus|heavy|Heavy) ;;
      *) echo "$(두말 "라이트나 플러스 중 하나로 말씀해 주십시오." "Please choose Lite or Plus.")" >&2; exit 1 ;; esac
    [ "$KEY" = "-" ] && KEY="$(키읽기)"
    if [ -n "$KEY" ]; then
      키꼴 "$KEY" || 꼴틀림
      ANSWER="$(결제 %EB%93%B1%EA%B8%89 "$(몸 사람id "$PERSONID" 맥지문 "$MACPRINT" 키 "$KEY" 등급 "$NEW" 언어 "$NFL")")" || 못닿음
    elif [ -n "$KEEP" ]; then
      ANSWER="$(결제 %EB%93%B1%EA%B8%89 "$(몸 사람id "$PERSONID" 맥지문 "$MACPRINT" 등급 "$NEW" 언어 "$NFL" 남길 "$KEEP" \
        | python3 -I -c 'import json,sys; d=json.load(sys.stdin); d["남길"]=[x for x in d["남길"].split(",") if x][:2]; print(json.dumps(d, ensure_ascii=False))')")" || 못닿음
    else
      ANSWER="$(결제 %EB%93%B1%EA%B8%89 "$(몸 사람id "$PERSONID" 맥지문 "$MACPRINT" 등급 "$NEW" 언어 "$NFL")")" || 못닿음
    fi
    [ -n "$ANSWER" ] || 못닿음
    서버말 "$ANSWER"
    if printf '%s' "$ANSWER" | grep -q '"앱들"' && printf '%s' "$ANSWER" | grep -q '"된다" *: *false'; then
      echo "  [모델] 위 목록을 사용자에게 보여 드리고 «계속 쓰실 유료 제품 2개까지»(무료 제품 1개는 따로 그대로)를 고르시게 하십시오. 답을 들은 뒤에만:"
      echo "  [모델]  $0 등급 라이트 남길 <고른 제품>[,<고른 제품>] — 고르지 않은 제품은 기다림 없이 빠집니다(하나씩 풀면 다시 넣을 때 30일을 기다립니다)."
    fi
    exit 0 ;;
  앱빼기)
    BID="${2:?비울 제품 번호를 적어 주십시오 — 「열쇠.sh 보기」에 나옵니다}"
    if [ "${3-}" != "확인" ]; then
      echo "  $(두말 "이 제품의 제품등록을 풀려고 합니다: $BID" "About to remove this product from your plan's product count: $BID")"
      echo "  $(두말 "풀면 그 자리가 바로 돌아옵니다. 같은 제품을 다시 넣는 것은 30일 뒤입니다(한 달에 한 번은 바로 됩니다). 무료 제품은 30일에 한 번 바꿀 수 있습니다. 푸시겠습니까?" "The slot comes back right away. Re-adding the same product waits 30 days (once a month it's immediate). The free product can be switched once every 30 days. Release it?")"
      echo "  [모델] 사람이 그러라고 하면: 열쇠.sh 앱빼기 $BID 확인 — 사람이 답하기 전에는 부르지 마십시오"
      exit 0
    fi
    ANSWER="$(서버 앱칸빼기 "$(몸 p_사람id "$PERSONID" p_맥지문 "$MACPRINT" p_번들id "$BID")")" || 못닿음
    [ -n "$ANSWER" ] || 못닿음
    서버말 "$ANSWER"
    rm -f "$NF_HOME/이용권.json" 2>/dev/null
    exit 0 ;;
esac

if [ "${2-}" = "풀기" ]; then
  NUM="${3:?뺄 컴퓨터의 번호를 적어 주십시오}"
  키꼴 "$CODE" || 꼴틀림
  case "$NUM" in ''|*[!0-9]*) echo "$(두말 "뺄 컴퓨터 번호는 숫자로 적어 주십시오." "Give the computer number as a digit.")" >&2; exit 1 ;; esac
  ANSWER="$(결제 %ED%92%80%EA%B8%B0 "$(몸 사람id "$PERSONID" 맥지문 "$MACPRINT" 키 "$CODE" 번호 "$NUM" 언어 "$NFL" \
    | python3 -I -c 'import json,sys; d=json.load(sys.stdin); d["번호"]=int(d["번호"]); print(json.dumps(d, ensure_ascii=False))')")" || 못닿음
  [ -n "$ANSWER" ] || 못닿음
  서버말 "$ANSWER"
  exit 0
fi

키꼴 "$CODE" || 꼴틀림
BODY="$(몸 p_사람id "$PERSONID" p_열쇠 "$CODE" p_맥지문 "$MACPRINT")"
ANSWER="$(서버 활성화 "$BODY")"
RC=$?

if [ "$RC" -ne 0 ] || [ -z "$ANSWER" ]; then
  echo "$(두말 "지금 서버에 닿지 못했습니다. 라이선스 키가 틀린 것이 아닙니다 — 잠시 뒤에 다시 해 주십시오." "Couldn't reach the Nightflight server. Your key is fine — please try again in a moment.")" >&2
  exit 1
fi

OUT="$(ANSWER="$ANSWER" NFL="$NFL" GARBLED="$GARBLED" python3 -I - <<'PY'
import json, os, sys
en = os.environ.get("NFL") == "en"
try:
    d = json.loads(os.environ["ANSWER"])
except Exception:
    print("ERR\t" + os.environ["GARBLED"]); sys.exit(0)
if not isinstance(d, dict) or "말" not in d:
    print("ERR\t" + os.environ["GARBLED"]); sys.exit(0)
말 = str((d.get("말_en") if en else None) or d["말"])
if d.get("코드") in ("메일확인", "맥가득"):
    print("MAIL\t" + 말); sys.exit(0)
print(("OK" if d.get("된다") else "NO") + "\t" + 말)
PY
)"
KIND="${OUT%%	*}"
SAID="${OUT#*	}"

printf '  %s\n' "$SAID"
if [ "$KIND" = "MAIL" ]; then
  ANSWER="$(결제 %ED%92%80%EA%B8%B0 "$(몸 사람id "$PERSONID" 맥지문 "$MACPRINT" 키 "$CODE" 언어 "$NFL")")" || 못닿음
  [ -n "$ANSWER" ] || 못닿음
  서버말 "$ANSWER"
  exit 0
fi
if [ "$KIND" = "OK" ]; then
  [ -L "$STATEFILE" ] && rm -f "$STATEFILE"
  ( umask 077; printf '%s\n' "$SAID" > "$STATEFILE" ); chmod 600 "$STATEFILE" 2>/dev/null
  exit 0
fi
exit 1
