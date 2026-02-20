# Design System — Master

모든 프로젝트의 상위 디자인 규칙 저장소.

## 파일 구조

```
design-system/
├── web-design-system.md          ← AI에게 주입할 마스터 규칙 (skill 파일)
├── tailwind.config.template.js   ← tailwind 설정 템플릿
└── README.md
```

## 새 프로젝트 적용 방법

```bash
# 1. 프로젝트 skills 디렉토리에 복사
cp web-design-system.md ../{프로젝트}/.claude/skills/web-design-system.md

# 2. 복사한 파일에서 교체할 것
#    - 섹션 1: PRIMARY / SECONDARY 헥스코드
#    - 섹션 9: 레퍼런스 스타일 묘사

# 3. tailwind.config.js 교체
cp tailwind.config.template.js ../{프로젝트}/tailwind.config.js
#    - colors.primary / colors.secondary 값만 교체
```

## 색상 가이드라인

| 용도 | 사용처 |
|------|--------|
| primary | CTA 버튼, 링크, 활성 상태, 강조 |
| secondary | 긍정 지표, 상승, 성공, 완료 |
| gray 계열 | 텍스트, 배경, 테두리, 구분선 |

## 버전 관리

마스터 규칙 수정 시:
1. 이 파일 version 업데이트
2. 각 프로젝트 skills/ 파일에 변경사항 수동 반영
3. 커밋 메시지에 `design-system: vX.X.X` 태그

## 현재 적용 프로젝트

- [ ] eimas — 적용 예정
