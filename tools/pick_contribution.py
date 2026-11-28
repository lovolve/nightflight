#!/usr/bin/env python3
"""기여 — 기록에서 «검사가 못 막은 것»을 골라 쌓는다.

기록에는 이미 시행착오가 적혀 있다. 할 일은 모으는 것이 아니라 보낼 것을 고르는 것이다.

기여물은 «검사가 못 막은 것»이다:
  되돌림      — 정했다가 되돌렸다. 전제가 틀렸다는 증거다
  못함        — AI가 못 해서 사람 손이 필요했다. 도구의 빈 곳이다
  전제바뀜    — 한때 맞다고 본 것이 바뀌었다
  같은 자리 3번+ — 반복은 멈출 신호가 없었다는 뜻이다

막음은 기여물이 아니다. 막혔다는 것은 이미 검사가 있다는 뜻이다.

지키는 것 여섯:
 1. 동의 없이 아무것도 담지 않는다. 동의id 가 없는 건은 기여물이 아니다
 3. 앱 이름·파일 경로·사람 이름을 담지 않는다. 담는 것은 «증상의 모양»이다
 4. 건마다 식별자를 붙인다 — 없으면 «제 것을 지워 주세요»에 답할 수 없다
 5. 무엇이 나갈지 보이고, 지울 수 있어야 한다
 6. 모은 건수가 차기 전에 «남이 겪은 것이 막아 줍니다»라고 말하지 않는다

앱은 이름 대신 되돌릴 수 없는 이름표(앱 자리로 만든 8자)로 담는다.
지워 달라는 요청에는 답할 수 있고, 앱 이름은 어디에도 남지 않는다.

후보의 본문은 사용자가 쓴 문장이라 기계가 고쳐 쓰지 않는다.
기계는 경로·앱 자리 이름만 잡고, 담지 못하는 것은 미리 보인다.

쓰기:  pick_contribution.py 동의 ["<사용자 말 그대로>"]
       pick_contribution.py 후보
       pick_contribution.py 담기 "<일부 글자>"
       pick_contribution.py 목록
       pick_contribution.py 취소 "<건id>"
       pick_contribution.py 보내기      (대화 시작 자동 점검이 뒤에서 부른다 · 꺼져 있으면 아무것도 안 한다)
"""
import hashlib
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

sys.path.insert(0, str(HERE))
try:
    from count_same_symptom import SRC
except Exception:
    SRC = None

import _root as _root_mod

REPEAT_MIN = 3
보내기켬 = True
KINDS = ("되돌림", "못함", "전제바뀜", "반복")


def _p(*a, **kw):
    print(*a, **kw)


def _root():
    return Path(os.environ["NF_ROOT"]) if os.environ.get("NF_ROOT") else _root_mod.root()


def _state():
    return Path(os.environ["NF_STATE"]) if os.environ.get("NF_STATE") else _root_mod.state_dir()


def _home():
    v = os.environ.get("NF_HOME") or os.environ.get("NIGHTFLIGHT_HOME")
    return Path(v) if v else Path.home() / ".nightflight"


def _person():
    v = os.environ.get("NF_PERSON")
    return Path(v) if v else _home() / "people.tsv"


def _store():
    return _home() / "contributions.tsv"


class _잠금:
    def __enter__(self):
        self.f = None
        try:
            import fcntl
            _home().mkdir(parents=True, exist_ok=True)
            self.f = open(_home() / "contributions.lock", "a")
            fcntl.flock(self.f, fcntl.LOCK_EX)
        except Exception:
            pass
        return self

    def __exit__(self, *a):
        if self.f is not None:
            self.f.close()


def _통째쓰기(path, rows):
    t = path.with_name(path.name + ".tmp%d" % os.getpid())
    t.write_text("".join("\t".join(r) + "\n" for r in rows), encoding="utf-8")
    os.replace(t, path)


