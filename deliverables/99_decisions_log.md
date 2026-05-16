# 99 — Decisions Log

> **Purpose**: Single source of truth for every non-obvious choice made during the engagement, with rationale and rejected alternatives. This is the artifact SR 11-7 model risk review will scrutinize most closely under the "conceptual soundness" principle. It is also the artifact a model risk reviewer (internal or external) will ask for first.
>
> **Update rule**: Any time you make a decision that wasn't obvious — choosing between two approaches, applying a threshold, rejecting a methodology — log it here within the same working day. Backfilling later loses the reasoning.

---

## Decision template

Each decision uses this structure:

```
### D[N] — [short title]
- Date:
- Phase:
- Decision:
- Alternatives considered:
- Rationale:
- Risk if wrong:
- Reviewer / owner:
- Status:
- Related: links to relevant deliverables, code, or follow-ups
```

---

## D01 — Target variable definition

- **Date**: 2026-05-15
- **Phase**: 1 (Framing)
- **Decision**: Binary classification — `default within 24 months of loan origination, defined as 90 days past due (DPD) ≥ 90`. In the Home Credit stand-in dataset, this is the `target` column in the base table as labeled by the competition organizers.
- **Alternatives considered**:
  1. Expected loss regression (PD × LGD × EAD) — dataset doesn't have LGD / EAD components → infeasible without additional data
  2. Multi-class default severity (30 / 60 / 90 / charge-off) — adds complexity without changing the binary action space (approve/decline)
  3. Time-to-event / survival model — handles right-censoring better but harder to defend to model risk; not industry standard for credit decisioning
- **Rationale**: Direct binary classification matches the regulatory and industry convention for credit decisioning. Passes all 8 "good target" criteria except partial fails on right-censoring (handled by dropping recent vintages) and survivorship bias (documented).
- **Risk if wrong**: If "default" is operationally defined differently at NovaLend (e.g., 60 DPD or charge-off), our model is solving a slightly different problem. Mitigation: lock the definition with the CRO at engagement start; flag if it changes mid-engagement.
- **Reviewer / owner**: Senior DS (owner), CRO (sign-off pending)
- **Status**: Locked pending CRO confirmation
- **Related**: [02_problem_framing.md](02_problem_framing.md)

---

## D02 — Model family — champion + benchmark pattern

- **Date**: 2026-05-15
- **Phase**: 1 (Framing)
- **Decision**: **Gradient Boosting (LightGBM)** as champion model. **Logistic regression with the same feature set** as the "interpretable benchmark" required by SR 11-7. Both models report to the model risk committee; the GBM is the deployment candidate.
- **Alternatives considered**:
  1. Logistic regression alone — leaves ~5 Gini points on the table from nonlinear interactions in this dataset
  2. Neural network — tabular data + ~1.5M rows is not a regime where NNs reliably beat GBM; explainability burden is higher
  3. Stacked ensemble — compounds the interpretability problem; adverse action codes become "average of N model explanations" — not defensible to ECOA
- **Rationale**: GBM is the industry standard for credit risk for the right reasons (handles missingness natively, monotonic constraints available for stability, SHAP-derivable for adverse action codes, fast to train, well-understood by examiners). The logistic benchmark satisfies SR 11-7's "interpretable challenger" expectation.
- **Risk if wrong**: If LightGBM-specific behavior (e.g., monotonic constraint handling) doesn't generalize, fall back to XGBoost — same family, comparable behavior. Not a binding risk.
- **Reviewer / owner**: Senior DS
- **Status**: Locked
- **Related**: [02_problem_framing.md](02_problem_framing.md), upcoming `06_model_methodology.md`

---

## D03 — Data processing tool — Polars

- **Date**: 2026-05-15
- **Phase**: 2 (Data audit)
- **Decision**: **Polars** for multi-table loading and aggregation. **Pandas** for the final feature matrix that feeds scikit-learn / LightGBM (ecosystem compatibility). DuckDB available for ad-hoc SQL exploration if needed.
- **Alternatives considered**:
  1. Pandas throughout — chokes on multi-million-row joins; would force premature subsampling
  2. PySpark — overkill for this data volume; adds operational complexity (JVM)
  3. DuckDB throughout — strong on multi-table joins but weaker native ML integration
- **Rationale**: Polars is the right tool for the 1-10M row + multi-table regime. Pandas at the final stage avoids friction with the model libraries.
- **Risk if wrong**: Low — Polars is mature for this scale. If we hit a bug, fall back to pandas with chunked reads.
- **Reviewer / owner**: Senior DS
- **Status**: Locked
- **Related**: [src/data/load.py](../src/data/load.py)

---

## D04 — Execution environment — Kaggle Notebooks

- **Date**: 2026-05-15
- **Phase**: 0 (Setup)
- **Decision**: All analysis runs on **Kaggle Notebooks** (where the 26 GB dataset is mounted at `/kaggle/input/...`). Code is edited locally in VSCode and synced via GitHub. The repo's `src/config.py` reads `DATA_DIR` from environment, defaulting to the Kaggle mount path.
- **Alternatives considered**:
  1. Download data locally and run on laptop — 26 GB > laptop disk; infeasible
  2. Local subsample (Kaggle API to pull ~2 GB) — possible for development but loses representativeness for stability evaluation
  3. Google Colab — feasible but Kaggle Notebooks have native dataset mounting
  4. AWS / GCP managed notebook — overkill for engagement budget
