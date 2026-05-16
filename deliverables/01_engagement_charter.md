# 01 — Engagement Charter

> **Status**: Active · **Phase**: 1 of 4 (Diagnostic) · **Last updated**: 2026-05-15
> **Audience**: NovaLend executive sponsor, engagement team, model risk reviewer
> **Methodology**: See [interview_prep/00_consulting_methodology.md](../interview_prep/00_consulting_methodology.md) Part 1 (goal decomposition)

---

## Client context

**NovaLend** is a federally chartered, mid-size US consumer lender with approximately **$10B** in outstanding unsecured personal loans across **~5M customers**. Federally chartered → OCC-supervised → subject to **SR 11-7** model risk management and **ECOA / Regulation B** fair-lending requirements.

Current credit decisioning runs on a **custom logistic regression scorecard** built by an external consulting firm in 2019, frozen at the coefficient level, recalibrated twice (intercept-only). The scorecard uses ~35 inputs spanning internal application data and credit bureau pulls; outputs a score cut at a fixed threshold to drive approve/decline.

## The trigger

Over the last three quarters the book-wide **90-day-past-due rate has moved from 3.1% → 3.4% → 3.7%**, with concentration in two segments:

- **Borrowers under 30 with thin credit files**
- **Borrowers in three states NovaLend expanded into 18 months ago**

The underwriting team attributes this to macro conditions; the data science team reports the scorecard is "broadly performing." Neither hypothesis has been rigorously tested.

Concurrently, the **OCC examination 8 months ago** flagged two open findings: (1) model documentation needs refresh, (2) recommend developing a "challenger" model for the scorecard. Both remain unresolved.

## Decision the engagement must inform

The **Board Risk Committee** needs a recommendation on whether to **modernize the credit decisioning system**, and if so, with what governance and monitoring posture. The CRO has signaled she leans toward modernization but wants the recommendation grounded in a defensible analysis, not a slide deck.

The recommendation must answer three nested questions:

1. **Tactical (this quarter)** — Should NovaLend pause approvals on any segment immediately?
2. **Strategic (this year)** — Should NovaLend replace the legacy scorecard with an ML-based system?
3. **Governance (ongoing)** — Whatever the choice, what monitoring, validation, and recalibration posture is required?

This engagement is sized to inform decision **#2**, with a sidebar recommendation on **#3**. Decision **#1** remains with the CRO regardless of our findings.

## Deliverable

**Single document**: a board-ready recommendation memo with three appendices —

1. Technical methodology
2. Financial impact projection
3. Implementation roadmap

The **model we build is evidence, not the deliverable**. A common failure mode in this kind of engagement is over-building the model and under-investing in the documentation that justifies it. We will not repeat that mistake.

## Scope

### In scope
- Build a champion-grade ML credit risk model on representative historical data
- Build an interpretable benchmark (logistic regression) per SR 11-7 requirements
- Quantify business impact via portfolio profit simulation against the legacy scorecard
- Fair-lending audit on age and gender per ECOA / Regulation B (4/5 rule, demographic parity, equal opportunity, calibration parity)
- Stability analysis — Gini stability metric + per-quarter performance variance
- Compliance documentation map: SR 11-7, ECOA, NIST AI RMF
- Production architecture sketch (FastAPI, audit logging, monitoring blueprint)
- Recommendation memo + three appendices

### Out of scope
- Full underwriting system integration (we deliver the risk scoring component only)
- Live loan origination system integration
- Training on production-volume data (we develop on representative subsample; full-data validation is a recommended next step)
- Litigation-grade fair-lending audit (we demonstrate the methodology; formal audit is a recommended next step)
- Implementation of privacy-enhancing technologies (discussed in `docs/security.md`, not built)
- Macro-overlay model (proposed as future-state engagement — see `15_future_work.md`)

### Explicitly *not* a goal
- Topping a Kaggle leaderboard. The dataset we use (Home Credit Credit Risk Model Stability, 2024) is the analytical stand-in for NovaLend's data; we optimize for deployability and compliance, not leaderboard rank.

## Success criteria (defined before building)

