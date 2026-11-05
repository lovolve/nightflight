#!/usr/bin/env python3
"""SECURITY DEFINER 함수의 실행 권한이 «정말» 막혔는지 본다 — 앱 공용."""
import os
import re
import subprocess
import sys
from pathlib import Path


def _rec(kind, line, why, if_not=""):
    led = Path(__file__).resolve().parent.parent / "bin" / "ledger.sh"
    if not os.access(led, os.X_OK):
        return
    try:
        subprocess.run([str(led), kind, line, why, if_not], capture_output=True, timeout=5)
    except Exception:
        pass

FUNC = re.compile(r"create\s+(?:or\s+replace\s+)?function\s+(?:public\.)?(\w+)", re.I)
DEFINER = re.compile(r"security\s+definer", re.I)
RETURNS_TRIGGER = re.compile(r"returns\s+trigger", re.I)
REVOKE = re.compile(
    r"revoke\s+[^;]*?\bon\s+function\s+(?:public\.)?(\w+)[^;]*?\bfrom\s+([^;]+);", re.I | re.S)
DEFAULT_PRIV = re.compile(
    r"alter\s+default\s+privileges[^;]*?revoke\s+[^;]*?on\s+functions[^;]*?from\s+([^;]+);", re.I | re.S)


def find_migration_dirs(args):
    if args:
        return [Path(a) for a in args]
    try:
        root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        root = Path.cwd()
    d = root / "supabase" / "migrations"
    return [d] if d.is_dir() else []


def check(mig_dir: Path):
    sqls = sorted(mig_dir.glob("*.sql"))
    if not sqls:
        return [], [], []
    whole = "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in sqls)

    blanket = any("public" in m.group(1).lower() for m in DEFAULT_PRIV.finditer(whole))

    revoked: dict[str, set[str]] = {}
    for m in REVOKE.finditer(whole):
        roles = {r.strip().strip('"').lower() for r in m.group(2).split(",")}
        revoked.setdefault(m.group(1), set()).update(roles)

    problems, ok, review = [], [], []
    for f in sqls:
        text = f.read_text(encoding="utf-8", errors="ignore")
        for m in FUNC.finditer(text):
            name = m.group(1)
            tail = text[m.end():m.end() + 2000]
            if not DEFINER.search(tail):
                continue
            if RETURNS_TRIGGER.search(tail):
                continue
            roles = revoked.get(name, set())
            if blanket or "public" in roles:
                ok.append(name)
            elif roles:
                problems.append((f.name, name,
                                 f"revoke 대상이 {sorted(roles)} 뿐 — **PUBLIC 상속이 남는다**"))
            else:
                review.append((f.name, name))
    return problems, ok, review


def main():
    dirs = find_migration_dirs(sys.argv[1:])
    if not dirs:
        print("supabase/migrations 를 못 찾았다. 폴더를 인자로 줄 것.")
        return 0
    bad = 0
    for d in dirs:
        problems, ok, review = check(d)
        label = d.parent.parent.name
        if not problems and not ok and not review:
            print(f"  {label:18s} SECURITY DEFINER 함수 없음")
            continue
        if problems:
            bad += len(problems)
            _rec("막음",
                 "남의 정보를 볼 수 있는 문이 열린 채로 있던 것",
                 f"Supabase 권한 검사 — {label} {len(problems)}건 (막으려 했는데 PUBLIC 상속이 남음)",
                 "로그인만 한 사람이 남의 연락처와 주문을 그대로 볼 수 있었습니다")
            print(f"  🔴 {label:16s} {len(problems)}건 — **막으려 했는데 안 막혔다**(그 함정)")
            for fn, name, why in problems:
                print(f"       {name}()  {why}   ({fn})")
        else:
            print(f"  ✅ {label:16s} 막으려 한 것은 전부 PUBLIC 까지 차단 (revoke 있는 함수 {len(ok)}개)")
        if review:
            names = sorted({n for _, n in review})
            print(f"     🟡 확인 필요 {len(names)}개 — SECURITY DEFINER 인데 revoke 가 없다.")
            print(f"        토큰으로 지키는 anon 전용 RPC 면 정상이다. 아니면 열려 있는 것이다.")
            print(f"        {', '.join(names[:8])}{' …' if len(names) > 8 else ''}")
    if bad:
        print("\n  고치는 법:  revoke all on function <이름>(<인자>) from public, anon;")
        print("  그리고 앞으로를 막으려면:")
        print("    alter default privileges in schema public revoke execute on functions from public, anon;")
        print("  ⚠️ 고친 뒤에도 **배포 후 Supabase 어드바이저**를 본다 — 정적 검사는 「썼는가」까지만 안다.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
