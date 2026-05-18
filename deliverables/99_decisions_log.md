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

## D08 — Unified tax-data features (replaces individual tax registries)

- **Date**: 2026-05-17
- **Phase**: 2 (Data audit, runtime finding)
- **Decision**: Do **not** use `tax_registry_a`, `tax_registry_b`, `tax_registry_c` columns individually as model features. Instead construct two unified features per applicant: `any_tax_data` (binary indicator: did ANY tax registry have a record for this applicant) and `tax_amount_max` (max across providers for any amount-valued tax column). Implementation lands in `src/features/` during Phase 3.
- **Alternatives considered**:
  1. Use all three tax registries as separate features — fails on stability because each is available only ~30 weeks out of 91; any model relying on one will degrade in the period that registry is absent
  2. Drop all tax registry features — leaves substantial signal on the table; tax data is genuinely predictive of repayment capacity
  3. Train a separate model per time period that uses whichever tax registry is active — operationally untenable; cannot deploy
- **Rationale**: The Cell 10 audit confirmed a **provider-swap pattern**: tax_registry_c (weeks 5–40) → tax_registry_a (weeks 35–67) → tax_registry_b (weeks 67–91). Unifying across providers converts a high-drift signal into a low-drift composite. This is industry-standard treatment for multi-provider bureau data.
- **Risk if wrong**: If the three tax providers actually measure subtly different things (e.g., different income types), unifying them loses precision. Mitigation: validate by comparing the unified feature's predictive power against each individual registry's predictive power on the windows where that registry is present.
- **Reviewer / owner**: Senior DS
- **Status**: Locked
- **Related**: [03_data_understanding.md §B.4](03_data_understanding.md), Phase 3 feature engineering

---

## D09 — Drop credit_bureau_b from feature set

- **Date**: 2026-05-17
- **Phase**: 2 (Data audit, runtime finding)
- **Decision**: Exclude all features derived from `credit_bureau_b_1` and `credit_bureau_b_2` from the modeling feature set.
- **Alternatives considered**:
  1. Include credit_bureau_b features with imputation for the 95% missing — adds noise + a stability risk for negligible signal
  2. Include only as a binary "has credit_bureau_b" indicator — minor signal but adds little value and consumes model capacity
- **Rationale**: Audit Cell 10 shows credit_bureau_b coverage maxes at **5.1% across the entire training period**. At this level of sparsity, any feature derived from credit_bureau_b is dominated by its absence pattern, not its value. The marginal lift is small and the stability risk (b's coverage could move from 5% to 0% in test) is not worth it.
- **Risk if wrong**: If credit_bureau_b actually carries signal we're not seeing in the coverage data, we lose that. Acceptable trade given coverage levels.
- **Reviewer / owner**: Senior DS
- **Status**: Locked
- **Related**: [03_data_understanding.md §B.4](03_data_understanding.md)

---

## D10 — Training-window cutoff at WEEK_NUM = 67 (or treat as regime change)

- **Date**: 2026-05-17
- **Phase**: 2 (Data audit, runtime finding)
- **Decision**: Drop training rows with `WEEK_NUM > 67` from the primary training set, OR treat them as a separate regime requiring separate evaluation. Specifically: rows after WEEK_NUM=67 are confounded by (a) the tax_registry_a → tax_registry_b swap, and (b) the COVID-era right-censoring + forbearance regime that artificially suppresses default rates.
- **Alternatives considered**:
  1. Use the full data through WEEK_NUM=91 — model learns the wrong relationship in the COVID period (low default → easy to predict, but generalizes poorly to post-COVID inference)
  2. Build a separate COVID-period model — operationally complex, low ROI for an engagement-scope decision
  3. Time-weight the loss function down for COVID-period rows — softer version of dropping; requires tuning
- **Rationale**: Two independent forces converge at WEEK_NUM ≈ 65–67: (a) the audit-confirmed tax provider swap, (b) the COVID-19 pandemic onset (~March 2020 corresponds to WEEK_NUM ~65). The combined regime change makes the late-period data fundamentally different from the early-period data. Training on it would teach the model patterns that don't generalize to normal-regime inference.
- **Risk if wrong**: If the post-WEEK_NUM=67 period is actually representative of future inference conditions (e.g., if NovaLend operates in a permanent COVID-influenced regime), dropping it loses generalizable signal. Mitigation: report performance both with and without the cutoff; let the CRO inform whether the deployment context is normal-regime or COVID-influenced regime.
- **Reviewer / owner**: Senior DS (lock), CRO (advisability of cutoff for production regime)
- **Status**: Locked for engagement evaluation; CRO advisability flagged
- **Related**: [03_data_understanding.md §B.3](03_data_understanding.md), industry precedent (OCC bulletin on COVID-era model development)

---

## Reserved slots (decisions expected in upcoming phases)

- D11 — Feature engineering aggregation strategy per depth (Phase 3)
- D12 — Class imbalance handling method (Phase 4)
- D13 — Cross-validation strategy (time-aware vs stratified k-fold) (Phase 4)
- D14 — Hyperparameter tuning approach (Optuna config) (Phase 5)
- D15 — Adverse action reason code methodology (SHAP top-N) (Phase 6)
- D16 — Fairness mitigation method if 4/5 rule fails (Phase 6)
- D17 — Production architecture (Phase 7)
- D18 — Monitoring & retraining cadence (Phase 7)
- D19 — Model card structure for handoff (Phase 8)
