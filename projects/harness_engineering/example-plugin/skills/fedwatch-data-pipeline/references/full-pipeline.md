# Fed Watch 분석 데이터 파이프라인 설계

## 📊 현재 상황 정리

### 1. 보유 데이터
✅ **회의별 병합 파일** (`meeting_YYYYMMDD_merged.csv`)
- 구조: `Date, (0-25), (25-50), ..., (1575-1600)`
- 각 행: 특정 날짜의 확률 분포
- 예: meeting_20251210_merged.csv (273일치)

✅ **시장 데이터 수집 스크립트** (`collect_macro_finance_v2.py`)
- Yahoo Finance: 주가, 원자재, 환율 등
- FRED API: 금리, 거시경제 지표, 이벤트

❌ **필요하지만 없는 것:**
- 패널 형식 데이터 (`complete_cme_panel_history.csv`)
- 실제 FOMC 결정 금리

---

## 🔧 해결 방안

### Phase 1: 확률 분포 → 기대금리 변환

#### 방법 1: 가중평균 (기댓값) **[추천]**
```python
def calculate_expected_rate(prob_row):
    """
    확률 분포에서 기대금리 계산 (가중평균)
    
    Args:
        prob_row: pandas Series, (0-25)=0.1, (25-50)=0.3, ...
    
    Returns:
        expected_rate_bp: float, 기댓값 (bp 단위)
    """
    total_prob = 0
    expected_rate = 0
    
    for col, prob in prob_row.items():
        if pd.isna(prob) or prob == 0:
            continue
        
        # 컬럼명 파싱: "(0-25)" → 중간값 12.5
        if col.startswith('(') and ')' in col:
            range_str = col.strip('()')
            low, high = map(int, range_str.split('-'))
            mid_point = (low + high) / 2
            
            expected_rate += mid_point * prob
            total_prob += prob
    
    # 정규화 (혹시 합이 1이 아닌 경우 대비)
    if total_prob > 0:
        return expected_rate / total_prob
    else:
        return np.nan

# 사용 예시
df['exp_rate_bp'] = df.apply(
    lambda row: calculate_expected_rate(row.drop('Date')), 
    axis=1
)
```

**장점:**
- 이론적으로 가장 합리적 (확률 가중 평균)
- 분포의 모든 정보 활용
- 예전 분석과 일관성 유지

**단점:**
- 극단값(tail)에 민감할 수 있음

---

#### 방법 2: 중위수 (Median)
```python
def calculate_median_rate(prob_row):
    """확률 분포의 중위수"""
    cumsum = 0
    for col, prob in prob_row.items():
        if pd.isna(prob):
            continue
        cumsum += prob
        if cumsum >= 0.5:
            # 이 구간이 중위수
            range_str = col.strip('()')
            low, high = map(int, range_str.split('-'))
            return (low + high) / 2
    return np.nan
```

**장점:**
- 극단값에 강건 (robust)
- 시장의 "중심 의견" 반영

**단점:**
- tail 정보 무시

---

#### 방법 3: 최빈값 (Mode)
```python
def calculate_mode_rate(prob_row):
    """가장 높은 확률의 구간"""
    max_prob = prob_row.max()
    mode_col = prob_row.idxmax()
    
    range_str = mode_col.strip('()')
    low, high = map(int, range_str.split('-'))
    return (low + high) / 2
```

**장점:**
- 시장의 "컨센서스" 반영
- 계산 빠름

**단점:**
- 분포의 대부분 정보 무시
- bimodal 분포 처리 어려움

---

### 💡 **추천: 가중평균 + 분산도 함께 계산**

