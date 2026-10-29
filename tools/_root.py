"""프로젝트 루트와 기록 자리를 «도구와 무관하게» 찾는다.

🔴 왜 (
   그리고 「나도 커서를 썼었어. **vscode로 코딩을 할 줄 모르는거지, 비개발자 중에도
   그 툴 자체를 아예 안 쓰는 건 아니야. 성급하게 배제할 필요가 아예 없어**」
   → ⛔ 내가 「비개발자는 Cursor 에 없다」고 **확인 없이 단정했다.** 창업자가 반례다.
     비개발자가 앱을 만들려 하면 튜토리얼이 Cursor 를 깔라고 한다 — **거기 앉아 있고
     코딩만 못 한다.** 그게 야간비행 타깃이다.

⭐ 실측(2026-10-03): 훅은 Codex 가 **클로드와 이벤트 이름·stdin JSON 모양이 같아**
   «안 고치고 돈다». Cursor 는 이름이 다르지만 Polyhook 같은 어댑터가 이미 있다.
   MCP 는 Linux Foundation 표준이고 주요 클라이언트가 모두 받는다.
   → **남은 의존이 「환경변수 이름」과 「기록 디렉터리」 둘뿐이었다.** 그 둘을 여기서 없앤다.

⛔ 못: **도구 목록을 박지 않는다.** 새 도구가 나오면 또 고쳐야 하기 때문이다.
   환경변수를 «여러 개 시도»하고, 없으면 **git 루트**, 그것도 없으면 현재 위치다.
"""
import json
import os
import subprocess
from pathlib import Path

_ENV = ("NIGHTFLIGHT_PROJECT_DIR",
        "CLAUDE_PROJECT_DIR",
        "CODEX_PROJECT_DIR",
        "CURSOR_PROJECT_DIR",
        "PROJECT_ROOT")

_DIRS = (".nightflight", ".claude")


def root() -> Path:
    """프로젝트 루트."""
    for k in _ENV:
        v = os.environ.get(k)
        if v and Path(v).is_dir():
            return Path(v).resolve()
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=3)
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip()).resolve()
    except Exception:
        pass
    return Path.cwd().resolve()


_표식 = "야간비행이 더한 줄"
_표식2 = "야간비행이 더한 줄 (2)"


def _우리줄(l: str) -> bool:
    s = l.strip()
    return s == "" or s.startswith("#") or s in ("*", "/*") or s.startswith("!")


def _우리것걷기(기존: str) -> str:
    """옛 표식 줄부터 끝까지가 우리 줄뿐이면 걷는다 · 우리가 통째로 쓴 파일(첫 줄이 우리 자료의 첫 줄)이면 통째로 걷는다."""
    줄 = 기존.split("\n")
    자름 = len(줄)
    for i, l in enumerate(줄):
        if l.startswith("# \u2500\u2500 " + _표식 + " "):
            자름 = i
            break
    if not all(_우리줄(l) for l in 줄[자름 + 1:]):
        자름 = len(줄)
    if 줄 and 줄[0].startswith("# 야간비행이 이 폴더에 적는 것은") and all(_우리줄(l) for l in 줄[:자름]):
        자름 = 0
    return "\n".join(줄[:자름]).rstrip("\n")


def state_dir(create: bool = False) -> Path:
    """기록이 사는 디렉터리. 이미 있는 것을 쓰고, 없으면 첫 번째를 만든다."""
    r = root()
    for d in _DIRS:
        p = r / d
        if p.is_dir() and (d != ".claude" or (p / "ledger.tsv").is_file()):
            return p
    p = r / _DIRS[0]
    if create:
        p.mkdir(parents=True, exist_ok=True)
        _git에서뺀다(p)
    return p


