"""
Pipeline execution profiles for phase-level runtime policy.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PipelineProfile:
    """Phase-level execution policy for a single pipeline run."""

    name: str
    description: str

    # Phase 2 policies
    run_sentiment_bubble: bool = True
    skip_bubble_analysis: bool = False
    run_institutional_frameworks: bool = True
    run_adaptive_portfolio: bool = True
    run_market_structure_analytics: bool = True
    run_thematic_analytics: bool = True
    run_portfolio_construction: bool = True
    run_correlation_matrix: bool = True

    # Debate / validation
    run_debate: bool = True
    run_phase8_ai_validation: bool = True
    run_phase85_quick_validation: bool = True

    # Optional portfolio modules
    run_backtest: bool = True
    run_attribution: bool = True
    run_stress_test: bool = True

    # Operational controls
    run_operational_rebalance_refresh: bool = True
    expose_trade_plan: bool = True
    apply_operational_decision_override: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_LEGACY_PROFILE = PipelineProfile(
    name="legacy",
    description="Full legacy flow (all phases available by CLI flags).",
)


_US_TRADER_V1_PROFILE = PipelineProfile(
    name="us-trader-v1",
    description=(
        "US institutional trader baseline: keep execution/explainability path, "
        "defer heavy research-only phases."
    ),
    run_sentiment_bubble=True,
    skip_bubble_analysis=True,
    run_institutional_frameworks=False,
    run_adaptive_portfolio=True,
    run_market_structure_analytics=True,
    run_thematic_analytics=True,
    run_portfolio_construction=True,
    run_correlation_matrix=True,
    run_debate=True,
    run_phase8_ai_validation=False,
    run_phase85_quick_validation=False,
    run_backtest=False,
    run_attribution=False,
    run_stress_test=False,
    run_operational_rebalance_refresh=True,
    expose_trade_plan=True,
    apply_operational_decision_override=True,
)

_MONETARY_POLICY_V1_PROFILE = PipelineProfile(
    name="monetary-policy-v1",
    description=(
        "Monetary policy intelligence baseline: prioritize macro/policy interpretation, "
        "institutional context, reporting, and governance over trading modules."
    ),
    run_sentiment_bubble=False,
    skip_bubble_analysis=True,
    run_institutional_frameworks=True,
    run_adaptive_portfolio=False,
    run_market_structure_analytics=False,
    run_thematic_analytics=False,
    run_portfolio_construction=False,
    run_correlation_matrix=False,
    run_debate=True,
    run_phase8_ai_validation=False,
    run_phase85_quick_validation=False,
    run_backtest=False,
    run_attribution=False,
    run_stress_test=False,
    run_operational_rebalance_refresh=False,
    expose_trade_plan=False,
    apply_operational_decision_override=False,
)

_NH_TRADING_V1_PROFILE = PipelineProfile(
    name="nh-trading-v1",
    description=(
        "NH Trading baseline: prioritize cross-asset interpretation, market structure, "
        "and risk-aware desk memo packaging over portfolio and execution modules."
    ),
    run_sentiment_bubble=False,
    skip_bubble_analysis=True,
    run_institutional_frameworks=True,
    run_adaptive_portfolio=False,
    run_market_structure_analytics=True,
    run_thematic_analytics=False,
    run_portfolio_construction=False,
    run_correlation_matrix=False,
    run_debate=True,
    run_phase8_ai_validation=False,
    run_phase85_quick_validation=False,
    run_backtest=False,
    run_attribution=False,
    run_stress_test=False,
    run_operational_rebalance_refresh=False,
    expose_trade_plan=False,
    apply_operational_decision_override=False,
)


_PROFILE_ALIASES = {
    "legacy": "legacy",
    "default": "legacy",
    "us-trader-v1": "us-trader-v1",
    "us_trader_v1": "us-trader-v1",
    "trader": "us-trader-v1",
    "monetary-policy-v1": "monetary-policy-v1",
    "monetary_policy_v1": "monetary-policy-v1",
    "mpi": "monetary-policy-v1",
    "nh-trading-v1": "nh-trading-v1",
    "nh_trading_v1": "nh-trading-v1",
    "nh-trading": "nh-trading-v1",
    "nh": "nh-trading-v1",
}


_PROFILES = {
    "legacy": _LEGACY_PROFILE,
    "us-trader-v1": _US_TRADER_V1_PROFILE,
    "monetary-policy-v1": _MONETARY_POLICY_V1_PROFILE,
    "nh-trading-v1": _NH_TRADING_V1_PROFILE,
}


def pipeline_profile_choices() -> tuple[str, ...]:
    """Canonical profile names for argparse choices."""
    return tuple(_PROFILES.keys())


def resolve_pipeline_profile(name: str | None) -> PipelineProfile:
    """Resolve canonical pipeline profile from name/alias."""
    raw = (name or "legacy").strip().lower()
    canonical = _PROFILE_ALIASES.get(raw)
    if canonical is None:
        supported = ", ".join(pipeline_profile_choices())
        raise ValueError(f"Unsupported profile '{name}'. Supported: {supported}")
    return _PROFILES[canonical]
