#!/usr/bin/env python3
"""규칙 0 검사 — 사용자에게 보이는 문구에 개발 용어가 있나.

⛔ 왜 이 검사가 있나 (2026-10-03): `RULE-0.md` 에 이력이 적혀 있다.
   §23 이 「개발용어는 권력이다」를 이미 적어 뒀는데 **그 문서를 인용하면서 어겼다** —
   온보딩에 셸 명령 8개를 넣었고, `asc.py:66` 이 비개발자에게
   「열쇠(.p8)를 이 앱의 tools/ 폴더에」라고 말하고 있었다.
   ⭐ **규칙을 아는 것으로는 안 지켜진다. 그래서 검사로 만든다.**

무엇을 보나 — «사용자 눈에 직접 닿는 것»만 본다
   1. `ledger.sh` 호출의 사용자 문구 인자 (제목·왜·하실 일)
   2. `board/cockpit.html` 의 화면 문자열
   3. 옆 저장소 `../nightflight-server/explain/*.md` (있으면)

⛔ 주석은 가린다 — 사고 기록이 옛 문장을 «인용»한다.
   2026-10-03 시험 8 에서 실제로 그 오탐이 났다.
⛔ 낱말 체크리스트는 «일부러» 개발 낱말을 보인다 → 파일 첫 20줄에
   `RULE-0: 낱말 목록` 이 있으면 그 파일은 건너뛴다.
"""
import pathlib
import re
import sys
from pathlib import Path

CMDS = (r"sysctl|sw_vers|xcode-select|xcodebuild|xcrun|simctl|altool|codesign|security|"
        r"defaults|plutil|osascript|pkill|chmod|mkdir|rm -|cat |grep |sed |awk |"
        r"npm |npx |pip |python3 |brew |git |df -|du -|ls -|curl |openssl")
PATHS = r"(~/|\.{0,2}/)[A-Za-z0-9_.\-]+/|[A-Za-z0-9_\-]+\.(p8|env|json|plist|xcodeproj|swift|sh|py|yml|toml|tsv)\b"
SEOLMYEONG = {
    "API": "다른 프로그램과 주고받는 창구",
    "URL": "인터넷 주소",
    "Xcode": "애플 앱을 만드는 프로그램",
    "TestFlight": "출시 전에 애플을 거쳐 시험으로 나눠 주는 곳",
    "SDK": "남이 만들어 둔 기능 묶음",
    "CLI": "글자로 다루는 프로그램",
    "JSON": "프로그램끼리 주고받는 글 형식",
    "OAuth": "다른 서비스 계정으로 로그인하게 해 주는 방식",
    "SSL": "주고받는 내용을 가리는 보안 방식",
    "TLS": "주고받는 내용을 가리는 보안 방식",
    "DNS": "주소를 실제 서버로 이어 주는 장치",
    "Keychain": "애플 기기가 비밀번호를 보관하는 곳",
    "YAML": "설정을 적는 글 형식",
    "RLS": "누가 어느 자료를 볼 수 있는지 정하는 규칙",
    "MCP": "바깥 도구를 붙이는 규격",
    "IAP": "앱 안에서 하는 결제",
    "CI/CD": "고칠 때마다 자동으로 검사하고 내보내는 것",
    "CI": "고칠 때마다 자동으로 검사하는 것",
    "JWT": "로그인한 사람임을 증명하는 글자",
    "UUID": "겹치지 않게 붙이는 식별 글자",
    "StoreKit": "애플 결제를 붙이는 도구",
    "CloudKit": "애플이 주는 저장 공간",
    "repo": "코드를 모아 두는 곳",
    "리포지토리": "코드를 모아 두는 곳",
    "저장소": "코드를 모아 두는 곳",
    "commit": "고친 것을 한 덩이로 기록에 남기는 것",
    "커밋": "고친 것을 한 덩이로 기록에 남기는 것",
    "merge": "갈라져 있던 것을 합치는 것",
    "머지": "갈라져 있던 것을 합치는 것",
    "브랜치": "본래 것과 따로 고치려고 떠 놓은 사본",
    "lint": "코드에 문제가 없는지 자동으로 보는 것",
    "린트": "코드에 문제가 없는지 자동으로 보는 것",
    "schema": "자료를 어떤 칸에 담을지 정해 둔 구성",
    "스키마": "자료를 어떤 칸에 담을지 정해 둔 구성",
    "마이그레이션": "저장 구성을 바꾸고 있던 자료를 옮기는 일",
    "네이티브": "그 기기에 맞게 직접 만든 앱",
    "웹뷰": "앱 안에서 웹사이트를 그대로 보여 주는 화면",
    "아키텍처": "전체를 어떻게 나눠 놓았는지",
    "상태머신": "지금 어느 상태인지와 다음에 갈 수 있는 곳을 정해 둔 것",
    "포그라운드": "앱이 화면에 떠 있는 동안",
    "백그라운드": "앱이 화면에 안 보이는 동안",
    "디버그": "문제를 찾아 고치는 일",
    "터미널": "글자로 다루는 화면",
    "디렉터리": "폴더",
    "환경변수": "프로그램이 돌 때 읽는 설정 값",
    "엔드포인트": "요청을 받는 주소",
    "프로비저닝": "애플이 이 기기와 이 앱에 허가를 내주는 절차",
    "빌드 산출물": "만들어 나온 파일",
    "파싱": "글을 읽어 쓸 수 있는 꼴로 바꾸는 일",
    "스택트레이스": "오류가 어디서 났는지 거슬러 적은 목록",
}