| Layer | Metric | Threshold | How measured |
|---|---|---|---|
| **ML performance** | Gini stability (competition metric) | > 0.50 | Walk-forward CV on time-split holdouts |
| **Business impact** | Expected portfolio profit improvement vs legacy scorecard | > 5% | Simulation in `notebooks/07_business_simulation.py` |
| **Fairness** | 4/5 disparate impact ratio across protected attributes | ≥ 0.80 | Fairlearn audit in `notebooks/08_fairness_audit.py` |
| **Explainability** | SHAP-derivable adverse action reasons per prediction | 100% coverage | Validated in `src/explainability/adverse_action.py` |
| **Stability** | Gini variance across quarterly windows | < 0.05 absolute | Per-quarter evaluation in `notebooks/06_stability_analysis.py` |
| **Production posture** | Inference p99 latency | < 200ms | Benchmarked in `src/serving/api.py` |

Failure to clear *any* threshold becomes a documented risk in `09_risk_register.md`, not an automatic project failure — but the recommendation reflects the gap.

## Stakeholder map

| Stakeholder | Concerns | What we need from them |
|---|---|---|
| **CRO** | Model risk, regulatory exposure, defensibility | Sign-off on validation methodology, target horizon |
| **Head of Underwriting** | Operational integration, override workflow | Acceptable false-positive ceiling, override policy |
| **Compliance** | ECOA, fair-lending audit trail, SR 11-7 conformance | Sign-off on adverse action reason format |
| **Internal Data Science (4-person team, ex-actuarial)** | Co-ownership of resulting model, technical credibility | Buy-in on architecture; we propose them as challenger-model owners |
| **Customer Experience** | Adverse action explanation human-readability | Reason code wording approval |
| **Board Risk Committee** | Aggregate model risk, governance posture | Acceptance of recommended risk tier |

## Engagement team

| Role | Time allocation | Responsibility |
|---|---|---|
| Partner | ~10% | Client relationship, board presentation |
| Engagement Manager | ~50% | Workplan, stakeholder management |
| **Senior Data Scientist (you)** | 100% | Technical workstream — model build, EDA, evaluation, documentation |
| Senior Analyst | ~50% | Financial modeling, business case |
| Compliance Advisor | ~10% | Regulatory interpretation, fair-lending audit review |

## Timeline

| Week | Phase | Major milestone |
|---|---|---|
| 1 | Scoping + data audit | Engagement charter signed, data audit findings (`03_data_understanding.md`) |
| 2 | Problem framing + EDA | Problem framing locked, baseline EDA findings |
| 3–4 | Feature engineering + baseline | Logistic baseline + first GBM, initial business simulation |
| 5–6 | Champion model + stability | Champion GBM tuned, stability and fairness audits |
| 7 | Compliance + production design | SR 11-7 / ECOA mapping, production architecture |
| 8 | Synthesis | Board memo + appendices, internal review, partner sign-off |

This document was the foundation deliverable; we are currently in Week 1.

## Operating principles

The team operates by four principles that will be reflected in every artifact:

1. **Interpretability is non-negotiable.** Every model we recommend must be defensible to the model risk committee. Black-box recommendations do not survive this client's prior consulting experience and will not survive ours.
2. **Compliance is architecture, not afterthought.** SR 11-7 documentation, ECOA fair-lending audit, and adverse action reason codes are deliverable inputs, not deliverable outputs. They shape the build.
3. **Stability over peak performance.** The competition metric (Gini stability) is also the right operational metric: a model that holds its Gini across quarters beats a model with higher average Gini and quarterly drift.
4. **Show your work.** Every non-obvious decision goes into `99_decisions_log.md` with rationale and rejected alternatives. This is what survives the next OCC exam.

## Open questions (escalate to client)

These are recorded in `04_data_gaps.md` as well; reproduced here for charter visibility:

- What is the exact contractual definition of "default" in NovaLend's current scorecard? (90 DPD at 24-month horizon assumed, to confirm)
- Has the underwriting team's "macro" hypothesis been tested? (We propose to test it in Phase 2 EDA.)
- What is the appetite for SHAP-derived adverse action reasons vs. the coefficient-based reasons of the legacy scorecard? (Compliance question.)
- Does NovaLend hold loans on book or originate-to-sell? (Affects default behavior interpretation.)
- Are there segments where new model decisions would override binding regulatory or policy constraints? (E.g., minimum age, hardship moratoria.)
