#!/usr/bin/env python3
"""화면 문구 검사 — 조종석에 나가는 말은 «그 기능이 정확히 무엇을 하는지»만 적는다.


  「이상한 말을 만들지 말라니까 어디에서도」
  「말을 내가 길이로 제한했어? 왜 의미 전달도 못하면서 무리하게 줄여?」
  「절대로 비유, 은유 쓰지말고 정확한 기능을 설명해」
  「오른쪽으로 하고, 안 보이는 작업은 빼고 걸어」

규칙 (기록을 적는 순간 · 턴 끝 · 시험 묶음 세 자리에서 같은 함수로 본다)
  ① 화면에 나가는 기록에는 «화면 문구» 칸이 있다. 원문은 기록용이고 화면에는 이 칸만 나간다.
  ② 화면 문구는 «무엇이 · 어떻게 된다/됐다» 명사구다 — 문장체(~습니다·~다) · 내부 이름(파일·함수·칸) ·
     지어낸 말·비유(lint_vague_words 의 목록) 를 받지 않는다. 길이 제한은 없다.
  ③ 됐다·남은것에는 «종류»가 있다 — 새 기능 · 문제 고침 · 안 보이는 작업. 진행 경과에는 앞의 둘만 나간다.

⚠️ 기계가 못 보는 것: 문구가 그 기능을 «정확하게» 설명하는지. 「치우친 안내 수정」은 이 검사를 통과한다.
   0 이 「정확하다」는 뜻이 아니다.

쓰는 법
  python3 tools/lint_screen_label.py
  python3 tools/lint_screen_label.py --한줄 [--종류 X] -- "문구"
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import _labels as _lb
종류들 = _lb.모든종류
시작날 = "2026-10-19"

_문장끝 = re.compile(r"(습니다|니다|어요|아요|해요|세요|다)[.。!]?\s*$")
_내부이름 = [
    (re.compile(r"[A-Za-z0-9_\-]+\.(py|sh|js|ts|json|tsv|md|html|swift|kt|yml|yaml)\b"), "파일 이름"),
    (re.compile(r"\b[a-z]+_[a-z0-9_]+\b"), "코드 이름(밑줄)"),
    (re.compile(r"\b(?!(?:iOS|iPhone|iPad|iCloud|iMessage|macOS|watchOS|tvOS|visionOS|iPadOS)\b)[a-z]+[A-Z][A-Za-z]+\b"), "코드 이름(낙타)"),
    (re.compile(r"`|\$\{|\$[A-Za-z]|(^|\s)--[A-Za-z가-힣]"), "명령·변수 꼴"),
    (re.compile(r"(^|[\s(])(~|\.{1,2})?/[A-Za-z0-9_가-힣.\-]+/"), "경로"),
]


def _금지말():
    try:
        import lint_vague_words as _v
        return dict(_v.BAN)
    except Exception:
        return {}


def 검사(문구: str, 종류: str = None, 기록: str = None, 숨김: bool = False) -> list:
    """문제 목록을 돌려준다. 빈 목록이면 통과.

    기록 = 됐다·남은것·표준·시도·영향 — 그 기록이 받는 «종류» 값만 받는다.
    숨김 = «안 보이는 작업»이라 화면 문구 없이 적는 경우.
    """
    t = (문구 or "").strip()
    bad = []
    허용 = _lb.종류표.get(기록, 종류들) if 기록 else 종류들
    if 종류 is not None and 종류 not in 허용:
        bad.append(f"종류는 {' · '.join(허용)} 중 하나입니다 — 받은 것: 「{종류}」")
    if 숨김 and 종류 == "안 보이는 작업" and not t:
        return bad
    if not t:
        return bad + ["화면 문구가 비어 있습니다"]
    if _문장끝.search(t):
        bad.append("문장으로 끝납니다(~습니다·~다) — «무엇이 · 어떻게» 명사구로 적습니다")
    for rx, 이름 in _내부이름:
        m = rx.search(t)
        if m:
            bad.append(f"{이름}이 들어 있습니다: 「{m.group(0).strip()}」 — 사용자가 겪는 일로 적습니다")
    for w, 대신 in _금지말().items():
        if w in t:
            bad.append(f"지어낸 말·비유 「{w}」 — 대신: {대신}")
    return bad


def _state():
    import os
    import _root as _r
    v = os.environ.get("NF_STATE")
    return Path(v) if v else _r.state_dir()


def _rows(p: Path):
    if not p.exists():
        return []
    return [l.rstrip("\n").split("\t") for l in p.read_text(encoding="utf-8").splitlines()
            if "\t" in l and not l.startswith("#")]


def 전부() -> int:
    st = _state()
    il, fl = _rows(st / "item-labels.tsv"), _rows(st / "feed-labels.tsv")
    표 = {c[0]: c for c in il}
    피드표 = {c[0]: c for c in fl}
    bad, warn = [], []
    for c in il:
        문구 = c[1] if len(c) > 1 else ""
        종류 = c[2] if len(c) > 2 and c[2] else None
        if 종류 == "안 보이는 작업" and not 문구:
            continue
        for b in 검사(문구, 종류):
            bad.append(f"  ⛔ 「{문구}」 — {b}")
    for c in fl:
        for 칸 in (c[1] if len(c) > 1 else "", c[2] if len(c) > 2 else ""):
            for b in 검사(칸):
                bad.append(f"  ⛔ 「{칸}」 — {b}")
    led = _rows(st / "ledger.tsv")
    끝 = [c[2] for c in led if len(c) > 2 and c[1] == "끝냄"]
    날 = {}
    for c in led:
        if len(c) > 2:
            날.setdefault(c[2], c[0][:10])
    빠짐 = []
    try:
        import feature_progress as _fp
        r = _fp.compute()
        for f in r["기능들"]:
            for h in f["하위"]:
                for z in h.get("줄들", []) + h.get("남은줄들", []):
                    if not z.get("이름표") or not z.get("종류"):
                        빠짐.append((z["무엇"], "화면 문구·종류"))
    except Exception as e:
        bad.append(f"  ⛔ 기능 진척을 못 만들어서 화면 문구를 못 쟀습니다 — {e}")
    for c in led[-80:]:
        if len(c) > 2 and c[1] in ("결정", "막음") and c[2] not in 피드표:
            빠짐.append((c[2], "항목·값"))
    for c in led:
        if len(c) > 2 and c[1] == "결정":
            f = 피드표.get(c[2])
            if not f:
                빠짐.append((c[2], "항목·값·다시 볼 조건"))
            elif len(f) < 4 or not f[3]:
                빠짐.append((c[2], "다시 볼 조건"))
    for c in led:
        if len(c) < 3 or c[1] not in ("표준", "시도", "영향", "남은것"):
            continue
        키 = c[2]
        if c[1] == "영향":
            키 = (c[4].partition(":")[2].strip() if len(c) > 4 else "")
        if c[1] == "남은것" and any(k in c[2] for k in 끝):
            continue
        t = 표.get(키)
        if not t or len(t) < 3 or not t[2]:
            빠짐.append((키 or c[2], "종류"))
        elif t[2] != "안 보이는 작업" and not t[1]:
            빠짐.append((키, "화면 문구"))
    for k in ("하는중", "다음"):
        xs = [c for c in led if len(c) > 2 and c[1] == k]
        if xs and xs[-1][2] not in 표:
            빠짐.append((xs[-1][2], "화면 문구"))
    본 = set()
    for what, 없음 in 빠짐:
        if what in 본:
            continue
        본.add(what)
        d = 날.get(what, "")
        (bad if d >= 시작날 else warn).append(f"  [{d}] {what[:50]} — {없음} 없음")
    if warn:
        print(f"  ⚠️ 규칙 전({시작날} 앞)에 적힌 줄 {len(warn)}개는 화면 문구가 없습니다 — 화면에는 원문이 «화면 문구 없음» 표지와 나갑니다")
    if bad:
        print("── 화면 문구 ───────────────────────────────")
        print("\n".join(bad[:30]))
        if len(bad) > 30:
            print(f"  … 그 밖 {len(bad) - 30}개")
        print("  ⭐ 붙이는 법: ledger.sh 화면문구 \"<원문 그대로>\" --화면 「…」 --종류 「새 기능|문제 고침|안 보이는 작업」")
        print("     결정·막음은 --항목 「…」 --값 「…」 · 하는중·다음은 --화면 「…」만")
        return 1
    print("  ✅ 화면 문구 — 화면에 나가는 줄마다 기능을 적은 문구가 있습니다")
    print("  ⚠️ 문구가 기능을 «정확하게» 설명하는지는 이 검사가 못 봅니다")
    return 0


def main(argv) -> int:
    if "--한줄" in argv:
        종류 = None
        if "--종류" in argv:
            종류 = argv[argv.index("--종류") + 1]
        문구 = argv[argv.index("--") + 1] if "--" in argv else ""
        기록 = argv[argv.index("--기록") + 1] if "--기록" in argv else None
        bad = 검사(문구, 종류, 기록, "--숨김" in argv)
        for b in bad:
            print(f"  ⛔ 화면 문구 「{문구}」 — {b}", file=sys.stderr)
        return 1 if bad else 0
    return 전부()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
