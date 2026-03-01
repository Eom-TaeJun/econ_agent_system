# GAMMA AI GENERATION PROMPT: SESSION 2 (The Price of Freedom)

## GLOBAL SYSTEM INSTRUCTIONS (Gamma Engine 2026)
- **Theme:** "Deep Tech Intelligence" (Charcoal Background / Neon Teal Accents)
- **Style:** "Professional & Analytical" (High data density, clean diagrams)
- **Typography:** Titles 26pt, Subheaders 17pt, Body 12pt.
- **Image Style:** "Futuristic Laboratory" or "Abstract Data Physics".
- **Target Audience:** Business Professionals & Junior Data Analysts (Use clear, persuasive, and intuitive language; avoid overly academic jargon).
- **Presentation Goal:** Deliver actionable insights and convince the audience of the core message using the "Reverse Pyramid" principle (Core conclusion first, supporting details next).
- **Constraints & Negative Prompts:** 
  - Do NOT use generic AI buzzwords or cliché corporate stock imagery.
  - Keep bullet points terse (max 2 lines per bullet).
  - Do NOT generate extra filler slides; stick strictly to the outlined headers.
- **Gamma Engine Directives:** Strictly adhere to the `[Layout: ...]` tags. Use optimal visual balancing for text and images.

---

# [Layout: Title Slide]
# 2차시: 자유에는 대가가 따른다
## 과적합(Overfitting)의 함정과 모델 평가의 정석

[Image: A high-tech laboratory with a glowing data model that looks too perfect, almost fragile. Futuristic, 8k resolution.]

- **강사:** [이름 입력]
- **핵심 메시지:** "외우지 말고 이해하라, 모델도 사람도 마찬가지다."
- **주요 내용:** 과적합, Ridge/Lasso, 평가지표의 진실

---

# [Layout: Split]
# 1. 복습: 회귀분석이 다중공선성을 싫어하는 이유
[Image: Two gears grinding against each other, labeled X1 and X2, causing a machine to smoke.]

- **수학적 고집:** 변수 간 연관성이 높으면 계수(Coefficient)가 요동칩니다.
- **해석의 불가능:** "키가 커서 몸무게가 느는 건지, 몸무게가 늘어서 키가 크는 건지" 알 수 없습니다.
- **ML의 태도:** "설명은 됐고, 결과만 맞으면 된다"는 전환이 여기서 시작됩니다.

---

# [Layout: Visual Focus]
# 2. 자유의 대가: 과적합(Overfitting) ⭐
[Image: A student intensely memorizing a specific exam paper instead of studying the textbook. Split screen: Exam Paper vs. Real World Problem.]

- **정의:** 학습 데이터는 100점, 하지만 새로운 데이터는 빵점.
- **원인:** 모델이 데이터의 '본질'이 아닌 '노이즈'를 외워버렸기 때문입니다.
- **비유:** 기출문제 정답만 외운 학생은 숫자 하나만 바뀌어도 틀립니다.

---

# [Layout: 2-column]
# 3. 규제화(Regularization)의 등장
[Image: A gardener pruning a wild overgrown bush into a clean shape.]

- **철학:** "너무 복잡한 수식은 만들지 마라!"
- **방법:** 오차를 줄이는 것뿐만 아니라, **계수(Beta)의 크기도 함께 줄입니다.**
- 수식이 단순해지면, 모델은 더 유연해집니다.

---

# [Layout: Split]
# 4. Ridge: 모든 변수를 품고 가다
[Image: A group of people all holding a heavy bar, sharing the weight equally.]

- **특징:** 모든 변수를 유지하되, 영향력(계수)을 0에 가깝게 억제합니다.
- **효과:** 변수가 많고 대부분이 조금이라도 의미가 있을 때 유리합니다.
- **이미지:** 골고루 누르는 압력.

---

# [Layout: Split]
# 5. Lasso: 냉정한 변수 선택
[Image: A hand pointing at a group, choosing only the most important person and removing the rest.]

- **특징:** 중요하지 않은 변수의 계수를 **정확히 0**으로 만듭니다.
- **효과:** 불필요한 변수를 자동으로 제거하는 '변수 선택' 기능이 있습니다.
- **이미지:** 날카로운 칼날로 불필요한 가지치기.

---

# [Layout: Visual Focus]
# 6. Bias-Variance Tradeoff ⭐
[Image: A target board with four scenarios: Low/High Bias vs Low/High Variance. Clean 3D infographic.]

- **Bias(편향):** 모델이 너무 단순해서 생기는 오차.
- **Variance(분산):** 모델이 너무 예민해서 생기는 오차.
- **최적의 지점:** 둘 사이의 균형을 찾는 것이 ML 엔지니어의 핵심 역량입니다.

---

# [Layout: Split]
# 7. 데이터의 삼분할: Train / Val / Test
[Image: A box of cookies split into three parts: 60% Eat, 20% Taste, 20% Save for later.]

- **Train:** 공부하는 단계 (문제집).
- **Validation:** 모의고사 단계 (방향 수정).
- **Test:** 실전 수능 (딱 한 번만!).
- **주의:** Test 데이터를 미리 보는 순간, 그 모델은 오염됩니다 (Data Leakage).

---

# [Layout: Grid]
# 8. 분류(Classification)의 세계로
[Image: A sorting machine dividing apples into "Good" and "Bad" bins.]

- 숫자를 맞히는 '회귀'와 달리, '종류'를 결정합니다.
- 예: 스팸인가? 암인가? 부도날 고객인가?

---

# [Layout: Table]
# 9. 혼동 행렬 (Confusion Matrix)

| 구분 | 예측: Positive | 예측: Negative |
|---|---|---|
| **실제: Positive** | TP (정답) | FN (놓침) |
| **실제: Negative** | FP (오답) | TN (정답) |

- 정확도(Accuracy)의 함정: 99명이 정상인 세상에서 무조건 '정상'이라 하면 정확도는 99%입니다.

---

# [Layout: Split]
# 10. 재현율(Recall) vs 정밀도(Precision)
[Image: Left: A doctor missing a patient (Recall). Right: A police officer arresting an innocent person (Precision).]

- **Recall:** "암 환자를 한 명도 놓치면 안 된다" (의료).
- **Precision:** "무고한 사람을 범인으로 잡으면 안 된다" (법적 판단).
- 비즈니스 목적에 따라 어떤 지표를 중시할지 결정해야 합니다.

---

# [Layout: Big Number]
# 11. AUC-ROC: 모델의 기본 체력
[Image: A curved graph showing the trade-off between sensitivity and specificity.]

- 특정 임계값에 상관없이 모델이 얼마나 '분류 능력'이 좋은지 보여주는 점수입니다.
- 실무에서 가장 많이 참조하는 지표 중 하나입니다.

---

# [Layout: Focus Card]
# 12. 실무 함정: Data Leakage
[Image: A crystal ball showing future stock prices hidden behind a wall.]

- 미래의 정보가 학습 데이터에 몰래 들어오는 현상.
- **예:** 오늘 종가를 맞히는데 내일 뉴스를 데이터에 넣은 격.
- 결과가 너무 좋으면(99.9%), 반드시 의심해야 합니다.

---

# [Layout: Split]
# 13. 마무리: 자유의 대가는 '검증'이다
[Image: A scale weighing "Freedom" against "Responsibility".]

- 머신러닝의 자유는 강력하지만, 검증되지 않은 모델은 독이 됩니다.
- **다음 차시 예고:** "직선으로 안 되는 세상 - 나무로 규칙을 만든다"

---
