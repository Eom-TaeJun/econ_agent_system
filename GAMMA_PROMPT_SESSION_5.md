# GAMMA AI GENERATION PROMPT: SESSION 5 (The Complete System)

## GLOBAL SYSTEM INSTRUCTIONS (Gamma Engine 2026)
- **Theme:** "System Intelligence & Ethics" (Deep Midnight Blue / Gold / Ivory)
- **Style:** "Strategic & Visionary" (Waterfall charts, system architecture, clarity)
- **Typography:** Titles 26pt, Subheaders 17pt, Body 12pt.
- **Image Style:** "Architectural Logic" or "Crystalline Clarity" (Golden keys, transparent layers).

---

# [Layout: Title Slide]
# 5차시: 설명할 수 있어야 쓸 수 있다
## 데이터 진단(EDA)부터 에이전틱 AI 통합까지의 완결

[Image: A grand architectural blueprint of an AI system where data flows through transparent pipes, becoming clear decisions. Cinematic, 8k.]

- **강사:** [이름 입력]
- **핵심 메시지:** "정확도는 숫자에 불과하고, 신뢰는 설명에서 나온다."
- **주요 내용:** EDA 실무, SHAP 해석, AI 윤리, 2026 에이전틱 로드맵

---

# [Layout: Split]
# 1. 잘 맞추면 끝인가? ML의 3가지 한계
[Image: Three dark silhouettes labeled "Black Box", "Bias", and "Non-Causality".]

- **한계 1 (Black Box):** 왜 이렇게 예측했는지 설명할 수 없습니다.
- **한계 2 (Bias):** 편향된 데이터는 차별을 재현합니다.
- **한계 3 (Non-Causality):** 상관관계만 보고 잘못된 액션을 취합니다.
- **실무의 결론:** 설명할 수 없는 모델은 현업에서 채택될 수 없습니다.

---

# [Layout: Visual Focus]
# 2. 블랙박스를 여는 열쇠: SHAP ⭐
[Image: A beautiful crystalline key opening a complex black engine, revealing golden internal logic.]

- **게임 이론의 도입:** "이 예측에서 각 변수는 얼마만큼의 공을 세웠는가?"
- **기여도 계산:** 나이, 사용료, 불만 건수가 최종 확률에 미친 영향을 숫자로 산출합니다.
- **비유:** Feature Importance가 '전교 인기투표'라면, SHAP은 '이번 시험의 과목별 기여도'입니다.

---

# [Layout: Waterfall Chart]
# 3. 워터폴 차트: 예측의 이유를 시각화하다 ⭐
[Image: A waterfall chart showing a base value of 45% being pushed by green bars (positive) and red bars (negative) to reach a final 80%.]

- **Base Value:** 평균적인 기본 확률.
- **변수의 작용:** '서비스 불만' (+30%) vs '잦은 로그인' (-8%).
- **설득의 무기:** "이 고객이 위험한 이유는 이 3가지 때문입니다"라고 보고할 수 있습니다.

---

# [Layout: Split]
# 4. 데이터 편향의 비극: Amazon 채용 AI
[Image: A digital scale tilted heavily to one side, with male/female icons representing data imbalance.]

- **현상:** 여성 지원자를 체계적으로 거절한 AI.
- **원인:** 과거 남성 위주의 채용 데이터를 그대로 학습했기 때문입니다.
- **해결책:** SHAP으로 특정 그룹에 대한 '부당한 마이너스 기여'를 찾아내고 수정해야 합니다.

---

# [Layout: 3-column]
# 5. 시각화 설득의 3단계 구조
[Image: Three connected icons: "Bullseye (Claim)", "Numbers (Evidence)", "Chart (Visualization)".]

1. **주장:** "고객 이탈이 심각하게 증가했습니다."
2. **근거:** "3월 12% → 5월 24%로 상승했습니다."
3. **시각화:** 꺾은선 그래프로 추세를 한눈에 보여줍니다.
- **원칙:** 숫자로 증명하지 않으면 주장이 아니라 '의견'일 뿐입니다.

---

# [Layout: Big Number]
# 6. EDA: "쓰레기 IN → 쓰레기 OUT"
[Image: A dirty camera lens taking a blurry photo of a beautiful landscape.]

- 모델링보다 중요한 것은 데이터의 품질입니다.
- 실무 프로젝트의 **70~80%**는 데이터 정제에 사용됩니다.
- 모델이 '카메라'라면, 데이터는 '렌즈와 필름'입니다.

---

