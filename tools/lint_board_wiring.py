#!/usr/bin/env python3
"""«보내는 쪽»과 «읽는 쪽»을 대조한다 — 계산은 되는데 화면에 안 가는 고장을 잡는다.

🔴 왜: 이 저장소에서 **같은 병이 세 번** 나왔다.
  ① `repeat-guard.tsv` 에 423줄이 쌓였는데 조종석에 **한 번도** 안 올라갔다(2026-09-29)
  ② 「됐다 N」·「확인 안 된 것 N」이 계산만 되고 **터미널에만 찍히고 버려졌다**(2026-09-29).
     비개발자가 당하는 가장 흔한 손해가 「만들었다는데 실제로는 아니었다」인데
     **거기에 정면으로 답하는 유일한 숫자**가 그러고 있었다
  ③ 「출시하면 지게 되는 것」(bound)이 2026-09-30 에 만들어졌는데 화면에 **읽는 줄이 없었다**
     — 2026-10-04 에 발견했다. 닷새 동안 아무도 몰랐다

⭐ 왜 사람이 못 보나: **보내는 쪽은 돌고, 읽는 쪽은 «없어도 오류가 안 난다».**
   화면은 빈칸으로 멀쩡해 보이고, 「없음」이 곧 실패 모양이다 —
   이 저장소가 설명 기능에서 이미 적어 둔 그 병이다.

⛔ 그래서 **문서로 적지 않고 검사로 만들었다**(전역 규칙: 검사로 만들 수 있으면 린트로).
   사람의 기억에 맡기면 네 번째가 온다.

보는 것 둘:
  ① **문서 단위** — 보내는 payload 와 화면이 읽는 자리를 짝짓는다
  ② **칸 단위** — 실제로 만들어진 JSON 의 «맨 윗칸»이 화면 어디에도 안 나오나
     ⚠️ ②는 `조종석준비` 를 한 번이라도 돌린 뒤에만 볼 수 있다.
        안 돌렸으면 **「안 봤다」고 말한다** — 0 을 「없었다」로 읽히게 두지 않는다.

사용:  python3 lint_board_wiring.py
종료:  1 = 해당된다(턴 끝에 말한다) · 0 = 깨끗하거나 못 쟀다
"""
import os
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _root

HERE = Path(__file__).resolve().parent.parent
def _보내는것들():
    것들 = [f for f in sorted((HERE / "bin").rglob("*"))
            if f.is_file() and f.suffix in (".py", ".sh")
            and re.search(r'\bw\(\s*["\']\w+\.json["\']', f.read_text(encoding="utf-8", errors="replace"))]
    return 것들


SENDS = _보내는것들()
SEND = SENDS[0] if SENDS else HERE / "bin" / "ledger.sh"
VIEW = HERE / "board" / "cockpit.html"
if os.environ.get("NF_BOARD_VIEW"):
    VIEW = Path(os.environ["NF_BOARD_VIEW"])

SKIP_DOC = {
}
SKIP_KEY = {
    "updatedAt": "화면이 showFresh() 안에서 쓴다 — 이름이 아니라 값으로만 지나간다",
    "stage": "drawTrack(last.stage, …) 로 변수에 담아 쓴다",
    "stageLabel": "같은 자리에서 last.label 로 담아 쓴다",
    "loose": "stages 안의 «미연결» 묶음 — drawTrack 의 넷째 인자다",
    "per": "stages 안의 단계별 묶음 — drawTrack 의 셋째 인자다",
    "items": "stuck·feed 가 공통으로 쓰는 바깥 이름이다",
    "by": "bound 안의 갈래 묶음 — Object.keys(b.by) 로 돈다",
    "total": "bound 의 합 — b.total 로 쓴다",
    "unsaid": "bound 의 «안 적힌 것» — b.unsaid 로 쓴다",
    "막힌것": "해 봤는데 안 된 것의 수 — AI가 일한 양", "못한것": "같은 갈래의 수",
    "확인된것": "함께 바뀌는 곳 중 확인된 수 — AI가 일한 양", "확인안된것": "같은 갈래의 수",
    "출처있음": "만드는 법 중 출처 있는 수 — AI가 일한 양", "출처없음": "같은 갈래의 수",
    "모른낱말": "기록 형식이 틀린 줄 — 터미널이 알린다", "verified": "확인한 완료의 수 — AI가 일한 양",
    "verifyKinds": "확인 방법별 수 — AI가 일한 양", "blocksNoWhy": "근거 없는 막음의 수 — 기록 형식",
    "blocksNoIfNot": "«안 막았으면»이 빈 옛 막음의 수 — 기록 형식",
    "두뇌있음": "출시 절차 판정에 서버 자료가 있었나 — 판정 결과가 이미 말한다",
    "미연결주제": "기록 주제가 기능에 안 이어진 것 — 설계표가 진행경과를 대신한다",
    "주제없음": "주제 없는 기록의 수 — 기록 형식",
    "unverified": "확인 안 된 완료 기록의 수 — 확인 요청 때 대화창에서 말한다",
    "noVerifyColumn": "확인 방법 칸이 빈 옛 완료 기록의 수 — 기록 형식",
}


