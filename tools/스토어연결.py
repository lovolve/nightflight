#!/usr/bin/env python3
"""스토어 연결 상태 — 야간비행이 스토어 일을 대신 하려면 먼저 연결(권한)이 있어야 한다. 바깥에 묻지 않고 이 컴퓨터의 파일만 본다."""
import json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _root

단계들 = "진단 기획 검증 설계 개발 테스트 출시 수정 출시후".split()


def _애플(뿌리: Path) -> str:
    for p in (Path(os.environ["ASC_ENV"]).expanduser() if os.environ.get("ASC_ENV") else None,
              뿌리 / "tools" / "asc.env", Path.home() / ".appstoreconnect" / "asc.env"):
        if p and p.is_file():
            kv = {}
            for l in p.read_text(errors="replace").splitlines():
                if "=" in l and not l.strip().startswith("#"):
                    k, v = l.split("=", 1); kv[k.strip()] = v.strip()
            kid = kv.get("ASC_KEY_ID", "")
            if not kid or not kv.get("ASC_ISSUER_ID"):
                return "설정 덜 됨"
            if not (Path.home() / ".appstoreconnect" / "private_keys" / f"AuthKey_{kid}.p8").is_file():
                return "열쇠 파일 없음"
            return "연결됨"
    return "연결 안 됨"


def compute(lp=None):
    lp = Path(lp) if lp else _root.ledger()
    if not lp.is_file():
        return {"보일까": False}
    플랫폼, cur = [], None
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import 단계끝
        cur = 단계끝.지금(lp)
    except Exception:
        pass
    for l in lp.read_text(encoding="utf-8", errors="replace").splitlines():
        c = l.split("\t")
        if len(c) > 3 and c[1] == "앱설정" and c[2] == "플랫폼" and c[3].strip():
            플랫폼 = [x.strip() for x in c[3].split("·")]
    뿌리 = lp.parent.parent
    애플 = _애플(뿌리) if any("iPhone" in x for x in 플랫폼) else "해당 없음"
    구글 = _구글() if any("안드로이드" in x for x in 플랫폼) else "해당 없음"
    개발뒤 = cur is not None and cur >= 4
    return {"보일까": 개발뒤 and 애플 not in ("연결됨", "해당 없음"),
            "구글보일까": 개발뒤 and 구글 not in ("연결됨", "해당 없음"),
            "애플": 애플, "구글": 구글, "단계": 단계들[cur] if cur is not None else ""}


def _구글() -> str:
    d = Path(os.environ.get("GPLAY_KEY_DIR") or (Path.home() / ".googleplay"))
    for k in (d.glob("*.json") if d.is_dir() else []):
        try:
            j = json.loads(k.read_text())
        except (OSError, ValueError):
            continue
        if j.get("type") == "service_account" and j.get("private_key"):
            return "연결됨"
    return "연결 안 됨"


if __name__ == "__main__":
    print(json.dumps(compute(), ensure_ascii=False, indent=1))
