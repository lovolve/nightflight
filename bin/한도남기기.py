#!/usr/bin/env python3
"""상태줄 입력에서 5시간 · 7일 한도만 사람 자리에 남긴다. 조종석 자료가 이 파일을 읽는다."""
import json, os, sys, time


def 칸들(입력: dict) -> list:
    한도 = 입력.get("rate_limits") or {}
    out = []
    for 이름 in ("five_hour", "seven_day"):
        k = 한도.get(이름) or {}
        p, t = k.get("used_percentage"), k.get("resets_at")
        if isinstance(p, (int, float)):
            out.append({"종류": 이름, "사용": round(p), "초기화": t if isinstance(t, (int, float)) else None})
    return out


def 남기기(칸: list) -> None:
    집 = os.environ.get("NIGHTFLIGHT_HOME") or os.path.expanduser("~/.nightflight")
    자리 = os.path.join(집, "한도.json")
    try:
        with open(자리, encoding="utf-8") as f:
            if json.load(f).get("한도") == 칸:
                return
    except (OSError, ValueError, AttributeError):
        pass
    os.makedirs(집, exist_ok=True)
    임시 = "%s.%d.tmp" % (자리, os.getpid())
    with open(임시, "w", encoding="utf-8") as f:
        json.dump({"도구": "클로드 코드", "잰때": int(time.time()), "한도": 칸}, f, ensure_ascii=False)
    os.replace(임시, 자리)


if __name__ == "__main__":
    try:
        칸 = 칸들(json.load(sys.stdin))
        if 칸:
            남기기(칸)
    except (OSError, ValueError, AttributeError):
        pass
