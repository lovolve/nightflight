#!/usr/bin/env python3
"""조종석이 읽을 **칸 파일들**을 기록에서 만든다 — `ledger.sh 조종석준비` 가 부른다.

⭐ 받는 것은 **환경변수**뿐이다(선 글은 안 읽는다). 만드는 자리는 `bin/ledger.sh` 다:
  · `STATE` — 기록 파일(`ledger.tsv`) · `OUT` — 칸 파일을 쓸 폴더(`<기록폴더>/board`)
  · `PERSON`·`NF_PERSONFILE` — 사람 자리 · `NF_TRACE` — 처방이 내려온 흔적
  · `UNVERIFIED_TOKENS` — 「확인 안 됨」 표지 한 줄(⛔ 여기에 목록을 다시 적지 않는다)
  · `NF_KEYLINE` — 열쇠 안내 글자(주인은 `project-root.sh` 의 `nf_keyline()` 이다)
  · `NF_BRAIN_SET` — 서버 자리가 다 있나 · `TOOLS` — 도구 폴더(설명을 거기서 읽는다)
⭐ 찍는 것은 사람이 읽는 몇 줄과, `OUT` 폴더의 칸 파일들이다.
⛔ **죽으면 끝값이 0 이 아니다** — 부르는 쪽이 그것을 보고 「만들지 못했습니다」라고 말한다.
  🔴 전에는 그 자리에서 상태를 안 봐서, 계산이 통째로 죽은 것을 오래 몰랐다(2026-09 실측).

🔴 **왜 파일로 빼냈나** (2026-10-25, ):
   전에는 이 943줄이 `bin/ledger.sh` 안의 헤러독이었다. 그 셸 파일이 **3,341줄**이었고
   그중 **1,124줄이 파이썬**이었다(실측).
   ⛔ 헤러독 안에는 **아무 도구도 닿지 않는다** — 린터·형식 검사·시험이 다 비껴간다.
   ⛔ 그리고 셸이 그 토막을 **한 줄로 묶어** 들고 있으므로, 어디서 틀렸는지도 셸 줄 번호로만
     나온다. 3,341줄 파일의 2,500번째 줄이라고 하면 사람이 찾지 못한다.
   ⭐ 파일로 빼면 그 뒤로는 **도구가 대신 잡는다.**
⛔ **`-I` 로 부른다.** 그래야 받는 분 폴더에 `json.py` 가 심겨 있어도 파이썬의 것을 읽는다.
"""
import json, os, re, sys

_UNV = os.environ["UNVERIFIED_TOKENS"].split()
def _unverified(why):
    low = (why or "").replace(" ", "")
    return any(t in low for t in _UNV)

def _직접정함(why):
    w = why or ""
    return bool(re.search(r"「[^」]+」", w)) or any(t in w for t in ("대표님", "창업자", "사용자"))


rows = []
with open(os.environ["STATE"], encoding="utf-8", errors="replace") as f:
    for line in f:
        c = line.rstrip("\n").split("\t")
        if len(c) >= 5:
            if c[1] == "막음" and len(c) == 5: c = c[:4] + ["", c[4]]
            rows.append((c + ["", "", ""])[:7])

NINE = ["진단","기획","검증","설계","개발","확인","출시","수정","출시후"]
SMAP = {}
_mp = os.path.join(os.path.dirname(os.environ["STATE"]), "stage-map.tsv")
if os.path.exists(_mp):
    for line in open(_mp, encoding="utf-8"):
        c = line.rstrip("\n").split("\t")
        if len(c) == 2 and c[1].isdigit(): SMAP[c[0]] = int(c[1])

broken = {}
for d, k, what, why, pre, topic, bound in rows:
    if k == "전제바뀜": broken[what] = pre
    elif k == "전제해소":
        for _kk in [x for x in list(broken) if what in x or x in what]:
            del broken[_kk]

moved = {}
for d, k, what, why, pre, topic, bound in rows:
    if k == "단계옮김": moved[what] = why
def restage(kind, what, lbl):
    if kind not in ("남은것", "됐다"): return lbl
    for key, to in moved.items():
        if key in what: return to
    return lbl

def label_to_idx(lbl, smap):
    if lbl in smap: return smap[lbl]
    _n = (lbl or "").strip().replace(" ", "")
    if _n in NINE: return NINE.index(_n)
    m = re.match(r"\s*(\d)\s*[-. ]\s*(\S+)", lbl or "")
    if m and 0 <= int(m.group(1)) < 9 and NINE[int(m.group(1))] == m.group(2):
        return int(m.group(1))
    return None

decisions, cur_lbl = [], ""
per = {}
loose = {"decisions": [], "blocks": [], "open": [], "done": [], "labels": []}
def bucket(lbl, smap):
    i = label_to_idx(lbl, smap)
    if i is None: return loose, None
    per.setdefault(i, {"decisions": [], "blocks": [], "open": [], "done": [], "labels": []})
    return per[i], i

