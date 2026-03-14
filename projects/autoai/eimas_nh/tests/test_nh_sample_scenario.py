from pipeline.nh_sample_scenarios import (
    FORECAST_PHD_SCENARIO_ID,
    build_forecast_phd_to_nh_package,
    render_forecast_phd_to_nh_markdown,
)


def test_build_forecast_phd_package_contains_nh_translation():
    result, memo = build_forecast_phd_to_nh_package()

    assert result.audit_metadata["scenario_id"] == FORECAST_PHD_SCENARIO_ID
    assert memo["desk_view"]["thesis"].startswith("The research suggests the market often gets the direction right")
    assert memo["execution_risk"]["handoff_required"] is True
    assert "13.3%" in render_forecast_phd_to_nh_markdown(result, memo)
    assert memo["desk_view"]["institutional_analysis"]["nh_public_signal_alignment"][0] == "outlook_and_response_strategy"
