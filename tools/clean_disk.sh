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

KEEP_DAYS="${CLEAN_KEEP_DAYS:-30}"
APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1
[ "${1:-}" = "--list" ] && APPLY=0

die() { echo "⛔ $*" >&2; exit 1; }
[ "$(uname)" = "Darwin" ] || die "맥에서만 돈다."

FREED=0
WOULD=0
FAILED=0

rec() {
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

ok_to_delete() {
  local p="$1"
  case "$p" in
    ""|"/"|"$HOME"|"$HOME/") return 1 ;;
    *..*) return 1 ;;
  esac
  case "$p" in
    "$HOME/Library/Caches/"?*) ;;
    "$HOME/Library/Application Support/"?*) ;;
    "$HOME/Library/Developer/Xcode/UserData/"?*) ;;
    "$HOME/.npm/_npx/"?*) ;;
    *) return 1 ;;
  esac
  case "$p" in
    "$HOME/.docker"*|"$HOME/.claude/projects"*) return 1 ;;
    *"/Google/Chrome"*|*"/Firefox"*|*"/CoreSimulator"*) return 1 ;;
    *"/Cookies"*|*"/Local Storage"*|*"/IndexedDB"*|*"/Session Storage"*|*"/WebStorage"*) return 1 ;;
  esac
  return 0
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

echo
if [ "$APPLY" -eq 1 ]; then echo "🧹 디스크 청소 — 실제로 지웁니다 (오래된 것 기준: ${KEEP_DAYS}일)"
else echo "👀 디스크 청소 — 보여만 드립니다. 지우려면 --apply (오래된 것 기준: ${KEEP_DAYS}일)"; fi
FREE_BEFORE=$(df -h /System/Volumes/Data | awk 'NR==2{print $4}')
echo "   시작 전 남은 공간: $FREE_BEFORE"

echo
echo "A. 순수 캐시 (지워도 다시 생긴다)"
sweep "$HOME/Library/Caches/pip"                                   "파이썬 패키지 캐시"
sweep "$HOME/Library/Caches/Homebrew"                              "brew 내려받기 캐시"
sweep "$HOME/Library/Caches/node-gyp"                              "네이티브 빌드 헤더"
sweep "$HOME/Library/Caches/deno"                                  "deno 모듈 캐시"
sweep "$HOME/Library/Caches/org.swift.swiftpm"                     "Swift 패키지 캐시 (다음 빌드 한 번 느림)"
sweep "$HOME/Library/Developer/Xcode/UserData/IB Support"          "인터페이스 빌더 찌꺼기"
sweep "$HOME/Library/Developer/Xcode/UserData/IB%20Support"        "같은 폴더가 URL 인코딩된 이름으로 하나 더 생긴다"
sweep "$HOME/Library/Caches/notion-updater"                        "노션 업데이터가 받아 둔 설치본"

