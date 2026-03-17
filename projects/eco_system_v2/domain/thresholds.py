"""
domain/thresholds.py — 정량 분석 임계값 + 해석 참조

모든 하드코딩 상수를 한 곳에 모아 근거를 문서화한다.
규칙: stdlib만 허용 (domain 순수성 유지).

각 임계값은 (값, 해석) 형태로 관리하며, 코드에서 값을,
출력에서 해석을 참조한다.

근거 수준 표기:
  [학술] — 학술 논문 또는 공식 연구에 기반
  [관행] — 업계 컨벤션 또는 실증 데이터 분포에 기반
  [설계] — 자체 설계 (백테스트 미검증, 추후 최적화 대상)

변경 시 근거를 함께 업데이트할 것.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Threshold:
    """단일 임계값 + 해석."""
    value: float
    label: str       # 출력용 한글 라벨
    rationale: str   # 왜 이 값인지 근거


# ============================================================================
# VIX 임계값
# ============================================================================
# CBOE VIX 장기 평균 ~19.5 (1990-2024).
# 16 미만: 역사적 하위 25% — 공포 부재, 위험자산 우호.
# 22 이상: 장기 평균+1σ — 불확실성 확대, 헤지 수요 증가.
# 30 이상: 상위 5% — 극단 공포 (COVID, 금융위기 수준).

VIX_LOW = Threshold(16.0, "VIX 안정", "[관행] CBOE VIX 장기 분포 하위 25%ile — Whaley(2000) 'Investor Fear Gauge'")
VIX_MID = Threshold(22.0, "VIX 경계", "[관행] 장기 평균(~19.5)+1σ — CBOE 1990-2024 실증 분포")
VIX_HIGH = Threshold(30.0, "VIX 극단", "[관행] 장기 분포 상위 5% — 2008·2020 위기 수준, CBOE 실증")


# ============================================================================
# 스코어 가중치 (QuantAgent _quantitative_signal)
# ============================================================================
# 총 score 범위 약 -2 ~ +2. 각 지표의 가중치는 아래 원칙:
#   - 핵심 지표(VIX, 레짐): ±0.3~0.5 (가장 큰 영향)
#   - 보조 지표(DXY, RSI): ±0.05~0.1 (미세 조정)
#   - 신규 지표(oil, copper, HYG): ±0.05~0.15 (확증/반증 역할)
# 최종 신호 판단 임계값 ±0.2는 neutral 구간을 확보하여 약한 신호를 걸러냄.

@dataclass(frozen=True)
class ScoreWeight:
    """스코어 가중치 + 해석."""
    weight: float
    rationale: str


# --- VIX 스코어 ---
SCORE_VIX_LOW = ScoreWeight(0.3, "[설계] VIX<16: 핵심 지표로 높은 가중치. 백테스트 미검증")
SCORE_VIX_HIGH = ScoreWeight(-0.3, "[설계] VIX 22~30: 핵심 지표 가중. 백테스트 미검증")
SCORE_VIX_EXTREME = ScoreWeight(-0.5, "[설계] VIX≥30: 전체 지표 중 최대 단일 가중. 백테스트 미검증")

# --- SPX 30일 수익률 ---
# ±3%는 월간 수익률 1σ 수준 (SPX 월간 σ ≈ 4.5%)
SPX_RETURN_THRESHOLD = Threshold(3.0, "SPX 30일 수익률", "[관행] 월간 수익률 약 1σ 수준 — SPX 월간 σ≈4.5% (1926-2024)")
SCORE_SPX_POSITIVE = ScoreWeight(0.2, "[설계] SPX 모멘텀 확인. 백테스트 미검증")
SCORE_SPX_NEGATIVE = ScoreWeight(-0.2, "[설계] SPX 하락 모멘텀 확인. 백테스트 미검증")

# --- 수익률 곡선 ---
# -0.5%: 본격 역전 (1970년 이후 6회 경기침체 중 5회에서 -0.5% 이상 역전 선행)
# 0%~-0.5%: 근접 역전 (경기 둔화 초기 신호)
# +1.0%: 정상 범위 (건강한 경기 확장기 수준)
SPREAD_INVERSION = Threshold(-0.5, "수익률 곡선 역전", "[학술] Estrella & Hardouvelis(1991) — 1970년 이후 침체 5/6 선행")
SPREAD_NEAR_INVERSION = Threshold(0.0, "수익률 곡선 근접 역전", "[학술] NY Fed 연구 — 0% 근접 시 경기 둔화 초기 경고")
SPREAD_NORMAL = Threshold(1.0, "수익률 곡선 정상", "[관행] 건강한 확장기 평균 스프레드 수준 (1990-2024)")
SCORE_SPREAD_INVERTED = ScoreWeight(-0.25, "[설계] 역전의 높은 역사적 신뢰도 반영. 백테스트 미검증")
SCORE_SPREAD_NEAR = ScoreWeight(-0.1, "[설계] 초기 경고 수준의 약한 가중. 백테스트 미검증")
SCORE_SPREAD_NORMAL = ScoreWeight(0.1, "[설계] 정상 환경의 약한 긍정 가중. 백테스트 미검증")

# --- DXY 달러 인덱스 ---
# 장기 평균 ~96 (2000-2024). 105+ = 강달러로 신흥국·원자재·수출 부담
DXY_STRONG = Threshold(105.0, "달러 강세", "[관행] ICE Dollar Index 2000-2024 평균(~96)+1σ")
DXY_WEAK = Threshold(95.0, "달러 약세", "[관행] ICE Dollar Index 장기 평균 이하")
SCORE_DXY_STRONG = ScoreWeight(-0.1, "[설계] 보조지표로 약한 가중. 백테스트 미검증")
SCORE_DXY_WEAK = ScoreWeight(0.1, "[설계] 보조지표로 약한 가중. 백테스트 미검증")

# --- RSI ---
# Wilder(1978) 원래 정의: 70 이상 과매수, 30 이하 과매도
RSI_OVERBOUGHT = Threshold(70.0, "RSI 과매수", "[학술] Wilder(1978) 'New Concepts in Technical Trading Systems' 원래 정의")
RSI_OVERSOLD = Threshold(30.0, "RSI 과매도", "[학술] Wilder(1978) 원래 정의")
SCORE_RSI = ScoreWeight(0.05, "[설계] 역추세 보조지표로 최소 가중. 백테스트 미검증")

# --- 원유 (WTI) ---
# $90+: 2022년 에너지 위기 수준, 소비자 물가·기업 원가 부담 가중
# $55 미만: 에너지 비용 절감 → 소비·기업 실적 우호 (단, 과잉공급 우려도 있음)
OIL_HIGH = Threshold(90.0, "고유가", "[관행] 2022 에너지위기 기준 — EIA 'oil price shock' 연구에서 $80-90+ 구간이 성장 저해")
OIL_LOW = Threshold(55.0, "저유가", "[관행] 2019-20 저점 부근 — Hamilton(2009) 유가-GDP 비선형 관계")
SCORE_OIL_HIGH = ScoreWeight(-0.1, "[설계] 보조지표 가중. Hamilton(2009) 비선형 효과 참고. 백테스트 미검증")
SCORE_OIL_LOW = ScoreWeight(0.05, "[설계] 과잉공급 가능성으로 비대칭 약한 가중. 백테스트 미검증")

# --- 구리 (Dr. Copper) ---
# 구리는 경기 선행지표 ('Dr. Copper' 별칭).
# $4.5+: 2021~2022 고점 수준 — 글로벌 제조업·건설 활황
# $3.5 미만: 경기 둔화기 수준 (2019-2020 저점 부근)
COPPER_HIGH = Threshold(4.5, "구리 강세", "[관행] COMEX 2021-22 고점 — 'Dr. Copper' 경기 선행지표 통설")
COPPER_LOW = Threshold(3.5, "구리 약세", "[관행] COMEX 2019-20 저점 부근 — 경기 둔화기 가격대")
SCORE_COPPER_HIGH = ScoreWeight(0.1, "[설계] Dr. Copper 통설 기반 보조 가중. 백테스트 미검증")
SCORE_COPPER_LOW = ScoreWeight(-0.1, "[설계] Dr. Copper 통설 기반 보조 가중. 백테스트 미검증")

# --- HYG (하이일드 채권 ETF) ---
# HYG는 신용 위험(credit spread)의 프록시.
# $72 미만: 신용 스프레드 확대 → 부도 위험 인식 상승 (2022 저점 ~$70)
# $80 이상: 정상 범위 — 신용 시장 안정 (2023-24 평균 $76-$80)
HYG_STRESS = Threshold(72.0, "신용 스트레스", "[관행] iShares HYG 2022 저점(~$70) 부근 — 신용 스프레드 프록시")
HYG_STABLE = Threshold(80.0, "신용 안정", "[관행] iShares HYG 2023-24 정상 범위 상단")
SCORE_HYG_STRESS = ScoreWeight(-0.15, "[설계] 신용 스트레스는 시스템 위험으로 보조 중 높은 가중. 백테스트 미검증")
SCORE_HYG_STABLE = ScoreWeight(0.05, "[설계] 안정은 약한 긍정 (기본 상태에 가까움). 백테스트 미검증")

# --- LASSO ---
LASSO_MIN_R2 = Threshold(0.05, "LASSO 최소 R²", "[관행] R²<0.05는 통계적으로 무작위 수준 — 사회과학 최소 효과 크기 기준")
LASSO_MAX_WEIGHT = Threshold(0.3, "LASSO 최대 가중치", "[설계] 단일 모델 지배 방지 cap. 백테스트 미검증")

# --- 신호 판단 ---
# ±0.2: 여러 지표가 일관되게 한 방향을 가리킬 때만 방향 신호를 내기 위한 neutral 구간.
# 단일 지표의 최대 기여(0.5)의 40% 수준 — 최소 2개 이상 지표 동조 필요.
SIGNAL_THRESHOLD = Threshold(0.2, "신호 판단 임계", "[설계] 단일 지표 최대 기여(0.5)의 40% — 최소 2개 동조 필요. 백테스트 미검증")

# --- 신뢰도 ---
# base 0.4: 최소 신뢰도 (score=0이라도 데이터 기반이므로 기본 40%)
# --- 신뢰도 공식 ---
# 기존: min(1.0, 0.4 + abs(score)) → score 0.6이면 100% (너무 쉽게 도달)
# 개선: sigmoid 스타일 감쇠 + 상한 0.92
#   이유: [설계] 가중치가 백테스트 미검증이므로 모델 불확실성 최소 8% 보존.
#   0.92 = "매우 높은 확신이지만 모델 한계를 인정"
#   참고: Tetlock(2015) 'Superforecasting' — 최고 예측가도 극단적 확률을 피함
CONFIDENCE_BASE = Threshold(0.35, "기본 신뢰도", "[설계] 데이터 기반 최소 보장. 0.4→0.35 하향 (과신 방지)")
CONFIDENCE_CAP = Threshold(0.92, "신뢰도 상한", "[설계] 백테스트 미검증 모델 불확실성 8% 보존. Tetlock(2015) 극단확률 회피 원칙")
CONFIDENCE_SCALE = Threshold(0.7, "신뢰도 스케일", "[설계] score→신뢰도 변환 감쇠율. 1.0이면 선형, 0.7이면 고점 접근 시 감쇠")

# --- 스코어 클램프 ---
# 단일 방향으로 모든 지표가 일치해도 이론적 최대는 ~2.0.
# 클램프 ±1.5: 개별 지표의 동시 극단 활성화(tail event)에서도 과잉 확신 방지
SCORE_CLAMP = Threshold(1.5, "스코어 클램프", "[설계] 극단 누적 방지. 백테스트 미검증")


# ============================================================================
# 리스크 서비스 임계값
# ============================================================================

RISK_YIELD_SPREAD_INVERSION = Threshold(
    -0.5, "경기침체 경고 수준 역전",
    "[학술] Estrella & Hardouvelis(1991) — VIX HIGH + 역전 시 EXTREME 격상"
)


# ============================================================================
# 포트폴리오 서비스 임계값
# ============================================================================

PORTFOLIO_SIGNAL_MAX_TILT = Threshold(10.0, "신호 최대 조정", "[설계] 합의 100%일 때 ±10%p. Bridgewater risk parity 참고하되 자체 설정. 백테스트 미검증")
PORTFOLIO_RISK_HIGH_SHIFT = Threshold(5.0, "HIGH 리스크 조정", "[설계] 방어적 현금 확대. 백테스트 미검증")
PORTFOLIO_RISK_EXTREME_SHIFT = Threshold(10.0, "EXTREME 리스크 조정", "[설계] 자산 보존 모드. 백테스트 미검증")
PORTFOLIO_RISK_LOW_SHIFT = Threshold(3.0, "LOW 리스크 조정", "[설계] 보수적 소폭 확대. 백테스트 미검증")
PORTFOLIO_LASSO_MIN_R2 = Threshold(0.1, "LASSO 배분 반영 최소 R²", "[관행] R²<0.1은 모델 설명력 10% 미만 — 배분 결정에 불충분")
PORTFOLIO_LASSO_MAX_TILT = Threshold(5.0, "LASSO 최대 배분 조정", "[설계] 단일 모델 과잉반응 방지. 백테스트 미검증")

# --- LASSO 신호 임계값 ---
LASSO_BULLISH_RETURN = Threshold(1.0, "LASSO 강세 임계", "[관행] 20일 +1% ≈ 연환산 +12% — SPX 장기 평균 수익률(~10%) 초과 수준")
LASSO_BEARISH_RETURN = Threshold(-1.0, "LASSO 약세 임계", "[관행] 20일 -1% ≈ 연환산 -12% — 의미있는 하락 수준")
