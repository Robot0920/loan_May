# Credit Risk System — Technical Roadmap & System Design

**Project framing**: This document is structured the way a McKinsey / QuantumBlack engagement lead would scope a project before execution. Every decision has stated criteria, multiple options considered, and tools justified.

**Scope**: 2-week build (5/15 – 5/27), single-developer, designed to be demo-able in TEI as your own work.

**Dataset**: Home Credit — Credit Risk Model Stability (Kaggle, 2024)
**Starting point**: https://www.kaggle.com/code/jetakow/home-credit-2024-starter-notebook

---

## Phase 0 — Engagement Scoping (Before You Write Any Code)

A consulting engagement starts with scoping, not data. The discipline of pretending this is a client engagement is the point — it changes how you frame everything downstream.

### Client mental model (you invent this, but ground it in realism)

| Element | Your assumption |
|---|---|
| Client | Mid-size consumer lender (~5M customers, ~$10B loan book) considering an ML-driven underwriting upgrade |
| Current state | Rule-based scorecard built 6 years ago; recent default rate creep on younger borrowers |
| Decision they need to make | Whether to deploy an ML-based credit decisioning system, and if yes, what governance / monitoring posture |
| Time horizon | 12-week engagement, your work is the technical proof-of-concept phase (weeks 4–8) |
| Project sponsor | Chief Risk Officer (signs off on model risk), reports to Board Risk Committee |
| End user of the model | Underwriting team, automated decisioning system |

### The actual question your project answers

Not "can we predict defaults better than baseline?" — that's a research question.

The real question: **"Can we build a credit decisioning model that improves expected portfolio profit by ≥X bps, while staying compliant with SR 11-7 and ECOA, and remaining stable over time without quarterly recalibration?"**

This framing is what you'll talk about in TEI. It contains: business value, compliance constraint, operational constraint.

### Success criteria (define before building)

| Layer | Metric | Threshold |
|---|---|---|
| **ML performance** | Gini stability (competition metric) | > 0.50 |
| **Business impact** | Expected profit improvement over rule-based baseline (in simulation) | > 5% |
| **Fairness** | 4/5 disparate impact ratio across protected attributes | ≥ 0.80 |
| **Explainability** | SHAP-derivable adverse action reasons | 100% of predictions |
| **Stability** | Gini variance across quarterly windows | < 0.05 absolute |
| **Production** | Inference p99 latency | < 200ms |

### Scope cuts (what you're NOT doing — also a real consulting move)

