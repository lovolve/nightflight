#!/usr/bin/env python3
"""야간비행 로그인 — 이 컴퓨터를 구글 · 애플 계정에 연결한다(기기 연결, RFC 8628 꼴).

흐름: 시작 → 대화창에 주소와 확인 문자 8자를 보이고 브라우저를 연다 → 사람이 로그인하고 8자를 넣어 승인한다
      → 대기(5초 간격으로 «승인됐나»)가 컴퓨터 열쇠를 한 번 받는다 → 이 컴퓨터에만 둔다.

⛔ 열쇠를 화면 · 기록 · 명령 인자에 싣지 않는다. 서버로는 몸(표준입력이 아닌 요청 몸)으로만 보낸다.
⛔ 열쇠 자리: <야간비행 집>/account/key — 폴더 700 · 파일 600 · 링크면 지우고 새로 쓴다.
⛔ 기다리는 상태(기기 비밀)도 같은 폴더의 login.pending(600). 어느 대화든 이어받아 마무리한다.
   두 대화가 동시에 묻지 않게 login.lock 폴더로 잠근다(맥에는 flock 이 없다).
⛔ 못 닿았으면 못 닿았다고 말한다 — «틀렸다»로 말하지 않는다.
⛔ 프록시와 설정 파일을 따르지 않는다(session_start.py · nf_post 와 같은 선).

쓰는 법(모델이 부른다 — license_key.sh 가 넘긴다):
  account_login.py 시작          로그인 시작(이미 기다리는 중이면 같은 주소 · 문자를 다시 보인다)
  account_login.py 대기 [초]     승인을 기다린다(기본 100초, 최대 110초) — 끝값 0 연결 · 3 아직 · 1 실패
  account_login.py 상태          이 컴퓨터가 계정에 붙어 있나
  account_login.py 해제 확인     이 컴퓨터만 계정에서 뗀다(«확인» 없이는 무엇을 할지만 말한다)
  account_login.py 기다리나      기다리는 로그인이 있으면 끝값 0(대화 시작이 부른다 · 출력 없음)
환경: NF_HOME · NF_BRAIN_BASE · NF_DOORKEY · NF_PID · NF_MPRINT · NFL(ko|en)
"""
import json
import os
import re
import shutil

import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

EN = os.environ.get("NFL") == "en"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nf_paths
집 = str(nf_paths.집())
자리 = os.path.join(집, "account")
열쇠파일 = os.path.join(자리, "key")
메일파일 = os.path.join(자리, "mail")
대기파일 = os.path.join(자리, "login.pending")
잠금 = os.path.join(자리, "login.lock")
바뀜표 = os.path.join(집, "plan_changed")
열쇠꼴 = re.compile(r"^[A-Za-z0-9_-]{43}$")
_프록시막음 = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def 말(ko, en):
    return en if EN else ko


def 찍기(ko, en):
    print("  " + 말(ko, en))


def 모델(글):
    print("  [모델] " + 글)



def 자리만들기():
    os.makedirs(자리, mode=0o700, exist_ok=True)
    if os.path.islink(자리):
        raise OSError("account 자리가 링크입니다")
    os.chmod(자리, 0o700)


def 몰래쓰기(길, 글):
    자리만들기()
    if os.path.islink(길):
        os.remove(길)
    임시 = 길 + ".tmp.%d" % os.getpid()
    fd = os.open(임시, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(글)
    os.chmod(임시, 0o600)
    os.replace(임시, 길)


def 읽기(길):
    try:
        if os.path.islink(길) or not os.path.isfile(길):
            return ""
        with open(길, encoding="utf-8") as f:
            return f.read(4096).strip()
    except OSError:
        return ""


def 열쇠():
    k = 읽기(열쇠파일)
    return k if 열쇠꼴.match(k) else ""


def 지우기(*길들):
    for 길 in 길들:
        try:
            os.remove(길)
        except OSError:
            pass


def 플랜바뀜():
    지우기(os.path.join(집, "license.json"), os.path.join(집, "free_ended"), os.path.join(집, "license_state"))
    try:
        with open(바뀜표, "w", encoding="utf-8") as f:
            f.write(str(int(time.time())) + "\n")
    except OSError:
        pass



class 못닿음(Exception):
    pass


def 부르기(길, 몸, 제한=10):
    기본 = os.environ.get("NF_BRAIN_BASE", "")
    if not 기본.startswith("https://"):
        raise 못닿음("주소")
    주소 = 기본.rstrip("/") + "/functions/v1/gyejeong/" + urllib.parse.quote(길)
    req = urllib.request.Request(주소, data=json.dumps(몸, ensure_ascii=False).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "apikey": os.environ.get("NF_DOORKEY", "")})
    try:
        with _프록시막음.open(req, timeout=제한) as r:
            return json.loads(r.read(8192).decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read(8192).decode("utf-8"))
        except Exception:
            raise 못닿음(str(e.code))
    except Exception as e:
        raise 못닿음(type(e).__name__)


