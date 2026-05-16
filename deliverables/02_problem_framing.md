# 02 — Problem Framing

> **Status**: Active · **Phase**: 1 · **Last updated**: 2026-05-15
> **Methodology applied**: [interview_prep/00_consulting_methodology.md](../interview_prep/00_consulting_methodology.md) Parts 1 + 3
> **Related deliverables**: [01_engagement_charter.md](01_engagement_charter.md) · [03_data_understanding.md](03_data_understanding.md) · [99_decisions_log.md](99_decisions_log.md)

This document operationalizes the engagement scope from the charter into the specific question we will answer. Every modeling decision downstream is justified against this framing.

---

## The decision sentence

> *"The CRO will decide **whether to replace the legacy logistic scorecard with an ML-based credit decisioning system**, based on a prediction of **whether an applicant will default within 24 months of origination (90 DPD)**, at the time of **loan application**, and the consequence of a wrong prediction is **a marginal $ loss (false approve) or marginal $ revenue forgone (false decline) — measurable via portfolio profit simulation**."*

This sentence is the contract between this engagement's analytical work and the client's decision. Every choice in the project is justified against it.

---

## Decomposition (MECE)

We decompose the central question into three mutually exclusive sub-problems whose union covers the decision:

### Sub-problem A — Is the legacy scorecard *actually* failing?
- **Decision enabled**: continue calibration vs. develop replacement
- **Method**: vintage analysis on legacy scorecard outputs, decomposed by segment and time
- **Owner**: Phase 2 (data audit + EDA)

### Sub-problem B — Can an ML model *materially* outperform the legacy scorecard on the dimensions NovaLend cares about (default rate at fixed approval volume, calibration, stability across time)?
- **Decision enabled**: which model architecture to recommend
- **Method**: benchmark logistic + champion GBM, compare across multi-layer evaluation
- **Owner**: Phases 3–5 (feature engineering, modeling, evaluation)

### Sub-problem C — Will the recommended model be defensible to OCC examiners, the Board Risk Committee, and a fair-lending challenge?
- **Decision enabled**: governance and monitoring posture
- **Method**: SR 11-7 conformance mapping, ECOA fair-lending audit, stability analysis, adverse action documentation
- **Owner**: Phases 6–7 (compliance, fairness, production)

**Why this decomposition is MECE**:
- A and B are distinct: A is diagnostic of the *current* state; B is prospective on a *replacement*. Both could resolve to "yes" or "no" independently.
- C is orthogonal: even if A and B both say "build a new model", C may block deployment.
- The union covers the recommendation: any path through {A, B, C} produces a defensible board recommendation.

---

## Target variable: choice and rationale

### Chosen target

**Binary classification target**: `default within 24 months of loan origination`, defined as **90 days past due (DPD) ≥ 90 within the 24-month observation window**.

In the Home Credit Credit Risk Model Stability dataset (our analytical stand-in), this corresponds to the `target` column in the base table, which the competition organizers have defined and labeled.

### Why this target — passes all 8 "good target" criteria

| # | Criterion | Status | Detail |
|---|---|---|---|
| 1 | Observable | ✅ | Directly labeled in `train_base.parquet` `target` column |
| 2 | Actionable | ✅ | Drives the approve/decline decision exactly |
| 3 | Time-locked | ✅ | Anchored at `date_decision` (application date) |
| 4 | Available with horizon | ⚠️ | 24-month horizon means most recent ~24 months are right-censored — these rows will be excluded from training |
| 5 | Stable definition | ⚠️ | Definition stable in the Kaggle dataset; production note: NovaLend's policy must be verified to ensure historical consistency |
| 6 | Sampling unbiased | ⚠️ | **Survivorship bias**: training data is the approved population only; the declined population has no outcome and is not in the dataset. Documented in `09_risk_register.md` |
| 7 | Sufficient events | ✅ | Default rate ~3% × ~1.5M training applications = ~45k events (well above the 1k events minimum) |
| 8 | Dollar-translatable | ✅ | Each default converts via `LGD × EAD × loan_amount` to expected loss; full conversion in `notebooks/07_business_simulation.py` |

### Targets considered and rejected

This is the documentation the model risk committee will look for. We considered three alternatives:

