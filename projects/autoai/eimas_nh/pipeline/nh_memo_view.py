#!/usr/bin/env python3
"""
NH Trading memo view helpers.

This module builds a thin, desk-facing memo on top of the full EIMASResult
artifact so the project can be explained as a risk-aware Trading copilot
rather than a generic investment engine.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pipeline.memo_view import (
    _compact_text,
    _derive_run_mode,
    _extract_summary_message,
    _get_value,
    _to_float,
)
from pipeline.role_profiles import build_default_role_profile_briefs, resolve_role_profile


def _scenario_watchlist(result: Any) -> List[str]:
    watchlist: List[str] = []
    warnings = list(getattr(result, "warnings", []) or [])
    events = list(getattr(result, "events_detected", []) or [])

    for warning in warnings[:2]:
        if isinstance(warning, str) and warning.strip():
            watchlist.append(warning.strip())

    for event in events[:2]:
        if isinstance(event, dict):
            event_type = str(event.get("type", "")).strip()
            description = _compact_text(event.get("description", ""), max_chars=120)
            if event_type and description:
                watchlist.append(f"{event_type}: {description}")
            elif event_type:
                watchlist.append(event_type)

    approval_status = getattr(result, "approval_status", None)
    if not isinstance(approval_status, dict) or not approval_status:
        watchlist.append("Approval state is not recorded; human desk review is still required.")

    return watchlist[:4]


def build_nh_trading_memo(result: Any) -> Dict[str, Any]:
    """Build the NH Trading desk memo view."""
    fred_summary = getattr(result, "fred_summary", {}) or {}
    market_indicators = getattr(result, "market_indicators", {}) or {}
    regime = getattr(result, "regime", {}) or {}
    audit_metadata = getattr(result, "audit_metadata", {}) or {}
    approval_status = getattr(result, "approval_status", {}) or {}
    failsafe_status = getattr(result, "failsafe_status", {}) or {}

    metadata = {
        "view_name": "NHTradingDeskMemoV0",
        "view_version": "0.1.0",
        "generated_at": getattr(result, "timestamp", ""),
        "as_of": audit_metadata.get("data_as_of", getattr(result, "timestamp", "")),
        "schema_version": getattr(result, "schema_version", ""),
        "run_mode": _derive_run_mode(result),
        "source_artifact": "EIMASResult",
        "target_company": "NH Investment & Securities",
        "target_role": "Trading",
    }

    market_context = {
        "regime": _get_value(regime, "regime", "Unknown"),
        "trend": _get_value(regime, "trend", "Unknown"),
        "volatility": _get_value(regime, "volatility", "Unknown"),
        "risk_score": _to_float(getattr(result, "risk_score", None)),
        "risk_level": getattr(result, "risk_level", "UNKNOWN"),
        "confidence": _to_float(getattr(result, "confidence", None)),
        "vix_current": _to_float(_get_value(market_indicators, "vix_current")),
        "net_liquidity": _to_float(_get_value(fred_summary, "net_liquidity")),
        "treasury_2y": _to_float(_get_value(fred_summary, "treasury_2y")),
        "treasury_10y": _to_float(_get_value(fred_summary, "treasury_10y")),
        "spread_10y2y": _to_float(_get_value(fred_summary, "spread_10y2y")),
        "liquidity_regime": _get_value(fred_summary, "liquidity_regime", "Unknown"),
        "curve_status": _get_value(fred_summary, "curve_status", "Unknown"),
        "rates_focus": "US policy path -> KR curve / FICC interpretation",
    }

    desk_view = {
        "question": "What should the NH rates/FICC desk watch now across front-end rates, curve repricing, and liquidity risk?",
        "final_recommendation": getattr(result, "final_recommendation", "HOLD"),
        "summary_message": _extract_summary_message(result),
        "thesis": _extract_summary_message(result),
        "base_case": "US rates and liquidity context remain readable, and the memo can support a bounded FICC interpretation.",
        "risk_case": "Curve repricing, liquidity deterioration, or event surprise can invalidate the read quickly.",
        "desk_focus": "Rates / bonds / FICC first, data analysis as support rather than identity.",
        "recent_signal_alignment": [
            "strategy_over_raw_prediction",
            "bond_price_discovery",
            "policy_to_curve_translation",
            "customer_readable_risk_translation",
        ],
        "events_detected": list(getattr(result, "events_detected", []) or []),
        "information_flow": getattr(result, "information_flow", {}) or {},
        "institutional_analysis": getattr(result, "institutional_analysis", {}) or {},
        "fomc_analysis": getattr(result, "fomc_analysis", {}) or {},
        "scenario_watchlist": _scenario_watchlist(result),
        "cross_asset_ready": bool(getattr(result, "information_flow", None))
        or bool(getattr(result, "fomc_analysis", None)),
    }

    execution_risk = {
        "market_structure_ready": bool(getattr(result, "hft_microstructure", None))
        and not bool(_get_value(getattr(result, "hft_microstructure", {}), "skipped", False)),
        "warnings": list(getattr(result, "warnings", []) or [])[:10],
        "approval_status": approval_status,
        "failsafe_status": failsafe_status,
        "handoff_required": bool(failsafe_status) or not bool(approval_status),
        "handoff_reason": (
            "Human desk review is required because approval or failsafe state is incomplete."
            if bool(failsafe_status) or not bool(approval_status)
            else "Approval state is present; desk can review the memo as a bounded internal input."
        ),
        "product_risk_focus": [
            "liquidity",
            "margin",
            "forced_liquidation",
        ],
        "rates_risk_focus": [
            "duration_shock",
            "curve_repricing",
            "front_end_rate_surprise",
            "basis_or_liquidity_gap",
        ],
    }

    evidence = {
        "fact_check_grade": getattr(result, "fact_check_grade", "N/A"),
        "whitening_summary": getattr(result, "whitening_summary", ""),
        "audit_metadata": audit_metadata,
        "source_gap_notes": [
            "NH-specific FICC and bond desk memo fixtures are not attached yet.",
        ],
        "recent_public_signals": [
            "2025-11 NH RESEARCH FORUM: outlook and response strategy across bonds and FICC.",
            "2025-12 NH remained a bond and CP final quote yield reporter for 2026 H1.",
            "2026-01 to 2026-02 public NH commentary emphasized policy path, curve, liquidity, and market sentiment.",
            "2026-01 government bond special sale translated bond view into customer-facing product language.",
        ],
    }

    memo = {
        "metadata": metadata,
        "market_context": market_context,
        "desk_view": desk_view,
        "execution_risk": execution_risk,
        "evidence": evidence,
    }

    role_profile_briefs = build_default_role_profile_briefs(memo)
    trading_profile = resolve_role_profile("securities-trading")
    role_profile_briefs[trading_profile.name] = {
        **role_profile_briefs.get(trading_profile.name, {}),
        "name": trading_profile.name,
        "audience": trading_profile.audience,
        "candidate_positioning": trading_profile.candidate_positioning,
        "project_translation": trading_profile.project_translation,
        "primary_value": trading_profile.primary_value,
        "resume_focus": list(trading_profile.resume_focus),
        "interview_focus": list(trading_profile.interview_focus),
        "emphasis_sections": list(trading_profile.emphasis_sections),
        "anti_pitch": list(trading_profile.anti_pitch),
        "memo_hook": desk_view["summary_message"] or trading_profile.project_translation,
        "control_story": {
            "handoff_required": execution_risk["handoff_required"],
            "approval_state": str(approval_status.get("status", "unknown"))
            if isinstance(approval_status, dict)
            else "unknown",
        },
    }
    memo["role_profile_briefs"] = role_profile_briefs
    return memo


def populate_nh_trading_memo(result: Any) -> Dict[str, Any]:
    """Attach the NH Trading memo view to the mutable result object and return it."""
    memo = build_nh_trading_memo(result)
    setattr(result, "nh_trading_memo", memo)
    return memo
