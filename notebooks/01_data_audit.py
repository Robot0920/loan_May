# ---
# title: 01 — Data Audit (board-question driven)
# purpose: Audit the Home Credit 2024 dataset. Cells are ordered by their binding
#   to the board recommendation, not by table convenience. Findings flow into
#   deliverables/03_data_understanding.md Layer B.
# runs_on: Kaggle Notebook (data mounted under /kaggle/input/...)
#
# CELL ORDER (board-question driven):
#   Cell 0   bootstrap: clone repo + sys.path
#   Cell 1   foundation: confirm data attached
#   Cell 2   foundation: load feature dictionary (the 'free' metadata)
#   Cell 3   foundation: list tables + infer source family per table
#   ---- Q1 DIAGNOSTIC: is the legacy scorecard broken or is the world different? ----
#   Cell 4   base table profile (rows, default rate, time range)
#   Cell 5   H1 — default rate trend across vintages
#   Cell 6   H2 — default rate decomposition by segment × time
#   ---- Q3 DATA LIMITATIONS: what constrains the recommendation? ----
#   Cell 7   per-table grain check (depth confirmation)
#   Cell 8   high-missingness columns
#   Cell 9   H3 / general — column-suffix breakdown (feature-engineering scope)
#   ---- Q4 STABILITY / GOVERNANCE: what to monitor? ----
#   Cell 10  H4 — external-source coverage drift over WEEK_NUM
#   ---- OUTPUT ----
#   Cell 11  save audit outputs to /kaggle/working/loan_May/data/interim/
#   Cell 12  (markdown) what to copy into deliverables/03_data_understanding.md
# ---

# %% [markdown]
# # Data Audit — Phase 2
#
# Each cell below is bound to one of four board-recommendation questions:
#
# - **Q1 (diagnostic)** — Is the legacy scorecard broken, or is the world different?
# - **Q3 (data limitations)** — What constrains the recommendation?
# - **Q4 (stability / governance)** — What to monitor in production?
#
# (Q2 — projected business impact — is answered by modeling, not audit.)
#
# Findings populate `deliverables/03_data_understanding.md` Layer B.

# %% [markdown]
# ## Cell 0 — Bootstrap (clone repo + path setup)
# Run this once per Kaggle session.

# %%
import sys, os, subprocess
REPO = "/kaggle/working/loan_May"
if os.path.exists(REPO):
    subprocess.run(["git", "-C", REPO, "pull"], check=True)
else:
    subprocess.run(["git", "clone", "https://github.com/Robot0920/loan_May.git", REPO], check=True)
if REPO not in sys.path:
    sys.path.insert(0, REPO)
print("Repo at:", REPO)
print("sys.path[0]:", sys.path[0])

# %% [markdown]
# ## Cell 1 — Foundation: confirm data is attached

# %%
from src.config import DATA_DIR, TRAIN_DIR, TEST_DIR
print(f"DATA_DIR  = {DATA_DIR}  exists={DATA_DIR.exists()}")
print(f"TRAIN_DIR = {TRAIN_DIR} exists={TRAIN_DIR.exists()}")
print(f"TEST_DIR  = {TEST_DIR}  exists={TEST_DIR.exists()}")
assert DATA_DIR.exists(), "Dataset not attached. Use 'Add Input' in Kaggle UI."

# %% [markdown]
# ## Cell 2 — Foundation: load the official feature dictionary
#
# **Free information**: the dataset ships with `feature_definitions.csv` (465 unique
# variables documented by the competition organizers). We load it and merge with our
# suffix-parsed metadata to classify each feature by dtype family without inspecting
# the data itself.

# %%
from src.data.schema import build_feature_dictionary, suffix_breakdown

feature_dict = build_feature_dictionary(DATA_DIR)
print(f"Loaded {feature_dict.height} feature definitions.")
print()
print("Sample:")
print(feature_dict.head(8))
print()
print("Breakdown by suffix (free dtype classification):")
print(suffix_breakdown(feature_dict["Variable"].to_list()))

