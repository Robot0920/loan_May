# CODEBASE — file-by-file inventory

> **Purpose**: One place to look up what every file in this repo is for, who reads it, and whether it stays around long-term or gets refactored out as the engagement matures.
>
> **How to read**: Files are tagged with a **role** label.

## Role labels

| Label | Meaning |
|---|---|
| 🎯 **DELIVERABLE** | Client-facing artifact. Stays in repo, ends up in the board memo or appendix. Lives in `deliverables/`. |
| ⚙️ **CODE** | Production-style Python module. Pure functions, tested. Stays in repo. Lives in `src/`. |
| 📊 **NOTEBOOK** | Analysis script (`.py` with `# %%` cells). Run on Kaggle to produce findings. Stays in repo as a methodology artifact. Lives in `notebooks/`. |
| 📋 **PLAYBOOK** | Strategic / methodology reference. Used to plan and defend work. Stays in repo. |
| 🎓 **PRACTICE** | Personal interview-prep notes. Side resource, can be removed without affecting the engagement. Lives in `interview_prep/`. |
| 🔧 **CONFIG** | Project configuration (build, deps, ignore). Stays in repo. |
| 🚫 **GITIGNORED** | Not in version control. Local-only or generated. |

---

## Root level

| File | Role | Notes |
|---|---|---|
| [README.md](README.md) | 📋 PLAYBOOK | Entry point. Project overview, dev loop, folder map. |
| [CODEBASE.md](CODEBASE.md) | 📋 PLAYBOOK | This file. File-by-file inventory. |
| [credit_risk_system_roadmap.md](credit_risk_system_roadmap.md) | 📋 PLAYBOOK | The strategic 10-phase engagement plan. Pre-dates the refactored repo; treat as the master strategy doc. |
| [requirements.txt](requirements.txt) | 🔧 CONFIG | Python dependencies. Used both for local `pip install` (if you do linting locally) and as the dependency list for Kaggle to install via `!pip install -r`. |
| [.gitignore](.gitignore) | 🔧 CONFIG | Excludes raw data, model artifacts, secrets, IDE folders. |
| `pyproject.toml` | 🔧 CONFIG | (TBD — not yet written) For ruff config + package metadata. |

---

## `deliverables/` — 🎯 client-facing portfolio (the engagement product)

All files in this folder are docs because **the client gets docs, not code**. Code is the engineering artifact that *produced* the docs; the docs are what land in front of the CRO, board, and OCC.

| File | Status | Audience | What it contains |
|---|---|---|---|
| [01_engagement_charter.md](deliverables/01_engagement_charter.md) | ✅ done | CRO, partner, EM | Client context, decision the engagement informs, in/out scope, success criteria, stakeholder map, timeline, operating principles |
| [02_problem_framing.md](deliverables/02_problem_framing.md) | ✅ done | CRO, model risk reviewer | The decision sentence; MECE sub-problem decomposition; target choice + rationale + rejected alternatives; 4-layer evaluation framework; H1–H5 hypotheses |
| [03_data_understanding.md](deliverables/03_data_understanding.md) | 🟡 Layer A done, Layer B awaiting audit run | CRO, model risk, data engineering | Eyeballing findings (provenance, grain, naming, suffix conventions, special semantics) + placeholders for runtime audit findings |
| [99_decisions_log.md](deliverables/99_decisions_log.md) | 🟡 D01–D07 logged, D08–D16 reserved | Model risk reviewer (primary), engagement team | Every non-obvious decision with date, rationale, rejected alternatives, risk if wrong |

### Planned future deliverables (consolidated structure — won't fragment further)

| Future file | What goes in | When |
|---|---|---|
| `04_model_build.md` | Feature catalog + model methodology + evaluation framework details + tuning approach | After Phase 4 |
| `05_validation.md` | Fairness audit + stability analysis + business simulation + risk register | After Phase 5 |
| `06_compliance_governance.md` | SR 11-7 mapping + ECOA/Reg B + NIST AI RMF + governance posture + security/PII | After Phase 6 |
| `07_recommendation.md` | Production architecture + monitoring plan + A/B test design + final board memo + future work | After Phase 7 |

**Total when complete: 8 deliverables + decisions log.** Down from the originally-sketched 15+ files.

---

## `src/` — ⚙️ engineering code (the analysis engine)

Layered architecture: I/O → semantics → diagnostics. Each layer importable independently. All functions pure (no global state).

