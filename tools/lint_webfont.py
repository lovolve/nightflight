#!/usr/bin/env python3
"""받는 분께 **나가는 파일**이 글꼴을 바깥에서 받나 — 0 이어야 한다.

🔴 왜 (2026-10-26):
   조종석(`board/cockpit.html`)과 대시보드(`tools/gen_projects_board.py`)가 글꼴을
   `fonts.googleapis.com` 에서 받고 있었다. 둘 다 `data/배포.tsv` 에서 **나감**이다.
   그러면 받는 분이 그 화면을 **열 때마다 그분의 IP 주소와 브라우저 정보가 구글로 간다.**
   처리방침에는 그 말이 없다. 랜딩은 2026-10-25 에 같은 이유로 이미 뺐다.
   ⛔ 우리 서버가 부르는 곳(Paddle·Vercel)은 코드에 보인다. 이것은 **받는 분의 브라우저가
     직접** 부른다 — 우리 서버를 거치지 않아서 **눈에 안 띈다.** 그래서 검사가 본다.

⭐ 왜 문서가 아니라 검사인가: 랜딩에서 뺀 날 조종석·대시보드는 **그대로 남아 있었다.**
   한 자리를 고치고 같은 병의 옆자리를 안 본 것이라, 사람 기억에 맡길 자리가 아니다.


**나가는 파일에 글꼴을 부르는 바깥 주소가 있나** (`fonts.googleapis.com`·`fonts.gstatic.com`)
   ⭐ 「어느 파일을 보나」를 **열거하지 않는다** — `data/배포.tsv` 의 「안나감」을 걷고
     나머지를 **다 본다**. 열거로 적으면 **새로 생기는 화면을 못 따라간다**
     (이 저장소가 `.gitignore` 로 그 값을 두 번 치렀다).


처음 고친 길은 글꼴을 **파일 안에 박는 것**이었다. 조종석이 279KB → **971,558바이트**가 되어
1MB 선까지 **77,018바이트**(7.3%)만 남았고, 이 파일은 다른 대화도 자주 만지므로
「넘지 않나」를 여기서 봤다.
⭐ 그런데 **재 보니 박을 값어치가 없었다**: 박은 판과 뺀 판을 바깥을 못 부르게 막고
  각각 찍어 점 단위로 견주니 **세게 다른 점이 0.9%**(385,000점 중 3,402)였다 —
  숫자·칸·막대가 전부 같은 자리였다. 692KB 를 더 보내서 바뀐 것이 그만큼이다.
⭐  → **받는 분 컴퓨터에 이미 있는 글꼴을 쓴다**(조종석 282KB).
⛔ 그래서 한도 검사는 **틀린 말이 됐다** — 글꼴이 안 들어 있으니 잴 까닭이 없다.
  파일 크기를 다시 봐야 할 일이 생기면 **그때 그 까닭으로** 새로 둔다.

⛔ **막지 않는다. 보이게 한다.** 다만 **해당되면 1 로 끝낸다** — 턴 끝에 말해야 한다.

사용:  python3 lint_webfont.py [저장소]
끝값:  1 = 손볼 것이 있다 · 0 = 없다
"""
from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
from pathlib import Path

뿌리 = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
표 = 뿌리 / "data" / "배포.tsv"

자기 = "tools/lint_webfont.py"
글꼴주소 = re.compile(r"fonts\.googleapis\.com|fonts\.gstatic\.com")


def 파일들(d: Path) -> list:
    """추적되는 것 **과** 아직 추적 안 되는 새 파일을 함께 본다.

    ⛔ 추적되는 것만 보면 **방금 지은 새 화면**을 못 본다 — 커밋 전에 말해야 한다.
    ⛔ `core.quotepath=off` 가 있어야 한글 이름이 글자 그대로 나온다 — 없으면 git 이
      `"\\355\\225\\234…"` 로 찍고 꼴 맞추기가 통째로 어긋난다(두뇌 저장소 2026-10-24 실측).
    """
    r = subprocess.run(["git", "-c", "core.quotepath=off", "ls-files", "-z",
                        "-c", "-o", "--exclude-standard"],
                       cwd=str(d), capture_output=True, text=True)
    return sorted({f for f in r.stdout.split("\0") if f})


def 안나감꼴(p: Path) -> list:
    """`data/배포.tsv` 의 「안나감」 꼴. ⛔ 「나가는 것」을 열거하지 않는다."""
    꼴들 = []
    if not p.exists():
        return 꼴들
    for 줄 in p.read_text(encoding="utf-8").splitlines():
        if not 줄.strip() or 줄.startswith("#"):
            continue
        c = 줄.split("\t")
        if len(c) < 4 or c[0] == "꼴" or c[1].strip() != "안나감":
            continue
        꼴들.append(c[0].strip())
    return 꼴들


def 맞나(경로: str, 꼴: str) -> bool:
    """`**` 는 여러 칸, `*` 는 한 칸. ⛔ fnmatch 의 `*` 는 `/` 도 먹어서 그대로 쓰면 안 된다.
    ⭐ `tools/lint_distribution.py` 와 **같은 셈**이다 — 한쪽만 고치면 두 검사가 갈린다."""
    if 꼴.endswith("/**"):
        return 경로 == 꼴[:-3] or 경로.startswith(꼴[:-2])
    쪽, 꼴쪽 = 경로.split("/"), 꼴.split("/")
    if len(쪽) != len(꼴쪽):
        return False
    return all(fnmatch.fnmatchcase(a, b) for a, b in zip(쪽, 꼴쪽))


def main() -> int:
    안꼴 = 안나감꼴(표)
    걸린것, 본것 = [], 0
    for 이름 in 파일들(뿌리):
        if 이름 == 자기 or any(맞나(이름, k) for k in 안꼴):
            continue
        f = 뿌리 / 이름
        if not f.is_file() or f.is_symlink():
            continue
        try:
            글 = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        본것 += 1
        for n, 줄 in enumerate(글.split("\n"), 1):
            if 글꼴주소.search(줄):
                걸린것.append((이름, n, 줄.strip()[:90]))

    if 걸린것:
        print("── 글꼴을 바깥에서 받는 자리 ──────────────────")
        for 이름, n, 줄 in 걸린것:
            print("  🔴 %s:%d" % (이름, n))
            print("     「%s」" % 줄)
        print("     ⛔ 받는 분이 이 화면을 **열 때마다** 그분의 IP 주소와 브라우저 정보가")
        print("        구글로 갑니다. 처리방침에 그 말이 없습니다.")
        print("     ⭐ 고치는 법: **글꼴을 부르지 말고 받는 분 컴퓨터에 이미 있는 글꼴을")
        print("        쓰십시오.** 그 줄을 지우고 `font-family` 의 예비 글꼴로 받으면 됩니다 —")
        print("        맥 `system-ui`·`Apple SD Gothic Neo` · 윈도우 `Malgun Gothic` ·")
        print("        리눅스 `Noto Sans CJK KR` · 고정폭 `Consolas`·`DejaVu Sans Mono`.")
        print("        ⛔ 파일 안에 **박지 않습니다** — 재 보니 보이는 차이가 0.9% 였고")
        print("           조종석이 692KB 무거워졌습니다(창업자 2026-10-26, 위 머리글).")
    if 걸린것:
        return 1

    print("  ✅ 나가는 파일 %d개에 글꼴을 부르는 바깥 주소가 **0곳**이다" % 본것)
    print("     ⚠️ 이 검사는 **글꼴 주소만** 본다 — 다른 바깥 호출은 `lint_outbound.py` 의 몫이다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
