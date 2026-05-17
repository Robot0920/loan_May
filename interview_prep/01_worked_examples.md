# 05 — Goal → Decision → Target Decomposition

> **My personal interview-prep notes.** This is the thinking framework I rehearse for the *first 10 minutes* of any technical case interview, before any modeling discussion. The point is to not jump to "I'd build an XGBoost" before I've earned the right to say what to predict.
>
> **Scope of this note**: only the **bones** of the framework — Goal → Problem → Decision → ML/Analysis → Target → first DS steps. The **flesh** (model architecture, evaluation metric design, monitoring posture, deployment, fairness, compliance) is built up in later notes and in `deliverables/`. Don't skip ahead in interviews either — finish the scoping conversation first.

---

## The core principle I keep forgetting (and need to drill)

> **Target variable is reverse-engineered from the decision.** It is not "what's in the dataset", it is "what prediction would change the decision the client needs to make".

If you can't finish this sentence —

> *"If I had a perfect prediction of ___, the client could decide ___, which would deliver ___ business outcome."*

— then your target is wrong, and no amount of model tuning will fix it.

Every business goal can be rewritten as one of these sentences. The decomposition exercise below is just **forcing that sentence to exist** before I touch data.

---

## The decomposition template I use

For any client goal, walk through **6 stages** in order. Don't skip.

```
Stage 1.  BUSINESS GOAL
          (client's words, vague, executive)
              ↓
Stage 2.  DECOMPOSED PROBLEMS
          (2–4 mutually exclusive sub-problems whose union covers the goal)
              ↓
Stage 3.  DECISIONS THAT FOLLOW
          (for each sub-problem: what specific decision does solving it enable?)
              ↓
Stage 4.  ML / ANALYSIS THAT SUPPORTS THE DECISION
          (classification? regression? causal inference? optimization? what mode?)
              ↓
Stage 5.  TARGET VARIABLE (reverse-engineered)
          (what specifically am I predicting / measuring? defined by Stage 4)
              ↓
Stage 6.  INITIAL DS WORKFLOW STEPS
          (data sufficiency check, EDA, leakage check — to validate Stages 2–5 are tractable)
```

**Watch out**: weak candidates collapse Stages 2–5 into a single jump from goal → "I'd use ML". Strong candidates make each stage explicit. The interviewer is grading the *transitions*, not the model.

---

## Worked example 1 — "Grow loan book by 15% next year without raising default rate"

### Stage 1 — Goal
> *"We want to grow our loan book by 15% next year without raising our default rate."*

What the client is really saying: "find me incremental safe applicants." NOT "predict default better in general."

### Stage 2 — Decomposed problems

Two sub-problems whose union covers the goal:

| Sub-problem | Mechanism |
|---|---|
| **2a. Find safe applicants currently being rejected** | Expand approval pool by lowering threshold on segments where current scorecard is too conservative |
| **2b. Find unsafe applicants currently being approved** | Tighten threshold on segments where current scorecard is too lax (frees up "default budget" to expand elsewhere) |

Note: 2a alone might raise default rate. 2b alone might shrink the book. **Both together** lets the book grow while default rate stays flat. **Senior framing**: I'd present this trade-off explicitly to the client — they may not realize they need both moves.

### Stage 3 — Decisions

| Sub-problem | Decision |
|---|---|
| 2a | For each segment, what should the new approval cutoff be? Build a segment-level approval threshold table |
| 2b | Same — but tightening, not loosening |

The **deliverable** the client uses is not the model — it's a **policy table**: for each (segment × applicant score), what's the action.

### Stage 4 — ML / Analysis

This is the subtle part. The naive answer is "binary classification". But because the decision is *threshold-based* and *segment-based*, the right framing is:

- **Binary classification model for default within 24 months** (standard)
- **PLUS** an evaluation metric that focuses on the **PR curve in the higher-recall region** (where the marginal applicants live)
- **PLUS** segment-stratified evaluation — overall AUC could be flat while the model is terrible on the marginal-borrower segments
- **OPTIONAL**: uplift modeling for "what's the incremental default risk of approving this currently-rejected applicant" — but uplift modeling requires randomized exposure data which we probably don't have. Document as a future-state improvement.

### Stage 5 — Target variable (the reverse-engineered piece)