def 못닿음말():
    찍기("지금 서버에 닿지 못했습니다. 잠시 뒤에 다시 해 주십시오.", "Couldn't reach the Nightflight server. Please try again in a moment.")


def 서버말(d, ko, en):
    t = (d.get("말_en") if EN else d.get("말")) or d.get("말") if isinstance(d, dict) else ""
    찍기(t or ko, t or en)


def 기종():
    try:
        이름 = subprocess.run(["sw_vers", "-productName"], capture_output=True, text=True, timeout=3).stdout.strip()
        판 = subprocess.run(["sw_vers", "-productVersion"], capture_output=True, text=True, timeout=3).stdout.strip()
        모델명 = subprocess.run(["sysctl", "-n", "hw.model"], capture_output=True, text=True, timeout=3).stdout.strip()
        return (" ".join(x for x in (이름, 판) if x) + ((" · " + 모델명) if 모델명 else ""))[:60] or None
    except (OSError, subprocess.SubprocessError):
        return None



class 잠그기:
    def __enter__(self):
        자리만들기()
        for _ in range(40):
            try:
                os.mkdir(잠금, 0o700)
                return self
            except FileExistsError:
                try:
                    if time.time() - os.stat(잠금).st_mtime > 120:
                        os.rmdir(잠금)
                        continue
                except OSError:
                    pass
                time.sleep(0.25)
        raise TimeoutError

    def __exit__(self, *a):
        try:
            os.rmdir(잠금)
        except OSError:
            pass


def 기다림읽기():
    try:
        d = json.loads(읽기(대기파일) or "{}")
    except ValueError:
        return None
    if not isinstance(d, dict) or not 열쇠꼴.match(str(d.get("기기비밀", ""))):
        return None
    if float(d.get("끝", 0)) <= time.time():
        지우기(대기파일)
        return None
    return d


def 우리주소(주):
    return any(주 == 뿌리 + "/link" or 주.startswith(뿌리 + "/link?") for 뿌리 in (계정주소(), "https://nightflight.lovolve.app/account"))


def 주소보임(d):
    주 = str(d.get("주소") or "")
    return 주 + ("&" if "?" in 주 else "?") + "lang=" + ("en" if EN else "ko")


def 안내(d, 열었나):
    남 = max(0, int(float(d["끝"]) - time.time())) // 60
    찍기("브라우저에서 아래 주소를 여시고, 구글이나 애플로 로그인하신 뒤 확인 문자를 넣어 주십시오.",
        "Open the address below, sign in with Google or Apple, then enter the confirmation code.")
    print("    " + 주소보임(d))
    찍기("야간비행 연결 확인 문자: " + str(d.get("확인문자")), "Nightflight connection code: " + str(d.get("확인문자")))
    if 열었나:
        찍기("브라우저를 열어 두었습니다. 휴대폰에서 주소를 여셔도 됩니다.", "We opened your browser. You can also open the address on your phone.")
    찍기("이 대화창에서 직접 시작하신 게 아니면 승인하지 마십시오. %d분 안에 마치시면 됩니다." % 남,
        "Only approve it if you started this from this chat. You have %d minutes." % 남)


