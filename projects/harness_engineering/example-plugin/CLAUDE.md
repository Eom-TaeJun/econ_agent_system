# Finance Analysis Harness — 운영 매뉴얼

> **세션 시작 시 필독 순서:**
> 1. `INTENT.md` — 프로젝트 의도·불변 원칙·도메인 어휘 레지스터
> 2. 이 파일 (`CLAUDE.md`) — 운영 규칙·파이프라인

---

## 이 플러그인의 목적

금융·경제 데이터를 **도메인 지식 기반**으로 분석하는 에이전틱 파이프라인.
AI는 실행 도구이고, 분석의 방향과 해석은 도메인 지식이 결정한다.

---

## 핵심 원칙 (항상 유지)

1. **데이터 검증 선행**: 분석 전에 반드시 data-validator 에이전트 실행
2. **인과관계 우선**: 상관관계만 보고하지 말고 "왜 그런가?"까지 추론
3. **레짐 판단 후 섹터**: 거시 레짐(Goldilocks/Overheating/Stagflation/Recession) 먼저, 그 다음 자산 방향
4. **이상치 = 정보**: 금융 데이터 이상치는 제거 전 이벤트 연결 확인
5. **수치는 단위와 기간 함께**: "4.7%", "+65bp", "$36B+" 형식 필수

---

## 에이전트 파이프라인

```
사용자 요청
    ↓
[Commands] /analyze, /regime, /signal-check, /report
    ↓
[Agents 순서]
  1. data-validator  → 데이터 품질 확인 (실패 시 중단)
  2. macro-analyst   → 레짐 판단 + 정책 경로
  3. signal-interpreter → 시그널 일관성 + 이상 탐지
  4. quant-coder     → 코드 실행 + 시각화 (필요 시)
  5. report-writer   → 최종 리포트 저장
```

### 에이전트 핸드오프 규칙

각 에이전트는 작업 완료 후 `outputs/context/` 에 중간 결과를 저장:
```
outputs/
├── context/
│   ├── validation_result.json   ← data-validator 출력
│   ├── regime_snapshot.json     ← macro-analyst 출력
│   ├── signal_summary.json      ← signal-interpreter 출력
│   └── chart_paths.json         ← quant-coder 출력
├── charts/                      ← 생성된 차트 이미지
└── reports/                     ← 최종 리포트 (YYYYMMDD 형식)
```

다음 에이전트는 이전 에이전트의 context 파일을 읽고 시작한다.

---

## MCP 도구 사용법

### EIMAS (경제 분석 시스템 연동)

```python
# EIMAS 상태 확인 (API 실행 중? 파일 있음?)
mcp__finance-analysis-harness_eimas__eimas_status()

# 현재 레짐 조회 (BULLISH/BEARISH/NEUTRAL)
mcp__finance-analysis-harness_eimas__get_regime(ticker="SPY")

# 최신 종합 분석 결과 (all/regime/recommendation/risk/analysis/strategy)
mcp__finance-analysis-harness_eimas__get_latest_analysis(section="recommendation")

# 에이전트 합의 시그널 (BUY/SELL/HOLD)
mcp__finance-analysis-harness_eimas__get_signals(limit=5)

# 레짐 이력 (최근 10개, 선택적 필터)
mcp__finance-analysis-harness_eimas__get_regime_history(limit=10, regime_filter="BEARISH")

# AI 리포트 요약
mcp__finance-analysis-harness_eimas__get_ai_report(section="executive_summary")

# 이벤트 DB 조회 (읽기 전용)
mcp__finance-analysis-harness_eimas__query_events(since_days=7, limit=20)
```

**EIMAS 이중 모드:**
- `python main.py --full` 실행 중 → API 실시간 조회 (localhost:8000)
- API 꺼져 있음 → `outputs/*.json` 파일 직접 읽기 (자동 폴백)

### FRED 데이터

```python
# FRED 데이터 조회
mcp__finance-analysis-harness_fred-api__fetch_series(
    series_id="DGS10",     # 10년물 국채금리
    start_date="2020-01-01"
)

# 시장 데이터 조회
mcp__finance-analysis-harness_market-data__get_price(
    ticker="^VIX",
    period="1y"
)
```

MCP 서버가 없을 경우 Bash로 대체:
```python
# FRED 직접 조회 fallback
import requests
r = requests.get(f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key={FRED_API_KEY}&file_type=json")
```

---

## 자주 쓰는 시계열 ID

| 지표 | FRED ID | 설명 |
|------|---------|------|
| 미국 10년물 | DGS10 | 10-Year Treasury |
| 미국 2년물 | DGS2 | 2-Year Treasury |
| Fed Funds Rate | FEDFUNDS | 기준금리 |
| CPI | CPIAUCSL | 소비자물가지수 |
| Core PCE | PCEPILFE | Fed 공식 목표 |
| 실업률 | UNRATE | Headline |
| 원달러 환율 | DEXKOUS | KRW/USD |
| M2 | M2SL | 광의통화 |

---

## 분석 결과 해석 기준

### 레짐 매트릭스 (항상 이것으로 시작)
```
             인플레이션 ↑    인플레이션 ↓
성장 ↑     Overheating      Goldilocks ← 현재 근접
성장 ↓     Stagflation      Recession
```

### 즉시 경보 조건 (모두 충족 시 리스크 경고 발령)
- VIX > 25 AND HY OAS > 500bp
- 10Y-2Y 역전 후 steepening 시작
- 원달러 > 1,500 (BOK 개입 임계)

---

## 파일 경로 규칙

```
${CLAUDE_PLUGIN_ROOT}/
├── CLAUDE.md                 ← 이 파일 (운영 매뉴얼)
├── .mcp.json                 ← MCP 서버 설정
├── .claude-plugin/plugin.json
├── skills/                   ← 도메인 지식 (자동 로드)
├── agents/                   ← 에이전트 정의
├── commands/                 ← 슬래시 커맨드
├── hooks/                    ← 가드레일
├── mcp_servers/              ← MCP 서버 구현 코드
└── outputs/                  ← 분석 결과 저장
```

분석 중 생성 파일은 반드시 `outputs/` 하위에만 저장.
소스 코드, Skills, Agents 파일은 수정하지 않는다.

---

## 한국어/영어 혼용 규칙

- 분석 리포트: 한국어 기본, 전문 용어는 영어 병기
  - 예: 수익률 곡선(Yield Curve), 기저효과(Base Effect)
- 수치 단위: 한국식 (억원, 조원) + 영어 병기 ($B)
- 시계열 표현: "전월대비(MoM)", "전년대비(YoY)"

---

## 새 세션 시작 시 체크리스트

SessionStart hook이 자동으로 수행:
1. API 키 확인 (FRED_API_KEY, BOK_API_KEY)
2. outputs/ 디렉토리 생성
3. 시장 컨텍스트 스냅샷 로드

수동으로 확인할 것:
- [ ] 분석 기간 (start_date, end_date)
- [ ] 분석 주제 (레짐 전반 vs 특정 지표 vs 개별 종목)
- [ ] 출력 형식 (리포트 파일 vs 인터랙티브 대화)
