#!/usr/bin/env python3
"""«완료»로 적은 세부기능의 확인 방법에 맞는 «실행 흔적»이 대화 기록에 있나."""
from __future__ import annotations
import json
import os
import re
import shlex
import sys
from pathlib import Path

TAIL = 1024 * 1024

KIND = (
    ("시험", re.compile(r"시험|테스트|test", re.I)),
    ("화면", re.compile(r"화면|시뮬레이터|에뮬레이터|스크린샷|눈으로|브라우저|미리보기|직접 눌러|눌러 봄|눌러봄")),
    ("빌드", re.compile(r"빌드|build", re.I)),
)
EVID_CMD = {
    "시험": re.compile(r"\b(pytest|xcodebuild\b[^\n]*\btest|swift test|npm (run )?test|npx (vitest|jest|playwright)|vitest|jest|gradlew?\b[^\n]*test|deno test|go test|cargo test|flutter test)\b|tests?/run\.sh|_test\.(ts|py)|test_[\w]+\.py|lint_\w+\.py"),
    "화면": re.compile(r"\b(simctl|shot\.sh|screencapture|adb shell|playwright)\b"),
    "빌드": re.compile(r"\b(xcodebuild|gradlew?|npm run build|next build|vite build|swift build|flutter build|cargo build|tsc)\b"),
}
EVID_TOOL = {
    "시험": (),
    "화면": ("Simulator", "Claude_Browser", "claude-in-chrome", "computer-use", "preview_"),
    "빌드": ("Simulator__build",),
}
LEDGER_CALL = re.compile(r"ledger\.sh[\"']?\s+세부상태\s")


def 부름들(path: Path) -> list[tuple[str, str]]:
    with path.open("rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - TAIL))
        blob = f.read().decode("utf-8", errors="replace")
    out = []
    for line in blob.splitlines():
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") != "assistant":
            continue
        for p in (d.get("message") or {}).get("content") or []:
            if isinstance(p, dict) and p.get("type") == "tool_use":
                inp = p.get("input") or {}
                out.append((str(p.get("name") or ""), str(inp.get("command") or "")))
    return out


def 완료부름(cmd: str) -> list[tuple[str, str, str]]:
    out = []
    for seg in re.split(r"&&|;|\|\||\n", cmd):
        if not LEDGER_CALL.search(seg):
            continue
        try:
            w = shlex.split(seg)
        except ValueError:
            continue
        i = next((k for k, x in enumerate(w) if x == "세부상태"), None)
        if i is None or len(w) < i + 4:
            continue
        기능, 세부, 상태 = w[i + 1], w[i + 2], w[i + 3]
        if 상태 == "완료":
            out.append((기능, 세부, " ".join(w[i + 4:])))
    return out


def 짚을것(calls: list[tuple[str, str]]) -> list[str]:
    hits = []
    for n, (name, cmd) in enumerate(calls):
        for 기능, 세부, how in 완료부름(cmd):
            갈래 = [k for k, rx in KIND if rx.search(how)]
            if not 갈래:
                continue
            앞 = calls[:n]
            없는 = [k for k in 갈래
                    if not any(EVID_CMD[k].search(c) or any(t in nm for t in EVID_TOOL[k]) for nm, c in 앞)]
            if 없는 and len(없는) == len(갈래):
                hits.append("「%s › %s」 확인 방법 «%s» — %s 실행 흔적 없음" % (기능, 세부, how or "(빈칸)", "·".join(없는)))
    return hits


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("NF_TRANSCRIPT", "")
    if not arg or not Path(arg).is_file():
        print("⛔ 이번 턴 기록을 못 받았습니다 — **검사하지 않았습니다.** ⚠️ 이건 「깨끗하다」가 아닙니다.")
        return 0
    try:
        hits = 짚을것(부름들(Path(arg)))
    except Exception as e:
        print("⛔ 기록을 못 읽었습니다(%s) — **검사하지 않았습니다.**" % type(e).__name__)
        return 0
    if not hits:
        return 0
    print("🔴 «완료»로 적은 세부기능의 확인 방법에 맞는 실행이 이 대화에 없습니다:")
    for h in hits[:6]:
        print("   · " + h)
    print()
    print("   ① 적은 방법대로 지금 돌려 보십시오(시험 · 화면 · 빌드).")
    print('   ② 돌리지 않았으면 ledger.sh 세부상태 <기능> <세부> "확인 필요" "확인 안 함" 으로 고치십시오.')
    print("   ③ 다른 대화에서 확인했으면 확인 방법에 그 근거(날짜 · 결과)를 적으십시오.")
    print("   ⭐ 랜딩은 «AI가 완료라 해도 검증 안 한 항목은 «확인 안 함»으로 표시»한다고 약속합니다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
