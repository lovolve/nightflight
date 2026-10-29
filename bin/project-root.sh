#!/bin/bash
if [ -z "${NF_LC_WAS:-}" ]; then
  for _nf_lcv in "${LC_ALL:-}" "${LC_MESSAGES:-}" "${LANG:-}"; do
    case "$_nf_lcv" in C|POSIX|C.*|"") : ;; *) NF_LC_WAS="$_nf_lcv"; break ;; esac
  done
  unset _nf_lcv
fi
export NF_LC_WAS
LC_ALL=C; export LC_ALL
nf_curl() {
  _nf_c_https=1
  for _nf_c_a in "$@"; do
    case "$_nf_c_a" in
      http://*)  nf_dev 2>/dev/null && _nf_c_https=0; break ;;
      https://*) _nf_c_https=1; break ;;
    esac
  done
  unset _nf_c_a
  if [ "$_nf_c_https" = 1 ]; then
    unset _nf_c_https
    command curl -q --noproxy '*' --proto '=https' "$@"
  else
    unset _nf_c_https
    command curl -q --noproxy '*' "$@"
  fi
}

nf_post() {
  _nf_u="$1"; shift
  _nf_b="$1"; shift
  printf '%s' "$_nf_b" | nf_curl -sS --max-time "${NF_BRAIN_TIMEOUT:-10}" \
    -X POST "$_nf_u" -H 'Content-Type: application/json' "$@" --data-binary @-
  _nf_rc=$?
  unset _nf_u _nf_b
  return $_nf_rc
}

