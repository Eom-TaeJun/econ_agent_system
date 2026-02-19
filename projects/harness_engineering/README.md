# 하니스 엔지니어링 (Harness Engineering)

> "2025년은 에이전트의 해였다. 2026년은 에이전트 하니스의 해다."
> — Aakash Gupta, Jan 2026

---

## 1. 왜 컨택스트 엔지니어링에서 하니스 엔지니어링으로?

### 컨택스트 엔지니어링의 한계
컨택스트 엔지니어링은 LLM에게 **무엇을, 어떤 형태로 전달할 것인가**에 집중했다.
- 프롬프트 설계
- 컨텍스트 윈도우 관리
- RAG / 정보 검색

하지만 에이전트가 복잡하고 장기적인 작업을 수행하게 되면서 **컨텍스트 하나만으로는 부족**해졌다.
모델은 이제 단일 응답을 넘어서 수시간, 수일에 걸쳐 작업을 수행해야 한다.

### 하니스 엔지니어링의 등장
- 모델 자체는 점점 **상품화(commodity)** 되고 있다
- 같은 모델이라도 하니스에 따라 성능이 극적으로 달라진다
- Can Bölük의 실험: edit format(하니스)만 바꿨는데 15개 모델 성능이 **하나의 오후 만에** 개선됨
- **하니스 = 경쟁 우위의 핵심**

> "모델은 엔진이고, 하니스는 자동차다. 아무리 좋은 엔진도 핸들과 브레이크 없이는 쓸모없다."

---

## 2. 하니스(Harness)란?

에이전트 하니스는 **LLM을 감싸는 소프트웨어 인프라** 전체를 의미한다.
모델이 추론과 텍스트 생성을 담당한다면, 하니스는 **그 외의 모든 것**을 담당한다.

### 공식 정의 (parallel.ai)
> "An agent harness is the complete architectural system surrounding an LLM that manages the lifecycle of context: from intent capture through specification, compilation, execution, verification, and persistence."

### 핵심 역할
| 역할 | 설명 |
|------|------|
| 툴 실행 관리 | 모델의 tool call을 감지하고 실제로 실행 |
| 메시지 히스토리 루프 | context window를 관리하며 대화 흐름 유지 |
| 컨텍스트 엔지니어링 로직 | 어떤 정보를 포함/제외할지 결정 |
| 상태 영속성 | 세션 간 작업 상태 유지 |
| 안전 가드레일 | 치명적 실패 방지, 승인 요청 |

---

## 3. 핵심 컴포넌트

### 3.1 툴 통합 레이어 (Tool Integration Layer)
- 외부 API, 데이터베이스, 코드 실행기, 커스텀 툴 연결
- 무한 루프, 캐스케이딩 실패 등 나쁜 패턴 방지
- **올바른 툴을, 올바른 순서로, 올바른 타이밍에**

### 3.2 메모리 & 상태 관리 (Memory & State Management)
- **단기 메모리**: 현재 세션 컨텍스트
- **세션 메모리**: 세션 간 브릿지
- **장기 메모리**: 영구 저장소 (DB, 파일 시스템)
- 컨텍스트 윈도우 고갈 없이 장기 작업 지원

### 3.3 컨텍스트 엔지니어링 (Context Engineering as Harness Responsibility)
하니스가 수행하는 컨텍스트 관리 전략:
- **Context Isolation**: 서브태스크를 분리해 컨텍스트 오염 방지
- **Context Reduction**: 불필요한 정보 압축/삭제 (context rot 방지)
- **Context Retrieval**: 필요한 시점에 관련 정보 동적 주입
- **Context Offloading**: 정보를 외부 시스템으로 이동

### 3.4 계획 & 분해 (Planning & Decomposition)
- 큰 목표를 점진적 서브태스크로 분해
- 구조화된 가이드라인 제공
- 마일스톤 추적 및 재계획

### 3.5 검증 & 가드레일 (Verification & Guardrails)
- 출력 검증, 테스트 실행
- 안전 제약 조건 적용
- Human-in-the-loop: 중요한 결정에서 승인 요청

