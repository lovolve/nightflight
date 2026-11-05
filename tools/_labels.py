"""야간비행 도구"""
from pathlib import Path

안보임 = "안 보이는 작업"
종류표 = {
    "됐다": ("새 기능", "문제 고침", 안보임),
    "남은것": ("새 기능", "문제 고침", "대표님 결정 필요", 안보임),
    "표준": ("사용자에게 보이는 것", 안보임),
    "시도": ("사용자에게 보이는 것", 안보임),
    "영향": ("사용자에게 보이는 것", 안보임),
}
모든종류 = tuple(sorted({v for vs in 종류표.values() for v in vs}))


def _rows(p: Path):
    if not p.exists():
        return []
    return [l.rstrip("\n").split("\t") for l in p.read_text(encoding="utf-8").splitlines()
            if "\t" in l and not l.startswith("#")]


def 항목표(state: Path) -> dict:
    out = {}
    for c in _rows(Path(state) / "item-labels.tsv"):
        out[c[0]] = ((c[1] or None) if len(c) > 1 else None, (c[2] or None) if len(c) > 2 else None)
    return out


def 기록표(state: Path) -> dict:
    out = {}
    for c in _rows(Path(state) / "feed-labels.tsv"):
        if len(c) >= 3:
            out[c[0]] = (c[1], c[2], (c[3] or None) if len(c) > 3 else None)
    return out


def 종류(표: dict, 원문: str):
    if 원문.startswith("사용자에게 보이는 변화는 없습니다"):
        return 안보임
    return 표.get(원문, (None, None))[1]


def 붙이기(표: dict, row: dict, 원문: str) -> dict:
    row["이름표"] = 표.get(원문, (None, None))[0]
    row["종류"] = 종류(표, 원문)
    return row