def 시작():
    if 열쇠():
        찍기("이 컴퓨터는 이미 계정에 연결돼 있습니다.", "This computer is already connected to your account.")
        플랜바뀜()
        모델("다른 계정으로 바꾸려면 사용자가 원할 때만 `license_key.sh 해제` 뒤 다시 로그인합니다. 지금 상태는 `license_key.sh 계정` 으로 봅니다.")
        return 0
    with 잠그기():
        d = 기다림읽기()
        if d:
            안내(d, False)
            모델("이어서 `license_key.sh 로그인대기` 를 부르십시오. 아직이면 다시 부릅니다.")
            return 0
        mp = os.environ.get("NF_MPRINT", "")
        if not re.match(r"^[0-9a-f]{64}$", mp):
            찍기("이 컴퓨터를 알아보지 못했습니다. 야간비행을 다시 깔아 주십시오.", "Nightflight couldn't recognize this computer. Please reinstall it.")
            return 1
        몸 = {"맥지문": mp, "언어": "en" if EN else "ko"}
        pid = os.environ.get("NF_PID", "")
        if re.match(r"^[A-Za-z0-9_-]{8,64}$", pid):
            몸["사람id"] = pid
        k = 기종()
        if k:
            몸["기종"] = k
        try:
            r = 부르기("로그인시작", 몸)
        except 못닿음:
            못닿음말()
            return 1
        if not isinstance(r, dict) or r.get("된다") is not True or not 열쇠꼴.match(str(r.get("기기비밀", ""))) \
                or not 우리주소(str(r.get("주소", ""))):
            서버말(r if isinstance(r, dict) else {}, "로그인을 시작하지 못했습니다. 잠시 뒤에 다시 해 주십시오.", "Couldn't start sign-in. Please try again in a moment.")
            return 1
        d = {"기기비밀": r["기기비밀"], "확인문자": str(r.get("확인문자", ""))[:9], "주소": r["주소"],
             "간격": max(5, int(r.get("간격") or 5)), "끝": time.time() + min(900, int(r.get("남은초") or 600))}
        몰래쓰기(대기파일, json.dumps(d, ensure_ascii=False))
    열었나 = False
    if os.environ.get("NF_NO_BROWSER") != "1" and shutil.which("open"):
        try:
            열었나 = subprocess.run(["open", 주소보임(d)], capture_output=True, timeout=5).returncode == 0
        except (OSError, subprocess.SubprocessError):
            열었나 = False
    안내(d, 열었나)
    모델("사용자에게 답할 때 맨 위에 `## 야간비행 연결 확인 문자` 제목 줄을 두고(영어 사용자는 `## Nightflight connection code`), 바로 아래에 확인 문자 %s 하나만 든 코드 칸(```text)을 두십시오 — 그 칸에 복사 버튼이 붙습니다. 그 아래에 주소와 짧은 순서를 보인 뒤 `license_key.sh 로그인대기` 를 부르십시오. 끝값 3(아직)이면 다시 부릅니다." % str(d.get("확인문자")))
    return 0


def 대기(최대=100):
    끝시각 = time.time() + max(5, min(110, 최대))
    while True:
        try:
            with 잠그기():
                d = 기다림읽기()
                if not d:
                    if 열쇠():
                        찍기("이 컴퓨터는 계정에 연결돼 있습니다.", "This computer is connected to your account.")
                        return 0
                    찍기("기다리는 로그인이 없습니다. «야간비행 로그인»으로 다시 시작하십시오.", "There's no sign-in in progress. Say “Nightflight login” to start again.")
                    return 1
                try:
                    r = 부르기("승인됐나", {"기기비밀": d["기기비밀"]})
                except 못닿음:
                    r = {"상태": "대기"}
                상태 = r.get("상태") if isinstance(r, dict) else None
                if 상태 == "연결" and 열쇠꼴.match(str(r.get("열쇠", ""))):
                    몰래쓰기(열쇠파일, r["열쇠"] + "\n")
                    메일 = str(r.get("메일") or "")[:120]
                    if 메일:
                        몰래쓰기(메일파일, 메일 + "\n")
                    지우기(대기파일)
                    플랜바뀜()
                    찍기("이 컴퓨터를 %s 계정에 연결했습니다." % (메일 or "그"), "Connected this computer to %s." % (메일 or "your account"))
                    모델("이어서 `license_key.sh 보기` 로 플랜을 확인해 사용자에게 한 줄로 알리십시오. 이용권이 없는 계정이면 «다른 계정(구글/애플)으로 사셨는지» 여쭈십시오.")
                    모델("이 대화에서 플랜·결제 때문에 단계 안내를 못 받았으면, 그 단계 안내를 `brain.sh <단계> <갈래>` 로 다시 받아 하던 일을 이어 가십시오. 사용자에게 다시 시키라고 하지 마십시오.")
                    return 0
                if 상태 in ("만료", "넘침", "횟수"):
                    지우기(대기파일)
                    if 상태 == "넘침":
                        찍기("이 계정에는 컴퓨터가 이미 3대 연결돼 있습니다. 내 계정 화면에서 한 대를 해제하신 뒤 다시 로그인해 주십시오.",
                            "This account already has 3 computers. Disconnect one on your account page, then sign in again.")
                        print("    " + 계정화면주소())
                    elif 상태 == "횟수":
                        찍기("최근 30일 동안 새 컴퓨터를 너무 많이 연결했습니다. 나중에 다시 해 주십시오.",
                            "Too many new computers were connected in the last 30 days. Please try again later.")
                    else:
                        찍기("로그인 시간이 지났습니다. «야간비행 로그인»으로 다시 시작하십시오.", "The sign-in timed out. Say “Nightflight login” to start again.")
                    return 1
                간격 = int(d.get("간격") or 5) + (5 if 상태 == "천천히" else 0)
        except TimeoutError:
            간격 = 5
        if time.time() + 간격 > 끝시각:
            찍기("아직 승인을 기다리고 있습니다.", "Still waiting for approval.")
            모델("사용자가 승인을 마쳤는지 묻지 말고 `license_key.sh 로그인대기` 를 다시 부르십시오.")
            return 3
        time.sleep(간격)