### 3.6 서브에이전트 조율 (Sub-agent Coordination)
- 복잡한 작업을 전문화된 에이전트들로 분배
- 에이전트 간 통신 관리
- 결과 병합 및 충돌 해결

---

## 4. 컨텍스트 엔지니어링 vs 하니스 엔지니어링

| 구분 | 컨텍스트 엔지니어링 | 하니스 엔지니어링 |
|------|-------------------|-----------------|
| 초점 | 모델에 전달되는 정보 | 모델을 둘러싼 시스템 전체 |
| 범위 | 단일 요청/응답 사이클 | 전체 작업 수명주기 |
| 핵심 문제 | 무엇을 전달할까? | 어떻게 신뢰성 있게 실행할까? |
| 주요 기술 | 프롬프트, RAG, 압축 | 툴 통합, 상태 관리, 오케스트레이션 |
| 적용 범위 | 단기 작업 | 장기/복잡한 작업 |

> **중요**: 컨텍스트 엔지니어링은 하니스의 **한 부분**이다. 하니스가 더 큰 개념.

---

## 5. 2026년의 중요성

### 패러다임 전환
- **2023**: 프롬프트 엔지니어링의 시대
- **2024**: 컨텍스트 엔지니어링의 시대
- **2025**: 에이전트의 시대 (에이전트가 작동한다는 것을 증명)
- **2026**: 하니스 엔지니어링의 시대 (에이전트를 **신뢰성 있게** 작동시키는 것)

### 왜 지금인가?
1. **모델 상품화**: GPT, Claude, Gemini 간 성능 격차 축소 → 하니스가 차별화 요소
2. **장기 작업 수요**: 단순 Q&A → 수시간/수일 걸리는 복잡한 작업
3. **신뢰성 요구**: 데모에서 프로덕션으로 → 안정성, 재현성이 필수
4. **57%의 기업이 에이전트 프로덕션 배포**: 이제는 "작동하는가"가 아니라 "신뢰할 수 있는가"

### 시장 규모
- 2024: $5.40B → 2025: $7.63B → 2030: $50.31B (CAGR 45.8%)

---

## 6. 실제 사례

### 6.1 Claude Code (Anthropic)
- 동일한 모델에 **더 나은 하니스**를 씌워 경쟁 우위 확보
- 자동 컨텍스트 압축(compaction)으로 장기 작업 지원
- 파일시스템 접근 제어, 툴 오케스트레이션

### 6.2 OpenAI Codex + 하니스 엔지니어링
- 3명의 엔지니어가 5개월 만에 **100만 줄** 코드베이스 생성
- 엔지니어 1인당 하루 평균 **3.5 PR** 처리
- "수동으로 입력된 코드 없음(no manually typed code)"을 원칙으로 설정
- 결정론적 커스텀 린터 + LLM 에이전트 조합
- "황금 원칙(golden principles)"을 레포지토리에 직접 인코딩
- 주기적 정리 프로세스: 일관성 유지를 위한 가비지 컬렉션 에이전트

### 6.3 The Harness Problem (Can Bölük, Feb 2026)
**핵심 발견**: 에디트 포맷만 바꿨는데 16개 모델 성능이 극적으로 개선
- `patch` 포맷: 거의 모든 모델에서 최악의 성능
- `string replacement` 포맷: 개선
- **`hashline` 포맷** (혁신): 각 코드 라인에 콘텐츠 해시 태그 부여
  - 모델이 정확한 공백/텍스트 재현 없이 안정적 식별자로 참조
  - 토큰 수 약 20% 감소
  - 일부 모델은 단순 포맷 변경으로 **10배 성능 향상**

---

## 7. 효과적인 하니스 설계 원칙

### 7.1 결정론과 비결정론의 분리
- 결정론적 부분 (린터, 구조 테스트, 경계): 하니스가 담당
- 비결정론적 부분 (추론, 창의성): 모델이 담당

