#!/usr/bin/env python3
"""화면에 찍는 글 안에 **백틱**이 있나 — 배시가 그것을 «명령»으로 돌리는 자리다.

🔴 왜 (2026-10-25, 제가 그 자리를 두 번 만들었다):
   배시의 큰따옴표 안에서 백틱은 **명령 치환**이다. 그래서 이름표를 적은 것인데 돌아간다.

       ok "`claude` 가 없어도 …"      → 배시가 **claude 를 실제로 돌렸다**(실측)
       ok "`--모아` 없이는 …"          → 「command not found」가 찍히고 글자는 **사라진다**

   ⛔ `bash -n` 이 통과한다. ⛔ 끝값도 0 이다. 이 저장소가 아는 모양 그대로 — 「조용히 틀렸다」
     (`lint_shell_hangul.py` 머리의 한글 변수와 같은 병이다).
   ⛔ 더 나쁜 것은 **시험 안에서 돌았다**는 것이다. 무엇이 느려지거나 바뀌어도 아무도 안 본다.
   ⭐ 고침은 「」 로 쓰는 것이다 — 이 저장소의 글 꼴이 이미 그것이다.


   **줄 머리가 `ok`·`fail`·`skip`·`echo`·`printf` 인 것만** 본다. 그 자리는 **언제나 배시**다.
   파이썬 헤러독 안의 글(`say("… `ledger.sh …` …")`)은 파이썬 글자라 백틱이 **무해하고**,
   이 저장소는 거기서 백틱을 **일부러 많이 쓴다**(모델에게 명령을 알려 주는 자리다 — 23곳).
   ⛔ 그 23곳까지 잡으면 매번 울고, 그러면 꺼진다.

사용:  python3 lint_shell_backtick.py [저장소]
끝값:  1 = 있다 · 0 = 없다
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _root import root as _repo_root

LOOK = ("bin/*.sh", "bin/ledger.d/*.sh", "tools/*.sh", "tests/*.sh", "probe/*.sh", "hooks/*.sh")
SAY = re.compile(r'^\s*(?:(?:else|then|elif|if|&&|\|\|)\s+)*(ok|fail|skip|echo|printf)\s+"')
QUOTED = re.compile(r'"((?:[^"\\]|\\.)*)"')


def 본다(뿌리: Path):
    걸린것 = []
    for 꼴 in LOOK:
        for f in sorted(뿌리.glob(꼴)):
            if not f.is_file():
                continue
            try:
                글 = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for n, 줄 in enumerate(글.split("\n"), 1):
                if not SAY.match(줄):
                    continue
                m = QUOTED.search(줄)
                if m and "`" in m.group(1):
                    걸린것.append((f.relative_to(뿌리), n, 줄.strip()[:88]))
    return 걸린것


if __name__ == "__main__":
    뿌리 = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else _repo_root()
    걸린것 = 본다(뿌리)
    if not 걸린것:
        sys.exit(0)
    print("  ⛔ 찍는 글 안에 백틱이 있는 곳이 %d 곳입니다 — 배시가 그것을 돌립니다." % len(걸린것))
    print("     고침: 백틱 대신 「」 로 쓰십시오(이 저장소의 글 꼴입니다).")
    for p, n, 글 in 걸린것:
        print("     · %s:%d  %s" % (p, n, 글))
    sys.exit(1)