done_keys = [r[2] for r in rows if r[1] == "끝냄"]
fixed_keys = [r[2] for r in rows if r[1] == "풀림"]
gone_keys = [r[2] for r in rows if r[1] == "없어짐"]
undone_keys = [r[2] for r in rows if r[1] == "되돌림"]
stuck = []
_LBDIR = os.path.dirname(os.environ["STATE"])
def _lbrows(n):
    q = os.path.join(_LBDIR, n)
    if not os.path.exists(q):
        return []
    return [l.rstrip("\n").split("\t") for l in open(q, encoding="utf-8") if "\t" in l and not l.startswith("#")]
_ITEM = {c[0]: ((c[1] or None) if len(c) > 1 else None, (c[2] or None) if len(c) > 2 else None) for c in _lbrows("item-labels.tsv")}
_FEED = {c[0]: (c[1], c[2], (c[3] or None) if len(c) > 3 else None) for c in _lbrows("feed-labels.tsv") if len(c) >= 3}
for d, k, what, why, pre, topic, bound in rows:
    if k == "단계":
        cur_lbl = what
        b, i = bucket(cur_lbl, SMAP)
        if what not in b["labels"]: b["labels"].append(what)
    elif k == "결정":
        if any(kk in what or what in kk for kk in undone_keys): continue
        hit = next((v for kk, v in broken.items() if kk in what), None)
        it = {"at": d, "what": what, "premise": pre, "broken": hit or "", "topic": topic,
              "bound": bound,
              "직접": _직접정함(why)}
        if what in _FEED:
            it["항목"], it["값"], it["조건"] = _FEED[what]
        decisions.append(it)
        bucket(cur_lbl, SMAP)[0]["decisions"].append(it)
    elif k == "됐다":
        ok = not _unverified(why)
        import hashlib as _h
        _id = _h.sha1(f"{d}\t{what}".encode("utf-8")).hexdigest()[:12]
        bucket(restage("됐다", what, pre or cur_lbl), SMAP)[0]["done"].append(
            {"id": _id, "at": d, "what": what, "how": why, "ok": ok, "topic": topic})
    elif k == "막음":
        bucket(cur_lbl, SMAP)[0]["blocks"].append(
            {"what": what, "why": why, "ifNot": pre, "key": topic})
    elif k == "남은것":
        if not any(kk in what for kk in done_keys + gone_keys):
            bucket(restage("남은것", what, why or cur_lbl), SMAP)[0]["open"].append(
                {"what": what, "key": pre, "topic": topic,
                 "이름표": _ITEM.get(what, (None, None))[0], "종류": _ITEM.get(what, (None, None))[1]})
    elif k == "못함":
        _머 = what.split(" — ")[0].replace(" ", "")[:14]
        _뒤됨 = any(r[1] == "됐다" and r[0][:10] >= d[:10] and r[2].split(" — ")[0].replace(" ", "")[:14] == _머 for r in rows if len(r) > 2)
        if not _뒤됨 and not any(kk in what for kk in fixed_keys + gone_keys):
            stuck.append({"what": what, "lack": why, "todo": pre})

stage_label = next((r[2] for r in reversed(rows) if r[1] == "단계"), "")
stage = label_to_idx(stage_label, SMAP)

blocks = [r for r in rows if r[1] == "막음"]
handled, card = [], None
for d, k, what, why, pre, topic, bound in rows:
    if k in ("결정", "끝냄"): card = None
    if k == "카드":
        handled = [x for x in (pre or "").split("\x1e") if x.strip()]
        card = {"what": what, "why": why}
    elif k == "막음": handled.append(what)
if card: card["handled"] = handled[-6:]

_fl = {}
_flp = os.path.join(os.path.dirname(os.environ["STATE"]), "feed-labels.tsv")
if os.path.exists(_flp):
    for _l in open(_flp, encoding="utf-8"):
        _c = _l.rstrip("\n").split("\t")
        if len(_c) >= 3 and not _c[0].startswith("#"):
            _fl[_c[0]] = (_c[1], _c[2])
feed = []
for d, k, what, why, pre, topic, bound in rows[-80:]:
    if k in ("막음", "결정", "단계", "전제바뀜", "되돌림", "됐다", "못함"):
        it = {"at": d, "kind": k, "text": what}
        if what in _fl:
            it["항목"], it["값"] = _fl[what]
        if k == "결정" and bound:
            it["비용"] = bound
        if k == "막음":
            _same = [r[0] for r in rows if r[1] == "막음" and r[2] == what]
            it["횟수"], it["처음"] = len(_same), min(_same)
        if k == "됐다":
            if not _unverified(why):
                continue
            it["text"] = what + " — " + why
        feed.append(it)
feed.reverse()

w = lambda n, o: open(os.path.join(os.environ["OUT"], n), "w", encoding="utf-8").write(
    json.dumps(o, ensure_ascii=False, indent=1))
import datetime

RG = os.path.join(os.path.dirname(os.environ["STATE"]), "repeat-guard.tsv")
repeat = None
if os.path.exists(RG):
    from collections import Counter
    rows_rg = [l.rstrip("\n").split("\t") for l in open(RG, encoding="utf-8") if "\t" in l]
    if rows_rg:
        last_session = rows_rg[-1][0]
        c = Counter(r[1] for r in rows_rg if r[0] == last_session)
        if c:
            f, n = c.most_common(1)[0]
            if n >= 3:
                repeat = {"file": os.path.basename(f), "count": n,
                          "worst": max(v for v in Counter(r[1] for r in rows_rg).values())}
                _fc = Counter(r[2] for r in rows_rg if r[0] == last_session and r[1] == f and len(r) > 2 and r[2])
                if _fc:
                    repeat["기능"] = _fc.most_common(1)[0][0]

