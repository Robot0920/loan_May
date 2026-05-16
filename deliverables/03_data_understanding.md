# 03 — Data Understanding

> **Status**: Eyeballing complete · Audit execution pending · **Phase**: 2 · **Last updated**: 2026-05-15
> **Methodology applied**: [interview_prep/00_consulting_methodology.md](../interview_prep/00_consulting_methodology.md) Part 2
> **Related**: [02_problem_framing.md](02_problem_framing.md) · [04_data_gaps.md](04_data_gaps.md) · [notebooks/01_data_audit.py](../notebooks/01_data_audit.py)

This deliverable has two layers:
- **Layer A — Eyeballing findings**: derived from dataset documentation, schema, and naming conventions *without writing code*. Already complete.
- **Layer B — Runtime audit findings**: produced by [notebooks/01_data_audit.py](../notebooks/01_data_audit.py) on Kaggle. Placeholders are clearly marked with `⏳ TO BE FILLED FROM AUDIT RUN`. The user runs the audit on Kaggle and pastes the resulting numbers back.

The audit method is itself a deliverable. See [00_audit_methodology.md](00_audit_methodology.md) (TBD) for the framework.

---

## Layer A — Eyeballing findings (no code)

### A.1 — Data ecosystem inventory

**Source**: Home Credit Credit Risk Model Stability (Kaggle competition, 2024), used as the analytical stand-in for NovaLend's loan-decisioning data.

**Total scale**: 26.77 GB, 138 files, **2,588 columns** across all tables, **465 unique features defined** in `feature_definitions.csv`. Train and test mirror the same schema.

**Provenance breakdown** (eyeballed from dataset docs):

| Source family | Tables | Provider | Risk implication |
|---|---|---|---|
| **Internal — NovaLend systems** | `base`, `static_0`, `applprev_1`, `applprev_2`, `other_1`, `deposit_1`, `person_1`, `person_2`, `debitcard_1` | NovaLend | High control, low schema risk |
| **External — Tax Registry A** | `tax_registry_a_1` | Third-party provider A | Coverage may drift; warned by docs |
| **External — Tax Registry B** | `tax_registry_b_1` | Third-party provider B | Coverage may drift; warned by docs |
| **External — Tax Registry C** | `tax_registry_c_1` | Third-party provider C | Coverage may drift; warned by docs |
| **External — Credit Bureau A** | `credit_bureau_a_1`, `credit_bureau_a_2`, `static_cb_0` | Bureau A | Largest external source (11+11 shards on depth-2) |
| **External — Credit Bureau B** | `credit_bureau_b_1`, `credit_bureau_b_2` | Bureau B | Secondary bureau |

> **🚩 Senior observation (high-value)**: The dataset documentation contains a critical caveat: *"some external data providers might not be available for future (test) evaluations, which is anticipated."*
>
> **Implication**: Train and test schema are not guaranteed identical at the external-source level. A model that leans heavily on tax_registry_b or credit_bureau_b features will look great in CV and fail catastrophically on test. **This is precisely the stability problem the competition metric is designed to penalize.**
>
> **Action enforced downstream**: In feature engineering ([05_feature_catalog.md](05_feature_catalog.md)), every feature derived from an external source receives a **stability-risk score** based on its source's test coverage. Features from high-risk sources get a penalty multiplier on their importance ranking before final feature selection.

### A.2 — Grain semantics (from docs, not from data)

The dataset uses an **explicit depth convention** documented in the dataset description:

| Depth | Meaning | Join strategy |
|---|---|---|
| **0** | One row per `case_id` (application-level) | Direct left join onto base table |
| **1** | One row per `case_id` per child entity, indexed by `num_group1` | **Must aggregate** before joining; aggregation strategy = feature engineering decision |
| **2** | One row per `case_id` per child entity per month, indexed by `num_group1` × `num_group2` | **Must aggregate twice** (typically: temporal aggregation → entity aggregation → applicant aggregation) |

**Special semantic**: `num_groupN = 0` denotes the **applicant themselves**, with `num_groupN > 0` denoting related parties (co-applicants, household members).

