---
name: financial-graph-theory
description: |
  금융 네트워크 분석, 자산 간 연결 구조, 시스템 리스크 전파,
  MST(최소신장트리) 기반 포트폴리오 분석, NetworkX 중심성 분석,
  또는 "금융 시스템을 그래프로 모델링"하는 작업 시 활성화된다.
  단순 상관관계 분석이나 이분법적 포트폴리오 구성에는 활성화하지 않는다.
version: 1.0.0
created: 2026-02-21
source: F:/2025-2/금융/최종 클라우드/06_네트워크_그래프/
---

# 금융 그래프 이론 프레임워크

## 핵심 개념: 금융 시스템을 그래프로

```
금융 네트워크의 구성 요소:
  노드(Node) = 자산, 기업, 금융기관, 국가
  엣지(Edge) = 상관관계, 익스포저, 자본 흐름, 거래 관계
  가중치(Weight) = 연결의 강도 (상관계수, 거래량 등)

왜 그래프인가:
  전통 통계: 자산을 독립적 또는 페어 단위로 분석
  그래프 이론: 전체 네트워크 구조 속에서 각 자산의 역할 분석
  → 시스템 리스크 전파 경로 식별 가능
```

---

## MST (최소신장트리) — Mantegna 방법론

> Mantegna (1999), *European Physical Journal B* — 금융 시장에 그래프 이론 최초 적용

### MST 구성 과정

```python
import numpy as np
import networkx as nx
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import minimum_spanning_tree

# 1. 상관→거리 변환
corr_matrix = returns.corr()
dist_matrix = np.sqrt(0.5 * (1 - corr_matrix))

# 2. MST 생성 (Kruskal's Algorithm)
# 가장 짧은 엣지부터 순차적으로 추가, 사이클 형성 시 제외
# 결과: N개 노드, N-1개 엣지의 트리 구조

# 3. NetworkX로 분석
G = nx.minimum_spanning_tree(nx.from_numpy_array(dist_matrix.values))
```

### MST 해석

```
MST에서 중심 노드 = 시스템 전체에 가장 큰 영향력을 가진 자산
  예: S&P500 MST에서 SPY ETF가 중심 → 제거 시 전체 구조 붕괴

MST 엣지 길이:
  짧은 엣지 = 강한 상관관계 = 같은 리스크 팩터 공유
  긴 엣지 = 약한 상관관계 = 좋은 분산 대상

포트폴리오 활용:
  MST 말단(leaf) 노드 = 다른 자산과 가장 독립적 → 분산 효과 극대화
  MST 허브(hub) 노드 = 시스템 리스크 전파자 → 비중 축소 검토
```

---

## NetworkX 중심성 지표

| 지표 | 공식 | 금융 해석 |
|------|------|---------|
| **Degree Centrality** | 직접 연결된 노드 수 / (N-1) | 직접 익스포저 많은 자산/기관 |
| **Betweenness Centrality** | 다른 노드 쌍의 최단 경로 중 이 노드를 지나는 비율 | 전파 중개자 역할 (제거 시 네트워크 분리) |
| **Eigenvector Centrality** | PageRank 유사 — 중요한 노드와 연결될수록 가중치 증가 | 시스템적 중요 자산 (SIFI 식별) |
| **Closeness Centrality** | 다른 모든 노드까지 평균 최단 거리의 역수 | 정보/충격이 빠르게 퍼지는 자산 |

```python
import networkx as nx

# 주요 중심성 계산
degree_cent = nx.degree_centrality(G)
between_cent = nx.betweenness_centrality(G, weight='weight')
eigen_cent = nx.eigenvector_centrality(G, weight='weight')

# 시스템적 중요 자산 식별
sifi_score = {
    node: (between_cent[node] * 0.4 +
           eigen_cent[node] * 0.4 +
           degree_cent[node] * 0.2)
    for node in G.nodes()
}
top_sifi = sorted(sifi_score, key=sifi_score.get, reverse=True)[:5]
```

---

## 금융 그래프 분석 실무 활용

### 시스템 리스크 전파 분석

```
단계별 분석:
  1. 상관 행렬 → 거리 행렬 변환
  2. 임계값(threshold) 적용하여 엣지 필터링
     (예: |ρ| > 0.7인 쌍만 연결)
  3. 커뮤니티 탐지 (Louvain, Girvan-Newman)
     → 자연스러운 자산 클러스터 식별
  4. 중심성 지표로 핵심 전파자 식별
  5. 연결 제거 실험 (node removal) → 취약성 테스트

실무 응용:
  VIX 급등 시기 네트워크 밀도 증가 패턴 분석
  2008/2020 위기 시 엣지 수 급증 = 동조화 심화
```

### 포트폴리오 구성에서의 그래프 이론

```
MST 기반 배분 원칙:
  허브 노드 (중심성 높음) → 비중 축소 (리스크 집중 원천)
  리프 노드 (중심성 낮음) → 비중 증가 (진정한 분산)

HRP와의 연결:
  HRP의 계층적 클러스터링 = 사실상 MST의 단순화된 버전
  D̄(i,j) 시스템 유사도 = 그래프 이론의 betweenness와 유사한 개념

고급 활용:
  Graph Attention Network (GAT): 그래프 구조 + 딥러닝
  → 동적 상관관계 변화 포착
  → 기존 고정 상관 행렬 한계 극복
```

---

## LLM + 강화학습 기반 금융 그래프 추론

```
배경:
  금융 그래프는 비유클리드(non-Euclidean) 공간
  → 전통 ML이 직접 처리 어려움

LLM 역할:
  금융 그래프를 텍스트로 표현하여 LLM 입력
  예: "SPY는 QQQ, IWM과 높은 상관관계를 갖고, TLT와는 음의 관계..."
  → LLM이 관계 구조를 이해하고 추론

강화학습 역할:
  그래프 탐색(graph traversal) = 순차적 의사결정
  포트폴리오 리밸런싱 = 그래프 노드 가중치 재조정
  → DQN/PPO로 최적 탐색 경로 학습

현재 한계:
  동적 금융 그래프의 실시간 업데이트 처리
  대규모 자산 유니버스에서의 확장성
  해석 가능성(explainability)
```

---

## 핵심 참고문헌

| 저자 | 연도 | 기여 |
|------|------|------|
| Mantegna | 1999 | 주식 시장 MST 최초 적용 |
| de Prado | 2016 | HRP — 그래프 이론 → 포트폴리오 |
| O'Hara | 2015 | HFT 시대 미시구조 네트워크 |
| Greenwood et al. | 2019 | 버블 탐지 — 조건부 효율성 |
