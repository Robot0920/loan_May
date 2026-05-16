"""Schema utilities for the Home Credit 2024 dataset.

Two responsibilities:
1. Parse the dataset's column naming convention to classify every column by its
   transformation family (P/A/D/M/T/L) and its base name. This lets us auto-route
   columns to appropriate feature treatments (numeric, date, categorical) without
   inspecting each of the 2,588 columns by hand.
2. Load and query the feature_definitions.csv that documents 465 distinct features.
   This is the feature dictionary the rest of the pipeline reads from.

Naming convention (per dataset documentation):
    <base_name>_<id_number><suffix>
where suffix ∈ {P, A, D, M, T, L} and id_number is an integer.

Suffix semantics:
    P  -> Days Past Due (DPD) transform           -> continuous numeric
    A  -> Amount transform                        -> continuous (consider log)
    D  -> Date transform                          -> parse to date / days-since
    M  -> Masking transform on categorical        -> categorical, encode
    T  -> Unspecified transform                   -> inspect case-by-case
    L  -> Unspecified transform                   -> inspect case-by-case

Special columns (no suffix, anchor / identifier roles):
    case_id, date_decision, WEEK_NUM, MONTH, target, num_group1, num_group2
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import polars as pl

from src.config import DATA_DIR


# ---- column-name parsing ----

_COL_RE = re.compile(r"^(?P<base>.+?)_(?P<num>\d+)(?P<suffix>[A-Z])$")

# Columns that don't follow the suffix convention — they have special semantics.
SPECIAL_COLUMNS: set[str] = {
    "case_id",
    "date_decision",
    "WEEK_NUM",
    "MONTH",
    "target",
    "num_group1",
    "num_group2",
}

SUFFIX_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "P": {
        "family": "DPD (Days Past Due)",
        "dtype": "continuous_numeric",
        "treatment": "use raw; high predictive value in credit risk",
    },
    "A": {
        "family": "Amount",
        "dtype": "continuous_numeric",
        "treatment": "consider log1p transform; clip extremes",
    },
    "D": {
        "family": "Date",
        "dtype": "date",
        "treatment": "parse to date; compute days_since_application relative to date_decision",
    },
    "M": {
        "family": "Masked categorical",
        "dtype": "categorical",
        "treatment": "encode (target/ordinal/one-hot per cardinality)",
    },
    "T": {
        "family": "Unspecified transform",
        "dtype": "unknown",
        "treatment": "inspect distribution; treat as continuous unless evidence otherwise",
    },
    "L": {
        "family": "Unspecified transform",
        "dtype": "unknown",
        "treatment": "inspect distribution; treat as continuous unless evidence otherwise",
    },
}


@dataclass(frozen=True)
class ColumnInfo:
    name: str
    is_special: bool
    base_name: Optional[str]
    id_number: Optional[int]
    suffix: Optional[str]
    dtype_family: Optional[str]
    recommended_treatment: Optional[str]


def parse_column_name(col: str) -> ColumnInfo:
    """Parse a column name into its components and recommended treatment."""
    if col in SPECIAL_COLUMNS:
        return ColumnInfo(
            name=col,
            is_special=True,
            base_name=None,
            id_number=None,
            suffix=None,
            dtype_family="special_anchor",
            recommended_treatment="identifier/target/anchor — not a feature",
        )
    m = _COL_RE.match(col)
    if not m:
        return ColumnInfo(
            name=col,
            is_special=False,
            base_name=None,
            id_number=None,
            suffix=None,
            dtype_family="unparsed",
            recommended_treatment="does not match naming convention; inspect manually",
        )
    suffix = m.group("suffix")
    meta = SUFFIX_DESCRIPTIONS.get(suffix, {
        "family": f"unknown suffix '{suffix}'",
        "dtype": "unknown",
        "treatment": "inspect manually",
    })
    return ColumnInfo(
        name=col,
        is_special=False,
        base_name=m.group("base"),
        id_number=int(m.group("num")),
        suffix=suffix,
        dtype_family=meta["family"],
        recommended_treatment=meta["treatment"],
    )


def classify_columns(columns: list[str]) -> pl.DataFrame:
    """Apply parse_column_name across a list of column names.

    Returns a Polars DataFrame with one row per column and its parsed metadata.
    """
    rows = [
        {
            "column": ci.name,
            "is_special": ci.is_special,
            "base_name": ci.base_name,
            "id_number": ci.id_number,
            "suffix": ci.suffix,
            "dtype_family": ci.dtype_family,
            "recommended_treatment": ci.recommended_treatment,
        }
        for ci in (parse_column_name(c) for c in columns)
    ]
    return pl.DataFrame(rows)


def suffix_breakdown(columns: list[str]) -> pl.DataFrame:
    """Count columns by suffix and report 5 sample columns per suffix.

    Used to answer: 'How many of the 2,588 columns are each type?'
    """
    classified = classify_columns(columns)
    grouped = (
        classified
        .group_by("suffix")
        .agg(
            pl.len().alias("count"),
            pl.col("column").head(5).alias("sample_columns"),
            pl.col("dtype_family").first().alias("dtype_family"),
            pl.col("recommended_treatment").first().alias("recommended_treatment"),
        )
        .sort("count", descending=True)
    )
    return grouped


# ---- feature dictionary (feature_definitions.csv) ----

def load_feature_definitions(data_dir: Path = DATA_DIR) -> pl.DataFrame:
    """Load the official feature_definitions.csv shipped with the dataset.

    Returns a 2-column DataFrame: Variable, Description.
    Raises FileNotFoundError if the file is missing.
    """
    candidates = [
        data_dir / "feature_definitions.csv",
        data_dir.parent / "feature_definitions.csv",  # in case DATA_DIR points one level deeper
    ]
    for c in candidates:
        if c.exists():
            return pl.read_csv(c)
    raise FileNotFoundError(
        f"feature_definitions.csv not found in {data_dir} or its parent.\n"
        f"Tried: {[str(c) for c in candidates]}"
    )


def build_feature_dictionary(data_dir: Path = DATA_DIR) -> pl.DataFrame:
    """Join the official feature_definitions with our suffix-parsed metadata.

    Returns a DataFrame with one row per known variable:
        Variable, Description, base_name, suffix, dtype_family, recommended_treatment
    """
    defs = load_feature_definitions(data_dir)
    if "Variable" not in defs.columns:
        raise ValueError(f"Expected 'Variable' column in feature_definitions; got {defs.columns}")
    classified = classify_columns(defs["Variable"].to_list())
    return defs.join(
        classified.select(["column", "base_name", "suffix", "dtype_family", "recommended_treatment"]),
        left_on="Variable",
        right_on="column",
        how="left",
    )


def lookup_feature(dictionary: pl.DataFrame, name: str) -> dict | None:
    """Look up a single feature's metadata from the dictionary."""
    row = dictionary.filter(pl.col("Variable") == name)
    if row.is_empty():
        return None
    return row.to_dicts()[0]


