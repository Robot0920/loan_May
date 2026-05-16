"""Data audit functions. Used by `notebooks/01_data_audit.py` to produce the
findings that go into `deliverables/03_data_understanding.md`.

These are not training-pipeline transformations — they are diagnostic. Run them
once per fresh data drop and once per quarter in production.
"""

from __future__ import annotations

import math
from typing import Optional

import polars as pl

from src.config import (
    ID_COL,
    TARGET_COL,
    DATE_COL,
    WEEK_COL,
    HIGH_MISSING_THRESHOLD,
)


def table_summary(df: pl.DataFrame, name: str = "table") -> dict:
    """Headline summary: rows, columns, memory, dtypes breakdown.

    The memory figure is an estimate from Polars' internal accounting; for parquet
    on disk it differs from RAM size by ~3-5x depending on compression.
    """
    dtype_counts: dict[str, int] = {}
    for dt in df.dtypes:
        key = str(dt)
        dtype_counts[key] = dtype_counts.get(key, 0) + 1
    return {
        "table": name,
        "rows": df.height,
        "cols": df.width,
        "memory_mb": round(df.estimated_size("mb"), 2),
        "dtype_counts": dtype_counts,
    }


def missingness_report(
    df: pl.DataFrame,
    threshold: float = HIGH_MISSING_THRESHOLD,
) -> pl.DataFrame:
    """One row per column with null fraction. Sorted descending.

    Args:
        threshold: filter to columns with null_fraction >= threshold.
                   Set to 0.0 to see all columns.
    """
    n = df.height
    if n == 0:
        return pl.DataFrame({"column": [], "null_count": [], "null_fraction": []})
    null_counts = df.null_count()
    rows = [
        {
            "column": col,
            "null_count": null_counts[col].item(),
            "null_fraction": round(null_counts[col].item() / n, 4),
        }
        for col in df.columns
    ]
    out = pl.DataFrame(rows).sort("null_fraction", descending=True)
    return out.filter(pl.col("null_fraction") >= threshold)


def target_distribution(
    df: pl.DataFrame,
    target_col: str = TARGET_COL,
) -> dict:
    """Class balance. For binary target, also returns positive rate (default rate)."""
    if target_col not in df.columns:
        return {"error": f"'{target_col}' not in columns"}
    vc = (
        df.group_by(target_col)
        .len()
        .sort(target_col)
        .rename({"len": "count"})
    )
    total = df.height
    counts = {row[target_col]: row["count"] for row in vc.to_dicts()}
    pos = counts.get(1, 0)
    return {
        "total": total,
        "class_counts": counts,
        "positive_rate": round(pos / total, 6) if total else 0.0,
    }


def time_coverage(
    df: pl.DataFrame,
    date_col: str = DATE_COL,
    week_col: str = WEEK_COL,
) -> dict:
    """Temporal span and per-quarter row counts. Used to spot coverage gaps and
    population shifts across vintages.
    """
    if date_col not in df.columns:
        return {"error": f"'{date_col}' not in columns"}
    s = df[date_col].drop_nulls()
    if s.is_empty():
        return {"error": f"'{date_col}' has no non-null values"}
    out: dict = {
        "min_date": str(s.min()),
        "max_date": str(s.max()),
        "n_unique_dates": int(s.n_unique()),
    }
    if week_col in df.columns:
        out["week_range"] = (int(df[week_col].min()), int(df[week_col].max()))
        out["n_unique_weeks"] = int(df[week_col].n_unique())
    return out


def grain_check(df: pl.DataFrame, id_col: str = ID_COL) -> dict:
    """Confirm whether a table is 1:1 (depth-0) or 1:N (depth-1+) on id_col.

    Critical before any join — joining a 1:N table without aggregation explodes
    the row count and silently leaks information.
    """
    if id_col not in df.columns:
        return {"error": f"'{id_col}' not in columns"}
    n = df.height
    n_unique = df[id_col].n_unique()
    return {
        "rows": n,
        "unique_ids": n_unique,
        "rows_per_id_avg": round(n / n_unique, 3) if n_unique else 0.0,
        "is_one_to_one": n == n_unique,
    }


def population_stability_index(
    reference: pl.Series,
    current: pl.Series,
    bins: int = 10,
) -> float:
    """Population Stability Index between two distributions.

    PSI < 0.10: no significant change
    0.10 <= PSI < 0.25: moderate shift
    PSI >= 0.25: significant shift, model recalibration warranted

    Numeric implementation: quantile bins on the reference, count both
    distributions into those bins, sum (ref_pct - cur_pct) * ln(ref_pct / cur_pct).
    """
    ref = reference.drop_nulls().cast(pl.Float64)
    cur = current.drop_nulls().cast(pl.Float64)
    if ref.is_empty() or cur.is_empty():
        return float("nan")
    # Edges from reference quantiles
    qs = [i / bins for i in range(1, bins)]
    edges = sorted({ref.quantile(q) for q in qs if ref.quantile(q) is not None})
    edges = [-float("inf"), *edges, float("inf")]

    interior_edges = edges[1:-1]

    def _bin_pcts(s: pl.Series) -> list[float]:
        # Bucket values into the same interior edges; count per bucket; normalize.
        # Bucket index 0 = below first edge, len(edges)-1 = above last edge.
        bucket = s.cut(breaks=interior_edges, include_breaks=False)
        vc = bucket.value_counts(sort=False)
        # value_counts column is the original series name; rename for safety
        bucket_col = [c for c in vc.columns if c != "count"][0]
        # Re-index to all bins so missing categories appear as 0
        counts_by_bin = {row[bucket_col]: row["count"] for row in vc.to_dicts()}
        total = s.len() if s.len() > 0 else 1
        all_bin_keys = list(counts_by_bin.keys())
        return [counts_by_bin.get(k, 0) / total for k in all_bin_keys]

    eps = 1e-6
    ref_pcts = _bin_pcts(ref)
    cur_pcts = _bin_pcts(cur)
    L = max(len(ref_pcts), len(cur_pcts))
    ref_pcts += [eps] * (L - len(ref_pcts))
    cur_pcts += [eps] * (L - len(cur_pcts))
    psi = 0.0
    for r, c in zip(ref_pcts, cur_pcts):
        r = max(r, eps)
        c = max(c, eps)
        psi += (r - c) * math.log(r / c)
    return psi