# %% [markdown]
# ## Cell 3 — Foundation: list tables and infer source families
#
# For each logical table, infer whether it's internal (NovaLend) or external (third
# party). External sources are the **stability risk** flagged in the dataset docs.

# %%
from src.data.load import list_tables, table_depth
from src.data.schema import infer_source_family
import pandas as pd

tables = list_tables(TRAIN_DIR)
table_rows = []
for name in sorted(tables.keys()):
    source_kind, provider = infer_source_family(name)
    table_rows.append({
        "table": name,
        "shards": len(tables[name]),
        "depth": table_depth(name),
        "source_kind": source_kind,
        "provider": provider,
    })
table_df = pd.DataFrame(table_rows)
print(table_df.to_string(index=False))

print()
print(f"Internal tables: {(table_df.source_kind == 'internal').sum()}")
print(f"External tables: {(table_df.source_kind == 'external').sum()}")
print(f"External providers represented: {table_df[table_df.source_kind == 'external'].provider.nunique()}")

# %% [markdown]
# ---
# # Q1 (DIAGNOSTIC) — Is the legacy scorecard broken or is the world different?
# ---

# %% [markdown]
# ## Cell 4 — Base table profile (foundation for Q1)
#
# Confirms we have enough data to model at all, and surfaces the headline numbers
# the board memo will lead with: total applications, default rate, time range.

# %%
from src.data.load import load_base
from src.data.validate import table_summary, target_distribution, time_coverage, grain_check

base = load_base(TRAIN_DIR)
print("=== Base table summary ===")
print(table_summary(base, "base"))
print()
print("=== Grain check on case_id ===")
print(grain_check(base))
print()
print("=== Target distribution ===")
print(target_distribution(base))
print()
print("=== Time coverage ===")
print(time_coverage(base))

# %% [markdown]
# ## Cell 5 — H1: default rate across vintages
#
# > **Hypothesis H1**: Default rate is rising across vintages (concept drift / scorecard staleness).
# > Falsifying observation: a flat trend across time buckets.
#
# **If trending up** → "the scorecard is failing as the population changes" → modernization
# justified on diagnostic grounds.
# **If flat** → the rising book-wide default rate is segment-specific or operational, not a
# model-decay story → modernization motivation weakens; recommend deeper investigation.
#
# Either result is **directly board-relevant**.

# %%
from src.data.validate import time_split_audit
import matplotlib.pyplot as plt

trend = time_split_audit(base, n_buckets=12)
print(trend)

trend_pd = trend.to_pandas()
fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(trend_pd["bucket"], trend_pd["default_rate"], color="steelblue")
ax.set_xlabel("Time bucket (equal-row, oldest → newest)")
ax.set_ylabel("Default rate")
ax.set_title("H1: Default rate over time — diagnostic for the CRO's question")
ax.set_xticks(trend_pd["bucket"])
plt.tight_layout()
plt.show()

# %% [markdown]
# ### H1 result (write this into deliverables/03 Layer B):
# - Trend direction: ___ (rising / flat / falling / non-monotonic)
# - Magnitude: from X% in earliest bucket to Y% in latest
# - **Board-relevant interpretation**: ___

# %% [markdown]
# ## Cell 6 — H2: default rate decomposition by segment × time
#
# > **Hypothesis H2**: The uptick is concentrated in specific segments (e.g. younger or
# > newer-market borrowers), not population-wide.
# > Falsifying observation: even rise across all segments.
#
# We need segment columns. The Home Credit dataset has limited demographic columns at
# the base level; many demographic-like fields live in `person_1` (e.g. age proxies).
# For first pass, we use `WEEK_NUM` quartile as a coarse "vintage segment" — better
# segment definitions arrive after loading person_1 in EDA.
#
# **First-pass version**: decomposes default rate by `WEEK_NUM` buckets (already done in
# Cell 5). True segmentation (by age band, by file thickness, by geography proxy) requires
# joining demographic features and is deferred to the EDA notebook.
#
# **What to add later**: once we have age and geographic proxies, re-run this with
# segment_cols=['age_bucket', 'geo_proxy'].

