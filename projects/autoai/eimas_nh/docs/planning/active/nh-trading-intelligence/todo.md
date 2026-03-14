---
plan_id: nh-trading-intelligence
status: active
last_updated: 2026-03-14
---

# NH Trading Intelligence Todo

## Now

- [ ] NH FICC / 채권시장동향 기준 sample memo field 확정
- [ ] `forecast` 결과를 NH memo의 `scenario_watchlist`에 어떻게 올릴지 정리
- [ ] `미국 금리 경로 -> 국내 금리커브/FICC` sample memo 1호 초안 작성
- [ ] README의 긴 범용 투자 설명 더 줄이기
- [ ] NH용 sample artifact fixture 추가

## Next

- [ ] `NHTradingDeskMemoV0`를 markdown/html exporter에 우선 노출
- [ ] NH role profile 기준 자기소개서 공통 문장 초안 연결
- [ ] `duration shock`, `curve repricing`, `margin/liquidity` 리스크 블록을 메모 템플릿에 반영

## Later

- [ ] NH용 sample memo 2종 금리/FICC, 시장구조 작성
- [ ] desk 메모와 면접 답변 연결 문장 모음 정리

## Done

- [x] `eimas_mpi` 기반으로 `eimas_nh` 경량 복사
- [x] NH Trading 전용 planning harness 추가
- [x] `core_message.md`로 사람상 단일 문장 고정
- [x] `evaluation_rubric.md`로 합격 기준 고정
- [x] `memo_contract.md`로 `NHTradingDeskMemoV0` 최소 계약 정의
- [x] NH Trading의 우선 축을 `채권/금리/FICC`로 재정렬
- [x] sample scenario 1을 `미국 금리 경로 -> 국내 금리커브/FICC`로 고정
