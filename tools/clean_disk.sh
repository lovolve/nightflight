#!/bin/bash
if [ -z "${NF_LC_WAS:-}" ]; then
  for _nf_lcv in "${LC_ALL:-}" "${LC_MESSAGES:-}" "${LANG:-}"; do
    case "$_nf_lcv" in C|POSIX|C.*|"") : ;; *) NF_LC_WAS="$_nf_lcv"; break ;; esac
  done
  unset _nf_lcv
fi
export NF_LC_WAS
LC_ALL=C; export LC_ALL
set -e

APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1
[ "${1:-}" = "--list" ] && APPLY=0

die() { echo "⛔ $*" >&2; exit 1; }
[ "$(uname)" = "Darwin" ] || die "맥에서만 돈다."

_me="${BASH_SOURCE[0]}"; _i=0
while [ -L "$_me" ] && [ "$_i" -lt 20 ]; do
  _t="$(readlink "$_me")"; case "$_t" in /*) _me="$_t" ;; *) _me="$(cd "$(dirname "$_me")" && pwd -P)/$_t" ;; esac
  _i=$((_i+1))
done
TABLE="${CLEAN_TABLE:-$(cd "$(dirname "$_me")/.." 2>/dev/null && pwd -P)/data/cleanup_disk.tsv}"
unset _me _i _t
[ -f "$TABLE" ] || die "정리 기준표가 없습니다 — 아무것도 지우지 않습니다: $TABLE"

rows() {
  local g p c w e
  while IFS="$(printf '\t')" read -r g p c w e; do
    case "$g" in ""|"#"*) continue ;; esac
    [ "$g" = "$1" ] || continue
    p="${p/#\~/$HOME}"
    printf '%s\t%s\t%s\t%s\n' "$p" "$c" "$w" "$e"
  done < "$TABLE"
}
DENY_LIST="$(rows 금지 | cut -f1)"
ALLOW_LIST="$( { rows 지움; rows 조건; } | cut -f1 | sed 's|/\*$||')"

FREED=0
WOULD=0
FAILED=0
COVERED=""

rec() {
  [ -n "${CLEAN_NO_RECORD:-}" ] && return 0
  local SELF="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")"
  local L="$(cd "$(dirname "$SELF")/../bin" 2>/dev/null && pwd)/ledger.sh"
  [ -x "$L" ] || return 0
  "$L" "$1" "$2" "$3" "${4:-}" >/dev/null 2>&1 || true
  [ -n "${5:-}" ] && "$L" 화면문구 "$2" --항목 "$5" --값 "${6:-}" >/dev/null 2>&1 || true
}

bytes() {
  local v=""
  [ -e "$1" ] && v=$(du -sk "$1" 2>/dev/null | tail -1 | awk '{print $1*1024}')
  case "$v" in ''|*[!0-9]*) echo 0 ;; *) echo "$v" ;; esac
}
human() { awk -v b="$1" 'BEGIN{ s="B KB MB GB TB"; split(s,u," "); i=1;
  while (b>=1024 && i<5) { b/=1024; i++ } printf (i==1?"%d%s":"%.1f%s"), b, u[i] }'; }

under_any() {
  local p="$1" x
  while IFS= read -r x; do
    [ -n "$x" ] || continue
    case "$p" in "$x"|"$x"/*) return 0 ;; esac
  done <<EOF2
$2
EOF2
  return 1
}

CACHE_DIRS="Cache|Code Cache|GPUCache|Service Worker|DawnWebGPUCache|DawnGraphiteCache|Shared Dictionary|CachedData"

ok_to_delete() {
  local p="$1"
  case "$p" in
    ""|"/"|"$HOME"|"$HOME/") return 1 ;;
    *..*) return 1 ;;
    "$HOME"/*) ;;
    *) return 1 ;;
  esac
  case "$p" in
    "$HOME/.docker"*|"$HOME/.claude/projects"*|"$HOME/.ssh"*|"$HOME/Library/Keychains"*|"$HOME/.nightflight"*) return 1 ;;
    *"/Cookies"*|*"/Local Storage"*|*"/IndexedDB"*|*"/Session Storage"*|*"/WebStorage"*) return 1 ;;
  esac
  under_any "$p" "$DENY_LIST" && return 1
  under_any "$p" "$ALLOW_LIST" && return 0
  case "$p" in
    "$HOME/Library/Caches/"*.ShipIt) return 0 ;;
    "$HOME/Library/Application Support/"?*)
      local b="${p##*/}"
      case "|$CACHE_DIRS|" in *"|$b|"*) return 0 ;; esac ;;
  esac
  return 1
}

