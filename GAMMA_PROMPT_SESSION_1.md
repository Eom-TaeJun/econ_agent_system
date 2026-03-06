# GAMMA AI GENERATION PROMPT: SESSION 1 (Why ML?)

## GLOBAL SYSTEM INSTRUCTIONS (Gamma Engine 2026)
- **Theme:** "Professional Modern Deep Tech" (Dark Slate / Indigo accents)
- **Style:** "Storytelling with Data Density" (Clean, high contrast, minimalist)
- **Typography Hierarchy:** 
  - Slide Titles: 28pt Bold (Tracking -2%)
  - Subheaders: 18pt Semibold
  - Body Text: 12pt Regular (Leading 1.6)
  - Footnotes/Sources: 9pt Italic
- **Layout Logic:** Prioritize 2-column or Grid layouts for "Vs." comparisons.
- **Image Engine:** Use "Photorealistic" or "Clean 3D Isometric" style.
- **Language:** Korean (Primary) with English technical terms in brackets.
- **Target Audience:** Business Professionals & Junior Data Analysts (Use clear, persuasive, and intuitive language; avoid overly academic jargon).
- **Presentation Goal:** Deliver actionable insights and convince the audience of the core message using the "Reverse Pyramid" principle (Core conclusion first, supporting details next).
- **Constraints & Negative Prompts:** 
  - Do NOT use generic AI buzzwords or cliché corporate stock imagery.
  - Keep bullet points terse (max 2 lines per bullet).
  - Do NOT generate extra filler slides; stick strictly to the outlined headers.
- **Gamma Engine Directives:** Strictly adhere to the `[Layout: ...]` tags. Use optimal visual balancing for text and images.

---

# [Layout: Title Slide]
# 1차시: 왜 머신러닝(ML)인가?
## 통계학에서 에이전틱 AI까지의 여정

