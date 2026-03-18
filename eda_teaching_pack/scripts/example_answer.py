"""
EDA Teaching Pack — 예시 답안 생성 스크립트 (강사 전용)
=====================================================
raw_dirty.csv를 Q1~Q10 순서대로 분석하고,
모든 시각화를 publish/example_visuals/ 에 저장한다.

Usage:
    cd eda_teaching_pack
    python scripts/example_answer.py
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")
import matplotlib.font_manager as fm

# Korean font setup
_korean_font = None
for candidate in ["NanumGothic", "NanumBarunGothic", "Malgun Gothic"]:
    if any(candidate in f.name for f in fm.fontManager.ttflist):
        _korean_font = candidate
        break
if _korean_font:
    plt.rcParams["font.family"] = _korean_font
    plt.rcParams["axes.unicode_minus"] = False
else:
    print("[WARN] Korean font not found — labels may render as boxes")

sns.set_theme(style="whitegrid", font=_korean_font or "sans-serif")
plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "font.size": 10,
})

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# ─────────────────────────────────────────────
# Configurable analysis parameters
# ─────────────────────────────────────────────

# IQR fence multiplier — Tukey (1977) standard.
# 1.5 = "inner fence" (mild outliers), 3.0 = "outer fence" (extreme).
IQR_MULTIPLIER = 1.5

# Group key for group_median imputation.
# Rationale: 서울 공공자전거 수요는 시간대(Hour)에 가장 강하게 의존 (r≈0.4).
#   대안: ["Hour", "Seasons"] — 계절별 시간 패턴이 다를 경우 더 정교하나
#         그룹당 관측수가 줄어 중앙값 추정이 불안정해질 수 있음.
GROUP_MEDIAN_KEYS = ["Hour"]

# Time-of-day bin boundaries for feature engineering.
# Rationale: 서울 대중교통 운영 시간대 기준 (출근 6-9, 퇴근 18-21),
#   오전/오후는 근무시간 기반 관례적 구분.
#   서울시 교통정보센터 시간대 분류와 유사.
#   대안: [0,5,9,12,18,21,24] 등 — 피크 시점을 더 세분화 가능.
TIMEBIN_EDGES = [0, 6, 10, 14, 18, 22, 24]
TIMEBIN_LABELS = ["새벽(0-5)", "출근(6-9)", "오전(10-13)",
                  "오후(14-17)", "퇴근(18-21)", "야간(22-23)"]

# Histogram bin count.
# Freedman-Diaconis rule for n≈8760 gives ~30-50 bins. 40 chosen for detail.
HIST_BINS = 40

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "publish" / "example_visuals"
OUT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_LINES: list[str] = []


def log(msg: str):
    """Print and collect report lines."""
    print(msg)
    REPORT_LINES.append(msg)


# ─────────────────────────────────────────────
# Helper functions (Q1~Q6 에서 사용)
# ─────────────────────────────────────────────

def profile_data(df: pd.DataFrame) -> pd.DataFrame:
    """Return schema/profile summary table."""
    info = []
    for col in df.columns:
        info.append({
            "Column": col,
            "Dtype": str(df[col].dtype),
            "Non-Null": df[col].notna().sum(),
            "Null": df[col].isna().sum(),
            "Null%": round(df[col].isna().mean() * 100, 2),
            "Unique": df[col].nunique(),
            "Example": df[col].dropna().iloc[0] if df[col].notna().any() else None,
        })
    return pd.DataFrame(info)


def calc_missing_ratio(df: pd.DataFrame) -> pd.Series:
    """Return missing ratio by column (0~1)."""
    return df.isna().mean().sort_values(ascending=False)


def handle_missing(df: pd.DataFrame, method: str,
                   group_cols=None, target_cols=None) -> pd.DataFrame:
    """Apply missing-value strategy and return cleaned frame."""
    out = df.copy()
    if method == "drop":
        out = out.dropna()
    elif method == "group_median":
        if target_cols is None:
            target_cols = out.select_dtypes(include="number").columns.tolist()
        if group_cols is None:
            group_cols = GROUP_MEDIAN_KEYS
        for col in target_cols:
            if out[col].isna().any():
                medians = out.groupby(group_cols)[col].transform("median")
                out[col] = out[col].fillna(medians)
        # remaining non-numeric NaNs: forward fill then drop
        out = out.fillna(method="ffill").dropna()
    return out.reset_index(drop=True)


def detect_outliers_iqr(df: pd.DataFrame, cols) -> pd.DataFrame:
    """Return boolean DataFrame indicating IQR outlier flags."""
    flags = pd.DataFrame(index=df.index)
    for col in cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - IQR_MULTIPLIER * iqr
        upper = q3 + IQR_MULTIPLIER * iqr
        flags[col] = (df[col] < lower) | (df[col] > upper)
    return flags


def treat_outliers(df: pd.DataFrame, cols, strategy: str = "cap") -> pd.DataFrame:
    """Apply outlier treatment. strategy: remove or cap."""
    out = df.copy()
    if strategy == "cap":
        for col in cols:
            q1 = out[col].quantile(0.25)
            q3 = out[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - IQR_MULTIPLIER * iqr
            upper = q3 + IQR_MULTIPLIER * iqr
            out[col] = out[col].clip(lower, upper)
    elif strategy == "remove":
        flags = detect_outliers_iqr(out, cols)
        mask = flags.any(axis=1)
        out = out[~mask].reset_index(drop=True)
    return out


def summary_stats(df: pd.DataFrame, target: str = "Rented Bike Count") -> dict:
    """Return key summary statistics for target."""
    s = df[target]
    return {
        "rows": len(df),
        "missing_cells": int(df.isna().sum().sum()),
        "mean": round(s.mean(), 1),
        "median": round(s.median(), 1),
        "std": round(s.std(), 1),
        "iqr": round(s.quantile(0.75) - s.quantile(0.25), 1),
    }


# ═════════════════════════════════════════════
# MAIN ANALYSIS
# ═════════════════════════════════════════════

def main():
    TARGET = "Rented Bike Count"

    # ── Load ──
    df_raw = pd.read_csv(DATA_DIR / "raw_dirty.csv")
    df = df_raw.copy()
    log(f"[Load] shape = {df.shape}")

    # ── Q1: Baseline Diagnostics ──
    log("\n" + "=" * 60)
    log("Q1: 데이터 스키마 점검")
    log("=" * 60)
    profile = profile_data(df)
    log(profile.to_string(index=False))
    baseline = summary_stats(df, TARGET)
    log(f"\n[Baseline] rows={baseline['rows']}, missing_cells={baseline['missing_cells']}, "
        f"mean={baseline['mean']}, median={baseline['median']}, IQR={baseline['iqr']}")

    # ── Q2: Duplicate & Type Error Check ──
    log("\n" + "=" * 60)
    log("Q2: 중복 및 타입 오류 점검")
    log("=" * 60)

    dup_count = df.duplicated().sum()
    log(f"중복 행 수: {dup_count}")
    df = df.drop_duplicates().reset_index(drop=True)
    log(f"중복 제거 후: {len(df)} 행")

    # Category inconsistency
    log(f"\nSeasons value_counts (수정 전):\n{df['Seasons'].value_counts().to_string()}")
    df["Seasons"] = df["Seasons"].str.strip().str.title()
    log(f"Seasons value_counts (수정 후):\n{df['Seasons'].value_counts().to_string()}")

    # Date parsing
    date_before_na = df["Date"].isna().sum()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    date_after_na = df["Date"].isna().sum()
    log(f"\nDate 파싱: 기존 NaN={date_before_na}, 파싱 후 NaT={date_after_na}")

    # snapshot after Q2 cleanup
    df_after_q2 = df.copy()

    # ── Q3: Missing-Value Diagnostics ──
    log("\n" + "=" * 60)
    log("Q3: 결측치 진단")
    log("=" * 60)
    missing = calc_missing_ratio(df)
    missing_nonzero = missing[missing > 0]
    log(f"\n결측 비율 (>0):\n{(missing_nonzero * 100).round(2).to_string()} %")
    log(f"총 결측 셀 수: {int(df.isna().sum().sum())}")

    # --- Fig 1: Missing ratio bar chart ---
    fig, ax = plt.subplots(figsize=(8, 4))
    missing_nonzero_pct = (missing_nonzero * 100)
    missing_nonzero_pct.plot.barh(ax=ax, color="salmon")
    ax.set_xlabel("Missing %")
    ax.set_title("Q3: 변수별 결측 비율")
    for i, (v, name) in enumerate(zip(missing_nonzero_pct.values, missing_nonzero_pct.index)):
        ax.text(v + 0.1, i, f"{v:.1f}%", va="center", fontsize=9)
    fig.savefig(OUT_DIR / "01_missing_ratio_bar.png")
    plt.close(fig)

    # --- Fig 2: Missing pattern heatmap ---
    cols_with_missing = df.columns[df.isna().any()].tolist()
    if cols_with_missing:
        sample_idx = df[df[cols_with_missing].isna().any(axis=1)].index
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(df.loc[sample_idx[:300], cols_with_missing].isna().astype(int),
                    cbar=False, cmap="YlOrRd", yticklabels=False, ax=ax)
        ax.set_title("Q3: 결측 패턴 히트맵 (상위 300행)")
        fig.savefig(OUT_DIR / "02_missing_heatmap.png")
        plt.close(fig)

    # ── Q4: Missing-Value Strategy Comparison ──
    log("\n" + "=" * 60)
    log("Q4: 결측치 처리 전략 비교")
    log("=" * 60)

    df_drop = handle_missing(df_after_q2, method="drop")
    df_gmed = handle_missing(df_after_q2, method="group_median",
                             group_cols=GROUP_MEDIAN_KEYS)

    stats_before = summary_stats(df_after_q2, TARGET)
    stats_drop = summary_stats(df_drop, TARGET)
    stats_gmed = summary_stats(df_gmed, TARGET)

    compare = pd.DataFrame({
        "처리 전": stats_before,
        "drop": stats_drop,
        "group_median": stats_gmed,
    }).T
    log(f"\n{compare.to_string()}")
    drop_loss = (1 - len(df_drop) / len(df_after_q2)) * 100
    log(f"drop 손실률: {drop_loss:.1f}%")

    # --- Fig 3: Target histogram before/after ---
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
    for ax, (name, frame) in zip(axes, [
        ("처리 전", df_after_q2), ("drop", df_drop), ("group_median", df_gmed)
    ]):
        ax.hist(frame[TARGET].dropna(), bins=HIST_BINS, color="steelblue", alpha=0.7, edgecolor="white")
        ax.set_title(name)
        ax.set_xlabel(TARGET)
        mu = frame[TARGET].mean()
        med = frame[TARGET].median()
        ax.axvline(mu, color="red", ls="--", label=f"mean={mu:.0f}")
        ax.axvline(med, color="orange", ls="--", label=f"median={med:.0f}")
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Frequency")
    fig.suptitle("Q4: 결측치 처리 전/후 타깃 분포", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "03_target_hist_missing.png")
    plt.close(fig)

    # --- Fig 4: Target boxplot before/after ---
    fig, ax = plt.subplots(figsize=(8, 4))
    box_data = [
        df_after_q2[TARGET].dropna().values,
        df_drop[TARGET].values,
        df_gmed[TARGET].values,
    ]
    bp = ax.boxplot(box_data, labels=["처리 전", "drop", "group_median"],
                    patch_artist=True, widths=0.5)
    colors_list = ["#ffcccc", "#aed6f1", "#a9dfbf"]
    for patch, c in zip(bp["boxes"], colors_list):
        patch.set_facecolor(c)
    ax.set_ylabel(TARGET)
    ax.set_title("Q4: 결측치 처리 전/후 타깃 박스플롯")
    fig.savefig(OUT_DIR / "04_target_boxplot_missing.png")
    plt.close(fig)

    # ── Q5: Outlier Detection ──
    log("\n" + "=" * 60)
    log("Q5: 이상치 탐지")
    log("=" * 60)

    # Use group_median frame going forward
    df_work = df_gmed.copy()

    # Domain rule violations
    neg_bike = (df_work[TARGET] < 0).sum()
    neg_rain = (df_work["Rainfall"] < 0).sum()
    neg_snow = (df_work["Snowfall"] < 0).sum()
    log(f"도메인 규칙 위반 — 음수 대여량: {neg_bike}, 음수 강수량: {neg_rain}, 음수 적설량: {neg_snow}")

    # Fix domain violations first
    df_work.loc[df_work[TARGET] < 0, TARGET] = np.nan
    df_work[TARGET] = df_work[TARGET].fillna(df_work.groupby("Hour")[TARGET].transform("median"))
    df_work["Rainfall"] = df_work["Rainfall"].clip(lower=0)
    df_work["Snowfall"] = df_work["Snowfall"].clip(lower=0)

    # IQR outliers (Rainfall/Snowfall excluded — zero-inflated, IQR=0)
    num_cols = ["Temperature", "Humidity", "WindSpeed", "Visibility",
                "DewPoint", "SolarRadiation", TARGET]
    outlier_flags = detect_outliers_iqr(df_work, num_cols)
    outlier_counts = outlier_flags.sum().sort_values(ascending=False)
    log(f"\nIQR 이상치 건수:\n{outlier_counts.to_string()}")
    log(f"이상치 보유 행 수: {outlier_flags.any(axis=1).sum()} ({outlier_flags.any(axis=1).mean()*100:.1f}%)")

    # --- Fig 5: Outlier boxplots ---
    top_outlier_cols = outlier_counts[outlier_counts > 0].index.tolist()[:6]
    if top_outlier_cols:
        fig, axes = plt.subplots(2, 3, figsize=(14, 8))
        for ax, col in zip(axes.flat, top_outlier_cols):
            ax.boxplot(df_work[col].dropna().values, patch_artist=True,
                       boxprops=dict(facecolor="#aed6f1"))
            n_out = outlier_flags[col].sum()
            ax.set_title(f"{col}\n(outliers: {n_out})")
        for ax in axes.flat[len(top_outlier_cols):]:
            ax.set_visible(False)
        fig.suptitle("Q5: IQR 기준 이상치 탐지 — 주요 변수 박스플롯", fontsize=12)
        fig.tight_layout()
        fig.savefig(OUT_DIR / "05_outlier_boxplots.png")
        plt.close(fig)

    # ── Q6: Outlier Treatment Comparison ──
    log("\n" + "=" * 60)
    log("Q6: 이상치 처리 전략 비교")
    log("=" * 60)

    df_out_remove = treat_outliers(df_work, num_cols, strategy="remove")
    df_out_cap = treat_outliers(df_work, num_cols, strategy="cap")

    stats_pre_out = summary_stats(df_work, TARGET)
    stats_remove = summary_stats(df_out_remove, TARGET)
    stats_cap = summary_stats(df_out_cap, TARGET)

    compare_out = pd.DataFrame({
        "이상치 처리 전": stats_pre_out,
        "remove": stats_remove,
        "cap": stats_cap,
    }).T
    log(f"\n{compare_out.to_string()}")
    remove_loss = (1 - len(df_out_remove) / len(df_work)) * 100
    log(f"remove 손실률: {remove_loss:.1f}%")

    # --- Fig 6: Before/after boxplot (outlier treatment) ---
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for ax, (name, frame) in zip(axes, [
        ("처리 전", df_work), ("remove", df_out_remove), ("cap", df_out_cap)
    ]):
        ax.boxplot(frame[TARGET].dropna().values, patch_artist=True,
                   boxprops=dict(facecolor="#f9e79f"))
        ax.set_title(f"{name}\n(n={len(frame)}, mean={frame[TARGET].mean():.0f})")
        ax.set_ylabel(TARGET if ax == axes[0] else "")
    fig.suptitle("Q6: 이상치 처리 전/후 타깃 박스플롯", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "06_outlier_treatment_boxplot.png")
    plt.close(fig)

    # ── Choose final working frame: cap strategy ──
    df_final = df_out_cap.copy()
    log(f"\n[최종 분석 프레임] cap 전략 채택 — {len(df_final)} 행")

    # ── Q7: Feature Engineering ──
    log("\n" + "=" * 60)
    log("Q7: 파생 변수 생성")
    log("=" * 60)

    # Time-of-day bins
    df_final["TimeBin"] = pd.cut(df_final["Hour"], bins=TIMEBIN_EDGES, labels=TIMEBIN_LABELS,
                                  right=False, include_lowest=True)

    # Weekend/weekday
    if pd.api.types.is_datetime64_any_dtype(df_final["Date"]):
        df_final["DayOfWeek"] = df_final["Date"].dt.dayofweek
        df_final["IsWeekend"] = (df_final["DayOfWeek"] >= 5).astype(int)
    else:
        df_final["Date"] = pd.to_datetime(df_final["Date"], errors="coerce")
        df_final["DayOfWeek"] = df_final["Date"].dt.dayofweek
        df_final["IsWeekend"] = (df_final["DayOfWeek"] >= 5).astype(int)

    # Month
    df_final["Month"] = df_final["Date"].dt.month

    log(f"파생 변수: TimeBin, IsWeekend, DayOfWeek, Month")
    log(f"TimeBin 분포:\n{df_final['TimeBin'].value_counts().sort_index().to_string()}")

    # --- Fig 7: Demand by TimeBin ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Bar chart: mean demand by time bin
    time_demand = df_final.groupby("TimeBin", observed=True)[TARGET].mean()
    time_demand.plot.bar(ax=axes[0], color="teal", alpha=0.8, edgecolor="white")
    axes[0].set_title("시간대 구간별 평균 수요")
    axes[0].set_ylabel("평균 대여 수")
    axes[0].tick_params(axis="x", rotation=30)

    # Box: weekend vs weekday
    df_final.boxplot(column=TARGET, by="IsWeekend", ax=axes[1],
                     patch_artist=True,
                     boxprops=dict(facecolor="#aed6f1"))
    axes[1].set_xticklabels(["평일", "주말"])
    axes[1].set_title("평일 vs 주말 수요 분포")
    axes[1].set_ylabel("대여 수")
    fig.suptitle("Q7: 파생 변수 기반 수요 패턴", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "07_feature_engineering.png")
    plt.close(fig)

    # ── Q8: Peak Demand (Before vs After) ──
    log("\n" + "=" * 60)
    log("Q8: 수요 피크 시간 (전/후 비교)")
    log("=" * 60)

    hourly_before = df_after_q2.groupby("Hour")[TARGET].mean()
    hourly_after = df_final.groupby("Hour")[TARGET].mean()

    peak_before = hourly_before.idxmax()
    peak_after = hourly_after.idxmax()
    log(f"처리 전 피크: {peak_before}시 ({hourly_before.max():.1f}대)")
    log(f"처리 후 피크: {peak_after}시 ({hourly_after.max():.1f}대)")
    log(f"최저 시간: {hourly_after.idxmin()}시 ({hourly_after.min():.1f}대)")

    # --- Fig 8: Hourly demand line chart ---
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(hourly_before.index, hourly_before.values,
            "o-", color="gray", alpha=0.6, label=f"처리 전 (peak={peak_before}시)")
    ax.plot(hourly_after.index, hourly_after.values,
            "s-", color="steelblue", label=f"처리 후 (peak={peak_after}시)")
    ax.axvline(peak_after, color="steelblue", ls=":", alpha=0.5)
    ax.set_xlabel("Hour")
    ax.set_ylabel("평균 대여 수")
    ax.set_title("Q8: 시간대별 평균 수요 — 전/후 오버레이")
    ax.set_xticks(range(24))
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(OUT_DIR / "08_hourly_demand_line.png")
    plt.close(fig)

    # ── Q9: Weather vs Demand ──
    log("\n" + "=" * 60)
    log("Q9: 날씨 vs 수요 관계")
    log("=" * 60)

    weather_cols = ["Temperature", "Humidity", "WindSpeed", "Visibility", "DewPoint"]

    # Correlation before/after
    corr_before = df_after_q2[weather_cols + [TARGET]].corr()[TARGET].drop(TARGET)
    corr_after = df_final[weather_cols + [TARGET]].corr()[TARGET].drop(TARGET)
    corr_compare = pd.DataFrame({"처리 전": corr_before.round(3), "처리 후": corr_after.round(3)})
    log(f"\n상관계수 비교:\n{corr_compare.to_string()}")

    # --- Fig 9a: Correlation heatmap (before vs after) ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    all_cols = weather_cols + [TARGET]

    sns.heatmap(df_after_q2[all_cols].corr(), annot=True, fmt=".2f",
                cmap="RdBu_r", vmin=-1, vmax=1, ax=axes[0], square=True)
    axes[0].set_title("처리 전 상관행렬")

    sns.heatmap(df_final[all_cols].corr(), annot=True, fmt=".2f",
                cmap="RdBu_r", vmin=-1, vmax=1, ax=axes[1], square=True)
    axes[1].set_title("처리 후 상관행렬")

    fig.suptitle("Q9: 기상 변수 상관 히트맵 — 전/후 비교", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "09a_correlation_heatmap.png")
    plt.close(fig)

    # --- Fig 9b: Scatter plots ---
    scatter_cols = ["Temperature", "Humidity", "WindSpeed", "DewPoint"]
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for ax, col in zip(axes.flat, scatter_cols):
        ax.scatter(df_after_q2[col], df_after_q2[TARGET],
                   alpha=0.15, s=8, color="gray", label="처리 전")
        ax.scatter(df_final[col], df_final[TARGET],
                   alpha=0.15, s=8, color="steelblue", label="처리 후")
        r = df_final[[col, TARGET]].corr().iloc[0, 1]
        ax.set_xlabel(col)
        ax.set_ylabel(TARGET)
        ax.set_title(f"{col} vs Demand (r={r:.2f})")
        ax.legend(fontsize=8, loc="upper right")
    fig.suptitle("Q9: 기상 변수 vs 수요 산점도", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "09b_weather_scatter.png")
    plt.close(fig)

    # ── Q10: Final Summary ──
    log("\n" + "=" * 60)
    log("Q10: 결론 및 권고안")
    log("=" * 60)

    final_stats = summary_stats(df_final, TARGET)

    log(f"""
