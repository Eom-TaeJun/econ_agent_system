# 04. 회의록 브리핑

## 목적

회의록이나 미팅 노트를 NotebookLM에 누적 적재하고
결정사항, 액션아이템, 컨텍스트를 빠르게 파악한다.

---

## notebooklm.google.com에서 수동으로 할 것

1. 새 노트북 생성 (예: "회의록_[프로젝트명]_[분기]")
2. 소스 추가:
   - 회의록 텍스트 파일 또는 Google Docs URL 붙여넣기
   - 새 회의가 생기면 소스 추가
3. 노트북 URL 복사

---

## Claude Code에서 사용하는 MCP 명령어

```
# 노트북 등록
"Add https://notebooklm.google.com/notebook/xxx to library with tag meeting"

# 노트북 선택
"Select notebook with tag meeting"

# 브리핑 질문 예시
"Ask: 지금까지 결정된 사항들을 날짜순으로 정리해줘"
"Ask: 아직 완료되지 않은 액션아이템 목록을 만들어줘"
"Ask: [이름]이 담당하는 업무는 무엇인가?"
"Ask: 이 프로젝트에서 반복적으로 나오는 이슈나 리스크는?"
"Ask: 최근 회의에서 가장 중요한 결정 3가지는?"
```

---

## 예상 출력 형태

- 결정사항 타임라인 표
- 미완료 액션아이템 체크리스트 (담당자 포함)
- 담당자별 업무 요약
- 반복 이슈 리스트
- 최근 핵심 결정 요약
