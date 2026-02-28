# GAMMA AI GENERATION PROMPT: SESSION 3 (Making Rules with Trees)

## GLOBAL SYSTEM INSTRUCTIONS (Gamma Engine 2026)
- **Theme:** "Natural Logic" (Forest Green / Wood Brown / White accents)
- **Style:** "Hierarchical & Intuitive" (Flowcharts, branching diagrams)
- **Typography:** Titles 26pt, Subheaders 17pt, Body 12pt.
- **Image Style:** "Organic Digital" (Digital trees made of data pixels).

---

# [Layout: Title Slide]
# 3차시: 나무로 규칙을 만든다
## 의사결정나무(Decision Tree)와 앙상블의 마법

[Image: A majestic digital tree with glowing leaves, its branches splitting logically into "Yes" and "No" paths. 3D Render.]

- **강사:** [이름 입력]
- **핵심 메시지:** "단순한 나무가 모여 무적의 숲을 이룬다."
- **주요 내용:** 의사결정나무, Bagging, 랜덤 포레스트

---

# [Layout: Split]
# 1. 직선으로 설명 안 되는 세상
[Image: A scatter plot where data points form a complex swirl that a straight line cannot capture.]

- 세상은 선형(Linear)적이지 않습니다.
- "나이가 많을수록 소득이 늘다가, 은퇴 시점에 급감한다" - 이런 꺾이는 패턴은 어떻게 잡을까요?

---

# [Layout: Visual Focus]
# 2. 스무고개: 의사결정나무 ⭐
[Image: A 20-questions game interface. Question: "Is income > $50k?" -> Yes/No.]

- **원리:** 데이터를 가장 잘 가를 수 있는 '질문'을 계속 던집니다.
- **구조:** 뿌리(Root)에서 시작해 잎(Leaf)에서 결론을 내립니다.
- 인공지능이 왜 그런 판단을 했는지 '눈으로 확인'할 수 있는 가장 직관적인 모델입니다.

---

# [Layout: 3-column]
# 3. 의사결정나무의 강력함
[Image: Icons for "Magnifying Glass", "Robot arm", "Human Brain".]

1. **해석 가능:** "소득이 낮고 연체가 있어서 거절됨"이라고 명확히 말해줍니다.
2. **전처리 불필요:** 데이터 스케일을 맞추거나 정규화할 필요가 없습니다.
3. **비선형성:** 복잡하게 꺾인 데이터도 질문을 겹쳐서 해결합니다.

---

# [Layout: Split]
# 4. 나무의 치명적 약점: 불안정성
[Image: A small wind blowing a large tree, making it shake violently.]

- 데이터가 아주 조금만 바뀌어도 나무의 모양이 완전히 뒤바뀝니다.
- **과적합의 제왕:** 끝까지 가지를 뻗으면 데이터를 통째로 외워버립니다.
- 해결책: 가지치기(Pruning)를 통해 적당히 멈춰야 합니다.

---

# [Layout: Focus Card]
# 5. 해결책 1: 집단지성 (Bagging)
[Image: A crowd of diverse experts all voting on a single problem.]

- **아이디어:** 똑똑한 전문가 한 명보다, 평범한 여러 명의 투표가 낫다!
- 데이터를 여러 묶음으로 나누어 여러 개의 나무를 동시에 키웁니다.
- 각 나무의 오답이 서로 상쇄되면서 전체적인 '안정성'이 올라갑니다.

---

# [Layout: Visual Focus]
# 6. 랜덤 포레스트(Random Forest) ⭐
[Image: A lush digital forest where each tree is slightly different but works together.]

- **핵심:** 나무를 만들 때 '데이터'도 랜덤으로 뽑고, '변수'도 랜덤으로 선택합니다.
- 서로 다른 시각을 가진 수백 개의 나무가 투표하여 최종 결론을 냅니다.
- **실무의 수호신:** 대충 돌려도 성능이 잘 나오고 과적합에 매우 강합니다.

---

# [Layout: Split]
# 7. 변수 중요도(Feature Importance)
[Image: A bar chart showing which variables (e.g., Age, Income, Debt) contributed most to the forest's decision.]

- 블랙박스 같던 숲에서도 "어떤 변수가 가장 큰 영향을 미쳤는지" 순위를 매길 수 있습니다.
- 비즈니스 인사이트를 얻는 가장 빠른 방법입니다.

---

# [Layout: Grid]
# 8. 실무 사례: 나무가 하는 일
[Image: Icons for Bank Loan, Medical Diagnosis, E-commerce.]

- **은행:** 대출 승인/거절의 명확한 '규칙' 생성.
- **의료:** 증상에 따른 질병 분류 트리.
- **커머스:** 고객의 구매 경로(Path) 분석.

---

# [Layout: Split]
# 9. 마무리: 나무 하나에서 숲으로
[Image: A single seedling growing into a vast forest.]

- 단순함(Tree)을 연결하여 복잡함(Forest)을 정복합니다.
- 하지만 투표(Bagging)만으로는 부족할 때가 있습니다.
- **다음 차시 예고:** "오답 노트 공부법 - 틀린 것만 패는 Boosting"

---