[최종 요약 지표]
  행 수:       {baseline['rows']} → {final_stats['rows']}
  결측 셀 수:  {baseline['missing_cells']} → {final_stats['missing_cells']}
  평균:        {baseline['mean']} → {final_stats['mean']}
  중앙값:      {baseline['median']} → {final_stats['median']}
  IQR:         {baseline['iqr']} → {final_stats['iqr']}

[인사이트 1] 출퇴근 시간대 수요 집중
  사실: 오전 8시와 오후 6시에 수요가 집중된다.
  근거: 처리 후 18시 평균 {hourly_after[18]:.0f}대, 8시 {hourly_after[8]:.0f}대 — 전체 평균 대비 약 {hourly_after[18]/hourly_after.mean():.1f}배.
  제안: 해당 시간대에 자전거 재배치를 우선 배정한다.

[인사이트 2] 기온이 수요의 핵심 결정 변수
  사실: 기온과 수요의 상관이 가장 높다 (r={corr_after['Temperature']:.2f}).
  근거: 처리 전/후 모두 동일한 방향이며, 처리 후 관계가 더 안정적이다.
  제안: 기온 기반 수요 예측 모델을 우선 고려한다.

[인사이트 3] 결측치 처리 전략에 따라 표본 손실이 크게 달라짐
  사실: drop 전략은 {drop_loss:.1f}% 표본 손실, group_median은 0% 손실.
  근거: Date 컬럼 결측이 다른 컬럼과 겹쳐 drop 시 연쇄 손실 발생.
  제안: 결측 패턴이 겹칠 때는 group_median 등 대체 전략이 바람직하다.