def 계정주소():
    return "https://account.lovolve.app"


def 계정화면주소():
    return "https://nightflight.lovolve.app/account/"


def 상태():
    k = 열쇠()
    if not k:
        if 기다림읽기():
            찍기("로그인을 기다리는 중입니다.", "A sign-in is in progress.")
            return 3
        찍기("이 컴퓨터는 계정에 연결돼 있지 않습니다. 무료로 쓰시거나 이용권을 사셨으면 «야간비행 로그인»이라고 말씀해 주십시오.",
            "This computer isn't connected to an account. To use Nightflight free, or if you bought a plan, say “Nightflight login”.")
        return 1
    try:
        r = 부르기("열쇠확인", {"열쇠": k, "맥지문": os.environ.get("NF_MPRINT", "")})
    except 못닿음:
        못닿음말()
        return 1
    if isinstance(r, dict) and r.get("있나") is True:
        메일 = str(r.get("메일") or 읽기(메일파일))[:120]
        찍기("%s 계정에 연결돼 있습니다." % 메일, "Connected to %s." % 메일)
        if r.get("이용권있나") is not True:
            찍기("이 계정에는 이용권이 없습니다. 다른 방법(구글/애플)으로 사셨는지 확인해 주십시오. " + nf_paths.결제말(False),
                "This account has no plan. Check whether you bought it with your other sign-in (Google/Apple). " + nf_paths.결제말(True))
        return 0
    if isinstance(r, dict) and r.get("까닭") in ("없음", "다른컴퓨터"):
        지우기(열쇠파일, 메일파일)
        플랜바뀜()
        찍기("이 컴퓨터의 연결이 풀렸습니다. «야간비행 로그인»으로 다시 연결해 주십시오.", "This computer was disconnected. Say “Nightflight login” to reconnect.")
        return 1
    못닿음말()
    return 1


def 해제(확인):
    k = 열쇠()
    if not k:
        찍기("이 컴퓨터는 계정에 연결돼 있지 않습니다.", "This computer isn't connected to an account.")
        return 0
    if not 확인:
        찍기("이 컴퓨터를 계정에서 떼려고 합니다. 떼면 이 컴퓨터에서는 플랜을 쓸 수 없고, 다시 로그인하면 돌아옵니다. 떼시겠습니까?",
            "About to disconnect this computer from your account. Your plan stops working here until you sign in again. Disconnect?")
        모델("사람이 그러라고 하면: `license_key.sh 해제 확인` — 사람이 답하기 전에는 부르지 마십시오.")
        return 0
    try:
        r = 부르기("이컴퓨터해제", {"열쇠": k, "맥지문": os.environ.get("NF_MPRINT", "")})
    except 못닿음:
        못닿음말()
        return 1
    if isinstance(r, dict) and r.get("된다") is True:
        지우기(열쇠파일, 메일파일)
        플랜바뀜()
        찍기("이 컴퓨터를 계정에서 뗐습니다.", "Disconnected this computer from your account.")
        return 0
    찍기("해제하지 못했습니다. 잠시 뒤에 다시 해 주십시오.", "Couldn't disconnect. Please try again in a moment.")
    return 1


def main(a):
    c = a[0] if a else ""
    if c == "시작":
        return 시작()
    if c == "대기":
        try:
            return 대기(int(a[1]) if len(a) > 1 else 100)
        except ValueError:
            return 대기()
    if c == "상태":
        return 상태()
    if c == "해제":
        return 해제(len(a) > 1 and a[1] == "확인")
    if c == "기다리나":
        return 0 if 기다림읽기() else 1
    print(__doc__.split("쓰는 법")[1].split("환경:")[0].strip())
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(1)
    except (OSError, TimeoutError):
        찍기("이 컴퓨터에 로그인 상태를 적지 못했습니다. 잠시 뒤에 다시 해 주십시오.", "Couldn't save the sign-in state on this computer. Please try again.")
        sys.exit(1)