def _rows(path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if "\t" in line:
            out.append(line.split("\t"))
    return out


def _id(kind, body):
    return hashlib.sha1(f"{kind}\t{body}".encode("utf-8")).hexdigest()[:12]


def _app_tag():
    return hashlib.sha1(str(_root()).encode("utf-8")).hexdigest()[:8]


def _app_name():
    name = ""
    for c in _rows(_state() / "ledger.tsv"):
        if len(c) > 3 and c[1] == "앱설정" and c[2] == "앱이름":
            name = c[3].strip()
    return "" if name in ("", "없음", "모름") else name


def _leak(text):
    for mark in ("/Users/", "/private/", "/home/", "~/"):
        if mark in text:
            return "파일 경로가 들어 있습니다"
    if "/" in text and any(text.count(e) for e in (".swift", ".py", ".json", ".md", ".tsv")):
        return "파일 이름이 들어 있습니다"
    name = _root().name
    if name and len(name) >= 3 and name.lower() in text.lower():
        return "앱 자리 이름이 들어 있습니다"
    app = _app_name()
    if len(app) >= 2 and app in text:
        return f"앱 이름(「{app}」)이 들어 있습니다"
    return ""


def candidates():
    led = _rows(_state() / "ledger.tsv")
    got = {r[1] for r in _rows(_store()) if len(r) > 1}
    out = []

    def add(kind, body, side):
        body = (body or "").strip()
        if not body:
            return
        iid = _id(kind, body)
        if iid in got:
            return
        if any(c["건id"] == iid for c in out):
            return
        out.append({"종류": kind, "본문": body, "곁들임": (side or "").strip(),
                    "건id": iid, "못담는이유": _leak(body + " " + (side or ""))})

    for c in led:
        kind = c[1] if len(c) > 1 else ""
        if kind == "되돌림":
            add("되돌림", c[2] if len(c) > 2 else "",
                "틀렸던 전제: " + (c[4] if len(c) > 4 else ""))
        elif kind == "못함":
            add("못함", c[2] if len(c) > 2 else "",
                "없던 것: " + (c[3] if len(c) > 3 else ""))
        elif kind == "전제바뀜":
            add("전제바뀜", c[4] if len(c) > 4 else "",
                "어느 결정: " + (c[2] if len(c) > 2 else ""))

    if SRC:
        root = str(_root()) + os.sep
        seen = {}
        for c in _rows(_state() / "internal" / "repeat-guard.tsv"):
            f = c[1] if len(c) > 1 else ""
            if not f.startswith(root) or not f.endswith(tuple(SRC)):
                continue
            seen[f] = seen.get(f, 0) + 1
        for n in sorted({v for v in seen.values() if v >= REPEAT_MIN}, reverse=True):
            k = sum(1 for v in seen.values() if v == n)
            body = f"같은 코드 한 곳을 {n}번 고쳤다"
            if k > 1:
                body = f"같은 코드 한 곳을 {n}번 고쳤다 (그런 자리가 {k}곳)"
            add("반복", body, "멈출 신호가 없었다")

    out.sort(key=lambda c: KINDS.index(c["종류"]))
    return out


def consent_id():
    for c in _rows(_person()):
        if len(c) > 2 and c[1] == "기여동의":
            return c[2], c[0]
    return "", ""


def cmd_동의(said):
    cid, when = consent_id()
    if cid:
        _p(f"  · 이미 동의하셨습니다 ({when}). 앱이 바뀌어도 다시 여쭙지 않습니다.")
        return 0
    if not said:
        _p()
        _p("── 사용자에게 이렇게 여쭙니다 ──────────────────────")
        _p()
        _p("  만드시면서 **되돌린 것 · 제가 못 해서 손이 가신 것 · 한때 맞다고 보셨다가")
        _p("  바뀐 것**이 기록에 남아 있습니다. 그것을 저희에게 보내 주시겠습니까?")
        _p()
        _p("  · 보내는 것은 **무엇이 안 막혔나**뿐입니다. 막힌 것은 안 보냅니다")
        _p("  · 앱 이름도, 파일 이름도, 쓰시는 분의 이름도 담지 않습니다")
        _p("  · 무엇이 나갈지 **먼저 보시고**, 한 건씩 고르시고, 언제든 지우실 수 있습니다")
        if _켜짐():
            _p("  · 동의하시면 고르신 것만 다음 대화 시작 때 보냅니다. 보내기 전에 지우시면 안 나갑니다")
        else:
            _p("  · ⚠️ 지금은 **모아 두기만** 합니다 — 보내기는 아직 꺼져 있습니다")
        _p()
        _p("  ⛔ 지금 드릴 수 없는 말이 하나 있어 미리 적습니다 — 「남이 겪은 것이 사용자를")
        _p("     막아 드립니다」는 **아직 사실이 아닙니다.** 모인 것이 적습니다.")
        _p("     그 말씀은 쌓인 뒤에 드립니다.")
        _p()
        return 0
    said = said.replace("\t", " ").replace("\r", " ").replace("\n", " ")
    cid = hashlib.sha1(f"{_today()}\t{said}".encode("utf-8")).hexdigest()[:12]
    _person().parent.mkdir(parents=True, exist_ok=True)
    with _person().open("a", encoding="utf-8") as f:
        f.write(f"{_today()}\t기여동의\t{cid}\t{said}\t\t\n")
    _p(f"  · 동의하셨다고 적었습니다. 앱이 바뀌어도 다시 여쭙지 않습니다.")
    _p(f"    들은 말: {said}")
    return 0


def _today():
    import datetime
    return os.environ.get("NF_TODAY") or datetime.date.today().isoformat()


def cmd_후보():
    cs = candidates()
    _p()
    _p("── 보낼 수 있는 것 — **검사가 못 막은 것** ────────")
    if not cs:
        _p("   아직 없습니다.")
        _p("   ⚠️ 이건 「잘 돌고 있다」가 아니라 **되돌린 것도 못 한 것도 아직 없다**는 뜻입니다.")
        _p()
        return 0
    last = ""
    for i, c in enumerate(cs, 1):
        if c["종류"] != last:
            last = c["종류"]
            _p()
            _p(f"   [{last}] {_왜(last)}")
        _p(f"     {i}. {_cut(c['본문'], 150)}")
        if c["곁들임"]:
            _p(f"        {_cut(c['곁들임'], 110)}")
        if c["못담는이유"]:
            _p(f"        ⛔ 담을 수 없습니다 — {c['못담는이유']}.")
            _p(f"           그 말은 직접 쓰신 문장이라 제가 고쳐 쓰지 않습니다.")
    _p()
    _p("   ⛔ **막은 것은 여기 없습니다** — 막혔다는 것은 이미 보는 눈이 있다는 뜻이고,")
    _p("      그건 새로 만들 검사의 재료가 아닙니다.")
    _p("   보내실 것을 말씀해 주시면 표시해 두겠습니다. 고르지 않으신 것은 나가지 않습니다.")
    app = _app_name()
    if len(app) >= 2:
        _p(f"   ✅ **「{app}」**·경로·파일 이름이 든 줄은 제가 빼 뒀습니다.")
        _p("      ⚠️ 다만 **사람 이름**은 제가 못 봅니다 — 들어 있으면 빼 달라고 말씀해 주세요.")
    elif app:
        _p(f"   ⚠️ 앱 이름이 **한 글자(「{app}」)**라 제가 걸러낼 수 없습니다 —")
        _p("      그 이름이 든 줄은 빼 달라고 말씀해 주세요.")
    else:
        _p("   ⚠️ 제가 걸러낸 것은 **경로와 폴더 이름**뿐입니다. 앱의 **한글 이름**은 제가 못 봅니다 —")
        _p("      앱 이름을 한 번 알려 주시면 그 이름이 든 줄은 제가 빼 드립니다.")
        _p("      그때까지는 윗줄에 앱 이름이나 사람 이름이 있으면 빼 달라고 말씀해 주세요.")
    if any(len(c["본문"]) > 150 for c in cs):
        _p("   ⚠️ 긴 줄은 줄여 보였습니다 — **담기는 전문이 담깁니다.**")
        _p("      고르신 뒤 「나갈 것」에서 그대로 보실 수 있습니다.")
    _p()
    return 0


def _cut(s, n):
    s = s.strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _왜(kind):
    return {"되돌림": "정했다가 되돌리셨습니다 — 전제가 틀렸다는 증거입니다",
            "못함": "제가 못 해서 손이 가셨습니다 — 도구의 구멍입니다",
            "전제바뀜": "한때 맞다고 보신 것이 바뀌었습니다",
            "반복": "같은 자리를 여러 번 고치셨습니다 — 멈출 신호가 없었습니다"}.get(kind, "")


def cmd_담기(key):
    cid, _ = consent_id()
    if not cid:
        _p("  ⛔ 아직 여쭙지 않았습니다 — 동의 없이는 한 건도 담지 않습니다.", file=sys.stderr)
        return 1
    cs = candidates()
    hit = [c for c in cs if c["건id"] == key] or [c for c in cs if key in c["본문"]]
    if not hit:
        _p(f"  「{key}」이 들어간 것을 후보에서 못 찾았습니다.")
        _p("     이미 담으신 것일 수도 있습니다 — 담긴 것을 보여드릴 수 있습니다.")
        return 0
    if len(hit) > 1:
        _p(f"  「{key}」이 들어간 것이 {len(hit)}건입니다. 어느 것인지 말씀해 주세요:")
        for c in hit:
            _p(f"     · {c['본문']}")
        return 0
    c = hit[0]
    if c["못담는이유"]:
        _p(f"  ⛔ 담지 않았습니다 — {c['못담는이유']}.", file=sys.stderr)
        _p("     앱 이름·파일 이름·사람 이름은 담지 않기로 정해져 있습니다.", file=sys.stderr)
        _p("     제가 그 문장을 고쳐 쓰면 그건 제가 지어낸 말이 됩니다.", file=sys.stderr)
        return 1
    _store().parent.mkdir(parents=True, exist_ok=True)
    with _잠금(), _store().open("a", encoding="utf-8") as f:
        f.write(f"{_today()}\t{c['건id']}\t{c['종류']}\t{c['본문']}\t{c['곁들임']}"
                f"\t{_app_tag()}\t{cid}\n")
    _p(f"  · 보낼 것으로 표시했습니다 [{c['종류']}] {c['본문']}")
    _p(f"    지우실 때 쓰는 이름표: {c['건id']}")
    if _켜짐():
        _p("    다음 대화 시작 때 보냅니다. 그 전에 지우시면 나가지 않습니다.")
    else:
        _p("    ⚠️ 아직 보내지 않습니다 — 보내기가 꺼져 있습니다.")
    return 0


def cmd_목록():
    rs = _rows(_store())
    _p()
    _p("── 나갈 것 ───────────────────────────────────────")
    if not rs:
        _p("   아직 없습니다. 고르지 않으신 것은 나가지 않습니다.")
        _p()
        return 0
    for r in rs:
        when, iid, kind, body = (r + ["", "", "", ""])[:4]
        side = r[4] if len(r) > 4 else ""
        _p(f"   · [{kind}] {body}")
        if side:
            _p(f"       {side}")
        보낸날 = _보냄().get(iid)
        _p(f"       담은 날 {when} · 이름표 {iid}" + (f" · 보낸 날 {보낸날}" if 보낸날 else " · 아직 안 보냄"))
    _p()
    _p(f"   모두 {len(rs)}건입니다. 지우실 것이 있으면 말씀해 주세요 — 바로 지웁니다.")
    if _켜짐():
        _p("   아직 안 보낸 것은 다음 대화 시작 때 보냅니다. 보낸 것도 지우시면 서버에서 지웁니다.")
    else:
        _p("   ⛔ **아직 보내지 않습니다.** 보내기가 꺼져 있습니다.")
    _p()
    return 0


def cmd_취소(key):
    with _잠금():
        rs = _rows(_store())
        keep = [r for r in rs if not (len(r) > 1 and (r[1] == key or key in (r[3] if len(r) > 3 else "")))]
        gone = len(rs) - len(keep)
        if gone == 0:
            _p(f"  「{key}」에 해당하는 것을 못 찾았습니다. 나갈 것이 {len(rs)}건 있습니다.")
            return 0
        _통째쓰기(_store(), keep)
    _p(f"  · {gone}건을 지웠습니다. 나갈 것은 {len(keep)}건 남았습니다.")
    보낸것 = _보냄()
    지울것 = [r[1] for r in rs if r not in keep and len(r) > 1 and r[1] in 보낸것]
    if 지울것:
        _지움대기더하기(지울것)
        남음 = _지움대기처리()
        if 남음 is None or 남음:
            _p("    서버에 이미 보낸 것이 있습니다. 지금 서버에 닿지 못해 다음 대화 시작 때 다시 지웁니다.")
        else:
            _p("    서버에 보냈던 것도 지웠습니다.")
    return 0


def _켜짐():
    v = os.environ.get("NF_CONTRIB_SEND")
    if v in ("0", "1"):
        return v == "1"
    return 보내기켬


def _보냄파일():
    return _home() / "contributions_sent.tsv"


def _지움파일():
    return _home() / "contributions_delete.tsv"


def _보냄():
    return {r[0]: r[1] for r in _rows(_보냄파일()) if len(r) > 1}


def _지움대기더하기(ids):
    with _잠금():
        _지움대기더하기_잠근뒤(ids)


def _지움대기더하기_잠근뒤(ids):
    있음 = {r[0] for r in _rows(_지움파일()) if r}
    _지움파일().parent.mkdir(parents=True, exist_ok=True)
    with _지움파일().open("a", encoding="utf-8") as f:
        for i in ids:
            if i not in 있음:
                f.write(f"{i}\t{_today()}\n")


def _서버():
    sys.path.insert(0, str(HERE.parent / "bin"))
    try:
        import account_login as al
    except Exception:
        return None
    k, m = al.열쇠(), os.environ.get("NF_MPRINT", "")
    if not k or not m or not os.environ.get("NF_BRAIN_BASE", "").startswith("https://"):
        return None
    return al.부르기, k, m


def _지움대기처리():
    ids = [r[0] for r in _rows(_지움파일()) if r]
    if not ids:
        return 0
    s = _서버()
    if not s:
        return None
    부르기, k, m = s
    try:
        d = 부르기("기여지우기", {"열쇠": k, "맥지문": m, "건id": ids[:100]})
    except Exception:
        return None
    if not (isinstance(d, dict) and d.get("됐나")):
        return None
    done = set(ids[:100])
    with _잠금():
        keep = [r for r in _rows(_지움파일()) if r and r[0] not in done]
        _통째쓰기(_지움파일(), keep)
        sent = [r for r in _rows(_보냄파일()) if r and r[0] not in done]
        _통째쓰기(_보냄파일(), sent)
    return len(keep)


def cmd_보내기():
    if not _켜짐():
        return 0
    _지움대기처리()
    cid, _ = consent_id()
    if not cid:
        return 0
    보낸것 = _보냄()
    줄 = []
    for r in _rows(_store()):
        when, iid, kind, body, side, tag, rcid = (r + [""] * 7)[:7]
        if not rcid or iid in 보낸것 or kind not in KINDS:
            continue
        줄.append({"건id": iid, "종류": kind, "본문": body, "곁들임": side,
                  "출처앱": tag, "출처날": when, "동의id": rcid})
    if not 줄:
        return 0
    s = _서버()
    if not s:
        return 0
    부르기, k, m = s
    for i in range(0, len(줄), 20):
        try:
            d = 부르기("기여보내기", {"열쇠": k, "맥지문": m, "줄": 줄[i:i + 20]}, 20)
        except Exception:
            return 0
        if not (isinstance(d, dict) and d.get("됐나")):
            return 0
        받은 = d.get("건id") or []
        if 받은:
            _보냄파일().parent.mkdir(parents=True, exist_ok=True)
            with _잠금(), _보냄파일().open("a", encoding="utf-8") as f:
                for iid in 받은:
                    if isinstance(iid, str) and iid not in 보낸것:
                        f.write(f"{iid}\t{_today()}\n")
                        보낸것[iid] = _today()
    return 0


def main(argv):
    if not argv:
        _p(__doc__)
        return 0
    what, rest = argv[0], argv[1:]
    if what == "동의":
        return cmd_동의(rest[0] if rest else "")
    if what == "후보":
        return cmd_후보()
    if what == "담기":
        if not rest:
            _p("  무엇을 담을지 일부 글자가 필요합니다.", file=sys.stderr)
            return 1
        return cmd_담기(rest[0])
    if what == "목록":
        return cmd_목록()
    if what == "보내기":
        return cmd_보내기()
    if what == "취소":
        if not rest:
            _p("  지울 것의 이름표가 필요합니다.", file=sys.stderr)
            return 1
        return cmd_취소(rest[0])
    _p(f"  모르는 것입니다: {what}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
