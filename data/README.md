# Data — Access Pattern

The Home Credit Credit Risk Model Stability dataset is 26 GB. We do **not** download it locally. Instead, code runs on Kaggle Notebooks where the data is mounted automatically.

## Production access (Kaggle Notebooks)

Data lives at:

```
/kaggle/input/home-credit-credit-risk-model-stability/
├── parquet_files/
│   ├── train/
│   │   ├── train_base.parquet
│   │   ├── train_static_0_0.parquet
│   │   ├── train_static_cb_0.parquet
│   │   ├── train_applprev_1_0.parquet
│   │   ├── train_credit_bureau_a_1_0.parquet
│   │   ├── train_credit_bureau_a_2_0.parquet
│   │   └── ... (many more shards)
│   └── test/
│       └── ... (mirror structure)
├── csv_files/                ← same data as CSV; we use parquet
├── feature_definitions.csv   ← schema documentation
└── sample_submission.csv
```

`src/config.py` reads `DATA_DIR` from the environment, defaulting to the Kaggle mount path above. Override only if you have a local subsample.

## Setup checklist (one-time)

1. **Create a Kaggle account** (if you don't have one): https://www.kaggle.com/account/login
2. **Join the competition**: https://www.kaggle.com/competitions/home-credit-credit-risk-model-stability → "Late Submission" / "Join"
3. **Create a notebook**: from the competition page, **Code** → **New Notebook**
4. **Attach the data**: in the new notebook, **Add Input** (right sidebar) → search "Home Credit" → click **+** on the entry labeled "3856 Teams · Featured"
5. **Verify**: run `import os; print(os.listdir("/kaggle/input/home-credit-credit-risk-model-stability"))`

## Bootstrap cell (paste at top of every Kaggle notebook)

```python
import sys, os, subprocess
REPO = "/kaggle/working/loan_May"
if not os.path.exists(REPO):
    subprocess.run(["git", "clone", "https://github.com/Robot0920/loan_May.git", REPO], check=True)
else:
    subprocess.run(["git", "-C", REPO, "pull"], check=True)
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from src.config import DATA_DIR, TRAIN_DIR, TEST_DIR
```

After this, every `from src.X import Y` works inside Kaggle.

## Local development (optional, for offline work)

If you want a small subsample on your laptop to prototype features:

```bash
pip install kaggle
# Place your kaggle.json API token at ~/.kaggle/kaggle.json (chmod 600)
mkdir -p data/raw
kaggle competitions download -c home-credit-credit-risk-model-stability \
    -f parquet_files/train/train_base.parquet -p data/raw/
# Repeat for whichever specific small files you need (avoid the depth-2 monthlies)
```

Then set the env var before running any script:

```bash
export DATA_DIR="$(pwd)/data/raw/home-credit-credit-risk-model-stability"
```

## Schema reference

Open `feature_definitions.csv` in the dataset for column-by-column documentation maintained by the competition organizers. The naming convention is:

- Column suffix `_M` → categorical (modus / mode)
- Column suffix `_D` → date
- Column suffix `_T` → text
- Column suffix `_P` → numeric (price/amount)
- Column suffix `_A` → numeric (amount, in account currency)
- Column suffix `_L` → numeric (length, e.g. months)

Use these to filter columns by type during EDA.

## What is NOT in this folder

Nothing. The `raw/`, `interim/`, `processed/`, `external/` subfolders are gitignored. All actual data lives on Kaggle's servers (production) or your Kaggle Notebook session's working directory (intermediate).