BOUND_KINDS = ["돈", "시간", "법", "못되돌림"]
bound_by = {kk: [] for kk in BOUND_KINDS}
bound_unsaid = 0
for _it in decisions:
    bt = (_it.get("bound") or "").strip()
    if not bt:
        bound_unsaid += 1
        continue
    for kk in BOUND_KINDS:
        if bt.startswith(kk):
            bound_by[kk].append({"what": _it["what"], "detail": bt[len(kk):].lstrip(": ").strip()})
            break
w("bound.json", {"by": bound_by, "unsaid": bound_unsaid,
                 "total": sum(len(v) for v in bound_by.values())})

import datetime as _dt
_TODAY = _dt.date.today()
def _days(a, b=None):
    try: d0 = _dt.date.fromisoformat(a)
    except Exception: return None
    try: d1 = _dt.date.fromisoformat(b) if b else _TODAY
    except Exception: return None
    return (d1 - d0).days

_prows = list(rows)
_pp = os.environ.get("PERSON")
if _pp and os.path.exists(_pp):
    for line in open(_pp, encoding="utf-8"):
        c = line.rstrip("\n").split("\t")
        if len(c) >= 3: _prows.append((c + ["", "", "", ""])[:7])
_asked_row = next((r for r in _prows if r[1] == "아는낱말"), None)
_risen = [{"word": r[2], "at": r[0]} for r in _prows if r[1] == "낱말올림"]
_mon = _TODAY.strftime("%Y-%m") if "_TODAY" in dir() else ""
_dict = {"built": bool(_asked_row),
         "why": "" if _asked_row else "아직 안 물어봤습니다 — 「아는 낱말 체크」가 먼저입니다",
         "risen": _risen,
         "thisMonth": sum(1 for x in _risen if x["at"][:7] == _TODAY.strftime("%Y-%m"))}

piled_blocks, blocks_nowhy, blocks_noifnot = [], 0, 0
for r in rows:
    if r[1] != "막음": continue
    if not r[3]: blocks_nowhy += 1; continue
    if not r[4]: blocks_noifnot += 1
    piled_blocks.append({"at": r[0], "what": r[2], "why": r[3], "ifNot": r[4] or ""})

reverted = [{"at": r[0], "what": r[2], "when": r[3], "premise": r[4]}
            for r in rows if r[1] == "되돌림"]

_end = {r[2]: r[0] for r in rows if r[1] == "기다림끝"}
_asked = {r[2]: r[0] for r in rows if r[1] == "문의권함"}
def _hit(dic, what):
    return next((v for kk, v in dic.items() if kk in what or what in kk), None)
waiting, waited = [], []
for r in rows:
    if r[1] != "기다림": continue
    what, usual, mx = r[2], r[3], r[4]
    mxn = int(mx) if str(mx).isdigit() else None
    done_at = _hit(_end, what)
    if done_at:
        waited.append({"what": what, "from": r[0], "to": done_at,
                       "days": _days(r[0], done_at), "usual": usual, "max": mxn})
    else:
        n = _days(r[0])
        waiting.append({"what": what, "from": r[0], "days": n, "usual": usual, "max": mxn,
                        "over": bool(n is not None and mxn is not None and n > mxn),
                        "askedAt": _hit(_asked, what)})

_seq = [(r[0], r[2]) for r in rows if r[1] == "단계"]
_span = {}
for _i, (_d0, _lbl) in enumerate(_seq):
    _d1 = _seq[_i + 1][0] if _i + 1 < len(_seq) else None
    _n = _days(_d0, _d1)
    _e = _span.setdefault(_lbl, {"label": _lbl, "idx": label_to_idx(_lbl, SMAP),
                                 "days": 0, "visits": 0, "from": _d0, "open": False})
    _e["visits"] += 1
    if _n is not None: _e["days"] += _n
    if _d1 is None: _e["open"] = True
stage_days = sorted(_span.values(), key=lambda x: (x["idx"] is None,
                                                   x["idx"] if x["idx"] is not None else 99))

w("piled.json", {
    "blocks": piled_blocks, "blocksNoWhy": blocks_nowhy, "blocksNoIfNot": blocks_noifnot,
    "decisions": decisions, "reverted": reverted,
    "waiting": waiting, "waited": waited, "stageDays": stage_days,
    "dict": _dict,
})

w("stuck.json", {"items": stuck})

import importlib.util as _ilu


def _plan():
    try:
        _pp = os.path.join(os.environ.get("TOOLS", ""), "plan.py")
        _ps = _ilu.spec_from_file_location("_plan", _pp)
        _pm = _ilu.module_from_spec(_ps); _ps.loader.exec_module(_pm)
        return _pm.compute()
    except Exception as _e:
        return {"있나": False, "못봤다": f"{type(_e).__name__}", "단계": {}}


def _intro():
    out = {}
    try:
        for line in open(os.environ["STATE"], encoding="utf-8", errors="replace"):
            c = line.rstrip("\n").split("\t")
            if len(c) > 3 and c[1] == "제품소개" and c[2] and c[3]:
                out[c[2]] = c[3]
    except Exception:
        pass
    return out


