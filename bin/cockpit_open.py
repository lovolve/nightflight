#!/usr/bin/env python3
"""대화가 시작될 때 조종석 서버를 켜고, AI에게 «오른쪽 브라우저 칸에 조종석을 열라»고 알린다."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

여기 = Path(__file__).resolve().parent
sys.path.insert(0, str(여기))
sys.path.insert(0, str(여기.parent / "tools"))

줄표 = "cockpit_server.sh"


def _영어() -> bool:
    try:
        return subprocess.run(["bash", "-c", '. "$1" >/dev/null 2>&1; nf_lang', "_", str(여기 / "project-root.sh")],
                              capture_output=True, text=True, timeout=5).stdout.strip() == "en"
    except (OSError, subprocess.SubprocessError):
        return False


def 서버주소(뿌리, 제한: float = 15) -> str:
    import cockpit_file
    if not (cockpit_file.기록집(Path(뿌리)) / "board").is_dir():
        return ""
    try:
        r = subprocess.run([sys.executable, "-I", str(여기 / "cockpit_server.py"), str(뿌리), "--뒤에서"],
                           capture_output=True, text=True, timeout=제한)
    except (OSError, subprocess.SubprocessError):
        return ""
    주소 = (r.stdout or "").strip().splitlines()[:1]
    if r.returncode != 0 or not 주소 or not 주소[0].startswith("http://127.0.0.1:"):
        return ""
    return 주소[0]


def _알릴곳(집: Path, 대화: str) -> Path:
    return 집 / "cockpit_pending" / "".join(c for c in 대화 if c.isalnum() or c in "-_")[:80]


def 실행줄_넣기(뿌리: Path, 주소: str, 집: Path, 영어: bool) -> bool:
    try:
        자리 = int(주소.rstrip("/").rsplit(":", 1)[1])
    except (ValueError, IndexError):
        return False
    실행 = 집 / 줄표
    몸 = ("#!/bin/bash\n# 야간비행 조종석 서버 — 대화 시작이 매번 다시 쓴다(플러그인 판이 바뀌면 경로가 바뀐다)\n"
          'S="%s"\nR="${1:-.}"\n'
          '# 앱이 정한 자리가 바뀌면(PORT) 그 자리에서 띄운다 — 그래야 앱이 연 주소에 조종석이 있다\n'
          'if [ -n "${PORT:-}" ]; then exec python3 -I "$S" "$R" --자리 "$PORT"; fi\n'
          'python3 -I "$S" "$R" || exit 1\n'
          '# 이미 떠 있던 서버를 쓴 경우 — 그 서버가 살아 있는 동안 브라우저 칸이 끝났다고 보지 않게 머문다\n'
          'while python3 -I "$S" "$R" --살아있나; do sleep 15; done\n') % (여기 / "cockpit_server.py")
    try:
        집.mkdir(parents=True, exist_ok=True)
        if not 실행.is_file() or 실행.read_text(encoding="utf-8") != 몸:
            임시 = 실행.with_name(실행.name + ".tmp.%d" % os.getpid())
            임시.write_text(몸, encoding="utf-8")
            os.chmod(임시, 0o755)
            os.replace(임시, 실행)
    except OSError:
        return False
    기본집 = Path(os.environ.get("HOME") or Path.home()) / ".nightflight"
    부를곳 = '"$HOME/.nightflight/%s"' % 줄표 if 집 == 기본집 else '"%s"' % 실행
    줄 = {"name": "Nightflight cockpit" if 영어 else "야간비행 조종석",
         "runtimeExecutable": "bash",
         "runtimeArgs": ["-c", "exec %s ." % 부를곳],
         "port": 자리,
         "url": "http://127.0.0.1:%d" % 자리}
    파일 = 뿌리 / ".claude" / "launch.json"
    if 파일.exists():
        try:
            값 = json.loads(파일.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        if not isinstance(값, dict) or not isinstance(값.get("configurations", []), list):
            return False
    else:
        값 = {"version": "0.0.1", "configurations": []}
    목록 = 값.setdefault("configurations", [])
    우리 = [i for i, c in enumerate(목록) if isinstance(c, dict) and 줄표 in " ".join(map(str, c.get("runtimeArgs") or []))]
    if 우리:
        if 목록[우리[0]] == 줄 and len(우리) == 1:
            return False
        목록[우리[0]] = 줄
        for i in reversed(우리[1:]):
            del 목록[i]
    else:
        목록.append(줄)
    try:
        파일.parent.mkdir(parents=True, exist_ok=True)
        임시 = 파일.with_name(파일.name + ".tmp.%d" % os.getpid())
        임시.write_text(json.dumps(값, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(임시, 파일)
    except OSError:
        return False
    return True


def 알림글(주소: str, 영어: bool) -> str:
    if 영어:
        return ("Nightflight cockpit: in this reply, before anything else, call mcp__Claude_Browser__preview_start once with "
                f'url "{주소}". Then call mcp__ccd_view__show_pane with pane \"preview\" — without it the pane stays hidden and the user only sees an Open card (if it is listed only as a deferred tool, first load it with ToolSearch query "select:mcp__ccd_view__show_pane"; skip it only when the name is not listed at all). Opening or reopening a conversation resets the right-hand browser pane to an empty tab, '
                "so the cockpit has to be opened again. It updates itself every few seconds. Do not take a screenshot of it. "
                "If it fails, tell the user to press the play button next to «Nightflight cockpit» in the browser pane, "
                "or to type /cockpit.")
    return (f"야간비행 조종석: 이번 답에서 다른 일보다 먼저 mcp__Claude_Browser__preview_start 를 url «{주소}» 로 한 번 부르십시오. 그다음 mcp__ccd_view__show_pane 을 pane «preview» 로 부르십시오 — 안 부르면 칸이 숨은 채 «열기» 카드만 떠서 사용자가 눌러야 보입니다(도구 목록에 이름만 있고 아직 안 불러온 도구면 ToolSearch 를 query «select:mcp__ccd_view__show_pane» 로 먼저 부릅니다 · 이름이 아예 없을 때만 건너뜁니다). "
            "대화를 새로 열거나 다시 열면 오른쪽 브라우저 칸이 빈 탭으로 돌아가므로 다시 열어야 합니다. "
            "조종석은 몇 초마다 저절로 바뀝니다. 화면을 찍지는 마십시오. "
            "열리지 않으면 사용자에게 브라우저 칸의 «야간비행 조종석» 옆 ▶ 버튼을 누르거나 입력창에 /cockpit 을 입력하면 열린다고 알려 주십시오.")


def 대화시작(_입력: dict) -> int:
    if _입력.get("source") == "compact":
        return 0
    from registered import 등록된_대화인가
    if not 등록된_대화인가(_입력):
        return 0
    import _root
    뿌리 = _root.root()
    주소 = 서버주소(뿌리)
    if not 주소:
        return 0
    import nf_paths
    집 = nf_paths.집()
    영어 = _영어()
    실행줄_넣기(Path(뿌리), 주소, 집, 영어)
    대화 = str(_입력.get("session_id") or "")
    if not 대화:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                                 "additionalContext": 알림글(주소, 영어)}}, ensure_ascii=False))
        return 0
    try:
        곳 = _알릴곳(집, 대화)
        곳.parent.mkdir(parents=True, exist_ok=True)
        for 옛 in 곳.parent.iterdir():
            try:
                if time.time() - 옛.stat().st_mtime > 86400:
                    옛.unlink()
            except OSError:
                pass
        곳.write_text(str(뿌리), encoding="utf-8")
    except OSError:
        pass
    return 0


def 첫글(_입력: dict) -> int:
    대화 = str(_입력.get("session_id") or "")
    if not 대화:
        return 0
    import nf_paths
    곳 = _알릴곳(nf_paths.집(), 대화)
    try:
        뿌리 = Path(곳.read_text(encoding="utf-8").strip())
        곳.unlink()
    except OSError:
        return 0
    if not 뿌리.is_dir():
        return 0
    주소 = 서버주소(뿌리)
    if not 주소:
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                             "additionalContext": 알림글(주소, _영어())}}, ensure_ascii=False))
    return 0


def main() -> int:
    try:
        입력 = json.load(sys.stdin) or {}
    except Exception:
        입력 = {}
    if not isinstance(입력, dict):
        입력 = {}
    if os.environ.get("CLAUDE_CODE_ENTRYPOINT") != "claude-desktop":
        return 0
    if 입력.get("hook_event_name") == "UserPromptSubmit":
        return 첫글(입력)
    return 대화시작(입력)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
