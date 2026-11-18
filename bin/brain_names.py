#!/usr/bin/env python3
"""서버가 보낸 안내 이름 목록에서 이 플러그인이 보이지 않을 이름을 뺀다."""
import hashlib
import json
import sys

숨김 = frozenset({
    "7bf8f2b9891698d314213a6485765d47efc47464f8909891207fb056d03b93d1",
    "a508ed77a4699c6ab5d7a127c1c90480dc1b972a81436cda7513a3798e565048",
    "6175ca7814d83250f0218ce731856d11f47d47a93a15010e26745baafc7846ec",
    "8131958cf325676600f5d87f587bf025fe876f1224d9130e374c97ff77fdb70a",
    "d95e9f4bbee5d0aacbc14707843c0d62cac6598b15609df129a223ef8182ffe8",
    "3e285d7581509041226bac66219ded4ffbd2091b214b32ffbf8c1de6f209744a",
    "035534c168c383e87f2e5cb65d3fc8aea99b88c14955a3e00a63e29491cac81d",
    "9eea17faf55ac3198bc4c1206559162621796e28587104324ab3d8be3b3475a6",
    "9f56b18380fd584a1f00f8b890dee81991abacb36f13eb30dab05e0452cf20a7",
})


def 보일것(이름들):
    return [g for g in (이름들 or []) if hashlib.sha256(("야간비행목록:" + str(g)).encode()).hexdigest() not in 숨김]


if __name__ == "__main__":
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except Exception:
        d = {}
    print(" · ".join(보일것(d.get("이_단계에_있는_갈래"))))
