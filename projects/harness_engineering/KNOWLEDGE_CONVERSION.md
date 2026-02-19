# 기존 지식 파일을 Skill로 변환하는 방법

> 텍스트, PDF, Python, Markdown 등 다양한 형태의 기존 자료를
> Skill의 컨텍스트로 효과적으로 전달하는 전략

---

## 핵심 원칙

**Skill에 들어가야 하는 것**: Claude가 특정 상황에서 자동으로 "알아야 하는" 내용
**Skill에 들어가면 안 되는 것**: 원본 파일 전체, 실행 코드, 대용량 데이터

---

## 파일 형태별 변환 전략

### 1. Markdown 파일 (.md)
→ **가장 쉬운 케이스. 거의 그대로 사용 가능.**

```
기존: methodology.md (분석 방법론 문서)
변환: skills/methodology/SKILL.md

작업:
1. 파일 상단에 YAML frontmatter 추가
2. description에 "언제 활성화되는지" 작성
3. 내용이 너무 길면 핵심 기준·원칙만 추출
```

**변환 예시:**
```markdown
# 기존 파일 내용 (그대로 유지)
---
# 기존 파일 상단에 삽입

---
name: methodology
description: |
  분석 방법론, 통계 모델 선택, 검증 절차 관련 작업 시 활성화.
version: 1.0.0
---

# (기존 내용)
```

---

### 2. Python 파일 (.py)
→ **코드 자체가 아닌 "패턴·컨벤션·주의사항"을 추출**

```
기존: lasso_model.py (LASSO 구현 코드)
변환: skills/lasso-standards/SKILL.md

추출할 내용:
- 함수 시그니처와 파라미터 설명 (docstring)
- 핵심 설계 결정 (왜 TimeSeriesSplit? 왜 Treasury 제외?)
- 재사용 패턴 (주석으로 설명된 부분)
- 주의사항 (코드 내 WARNING 주석)
```

**변환 예시:**
```markdown
---
name: lasso-standards
description: LASSO 모델을 금융 데이터에 적용할 때 활성화.
---

# LASSO 금융 적용 표준

## 필수 설정
- CV: `TimeSeriesSplit(n_splits=5)` — 미래 누수 방지 (일반 KFold 금지)
- 스케일링: `StandardScaler` 필수 (계수 비교 가능성)
- max_iter: 10000 이상 (수렴 실패 방지)

## 변수 제외 규칙
Treasury 계열 변수 제외 (simultaneity bias):
`DGS2, DGS5, DGS10, DGS30, T10Y2Y, DFII10`

## 실제 구현 참조
전체 코드: `lib/lasso_model.py`의 `fit_lasso()` 함수
```

---

### 3. PDF 파일 (.pdf)
→ **논문·보고서: 핵심 방법론과 기준값만 추출**

```
기존: bekaert_2022_vix_decomposition.pdf (학술 논문)
변환: skills/financial-signals/references/vix-decomposition.md
      (SKILL.md에서 @참조 또는 내용 통합)

추출할 내용:
- 핵심 공식/방정식
- 기준값 (임계값, 파라미터 추정치)
- 해석 가이드라인
- 방법론 한계
```

**변환 예시:**
```markdown
## VIX 분해 방법론 (Bekaert et al. 2022)

### 핵심 공식
VIX² ≈ Risk Premium Component + Uncertainty Component

### 추정 방법
- VAR 모델로 미래 분산 예측 → Uncertainty
- 잔차 = Risk Premium
- 월별 데이터, rolling 36개월 window 권장

### 해석 기준
- Risk Premium 주도 VIX 상승: 시장 공포 (단기적, 빠른 회복 가능)
- Uncertainty 주도 VIX 상승: 구조적 불확실성 (장기화 가능성)
```

---

### 4. 텍스트 파일 (.txt)
→ **형식에 따라 다르게 처리**

| 내용 유형 | 변환 방법 |
|----------|----------|
| 분석 노트·메모 | 핵심 인사이트만 추출 → SKILL.md 통합 |
| 데이터 사전 (변수 설명) | 테이블 형식으로 정리 → references/ 폴더 |
| 체크리스트 | 그대로 SKILL.md에 체크리스트 섹션으로 |
| 로그·기록 | Skill 대상 아님 (outputs/ 보관) |

---

### 5. 대용량 참조 자료 (긴 문서)
→ **SKILL.md + references/ 폴더 분리 구조**

```
skills/
└── my-domain/
    ├── SKILL.md              ← 핵심 원칙만 (1-2페이지 분량)
    └── references/
        ├── full-guide.md     ← 상세 내용 (대용량 OK)
        ├── formula-sheet.md  ← 공식 모음
        └── glossary.md       ← 용어 사전
```

SKILL.md에서 참조:
```markdown
# 핵심 원칙 (여기에 요약)

상세 내용은 `${CLAUDE_PLUGIN_ROOT}/skills/my-domain/references/full-guide.md` 참조.
```

---

## 변환 품질 기준

좋은 Skill 변환의 특징:

| 좋은 예 | 나쁜 예 |
|--------|--------|
| "Z-score > 3.5이면 이상치로 분류" | "이상치를 적절히 처리하라" |
| "LASSO에서 Treasury 변수는 simultaneity로 제외" | "변수 선택에 주의하라" |
| "HY OAS > 500bp = 위험 구간" | "스프레드가 높으면 위험" |
| 1-2페이지 분량의 핵심 기준 | 50페이지 원본 PDF 붙여넣기 |

---

## 변환 작업 흐름

```
기존 파일 목록 작성
      ↓
파일별 핵심 추출 (Claude에게 요청 가능)
  "이 파일에서 분석 시 항상 지켜야 할 기준과 임계값만 추출해줘"
      ↓
Skill 카테고리 분류
  - 도메인 지식 → skills/domain-name/SKILL.md
  - 방법론 기준 → skills/methodology/SKILL.md
  - 코드 패턴   → skills/code-standards/SKILL.md
  - 도구 사용법 → skills/tooling/SKILL.md
      ↓
description 작성
  "이 스킬이 언제 필요한지" 구체적으로
      ↓
대용량 원본은 references/ 폴더에 보관
      ↓
테스트: 관련 작업 시 스킬이 자동 활성화되는지 확인
```

---

## 실제 예시: EIMAS 프로젝트 지식 변환

```
기존 파일                           → 변환 위치
─────────────────────────────────────────────────
CLAUDE.md (방법론 문서)             → skills/macro-economics/SKILL.md 통합
forecasting_20251218.py             → skills/analysis-standards/references/lasso-guide.md
critical_path_analyzer.py의 docstr  → skills/financial-signals/SKILL.md 통합
bekaert 논문 PDF                    → skills/financial-signals/references/vix-decomp.md
README.md들                         → 해당 스킬 references/ 폴더
기존 분석 결과 .json/.md            → Skill 대상 아님 (outputs/ 그대로 보관)
```