```python
def calculate_rate_statistics(prob_row):
    """기댓값 + 표준편차 계산"""
    rates = []
    probs = []
    
    for col, prob in prob_row.items():
        if pd.isna(prob) or prob == 0:
            continue
        if col.startswith('(') and ')' in col:
            range_str = col.strip('()')
            low, high = map(int, range_str.split('-'))
            mid_point = (low + high) / 2
            
            rates.append(mid_point)
            probs.append(prob)
    
    if len(rates) == 0:
        return np.nan, np.nan
    
    # 정규화
    probs = np.array(probs)
    probs = probs / probs.sum()
    rates = np.array(rates)
    
    # 기댓값
    exp_rate = np.sum(rates * probs)
    
    # 표준편차 (불확실성 지표)
    variance = np.sum(((rates - exp_rate) ** 2) * probs)
    std_dev = np.sqrt(variance)
    
    return exp_rate, std_dev

# 사용
df[['exp_rate_bp', 'rate_uncertainty']] = df.apply(
    lambda row: calculate_rate_statistics(row.drop('Date')),
    axis=1,
    result_type='expand'
)
```

**이점:**
- `rate_uncertainty`를 추가 변수로 사용 가능
- "시장이 얼마나 확신하는가" 측정

---

## 📋 Phase 2: 패널 데이터 구조 생성

### 목표 구조
```
meeting_date | asof_date  | exp_rate_bp | rate_uncertainty | days_to_meeting
-------------|------------|-------------|------------------|----------------
2025-07-30   | 2024-09-12 | 327.5       | 45.2             | 321
2025-07-30   | 2024-09-13 | 325.8       | 44.8             | 320
...
2025-12-10   | 2024-11-08 | 387.2       | 52.1             | 397
2025-12-10   | 2024-11-09 | 385.9       | 51.7             | 396
```

### 구현 스크립트

```python
def convert_to_panel(meeting_files_dir, output_file):
    """
    회의별 병합 파일들을 하나의 패널 데이터로 변환
    
    Args:
        meeting_files_dir: 병합 파일들이 있는 디렉토리
        output_file: 출력 패널 파일명
    """
    import glob
    from pathlib import Path
    from datetime import datetime
    
    all_panels = []
    
    # 모든 meeting_*_merged.csv 파일 찾기
    pattern = f"{meeting_files_dir}/meeting_*_merged.csv"
    files = glob.glob(pattern)
    
    print(f"발견된 회의 파일: {len(files)}개\n")
    
    for filepath in sorted(files):
        # 파일명에서 회의 날짜 추출
        filename = Path(filepath).stem
        # meeting_20251210_merged → 20251210
        meeting_date_str = filename.split('_')[1]
        meeting_date = pd.to_datetime(meeting_date_str, format='%Y%m%d')
        
        print(f"처리 중: {meeting_date.date()}")
        
        # 데이터 로드
        df = pd.read_csv(filepath)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # 확률 분포 → 기대금리 계산
        prob_cols = [c for c in df.columns if c != 'Date']
        
        stats = df[prob_cols].apply(
            calculate_rate_statistics,
            axis=1,
            result_type='expand'
        )
        stats.columns = ['exp_rate_bp', 'rate_uncertainty']
        
        # 패널 구조 생성
        panel = pd.DataFrame({
            'meeting_date': meeting_date,
            'asof_date': df['Date'],
            'exp_rate_bp': stats['exp_rate_bp'],
            'rate_uncertainty': stats['rate_uncertainty']
        })
        
        # days_to_meeting 계산
        panel['days_to_meeting'] = (
            panel['meeting_date'] - panel['asof_date']
        ).dt.days
        
        # 음수 제거 (과거 데이터)
        panel = panel[panel['days_to_meeting'] >= 0]
        
        all_panels.append(panel)
        print(f"  → {len(panel)}개 관측치")
    
    # 전체 병합
    full_panel = pd.concat(all_panels, ignore_index=True)
    full_panel.sort_values(['meeting_date', 'asof_date'], inplace=True)
    
    # 저장
    full_panel.to_csv(output_file, index=False)
    
    print(f"\n[완료] 패널 데이터 생성: {output_file}")
    print(f"  - 총 관측치: {len(full_panel):,}개")
    print(f"  - 회의 수: {full_panel['meeting_date'].nunique()}개")
    print(f"  - 기간: {full_panel['asof_date'].min().date()} ~ {full_panel['asof_date'].max().date()}")
    
    return full_panel

# 실행
panel = convert_to_panel(
    meeting_files_dir='~/projects/forecast/merged',
    output_file='~/projects/forecast/complete_cme_panel_history.csv'
)
```

