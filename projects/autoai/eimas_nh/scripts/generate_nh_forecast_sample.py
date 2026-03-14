#!/usr/bin/env python3
"""Generate a lightweight NH Trading sample from forecast/phd findings."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.nh_sample_scenarios import (  # noqa: E402
    FORECAST_PHD_SCENARIO_ID,
    build_forecast_phd_to_nh_package,
    render_forecast_phd_to_nh_markdown,
)


def main() -> int:
    output_dir = REPO_ROOT / "examples" / "nh-trading" / FORECAST_PHD_SCENARIO_ID
    output_dir.mkdir(parents=True, exist_ok=True)

    result, memo = build_forecast_phd_to_nh_package()

    result_path = output_dir / "eimas_result.json"
    memo_path = output_dir / "nh_trading_memo.json"
    note_path = output_dir / "process_and_result.md"

    result_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    memo_path.write_text(json.dumps(memo, indent=2, ensure_ascii=False), encoding="utf-8")
    note_path.write_text(render_forecast_phd_to_nh_markdown(result, memo), encoding="utf-8")

    print("Generated NH Trading sample artifacts:")
    print(f"- {result_path}")
    print(f"- {memo_path}")
    print(f"- {note_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
