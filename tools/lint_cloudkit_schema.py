#!/usr/bin/env python3
"""저장 모양이 바뀌었는데 **클라우드킷에 안 알렸나** — 앱 공용.

왜 공용인가 (2026-10-14 에 값을 치르고 배운 모양):
  애플은 개발 쪽 클라우드킷에 **«실제로 한 건 올라간» 모양만** 만든다.
  그래서 새 저장 칸이나 새 저장 모양을 더해도, **아무도 그걸 한 건 안 적으면
  영영 안 생긴다.** 대시보드에서 「Deploy Schema Changes」를 눌러도 **올릴 게 없다.**
  → 테스트플라이트·스토어 빌드에서 **그 칸이 조용히 안 따라온다.**

  ⛔ **빌드는 통과하고 시험도 통과한다.** 앱은 멀쩡히 돌고, 다만 **동기화만 안 된다.**
    그래서 사람이 알아챌 길이 없다 — 기기를 둘 쓰거나 앱을 지웠다 깔아 봐야 안다.

실측(아껴주는 가계부, 2026-10-14):
  · 대시보드 Development 에 `Users` 하나뿐이었다 — 우리 모양이 **하나도 없었다**
  · 즉 **iCloud 동기화가 한 번도 된 적이 없었다.** 「켜는 코드」를 2026-10-05 에
    넣고 **도는지는 아무도 안 봤다.** 아홉 날 동안 적은 것이 기기에만 있었다
  · 앱을 띄우고 한 건 적으니 `CD_StoredEntry` 가, 설정이 올라가니
    `CD_StoredSettings` 가 생겼다. **반복 규칙과 「안 적겠다」 기억은 안 생겼다** —
    쓰다 보니 생기는 것이 아니어서 사람이 손으로 만들어 줘야 했고, 그래서 빠졌다

⭐ 그래서 두 가지를 둔다:
  ① 앱에 **`-warmCloudKit`** 실행 인자 — 모양마다 한 건 넣고 곧바로 치운다
     (클라우드킷은 한 번 생긴 모양을 안 지우므로 그걸로 충분하다)
  ② 이 검사 — **저장 모양이 바뀌었는데 ①을 안 돌렸으면** 말한다

⚠️ **이건 정적 검사다.** 대시보드를 못 본다 — 「Deploy 를 눌렀나」는 끝내 사람만 안다.
   이 검사가 아는 것은 **「모양이 지난번 적어 둔 것과 달라졌나」**까지다.

  사용:  python3 lint_cloudkit_schema.py
         python3 lint_cloudkit_schema.py --적었음
"""
import re
import subprocess
import sys
from pathlib import Path

STAMP = ".cloudkit-schema"


def repo_root() -> Path:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=5)
        if out.returncode == 0:
            return Path(out.stdout.strip())
    except Exception:
        pass
    return Path.cwd()


def models(root: Path) -> dict[str, list[str]]:
    """`@Model` 이 붙은 저장 모양과 그 칸 이름들."""
    out: dict[str, list[str]] = {}
    for f in sorted(root.rglob("*.swift")):
        if "/.build/" in str(f) or "/DerivedData/" in str(f):
            continue
        try:
            text = f.read_text()
        except Exception:
            continue
        if "@Model" not in text:
            continue
        for m in re.finditer(r"@Model\s*\n\s*(?:public\s+)?final class (\w+)", text):
            name = m.group(1)
            body = text[m.end():]
            end = body.find("\n}")
            body = body[:end if end > 0 else len(body)]
            cols = re.findall(r"\n\s+var (\w+)\s*:\s*[^\n{=]+(?:=|$)", body)
            out[name] = sorted(set(cols))
    return out


def registered(root: Path) -> list[str]:
    """`Schema([...])` 에 적힌 것 — 안 적으면 아예 안 올라간다."""
    for f in root.rglob("*App.swift"):
        try:
            t = f.read_text()
        except Exception:
            continue
        m = re.search(r"Schema\(\[([^\]]+)\]\)", t, re.S)
        if m:
            return sorted(re.findall(r"(\w+)\.self", m.group(1)))
    return []


def fingerprint(root: Path) -> str:
    ms = models(root)
    reg = registered(root)
    lines = [f"{n}:{','.join(ms[n])}" for n in sorted(ms)]
    return "\n".join([f"등록:{','.join(reg)}"] + lines) + "\n"


def main() -> int:
    root = repo_root()
    now = fingerprint(root)
    if "@Model" not in "".join(now):
        pass
    if not models(root):
        print("  · 저장 모양(@Model)이 없는 저장소입니다 — 볼 것이 없습니다")
        return 0

    stamp = root / STAMP
    if "--적었음" in sys.argv:
        stamp.write_text(now, encoding="utf-8")
        print(f"  ✅ 지금 모양을 적어 뒀습니다 ({STAMP}) — 이 파일도 같이 올려 두십시오")
        return 0

    old = stamp.read_text(encoding="utf-8") if stamp.exists() else ""
    if old == now:
        print("  ✅ 저장 모양이 지난번 알린 것과 같습니다")
        return 0

    print("🔴 저장 모양이 바뀌었는데 클라우드킷에 알린 기록이 없습니다\n")
    o, n = set(old.splitlines()), set(now.splitlines())
    for line in sorted(n - o):
        print(f"  + {line}")
    for line in sorted(o - n):
        print(f"  - {line}")
    print("""
  ⛔ 그냥 두면 **테스트플라이트·스토어에서 그 칸이 조용히 안 따라옵니다.**
     빌드도 시험도 통과하므로 아무도 못 알아챕니다.

  고치는 길 셋 — 순서가 중요합니다:
    ① iCloud 에 로그인한 기기(시뮬레이터도 됩니다)에서
         xcrun simctl launch <기기> <번들id> -warmCloudKit
       앱에 그 실행 인자가 없으면 먼저 만드십시오(실행 인자를 받으면 모든 레코드 종류를
       한 번씩 저장했다 지우는 작은 코드입니다 — 개발 빌드에서만 돌게 둡니다)
    ② icloud.developer.apple.com → 그 컨테이너 → Deploy Schema Changes
       ⚠️ **이건 사람만 할 수 있습니다** — 프로그램용 통로가 없습니다
    ③ 돌아와서:  python3 lint_cloudkit_schema.py --적었음   (그리고 커밋)

  ⚠️ 이 검사는 대시보드를 못 봅니다. 「눌렀나」는 끝내 사람만 압니다 —
     그래서 ③을 «눌렀다는 사람의 말»로 적습니다.""")
    return 1


if __name__ == "__main__":
    sys.exit(main())
