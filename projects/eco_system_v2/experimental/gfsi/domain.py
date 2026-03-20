"""
experimental/gfsi/domain.py — GFSI Value Objects + Thresholds

규칙: stdlib만 허용 (domain 순수성 유지).

GFSI (Global Fear & Stress Index)
  5개 채널을 0-100 스케일로 통합한 글로벌 리스크 지표.
  0 = 극단 공포/스트레스, 100 = 극단 탐욕/안정

v0.3 채널 구성 (v0.1 6채널 → 5채널 개편):
  1. crypto_vol   — BTC 실현변동성 비율 + ETH/BTC (24/7, 가격 기반)
  2. stable_flow  — 스테이블코인 시총 + DeFi TVL (24/7, 온체인)
  3. geo_stress   — GPR 텍스트 시그널 + 유가·금 프록시 (텍스트+가격 결합)
  4. news_stress  — EPU 경제정책 불확실성 (텍스트 기반)
  5. liquidity    — Fed RRP + TGA (구조적 배경)

삭제:
  - currency (DXY/JPY): VIX와 동시 반응, 24/7 아님, crypto_vol이 커버
  - sentiment (F&G): 예측력 52%, crypto_vol과 이중반영

근거 수준 표기:
  [학술] — 학술 논문 또는 공식 연구 기반
  [관행] — 업계 컨벤션 또는 실증 분포 기반
  [설계] — 자체 설계 (백테스트 미검증, 추후 최적화 대상)
  [검증] — 학술/실증 데이터로 범위 확인 완료
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class GFSILevel(str, Enum):
    """GFSI 레벨 해석."""
    CRISIS = "CRISIS"           # 0-20: 극단 공포, 유동성 이탈
    STRESS = "STRESS"           # 20-40: 스트레스
    NEUTRAL = "NEUTRAL"         # 40-60: 중립
    EXPANSION = "EXPANSION"     # 60-80: 자본 유입, 낮은 변동성
    EUPHORIA = "EUPHORIA"       # 80-100: 과열 경고


class Channel(str, Enum):
    """GFSI 구성 채널 (v0.3: 5채널)."""
    CRYPTO_VOL = "crypto_vol"
    STABLE_FLOW = "stable_flow"
    GEO_STRESS = "geo_stress"
    NEWS_STRESS = "news_stress"
    LIQUIDITY = "liquidity"


# ============================================================================
# Thresholds
# ============================================================================

@dataclass(frozen=True)
class ChannelWeight:
    """채널 가중치 + 근거."""
    channel: Channel
    weight: float
    rationale: str


# 채널 가중치 — 합계 1.0
CHANNEL_WEIGHTS: tuple[ChannelWeight, ...] = (
    ChannelWeight(
        Channel.CRYPTO_VOL, 0.25,
        "[설계] 24/7 핵심. BTC vol은 주말/장외 리스크 선반영. 유일한 완전 24/7 가격 채널"
    ),
    ChannelWeight(
        Channel.STABLE_FLOW, 0.20,
        "[설계] 24/7 온체인. 법정화폐→크립토 유입 프록시. VIX에 전혀 안 잡히는 독립 정보"
    ),
    ChannelWeight(
        Channel.GEO_STRESS, 0.25,
        "[검증] GPR 텍스트(Caldara & Iacoviello 2022) + 유가·금 가격 프록시 결합. "
        "텍스트가 가격보다 선행 → 뉴스 발생 시점 포착"
    ),
    ChannelWeight(
        Channel.NEWS_STRESS, 0.15,
        "[학술] EPU(Baker, Bloom & Davis). 경제정책 불확실성은 지정학과 별개 차원. "
        "무역전쟁, 금리정책, 규제 변화 등 비군사적 리스크 포착"
    ),
    ChannelWeight(
        Channel.LIQUIDITY, 0.15,
        "[학술] Fed RRP/TGA는 시스템 유동성 프록시. Pozsar(2022) 'plumbing' 프레임워크"
    ),
)


# GFSI 레벨 경계
GFSI_CRISIS = 20.0    # [설계] 하위 20% — 복수 채널 동시 스트레스
GFSI_STRESS = 40.0    # [설계] 하위 40% — 주의 필요
GFSI_EXPANSION = 60.0  # [설계] 상위 40% — 리스크 온
GFSI_EUPHORIA = 80.0   # [설계] 상위 20% — 과열 경고, 역추세 고려

# BTC 변동성 임계값
BTC_VOL_RATIO_HIGH = 1.5   # [설계] 20d/60d vol ratio — 단기 변동성 급등
BTC_VOL_RATIO_LOW = 0.7    # [설계] 단기 변동성 수축 — 안정기

# 스테이블코인 흐름
STABLE_MCAP_CHANGE_HIGH = 2.0   # [설계] 7일 시총 +2% — 의미있는 유입
STABLE_MCAP_CHANGE_LOW = -2.0   # [설계] 7일 시총 -2% — 의미있는 유출

# 지정학 프록시
OIL_GOLD_CORR_HIGH = 0.6   # [검증] 20일 상관 — 장기평균 0.42, 위기시 0.78. Reboredo(2013)

# GPR (Geopolitical Risk Index) — Caldara & Iacoviello (2022)
GPR_LOW = 50.0     # [학술] 역사적 안정기 하한. 평균 ~100
GPR_HIGH = 300.0   # [학술] 주요 위기 수준. 러-우 침공시 ~400, 9/11 ~500
                    # 300 이상은 clamp → 일상적 변동에서 해상도 유지

# EPU (Economic Policy Uncertainty) — Baker, Bloom & Davis
EPU_LOW = 50.0     # [학술] 안정기 하한. 역사적 평균 ~100-130
EPU_HIGH = 400.0   # [학술] 위기 수준. COVID시 ~600, 정부셧다운시 ~300+
                    # FRED 시리즈: USEPUINDXD (일일)

# Fed 유동성 임계값
TGA_CENTER_B = 650.0         # [검증] 재무부 자체 목표 ~$600B + 2024-2026 평균 고려
TGA_DEVIATION_LOW_B = 200.0  # [검증] 중심 대비 $200B 이하 = 부채한도 위기 수준
TGA_DEVIATION_HIGH_B = 350.0 # [검증] 중심 대비 $350B 초과 = 유동성 흡수 부담
RRP_NEAR_ZERO_B = 50.0       # [검증] RRP $50B 미만이면 퍼센트 변화율 무의미
RRP_ABS_CHANGE_B = 50.0      # [검증] 주간 절대 변동 기준 ($B)

# 선행성 테스트
LEAD_LAG_MAX_DAYS = 10      # [설계] 최대 10일 선행/후행 탐색
GRANGER_P_VALUE = 0.05      # [학술] 5% 유의수준


# ============================================================================
# Value Objects
# ============================================================================

@dataclass(frozen=True)
class ChannelScore:
    """단일 채널의 점수 + 메타데이터."""
    channel: Channel
    score: float            # 0-100
    raw_values: dict        # 원시 데이터 (디버깅/검증용)
    signal: str = ""        # 해석 텍스트
    data_quality: float = 1.0   # 0-1: 데이터 품질 (일부 소스 실패 시 감소)

    def to_dict(self) -> dict:
        return {
            "channel": self.channel.value,
            "score": round(self.score, 2),
            "signal": self.signal,
            "data_quality": self.data_quality,
            "raw_values": self.raw_values,
        }


@dataclass(frozen=True)
class GFSIResult:
    """GFSI 산출 결과 — 불변 Value Object."""
    score: float                    # 0-100 종합 점수
    level: GFSILevel
    channels: tuple[ChannelScore, ...]
    vix_current: float = 0.0       # 비교용 VIX
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "0.3.0"

    def to_dict(self) -> dict:
        return {
            "gfsi_score": round(self.score, 2),
            "gfsi_level": self.level.value,
            "vix_current": self.vix_current,
            "channels": [ch.to_dict() for ch in self.channels],
            "collected_at": self.collected_at,
            "version": self.version,
        }

    def to_summary(self) -> str:
        """한 줄 요약."""
        return (
            f"GFSI: {self.score:.1f} ({self.level.value}) | "
            f"VIX: {self.vix_current:.1f} | "
            f"{self.collected_at[:10]}"
        )


@dataclass(frozen=True)
class LeadLagResult:
    """채널 vs VIX 선행/후행 분석 결과."""
    channel: Channel
    optimal_lag_days: int       # 양수=채널이 VIX 선행, 음수=후행
    correlation: float          # 최적 lag에서의 상관계수
    granger_p_value: float      # Granger 인과 p-value
    is_significant: bool        # p < 0.05
    r_squared: float = 0.0     # VIX 설명력 (이중반영 체크)
    residual_info: float = 0.0  # 잔차 정보량 (VIX가 못 잡는 부분)

    def to_dict(self) -> dict:
        return {
            "channel": self.channel.value,
            "optimal_lag_days": self.optimal_lag_days,
            "correlation": round(self.correlation, 4),
            "granger_p_value": round(self.granger_p_value, 4),
            "is_significant": self.is_significant,
            "r_squared": round(self.r_squared, 4),
            "residual_info": round(self.residual_info, 4),
        }


@dataclass(frozen=True)
class DailyEvaluation:
    """일일 GFSI 평가 기록."""
    date: str                       # YYYY-MM-DD
    gfsi: GFSIResult
    vix_change_1d: float = 0.0      # VIX 전일 대비 변화
    gfsi_change_1d: float = 0.0     # GFSI 전일 대비 변화
    btc_return_1d: float = 0.0      # BTC 1일 수익률 (%)
    spx_return_1d: float = 0.0      # SPX 1일 수익률 (%)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "gfsi": self.gfsi.to_dict(),
            "vix_change_1d": round(self.vix_change_1d, 4),
            "gfsi_change_1d": round(self.gfsi_change_1d, 4),
            "btc_return_1d": round(self.btc_return_1d, 4),
            "spx_return_1d": round(self.spx_return_1d, 4),
            "notes": self.notes,
        }


# ============================================================================
# 유틸리티 함수
# ============================================================================

def classify_level(score: float) -> GFSILevel:
    """GFSI 점수를 레벨로 분류."""
    if score < GFSI_CRISIS:
        return GFSILevel.CRISIS
    if score < GFSI_STRESS:
        return GFSILevel.STRESS
    if score < GFSI_EXPANSION:
        return GFSILevel.NEUTRAL
    if score < GFSI_EUPHORIA:
        return GFSILevel.EXPANSION
    return GFSILevel.EUPHORIA


def get_weight(channel: Channel) -> float:
    """채널 가중치 조회."""
    for cw in CHANNEL_WEIGHTS:
        if cw.channel == channel:
            return cw.weight
    return 0.0