sweep() {
  local p="$1" why="$2" sz
  [ -e "$p" ] || return 0
  sz=$(bytes "$p"); [ "$sz" -gt 0 ] || return 0

  if ! ok_to_delete "$p"; then
    printf "  건너뜀 %8s  %s  (안전장치가 막았다)\n" "$(human "$sz")" "${p/#$HOME/~}"
    return 0
  fi
  if [ "$APPLY" -eq 0 ]; then
    printf "  지울것 %8s  %-52s %s\n" "$(human "$sz")" "${p/#$HOME/~}" "$why"
    WOULD=$((WOULD+sz)); return 0
  fi

  rm -rf "$p" 2>/dev/null || true
  if [ -e "$p" ]; then
    printf "  ⚠️ 실패 %8s  %s  (권한이 막혔다 — Finder 로 지우셔야 합니다)\n" "$(human "$sz")" "${p/#$HOME/~}"
    FAILED=$((FAILED+1))
  else
    printf "  지움   %8s  %s\n" "$(human "$sz")" "${p/#$HOME/~}"
    FREED=$((FREED+sz))
  fi
}

recent() { [ -n "$(find "$1" -maxdepth 2 -mtime -"$2" 2>/dev/null | head -1)" ]; }

expand() {
  local p="$1" x
  case "$p" in
    */\*) for x in "${p%/\*}"/* "${p%/\*}"/.[!.]*; do [ -e "$x" ] && printf '%s\n' "$x"; done ;;
    *) [ -e "$p" ] && printf '%s\n' "$p" ;;
  esac
  return 0
}

OPEN_FILES="$(lsof -Fn -u "$(id -u)" 2>/dev/null | sed -n 's/^n//p' | grep "^$HOME/Library/" | sort -u || true)"
in_use() {
  printf '%s\n' "$OPEN_FILES" | grep -qF "$1/" && return 0
  pgrep -qf "$1/" 2>/dev/null && return 0
  return 1
}

echo
if [ "$APPLY" -eq 1 ]; then echo "🧹 디스크 청소 — 실제로 지웁니다 (기준표: 표에 없는 자리는 안 지웁니다)"
else echo "👀 디스크 청소 — 보여만 드립니다. 지우려면 --apply (기준표: 표에 없는 자리는 안 지웁니다)"; fi
FREE_BEFORE=$(df -h /System/Volumes/Data | awk 'NR==2{print $4}')
echo "   시작 전 남은 공간: $FREE_BEFORE"

echo
echo "A. 지워도 다시 생기는 것"
while IFS="$(printf '\t')" read -r p c w e; do
  COVERED="$COVERED
${p%/\*}"
  while IFS= read -r x; do [ -n "$x" ] && sweep "$x" "$w"; done < <(expand "$p")
done < <(rows 지움)

echo
echo "A2. 앱 업데이트를 기다리는 파일"
for sh in "$HOME/Library/Caches/"*.ShipIt; do
  [ -d "$sh" ] || continue
  tgt=$(plutil -extract targetBundleURL raw -o - "$sh/ShipItState.plist" 2>/dev/null | sed 's|^file://||; s|/$||' || true)
  tgt=$(printf '%b' "${tgt//%/\\x}")
  name="$(basename "$sh" .ShipIt)"
  if [ -z "$tgt" ] || [ ! -e "$tgt" ]; then
    sweep "$sh" "대상 앱이 없다 — 죽은 업데이트"
    continue
  fi
  have=$(plutil -extract CFBundleShortVersionString raw -o - "$tgt/Contents/Info.plist" 2>/dev/null || true)
  newp=$(find "$sh" -maxdepth 4 -name Info.plist -path "*.app/Contents/*" 2>/dev/null | head -1 || true)
  want=""
  [ -n "$newp" ] && want=$(plutil -extract CFBundleShortVersionString raw -o - "$newp" 2>/dev/null || true)
  if [ -z "$want" ]; then
    sz=$(bytes "$sh")
    [ "$sz" -gt 52428800 ] && printf "  건너뜀 %8s  %-40s (안에 업데이트가 없다 — 판단 보류)\n" \
      "$(human "$sz")" "$name"
  elif [ -n "$have" ] && [ "$have" = "$want" ]; then
    sweep "$sh" "이미 적용된 업데이트 ($have)"
  else
    printf "  건너뜀 %8s  %-40s (설치 대기 %s → %s · 앱을 껐다 켜면 사라집니다)\n" \
      "$(human "$(bytes "$sh")")" "$name" "${have:-?}" "${want:-?}"
  fi
done

echo
echo "B. 앱 캐시 (쓰는 중이 아닌 앱만 — 로그인은 안 건드린다)"
for root in "$HOME/Library/Application Support"/*; do
  [ -d "$root" ] || continue
  under_any "$root" "$DENY_LIST" && continue
  app="$(basename "$root")"
  case "$app" in com.apple.*|CrashReporter|AddressBook|CloudDocs|Claude) continue ;; esac
  found="$(find "$root" -maxdepth 4 -type d 2>/dev/null | awk -F/ -v pat="$CACHE_DIRS" '
    BEGIN{n=split(pat,a,"|"); for(i=1;i<=n;i++) want[a[i]]=1}
    { if ($NF in want) print }' || true)"
  [ -n "$found" ] || continue
  tot=0
  while IFS= read -r d; do [ -n "$d" ] && tot=$((tot + $(bytes "$d"))); done <<EOF3
$found
EOF3
  [ "$tot" -ge 10485760 ] || continue
  if in_use "$root"; then
    printf "  건너뜀 %8s  %-40s (지금 쓰는 중이다 — 앱을 끈 뒤 다시 보십시오)\n" "$(human "$tot")" "$app"
    continue
  fi
  while IFS= read -r d; do [ -n "$d" ] && sweep "$d" "$app 캐시"; done <<EOF4
$found
EOF4
done

echo
echo "C. 조건이 맞는 것 (오래 안 씀 · 쓰는 앱이 꺼져 있음)"
while IFS="$(printf '\t')" read -r p c w e; do
  COVERED="$COVERED
${p%/\*}"
  days=""; case "$c" in 날수:*) days="${c#날수:}" ;; esac
  case "$days" in *[!0-9]*) days=30 ;; esac
  while IFS= read -r x; do
    [ -n "$x" ] || continue
    if [ "$c" = "앱꺼짐" ]; then
      if in_use "$x"; then
        printf "  건너뜀 %8s  %-40s (지금 쓰는 중이다 — 앱을 끈 뒤 다시 보십시오)\n" "$(human "$(bytes "$x")")" "$w"
        continue
      fi
      sweep "$x" "$w"; continue
    fi
    [ -n "$days" ] && recent "$x" "$days" && continue
    sweep "$x" "$w${days:+ (${days}일 넘게 안 씀)}"
  done < <(expand "$p")
done < <(rows 조건)

echo
echo "D. 사람이 판단할 것 (이 도구는 안 지웁니다 — 지우면 생기는 일을 보고 정하십시오)"
SHOWN=0
while IFS="$(printf '\t')" read -r p c w e; do
  COVERED="$COVERED
${p%/\*}"
  days="${c#날수:}"; case "$c" in 날수:*) ;; *) days="" ;; esac
  tot=0; n=0
  while IFS= read -r x; do
    [ -n "$x" ] || continue
    [ -n "$days" ] && recent "$x" "$days" && continue
    tot=$((tot + $(bytes "$x"))); n=$((n+1))
  done < <(expand "$p")
  [ "$tot" -ge 104857600 ] || continue
  label="${p%/\*}"; label="${label/#$HOME/~}"
  case "$p" in */\*) label="$label 안 ${n}개" ;; esac
  printf "  판단   %8s  %s — %s\n" "$(human "$tot")" "$w" "$label"
  printf "  %8s  └ 지우면: %s\n" "" "$e"
  SHOWN=$((SHOWN+1))