[운영 제안]
  출퇴근 시간(8시, 18시) 전후로 자전거 재배치를 집중 실시하고,
  기온 예보를 활용한 일일 수요 예측을 운영에 반영한다.

[한계 1] 결측이 MNAR일 가능성을 완전히 배제하지 못함.
[한계 2] 이상치 일부는 실제 이벤트(날씨/행사)일 수 있어 과도한 처리 위험 존재.
""")

    # ── Save summary comparison table as CSV ──
    all_compare = pd.DataFrame({
        "항목": ["총 행 수", "결측 셀 수", "타깃 평균", "타깃 중앙값", "타깃 IQR"],
        "처리 전 (raw_dirty)": [
            baseline["rows"], baseline["missing_cells"],
            baseline["mean"], baseline["median"], baseline["iqr"]
        ],
        "Q2 후 (중복/타입 정리)": [
            stats_before["rows"], stats_before["missing_cells"],
            stats_before["mean"], stats_before["median"], stats_before["iqr"]
        ],
        "결측 drop": [
            stats_drop["rows"], stats_drop["missing_cells"],
            stats_drop["mean"], stats_drop["median"], stats_drop["iqr"]
        ],
        "결측 group_median": [
            stats_gmed["rows"], stats_gmed["missing_cells"],
            stats_gmed["mean"], stats_gmed["median"], stats_gmed["iqr"]
        ],
        "이상치 cap (최종)": [
            final_stats["rows"], final_stats["missing_cells"],
            final_stats["mean"], final_stats["median"], final_stats["iqr"]
        ],
    })
    all_compare.to_csv(OUT_DIR / "summary_comparison.csv", index=False)
    log(f"\n[저장] 요약 비교표 → {OUT_DIR / 'summary_comparison.csv'}")

    # ── Save report ──
    report_path = OUT_DIR / "example_answer_report.txt"
    report_path.write_text("\n".join(REPORT_LINES), encoding="utf-8")
    log(f"[저장] 텍스트 리포트 → {report_path}")

    # ── File list ──
    log("\n[생성된 파일 목록]")
    for f in sorted(OUT_DIR.glob("*")):
        log(f"  {f.name}")


if __name__ == "__main__":
    main()
