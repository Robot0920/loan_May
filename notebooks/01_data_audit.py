# ---
# title: 01 — Data Audit
# purpose: First pass against the Home Credit 2024 dataset. Confirms what tables
#   exist, their grain, missingness, target distribution, and temporal coverage.
#   Output feeds deliverables/03_data_understanding.md.
# runs_on: Kaggle Notebook (data mounted at /kaggle/input/...)
# usage:
#   In a Kaggle notebook, after running the bootstrap cell that clones this repo
#   and sets sys.path, copy each `# %% cell` block below into its own notebook cell.
#   (Or use jupytext to convert: `jupytext --to ipynb 01_data_audit.py`.)
# ---

# %% [markdown]
# # Phase 2 — Data Audit (Engagement Day 2)
#
# We have NovaLend's data delivered via the Home Credit Credit Risk Model Stability
# competition (Kaggle, 2024) as our stand-in. Before any modeling we need to
# answer six diagnostic questions:
#
# 1. What tables exist and what is each table's grain (1:1, 1:N, 1:N:M with case_id)?
# 2. What is the target distribution and is it stable over time?
# 3. What is the temporal coverage and are there gaps?
# 4. Which columns have high missingness, and is missingness informative?
# 5. Are there leakage candidates (fields known only after application date)?
# 6. Which fields are PII or protected attributes (age, gender, location)?
#
# Findings from this notebook get written up in
# `deliverables/03_data_understanding.md`.

# %% [markdown]
# ## Cell 0 — Repo + path bootstrap
# (Run this once per Kaggle session. Skip if you already ran it earlier.)

# %%
import sys, os, subprocess

REPO_DIR = "/kaggle/working/loan_May"
if not os.path.exists(REPO_DIR):
    subprocess.run(["git", "clone", "https://github.com/Robot0920/loan_May.git", REPO_DIR], check=True)
else:
    subprocess.run(["git", "-C", REPO_DIR, "pull"], check=True)

# Put repo root on path so `from src.X import Y` works
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

# %% [markdown]
# ## Cell 1 — Inspect what's actually in `/kaggle/input/`

# %%
from src.config import DATA_DIR, TRAIN_DIR, TEST_DIR
print(f"DATA_DIR  = {DATA_DIR}  exists={DATA_DIR.exists()}")
print(f"TRAIN_DIR = {TRAIN_DIR} exists={TRAIN_DIR.exists()}")
print(f"TEST_DIR  = {TEST_DIR}  exists={TEST_DIR.exists()}")

# If TRAIN_DIR doesn't exist, the dataset isn't attached. Use Add Input on the right
# sidebar in the Kaggle UI and pick "Home Credit - Credit Risk Model Stability"
# (the one with ~3800 teams, marked Featured).

# %% [markdown]
# ## Cell 2 — Enumerate logical tables and their shard counts

# %%
from src.data.load import list_tables, table_depth

tables = list_tables(TRAIN_DIR)
print(f"{'TABLE':<35} {'SHARDS':>8} {'DEPTH':>6}")
print("-" * 53)
for name in sorted(tables.keys()):
    print(f"{name:<35} {len(tables[name]):>8} {table_depth(name):>6}")

# Depth legend:
#   0 = application-level (one row per case_id) → safe to left-join
#   1 = one row per child entity per case_id (prior credit, prior application) → aggregate first
#   2 = monthly grain (one row per child entity per case_id per month) → aggregate twice

# %% [markdown]
# ## Cell 3 — Load the base table (the spine)
# Has `case_id`, `date_decision`, `WEEK_NUM`, `MONTH`, and the binary `target`.

# %%
from src.data.load import load_base
from src.data.validate import table_summary, target_distribution, time_coverage, grain_check

base = load_base(TRAIN_DIR)
print("Summary:", table_summary(base, "base"))
print()
print("Grain check on case_id:", grain_check(base))
print()
print("Target distribution:", target_distribution(base))
print()
print("Time coverage:", time_coverage(base))

# %% [markdown]
# ## Cell 4 — Default rate over time
# This is the *first* meaningful business signal. If the default rate trends
# upward across vintages, that's the macro / scorecard staleness diagnostic
# the CRO asked about. If it's flat, the rising default rate at NovaLend is
# either book-mix or specific segments — not population-wide drift.

# %%
from src.data.validate import time_split_audit

trend = time_split_audit(base, n_buckets=12)
print(trend)

# Plot it
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(9, 4))
trend_pd = trend.to_pandas()
ax.bar(trend_pd["bucket"], trend_pd["default_rate"], color="steelblue")
ax.set_xlabel("Time bucket (equal-sized)")
ax.set_ylabel("Default rate")
ax.set_title("Default rate across time buckets — drift diagnostic")
ax.set_xticks(trend_pd["bucket"])
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Cell 5 — Per-table summary (shape, missingness, grain)
# Loops over every depth-0 and depth-1 table. Skip depth-2 (monthly) for now —
# they're huge and we'll audit them in a separate pass after we've made join decisions.

# %%
from src.data.load import load_table
from src.data.validate import missingness_report

summaries = []
high_missing_by_table = {}

for name in sorted(tables.keys()):
    if table_depth(name) == 2:
        continue  # defer monthly tables
    if name == "base":
        continue  # already audited
    try:
        df = load_table(name, TRAIN_DIR)
    except Exception as e:
        print(f"[skip] {name}: {e}")
        continue
    summaries.append({**table_summary(df, name), **grain_check(df)})
    hm = missingness_report(df, threshold=0.50)
    if hm.height > 0:
        high_missing_by_table[name] = hm

import pandas as pd
print(pd.DataFrame(summaries).to_string(index=False))

# %% [markdown]
# ## Cell 6 — Columns with > 50% missingness (per table)
# Missingness > 50% is a candidate for either drop or "missingness indicator only"
# treatment. The interesting follow-up is whether missingness *correlates with
# target* — if it does, the missingness itself is the feature, not the value.

# %%
for name, hm in high_missing_by_table.items():
    print(f"\n=== {name} ({hm.height} cols with >50% missingness) ===")
    print(hm.head(15))

# %% [markdown]
# ## Cell 7 — Save audit outputs to /kaggle/working/ for later commit
# These get copied/pasted into `deliverables/03_data_understanding.md` (manual)
# or written to disk and committed back via the Kaggle ↔ GitHub link.

# %%
from src.config import ensure_work_dirs, INTERIM_DIR
ensure_work_dirs()

pd.DataFrame(summaries).to_csv(INTERIM_DIR / "audit_table_summaries.csv", index=False)
trend.write_csv(INTERIM_DIR / "audit_default_rate_trend.csv")
print(f"Wrote audit outputs to {INTERIM_DIR}")

# %% [markdown]
# ## What to do next
#
# 1. Copy the numbers from Cell 3, Cell 4 (default rate trend), and Cell 5
#    (table grain/shape) into `deliverables/03_data_understanding.md`.
# 2. From Cell 4: if default rate trends upward, note it as the "drift diagnostic"
#    finding that addresses the CRO's question. If flat, document that too — equally
#    important finding.
# 3. From Cell 6: pick the top 5 high-missingness columns and add a `TODO` to
#    `deliverables/04_data_gaps.md` to investigate whether missingness predicts target.
# 4. Move to `notebooks/02_eda.py` for deeper exploration of the application-level
#    features.
