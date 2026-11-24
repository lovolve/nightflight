#!/usr/bin/env python3
"""기록의 **분류**를 사용자가 보는 말로 바꾼다."""
import os
from pathlib import Path


def _state() -> Path:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import _root
    return _root.state_dir()


_표 = None


def _읽는다() -> dict:
    global _표
    if _표 is not None:
        return _표
    out = {}
    p = _state() / "feature-map.tsv"
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            c = line.split("\t")
            if len(c) >= 2 and c[0].strip():
                out[c[0].strip()] = (c[2].strip() if len(c) > 2 and c[2].strip() else c[1].strip())
    except Exception:
        out = {}
    _표 = out
    return out


def 사용자말(분류: str) -> str:
    if not 분류:
        return 분류
    return _읽는다().get(분류.strip(), 분류)


def 바꾼다(per: dict) -> dict:
    if not isinstance(per, dict):
        return per
    out = {}
    for k, v in per.items():
        나 = 사용자말(k)
        if 나 in out and isinstance(out[나], list) and isinstance(v, list):
            out[나] = out[나] + v
        else:
            out[나] = v
    return out


if __name__ == "__main__":
    t = _읽는다()
    print(f"── 분류 → 사용자 말 ({len(t)}개) ─────────────")
    for k, v in sorted(t.items()):
        print(f"  {k:<12} → {v}")
