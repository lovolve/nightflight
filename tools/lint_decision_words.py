#!/usr/bin/env python3
"""야간비행 도구"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAIL = 768 * 1024
ASK_TOOLS = ("AskUserQuestion",)
ASK_KEYS = ("ask",)


def 사전() -> tuple[set[str], dict[str, str]]:
    안씀, 바꿈 = set(), {}
    p = ROOT / "data" / "word_dictionary.tsv"
    if not p.exists():
        return 안씀, 바꿈
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        c = line.split("\t")
        if len(c) < 2:
            continue
        w, g = c[0].strip(), c[1].strip()
        if g == "라":
            안씀.add(w)
        elif g == "다" and len(c) > 2:
            바꿈[w] = c[2].strip()
    return 안씀, 바꿈


def _글(content) -> list[str]:
    if isinstance(content, str):
        return [content]
    return [p.get("text") or "" for p in content or [] if isinstance(p, dict) and p.get("type") == "text"]


def 이번턴(path: Path) -> tuple[list[str], list[str], str]:
    with path.open("rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - TAIL))
        blob = f.read().decode("utf-8", errors="replace")
    rows = []
    for line in blob.splitlines():
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    사람 = []
    끝 = -1
    for i, d in enumerate(rows):
        if d.get("type") == "user":
            t = "".join(_글((d.get("message") or {}).get("content")))
            if t.strip() and not t.lstrip().startswith("<"):
                사람.append(t)
                끝 = i
    묻는, 답 = [], []
    for d in rows[끝 + 1:]:
        if d.get("type") != "assistant":
            continue
        content = (d.get("message") or {}).get("content") or []
        답 += _글(content)
        for p in content if isinstance(content, list) else []:
            if not (isinstance(p, dict) and p.get("type") == "tool_use"):
                continue
            name, inp = str(p.get("name") or ""), p.get("input") or {}
            if name.endswith(ASK_TOOLS):
                for q in inp.get("questions") or []:
                    묻는.append(str(q.get("question") or ""))
                    for o in q.get("options") or []:
                        묻는 += [str(o.get("label") or ""), str(o.get("description") or "")]
            elif name.endswith("wrap_up") and inp.get("ask"):
                묻는.append(str(inp.get("ask")))
                acts = inp.get("actions")
                if isinstance(acts, str):
                    try:
                        acts = json.loads(acts)
                    except Exception:
                        acts = []
                for a in acts or []:
                    if isinstance(a, dict) and not a.get("action"):
                        묻는.append(str(a.get("label") or ""))
    return 묻는, 답, "\n".join(사람)


def 질문문단(답: list[str]) -> list[str]:
    out = []
    for t in 답:
        t = re.sub(r"```.*?```", "", t, flags=re.S)
        for para in re.split(r"\n\s*\n", t):
            if re.search(r"[?？]\s*($|\*|\))", para, flags=re.M):
                out.append(para)
    return out


CODE = re.compile(r"`[^`\n]+`")
PATH = re.compile(r"(?:~/|\.{0,2}/)?[A-Za-z0-9_\-]+/[A-Za-z0-9_\-./]+|\b[\w\-]+\.(?:swift|py|sh|ts|tsx|js|json|tsv|plist|sql|md)\b")
CAMEL = re.compile(r"\b[A-Z][a-z]+[A-Z][A-Za-z]+\b")


def 짚을것(조각: list[str], 사람말: str) -> list[str]:
    안씀, 바꿈 = 사전()
    hits = []
    for t in 조각:
        if not t.strip():
            continue
        for m in CODE.findall(t):
            hits.append("코드 조각 %s" % m)
        for m in PATH.findall(CODE.sub("", t)):
            if "://" not in t and m not in 사람말:
                hits.append("파일 길 «%s»" % m)
        for m in CAMEL.findall(CODE.sub("", t)):
            if m not in 사람말:
                hits.append("영문 이름 «%s»" % m)
        for w in 안씀:
            if w in t and w not in 사람말:
                hits.append("«%s»(쓰지 않는 말 — 무엇이 달라지는지로)" % w)
        for w, alt in 바꿈.items():
            if w in t and w not in 사람말:
                hits.append("«%s» → «%s»" % (w, alt))
    seen, out = set(), []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("NF_TRANSCRIPT", "")
    if not arg or not Path(arg).is_file():
        print("⛔ 이번 턴 기록을 못 받았습니다 — **검사하지 않았습니다.** ⚠️ 이건 「깨끗하다」가 아닙니다.")
        return 0
    try:
        묻는, 답, 사람말 = 이번턴(Path(arg))
    except Exception as e:
        print("⛔ 기록을 못 읽었습니다(%s) — **검사하지 않았습니다.**" % type(e).__name__)
        return 0
    조각 = 묻는 + 질문문단(답)
    hits = 짚을것(조각, 사람말)
    if not hits:
        return 0
    print("🔴 사용자에게 결정을 묻는 글에 개발 용어가 있습니다: " + " · ".join(hits[:8]))
    print()
    print("   묻는 글은 세 칸으로 옮겨 다시 쓰십시오.")
    print("   ① 기술 사실은 접어 둡니다.")
    print("   ② **사용자가 무엇을 할 수 있게 · 못 하게 되는지**를 씁니다 — 이것이 빠지면 사용자가 판단하지 못합니다.")
    print("   ③ 사용자 제품 지식만으로 답할 수 있는 질문을 씁니다.")
    print("   예: «이 방식으로는 가족 공유를 못 넣습니다. 가족 공유가 중요합니까?»")
    print("   ②를 못 쓰겠으면 아직 그 결과를 모르는 것입니다 — 더 알아본 뒤 다시 물으십시오.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
