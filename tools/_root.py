"""프로젝트 루트와 기록 자리를 «도구와 무관하게» 찾는다."""
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


def _git맨위(곳: Path):
    try:
        out = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(곳), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=3)
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip()).resolve()
    except Exception:
        pass
    return None


def _등록된곳(r: Path) -> Path:
    ppl = Path(os.environ.get("NIGHTFLIGHT_HOME") or (Path.home() / ".nightflight")) / "people.tsv"
    try:
        등록 = sorted({c[2] for c in (l.split("\t") for l in ppl.read_text(encoding="utf-8").splitlines())
                     if len(c) > 2 and c[1] == "프로젝트" and c[2]})
    except OSError:
        return r
    if not 등록:
        return r
    실제 = {}
    for e in 등록:
        try:
            if Path(e).is_dir():
                실제.setdefault(Path(e).resolve(), Path(e).resolve())
        except OSError:
            continue
    집 = Path.home().resolve()
    후보 = [r] + [p for p in _위들(r, 집)] + [_git맨위(r)]
    for 원함 in 후보:
        if 원함 is not None and 원함 in 실제:
            return 실제[원함]
    return r


def _위들(r: Path, 집: Path):
    for p in r.parents:
        if p == 집 or p == Path("/"):
            return
        yield p


_뿌리담음: dict = {}


def root() -> Path:
    열쇠 = (tuple(os.environ.get(k, "") for k in _ENV), os.getcwd())
    if 열쇠 not in _뿌리담음:
        _뿌리담음[열쇠] = _root찾기()
    return _뿌리담음[열쇠]


def _root찾기() -> Path:
    for k in _ENV:
        v = os.environ.get(k)
        if v and Path(v).is_dir():
            return _등록된곳(Path(v).resolve())
    t = _git맨위(Path.cwd())
    집 = Path.home().resolve()
    구름 = 집 / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
    if t is not None and t in (Path("/"), 집, 집 / "Desktop", 집 / "Documents", 집 / "Downloads", 집 / "Library", 구름, 구름 / "Desktop", 구름 / "Documents"):
        t = None
    return _등록된곳(t if t else Path.cwd().resolve())


_표식 = "야간비행이 더한 줄"
_표식2 = "야간비행이 더한 줄 (2)"


def _우리줄(l: str) -> bool:
    s = l.strip()
    return s == "" or s.startswith("#") or s in ("*", "/*") or s.startswith("!")


def _우리것걷기(기존: str) -> str:
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


_클로드자리 = {"skills", "commands", "agents", "rules", "hooks", "output-styles", "plugins", "worktrees", "memory",
             "settings.json", "settings.local.json", "launch.json", "CLAUDE.md", "CLAUDE.local.md", "mcp.json", ".mcp.json"}


def _위험한링크(집: Path):
    import os
    plug = str(Path(__file__).resolve().parent.parent)
    try:
        if 집.is_symlink():
            return 집
        if not 집.is_dir():
            return None
        for 첫 in sorted(집.iterdir()):
            if 집.name == ".claude" and 첫.name in _클로드자리:
                continue
            후보 = [첫] + (sorted(첫.iterdir()) if 첫.is_dir() and not 첫.is_symlink() else [])
            for l in 후보:
                if not l.is_symlink() or l.parent.name == "tools" and l.parent.parent == 집:
                    continue
                t = os.readlink(l)
                if t.startswith(plug + os.sep):
                    continue
                if t not in ("", ".", "..") and "/" not in t and (l.parent / t).is_file() and not (l.parent / t).is_symlink():
                    continue
                return l
    except OSError:
        pass
    return None


class 쓰지않는기록폴더(SystemExit):
    pass


def _멈춤(l: Path, r: Path) -> None:
    import sys
    try:
        보일길 = l.relative_to(r)
    except ValueError:
        보일길 = l
    print(f"  ⚠️ 야간비행: 기록 폴더 안에 다른 곳을 가리키는 바로가기가 있어 이 폴더에는 기록하지 않습니다: {보일길}\n"
          "     그 바로가기를 옮기거나 지우시면 다시 기록합니다(야간비행은 바로가기를 지우지 않습니다).", file=sys.stderr)
    raise 쓰지않는기록폴더(3)


SYS = "internal"


def sys_path(state, name: str, read: bool = False) -> Path:
    새 = Path(state) / SYS / name
    if read:
        옛 = Path(state) / name
        return 새 if 새.exists() or not 옛.exists() else 옛
    새.parent.mkdir(parents=True, exist_ok=True)
    return 새


def state_dir(create: bool = False) -> Path:
    r = root()
    for d in _DIRS:
        p = r / d
        if p.is_dir() and (d != ".claude" or (p / "ledger.tsv").is_file()):
            l = _위험한링크(p)
            if l is not None:
                _멈춤(l, r)
            return p
    p = r / _DIRS[0]
    if p.is_symlink():
        _멈춤(p, r)
    if create:
        p.mkdir(parents=True, exist_ok=True)
        _git에서뺀다(p)
    return p


def _git에서뺀다(집: Path) -> None:
    글 = 집.parent / ".claude-plugin" / "plugin.json"
    if 글.is_file() and False:
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
    이름 = "record_dir_claude_gitignore.txt" if 집.name == ".claude" else "record_dir_gitignore.txt"
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
    줄들 = 본문.splitlines()
    if not any(x.startswith("!") for x in 줄들):
        return 본문
    try:
        if subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(집), "rev-parse", "--is-inside-work-tree"],
                          capture_output=True, timeout=10).returncode != 0:
            return 본문
        if 남김.strip():
            길.write_text(남김 + "\n", encoding="utf-8")
        elif 길.exists():
            길.unlink()
        남는 = []
        for x in 줄들:
            if x.startswith("!") and x != "!.gitignore" and "*" not in x:
                if subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(집), "check-ignore", "-q", "--", x[1:]],
                                  capture_output=True, timeout=10).returncode == 0:
                    continue
            남는.append(x)
        return "\n".join(남는) + "\n"
    except (OSError, subprocess.SubprocessError):
        return 본문


def ledger() -> Path:
    return state_dir() / "ledger.tsv"


무거운폴더 = frozenset({".git", "node_modules", "Pods", ".venv", "venv", ".build", "DerivedData", "__pycache__"})


def 훑기(뿌리, 꼴들, 더뺄=()):
    import fnmatch
    뺄 = 무거운폴더 | frozenset(더뺄)
    if isinstance(꼴들, str):
        꼴들 = (꼴들,)
    for d, dirs, files in os.walk(str(뿌리)):
        dirs[:] = sorted(x for x in dirs if x not in 뺄)
        for f in sorted(files):
            if any(fnmatch.fnmatchcase(f, p) for p in 꼴들):
                yield Path(d) / f
