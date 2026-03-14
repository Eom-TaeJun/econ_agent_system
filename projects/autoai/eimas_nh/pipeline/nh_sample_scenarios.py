#!/usr/bin/env python3
"""
Reusable NH Trading sample scenarios.

These builders package local research artifacts into a compact NH Trading
memo so portfolio examples can be generated without running the full stack.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from pipeline.nh_memo_view import build_nh_trading_memo
from pipeline.schemas import EIMASResult


FORECAST_PHD_SCENARIO_ID = "forecast-phd-to-nh-rates"


def build_forecast_phd_to_nh_result() -> EIMASResult:
    """Bridge forecast/phd findings into a sample NH Trading result."""
    result = EIMASResult(
        timestamp="2026-03-14T09:00:00",
        schema_version="nh-sample-0.1.0",
        fred_summary={
            "net_liquidity": 5850.0,
            "treasury_2y": 4.18,
            "treasury_10y": 4.05,
            "spread_10y2y": -0.13,
            "liquidity_regime": "Tighter than neutral",
            "curve_status": "Inverted but easing",
        },
        market_indicators={
            "vix_current": 19.2,
            "move_index": 112.0,
        },
        regime={
            "regime": "Transition",
            "trend": "Policy repricing watch",
            "volatility": "Elevated",
        },
        risk_score=47.0,
        risk_level="MEDIUM",
        confidence=0.67,
        final_recommendation="HOLD",
        warnings=[
            "FedWatch density intervals stayed too narrow near FOMC meetings; widen scenario bands before desk reuse.",
            "When VIX rises, overconfidence can deepen and curve repricing can accelerate.",
            "Foreign futures flow and BOJ/BOK policy tone can reopen front-end volatility quickly.",
        ],
        events_detected=[
            {
                "type": "Density calibration",
                "description": "Immediate-horizon 80% coverage fell to 13.3%, indicating severe overconfidence in policy-path pricing.",
            },
            {
                "type": "Information flow",
                "description": "MOVE led rate-expectation variance at 2-3 day lags, pointing to bond-market leadership.",
            },
            {
                "type": "Macro catalyst",
                "description": "NFP caused the largest repricing impulse with abs_ratio 3.87 across the research sample.",
            },
        ],
        operational_report={
            "summary": (
                "Policy-path certainty still looks too tight for an NH rates/FICC desk to trust "
                "without wider scenario bands and explicit liquidity handoff."
            ),
        },
        information_flow={
            "lead_signal": "MOVE -> FedWatch variance at 2-3 day lags",
            "macro_event_priority": "NFP repricing > CPI within the research window",
            "desk_translation": "Treat Treasury-vol shocks as an early warning for KR curve repricing risk.",
        },
        institutional_analysis={
            "nh_targeting": "Rates/FICC desk memo for KR curve interpretation and handoff",
            "nh_public_signal_alignment": [
                "outlook_and_response_strategy",
                "bond_price_discovery",
                "policy_to_curve_translation",
                "customer_readable_bond_language",
            ],
            "candidate_story": (
                "Translate research on market overconfidence into a bounded desk memo "
                "instead of a generic forecasting or AI demo."
            ),
        },
        fomc_analysis={
            "paper_title": "Distributional Overconfidence in FOMC Rate Expectations",
            "core_finding": "Point forecasts were accurate, but density forecasts were structurally too tight.",
            "coverage_80_immediate": 0.133,
            "vix_beta": -0.0171,
            "lasso_cv_r2": 0.012,
            "bond_market_lead": "MOVE Granger-led expectation variance",
            "news_catalyst": "NFP abs_ratio 3.87",
        },
        hft_microstructure={
            "skipped": True,
            "reason": "This sample focuses on rates/FICC interpretation, not routing or live execution.",
        },
        approval_status={
            "status": "pending",
            "owner": "human-desk-review",
        },
        audit_metadata={
            "data_as_of": "2026-03-14T09:00:00",
            "scenario_id": FORECAST_PHD_SCENARIO_ID,
            "source_mode": "forecast_phd_bridge",
            "source_bundle": [
                "/home/tj/projects/forecast/phd/paper_v2.md",
                "/home/tj/projects/자기소개서/NH투자증권_Trading_현업조사_2026Q1.md",
            ],
            "target_memo": "NHTradingDeskMemoV0",
        },
        fact_check_grade="A-",
        whitening_summary=(
            "Sample memo uses statistics extracted from paper_v2 and maps them to recent NH "
            "Trading/FICC public signals. No live execution or market data refresh is attached."
        ),
    )
    return result


def build_forecast_phd_to_nh_package() -> Tuple[EIMASResult, Dict[str, Any]]:
    """Return both the sample result and the tailored NH memo payload."""
    result = build_forecast_phd_to_nh_result()
    memo = build_nh_trading_memo(result)

    memo["desk_view"]["question"] = (
        "How should the NH rates/FICC desk respond when market-implied policy certainty "
        "stays too tight despite elevated volatility and bond-market stress signals?"
    )
    memo["desk_view"]["thesis"] = (
        "The research suggests the market often gets the direction right but understates the "
        "distribution width, so NH should widen KR curve scenario bands before trusting front-end pricing."
    )
    memo["desk_view"]["base_case"] = (
        "If policy repricing remains orderly, the desk can use wider scenario bands and bond-volatility "
        "signals to interpret KR duration and curve moves without overcommitting to a single path."
    )
    memo["desk_view"]["risk_case"] = (
        "If VIX, MOVE, or foreign futures flows re-accelerate, front-end certainty can break quickly and "
        "force a sharper KR curve repricing than point forecasts imply."
    )
    memo["desk_view"]["scenario_watchlist"] = [
        "Check whether front-end pricing is narrower than the realized event distribution again.",
        "Treat MOVE spikes as an early warning for KR curve stress rather than a lagging confirmation.",
        "Watch NFP-class macro releases and foreign futures positioning for fast repricing.",
        "Escalate to human review before turning the memo into product or sales language.",
    ]

    memo["execution_risk"]["handoff_required"] = True
    memo["execution_risk"]["handoff_reason"] = (
        "The sample memo is intentionally bounded: it informs rates/FICC interpretation, "
        "but live execution, curve positioning, and customer translation still need human desk review."
    )

    memo["evidence"]["source_gap_notes"] = [
        "This sample bridges local forecast/phd research into an NH-style memo; it is not a live NH desk report.",
        "Recent NH public signals are referenced from the local Trading field-research memo rather than direct live feeds.",
    ]
    memo["evidence"]["recent_public_signals"] = [
        "2025-11 NH RESEARCH FORUM emphasized outlook and response strategy across bonds and FICC.",
        "2025-12 NH remained a bond and CP final quote yield reporter into 2026 H1.",
        "2026-01 to 2026-02 NH public rates commentary focused on policy path, curve, liquidity, and sentiment.",
        "2026-01 NH translated bond-market judgment into customer language via a government-bond special sale.",
    ]

    memo["role_profile_briefs"]["securities-trading"]["memo_hook"] = memo["desk_view"]["thesis"]
    result.nh_trading_memo = memo
    return result, memo


def render_forecast_phd_to_nh_markdown(result: EIMASResult, memo: Dict[str, Any]) -> str:
    """Render a portfolio-friendly process and result note."""
    market_context = memo["market_context"]
    desk_view = memo["desk_view"]
    execution_risk = memo["execution_risk"]
    evidence = memo["evidence"]

    lines = [
        "# NH Trading Sample: Forecast PhD -> Rates/FICC Memo",
        "",
        "## Target",
        "- Scenario: US policy-path overconfidence -> KR curve / NH rates-FICC interpretation",
        "- Audience: NH Investment & Securities Trading (rates/FICC lens)",
        "- Goal: Show that forecast research can be translated into a bounded desk memo",
        "",
        "## Process",
        "1. Extract the core findings from `forecast/phd/paper_v2.md`.",
        "2. Reframe those findings around NH's recent public Trading/FICC signals.",
        "3. Package the result into `NHTradingDeskMemoV0` with thesis, scenarios, and handoff.",
        "",
        "## Research Inputs",
        "- Immediate-horizon 80% coverage: 13.3%",
        "- VIX beta on coverage: -0.0171",
        "- Bond-market lead: MOVE -> expectation variance",
        "- Main macro catalyst: NFP abs_ratio 3.87",
        "- Practical implication: widen scenario bands before desk reuse",
        "",
        "## Result Memo",
        f"- Question: {desk_view['question']}",
        f"- Thesis: {desk_view['thesis']}",
        f"- Base case: {desk_view['base_case']}",
        f"- Risk case: {desk_view['risk_case']}",
        "",
        "## Market Context",
        f"- Regime: {market_context['regime']} / {market_context['trend']}",
        f"- Volatility: {market_context['volatility']}",
        f"- Treasury 2y / 10y: {market_context['treasury_2y']} / {market_context['treasury_10y']}",
        f"- 10y-2y spread: {market_context['spread_10y2y']}",
        f"- Liquidity regime: {market_context['liquidity_regime']}",
        f"- Rates focus: {market_context['rates_focus']}",
        "",
        "## Watchlist",
    ]

    for item in desk_view["scenario_watchlist"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Handoff",
            f"- Required: {execution_risk['handoff_required']}",
            f"- Reason: {execution_risk['handoff_reason']}",
            "",
            "## Evidence Notes",
        ]
    )

    for item in evidence["source_gap_notes"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Candidate Translation",
            "- This is not a generic AI demo.",
            "- It shows a candidate who reads rates uncertainty as a distribution problem,",
            "  checks overconfidence, and hands the result to a desk in memo form.",
            "",
            "## Local Sources",
            f"- {result.audit_metadata['source_bundle'][0]}",
            f"- {result.audit_metadata['source_bundle'][1]}",
        ]
    )

    return "\n".join(lines) + "\n"
