#!/usr/bin/env python3
"""밖으로 나가는 길에 **봉투가 붙어 있나** — 측정 여섯이 잊히는 것을 막는다.

🔴 왜 (기획 §51-4 · design/측정-여섯.md):
   측정 여섯은 **기능이 아니라 측정**이라 나중으로 밀기 쉽고,
   **나중에는 과거를 만들 수 없어서 못 고친다.** 지금(우리 서버로 나가는 길 0개) 못 박았고,
   ⛔ **문서로만 둔 못은 지켜지지 않는다** — 이 저장소가 그 증거를 여럿 갖고 있다.

⭐ 그래서 이 검사가 **첫 호출이 생기는 순간** 말한다.
   🔴 **그 순간이 왔다** — 2026-10-13 실측: 나가는 호출 **1곳**(두뇌 배선).
      봉투가 붙어 있어 ✅ 다. ⛔ 「붙어 있다」는 **지금 그렇다**는 뜻이고,
      다음 호출이 생길 때 또 봐야 한다 — 그래서 이 검사는 계속 돈다.
   📌 이력: 2026-10-04 실측에서는 **해당 0건**이었다(우리 서버로 나가는 호출이 없었다).
      ⭐ 그때 못을 박아 뒀기 때문에 **첫 호출이 생기는 자리에서 바로 잡혔다** —
         0 일 때 미리 박은 못이 일을 했다는 기록이라 지우지 않는다.
   ⚠️ **0 이 「안전」이 아니라 「아직 안 보낸다」**는 뜻이다 — 0 일 때는 그렇게 찍는다.

보는 것
  ① 우리 서버(두뇌)로 나가는 호출이 생겼나
  ② 그 자리에 **요청 id** 와 **열쇠 상태**가 붙어 있나(봉투 ⑥)
  ③ 기여물을 담는 자리에 **건별 식별자·출처·동의**가 붙어 있나(⑤)

⛔ **애플로 나가는 것은 세지 않는다** — 그것은 대표님 «자기 데이터»이고
   우리가 세는 깔때기가 아니다(`asc.py`·`asc_mcp.py`·`verify_upload.sh`).

⛔ **막지 않는다. 보이게 한다.** 다만 **해당되면 1 로 끝낸다** — 턴 끝에 말해야 하기 때문이다.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

전송정의 = ("bin/project-root.sh",)

SKIP = {
    "tools/asc.py": "애플 App Store Connect — 사용자 자기 데이터",
    "tools/asc_mcp.py": "같은 것(MCP 로 감싼 것)",
    "tools/verify_upload.sh": "같은 것(올라갔는지 확인)",
    "tools/lint_user_facing.py": "낱말 목록에 `curl` 이 글자로 들어 있다",
    "tools/lint_outbound.py": "이 파일 자체",
    "probe/headers-probe.sh": "탐침 — 헬퍼가 «불리는가»만 본다(나가는 호출이 아니다)",
    "tools/글꼴박기.py": "글꼴 원본 받기 — 만드는 사람만 돈다. 깔때기가 아니다",
}
NET = re.compile(r"urllib\.request\.urlopen|requests\.(get|post|put)|curl\s+-|"
                 r"fetch\(|http\.client|socket\.create_connection|"
                 r"\bnf_post\s|\bnf_curl\s|_프록시막음\.open\(")
ENV = re.compile(r"요청id|request_id|열쇠상태|key_state")
GIVE = re.compile(r"건id|item_id|동의id|consent_id")


SAID_OUT = []


def 프록시를막았나(뿌리: Path):
    """파이썬이 서버를 부르는 자리가 **프록시를 안 따르나.**

    🔴 왜 (2026-10-25 보안 레드팀 8회차 · 재서 확인했다):
      `urllib.request.urlopen` 은 `HTTPS_PROXY`·`https_proxy` 를 **그대로 따른다.**
      가짜 프록시를 세우고 그 환경변수를 심으니 요청이 거기로 갔다 —
      `CONNECT …supabase.co:443`. 막으면 진짜 서버로 간다(401 = 도달).
      ⛔ 거기에 믿을 인증서까지 심으면 **몸이 읽힌다** — 사람id·맥지문·애플 자격이다.
    ⭐ 셸 쪽은 `nf_curl` 이 `--noproxy '*'` 로 막는다. 파이썬도 같은 선이라야 한다.
    ⛔ `urlopen(` 을 그대로 쓰면 운다 — `ProxyHandler({})` 로 만든 여는것을 쓰게 한다.
    """
    나쁜 = []
    for q in sorted(list((뿌리 / "bin").rglob("*.py")) + list((뿌리 / "tools").rglob("*.py"))):
        if not q.is_file():
            continue
        try:
            원 = q.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        이름 = str(q.relative_to(뿌리))
        if 이름 in 전송정의 or q.name == "lint_outbound.py" or q.name.startswith("_"):
            continue
        for i, l in enumerate(원.split("\n"), 1):
            글 = l.strip()
            if 글.startswith("#") or "urlopen(" not in 글:
                continue
            if "re.compile" in 글 or "urllib\\.request" in 글:
                continue
            if "ProxyHandler" in 원 and "_프록시막음" in 원:
                continue
            나쁜.append((이름, i, 글[:60]))
    return 나쁜


def main() -> int:
    안막음 = 프록시를막았나(HERE)
    if 안막음:
        print("  ⛔ 파이썬이 **프록시를 따라갑니다** — 심어 둔 프록시로 몸이 갑니다.")
        print("     🔴 실측(2026-10-25): 가짜 프록시를 세우고 `HTTPS_PROXY` 를 심으니")
        print("        요청이 거기로 갔습니다. 믿을 인증서까지 심으면 **몸이 읽힙니다** —")
        print("        그 몸에 사람id·맥지문·애플 자격이 있습니다.")
        for 이름, 줄, 글 in 안막음[:6]:
            print("       · %s:%d  %s" % (이름, 줄, 글))
        print("     ⭐ 고치는 법: 프록시를 막은 여는것을 만들어 그것으로 부르십시오.")
        print("        [모델] urllib.request.build_opener(urllib.request.ProxyHandler({}))")
        return 1
    hits, gives = [], []
    for f in sorted(list((HERE / "bin").rglob("*.sh")) + list((HERE / "tools").rglob("*.py"))
                    + list((HERE / "tools").rglob("*.sh")) + list((HERE / "probe").rglob("*.sh"))):
        rel = str(f.relative_to(HERE))
        if rel in SKIP:
            continue
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        body = "\n".join(lines)
        _in_doc, _doc = False, set()
        for _i, _l in enumerate(lines, 1):
            _q = _l.count('"""') + _l.count("'''")
            if _in_doc:
                _doc.add(_i)
            if _q % 2 == 1:
                _in_doc = not _in_doc
                _doc.add(_i)
        for i, raw in enumerate(lines, 1):
            line = re.sub(r"\s#.*$", "", raw)
            if line.lstrip().startswith("#") or i in _doc:
                continue
            if re.search(r"밖으로검사:\s*찾는 말이다", raw):
                SAID_OUT.append(f"{rel}:{i}")
                continue
            if rel in 전송정의 and re.search(r"command curl|\bnf_curl\s", line):
                SAID_OUT.append(f"{rel}:{i}")
                continue
            if NET.search(line):
                hits.append((rel, i, raw.strip()[:70], bool(ENV.search(body))))
            if re.search(r"기여물|contribution", line) and not line.lstrip().startswith("#"):
                gives.append((rel, i, bool(GIVE.search(body))))

    bad = []
    for rel, i, txt, has_env in hits:
        if not has_env:
            bad.append(f"  🔴 {rel}:{i} 밖으로 보내는데 **봉투가 없다**")
            bad.append(f"     「{txt}」")
            bad.append("     요청id · 열쇠상태를 같이 남긴다 — 없으면 깔때기의 분모가 영원히 없다")
            bad.append("     (design/측정-여섯.md ⑥)")
    for rel, i, has_id in gives:
        if not has_id:
            bad.append(f"  🔴 {rel}:{i} 기여물을 담는데 **건별 식별자가 없다**")
            bad.append("     건id · 출처 · 동의id — 없으면 「제 것을 지워 주세요」에 답할 수 없다")
            bad.append("     ⛔ 소급 부여가 불가능하다 (design/측정-여섯.md ⑤)")

    if bad:
        print("── 밖으로 나가는 길 ──────────────────────────")
        print("\n".join(bad))
        return 1

    if not hits:
        print("  ✅ 우리 서버로 나가는 호출이 **아직 없다** — 봉투를 잊을 자리도 없다")
        print(f"     ⚠️ 이건 「안전하다」가 아니라 「아직 안 보낸다」다. 애플 쪽 {len(SKIP)-3}곳은 세지 않는다")
        if SAID_OUT:
            print(f"     ⚠️ {len(SAID_OUT)}곳은 「찾는 말이다」라고 **선언해서** 넘겼다 — "
                  + " · ".join(SAID_OUT[:6]))
        return 0
    print(f"  ✅ 나가는 호출 {len(hits)}곳에 봉투가 붙어 있다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
