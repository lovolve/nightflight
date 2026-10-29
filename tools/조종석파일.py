#!/usr/bin/env python3
"""조종석을 **파일 하나로** 짓는다 — 클로드가 없는 자리에서도 열리게.

🔴 왜 (2026-10-24  — 코덱스·제미나이·커서):
   조종석은 claude.ai 아티팩트 안에서만 섰다. 자료가 `claude.use('db')` **하나로만** 들어왔고
   그 파일에 대비하는 자리가 **0곳**이었다 — 다른 도구에서는 **빈 화면**이다.
   ⭐ 대시보드(`gen_projects_board.py`)는 이미 자료를 **박아서** 파일로 낸다. 같은 길을 쓴다.
   ⭐  — 클로드에서는 지금처럼 아티팩트, 다른 데서는 파일.


1. **실시간이라고 말하지 않는다.** 박힌 값은 «언제 적은 판»이다. 화면이 그 때를 같이 찍는다.
   ⛔ 멈춘 값을 지금 값으로 읽게 두면, 그게 「0 이 안전처럼 보이는」 것과 같은 병이다.
2. **아티팩트 쪽을 안 건드린다.** 원본(`board/cockpit.html`)의 자리는 `null` 그대로다 —
   클로드 안에서는 **실시간이 이긴다.**
3. **자리가 없으면 멈춘다.** 원본에서 `/*__BOARD__*/null` 을 못 찾으면 **짓지 않는다** —
   조용히 자료 없는 판을 내면 「기록이 비었다」로 읽힌다.
4. **칸이 비어도 짓는다.** 첫 대화 전에는 칸이 없다 — 그때는 화면이
   「기록이 아직 비어 있습니다」라고 말한다(0 을 「없다」로 안 읽는 자리다).

사용:  python3 조종석파일.py [제품폴더]      → 그 제품의 기록 폴더 안에 조종석.html
끝값:  1 = 못 지었다 · 0 = 지었다
"""
from __future__ import annotations
import json
import sys
from datetime import datetime
from pathlib import Path

여기 = Path(__file__).resolve().parent
sys.path.insert(0, str(여기))
import _root

자리 = "/*__BOARD__*/null"


def 기록집(뿌리: Path) -> Path:
    """기록이 사는 폴더. ⛔ `.claude` 를 **박지 않는다** — 새 앱은 `.nightflight` 를 쓴다.
    🔴 처음에 박아 뒀다가 묶음이 잡았다(2026-10-24): `.nightflight` 를 쓰는 제품에
      `.claude` 를 **새로 만들어** 기록 자리가 둘로 갈렸다. `_root.py` 가 보는 차례와 같게 맞춘다."""
    for d in _root._DIRS:
        if (뿌리 / d).is_dir():
            return 뿌리 / d
    return 뿌리 / _root._DIRS[0]


def 짓는다(뿌리: Path) -> Path | None:
    원본 = 여기.parent / "board" / "cockpit.html"
    if not 원본.exists():
        print("  ⛔ 조종석 원본을 못 찾았습니다: %s" % 원본)
        return None
    글 = 원본.read_text(encoding="utf-8")
    if 자리 not in 글:
        print("  ⛔ 조종석에 자료를 박을 자리가 없습니다 — 짓지 않았습니다.")
        print("     (원본이 바뀌었을 수 있습니다. 그 자리를 되살린 뒤 다시 부르십시오.)")
        return None

    집 = 기록집(뿌리)
    판 = {}
    칸집 = 집 / "board"
    if 칸집.is_dir():
        for f in sorted(칸집.glob("*.json")):
            try:
                판[f.stem] = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                pass
    판["적은때"] = datetime.now().strftime("%m-%d %H:%M")

    나갈곳 = 집 / "조종석.html"
    나갈곳.parent.mkdir(parents=True, exist_ok=True)
    박음 = json.dumps(판, ensure_ascii=False).replace("</", "<\\/")
    몸 = 글.replace(자리, "/*__BOARD__*/" + 박음, 1)
    껍질 = ('<!DOCTYPE html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '</head>\n<body>\n')
    나갈곳.write_text(껍질 + 몸 + "\n</body>\n</html>\n", encoding="utf-8")
    print("  ✅ 조종석을 파일로 지었습니다 — 칸 %d개 · %s" % (len(판) - 1, 나갈곳))
    if len(판) - 1 == 0:
        print("     ⚠️ 칸이 **하나도 없습니다** — 첫 대화를 하면 채워집니다.")
        print("        (「기록이 없다」가 아니라 「아직 안 적혔다」입니다.)")
    return 나갈곳


if __name__ == "__main__":
    인자 = [a for a in sys.argv[1:] if not a.startswith("-")]
    표 = [a for a in sys.argv[1:] if a.startswith("-")]
    if [t for t in 표 if t not in ("-h", "--help")]:
        print("  ⛔ 모르는 표가 있습니다: %s" % " ".join(표))
        print("     쓰는 법:  조종석파일.py [제품 폴더]")
        sys.exit(1)
    if 표:
        print(__doc__)
        sys.exit(0)
    뿌리 = Path(인자[0]).resolve() if 인자 else _root.root()
    if not 뿌리.is_dir():
        print("  ⛔ 그런 폴더가 없습니다: %s" % 뿌리)
        print("     만들지 않았습니다. 폴더 이름을 보아 주십시오.")
        sys.exit(1)
    sys.exit(0 if 짓는다(뿌리) else 1)
