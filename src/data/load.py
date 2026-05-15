"""Loaders for the Home Credit 2024 stability dataset.

The dataset is organized as a relational schema across many parquet files under
`parquet_files/{train,test}/`. Files are named with a depth suffix:

    {split}_base.parquet                            depth 0, the spine (has target)
    {split}_static_0_{shard}.parquet                depth 0, application-level
    {split}_static_cb_0.parquet                     depth 0, application-level (bureau)
    {split}_applprev_1_{shard}.parquet              depth 1, one row per prior application
    {split}_credit_bureau_a_1_{shard}.parquet       depth 1, one row per bureau record
    {split}_credit_bureau_a_2_{shard}.parquet       depth 2, monthly per bureau record
    ... and so on.

Depth semantics:
    depth 0 -> 1:1 with case_id (safe to left-join directly)
    depth 1 -> 1:N with case_id (must aggregate before joining)
    depth 2 -> 1:N:M with case_id (must aggregate twice)

Large logical tables are sharded across multiple files (suffix `_0`, `_1`, ...).
This module concatenates shards back into a single logical table.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import polars as pl

from src.config import TRAIN_DIR, TEST_DIR, ID_COL


# Shard suffix at the end of a stem: e.g. "static_0_3" -> base "static_0", shard "3"
_SHARD_RE = re.compile(r"^(?P<base>.+)_(?P<shard>\d+)$")


def _logical_table_name(stem: str) -> str:
    """Strip split prefix ('train_'/'test_') and trailing shard index.

    Examples:
        'train_base'           -> 'base'
        'train_static_0_3'     -> 'static_0'
        'train_credit_bureau_a_2_5' -> 'credit_bureau_a_2'
    """
    for prefix in ("train_", "test_"):
        if stem.startswith(prefix):
            stem = stem[len(prefix):]
            break
    m = _SHARD_RE.match(stem)
    if m:
        return m.group("base")
    return stem


def list_tables(directory: Path = TRAIN_DIR) -> dict[str, list[Path]]:
    """Group parquet files in `directory` by their logical table name.

    Returns a dict mapping logical table name -> sorted list of shard file paths.
    """
    groups: dict[str, list[Path]] = {}
    for f in sorted(directory.glob("*.parquet")):
        table = _logical_table_name(f.stem)
        groups.setdefault(table, []).append(f)
    return groups


def table_depth(table_name: str) -> int:
    """Infer table depth from its name. Returns 0, 1, or 2.

    The convention in this dataset: depth is the integer suffix on the table name.
    'base' and tables with no numeric suffix default to depth 0.
    """
    m = re.search(r"_(\d)$", table_name)
    if m:
        return int(m.group(1))
    return 0


def load_table(
    table_name: str,
    directory: Path = TRAIN_DIR,
    columns: Iterable[str] | None = None,
) -> pl.DataFrame:
    """Load a logical table by name, concatenating all shards.

    Args:
        table_name: logical name (e.g. 'base', 'static_0', 'applprev_1').
        directory: TRAIN_DIR or TEST_DIR.
        columns: optional column subset for memory savings.

    Raises:
        KeyError if the table is not present in the directory.
    """
    groups = list_tables(directory)
    if table_name not in groups:
        raise KeyError(
            f"Table '{table_name}' not found in {directory}.\n"
            f"Available tables: {sorted(groups.keys())}"
        )
    paths = groups[table_name]
    cols = list(columns) if columns is not None else None
    frames = [pl.read_parquet(p, columns=cols) for p in paths]
    if len(frames) == 1:
        return frames[0]
    # diagonal_relaxed handles minor schema variation across shards (rare but happens)
    return pl.concat(frames, how="diagonal_relaxed")


def load_base(directory: Path = TRAIN_DIR) -> pl.DataFrame:
    """Load the base table — the spine that every other table joins onto.

    Columns include `case_id`, `date_decision`, `WEEK_NUM`, `MONTH`, `target`
    (only in train).
    """
    return load_table("base", directory)


def scan_table(
    table_name: str,
    directory: Path = TRAIN_DIR,
) -> pl.LazyFrame:
    """Lazy version of load_table for large tables you want to filter/aggregate
    before materializing. Returns a LazyFrame; call .collect() to execute.
    """
    groups = list_tables(directory)
    if table_name not in groups:
        raise KeyError(f"Table '{table_name}' not found in {directory}.")
    paths = groups[table_name]
    return pl.concat(
        [pl.scan_parquet(p) for p in paths], how="diagonal_relaxed"
    )


def assert_case_id_present(df: pl.DataFrame, table_name: str) -> None:
    """Sanity check: every non-base table should carry case_id for joinability."""
    if ID_COL not in df.columns:
        raise ValueError(
            f"Table '{table_name}' is missing required join key '{ID_COL}'."
        )