def _git에서뺀다(집: Path) -> None:
    """기록 폴더를 **받는 분의 저장소에 안 올라가게** 한다 (2026-10-25 레드팀 4회차).

    🔴 왜: 여기에는 그분의 컴퓨터 상태·정하신 것·조종석 주소가 쌓인다. 공개 저장소를
      쓰시면 그것이 누구에게나 보인다. 우리 저장소는 자기 것을 막아 두고 **받는 분 것은
      안 막고 있었다**(그 장치가 0곳이었다).
    ⭐ 본문의 주인은 `data/기록폴더-gitignore.txt` 하나다 — 셸 쪽(`nf_state_make`)도 그것을 쓴다.
    ⛔ 이미 있으면 **안 덮고 «덧붙인다»** (2026-10-25 레드팀 6회차 · 옆 대화가 짚었다).
      🔴 전에는 있으면 그냥 돌아섰다. 그래서 받는 분 폴더에 `.claude/.gitignore` 가 이미
        있으면(클로드 코드가 만들어 두는 일이 흔하다) 기록이 그분 저장소에 그대로 커밋됐다 —
        실측으로 `ledger.tsv`·`board/*.json` 열일곱 개가 담겼다.
      ⭐ 덧붙이기는 그분이 적어 두신 줄을 **한 글자도 안 건드린다.**
      ⭐ 표식(`_표식`)으로 **두 번 안 붙인다** — 셸 쪽(`NF_GI_MARK`)과 **같은 글자**다.
        ⛔ 두 곳이 어긋나면 한쪽이 매 턴 또 붙여서 파일이 자란다.
    """
    글 = 집.parent / ".claude-plugin" / "plugin.json"
    if 글.is_file() and (집.parent / ".nightflight-dev").is_file():
        try:
            if json.loads(글.read_text(encoding="utf-8")).get("name") == "nightflight":
                return
        except (OSError, ValueError):
            pass
    길 = 집 / ".gitignore"
    기존 = ""
    if 길.exists():
        try:
            기존 = 길.read_text(encoding="utf-8")
        except OSError:
            return
        if _표식2 in 기존:
            return
    이름 = "기록폴더-claude-gitignore.txt" if 집.name == ".claude" else "기록폴더-gitignore.txt"
    본문 = "*\n!.gitignore\n"
    자료 = Path(__file__).resolve().parent.parent / "data" / 이름
    try:
        if 자료.is_file():
            본문 = 자료.read_text(encoding="utf-8")
        남김 = _우리것걷기(기존) if 기존 else ""
        본문 = _손님이뺀것은안살림(집, 길, 남김, 본문)
        덩어리 = "# \u2500\u2500 %s \u2500\u2500 시작\n%s\n# \u2500\u2500 %s \u2500\u2500 끝\n" % (_표식2, 본문.rstrip("\n"), _표식2)
        길.write_text((남김 + "\n\n" if 남김.strip() else "") + 덩어리, encoding="utf-8")
    except OSError:
        pass


def _손님이뺀것은안살림(집: Path, 길: Path, 남김: str, 본문: str) -> str:
    """🔴 14회차(설치 재현): `.claude` 꼴의 «되살림» 줄(`!settings.json` …)이 손님이 일부러 뺀 파일을 다시 커밋에 담았다
    (아래 폴더의 `!` 는 위 폴더의 제외를 이긴다). ⭐ 우리 덩이 없이 손님 규칙만으로 먼저 물어보고, 손님이 뺀 이름은 되살리지 않는다.
    셸 쪽(`nf_state_make`)과 같은 규칙이다. `*` 가 든 줄은 이름을 하나로 못 정해 그대로 둔다."""
    줄들 = 본문.splitlines()
    if not any(x.startswith("!") for x in 줄들):
        return 본문
    try:
        if subprocess.run(["git", "-C", str(집), "rev-parse", "--is-inside-work-tree"],
                          capture_output=True, timeout=10).returncode != 0:
            return 본문
        if 남김.strip():
            길.write_text(남김 + "\n", encoding="utf-8")
        elif 길.exists():
            길.unlink()
        남는 = []
        for x in 줄들:
            if x.startswith("!") and x != "!.gitignore" and "*" not in x:
                if subprocess.run(["git", "-C", str(집), "check-ignore", "-q", "--", x[1:]],
                                  capture_output=True, timeout=10).returncode == 0:
                    continue
            남는.append(x)
        return "\n".join(남는) + "\n"
    except (OSError, subprocess.SubprocessError):
        return 본문


def ledger() -> Path:
    return state_dir() / "ledger.tsv"