- **Rationale**: Kaggle Notebooks mirror the consulting pattern of "data lives in client environment; consultant code lives in firm repo". The dev loop (edit local → push GitHub → pull Kaggle → run) is operationally clean and the data never leaves Kaggle's environment.
- **Risk if wrong**: If Kaggle imposes session timeouts that interrupt long-running jobs, fall back to running on Colab Pro ($10/mo) or a small cloud VM with Kaggle API.
- **Reviewer / owner**: Senior DS
- **Status**: Locked
- **Related**: [data/README.md](../data/README.md), [notebooks/01_data_audit.py](../notebooks/01_data_audit.py)

---

## D05 — Audit methodology — hypothesis-driven, not blind profiling

- **Date**: 2026-05-15
- **Phase**: 2 (Data audit)
- **Decision**: Pre-write hypotheses H1–H5 in [02_problem_framing.md](02_problem_framing.md) **before** writing any audit code. Audit code is structured to test those hypotheses, not to produce kitchen-sink summary statistics.
- **Alternatives considered**:
  1. `ydata-profiling` / `pandas-profiling` auto-report — produces 200 charts, 198 of which are noise; cannot be triaged in the engagement timeline
  2. Bottom-up EDA (load, describe, look for surprises) — generates findings but rarely actionable ones
- **Rationale**: Per methodology Part 4 — hypothesis-driven EDA produces findings that are decision-relevant by construction. Blind profiling produces facts that may or may not matter.
- **Risk if wrong**: Risk is missing an important unexpected finding that hypotheses didn't cover. Mitigation: hypothesis list is reviewed at the end of audit; if anything surprising emerges from the targeted tests, we add a hypothesis and run a follow-up audit cycle.
- **Reviewer / owner**: Senior DS
- **Status**: Locked
- **Related**: [03_data_understanding.md](03_data_understanding.md), [interview_prep/00_consulting_methodology.md](../interview_prep/00_consulting_methodology.md) Part 4

---

## D06 — External-source stability handling

- **Date**: 2026-05-15
- **Phase**: 2 (Data audit, eyeballing)
- **Decision**: Features derived from external sources (Tax Registry A/B/C, Credit Bureau A/B) will be evaluated for **train-vs-test coverage drift** before being admitted to the feature set. Features from sources with > 20% coverage drop in test will receive a **stability penalty multiplier** on their importance score, or be excluded outright if coverage drops > 50%.
- **Alternatives considered**:
  1. Ignore source-level coverage — risk: model relies on signals that disappear at inference time, blows up stability metric
  2. Drop all external-source features — too conservative; loses substantial predictive signal
  3. Treat external-source coverage as a model feature itself — interesting (could model "is this applicant covered by tax registry b") but adds complexity; deferred
- **Rationale**: The dataset documentation explicitly warns external providers may be unavailable in test. The competition stability metric directly penalizes models that rely on signals which become missing. Building source-coverage into feature selection is preventive rather than corrective.
- **Risk if wrong**: If our train/test coverage assessment is wrong (e.g., a source we excluded is actually stable), we lose some signal. Acceptable trade in a stability-rewarding evaluation.
- **Reviewer / owner**: Senior DS
- **Status**: Locked; implementation in [05_feature_catalog.md](05_feature_catalog.md) and `src/data/schema.py`
- **Related**: [03_data_understanding.md](03_data_understanding.md) section A.1

---

## D07 — Repo structure — deliverables vs interview_prep separation

- **Date**: 2026-05-15
- **Phase**: 0 (Setup)
- **Decision**: Repo is organized with **`deliverables/`** as the client-facing main artifacts (engagement charter, problem framing, data understanding, decisions log, etc. — what a client and model risk reviewer would read) and **`interview_prep/`** as side resources (consulting methodology reference, case-practice prompts, worked examples — what the author uses for personal interview rehearsal).
- **Alternatives considered**:
  1. Everything in `docs/` — fails to distinguish client-facing work from personal practice notes
  2. Two separate repos — overkill; the two coexist and reference each other
- **Rationale**: Real engagement deliverables and interview preparation are different products with different audiences. Keeping them clearly separated avoids accidental conflation (e.g., interview talking points appearing in a client-facing doc). The interview_prep is honest scaffolding — practicing the muscle on this project — and should be visible but not the main artifact.
- **Risk if wrong**: Minimal — easily refactored later.
- **Reviewer / owner**: Senior DS
- **Status**: Locked
- **Related**: [README.md](../README.md), entire repo structure

---

## Reserved slots (decisions expected in upcoming phases)

- D08 — Feature engineering aggregation strategy per depth (Phase 3)
- D09 — Class imbalance handling method (Phase 4)
- D10 — Cross-validation strategy (time-aware vs stratified k-fold) (Phase 4)
- D11 — Hyperparameter tuning approach (Optuna config) (Phase 5)
- D12 — Adverse action reason code methodology (SHAP top-N) (Phase 6)
- D13 — Fairness mitigation method if 4/5 rule fails (Phase 6)
- D14 — Production architecture (Phase 7)
- D15 — Monitoring & retraining cadence (Phase 7)
- D16 — Model card structure for handoff (Phase 8)
