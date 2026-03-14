from pipeline.nh_memo_view import build_nh_trading_memo, populate_nh_trading_memo
from pipeline.schemas import EIMASResult


def test_build_nh_trading_memo_maps_core_sections():
    result = EIMASResult(
        timestamp="2026-03-14T09:00:00",
        fred_summary={
            "net_liquidity": 5750.0,
            "treasury_2y": 4.15,
            "treasury_10y": 4.03,
            "spread_10y2y": -0.12,
            "liquidity_regime": "Abundant",
            "curve_status": "Inverted",
        },
        market_indicators={"vix_current": 18.1},
        regime={"regime": "Transition", "trend": "Neutral", "volatility": "Elevated"},
        risk_score=44.2,
        risk_level="MEDIUM",
        confidence=0.61,
        final_recommendation="HOLD",
        warnings=["Watch cross-asset reaction after policy surprise"],
        events_detected=[{"type": "FOMC", "description": "Repricing in front-end rates"}],
        approval_status={"status": "pending"},
        audit_metadata={"data_as_of": "2026-03-14T08:55:00"},
    )

    memo = build_nh_trading_memo(result)

    assert memo["metadata"]["view_name"] == "NHTradingDeskMemoV0"
    assert memo["metadata"]["target_company"] == "NH Investment & Securities"
    assert memo["market_context"]["treasury_2y"] == 4.15
    assert memo["market_context"]["rates_focus"] == "US policy path -> KR curve / FICC interpretation"
    assert memo["desk_view"]["question"].startswith("What should the NH rates/FICC desk watch")
    assert memo["desk_view"]["desk_focus"].startswith("Rates / bonds / FICC first")
    assert "bond_price_discovery" in memo["desk_view"]["recent_signal_alignment"]
    assert memo["desk_view"]["events_detected"][0]["type"] == "FOMC"
    assert memo["execution_risk"]["handoff_required"] is False
    assert "Approval state is present" in memo["execution_risk"]["handoff_reason"]
    assert "curve_repricing" in memo["execution_risk"]["rates_risk_focus"]
    assert memo["evidence"]["source_gap_notes"]
    assert memo["evidence"]["recent_public_signals"]
    assert memo["role_profile_briefs"]["securities-trading"]["name"] == "securities-trading"


def test_populate_nh_trading_memo_attaches_result_field():
    result = EIMASResult(timestamp="2026-03-14T09:00:00")

    memo = populate_nh_trading_memo(result)

    assert result.nh_trading_memo == memo
    assert memo["metadata"]["generated_at"] == "2026-03-14T09:00:00"