echo
echo "A2. 앱 업데이트를 기다리는 파일"
for sh in "$HOME/Library/Caches/"*.ShipIt; do
  [ -d "$sh" ] || continue
  tgt=$(plutil -extract targetBundleURL raw -o - "$sh/ShipItState.plist" 2>/dev/null | sed 's|^file://||; s|/$||')
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
echo "B. 앱 캐시 (앱이 꺼져 있을 때만 — 로그인은 안 건드린다)"
CACHE_DIRS="Cache|Code Cache|GPUCache|Service Worker|DawnWebGPUCache|DawnGraphiteCache|Shared Dictionary|CachedData"
for entry in \
  "Notion|$HOME/Library/Application Support/Notion" \
  "Obsidian|$HOME/Library/Application Support/obsidian" \
  "Figma|$HOME/Library/Application Support/Figma" \
  "Visual Studio Code|$HOME/Library/Application Support/Code" \
  ; do
  proc="${entry%%|*}"; root="${entry#*|}"
  [ -d "$root" ] || continue
  if pgrep -qf "/Applications/$proc.app" 2>/dev/null || pgrep -qf "$root/" 2>/dev/null; then
    printf "  건너뜀 %8s  %-52s (%s 가 켜져 있다)\n" "$(human "$(bytes "$root")")" "${root/#$HOME/~}" "$proc"
    continue
  fi
  while IFS= read -r d; do
    [ -n "$d" ] && sweep "$d" "$proc 캐시"
  done < <(find "$root" -maxdepth 4 -type d 2>/dev/null | awk -F/ -v pat="$CACHE_DIRS" '
    BEGIN{n=split(pat,a,"|"); for(i=1;i<=n;i++) want[a[i]]=1}
    { if ($NF in want) print }')
done

echo
echo "C. ${KEEP_DAYS}일 넘게 안 쓴 것"
if [ -d "$HOME/.npm/_npx" ]; then
  while IFS= read -r d; do
    [ -n "$d" ] && sweep "$d" "npx 로 한 번 쓰고 남은 것"
  done < <(find "$HOME/.npm/_npx" -maxdepth 1 -mindepth 1 -type d -mtime +"$KEEP_DAYS" 2>/dev/null)
fi
if [ -d "$HOME/Library/Caches/ms-playwright" ]; then
  find "$HOME/Library/Caches/ms-playwright" -maxdepth 0 -mtime +"$KEEP_DAYS" 2>/dev/null | while IFS= read -r d; do
    [ -n "$d" ] && sweep "$d" "플레이라이트 브라우저 (다시 받는 데 ~500MB)"
  done
fi

echo
echo "D. 사람이 판단할 것 (이 도구는 안 지웁니다)"
ORPHAN=0
for d in "$HOME/Library/Application Support"/*; do
  [ -d "$d" ] || continue
  name="$(basename "$d")"
  case "$name" in com.apple.*|Caches|CrashReporter|AddressBook|CloudDocs|Google) continue ;; esac
  sz=$(bytes "$d"); [ "$sz" -gt 1073741824 ] || continue
  if [ ! -e "/Applications/$name.app" ] && [ ! -e "$HOME/Applications/$name.app" ]; then
    printf "  없는 앱? %7s  %-30s  (/Applications/%s.app 이 없다)\n" "$(human "$sz")" "$name" "$name"
    ORPHAN=$((ORPHAN+1))
  fi
done
for entry in "cursor|/Applications/Cursor.app" "vscode|/Applications/Visual Studio Code.app" \
             "android-studio|/Applications/Android Studio.app" "sublime|/Applications/Sublime Text.app"; do
  n="${entry%%|*}"; app="${entry#*|}"
  d="$HOME/.$n"; [ -d "$d" ] || continue
  [ -e "$app" ] && continue
  sz=$(bytes "$d"); [ "$sz" -gt 52428800 ] || continue
  printf "  없는 앱? %7s  %-30s  (%s 이 없다)\n" "$(human "$sz")" "~/.$n" "$app"
  ORPHAN=$((ORPHAN+1))
done
[ "$ORPHAN" -eq 0 ] && echo "  없는 앱이 두고 간 큰 데이터: 없음"
KEEP_NOTE_vm_bundles="남기기로 결정 (2026-10-13)"
KEEP_NOTE_avd="남기기로 결정 (2026-10-13)"
KEEP_NOTE_gradle="남기기로 결정 (2026-10-14)"
for big in "$HOME/Library/Application Support/Claude/vm_bundles" "$HOME/.android/avd" "$HOME/.gradle" "$HOME/Downloads"; do
  [ -e "$big" ] || continue
  sz=$(bytes "$big"); [ "$sz" -gt 1073741824 ] || continue
  note=""
  case "$big" in
    *vm_bundles) note="  ← $KEEP_NOTE_vm_bundles" ;;
    *.android/avd) note="  ← $KEEP_NOTE_avd" ;;
    *.gradle) note="  ← $KEEP_NOTE_gradle" ;;
  esac
  printf "  큰 것   %7s  %s%s\n" "$(human "$sz")" "${big/#$HOME/~}" "$note"
done

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
  echo "   ⭐ «지금» 조사하십시오 — 더 커지면 목록 조회가 안 됩니다 (2026-10-13 실측):"
  echo "        ls -fU /private/var/folders/*/*/T | head -40"
  rec 막음 "시스템 임시 폴더가 $(human "$VARF") 까지 불어 있었다" \
           "clean_disk.sh 가 /private/var/folders 를 쟀다" \
           "더 커지면 원인 조사조차 못 하게 될 뻔했다 (2026-10-13: 130만 개에서 조회 실패)" \
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