done < <(rows 판단)

ORPHAN=0
for d in "$HOME/Library/Application Support"/*; do
  [ -d "$d" ] || continue
  name="$(basename "$d")"
  case "$name" in com.apple.*|Caches|CrashReporter|AddressBook|CloudDocs|Google) continue ;; esac
  sz=$(bytes "$d"); [ "$sz" -gt 1073741824 ] || continue
  if [ ! -e "/Applications/$name.app" ] && [ ! -e "$HOME/Applications/$name.app" ]; then
    printf "  없는 앱? %7s  %-30s  (/Applications/%s.app 이 없다 — 이름이 달라 잘못 잡혔을 수 있습니다)\n" "$(human "$sz")" "$name" "$name"
    ORPHAN=$((ORPHAN+1))
  fi
done
for entry in "cursor|/Applications/Cursor.app" "vscode|/Applications/Visual Studio Code.app" \
             "android-studio|/Applications/Android Studio.app" "sublime|/Applications/Sublime Text.app"; do
  n="${entry%%|*}"; app="${entry#*|}"
  d="$HOME/.$n"; [ -d "$d" ] || continue
  [ -e "$app" ] && continue
  [ -e "$HOME$app" ] && continue
  sz=$(bytes "$d"); [ "$sz" -gt 52428800 ] || continue
  printf "  없는 앱? %7s  %-30s  (%s · ~%s 에서 못 찾았다)\n" "$(human "$sz")" "~/.$n" "$app" "$app"
  ORPHAN=$((ORPHAN+1))
done
[ "$SHOWN" -eq 0 ] && [ "$ORPHAN" -eq 0 ] && echo "  판단할 큰 것: 없음"

echo
echo "E. 표에 없는 큰 자리 (무엇인지 모릅니다 — 지우지 않습니다)"
UNK=0
for d in "$HOME/Library/Caches"/* "$HOME/Library/Developer"/* "$HOME"/.[!.]*; do
  [ -d "$d" ] && [ ! -L "$d" ] || continue
  under_any "$d" "$DENY_LIST" && continue
  under_any "$d" "$COVERED" && continue
  printf '%s\n' "$COVERED" | grep -qF "$d/" && continue
  printf '%s\n' "$DENY_LIST" | grep -qF "$d/" && continue
  case "$d" in *.ShipIt|"$HOME/.Trash") continue ;; esac
  sz=$(bytes "$d"); [ "$sz" -ge 1073741824 ] || continue
  printf "  모름   %8s  %s\n" "$(human "$sz")" "${d/#$HOME/~}"
  UNK=$((UNK+1))
done
[ "$UNK" -eq 0 ] && echo "  없음"

VARF=$(bytes /private/var/folders)
for _c in /private/var/folders/*/*/X/com.google.Chrome.code_sign_clone; do
  [ -d "$_c" ] && VARF=$(( VARF - $(bytes "$_c") ))
