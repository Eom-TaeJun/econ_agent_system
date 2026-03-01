# 다날 포트폴리오 프로젝트 설계

> 상태: 확정 준비 중
> 업데이트: 2026-03-01 (GitHub 레퍼런스 반영)

---

## GitHub 레퍼런스 (결합 방식 선례)

### Tier 1: 완전 일치 사례

#### 1. `staskh/trading_skills` ★ 구조 참고
```
.claude/skills/
  fundamentals/
    SKILL.md          ← 트리거 조건 + "Run: uv run python scripts/fundamentals.py SYMBOL"
    scripts/
      fundamentals.py ← yfinance 실제 수집
      piotroski.py
  technical-analysis/
    scripts/
      technicals.py
mcp_server/server.py  ← FastMCP 래퍼 (Claude Desktop 병행 지원)
src/trading_skills/   ← 공유 Python 라이브러리
```
**핵심 패턴:** SKILL.md → Python 스크립트 직접 호출. 스킬 폴더 안에 scripts/ 포함.

#### 2. `daloopa/investing` ★ 아키텍처 참고
```
.claude/skills/       ← Claude Code 인터페이스 (18개 스킬)
recipes/              ← 독립 실행 Python 스크립트 (배치/자동화)
infra/                ← 공유 유틸리티 (market_data.py, chart_generator.py...)
.mcp.json             ← 데이터 벤더 연결
```
**핵심 패턴:** skills(인터랙티브) + recipes(배치) + infra(공유) 3-레이어 분리.

---

## 채택할 아키텍처: daloopa 3-레이어 + staskh 스크립트 패턴

```
danal-research/
│
├── .claude/                      ← Claude Code 인터페이스
│   ├── skills/
│   │   ├── weekly-brief/
│   │   │   └── SKILL.md          ← morning-note 변용 + "Run: python src/collect.py"
│   │   ├── im-draft/
│   │   │   └── SKILL.md          ← cim-builder 변용
│   │   └── stablecoin-market/    ← 新 (다날 특화)
│   │       └── SKILL.md
│   └── commands/
│       ├── brief.md              ← /brief
│       ├── im.md                 ← /im [company]
│       └── screen.md             ← /screen [sector]
│
├── src/                          ← Python 수집/분석 (= recipes + infra 통합)
│   ├── collect.py                ← eco_system/collect.py 편입 + CoinGecko 추가
│   ├── research.py               ← eco_system/research.py 편입 + 스키마 분리
│   └── report.py                 ← eco_system/report.py 편입 + Markdown 출력
│
├── outputs/
│   └── reports/                  ← 샘플 리포트 (GitHub에 미리 올림)
│       ├── brief_20260301.md
│       └── im_Circle_20260301.md
│
├── main.py                       ← CLI 진입점 (<80줄)
├── requirements.txt
└── README.md                     ← 5초 임팩트
```

---

## SKILL.md 연결 패턴 (staskh 방식)

```markdown
# Weekly Brief Skill

트리거: "주간 브리핑", "핀테크 동향", "디지털자산 현황", "weekly brief"

## 실행
Run: python src/collect.py --mode brief
Run: python src/report.py --type brief

## 출력
outputs/reports/brief_YYYYMMDD.md
```

SKILL.md는 짧게 — 트리거 조건 + 실행 명령 + 출력 경로만.
도메인 지식은 SKILL.md 본문에 서술 (skills/stablecoin-market/SKILL.md만 새로 작성).

---

## Python 편입 계획

| 파일 | 출처 | 변경 내용 | 예상 줄수 |
|------|------|---------|---------|
| `src/collect.py` | eco_system/phases/collect.py (53줄) | CoinGecko 스테이블코인 추가 | ~80줄 |
| `src/research.py` | eco_system/agents/research.py (57줄) | 스키마 의존성 분리 | ~60줄 |
| `src/report.py` | eco_system/phases/report.py (31줄) | JSON → Markdown 출력 | ~50줄 |
| `src/coingecko.py` | 新 작성 | 스테이블코인 시총/거래량 | ~40줄 |
| `main.py` | 新 작성 | CLI argparse | <80줄 |

EIMAS/lib/data_collector.py (858줄) — 편입 불가, 참조만

---

## 데이터 소스

| 소스 | 용도 | 비용 | API키 |
|------|------|------|-------|
| FRED | 금리·환율·CPI·M2 | 무료 | 있음 |
| CoinGecko | 스테이블코인 시총·거래량 | 무료 (rate limit 있음) | 불필요 |
| DeFiLlama | TVL·온체인 | 무료 | 불필요 |
| Perplexity | 뉴스·최신 동향 | 유료 | 있음 |
| yfinance | BTC·ETH·거시 시장 | 무료 | 불필요 |

---

## 경량화 수칙 (EIMAS 반면교사)

1. main.py < 80줄, 모드 3개 이하
2. src/ 파일 1개당 100줄 이하
3. SKILL.md 1개당 50줄 이하 (트리거 + 실행 + 출력 형식만)
4. 기능 추가 전 기존 파일 삭제 검토
5. DB 없음 — JSON 파일만

---

## GitHub README 전략 (5초 임팩트)

```markdown
# danal-research

핀테크 & 디지털자산 투자 리서치 자동화

## 사용법
python main.py --brief              # 주간 핀테크 브리핑
python main.py --im "Circle"        # 투자 검토 보고서 초안
python main.py --screen stablecoin  # 시장 스크리닝

## 샘플 출력
→ outputs/reports/brief_20260301.md
→ outputs/reports/im_Circle_20260301.md
```

---

## 다음 단계

- [ ] 1. 프로젝트 이름 확정 (`danal-research` vs 다른 안)
- [ ] 2. GitHub 레포 생성
- [ ] 3. `.claude/` 폴더 구조 생성 + Anthropic 플러그인에서 skills 변용
- [ ] 4. `src/collect.py` 편입 (eco_system 기반 + CoinGecko 추가)
- [ ] 5. `src/report.py` → Markdown 출력으로 수정
- [ ] 6. `stablecoin-market/SKILL.md` 직접 작성
- [ ] 7. 샘플 리포트 실행 후 `outputs/` 에 저장
- [ ] 8. README 작성 후 GitHub 업로드
