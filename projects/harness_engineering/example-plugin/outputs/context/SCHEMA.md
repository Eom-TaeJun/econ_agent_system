# 에이전트 핸드오프 컨텍스트 스키마

에이전트 간 데이터는 이 디렉토리의 JSON 파일로 전달된다.
각 에이전트는 시작 전에 이전 에이전트의 파일을 읽고,
완료 후 자신의 파일을 여기 저장한다.

---

## validation_result.json (data-validator → 이후 모든 에이전트)

```json
{
  "validated_at": "2026-02-20T10:30:00",
  "status": "pass | warn | fail",
  "datasets": [
    {
      "name": "DGS10",
      "rows": 756,
      "missing_pct": 0.5,
      "outliers": 2,
      "is_stationary": false,
      "notes": "비정상 → 차분 사용 권고"
    }
  ],
  "can_proceed": true,
  "warnings": ["DGS10 비정상 시계열"],
  "blockers": []
}
```

## regime_snapshot.json (macro-analyst → signal-interpreter, quant-coder, report-writer)

```json
{
  "analyzed_at": "2026-02-20T10:45:00",
  "regime": "Goldilocks | Overheating | Stagflation | Recession",
  "confidence": "high | medium | low",
  "growth_direction": "up | flat | down",
  "inflation_direction": "up | flat | down",
  "fed_path": "hold | cut | hike",
  "key_risks": ["관세 불확실성", "Fed 의장 교체"],
  "asset_bias": {
    "equity": "overweight | neutral | underweight",
    "bond": "overweight | neutral | underweight",
    "gold": "overweight | neutral | underweight",
    "cash": "overweight | neutral | underweight"
  }
}
```

## signal_summary.json (signal-interpreter → quant-coder, report-writer)

```json
{
  "interpreted_at": "2026-02-20T11:00:00",
  "risk_mode": "risk-on | risk-off | neutral",
  "signal_strength": 3,
  "signals": [
    {
      "name": "VIX",
      "value": 14.2,
      "zscore": -1.1,
      "interpretation": "컴플레이선시 구간 (12퍼센타일)",
      "direction": "bearish_signal"
    },
    {
      "name": "HY_OAS",
      "value": 298,
      "zscore": -1.8,
      "interpretation": "5퍼센타일 - 리스크 프리미엄 최소",
      "direction": "bearish_signal"
    }
  ],
  "anomalies": [],
  "consistency": "consistent | mixed | contradictory"
}
```

## chart_paths.json (quant-coder → report-writer)

```json
{
  "generated_at": "2026-02-20T11:15:00",
  "charts": [
    {
      "name": "yield_curve",
      "path": "outputs/charts/yield_curve_20260220.png",
      "description": "미국 수익률 곡선"
    }
  ],
  "key_metrics": {}
}
```