def _validations():
    out = []
    _lbl = {}
    try:
        for line in open(os.path.join(os.path.dirname(os.environ["STATE"]), "item-labels.tsv"), encoding="utf-8"):
            c = line.rstrip("\n").split("\t")
            if len(c) > 1 and not line.startswith("#"):
                _lbl[c[0]] = c[1]
    except Exception:
        pass
    try:
        for line in open(os.environ["STATE"], encoding="utf-8", errors="replace"):
            c = line.rstrip("\n").split("\t")
            if len(c) > 3 and c[1] == "검증":
                out.append({"날": c[0], "결론": c[2], "출처": c[3], "판정": c[4] if len(c) > 4 else "",
                            "틀": c[5] if len(c) > 5 else "", "화면": _lbl.get(c[2], "")})
    except Exception:
        pass
    return out


def _diagnosis():
    import subprocess, plistlib, platform, glob
    out = {}
    def run(*a):
        try:
            return subprocess.run(a, capture_output=True, text=True, timeout=2).stdout.strip()
        except Exception:
            return ""
    v = run("sysctl", "-n", "machdep.cpu.brand_string")
    if v: out["칩"] = v
    v = platform.mac_ver()[0]
    if v: out["운영체제"] = "macOS " + v
    try:
        with open("/Applications/Xcode.app/Contents/version.plist", "rb") as f:
            out["Xcode"] = plistlib.load(f).get("CFBundleShortVersionString", "")
    except Exception:
        pass
    rts = sorted({os.path.basename(x).replace(".simruntime", "")
                  for x in glob.glob("/Library/Developer/CoreSimulator/Volumes/*/Library/Developer/CoreSimulator/Profiles/Runtimes/*.simruntime")})
    if rts: out["시뮬레이터"] = " · ".join(rts)
    v = run("git", "--version")
    if v: out["git"] = v.replace("git version ", "").split(" ")[0]
    try:
        _dk = "/System/Volumes/Data" if os.path.isdir("/System/Volumes/Data") else "/"
        _v = run("df", "-g", _dk).splitlines()[1].split()[3]
        out["디스크 여유"] = "%sGB" % int(_v)
    except Exception:
        pass
    a = {}
    try:
        for line in open(os.environ["STATE"], encoding="utf-8", errors="replace"):
            c = line.rstrip("\n").split("\t")
            if len(c) > 3 and c[1] == "앱설정":
                a[c[2]] = c[3]
    except Exception:
        pass
    if a.get("플랫폼") or a.get("나라"):
        out["어디에 팔 건가"] = " · ".join(x for x in (a.get("플랫폼"), a.get("나라")) if x)
    if a.get("돈받기"): out["돈을 받을 건가"] = a["돈받기"]
    if a.get("만들것"): out["만드는 것의 종류"] = a["만들것"]
    return out


def _진단표채움(표, 값):
    if not isinstance(표, dict) or not 값:
        return 표
    단 = 표.setdefault("단계", {})
    if (단.get("0") or {}).get("기능들"):
        return 표
    def 줄(이름, v):
        return {"이름": 이름, "상태": "완료" if v else "시작 전", "이름표": "", "확인": v or "",
                "출처": "자동 진단", "바뀐날": "", "때": None}
    기 = []
    환경 = [줄(k, 값[k]) for k in ("칩", "운영체제", "디스크 여유", "Xcode", "시뮬레이터", "git") if 값.get(k)]
    if 환경:
        기.append({"기능": "개발 환경 점검", "세부": 환경, "설명": ""})
    질문 = [줄(k, 값.get(k, "")) for k in ("어디에 팔 건가", "돈을 받을 건가", "만드는 것의 종류")]
    기.append({"기능": "제품 질문", "세부": 질문, "설명": ""})
    for f in 기:
        f["수"] = {k: sum(1 for z in f["세부"] if z["상태"] == k) for k in ("시작 전", "진행 중", "완료", "확인 필요", "방법 찾는 중")}
    단["0"] = {"기능들": 기, "세부전체": sum(len(f["세부"]) for f in 기),
              "세부완료": sum(f["수"]["완료"] for f in 기)}
    return 표


def _arch_sections(path):
    try:
        out, cur = [], None
        for l in open(path, encoding="utf-8"):
            l = l.rstrip("\n")
            if l.startswith("## "):
                cur = {"제목": l[3:].strip(), "줄": []}; out.append(cur)
            elif cur is not None and l.strip() and len(cur["줄"]) < 8:
                cur["줄"].append(l.strip().lstrip("-").strip())
        return out[:12]
    except Exception:
        return None