def 우리링크(f: Path) -> bool:
    """손님 폴더에 놓인 «우리 파일로 가는 링크»인가 — 그 파일은 손님 것이 아니다.
    🔴 11~13회차 ④⑤(돌려서 확인): 설치가 tools/ 에 건 링크 파일(우리 검사 도구)을 «손볼 곳 9곳»으로 손님 모델에게 넘겼다 —
      모델이 고치면 링크를 타고 «모든 앱이 같이 쓰는» 플러그인 원본이 바뀐다."""
    try:
        return f.is_symlink() and Path(__file__).resolve().parent.parent in f.resolve().parents
    except OSError:
        return False


def 기록자리(뿌리: Path) -> Path:
    """그 제품의 기록 자리 — `.nightflight`, 없으면 `.claude`(셸 project-root.sh · tools/_root.py 와 같은 규칙: 있는 폴더 먼저).
    🔴 13회차 ⑤⑥: `.claude` 를 박아 새 꼴(.nightflight) 제품의 기록을 못 읽었다."""
    for d in (".nightflight", ".claude"):
        if (뿌리 / d).is_dir() and (d != ".claude" or (뿌리 / d / "ledger.tsv").is_file()):
            return 뿌리 / d
    return 뿌리 / ".nightflight"


def 설명찾기(낱말: str) -> str:
    """⭐ 표에 **조사가 붙은 꼴**(`저장소에`·`터미널에`)로 들어 있는 것이 있다 —
    그대로 못 찾으면 **끝의 조사를 떼고** 한 번 더 본다. 그래도 없으면 빈 글자다.
    ⛔ 지어내지 않는다 — 설명이 없으면 **없는 채로** 나가고, 그건 적어야 할 일이다."""
    if 낱말 in SEOLMYEONG:
        return SEOLMYEONG[낱말]
    for 조사 in ("에서", "으로", "에", "을", "를", "이", "가", "은", "는", "의", "도"):
        if 낱말.endswith(조사) and 낱말[: -len(조사)] in SEOLMYEONG:
            return SEOLMYEONG[낱말[: -len(조사)]]
    return ""


def 내앱말(root=None) -> set:
    """⭐ **그 사람이 «지은» 이름** — 앱 이름과 기능 지도의 말.
    . 설명을 붙이지 않고 바꾸지도 않는다.
    ⚠️ 지금 아는 자리는 **둘**이다 — 앱 이름과 기능 지도. 그 밖에 지으신 이름은
       우리가 알 길이 없다. 0 이 「그 사람 말이 없다」는 뜻이 아니다."""
    import json as _j
    r = pathlib.Path(root) if root else pathlib.Path(".")
    out = set()
    try:
        d = _j.loads((기록자리(r) / "board" / "now.json").read_text(encoding="utf-8"))
        for k in ("앱이름", "폴더"):
            if (d.get(k) or "").strip():
                out.add(d[k].strip())
    except Exception:
        pass
    try:
        for line in (기록자리(r) / "feature-map.tsv").read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or not line.strip():
                continue
            for 칸 in line.split("\t"):
                if 칸.strip():
                    out.add(칸.strip())
    except Exception:
        pass
    return out



