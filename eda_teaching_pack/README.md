# EDA Training Pack

## 1) 목표
이 패키지는 학습자가 아래 핵심 개념을 "코드 암기"가 아니라 "전후 비교"로 이해하도록 설계되었습니다.

- 데이터 전처리
- 결측치 진단/처리
- 이상치 탐지/처리
- 시각화 기반 인사이트 도출

## 2) 권장 데이터셋

- 이름: Seoul Bike Sharing Demand
- 특징: 시간 변수 + 날씨 변수 + 수요 타깃이 함께 있어 EDA와 시각화 학습에 적합
- 권장 파일 구성:
  - `data/raw_clean.csv` (원본)
  - `data/raw_dirty.csv` (결측치/이상치를 일부 주입한 학습용)

## 3) 패키지 구성

- `assignment.md`: 과제 본문(문항 10개)
- `concept_cards.md`: 키워드 개념 카드(왜/언제/결과)
- `expected_output.md`: 제출물 예시 포맷과 전후 비교 예시
- `rubric.md`: 채점 기준
- `starter.ipynb`: 학습자용 TODO 노트북(정답 코드 없음)
- `instructor_guide.md`: 강의자용 진행/피드백 가이드
- `scripts/make_dirty_dataset.py`: `raw_clean.csv` -> `raw_dirty.csv` 생성기

## 4) 운영 방식(권장)

1. 학습자에게 `raw_dirty.csv`만 먼저 제공
2. 과제 문항 순서대로 전처리 및 시각화 수행
3. 처리 전/후를 같은 질문으로 비교
4. 마지막에 인사이트와 한계 정리

## 5) 강의자 운영 팁

- 정답 코드는 공개하지 말고, 함수 인터페이스와 평가 기준만 공개합니다.
- 그래프는 반드시 `Before`/`After`를 같은 축으로 비교하게 합니다.
- "좋아졌다" 대신 "무엇이 얼마나 변했다"를 숫자로 작성하게 합니다.

## 6) dirty 데이터 생성 예시

```bash
python scripts/make_dirty_dataset.py \
  --input data/raw_clean.csv \
  --output data/raw_dirty.csv \
  --missing-rate 0.03 \
  --outlier-rate 0.01 \
  --duplicate-rate 0.005 \
  --datetime-cols Date \
  --category-corrupt-rate 0.01 \
  --non-negative-cols Rainfall,Snowfall \
  --seed 42
```

## 7) 배포용 문서 변환 (MD -> DOCX/PDF)

- 배포용 초안 MD:
  - `publish/md/01_problem_sheet_draft.md`
  - `publish/md/02_example_and_rubric_draft.md`
  - `publish/md/03_solution_guide_draft.md`
- 변환 스크립트:
  - `scripts/export_publish_docs.py`
- 출력 폴더:
  - `publish/docx/`
  - `publish/pdf/`

실행 예시:

```bash
python scripts/export_publish_docs.py
```