def main() -> int:
    if not SENDS or not VIEW.exists():
        print("  ⚠️ 보내는 쪽·읽는 쪽 파일을 못 찾아 **재지 못했습니다**")
        print(f"     찾은 자리: {[str(x) for x in SENDS]} · {VIEW}")
        return 0

    send_src = "\n".join(f.read_text(encoding="utf-8") for f in SENDS)
    view_src = VIEW.read_text(encoding="utf-8")
    sent = set(re.findall(r'w\(\s*"([A-Za-z0-9_]+)\.json"', send_src))
    read = set(re.findall(r"""db\.doc\(\s*['"]state/([A-Za-z0-9_]+)['"]""", view_src))

    bad = []
    for n in sorted(sent - read - set(SKIP_DOC)):
        bad.append(f"  🔴 「{n}」을 보내는데 화면이 읽지 않습니다 — 계산만 되고 버려집니다")
        bad.append("     보내는 자리: %s 의 w(\"%s.json\")"
                   % (" · ".join(str(x.relative_to(HERE)) for x in SENDS), n))
        bad.append(f"     붙일 자리:   board/cockpit.html 에 db.doc('state/{n}')")
    SCREEN_WRITES = {"pressed"}
    for n in sorted(read - sent - SCREEN_WRITES):
        bad.append(f"  🔴 화면이 「{n}」을 읽는데 보내는 쪽이 없습니다 — 영원히 빈칸입니다")

    try:
        board = _root.state_dir() / "board"
    except Exception:
        board = None
    if not board or not board.is_dir():
        print("  ⚠️ 칸 단위는 **재지 못했습니다** — `ledger.sh 조종석준비` 를 아직 안 돌렸습니다")
        print("     (이건 「문제가 없었다」가 아니라 「안 봤다」입니다)")
    else:
        for f in sorted(board.glob("*.json")):
            if f.stem not in read:
                continue
            try:
                keys = list(json.loads(f.read_text(encoding="utf-8")).keys())
            except Exception:
                continue
            for k in keys:
                if k in SKIP_KEY or re.search(rf"(?<!\w){re.escape(k)}(?!\w)", view_src):
                    continue
                bad.append(f"  ⚠️ 「{f.stem}」의 칸 「{k}」이 화면에 한 번도 안 나옵니다")
                bad.append("     보내기만 하고 안 쓰는 칸입니다 — 쓰거나, 안 보냅니다")

    돌려주는함수 = ("단계그림", "지도HTML", "한줄요약", "범례")
    for 이름 in 돌려주는함수:
        m = re.search(rf"function {re.escape(이름)}\s*\([^)]*\)\s*\{{", view_src)
        if not m:
            continue
        깊이, i, 끝 = 0, m.end() - 1, len(view_src)
        while i < 끝:
            c = view_src[i]
            if c == "{":
                깊이 += 1
            elif c == "}":
                깊이 -= 1
                if 깊이 == 0:
                    break
            i += 1
        몸통 = view_src[m.end():i]
        for 쓰는말 in ("박.innerHTML", "박.hidden", "document.getElementById", "$("):
            if 쓰는말 in 몸통:
                bad.append(f"  ⛔ 「{이름}」은 글을 돌려주는 함수인데 안에서 「{쓰는말}」을 씁니다")
                bad.append("     화면에 바로 쓰면 그 함수를 부르는 쪽이 통째로 멈춥니다 — `return` 으로 돌려줍니다")

    if not bad:
        print("  ✅ 조종석 배선 — 보내는 것과 읽는 것이 맞습니다")
        return 0
    print("── 조종석 배선 ────────────────────────────────")
    print("\n".join(bad))
    return 1


if __name__ == "__main__":
    sys.exit(main())
