#!/usr/bin/env python3
"""재고 말할 사실 — 표(data/facts.tsv) 읽기 · 잰 값 적기 · 잰 값 읽기.

개발 중에 기억해야 할 사실을 기억이나 기록으로 단정하지 않고, 그때 재서 답하게 하는 장치다.
⛔ 잰 값은 «그날 그 도구가 본 것»이다. 오래되면 다시 잰다 — 적어 둔 값을 지금 상태로 말하지 않는다.

  쓰는 법:  facts.py 적기 <이름> <값> <근거>     잰 도구가 부른다(사람이 손으로 적지 않는다)
            facts.py 보기                         이 앱에 켜진 사실 · 잰 값과 날짜 · 오래됐는지
            facts.py 더하기 <이름> <단정말> <흔적> <재는법> [날수]   사고가 난 사실을 이 앱 표에 한 줄 더한다
            facts.py 공용후보                     여러 앱 표에 같은 이름이 있는 사실(공용 표로 옮길 후보)

"""
from __future__ import annotations
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
TABLE = Path(__file__).resolve().parent.parent / "data" / "facts.tsv"
LOG = "facts_measured.tsv"


APP_TABLE = "facts.tsv"


def _줄읽기(path: Path, 출처: str) -> list[dict]:
    줄 = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 줄
    for l in lines:
        if not l.strip() or l.startswith("#"):
            continue
        c = l.split("\t")
        if len(c) < 5:
            continue
        try:
            날수 = int(c[4])
        except ValueError:
            날수 = 7
        줄.append({"이름": c[0], "단정말": c[1], "흔적": c[2], "재는법": c[3], "날수": 날수,
                  "조건": c[5].strip() if len(c) > 5 else "", "출처": 출처})
    return 줄


def _앱표자리() -> Path | None:
    if os.environ.get("NF_FACTS_APP_TABLE"):
        return Path(os.environ["NF_FACTS_APP_TABLE"])
    try:
        import _root
        st = _root.state_dir(create=False)
        return st / APP_TABLE if st.is_dir() else None
    except Exception:
        return None


def _앱뿌리() -> Path:
    if os.environ.get("NF_FACTS_APP_ROOT"):
        return Path(os.environ["NF_FACTS_APP_ROOT"])
    try:
        import _root
        return _root.root()
    except Exception:
        return Path.cwd()


def _판정기():
    try:
        import gates
        state = os.environ.get("NF_FACTS_LEDGER")
        if not state:
            import _root
            state = str(_root.ledger())
        person = str(Path(os.environ.get("NIGHTFLIGHT_HOME") or (Path.home() / ".nightflight")) / "people.tsv")
        axes, when = {}, {}
        gates._load(axes, when, state, 1, 2, 3, 0)
        gates._load(axes, when, person, None, 1, 2, 0)
        return gates._judger(axes, set(axes))
    except Exception:
        return None


def 켜졌나(조건: str, 판정=None, 뿌리: Path | None = None) -> bool:
    조건 = (조건 or "").strip()
    if not 조건:
        return True
    if 조건.startswith("파일:"):
        return any((뿌리 or _앱뿌리()).glob(조건[3:].strip()))
    if 판정 is None:
        return True
    try:
        return 판정(조건) != "안걸림"
    except Exception:
        return True


def 표(켜진것만: bool = True) -> list[dict]:
    공용 = _줄읽기(Path(os.environ.get("NF_FACTS_TABLE") or TABLE), "공용")
    p = _앱표자리()
    앱 = _줄읽기(p, "이 앱") if p else []
    이름들 = {f["이름"] for f in 앱}
    합 = [f for f in 공용 if f["이름"] not in 이름들] + 앱
    if not 켜진것만:
        return 합
    판정 = _판정기() if any(f["조건"] and not f["조건"].startswith("파일:") for f in 합) else None
    뿌리 = _앱뿌리()
    return [f for f in 합 if 켜졌나(f["조건"], 판정, 뿌리)]


APP_HEAD = """# 이 앱에서만 재고 말할 사실 — 칸과 뜻은 야간비행 공용 표(data/facts.tsv)와 같다.
"""


