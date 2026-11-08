#!/usr/bin/env python3
"""설계 단계에 들어가면 첫 할 일 «기능마다 표준 구현 방식 조사»를 알린다 — 막지 않는다."""
import os, sys
from pathlib import Path

기록 = Path(sys.argv[1]) if len(sys.argv) > 1 else None
if not 기록 or not 기록.is_file():
    sys.exit(0)
도구 = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(도구))
os.environ.setdefault("NF_STATE", str(기록.parent))
try:
    import standards, plan
    st = standards.compute(기록)
    d = plan.compute() if hasattr(plan, "compute") else {}
except Exception:
    st, d = {"기능별": {}}, {}

기능들 = []
for k, p in ((d or {}).get("단계") or {}).items():
    if not str(k).isdigit() or int(k) < 4:
        continue
    for f in p.get("기능들") or []:
        if f.get("기능") and f["기능"] not in 기능들:
            기능들.append(f["기능"])
빈것 = [f for f in 기능들 if not any(standards.완성(x) for x in (st.get("기능별") or {}).get(f, []))]

print("  · 설계의 첫 할 일 — 기능마다 표준방식을 확인합니다.")
print("    [모델] 다른 설계보다 먼저 하십시오. 기능마다 «도구 조합에서 만든 회사와 많은 앱이 하는 방식»을 찾고, 실패 경우까지 적으십시오.")
print("    [모델] 믿을 차례: 공식 문서 · 공식 예제 → 널리 쓰는 패키지의 권장 사용법 → 같은 기능 앱 3~5개 → 직접 돌려 본 결과. 기억만으로 적지 않습니다.")
print("    [모델] 적는 법: ledger.sh 표준 \"<방식>\" \"<출처>\" 공식문서|남이한것|돌려봄 \"<기능>\" \"<도구 조합>\" \"<실패 경우>\"")
if 빈것:
    print("    표준방식 확인이 아직 없는 기능 %d개: %s" % (len(빈것), " · ".join(빈것[:12]) + (" …" if len(빈것) > 12 else "")))
elif 기능들:
    print("    설계표의 기능 %d개 모두 표준방식 확인이 있습니다." % len(기능들))
