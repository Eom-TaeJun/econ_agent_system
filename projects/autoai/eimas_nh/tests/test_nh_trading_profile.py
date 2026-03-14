from pipeline.app.profiles import resolve_pipeline_profile
from pipeline.phases.phase2_enhanced import analyze_enhanced
from pipeline.schemas import EIMASResult


def test_nh_trading_profile_keeps_market_structure_but_disables_trade_path(monkeypatch):
    profile = resolve_pipeline_profile("nh-trading-v1")

    assert profile.run_institutional_frameworks is True
    assert profile.run_market_structure_analytics is True
    assert profile.run_adaptive_portfolio is False
    assert profile.run_portfolio_construction is False
    assert profile.expose_trade_plan is False
    assert profile.apply_operational_decision_override is False

    result = EIMASResult(timestamp="2026-03-14T09:00:00", audit_metadata={})

    monkeypatch.setattr(
        "pipeline.phases.phase2_enhanced.analyze_volatility_garch",
        lambda market_data: {"status": "ok"},
    )
    monkeypatch.setattr(
        "pipeline.phases.phase2_enhanced.analyze_information_flow",
        lambda market_data: {"status": "ok"},
    )

    analyze_enhanced(result, market_data={}, quick_mode=False, pipeline_profile=profile)

    assert result.hft_microstructure.get("skipped") is not True
    assert result.allocation_result.get("skipped") is True
    assert result.rebalance_decision.get("skipped") is True
