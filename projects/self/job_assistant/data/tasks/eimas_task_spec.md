# EIMAS 코드 추가 Task 명세서
> 머리(Claude Code)가 작성 → 손(Codex)이 task JSON 파일 생성
> 생성 위치: ~/projects/self/job_assistant/data/tasks/pending/

## 공통 JSON 포맷

```json
{
  "task_id": "<8자리 uuid>",
  "created_at": "<ISO8601>",
  "type": "code_modification",
  "project": "eimas",
  "project_path": "/home/tj/projects/autoai/eimas",
  "title": "<작업 제목>",
  "target_file": "<수정할 파일 경로 (project_path 기준 상대경로)>",
  "description": "<무엇을 왜 추가하는가>",
  "implementation_guide": "<구체적인 구현 방향>",
  "appeal_for": ["<어필 직군1>", "<어필 직군2>"],
  "cover_letter_pitch": "<자소서에서 이 기능을 어떻게 서술할지>",
  "priority": 1,
  "status": "pending"
}
```

---

## Task 1 — Kupiec/Christoffersen VaR Backtest

- **target_file**: `lib/stress_test.py`
- **title**: VaR 통계 검증 모듈 추가 (Kupiec + Christoffersen)
- **appeal_for**: AI Risk Engineer, Market Risk Engineer
- **priority**: 1

**description**:
현재 stress_test.py는 VaR를 계산하지만, 그 VaR 모델이 실제로 통계적으로 유효한지 검증하는 로직이 없다.
Kupiec POF Test와 Christoffersen Interval Forecast Test를 추가해 Basel 규제 기준 충족 여부를 자동으로 판정한다.

**implementation_guide**:
```
class VaRBacktest:
    def kupiec_pof_test(violations, n, confidence_level):
        # 위반 횟수(violations)와 전체 관측 수(n)로
        # LR_uc 통계량 계산 → chi2 분포 p-value
        # H0: 실제 위반율 = (1 - confidence_level)
        # return: {"lr_stat": float, "p_value": float, "reject_h0": bool}

    def christoffersen_test(violation_sequence):
        # 위반이 연속되는지 검정 (독립성)
        # 전환행렬 추정 → LR_ind 통계량
        # return: {"lr_stat": float, "p_value": float, "reject_h0": bool}

    def basel_traffic_light(violations, n):
        # 250거래일 기준 Basel 등급 판정
        # 0-4: 초록, 5-9: 노랑, 10+: 빨강
        # return: {"color": str, "violations": int, "threshold": int}

    def run_full_backtest(returns_series, var_series, confidence_level=0.99):
        # 전체 결과 딕셔너리 반환
```

**cover_letter_pitch**:
"VaR 모델이 통계적으로 유효한지 Kupiec Test로 검증하고, Basel Traffic Light 기준으로 등급을 산출했습니다.
좋아 보이는 리스크 수치도 통계적 검증 없이는 믿지 않는 원칙을 시스템에 내재화했습니다."

---

## Task 2 — Debate Effectiveness Logger

- **target_file**: `agents/methodology_debate.py`
- **title**: 에이전트 토론 효과 정량화 로거 추가
- **appeal_for**: Decision Scientist, AI Engineer
- **priority**: 1

**description**:
현재 methodology_debate.py는 에이전트들이 토론하고 결론을 내지만,
토론이 결론을 "얼마나" 바꾸는지 측정하지 않는다.
토론 전 각 에이전트의 초기 결론과 토론 후 최종 결론을 비교해
편향 제거 효과를 수치로 기록한다.

**implementation_guide**:
```
class DebateEffectivenessLogger:
    def record_initial_positions(agent_id, initial_conclusion, confidence):
        # 토론 시작 전 각 에이전트의 포지션 기록
        # {"agent_id": str, "initial": str, "confidence": float, "timestamp": str}

    def record_final_consensus(final_conclusion, rounds_taken):
        # 토론 후 최종 합의 기록

    def compute_effectiveness():
        # position_change_rate: 초기 대비 결론 바뀐 에이전트 비율
        # consensus_round: 몇 번째 라운드에서 합의됐는가
        # divergence_score: 초기 포지션 간 분산 (높을수록 다양한 관점)
        # return: {"change_rate": float, "consensus_round": int, "divergence": float}

    def save_log(output_path):
        # outputs/debate_logs/ 에 JSON 저장
```