---

## 🎯 Phase 3: 실제 FOMC 금리 데이터

### 방법 1: 수동 입력 (간단하고 정확)

```python
# actual_fed_rates.py

ACTUAL_FOMC_RATES = {
    # meeting_date: (lower_bp, upper_bp, decision_bp_midpoint)
    '2025-05-07': (450, 475, 462.5),
    '2025-06-18': (450, 475, 462.5),  # 동결
    '2025-07-30': (425, 450, 437.5),  # -25bp
    '2025-09-17': (425, 450, 437.5),  # 동결
    '2025-10-29': (425, 450, 437.5),  # 동결
    '2025-12-10': (425, 450, 437.5),  # 동결 (가정)
    # ... 26년 회의들
}

def get_actual_rate(meeting_date):
    """
    실제 FOMC 결정 금리 반환
    
    Args:
        meeting_date: str or datetime, 'YYYY-MM-DD' or datetime
    
    Returns:
        float: 실제 금리 (bp, 중간값)
    """
    if isinstance(meeting_date, str):
        meeting_date = pd.to_datetime(meeting_date).strftime('%Y-%m-%d')
    else:
        meeting_date = meeting_date.strftime('%Y-%m-%d')
    
    if meeting_date in ACTUAL_FOMC_RATES:
        return ACTUAL_FOMC_RATES[meeting_date][2]  # 중간값
    else:
        return np.nan

# 패널에 추가
panel['actual_rate_bp'] = panel['meeting_date'].apply(get_actual_rate)
panel['forecast_error'] = panel['exp_rate_bp'] - panel['actual_rate_bp']
```

**장점:**
- 100% 정확
- 간단하고 빠름
- 수정 용이

**단점:**
- 수동 업데이트 필요

---

### 방법 2: FRED API (자동화)

```python
def fetch_actual_rates_from_fred(fred_api, start_date='2024-01-01'):
    """
    FRED에서 실제 Fed Funds Rate 가져오기
    
    FRED 코드:
    - DFF: 일별 Effective Federal Funds Rate
    - DFEDTARU: 연준 목표 금리 상단
    - DFEDTARL: 연준 목표 금리 하단
    """
    from fredapi import Fred
    
    fred = Fred(api_key=fred_api)
    
    # 목표 금리 (상단/하단)
    upper = fred.get_series('DFEDTARU', observation_start=start_date)
    lower = fred.get_series('DFEDTARL', observation_start=start_date)
    
    # 중간값 계산
    target_rate = (upper + lower) / 2
    
    return target_rate

# FOMC 회의 날짜에 매핑
def map_meeting_to_actual(panel, actual_rates):
    """
    각 회의의 실제 금리 매핑
    """
    panel = panel.copy()
    
    def get_rate_at_meeting(meeting_date):
        # 회의일 또는 직후 영업일의 금리
        try:
            # 회의일 이후 7일 이내의 금리 (발표 반영)
            mask = (actual_rates.index >= meeting_date) & \
                   (actual_rates.index <= meeting_date + pd.Timedelta(days=7))
            if mask.any():
                return actual_rates[mask].iloc[0] * 100  # % → bp
        except:
            pass
        return np.nan
    
    panel['actual_rate_bp'] = panel['meeting_date'].apply(get_rate_at_meeting)
    return panel
```

**장점:**
- 자동화 가능
- 업데이트 용이

**단점:**
- 회의일과 발표일 매칭 필요
- API 제한

---

## 📊 Phase 4: 시장 데이터 문제 해결

### 문제: 일별 데이터가 아닌 경우 결측치 과다

#### 해결책 1: 일별 변수만 선택 **[추천]**