def _arch_struct(path):
    import re as _re
    try:
        secs, cur = [], None
        for l in open(path, encoding="utf-8"):
            l = l.rstrip("\n")
            if l.startswith("## "):
                cur = {"제목": l[3:].strip(), "줄": []}; secs.append(cur)
            elif cur is not None and l.strip().startswith("- "):
                cur["줄"].append(l.strip()[2:].strip())
        def 항목(x):
            m = _re.match(r"\*\*(.+?)\*\*\s*[:：]\s*(.*)", x)
            return (m.group(1).strip(), m.group(2).strip()) if m else (None, x.replace("**", ""))
        부품, 흐름, 묶임 = [], [], []
        for sc in secs:
            if sc["제목"].startswith("부품"):
                for x in sc["줄"]:
                    n, d = 항목(x)
                    if n: 부품.append({"이름": n.split(" — ")[0].strip(), "온이름": n, "설명": d, "칸": []})
            elif sc["제목"].startswith("흐름"):
                for x in sc["줄"]:
                    n, d = 항목(x)
                    if n:
                        단, 곳 = [], []
                        for t in d.split("→"):
                            t = t.strip().rstrip(".")
                            if not t: continue
                            m2 = _re.search(r"\s*\[([^\]]+)\]\s*$", t)
                            단.append(t[:m2.start()].strip() if m2 else t); 곳.append(m2.group(1).strip() if m2 else "")
                        흐름.append({"이름": n, "단계": 단, "단계부품": 곳})
            elif "묶인" in sc["제목"]:
                묶임 = [x.replace("**", "") for x in sc["줄"]]
        for sc in secs:
            if sc["제목"].endswith(" 안"):
                key = sc["제목"][:-2].strip()
                for b in 부품:
                    if key and key in b.get("온이름", b["이름"]):
                        for x in sc["줄"]:
                            n, d = 항목(x)
                            if n: b["칸"].append({"이름": n, "설명": d})
                        break
        for b in 부품: b.pop("온이름", None)
        return {"부품": 부품, "흐름": 흐름, "묶임": 묶임} if (부품 and 흐름) else None
    except Exception:
        return None


def _ignore_detail(_r):
    import subprocess, fnmatch
    try:
        rules = [l.strip() for l in open(os.path.join(_r, ".gitignore"), encoding="utf-8")
                 if l.strip() and not l.strip().startswith("#")]
    except Exception:
        rules = []
    pats = (".env", ".env.*", "*.env", "*.p8", "*.p12", "*.pem", "*.key", "*.keystore", "*.jks",
            "secrets*", "credentials*", "GoogleService-Info.plist", "google-services.json", "service-account*.json")
    skip = {".git", "node_modules", "DerivedData", "build", ".build", "Pods", ".venv", "venv", "dist", ".next"}
    found = []
    for dp, dn, fn in os.walk(_r):
        dn[:] = [d for d in dn if d not in skip]
        if dp[len(_r):].count(os.sep) >= 3:
            dn[:] = []
        for f in fn:
            if any(fnmatch.fnmatch(f, p) for p in pats) and not f.endswith((".example", ".sample", ".template")):
                found.append(os.path.relpath(os.path.join(dp, f), _r))
        if len(found) > 40:
            break
    def git(*a):
        try:
            return subprocess.run(("git", "-C", _r) + a, capture_output=True, text=True, timeout=3)
        except Exception:
            return None
    files = []
    for f in sorted(found)[:40]:
        ign = git("check-ignore", "-q", f); trk = git("ls-files", "--error-unmatch", f)
        keys = []
        if os.path.basename(f).startswith(".env") or f.endswith(".env"):
            try:
                for l in open(os.path.join(_r, f), encoding="utf-8", errors="ignore"):
                    l = l.strip()
                    if l and not l.startswith("#") and "=" in l:
                        keys.append(l.split("=", 1)[0].replace("export ", "").strip())
            except Exception:
                pass
        files.append({"파일": f, "막힘": (ign.returncode == 0) if ign else None,
                      "올라감": (trk.returncode == 0) if trk else None, "키이름": keys[:30]})
    real = None
    out = git("ls-files", "-z", "-o", "-i", "--exclude-standard", "--directory")
    if out is not None and out.returncode == 0:
        cnt, order, one, link = {}, [], {}, {}
        for x in out.stdout.split("\0"):
            if not x or x.startswith(".git/"):
                continue
            top = x if x.endswith("/") else (x.rsplit("/", 1)[0] + "/" if "/" in x else x)
            if top not in cnt:
                cnt[top] = 0; order.append(top); one[top] = x
            cnt[top] += 1
            link[top] = link.get(top, True) and os.path.islink(os.path.join(_r, x.rstrip("/")))
        real = [dict({"이름": (one[k] if cnt[k] == 1 else k), "수": cnt[k]}, **({"연결": True} if link.get(k) else {}))
                for k in sorted(order)][:40]
    return {"규칙": rules[:60], "규칙수": len(rules), "비밀파일": files, "안올린것": real}


def _design_check():
    try:
        _r = os.path.dirname(os.path.dirname(os.path.abspath(os.environ["STATE"])))
        _arch = [x for x in ("ARCHITECTURE.md", "docs/ARCHITECTURE.md", "docs/architecture.md", "docs/구조.md")
                 if os.path.isfile(os.path.join(_r, x))]
        return {"gitignore": os.path.isfile(os.path.join(_r, ".gitignore")), "구조문서": _arch[0] if _arch else None,
                "막는것": _ignore_detail(_r), "구조내용": _arch_sections(os.path.join(_r, _arch[0])) if _arch else None,
                "구조": _arch_struct(os.path.join(_r, _arch[0])) if _arch else None}
    except Exception:
        return {"gitignore": None, "구조문서": None}