> **🚩 Senior observation**: This special semantic means person-table aggregation cannot be "one size fits all". The applicant's own features (where `num_groupN = 0`) should be treated as **depth-0 features** (direct join). Related-party features (where `num_groupN > 0`) should be **aggregated** (count, max, sum). A naive aggregation that includes the applicant's own row in the same aggregate is incorrect.

### A.3 — Column naming conventions (free dtype information)

The dataset uses **suffix conventions** documented in the dataset description that encode column transformations:

| Suffix | Meaning | Treatment |
|---|---|---|
| `_P` | DPD (Days Past Due) transform | Highly predictive; numeric; treat as continuous |
| `_A` | Amount transform | Numeric; may need log-transform |
| `_D` | Date transform | Compute `days_since_application` relative to `date_decision` |
| `_M` | Masked categorical | Categorical; encode (target / ordinal / one-hot per cardinality) |
| `_T` | Unspecified transform | Inspect case-by-case |
| `_L` | Unspecified transform | Inspect case-by-case |

> **🚩 Senior move**: Write a single parser that takes any column name and returns `(dtype, transform_family, recommended_treatment)`. Apply across all 2,588 columns at once instead of inspecting them individually. This is implemented in `src/data/schema.py` (TBD next pass).

### A.4 — Special columns (anchor points)

Per the dataset documentation:

| Column | Role | Why it matters |
|---|---|---|
| `case_id` | Unique application identifier | Join key for every other table |
| `date_decision` | Application / decision date | **The temporal anchor**. Every feature must be computable strictly before this date — leakage prevention pivots on this |
| `WEEK_NUM` | Week index for aggregation | Used by the competition's stability metric |
| `MONTH` | Month index for aggregation | Coarser temporal window |
| `target` | Binary default outcome | What we predict (see [02_problem_framing.md](02_problem_framing.md)) |
| `num_group1`, `num_group2` | Child-entity indices for depth ≥ 1 tables | Drive aggregation strategy |

### A.5 — Already-identified data gaps (write up in [04_data_gaps.md](04_data_gaps.md))

From eyeballing alone, four data gaps are already evident:

1. **No applicant-declined outcome data** — standard survivorship bias issue (also flagged in `02_problem_framing.md`)
2. **No real-time bureau pull capability** — we work off snapshots, not live data
3. **No macroeconomic context** — must be added from public sources (Fed funds, unemployment) for any macro-overlay work
4. **Limited geographic granularity** — state-level at best, no ZIP — limits fair-lending audit on geographic disparate impact

---

## Layer B — Runtime audit findings (filled in after Kaggle execution)

Numbers in this section come from running [notebooks/01_data_audit.py](../notebooks/01_data_audit.py) on Kaggle. The notebook is structured to test the eyeballing hypotheses above, not to do blind profiling.

### B.1 — Table inventory & shape

⏳ **TO BE FILLED FROM AUDIT RUN** — output of `notebooks/01_data_audit.py` Cell 2.

Expected table (paste from notebook output):

```
TABLE                              SHARDS   DEPTH
-----------------------------------------------
base                                    1       0
static_0                                ?       0
static_cb_0                             1       0
applprev_1                              2       1
applprev_2                              1       2
credit_bureau_a_1                       4       1
credit_bureau_a_2                      11       2
credit_bureau_b_1                       1       1
credit_bureau_b_2                       1       2
debitcard_1                             1       1
deposit_1                               1       1
other_1                                 1       1
person_1                                1       1
person_2                                1       2
tax_registry_a_1                        1       1
tax_registry_b_1                        1       1
tax_registry_c_1                        1       1
```

### B.2 — Base table profile

⏳ **TO BE FILLED** — output of Cell 3.

| Metric | Value |
|---|---|
| Row count (training) | `(fill in)` |
| Column count | `(fill in)` |
| Memory footprint (MB) | `(fill in)` |
| Unique `case_id` | `(fill in)` |
| Target positive count | `(fill in)` |
| **Default rate** | `(fill in)` |
| Date range (`date_decision` min → max) | `(fill in)` |
| Week range (`WEEK_NUM` min → max) | `(fill in)` |