done
[ "$VARF" -lt 0 ] && VARF=0
if [ "$VARF" -gt 2147483648 ]; then
  echo
  echo "⚠️ 시스템 임시 폴더가 커졌습니다 — $(human "$VARF") (평소 900MB 안팎)"
  echo "   어떤 프로그램이 임시 파일을 만들고 안 치우는 중일 수 있습니다."
  echo "   ⛔ 직접 지우지 마십시오 (돌고 있는 앱이 씁니다). 재시동하면 비워집니다."
  echo "   ⭐ «지금» 조사하십시오 — 더 커지면 목록 조회가 안 됩니다:"
  echo "        ls -fU /private/var/folders/*/*/T | head -40"
  rec 막음 "시스템 임시 폴더가 $(human "$VARF") 까지 불어 있었다" \
           "clean_disk.sh 가 /private/var/folders 를 쟀다" \
           "더 커지면 목록 조회가 안 되어 원인을 찾기 어려워진다" \
           "시스템 임시 폴더" "$(human "$VARF") — 재시동하면 비워짐"
fi

echo
if [ "$APPLY" -eq 1 ]; then
  echo "✅ 되찾은 공간: $(human "$FREED")"
  [ "$FAILED" -gt 0 ] && echo "⚠️ 권한에 막힌 것 ${FAILED}건 — Finder 로 지우셔야 합니다"
  FREE_NOW=$(df -h /System/Volumes/Data | awk 'NR==2{print $4}')
  echo "   지금 남은 공간: $FREE_NOW"
else
  echo "👉 지우면 되찾을 공간: $(human "$WOULD")"
  echo "   실제로 지우려면:  $(basename "$0") --apply"
fi
echo
