# 03. 유튜브 채널 분석

## 목적

유튜브 영상/채널의 트랜스크립트를 NotebookLM에 적재하고
콘텐츠 패턴, 주요 주장, 시리즈 흐름을 분석한다.

---

## notebooklm.google.com에서 수동으로 할 것

1. 새 노트북 생성 (예: "유튜브_[채널명]")
2. 소스 추가:
   - 유튜브 영상 URL 직접 붙여넣기 (NotebookLM이 트랜스크립트 자동 수집)
   - 여러 영상을 한 노트북에 모아서 시리즈 분석 가능
3. 노트북 URL 복사

---

## Claude Code에서 사용하는 MCP 명령어

```
# 노트북 등록
"Add https://notebooklm.google.com/notebook/xxx to library with tag youtube"

# 노트북 선택
"Select notebook with tag youtube"

# 분석 질문 예시
"Ask: 이 채널이 반복적으로 강조하는 핵심 메시지는?"
"Ask: 영상들에서 공통으로 등장하는 키워드 TOP 10을 뽑아줘"
"Ask: 최근 콘텐츠의 논조 변화가 있나? 있다면 어떤 방향으로?"
"Ask: 이 영상에서 제시된 주요 논거와 근거를 정리해줘"
"Ask: 시청자에게 취하라고 권유하는 행동(CTA)은 무엇인가?"
```

---

## 예상 출력 형태

- 핵심 메시지 요약 (3~5개 bullet)
- 키워드 빈도 리스트
- 논조 변화 타임라인
- 논거 구조 정리
- CTA 패턴 분석
