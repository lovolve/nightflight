#!/usr/bin/env python3
"""구글 플레이 도구 — 연결(서비스 계정 열쇠) · 스토어 정보(제목 · 짧은 설명 · 긴 설명) 보기 · 바꾸기.

⛔ 열쇠 파일(.json)은 이 컴퓨터의 ~/.googleplay/ 에만 둔다 — 작업 중인 앱 폴더에 두면 코드와 같이 올라간다. 대화창에 붙여 넣지 않는다.
⛔ 바꾸기는 --confirm 이 있어야 한다 · 구글은 바꾼 스토어 정보를 «검토 뒤» 내보낸다(바로 바뀌지 않는다).

  준비                                   연결 — 열쇠가 없으면 사람이 할 차례를 찍고, 있으면 붙는지 확인한다
  meta [--pkg <패키지 이름>]                스토어 정보 보기(언어마다)
  meta set <언어> <칸> <값> [--confirm]     한 칸 바꾸기 — 칸: title · shortDescription · fullDescription
"""
import base64, json, os, re, subprocess, sys, tempfile, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

_프록시막음 = urllib.request.build_opener(urllib.request.ProxyHandler({}))
API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"
칸이름 = {"title": "앱 이름", "shortDescription": "짧은 설명", "fullDescription": "긴 설명"}


def _열쇠자리() -> Path:
    return Path(os.environ.get("GPLAY_KEY_DIR") or (Path.home() / ".googleplay"))


def _열쇠():
    d = _열쇠자리()
    ks = sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True) if d.is_dir() else []
    for k in ks:
        try:
            j = json.loads(k.read_text())
        except (OSError, ValueError):
            continue
        if j.get("type") == "service_account" and j.get("private_key") and j.get("client_email"):
            return k, j
    return None, None


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def 서명(j: dict, now: int = None) -> str:
    now = now or int(time.time())
    h = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    p = _b64(json.dumps({"iss": j["client_email"], "scope": "https://www.googleapis.com/auth/androidpublisher",
                          "aud": j.get("token_uri", "https://oauth2.googleapis.com/token"), "iat": now, "exp": now + 3000}).encode())
    with tempfile.TemporaryDirectory() as td:
        os.chmod(td, 0o700)
        kp = os.path.join(td, "k.pem")
        with open(os.open(kp, os.O_WRONLY | os.O_CREAT, 0o600), "w") as f:
            f.write(j["private_key"])
        sig = subprocess.run(["openssl", "dgst", "-sha256", "-sign", kp], input=(h + "." + p).encode(),
                             capture_output=True, check=True).stdout
    return h + "." + p + "." + _b64(sig)


_토큰 = {}


def 토큰(j: dict) -> str:
    if _토큰.get("v") and _토큰.get("exp", 0) > time.time() + 60:
        return _토큰["v"]
    body = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": 서명(j)}).encode()
    r = urllib.request.Request(j.get("token_uri", "https://oauth2.googleapis.com/token"), data=body, method="POST",
                               headers={"Content-Type": "application/x-www-form-urlencoded"})
    with _프록시막음.open(r) as resp:
        d = json.loads(resp.read())
    _토큰.update(v=d["access_token"], exp=time.time() + int(d.get("expires_in", 3000)))
    return _토큰["v"]


def req(j, method, path, body=None):
    r = urllib.request.Request(API + path, method=method, headers={"Authorization": "Bearer " + 토큰(j), "Content-Type": "application/json"})
    if body is not None:
        r.data = json.dumps(body).encode()
    try:
        with _프록시막음.open(r) as resp:
            data = resp.read()
            return json.loads(data) if data else {}
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:1200], file=sys.stderr)
        raise


def 이폴더패키지() -> str:
    for p in list(Path.cwd().glob("android/app/build.gradle*"))[:2]:
        m = re.search(r'applicationId\s*[= ]\s*["\']([\w.]+)["\']', p.read_text(errors="replace"))
        if m:
            return m.group(1)
    a = Path.cwd() / "app.json"
    if a.is_file():
        try:
            d = json.loads(a.read_text())
            pk = ((d.get("expo") or d).get("android") or {}).get("package")
            if pk:
                return pk
        except ValueError:
            pass
    return ""


def _패키지(args) -> str:
    if "--pkg" in args and args.index("--pkg") + 1 < len(args):
        return args[args.index("--pkg") + 1]
    return os.environ.get("GPLAY_PACKAGE") or 이폴더패키지() or sys.exit(
        "안드로이드 패키지 이름을 못 찾았습니다 — --pkg <패키지 이름> 으로 주십시오(구글 플레이 콘솔의 앱 이름 아래에 보입니다).")


