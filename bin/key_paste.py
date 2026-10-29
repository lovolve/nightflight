#!/usr/bin/env python3
"""붙여 넣기 장치(key_paste.sh)의 검사 — 훅 입력(JSON)을 표준입력으로 받아, 막을 것·알릴 것·할 일 없음(PASS)을 낸다.

🔴 6회차 보안 레드팀(추정): 윈도우의 파이썬은 `/dev/fd/3` 를 못 열어서, 셸 안 heredoc 으로 넘기던 이 글이 늘 실패했다 —
   그러면 키를 넣을 때마다 셸 대비책이 「잠시 뒤 다시」만 냈다(영구 실패인데 일시 장애처럼). ⭐ 그래서 파일로 뺐다.
⛔ 이 파일은 사용자 폴더에서 돈다 — 반드시 `python3 -I` 로 부른다(폴더의 가짜 모듈을 안 집게).
"""
import json, os, re, subprocess, sys, unicodedata
try:
    sys.stdout.reconfigure(encoding="utf-8")
    prompt = (json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}") or {}).get("prompt", "") or ""
    if not isinstance(prompt, str):
        raise ValueError("prompt 가 글이 아니다")
except Exception:
    sys.exit(0)
접기 = str.maketrans("АВСЕНІЈКМНОРЅТХУаеорсухіјѕΑΒΕΖΗΙΚΜΝΟΡΤΥΧον〜ㅡ",
                     "ABCEHIJKMHOPSTXYaeopcyxijsABEZHIKMNOPTYXov--")
prompt = unicodedata.normalize("NFKC", prompt)
prompt = "".join(c for c in prompt if unicodedata.category(c) not in ("Cf", "Mn", "Me") and c not in "\u3164\u115f\u1160\uffa0\u2800")
prompt = re.sub(r"[‐-―−﹘﹣－]", "-", prompt.translate(접기))
keysh = os.environ["KEYSH"]
en = os.environ.get("NFL") == "en"
def 두말(ko, en_):
    return en_ if en else ko
def 막기(said):
    속 = {"hookEventName": "UserPromptSubmit"}
    if os.environ.get("NF_HOST_CLAUDE"):
        속["suppressOriginalPrompt"] = True
    print(json.dumps({"decision": "block", "reason": said, "hookSpecificOutput": 속}, ensure_ascii=False))
    sys.exit(0)
키글 = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
KEY = re.compile(r"(?<![A-Z0-9])NF-[" + 키글 + r"]{8}-[" + 키글 + r"]{10}(?:(?![A-Za-z0-9])|(?=\d{1,2}\s{0,2}번))")
예시키 = {"NF-ABCDEFGH-JKMNPQRSTU"}
def 예시인가(k):
    속 = re.sub(r"[^A-Z0-9]", "", k.upper())[2:]
    return 속 in {re.sub(r"[^A-Z0-9]", "", x)[2:] for x in 예시키} or len(set(속)) <= 2
구분 = r"[^A-Za-z0-9가-힣]{0,4}"
닮은키틀 = re.compile(r"(?<![A-Za-z0-9])([Nn])" + 구분 + r"([Ff])[^A-Za-z0-9가-힣]{0,6}([A-Za-z0-9](?:" + 구분 + r"[A-Za-z0-9]){16}(?:" + 구분 + r"[A-Za-z0-9]){0,2})")
붙은키틀 = re.compile(r"([Nn][Ff])-([A-Za-z0-9]{8}-[A-Za-z0-9]{10})")
키맥락 = re.compile(r"(?i)\b(?:license|key|activate)\b|키|라이선스|라이센스|넣어|등록|붙여")
def 글인가(몸글):
    조각 = re.findall(r"[A-Za-z0-9]+", 몸글)
    길이 = [len(t) for t in 조각]
    글자 = re.findall(r"[A-Za-z]", 몸글)
    if "_" in 몸글 and any(t.isalpha() and len(t) >= 5 for t in 조각):
        return True
    if len(re.findall(r"[IiLlOo01]", 몸글)) >= 2:
        return True
    if re.search(r"\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}", 몸글):
        return True
    if len(글자) < 4 or (sum(1 for c in 글자 if c in "AEIOUaeiou") / len(글자) >= 0.4 and re.search(r"[IOio]", 몸글)):
        return True
    def 고른(L): return len(set(L[:-1])) <= 1 and (len(L) < 2 or L[-1] <= L[0] + 1)
    def 키모양(L):
        if len(L) <= 1 or 고른(L): return True
        if len(L) <= 6 and any(7 <= sum(L[:i]) <= 9 and 9 <= sum(L[i:]) <= 11 and i <= 3 and len(L) - i <= 3 for i in range(1, len(L))):
            return True
        for i in range(1, len(L)):
            if 7 <= sum(L[:i]) <= 9 and len(set(L[:i])) == 1 and 고른(L[i:]): return True
        return False
    if not (키모양(길이) or (len(길이) > 1 and sum(길이[:-1]) >= 17 and 키모양(길이[:-1]))):
        return True
    if 길이[:2] in ([8, 10], [8, 9], [8, 11]) or (len(길이) >= 3 and len(set(길이[:-1])) == 1 and 길이[0] >= 3):
        return False
    낱말 = [t for t in 조각 if t.isalpha() and len(t) >= 3]
    if len(낱말) >= 2 and len({len(t) for t in 낱말}) > 1:
        return True
    if len(조각) >= 4 and sum(1 for t in 조각 if t.isalpha() and len(t) >= 2) >= 3:
        return True
    return False