nf_realdir() {
  _nf_rp="${1:-}"
  _nf_rn=0
  while [ -L "$_nf_rp" ] && [ "$_nf_rn" -lt 20 ]; do
    _nf_rl="$(readlink "$_nf_rp" 2>/dev/null)" || break
    case "$_nf_rl" in
      /*) _nf_rp="$_nf_rl" ;;
      *)  _nf_rp="$(cd "$(dirname "$_nf_rp")" 2>/dev/null && pwd -P)/$_nf_rl" ;;
    esac
    _nf_rn=$((_nf_rn + 1))
  done
  if [ -L "$_nf_rp" ]; then unset _nf_rp _nf_rn _nf_rl; return 1; fi
  (cd "$(dirname "$_nf_rp")" 2>/dev/null && pwd -P)
  unset _nf_rp _nf_rn _nf_rl
}

NF_PYDIR="$(nf_realdir "${BASH_SOURCE[0]:-$0}")"

NF_ROOT=""
for k in NIGHTFLIGHT_PROJECT_DIR CLAUDE_PROJECT_DIR CODEX_PROJECT_DIR CURSOR_PROJECT_DIR PROJECT_ROOT; do
  v="$(eval printf '%s' "\${$k:-}")"
  [ -n "$v" ] && [ -d "$v" ] && NF_ROOT="$v" && break
done
[ -n "$NF_ROOT" ] || NF_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD")"
NF_STATE=""
if [ -d "$NF_ROOT/.nightflight" ]; then NF_STATE="$NF_ROOT/.nightflight"
elif [ -f "$NF_ROOT/.claude/ledger.tsv" ]; then NF_STATE="$NF_ROOT/.claude"
fi
[ -n "$NF_STATE" ] || NF_STATE="$NF_ROOT/.nightflight"

nf_registered() { [ -f "$NF_STATE/ledger.tsv" ]; }

NF_GI_MARK="야간비행이 더한 줄"
NF_GI_MARK2="야간비행이 더한 줄 (2)"

nf_state_make() {
  mkdir -p "$NF_STATE" 2>/dev/null || return 1
  if [ -f "$NF_ROOT/.claude-plugin/plugin.json" ] && [ -f "$NF_ROOT/.nightflight-dev" ] \
     && grep -q '"name"[[:space:]]*:[[:space:]]*"nightflight"' "$NF_ROOT/.claude-plugin/plugin.json" 2>/dev/null; then
    return 0
  fi
  if [ -e "$NF_STATE/.gitignore" ]; then
    grep -qF "$NF_GI_MARK2" "$NF_STATE/.gitignore" 2>/dev/null && return 0
  fi
  case "$NF_STATE" in
    */.claude) _nf_gi_name="기록폴더-claude-gitignore.txt" ;;
    *)         _nf_gi_name="기록폴더-gitignore.txt" ;;
  esac
  for _nf_d in "${CLAUDE_PLUGIN_ROOT:-}/data" \
               "${NF_PYDIR:-/nonexistent}/../data" \
               "${NIGHTFLIGHT_PLUGIN:-/nonexistent}/data"; do
    [ -f "$_nf_d/$_nf_gi_name" ] && _nf_gi="$_nf_d/$_nf_gi_name" && break
  done
  unset _nf_d
  if [ -n "${_nf_gi:-}" ] && [ -f "$_nf_gi" ]; then
    _nf_gi_body="$(cat "$_nf_gi")"
  else
    _nf_gi_body="$(printf '*\n!.gitignore\n')"
  fi
  _nf_gi_keep=""
  if [ -e "$NF_STATE/.gitignore" ]; then
    _nf_gi_keep="$(awk -v old="# ── $NF_GI_MARK " '
      function ours(l) { return (l ~ /^[[:space:]]*$/ || l ~ /^#/ || l == "*" || l == "/*" || l ~ /^!/) }
      { L[NR] = $0 }
      END {
        cut = NR + 1
        for (i = 1; i <= NR; i++) if (index(L[i], old) == 1) { cut = i; break }
        for (j = cut + 1; j <= NR; j++) if (!ours(L[j])) { cut = NR + 1; break }
        if (index(L[1], "# 야간비행이 이 폴더에 적는 것은") == 1) {
          all = 1; for (j = 1; j < cut; j++) if (!ours(L[j])) { all = 0; break }
          if (all) cut = 1
        }
        for (i = 1; i < cut; i++) print L[i]
      }' "$NF_STATE/.gitignore" 2>/dev/null)" || _nf_gi_keep=""
  fi
  if git -C "$NF_STATE" rev-parse --is-inside-work-tree >/dev/null 2>&1 && printf '%s' "$_nf_gi_body" | grep -q '^!'; then
    if [ -n "$(printf '%s' "$_nf_gi_keep" | tr -d '[:space:]')" ]; then
      printf '%s\n' "$_nf_gi_keep" > "$NF_STATE/.gitignore.nf$$" 2>/dev/null && mv -f "$NF_STATE/.gitignore.nf$$" "$NF_STATE/.gitignore" 2>/dev/null
    else
      rm -f "$NF_STATE/.gitignore" 2>/dev/null
    fi
    _nf_gi_body="$(printf '%s\n' "$_nf_gi_body" | while IFS= read -r _nf_l; do
      if [[ "$_nf_l" == '!'* && "$_nf_l" != '!.gitignore' && "$_nf_l" != *'*'* ]] \
         && git -C "$NF_STATE" check-ignore -q -- "${_nf_l#!}" 2>/dev/null; then
        continue
      fi
      printf '%s\n' "$_nf_l"
    done)"
    unset _nf_l
  fi
  { if [ -n "$(printf '%s' "$_nf_gi_keep" | tr -d '[:space:]')" ]; then printf '%s\n\n' "$_nf_gi_keep"; fi
    printf '# ── %s ── 시작\n%s\n# ── %s ── 끝\n' "$NF_GI_MARK2" "$_nf_gi_body" "$NF_GI_MARK2"
  } > "$NF_STATE/.gitignore.nf$$" 2>/dev/null && mv -f "$NF_STATE/.gitignore.nf$$" "$NF_STATE/.gitignore" 2>/dev/null || true
  unset _nf_gi_keep
  unset _nf_gi _nf_gi_name _nf_gi_body
  return 0
}

