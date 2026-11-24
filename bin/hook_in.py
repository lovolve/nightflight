#!/usr/bin/env python3
"""훅 입력(표준입력)을 끝까지 읽되, 1초 동안 아무것도 안 오면 그만 기다린다 — 훅 다섯이 같이 쓴다."""
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
