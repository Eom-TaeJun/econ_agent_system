---
name: eth-blockchain-analysis
description: |
  Chainlink 오라클과 Uniswap DEX의 ETH/USD 시계열 데이터 정제·분석 표준.
  블록체인 온체인 데이터 분석, 오라클-DEX 스프레드, 변동성 레짐,
  유동성 충격 분석 시 자동 활성화된다.
version: 1.0.0
updated: 2026-02-20
source: datasets/open_price/ETH_TIME_SERIES_METHOD_STANDARD_v1.md
---

# ETH 시계열 분석 표준 (v1)

## 데이터 성격

| 소스 | 특성 | 역할 |
|------|------|------|
| **Chainlink** | 이벤트 기반 오라클 업데이트 | 기준가격 (anchor) |
| **Uniswap v3** | 체결(스왑) 기반 초고빈도 | 실행가격 (executable) |

두 소스는 관측 메커니즘이 다름 → **원시값 직접 비교 금지**, 시간 정렬 후 비교.

## 스키마 규칙

```python
# 필수 타입 통일
df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)  # UTC aware 강제
# 가격: float64 / 수량·거래량: float64 / 블록번호: int64
```

## 정제 기준 (필수)

```python
# 1. 무효가격 제거
df = df[df['price'] > 0]

# 2. 완전 중복 제거
df = df.drop_duplicates()

# 3. Chainlink 고유키: global_round_id (중복 시 최신 1건)
# 4. Uniswap 고유키: tx_hash + block_number + timestamp + usdc_amount + eth_amount

# 5. 극단치 — 즉시 삭제 X, 플래그로 마킹
df['jump_flag'] = (df['return'].abs() > 0.15).astype(int)      # 1분 수익률 15% 초과
df['spread_anomaly'] = (df['spread_abs'] > spread_p99).astype(int)
```

## 품질 게이트 (QC) — 분석 전 모두 통과해야 함

| Gate | 조건 |
|------|------|
| A | 시간 역행 행 수 = **0** |
| B | 필수 컬럼 null 비율 < **0.1%** |
| C | Chainlink 연속 업데이트 간격 p99 < **120분** |
| D | Uniswap 수량 부호 위반 비율 < **0.01%** |
| E | 집계 후 결측 바 비율(1h) < **1%** |

## 시계열 정렬 기준

```python
# 공통 비교 프레임: 1m, 5m, 1h bar
# Uniswap 바 가격: VWAP 사용
# Chainlink: 바 시점까지 마지막 값을 asof 방식으로 매핑
chainlink_bar = chainlink.resample('1h').last()           # asof
uniswap_bar   = uniswap.resample('1h').apply(vwap)        # VWAP
```

## 핵심 지표

```python
r_t     = np.log(P_t / P_t_prev)              # 로그 수익률
spread_usd = P_uni - P_cl                      # 절대 스프레드
spread_bps = 10000 * (P_uni - P_cl) / P_cl    # bps 스프레드
rvol       = np.sqrt((r_t**2).rolling(n).sum()) # Realized Vol
staleness  = (now - last_oracle_update).dt.total_seconds() / 60  # 오라클 갱신 지연 (분)
```

## 분석 순서 (권장)

1. **단일 소스 기술통계** — 가격·수익률·거래량 분포
2. **오라클-DEX 스프레드** — 절대값, bps, 지속시간, 빈도
3. **변동성 레짐 분할** — rolling volatility 기반 저/중/고
4. **유동성 충격 분석** — 대형 volume 전후 가격 반응
5. **이벤트 분석** — 급등락, 대형 괴리, 비정상 스파이크

## 블록체인 도메인 주의사항

- 블록 타임 ≠ 벽시계 시간 (미세 오차 허용)
- 동일 tx에서 다중 이벤트 가능 → tx 단위 집계 vs 이벤트 단위 분석 분리
- USDC 디페그 위험 → 대형 괴리 구간에 이벤트 주석 필수

## 리포팅 최소 산출물

- [ ] 데이터 품질표 (QC 통과/실패)
- [ ] 기간/행수/커버리지 요약
- [ ] 가격 오버레이 차트 + 스프레드 차트
- [ ] 이상 이벤트 Top 20 테이블 (시각, 블록, tx, 스프레드, 거래량)

## 재현성 규칙

```
raw/      → 불변 (원본)
silver/   → 정제 결과: {name}_{YYYYMMDD}_{rule_version}.parquet
gold/     → 집계 결과: {name}_{timeframe}_{YYYYMMDD}.parquet
```

---
원본 스탠다드: `datasets/open_price/ETH_TIME_SERIES_METHOD_STANDARD_v1.md`
