#!/usr/bin/env python3
"""셸에서 파이썬을 **글로 넘길 때** `-I` 를 붙였나 — 열린 폴더의 가짜 모듈이 도는 자리다.

🔴 왜 (2026-10-25, 보안 레드팀 ③ · 두 대화가 **따로따로 심어서** 확인했다):
   `python3 - <<'PY'` 와 `python3 -c '…'` 는 **지금 폴더(`cwd`)를 모듈 길에 넣는다.**
   그래서 **사용자의 제품 폴더에 `json.py` 가 있으면 그것이 돌아간다.**
   이 저장소의 훅은 거의 다 **사용자 폴더 안에서** 돈다 — 대화 시작·턴 끝·붙여 넣은 말.

   실측(한 폴더에 `json.py` 를 심고):

       python3 -c 'import json'      → 심은 파일이 돌았다
       python3 -I -c 'import json'   → 진짜 표준 라이브러리를 집었다

   ⭐ 맥 기본 `/usr/bin/python3`(3.9.6)과 3.14 **둘 다** 그랬다(옆 대화 실측).
   ⛔ 받는 사람은 **남이 만든 꾸러미를 자기 제품 폴더에 풀어 놓는다.** 거기에 이 이름을
     한 개 두면 야간비행의 훅이 그 사람의 컴퓨터에서 그 글을 돌린다.
   ⭐ 고침은 낱말 하나(`-I`)라서 문서가 아니라 검사로 내린다
     (전역 규칙 0: 「검사로 만들 수 있나 → 린트로 만든다」).


- **파일 꼴**(`python3 tools/x.py`)은 그대로 둔다 — 그 자리는 **그 파일의 폴더**가 길에 들어가고,
  우리 도구가 옆의 `_root.py`·`machine.py` 를 집는 길이 바로 그것이다. `-I` 를 붙이면 **깨진다.**
- **주석 줄.**
- `-I` 와 같은 일을 손으로 적은 자리(`-E` 와 `-s` 를 둘 다 적었다)도 통과시킨다.
- ⛔ **시험(`tests/*.sh`)은 보지 않는다** — 배포되지 않고(`data/배포.tsv`: `tests/**` 안나감)
  자기가 만든 임시 폴더에서만 돈다. 사용자 폴더가 다른 곳이다.
  ⭐ 넣으면 113곳이 울고, **그러면 사람이 검사를 끈다**(이 저장소가 아는 모양이다).

⚠️ `-I` 는 `PYTHON*` 환경변수와 사용자 site-packages 도 끊는다. 이 저장소는 **바깥 꾸러미를 안 쓴다**
   (실측 2026-10-25: 56곳 전부 표준 라이브러리만 집고, 우리 모듈을 쓰는 한 곳 `bin/ledger.sh` 는
   `sys.path` 를 직접 넣는다). ⛔ 바깥 꾸러미가 필요한 날이 오면 **그 자리를 파일로 빼라.**
   이 검사를 끄지 마라.

사용:  python3 lint_python_isolated.py [저장소]
끝값:  1 = 안 붙은 곳이 있다 · 0 = 없다
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _root import root as _repo_root

집들 = ("bin", "hooks", "tools", "probe")
CALL = re.compile(r"\bpython3?(?:\.\d+)?((?:\s+-[A-Za-z]+)*)\s*(-c\b|-(?=\s|$|<|\|))")
SAFE = re.compile(r"-[A-Za-z]*I|(?=.*-E)(?=.*-s)")


def 볼파일(뿌리: Path):
    봤다 = set()
    for d in 집들:
        p = 뿌리 / d
        if p.is_dir():
            for f in sorted(p.rglob("*.sh")):
                if f not in 봤다:
                    봤다.add(f)
                    yield f
    b = 뿌리 / "bin"
    if b.is_dir():
        for f in sorted(b.iterdir()):
            if f.is_file() and f not in 봤다:
                try:
                    if f.read_text(encoding="utf-8").startswith("#!"):
                        봤다.add(f)
                        yield f
                except (UnicodeDecodeError, OSError):
                    pass
    hj = 뿌리 / "hooks" / "hooks.json"
    if hj.is_file():
        yield hj


def 본다(뿌리: Path):
    걸린것 = []
    for f in 볼파일(뿌리):
        try:
            줄들 = f.read_text(encoding="utf-8").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        for n, 줄 in enumerate(줄들, 1):
            if 줄.lstrip().startswith("#"):
                continue
            for m in CALL.finditer(줄):
                if SAFE.search(m.group(1) or ""):
                    continue
                걸린것.append((f.relative_to(뿌리), n, 줄.strip()[:95]))
                break
    return 걸린것


if __name__ == "__main__":
    뿌리 = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else _repo_root()
    걸린것 = 본다(뿌리)
    if not 걸린것:
        sys.exit(0)
    print("  ⛔ 파이썬을 글로 넘기면서 `-I` 를 안 붙인 곳이 %d 곳입니다." % len(걸린것))
    print("     그 자리는 **사용자 폴더의 `json.py` 가 돌아갑니다**(실측 2026-10-25).")
    print("     고침: `python3 -c` → `python3 -I -c` · `python3 -` → `python3 -I -`")
    print("     (파일을 부르는 꼴 `python3 x.py` 는 그대로 두십시오 — 거기는 `-I` 가 깨뜨립니다.)")
    for p, n, 글 in 걸린것:
        print("     · %s:%d  %s" % (p, n, 글))
    sys.exit(1)