- **Target**: binary default within 24 months at 90 DPD
- **BUT** the *target's evaluation lens* is different from a generic classifier:
  - Care about model performance in deciles 6–8 (marginal borrowers), not deciles 1–2 (clearly safe) or deciles 9–10 (clearly risky)
  - Care about *calibration*, not just ranking, because the policy table converts scores to thresholds (predicted probability must match actual default rate)

**Same target as a vanilla project. Different evaluation lens. That's the senior move.**

### Stage 6 — Initial DS workflow

1. **EDA on the historical approved population**: standard
2. **EDA on the historical rejected population**: we probably have very limited outcome data on these — flag the **selection bias / reject inference** issue immediately as a known limitation
3. **Segment definition**: agree with the client on the 6–10 segments that matter (likely: file thickness × tenure × loan purpose)
4. **Volume-cap analysis (back-of-envelope)**: at the current default rate of X%, if we want to grow approvals by 15%, the new marginal approvals can have at most a default rate of Y% before book-wide rate moves. Compute Y. This sets the *necessary precision* the model has to hit
5. **Decline rate decomposition by segment**: which segments have unusually high decline rates? These are the candidates for sub-problem 2a

---

## Worked example 2 — "Reduce default losses by 10% while maintaining current approval volume"

### Stage 1 — Goal
> *"We want to reduce our default losses by 10% while maintaining current approval volume."*

The key word is **losses**, not **defaults**. Losses ≠ defaults. **A default that recovers 60% of principal is half the loss of a default that recovers 20%.** This changes everything downstream.

### Stage 2 — Decomposed problems

| Sub-problem | Mechanism |
|---|---|
| **2a. Reduce probability of default (PD)** at the marginal applicant | Same scorecard improvement story |
| **2b. Reduce loss-given-default (LGD)** | Risk-based pricing (higher rate → more collected before default), better collateralization, faster intervention |
| **2c. Reduce exposure-at-default (EAD)** | Lower initial credit limits on high-risk borrowers, faster amortization schedules |
| **2d. Reduce loss conditional on default** via better collections | Operational, not modeling — early intervention, restructuring |

This is the **expected-loss decomposition**: `EL = PD × LGD × EAD`. The interviewer wants to see you know this identity.

### Stage 3 — Decisions

| Sub-problem | Decision |
|---|---|
| 2a | Underwriting policy (same as Example 1, narrower focus) |
| 2b | **Pricing matrix**: interest rate per (segment × score) bucket |
| 2c | **Limit-setting policy**: initial credit limit per (segment × score) bucket |
| 2d | **Collections strategy**: which delinquent loans get human-touched first |

### Stage 4 — ML / Analysis

Three models, not one (this is the senior move):

| Model | Type | Output |
|---|---|---|
| **PD model** | Binary classification | P(default \| applicant features) |
| **LGD model** | Regression (often beta-distributed or 2-stage) | E[loss \| default] |
| **EAD model** | Regression (sometimes constant for installment loans) | E[balance at default] |

Then combine: **Expected loss per applicant = PD × LGD × EAD × loan_amount**. This is what the pricing decision uses.

### Stage 5 — Target variable

- **PD target**: binary default at 90 DPD within 24 months (same as Example 1)
- **LGD target**: continuous, `($ owed at default - $ recovered through collections + recovery costs) / $ owed at default`, defined only for defaulted loans
  - **Critical issue**: this is a *conditional* model — training set is only the ~3% who defaulted. Sample size shrinks dramatically. Need to discuss whether enough signal.
  - **Also**: LGD is often bimodal (full loss vs partial recovery) — naive regression underperforms; mixture model or two-stage approach
- **EAD target**: continuous, `balance at time of default`. For installment loans this is close to a deterministic function of original loan amount × age; for revolving credit (cards) it's a real model

### Stage 6 — Initial DS workflow

1. **First check**: do we even *have* recovery data on historical defaults? CRO said yes — verify in EDA
2. **Distribution of LGD** across defaulted loans — bimodal or unimodal? Drives model choice
3. **Correlation of LGD with PD-score quintile** — high-PD loans typically also have high LGD (selection on observables). Document this
4. **Sample-size feasibility**: with ~3% default rate and N applicants, do we have enough defaulted loans (~0.03N) to train a stable LGD model? Rule of thumb: need ≥ 1000 events per model
5. **Pricing elasticity**: do we have any historical data on how interest rate affects default? Probably not — flag as known limitation, propose A/B test as future work

