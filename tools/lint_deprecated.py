#!/usr/bin/env python3
"""폐기된 결론이 **표지 없이** 남아 있나

설계: nightflight-server design/들고-있는-것.md ⓒ
      ()

🔴 **왜 이 검사가 있나 — 2026-10-10 에 내가 틀렸다.**
   라고 답했다.
   그 선은 **닷새 전(10-05)에 창업자 지시로 폐기**돼 있었고, 폐기 사실은
   `data/관문.tsv` **주석에 적혀 있었다.** 나는 그 파일을 안 읽었다.
   ⛔ **부주의가 아니다** — 죽은 결론이 **다른 파일에서 살아 있는 문장으로** 남아 있었고
   어느 것이 살아 있는지 **기계가 말해 주지 않았다.**

⭐⭐ **그래서 이 검사가 하는 일은 하나다: 죽은 말이 어디에 살아 있는지 찍는다.**
   사람(나)이 「이 문서가 최신인가」를 기억할 일이 아니다.


    폐기된말 ⇥ 폐기된날 ⇥ 누가 ⇥ 무엇으로 ⇥ 어디서정했나

⛔ **「무엇으로」가 비면 거절한다.** 대체가 없는 것은 폐기가 아니라 **삭제**이고,
   삭제면 그 말이 **어디에도 없어야** 한다. 「그냥 쓰지 마라」는 다음 세션이 못 쓴다.


    🔴 폐기 2026-10-05 — 

⭐ **표가 아니라 「그 자리」에 있어야 한다.** 내가 틀린 이유가 그것이다 —
   표(주석)는 다른 파일에 있었고 나는 **죽은 문장이 있는 파일만** 읽었다.

⛔ **이 검사는 「폐기된 줄이 있나」를 세지 않는다** — 그건 정상이다(이력은 남긴다).
   세는 것은 **「표지 없이 살아 있는 척하는 자리」**다.
"""
import re
import sys
from pathlib import Path

MARK = re.compile(r"폐기\s*(\d{4}-\d{2}-\d{2})")
NEAR = 6

PUB_GLOBS = ("data/*.tsv", "skills/*/SKILL.md", "*.md", "board/*.html",
             "tools/*.py", "bin/*.sh", "bin/ledger.d/*.sh", "tests/*.sh")
BRAIN_GLOBS = ("design/*.md", "catalog/*.md", "catalog/*.tsv", "*.md", "explain/*.md")


def _rows(p: Path):
    """폐기 표. 칸: 폐기된말 ⇥ 폐기된날 ⇥ 누가 ⇥ 무엇으로 ⇥ 어디서정했나"""
    if not p.is_file():
        return None
    out = []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("#") or "\t" not in line:
            continue
        c = [x.strip() for x in line.split("\t")]
        out.append((i, (c + ["", "", "", "", ""])[:5]))
    return out


def _files(root: Path, globs):
    seen, out = set(), []
    for g in globs:
        for f in sorted(root.glob(g)):
            if f.is_file() and f not in seen:
                seen.add(f)
                out.append(f)
    return out


def _marked(lines, idx):
    """죽은 말이 있는 줄 주변에 표지가 있나."""
    lo, hi = max(0, idx - NEAR), min(len(lines), idx + NEAR + 1)
    return any(MARK.search(lines[j]) for j in range(lo, hi))


def main():
    here = Path(__file__).resolve().parent
    plugin = here.parent
    brain = plugin.parent / "nightflight-server"

    tables = [(plugin / "data" / "폐기.tsv", plugin, PUB_GLOBS)]
    if brain.is_dir():
        tables.append((brain / "catalog" / "폐기.tsv", brain, BRAIN_GLOBS))

    bad, noreplace, missing, counted, nomeasure = [], [], [], 0, []

    for tbl, root, globs in tables:
        rows = _rows(tbl)
        if rows is None:
            nomeasure.append(str(tbl.relative_to(tbl.parent.parent)))
            continue
        files = _files(root, globs)
        for ln, (dead, when, who, instead, where) in rows:
            if not dead:
                continue
            counted += 1
            if not instead:
                noreplace.append((tbl.name, ln, dead))
            hits = 0
            for f in files:
                if f.name == tbl.name:
                    continue
                try:
                    lines = f.read_text(encoding="utf-8").splitlines()
                except Exception:
                    continue
                for i, raw in enumerate(lines):
                    if dead not in raw:
                        continue
                    hits += 1
                    if not _marked(lines, i):
                        bad.append((f.relative_to(root), i + 1, dead, when, instead))
            if hits == 0:
                missing.append((tbl.name, ln, dead))

    if nomeasure:
        print("  ⚠️ 폐기 표가 없어 **재지 못했습니다** — " + " · ".join(nomeasure))
        print("     (이건 「폐기된 것이 없다」가 아니라 「못 쟀다」입니다)")

    if not bad and not noreplace:
        if counted:
            print(f"  ✅ 폐기된 말 {counted}가지 — 표지 없이 남아 있는 자리가 없습니다")
            if missing:
                print(f"     ⚠️ 그중 {len(missing)}가지는 **어디에도 없습니다** — "
                      "지워진 것이면 표에서 빼고, 아니면 적은 말을 고치십시오")
                for t, ln, d in missing[:5]:
                    print(f"        · {t}:{ln} 「{d[:40]}」")
        print("     ⚠️ 이 검사는 **표에 적은 말**만 봅니다 — 0 이 「전부 최신」은 아닙니다")
        return 0

    print("── 폐기된 결론이 표지 없이 남아 있다 ────────────")
    for rel, ln, dead, when, instead in bad[:20]:
        print(f"  🔴 {rel}:{ln}")
        print(f"     「{dead[:50]}」 — {when} 에 폐기됐습니다")
        print(f"     대신: {instead[:70]}")
    if len(bad) > 20:
        print(f"  … 그리고 {len(bad) - 20}곳 더")
    for t, ln, dead in noreplace:
        print(f"  🔴 {t}:{ln} 「{dead[:40]}」 에 **무엇으로 대신하나**가 비어 있습니다")
        print("     ⛔ 대체가 없으면 폐기가 아니라 삭제입니다 — 그 말을 아예 지우십시오")
    print()
    print("  ⭐ 고치는 길 둘: ① 그 자리를 **새 결론으로 고친다**")
    print("                  ② 이력으로 남길 것이면 **그 자리에** 표지를 단다 —")
    print("                     「🔴 폐기 2026-10-05 — 누가. 대신: …」")
    print("  ⛔ 표에만 적고 그 자리를 그냥 두지 마십시오 — 다음 세션이 그 문장을 읽습니다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
