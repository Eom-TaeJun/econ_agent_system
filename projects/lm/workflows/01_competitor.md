# 01. 경쟁사 자동 분석

## 목적

경쟁사의 IR 자료, 공시, 뉴스 기사를 NotebookLM에 모아두고
Claude Code에서 구조화된 분석 질문을 던져 인사이트를 추출한다.

---

## notebooklm.google.com에서 수동으로 할 것

1. 새 노트북 생성 (예: "경쟁사분석_[회사명]_[연도]")
2. 소스 추가:
   - 경쟁사 IR 발표 자료 PDF 업로드
   - 공시 페이지 URL 붙여넣기
   - 관련 뉴스 기사 URL 붙여넣기
3. 노트북 URL 복사

---

## Claude Code에서 사용하는 MCP 명령어

```
# 노트북 등록
"Add https://notebooklm.google.com/notebook/xxx to library with tag competitor"

# 노트북 선택
"Select notebook with tag competitor"

# 분석 질문 예시
"Ask: 이 회사의 핵심 수익 모델은 무엇이고, 전년 대비 어떻게 변했나요?"
"Ask: 경쟁사가 강조하는 기술 차별점 3가지를 요약해줘"
"Ask: 리스크 요인과 회사의 대응 전략을 정리해줘"
"Ask: 향후 12개월 성장 전략은?"
```

---

## 예상 출력 형태

- 수익 모델 변화 요약 (표 또는 bullet)
- 기술 차별점 3~5개 리스트
- 리스크 매트릭스 (발생 가능성 × 영향도)
- 전략 방향 한 단락 요약
