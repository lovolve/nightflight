#!/usr/bin/env python3
"""훅 입력(표준입력)을 끝까지 읽되, 1초 동안 아무것도 안 오면 그만 기다린다 — 훅 다섯이 같이 쓴다.

🔴 왜 (2026-10-10 실제로 겪었다 · 2026-10-25 코드 품질 레드팀 ⑤):
   `cat` 은 훅이 입력을 닫으면 끝나지만, **입력이 열린 채 조용한 자리**(도구·CI·다른 스크립트에서 부를 때)에서는
   닫힘을 영원히 기다린다. 화면에는 아무것도 안 나온다. check_touched.sh 만 이렇게 고쳐 두고
   나머지 훅 넷(session_start · word_rise · 정리듣기 · key_paste)은 `cat` 그대로였다.
⭐ 글이 계속 오는 동안은 계속 읽고(잘림 방지), 1초 동안 아무것도 안 오면 그만 기다린다.
⛔ 이 파일을 «읽지 못하고» 끝나면(선택기를 못 씀) 끝값 3 — 부르는 쪽이 `cat` 으로 물러난다.
   ⭐ 파이썬이 없을 때도 같다(끝값 127). 그래서 키 붙여 넣기의 셸 대비책은 늘 원문을 받는다.
🔴 보안 레드팀 10회차 ②(A·B 재현): 키 막기에서 «1초 쉬면 그만»이 구멍이었다 — 첫 글자가 1.3초 늦거나 중간에 멈추고 키가
   뒤쪽에 있으면 앞부분만 보고 PASS 를 냈다. 그리고 앞부분만 읽고 죽으면 셸이 `cat` 으로 «남은 뒷부분»만 받아 키를 놓쳤다.
   ⭐ `--끝까지`(키 붙여 넣기만): 쉬는 틈과 상관없이 닫힘(EOF)까지 읽되 전체 5초까지만. 못 닿으면 끝값 4 — 부르는 쪽이 «확인 못 함»으로 막는다.
      다른 훅은 지금 그대로(1초 쉬면 그만 · 끝값 0) — 그 훅들은 놓쳐도 키가 새지 않는다.
⛔ 사용자 폴더에서 돈다 — 반드시 `python3 -I` 로 부른다.
   부르는 꼴: IN="$(python3 -I "$HERE/hook_in.py" 2>/dev/null)" || IN="$(cat 2>/dev/null || true)"
"""
import os
import selectors
import sys
import time

끝까지 = "--끝까지" in sys.argv[1:]

try:
    import stat
    if stat.S_ISREG(os.fstat(sys.stdin.fileno()).st_mode):
        sys.stdout.buffer.write(sys.stdin.buffer.read())
        sys.exit(0)
except SystemExit:
    raise
except Exception:
    pass
try:
    sel = selectors.DefaultSelector()
    sel.register(sys.stdin, selectors.EVENT_READ)
except Exception:
    sys.exit(3)
buf = []
마감 = time.monotonic() + 5.0
닫힘 = False
while True:
    남은 = 마감 - time.monotonic() if 끝까지 else 1.0
    if 남은 <= 0 or not sel.select(남은):
        break
    try:
        c = os.read(sys.stdin.fileno(), 65536)
    except Exception:
        break
    if not c:
        닫힘 = True
        break
    buf.append(c)
sys.stdout.buffer.write(b"".join(buf))
if 끝까지 and not 닫힘:
    sys.exit(4)
