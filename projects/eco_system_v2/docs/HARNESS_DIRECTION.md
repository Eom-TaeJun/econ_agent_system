# eco_system_v2 Harness Direction

이 프로젝트는 `forecast`와 달리 **full harness 후보**다.

이미 아래 요소가 들어와 있다.

- `CLAUDE.md`
- `AGENTS.md`
- `.claude/commands/`
- `.claude/skills/`
- `.claude/hooks/`

따라서 방향은 "하네스를 새로 발명"이 아니라, **기존 멀티에이전트 구조를 repo-backed delivery workflow로 더 명확하게 고정하는 것**이다.

---

## 1. source of truth

기능 추가나 구조 변경 전, Claude는 아래 파일을 먼저 읽는다.

1. `CLAUDE.md`
2. `AGENTS.md`
3. `DOMAIN.md`
4. 이 문서 `docs/HARNESS_DIRECTION.md`

관련 작업일 때:

- 도메인 객체 수정: `.claude/skills/domain-guide/SKILL.md`
- 정량분석/레짐/리스크 수정: `.claude/skills/analysis-standards/SKILL.md`
- 실행/상태 확인: `.claude/commands/run.md`, `.claude/commands/check.md`, `.claude/commands/status.md`

---

## 2. 이 프로젝트에서 harness가 뜻하는 것

eco_system_v2의 harness는 다음을 의미한다.

- 도메인 경계가 파일로 고정되어 있다
- 에이전트 역할이 문서와 코드에 일치한다
- 검증 명령이 명시되어 있다
- 세션이 바뀌어도 현재 구조와 진행 상황을 이어받을 수 있다

즉, **repo-backed multi-agent engineering workflow**다.

---

## 3. 지금 상태 평가

### 이미 갖춰진 것

- `CLAUDE.md`가 경계와 실행 방법을 잘 설명함
- `AGENTS.md`가 5개 에이전트 + 3개 실행 모드를 설명함
- `DOMAIN.md`가 14개 도메인 객체의 필드 상세를 포함함
- `docs/ARCHITECTURE.md`가 계층 경계, 데이터 흐름, 변경 이력을 기록함
- `docs/PROGRESS.md`가 완료/진행/보류 작업 상태를 추적함
- `skills`와 `hooks`가 이미 존재함
- domain purity 검사처럼 deterministic check가 있음

### 선택적 확장

- 큰 기능 작업의 현재 phase를 남길 `.harness/state.json` (현재 불필요)

---

## 4. 권장 harness 레벨

### 지금 즉시 유지할 것

- `CLAUDE.md`
- `AGENTS.md`
- `.claude/skills/`
- `.claude/hooks/`
- 기존 run/status/check commands

### 이미 추가된 것

- `docs/ARCHITECTURE.md` — 에이전트 흐름, 실행 모드, 리포트 생성 경로, bounded context 설명
- `docs/PROGRESS.md` — 현재 기능 작업, 남은 검증, 다음 세션 TODO

### 선택적 확장

- `.harness/state.json` — 큰 기능 작업일 때만 사용 (현재 불필요)

### 과하지 않은 선

- 모든 작은 패치에 state 파일 강제하지 않기
- 문서 없이 코드만 바꾸는 것만 피하기

---

## 5. 기능 추가 / 수정 시 작업 순서

### A. 작은 수정

예: 에이전트 로직 버그, 출력 포맷 수정, import 경계 정리

1. 관련 파일 읽기
2. 코드 수정
3. 최소 verify 실행

예:

```bash
python main.py --quick
python -m compileall domain/ agents/ infrastructure/
grep -r "import yfinance\|import anthropic\|import httpx" domain/
```

### B. 기능 추가

예: 새 Agent, 새 ReportSection, 새 실행 모드, 새 리스크 계산

1. 먼저 `AGENTS.md` 또는 `CLAUDE.md`에서 구조 충돌 확인
2. 경계나 흐름이 바뀌면 `docs/ARCHITECTURE.md`를 먼저 작성 또는 갱신
3. 구현
4. quick/full/forecast 중 영향 범위에 맞게 검증
5. 여러 세션 작업이면 `docs/PROGRESS.md` 또는 `.harness/state.json` 갱신

### C. 구조 변경

예: agent pipeline 재배치, domain model 변경, report flow 변경

1. 문서 먼저 (`AGENTS.md`, `CLAUDE.md`, 이후 `docs/ARCHITECTURE.md`)
2. 그 다음 코드
3. verify 후 outputs 확인

---

## 6. 검증 규칙

기본 verify 세트:

```bash
python main.py --quick
python main.py --full
python -m compileall domain/ agents/ infrastructure/
grep -r "import yfinance\|import anthropic\|import httpx" domain/
```

작업 유형별 추가:

- ForecastAgent 변경: `python main.py --forecast`
- 리포트 변경: `python main.py --full --report`
- 도메인 모델 변경: `outputs/eco_*.json` 구조 확인

---

## 7. Claude에게 기대하는 행동

기능 추가나 수정 요청을 받으면 Claude는 먼저:

1. 이 변경이 `small fix / feature / structural change` 중 무엇인지 분류
2. 문서 선수정이 필요한지 판단
3. 필요한 verify 명령을 명시
4. 세션 넘김 가능성이 크면 progress/state 파일을 제안

---

## 8. 결론

eco_system_v2는 full harness 구조를 갖추고 있다.

현재 상태:

- `CLAUDE.md` + `AGENTS.md` + `DOMAIN.md` — source of truth 완비
- `docs/ARCHITECTURE.md` — 계층 경계, 데이터 흐름, 변경 이력
- `docs/PROGRESS.md` — 완료/진행/보류 작업 추적
- `.claude/` — commands, agents, skills, hooks 운용 중

유지 원칙: 새 프레임워크를 추가하지 말고, 기존 repo artifact를 갱신하며 세션 간 연속성을 유지한다.