try:
    _fp = os.path.join(os.environ.get("TOOLS", ""), "feature_progress.py")
    _sp = _ilu.spec_from_file_location("_fp", _fp)
    _m = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_m)
    _fd = _m.compute()
    _fd["설계표"] = _plan()
    _fd["설계점검"] = _design_check()
    _fd["진단값"] = _diagnosis()
    _fd["설계표"] = _진단표채움(_fd.get("설계표"), _fd["진단값"])
    _fd["검증기록"] = _validations()
    _fd["제품소개"] = _intro()
    w("features.json", _fd)
except Exception as _e:
    w("features.json", {"기능들": [], "못봤다": f"{type(_e).__name__}", "설계표": _plan(), "설계점검": _design_check()})
_appname = ([r[3] for r in rows if r[1] == "앱설정" and r[2] == "앱이름" and len(r) > 3 and r[3].strip()] or [""])[-1]
if not _appname:
    try:
        _fl = os.path.join(os.path.dirname(os.environ.get("STATE", "")), "feed-labels.tsv")
        _원문 = {r[2] for r in rows if r[1] == "결정" and len(r) > 2}
        for _l in open(_fl, encoding="utf-8"):
            _c = _l.rstrip("\n").split("\t")
            if len(_c) > 2 and not _l.startswith("#") and _c[1].strip() == "제품 이름" and _c[0] in _원문 and _c[2].strip():
                _appname = _c[2].split(" (")[0].strip()
    except Exception:
        pass
_folder = os.path.basename(os.path.dirname(os.path.dirname(os.environ["STATE"]))) \
    if os.environ.get("STATE") else ""
_칸없음 = sum(1 for c in rows if len(c) > 1 and c[1] == "끝냄")
_확인방법 = {}
for c in rows:
    if len(c) > 3 and c[1] == "됐다" and c[3].strip():
        for _찾, _이름 in (("변이", "변이"), ("거짓 경보", "거짓 경보"), ("대조", "대조"),
                          ("전수", "빠짐없이"), ("세어", "빠짐없이"),
                          ("재 봤", "재 봄"), ("재니", "재 봄"), ("돌려", "돌려 봄"),
                          ("시험", "시험"), ("검사", "검사"), ("실측", "실측"),
                          ("원문", "원문 확인"), ("눌러", "눌러 봄")):
            if _찾 in c[3]:
                _확인방법[_이름] = _확인방법.get(_이름, 0) + 1
                break
        else:
            _확인방법["분류 못 함"] = _확인방법.get("분류 못 함", 0) + 1

w("now.json", {"stuck": len(stuck), "updatedAt": datetime.datetime.now(datetime.timezone.utc)
                 .isoformat(timespec="seconds").replace("+00:00", "Z"),
               "앱이름": _appname, "폴더": _folder,
               "stage": stage, "stageLabel": stage_label,
               "decisions": len(decisions), "broken": sum(1 for x in decisions if x["broken"]),
               "blocks": len(blocks), "ask": card,
               "done": sum(len(v["done"]) for v in list(per.values()) + [loose]),
               "unverified": sum(1 for v in list(per.values()) + [loose]
                                 for d in v["done"] if not d["ok"]),
               "verified": sum(1 for v in list(per.values()) + [loose]
                               for d in v["done"] if d["ok"]),
               "noVerifyColumn": _칸없음,
               "verifyKinds": _확인방법,
               "repeat": repeat})
w("feed.json", {"items": feed[:60]})

try:
    _rd = os.path.join(os.environ.get("TOOLS", ""), "read_dates.py")
    _rs = _ilu.spec_from_file_location("_rd", _rd)
    _rm = _ilu.module_from_spec(_rs); _rs.loader.exec_module(_rm)
    w("readdates.json", _rm.compute())
except Exception as _e:
    w("readdates.json", {"못쟀다": True, "줄들": [], "안읽은것": [],
                         "가장오래된": None, "요약만": 0, "못봤다": f"{type(_e).__name__}"})

try:
    _st = os.path.join(os.environ.get("TOOLS", ""), "standards.py")
    _ss = _ilu.spec_from_file_location("_st", _st)
    _sm = _ilu.module_from_spec(_ss); _ss.loader.exec_module(_sm)
    w("standards.json", _sm.compute())
except Exception as _e:
    w("standards.json", {"못쟀다": True, "기능별": {}, "출처있음": 0,
                         "출처없음": 0, "모른낱말": [], "못봤다": f"{type(_e).__name__}"})

try:
    _at = os.path.join(os.environ.get("TOOLS", ""), "attempts.py")
    _as = _ilu.spec_from_file_location("_at", _at)
    _am = _ilu.module_from_spec(_as); _as.loader.exec_module(_am)
    w("attempts.json", _am.compute())
except Exception as _e:
    w("attempts.json", {"못쟀다": True, "기능별": {}, "막힌것": 0,
                        "못한것": 0, "모른낱말": [], "못봤다": f"{type(_e).__name__}"})

try:
    _없앤기능 = {x["이름"] for x in ((_plan() or {}).get("없앤것") or []) if x.get("종류") == "기능"}
except Exception:
    _없앤기능 = set()
