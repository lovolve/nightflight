#!/usr/bin/env python3
"""셸 파일이 **한국어 지역 설정에서 중간에 멈추지 않나** — `LC_ALL=C` 가 맨 앞에 있나.

🔴 왜 (2026-10-25 보안 레드팀 8회차 · 옆 대화가 찾고 제가 재현했다):
   맥 기본 bash 는 3.2 다. 지역 설정이 `ko_KR.eucKR` 이면 그 bash 가 우리 파일의
   **UTF-8 한글 바이트를 EUC-KR 멀티바이트로 읽어** 따옴표·괄호를 삼킨다.
   ⛔ 실측: `bin/*.sh` 열 개가 그 설정에서 문법 오류로 멈췄다(UTF-8 에서는 0개).
     `bin/project-root.sh` 는 460줄에서 멈춰 **함수 13개 중 3개가 정의되지 않았다** —
     `nf_macprint`·`nf_bundleid`·`nf_plan`. 맥지문과 제품 번호가 빠지니
     **이용권이 조용히 깨진다.** 오류는 `2>/dev/null` 에 삼켜져 보이지도 않는다.
   ⚠️ 맥 기본은 UTF-8 이라 만날 일은 드물다. 그래서 «낮음»이지만 **조용히** 깨진다.

⭐ 고침은 파일 맨 앞의 `LC_ALL=C` 한 줄이다. 재서 고른 것이다 —
  `LC_CTYPE=C` 는 **안 듣는다**(부르는 쪽 `LC_ALL` 이 덮는다). `LC_ALL=C` 만 듣는다.


`bash -n` 은 **파싱만 하고 실행을 안 한다.** 그래서 파일 안의 `LC_ALL=C` 가
돌지 않고, 고친 파일도 `LC_ALL=ko_KR.eucKR bash -n` 에서는 그대로 실패한다.
⭐ 고쳐지는 것은 **실제로 돌 때**다(bash 가 줄을 읽어 가며 파싱하므로 앞의 대입이 먹는다).
  ⛔ 그러니 「`bash -n` 이 통과하나」로 재면 **영원히 빨간 줄**이 된다 — 사람이 끈다.
  ⭐ 그래서 이 검사는 **그 한 줄이 «첫 한글보다 앞에» 있나**를 본다. 그것이 재는 것이다.


1. **`LC_ALL=C` 가 있나** · 2. **그것이 «주석이 아닌 첫 한글»보다 앞에 있나**
   ⛔ 뒤에 있으면 아무 쓸모가 없다 — 그 앞에서 이미 삼켜진다.


- `tests/`·`probe/` 는 안 본다 — 받는 분에게 안 가고, 묶음은 자기 지역 설정을 정한다.
- 확장자 없는 명령 파일도 본다(`bin/조종석열기` 처럼 사람이 치는 것).

사용:  python3 lint_shell_locale.py [저장소]
끝값:  1 = 멈출 파일이 있다 · 0 = 없다
"""
from __future__ import annotations

import sys
from pathlib import Path


def 본다(뿌리: Path):
    나쁜, 본것 = [], 0
    for p in sorted(list((뿌리 / "bin").rglob("*")) + list((뿌리 / "tools").glob("*.sh"))):
        if not p.is_file():
            continue
        try:
            원 = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if p.suffix not in (".sh", "") or (p.suffix == "" and not 원.startswith("#!")):
            continue
        본것 += 1
        줄들 = 원.split("\n")
        첫한글 = next((i for i, x in enumerate(줄들)
                       if any(ord(c) > 127 for c in x)
                       and not x.lstrip().startswith("#")), None)
        if 첫한글 is None:
            continue
        둔자리 = next((i for i, x in enumerate(줄들)
                       if x.strip().startswith("LC_ALL=C")), None)
        이름 = str(p.relative_to(뿌리))
        if 둔자리 is None:
            나쁜.append((이름, "LC_ALL=C 가 없다", 첫한글 + 1))
        elif 둔자리 > 첫한글:
            나쁜.append((이름, "LC_ALL=C 가 코드의 첫 한글(%d줄)보다 뒤에 있다(%d줄)"
                         % (첫한글 + 1, 둔자리 + 1), 첫한글 + 1))
    return 나쁜, 본것


def main() -> int:
    뿌리 = Path(sys.argv[1] if len(sys.argv) > 1 else
                Path(__file__).resolve().parent.parent).resolve()
    나쁜, 본것 = 본다(뿌리)
    if 본것 == 0:
        print("  ⚠️ 셸 파일을 못 찾아 **재지 못했습니다** — 「없다」가 아닙니다.")
        return 0
    if not 나쁜:
        print("=== 한국어 지역 설정에서 멈추지 않나 — 셸 파일 %d개 ✅ ===" % 본것)
        print("  ⭐ 한글이 코드에 있는 파일은 전부 그 앞에 `LC_ALL=C` 가 있습니다.")
        print("  ⚠️ 이 검사는 **그 한 줄이 있나**만 봅니다 — `bash -n` 으로는 못 잽니다")
        print("     (그 명령은 글을 **읽어만** 보고 파일 안의 줄을 돌리지 않습니다).")
        return 0
    print("=== 한국어 지역 설정에서 **중간에 멈출** 셸 파일 %d개 ===" % len(나쁜))
    print()
    print("  🔴 맥 기본 bash 3.2 가 `ko_KR.eucKR` 에서 UTF-8 한글을 EUC-KR 로 읽어")
    print("     **따옴표·괄호를 삼킵니다.** 파일이 중간에 멈추고, 그 뒤 함수가 정의되지")
    print("     않습니다. 오류는 보통 삼켜져서 **조용히** 깨집니다.")
    for 이름, 왜, 첫 in 나쁜:
        print("       · %-26s %s" % (이름, 왜))
    print()
    print("  ⭐ 고치는 법: 셰뱅 바로 뒤(첫 한글보다 앞)에 한 줄을 넣으십시오.")
    print("     [모델] LC_ALL=C; export LC_ALL")
    print("     ⛔ `LC_CTYPE=C` 는 안 듣습니다 — 부르는 쪽 `LC_ALL` 이 덮습니다(실측).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
