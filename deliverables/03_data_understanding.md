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

✅ **From audit Cells 4–5 (2026-05-17 run)**.

| Metric | Value | Notes |
|---|---|---|
| Row count (training) | ~1,527,000 | Inferred from 12 buckets × 127,221 rows/bucket |
| Date range | 2019-01-01 → 2020-10-05 | ~21 months |
| **Total defaults** | ~53,000 | Sum across buckets |
| **Overall default rate** | **~3.5%** | Sufficient for stable training (well above 1k events threshold) |
| Week range | 0 → ~91 | Approx weekly granularity |

⏳ Still pending from later cells: column count, memory, unique case_id (Cell 4 output not pasted yet).

### B.3 — Default rate over time (H1 test)

✅ **From audit Cell 5 (2026-05-17 run)**.

| Bucket | Date range | N | Default rate |
|---|---|---|---|
| 0 | 2019-01-01 → 2019-02-23 | 127,222 | 2.63% |
| 1 | 2019-02-23 → 2019-04-20 | 127,222 | 2.77% |
| 2 | 2019-04-20 → 2019-06-13 | 127,221 | 3.06% |
| 3 | 2019-06-13 → 2019-07-23 | 127,222 | 2.68% |
| 4 | 2019-07-23 → 2019-09-01 | 127,221 | 2.67% |
| 5 | 2019-09-01 → 2019-10-15 | 127,222 | 3.52% |
| 6 | 2019-10-15 → 2019-11-17 | 127,222 | 3.72% |
| 7 | 2019-11-17 → 2019-12-20 | 127,221 | 3.55% |
| 8 | 2019-12-20 → 2020-01-26 | 127,222 | 3.68% |
| 9 | **2020-01-26 → 2020-03-18** | 127,221 | **4.83%** (peak) |
| 10 | 2020-03-18 → 2020-07-24 | 127,222 | 2.52% (drop) |
| 11 | 2020-07-24 → 2020-10-05 | 127,221 | 2.10% (lowest) |

**Hypothesis H1 result**: ⚠️ **Partially confirmed but muddied by regime change**

- **2019-Q1 through 2020-Q1 (buckets 0–9)**: gradual upward trend from 2.63% → 4.83% over ~14 months. **Confirms the CRO's observation of "default rate creeping up"** in the pre-COVID period.
- **2020-Q2 onward (buckets 10–11)**: dramatic drop to 2.10–2.52%. This is **NOT improvement in borrower quality**. Three forces masking the underlying trend:
  1. **Right-censoring**: applications from this period haven't had the full 24-month observation window to mature
  2. **COVID forbearance**: pandemic-era policy interventions artificially suppressed reported delinquency
  3. **Stimulus payments**: improved short-term cashflow even for marginal borrowers

**Interpretation for CRO**: The pre-COVID portion of the data confirms a real upward drift in default risk — modernization is justified on diagnostic grounds. **However**, the post-COVID buckets are not reliable evidence and **must be excluded from training** or treated as a separate regime. This is a critical modeling decision documented as [D10](99_decisions_log.md#d10).

**Industry-specific note for the board memo**: this same regime-change pattern affected the entire US consumer lending industry in 2020. The OCC and FDIC have explicit guidance on handling COVID-era credit data in model development. NovaLend's situation is not unique.

### B.4 — Source coverage over time (H4 test) — **🚨 the smoking gun**

✅ **From audit Cell 10 (2026-05-17 run)**.

| External source | Min cov | Max cov | Avg cov | Drift range | Pattern |
|---|---|---|---|---|---|
| `static_cb` | 4.51% | 100% | 98.3% | 95.5 | Solid after startup phase (week 5+) |
| `credit_bureau_a_1` | 3.76% | 97.4% | 91.0% | 93.7 | Solid after week 25 |
| **`tax_registry_a`** | **0%** | **78.2%** | 23.8% | 78.2 | 🚨 **Available weeks ~35–67 only**; 0% before and after |
| **`tax_registry_b`** | **0%** | **73.3%** | 18.5% | 73.3 | 🚨 **Available weeks ~67–91 only**; 0% before |
| **`tax_registry_c`** | **0%** | **70.8%** | 27.7% | 70.8 | 🚨 **Available weeks ~5–40 only**; 0% after |
| `credit_bureau_b` | 0% | 5.1% | 2.5% | 5.1 | Effectively absent across entire history |

**Hypothesis H4 result**: ✅ **Confirmed and worse than expected.**

This is **not random drift** — it is a **provider-swap pattern**. NovaLend (or its data supplier) appears to have switched tax data providers twice during the observation period:
- **Weeks 0–35**: tax_registry_c only
- **Weeks 35–40**: brief overlap (c + a)
- **Weeks 40–67**: tax_registry_a only
- **Weeks 67–91**: tax_registry_b only

This is **the smoking gun** for the stability metric: any model relying on individual tax registry columns will see its training and test populations have completely different external-data signatures. This is precisely the failure mode the dataset documentation warned about.

**Board-recommendation implication (drives 3 decisions)**:

1. **D08 (locked)**: Construct a **unified "any tax data" indicator** + **unified tax amount** by max/sum across the three tax registries. This converts a high-drift signal into a low-drift one.
2. **D09 (locked)**: **Drop `credit_bureau_b` from the feature set entirely** — max 5.1% coverage means it's noise, and including it would add stability risk for negligible signal.
3. **D10 (locked)**: **Exclude data after WEEK_NUM = 67** from training, or treat as a separate regime, due to combined effects of (a) the tax_registry_a → tax_registry_b swap and (b) COVID right-censoring.

**Industry note**: provider-swap patterns are common in lending — banks change bureau contracts, regulators force data unbundling, M&A consolidates providers. The defensive pattern (unify across providers) is industry-standard practice for credit bureau data.

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
