#!/usr/bin/env python3
"""야간비행 도구"""
import json
import os
import re
import sys

번호없음 = ("(번호없음)", "no-bundle-id")


def 목록(길=None):
    집 = os.environ.get("NF_HOME") or os.environ.get("NIGHTFLIGHT_HOME") or os.path.expanduser("~/.nightflight")
    길 = 길 or os.environ.get("PERSON") or os.path.join(집, "people.tsv")
    표 = {}
    try:
        with open(길, encoding="utf-8", errors="replace") as f:
            for 줄 in f:
                칸 = 줄.rstrip("\n").split("\t")
                if len(칸) > 3 and 칸[1] == "프로젝트" and 칸[3].strip():
                    이름 = re.sub(r"[^\w .-]", "", os.path.basename(칸[2].rstrip("/")))[:40].strip()
                    if 이름:
                        표[칸[3].strip()] = 이름
    except OSError:
        pass
    return 표


def 보임(번호, 표, en=False):
    번호 = str(번호)
    if 번호 in 번호없음:
        return "no app id" if en else "앱 번호를 못 읽은 제품"
    if 번호 in 표:
        return "%s (%s)" % (표[번호], 번호)
    return ("A product registered on another computer (%s)" if en else "다른 컴퓨터에서 등록한 제품(%s)") % 번호


def main():
    en = (os.environ.get("NFL") or os.environ.get("NF_LANG")) == "en"
    인자 = sys.argv[1:]
    if 인자 == ["--서버답"]:
        try:
            d = json.loads(os.environ.get("ANSWER") or "")
            인자 = [str(x) for x in d.get("앱들") or []]
        except (ValueError, AttributeError):
            인자 = []
    표 = 목록()
    for 번호 in 인자:
        print(보임(번호, 표, en))


if __name__ == "__main__":
    main()