# [Layout: Split]
# 7. 결측치(Missing Value) 처리 가이드
[Image: A puzzle with some missing pieces being filled by different colored tiles.]

- **5% 미만:** 과감히 삭제 (정보 손실 최소화).
- **5~30%:** 그룹별 평균이나 중앙값으로 대체.
- **30% 초과:** 변수 자체를 삭제하거나, '결측 여부'를 새로운 변수로 생성.
- **핵심:** 처리한 근거를 반드시 문서로 남겨야 합니다.

---

# [Layout: Split]
# 8. 이상치(Outlier): 에러인가, 사건인가?
[Image: A box plot showing a single point far away. One label says "Error", the other says "Key Event".]

- **에러:** 대여량 -50 (불가능함) → 제거.
- **사건:** 폭우나 공휴일로 인한 대여 폭증 → 유지 및 분석.
- **원칙:** 제거하기 전에 반드시 도메인 전문가에게 물어봐야 합니다.

---

# [Layout: Table]
# 9. Before / After 증명의 원칙

| 항목 | 전처리 전 (Raw) | 전처리 후 (Clean) |
|---|---|---|
| **결측치 비율** | 12.5% | 0.0% |
| **이상치 개수** | 42건 | 0건 |
| **평균 / 표준편차** | 45 (±82) | 51 (±52) |

- **품질 증명:** 수치 변화를 보여주지 못하면 분석은 신뢰받을 수 없습니다.

---

# [Layout: Grid]
# 10. 과제: 서울 자전거 공유 수요 분석
[Image: A map of Seoul with bicycle icons and data charts overlaid.]

- **시나리오:** 따릉이 데이터 분석가가 되어 결측/이상치를 정제하라.
- **미션:** 파생 변수를 생성하고, 전처리 전후의 통계적 변화를 숫자로 증명하라.
- **목표:** '왜 이 방법을 선택했는가'에 대한 논리적 근거 기록.

---

# [Layout: Timeline]
# 11. 당신의 다음 단계: 4단계 로드맵 ⭐
[Image: A mountain path with 4 stops: 1. sklearn, 2. XGBoost, 3. SHAP, 4. Agentic AI.]

1. **sklearn (2주):** 기초 모델링과 평가의 기본기.
2. **XGBoost (3주):** 실무 성능의 극한을 짜내는 최적화.
3. **SHAP (2주):** 결과에 책임을 지는 해석 능력.
4. **Agentic AI (4주):** 모델을 부품으로 사용하는 자동화 시스템 구축.

---

# [Layout: Split]
# 12. 에이전틱 AI 시대의 ML 엔지니어링
[Image: A robot hand connecting an "ML Brain" module into a larger "Agentic Engine".]

- **2026년 신호:** 멀티에이전트 관련 문의 **1,445% 증가**.
- **에이전트의 구조:** 의도 파악 → 계획 수립 → **ML 도구 호출**.
- ML 예측 모듈이 없으면 에이전트는 결정을 내리지 못하는 '맹목' 상태가 됩니다.

---

# [Layout: 2-column]
# 13. 시장의 차별점: "누가 운영하는가?"
[Image: A mechanic fixing a high-tech racing engine while it's running.]

- **단순 제작:** 누구나 할 수 있는 정확도 90% 모델.
- **진짜 실력:** 배포 후 성능 하락(Drift)을 감지하고, SHAP으로 이유를 찾아 재학습시키는 '운영' 능력.
- 2026년 기업이 원하는 것은 '모델 제작자'가 아니라 '모델 운영자'입니다.

---

# [Layout: Focus Card]
# 14. 수미상관: 야구공 질문의 답 ⭐
[Image: The pitcher from Session 1, but now with a clear SHAP waterfall chart next to him.]

- **질문:** "왜 이 타자는 이 구종에만 약한가?"
- **답:** "데이터 분석과 XGBoost, 그리고 SHAP을 통해 우리는 **회전수(RPM)**와 **투구 각도**가 타자의 타이밍을 뺏는 핵심 범인임을 밝혀냈습니다."
- 이제 여러분은 숫자로 처방을 내릴 수 있습니다.

---

# [Layout: Split]
# 15. 마지막 메시지: 질문하는 습관
[Image: A sunset horizon with a large question mark silhouette.]

- 함수와 수식은 도구일 뿐, 시간이 지나면 낡습니다.
- 하지만 **"이게 정말 맞는가?"**를 묻는 질문하는 습관은 영원합니다.
- **도구가 아니라 물음표를 가져가세요.** 질문하는 사람이 도구를 지배합니다.

---