```python
# 결측 비율 확인
def check_missing_ratio(df, threshold=0.9):
    """
    각 변수의 유효 데이터 비율 확인
    
    Args:
        df: DataFrame
        threshold: 최소 유효 데이터 비율 (0.9 = 90%)
    
    Returns:
        valid_vars: 기준 통과한 변수 리스트
    """
    total = len(df)
    missing_info = []
    
    for col in df.columns:
        if col == 'Date':
            continue
        valid = df[col].notna().sum()
        ratio = valid / total
        missing_info.append({
            'variable': col,
            'valid_count': valid,
            'valid_ratio': ratio,
            'pass': ratio >= threshold
        })
    
    result = pd.DataFrame(missing_info).sort_values('valid_ratio')
    
    print(f"[결측치 분석] 총 {len(result)}개 변수")
    print(f"  기준: 유효 데이터 {threshold*100:.0f}% 이상\n")
    
    failed = result[~result['pass']]
    passed = result[result['pass']]
    
    if len(failed) > 0:
        print(f"제외 대상 ({len(failed)}개):")
        for _, row in failed.iterrows():
            print(f"  ✗ {row['variable']:<30} {row['valid_ratio']:.1%}")
    
    print(f"\n사용 가능 ({len(passed)}개):")
    for _, row in passed.head(10).iterrows():
        print(f"  ✓ {row['variable']:<30} {row['valid_ratio']:.1%}")
    
    if len(passed) > 10:
        print(f"  ... (외 {len(passed)-10}개)")
    
    return passed['variable'].tolist()

# 사용
valid_vars = check_missing_ratio(market_data, threshold=0.9)
market_data_clean = market_data[['Date'] + valid_vars]
```

---

#### 해결책 2: Forward Fill (신중하게)

```python
# 금리 변수는 forward fill 합리적
rate_vars = ['US10Y', 'US2Y', 'Baa_Yield', 'SOFR']

for var in rate_vars:
    if var in market_data.columns:
        # 최대 5일까지만 forward fill
        market_data[var] = market_data[var].fillna(method='ffill', limit=5)
```

**주의:**
- 이벤트 변수는 ffill 하면 안됨! (발표일만 1)
- 가격 변수도 ffill 위험 (인위적 연속성)

---

#### 해결책 3: 주간 데이터로 다운샘플링

```python
# 모든 데이터를 주간으로 통일
market_weekly = market_data.resample('W-FRI').last()

# 패널도 주간으로
panel_weekly = panel[panel['asof_date'].dt.dayofweek == 4]  # 금요일만
```

**장점:**
- 결측 문제 완화
- 노이즈 감소

**단점:**
- 관측치 감소
- 일별 변동 포착 못함

---

## 🎯 최종 추천 파이프라인

```
1. 회의별 파일 → 패널 변환
   └─ convert_to_panel()
   └─ 기대금리: 가중평균
   └─ 불확실성: 표준편차

2. 실제 금리 추가
   └─ 수동 입력 (actual_fed_rates.py)
   └─ 또는 FRED API

3. 시장 데이터 정제
   └─ 결측 90% 이상 변수만 사용
   └─ 금리: forward fill (최대 5일)
   └─ 이벤트: 0 채우기

4. 최종 병합
   └─ panel + market_data (left join)
   └─ 날짜 기준 (asof_date)

5. 파생변수 생성
   └─ d_Exp_Rate (일별 변화)
   └─ Horizon 구간
   └─ Returns, Diffs
```

---

## 📝 다음 단계

1. **먼저 확인:** 어떤 방식으로 기대금리를 계산할지 결정
   - 가중평균? 중위수? (저는 가중평균 추천)

2. **패널 변환 스크립트 작성**
   - 위의 `convert_to_panel()` 구현

3. **실제 금리 데이터 준비**
   - 수동 입력으로 시작 (빠르고 정확)

4. **시장 데이터 점검**
   - `collect_macro_finance_v2.py` 실행
   - 결측 비율 확인

준비 되면 알려주세요! 각 단계별 코드를 작성해드리겠습니다. 🚀