NF_HOME="${NIGHTFLIGHT_HOME:-$HOME/.nightflight}"
case "$NF_HOME" in /*) ;; *) NF_HOME="$HOME/.nightflight" ;; esac
if [ -n "${NIGHTFLIGHT_HOME:-}" ] && [ -e "$NF_HOME" ] && [ ! -O "$NF_HOME" ]; then NF_HOME="$HOME/.nightflight"; fi
NF_PERSON="$NF_HOME/사람.tsv"
NF_PERSONFILE="$NF_HOME/사람id"
export NF_ROOT NF_STATE NF_HOME NF_PERSON NF_PERSONFILE

nf_dev() {
  [ -n "${NF_PYDIR:-}" ] && [ -f "$NF_PYDIR/../.nightflight-dev" ]
}

NF_BRAIN_BUILTIN="https://tmrivrgrtgsjevikwagr.supabase.co"
NF_BRAIN_BASE="${NF_BRAIN_BASE:-$NF_BRAIN_BUILTIN}"
if [ -n "${NF_BRAIN_ANON:-}" ] && ! nf_dev; then
  case "$NF_BRAIN_ANON" in
    eyJ*.*.*) : ;;
    *) echo "  ⚠️ 저희 서버로 들어가는 열쇠가 이 컴퓨터 바깥에서 바뀌어 있어 **쓰지 않았습니다** — 원래 것으로 갑니다." >&2
       unset NF_BRAIN_ANON ;;
  esac
fi
NF_DOORKEY="${NF_BRAIN_ANON:-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtcml2cmdydGdzamV2aWt3YWdyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTEwOTE2ODgsImV4cCI6MjEwNjY2NzY4OH0.xIwOjKZX0OgkKsD9aKE3jh7-9E42mSW_Ld7iabOx9wA}"

nf_addr_ok() {
  case "${1:-}" in
    https://*) ;;
    http://*) nf_dev || return 1 ;;
    *) return 1 ;;
  esac
  _nf_h="${1#*://}"; _nf_h="${_nf_h%%/*}"; _nf_h="${_nf_h%%\?*}"; _nf_h="${_nf_h%%\#*}"
  _nf_h="$(printf '%s' "$_nf_h" | tr 'A-Z' 'a-z')"
  case "$_nf_h" in
    *[!a-z0-9.:-]*) return 1 ;;
  esac
  case "$_nf_h" in
    127.0.0.1|127.0.0.1:*|localhost|localhost:*)
      nf_dev && return 0 || return 1 ;;
    *)
      _nf_our="${NF_BRAIN_BUILTIN#*://}"; _nf_our="${_nf_our%%/*}"
      _nf_our="$(printf '%s' "$_nf_our" | tr 'A-Z' 'a-z')"
      if [ "$_nf_h" = "$_nf_our" ]; then
        unset _nf_our; return 0
      fi
      unset _nf_our
      case "$_nf_h" in
        *.supabase.co) nf_dev && return 0 || return 1 ;;
      esac
      return 1 ;;
  esac
}

if ! nf_addr_ok "$NF_BRAIN_BASE"; then
  echo "  ⚠️ 저희 서버로 가는 주소가 이 컴퓨터 바깥에서 바뀌어 있어 **쓰지 않았습니다** — 본래 주소로 갑니다." >&2
  NF_BRAIN_BASE="$NF_BRAIN_BUILTIN"
fi
if [ -n "${NF_BRAIN_URL:-}" ] && ! nf_addr_ok "$NF_BRAIN_URL"; then
  echo "  ⚠️ 저희 서버로 가는 주소가 이 컴퓨터 바깥에서 바뀌어 있어 **쓰지 않았습니다** — 본래 주소로 갑니다." >&2
  unset NF_BRAIN_URL
fi
if [ -n "${NF_CARRY_URL:-}" ] && ! nf_addr_ok "$NF_CARRY_URL"; then
  echo "  ⚠️ 저희 서버로 가는 주소가 이 컴퓨터 바깥에서 바뀌어 있어 **쓰지 않았습니다** — 본래 주소로 갑니다." >&2
  unset NF_CARRY_URL
fi

export NF_BRAIN_BASE NF_BRAIN_BUILTIN NF_DOORKEY

nf_keyline() {
  case "${1:-}" in
    만료)
      if [ "$(nf_lang)" = "en" ]; then
        echo "Renewed? Tell this chat the email you paid with, then enter the code we send you."
      else
        echo "갱신하셨으면 결제하신 메일 주소를 이 대화창에 알려 주십시오. 메일로 받은 코드를 넣으시면 바로 이어집니다."
      fi ;;
    *)
      if [ "$(nf_lang)" = "en" ]; then
        echo "Paid already? Tell this chat the email you paid with, then enter the code we send you."
      else
        echo "결제하셨으면 결제하신 메일 주소를 이 대화창에 알려 주십시오. 메일로 받은 코드를 넣으시면 됩니다."
      fi ;;
  esac
}

nf_personid() {
  mkdir -p "$NF_HOME" 2>/dev/null
  chmod 700 "$NF_HOME" 2>/dev/null || true
  if [ -L "$NF_PERSONFILE" ] || { [ -e "$NF_PERSONFILE" ] && [ ! -O "$NF_PERSONFILE" ]; }; then
    rm -f "$NF_PERSONFILE" 2>/dev/null || { echo "  ⛔ 이 컴퓨터의 야간비행 사람 번호 파일이 다른 계정 것입니다: $NF_PERSONFILE" >&2; return 1; }
  fi
  if [ ! -s "$NF_PERSONFILE" ]; then
    (uuidgen 2>/dev/null || python3 -I -c "import uuid; print(uuid.uuid4())") \
      | tr 'A-Z' 'a-z' > "$NF_PERSONFILE"
  fi
  chmod 600 "$NF_PERSONFILE" 2>/dev/null || true
  cat "$NF_PERSONFILE"
}

NF_LANG_SEEN=""
nf_lang() {
  if [ -n "$NF_LANG_SEEN" ]; then printf '%s' "$NF_LANG_SEEN"; return 0; fi
  case "${NF_LANG:-}" in
    ko|en) NF_LANG_SEEN="$NF_LANG"; printf '%s' "$NF_LANG_SEEN"; return 0 ;;
  esac
  _nf_l=""
  if [ "$(uname -s 2>/dev/null)" = "Darwin" ]; then
    _nf_l="$(defaults read -g AppleLanguages 2>/dev/null | tr -d ' "()' | tr -d "\n" | cut -d, -f1)"
  fi
  [ -n "$_nf_l" ] || _nf_l="${NF_LC_WAS:-${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}}"
  case "$_nf_l" in
    ko|ko[-_]*|Korean*) NF_LANG_SEEN="ko" ;;
    "")                 NF_LANG_SEEN="en" ;;
    *)                  NF_LANG_SEEN="en" ;;
  esac
  printf '%s' "$NF_LANG_SEEN"
}

nf_say() {
  NFL="$(nf_lang)" python3 -I - "${1:-}" "${2:-말}" <<'PYSAY' 2>/dev/null
import json, os, sys
try:
    d = json.loads(sys.argv[1] or "{}") or {}
except Exception:
    d = {}
칸 = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else "말"
글 = d.get(칸) or ""
if os.environ.get("NFL") == "en":
    글 = d.get(칸 + "_en") or 글
print(글)
PYSAY
}

nf_plan() {
  case "$(nf_lang)/${1:-}" in
    ko/라이트) printf '라이트 플랜' ;;
    ko/헤비)   printf '플러스 플랜' ;;
    ko/무제한) printf '맥스 플랜' ;;
    en/라이트) printf 'Lite plan' ;;
    en/헤비)   printf 'Plus plan' ;;
    en/무제한) printf 'Max plan' ;;
    *)         printf '%s' "${1:-}" ;;
  esac
}

nf_macprint() {
  if nf_dev && [ -n "${NF_MACPRINT:-}" ]; then
    printf '%s' "$NF_MACPRINT"; return
  fi
  local u=""
  case "$(uname -s 2>/dev/null)" in
    Darwin)
      u="$(ioreg -rd1 -c IOPlatformExpertDevice 2>/dev/null | awk -F'"' '/IOPlatformUUID/{print $4; exit}')" ;;
    Linux)
      [ -r /etc/machine-id ] && u="$(cat /etc/machine-id 2>/dev/null)"
      [ -n "$u" ] || { [ -r /var/lib/dbus/machine-id ] && u="$(cat /var/lib/dbus/machine-id 2>/dev/null)"; } ;;
    MINGW*|MSYS*|CYGWIN*)
      u="$(reg.exe query 'HKLM\SOFTWARE\Microsoft\Cryptography' //v MachineGuid 2>/dev/null \
           | awk '/MachineGuid/{print $NF; exit}' | tr -d '\r')" ;;
  esac
  u="$(printf '%s' "$u" | tr -d '[:space:]')"
  [ -n "$u" ] || return 0
  printf '야간비행:%s' "$u" | { shasum -a 256 2>/dev/null || sha256sum 2>/dev/null || openssl dgst -sha256 -r 2>/dev/null; } | awk '{print $1}'
}

nf_bundleid() {
  if nf_dev 2>/dev/null && [ -n "${NF_BUNDLEID+x}" ]; then printf '%s' "$NF_BUNDLEID"; return; fi
  local root="${NF_ROOT:-$PWD}" id
  id="$(find "$root" -maxdepth 4 -name project.pbxproj -not -path '*/Pods/*' -not -path '*/node_modules/*' 2>/dev/null \
    | head -5 \
    | xargs -I{} grep -h 'PRODUCT_BUNDLE_IDENTIFIER = ' {} 2>/dev/null \
    | sed -E 's/.*PRODUCT_BUNDLE_IDENTIFIER = "?([^";]*)"?;.*/\1/' \
    | grep -v -E '\$|Tests$|UITests$' \
    | awk '{ print length($0) "\t" $0 }' | sort -n | head -1 | cut -f2 \
    | tr 'A-Z' 'a-z')"
  if [ -n "$id" ]; then printf '%s' "$id"; return; fi
  id="$(find "$root" -maxdepth 4 \( -name build.gradle -o -name build.gradle.kts \) -not -path '*/node_modules/*' 2>/dev/null \
    | head -5 \
    | xargs -I{} grep -h -E '^[[:space:]]*applicationId[[:space:]=]+"[A-Za-z0-9_.]+"' {} 2>/dev/null \
    | sed -E 's/.*"([A-Za-z0-9_.]+)".*/\1/' \
    | awk '{ print length($0) "\t" $0 }' | sort -n | head -1 | cut -f2 \
    | tr 'A-Z_' 'a-z-')"
  if [ -n "$id" ]; then printf '%s' "$id"; return; fi
  local pj
  pj="$(find "$root" -maxdepth 3 -name package.json -not -path '*/node_modules/*' 2>/dev/null \
    | awk -F/ '{ print NF "\t" $0 }' | sort -n | head -1 | cut -f2-)"
  [ -n "$pj" ] || return 0
  python3 -I - "$pj" <<'EOPY' 2>/dev/null
import json, os, re, sys
p = sys.argv[1]
기본 = {"my-app", "my-project", "my-v0-project", "vite-project", "vite-react-typescript-starter",
        "react-app", "my-react-app", "next-app", "my-next-app", "nextjs", "svelte-app", "sveltekit",
        "astro", "nuxt-app", "app", "web", "website", "site", "frontend", "client", "project",
        "demo", "test", "untitled", "workspace", "monorepo", "root"}
def 다듬(x):
    x = re.sub(r"[^a-z0-9.-]+", "-", (x or "").lower()).strip(".-")
    return x[:150]
try:
    이름 = str(json.load(open(p, encoding="utf-8")).get("name") or "")
except Exception:
    이름 = ""
이름 = 다듬(이름.split("/")[-1] if 이름.startswith("@") else 이름)
if not 이름 or 이름 in 기본:
    이름 = 다듬(os.path.basename(os.path.dirname(os.path.abspath(p))))
if len(이름) >= 1:
    print("web." + 이름, end="")
EOPY
}