WORDS = (
    ("API", 1), ("URL", 1), ("Xcode", 1), ("TestFlight", 1),
    ("SDK", 2), ("CLI", 2), ("JSON", 2), ("OAuth", 2), ("SSL", 2), ("DNS", 2),
    ("Keychain", 2),
    ("YAML", 3), ("RLS", 3), ("MCP", 3), ("IAP", 3), ("CI/CD", 3), ("JWT", 3),
    ("TLS", 3), ("UUID", 3), ("StoreKit", 3), ("CloudKit", 3),
    ("CI", 0), ("repo", 0), ("commit", 0), ("merge", 0), ("lint", 0), ("schema", 0),
    ("네이티브", 1),
    ("아키텍처", 2),
    ("상태머신", 3), ("포그라운드", 3),
    ("백그라운드", 0),

    ("디버그", 1), ("터미널에", 1, "터미널"),
    ("웹뷰", 3),
    ("커밋", 2), ("브랜치", 2), ("저장소에", 2, "저장소"), ("디렉터리", 2),
    ("환경변수", 2),
    ("머지", 3), ("리포지토리", 3), ("린트", 3), ("마이그레이션", 3), ("스키마", 3),
    ("엔드포인트", 3), ("프로비저닝", 3), ("빌드 산출물", 3), ("파싱", 3),
    ("스택트레이스", 3),
)