**cover_letter_pitch**:
"에이전트 토론 전/후 결론 변경률을 측정했습니다. 다양한 페르소나의 토론이
단일 에이전트 대비 결론을 XX% 케이스에서 수정했으며, 이는 AI 편향 제거가
정성적 주장이 아니라 측정 가능한 효과임을 보여줍니다."

---

## Task 3 — Regime-Conditional Performance Metrics

- **target_file**: `lib/performance_attribution.py`
- **title**: 레짐별 포트폴리오 성과 지표 추가
- **appeal_for**: Quant Researcher, AI Risk Engineer
- **priority**: 2

**description**:
현재 performance_attribution.py는 성과 귀속 분석을 하지만,
레짐(Goldilocks/Overheating/Stagflation/Recession)별 성과 비교 테이블이 없다.
레짐 탐지가 포트폴리오 성과를 실제로 개선했는지 수치로 증명한다.

**implementation_guide**:
```
class RegimePerformanceAnalyzer:
    def compute_regime_metrics(returns_series, regime_labels):
        # 레짐별로 분리 후 각 성과 지표 계산
        # Sharpe Ratio: annualized (sqrt(252) 적용)
        # Calmar Ratio: annualized return / max drawdown
        # Max Drawdown: 누적 고점 대비 최대 낙폭
        # Win Rate: 양수 수익률 비율
        # return: DataFrame with regime x metric

    def compare_regime_aware_vs_naive(regime_returns, naive_returns):
        # 레짐 인식 전략 vs 단순 buy-and-hold 비교
        # Sharpe 차이, 최대낙폭 차이
        # return: {"sharpe_improvement": float, "dd_reduction": float}

    def plot_regime_performance_table(output_path):
        # 레짐별 성과표를 HTML/PNG로 저장
        # outputs/regime_performance/ 에 저장
```

**cover_letter_pitch**:
"GMM 레짐 탐지를 포트폴리오 전략에 결합했을 때 Goldilocks 레짐에서
Sharpe X.XX로 단순 전략 대비 XX% 향상됨을 백테스팅으로 확인했습니다.
레짐을 먼저 탐지하면 리스크 조정 수익률이 구조적으로 개선됩니다."

---

## Task 4 — Risk Score Attribution Breakdown

- **target_file**: `lib/risk_manager.py`
- **title**: 리스크 점수 구성 요소 기여도 분해
- **appeal_for**: AI Risk Engineer, Macro Data Scientist
- **priority**: 2

**description**:
현재 risk_manager.py는 종합 리스크 점수를 출력하지만,
그 점수가 어떤 요소(VIX, 레버리지, 신용스프레드, 유동성 등)에서
얼마나 기여했는지 분해하지 않는다.
설명 가능한(Explainable) 리스크 점수 구조를 추가한다.

**implementation_guide**:
```
class RiskScoreAttribution:
    def decompose_risk_score(risk_components: dict) -> dict:
        # 각 리스크 요소의 기여도를 정규화해 비율로 반환
        # 예: {"vix_contrib": 0.38, "leverage_contrib": 0.27,
        #       "spread_contrib": 0.21, "liquidity_contrib": 0.14}

    def format_explanation(attribution: dict) -> str:
        # 사람이 읽을 수 있는 설명 생성
        # "리스크 점수 72의 주요 원인: VIX 기여 38%, 레버리지 27%"

    def flag_dominant_risk(attribution: dict) -> str:
        # 가장 큰 기여 요소 반환 (경보 우선순위 결정용)
```

**cover_letter_pitch**:
"리스크 점수를 VIX·레버리지·신용스프레드·유동성 기여도로 분해했습니다.
블랙박스 점수가 아니라 '왜 이 점수인가'를 설명할 수 있어야
실제 의사결정에 사용될 수 있다고 생각했습니다."
