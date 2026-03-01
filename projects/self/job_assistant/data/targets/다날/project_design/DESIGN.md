# 다날 포트폴리오 프로젝트 설계

> 상태: 의논 중
> 원칙: 기존 시스템 재사용 우선 / MD 제약 최소화

---

## 전략: 재사용 먼저

Anthropic financial-services-plugins를 베이스로.
새로 만드는 것은 다날 특화 부분만.

### 재사용할 것

| 출처 | 재사용 방식 |
|------|-----------|
| `equity-research/morning-note` | → `weekly-brief` 스킬로 변용 |
| `investment-banking/cim-builder` | → `im-draft` 스킬로 변용 (CIM=IM 구조 동일) |
| `equity-research/idea-generation` | → `screen` 스킬로 변용 |
| 커맨드 .md 형식 (2-3줄) | 그대로 복사 |

### 새로 만드는 것 (최소)

- `stablecoin-market` Skill — 다날 피벗 방향 특화
- Python 데이터 수집 스크립트 — FRED + CoinGecko (API키 있음)
- 샘플 리포트 — `outputs/reports/` 에 실제 결과물

---

## 프로젝트 구조

```
danal-research/  (이름 의논 필요)
│
├── README.md              ← GitHub 공개용 (다날 JD 키워드 반영)
├── CLAUDE.md              ← 2섹션 이하 (운영 규칙만)
│
├── skills/
│   ├── weekly-brief/      ← morning-note 변용
│   │   └── SKILL.md       ← 핵심 워크플로우만, 100줄 이하
│   ├── im-draft/          ← cim-builder 변용
│   │   └── SKILL.md
│   └── stablecoin-market/ ← 새로 작성 (다날 특화, 유일한 신규)
│       └── SKILL.md
│
├── commands/
│   ├── brief.md           ← /brief: 주간 핀테크 브리핑
│   ├── im.md              ← /im [company]: IM 초안
│   └── screen.md          ← /screen [sector]: 스크리닝
│
├── data/
│   └── collect.py         ← 데이터 수집 (FRED + CoinGecko)
│
└── outputs/
    └── reports/
        └── sample_brief_20260301.md  ← 실제 작동 증명 샘플
```

---

## Skills 작성 원칙 (MD 제약 최소화)

논문 기준: 인간이 직접 작성한 짧은 지침 = +4~16% 성능
AI 자동생성 지침 = -3% + 비용 20% 증가

```
각 SKILL.md:
- 직접 작성 (AI 생성 금지)
- 100줄 이하
- 워크플로우 + 출력 형식만
- "항상 에러 핸들링해라" 같은 일반 규칙 금지
```

---

## 3가지 커맨드 산출물

### /brief → weekly-brief
```markdown
# 핀테크/디지털자산 주간 브리핑 (2026-03-01)

## 거시경제 스냅샷
- Fed Funds Rate: 4.25% (변화 없음)
- USD/KRW: 1,340 (+0.3% WoW)
- BTC: $95,200 (+4.1% WoW)

## 스테이블코인 시장
- 전체 시총: $245B (+2.1% WoW)
- USDT 도미넌스: 67.2%

## 이번 주 주목 뉴스
1. EU MiCA 2단계 시행 예정 (3월 말)
2. Circle IPO 재추진 보도

## 투자 시사점
...
```

### /im Circle → im-draft
```markdown
# Investment Memorandum — Circle Internet Financial

## Executive Summary
## Company Overview
## Market Opportunity (TAM/SAM/SOM)
## Investment Thesis
## Key Risks & Mitigants
```

### /screen stablecoin → screen
```markdown
# 스테이블코인 섹터 스크리닝 (2026-03-01)

| 프로젝트 | 시총 | 성장률 | 리스크 | 투자 관심도 |
|---------|------|--------|--------|-----------|
| USDT    | $143B | +3%   | 준비금 투명성 | — |
| USDC    | $57B  | +12%  | 규제 리스크  | ★★★ |
```

---

## 데이터 수집 (collect.py)

```python
# 목적: 거시경제 + 디지털자산 핵심 지표 수집
# 입력: 없음 (자동 수집)
# 출력: outputs/context/snapshot.json
# 실패 시: 각 소스별 독립 실패 처리 (일부 실패해도 계속)
# 제외: 실시간 스트리밍, WebSocket

SOURCES = {
    "fred": ["FEDFUNDS", "DEXKOUS", "CPIAUCSL", "DGS10"],  # API키 있음
    "coingecko": ["tether", "usd-coin", "bitcoin"],         # 무료
    "defillama": "https://api.llama.fi/tvl/ethereum"        # 무료
}
```

---

## GitHub README 핵심 (5초 임팩트)

```
# danal-research
핀테크 & 디지털자산 투자 리서치 자동화 에이전트

## 무엇을 하는가
- /brief  : 주간 핀테크/디지털자산 시장 브리핑 생성
- /im     : 투자 검토 보고서(IM) 초안 자동 작성
- /screen : 섹터별 투자 기회 스크리닝

## 샘플 출력
[📄 2026-03-01 주간 브리핑](outputs/reports/brief_20260301.md)
[📄 Circle IM 초안](outputs/reports/im_Circle_20260301.md)
```

---

## 의논할 것

1. **프로젝트 이름** — `danal-research` vs `finvest` vs 다른 안?
2. **collect.py 포함 여부** — 실제 API 호출 코드 vs 스킬만으로 구성?
   - 코드 있으면 "실제 작동하는 프로젝트" 증명 가능
   - 코드 없으면 Claude Code 플러그인 형식 그대로 (Anthropic 플러그인과 동일)
3. **샘플 리포트** — 미리 실행해서 outputs/에 넣어둘지?
4. **stablecoin-market Skill** 내용 — 어느 수준까지 직접 작성할지?