def _없앤것걷기(d, *자리):
    if not _없앤기능 or not isinstance(d, dict):
        return d
    for k in 자리:
        v = d.get(k)
        if isinstance(v, dict):
            d[k] = {a: (b if not isinstance(b, list) else [r for r in b if not (isinstance(r, dict) and r.get("같이볼쪽") in _없앤기능)])
                    for a, b in v.items() if a not in _없앤기능}
    return d

try:
    _dp = os.path.join(os.environ.get("TOOLS", ""), "dependencies.py")
    _ds = _ilu.spec_from_file_location("_dp", _dp)
    _dm = _ilu.module_from_spec(_ds); _ds.loader.exec_module(_dm)
    w("deps.json", _없앤것걷기(_dm.compute(), "고치는쪽별", "따져본기능"))
except Exception as _e:
    w("deps.json", {"못쟀다": True, "고치는쪽별": {}, "확인된것": 0,
                    "확인안된것": 0, "모른낱말": [], "못봤다": f"{type(_e).__name__}"})

try:
    _sp = os.path.join(os.environ.get("TOOLS", ""), "states.py")
    _ss = _ilu.spec_from_file_location("_sp", _sp)
    _sm = _ilu.module_from_spec(_ss); _ss.loader.exec_module(_sm)
    _st = _sm.compute(os.environ.get("STATE"))
    for _k in ("적힌줄", "걸림수"):
        _st.pop(_k, None)
    w("states.json", _없앤것걷기(_st, "기능별", "기능별본것"))
except Exception as _e:
    w("states.json", {"못쟀다": True, "기능별": {}, "기능별본것": {},
                      "적힌줄": 0, "내판단": 0, "걸림수": 0,
                      "못봤다": f"{type(_e).__name__}"})

try:
    _gp = os.path.join(os.environ.get("TOOLS", ""), "gates.py")
    _gs = _ilu.spec_from_file_location("_gp", _gp)
    _gm = _ilu.module_from_spec(_gs); _gs.loader.exec_module(_gm)
    w("gates.json", _gm.compute(os.environ.get("STATE"), os.environ.get("PERSON")))
except Exception as _e:
    w("gates.json", {"못쟀다": "못봤음", "총": 0, "걸림": [], "안걸림": 0,
                     "모름": [], "두뇌있음": False, "오늘신청": [], "제출뒤": [],
                     "날짜없음": [], "막힘": [], "못봤다": f"{type(_e).__name__}"})
EXP = {}
_tools = os.environ.get("TOOLS", "")
_ed = os.path.join(os.path.dirname(_tools), "explain") if _tools else ""
_srv = os.path.join(os.path.dirname(os.path.dirname(_tools)),
                    "nightflight-server", "explain") if _tools else ""
for base in [os.environ.get("NF_EXPLAIN", ""), _ed, _srv]:
    if base and os.path.isdir(base):
        for f in os.listdir(base):
            if f.endswith(".md"):
                EXP[f[:-3]] = open(os.path.join(base, f), encoding="utf-8").read()
        break
_miss = set()
def attach(items):
    for it in items:
        k = it.get("key")
        if k and k in EXP: it["explain"] = EXP[k]
        elif k: _miss.add(k)
        it.pop("key", None)
for v in list(per.values()) + [loose]:
    attach(v["blocks"]); attach(v["open"])

_open_all = [o for v in list(per.values()) + [loose] for o in v["open"]]
_open_mine = sum(1 for o in _open_all if (o.get("topic") or "") == "절차")
_tr = os.environ.get("NF_TRACE", "")
_rows = []
if _tr and os.path.isfile(_tr):
    for _ln in open(_tr, encoding="utf-8"):
        _c = _ln.rstrip("\n").split("\t")
        if len(_c) >= 4:
            _rows.append({"언제": _c[0], "단계": _c[1], "갈래": _c[2], "결과": _c[3]})
_today = datetime.date.today().isoformat()
_t_rows = [r for r in _rows if r["언제"].startswith(_today)]
_down = [r for r in _t_rows if r["결과"] == "내려옴"]
_검증 = [r for r in rows if len(r) > 4 and r[1] == "검증"]
_설계 = [r for r in rows if len(r) > 4 and r[1] == "설계"]
_갈래 = [r for r in rows if len(r) > 4 and r[1] == "갈래"]
_갈래묶음 = {}
for _r in _갈래:
    _주제 = _r[2].split(" — ")[0]
    _갈래묶음.setdefault(_주제, []).append(
        {"이름": (_r[5] if len(_r) > 5 else ""), "출처": _r[3], "고름": _r[4] == "고름"})
_단확 = {}
for _r in rows:
    if len(_r) > 5 and _r[1] == "단계확인":
        _단확.setdefault(_r[5], []).append({"무엇": _r[2], "상태": _r[4], "비고": _r[3]})
w("bystage.json", {
    **{k: {"있나": True, "줄": v} for k, v in _단확.items()},
    "2": {"있나": bool(_검증),
          "확인됨": [{"무엇": r[2], "근거": r[3], "틀": (r[5] if len(r) > 5 else "")}
                   for r in _검증 if r[4] == "확인됨"],
          "치명적": [{"무엇": r[2], "근거": r[3], "틀": (r[5] if len(r) > 5 else "")}
                   for r in _검증 if r[4] == "치명적"]},
    "3": {"있나": bool(_설계 or _갈래),
          "넣음":   [{"무엇": r[2], "왜": r[3]} for r in _설계 if r[4] == "넣음"],
          "뺌":     [{"무엇": r[2], "왜": r[3]} for r in _설계 if r[4] == "뺌"],
          "다음번": [{"무엇": r[2], "왜": r[3]} for r in _설계 if r[4] == "다음번"],
          "갈래": _갈래묶음},
})

