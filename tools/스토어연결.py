#!/usr/bin/env python3
"""스토어 연결 상태 — 야간비행이 스토어 일을 대신 하려면 먼저 연결(권한)이 있어야 한다. 바깥에 묻지 않고 이 컴퓨터의 파일만 본다.

⭐ 대표님 2026-11-03 «출시 관련해서 야간비행이 대신 해주려면 권한을 먼저 가져야 하잖아 … 지금은 이미 연결된 후에 테스트를 한 거잖아» · «가부터 진행해».
  연결 확인이 흐름에 안 묶여, 사용자가 먼저 말하지 않으면 출시 때까지 아무도 몰랐다.
⭐ 언제 보이나: 앱을 스토어에 내는 프로젝트(플랫폼에 iPhone)가 개발 단계(4) 이상일 때 — 출시 전에 미리 연결해 두게.
⛔ 연결됐는지는 «설정 파일과 열쇠 파일이 있나»까지만 본다(빠르고 바깥에 안 묻는다). 실제로 붙는지는 `asc.py 준비` 가 본다.

쓰는 법: 스토어연결.py [--json]   (프로젝트 폴더에서 · 기록은 _root 가 찾는다)
"""
import json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _root

단계들 = "진단 기획 검증 설계 개발 확인 출시 수정 출시후".split()


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
    """구글 플레이 — ~/.googleplay 에 서비스 계정 열쇠(.json)가 있나(tools/gplay.py 와 같은 자리)."""
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
