#!/usr/bin/env python3
"""「창업자/대표님 결정」이라고 적으면서 **말씀을 인용하지 않은 곳** (보고 전용).

🔴 왜 (2026-08-26): `docs/PLAN.md`의 D6 방침이 「창업자 결정 (2026-08-14)」이라고
  적혀 있었다. 그런데 그 줄을 만든 커밋(`3382b61`)은 **내가 쓴 것**이고,
  대표님 말씀은 어디에도 인용돼 있지 않았다. 커밋의 「근거」 문단도 **내 논리**였다.

  즉 내가 정한 것에 **남의 이름을 붙였다.** 그 결과:
  ① 대표님은 하지도 않은 결정의 책임을 지게 됐고
  ② 나는 나중에 그 줄을 근거로 **「이건 정해진 것」이라며 다시 묻지 않았다**
  ③ 고 물으셨을 때 나는 그 줄을 들이밀며
     **책임을 미뤘다.** 틀린 판단보다 이게 더 나쁘다.


「창업자 결정 / 확정 / 지시 / 승인」이라고 쓰려면 **그 말씀을 그대로 인용**한다.
  ✅  창업자 결정 — *"결제 대기로 묶은 분류가 틀렸다"* (2026-08-24)
  ❌  창업자 결정 (2026-08-24)

인용이 없으면 그것은 **내 판단**이다. 그렇게 적는다:
  ✅  내 판단 — 근거는 …. 대표님 확인 필요.

⛔ 계약 검사에 넣지 않는다. 옛 문서 35곳이 한꺼번에 빨개지면 사람이 통째로 무시한다.
   종료 코드는 언제나 0이다. **새로 쓰는 것부터 지킨다.**


창업자가 사람 CTO 의 문제로 꼽은 넷 중 마지막 —
**「개발용어로 말해놓고 나중에 대표가 그렇게 결정했다고 거짓말한다」**.
그게 이 도구가 잡는 것이고, **넷 중 기계가 잡을 수 있는 유일한 항목**이다.

그런데 이 도구는 **어느 앱 두 곳에만 있었다.** 옆 앱으로 안 건너가는 것이
정확히 다른 앱이 RLS PUBLIC 을 실서버에서 다시 배운 그 병이다
(옵시디언 기획 노트 §18·§23). 그래서 `appkit-shared` 로 올린다.

  사용:  python3 check_attribution.py [경로 ...]
         python3 check_attribution.py ~/<노트 폴더>/wiki
         RECENT_DAYS=14 python3 check_attribution.py
"""
import re
import sys
from pathlib import Path

import os
import subprocess
import time


def _repo_root() -> Path:
    try:
        return Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL).strip())
    except Exception:
        return Path.cwd()


ROOT = Path(os.environ.get("LINT_ROOT") or _repo_root())
if len(sys.argv) > 1:
    TARGETS = [Path(a).expanduser() for a in sys.argv[1:]]
else:
    TARGETS = [p for p in (ROOT / "docs", ROOT / "CLAUDE.md", ROOT / "BUILD-LOG.md") if p.exists()]
RECENT_DAYS = int(os.environ.get("RECENT_DAYS", "14"))

CLAIM = re.compile(r"(창업자|대표님)\s*(결정|확정|지시|승인)")
QUOTE = re.compile(
    r"「[^」]{1,}」"
    r"|\*\"[^\"]{4,}\"\*"
    r"|\"[^\"\n]{2,}\""
    r"|^\s*>\s+\S"
    r"|직접 재확인|직접 확인")

FORWARD = re.compile(
    r"(창업자|대표님)\s*(결정|확정|지시|승인)\s*(이|가)?\s*(필요|대기|받아야|여쭤|물어)"
    r"|(창업자|대표님)\s*(결정|확정|지시|승인)\s*(사항|권한|몫|영역|자리)"
    r"|(창업자|대표님)\s*(결정|확정|지시|승인)\s*(→|->|\||후에|한 뒤|하면|받고)"
    r"|(은|는|이|가)\s*\*{0,2}(창업자|대표님)\s*(결정|확정)\*{0,2}\s*(이다|이고|이며|입니다)")


