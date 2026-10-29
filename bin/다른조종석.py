#!/usr/bin/env python3
"""이 컴퓨터의 다른 조종석 가운데 «컴퓨터 상태»가 낡은 것을 찾는다.

🔴 2026-10-28  —
   안 되고 있었다. 조종석마다 그 제품에서 대화할 때만 새 값을 받아서, 대화를 안 한 제품의 조종석은
   15시간 전 값을 보였다. 컴퓨터는 하나인데 조종석마다 상태가 달랐다.
⭐ 어느 제품에서 대화하든 턴 끝에 «다른 조종석에도 컴퓨터 상태를 올려라»를 붙인다(`board_push.sh` 가 부른다).
⛔ 매 턴 다 올리면 AI 사용량이 조종석 수만큼 는다 — 그래서 «상태가 바뀌었거나(양호·주의·위험 · 주의 목록) 한 시간이 지난» 조종석만 고른다.

쓰는 법:  python3 -I 다른조종석.py <지금 제품의 기록 자리>      → 줄마다 «주소<탭>제품 폴더»
          python3 -I 다른조종석.py --올렸다 <기록 자리> <machine.json>   → 그 조종석에 올린 값을 적어 둔다
"""
import json
import os
import sys
import time
from pathlib import Path

한시간 = 3600


def 무늬(md: dict) -> str:
    """상태가 «바뀌었나»를 가르는 것 — 숫자 한 자리 바뀐 것으로는 다시 올리지 않는다."""
    return json.dumps([md.get("압박말"), md.get("걸리나짝"), md.get("시뮬부팅"), md.get("못쟀다")], ensure_ascii=False)


def 기록자리(뿌리: Path):
    for d in (".nightflight", ".claude"):
        p = 뿌리 / d
        if p.is_dir() and (p / "ledger.tsv").is_file():
            return p
    return None


def 올렸다(st: Path, machine: Path):
    try:
        md = json.loads(machine.read_text(encoding="utf-8"))
    except Exception:
        return 0
    (st / "board.machine").write_text(json.dumps({"때": time.time(), "무늬": 무늬(md)}, ensure_ascii=False), encoding="utf-8")
    return 0


def main(argv):
    if argv[:1] == ["--올렸다"] and len(argv) >= 3:
        return 올렸다(Path(argv[1]), Path(argv[2]))
    안내 = argv[:1] == ["--안내"]
    if 안내:
        argv = argv[1:]
    if not argv:
        return 0
    지금 = Path(argv[0]).resolve()
    여기 = argv[1] if len(argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    줄 = []
    try:
        md = json.loads((지금 / "board" / "machine.json").read_text(encoding="utf-8"))
    except Exception:
        return 0
    새무늬 = 무늬(md)
    집 = Path(os.environ.get("HOME", "~")).expanduser()
    for 뿌리 in sorted(p for p in 집.iterdir() if p.is_dir() and not p.name.startswith(".")):
        st = 기록자리(뿌리)
        if not st or st.resolve() == 지금:
            continue
        try:
            url = (st / "board.url").read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if not url.startswith("https://claude.ai/"):
            continue
        try:
            전 = json.loads((st / "board.machine").read_text(encoding="utf-8"))
        except Exception:
            전 = {}
        if 전.get("무늬") == 새무늬 and time.time() - float(전.get("때") or 0) < 한시간:
            continue
        줄.append((url, st))
    if not 안내:
        for url, st in 줄:
            print(f"{url}\t{st}")
        return 0
    if 줄:
        m = f"{지금}/board/machine.json"
        print("  ⑤ 이 컴퓨터의 다른 조종석도 «컴퓨터 상태»가 낡았습니다 — 같은 컴퓨터라 같은 값이어야 합니다. 주소마다: "
              f"ArtifactData get · collection \"state\" · doc_id \"machine\" 으로 version 을 받고 → set · file_path \"{m}\" · if_version "
              f"→ 끝나면 `python3 -I {여기}/다른조종석.py --올렸다 <그 기록 자리> {m}`")
        for url, st in 줄:
            print(f"     · {url}  (기록 자리 {st})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