def _사전():
    p = Path(__file__).resolve().parent.parent / "data" / "낱말사전.tsv"
    try:
        rows = [l.split("\t") for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    except Exception:
        return [], {}
    있음 = {w[0] for w in WORDS} | set(SEOLMYEONG)
    더할, 풀이 = [], {}
    for c in rows:
        if len(c) < 2 or c[1] not in ("나", "라") or c[0] in 있음:
            continue
        더할.append((c[0], 0))
        if c[1] == "나" and len(c) > 2 and c[2] and not c[2].startswith("→"):
            풀이[c[0]] = c[2]
    return 더할, 풀이


_더할, _풀이 = _사전()
WORDS = WORDS + tuple(_더할)
SEOLMYEONG.update(_풀이)
쓰지않음 = {c.split("\t")[0] for c in (Path(__file__).resolve().parent.parent / "data" / "낱말사전.tsv").read_text(encoding="utf-8").splitlines()
           if not c.startswith("#") and "\t라" in c} if (Path(__file__).resolve().parent.parent / "data" / "낱말사전.tsv").is_file() else set()


def _alt(words):
    """정규식 묶음을 만든다. ⛔ **긴 것부터** — 「CI/CD」가 「CI」로 먼저 잡히면 뒤가 남는다."""
    return "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))


_EN = [w[0] for w in WORDS if re.match(r"^[A-Za-z]", w[0])]
_KO = [w[0] for w in WORDS if not re.match(r"^[A-Za-z]", w[0])]
JARGON_EN = r"\b(" + _alt(_EN) + r")\b"
JARGON_KO = r"(?<![가-힣])(" + _alt(_KO) + r")"
try:
    _가 = [l.split("\t")[0] for l in (Path(__file__).resolve().parent.parent / "data" / "낱말사전.tsv").read_text(encoding="utf-8").splitlines()
          if not l.startswith("#") and "\t가" in l]
except Exception:
    _가 = []
_조각 = []
for _w in sorted(_KO, key=len, reverse=True):
    _뒤 = [g[len(_w):] for g in _가 if g.startswith(_w) and g != _w]
    _조각.append(re.escape(_w) + ("(?!" + "|".join(re.escape(x) for x in _뒤) + ")" if _뒤 else ""))
JARGON_KO = r"(?<![가-힣])(" + "|".join(_조각) + r")"

SKIP_MARK = "RULE-0: 낱말 목록"


def _strip_comments(line: str, kind: str) -> str:
    """주석을 지운다 — 사고 기록이 옛 문장을 인용한다."""
    if kind in ("py", "sh"):
        s = line.lstrip()
        if s.startswith("#"):
            return ""
        return re.sub(r"\s#.*$", "", line)
    if kind == "md":
        s = line.lstrip()
        if s.startswith(("⛔", ">", "|", "```")) or "RULE-0" in line:
            return ""
        return line
    if kind == "html":
        return re.sub(r"<!--.*?-->", "", line)
    return line


BROKEN_PROMISE = (
    (r"하루\s*[0-9]+\s*분", "「무엇을 확인했는지」로 바꿉니다 — 분으로 팔지 않습니다"),
    (r"24\s*시간\s*(일하는|내내|쉬지)", "「쉬지 않는다」는 약속은 지킬 수 없습니다"),
    (r"[0-9]+\s*배\s*(빠르|빨리|빠른)", "「N배」는 분모가 없습니다 — 「안 했으면 어떻게 될 뻔했나」로"),
    (r"자동으로\s*(다|전부|모두)\s*(됩니다|해|처리)", "다 되지 않습니다 — 직접 정하실 것이 남습니다"),
    (r"(며칠|[0-9]+\s*일)\s*(이면|만에|안에)\s*(끝|완성|출시)", "날짜는 «기다리는 날»에만 씁니다(발표된 값)"),
    (r"순식간|금방|곧\s*됩니다", "측정이 아닙니다 — 「지금 어디쯤인가」로 말합니다"),
    (r"(남이|다른 (사람|분)|먼저 (한|겪은)).{0,12}(겪은|시행착오|실수).{0,16}(막아|막습니다|예방)",
     "아직 사실이 아닙니다 — 기여물이 0건입니다(기여.md 못 ⑥). "
     "해제 조건: 서로 다른 3사람. 지금은 「저희가 저희 앱 만들며 멈춘 자리」로 씁니다"),
)
GLOSS = re.compile(r"(이)?라고 부릅니다")


def _설명붙었나(text: str, word: str) -> bool:
    """그 낱말 **바로 뒤**에 괄호 설명이 붙어 있나. ⛔ 다른 자리의 괄호는 안 센다."""
    i = text.find(word)
    if i < 0:
        return False
    뒤 = text[i + len(word):]
    m = re.match(r"\s*[(（]([^)）]{4,})[)）]", 뒤)
    return bool(m)
TAUGHT = []


def _onboarding_known() -> set:
    """온보딩에서 **안다고 체크하신** 낱말 (`아는낱말` 줄, 띄어쓰기로 나뉜다).
    ⛔ 이건 세지 않는다 — **한 번 안다고 하셨으면 아는 것**이다. 세는 것은 «쓰기 시작한 것»뿐이다."""
    try:
        home = os.environ.get("NIGHTFLIGHT_HOME") or str(pathlib.Path.home() / ".nightflight")
        f = pathlib.Path(home) / "사람.tsv"
        if not f.exists():
            return set()
        out = set()
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            c = line.split("\t")
            if len(c) >= 3 and c[1] == "아는낱말":
                out.update(w for w in c[2].split() if w)
        return out
    except Exception:
        return set()


def 올라간낱말() -> set:
    """대표님이 «먼저 쓰신» 낱말 — 적응형 사전이 올려 둔 것.

    🔴 **이 연결이 빠져 있었다**(2026-10-08 발견). `word_rise.sh` 가 올림을
      사람 기록에 적기만 하고, 이 검사는 그걸 «안 읽었다» — 올려도 계속 울렸다.
      실제로 「Xcode」가 2026-10-05 에 올라가 있었는데 아무 데도 안 쓰였다.
    ⭐ 설계(design/여정.md §적응형)는 「먼저 쓰면 조용히 올린다」이다.
      올린 다음 조용해지지 않으면 올린 것이 아니다.
    """
    import os
    home = os.environ.get("NIGHTFLIGHT_HOME") or os.path.expanduser("~/.nightflight")
    try:
        f = pathlib.Path(home) / "사람.tsv"
        if not f.exists():
            return set()
        import collections as _c
        본것 = _c.Counter()
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            c = line.split("\t")
            if len(c) >= 3 and c[1] == "낱말올림":
                본것[c[2].strip()] += 1
        return {w for w, n in 본것.items() if n >= 2}
    except Exception:
        return set()


RAISED = 올라간낱말()
_ONBOARD = _onboarding_known()
_MYWORDS = 내앱말()


def _hits(text: str, around: str = ""):
    out = []
    for pat, instead in BROKEN_PROMISE:
        m = re.search(pat, text)
        if m:
            out.append(f"약속을 어기는 말「{m.group(0)}」 → {instead}")
    for name, pat in (("명령", CMDS), ("경로·확장자", PATHS),
                      ("영문 용어", JARGON_EN), ("개발 낱말", JARGON_KO)):
        m = re.search(pat, text)
        if m and name in ("영문 용어", "개발 낱말"):
            word = m.group(0)
            if word in RAISED or word in _ONBOARD or word in _MYWORDS:
                continue
            if _설명붙었나(text, word):
                TAUGHT.append(word)
                continue
            if GLOSS.search(text) or re.search(r"아는말인가\s+" + re.escape(word),
                                               around or ""):
                TAUGHT.append(word)
                continue
        if m:
            out.append(f"{name}「{m.group(0).strip()}」")
    return out


def scan_ledger_calls(root: Path):
    """ledger.sh 를 부르는 곳의 «사용자 문구» 인자.

    ⭐ **모델 통로는 여기서도 예외다** (2026-10-12). `scan_prints` 주석이 이 병을
       이미 적어 뒀다 — 「그 예외가 거기만 적혀 있어 이 검사와 어긋나 있었다」.
       🔴 **같은 일이 이 함수에 또 있었다**: 시작 훅이 모델에게 「`ledger.sh 표준목록`」을
       알려 주는데 이 검사가 3곳을 물었다. 모델은 그 명령을 «그대로» 알아야 한다 —
       풀어 쓰면 못 돌린다.
    ⛔ 표지 규칙·세는 자리는 `scan_prints` 와 **같은 것을 쓴다**(`MODEL_ONLY`) —
       두 곳에 두면 한쪽이 낡는다(우리 표준: 같은 것을 세는 자리는 하나만 둔다).
    """
    bad = []
    for f in list(root.rglob("*.py")) + list(root.rglob("*.sh")):
        if ".git" in f.parts or "tests" in f.parts or 우리링크(f):
            continue
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        inside = False
        for i, raw in enumerate(lines, 1):
            kind = "py" if f.suffix == ".py" else "sh"
            line = _strip_comments(raw, kind)
            if not line.strip():
                continue
            if re.search(r"ledger\.sh|_led|LEDGER", line) and re.search(r"못함|됐다|결정|전제", line):
                inside = True
            if not inside:
                continue
            if re.search(r"RULE-0 모델만:\s*(\S.*)$", raw) and "re.search" not in raw:
                MODEL_ONLY.append((f, i))
                continue
            for q in re.findall(r'"([^"]{8,})"', line):
                if len(re.findall(r"[가-힣]", q)) < 4:
                    continue
                h = _hits(q)
                if h:
                    bad.append((f, i, q[:70], h))
            if line.rstrip().endswith(("]", ")", ";")):
                inside = False
    return bad


def scan_tables(root: Path):
    """🔴 **표의 문구도 사용자에게 간다** (2026-10-08 에 실제로 샜다).

    `data/기능.tsv` 의 「바로 말하는 것」이 조종석과 「묶임」 화면에 그대로 찍히는데
    이 검사가 표를 안 보고 있었다 — 「시뮬레이터로는 확인이 안 돼」가 그대로 나갔다.
    ⛔ 칸 번호를 여기 적지 않는다. 표가 머리글에 `RULE-0: 사용자 문구 칸 = N` 으로 밝힌다 —
       검사 쪽에 목록을 두면 표가 늘 때 한 곳이 낡는다(이 저장소가 여러 번 치른 값).
    ⚠️ 표지가 없는 표는 **안 본다.** 그 수를 세어 말한다 — 0 을 「안전」으로 찍지 않는다.
    """
    bad, skipped, nouser = [], [], []
    d = root / "data"
    if not d.is_dir():
        return bad, skipped, nouser
    for f in sorted(d.glob("*.tsv")):
        head = "\n".join(f.read_text(encoding="utf-8").splitlines()[:30])
        m = re.search(r"RULE-0:\s*사용자 문구 칸\s*=\s*(\d+(?:\s*,\s*\d+)*)", head)
        if not m:
            skipped.append(f.name)
            continue
        nums = [int(x) for x in re.split(r"\s*,\s*", m.group(1))]
        if nums == [0]:
            nouser.append(f.name)
            continue
        if 0 in nums:
            skipped.append(f.name)
            continue
        cols = [n - 1 for n in nums]
        for i, raw in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if raw.startswith("#") or "\t" not in raw:
                continue
            cells = raw.split("\t")
            for col in cols:
                if col >= len(cells):
                    continue
                t = cells[col]
                if not re.search(r"[가-힣]", t):
                    continue
                h = _hits(t)
                if h:
                    bad.append((f, i, t.strip()[:70], h))
    return bad, skipped, nouser


def scan_screen(root: Path):
    """조종석 화면에 박힌 문자열."""
    bad = []
    f = root / "board" / "cockpit.html"
    if not f.exists():
        return bad
    txt = f.read_text(encoding="utf-8")
    for i, raw in enumerate(txt.splitlines(), 1):
        line = _strip_comments(raw, "html")
        for t in re.findall(r">([^<>{}]{6,})<", line):
            if not re.search(r"[가-힣]", t):
                continue
            h = _hits(t)
            if h:
                bad.append((f, i, t.strip()[:70], h))
    return bad


def scan_user_speech(root: Path):
    """⭐ 설계 문서 «안»의 사용자 말풍선만 본다 — `「…」` 로 묶인 줄.

    카탈로그는 모델이 읽는 지시라 개발 낱말이 정당하게 들어 있다(04-개발-모듈 등).
    그런데 그 안의 **「…」 는 사용자가 그대로 읽는 말**이다. 거기만 본다.
    """
    bad = []
    d = root.parent / "nightflight-server"
    if not d.exists():
        return bad
    for f in sorted(list(d.glob("catalog/*.md")) + list(d.glob("explain/*.md"))):
        lines = f.read_text(encoding="utf-8").splitlines()
        if any(SKIP_MARK in l for l in lines[:20]):
            continue
        skip_next_table = False
        for i, raw in enumerate(lines, 1):
            if SKIP_MARK in raw:
                skip_next_table = True
                continue
            if skip_next_table:
                if raw.strip().startswith("|"):
                    continue
                if raw.strip():
                    skip_next_table = False
            if raw.lstrip().startswith("⛔") or "RULE-0" in raw:
                continue
            for q in re.findall(r"「([^」]{8,})」", raw):
                if len(re.findall(r"[가-힣]", q)) < 4:
                    continue
                h = _hits(q)
                if h:
                    bad.append((f, i, q[:70], h))
    return bad




MODEL_ONLY = []


def scan_echo(root: Path):
    """⭐ `bin/`·`tools/` 의 `echo`·`print` — 화면에 «직접» 찍히는 글이다.

    🔴 2026-10-03 레드팀이 찾은 구멍: 이 검사가 ①기록 호출 인자 ②조종석 화면
       ③설계 문서의 말풍선만 봤다. **그래서 설치 스크립트가 셸 명령과 개인 볼트 경로를
       찍는 것을 «구조적으로 못 봤다».** RULE-0 이 「문서로만 두면 안 지켜진다 —
       이 문서가 그 증거다」라고 적어 둔 바로 그 자리에 구멍이 남아 있었다.
    ⛔ 한글 4자 이상인 줄만 본다 — 코드·변수를 사용자 문구로 세지 않는다(같은 오탐 회피).
       ⚠️ **그래서 영문만 있는 줄은 못 본다** — `Xcode → Edit Scheme → …` 같은 줄은
          사용자 문구인데 통과한다. 0 이 「전부 안전」이 아닌 이유 하나가 이것이다.

    ⭐ **모델 통로는 예외다** (2026-10-04). `check_touched.sh` 가 통로를 둘로 갈라 뒀고
       (`systemMessage`=사람 / `additionalContext`=모델) **모델 쪽은 개발 용어가 정당하다.**
       그 예외가 거기만 적혀 있어 이 검사와 어긋나 있었다 — 이제 RULE-0.md 에 적고
       여기서 알아본다.
    ⛔ **선언이 필요하다**: 그 줄에 `RULE-0 모델만:<이유>` 를 적어야 넘어간다.
       이유 없이 표지만 달면 그대로 걸린다 — 표지가 «조용한 면제»가 되면 안 된다.
    ⛔ 그리고 **몇 줄이 그 표지를 달고 있는지 세어 찍는다.** 안 보이면 늘어난다.
    """
    bad = []
    for f in sorted(x for d in ("bin", "tools") for x in (root / d).rglob("*")
                    if x.is_file() and x.suffix in (".py", ".sh") and not 우리링크(x)):
        kind = "py" if f.suffix == ".py" else "sh"
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, raw in enumerate(lines, 1):
            line = _strip_comments(raw, kind)
            if not re.search(r'\b(echo|print)\b', line):
                continue
            if re.search(r"RULE-0 모델만:\s*(\S.*)$", raw):
                MODEL_ONLY.append((f, i))
                continue
            around = "\n".join(lines[max(0, i - 7):i])
            for q in re.findall(r'"([^"]{8,})"', line) + re.findall(r"'([^']{8,})'", line):
                if len(re.findall(r"[가-힣]", q)) < 4:
                    continue
                h = _hits(q, around)
                if h:
                    bad.append((f, i, q[:70], h))
    return bad


def check_one(text: str) -> int:
    """⭐ **문구 하나만 본다** — 실행 중에 쓰이는 말을 그 자리에서 거른다 (2026-10-04).

    왜 생겼나: 결정 카드 ③번 칸이 「개발지식 없이 답하실 수 있는 질문인지
    **확인했습니다**」라고만 적고 있었다 — 검사했다고 «말할» 뿐 증거가 없었다.
    ⭐ ③의 증거는 **그 칸의 문장 자체**다. 개발 낱말 없이 쓸 수 있으면 통과한 것이고,
       못 쓰면 그 질문은 아직 여쭐 준비가 안 된 것이다.
    ⛔ 낱말 목록을 복사하지 않는다 — 두 곳에 있으면 한 곳이 반드시 낡는다.
       그래서 같은 `_hits()` 를 쓴다.
    """
    hits = _hits(text)
    if not hits:
        return 0
    print("  ⛔ 이 문장에 개발 용어가 있습니다:", file=sys.stderr)
    print(f"     「{text}」", file=sys.stderr)
    print(f"     → {' · '.join(hits)}", file=sys.stderr)
    print("     대체어를 찾지 말고 «지웁니다» — 사용자는 비개발자입니다(규칙 0).", file=sys.stderr)
    return 1


ASK_TIERS = (1, 2)


def 도구가쓰는낱말() -> set:
    """도구가 화면에서 `아는말인가` 로 실제로 묻는 낱말. ⛔ 목록을 손으로 두지 않는다."""
    import subprocess
    here = Path(__file__).resolve().parent.parent
    out = set()
    for d in ("bin", "tools"):
        p = here / d
        if not p.is_dir():
            continue
        try:
            r = subprocess.run(["grep", "-rhoEI", "아는말인가 [가-힣A-Za-z]+", str(p)],
                               capture_output=True, text=True, timeout=10)
            for line in r.stdout.splitlines():
                w = line.replace("아는말인가 ", "").strip()
                if w:
                    out.add(w)
        except Exception:
            pass
    return out


def _ask_list():
    """물어볼 낱말. ⛔ 무작위가 아니다 — 같은 사람에게 두 번 물으면 같아야 한다.

    ⛔ **단마다 영문·한글을 번갈아 뽑는다.** 표 순서대로 채우면 영문이 몫을 다 먹고
       16개가 거의 다 영문이 된다 — 그러면 **영어 시험처럼 읽히고**, 대표님이 실제로
       만나는 말(커밋·브랜치·마이그레이션)이 빠진다. 2026-10-04 에 실제로 그렇게 나왔다.
    """
    def show(w):
        return w[2] if len(w) > 2 else w[0]
    used = 도구가쓰는낱말()
    out = []
    for tier in ASK_TIERS:
        en = [show(w) for w in WORDS if w[1] == tier and re.match(r"^[A-Za-z]", w[0])]
        ko = [show(w) for w in WORDS if w[1] == tier and not re.match(r"^[A-Za-z]", w[0])]
        while en or ko:
            if en: out.append(en.pop(0))
            if ko: out.append(ko.pop(0))
    for w in WORDS:
        if w[1] in ASK_TIERS or w[1] == 0:
            continue
        if w[0] in used and show(w) not in out:
            out.append(show(w))
    return out


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--문구":
        return check_one(" ".join(sys.argv[2:]))
    if len(sys.argv) > 1 and sys.argv[1] == "--낱말":
        print("\n".join(_ask_list()))
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "--낱말전부":
        for w in WORDS:
            print(f"{w[0]}\t{w[2] if len(w) > 2 else w[0]}")
        return 0
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    _tbad, _tskip, _tnouser = scan_tables(root)
    groups = [("기록의 사용자 문구", scan_ledger_calls(root)),
              ("화면에 찍는 글(echo·print)", scan_echo(root)),
              ("조종석 화면", scan_screen(root)),
              ("표의 사용자 문구", _tbad),
              ("설명·카탈로그 안의 «사용자 말풍선»", scan_user_speech(root))]
    total = sum(len(g[1]) for g in groups)
    def _못_쟀다를_말한다():
        print("  ⚠️ 이 검사는 «직접 닿는 네 자리»만 본다 — 0 이 「전부 안전」은 아니다.")
        if _tskip:
            print(f"  ⚠️ 표 {len(_tskip)}개는 **안 봤다** — 사용자 문구 칸을 안 밝힌 표다: "
                  + " · ".join(_tskip))
        if _tnouser:
            print(f"  · 표 {len(_tnouser)}개는 「사용자에게 보이는 칸이 **없다**」고 밝혔다: "
                  + " · ".join(_tnouser))
        if TAUGHT:
            u = sorted(set(TAUGHT))
            print(f"  ⭐ 「한 번 풀고 쓴」 낱말 {len(u)}개는 통과시켰다 — " + " · ".join(u))
            print("     (규칙 0 ②: 피하지 않고 풀어 쓴다 · ① 셸 명령·경로는 그대로 금지다)")
        if MODEL_ONLY:
            print(f"  ⚠️ 「모델만」으로 선언된 줄 {len(MODEL_ONLY)}곳은 세지 않았다 —")
            print("     " + " · ".join(f"{f.name}:{i}" for f, i in MODEL_ONLY))

    print(f"=== 규칙 0 — 사용자에게 보이는 문구 · 손볼 곳 {total}곳 ===")
    if not total:
        print("\n  ✅ 개발 용어·명령·경로가 사용자 문구에 없다.")
        _못_쟀다를_말한다()
        return 0
    for name, bad in groups:
        if not bad:
            continue
        print(f"\n  🔴 {name} — {len(bad)}곳")
        for f, i, txt, h in bad[:12]:
            try:
                rel = f.relative_to(root)
            except ValueError:
                rel = f
            print(f"    {rel}:{i}")
            print(f"      「{txt}」")
            print(f"      → {' · '.join(h)}")
        if len(bad) > 12:
            print(f"    … {len(bad) - 12}곳 더")
    print("\n  ⛔ 사용자는 비개발자다 — RULE-0.md. 대체어를 찾지 말고 «지운다».")
    print()
    _못_쟀다를_말한다()
    return 1


if __name__ == "__main__":
    sys.exit(main())
