---
name: 1-기획
description: 기획 단계일 때 쓴다 — 무엇을 만들지, 누구를 위한 것인지, 무엇으로 돈을 받을지를 정할 때. 초안을 먼저 보여 주고, 사용자가 정할 것은 항목별 선택지로 고르게 한다 (야간비행에 등록한 프로젝트에서만 쓴다)
---

**English-speaking user** (the user writes in English, or a Nightflight notice says LANGUAGE: English): stop reading this file. Read `${CLAUDE_PLUGIN_ROOT}/skills/1-기획/en.md` and follow it instead, and write to the user in English.

# 1-기획


## 무엇을 하는 단계인가

**결정 ①** 기획 확정 — 타깃도 같이 확정한다.

## 도구

큰 변경 전 계획 · 진행 표시 · 화면 직접 확인 · 코드 검토는 `${CLAUDE_PLUGIN_ROOT}/data/tool_use.md` 를 따른다.

## 두뇌에 무엇을 묻나

타깃을 좁히는 틀과 벤치마크 고르는 법은 **두뇌가 내려준다**.

⭐ **부르는 법** — 이 단계에 들어오면 **먼저 묻는다**:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/brain.sh" 1 <갈래>
```

갈래를 모르면 아무 말이나 넣으면 **물을 수 있는 갈래 목록**이 돌아온다.
⛔ 받은 것을 **파일로 적어 두지 않는다** — 적는 순간 노하우가 깔려 나간다(기획 §43-6).
⛔ 못 받아도 **멈추지 않는다.** 아는 것만으로 진행하고 **「두뇌에서 못 받았다」고 적는다.**

## 사용자에게 묻는 법

물을 일이 생기면 먼저 `${CLAUDE_PLUGIN_ROOT}/data/asking.md` 를 읽고 그대로 묻는다 — 항목별 선택지 · 권장안 맨 위 · «아직 모르겠다».

정한 것은 칸마다 적는다.

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/ledger.sh" 제품소개 <한줄|누구|문제|대안|왜지금|해결|뺄것|성공기준|첫사용자|수익> "<사용자의 말>"
```

## ⛔ 못 — 이 단계에서 하지 않는 것

1. **찾을 수 있는 것을 묻지 않는다.** 리서치로 채워 **초안을 먼저** 보여준다
2. **평점으로 벤치마크를 고르지 않는다**
3. 페르소나의 **한계를 같이 말한다** — 흉내다. 실제 사용자 확인과 짝을 이룬다
