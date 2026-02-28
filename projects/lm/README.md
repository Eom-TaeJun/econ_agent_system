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
- **구현체**: [alfredang/notebooklm-mcp](https://github.com/alfredang/notebooklm-mcp) (2026-02 교체)
- **설치 경로**: `~/projects/lm/notebooklm-mcp/`
- **실행**: `uv --directory ~/projects/lm/notebooklm-mcp run python server.py`
- **인증**: `cd ~/projects/lm/notebooklm-mcp && uv run notebooklm login`
- **인증 데이터**: `~/.notebooklm/` (브라우저 프로파일 저장)
- **전환 이유**: 노트북 생성·소스 추가·컨텐츠 생성(팟캐스트·슬라이드 등) 지원

> 이전 버전 (PleasePrompto/notebooklm-mcp): 질문·라이브러리 관리만 가능했음

---

## 주요 MCP 툴

| 툴 | 용도 |
|----|------|
| `ask_question` | 노트북에 질문 → Gemini 답변 |
| `list_notebooks` | 계정 내 노트북 목록 조회 |
| `create_notebook` | 새 노트북 생성 |
| `add_source` | URL·텍스트 소스 추가 |
| `generate_podcast` | 팟캐스트 오디오 생성 |
| `generate_slides` | 슬라이드 생성 |
| `generate_mindmap` | 마인드맵 생성 |
| `generate_quiz` | 퀴즈·플래시카드 생성 |

---

## 검증 체크리스트

- [x] Google Chrome WSL2 설치 (`/usr/bin/google-chrome-stable`)
- [x] alfredang/notebooklm-mcp 설치 (`uv sync`)
- [x] NotebookLM 인증 완료 (`uv run notebooklm login`)
- [x] 서버 기동 테스트 통과
- [ ] Claude Code 재시작 후 MCP 연결 확인