def source_coverage_over_time(
    base_df: pl.DataFrame,
    source_df: pl.DataFrame,
    source_name: str,
    id_col: str = ID_COL,
    week_col: str = WEEK_COL,
) -> pl.DataFrame:
    """For each WEEK_NUM in base_df, fraction of case_ids that have ANY record
    in source_df. Answers H4: do external sources drift over time?

    Used to flag features built on sources whose coverage drops in later weeks —
    those features will look strong in early-period CV and fail on test where the
    source may be missing entirely.

    Args:
        base_df: the spine (every case_id in scope).
        source_df: a single source table (typically depth-1, e.g. credit_bureau_b_1).
        source_name: free-text label used in the output column for joining results.

    Returns a Polars DataFrame:
        week | n_base | n_with_source | coverage_pct | source_name
    """
    if id_col not in base_df.columns or week_col not in base_df.columns:
        raise ValueError(f"base_df missing {id_col} or {week_col}")
    if id_col not in source_df.columns:
        raise ValueError(f"source_df ({source_name}) missing {id_col}")
    covered_ids = source_df.select(id_col).unique()
    return (
        base_df
        .select([id_col, week_col])
        .join(
            covered_ids.with_columns(pl.lit(True).alias("_has_source")),
            on=id_col,
            how="left",
        )
        .with_columns(pl.col("_has_source").fill_null(False))
        .group_by(week_col)
        .agg(
            pl.len().alias("n_base"),
            pl.col("_has_source").sum().alias("n_with_source"),
        )
        .with_columns(
            (pl.col("n_with_source") / pl.col("n_base") * 100).round(2).alias("coverage_pct"),
            pl.lit(source_name).alias("source"),
        )
        .sort(week_col)
    )


def default_rate_by_segment(
    base_df: pl.DataFrame,
    segment_cols: list[str],
    target_col: str = TARGET_COL,
    week_col: str = WEEK_COL,
    n_time_buckets: int = 6,
) -> pl.DataFrame:
    """Decompose default rate by (segment × time bucket). Answers H2: is the
    default-rate uptick concentrated in specific segments?

    The result lets us distinguish:
      - Population-wide drift  -> all segments rise together
      - Segment-specific issue -> one segment's default rate rises while others stay flat

    Args:
        base_df: must contain target_col, week_col, and every column in segment_cols.
        segment_cols: list of columns to group by (e.g. ['age_bucket'] or
                      ['age_bucket', 'state_proxy']).
        n_time_buckets: number of equal-row buckets along week_col.
    """
    for c in [target_col, week_col, *segment_cols]:
        if c not in base_df.columns:
            raise ValueError(f"'{c}' not in base_df")
    bucketed = base_df.sort(week_col).with_columns(
        ((pl.col(week_col).rank("ordinal") - 1) * n_time_buckets // pl.len()).alias(
            "time_bucket"
        )
    )
    return (
        bucketed
        .group_by([*segment_cols, "time_bucket"])
        .agg(
            pl.len().alias("rows"),
            pl.col(target_col).sum().alias("defaults"),
            pl.col(target_col).mean().alias("default_rate"),
            pl.col(week_col).min().alias("week_start"),
            pl.col(week_col).max().alias("week_end"),
        )
        .sort([*segment_cols, "time_bucket"])
    )


def time_split_audit(
    df: pl.DataFrame,
    date_col: str = DATE_COL,
    target_col: str = TARGET_COL,
    n_buckets: int = 8,
) -> pl.DataFrame:
    """Bucket the rows into equal-size temporal buckets and report per-bucket
    row count and default rate. Used to spot whether the default rate is trending
    over time (concept drift) before any modeling.
    """
    if date_col not in df.columns:
        raise ValueError(f"'{date_col}' not in columns")
    if target_col not in df.columns:
        raise ValueError(f"'{target_col}' not in columns")
    return (
        df.sort(date_col)
        .with_columns(
            ((pl.col(date_col).rank("ordinal") - 1) * n_buckets // pl.len()).alias(
                "bucket"
            )
        )
        .group_by("bucket")
        .agg(
            pl.col(date_col).min().alias("bucket_start"),
            pl.col(date_col).max().alias("bucket_end"),
            pl.len().alias("rows"),
            pl.col(target_col).mean().alias("default_rate"),
            pl.col(target_col).sum().alias("defaults"),
        )
        .sort("bucket")
    )
