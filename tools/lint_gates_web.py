#!/usr/bin/env python3
"""웹이 쓸 관문 표가 **낡았나**

설계: nightflight-server design/설치전-관문셈.md §4
      ()


를 시키셨고, 만들기 전에 4-개발 처방을 다시 봤다:
   「**값이 두 곳에 있으면 검사가 아니라 «구조»로 푼다** — 한 곳이면 볼 필요가 없다」

⭐ 그래서 **판정 규칙을 웹에 보내지 않기로** 했다. 네 축의 답을 **전부 돌려 미리 계산**하고
   (`gen_gates_web.py`), 웹은 **표를 찾아보기만** 한다.
   → 규칙은 `gates.py` **한 곳**에만 있다. **어긋날 길이 구조적으로 없다.**


`관문.tsv` 가 바뀌거나 `gates.py` 의 판정이 바뀌면 **만들어 둔 표가 옛 답을 들고 있다.**
⭐ 그래서 **다시 만들어 보고 지문을 견준다.** 다르면 울린다.


- **표가 없으면 「못 쟀다」**다 — ⛔ 「맞다」가 아니다. 0 을 안전으로 찍지 않는다.
- **다시 만들어 «덮어쓰지» 않는다** — 검사가 조용히 고치면 **사람이 안 본다.**
  무엇이 달라졌는지 말하고, 고치는 것은 사람이 시킨다.
"""
import importlib.util
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
OUT = _HERE.parent / "board" / "관문셈.json"


def main() -> int:
    if not OUT.is_file():
        print("  ⚠️ 웹이 쓸 출시 절차 표가 **없어서 재지 못했습니다**.")
        print("     (이건 「맞다」가 아니라 「못 쟀다」입니다.)")
        print("     만들려면: 출시 절차 표 만들기를 한 번 돌립니다.")
        return 0

    spec = importlib.util.spec_from_file_location("g", _HERE / "gen_gates_web.py")
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
        fresh = m.build()
        want = m.지문(fresh)
    except Exception as e:
        print(f"  ⛔ 다시 만들어 보지 못해 **재지 못했습니다** ({type(e).__name__}).")
        print("     ⚠️ 이건 「맞다」가 아닙니다.")
        return 1

    try:
        have = json.loads(OUT.read_text(encoding="utf-8"))
    except Exception:
        print("  ⛔ 출시 절차 표를 읽지 못했습니다 — **재지 못했습니다.**")
        return 1

    dirty = [g for g in have.get("관문들", [])
             if any(m in (g.get("말", "") + g.get("이름", "")) for m in ("**", "⛔", "⭐", "🔴", "«", "»"))]
    if dirty:
        print("── 터미널 꾸밈이 웹 표로 샜다 ──────────────────")
        print()
        for g in dirty[:6]:
            print(f"  🔴 「{g['이름']}」 — 「{g.get('말','')[:60]}」")
        print()
        print("  ⭐ 화면은 이 글을 **그대로 찍는다** — 별표가 그대로 보인다.")
        print("     보내는 자리에서 걷어내십시오(터미널 쪽 글은 그대로 둡니다).")
        return 1

    try:
        있는것 = m.지문(have)
    except (KeyError, TypeError):
        print("  ⛔ 들고 있는 표에서 지문을 **다시 재지 못했습니다** — 꼴이 깨졌습니다.")
        print("     ⭐ 표 만드는 도구를 다시 돌리십시오 — 검사가 대신 고치지 않습니다.")
        print("        [모델] python3 tools/gen_gates_web.py")
        return 1
    if 있는것 != have.get("지문"):
        print("── 들고 있는 표가 **손으로 고쳐져** 있다 ────────────────")
        print()
        print(f"  🔴 적어 둔 지문 {have.get('지문')} · 내용을 다시 재니 {있는것}")
        print("     ⛔ 이 파일은 **도구가 짓는 것**입니다. 손으로 고치면 다음에 다시 지을 때")
        print("        지워지고, 그 사이에는 화면이 **틀린 답**을 보입니다.")
        print("     ⭐ 표 만드는 도구를 다시 돌리십시오 — 그러면 손질이 지워지고 맞아집니다.")
        print("        [모델] python3 tools/gen_gates_web.py")
        print("     ⭐ 고치실 것이 있으면 **관문 표나 판정 규칙 쪽**을 고치십시오 —")
        print("        규칙은 거기 한 곳에만 있습니다.")
        print("        [모델] data/관문.tsv · tools/gates.py · 자세히는 board/README.md")
        return 1
    if 있는것 == want:
        print(f"  ✅ 웹이 쓸 출시 절차 표가 최신입니다 (경우 {fresh['경우수']:,}가지 · 지문 {want})")
        print("     ⭐ 판정 규칙은 **웹에 안 갑니다** — 미리 계산한 표만 갑니다.")
        print("        그래서 «어긋남»이 구조적으로 생길 수 없습니다.")
        return _조각도_본다()

    print("── 웹이 쓸 출시 절차 표가 낡았다 ────────────────────")
    print()
    print(f"  🔴 들고 있는 지문 {have.get('지문')} · 지금 만들면 {want}")
    hg = {g["번호"]: g for g in have.get("관문들", [])}
    fg = {g["번호"]: g for g in fresh.get("관문들", [])}
    for no in sorted(set(hg) | set(fg)):
        a, b = hg.get(no), fg.get(no)
        if a == b:
            continue
        if a is None:
            print(f"     · 출시 절차가 **새로 생겼다**: {b['이름']}")
        elif b is None:
            print(f"     · 출시 절차가 **없어졌다**: {a['이름']}")
        else:
            for k in ("이름", "최대", "확인", "시작", "말"):
                if a.get(k) != b.get(k):
                    print(f"     · 「{b['이름']}」의 **{k}**: 「{a.get(k)}」 → 「{b.get(k)}」")
    ho, fo = have.get("표", {}), fresh["표"]
    if len(ho) != len(fo):
        print(f"     · 경우 수가 다릅니다: 들고 있는 것 {len(ho):,} · 지금 {len(fo):,}")
    diff = [k for k in fo if k in ho and ho[k] != fo[k]]
    if diff:
        print(f"     · 답이 달라진 경우 {len(diff):,}가지. 예:")
        for k in diff[:3]:
            print(f"        {k}")
            print(f"          전: 안 걸림 {ho[k].get('안걸림')} · 걸림 {len(ho[k].get('걸림', []))}"
                  f" · 모르는 것 {ho[k].get('못센것')}")
            print(f"          후: 안 걸림 {fo[k].get('안걸림')} · 걸림 {len(fo[k].get('걸림', []))}"
                  f" · 모르는 것 {fo[k].get('못센것')}")
    gone = [k for k in ho if k not in fo]
    new = [k for k in fo if k not in ho]
    if gone:
        print(f"     · 없어진 경우 {len(gone):,}가지")
    if new:
        print(f"     · 새로 생긴 경우 {len(new):,}가지")
    print()
    print("  ⭐ 고치는 길: **출시 절차 표 만들기를 다시 돌립니다.**")
    print("  ⛔ 이 검사가 **대신 고치지 않습니다** — 조용히 고치면 사람이 안 봅니다.")
    print("     ⚠️ 웹 화면이 지금 **옛 답**을 보이고 있습니다.")
    return 1