---

## Worked example 3 — "Automate underwriting to cut latency from 48h to under 5min"

### Stage 1 — Goal
> *"We want to automate underwriting decisions to cut decision latency from 48 hours to under 5 minutes."*

This is **NOT a modeling problem at its core** — it's an **operations + decision-confidence problem**. The model is a component, not the whole answer. **Failing to recognize this is the most common mistake on this type of question.**

### Stage 2 — Decomposed problems

| Sub-problem | Mechanism |
|---|---|
| **2a. Identify "obvious" approve cases** | Auto-approve when model is very confident applicant is safe |
| **2b. Identify "obvious" decline cases** | Auto-decline when model is very confident applicant is risky |
| **2c. Route ambiguous cases to humans** | Manual underwriter queue for the remaining ~X% |
| **2d. Build the inference infrastructure** | Sub-5-min SLA = model serving + bureau pull + decision logic in one synchronous call |

### Stage 3 — Decisions

| Sub-problem | Decision |
|---|---|
| 2a + 2b | **Two thresholds**: lower (below = auto-decline), upper (above = auto-approve). Between = human review. Tune by allowable error budget |
| 2c | Staffing model for the human queue: how many underwriters needed at the projected volume |
| 2d | Tech architecture: API design, latency budget, retry/fallback logic |

### Stage 4 — ML / Analysis

The ML piece is the same default model — **what's different is the use of predicted probability + confidence**:

- Point estimate of P(default) — same as Examples 1 and 2
- **Confidence band** on that estimate — this is the new piece
  - Methods: conformal prediction, quantile regression, ensemble uncertainty
- **Calibration becomes business-critical** — the thresholds are interpreted as probabilities, so the probabilities have to be right (not just ranked correctly)
- **Operations research wrapper**: given the score distribution and the manual queue capacity, optimize the two thresholds to maximize auto-decision rate subject to:
  - Default rate of auto-approvals ≤ X
  - False decline rate of auto-declines ≤ Y
  - Manual queue volume ≤ underwriter capacity

### Stage 5 — Target variable

- **Primary target**: binary default within 24 months at 90 DPD (same as before)
- **Secondary target / wrapper**: per-applicant **upper confidence bound on P(default)** at α=0.05 (or whatever level matches risk appetite)
- **Operational target (separate)**: % of applications auto-decided per day — this is what's monitored in production, not AUC

### Stage 6 — Initial DS workflow

1. **Calibration audit on the existing scorecard FIRST** — before any new model. Is the current scorecard's probability output even meaningful? Most legacy scorecards have terrible calibration because they're score-based not probability-based
2. **Distribution of model confidence** on a held-out set — what fraction of applicants are "obvious"? If only 20%, automation gain is small
3. **Threshold-sensitivity analysis**: at various (lower, upper) threshold pairs, what's the auto-decision rate, expected default rate, manual queue volume? Build the trade-off frontier
4. **Latency budget breakdown**: of the 5-minute SLA, how much is model inference (probably milliseconds), how much is bureau pull (probably seconds-to-minutes — usually the binding constraint), how much is decision logic? Often the model is *not* the slow part
5. **Define manual-review handoff schema**: when a case goes to a human, what info / explanation does the underwriter get? (SHAP top-5 reasons; reason codes)

---

## Synthesis — what changes across the three examples

| | Example 1 (Grow) | Example 2 (Reduce loss) | Example 3 (Automate) |
|---|---|---|---|
| **Same target?** | Yes (binary default) | **No — three targets**: PD + LGD + EAD | Yes (binary default) + confidence wrapper |
| **Same evaluation?** | No — focus on marginal-borrower segments | No — expected-loss in dollars, not classification metrics | No — calibration + auto-rate + queue volume |
| **Same model type?** | Same | Three separate models | Same + uncertainty quantification |
| **Biggest data gap?** | Reject inference (no outcomes on declined) | Sample size for LGD model | Confidence quantification on existing scorecard |
| **Biggest non-DS work?** | Segment definition | Pricing matrix design | Operations / staffing model |