_하는중 = [r for r in rows if len(r) > 2 and r[1] == "하는중"]
_다음 = [r for r in rows if len(r) > 3 and r[1] == "다음"]
_오늘 = datetime.date.today().isoformat()
_마지막 = _하는중[-1] if _하는중 else None
_il = {}
_ilp = os.path.join(os.path.dirname(os.environ["STATE"]), "item-labels.tsv")
if os.path.exists(_ilp):
    for _l in open(_ilp, encoding="utf-8"):
        _c = _l.rstrip("\n").split("\t")
        if len(_c) >= 2 and not _c[0].startswith("#"):
            _il[_c[0]] = _c[1]
w("doing.json", {
    "있나": bool(_마지막),
    "무엇": (_마지막[2] if _마지막 else ""),
    "화면": (_il.get(_마지막[2]) if _마지막 else None),
    "언제": (_마지막[0] if _마지막 else ""),
    "오늘인가": bool(_마지막 and _마지막[0].startswith(_오늘)),
    "다음": ({"무엇": _다음[-1][2], "화면": _il.get(_다음[-1][2]), "왜": _다음[-1][3], "언제": _다음[-1][0]}
             if _다음 else None),
})

w("brain.json", {
    "길섰나": bool(os.environ.get("NF_BRAIN_SET")),
    "사람id있나": bool(os.environ.get("NF_PERSONFILE")
                   and os.path.isfile(os.environ["NF_PERSONFILE"])),
    "한번도안불렀다": not _rows,
    "오늘내려옴": len(_down),
    "오늘못받음": sum(1 for r in _t_rows if r["결과"] in ("못받음", "못읽음")),
    "오늘거절": sum(1 for r in _t_rows if r["결과"].startswith("거절")),
    "오늘없는갈래": sum(1 for r in _t_rows if r["결과"] == "없는갈래"),
    "최근": _rows[-6:][::-1],
})

try:
    import sys as _sys, time as _time
    _sys.path.insert(0, os.environ.get("TOOLS", ""))
    import machine as _mm
    _md = _mm.잰다()
    _md["걸리나"] = _mm.걸리나(_md)
    _md["걸리나짝"] = _mm.걸리나짝(_md)
    _md["잰때"] = _time.time()
except Exception as _e:
    _md = {"못쟀다": type(_e).__name__}
w("machine.json", _md)

try:
    import subprocess as _sp
    _제품 = os.path.dirname(os.path.dirname(os.path.abspath(os.environ["STATE"])))
    _pp = _sp.run([sys.executable, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "플랜자료.py"), _제품],
                  capture_output=True, text=True, timeout=5)
    _plan = json.loads(_pp.stdout) if _pp.returncode == 0 and _pp.stdout.strip() else {"못받음": "끝값 " + str(_pp.returncode)}
except Exception as _e:
    _plan = {"못받음": type(_e).__name__}
w("plan.json", _plan)

w("stages.json", {"per": {str(i): v for i, v in per.items()}, "loose": loose,
                 "open": len(_open_all), "openMine": _open_mine})
_자세히 = os.environ.get("NF_DETAIL") == "1"
if _자세히: print(f"  · 조종석에 보낼 것: 단계 {stage_label!r}"
      + (f" → 트랙 {stage}" if stage is not None else " → 트랙 «미연결»")
      + f" · 결정 {len(decisions)} · 다시 볼 전제 {sum(1 for x in decisions if x['broken'])} · 막음 {len(blocks)}"
      + f" · 남은 것 {sum(len(v['open']) for v in list(per.values()) + [loose])}"
      + f" · 됐다 {sum(len(v['done']) for v in list(per.values()) + [loose])}"
      + f"(확인 안 된 것 {sum(1 for v in list(per.values()) + [loose] for d in v['done'] if not d['ok'])})"
      + " · 단계별: " + ", ".join(f"{i}-{NINE[i]} {len(v['decisions'])}건" for i, v in sorted(per.items())))
if _자세히: print(f"  · 쌓인 것: 막음 {len(piled_blocks)}"
      + (f"(근거 없어 안 적은 것 {blocks_nowhy})" if blocks_nowhy else "")
      + (f"(「안 막았으면」 빈 옛 줄 {blocks_noifnot})" if blocks_noifnot else "")
      + f" · 되돌림 {len(reverted)} · 기다리는 것 {len(waiting)}"
      + (f"(최대 넘긴 것 {sum(1 for x in waiting if x['over'])})" if any(x["over"] for x in waiting) else "")
      + f" · 걸린 날이 남은 것 {len(waited)}"
      + " · 단계 소요: " + (", ".join(
          f"{x['label']} {x['days']}일" + (f"×{x['visits']}" if x["visits"] > 1 else "")
          + ("(계속)" if x["open"] else "") for x in stage_days) or "아직 없음"))