머리없는키틀 = re.compile(r"(?<![A-Za-z0-9])[" + 키글 + r"]{8}-[" + 키글 + r"]{10}(?![A-Za-z0-9-])")
import bisect
def 덩이자리(글, 꼴):
    자리 = [(m.start(), m.end()) for m in re.finditer(꼴, 글)]
    시작들 = [s for s, _ in 자리]
    def 품은(i):
        k = bisect.bisect_right(시작들, i) - 1
        return 자리[k] if k >= 0 and 자리[k][0] <= i < 자리[k][1] else None
    def 찾기(i, j):
        왼, 오 = 품은(i), 품은(j - 1)
        return (왼[0] if 왼 else i, 오[1] if 오 else j)
    return 찾기
def 닮은키(글):
    기억 = {}
    def 셈(열쇠, 재기):
        if 열쇠 not in 기억:
            기억[열쇠] = 재기()
        return 기억[열쇠]
    큰덩이 = 덩이자리(글, r"[A-Za-z0-9+/=_-]+")
    이름덩이 = 덩이자리(글, r"[A-Za-z0-9-]+")
    알덩이 = 덩이자리(글, r"[A-Za-z0-9]+")
    for x in 머리없는키틀.finditer(글):
        if re.search(r"[2-9]", x.group(0)) and re.search(r"[A-Z]", x.group(0)) and not 예시인가("NF-" + x.group(0)):
            return True
    for x in 붙은키틀.finditer(글):
        속 = re.sub(r"[^A-Za-z0-9]", "", x.group(2))
        if re.search(r"[0-9]", 속) and not 예시인가("NF-" + 속.upper()) and not (x.group(1) == "nf" and not re.search(r"[A-Z]", 속)) \
           and len(re.findall(r"[IiLlOo01]", 속)) < 2:
            return True
    for x in 닮은키틀.finditer(글):
        머리, 몸글 = x.group(1) + x.group(2), x.group(3)
        a, b = 큰덩이(x.start(), x.end())
        if b - a > 40 and 셈(("+/=", a, b), lambda: bool(re.search(r"[+/=]", 글[a:b]))):
            continue
        e, f2 = 알덩이(x.start(3), x.start(3) + 1)
        if f2 - e >= 19 and len(re.findall(r"[a-z][A-Z]|[A-Z][a-z]", 글[e:f2])) >= 4:
            continue
        속 = "".join(re.findall(r"[A-Za-z0-9]", 몸글))
        if not re.search(r"[0-9]", 속) or 예시인가("NF-" + 속.upper()) or 글인가(몸글):
            continue
        if 머리 == "nf" and not re.search(r"[A-Z]", 속[:17]):
            c, d = 이름덩이(x.start(), x.end())
            if 셈(("-", c, d), lambda: 글.count("-", c, d)) >= 3:
                continue
            if re.fullmatch(r"nf-[a-z]+-[bcdfghjklmnpqrstvwxz2456789]{10}", 글[c:d]):
                continue
            y = re.fullmatch(r"nf-([a-hjkmnp-z2-9]{8})-([a-hjkmnp-z2-9]{10})", 글[c:d])
            if y and re.search(r"[2-9]", y.group(0)):
                if not (y.group(1).isalpha() and re.fullmatch(r"[bcdfghjklmnpqrstvwxz2456789]+", y.group(2))):
                    return True
                continue
            if 키맥락.search(글[max(0, x.start() - 40): x.end() + 40]) or (len(글) < len(x.group(0)) + 20 and re.sub(r"[\s\W_]", "", 글) == re.sub(r"[\s\W_]", "", x.group(0))):
                return True
            continue
        return True
    return False
m = KEY.search(prompt)
등급말 = r"(플러스|헤비|라이트|plus|heavy|lite)"
등급꼴 = [re.compile(r"(?:지금|이제)?\s{0,3}" + 등급말 + r"\s{0,3}(?:플랜)?\s{0,3}(?:으로|로)\s{0,3}"
                     r"(?:바꿔|전환해|변경해|올려|내려)\s{0,3}(?:줘|주세요|주십시오)?\s{0,3}[.!]?", re.I),
          re.compile(등급말 + r"\s{0,3}(?:플랜)?\s{0,3}(?:으로|로)?\s{0,3}확정\s{0,3}(?:해\s{0,3}(?:줘|주세요)?)?\s{0,3}[.!]?", re.I),
          re.compile(r"(?:please\s{1,3})?(?:switch|change|upgrade|downgrade|move)\s{1,3}(?:me\s{1,3}|my\s{1,3}plan\s{1,3})?to\s{1,3}(?:the\s{1,3})?"
                     + 등급말 + r"(?:\s{1,3}plan)?(?:\s{1,3}please)?\s{0,3}[.!]?", re.I)]
