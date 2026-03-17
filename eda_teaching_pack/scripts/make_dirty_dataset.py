#!/usr/bin/env python3
"""
Generate a teaching dataset with controlled quality issues.

Usage example:
  python scripts/make_dirty_dataset.py \
    --input data/raw_clean.csv \
    --output data/raw_dirty.csv \
    --missing-rate 0.03 \
    --outlier-rate 0.01 \
    --duplicate-rate 0.005 \
    --datetime-cols Date
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create dirty dataset for EDA training.")
    parser.add_argument("--input", required=True, help="Path to clean input CSV.")
    parser.add_argument("--output", required=True, help="Path to output dirty CSV.")
    parser.add_argument("--missing-rate", type=float, default=0.03, help="Per-column missing injection rate.")
    parser.add_argument("--outlier-rate", type=float, default=0.01, help="Per-column outlier injection rate.")
    parser.add_argument("--duplicate-rate", type=float, default=0.005, help="Row duplicate append rate.")
    parser.add_argument(
        "--datetime-cols",
        default="",
        help="Comma-separated datetime columns to corrupt slightly (example: Date,Timestamp).",
    )
    parser.add_argument("--datetime-corrupt-rate", type=float, default=0.002, help="Per datetime-column corruption rate.")
    parser.add_argument(
        "--category-cols",
        default="",
        help="Comma-separated categorical columns to corrupt by case-changing.",
    )
    parser.add_argument("--category-corrupt-rate", type=float, default=0.01, help="Per category-column corruption rate.")
    parser.add_argument(
        "--non-negative-cols",
        default="Rainfall,Snowfall",
        help="Comma-separated columns that must remain >= 0 after outlier injection.",
    )
    parser.add_argument(
        "--exclude-cols",
        default="",
        help="Comma-separated columns to exclude from all modifications.",
    )
    parser.add_argument("--max-missing-cols", type=int, default=6, help="Max columns to inject missing values into.")
    parser.add_argument("--max-outlier-cols", type=int, default=5, help="Max numeric columns to inject outliers into.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    return parser.parse_args()


def split_csv_arg(raw: str) -> list[str]:
    if not raw.strip():
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def sample_columns(cols: Iterable[str], max_n: int, rng: np.random.Generator) -> list[str]:
    col_list = list(cols)
    if not col_list:
        return []
    n = min(max_n, len(col_list))
    pick = rng.choice(col_list, size=n, replace=False)
    return [str(x) for x in pick]


def infer_outlier_candidates(df: pd.DataFrame, exclude_cols: set[str]) -> list[str]:
    candidates: list[str] = []
    for col in df.select_dtypes(include=[np.number]).columns:
        if col in exclude_cols:
            continue

        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty:
            continue

        name = col.lower()
        if any(k in name for k in ("hour", "month", "day", "weekday", "weekend", "season", "holiday", "year")):
            continue

        n_unique = int(series.nunique())
        if n_unique <= 5:
            continue

        if series.min() >= 0 and series.max() <= 1 and n_unique <= 3:
            continue

        candidates.append(col)
    return candidates


def inject_missing(df: pd.DataFrame, cols: list[str], rate: float, rng: np.random.Generator) -> dict[str, int]:
    counts: dict[str, int] = {}
    if rate <= 0:
        return counts
    n_rows = len(df)
    n = max(1, int(n_rows * rate))
    for col in cols:
        idx = rng.choice(df.index.to_numpy(), size=min(n, n_rows), replace=False)
        df.loc[idx, col] = np.nan
        counts[col] = len(idx)
    return counts


def inject_outliers(df: pd.DataFrame, cols: list[str], rate: float, rng: np.random.Generator) -> dict[str, int]:
    counts: dict[str, int] = {}
    if rate <= 0:
        return counts

    n_rows = len(df)
    n = max(1, int(n_rows * rate))

    for col in cols:
        series = pd.to_numeric(df[col], errors="coerce")
        non_na = series.dropna()
        if non_na.empty:
            continue

        q1 = non_na.quantile(0.25)
        q3 = non_na.quantile(0.75)
        iqr = q3 - q1
        scale = iqr if iqr > 0 else float(non_na.std(ddof=0))
        if not np.isfinite(scale) or scale == 0:
            scale = max(1.0, float(non_na.abs().mean()))

        upper = q3 + 1.5 * iqr
        lower = q1 - 1.5 * iqr

        valid_idx = non_na.index.to_numpy()
        size = min(n, len(valid_idx))
        idx = rng.choice(valid_idx, size=size, replace=False)
        half = size // 2

        high_noise = rng.uniform(1.0, 3.0, size=half) * scale
        low_noise = rng.uniform(1.0, 3.0, size=size - half) * scale

        high_vals = upper + high_noise
        low_vals = lower - low_noise
        injected = np.concatenate([high_vals, low_vals])
        rng.shuffle(injected)

        df.loc[idx, col] = injected
        counts[col] = size

    return counts


def inject_category_corruption(
    df: pd.DataFrame, cols: list[str], rate: float, rng: np.random.Generator
) -> dict[str, int]:
    """Corrupt categorical columns by changing case of some values."""
    counts: dict[str, int] = {}
    if rate <= 0:
        return counts

    n_rows = len(df)
    n = max(1, int(n_rows * rate))
    for col in cols:
        if col not in df.columns:
            continue
        non_na = df[col].dropna()
        if non_na.empty:
            continue
        idx = rng.choice(non_na.index.to_numpy(), size=min(n, len(non_na)), replace=False)
        df.loc[idx, col] = df.loc[idx, col].astype(str).str.lower()
        counts[col] = len(idx)
    return counts


def clip_non_negative(df: pd.DataFrame, cols: list[str]) -> None:
    """Ensure injected outliers don't create physically impossible negative values
    for columns that must be non-negative (e.g. Rainfall, Snowfall)."""
    for col in cols:
        if col in df.columns:
            series = pd.to_numeric(df[col], errors="coerce")
            neg_mask = series < 0
            if neg_mask.any():
                df.loc[neg_mask, col] = 0.0


def inject_datetime_corruption(
    df: pd.DataFrame, cols: list[str], rate: float, rng: np.random.Generator
) -> dict[str, int]:
    counts: dict[str, int] = {}
    if rate <= 0:
        return counts

    n_rows = len(df)
    n = max(1, int(n_rows * rate))
    for col in cols:
        if col not in df.columns:
            continue
        idx = rng.choice(df.index.to_numpy(), size=min(n, n_rows), replace=False)
        df.loc[idx, col] = "INVALID_DATE"
        counts[col] = len(idx)
    return counts


def append_duplicates(df: pd.DataFrame, rate: float, rng: np.random.Generator) -> tuple[pd.DataFrame, int]:
    if rate <= 0 or df.empty:
        return df, 0
    n_rows = len(df)
    n = max(1, int(n_rows * rate))
    idx = rng.choice(df.index.to_numpy(), size=min(n, n_rows), replace=True)
    dup_df = df.loc[idx].copy()
    out = pd.concat([df, dup_df], ignore_index=True)
    return out, len(dup_df)


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    original_rows = len(df)
    original_missing = int(df.isna().sum().sum())

    exclude_cols = set(split_csv_arg(args.exclude_cols))
    datetime_cols = [c for c in split_csv_arg(args.datetime_cols) if c in df.columns and c not in exclude_cols]

    candidate_missing_cols = [c for c in df.columns if c not in exclude_cols]
    missing_cols = sample_columns(candidate_missing_cols, args.max_missing_cols, rng)

    numeric_cols = infer_outlier_candidates(df, exclude_cols)
    outlier_cols = sample_columns(numeric_cols, args.max_outlier_cols, rng)

    category_cols = [c for c in split_csv_arg(args.category_cols) if c in df.columns and c not in exclude_cols]
    if not category_cols:
        # Auto-detect categorical columns if not specified
        cat_candidates = [c for c in df.select_dtypes(include=["object"]).columns
                         if c not in exclude_cols and c not in datetime_cols]
        category_cols = cat_candidates

    non_negative_cols = split_csv_arg(args.non_negative_cols)

    missing_counts = inject_missing(df, missing_cols, args.missing_rate, rng)
    outlier_counts = inject_outliers(df, outlier_cols, args.outlier_rate, rng)
    clip_non_negative(df, non_negative_cols)
    category_counts = inject_category_corruption(df, category_cols, args.category_corrupt_rate, rng)
    datetime_counts = inject_datetime_corruption(df, datetime_cols, args.datetime_corrupt_rate, rng)
    df, dup_count = append_duplicates(df, args.duplicate_rate, rng)

    df.to_csv(output_path, index=False)

    final_rows = len(df)
    final_missing = int(df.isna().sum().sum())

    print("Dirty dataset generated")
    print(f"- input:  {input_path}")
    print(f"- output: {output_path}")
    print(f"- seed: {args.seed}")
    print(f"- rows: {original_rows} -> {final_rows} (duplicates added: {dup_count})")
    print(f"- missing cells: {original_missing} -> {final_missing}")
    print(f"- missing injected: {missing_counts}")
    print(f"- outliers injected: {outlier_counts}")
    if category_counts:
        print(f"- category corruption: {category_counts}")
    if datetime_cols:
        print(f"- datetime corruption: {datetime_counts}")
    if non_negative_cols:
        print(f"- non-negative clipped: {non_negative_cols}")


if __name__ == "__main__":
    main()
