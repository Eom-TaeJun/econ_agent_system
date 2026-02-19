---
description: 완료된 분석을 리포트로 저장
argument-hint: [파일명 또는 주제] (생략 시 자동 생성)
allowed-tools: Read, Write
---

지금까지 이 세션에서 수행된 분석 결과를 종합하여 리포트를 작성하라.

**report-writer 에이전트를 사용해 다음 구조로 작성하라:**

1. Executive Summary (3-5줄)
2. 분석 기준일 및 데이터 소스
3. 거시 레짐 판단 + 근거
4. 주요 시그널 현황
5. 리스크 요인 (상방/하방)
6. 결론 및 실행 함의

**저장 경로:**
- 지정된 파일명이 있으면: `outputs/$ARGUMENTS.md`
- 없으면: `outputs/report_YYYYMMDD_HHMMSS.md`

저장 완료 후 파일 경로와 Executive Summary를 출력하라.
