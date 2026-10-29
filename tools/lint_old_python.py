#!/usr/bin/env python3
"""받는 사람의 **맥 기본 파이썬(3.9)**에서 도나 — 꼴 검사는 통과하고 돌 때 죽는 자리다.

🔴 왜 (2026-10-25, 2회차 레드팀 ③ 이 짚고 제가 `/usr/bin/python3` 3.9.6 으로 돌려서 확인):
   `def f(x) -> int | None:` 은 3.10 부터다. 3.9 는 그 주석을 **돌 때 셈으로 읽어** 죽는다:

       TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'

   ⛔ `python3 -m py_compile` 은 **통과한다** — 주석은 문법이 맞기 때문이다. 그래서 안 보인다.
   ⛔ 실측: 매 턴 도는 도구 **네 개**가 그렇게 죽고 있었다
     (`gen_projects_board.py` · `lint_handoff_claim.py` · `lint_number_source.py` · `조종석파일.py`).
     홈브루 파이썬이 없는 맥이 **기본 상태**다 — 받는 사람 대부분이 그렇다.
   ⭐ 고침은 파일 머리의 한 줄이다: `from __future__ import annotations`.
     그 줄이 있으면 주석을 글자로 두고 돌 때 셈하지 않는다(3.7 부터 된다).


   이 컴퓨터에 3.9 가 있어서 재진 것이다. **다른 컴퓨터에는 없을 수 있다** —
   그러면 시험이 「못 잼」으로 넘어가고 아무도 안 본다.
   ⭐ 그래서 이 검사는 **글을 읽어서** 판정한다(어느 파이썬으로 돌든 같은 답이 나온다).
   ⚠️ 주석이 아닌 자리에서 `int | None` 을 쓰면(예: `isinstance`) 이 줄로는 안 풀린다.
     그 자리는 묶음이 3.9 로 실제로 돌려 본다(절 91).

사용:  python3 lint_old_python.py [저장소]
끝값:  1 = 3.9 에서 죽을 자리가 있다 · 0 = 없다
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _root import root as _repo_root



def 주석들(나무: ast.AST):
    """주석이 적히는 자리 전부 — 인자 · 돌려주는 값 · 변수."""
    for n in ast.walk(나무):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = n.args
            for 칸 in list(a.posonlyargs) + list(a.args) + list(a.kwonlyargs) + [a.vararg, a.kwarg]:
                if 칸 is not None and 칸.annotation is not None:
                    yield 칸.annotation
            if n.returns is not None:
                yield n.returns
        elif isinstance(n, ast.AnnAssign) and n.annotation is not None:
            yield n.annotation


def 새꼴인가(식: ast.AST) -> str | None:
    for n in ast.walk(식):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr):
            return "`X | Y` 꼴"
    return None


def 본다(뿌리: Path):
    걸린것 = []
    for f in sorted(뿌리.glob("tools/*.py")) + sorted(뿌리.glob("bin/*.py")):
        if f.name.startswith("__"):
            continue
        try:
            글 = f.read_text(encoding="utf-8")
            나무 = ast.parse(글)
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        if "from __future__ import annotations" in 글:
            continue
        for 식 in 주석들(나무):
            무엇 = 새꼴인가(식)
            if 무엇:
                걸린것.append((f.relative_to(뿌리), 식.lineno, 무엇))
                break
    return 걸린것


if __name__ == "__main__":
    뿌리 = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else _repo_root()
    걸린것 = 본다(뿌리)
    if not 걸린것:
        sys.exit(0)
    print("  ⛔ 맥 기본 파이썬(3.9)에서 **돌 때 죽는** 파일이 %d개입니다." % len(걸린것))
    print("     고침: 그 파일 머리에 한 줄을 넣으십시오 — from __future__ import annotations")
    print("     (받는 사람 대부분이 홈브루 파이썬 없이 3.9 를 씁니다. py_compile 은 통과합니다.)")
    for p, n, 무엇 in 걸린것:
        print("     · %s:%d  %s" % (p, n, 무엇))
    sys.exit(1)
