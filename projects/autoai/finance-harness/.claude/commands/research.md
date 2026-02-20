---
description: 뉴스 및 문서 리서치 (감성 분석 포함)
argument-hint: <topic>
allowed-tools: Read, Bash
---

다음 주제를 리서치하라: "$ARGUMENTS"

finance-researcher 에이전트를 사용하여:

## Step 1 — Perplexity 뉴스 수집

```bash
./scripts/api-helpers/perplexity-search.sh "$ARGUMENTS"
```

관련 키워드로 추가 검색:
```bash
./scripts/api-helpers/perplexity-search.sh "$ARGUMENTS market impact 2026"
./scripts/api-helpers/perplexity-search.sh "$ARGUMENTS analyst opinion"
```

## Step 2 — 결과 분석 및 감성 점수

수집된 뉴스를 분석하여:
- 3줄 핵심 요약
- 주요 인용문 (최소 2개)
- 감성 점수 (1-10)
- 신뢰도 평가 (High/Medium/Low)

## Step 3 — 인라인 출력

결과를 직접 출력 (파일 저장 없음).

**형식:**
```
## Research: {TOPIC}
**검색일:** {DATE}

### 요약
1. [핵심 포인트 1]
2. [핵심 포인트 2]
3. [핵심 포인트 3]

### 주요 인용
- "{인용문}" — {출처}, {날짜}

### 감성 점수: {X}/10 ({Bullish/Neutral/Bearish})
**근거:** {2-3줄}

### 신뢰도: {High/Medium/Low}

### 출처
[1] {URL}
[2] {URL}
```
