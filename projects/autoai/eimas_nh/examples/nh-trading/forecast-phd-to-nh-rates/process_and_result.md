# NH Trading Sample: Forecast PhD -> Rates/FICC Memo

## Target
- Scenario: US policy-path overconfidence -> KR curve / NH rates-FICC interpretation
- Audience: NH Investment & Securities Trading (rates/FICC lens)
- Goal: Show that forecast research can be translated into a bounded desk memo

## Process
1. Extract the core findings from `forecast/phd/paper_v2.md`.
2. Reframe those findings around NH's recent public Trading/FICC signals.
3. Package the result into `NHTradingDeskMemoV0` with thesis, scenarios, and handoff.

## Research Inputs
- Immediate-horizon 80% coverage: 13.3%
- VIX beta on coverage: -0.0171
- Bond-market lead: MOVE -> expectation variance
- Main macro catalyst: NFP abs_ratio 3.87
- Practical implication: widen scenario bands before desk reuse

## Result Memo
- Question: How should the NH rates/FICC desk respond when market-implied policy certainty stays too tight despite elevated volatility and bond-market stress signals?
- Thesis: The research suggests the market often gets the direction right but understates the distribution width, so NH should widen KR curve scenario bands before trusting front-end pricing.
- Base case: If policy repricing remains orderly, the desk can use wider scenario bands and bond-volatility signals to interpret KR duration and curve moves without overcommitting to a single path.
- Risk case: If VIX, MOVE, or foreign futures flows re-accelerate, front-end certainty can break quickly and force a sharper KR curve repricing than point forecasts imply.

## Market Context
- Regime: Transition / Policy repricing watch
- Volatility: Elevated
- Treasury 2y / 10y: 4.18 / 4.05
- 10y-2y spread: -0.13
- Liquidity regime: Tighter than neutral
- Rates focus: US policy path -> KR curve / FICC interpretation

## Watchlist
- Check whether front-end pricing is narrower than the realized event distribution again.
- Treat MOVE spikes as an early warning for KR curve stress rather than a lagging confirmation.
- Watch NFP-class macro releases and foreign futures positioning for fast repricing.
- Escalate to human review before turning the memo into product or sales language.

## Handoff
- Required: True
- Reason: The sample memo is intentionally bounded: it informs rates/FICC interpretation, but live execution, curve positioning, and customer translation still need human desk review.

## Evidence Notes
- This sample bridges local forecast/phd research into an NH-style memo; it is not a live NH desk report.
- Recent NH public signals are referenced from the local Trading field-research memo rather than direct live feeds.

## Candidate Translation
- This is not a generic AI demo.
- It shows a candidate who reads rates uncertainty as a distribution problem,
  checks overconfidence, and hands the result to a desk in memo form.

## Local Sources
- /home/tj/projects/forecast/phd/paper_v2.md
- /home/tj/projects/자기소개서/NH투자증권_Trading_현업조사_2026Q1.md
