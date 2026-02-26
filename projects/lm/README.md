# NotebookLM 통합 환경

Claude Code에서 NotebookLM을 직접 활용하기 위한 설정 및 워크플로우 모음.

---

## 빠른 명령어 참조

```
# 노트북 추가
"Add [URL] to library with tag [태그]"

# 노트북 목록 확인
"List my notebooks"

# 노트북 선택
"Select notebook [태그 또는 이름]"

# 질문하기
"Ask: [질문 내용]"

# 태그로 검색
"Search notebooks with tag [태그]"

# 재인증 (계정 전환 시)
"Re-authenticate NotebookLM"
```

---

## 파일 구조

```
~/projects/lm/
├── README.md          ← 이 파일
├── notebooks.md       ← 등록된 노트북 목록
└── workflows/
    ├── 01_competitor.md   # 경쟁사 자동 분석
    ├── 02_papers.md       # 논문/보고서 학습
    ├── 03_youtube.md      # 유튜브 채널 분석
    ├── 04_meetings.md     # 회의록 브리핑
    └── 05_consultant.md   # AI 컨설턴트 세팅
```

---

## MCP 서버 상태

- **서버명**: notebooklm
- **설치 명령**: `claude mcp add notebooklm npx notebooklm-mcp@latest`
- **인증**: 첫 사용 시 "Log me in to NotebookLM" → Chrome 브라우저 Google 로그인
- **프로필**: standard (10개 툴, 라이브러리 관리 포함)

---

## 주요 MCP 툴

| 툴 | 용도 |
|----|------|
| `ask_question` | 노트북에 질문 → Gemini 답변 |
| `add_notebook` | 노트북 URL + 태그 저장 |
| `list_notebooks` | 등록된 노트북 목록 확인 |
| `select_notebook` | 현재 작업 노트북 선택 |
| `search_notebooks` | 태그로 노트북 검색 |
| `setup_auth / re_auth` | 계정 전환 시 재인증 |

---

## 검증 체크리스트

- [ ] `claude mcp list` → notebooklm 항목 확인
- [ ] "Log me in to NotebookLM" → 브라우저 인증 성공
- [ ] 테스트 노트북 추가 → `add_notebook` 성공
- [ ] `ask_question` 응답 확인