# %%
import polars as pl
from src.data.validate import default_rate_by_segment

# Bucket WEEK_NUM into 4 vintage quartiles as a coarse first-pass segment proxy.
# True demographic segmentation (age band, geographic proxy) requires joining
# person_1 / static_0; that lives in notebooks/02_eda.py.
base_with_v = base.with_columns(
    ((pl.col("WEEK_NUM").rank("ordinal") - 1) * 4 // pl.len()).alias("vintage_q")
)
result = default_rate_by_segment(
    base_with_v,
    segment_cols=["vintage_q"],
    n_time_buckets=6,
)
print(result)

# Once person_1 is joined and age/geo proxies exist, re-run as:
#   default_rate_by_segment(base_joined, segment_cols=['age_band', 'state_proxy'])

# %% [markdown]
# ### H2 result placeholder:
# - First-pass (vintage quartile only): ___
# - Full segmentation (deferred to EDA notebook): TBD after person_1 join

# %% [markdown]
# ---
# # Q3 (DATA LIMITATIONS) — What constrains the recommendation?
# ---

# %% [markdown]
# ## Cell 7 — Per-table grain check (depth confirmation)
#
# Confirms our depth assignments from the docs match reality. A table that *should* be
# 1:1 but is actually 1:N indicates either a doc error or a data quality issue worth
# flagging in `04_data_gaps.md` (which lives inside `03_data_understanding.md`).

# %%
from src.data.load import load_table

depth_check = []
for name in sorted(tables.keys()):
    if table_depth(name) == 2:
        continue  # depth-2 tables are large; audit them separately
    if name == "base":
        continue
    try:
        df = load_table(name, TRAIN_DIR)
    except Exception as e:
        depth_check.append({"table": name, "error": str(e)[:80]})
        continue
    g = grain_check(df)
    expected_one_to_one = table_depth(name) == 0
    actual_one_to_one = g.get("is_one_to_one", False)
    depth_check.append({
        "table": name,
        "depth_expected": table_depth(name),
        "rows": g["rows"],
        "unique_ids": g["unique_ids"],
        "rows_per_id_avg": g["rows_per_id_avg"],
        "is_one_to_one": actual_one_to_one,
        "matches_expected_depth": expected_one_to_one == actual_one_to_one,
    })

import pandas as pd
print(pd.DataFrame(depth_check).to_string(index=False))

# %% [markdown]
# ## Cell 8 — High-missingness columns

# %%
from src.data.validate import missingness_report

high_missing_by_table = {}
for name in sorted(tables.keys()):
    if table_depth(name) == 2 or name == "base":
        continue
    try:
        df = load_table(name, TRAIN_DIR)
        hm = missingness_report(df, threshold=0.50)
        if hm.height > 0:
            high_missing_by_table[name] = hm
    except Exception as e:
        print(f"[skip] {name}: {e}")

for name, hm in high_missing_by_table.items():
    print(f"\n=== {name} ({hm.height} cols > 50% missing) ===")
    print(hm.head(10))

# %% [markdown]
# ## Cell 9 — H3 / general: column-suffix breakdown for the whole dataset
#
# > **Hypothesis H3**: Missingness in specific external sources correlates with default
# > (more on this in Cell 10).
# > **Also**: how many of the 2,588 columns are each dtype? Drives feature-engineering scope.

# %%
from src.data.schema import classify_columns

# Collect every column across every loaded table
all_columns = []
for name in sorted(tables.keys()):
    if table_depth(name) == 2:
        continue
    try:
        df = load_table(name, TRAIN_DIR)
        all_columns.extend(df.columns)
    except Exception:
        continue
all_columns = sorted(set(all_columns))
print(f"Total unique columns across depth-0/1 tables: {len(all_columns)}")
print()
print(suffix_breakdown(all_columns))

# %% [markdown]
# ---
# # Q4 (STABILITY / GOVERNANCE) — What to monitor in production?
# ---

# %% [markdown]
# ## Cell 10 — H4: external-source coverage drift over time
#
# > **Hypothesis H4**: Some external data providers drift in coverage over time.
# > The docs explicitly warn this. If confirmed, features built on the drifting sources
# > carry stability risk that must be reflected in feature selection (decision D06).
# >
# > Falsifying observation: all external sources show coverage > 95% across all WEEK_NUM
# > with no trend.

# %%
from src.data.validate import source_coverage_over_time

# Compute coverage for each external source against the base spine
external_tables = [name for name in tables.keys() if infer_source_family(name)[0] == "external"]
coverage_results = []
for name in external_tables:
    if table_depth(name) == 2:
        continue  # depth-2 tables don't tell us about coverage at applicant level
    try:
        src_df = load_table(name, TRAIN_DIR)
        cov = source_coverage_over_time(base, src_df, source_name=name)
        coverage_results.append(cov)
    except Exception as e:
        print(f"[skip] {name}: {e}")

if coverage_results:
    coverage_all = pl.concat(coverage_results, how="vertical")
    print("Coverage summary per source:")
    summary = (
        coverage_all
        .group_by("source")
        .agg(
            pl.col("coverage_pct").min().alias("min_cov"),
            pl.col("coverage_pct").max().alias("max_cov"),
            pl.col("coverage_pct").mean().alias("avg_cov"),
            (pl.col("coverage_pct").max() - pl.col("coverage_pct").min()).alias("drift_range"),
        )
        .sort("drift_range", descending=True)
    )
    print(summary)
    print()

    # Plot coverage trend per source
    coverage_pd = coverage_all.to_pandas()
    fig, ax = plt.subplots(figsize=(11, 5))
    for src in coverage_pd["source"].unique():
        sub = coverage_pd[coverage_pd["source"] == src].sort_values("WEEK_NUM")
        ax.plot(sub["WEEK_NUM"], sub["coverage_pct"], label=src, linewidth=1.2)
    ax.set_xlabel("WEEK_NUM")
    ax.set_ylabel("Coverage (%)")
    ax.set_title("H4: External-source coverage drift over time")
    ax.legend(fontsize=8, loc="best")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

# %% [markdown]
# ### H4 result placeholder:
# - Sources with drift > 20 pp range: ___
# - Sources requiring penalty in feature selection: ___
# - Sources to exclude entirely (drift > 50 pp): ___

# %% [markdown]
# ---
# # Save outputs
# ---

# %% [markdown]
# ## Cell 11 — Save audit results to /kaggle/working/ for later copy-back

# %%
from src.config import ensure_work_dirs, INTERIM_DIR
ensure_work_dirs()

pd.DataFrame(table_rows).to_csv(INTERIM_DIR / "audit_table_inventory.csv", index=False)
pd.DataFrame(depth_check).to_csv(INTERIM_DIR / "audit_depth_check.csv", index=False)
trend.write_csv(INTERIM_DIR / "audit_default_rate_trend.csv")
if coverage_results:
    coverage_all.write_csv(INTERIM_DIR / "audit_source_coverage.csv")
    summary.write_csv(INTERIM_DIR / "audit_source_coverage_summary.csv")

print(f"Audit outputs written to {INTERIM_DIR}")
print("Next: copy key tables/numbers into deliverables/03_data_understanding.md Layer B.")

# %% [markdown]
# ## Cell 12 (markdown only) — Copy-back checklist for deliverables/03
#
# After running everything above, fill in `deliverables/03_data_understanding.md` Layer B:
#
# - **Section B.1** (Table inventory): copy the table from Cell 3
# - **Section B.2** (Base table profile): copy numbers from Cell 4
# - **Section B.3** (H1 result): copy the trend chart description + interpretation
# - **Section B.4** (H4 source coverage): copy the summary table from Cell 10
# - **Section B.5** (Grain check): copy from Cell 7
# - **Section B.6** (High missingness): top 5 findings from Cell 8
# - **Section B.7** (Suffix breakdown): from Cell 9
#
# Then **update `deliverables/99_decisions_log.md`** with any treatment decisions made
# during this audit (e.g., "exclude tax_registry_b features because coverage drifts from
# 95% to 42% across WEEK_NUM" → D08, D09, etc.).