### B.3 — Default rate over time (H1 test)

⏳ **TO BE FILLED** — output of Cell 4.

| Time bucket | Date range | N | Default rate |
|---|---|---|---|
| `(fill in)` | | | |

**Hypothesis H1 result**: ⏳ TBD
- If default rate is **rising** across vintages → concept drift / scorecard staleness story (H1 confirmed)
- If **flat** → defect is segment-specific, not population-wide (H1 rejected; pivot to H2)
- **Either way is a finding**, because it disambiguates the CRO's question

**Interpretation for CRO**: ⏳ TBD

### B.4 — Source coverage over time (H4 test)

⏳ **TO BE FILLED** — requires audit-code refactor (next pass) to add per-source coverage.

| External source | Train coverage % | Trend over time | Test coverage (if visible) | Stability risk |
|---|---|---|---|---|
| tax_registry_a_1 | | | | |
| tax_registry_b_1 | | | | |
| tax_registry_c_1 | | | | |
| credit_bureau_a_1 | | | | |
| credit_bureau_a_2 | | | | |
| credit_bureau_b_1 | | | | |
| credit_bureau_b_2 | | | | |

### B.5 — Per-table grain check

⏳ **TO BE FILLED** — output of Cell 5.

For each table: rows / unique case_ids / rows-per-id / is_one_to_one. Confirms our **depth assignments** from the docs are correct. A surprise (depth-0 table that's actually 1:N, or depth-1 table that's 1:1) is itself a finding worth investigating.

### B.6 — High-missingness columns

⏳ **TO BE FILLED** — output of Cell 6.

Per table, columns with > 50% null. The interesting question is **whether missingness correlates with target** — that turns missingness into a feature, not a bug.

### B.7 — Column type breakdown by suffix (H3 / general)

⏳ **TO BE FILLED** — requires audit-code refactor.

| Suffix | Count of columns | Sample (first 5) | Recommended treatment |
|---|---|---|---|
| `_P` | | | continuous numeric, no transform |
| `_A` | | | continuous, candidate for log transform |
| `_D` | | | parse to date, compute days_since_application |
| `_M` | | | categorical, encode by cardinality |
| `_T` | | | inspect |
| `_L` | | | inspect |
| (no suffix) | | | inspect — likely special columns |

---

## What this deliverable enables downstream

| Downstream artifact | What it pulls from here |
|---|---|
| [04_data_gaps.md](04_data_gaps.md) | Section A.5 (eyeballed gaps), plus any runtime gaps from Layer B |
| [05_feature_catalog.md](05_feature_catalog.md) | Section A.3 (suffix conventions drive feature treatment per type), Section A.2 (grain drives aggregation strategy), Section B.4 (source stability penalties) |
| [02_problem_framing.md](02_problem_framing.md) — Hypotheses | Hypotheses H1–H5 are tested by sections B.3, B.4 |
| [99_decisions_log.md](99_decisions_log.md) | Any non-obvious treatment decision (e.g., "drop tax_registry_b because coverage drifts > 20% from train to test") |

---

## Status checklist

- [x] Layer A — eyeballing complete
- [ ] Layer B.1 — table inventory (run Cell 2)
- [ ] Layer B.2 — base profile (run Cell 3)
- [ ] Layer B.3 — default rate over time (run Cell 4)
- [ ] Layer B.4 — source coverage (requires audit refactor)
- [ ] Layer B.5 — grain check (run Cell 5)
- [ ] Layer B.6 — missingness (run Cell 6)
- [ ] Layer B.7 — suffix breakdown (requires audit refactor)
- [ ] Hypotheses H1–H5 explicitly resolved (test in B.3, B.4, B.7)
- [ ] Update [04_data_gaps.md](04_data_gaps.md) with any runtime gaps
- [ ] Update [99_decisions_log.md](99_decisions_log.md) with any treatment decisions
