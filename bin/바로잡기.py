#!/usr/bin/env python3
"""`ledger.sh 바로잡기` 의 몸 — 잘못 적은 기록 줄을 «지우지 않고 옮긴다».

🔴 왜 (2026-10-28 어느 앱으로 한 모델 비교 시험 — Opus · Sonnet · Haiku 셋 다):
   잘못 적은 줄(겹쳐 적은 영향 17쌍 · 틀린 인용 · «독립»으로 잘못 적은 결제 · 「단추」로 적은 화면 요소)을 고칠 명령이 없어
   셋 다 틀린 줄을 남긴 채 끝냈다. 하위 모델일수록 많았다 — 조종석에 같은 줄이 두 번, 틀린 줄이 그대로 보였다.
⭐ 옮긴 줄은 기록 자리의 `바로잡은줄.tsv` 에 «언제 · 어느 파일 · 왜 · 원래 줄» 로 남는다(이력은 줄이지 않는다). 조종석에서만 빠진다.

쓰는 법(ledger.sh 가 넘긴다): 바로잡기.py <기록 자리> <종류> <글 일부> <까닭>
  · 종류 — 기록 줄의 종류(결정 · 영향 · 독립 · 표준 · 상태 · 단계 · 시도 …). 화면 설계서 줄은 «화면:» 을 앞에 붙인다(화면:요소 · 화면:이름 · 화면:이동 …)
  · 종류 «겹침» — 날짜만 다르고 나머지가 같은 줄을 처음 것만 남기고 옮긴다(기록 · 화면 설계서 둘 다)
⛔ «등록» 줄은 옮기지 않는다(등록이 풀린다) · 맞는 줄이 둘 이상이면 옮기지 않고 목록을 보인다.
"""
import os, sys, time

st, 종류, 글, 왜 = (sys.argv[1:5] + ["", "", "", ""])[:4]
기록 = os.path.join(st, "ledger.tsv")
화면 = os.path.join(st, "screens.tsv")
남김 = os.path.join(st, "바로잡은줄.tsv")
오늘 = time.strftime("%Y-%m-%d")

def 읽기(p):
    try:
        return open(p, encoding="utf-8").read().split("\n")
    except OSError:
        return []

def 쓰기(p, 줄들):
    t = p + ".tmp%d" % os.getpid()
    with open(t, "w", encoding="utf-8") as f:
        f.write("\n".join(줄들))
    os.replace(t, p)

def 옮김(옮길):
    with open(남김, "a", encoding="utf-8") as f:
        for 이름, 줄 in 옮길:
            f.write("%s\t%s\t%s\t%s\n" % (오늘, 이름, (왜 or "겹침").replace("\t", " ").replace("\n", " "), 줄))

if 종류 == "겹침":
    합 = 0
    for p, 키 in ((기록, lambda c: tuple(c[1:])), (화면, lambda c: tuple(c))):
        줄들 = 읽기(p)
        if not 줄들:
            continue
        본, 남는, 옮길 = set(), [], []
        for 줄 in 줄들:
            c = 줄.split("\t")
            if not 줄.strip() or 줄.startswith("#") or (p == 기록 and len(c) > 1 and c[1] == "등록"):
                남는.append(줄); continue
            k = 키(c)
            if k in 본:
                옮길.append((os.path.basename(p), 줄))
            else:
                본.add(k); 남는.append(줄)
        if 옮길:
            쓰기(p, 남는); 옮김(옮길); 합 += len(옮길)
    print("  겹쳐 적은 줄 %d개를 옮겼습니다(처음 적은 것만 남김 · 옮긴 줄은 바로잡은줄.tsv 에 남습니다)." % 합)
    sys.exit(0)

if not 글.strip() or not 왜.strip():
    print("  ⛔ 바로잡을 줄의 글 일부와 까닭이 있어야 합니다.", file=sys.stderr); sys.exit(2)
if 종류 == "등록":
    print("  ⛔ 등록 줄은 바로잡지 않습니다 — 옮기면 이 프로젝트의 등록이 풀립니다.", file=sys.stderr); sys.exit(2)
if 종류.startswith("화면:"):
    p, k, 맞나 = 화면, 종류[3:], (lambda c: c[0] == 종류[3:])
else:
    p, k, 맞나 = 기록, 종류, (lambda c: len(c) > 1 and c[1] == 종류)
줄들 = 읽기(p)
찾음 = [i for i, 줄 in enumerate(줄들) if 줄.strip() and not 줄.startswith("#") and 맞나(줄.split("\t")) and 글 in 줄]
if not 찾음:
    print("  ⛔ «%s» 줄 가운데 「%s」 가 든 줄이 없습니다." % (종류, 글), file=sys.stderr); sys.exit(2)
if len(찾음) > 1:
    print("  ⛔ 맞는 줄이 %d개라 옮기지 않았습니다 — 글을 더 길게 주십시오:" % len(찾음), file=sys.stderr)
    for i in 찾음[:8]:
        print("     · " + 줄들[i][:150], file=sys.stderr)
    sys.exit(2)
줄 = 줄들.pop(찾음[0])
쓰기(p, 줄들); 옮김([(os.path.basename(p), 줄)])
print("  바로잡았습니다 — 조종석에서 뺐고, 원래 줄은 바로잡은줄.tsv 에 까닭과 함께 남겼습니다.")