def _조각도_본다() -> int:
    import subprocess
    frag = _HERE.parent / "board" / "관문셈-조각.html"
    gen = _HERE / "gen_gates_embed.py"
    if not frag.is_file():
        print("     ⚠️ 랜딩에 심을 조각은 **아직 없습니다** — 만드시려면 조각 도구를 돌리십시오.")
        return 0
    if not gen.is_file():
        print("     ⚠️ 조각 만드는 도구가 없어 **조각은 못 쟀습니다**(「맞다」가 아닙니다).")
        return 0
    before = frag.read_text(encoding="utf-8")
    r = subprocess.run([sys.executable, str(gen), "--찍기"],
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout:
        print("     🔴 조각을 만들어 보다 **실패했습니다** — 낡았는지 못 쟀습니다.")
        return 1
    if r.stdout == before:
        print("     ✅ 랜딩에 심을 조각도 최신입니다.")
        return 0
    print()
    print("  🔴 **랜딩에 심을 조각이 낡았습니다.**")
    print(f"     지금 {len(before):,} 글자 · 다시 만들면 {len(r.stdout):,} 글자")
    print("     ⛔ 낡은 조각은 랜딩이 **옛 답을 보입니다.**")
    print("     ⭐ 고치는 길: 조각 만드는 도구를 돌리십시오 — 검사가 대신 고치지 않습니다.")
    return 1
    if after == before:
        print("     ✅ 랜딩에 심을 조각도 최신입니다.")
        return 0
    print()
    print("  🔴 **랜딩에 심을 조각이 낡았습니다.**")
    print(f"     지금 {len(before):,} 글자 · 다시 만들면 {len(after):,} 글자")
    print("     ⛔ 낡은 조각은 랜딩이 **옛 답을 보입니다.**")
    print("     ⭐ 고치는 길: 조각 만드는 도구를 돌리십시오 — 검사가 대신 고치지 않습니다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
