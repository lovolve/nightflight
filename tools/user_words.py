#!/usr/bin/env python3
"""기록의 **분류**를 사용자가 보는 말로 바꾼다.

🔴 왜 생겼나 (2026-10-17):
   한 화면에 같은 것이 **두 이름으로** 나왔다 — 「출시 절차」와 「관문」.
   `feature_progress.py` 는 `feature-map.tsv` 를 거쳐 사용자 말을 쓰는데,
   `standards.py` · `attempts.py` · `dependencies.py` 는 **기록의 분류를 날것 그대로** 썼다.
   로 정했는데 그 셋에는 안 닿았다.

   ⛔ 비개발자 레드팀 4/4 가 같은 병을 짚었다 — 「어느 수를 믿을지 몰라
      **화면 전체를 못 믿게 됐다**」. 이름이 갈리면 수도 갈려 보인다.

⭐ 그래서 **사용자 말로 바꾸는 자리를 한 곳**으로 둔다. 네 도구가 같은 표를 본다.
⛔ 표에 없는 분류는 **지어내지 않는다** — 들어온 그대로 돌려준다.
"""
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
    """분류 하나를 사용자 말로. 표에 없으면 **그대로** 돌려준다."""
    if not 분류:
        return 분류
    return _읽는다().get(분류.strip(), 분류)


def 바꾼다(per: dict) -> dict:
    """분류별 묶음의 **열쇠만** 사용자 말로 바꾼다. 같은 말로 모이면 합친다."""
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
