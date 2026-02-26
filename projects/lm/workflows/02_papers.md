# 02. 논문/보고서 학습

## 목적

읽어야 할 논문이나 산업 보고서를 NotebookLM에 적재하고
핵심 개념, 방법론, 결론을 빠르게 추출한다.

---

## notebooklm.google.com에서 수동으로 할 것

1. 새 노트북 생성 (예: "논문_[주제]_[날짜]")
2. 소스 추가:
   - PDF 직접 업로드 (논문, 보고서)
   - arXiv/SSRN URL 붙여넣기
   - Google Scholar 링크 붙여넣기
3. 노트북 URL 복사

---

## Claude Code에서 사용하는 MCP 명령어

```
# 노트북 등록
"Add https://notebooklm.google.com/notebook/xxx to library with tag paper"

# 노트북 선택
"Select notebook with tag paper"

# 학습 질문 예시
"Ask: 이 논문의 핵심 주장과 기여를 3문장으로 요약해줘"
"Ask: 연구 방법론을 설명해줘. 어떤 데이터를 어떻게 분석했나?"
"Ask: 한계점과 저자가 언급한 future work는?"
"Ask: 실무에 적용 가능한 인사이트 3가지를 추출해줘"
"Ask: 이 연구와 관련된 핵심 개념들을 용어집 형태로 정리해줘"
```

---

## 예상 출력 형태

- 논문 3줄 요약
- 방법론 다이어그램 설명
- 한계점 bullet 리스트
- 실무 적용 포인트 3~5개
- 핵심 용어집
