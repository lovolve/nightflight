#!/usr/bin/env python3
"""「정리해줘」를 알아듣고 모델에게 무엇을 돌릴지 알린다."""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 믿는글 import 사용자가_쓴_말, 조종석주소

try:
    prompt = 사용자가_쓴_말((json.load(sys.stdin) or {}).get("prompt", "") or "")
except Exception:
    prompt = ""
here = os.environ["HERE"]
tools = os.path.join(os.path.dirname(here), "tools")

안함 = re.search(r"(하지\s*(마|말)|말아|말고|안\s*해도|않아도|하면\s*안|안\s*돼)", prompt)
정리말 = None if 안함 else re.search(r"(정리|치워|치우|비워|지워)", prompt)
시뮬 = re.search(r"(시뮬레이터|시뮬|가짜 ?전화기)", prompt)
공간 = re.search(r"(저장공간|저장 공간|디스크|용량|빈 ?용량)", prompt)
메모리 = re.search(r"(메모리|램|RAM|스왑)", prompt)
맨말 = bool(re.fullmatch(r"\s*(컴퓨터\s*)?(좀\s*)?(정리|치워)\s*(해\s*줘|해줘|줘|해|해주세요|해 주세요)?\s*", prompt))

say = []
if 정리말 and (시뮬 or 맨말):
    say.append(
        "야간비행: 사용자가 시뮬레이터를 정리해 달라고 하셨습니다. "
        "`" + here + "/resources.sh --정리` 를 돌리고, 나온 줄을 그대로 전하십시오. "
        "⭐ 이것은 되돌릴 수 있는 일입니다(다시 켜면 됩니다) — 따로 여쭙지 않아도 됩니다. "
        "⛔ 다만 돌린 «뒤»에 무엇이 꺼졌는지 수로 말씀드리십시오. 「정리했습니다」만 말하지 마십시오.")
if 정리말 and (공간 or 맨말):
    say.append(
        "야간비행: 사용자가 저장공간을 정리해 달라고 하셨습니다. "
        "⛔ 바로 지우지 마십시오. 먼저 `" + tools + "/clean_disk.sh` 를 **그대로**(인자 없이) 돌리면 "
        "무엇을 얼마나 지울지 **보여만** 줍니다. 그 목록을 사용자에게 그대로 전하고, "
        "«예»를 받은 뒤에만 같은 명령에 `--apply` 를 붙여 돌리십시오. "
        "⛔ 지운 «뒤»에 실제로 줄었는지 확인하고, 실패한 것은 실패라고 적으십시오 "
        "(그 도구 머리에 적힌 사고 이력입니다 — 실패를 성공으로 찍은 적이 있습니다).")

if 정리말 and (메모리 or 맨말):
    say.append(
        "야간비행: 사용자가 메모리를 정리해 달라고 했습니다. "
        "먼저 `" + tools + "/machine.py --메모리` 를 돌려 나온 목록을 그대로 전하십시오(합계 · 다시 여는 장치 · 클로드 대화 · 클로드 앱 · 그 밖의 앱). "
        "⛔ 아무것도 먼저 닫지 마십시오 — 닫을 것은 사용자가 고릅니다. 그다음 아래 차례로 제안하십시오(2026-10-27 실측에서 나온 것). "
        "① «다시 여는 장치»가 나왔으면: 그것을 먼저 꺼야 닫은 대화가 다시 안 열린다고 말하고, «예»를 받으면 "
        "`launchctl bootout gui/$(id -u)/<그 이름>` 뒤 그 파일 이름 끝에 `.retired-<오늘 날짜>` 를 붙여 둡니다(지우지 않음 — 되돌릴 수 있게). "
        "⚠️ 그 장치가 휴대폰 원격 제어용이면 닫은 뒤 휴대폰에서 그 대화에 못 들어간다고 먼저 말하십시오. "
        "② 터미널 대화: 고른 것만 닫습니다(그 대화가 `tmux` 안이면 `tmux kill-session`, 아니면 정상 종료). 기록은 남는다고 말하십시오. "
        "③ 클로드 앱 안 대화: 터미널에서 닫지 않습니다 — 사용자가 앱에서 그 대화를 닫게 안내하십시오(폴더 · 켠 날로 어느 것인지 알려 드림). "
        "④ «가장 큰 창»이 1.5GB 를 넘으면: 클로드 앱을 한 번 껐다 켜면 처음 크기로 돌아간다고 제안하십시오. 모든 대화가 멈추므로 한가할 때 사용자가 직접 하게 합니다. "
        "⑤ «작은 화면 칸»: 이 대화가 연 내장 브라우저 탭이 남아 있으면(tabs_context 로 확인) 닫으십시오 — 숨은 채로 메모리를 씁니다. "
        "⛔ 닫은 «뒤»에 `machine.py --메모리` 를 다시 돌려 합계와 스왑이 얼마나 줄었는지 수로 말씀드리십시오.")

