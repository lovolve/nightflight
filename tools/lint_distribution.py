#!/usr/bin/env python3
"""받는 사람에게 **무엇이 나가나** — 분류 안 된 파일이 있으면 운다.

🔴 왜 (2026-10-24 보안 레드팀):
   플러그인 배포가 **저장소 전체**였다. 대표님 기록(328줄 · 정한 것 33 · 표준 86)과
   이 컴퓨터의 메모리·디스크 값이 **설치하는 모든 사람에게 가게** 되어 있었다.
   비공개·출시 전이라 아직 안 나갔다. .

⭐ .
   지난 커밋 231개 중 68개가 대표님 기록을, 54개가 이 컴퓨터 상태를 담고 있어서
   **지금 지워도 안 지워진다.** 그래서 고치는 것이 아니라 새로 만든다.


1. **분류 안 된 파일** — `data/배포.tsv` 의 어느 꼴에도 안 맞는데 추적된다.
   ⛔ 분류가 비어 있는 것 자체가 고장이다 — 채울 때까지 운다.
2. **「꼭」인데 없다** — 이름을 바꾸거나 옮겼을 때 **조용히 빠지는 것**을 막는다
   (옆 대화 2026-10-24). 돈 낸 사람이 라이선스 키를 못 넣는 자리가 거기다.
3. **나가는데 아무도 안 부르는 검사** — ⚠️ 이건 **울리지 않고 적기만** 한다.
   배포가 틀린 것이 아니라 **배선이 빈 것**이라 고치는 자리가 다르다.
   ⛔ 그래도 적는다 — 안 적으면 「검사 N개가 있다」가 안심이 된다. 도는 것이 0개여도.


- **지우지 않는다.** 보여만 준다. 옮기는 것은 `tools/배포모으기.py` 가 한다.
- **`.gitignore` 를 대신하지 않는다.** 저기는 「커밋에 들어가나」, 여기는 「나가나」다.
  둘이 되지만 보는 것이 다르다 — 한쪽이 낡으면 다른 쪽이 운다.

사용:  python3 lint_distribution.py [저장소]
끝값:  1 = 손볼 것이 있다 · 0 = 없다
"""
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

뿌리 = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
표 = 뿌리 / "data" / "배포.tsv"


def 추적목록(d: Path):
    """⛔ `core.quotepath=off` 가 있어야 한글 이름이 글자 그대로 나온다 —
    없으면 git 이 `"\\355\\225\\234..."` 로 찍고 꼴 맞추기가 통째로 어긋난다(2026-10-24 실측)."""
    r = subprocess.run(["git", "-c", "core.quotepath=off", "ls-files", "-z"],
                       cwd=d, capture_output=True, text=True)
    return [f for f in r.stdout.split("\0") if f]


def 표읽기(p: Path):
    칸 = []
    if not p.exists():
        return 칸
    for 줄 in p.read_text(encoding="utf-8").splitlines():
        if not 줄.strip() or 줄.startswith("#"):
            continue
        c = 줄.split("\t")
        if len(c) < 4 or c[0] == "꼴":
            continue
        칸.append({"꼴": c[0].strip(), "나가나": c[1].strip(),
                   "꼭": c[2].strip() == "꼭", "왜": c[3].strip()})
    return 칸


def 맞나(경로: str, 꼴: str) -> bool:
    """`**` 는 여러 칸, `*` 는 한 칸. ⛔ fnmatch 의 `*` 는 `/` 도 먹어서 그대로 쓰면 안 된다."""
    if 꼴.endswith("/**"):
        return 경로 == 꼴[:-3] or 경로.startswith(꼴[:-2])
    쪽, 꼴쪽 = 경로.split("/"), 꼴.split("/")
    if len(쪽) != len(꼴쪽):
        return False
    return all(fnmatch.fnmatchcase(a, b) for a, b in zip(쪽, 꼴쪽))


def 가른다(파일들, 칸들):
    """⛔ **안나감 이 먼저다** — `bin/*.sh` 가 나가도 `bin/supabase_guard.sh` 는 안 나간다."""
    나감, 안나감, 모름 = [], [], []
    for f in 파일들:
        안 = next((k for k in 칸들 if k["나가나"] == "안나감" and 맞나(f, k["꼴"])), None)
        if 안:
            안나감.append((f, 안)); continue
        갈 = next((k for k in 칸들 if k["나가나"] == "나감" and 맞나(f, k["꼴"])), None)
        (나감.append((f, 갈)) if 갈 else 모름.append(f))
    return 나감, 안나감, 모름


def 안불리는검사(뿌리: Path, 나감파일들):
    """나가는 `lint_*.py` 중 **아무도 안 부르는 것**. ⚠️ 울리지는 않는다 — 적기만 한다."""
    글모음 = []
    for f in 나감파일들:
        p = 뿌리 / f
        if p.suffix in (".sh", ".json", ".md", ".py") and p.exists():
            try:
                글모음.append((f, p.read_text(encoding="utf-8", errors="ignore")))
            except OSError:
                pass
    검사들 = [f for f in 나감파일들 if Path(f).name.startswith("lint_")]
    남 = []
    for c in 검사들:
        이름, 몸통 = Path(c).name, Path(c).stem
        부름 = any(f != c and (이름 in g or re.search(r"\b" + re.escape(몸통) + r"\b", g))
                  for f, g in 글모음)
        if not 부름:
            남.append(c)
    return 남


