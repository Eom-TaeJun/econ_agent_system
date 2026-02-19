---
name: fedwatch-data-pipeline
description: |
  CME FedWatch 확률분포 데이터를 기대금리 패널로 변환하는 파이프라인.
  meeting_YYYYMMDD_merged.csv → complete_cme_panel_history.csv 변환,
  기대금리(exp_rate_bp) 계산, 시장 데이터 결합 작업 시 활성화된다.
version: 1.0.0
updated: 2026-02-20
source: projects/forecast/data_pipeline_design.md
---

# FedWatch 데이터 파이프라인 표준

## 입출력 구조

```
입력: meeting_YYYYMMDD_merged.csv (회의별)
  컬럼: Date | (0-25) | (25-50) | ... | (1575-1600)
  의미: 각 날짜의 금리 확률분포

출력: complete_cme_panel_history.csv (패널)
  컬럼: meeting_date | asof_date | exp_rate_bp | rate_uncertainty | days_to_meeting
```

## Step 1: 확률분포 → 기대금리 변환

**권장: 가중평균 + 표준편차 동시 계산**

```python
def calculate_rate_statistics(prob_row):
    """확률분포에서 기대금리(bp)와 불확실성 계산"""
    rates, probs = [], []

    for col, prob in prob_row.items():
        if pd.isna(prob) or prob == 0:
            continue
        if col.startswith('(') and ')' in col:
            low, high = map(int, col.strip('()').split('-'))
            rates.append((low + high) / 2)
            probs.append(prob)

    if not rates:
        return np.nan, np.nan

    probs = np.array(probs) / np.sum(probs)  # 정규화
    rates = np.array(rates)

    exp_rate  = np.sum(rates * probs)
    std_dev   = np.sqrt(np.sum(((rates - exp_rate) ** 2) * probs))
    return exp_rate, std_dev

# 적용
df[['exp_rate_bp', 'rate_uncertainty']] = df[prob_cols].apply(
    calculate_rate_statistics, axis=1, result_type='expand'
)
```

**기댓값 vs 중위수 vs 최빈값:**
| 방법 | 장점 | 단점 |
|------|------|------|
| **가중평균** (권장) | 분포 전체 활용, 이론적 합리성 | tail에 민감 |
| 중위수 | 극단값에 강건 | tail 정보 무시 |
| 최빈값 | 컨센서스 반영 | bimodal 처리 불가 |

## Step 2: 패널 구조 변환

```python
def convert_to_panel(meeting_files_dir, output_file):
    all_panels = []
    for filepath in sorted(glob.glob(f"{meeting_files_dir}/meeting_*_merged.csv")):
        meeting_date_str = Path(filepath).stem.split('_')[1]
        meeting_date = pd.to_datetime(meeting_date_str, format='%Y%m%d')

        df = pd.read_csv(filepath)
        df['Date'] = pd.to_datetime(df['Date'])
        prob_cols = [c for c in df.columns if c != 'Date']

        stats = df[prob_cols].apply(calculate_rate_statistics, axis=1, result_type='expand')
        stats.columns = ['exp_rate_bp', 'rate_uncertainty']

        panel = pd.DataFrame({
            'meeting_date':     meeting_date,
            'asof_date':        df['Date'],
            'exp_rate_bp':      stats['exp_rate_bp'],
            'rate_uncertainty': stats['rate_uncertainty'],
        })
        panel['days_to_meeting'] = (panel['meeting_date'] - panel['asof_date']).dt.days
        all_panels.append(panel[panel['days_to_meeting'] >= 0])

    return pd.concat(all_panels).sort_values(['meeting_date', 'asof_date'])
```

## Step 3: 실제 FOMC 금리 추가

```python
# 수동 입력 (빠르고 정확 — 권장)
ACTUAL_FOMC_RATES = {
    '2025-05-07': 462.5,
    '2025-06-18': 462.5,  # 동결
    '2025-07-30': 437.5,  # -25bp
    '2025-09-17': 437.5,
    '2025-10-29': 437.5,
    # FRED로 자동화: DFEDTARU + DFEDTARL 중간값
}
panel['actual_rate_bp'] = panel['meeting_date'].map(
    lambda d: ACTUAL_FOMC_RATES.get(d.strftime('%Y-%m-%d'), np.nan)
)
panel['forecast_error'] = panel['exp_rate_bp'] - panel['actual_rate_bp']
```

## Step 4: 시장 데이터 결합 — 결측치 처리

```python
# 유효 데이터 90% 이상 변수만 선택
def filter_by_coverage(df, threshold=0.9):
    valid = df.notna().mean()
    return valid[valid >= threshold].index.tolist()

valid_vars = filter_by_coverage(market_data.drop('Date', axis=1))
market_clean = market_data[['Date'] + valid_vars]

# 금리 변수만 forward fill (최대 5일)
rate_vars = ['Baa_Yield', 'SOFR']  # 이벤트 더미는 절대 ffill 금지
market_clean[rate_vars] = market_clean[rate_vars].ffill(limit=5)

# 패널과 left join
final = panel.merge(market_clean, left_on='asof_date', right_on='Date', how='left')
```

## 최종 파이프라인 순서

```
1. convert_to_panel()         → 회의별 파일 → 패널
2. ACTUAL_FOMC_RATES 추가     → 실제 금리 + 예측 오차
3. filter_by_coverage()       → 시장 데이터 정제 (90% 기준)
4. left join                  → 패널 + 시장 데이터 결합
5. d_Exp_Rate = groupby().diff() → 일별 변화량
6. Horizon 분리               → 초단기/단기/장기
```

---
상세 코드: `references/full-pipeline.md`