DEFER = re.compile(
    r"(창업자|대표님)\s*(결정|확정|몫|판단)[^\n]{0,80}"
    r"(정하지 않는다|여기서 정하지|자리만 만든다|여쭌다|여쭙|물어본다|받는다|기다린다)"
    r"|(정하지 않는다|여기서 정하지|자리만 만든다)[^\n]{0,80}(창업자|대표님)\s*(결정|확정|몫|판단)")


SHORT = []


def main() -> int:
    hits = []
    files = []
    for t in TARGETS:
        files += sorted(t.rglob("*.md")) if t.is_dir() else [t]
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").split("\n")
        except OSError:
            continue
        for i, line in enumerate(lines):
            if not CLAIM.search(line) or FORWARD.search(line):
                continue
            window = lines[max(0, i - 2):i + 3]
            joined = "\n".join(window)
            if any(QUOTE.search(w) for w in window) or QUOTE.search(joined):
                if not re.search(r"「[^」]{4,}」|\*\"[^\"]{4,}\"\*|^\s*>\s+\S",
                                 joined, re.M):
                    SHORT.append((path, i + 1))
                continue
            if DEFER.search("\n".join(window)):
                continue
            try:
                rel = path.relative_to(ROOT)
            except ValueError:
                rel = path
            recent = (time.time() - path.stat().st_mtime) < RECENT_DAYS * 86400
            hits.append((rel, i + 1, line.strip()[:88], recent))

    def _짧은것도_말한다():
        if not SHORT:
            return
        print(f"\n  ⚠️ {len(SHORT)}곳은 **짧은 괄호 하나로** 넘어갔다 — 그게 진짜 인용인지 보십시오")
        print("     (「가」 같은 한 글자 답은 인용이고, 「공개」 같은 강조는 인용이 아니다)")
        for f, i in SHORT[:8]:
            try:
                print(f"     · {f.relative_to(ROOT)}:{i}")
            except ValueError:
                print(f"     · {f}:{i}")

    print("=== 「창업자 결정」인데 말씀이 인용되지 않은 곳 (보고 전용) ===")
    if not hits:
        print("  ✅ 인용 없이 「창업자 결정」이라고 쓴 자리는 없다")
        _짧은것도_말한다()
        print(f"\n  ⚠️ 이 검사는 **「창업자|대표님 + 결정|확정|지시|승인」이라는 «말»**만 봅니다 —"
              " 0 이 「출처가 전부 분명하다」는 뜻은 아닙니다.")
        return 0
    new = [h for h in hits if h[3]]
    old = [h for h in hits if not h[3]]
    print(f"  {len(hits)}곳 — 이 중 무엇이 진짜 사용자 결정인지 **알 수 없다.**")
    print(f"  (최근 {RECENT_DAYS}일 안에 고친 문서 {len(new)}곳 · 그 전 {len(old)}곳)\n")

    if new:
        led = Path(__file__).resolve().parent.parent / "bin" / "ledger.sh"
        if os.access(led, os.X_OK):
            try:
                subprocess.run([str(led), "막음",
                                "제가 정한 것에 대표님 이름이 붙어 있던 것",
                                f"귀속 검사 — 최근 {RECENT_DAYS}일(우리가 정한 값, 실측) 안에 {len(new)}곳",
                                "나중에 「그때 그렇게 정하셨습니다」로 되돌아와, 하지 않은 결정을 되돌리게 됩니다"],
                               capture_output=True, timeout=5)
            except Exception:
                pass
        print(f"  🔴 최근 {RECENT_DAYS}일 — **지금 고칠 수 있는 것**")
        for path, line, text, _ in new:
            print(f"    {path}:{line}\n        {text}")
    if old:
        print(f"\n  ⬜ 그 전 {len(old)}곳 — 한꺼번에 고치려 들지 않는다(고치면 또 지어내게 된다).")
        for path, line, _, _ in old[:8]:
            print(f"    {path}:{line}")
        if len(old) > 8:
            print(f"    … 외 {len(old) - 8}곳")
    _짧은것도_말한다()
    print("\n  새로 쓸 때는 말씀을 그대로 인용한다. 인용이 없으면 「내 판단」이라고 적는다.")
    return 1 if new else 0


if __name__ == "__main__":
    sys.exit(main())