- **Not** building a full underwriting system — only the risk scoring component
- **Not** integrating with loan origination system
- **Not** training on production-volume data (you'll subsample to manage time)
- **Not** running real fair-lending lawsuit-grade audit (you'll demonstrate the methodology)
- **Not** implementing real privacy-enhancing tech (you'll discuss in `docs/security.md`)

---

## Phase 1 — Business Problem Framing (Before Touching Data)

### What you should write in `docs/decisions.md` before any code

```markdown
## Problem Statement

A consumer lender wants to predict the probability that a loan applicant
will default within the next 24 months, in order to drive an automated
underwriting decision.

The target variable (TARGET in the dataset) is binary: default within
horizon (1) or no default (0).

## Unit of Analysis

One row = one loan application. Each applicant may have multiple
historical applications in the bureau / previous_application tables;
those must be aggregated per current application.

## Why this framing, not alternatives

Considered three framings:

1. **Binary default prediction** (chosen): Aligns with the dataset's TARGET,
   simplest to validate against historical outcomes, matches how rule-based
   systems are currently built.

2. **Expected loss regression** (PD × LGD × EAD): Closer to the economic
   reality but requires loss-given-default and exposure-at-default data
   the dataset doesn't have. Out of scope.

3. **Limit + price optimization** (combined): Would maximize expected
   profit but requires elasticity data not in the dataset. Discussed
   as a future-state extension in docs/future_work.md.
```

### Stakeholder map (sketch in 5 min, refer back to it)

| Stakeholder | What they care about | What you need from them |
|---|---|---|
| CRO | Model risk, regulatory exposure, defensibility | Sign-off on validation methodology |
| Head of Underwriting | Operational integration, override workflow | Acceptable false-positive rate ceiling |
| Compliance | ECOA, fair lending audit trail | Documentation conformance |
| Data Engineering | Production data feeds, latency | Schema contract, SLA |
| Customer Experience | Adverse action explanations | Reason code human-readability |
| Board Risk Committee | Aggregate model risk, governance | Quarterly stability reports |

In TEI: "I built this assuming stakeholder X cares about Y" sounds dramatically more senior than "I built a model."

---

## Phase 2 — Data Strategy

### Inventory the data you have

The Home Credit 2024 dataset has multiple tables. Treat these as a relational schema, not a feature engineering convenience.

| Table | Grain | Why it matters |
|---|---|---|
| `application` | 1 row per current application | Target variable lives here |
| `credit_bureau` | 1 row per prior credit (multiple per applicant) | External credit signals |
| `previous_application` | 1 row per prior Home Credit application | Internal repayment behavior |
| `monthly_balance` | 1 row per month per prior credit | Temporal credit behavior |
| `card_balance` | 1 row per month per credit card | Revolving credit signals |
| `installments` | 1 row per installment payment | Payment timing patterns |
| `pos_cash_balance` | 1 row per month per POS / cash loan | Short-term credit behavior |

### Data assessment questions to answer before any modeling

Document the answers in `docs/data_understanding.md`:

1. **Volume**: How many applications? How many bureau records per applicant? What's the distribution? (Spot the long tail.)
2. **Time range**: What's the temporal span? Are there COVID-era gaps?
3. **Class balance**: What's the default rate? Stratified by which segments?
4. **Missingness**: Which columns are missing > 30%? Is it MCAR / MAR / MNAR? (Missing patterns themselves are features.)
5. **PII identification**: Which columns are PII / quasi-identifiers? (Even anonymized data has re-identification risk.)
6. **Protected attributes**: Age and gender are explicit. What else acts as a proxy? (ZIP-equivalent geographic info, employment type, education.)
7. **Distribution drift**: Do feature distributions drift across the time range? (Build the test now, you'll need it for stability analysis later.)
8. **Leakage candidates**: Any field that could only be known AFTER the target outcome? (E.g., months_balance from after application date.)

### What data we'd want but don't have

Document explicitly in `docs/data_gaps.md`. This is consulting-style work.

| Wanted | Not in dataset | Workaround / proxy |
|---|---|---|
| Real-time credit bureau pull | Historical snapshots only | Use most recent bureau snapshot per applicant |
| Macroeconomic context | No external macro data | Add unemployment / interest rate features from public sources |
| Loan purpose detail | Coarse-grained categories | Accept coarseness, document limitation |
| Income verification status | Partial | Treat verification status as feature, document risk |
| Geographic identifiers | Limited | Document fair-lending implication (no ZIP/region testing) |

### Tooling choice — pandas vs. polars vs. DuckDB

This is a real engineering decision worth thinking through.

| Tool | When to choose | Trade-off |
|---|---|---|
| **Pandas** | Default for EDA, < 5M rows in memory | Slow on multi-table joins at this scale |
| **Polars** | Multi-million row aggregations, multi-table joins | Newer ecosystem, fewer Stack Overflow answers |
| **DuckDB** | Complex SQL-style multi-table joins, "select X group by Y" patterns | Less native ML integration |

**Decision**: Use **Polars for the data processing pipeline** (faster, handles this dataset size well), **pandas for the final feature matrix** (ecosystem compatibility with scikit-learn / XGBoost). DuckDB optional for ad-hoc exploration.

This kind of considered choice — "I picked X for these reasons, vs Y" — is what TEI rewards.

---

## Phase 3 — Reference Code Strategy

You asked specifically about borrowing from gold medalist code. Here's the discipline.

### When to borrow, when not to

| Borrow ✅ | Don't borrow ❌ |
|---|---|
| Feature engineering ideas (specifically: temporal aggregation patterns, ratio features they invented) | Stacking / blending pipelines (over-fit to leaderboard, unmaintainable) |
| Cross-validation strategies (especially time-aware folds) | Kitchen-sink feature creation (1000+ features, not interpretable, not auditable) |
| Memory-optimization patterns (downcasting, parquet) | Hyperparameter values copied verbatim (won't transfer) |
| Multi-table join strategies | Custom CUDA implementations or exotic boosting libs |
| Validation framework structure | Final submission post-processing tricks |

### Why this discipline matters

**Gold medalists optimize for leaderboard rank. You optimize for: production-deployable, interpretable, compliant, stable.** Those are different objectives. A 13th-place gold solution may have 800 features and a 5-model stack — un-deployable in real banking and un-defensible to a model risk committee.

### Specific repos to read (and what to read in each)

**1. Mitsubishi Electric team's solution (13th gold, 2024 competition)**

This team specifically won by "robust features, model construction and adaptation to evaluation metrics" — exactly what you want to learn.

Search Kaggle discussion forum for their writeup:
https://www.kaggle.com/competitions/home-credit-credit-risk-model-stability/discussion

What to read: their feature engineering writeup, their CV strategy, how they thought about stability metric.
What to ignore: ensemble specifics, hyperparameter tuning details.

**2. benettia — 93rd place / 3858 (top 3%)**

🔗 https://github.com/benettia/Kaggle-Home-Credit-Risk

What to read: clean repo structure, feature selection methodology, validation approach.
What to ignore: he himself says it's not production-ready — you're going further.

**3. zulqarnainalipk — production-style structure**

🔗 https://github.com/zulqarnainalipk/Home-Credit---Credit-Risk-Model-Stability

What to read: how they structured the codebase into modular reusable framework, model persistence patterns, pipeline organization.
What to ignore: the model results — you're building your own.

**4. kozodoi — Top-4% on Home Credit 2018 (older competition, same domain)**

🔗 https://github.com/kozodoi/Kaggle_Home_Credit

What to read: their feature engineering chapter — many feature ideas transfer across the 2018 → 2024 datasets. Their `code_1_data_prep.ipynb` is excellent.
What to ignore: anything LightGBM-specific that's not generalizable.

**5. Open-source baseline (minerva-ml)**

🔗 https://github.com/minerva-ml/open-solution-home-credit

What to read: how to structure an open ML pipeline with config files, experiment tracking philosophy.
What to ignore: Neptune-specific integration (use MLflow instead).

### Other sources beyond Kaggle

| Source | What you get | Why useful |
|---|---|---|
| **FICO whitepapers on scorecard methodology** | Industry-standard credit scoring math | Lend credibility in TEI |
| **Federal Reserve SR 11-7 + OCC examiner guides** | Compliance lens on ML models | Make your project audit-defensible |
| **Fairlearn case studies on lending** | Concrete fair-lending audit examples | Real-world ECOA implementation |
| **Lending Club methodology blog posts** | How a real fintech built credit models | Industry context |
| **Bank of England staff working papers on ML credit models** | Regulatory perspective | Senior framing |
| **Microsoft InterpretML credit risk demo** | Worked SHAP example on similar data | Concrete reference |

🔗 InterpretML demo: https://github.com/interpretml/interpret

### Critique exercise (do this on 5/15)

Pick 2 reference notebooks. For each, write a 1-page critique answering:

1. What's the implicit business problem the author thought they were solving?
2. What 3 modeling decisions did they make? Were those choices justified or arbitrary?
3. What's the biggest production gap? (Usually: no explainability, no fairness audit, no stability analysis)
4. What 2 ideas would you steal? What would you reject?

This critique exercise gives you TEI talking points like: "I read 3 of the top public solutions on this dataset, and the consistent gap was X. I addressed it by Y."

---

## Phase 4 — Feature Engineering Architecture

### Feature categories with business reasoning

Document each category in `docs/features.md` with reasoning per feature group, not per feature.

| Category | Examples | Business reasoning |
|---|---|---|
| **Application-level demographics** | age, income, employment length | Direct creditworthiness signal |
| **Application-level loan characteristics** | loan_amount, loan_type, term, annuity-to-income ratio | Loan structure risk |
| **Behavioral — payment history** | count of late payments, max DPD in last N months | Strongest predictor in credit literature |
| **Behavioral — credit utilization** | revolving balance / credit limit, growth rate | Stress indicator |
| **Behavioral — application frequency** | recent credit inquiries, number of new accounts | Credit-seeking behavior signal |
| **Temporal — recency** | days since last default, days since last credit event | Memory of past behavior decays |
| **Temporal — trend** | balance growth over last 6 months, payment shortfall trend | Direction matters as much as level |
| **Aggregation — bureau** | max / mean / sum of bureau records per applicant | Captures portfolio-level signal |
| **Ratio features** | DTI, payment-to-income, loan-to-value | Bank scorecards rely on these |
| **Missingness indicators** | binary flag for each high-missingness column | Missing patterns themselves are predictive |

### Time-aware feature engineering — critical for stability

Most Kaggle solutions ignore this. Stability metric punishes models whose feature distributions drift over time.

**Rules**:
1. Every aggregation must specify a time window relative to application date (e.g., "12 months prior")
2. Never aggregate post-application data into features (data leakage)
3. Test feature distributions across quarterly windows during EDA
4. Drop features whose distribution drifts > X% across windows

### Leakage prevention checklist

Before any feature ships:

- [ ] Was this fact knowable at the time of application?
- [ ] Could this feature be derived from the target itself?
- [ ] Does this feature have suspiciously high univariate predictive power?
- [ ] Is the date field used to construct this feature strictly before the application date?

---

## Phase 5 — Modeling Strategy

### Baseline progression (do not skip baseline)

| Stage | Model | Purpose |
|---|---|---|
| **Baseline 0** | Predict class prior (majority class) | Establishes the dumb floor |
| **Baseline 1** | Logistic regression with 10 hand-picked features | Tells you which features matter most via coefficients; this is the SR 11-7 "interpretable benchmark" |
| **Model A** | Logistic regression with full feature set | Tests if added features help interpretable model |
| **Model B** | Gradient boosting (LightGBM or XGBoost) — your primary model | Industry standard for credit risk |
| **Model C** | Gradient boosting with stability constraints (monotonic constraints, regularization tuning) | Trades a bit of AUC for stability gains |
| **Optional ensemble** | Average of B and C | Skip unless time allows |

### Model family decision criteria

| Decision factor | Logistic regression | Gradient boosting | Neural network |
|---|---|---|---|
| Performance on tabular | Lower | Higher | Comparable to GBM |
| Interpretability | High (native coefficients) | Medium (SHAP needed) | Low |
| SR 11-7 defensibility | Easiest to defend | Defensible with SHAP | Hardest |
| Training time | Fast | Medium | Slow |
| Stability over time | Very stable | Stable with constraints | Less predictable |
| Adverse action explanation | Trivial | SHAP-derived | Hard |

**Decision for this project**: Gradient boosting as primary, logistic regression as the "interpretable benchmark" required by SR 11-7. Neural network not justified given tabular data and compliance requirements.

### Class imbalance handling — decision matrix

Class imbalance in this dataset is ~3%. Different methods have different failure modes.

| Method | When to use | Failure mode |
|---|---|---|
| **Class weights** | First try, simple, no data manipulation | May not help if features can't separate classes |
| **SMOTE** | When minority is severely under-represented (< 1%) | Synthetic samples may be unrealistic, especially with categorical features |
| **SMOTENC** | SMOTE variant for mixed categorical / continuous | Better than SMOTE for this dataset |
| **Undersampling majority** | When you have abundant data | Loses information |
| **Focal loss (in GBM)** | When easy negatives dominate gradient | Requires careful tuning |
| **Threshold tuning on PR-AUC** | Always do this regardless of method | Implicit in evaluation |

**Decision for this project**: Start with class weights. If validation PR-AUC < 0.X, try SMOTENC. Always tune threshold on PR-AUC, not accuracy.

### Stability — the project's distinguishing feature

The competition metric is Gini stability, not raw AUC. This means: a model with AUC 0.78 that stays 0.78 across quarters beats a model with AUC 0.82 that drops to 0.71.

**How to design for stability**:

1. **Walk-forward validation** — train on quarters 1–4, validate quarter 5; train on 1–5, validate 6; etc.
2. **Track per-quarter AUC** during training, not just overall
3. **Monotonic constraints on stable features** (in LightGBM, use `monotone_constraints`)
4. **Drop features with high temporal drift** even if predictive
5. **Stronger regularization** (higher `reg_lambda`) to reduce overfitting to recent quarters

### Hyperparameter tuning strategy

| Approach | When | Trade-off |
|---|---|---|
| **Grid search** | < 5 hyperparameters, small dataset | Exhaustive, slow at scale |
| **Random search** | Default for 5+ hyperparameters | Industry standard, fast |
| **Bayesian (Optuna)** | When training is expensive | Smarter, but more setup |
| **Manual / domain-driven** | When you have strong priors | Fastest, requires expertise |

**Decision**: Optuna with 50 trials, stratified by time-aware CV. Focus on `num_leaves`, `learning_rate`, `min_child_samples`, `reg_lambda`, `feature_fraction`.

🔗 Optuna: https://optuna.org/

---

## Phase 6 — Evaluation Framework (Three Layers)

A model that only optimizes one metric is a model that will fail in production.

### Layer 1 — Offline ML metrics

| Metric | Why |
|---|---|
| **AUC-ROC** | Industry-standard ranking metric |
| **PR-AUC** | More informative under class imbalance |
| **Brier score** | Tests probability calibration (critical for limit pricing) |
| **Calibration plot** | Visual check that predicted probability matches actual |
| **KS statistic** | Traditional credit scoring metric, expected in audits |
| **Gini coefficient** | = 2 × AUC – 1, standard in credit risk reporting |

### Layer 2 — Stability metrics (the competition's twist)

| Metric | Why |
|---|---|
| **Gini stability** | The competition's evaluation. Worth implementing exactly. |
| **Per-quarter AUC variance** | Catches models that work on average but drift |
| **Population Stability Index (PSI)** | Industry-standard input drift measure |
| **Characteristic Stability Index (CSI)** | Per-feature drift |

### Layer 3 — Business simulation

Convert model output into business decisions, then measure business impact.

**Simulation logic**:
1. For each loan in test set, predict default probability
2. Apply a threshold to decide approve / decline
3. For approved loans, simulate expected profit:
   - If default: lose Loss-Given-Default × Loan Amount
   - If no default: gain expected interest income over loan term
4. Aggregate to portfolio level
5. Compare expected profit at multiple approval thresholds
6. Compare against rule-based baseline (simple FICO-style threshold)

This simulation is the difference between "my model has AUC 0.78" and "my model improves expected portfolio profit by 6.3%." The second is what a CRO cares about.

### Layer 4 — Fairness audit (ECOA / Regulation B)

| Test | What it measures | Pass criterion |
|---|---|---|
| **Demographic parity** | Approval rates across protected groups | Within 5pp |
| **4/5 disparate impact rule** | Approval rate of protected group / unprotected | ≥ 0.80 |
| **Equal opportunity** | True positive rate across groups | Within 5pp |
| **Calibration parity** | Predicted probability accuracy across groups | Slope difference < 0.05 |

Use Fairlearn or AIF360. Document results in `docs/fairness_audit.md`.

🔗 Fairlearn: https://fairlearn.org/
🔗 AIF360: https://aif360.readthedocs.io/

### A/B test design (for "if this were deployed for real")

This is a thought exercise, not implementation. Document in `docs/ab_test_design.md`.

**Specify**:
- Hypothesis (e.g., "New model reduces 90-day default rate by ≥ 10%")
- Power calculation (sample size to detect effect at α=0.05, power=0.80)
- Randomization unit (applicant or branch?)
- Run duration (constrained by default observation window)
- Guardrail metrics (approval rate, customer satisfaction, regulatory complaints)
- Stopping rules

---

## Phase 7 — Compliance Layer (Threaded Through, Not Bolted On)

### SR 11-7 conformance map

For each SR 11-7 principle, document in `docs/compliance.md` how your project addresses it.

| SR 11-7 principle | Your artifact |
|---|---|
| Conceptual soundness | `docs/decisions.md` — explains feature logic, model choice |
| Implementation verification | Unit tests in `tests/` confirming production code matches development logic |
| Ongoing monitoring | `src/monitoring.py` — drift detection, performance alerts |
| Outcomes analysis | Walk-forward validation in `notebooks/stability_analysis.ipynb` |
| Independent validation | Documented as next-step in `docs/future_work.md` (single-developer limitation) |
| Model documentation | Comprehensive README + decision logs |
| Model inventory | Top of README lists model version, last train date, validation date |
| Model risk governance | `docs/governance.md` — proposes risk tier and review cadence |

### ECOA / Reg B conformance

| Requirement | Your artifact |
|---|---|
| Adverse action notice — specific reason | SHAP-based reason code generator in `src/adverse_action.py` |
| No discrimination on protected attributes | Fairness audit results in `docs/fairness_audit.md` |
| Disparate impact testing | 4/5 rule test results documented |
| Notice within 30 days | Discussed in architecture doc; out of project scope |

### NIST AI RMF mapping

Lighter touch than SR 11-7 / ECOA but reference it.

| NIST AI RMF function | Your artifact |
|---|---|
| GOVERN | `docs/governance.md` |
| MAP | `docs/risk_register.md` — what could go wrong |
| MEASURE | Evaluation framework — Layers 1–4 |
| MANAGE | Monitoring plan + retraining triggers |

---

## Phase 8 — Production Architecture

### Serving layer

| Component | Choice | Why |
|---|---|---|
| API framework | FastAPI | Industry standard, automatic OpenAPI docs, Pydantic validation |
| Request validation | Pydantic | Type-safe, generates schema |
| Model loading | At startup, in-memory | Low latency for synchronous prediction |
| Inference | Single-record sync API; batch via separate endpoint | Two latency profiles |
| Response | Prediction + SHAP top-5 reasons + model version | Audit-ready response |

### Logging architecture

Every prediction logged with:
- Timestamp (UTC, ISO 8601)
- Model version (semver)
- Input feature hash (SHA-256)
- Predicted probability
- Predicted class
- SHAP reason codes
- Request ID

Why: SR 11-7 outcome analysis requires you to compare predictions to actuals later. You can't do that without prediction logs.

### Monitoring

| Layer | What | Tool / pattern |
|---|---|---|
| Input drift | PSI on each feature per day | Custom or Evidently AI |
| Output drift | Distribution of predicted probabilities | Custom histogram comparison |
| Performance | Daily AUC on labeled actuals | Requires actuals feedback loop |
| Latency | p50/p99 inference time | Prometheus / Grafana |
| Fairness | Approval rate parity per day | Custom Fairlearn-based job |

🔗 Evidently AI: https://github.com/evidentlyai/evidently

### Deployment

| Component | Choice |
|---|---|
| Container | Docker, multi-stage build for image size |
| Orchestration | Kubernetes (discussed in `docs/deployment.md`, not implemented in scope) |
| Secrets / config | Environment variables, no hardcoded credentials |
| Health check | `/health` endpoint reporting model load + dependencies |

---

## Phase 9 — Documentation as Deliverable

Documentation is not afterthought. It IS the consulting deliverable. The model is the artifact; the documentation is the deliverable that justifies the artifact.

### Required docs

| File | Audience | Length |
|---|---|---|
| `README.md` | First-time reader / executive | 2 pages, includes 1-paragraph exec summary |
| `docs/decisions.md` | Future maintainer / model risk reviewer | Long, every key choice with reasoning |
| `docs/data_understanding.md` | Data engineer / model risk reviewer | EDA findings, data limitations |
| `docs/features.md` | Model risk reviewer | Feature catalog with business reasoning |
| `docs/compliance.md` | Compliance officer | SR 11-7 + ECOA + NIST mapping |
| `docs/fairness_audit.md` | Fair lending officer | Audit methodology + results |
| `docs/security.md` | InfoSec | PII handling, audit logging, PETs discussion |
| `docs/risk_register.md` | Model risk committee | Known limitations, failure modes |
| `docs/future_work.md` | Engagement extension PM | What's out of scope, what comes next |
| `docs/governance.md` | Board risk committee | Recommended model risk tier, review cadence |

### CEO summary (1 paragraph, top of README)

Format:

```
"This project demonstrates an ML-based credit risk system that improves
expected portfolio profit by X% in simulation over a rule-based baseline,
while satisfying SR 11-7 documentation requirements, passing ECOA
fair-lending audits, and maintaining Y stability across temporal validation.
The recommended next step is independent validation by a model risk team
prior to limited production pilot."
```

This is your TEI executive close-out. Memorize the structure, fill in your numbers.

---

## Phase 10 — Execution Roadmap (Maps to Your 2-Week Schedule)

| Day | Stage | Concrete deliverable |
|---|---|---|
| 5/15 | Setup + compliance read | Project structure, Kaggle data, SR 11-7 notes, jetakow notebook review |
| 5/16 | Phase 1 + 2 (framing + data) | `docs/decisions.md` problem framing, EDA notebook v1 |
| 5/17 | Phase 2 (data) + Phase 4 (baseline) | Data processing pipeline, logistic regression baseline |
| 5/18 | Phase 3 (reference critique) + Phase 4 (features) | Critique 2 reference notebooks, feature engineering v1, SHAP scaffold |
| 5/19 | Class imbalance | Class imbalance comparison done, documented |
| 5/20 | Phase 5 (modeling) + Phase 6 (business sim) | GBM v1, business profit simulation |
| 5/21 | Phase 8 (production) | FastAPI scaffold, Dockerfile, audit logging |
| 5/22 | Phase 6 (fairness) | Fairness audit results, `docs/fairness_audit.md` |
| 5/23 | Phase 5 (stability) + Phase 7 (compliance doc) | Walk-forward validation, stability metrics, `docs/compliance.md` |
| 5/24 | (mock day, no project work) | — |
| 5/25 | Phase 7 (security) | `docs/security.md`, PII handling, audit log finalization |
| 5/26 | Phase 5 (tuning) | Optuna HP tuning, model finalization |
| 5/27 | Phase 9 (final docs) | README executive summary, risk register, governance doc |

---

## Decision Tree Summary — "When To Use What"

Quick reference for choosing approaches:

```
Data too big for pandas?
├── < 5M rows → pandas
├── 5M–100M rows → polars
└── 100M+ rows or need SQL → DuckDB or Spark

Class imbalance method?
├── First attempt → class weights
├── Severe (< 1%) and categorical features → SMOTENC
├── GBM with easy-negative dominance → focal loss
└── Always → threshold tuning on PR-AUC

Model family?
├── Tabular + compliance-heavy → GBM (LightGBM/XGBoost)
├── Need maximum interpretability → logistic regression
├── Have time + sequential data → transformer (out of scope here)
└── Always include a logistic baseline (SR 11-7 expects it)

Validation strategy?
├── No temporal structure → stratified k-fold
├── Temporal structure (this project) → walk-forward / time-series CV
└── Stability metric → multiple time-window evaluation

Explainability tool?
├── Linear model → native coefficients + standardized
├── GBM / tree → SHAP TreeExplainer (fast)
├── Black box → SHAP KernelExplainer (slow)
└── Always → top-5 reasons per prediction for adverse action
```

---

## TEI Talking Points You Earn From This Project

After building this, you can say in TEI:

> "I built an end-to-end credit risk decisioning system on the Home Credit 2024 stability dataset. I want to walk you through three decisions where the right answer wasn't obvious.
>
> **First**, on framing. I could have framed this as a binary default prediction problem, but the actual client decision is about portfolio profit, not classification accuracy. So I built a profit simulation layer that takes model output and computes expected portfolio profit at different approval thresholds. That layer is what a CRO would actually look at, not the AUC.
>
> **Second**, on the trade-off between AUC and stability. The competition's evaluation metric is Gini stability, not raw AUC, because production credit models that drift quarterly are operationally useless even if their average performance is great. I tested four models — class-weighted logistic regression, vanilla GBM, GBM with monotonic constraints, and an ensemble — and found the monotonic GBM gave up about 2 points of AUC for a 30% reduction in temporal variance. That's a trade I'd recommend defending to a model risk committee.
>
> **Third**, on compliance. SR 11-7 requires conceptual soundness, ongoing monitoring, and outcomes analysis. ECOA requires adverse action reason codes. Most ML credit risk projects I've read about treat these as documentation that comes after the model. I treated them as architecture decisions — the SHAP layer is a deployed component, not a notebook. Adverse action reason codes come back with every prediction. Fairness audit on age and gender showed a 7% disparate impact gap that I documented as a known limitation requiring stakeholder input before production.
>
> The thing I'd do differently — my validation is single-developer. SR 11-7 explicitly requires independent validation, which is the natural next step for a model risk team."

This is what you're building toward. Every phase above produces a piece of this narrative.