def 더하기(이름, 단정말, 흔적, 재는법, 날수="7") -> str:
    import re
    for 칸, v in (("단정말", 단정말), ("흔적", 흔적)):
        try:
            re.compile(v)
        except re.error:
            return f"{칸} 칸이 찾는 말로 읽히지 않습니다 — 고쳐서 다시 부르십시오."
    if not str(날수).isdigit():
        return "날수는 숫자여야 합니다."
    if any("\t" in str(v) or "\n" in str(v) for v in (이름, 단정말, 흔적, 재는법)):
        return "칸 안에 탭 · 줄바꿈을 넣을 수 없습니다."
    p = _앱표자리()
    if p is None:
        return "이 폴더에 야간비행 기록 자리가 없어 더하지 못했습니다."
    if any(f["이름"] == 이름 for f in _줄읽기(p, "이 앱")):
        return f"«{이름}»은 이 앱 표에 이미 있습니다."
    p.parent.mkdir(parents=True, exist_ok=True)
    새 = not p.is_file()
    with p.open("a", encoding="utf-8") as f:
        if 새:
            f.write(APP_HEAD)
        f.write(f"{이름}\t{단정말}\t{흔적}\t{재는법}\t{날수}\n")
    return ""


def 공용후보() -> list[tuple[str, int]]:
    공용이름 = {f["이름"] for f in _줄읽기(Path(os.environ.get("NF_FACTS_TABLE") or TABLE), "공용")}
    ppl = Path(os.environ.get("NIGHTFLIGHT_HOME") or (Path.home() / ".nightflight")) / "people.tsv"
    try:
        곳들 = sorted({c[2] for c in (l.split("\t") for l in ppl.read_text(encoding="utf-8").splitlines())
                     if len(c) > 2 and c[1] == "프로젝트" and c[2]})
    except OSError:
        return []
    셈 = {}
    for 곳 in 곳들:
        for d in (".nightflight", ".claude"):
            p = Path(곳) / d / APP_TABLE
            if p.is_file():
                for 이름 in {f["이름"] for f in _줄읽기(p, "이 앱")}:
                    셈[이름] = 셈.get(이름, 0) + 1
                break
    return sorted([(n, k) for n, k in 셈.items() if k >= 2 and n not in 공용이름], key=lambda x: -x[1])


def _기록자리(create: bool) -> Path | None:
    if os.environ.get("NF_FACTS_LOG"):
        return Path(os.environ["NF_FACTS_LOG"])
    try:
        import _root
        st = _root.state_dir(create=False)
        if not st.is_dir():
            return None
        return _root.sys_path(st, LOG, read=not create)
    except Exception:
        return None


def 적기(이름: str, 값: str, 근거: str) -> bool:
    p = _기록자리(create=True)
    if p is None:
        return False
    clean = lambda s: str(s).replace("\t", " ").replace("\n", " ")[:300]
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d')}\t{clean(이름)}\t{clean(값)}\t{clean(근거)}\n")
        return True
    except OSError:
        return False


def 잰값들() -> dict:
    p = _기록자리(create=False)
    날수 = {f["이름"]: f["날수"] for f in 표(켜진것만=False)}
    out = {}
    try:
        lines = p.read_text(encoding="utf-8").splitlines() if p and p.is_file() else []
    except OSError:
        lines = []
    for l in lines:
        c = l.split("\t")
        if len(c) >= 4:
            out[c[1]] = c
    오늘 = time.time()
    res = {}
    for 이름, c in out.items():
        try:
            지남 = int((오늘 - time.mktime(time.strptime(c[0], "%Y-%m-%d"))) // 86400)
        except ValueError:
            지남 = 9999
        res[이름] = (c[0], c[2], c[3], 지남, 지남 > 날수.get(이름, 7))
    return res


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["적기"] and len(a) >= 4:
        return 0 if 적기(a[1], a[2], a[3]) else 1
    if a[:1] == ["보기"]:
        잰 = 잰값들()
        for f in 표():
            v = 잰.get(f["이름"])
            상태 = f"{v[1]} — {v[2]} ({v[0]} · {v[3]}일 전{' · 오래됨' if v[4] else ''})" if v else "잰 적 없음"
            print(f"[{f['출처']}] {f['이름']}: {상태}")
        return 0
    if a[:1] == ["더하기"] and len(a) >= 5:
        왜 = 더하기(a[1], a[2], a[3], a[4], a[5] if len(a) > 5 else "7")
        print(왜 or f"«{a[1]}»을 이 앱의 사실 표에 더했습니다.")
        return 1 if 왜 else 0
    if a[:1] == ["공용후보"]:
        for n, k in 공용후보():
            print(f"{n} — 앱 {k}곳")
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
