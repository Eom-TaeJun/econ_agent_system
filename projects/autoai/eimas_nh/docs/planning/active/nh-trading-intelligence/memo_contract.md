---
plan_id: nh-trading-intelligence
status: active
last_updated: 2026-03-14
---

# NH Trading Memo Contract v0

## 목적

`NH Trading Intelligence` vertical의 최소 산출물 계약을 정의한다.

이 문서는 새로운 거대한 스키마를 만드는 것이 아니라,
기존 `EIMASResult` 에서 어떤 필드가 NH Trading 기본 메모를 구성해야 하는지 정리한다.

---

## Output Name

`NHTradingDeskMemoV0`

목표는 아래 질문에 답하는 것이다.

1. 지금 금리와 채권 시장 환경은 어떤 상태인가
2. rates/FICC desk가 당장 읽어야 할 핵심 시나리오는 무엇인가
3. 커브와 유동성, 이벤트 재가격 관점의 실행 리스크는 무엇인가
4. 사람이 다시 확인해야 할 handoff는 무엇인가

---

## Minimum Sections

### 1. Metadata

- `generated_at`
- `as_of`
- `schema_version`
- `run_mode`
- `target_company`
- `target_role`

현재 매핑:

- `EIMASResult.timestamp`
- `EIMASResult.schema_version`
- `audit_metadata`

### 2. Market Context

- `regime`
- `trend`
- `volatility`
- `risk_score`
- `risk_level`
- `confidence`
- `vix_current`
- `net_liquidity`
- `treasury_2y`
- `treasury_10y`
- `spread_10y2y`
- `liquidity_regime`
- `curve_status`
- `rates_focus`

현재 매핑:

- `regime`
- `market_indicators`
- `fred_summary`
- `risk_score`
- `risk_level`
- `confidence`

### 3. Desk View

- `question`
- `summary_message`
- `thesis`
- `base_case`
- `risk_case`
- `desk_focus`
- `recent_signal_alignment`
- `events_detected`
- `scenario_watchlist`
- `cross_asset_ready`

현재 매핑:

- `final_recommendation`
- `events_detected`
- `information_flow`
- `institutional_analysis`
- `fomc_analysis`
- `warnings`

### 4. Execution Risk

- `market_structure_ready`
- `product_risk_focus`
- `rates_risk_focus`
- `handoff_required`
- `handoff_reason`
- `approval_status`
- `failsafe_status`

현재 매핑:

- `hft_microstructure`
- `warnings`
- `approval_status`
- `failsafe_status`

### 5. Evidence

- `fact_check_grade`
- `whitening_summary`
- `audit_metadata`
- `source_gap_notes`
- `recent_public_signals`

현재 매핑:

- `fact_check_grade`
- `whitening_summary`
- `audit_metadata`

### 6. Role Profile Briefs

- `securities-trading`

이 블록은 기술 설명보다
`이 프로젝트를 NH Trading 지원자답게 어떻게 말할지`를 고정한다.

---

## Current Problems

### 1. Desk thesis is still too implicit

현재 메모는 데이터는 보여주지만
`그래서 rates/FICC desk가 무엇을 읽어야 하는가`가 요약 문장에 덜 고정되어 있다.

### 2. Scenario language is weak

`base_case`, `risk_case`, `watchlist`가 지금은 얕게만 노출된다.

### 3. Product / execution risk is generic

`duration shock`, `curve repricing`, `liquidity`, `margin`를 넣어야 하는데,
현재는 NH Trading 문맥에서 어떤 상황에 왜 중요한지 설명층이 부족하다.

### 4. Source gap is not explicit enough

리서치/FICC/채권시장동향을 실제로 읽고 만든 샘플 메모라는 점이 아직 드러나지 않는다.

### 5. Recent NH emphasis is not explicit enough

2025년 하반기 이후 NH가 외부에 보여준
`전망 및 대응 전략`, `채권 가격발견`, `정책-커브-유동성 해석`,
`고객용 채권 언어`가 메모에 직접 드러나지 않는다.

---

## Proposed Serialized Shape

```json
{
  "metadata": {},
  "market_context": {},
  "desk_view": {},
  "execution_risk": {},
  "evidence": {},
  "role_profile_briefs": {}
}
```

이 정도 구조면 markdown memo, 면접용 PDF, 자소서 설명 문장에 공통으로 재사용할 수 있다.

---

## Mapping Rule

기존 `EIMASResult` 를 직접 폐기하지 않는다.

- `EIMASResult` 는 full run canonical artifact로 유지
- `NHTradingDeskMemoV0` 는 report/API/portfolio packaging이 읽는 축약 view로 둔다

즉 다음 단계는 아래 순서로 간다.

1. `EIMASResult -> NHTradingDeskMemoV0` 필드를 더 명시적으로 매핑
2. NH sample memo fixture 작성
3. markdown/html exporter와 자소서 설명 문장에 이 축약 view를 연결