| File | Role | What it does |
|---|---|---|
| [src/__init__.py](src/__init__.py) | ⚙️ CODE | Empty — makes `src` a package |
| [src/config.py](src/config.py) | ⚙️ CODE | **Environment**: resolves `DATA_DIR` from env var with Kaggle / local fallback; column-name constants (ID_COL, TARGET_COL, etc.); thresholds (PSI, missingness). Single source of truth for "what file is where". |
| [src/data/__init__.py](src/data/__init__.py) | ⚙️ CODE | Empty — makes `src.data` a sub-package |
| [src/data/load.py](src/data/load.py) | ⚙️ CODE | **I/O layer**. `list_tables()`, `load_table()`, `scan_table()`, `load_base()`. Handles sharded multi-table schema. Knows nothing about meaning. |
| [src/data/schema.py](src/data/schema.py) | ⚙️ CODE | **Semantics layer**. Parses `_P/_A/_D/_M/_T/_L` naming convention. Loads `feature_definitions.csv`. Builds the feature dictionary. Infers internal-vs-external source family per table. Takes already-loaded data, adds meaning. |
| [src/data/validate.py](src/data/validate.py) | ⚙️ CODE | **Diagnostics layer**. `table_summary`, `grain_check`, `target_distribution`, `time_coverage`, `missingness_report`, `time_split_audit` (H1), `source_coverage_over_time` (H4), `default_rate_by_segment` (H2), `population_stability_index`. Each function answers one board-relevant question. |

### Future src/ modules (planned, not yet written)

| Future file | Will contain |
|---|---|
| `src/data/join.py` | Aggregation patterns for depth-1 and depth-2 tables onto the base spine |
| `src/features/__init__.py` + subfiles (`temporal.py`, `aggregation.py`, `ratio.py`, `missingness.py`) | Feature engineering by category |
| `src/models/baseline_logistic.py` | Interpretable benchmark model (SR 11-7 challenger) |
| `src/models/gbm.py` | Champion LightGBM model with monotonic constraints |
| `src/evaluation/` (`metrics.py`, `stability.py`, `business_sim.py`, `fairness.py`) | The 4-layer evaluation framework |
| `src/explainability/shap_explainer.py` + `adverse_action.py` | SHAP-derived reason codes for ECOA |
| `src/serving/api.py` + `schemas.py` | FastAPI inference endpoint (Phase 7) |
| `src/monitoring/drift.py` + `performance.py` | Drift detection + performance monitoring jobs |

---

## `notebooks/` — 📊 analysis scripts (Kaggle-runnable)

Stored as `.py` files with `# %%` cell markers, **not** `.ipynb`. Two reasons: (1) git-diffable, (2) avoid the JSON merge-conflict hell of native notebooks. Convert to `.ipynb` with `jupytext --to ipynb` if you want to upload to Kaggle directly.

| File | Status | Bound to which phase | Notes |
|---|---|---|---|
| [notebooks/01_data_audit.py](notebooks/01_data_audit.py) | ✅ done | Phase 2 | 12 cells organized by board question (Foundation → Q1 diagnostic → Q3 limitations → Q4 stability). |

### Future notebooks (planned)

| Future file | Phase | What it does |
|---|---|---|
| `02_eda.py` | 3 | Application-level EDA, target relations, temporal feature drift, segment decomposition |
| `03_baseline_logistic.py` | 3 | Logistic regression with hand-picked features → SR 11-7 interpretable benchmark |
| `04_feature_engineering.py` | 3 | Build the full feature matrix from depth-0/1/2 tables |
| `05_gbm_modeling.py` | 4 | LightGBM champion model with monotonic constraints + Optuna tuning |
| `06_stability_analysis.py` | 5 | Walk-forward validation; PSI per feature; per-quarter Gini variance |
| `07_business_simulation.py` | 5 | Convert predictions to dollar impact at portfolio level vs legacy scorecard |
| `08_fairness_audit.py` | 6 | Fairlearn audit: 4/5 rule, demographic parity, equal opportunity, calibration parity |
| `09_shap_analysis.py` | 6 | SHAP TreeExplainer → top-N reason codes for adverse action |

---

## `interview_prep/` — 🎓 personal practice toolkit (side resource)

Two files only. **Can be deleted without affecting the engagement.** Kept because the methodology is the most transferable skill the project teaches.

