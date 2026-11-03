#!/usr/bin/env python3
"""출시 절차 조항 원문 · 읽은 날 표 — 어디서 읽나 한 곳에서 정하고, 서버에서 받아 둔다.

⭐ 2026-11-03 서버 대화: 원문은 처방 갈래 `관문/기준값`(6단계)으로 내려준다 — 본문의 ```tsv 막대 안
   머리 `번호⇥이름⇥출처⇥읽은날` + 줄들(번호는 data/관문.tsv 와 같다).
🔴 왜: gates.py · read_dates.py 가 «플러그인 옆자리»의 서버 저장소 파일만 읽어, 설치된 판(받는 분 맥)에서는
   조종석 출시 준비의 원문이 통째로 비었다(어느 제품에서 2,912자 → 0자 실측).
차례: ① 플러그인 옆 서버 저장소(만드는 쪽) ② 집 폴더 서버 저장소(만드는 사람 맥) ③ 서버에서 받아 둔 것(받는 분 맥).

쓰는 법: 관문기준값.py 받기     — 하루에 한 번만 서버에서 받아 사람 자리(~/.nightflight)에 둔다(못 받으면 조용히 넘어간다)
         관문기준값.py 자리     — 지금 쓸 표 자리를 찍는다
"""
import os, re, subprocess, sys, time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PLUGIN = _HERE.parent


def _받은자리() -> Path:
    return Path(os.environ.get("NIGHTFLIGHT_HOME") or (Path.home() / ".nightflight")) / "관문-기준값.tsv"


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
    brain = _PLUGIN / "bin" / "두뇌.sh"
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
