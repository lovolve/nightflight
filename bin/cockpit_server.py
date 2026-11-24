#!/usr/bin/env python3
"""조종석 서버 — 클로드 앱 오른쪽 브라우저 칸에 조종석을 띄우고, 몇 초마다 자료만 바꿔 넣는다."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
import sys
import threading
import time
import urllib.request
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

여기 = Path(__file__).resolve().parent
sys.path.insert(0, str(여기.parent / "tools"))
sys.path.insert(0, str(여기))
import cockpit_file

쉼한도 = 30 * 60
첫자리 = 8800
자리수 = 900
누름값 = {"완료", "넘어감", "되돌리기"}


def _뿌리표(뿌리: Path) -> str:
    return hashlib.sha256((str(뿌리) + "\0" + str(여기)).encode("utf-8")).hexdigest()[:16]


def _폴더표(뿌리: Path) -> str:
    return hashlib.sha256(str(뿌리).encode("utf-8")).hexdigest()[:16]


def 보이나(뿌리: Path) -> bool:
    옛 = _폴더표(뿌리)
    표들 = {_뿌리표(뿌리), 옛}
    try:
        for 판 in 여기.parent.parent.iterdir():
            if (판 / "bin").is_dir():
                표들.add(hashlib.sha256((str(뿌리) + "\0" + str((판 / "bin").resolve())).encode("utf-8")).hexdigest()[:16])
    except OSError:
        pass
    for 자리 in _자리들(뿌리):
        try:
            여는것 = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with 여는것.open("http://127.0.0.1:%d/who" % 자리, timeout=1) as r:
                d = json.loads(r.read().decode("utf-8"))
        except Exception:
            continue
        if d.get("뿌리") in 표들 or d.get("폴더") == 옛:
            return True
    return False


def _자리들(뿌리: Path):
    처음 = 첫자리 + zlib.crc32(str(뿌리).encode("utf-8")) % 자리수
    for i in range(20):
        yield 첫자리 + (처음 - 첫자리 + i) % 자리수


def _누구(자리: int) -> str | None:
    try:
        여는것 = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with 여는것.open("http://127.0.0.1:%d/who" % 자리, timeout=1) as r:
            return json.loads(r.read().decode("utf-8")).get("뿌리")
    except Exception:
        return None


def _칸바뀐때(뿌리: Path) -> float:
    칸집 = cockpit_file.기록집(뿌리) / "board"
    늦음 = 0.0
    try:
        for f in 칸집.glob("*.json"):
            늦음 = max(늦음, f.stat().st_mtime)
    except OSError:
        pass
    return 늦음


def _기록바뀐때(뿌리: Path) -> float:
    집 = cockpit_file.기록집(뿌리)
    늦음 = 0.0
    try:
        for f in 집.glob("*.tsv"):
            늦음 = max(늦음, f.stat().st_mtime)
    except OSError:
        pass
    return 늦음


def 만든다(뿌리: Path, 자리: int):
    열쇠 = secrets.token_hex(16)
    표 = _뿌리표(뿌리)
    기록도구 = 여기 / "ledger.sh"
    받는이름 = {"127.0.0.1:%d" % 자리, "localhost:%d" % 자리}
    상태 = {"마지막": time.time(), "짓는중": False, "지은때": 0.0}
    짓기잠금 = threading.Lock()

    def 칸다시():
        with 짓기잠금:
            if 상태["짓는중"] or time.time() - 상태["지은때"] < 5:
                return
            if _기록바뀐때(뿌리) <= _칸바뀐때(뿌리):
                return
            상태["짓는중"] = True

        def 일():
            try:
                subprocess.run(["bash", str(기록도구), "조종석준비"], cwd=str(뿌리), capture_output=True, timeout=120)
            except Exception:
                pass
            finally:
                상태["지은때"] = time.time()
                상태["짓는중"] = False
        threading.Thread(target=일, daemon=True).start()

    class 처리(BaseHTTPRequestHandler):
        server_version = "nightflight-cockpit"
        timeout = 10

        def log_message(self, *a):
            pass

        def _보냄(self, 코드: int, 몸: bytes, 꼴: str):
            self.send_response(코드)
            self.send_header("Content-Type", 꼴)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Length", str(len(몸)))
            self.end_headers()
            self.wfile.write(몸)

        def _제이슨(self, 코드: int, 값):
            self._보냄(코드, json.dumps(값, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def _이컴퓨터(self) -> bool:
            if self.headers.get("Host", "") not in 받는이름:
                return False
            return self.headers.get("Sec-Fetch-Site", "") in ("", "same-origin", "same-site", "none")

        def do_GET(self):
            if not self._이컴퓨터():
                return self._보냄(403, b"", "text/plain")
            길 = self.path.split("?", 1)[0]
            if 길 == "/who":
                return self._제이슨(200, {"뿌리": 표, "폴더": _폴더표(뿌리)})
            상태["마지막"] = time.time()
            if 길 == "/keep":
                return self._제이슨(200, {})
            if 길 == "/board.json":
                칸다시()
                return self._제이슨(200, {"판": cockpit_file.판모으기(뿌리), "바뀐때": _칸바뀐때(뿌리)})
            if 길 in ("/", "/cockpit.html"):
                글 = cockpit_file.원본글()
                if 글 is None:
                    return self._보냄(500, "조종석 원본을 못 찾았습니다.".encode("utf-8"), "text/plain; charset=utf-8")
                덧 = '<script>window.야간비행서버=' + json.dumps({"열쇠": 열쇠, "바뀐때": _칸바뀐때(뿌리)}) + ';</script>\n'
                return self._보냄(200, cockpit_file.쪽짓기(글, cockpit_file.판모으기(뿌리), 덧).encode("utf-8"), "text/html; charset=utf-8")
            return self._보냄(404, b"", "text/plain")

        def do_POST(self):
            if not self._이컴퓨터():
                return self._보냄(403, b"", "text/plain")
            상태["마지막"] = time.time()
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                return self._제이슨(415, {"오류": "꼴이 맞지 않습니다"})
            try:
                길이 = max(0, min(int(self.headers.get("Content-Length") or 0), 8192))
                값 = json.loads(self.rfile.read(길이).decode("utf-8") or "{}")
            except Exception:
                return self._제이슨(400, {"오류": "읽지 못했습니다"})
            if not isinstance(값, dict) or not secrets.compare_digest(str(값.get("열쇠", "")), 열쇠):
                return self._제이슨(403, {"오류": "열쇠가 맞지 않습니다"})
            길 = self.path.split("?", 1)[0]
            if 길 == "/mark":
                기능, 세부, 누름 = str(값.get("기능", "")), str(값.get("세부", "")), str(값.get("상태", ""))
                if 누름 not in 누름값 or not 기능 or not 세부 or len(기능) > 200 or len(세부) > 200:
                    return self._제이슨(400, {"오류": "값이 맞지 않습니다"})
                명령 = ["bash", str(기록도구), "조종석표시", 기능, 세부, 누름]
            elif 길 == "/pressed":
                누른것 = str(값.get("값", ""))
                if not 누른것 or len(누른것) > 200 or "\n" in 누른것:
                    return self._제이슨(400, {"오류": "값이 맞지 않습니다"})
                명령 = ["bash", str(기록도구), "앱설정", "이미한것", 누른것, "화면"]
            else:
                return self._제이슨(404, {"오류": "없는 자리입니다"})
            try:
                r = subprocess.run(명령, cwd=str(뿌리), capture_output=True, text=True, timeout=60)
            except Exception:
                return self._제이슨(500, {"오류": "기록하지 못했습니다"})
            if r.returncode != 0:
                return self._제이슨(500, {"오류": "기록하지 못했습니다"})
            return self._제이슨(200, {"됨": True, "바뀐때": _칸바뀐때(뿌리)})

    서버 = ThreadingHTTPServer(("127.0.0.1", 자리), 처리)
    서버.daemon_threads = True

    def 지킴이():
        while True:
            time.sleep(30)
            if time.time() - 상태["마지막"] > 쉼한도:
                서버.shutdown()
                return
    threading.Thread(target=지킴이, daemon=True).start()
    return 서버


def 뒤에서(뿌리: Path) -> int:
    표 = _뿌리표(뿌리)
    for 자리 in _자리들(뿌리):
        if _누구(자리) == 표:
            print("http://127.0.0.1:%d/" % 자리)
            return 0
    import hashlib, tempfile
    실패표 = Path(tempfile.gettempdir()) / ("nf_cockpit_fail_" + hashlib.sha256(str(뿌리).encode("utf-8")).hexdigest()[:16])
    try:
        if time.time() - 실패표.stat().st_mtime < 600:
            print("  ⛔ 조종석 서버를 띄우지 못했습니다.")
            return 1
    except OSError:
        pass
    subprocess.Popen([sys.executable, "-I", str(Path(__file__).resolve()), str(뿌리)],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True, close_fds=True)
    끝 = time.time() + 10
    while time.time() < 끝:
        for 자리 in _자리들(뿌리):
            if _누구(자리) == 표:
                print("http://127.0.0.1:%d/" % 자리)
                return 0
        time.sleep(0.2)
    try:
        실패표.touch()
    except OSError:
        pass
    print("  ⛔ 조종석 서버를 띄우지 못했습니다.")
    return 1


def main(argv) -> int:
    인자 = [a for a in argv if not a.startswith("-")]
    if not 인자:
        print("  쓰는 법: cockpit_server.py <제품 폴더>")
        return 1
    뿌리 = Path(인자[0]).resolve()
    if not 뿌리.is_dir():
        print("  ⛔ 그런 폴더가 없습니다: %s" % 뿌리)
        return 1
    if "--뒤에서" in argv:
        return 뒤에서(뿌리)
    if "--보이나" in argv:
        return 0 if 보이나(뿌리) else 1
    if "--살아있나" in argv:
        표 = _뿌리표(뿌리)
        return 0 if any(_누구(자리) == 표 for 자리 in _자리들(뿌리)) else 1
    표 = _뿌리표(뿌리)
    자리목록 = list(_자리들(뿌리))
    if "--자리" in argv:
        try:
            자리목록 = [int(argv[argv.index("--자리") + 1])]
        except (ValueError, IndexError):
            print("  ⛔ --자리 뒤에 숫자가 있어야 합니다.")
            return 1
    for 자리 in 자리목록:
        누구 = _누구(자리)
        if 누구 == 표:
            print("http://127.0.0.1:%d/" % 자리)
            return 0
        if 누구 is not None:
            continue
        try:
            서버 = 만든다(뿌리, 자리)
        except OSError:
            continue
        print("http://127.0.0.1:%d/" % 자리, flush=True)
        try:
            서버.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0
    print("  ⛔ 조종석 서버를 띄울 자리를 찾지 못했습니다.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
