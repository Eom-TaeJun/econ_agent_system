# Finance Analysis Harness — 예시 플러그인

금융 데이터 분석을 위한 하니스 엔지니어링 예시.
거시경제, 시장 시그널, 금융 분석 방법론을 Claude Code 플러그인으로 구현.

---

## 전체 구조 & 설계 의도

```
finance-analysis-harness/
│
├── .claude-plugin/plugin.json     ← 하니스 매니페스트
│
├── skills/                        ← 지식 자동 주입 레이어
│   ├── macro-economics/           : GDP·금리·물가 분석 기준
│   ├── financial-signals/         : VIX·수익률곡선·크레딧 해석
│   ├── analysis-standards/        : Python 코드·통계모델 컨벤션
│   └── korean-finance/            : 한국 시장 특수성
│
├── agents/                        ← 자율 실행 레이어
│   ├── data-validator.md          : 분석 전 데이터 품질 검증
│   ├── macro-analyst.md           : 레짐 판단 · 정책 분석
│   ├── signal-interpreter.md      : 시장 시그널 교차 해석
│   └── report-writer.md           : 리포트 생성 · 저장
│
├── hooks/                         ← 가드레일 레이어
│   ├── hooks.json                 : 이벤트 핸들러 설정
│   └── scripts/
│       ├── load-market-context.sh : SessionStart — API키 확인, 환경 초기화
│       └── validate-bash.sh       : PreToolUse — 위험 명령 차단
│
├── commands/                      ← 사용자 진입점 레이어
│   ├── analyze.md                 : /analyze — 전체 파이프라인
│   ├── regime.md                  : /regime — 빠른 레짐 스냅샷
│   ├── signal-check.md            : /signal-check — 시그널 즉시 해석
│   └── report.md                  : /report — 분석 결과 저장
│
└── .mcp.json                      ← 외부 서비스 연결
    ├── fred-api                   : FRED 거시경제 데이터
    └── market-data                : 시장 가격 데이터
```

---

## 컴포넌트별 설계 의도

### Skills — "자동으로 무엇을 알아야 하는가"

Skills는 Claude에게 **도메인 지식을 자동으로 주입**한다.
사용자가 "VIX 분석해줘"라고 하면 `financial-signals` 스킬이 자동 활성화되어
VIX 해석 기준, Bekaert 분해 방법론, 역사적 임계값이 컨텍스트에 들어간다.

별도로 "VIX는 20이 경계입니다" 같은 말을 할 필요가 없다.

| Skill | 활성화 조건 | 주입 내용 |
|-------|------------|----------|
| `macro-economics` | GDP·금리·고용 언급 | 지표 해석 기준, 레짐 매트릭스 |
| `financial-signals` | VIX·스프레드·곡선 언급 | 임계값, 역사적 맥락 |
| `analysis-standards` | 코드 작성·통계 분석 | Python 컨벤션, 모델 선택 기준 |
| `korean-finance` | 한국 시장·한국어 리포트 | 한국 데이터 소스, 특수성 |

### Agents — "누가 어떤 일을 전담하는가"

각 에이전트는 **단일 책임**을 갖는다. 분석 파이프라인의 각 단계를 독립 처리.

```
데이터 수집 → [data-validator] → [macro-analyst] → [signal-interpreter] → [report-writer]
               품질 검증          레짐 판단          시그널 교차확인         결과 저장
```

에이전트를 분리한 이유:
- **data-validator**: 분석 전 검증을 강제 → 나쁜 데이터로 좋은 분석 불가
- **macro-analyst**: 거시 전문 → 컨텍스트 오염 없이 집중 분석
- **signal-interpreter**: 시그널 전문 → 거시 결론에 편향되지 않는 독립 확인
- **report-writer**: 문서화 전문 → 분석과 글쓰기를 분리

### Hooks — "무엇을 자동으로 막고 확인하는가"

| Hook | 이벤트 | 역할 |
|------|--------|------|
| `load-market-context.sh` | SessionStart | API키 확인, outputs/ 생성, 환경변수 설정 |
| Prompt (Write 검증) | PreToolUse/Write | 민감정보 하드코딩, 잘못된 저장경로 차단 |
| `validate-bash.sh` | PreToolUse/Bash | rm -rf 등 위험 명령 차단 |
| Prompt (Bash 결과) | PostToolUse/Bash | 에러·경고 자동 감지 |
| Prompt (완료 검증) | Stop | 분석 완성도 보장 (5가지 체크) |
| Prompt (압축 보존) | PreCompact | 컨텍스트 손실 방지 |

### Commands — "사용자는 어떻게 시작하는가"

| Command | 용도 | 소요 시간 |
|---------|------|----------|
| `/analyze [주제]` | 전체 파이프라인 실행 | 10-20분 |
| `/regime` | 현재 레짐 빠른 확인 | 2-5분 |
| `/signal-check [시그널] [값]` | 단일 시그널 즉시 해석 | 1-2분 |
| `/report [파일명]` | 세션 분석 결과 저장 | 1-2분 |

### MCP Servers — "어떤 외부 데이터를 쓰는가"

| 서버 | 제공 데이터 | 인증 |
|------|------------|------|
| `fred-api` | FRED 거시경제 시계열 | `FRED_API_KEY` 환경변수 |
| `market-data` | 주가·ETF·환율·원자재 | 없음 (공개 데이터) |

---

## 실행 흐름 예시

```
사용자: /analyze 현재 인플레이션 상황

1. [SessionStart Hook]  API키 확인, 환경 초기화
2. [analyze Command]    파이프라인 지시문 전달
3. [Skill 자동 활성화]  macro-economics + financial-signals 활성화
4. [MCP: fred-api]      CPI, PCE, Breakeven, PPI 수집
5. [Agent: data-validator]  결측값·이상치 검증
6. [Agent: macro-analyst]   인플레이션 레짐 판단
7. [Agent: signal-interpreter] Breakeven·TIPS 교차 확인
8. [PostToolUse Hook]   각 Bash 실행 결과 에러 감지
9. [Agent: report-writer]   outputs/analyze_20260219.md 저장
10. [Stop Hook]         5가지 완성도 체크 → approve
```

---

## 설치 방법

```bash
# 1. 플러그인 디렉토리에 복사
cp -r finance-analysis-harness/ ~/.claude/plugins/

# 2. 환경변수 설정 (.bashrc 또는 .env)
export FRED_API_KEY="your_key_here"
export BOK_API_KEY="your_key_here"  # 한국은행 데이터 (선택)

# 3. MCP 서버 패키지 설치 (실제 구현 시)
pip install mcp-fred-server mcp-market-server

# 4. Claude Code에서 플러그인 활성화
# /plugins → finance-analysis-harness → Enable
```