### 7.2 엔트로피 관리
- 코드 decay와의 싸움: 문서 불일치, 아키텍처 위반 자동 감지
- 주기적인 "가비지 컬렉션" 에이전트 실행

### 7.3 반복적 피드백 루프
- 에이전트가 막힐 때 → 누락된 툴/가드레일 식별 → 레포지토리에 피드백
- 레포지토리 자체를 하니스의 컨텍스트 소스로 설계

### 7.4 최소 개입 원칙
- 하니스는 최소한으로 개입하되 치명적 실패는 반드시 방지
- 에이전트 자율성을 최대화하면서 안전망 유지

### 7.5 모듈성
- 인식(Perception), 메모리(Memory), 추론(Reasoning) 모듈을 플러그인 방식으로 교체 가능
- 특정 모델에 종속되지 않는 하니스 설계

---

## 8. 실용적 구현 패턴

### 세션 간 상태 유지
```python
# 각 세션 시작 시 이전 상태 복원
class AgentHarness:
    def __init__(self, task_id: str):
        self.state = self.load_state(task_id)  # 이전 세션 상태
        self.context_manager = ContextManager()
        self.tool_executor = ToolExecutor()

    def run_session(self):
        context = self.context_manager.build_context(self.state)
        result = self.model.invoke(context)
        self.state.update(result)
        self.save_state()  # 다음 세션을 위해 저장
```

### 컨텍스트 압축 전략
```python
class ContextManager:
    def build_context(self, state, max_tokens=100000):
        # 1. 중요도 기반 필터링
        recent = state.get_recent_messages(n=20)
        important = state.get_important_milestones()

        # 2. 오래된 내용 압축
        compressed_history = self.compress(state.old_messages)

        # 3. 현재 태스크 관련 정보만 주입
        task_context = self.retrieve_relevant(state.current_task)

        return self.assemble([important, compressed_history, task_context, recent])
```

---

## 9. 참고 자료

### 핵심 문서
- [Effective harnesses for long-running agents - Anthropic Engineering](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Harness Engineering - Martin Fowler](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html)
- [Harness engineering: leveraging Codex in an agent-first world - OpenAI](https://openai.com/index/harness-engineering/)
- [The importance of Agent Harness in 2026 - Phil Schmid](https://www.philschmid.de/agent-harness-2026)

### 2026년 주요 글
- [2025 Was Agents. 2026 Is Agent Harnesses. - Aakash Gupta](https://aakashgupta.medium.com/2025-was-agents-2026-is-agent-harnesses-heres-why-that-changes-everything-073e9877655e)
- [I Improved 15 LLMs at Coding in One Afternoon. Only the Harness Changed. - Can Bölük](https://blog.can.ac/2026/02/12/the-harness-problem/)
- [Improving Deep Agents with harness engineering - LangChain](https://blog.langchain.com/improving-deep-agents-with-harness-engineering/)

### 관련 개념
- [What is an agent harness? - Parallel.ai](https://parallel.ai/articles/what-is-an-agent-harness)
- [AI Agent Harness, 3 Principles for Context Engineering - Hugo Bowne](https://hugobowne.substack.com/p/ai-agent-harness-3-principles-for)
- [From Context Engineering to AI Agent Harnesses - Delphina High Signal](https://high-signal.delphina.ai/episode/context-engineering-to-ai-agent-harnesses-the-new-software-discipline)

---

## 10. 요약

```
컨텍스트 엔지니어링:  "모델에게 무엇을 줄 것인가?"
하니스 엔지니어링:    "모델이 신뢰성 있게 일하게 하는 시스템 전체를 어떻게 설계할 것인가?"

모델 = 엔진
하니스 = 자동차 전체 (핸들, 브레이크, 내비게이션, 안전벨트 포함)

모델은 상품화된다 → 하니스가 경쟁 우위다
```

> 2026년의 핵심 질문: 같은 모델을 쓰더라도 **누가 더 나은 하니스를 만드는가**?