조종석말 = len(prompt) <= 80 and re.search(r"조종석\s*(을|를|좀|창|화면)?\s*(좀\s*)?(열어|열기|열자|열 ?수|띄워|보여 ?줘|켜 ?줘)", prompt)
if 조종석말:
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    주소 = 조종석주소(os.path.join(root, ".nightflight")) or 조종석주소(os.path.join(root, ".claude"))
    if 주소:
        say.append("야간비행: 사용자가 조종석을 열어 달라고 하셨습니다. Artifact 도구를 action \"open\" · url " + 주소 + " 로 한 번만 부르십시오 — "
                   "대화창에 «열림» 버튼이 있는 조종석 창이 뜹니다. 사용자에게는 «아래 조종석 창의 ‹열림›을 누르시면 됩니다» 한 줄만 말하십시오. "
                   "⛔ 조종석열기 · 브라우저 · 크롬 · 다른 창은 쓰지 마십시오(로그인을 또 하게 됩니다).")
    else:
        say.append("야간비행: 사용자가 조종석을 열어 달라고 하셨는데 이 프로젝트의 조종석 주소가 아직 없습니다. "
                   "⛔ 조종석열기 · 브라우저 · 다른 창으로 열지 마십시오. 조종석을 올리는 안내(턴 끝 자동 점검)를 따라 먼저 올리고, 그다음 Artifact action \"open\" 으로 여십시오. "
                   "전에 올리지 않기로 했다면 다시 올릴지 먼저 묻고, 그렇다고 하면 `" + os.path.join(here, "ledger.sh") + " 조종석동의 네` 를 돌리십시오.")

if len(prompt) <= 80 and re.search(r"조종석\s*(을|를|좀)?\s*(좀\s*)?(올려|올리자)", prompt):
    try:
        동의 = open(os.path.join(os.environ.get("NIGHTFLIGHT_HOME") or os.path.expanduser("~/.nightflight"), "조종석동의"), encoding="utf-8").read().strip()
    except OSError:
        동의 = ""
    if 동의 == "아니오":
        say.append("야간비행: 사용자가 조종석에 올려 달라고 하셨습니다. `" + os.path.join(here, "ledger.sh") + " 조종석동의 네` 를 돌리십시오. "
                   "그러면 이번 턴 끝 안내가 올리는 차례를 알려 줍니다.")

if re.search(r"(야간비행|플러그인)[^.\n?]{0,8}(업데이트|최신 ?판으로|새 ?판으로)[^.\n?]{0,4}(해 ?줘|해 ?주세요|해 ?주십시오|하자|합시다|부탁|해$|해\.)", prompt.strip()):
    say.append(
        "야간비행: 사용자가 야간비행 업데이트를 요청하셨습니다. 차례대로 하십시오. "
        "클로드 코드: `claude plugin marketplace update lovolve` 뒤 `claude plugin update nightflight@lovolve -y`. "
        "`claude` 명령이 없으면 클로드 앱 안의 실행 파일을 찾아 쓰십시오. "
        "Codex: `codex plugin marketplace upgrade lovolve` 뒤 `codex plugin add nightflight@lovolve`. "
        "⛔ 끝난 «뒤»에 명령 출력에서 판 번호를 확인해 전하고, 실패하면 실패라고 말하십시오. "
        "그다음 앱을 다시 시작해야 적용된다고 말하십시오. Codex 는 `/hooks` 에서 다시 승인해야 할 수 있다고 함께 말하십시오.")

if say:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                             "additionalContext": "\n".join(say)}},
                     ensure_ascii=False))