def cmd_준비(args):
    d = _열쇠자리()
    d.mkdir(parents=True, exist_ok=True)
    os.chmod(d, 0o700)
    kp, j = _열쇠()
    if not j:
        if not os.environ.get("NF_NO_OPEN"):
            subprocess.run(["open", str(d)], check=False, capture_output=True)
        print("구글 플레이 연결 열쇠가 아직 없습니다. 사용자께 이 차례를 그대로 보여 드리십시오(사람만 할 수 있는 일입니다):")
        print("  1. Google Cloud 콘솔에 로그인해 프로젝트를 하나 고르거나 만드십시오.")
        print("  2. «API 및 서비스»에서 «Google Play Android Developer API»를 찾아 «사용»을 누르십시오.")
        print("  3. «IAM 및 관리자» → «서비스 계정»에서 서비스 계정을 만드십시오. 역할은 고르지 않아도 됩니다.")
        print("  4. 만든 서비스 계정 → «키» 탭 → «키 추가» → «JSON»을 누르십시오. ⚠️ 이 파일은 다시 내려받을 수 없습니다.")
        print("  5. 내려받은 파일을 방금 열린 폴더 창에 끌어다 놓으십시오. 작업 중인 앱 폴더에는 넣지 마십시오.")
        print("  6. Play Console → «사용자 및 권한» → «새 사용자 초대»에 서비스 계정 메일 주소(…@….iam.gserviceaccount.com)를 넣고, 앱 권한에서 «스토어 등록정보 관리»를 주십시오.")
        print("[모델] 다 되면 gplay.py 준비 를 다시 부르십시오.")
        sys.exit(1)
    os.chmod(kp, 0o600)
    print(f"열쇠 파일을 찾았습니다(서비스 계정 {j['client_email']}).")
    if os.environ.get("NF_GPLAY_NO_NET"):
        서명(j)
        print("  (시험: 서명까지 확인했습니다 — 구글에는 묻지 않았습니다)")
        return
    try:
        토큰(j)
    except Exception:
        sys.exit("구글 로그인에 실패했습니다 — 열쇠 파일이 맞는지, «Google Play Android Developer API»를 켰는지 확인해 주십시오.")
    pk = 이폴더패키지() if "--pkg" not in args else _패키지(args)
    if not pk:
        print("  붙었습니다. 이 폴더에서 안드로이드 앱 식별 이름을 못 찾아, 앱 접근은 아직 확인하지 않았습니다.")
        return
    try:
        e = req(j, "POST", f"{pk}/edits", {})
        req(j, "DELETE", f"{pk}/edits/{e['id']}")
        print(f"  붙었습니다 — 앱 «{pk}»의 스토어 정보에 닿습니다.")
    except Exception:
        sys.exit(f"구글에는 붙었지만 앱 «{pk}»에 닿지 못했습니다 — Play Console «사용자 및 권한»에서 서비스 계정에 이 앱 권한을 주셨는지 확인해 주십시오.")


def cmd_meta(args):
    kp, j = _열쇠()
    if not j:
        sys.exit("구글 플레이 연결이 아직 없습니다 — gplay.py 준비 를 먼저 부르십시오.")
    pk = _패키지(args)
    rest = [a for a in args if a not in ("--confirm",)]
    if "--pkg" in rest:
        i = rest.index("--pkg"); rest = rest[:i] + rest[i + 2:]
    e = req(j, "POST", f"{pk}/edits", {})
    try:
        ls = req(j, "GET", f"{pk}/edits/{e['id']}/listings").get("listings", [])
        if not rest:
            for l in ls:
                print(f"  [{l.get('language')}]")
                for k in 칸이름:
                    v = (l.get(k) or "(비어 있음)").replace("\n", " ")
                    print(f"    {칸이름[k]:8s} {v[:80]}" + (f" … ({len(l.get(k) or '')}자)" if len(l.get(k) or "") > 80 else ""))
            return
        if rest[0] != "set" or len(rest) < 4 or rest[2] not in 칸이름:
            sys.exit("쓰는 법: meta set <언어 예: ko-KR | en-US> <title|shortDescription|fullDescription> <값> [--confirm]")
        lang, k, val = rest[1], rest[2], rest[3]
        old = next((l.get(k) or "" for l in ls if l.get("language") == lang), None)
        print(f"  {pk} · [{lang}] {칸이름[k]}")
        print(f"    지금: {(old if old is not None else '(이 언어 없음 — 새로 만듭니다)')[:200] or '(비어 있음)'}")
        print(f"    바꿀 것: {val[:200]}")
        if "--confirm" not in sys.argv:
            print("  (아직 안 바꿨습니다 — 사용자가 좋다고 하시면 --confirm 을 붙여 다시 부르십시오)")
            return
        req(j, "PATCH", f"{pk}/edits/{e['id']}/listings/{lang}", {k: val})
        req(j, "POST", f"{pk}/edits/{e['id']}:commit")
        e = None
        print("  ✓ 바꿨습니다 — 구글 검토 뒤 스토어에 나갑니다.")
    finally:
        if e:
            try:
                req(j, "DELETE", f"{pk}/edits/{e['id']}")
            except Exception:
                pass


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    if a[0] == "준비":
        cmd_준비(a[1:])
    elif a[0] == "meta":
        cmd_meta(a[1:])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
