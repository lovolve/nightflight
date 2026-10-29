#!/usr/bin/env python3
"""설계표 — 단계 → 기능 → 세부기능 «자리»를 먼저 만들고, 그 자리의 상태를 채운다.

🔴 2026-10-20 

⛔ 전에는 거꾸로였다 — 끝낸 일 기록(`됐다`)을 주제 낱말로 모아 기능에 «갖다 붙였다».
   그래서 조종석에 기록 문장이 줄줄이 찍혔고, 몇 개 중 몇 개인지의 «분모»가 없었다.
⭐ 분모는 설계표가 정한다. 기록은 «확인을 요청할 때» 대화창에서 쓴다.

칸 (`<상태 폴더>/plan.tsv`):
  단계 ⇥ 기능 ⇥ 세부기능 ⇥ 상태 ⇥ 이름표 ⇥ 출처 ⇥ 바뀐날
  상태 = 시작 전 | 진행 중 | 완료 | 확인 필요 | 방법 찾는 중   (창업자 2026-10-20 선택)
  이름표 = 확인 필요 · 방법 찾는 중일 때만, 문장이 아닌 짧은 이름표 ()
  출처 = 기본(data/세부기능.tsv 에서 깔림) | 기획(사용자 기획으로 더함)

쓰는 법:
  plan.py 기능추가 <단계 0~8> <기능> [세부기능 ...]   세부기능을 안 주면 기본 표에서 깐다
  plan.py 세부기능 <단계 0~8> <기능> <세부기능>      사용자 기획으로 하나 더한다
  plan.py 세부빼기 <기능> <세부기능>
  plan.py 세부상태 <기능> <세부기능> <상태> [이름표]
  plan.py 세부상태 <기능> <세부기능> 완료 "<무엇으로 확인했나>"   ⭐ 확인 방법이 없으면 「확인 필요 · 확인 안 함」으로 적힌다
  plan.py 설치전 <기능> <세부기능> "<근거 — 어느 파일 · 어느 시험>"   개발 중간에 깐 앱 — 이미 만든 것을 «완료»로(근거는 출처 칸에)
  plan.py 설치전확인 <기능> <세부기능> "<무엇으로 확인했나>"           사람이 확인하면 완료
  plan.py 화면 <화면> "<설명>"  ·  화면요소 <화면> "<보이는 것>" <기능> [세부기능]  ·  화면이동 <화면> <다음 화면> "<무엇을 하면>"
  plan.py 화면종류 <화면> 폰|모니터|메일
  plan.py 화면이름 <화면> "<풀어 쓴 이름>"        ⭐ «키 메일»처럼 줄인 이름 대신 «라이선스 키가 담긴 메일»
  plan.py 화면언제 <화면> "<사용자가 언제 이 화면을 보나>"
  plan.py 화면하는일 <화면> "<사용자가 여기서 하는 일>"
  plan.py 화면갈림 <화면> "<이 화면 뒤에 갈리는 물음>"   갈리는 물음 — 이동 조건은 «예» · «아니오 · …»로 다시 적는다(같은 두 화면을 다시 적으면 조건만 바뀐다)
  plan.py 화면상태 <화면> "<상태>" ["<다음 상태로 가는 때>"] [나쁨]   상태머신 — 적은 순서대로 잇는다. 시간 · 결제로 같은 것이 바뀌는 화면에만
  plan.py 화면일 "<하는 일>" "<언제 — 비워도 됨>" <화면> [<화면|화면>] …   사용자가 하는 일 하나와 그때 지나는 화면 차례
                                                               «|» 는 «또는»(한 자리에서 갈리는 화면). 같은 이름을 다시 적으면 덮어쓴다
  plan.py 화면일빼기 "<하는 일>"
  plan.py 화면빼기 "<화면>" "<왜 — 없앤 화면 등>"
  plan.py 기능빼기 "<기능>" "<왜 — 없앤 기능 · 합친 기능 등>"
  plan.py 화면문제 <화면> "<«지금 하실 일»에 뜨는 글의 앞부분>"   이 문제가 어느 화면 이야기인가 — 개발 단계 그림에 빨간 점
  plan.py 보기
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _root as _root_mod

상태들 = ["시작 전", "진행 중", "완료", "확인 필요", "방법 찾는 중"]
이름표필요 = {"확인 필요", "방법 찾는 중"}
def _미확인말():
    v = os.environ.get("UNVERIFIED_TOKENS")
    if v:
        return v.split()
    import re as _re
    t = (Path(__file__).resolve().parent.parent / "bin" / "ledger.sh").read_text(encoding="utf-8")
    m = _re.search(r'^UNVERIFIED_TOKENS="([^"]*)"', t, _re.M)
    return m.group(1).split() if m else ["안함", "안봄", "못봄", "못봤", "못했", "못함", "못확인", "미확인"]


미확인말 = _미확인말()
단계이름 = ["진단", "기획", "검증", "설계", "개발", "확인", "출시", "수정", "출시후"]
_DATA = Path(__file__).resolve().parent.parent / "data" / "세부기능.tsv"


def _file():
    v = os.environ.get("NF_STATE")
    return (Path(v) if v else _root_mod.state_dir()) / "plan.tsv"


def 읽기():
    p = _file()
    if not p.exists():
        return []
    out = []
    for l in p.read_text(encoding="utf-8").splitlines():
        if not l or l.startswith("#"):
            continue
        c = (l.split("\t") + [""] * 7)[:7]
        out.append({"단계": c[0], "기능": c[1], "세부기능": c[2], "상태": c[3] or "시작 전",
                    "이름표": c[4], "출처": c[5], "바뀐날": c[6]})
    return out


def 쓰기(rows):
    p = _file()
    p.parent.mkdir(parents=True, exist_ok=True)
    head = "# 설계표 — 단계 ⇥ 기능 ⇥ 세부기능 ⇥ 상태 ⇥ 이름표 ⇥ 출처 ⇥ 바뀐날 (tools/plan.py 가 쓴다)\n"
    body = "".join("\t".join([r["단계"], r["기능"], r["세부기능"], r["상태"], r["이름표"],
                              r["출처"], r["바뀐날"]]) + "\n" for r in rows)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(head + body, encoding="utf-8")
    tmp.replace(p)


def 기본표():
    if not _DATA.exists():
        return {}
    t = {}
    for l in _DATA.read_text(encoding="utf-8").splitlines():
        if not l or l.startswith("#") or "\t" not in l:
            continue
        f, s = l.split("\t")[:2]
        t.setdefault(f.strip(), []).append(s.strip())
    return t


def _단계(v):
    if v not in [str(i) for i in range(9)]:
        sys.exit(f"  ⛔ 단계는 0~8 숫자입니다: {v}")
    return v


def _이름(v, 무엇):
    v = (v or "").strip()
    if not v:
        sys.exit(f"  ⛔ {무엇} 이름이 비었습니다")
    if "·" in v or "\t" in v:
        sys.exit(f"  ⛔ {무엇} 이름에 가운뎃점(·)이나 탭을 쓰지 않습니다: {v}")
    return v


def 기능추가(단계, 기능, 세부들):
    단계, 기능 = _단계(단계), _이름(기능, "기능")
    rows = 읽기()
    있는 = {(r["기능"], r["세부기능"]) for r in rows}
    출처 = "기획"
    if not 세부들:
        세부들 = 기본표().get(기능, [])
        출처 = "기본"
        if not 세부들:
            sys.exit(f"  ⛔ 「{기능}」의 기본 세부기능이 없습니다. 세부기능을 같이 적어 주십시오:\n"
                     f"     plan.py 기능추가 {단계} {기능} <세부기능> <세부기능> …")
    더함 = []
    for s in 세부들:
        s = _이름(s, "세부기능")
        if (기능, s) in 있는:
            continue
        rows.append({"단계": 단계, "기능": 기능, "세부기능": s, "상태": "시작 전", "이름표": "",
                     "출처": 출처, "바뀐날": date.today().isoformat()})
        더함.append(s)
    쓰기(rows)
    print(f"  · 설계표 [{단계이름[int(단계)]}] {기능} — 세부기능 {len(더함)}개 자리를 만들었습니다"
          + (" (기본 표에서)" if 출처 == "기본" else ""))
    for s in 더함:
        print(f"      ○ {s}")


def 세부기능(단계, 기능, 세부):
    기능추가(단계, 기능, [세부])


def 세부빼기(기능, 세부):
    rows = 읽기()
    남 = [r for r in rows if not (r["기능"] == 기능 and r["세부기능"] == 세부)]
    if len(남) == len(rows):
        sys.exit(f"  ⛔ 설계표에 「{기능} / {세부}」가 없습니다")
    쓰기(남)
    print(f"  · 설계표에서 뺐습니다: {기능} / {세부}")


def 세부상태(기능, 세부, 상태, 이름표=""):
    if 상태 not in 상태들:
        sys.exit("  ⛔ 상태는 다섯 중 하나입니다: " + " · ".join(상태들))
    이름표 = (이름표 or "").strip()
    낮춤 = False
    준말 = 이름표
    _단 = {r["단계"] for r in 읽기() if r["기능"] == 기능 and r["세부기능"] == 세부}
    if 상태 == "완료" and _단 & {"1", "3"}:
        if not 이름표:
            sys.exit(f"  ⛔ 기획·설계의 «완료»에는 정한 내용이 필요합니다 — 「{세부}」을 무엇으로 정했나요?\n"
                     f"     plan.py 세부상태 \"{기능}\" \"{세부}\" 완료 \"<정한 내용 한 줄>\"")
    elif 상태 == "완료":
        if not 이름표 or any(t in 이름표.replace(" ", "") for t in 미확인말):
            상태, 이름표, 낮춤 = "확인 필요", "확인 안 함", True
    if 상태 in 이름표필요 and not 이름표:
        sys.exit(f"  ⛔ 「{상태}」에는 짧은 이름표가 필요합니다 — 무엇을 확인하나 / 무엇이 막혔나.\n"
                 f"     문장이 아니라 이름표로 (예: 「알림 권한 문구」)")
    if 상태 not in 이름표필요 and 상태 != "완료":
        이름표 = ""
    rows = 읽기()
    hit = [r for r in rows if r["기능"] == 기능 and r["세부기능"] == 세부]
    if not hit:
        sys.exit(f"  ⛔ 설계표에 「{기능} / {세부}」 자리가 없습니다. 먼저 자리를 만드십시오:\n"
                 f"     plan.py 세부기능 <단계> {기능} {세부}")
    설치전 = all(str(r.get("출처", "")).startswith("설치 전") for r in hit)
    if not 설치전 and 상태 in ("진행 중", "완료") and any(int(r["단계"]) >= 4 and r["상태"] != 상태 for r in hit):
        n = _출처있는표준수(기능)
        if n is not None and n == 0:
            sys.exit(f"  ⛔ 「{기능}」에 출처 있는 표준 방식이 없습니다 — 표준 없이 «{상태}» 상태로 옮기지 않습니다.\n"
                     f"     먼저 이 기능을 같은 기능의 앱·공식 문서로 리서치해서 적으십시오:\n"
                     f"     ledger.sh 표준 \"<표준 방식 한 줄>\" \"<출처 — 어느 앱·어느 공식 문서>\" 공식문서|남이한것|돌려봄 \"{기능}\"\n"
                     f"     (「내기억」으로 적은 것은 세지 않습니다)")
        m = _연결따짐(기능)
        if m is False:
            sys.exit(f"  ⛔ 「{기능}」이 다른 기능과 어떻게 엮이는지 적혀 있지 않습니다 — 따져 보지 않고 «{상태}» 상태로 옮기지 않습니다.\n"
                     f"     엮이면:   ledger.sh 영향 \"{기능}\" \"<같이 바뀌는 기능>\" \"같은것을쓴다: <무엇>\" 리서치|표준|깨졌다\n"
                     f"     안 엮이면: ledger.sh 독립 \"{기능}\" \"<왜 다른 기능과 안 엮이나>\"")
    for r in hit:
        r["상태"], r["이름표"], r["바뀐날"] = 상태, 이름표, date.today().isoformat()
    쓰기(rows)
    if 상태 == "완료" and not 낮춤:
        lp = _file().with_name("ledger.tsv")
        if lp.exists():
            with open(lp, "a", encoding="utf-8") as f:
                f.write("\t".join([date.today().isoformat(), "세부확인", "", 이름표, "", "", f"{기능} › {세부}"]) + "\n")
    print(f"  · {기능} / {세부} → {상태}" + (f" ({이름표})" if 이름표 else ""))
    if 낮춤:
        print(("  ⚠️ 「" + 준말 + "」은 직접 확인한 것이 아니라서" if 준말 else "  ⚠️ 무엇으로 확인했는지가 없어")
              + " 「완료」가 아니라 「확인 필요 · 확인 안 함」으로 적었습니다.\n"
              f"     확인했으면: 세부상태 {기능} {세부} 완료 \"<무엇으로 확인했나 — 예: 휴대폰에서 눌러 봄>\"")


def 설치전(기능, 세부, 근거):
    """⭐ 개발 중간에 야간비행을 깐 앱 — 이미 만들어 둔 세부기능을 «완료»로 적는다. 근거는 출처 칸에 «설치 전 · …»으로 남긴다.
    🔴 2026-10-27  — «확인 필요»로 넣었더니 한 앱에서 40개가
       «지금 하실 일»을 덮었다. 이미 돌아가는 제품의 기능을 사용자 할 일로 만들면 안 된다.
    
    🔴 왜: 표준 방식이 없으면 «완료»를 거절해서, 코드에 이미 돌아가는 기능 40개가 전부 «시작 전»으로 들어갔다(2026-10-25 실측 — 그중 26개는 시험이 통과했다).
    ⭐ 근거(어느 파일 · 어느 시험)를 출처 칸에 남긴다. 옛 판(«확인 필요 · 설치 전 작업»)으로 적힌 줄도 다시 부르면 완료가 된다."""
    근거 = (근거 or "").strip()
    if not 근거:
        sys.exit("  ⛔ 근거가 필요합니다 — 어느 파일에 있나 · 어느 시험이 통과하나")
    rows = 읽기()
    hit = [r for r in rows if r["기능"] == 기능 and r["세부기능"] == 세부]
    if not hit:
        sys.exit(f"  ⛔ 설계표에 「{기능} / {세부}」 자리가 없습니다 — 먼저: ledger.sh 세부기능 4 \"{기능}\" \"{세부}\"")
    for r in hit:
        r["상태"], r["이름표"], r["출처"], r["바뀐날"] = "완료", "", "설치 전 · " + 근거.replace("\t", " "), date.today().isoformat()
    쓰기(rows)
    print(f"  · {기능} / {세부} → 완료 (설치 전에 만듦 — {근거})")


def 설치전확인(기능, 세부, 확인):
    """사람이 설치 전 작업을 확인했다 — «완료». 확인 방법이 없거나 «안 함»이면 세부상태와 같이 «확인 필요»로 남긴다."""
    rows = 읽기()
    hit = [r for r in rows if r["기능"] == 기능 and r["세부기능"] == 세부]
    if not hit or not all(str(r.get("출처", "")).startswith("설치 전") for r in hit):
        sys.exit(f"  ⛔ 「{기능} / {세부}」은 설치 전 작업으로 적힌 자리가 아닙니다 — 평소처럼 세부상태로 적으십시오")
    세부상태(기능, 세부, "완료", 확인)


def _연결따짐(기능):
    """그 기능의 연결을 따져 봤나 — True/False, 못 보면 None(«못 봄»)."""
    try:
        import dependencies as _dp
        return 기능 in _dp.연결된기능(_file().with_name("ledger.tsv"))
    except Exception:
        return None


def _출처있는표준수(기능):
    """그 기능에 적힌 «출처 있는» 표준 수. 못 세면 None(«못 봄») — 0 과 가른다."""
    try:
        import standards as _st
        d = _st.compute(_file().with_name("ledger.tsv"))
    except Exception:
        return None
    if d.get("못쟀다"):
        return 0
    return sum(1 for x in d.get("기능별", {}).get(기능, []) if x.get("확인") in _st.SOURCED)


def _설명파일():
    return _file().with_name("plan-notes.tsv")


def 설명읽기():
    p = _설명파일()
    out = {}
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            if l and not l.startswith("#") and "\t" in l:
                k, v = l.split("\t", 1)
                out[k] = v
    return out


def 기능설명(기능, 설명):
    if 기능 not in {r["기능"] for r in 읽기()}:
        sys.exit(f"  ⛔ 「{기능}」은 설계표에 없는 기능입니다")
    p = _설명파일()
    if not p.exists():
        p.write_text("# 기능 설명 — 기능 ⇥ 한 줄 (tools/plan.py 가 쓴다)\n", encoding="utf-8")
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"{기능}\t{(설명 or '').strip()}\n")
    print(f"  · 「{기능}」 설명: {설명}")


def _언제파일():
    return _file().with_name("plan-when.tsv")


def 언제읽기():
    p = _언제파일(); out = {}
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            if l and not l.startswith("#"):
                c = (l.split("\t") + [""] * 5)[:5]
                out[(c[0], c[1])] = {"언제": c[2], "물음": c[3], "지금까지": c[4]}
    return out


def 세부언제(기능, 세부, 언제, 물음="", 지금까지=""):
    if (기능, 세부) not in {(r["기능"], r["세부기능"]) for r in 읽기()}:
        sys.exit(f"  ⛔ 설계표에 「{기능} / {세부}」 자리가 없습니다")
    if not (언제 or "").strip():
        sys.exit("  ⛔ «언제»가 비었습니다 — 무엇이 먼저 일어나야 확인되나요")
    p = _언제파일()
    if not p.exists():
        p.write_text("# 때가 되면 확인할 것 — 기능 ⇥ 세부 ⇥ 언제 ⇥ 물음 ⇥ 지금까지 (tools/plan.py 가 쓴다)\n", encoding="utf-8")
    with open(p, "a", encoding="utf-8") as f:
        f.write("\t".join([기능, 세부, 언제.strip(), (물음 or "").strip(), (지금까지 or "").strip()]) + "\n")
    print(f"  · 「{기능} / {세부}」 — 나중에 확인할 것: {언제}")


def _화면파일():
    return _file().with_name("screens.tsv")


def 화면읽기():
    p = _화면파일()
    if not p.exists():
        return []
    화면, 순 = {}, []
    for l in p.read_text(encoding="utf-8").splitlines():
        if not l or l.startswith("#"):
            continue
        c = (l.split("\t") + [""] * 5)[:5]
        if c[0] == "화면" and c[1] and c[1] not in 화면:
            화면[c[1]] = {"이름": c[1], "설명": c[2], "요소": [], "이동": [], "종류": "",
                          "풀이름": "", "언제": "", "하는일": "", "상태": [], "갈림": "", "문제": []}
            순.append(c[1])
        elif c[0] == "요소" and c[1] in 화면:
            같은 = [e for e in 화면[c[1]]["요소"] if e["설명"] == c[2]]
            if 같은:
                같은[0]["기능"], 같은[0]["세부기능"] = c[3], c[4]
            else:
                화면[c[1]]["요소"].append({"번호": len(화면[c[1]]["요소"]) + 1, "설명": c[2], "기능": c[3], "세부기능": c[4]})
        elif c[0] == "종류" and c[1] in 화면:
            화면[c[1]]["종류"] = c[2]
        elif c[0] == "이동" and c[1] in 화면:
            같은 = [m for m in 화면[c[1]]["이동"] if m["다음"] == c[2]]
            if 같은:
                같은[0]["조건"] = c[3]
            else:
                화면[c[1]]["이동"].append({"다음": c[2], "조건": c[3]})
        elif c[0] == "갈림" and c[1] in 화면:
            화면[c[1]]["갈림"] = c[2]
        elif c[0] in ("이름", "언제", "하는일") and c[1] in 화면:
            화면[c[1]]["풀이름" if c[0] == "이름" else c[0]] = c[2]
        elif c[0] == "상태" and c[1] in 화면:
            화면[c[1]]["상태"].append({"상태": c[2], "때": c[3], "나쁨": c[4] == "나쁨"})
        elif c[0] == "상태비움" and c[1] in 화면:
            화면[c[1]]["상태"] = []
        elif c[0] == "문제" and c[1] in 화면 and c[2] and c[2] not in 화면[c[1]]["문제"]:
            화면[c[1]]["문제"].append(c[2])
        elif c[0] == "화면빼기" and c[1] in 화면:
            del 화면[c[1]]; 순.remove(c[1])
            for x in 화면.values():
                x["이동"] = [m for m in x["이동"] if m["다음"] != c[1]]
    return [화면[k] for k in 순]


def 없앤것읽기():
    """없앤 기능 · 화면 목록 — 조종석 자료가 엮임 · 상태 그림에서 이 이름들을 뺀다(기록은 지우지 않고 «없앴다»를 적는다)."""
    p = _화면파일()
    out = []
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            c = (l.split("\t") + [""] * 3)[:3]
            if c[0] in ("기능빼기", "화면빼기") and c[1]:
                out.append({"종류": "기능" if c[0] == "기능빼기" else "화면", "이름": c[1], "왜": c[2]})
    return out


def 기능빼기(기능, 왜):
    """기능 하나를 모든 단계에서 뺀다 — 설계표의 그 기능 줄 전부 · 그 기능을 가리키던 화면 요소(compute 가 뺀다) · 엮임 · 상태 그림(조종석 자료가 뺀다)."""
    rows = 읽기()
    남 = [r for r in rows if r["기능"] != 기능]
    if len(남) == len(rows):
        sys.exit(f"  ⛔ 설계표에 「{기능}」 기능이 없습니다")
    if len((왜 or "").strip()) < 4:
        sys.exit("  ⛔ 왜 빼는지 한 줄 적어 주십시오 — 없앤 기능인지, 다른 기능에 합쳤는지")
    단 = sorted({r["단계"] for r in rows if r["기능"] == 기능})
    쓰기(남)
    _화면적기(["기능빼기", 기능, 왜.strip()])
    print(f"  · «{기능}» 기능을 뺐습니다 — {왜.strip()}  (설계표 {', '.join(단)}단계에서 {len(rows) - len(남)}줄 · 그 기능을 가리키던 화면 요소 · 엮임 · 상태 그림에서도 빠집니다)")


def 화면일읽기():
    """⭐ 2026-10-27  — 사용자가 «하는 일» 하나와 그때 지나는 화면 차례.
    조종석 설계 단계가 이것을 줄마다 보이고, 누른 줄만 폰 화면으로 편다. 이름은 클로드가 코드와 기록에서 만든다(㉮).
    ⛔ 화면 차례만 적는다 — 화살표 위 «무엇을 하면»은 화면이동의 조건을 그대로 쓴다(두 곳에 적지 않는다)."""
    p = _화면파일()
    if not p.exists():
        return []
    일, 순 = {}, []
    for l in p.read_text(encoding="utf-8").splitlines():
        c = (l.split("\t") + [""] * 4)[:4]
        if c[0] == "일" and c[1]:
            if c[1] not in 일:
                순.append(c[1])
            일[c[1]] = {"이름": c[1], "때": c[2], "차례": [s.split("|") for s in c[3].split(",") if s]}
        elif c[0] == "일빼기" and c[1] in 일:
            del 일[c[1]]; 순.remove(c[1])
        elif c[0] == "화면빼기" and c[1]:
            for k in 일:
                일[k]["차례"] = [g for g in ([n for n in s if n != c[1]] for s in 일[k]["차례"]) if g]
    return [일[k] for k in 순]


def 화면일(이름, 때, 차례):
    이름 = _이름(이름, "하는 일")
    names = {x["이름"] for x in 화면읽기()}
    if not 차례:
        sys.exit("  ⛔ 화면을 하나 이상 주십시오 — 이 일을 할 때 지나는 화면 차례")
    for s in 차례:
        for n in s.split("|"):
            if n not in names:
                sys.exit(f"  ⛔ 「{n}」 화면이 없습니다 — 먼저: plan.py 화면 \"{n}\" \"<설명>\"")
    _화면적기(["일", 이름, (때 or "").strip(), ",".join(차례)])
    print(f"  · 하는 일 «{이름}» — " + " → ".join(" 또는 ".join(s.split("|")) for s in 차례))


def _화면적기(줄):
    p = _화면파일()
    if not p.exists():
        p.write_text("# 화면 설계서 — 화면 ⇥ 이름 ⇥ 설명 | 요소 ⇥ 화면 ⇥ 설명 ⇥ 기능 | 이동 ⇥ 화면 ⇥ 다음 화면 ⇥ 무엇을 하면 (tools/plan.py 가 쓴다)\n", encoding="utf-8")
    with open(p, "a", encoding="utf-8") as f:
        f.write("\t".join(줄) + "\n")


def 화면(이름, 설명):
    이름 = _이름(이름, "화면")
    if any(x["이름"] == 이름 for x in 화면읽기()):
        sys.exit(f"  ⛔ 「{이름}」 화면이 이미 있습니다")
    _화면적기(["화면", 이름, (설명 or "").strip()])
    c = ord(이름[-1]); 을 = "을" if 0xAC00 <= c <= 0xD7A3 and (c - 0xAC00) % 28 else "를"
    print(f"  · 화면 «{이름}»{을} 더했습니다")


def 화면요소(이름, 설명, 기능, 세부=""):
    if not any(x["이름"] == 이름 for x in 화면읽기()):
        sys.exit(f"  ⛔ 「{이름}」 화면이 없습니다 — 먼저: plan.py 화면 \"{이름}\" \"<설명>\"")
    if 기능 not in {r["기능"] for r in 읽기()}:
        sys.exit(f"  ⛔ 「{기능}」은 설계표에 없는 기능입니다 — 화면 위 요소는 설계표의 기능과 이어져야 진행 상태가 보입니다")
    if 세부 and 세부 not in {r["세부기능"] for r in 읽기() if r["기능"] == 기능}:
        sys.exit(f"  ⛔ 「{기능}」에 「{세부}」 세부기능이 없습니다")
    _화면적기(["요소", 이름, (설명 or "").strip(), 기능, 세부 or ""])
    print(f"  · «{이름}» 화면에 요소를 더했습니다 — {설명} ({기능}{' › ' + 세부 if 세부 else ''})")


def 화면종류(이름, 종류):
    if 종류 not in ("폰", "모니터", "메일"):
        sys.exit("  ⛔ 화면 종류는 «폰» · «모니터» · «메일»입니다")
    if not any(x["이름"] == 이름 for x in 화면읽기()):
        sys.exit(f"  ⛔ 「{이름}」 화면이 없습니다")
    _화면적기(["종류", 이름, 종류])
    print(f"  · «{이름}» → {종류} 화면")


def 화면이동(이름, 다음, 조건):
    names = {x["이름"] for x in 화면읽기()}
    for n in (이름, 다음):
        if n not in names:
            sys.exit(f"  ⛔ 「{n}」 화면이 없습니다")
    _화면적기(["이동", 이름, 다음, (조건 or "").strip()])
    print(f"  · «{이름}» → «{다음}» ({조건})")


def 화면칸(이름, 칸, 글):
    if not any(x["이름"] == 이름 for x in 화면읽기()):
        sys.exit(f"  ⛔ 「{이름}」 화면이 없습니다")
    글 = (글 or "").strip()
    if not 글:
        sys.exit("  ⛔ 빈 글은 적지 않습니다")
    _화면적기([칸, 이름, 글])
    print(f"  · «{이름}» {dict(이름='풀어 쓴 이름', 언제='언제 보나', 하는일='하는 일', 갈림='갈림 물음')[칸]} — {글}")


def 화면상태(이름, 상태, 때="", 나쁨=""):
    if not any(x["이름"] == 이름 for x in 화면읽기()):
        sys.exit(f"  ⛔ 「{이름}」 화면이 없습니다")
    if 나쁨 not in ("", "나쁨"):
        sys.exit("  ⛔ 넷째 칸은 비우거나 «나쁨»입니다(실패 · 만료처럼 끝나는 상태)")
    _화면적기(["상태", 이름, 상태.strip(), (때 or "").strip(), 나쁨])
    print(f"  · «{이름}» 상태 «{상태}»" + (f" → {때}" if 때 else ""))


def _기록낮춤():
    """Ⓘ 2026-10-24 레드팀 7회차 ·  기록이 가리키는 세부기능.
    ⭐ 기록(ledger.tsv 의 됐다 줄 일곱째 칸 «기능 › 세부기능 · …»)이 «확인 안 함»인데 설계표는 «완료»면
       화면에서는 «확인 필요 · 확인 안 함»으로 보낸다 — 두 기록이 어긋나면 확인 안 한 쪽을 믿는다.
    ⛔ 설계표 파일은 안 고친다(보내는 꼴만 낮춘다).
    ⭐ 그 세부기능을 가리키는 **마지막** 끝냄 기록만 본다 — 같은 날 «확인 안 함» 뒤에 확인해서 다시 적었으면 그쪽이 이긴다
       (날짜만 있고 시각이 없어 바뀐날로는 같은 날 앞뒤를 못 가린다). 설계표를 그 «다음 날» 이후에 완료로 고쳤으면 낮추지 않는다."""
    p = _file().with_name("ledger.tsv")
    out = {}
    if not p.exists():
        return out
    _정함 = {(r["기능"], r["세부기능"]) for r in 읽기() if r["단계"] in ("1", "3")}
    for l in p.read_text(encoding="utf-8").splitlines():
        c = l.split("\t")
        if len(c) < 7 or c[1] not in ("됐다", "세부확인") or not c[6].strip():
            continue
        if c[1] == "세부확인" and tuple(c[6].split(" › ", 1)) in _정함:
            for x in c[6].split(" · "):
                if " › " in x:
                    out[tuple(x.split(" › ", 1))] = None
            continue
        안함 = any(t in c[3].replace(" ", "") for t in 미확인말)
        for x in c[6].split(" · "):
            if " › " in x:
                out[tuple(x.split(" › ", 1))] = c[0] if 안함 else None
    return {k: v for k, v in out.items() if v}


def compute():
    """조종석에 보낼 꼴 — 단계별 기능, 기능별 세부기능과 상태 수."""
    rows = 읽기()
    _설명 = 설명읽기()
    _언제 = 언제읽기()
    낮출 = _기록낮춤()
    for r in rows:
        d = 낮출.get((r["기능"], r["세부기능"]))
        if d and r["상태"] == "완료" and (r.get("바뀐날") or "") <= d:
            r["상태"], r["이름표"] = "확인 필요", "확인 안 함"
    per = {}
    for r in rows:
        st = per.setdefault(r["단계"], {"기능들": [], "_i": {}})
        if r["기능"] not in st["_i"]:
            st["_i"][r["기능"]] = len(st["기능들"])
            st["기능들"].append({"기능": r["기능"], "세부": [], "수": {k: 0 for k in 상태들}, "설명": _설명.get(r["기능"], "")})
        f = st["기능들"][st["_i"][r["기능"]]]
        완 = r["상태"] == "완료"
        f["세부"].append({"이름": r["세부기능"], "상태": r["상태"], "이름표": "" if 완 else r["이름표"],
                         "확인": r["이름표"] if 완 else "", "출처": r["출처"], "바뀐날": r.get("바뀐날") or "",
                         "때": (_언제.get((r["기능"], r["세부기능"])) if not 완 else None)})
        f["수"][r["상태"]] = f["수"].get(r["상태"], 0) + 1
    for st in per.values():
        st.pop("_i")
        st["세부전체"] = sum(len(f["세부"]) for f in st["기능들"])
        st["세부완료"] = sum(f["수"]["완료"] for f in st["기능들"])
    있는 = {}
    for r in rows:
        있는.setdefault(r["기능"], set()).add(r["세부기능"])
    화면 = 화면읽기()
    for x in 화면:
        새 = []
        for e in x["요소"]:
            if e["기능"] and 있는 and e["기능"] not in 있는:
                continue
            if e["세부기능"] and e["세부기능"] not in 있는.get(e["기능"], set()):
                e = dict(e, 세부기능="")
            새.append(e)
        for i, e in enumerate(새, 1):
            e["번호"] = i
        x["요소"] = 새
    return {"있나": bool(rows), "상태들": 상태들, "단계": per, "화면들": 화면, "하는일들": 화면일읽기(), "없앤것": 없앤것읽기()}


def 보기():
    d = compute()
    if not d["있나"]:
        print("  설계표가 비었습니다 — 설계 단계에서 기능과 세부기능 자리를 만듭니다.")
        return
    표 = {"시작 전": "○", "진행 중": "◐", "완료": "●", "확인 필요": "△", "방법 찾는 중": "✕"}
    for k in sorted(d["단계"], key=int):
        st = d["단계"][k]
        print(f"\n  [{단계이름[int(k)]}] 세부기능 {st['세부완료']}/{st['세부전체']} 완료")
        for f in st["기능들"]:
            n = len(f["세부"])
            print(f"    {f['기능']}  {f['수']['완료']}/{n}")
            for s in f["세부"]:
                print(f"      {표.get(s['상태'], '?')} {s['이름']} — {s['상태']}"
                      + (f" ({s['이름표']})" if s["이름표"] else ""))


if __name__ == "__main__":
    a = sys.argv[1:]
    cmd = a[0] if a else "보기"
    try:
        if cmd == "기능추가" and len(a) >= 3:
            기능추가(a[1], a[2], a[3:])
        elif cmd == "세부기능" and len(a) == 4:
            세부기능(a[1], a[2], a[3])
        elif cmd == "세부빼기" and len(a) == 3:
            세부빼기(a[1], a[2])
        elif cmd == "세부상태" and len(a) in (4, 5):
            세부상태(a[1], a[2], a[3], a[4] if len(a) == 5 else "")
        elif cmd == "설치전" and len(a) == 4:
            설치전(a[1], a[2], a[3])
        elif cmd == "설치전확인" and len(a) == 4:
            설치전확인(a[1], a[2], a[3])
        elif cmd == "화면" and len(a) == 3:
            화면(a[1], a[2])
        elif cmd == "화면요소" and len(a) in (4, 5):
            화면요소(a[1], a[2], a[3], a[4] if len(a) == 5 else "")
        elif cmd == "세부언제" and 4 <= len(a) <= 6:
            세부언제(a[1], a[2], a[3], a[4] if len(a) > 4 else "", a[5] if len(a) > 5 else "")
        elif cmd == "기능설명" and len(a) == 3:
            기능설명(a[1], a[2])
        elif cmd == "화면종류" and len(a) == 3:
            화면종류(a[1], a[2])
        elif cmd == "화면이동" and len(a) == 4:
            화면이동(a[1], a[2], a[3])
        elif cmd in ("화면이름", "화면언제", "화면하는일", "화면갈림") and len(a) == 3:
            화면칸(a[1], cmd[2:], a[2])
        elif cmd == "화면상태" and 3 <= len(a) <= 5:
            화면상태(a[1], a[2], a[3] if len(a) > 3 else "", a[4] if len(a) > 4 else "")
        elif cmd == "화면일" and len(a) >= 4:
            화면일(a[1], a[2], a[3:])
        elif cmd == "화면문제" and len(a) == 3:
            if a[1] not in {x["이름"] for x in 화면읽기()}:
                sys.exit(f"  ⛔ 「{a[1]}」 화면이 없습니다")
            if len(a[2].strip()) < 6:
                sys.exit("  ⛔ 문제 글은 «지금 하실 일»에 뜨는 글의 앞부분을 6글자 넘게 적어 주십시오")
            _화면적기(["문제", a[1], a[2].strip()])
            print(f"  · «{a[1]}» 화면의 문제 — {a[2].strip()}")
        elif cmd == "기능빼기" and len(a) == 3:
            기능빼기(a[1], a[2])
        elif cmd == "화면빼기" and len(a) == 3:
            if a[1] not in {x["이름"] for x in 화면읽기()}:
                sys.exit(f"  ⛔ 「{a[1]}」 화면이 없습니다")
            if len(a[2].strip()) < 4:
                sys.exit("  ⛔ 왜 빼는지 한 줄 적어 주십시오 — 없앤 화면인지, 잘못 적은 화면인지")
            _화면적기(["화면빼기", a[1], a[2].strip()])
            print(f"  · «{a[1]}» 화면을 뺐습니다 — {a[2].strip()} (그 화면으로 가던 이동과 하는 일의 차례에서도 뺐습니다)")
        elif cmd == "화면일빼기" and len(a) == 2:
            if a[1] not in {x["이름"] for x in 화면일읽기()}:
                sys.exit(f"  ⛔ 「{a[1]}」 하는 일이 없습니다")
            _화면적기(["일빼기", a[1]])
            print(f"  · 하는 일 «{a[1]}»을 뺐습니다")
        elif cmd == "화면상태비움" and len(a) == 2:
            _화면적기(["상태비움", a[1]])
        elif cmd == "보기":
            보기()
        elif cmd == "json":
            print(json.dumps(compute(), ensure_ascii=False))
        else:
            sys.exit(__doc__.split("쓰는 법:")[1])
    except BrokenPipeError:
        pass
