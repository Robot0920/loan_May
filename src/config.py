"""Repo-wide configuration. Resolves data paths and constants from environment
variables so the same code runs unchanged on Kaggle Notebooks (default) and
locally with a subsampled dataset.

Environment variables:
    DATA_DIR    Root of the Home Credit competition data.
                Default: /kaggle/input/home-credit-credit-risk-model-stability
    WORK_DIR    Writable scratch space for intermediate / processed outputs.
                Default: /kaggle/working/loan_May/data
"""

from __future__ import annotations

import os
from pathlib import Path

# ---- data paths ----
# Kaggle mounts competition data at one of two paths depending on how the dataset
# was attached. We try both, then fall back to a local subsample path.
_SLUG = "home-credit-credit-risk-model-stability"
_CANDIDATE_DATA_DIRS = [
    Path(f"/kaggle/input/{_SLUG}"),
    Path(f"/kaggle/input/competitions/{_SLUG}"),
    Path.cwd() / "data" / "raw" / _SLUG,  # local subsample fallback
]


def _resolve_data_dir() -> Path:
    """Return the first existing candidate, or the env override, or the first
    candidate (which will then fail loudly when used)."""
    env = os.environ.get("DATA_DIR")
    if env:
        return Path(env)
    for c in _CANDIDATE_DATA_DIRS:
        if c.exists():
            return c
    return _CANDIDATE_DATA_DIRS[0]


DATA_DIR: Path = _resolve_data_dir()
TRAIN_DIR: Path = DATA_DIR / "parquet_files" / "train"
TEST_DIR: Path = DATA_DIR / "parquet_files" / "test"

WORK_DIR: Path = Path(
    os.environ.get("WORK_DIR", "/kaggle/working/loan_May/data")
)
INTERIM_DIR: Path = WORK_DIR / "interim"
PROCESSED_DIR: Path = WORK_DIR / "processed"

# ---- schema constants (Home Credit 2024 convention) ----
ID_COL: str = "case_id"
TARGET_COL: str = "target"
DATE_COL: str = "date_decision"
WEEK_COL: str = "WEEK_NUM"  # used by the competition's stability metric

# ---- reproducibility ----
RANDOM_SEED: int = 42

# ---- modeling defaults ----
N_CV_FOLDS: int = 5
HIGH_MISSING_THRESHOLD: float = 0.30
PSI_DRIFT_THRESHOLD: float = 0.25


def ensure_work_dirs() -> None:
    """Create WORK_DIR subfolders if they don't exist. Safe to call multiple times."""
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