**The lesson**: same dataset, three goals, three target frameworks. **The goal defines the target, not the data.** I keep needing to re-internalize this — junior DS instinct is to start from the data, find a target, then justify it. Senior DS starts from the goal.

---

## Common pitfalls I'm catching myself on

1. **Jumping straight to "I'd use XGBoost"** — I should be 5 minutes into the case before I've named a model
2. **Confusing default rate with default loss** — they are not the same. Example 2 hinges on this
3. **Picking a target before naming the decision** — if I can't say "this prediction would let the client decide X", my target is decoration, not analysis
4. **Saying "I'd improve the model"** — improve in which direction? AUC overall? AUC on the marginal segment? Calibration? Latency? Different goals reward different improvements
5. **Treating Example 3 as a modeling problem** — it's primarily an ops problem. The model is one component
6. **Missing the dollar-denominated reframing** — every senior conversation eventually goes "what does this look like in dollars". I should pre-empt by quantifying losses, gains, costs from the start

---

## Where this fits in the consulting interview

We're at the **first 10–15 minutes** of a 60-minute case. After this decomposition, the conversation goes:

1. ✅ Goal decomposition (this note) — **done in first 10 min**
2. ⬜ Data strategy: what we have / need / can't have — Methodology Part 2; lives in `deliverables/03_data_understanding.md`
3. ⬜ Feature engineering tradeoffs — Methodology Part 3 (target) + project's `deliverables/04_model_build.md`
4. ⬜ Model family choice — `deliverables/99_decisions_log.md` D02
5. ⬜ Evaluation framework — `deliverables/02_problem_framing.md` (4-layer framework) + `04_model_build.md`
6. ⬜ Deployment & monitoring — `deliverables/07_recommendation.md` (consolidated future deliverable)
7. ⬜ Compliance close — `deliverables/06_compliance_governance.md` (consolidated future deliverable)
8. ⬜ Synthesis to CEO — `deliverables/07_recommendation.md` final board memo section

This note is the **bones** of stages 1–5 above. The **flesh** (architecture detail, evaluation rationale, deployment posture, fairness, compliance) gets filled in as I work through the actual project deliverables in `deliverables/`. **Don't try to fake the flesh before you've done the project work.** That's what the project is *for*.

---

## Template for adding more examples (use this when I encounter new business goals)

```markdown
## Worked example N — "<client's goal in their own words>"

### Stage 1 — Goal
> *"<quote>"*

What the client is really saying: <one sentence>

### Stage 2 — Decomposed problems
| Sub-problem | Mechanism |
|---|---|
| 2a | |
| 2b | |
(2-4 sub-problems whose union covers the goal; mutually exclusive)

### Stage 3 — Decisions
| Sub-problem | Decision |
|---|---|

### Stage 4 — ML / Analysis
(classification? regression? causal? optimization? what type and why)

### Stage 5 — Target variable
- Primary target: <definition>
- Why this target (link back to Stage 3 decision):
- Known issues with this target:

### Stage 6 — Initial DS workflow
1. Data sufficiency check: <what to verify>
2. Critical EDA question: <what to look for first>
3. Known limitation to flag early: <what>
4. Back-of-envelope to do before modeling: <what>
```

---

## Practice prompts to drill myself with (add to as I find more)

These are the kinds of opener questions I want to be able to decompose on the spot. Set a 5-minute timer per prompt, walk through the 6 stages, then compare against my own notes here.

- "We want to grow our loan book by 15% next year without raising our default rate." *(done — Example 1)*
- "We want to reduce our default losses by 10% while maintaining current approval volume." *(done — Example 2)*
- "We want to automate underwriting decisions to cut decision latency from 48 hours to under 5 minutes." *(done — Example 3)*
- "We need to add a co-applicant feature to our personal loan product and want to know if it'll improve approvals." *(pending)*
- "Our 30-day-late rate is fine but our 90-day-roll-rate is creeping up — what should we do?" *(pending)*
- "Regulators flagged our adverse action notices as inadequate — we need to redesign." *(pending)*
- "We want to enter a new state where we have no historical data — how do we underwrite there?" *(pending — cold start problem, transfer learning territory)*
- "We're considering buying a portfolio of $500M in loans from a competitor — how do we price it?" *(pending — portfolio valuation, very different problem)*

(Add more as I encounter them in case books / interview discussions / real client briefs.)