[Image: A professional baseball stadium at night, focused on a pitcher's hand holding a glowing digital baseball, representing data in sports. Photorealistic, cinematic lighting.]

- **강사:** [이름 입력]
- **핵심 메시지:** "질문하는 사람만이 도구를 지배한다"
- **2026 ML 파이프라인 가이드**

---

# [Layout: Split]
# 1. 우리는 왜 분석을 하는가?
[Image: A sleek, professional dashboard showing raw data transforming into a glowing, persuasive insight or chart. Clean 3D Isometric style.]

### "데이터로 타인을 설득하기 위하여"

- **분석의 본질:** 선형회귀(Linear Regression)든 머신러닝(ML)이든, 결국 데이터로 내 주장을 증명하고 타인을 설득하는 과정입니다.
- **설득의 과정:** 이를 위해 우리는 데이터를 수집하고, 그 안에서 숨겨진 패턴을 발견해 냅니다.
- **우리의 목표:** 화려한 기법에 매몰되지 않고, 분석 결과를 비즈니스 언어로 번역해 설득하는 법을 배웁니다.

> **→ 실무에서는:** "왜 이런 결과가 나왔나?"에 대해 숫자로 증명된 명확한 근거(Prescription)를 제시해야 합니다.

---

# [Layout: Timeline]
# 2. 10년의 여정: 도구는 변해도 본질은 같다
[Image: A clean minimalist timeline from 2016 to 2026. 2016: R/Statistics, 2020: Python/Scikit-learn, 2023: LLM/Prompt, 2026: Agentic AI.]

- **2016:** 인터넷 서칭과 기초 R 회귀분석의 시대
- **2023:** GPT와 대화하며 코드를 짜는 시대
- **2026:** 에이전틱 AI와 시각화 설득의 시대

**"도구는 계속 바뀌었지만, 제가 던지는 질문은 똑같았습니다."**
- "이 패턴이 진짜 맞나?"
- "이 예측을 믿을 수 있나?"
- "왜 이렇게 나왔을까?"

---

# [Layout: 2-column]
# 3. 도구는 수단일 뿐, 목적은 하나
[Image: Left: A toolbox icon. Right: A bullseye target icon with the word "PERSUASION".]

### 우리가 배울 도구들
- EDA (데이터 진단)
- Linear Regression (기초)
- Decision Tree / Random Forest
- XGBoost (실무 표준)
- SHAP (해석과 설득)

### 단 하나의 목적: "설득"
- 문제를 데이터로 풀고, 그 과정을 남에게 설득하는 것.
- **ML은 도구일 뿐, 핵심은 당신의 논리입니다.**

---

# [Layout: Grid]
# 4. 오늘 아침 AI가 내린 결정들
[Image: Three icons in a grid: Youtube Logo, Credit Card with alert, Navigation Map.]

- **유튜브 추천:** "이 사람이 이 주제를 좋아할 것 같다"
- **이상거래 탐지(FDS):** "이 카드는 주인이 쓰는 게 아닐 것 같다"
- **내비게이션:** "이 길이 5분 더 빠를 것 같다"

**공통점:** 모두 '기계가 내린 예측'입니다.
- **실무 데이터:** 2024년 기준 금융기관 95% 이상이 FDS를 AI로 처리합니다.

---

# [Layout: Big Number]
# 5. 데이터 폭발: 120 제타바이트(ZB)
[Image: An immense digital ocean made of data bits, showing the scale of a Zettabyte.]

- **하루 데이터 생성량:** 영화 7조 2천억 편 분량.
- **혁명의 토양:** 데이터 폭증 + GPU 연산력 혁명.
- 과거엔 서버비 때문에 못 했던 분석을 이제 누구나 할 수 있습니다.

---

# [Layout: Split]
# 6. 통계학(선형회귀)의 엄격함과 그 한계
[Image: A chalkboard with complex formulas vs a computer screen with a neural network.]

### 설명과 계산량의 딜레마
- **다중공선성(Multicollinearity):** 선형회귀는 변수끼리 상관성이 높으면 설명력이 왜곡되고 계산량이 폭증하여 이를 극도로 꺼려했습니다.
- **엄격한 가정:** 완벽한 원인 규명을 추구하다 보니, 변수가 100개만 넘어가도 사람이 수식을 제어하기 불가능해졌습니다.

### 머신러닝(ML)의 파격적 발상
- "다중공선성? 상관없다. 복잡한 수식 설명은 기계에 맡기고, 우리는 압도적인 **예측**에만 집중하자."

---

# [Layout: Focus Card]
# 7. ML의 정의: 스스로 배우는 기계
[Image: A brain icon connected to gear icons, with data flowing in and predictions flowing out.]

- **ML의 핵심:** 인간이 수식을 세우지 않고, 기계가 가중치를 스스로 조정함.
- **블랙박스(Black Box):** 내부 수식은 복잡하지만, 결과값(Prediction)은 정확함.

> **비유:** 통계학은 '의사'(원인 규명), ML은 '주술사'(경험적 적중).

---

# [Layout: Visual Focus]
# 8. 무릎이 아프면 비가 온다
[Image: An elderly person's knee on the left, a rainy window on the right. An arrow in the middle says "Correlation".]

### 상관관계(Correlation) ≠ 인과관계(Causality)
- 무릎이 아파서 비가 오는 것이 아닙니다.
- **진짜 원인:** 기압 저하 → 관절 활액 팽창 → 통증 & 비.
- **ML의 함정:** 상관관계를 인과로 착각하는 순간 비즈니스는 실패합니다.

---

# [Layout: Split]
# 9. 상관에서 인과로 가는 4단계
[Image: A 4-step staircase icon. 1: Observe, 2: Hypothesize, 3: Experiment, 4: Conclude.]

1. **상관 발견:** 무릎 통증 관찰.
2. **가설 설정:** "기압 때문 아닐까?"
3. **실험 검증:** 기압만 변화시켜보기.
4. **인과 확정:** 메커니즘 증명.

**"ML로 예측하고, 통계로 검증한다."**

---

# [Layout: Table]
# 10. 통계학 vs 머신러닝 (ML)

| 구분 | 통계학 (Stats) | 머신러닝 (ML) |
|---|---|---|
| **목표** | 왜(Why)? - 인과 규명 | 얼마나(How)? - 예측 최적화 |
| **방법** | 가설 → 수식 → 검증 | 데이터 → 패턴 → 예측 |
| **장점** | 설명 가능성 높음 | 예측력 압도적 |
| **단점** | 대량 데이터 취약 | 블랙박스 (설명 불가) |

---

# [Layout: Split]
# 11. 기계가 허용한 성과, 그리고 '블랙박스'의 오해
[Image: A sophisticated crystal cube showing intricate, glowing neural pathways inside, demonstrating transparency. Photorealistic, cinematic lighting.]

### 다중공선성을 무시한 대가
- **압도적 예측력:** 1,000개가 넘는 변수가 서로 겹치고 연관되든 말든, 거뜬히 처리하여 최고의 예측값을 냅니다.
- **과거의 오해 (블랙박스):** 한때 ML은 "예측은 잘하는데 왜 그런지 설명은 못 하는 맹의(블랙박스)"로 치부되었습니다.

### 2026년의 ML은 더 이상 블랙박스가 아니다
- **투명해진 내부:** 이제 SHAP과 같은 설명 가능한 AI(XAI) 기법들로 모델 내부를 열어볼 수 있습니다. 
- 복잡한 수식과 다중공선성의 제약을 벗어난 막강한 **예측력**을 누리면서도, 어떤 이유로 결정되었는지 **설명하고 설득**할 수 있게 되었습니다.

---

# [Layout: 2x2 Matrix]
# 12. ML 질문 지도: 당신의 질문은?
[Image: A 2x2 matrix. X-axis: Goal (Regression vs Classification), Y-axis: Necessity (Discovery vs Prediction).]

1. **회귀 (Regression):** "얼마나?" (숫자 예측)
2. **분류 (Classification):** "어떤 종류?" (스팸/정상)
3. **군집 (Clustering):** "어떤 그룹?" (고객 세분화)
4. **해석 (Interpretability):** "왜?" (근거 설명)

---

# [Layout: Grid]
# 13. 실제 실무 사례 (Use Cases)
[Image: Icons for Finance, Marketing, Medical, and Sports.]

- **금융:** 신용 리스크 및 대출 거절/승인 판단.
- **마케팅:** 고객 이탈(Churn) 방지 쿠폰 발송.
- **의료:** 암 진단 보조 및 재입원 위험 분석.
- **스포츠:** 선수 기용 전술 및 성과 예측.

---

# [Layout: Split]
# 14. LLM 시대에도 ML인가? (Yes!)
[Image: A massive GPT icon next to a structured Excel spreadsheet.]

- **이유 1 (Table Data):** 실무 데이터의 80%는 여전히 표(Excel) 형태이며, ML이 훨씬 정확함.
- **이유 2 (Cost):** LLM은 비싸고 느리지만, ML(XGBoost)은 싸고 빠름.
- **이유 3 (Explainability):** 금융/의료 법적 규제 대응에는 ML+SHAP 조합이 필수.

---

# [Layout: Big Number]
# 15. 2026 신호: 에이전틱 AI 급증
[Image: A robot hand controlling multiple digital tools simultaneously.]

- **Gartner 보고:** 멀티에이전트 관련 문의 **1,445% 증가**.
- 분석가가 3주 걸리던 일을 에이전트가 2시간 만에 완료.
- **핵심:** 이 모든 에이전트의 '눈'과 '뇌'는 ML 예측 모듈입니다.

---

# [Layout: Visual Focus]
# 16. ML이 AI 시스템의 부품이 된다
[Image: A modular diagram. Agent Brain -> ML Module (Prediction) -> Tool Execution (Email/DB).]

- **에이전트 로직:** 의도 파악 → 정보 식별 → **ML 모듈 호출**.
- **ML의 역할:** "이 고객은 87% 확률로 이탈한다"는 판단 제공.
- **ML이 없으면 에이전트는 맹목입니다.**

---

# [Layout: Split]
# 17. 예고: 자유에는 대가가 따른다
[Image: A student memorizing an answer sheet vs a student understanding the principle.]

- **자유:** "뭐든 시도해봐, 예측만 잘하면 돼."
- **대가 (함정):** 
  - **과적합:** 데이터를 외워버린 모델.
  - **편향:** 차별을 학습한 AI.
  - **상관-인과 혼동:** 효과 없는 쿠폰 발송.

---

# [Layout: Focus Card]
# 18. 마무리: 질문하는 습관
[Image: A person looking at a digital horizon through a question mark shaped portal.]

- **핵심 1:** ML은 데이터에서 패턴을 찾는 도구다.
- **핵심 2:** 상관은 인과가 아니다. 속지 마라.
- **핵심 3:** 함수를 외우지 말고, "이 도구가 왜 필요한가?"를 물어라.

**"다음 시간: 자유가 만드는 첫 번째 함정 — 과적합"**

---
