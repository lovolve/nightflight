#!/usr/bin/env python3
"""`ledger.sh 등록` 이 부른다 — 서버에서 읽은 이용권 칸(JSON)을 보고 등록할 때 알려 드릴 말을 찍는다."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 제품이름
영어 = os.environ.get("NFL") == "en"


def 말(ko, en):
    return en if 영어 else ko


주소 = "https://www.lovolve.app/nightflight/#price"
열쇠 = os.environ["KEYSH"]
try:
    d = json.loads(os.environ.get("KAN") or "")
except ValueError:
    d = None
bid = os.environ.get("BID") or ""
이름표 = 제품이름.목록()
def 보임(b):
    return 제품이름.보임(b, 이름표)
if not isinstance(d, dict):
    print(말("  플랜의 제품등록은 지금 확인하지 못했습니다 — 아이디어 · 검증 단계는 그대로 쓰실 수 있습니다.",
             "  Could not check your plan's product slots right now. Plan and Validate still work as usual."))
else:
    무료 = d.get("무료앱")
    import datetime as _dt
    def _한국날(v):
        try:
            t = _dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
            return (t + _dt.timedelta(hours=9)).strftime("%Y-%m-%d") if t.tzinfo else str(v)[:10]
        except (ValueError, TypeError):
            return ""
    끝 = _한국날(d.get("무료끝")) if d.get("무료끝") else ""
    오늘 = _dt.date.today().isoformat()
    칸, 앱들 = (d.get("칸수"), d.get("앱들") or []) if d.get("있나") else (None, [])
    접은 = (d.get("접은제품") or []) if d.get("있나") else []
    if bid and (bid == 무료 or bid in 앱들):
        print(말("  이 제품은 이미 제품등록돼 있습니다(" + ("무료 제품" if bid == 무료 else "플랜") + ").",
                 "  This product already has a product slot (" + ("free slot" if bid == 무료 else "plan") + ")."))
    elif not 무료 and 끝 and 끝 < 오늘 and not d.get("있나"):
        print(말("  이 컴퓨터의 무료 1년이 끝났습니다(" + 끝 + "). 설계 단계부터는 이용권이 필요합니다. 플랜 안내: " + 주소,
                 "  The free year on this computer ended on " + 끝 + ". From Design on, you need a plan. Plans: " + 주소))
    elif not 무료:
        print(말("  설계 단계에 들어가면 이 제품이 이 컴퓨터의 무료 제품으로 제품등록됩니다(이 컴퓨터의 무료 1년 동안" + ((" · " + 끝 + "까지") if 끝 else "") + ").",
                 "  When this product reaches Design, it takes this computer's free product slot (free for one year on this computer" + ((", until " + 끝) if 끝 else "") + ")."))
    elif not d.get("있나"):
        print(말("  ⚠️ 이 컴퓨터의 무료 제품은 이미 «%s» 입니다(컴퓨터 한 대에 1개)." % 보임(무료),
                 "  ⚠️ This computer's free slot is already used by \"%s\" (one per computer)." % 보임(무료)))
        print(말("     아이디어 · 검증 단계는 그대로 쓰실 수 있고, 설계 단계부터는 이 제품에 이용권이 필요합니다. 플랜 안내: " + 주소,
                 "     Plan and Validate still work. From Design on, this product needs a plan. Plans: " + 주소))
    elif 칸 is not None and len(앱들) + len(접은) >= int(칸):
        _쓴것 = ", ".join([보임(a) for a in 앱들] + [보임(a) + 말("(접음)", " (paused)") for a in 접은])
        print(말("  ⚠️ 플랜의 제품등록 %d개를 이미 다 쓰셨습니다(무료 제품 %s · 유료 %s)." % (int(칸) + 1, 보임(무료), _쓴것),
                 "  ⚠️ All %d product slots on your plan are in use (free: %s · paid: %s)." % (int(칸) + 1, 보임(무료), _쓴것)))
        print(말("     아이디어 · 검증 단계는 그대로 쓰실 수 있습니다. 제품등록은 설계 단계부터라, 그때 이 제품도 1개가 됩니다.",
                 "     Plan and Validate still work. Slots count from Design, so this product will need one then."))
        print(말("     플러스 플랜으로 바꾸시거나, 다른 제품의 제품등록을 푸시면 그 자리가 바로 돌아옵니다(같은 제품을 다시 넣는 것은 30일 뒤입니다). 플랜 안내: " + 주소,
                 "     Switch to the Plus plan, or free another product's slot to get it back right away (the same product can take a slot again after 30 days). Plans: " + 주소))
        print("  [모델] 괄호 안이 제품 번호입니다. 풀려면 사용자가 고른 제품으로 " + 열쇠 + " 앱빼기 <제품 번호> 확인 · 플러스로 바꾸려면 " + 열쇠 + " 등급 플러스 (라이선스 키는 필요 없습니다 · 결제한 메일로 확인 링크가 갑니다)")
    else:
        _씀 = len(앱들) + len(접은)
        if 칸 is None:
            남 = 말("제한 없음", "no limit")
        else:
            남 = 말("%d개 중 %d개 사용 중(무료 1 + 유료 %d/%d)" % (int(칸) + 1, _씀 + 1, _씀, int(칸)),
                   "%d of %d in use (1 free + %d/%d paid)" % (_씀 + 1, int(칸) + 1, _씀, int(칸)))
        print(말("  플랜의 제품등록: " + 남 + " — 설계 단계에 들어가면 이 제품도 1개가 됩니다.",
                 "  Product slots on your plan: " + 남 + ". This product will take one when it reaches Design."))

목록 = {}
try:
    for 줄 in open(os.environ.get("PERSON") or "/nonexistent", encoding="utf-8", errors="replace"):
        칸들 = 줄.rstrip("\n").split("\t")
        if len(칸들) > 3 and 칸들[1] == "프로젝트" and os.path.isdir(칸들[2]):
            목록[칸들[2]] = 칸들[3]
except OSError:
    pass
if 목록:
    쓰는 = (set(d.get("앱들") or []) if d.get("있나") else set()) | ({d.get("무료앱")} if d.get("무료앱") else set()) if isinstance(d, dict) else set()
    칸씀 = [p for p, b in 목록.items() if b and b in 쓰는]
    print(말("  이 컴퓨터에 등록한 프로젝트 %d개 — 제품등록(설계 단계 이상) %d개 · 아이디어 · 검증 중 %d개." % (len(목록), len(칸씀), len(목록) - len(칸씀)),
             "  Projects registered on this computer: %d. With a product slot (Design or later): %d. In Plan or Validate: %d." % (len(목록), len(칸씀), len(목록) - len(칸씀))))