def 내용도본다(뿌리: Path, 나감파일들):
    """나가는 **파일 안의 글**도 본다 — 목록만 보면 주석 속 기록이 그대로 나간다.

    🔴 왜 (2026-10-25 보안 레드팀 2·3·4회차 ④가 회차마다 다시 짚었다):
       이 검사는 「어느 파일이 나가나」만 봤고, **그 안에 무엇이 적혀 있나는 안 봤다.**
       실측(2026-10-25, 모은 104개 안에서):
         · 개인 노트 폴더 이름 2줄(`bin/setup_new_app.sh` · `tools/check_attribution.py`)
         · 남의 앱 이름 12줄 — **막는 검사가 자기 목록을 싣고 나갔다**(아직 안 낸 앱까지)
         · 이 컴퓨터 실측 2줄(기기 용량을 적은 자리)
       ⛔ 전역 규칙을 어기는 자리다 — 「만드는 사람의 기록·상태는 절대 안 나간다」.
       ⭐ 셋 다 0 으로 만들고, **다시 늘지 않게** 여기서 본다.

    ⛔ 「창업자」·「대표님」 **낱말만으로는 안 잡는다.** 그 말은 **제품이 사용자를 부르는 말**이고
      대표님 말이라 바꾸지 않는다(2026-10-25 열어서 확인: 제품 설명 · 기록 갈래 이름 ·
      모델에게 주는 지시 · 화면 글이 그 낱말을 쓴다). 낱말로 막으면 **제품이 못 돈다.**
      ⭐ 그래서 **이 컴퓨터·이 사람·다른 앱을 가리키는 꼴**만 본다.
    """
    샐것 = [("개인 폴더 이름", re.compile(r"(?:^|[\s\"'/=])(?:Ob_[A-Za-z0-9]+|/Users/[a-z0-9]+)")),
            ("이 컴퓨터 실측", re.compile(r"\d+ ?GB 맥북")),
            ("개인 메일", re.compile(r"[A-Za-z0-9._%+-]+@(?:gmail|naver|daum|kakao)\.[a-z.]+"))]
    앱길 = 뿌리 / "data" / "다른앱.tsv"
    앱들 = ()
    if 앱길.is_file():
        앱들 = []
        for l in 앱길.read_text(encoding="utf-8").split("\n"):
            l = l.strip()
            if not l or l.startswith("#"):
                continue
            if "\t" in l:
                continue
            앱들.append(l)
        앱들 = tuple(앱들)
    걸린것 = []
    for 칸 in 나감파일들:
        상대 = 칸[0] if isinstance(칸, (tuple, list)) else 칸
        f = 뿌리 / 상대
        if not f.is_file():
            continue
        try:
            줄들 = f.read_text(encoding="utf-8").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        for n, l in enumerate(줄들, 1):
            for 이름, 꼴 in 샐것:
                if 꼴.search(l):
                    걸린것.append((상대, n, 이름, l.strip()[:72]))
            for a in 앱들:
                if a in l:
                    걸린것.append((상대, n, "다른 앱 이름(%s)" % a, l.strip()[:72]))
                    break
    return 걸린것


def 배포가리키는곳(뿌리: Path, 안나감파일들):
    """마켓플레이스 글이 가리키는 자리에 **「안 나감」 파일이 들어 있나.**

    🔴 2026-10-25 실측 — 제가 그동안 열어 보지 않고 레드팀 말만 옮기던 자리다:
      ① 마켓플레이스를 더하면 **저장소가 통째로 복제된다**(`.git` 까지).
         공식 것을 받아 재 봤다: 1.7MB 중 `.git` 이 468KB 였다.
      ② 공식 플러그인 44개의 `source` 는 **`./plugins/<이름>` 꼴 열여덟 개**이고
         `"."` 은 **하나도 없다.** `"."` 은 「저장소 전체가 플러그인」이라는 뜻이다.
    ⛔ 그래서 **`source` 를 고치는 것만으로는 안 막힌다** — 복제가 먼저 온다.
      ⭐ 막는 것은 .
    ⚠️ 그래서 여기서는 **울리지 않고 잰 것만 적는다.** 지금 저장소에서는 고칠 수 없고
      (안 나갈 29개가 추적되는 중이다), 고칠 수 없는 빨간 줄은 사람이 끈다.
      ⭐ **무는 자리는 `tools/배포모으기.py`** 다 — 거기는 «나가는 몸»을 짓는 자리라
        그때 `source` 가 그 폴더 안을 가리키는지 **실패로** 본다.
    """
    글 = 뿌리 / ".claude-plugin" / "marketplace.json"
    if not 글.exists():
        return []
    try:
        판 = json.loads(글.read_text(encoding="utf-8"))
    except Exception as e:
        return [("marketplace.json 을 읽지 못했습니다: %s" % e, [])]
    본다 = []
    for 칸 in 판.get("plugins", []):
        원 = 칸.get("source")
        if not isinstance(원, str):
            continue
        터 = 원.lstrip("./").rstrip("/")
        밑에 = [f for f, _ in 안나감파일들 if not 터 or f.startswith(터 + "/")]
        if 밑에:
            본다.append(("%s → source \"%s\"" % (칸.get("name", "?"), 원), 밑에))
    return 본다


