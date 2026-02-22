# Finance Analysis Harness — 프로젝트 의도 선언

> 이 파일은 프로젝트의 불변 핵심을 기록한다.
> 수정 시 반드시 명시적 승인이 필요하다.
> 새 세션의 AI는 이 파일을 CLAUDE.md보다 먼저 읽어야 한다.

---

## 핵심 목적 (Why)

금융·경제 데이터를 분석할 때, **AI가 매번 다르게 추론하지 않도록**
도메인 지식 기반의 일관된 분석 파이프라인을 제공한다.

분석의 방향과 해석은 도메인 지식(Skills)이 결정하고,
AI는 그 틀 안에서 실행 도구로 작동한다.

---

## 설계 불변 원칙 (Invariants)

이 원칙들은 프로젝트가 성장해도 변하지 않는다:

1. **도메인 어휘 우선** — 새 기능을 추가하기 전, 반드시 하단 어휘 레지스터에 용어를 먼저 등록한다.
2. **구조가 어휘를 따른다** — 파일명·폴더명은 도메인 어휘와 1:1 매핑이어야 한다.
3. **에이전트는 단일 책임** — 하나의 에이전트는 하나의 도메인 역할만 담당한다.
4. **출력은 outputs/ 하위에만** — 분석 결과는 반드시 `outputs/context/` 또는 `outputs/reports/`에만 저장한다.
5. **데이터 검증 선행** — 어떤 분석도 data-validator를 거치지 않고 시작할 수 없다.
6. **Skills는 읽기 전용** — AI는 Skills 파일을 수정하지 않는다. Skills는 인간이 관리한다.

---

## 안티-골 (절대 하지 않는다)

- 단일 에이전트에 모든 분석 책임을 몰아주는 것
- 어휘 레지스터에 없는 이름으로 파일·폴더를 생성하는 것
- `outputs/` 외부에 분석 결과를 저장하는 것
- AI가 Skills 파일을 직접 수정하는 것
- 도메인 지식 없이 AI 자체 추론만으로 투자 판단을 내리는 것
- 데이터 검증 없이 분석을 시작하는 것

---

## 도메인 어휘 레지스터 (Vocabulary Register)

사용자가 대화에서 이 단어를 사용하면,
AI는 설명 없이도 아래 구조로 직접 네비게이션한다.

| 도메인 용어 | 담당 에이전트 | 참조 스킬 | 출력 파일 | MCP 도구 |
|------------|-------------|---------|---------|---------|
| **레짐** | `agents/macro-analyst.md` | `skills/macro-economics/` | `outputs/context/regime_snapshot.json` | `get_regime()` |
| **시그널** | `agents/signal-interpreter.md` | `skills/financial-signals/` | `outputs/context/signal_summary.json` | `get_signals()` |
| **리스크** | `agents/risk-mgr.md` | `skills/risk-assessment/` | `outputs/context/risk_assessment.json` | — |
| **포트폴리오** | `agents/quant-coder.md` | `skills/portfolio-theory/` | `outputs/context/chart_paths.json` | — |
| **미시구조** | `agents/signal-interpreter.md` | `skills/market-microstructure/` | `outputs/context/signal_summary.json` | — |
| **온체인** | `agents/researcher.md` | `skills/crypto-onchain/` | `outputs/context/research_summary.json` | — |
| **리서치** | `agents/researcher.md` | — | `outputs/context/research_summary.json` | — |
| **검증** | `agents/data-validator.md` | `skills/analysis-standards/` | `outputs/context/validation_result.json` | — |
| **리포트** | `agents/report-writer.md` | — | `outputs/reports/analyze_YYYYMMDD.md` | — |
| **오케스트레이션** | `agents/orchestrator.md` | — | `outputs/context/orchestration_plan.json` | — |

---

## 새 도메인 어휘 추가 프로세스

새 기능이나 분석 영역이 생길 때 반드시 이 순서를 따른다:

```
1. 이 파일의 어휘 레지스터에 새 용어 추가
2. 대응하는 skills/ 폴더 생성 (SKILL.md 작성)
3. 필요 시 agents/ 파일 생성 또는 수정
4. CLAUDE.md의 에이전트 파이프라인 업데이트
5. 변경 사항 커밋 및 버전 태그
```

---

## 외부 모델 연동 (Multi-LLM)

| 역할 | 모델 | 환경변수 | 없으면 |
|------|------|---------|-------|
| 대용량 문서 처리 | `gemini-3.1-pro-preview` | `GOOGLE_API_KEY` | WebFetch 직접 수집 |
| 백테스팅 코드 생성 | `gpt-5.3-codex` | `OPENAI_API_KEY` | Claude가 직접 구현 |
| 브로커 실행 | TastyTrade MCP | `TASTYTRADE_USER/PASS` | dry_run 모드 |

---

## 구조 작동 원리 (참조 프레임워크)

| 패턴 | 출처 | 적용 위치 |
|------|------|---------|
| Canonical Intent 변환 | NeMo Guardrails | `hooks/scripts/skill-activation-prompt.mjs` |
| Lazy Skill Loading | Superpowers (42k★) | `hooks/scripts/skill-activation-prompt.mjs` |
| role / goal / backstory 트라이어드 | CrewAI | `agents/contracts.json` |
| Handoff 선언 | Semantic Kernel | `agents/contracts.json` |
| Intent 드리프트 차단 | 자체 설계 | `hooks/scripts/check-intent-drift.sh` |
| 의도 재로드 | Anthropic 장기 에이전트 연구 | `hooks/scripts/load-intent.sh` |

### Canonical Intent 흐름

```
사용자 입력 (자유문장)
    ↓ [skill-activation-prompt.mjs]
Canonical Intent 감지
  "레짐 분석" / "리스크 평가" / "포트폴리오 최적화" / ...
    ↓
어휘 레지스터 매핑
  → 담당 에이전트 + 참조 스킬 + 출력 파일 명시
    ↓
에이전트 파이프라인 실행
```

### 에이전트 계약

`agents/contracts.json` — 각 에이전트의 role/goal/backstory/handoff를 기계적으로 선언.
orchestrator는 이 파일을 읽어 라우팅을 결정한다.

---

## 버전 이력

| 날짜 | 변경 내용 | 승인자 |
|------|---------|------|
| 2026-02-22 | 최초 작성 | tj |
| 2026-02-22 | Canonical Intent, Lazy Loading, Contracts 패턴 추가 | tj |