| File | What it is | When to read |
|---|---|---|
| [00_consulting_methodology.md](interview_prep/00_consulting_methodology.md) | The 5-module methodology toolkit: goal decomposition → data understanding → target selection → EDA design → insight generation. Transferable across any tech-consulting DS engagement (not just credit risk). | Read first when prepping for any technical case interview. |
| [01_worked_examples.md](interview_prep/01_worked_examples.md) | Three worked examples of goal-to-target decomposition (grow book / reduce losses / automate underwriting). Drills the "target is reverse-engineered from the decision" principle. | After reading 00, when you want to see the methodology applied. |

---

## `data/` — 🚫 gitignored (lives on Kaggle)

| Path | Role | Notes |
|---|---|---|
| [data/README.md](data/README.md) | 📋 PLAYBOOK | Kaggle setup steps + the schema reference (suffix conventions, anchor columns) |
| `data/raw/`, `data/interim/`, `data/processed/`, `data/external/` | 🚫 GITIGNORED | Empty placeholders. Real data lives on Kaggle's servers (`/kaggle/input/...`); processed outputs live in Kaggle's `/kaggle/working/` per session. Only `.gitkeep` files committed. |

---

## Empty / placeholder folders

These exist for future phase work. They are committed but currently empty:

| Folder | Will contain | Phase |
|---|---|---|
| `tests/` | Unit tests for `src/` modules (SR 11-7 implementation verification) | 4+ |
| `deployment/` | Dockerfile, docker-compose for the inference API | 7 |
| `scripts/` | One-shot CLI utilities (e.g., bulk data download, model packaging) | as needed |

---

## "Keep / paste-and-delete" map (the question you asked)

| What | Status | When to remove |
|---|---|---|
| All `deliverables/*.md` | 🟢 **keep forever** | Never. These are the engagement product. |
| All `src/**/*.py` | 🟢 **keep forever** | Refactor as the project matures, but the modules stay. |
| `notebooks/01_data_audit.py` | 🟢 **keep forever** | Stays as methodology artifact (shows how the audit was done). |
| `interview_prep/*.md` | 🟡 **keep as long as useful** | Delete when you're done interview-prepping. Doesn't affect the engagement repo. |
| `credit_risk_system_roadmap.md` | 🟢 **keep forever** | The strategic backbone; will reference it from the final memo. |
| `README.md`, `CODEBASE.md` | 🟢 **keep forever** | Entry points. |
| `data/raw/.gitkeep` files | 🟢 keep | Just placeholders so empty folders are versioned. |
| `data/raw/*.parquet` (if you ever download locally) | 🚫 never commit | Gitignored. |
| Kaggle notebook cells (in Kaggle UI, not in this repo) | 🟡 **paste-and-delete after audit run** | Each session in Kaggle is ephemeral. The `.py` files in this repo are the source of truth; the Kaggle notebook is just an execution shell. |

### The "paste-and-delete" pattern specifically

When you run [notebooks/01_data_audit.py](notebooks/01_data_audit.py) on Kaggle:

1. The cells in the `.py` file are the **source code**.
2. You paste them into Kaggle as **execution cells** (one cell per `# %%` block).
3. The Kaggle cells produce **results** (numbers, charts).
4. You copy the **results** back into `deliverables/03_data_understanding.md` Layer B.
5. The Kaggle session itself is throwaway — when Kaggle expires the session, the cells go with it. No loss; the source of truth is the `.py` file.

If you make changes to the analysis WHILE in Kaggle (you find a bug, you adjust a parameter), **save those changes back to the `.py` file in VSCode** and re-push. The Kaggle notebook is a workspace; the `.py` file is the deliverable.

---

## Quick reference: where do I add new work?

| I want to... | Where it goes |
|---|---|
| Add a new audit / EDA function | `src/data/validate.py` (if diagnostic) or new module in `src/features/` (if feature engineering) |
| Run a new analysis | New `.py` file in `notebooks/` numbered next in sequence (`02_eda.py`, `03_baseline.py`, etc.) |
| Log a non-obvious decision | New entry in `deliverables/99_decisions_log.md` |
| Document a finding | The relevant section of `deliverables/03_data_understanding.md` (audit findings) or future `04_model_build.md` / `05_validation.md` |
| Record a new data gap | Add to `deliverables/03_data_understanding.md` section A.5 (gaps live inside data understanding, no separate file) |
| Practice an interview drill | `interview_prep/01_worked_examples.md` — add a new worked example using the template at the bottom |
| Update the strategic plan | `credit_risk_system_roadmap.md` |
