#!/usr/bin/env python3
"""새 표(public)를 만들면 «누가 읽고 쓸 수 있나»를 같이 적었는지 본다 — 앱 공용.

왜 있나 (2026-10-21):
  Supabase 가 **2026-10-30** 부터 기존 프로젝트에도 바꾼다 — public 에 새로 만든 표에
  공개 열쇠 · 로그인 사용자 · 서버 쪽 역할 권한을 **자동으로 붙이지 않는다.**
  (공지: supabase.com/changelog/45329 · 이미 있는 표는 그대로)
  그 뒤로 권한을 안 적은 새 표는 앱·엣지 함수에서 `42501 permission denied` 로 막힌다.
  (Supabase 를 쓰는 앱 전부).

  ⭐ 반대쪽 사고도 같이 막는다 — 2026-10-20 야간비행에서 새 표가 **자동 권한 때문에** 공개 열쇠로
     열려 있었다(RLS 가 막아서 새지는 않았다). 그래서 «GRANT 를 적어라»가 아니라
     **«GRANT 든 REVOKE 든 하나는 적어라 — 정한 것을 글로 남겨라»** 를 본다.

  ⛔ 이 파일의 원본은 `~/appkit-shared/tools/` 다. 앱마다 복사본이 있다 — 고치면 원본을 고치고 다시 나눈다.
  ⛔ 앱 이름·프로젝트 번호를 박지 않는다(이식 사고 2026-09-12). 이 검사는 글만 본다.

무엇을 «적었다»로 치나:
  · `grant … on [table] <표> … to …`   · `revoke … on [table] <표> … from …`
  · `grant … on all tables in schema public to …` (그 파일 이후 전부)
  어느 쪽이든 그 표를 만든 파일이나 그 뒤 파일에 있으면 된다.

언제부터 보나: 이름이 `YYYYMMDDHHMMSS_…` 인 마이그레이션은 이름의 날짜로, 아니면 파일 수정일로
  `--부터` 날짜(기본 2026-10-21) 이후 것만 본다. 그 전에 만든 표는 자동 권한을 이미 받았다 — 다시 보지 않는다.

  사용:  python3 lint_table_grants.py [마이그레이션_폴더 …] [--부터 YYYY-MM-DD]
         (폴더를 안 주면 현재 저장소의 supabase/migrations)
  끝값:  0 = 빠진 것 없음 · 1 = 빠진 표 있음 · 폴더가 없으면 0 이지만 「못 봤다」고 말한다
"""
import os
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

IDENT = r'(?:"[^"]+"|[\w가-힣]+)'
CREATE = re.compile(
    r"create\s+(?:unlogged\s+)?table\s+(?:if\s+not\s+exists\s+)?(?:(" + IDENT + r")\s*\.\s*)?(" + IDENT + r")",
    re.I)
TEMP = re.compile(r"create\s+(?:global\s+|local\s+)?temp(?:orary)?\s+table", re.I)
GRANT_ON = re.compile(r"\bgrant\s+[^;]*?\bon\s+(?:table\s+)?([^;]*?)\s+to\s+", re.I | re.S)
REVOKE_ON = re.compile(r"\brevoke\s+[^;]*?\bon\s+(?:table\s+)?([^;]*?)\s+from\s+", re.I | re.S)
ALL_PUBLIC = re.compile(r"\bgrant\s+[^;]*?\bon\s+all\s+tables\s+in\s+schema\s+public\b", re.I | re.S)
COMMENT = re.compile(r"--[^\n]*")
STAMP = re.compile(r"^(\d{8})\d{0,6}_")


def _strip(sql: str) -> str:
    return COMMENT.sub("", sql)


def _name(x: str) -> str:
    x = x.strip().strip('"')
    return x.split(".")[-1].strip().strip('"').lower()


def _schema_ok(s):
    return s is None or s.strip('"').lower() == "public"


def _when(p: Path) -> date:
    m = STAMP.match(p.name)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y%m%d").date()
        except ValueError:
            pass
    return date.fromtimestamp(p.stat().st_mtime)


def _objects(m) -> list:
    blob = m.group(1)
    if re.search(r"\b(function|sequence|schema|all)\b", blob, re.I):
        return []
    return [_name(x) for x in blob.split(",") if x.strip()]


def find_dirs(args):
    if args:
        return [Path(a) for a in args]
    try:
        root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                            text=True, stderr=subprocess.DEVNULL).strip())
    except Exception:
        root = Path.cwd()
    d = root / "supabase" / "migrations"
    return [d] if d.is_dir() else []


def check(d: Path, since: date):
    files = sorted(d.glob("*.sql"))
    texts = [(f, _strip(f.read_text(encoding="utf-8", errors="ignore"))) for f in files]
    missing = []
    for i, (f, sql) in enumerate(texts):
        if _when(f) < since:
            continue
        made = [_name(m.group(2)) for m in CREATE.finditer(TEMP.sub("", sql)) if _schema_ok(m.group(1))]
        if not made:
            continue
        later = "\n".join(t for _, t in texts[i:])
        if ALL_PUBLIC.search(later):
            continue
        said = set()
        for m in list(GRANT_ON.finditer(later)) + list(REVOKE_ON.finditer(later)):
            said.update(_objects(m))
        for t in made:
            if t not in said:
                missing.append((f.name, t))
    return files, missing


def main(argv):
    since = date(2026, 10, 21)
    args = []
    it = iter(argv)
    for a in it:
        if a == "--부터":
            since = datetime.strptime(next(it), "%Y-%m-%d").date()
        else:
            args.append(a)
    dirs = find_dirs(args)
    if not dirs:
        print("  ⚠️ 서버 변경 파일 폴더가 없어 못 봤습니다(「깨끗하다」가 아닙니다)")
        return 0
    bad = []
    seen = 0
    for d in dirs:
        if not d.is_dir():
            print(f"  ⚠️ 폴더가 없습니다: {d} — 못 봤습니다")
            continue
        files, miss = check(d, since)
        seen += len(files)
        bad += [(d, f, t) for f, t in miss]
    if not bad:
        print(f"  ✅ 새 표 권한 — 빠진 것 없음 (서버 변경 파일 {seen}개 · {since.isoformat()} 이후 것만 봄)")
        return 0
    print("── 새 표 권한 ─────────────────────────────")
    for d, f, t in bad:
        print(f"  ⛔ {f} — 표 「{t}」를 만들었는데 누가 읽고 쓸 수 있는지 안 적었습니다")
    print("     2026-10-30 부터 Supabase 가 새 표에 권한을 자동으로 안 붙입니다(이미 있는 표는 그대로).")
    print("     앱·엣지 함수가 직접 읽는 표면:  grant select, insert, update, delete on <표> to authenticated, service_role;")
    print("     서버 함수로만 닿는 표면:        revoke all on <표> from anon, authenticated;")
    print("     어느 쪽이든 «정한 것»을 같은 서버 변경 파일에 적습니다.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
