# Job Assistant — 확장 설계 문서

> 작성: 2026-03-02
> 목적: 기업 공고 입력 → 다각도 수집 → NotebookLM 업로드까지 자동화
> 원칙: 방향성 제시. 하드코딩 금지. 각 레이어는 교체 가능해야 한다.

---

## 현재 파이프라인

```
JobContext(company, role)
  → SearchAgent    (Perplexity: 공고·비전·현업)
  → AnalyzerAgent  (Claude: 구조화 분석)
  → WriterAgent    (Claude: 자소서 초안)
```

---

## 확장 파이프라인 (목표)

```
JobContext(company, role, url?)
  → CollectorAgent   (멀티소스 수집)
      ├── Perplexity : JD, 비전, 현업, 인터뷰, 합격수기
      ├── WebFetch   : 공식 채용 페이지, 뉴스
      └── 수동 업로드: PDF 리포트, 내부 문서
  → SummarizerAgent  (멀티모델 요약)
      ├── OpenAI GPT : 긴 원문 → 핵심 압축
      ├── Gemini     : 합격수기 패턴 추출
      └── Claude     : 전략 분석 (지원자 fit 매핑)
  → NotebookPublisher (NotebookLM 업로드)
      ├── 소스 1: JD + 회사 전략
      ├── 소스 2: 현업 인터뷰 + 합격수기
      ├── 소스 3: 지원자 프로필 매핑
      └── 소스 4: 업계 맥락 리포트
  → [기존] WriterAgent (자소서 초안)
```

---

## 1. CollectorAgent — 수집 레이어

### 역할
회사 + 직무를 받아 **4가지 카테고리**의 콘텐츠를 병렬 수집.

### 수집 카테고리

| 카테고리 | 수집 대상 | 검색 방법 |
|---------|---------|---------|
| `JD`     | 채용공고 전문, 자격요건, 우대사항 | Perplexity, URL 직접 |
| `COMPANY`| 회사 비전, 인재상, 최근 뉴스, 사업 방향 | Perplexity |
| `INSIDER`| 현직자 인터뷰, 현업 일과, 팀 문화 | Perplexity (블라인드·링크드인·유튜브 포함) |
| `SUCCESS`| 합격수기, 면접 후기, 코딩테스트 패턴 | Perplexity (취준커뮤니티 타겟) |

### 설계 원칙
- 카테고리별 쿼리 템플릿을 `query_templates.py`로 분리
- 쿼리 결과는 `raw_content: Dict[category, str]`로 저장
- 실패한 카테고리는 건너뛰고 기록 (필수 아님)

### 쿼리 템플릿 방향 (예시)

```python
QUERY_TEMPLATES = {
    "JD": [
        "{company} {role} 채용공고 자격요건 우대사항",
        "{company} {role} JD 직무기술서 2025 2026",
    ],
    "COMPANY": [
        "{company} 회사 비전 인재상 핵심가치 조직문화",
        "{company} 최근 사업 방향 전략 2025 2026",
    ],
    "INSIDER": [
        "{company} {role} 현직자 인터뷰 실제 업무 하루 일과",
        "{company} {role} 블라인드 팀문화 워라밸 업무강도",
    ],
    "SUCCESS": [
        "{company} {role} 합격 후기 자소서 면접 질문",
        "{company} 인턴 합격 스펙 자소서 팁 취준 커뮤니티",
    ],
}
```

---

## 2. SummarizerAgent — 요약 레이어

### 역할
수집된 raw content를 **모델별 특성에 맞게** 요약, NotebookLM 소스 형태로 변환.

### 모델 분담 원칙

| 작업 | 추천 모델 | 이유 |
|------|---------|------|
| 긴 원문 압축 (합격수기 다수) | OpenAI GPT-4o-mini | 빠르고 저렴, 요약 품질 좋음 |
| 패턴 추출 (면접 질문 공통점) | Gemini 2.0 Flash | 구조화 추출 강점 |
| 지원자 fit 매핑, 전략 분석 | Claude Sonnet | 맥락 이해 + 긴 추론 |
| 단순 정리·포맷팅 | Claude Haiku | 비용 절감 |