def 명령(글, 꼴들):
    t = 글.strip()
    if not t or len(t) > 300:
        return None
    for c in 꼴들:
        x = c.fullmatch(t)
        if x:
            return x
    return None
번호꼴 = [re.compile(r"(\d)\s{0,3}번\s{0,3}(?:컴퓨터\s{0,3})?(?:풀기|풀어|빼기|빼)\s{0,3}(?:줘|주세요)?\s{0,3}[.!]?"),
          re.compile(r"(?:풀기|빼기)\s{0,3}(\d)\s{0,3}[.!]?"),
          re.compile(r"(?:release|remove)\s{1,3}(?:computer\s{1,3})?#?(\d)\s{0,3}[.!]?", re.I)]
등급이름 = {"플러스": "헤비", "plus": "헤비", "heavy": "헤비", "lite": "라이트"}

def run(*args, key=""):
    try:
        p = subprocess.Popen([os.environ.get("NF_BASH") or "bash", keysh, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                             start_new_session=True)
        try:
            o, e = p.communicate(input=key + "\n", timeout=15)
        except subprocess.TimeoutExpired:
            try:
                import signal
                os.killpg(p.pid, signal.SIGKILL)
            except Exception:
                p.kill()
            p.communicate()
            raise
        out = (o or "") + (e or "")
    except Exception:
        out = 두말("지금 서버에 닿지 못했습니다. 라이선스 키가 틀린 것이 아닙니다 — 잠시 뒤에 다시 해 주십시오.",
                  "Couldn't reach the Nightflight server. Your key is fine — please try again in a moment.")
    lines = [l.strip() for l in out.splitlines() if "[모델]" not in l]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines).strip() or 두말("서버가 아무 말도 돌려주지 않았습니다. 잠시 뒤에 다시 해 주십시오.",
                                          "No response from the server. Please try again in a moment.")

if m and 예시인가(m.group(0)):
    m = None
없는등급꼴 = [re.compile(r"(?:지금|이제)?\s{0,3}(맥스|무제한|max|unlimited)\s{0,3}(?:플랜)?\s{0,3}(?:으로|로)\s{0,3}"
                    r"(?:바꿔|변경|올려|내려|옮겨|전환)\s{0,3}(?:해\s{0,3})?(?:줘|주세요|주십시오|요)?\s{0,3}[.!]?", re.I),
           re.compile(r"(?:please\s{1,3})?(?:switch|change|upgrade|move)\s{1,3}(?:me\s{1,3}|my\s{1,3}plan\s{1,3})?to\s{1,3}(?:the\s{1,3})?"
                    r"(max|unlimited)(?:\s{1,3}plan)?\s{0,3}[.!]?", re.I)]
if m and 명령(KEY.sub(" ", prompt), 없는등급꼴):
    막기(두말("맥스 플랜은 아직 없습니다. 지금 고르실 수 있는 플랜은 라이트·플러스입니다(키는 그대로 두었습니다).",
            "There's no Max plan yet. The plans available now are Lite and Plus (your key wasn't changed)."))
if m:
    k = m.group(0)
    rest = KEY.sub(" ", prompt)
    grade = 명령(rest, 등급꼴)
    n = None if grade else 명령(rest, 번호꼴)
    if grade:
        g = 등급이름.get(grade.group(1).lower(), grade.group(1))
        said = run("등급", g, "-", key=k)
    elif n:
        said = run("-", "풀기", n.group(1), key=k)
    else:
        said = run("-", key=k)
    if not (grade or n) and len(re.sub(r"[\s\W_]", "", rest)) > 20:
        said += "\n\n" + 두말("함께 쓰신 말씀은 AI에게 전하지 않았습니다. 키를 빼고 다시 보내 주십시오.",
                             "The rest of your message wasn't sent to the AI. Send it again without the key.")
    막기(said)
if 닮은키(prompt):
    막기(두말("라이선스 키처럼 보이는 글이 있어서 AI에게 보내지 않았습니다. 메일로 받은 키를 한 줄 그대로(띄어쓰기 없이) 다시 붙여 넣어 주십시오.",
            "Something that looks like a license key was in your message, so it wasn't sent to the AI. Paste the key from your email again on one line, exactly as it appears."))
if 명령(prompt, 등급꼴):
    ctx = ("야간비행: 이용권 등급을 바꾸시려는 말씀으로 보입니다. "
           "⛔ 라이선스 키를 대화로 받거나 명령을 부르지 마십시오. "
           "사용자에게 «바꾸실 플랜(라이트·플러스)과 라이선스 키를 한 메시지로 보내 주시면, 결제하신 메일로 금액이 적힌 "
           "확인 링크를 보내 드립니다 — 그 링크에서 확인하셔야 바뀝니다»라고만 전하십시오.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                             "additionalContext": ctx}}, ensure_ascii=False))
    sys.exit(0)
print("PASS")
