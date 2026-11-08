#!/usr/bin/env python3
"""이 컴퓨터의 다른 조종석 가운데 «컴퓨터 상태»가 낡은 것을 찾는다."""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trusted_text import 조종석주소

한시간 = 3600


def 무늬(md: dict) -> str:
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
        url = 조종석주소(str(st))
        if not url:
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
              f"→ 끝나면 `python3 -I {여기}/other_cockpits.py --올렸다 <그 기록 자리> {m}`")
        for url, st in 줄:
            print(f"     · {url}  (기록 자리 {st})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