def main() -> int:
    칸들 = 표읽기(표)
    if not 칸들 and not (뿌리 / ".nightflight-dev").is_file():
        return 0
    if not 칸들:
        print("  ⚠️ 배포 목록을 **재지 못했습니다** — data/배포.tsv 가 없거나 비었습니다.")
        print("     (「나갈 것이 없다」는 뜻이 아닙니다.)")
        return 1
    파일들 = 추적목록(뿌리)
    if not 파일들:
        print("  ⚠️ 추적되는 파일을 **재지 못했습니다** — 이 폴더는 저희 저장소가 아닙니다.")
        print("     (「나갈 것이 없다」는 뜻이 아닙니다. 이 검사는 만드는 쪽에서만 쓸모가 있습니다.)")
        return 0

    나감, 안나감, 모름 = 가른다(파일들, 칸들)
    빠짐 = [k for k in 칸들 if k["꼭"] and not any(맞나(f, k["꼴"]) for f in 파일들)]

    print("=== 받는 사람에게 나가는 것 — 나감 %d개 · 안 나감 %d개 ===" % (len(나감), len(안나감)))
    아픔 = 0
    샌것 = 내용도본다(뿌리, 나감)
    if 샌것:
        아픔 = 1
        print("\n  🔴 **나가는 파일 «안»에 만드는 사람의 것이 %d줄** — 목록만 맞아도 글이 나갑니다." % len(샌것))
        for 상대, n, 이름, 글 in 샌것[:12]:
            print("     · %s:%d  [%s]  %s" % (상대, n, 이름, 글))
        if len(샌것) > 12:
            print("     … 외 %d줄" % (len(샌것) - 12))
    if 모름:
        아픔 = 1
        print("\n  🔴 **분류 안 된 파일 %d개** — 나갈지 말지 안 정했습니다." % len(모름))
        print("     ⛔ 분류가 비어 있는 것 자체가 고장입니다. 배포 목록에 한 줄씩 적으십시오.")
        for f in 모름[:12]:
            print("       · " + f)
        if len(모름) > 12:
            print("       … 외 %d개" % (len(모름) - 12))
    if 빠짐:
        아픔 = 1
        print("\n  🔴 **「꼭」인데 그 파일이 없습니다 %d개** — 이름을 바꾸거나 옮기면 조용히 빠집니다." % len(빠짐))
        for k in 빠짐:
            print("       · %s — %s" % (k["꼴"], k["왜"]))
    if not 아픔:
        print("\n  ✅ 모든 파일이 나갈지 말지 정해져 있고, 「꼭」 나가야 할 것이 다 있습니다.")

    안불림 = 안불리는검사(뿌리, [f for f, _ in 나감])
    if 안불림:
        print("\n  ⚠️ 나가는데 **아무도 안 부르는 검사 %d개** — 이건 배포가 아니라 «배선»입니다." % len(안불림))
        print("     ⛔ 안 적으면 「검사가 N개 있다」가 안심이 됩니다. 도는 것이 0개여도.")
        for c in 안불림:
            print("       · " + c)
    for 어디, 밑에 in 배포가리키는곳(뿌리, 안나감):
        print("\n  ⚠️ **배포가 가리키는 자리에 「안 나감」 %d개가 들어 있습니다** — %s"
              % (len(밑에), 어디))
        print("     🔴 잰 것(2026-10-25): 마켓플레이스를 더하면 **저장소가 통째로 복제됩니다**")
        print("        (공식 것 실측 — 1.7MB 중 `.git` 이 468KB). `source` 만 고쳐도 안 막힙니다.")
        print("     ⭐ 막는 것은 정해진 것입니다 — 제품이 완성되면 **새로 만들어서** 올립니다.")
        print("     ⛔ 여기서는 울리지 않습니다 — 지금 만드는 곳에서는 고칠 수 없는 일이고,")
        print("        고칠 수 없는 빨간 줄은 사람이 끕니다. **무는 자리는 배포모으기 쪽**입니다.")
        for f in 밑에[:4]:
            print("       · " + f)
        if len(밑에) > 4:
            print("       … 외 %d개" % (len(밑에) - 4))
    print("\n  ⚠️ 이 검사는 **추적되는 파일만** 봅니다 — 추적 안 되는 파일은 안 봅니다(.gitignore 의 몫).")
    print("  ⚠️ 그리고 **지난 판은 못 봅니다.** 지금 지워도 예전에 올린 것에는 남습니다 —")
    print("     그래서 **새 저장소를 만드는 것**으로 정해져 있습니다.")
    return 아픔


if __name__ == "__main__":
    sys.exit(main())