# ---- table source family inference ----

_SOURCE_FAMILY_MAP: dict[str, tuple[str, str]] = {
    # table_prefix -> (source_kind, provider)
    "base": ("internal", "novalend_base"),
    "static_0": ("internal", "novalend_static"),
    "static_cb": ("external", "credit_bureau_static"),
    "applprev": ("internal", "novalend_applications"),
    "other": ("internal", "novalend_other"),
    "deposit": ("internal", "novalend_deposit"),
    "person": ("internal", "novalend_person"),
    "debitcard": ("internal", "novalend_debitcard"),
    "tax_registry_a": ("external", "tax_provider_a"),
    "tax_registry_b": ("external", "tax_provider_b"),
    "tax_registry_c": ("external", "tax_provider_c"),
    "credit_bureau_a": ("external", "credit_bureau_a"),
    "credit_bureau_b": ("external", "credit_bureau_b"),
}


def infer_source_family(table_name: str) -> tuple[str, str]:
    """Return (source_kind, provider) for a logical table name.

    Used by source-coverage analysis: knowing which tables are external lets us
    flag stability risk on features derived from them (the docs warn external
    providers may be unavailable in test).
    """
    for prefix, info in _SOURCE_FAMILY_MAP.items():
        if table_name.startswith(prefix):
            return info
    return ("unknown", "unknown")