### 출력 형식
각 카테고리별로 NotebookLM에 올릴 수 있는 텍스트 블록 생성.

```python
@dataclass
class SummarizedSource:
    title: str          # NotebookLM 소스 제목
    content: str        # 업로드할 텍스트
    category: str       # JD / COMPANY / INSIDER / SUCCESS
    model_used: str     # 어떤 모델로 요약했는지 기록
```

---

## 3. NotebookPublisher — NotebookLM 업로드 레이어

### 역할
SummarizedSource 목록을 받아 NotebookLM 노트북 생성 + 소스 일괄 업로드.

### 노트북 구성 원칙
고정 소스 4개 구조:

| 소스 번호 | 내용 | 생성 주체 |
|----------|------|---------|
| 소스 1 | JD + 회사 비전·전략 | CollectorAgent |
| 소스 2 | 현직자 인터뷰 + 합격수기 패턴 | CollectorAgent + SummarizerAgent |
| 소스 3 | 지원자 프로필 × 직무 매핑 | Claude (AnalyzerAgent) |
| 소스 4 | 업계 맥락 (선택: 리포트·뉴스) | 수동 or Perplexity |

### 인터페이스 방향

```python
class NotebookPublisher:
    def publish(self, company: str, role: str,
                sources: List[SummarizedSource]) -> str:
        """노트북 생성 후 notebook_id 반환"""
        ...

    def add_manual_source(self, notebook_id: str,
                          file_path: str) -> None:
        """PDF 등 수동 소스 추가"""
        ...
```

---

## 4. 데이터 모델 확장

기존 `JobPosting`, `Analysis` 유지하면서 추가:

```python
@dataclass
class CollectedContent:
    """카테고리별 수집 원문"""
    company: str
    role: str
    raw: Dict[str, str]          # category → raw text
    sources_used: List[str]      # 어떤 수집기 사용했는지

@dataclass
class NotebookResult:
    """NotebookLM 업로드 결과"""
    notebook_id: str
    notebook_title: str
    sources: List[SummarizedSource]
    created_at: str
```

---

## 5. 전체 흐름 조율 (main.py 확장)

```python
# 현재
context → search → analyze → write

# 목표
context
  → collect(company, role)          # Perplexity 멀티쿼리
  → summarize(raw_content)          # OpenAI/Gemini/Claude 분담
  → publish_notebook(summarized)    # NotebookLM 업로드
  → analyze(posting)                # Claude: fit 분석
  → write(analysis)                 # Claude: 자소서 초안
```

플래그로 단계 선택 가능하게:
```bash
python main.py --company "PwC컨설팅" --role "RA인턴" --steps collect,summarize,notebook
python main.py --company "신한투자증권" --role "해외주식팀RA" --steps all
```

---

## 6. 구현 우선순위

| 순위 | 작업 | 이유 |
|------|------|------|
| 1 | `CollectorAgent` 확장 (SUCCESS, INSIDER 쿼리 추가) | 당장 쓸 수 있음 |
| 2 | `NotebookPublisher` 신규 구현 | 노트북 자동화 핵심 |
| 3 | `SummarizerAgent` (OpenAI/Gemini 분담) | 수집 품질 향상 |
| 4 | `main.py` 플래그 방식으로 단계 선택 | 유연성 확보 |

---

## 7. 설정 확장 (config.py)

```python
# 추가 필요
MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "perplexity": "sonar-pro",
    "openai": "gpt-4o-mini",       # 요약용
    "gemini": "gemini-2.0-flash",  # 패턴 추출용
}

API_CONFIG:
    openai_key: str
    gemini_key: str
```

---

## 메모

- Perplexity는 실시간 웹 검색이 핵심 → 합격수기·인터뷰는 여기서
- OpenAI/Gemini는 이미 수집된 텍스트 요약에만 사용 (검색 안 함)
- Claude는 지원자 fit 판단 같은 맥락 추론에 집중
- NotebookLM MCP는 현재 연결되어 있으므로 Python SDK 대신 MCP 직접 활용 가능