| Target | Why rejected |
|---|---|
| **Expected Loss (PD × LGD × EAD)** | Would directly answer the dollar question. Rejected because the Home Credit dataset does not include loss-given-default or exposure-at-default data; we cannot decompose. Flagged as a **future-state extension** in `15_future_work.md` — for production, this would be the right target. |
| **Multi-class default severity** (e.g., 30 / 60 / 90 / charge-off) | Richer signal, but the action space remains binary (approve/decline) → adds complexity without changing decisions. Rejected for parsimony. |
| **Time-to-default (survival analysis)** | Better handles right-censoring on recent applications. Rejected for this engagement because (a) the regulatory and industry standard for credit decisioning is binary default within a fixed horizon, and (b) survival models are harder to explain to the model risk committee. Flagged as a **future-state extension**. |

### Known target risks (documented in `09_risk_register.md`)

1. **Survivorship bias**: training only on approved applicants underestimates default risk on currently-declined marginal segments. We cannot fix this within engagement scope; we will document and propose reject inference as a follow-on.
2. **Right censoring**: the most recent 24 months of applications cannot be used in training. This reduces training data and shifts the effective time range.
3. **Definition drift potential**: if NovaLend's operational definition of "default" changes mid-engagement (e.g., new charge-off policy), the target's meaning shifts. We will lock the definition at engagement start and flag changes if they occur.

---

## Unit of analysis

**One row = one loan application** at a specific application date, identified by `case_id` in the base table.

Each applicant may have multiple historical records in the bureau / prior application / monthly balance tables (depth ≥ 1). These must be **aggregated to the case_id grain** before joining onto the base table.

Aggregation strategy is the central feature-engineering decision and is documented separately in `05_feature_catalog.md`.

---

## Evaluation framework

A model that optimizes a single metric will fail. We evaluate on four layers (full detail in `07_evaluation_framework.md`):

| Layer | Purpose | Lead metric |
|---|---|---|
| 1. Offline ML metrics | Statistical performance | AUC-ROC, PR-AUC, Brier score, KS, Gini |
| 2. Stability metrics | Robustness to time | Gini stability (competition metric), per-quarter Gini variance, PSI per feature |
| 3. Business simulation | Dollar impact | Expected portfolio profit improvement vs. legacy scorecard |
| 4. Fairness audit | Regulatory defensibility | 4/5 disparate impact ratio, demographic parity, equal opportunity, calibration parity |

**Recommendation rule pre-committed (anti-rationalization)**:
- If stability differs by < 2 Gini points between champion candidates → recommend the more stable one
- If business simulation differs by < 3% portfolio profit → recommend the more stable one
- Ties break in favor of the simpler model

This pre-commitment prevents us from post-hoc justifying whichever model happens to "win" on a vanity metric.

---

## Out-of-scope problems and why

| Out-of-scope | Why | Where it goes |
|---|---|---|
| Reject inference (modeling outcomes for declined applicants) | Requires external matched data we don't have | `15_future_work.md` |
| Cold-start modeling for new states | Population insufficient; transfer learning territory | `15_future_work.md` |
| Macro-overlay model | Out of engagement scope; high-value follow-on | `15_future_work.md` |
| Pricing / limit-setting models | Requires LGD/EAD data | `15_future_work.md` |
| A/B test execution | We design the test; client runs it | `14_ab_test_design.md` |

---

## Hypotheses to test in EDA (Phase 2)

Stated **before** looking at the data (per methodology Part 4):

| # | Hypothesis | Falsifying observation |
|---|---|---|
| H1 | Default rate is rising across vintages — concept drift / scorecard staleness | If vintage analysis shows flat default rate at fixed months-on-book, H1 is rejected |
| H2 | The default rate uptick is concentrated in under-30 thin-file borrowers and the three expansion states | If decomposition shows even distribution across segments, H2 is rejected |
| H3 | Missingness in specific external data sources (e.g., one of the tax registry providers) correlates with default | If missingness is uncorrelated with default, H3 is rejected and missingness imputation is safer |
| H4 | Some external data sources have coverage that drifts over time (the docs warn this explicitly) | If all external sources have stable coverage across the time range, H4 is rejected and stability metric is easier to hit |
| H5 | Feature distributions drift across the time range, contributing to the stability challenge | If PSI < 0.10 on all major features across time buckets, H5 is rejected — stability is a free lunch |

EDA design (Phase 2) is purpose-built to test these five hypotheses. We will not produce charts that don't address one of them.
