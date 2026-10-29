#!/usr/bin/env python3
"""반복 감지(`repeat_guard.sh`)가 부른다 — 방금 바뀐 파일 가운데 «이 대화의 이 명령이 고친 것»만 골라 찍는다.

받는 것: 환경값 NF_CMD(방금 돈 Bash 명령 글) · 표준입력(직전 표시 뒤에 바뀐 파일 경로, 한 줄에 하나).
찍는 것: 센 파일 경로(한 줄에 하나). 셸 안에 두었던 것을 15회차에 파일로 뺐다(셸 안 파이썬 검사).
"""
import os, re, sys
cmd = os.environ.get("NF_CMD", "")
q = chr(39)
민 = re.sub(q + "[^" + q + "]*" + q + "|\"(?:[^\"\\\\]|\\\\.)*\"", " ", cmd)
민 = re.sub(r"[0-9]*>&[0-9-]+|&>\s*/dev/null|[0-9]*>>?\s*/dev/null", " ", 민)
읽기 = {"cat", "head", "tail", "less", "more", "grep", "rg", "egrep", "wc", "ls", "file", "stat", "diff", "cmp", "md5", "shasum",
        "jq", "bat", "cd", "pwd", "echo", "printf", "true", "test", "which", "type", "sort", "uniq", "cut", "tr", "column", "nl"}
def 읽기뿐():
    if ">" in 민: return False
    날토막 = re.split(r"&&|\|\||[;|\n]", cmd)
    for i, x in enumerate(re.split(r"&&|\|\||[;|\n]", 민)):
        w = x.strip().split()
        while w and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=\S*", w[0]): w = w[1:]
        if not w: continue
        첫 = os.path.basename(w[0])
        if 첫 in 읽기: continue
        if 첫 == "sed" and "-n" in w and not any(a.startswith("-i") for a in w) and not re.search(r"(^|[;{}0-9/$p\s])w\s", " ".join(날토막[i:i + 1]) if i < len(날토막) else ""): continue
        if 첫 == "git" and len(w) > 1 and w[1] in ("log", "diff", "show", "blame", "status"): continue
        return False
    return True
if not 읽기뿐():
    for 줄 in sys.stdin:
        f = 줄.rstrip("\n"); b = os.path.basename(f)
        if b and b in cmd:
            print(f)
