#!/usr/bin/env python3
"""출시 절차 조항 원문 · 읽은 날 표 — 어디서 읽나 한 곳에서 정하고, 서버에서 받아 둔다."""
import os, re, subprocess, sys, time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PLUGIN = _HERE.parent


def _받은자리() -> Path:
    return Path(os.environ.get("NIGHTFLIGHT_HOME") or (Path.home() / ".nightflight")) / "gate_thresholds.tsv"


def 자리() -> Path:
    for p in (_PLUGIN.parent / "nightflight-server" / "catalog" / "관문-기준값.tsv",
              Path.home() / "nightflight-server" / "catalog" / "관문-기준값.tsv",
              _받은자리()):
        if p.is_file():
            return p
    return _받은자리()


def 받기() -> int:
    dst = _받은자리()
    if dst.is_file() and time.time() - dst.stat().st_mtime < 86400:
        return 0
    brain = _PLUGIN / "bin" / "brain.sh"
    try:
        out = subprocess.run(["bash", str(brain), "6", "관문/기준값"], capture_output=True, text=True, timeout=20,
                             env={**os.environ, "NF_BRAIN_TIMEOUT": os.environ.get("NF_BRAIN_TIMEOUT", "10")}).stdout
    except (OSError, subprocess.SubprocessError):
        return 1
    m = re.search(r"```tsv\n(.*?)```", out, re.S)
    if not m or not m.group(1).startswith("번호\t이름\t출처"):
        return 1
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp")
    tmp.write_text("# 서버 처방 관문/기준값 에서 받음 · " + time.strftime("%Y-%m-%d") + "\n" + m.group(1), encoding="utf-8")
    tmp.replace(dst)
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["받기"]:
        sys.exit(받기())
    print(자리())
