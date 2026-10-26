# ARCHITECTURE

## Pipeline (5 steps)
```
1. Download      scripts/download_data.py   PhysioNet .psv files  ─► data/
2. Features      src/load_data.py + src/features.py   (past hours only)
3. Risk model    src/train.py   hospital A ─► calibrated risk + threshold
4. Gates         src/gates.py   risk + worsening + cooldown ─► NO_ALERT / WATCH / SUPPRESSED / REVIEW
5. Explain       src/explain.py + src/messages.py   ─► why-now in EN / TA / HI
```

## Offline vs online
| Part | When it runs | Where |
|---|---|---|
| Download, features, training, evaluation, demo data | Offline, once, on our laptop | `scripts/`, `src/` |
| Website | Online, every visit | `app/` reads only `app/demo_data/` |

The website never trains a model and never reads raw data. Everything it shows is precomputed.

## What is saved where
| File | Made by | Used by |
|---|---|---|
| `data/training_setA/`, `data/training_setB/`, `data/manifest.csv` | download_data.py | load_data.py (NOT in Git) |
| `results/threshold.json` | train.py | evaluate.py, docs |
| `results/metrics.json`, `results/gate_comparison.csv`, `results/*.png` | evaluate.py | README, app |
| `app/demo_data/model.joblib` | train.py | build_demo_data.py |
| `app/demo_data/demo_patients.csv.gz`, `metrics.json`, `gate_comparison.csv` | build_demo_data.py / evaluate.py | website |

## Folder map
| Folder / file | What it holds |
|---|---|
| `src/config.py` | Every threshold, path and seed (one place to change settings) |
| `src/load_data.py` → `features.py` → `train.py` | Offline pipeline on hospital A |
| `src/gates.py` | The three-gate controller (used by training, evaluation and the website) |
| `src/evaluate.py` | Hospital B evaluation, P0–P3 comparison, chart |
| `src/explain.py` + `src/messages.py` | Why-now reasons and EN/TA/HI sentences (also used live by the website) |
| `scripts/` | `download_data.py` (PhysioNet), `build_demo_data.py` (50 demo beds) |
| `app/Home.py`, `app/pages/` | The 4 website pages |
| `app/utils.py` | Shared loading (cached), language selector, status chips, gate table, safety footer |
| `app/demo_data/` | `demo_patients.csv.gz` (60 KB), `metrics.json`, `gate_comparison.csv`, `model.joblib` |
| `.streamlit/config.toml` | Light theme, so every viewer sees the same colours |
| `.streamlit/secrets.toml.example` | Template for the optional Clerk login settings (the real `secrets.toml` is git-ignored) |
| `tests/` | 49 tests: leakage, split, threshold rule, gates, metrics, explanations, messages, login gate |
| `docs/screenshots/` | Website screenshots for the README |

## The website at run time
- Reads only `app/demo_data/` (no raw data, no model loading). Internet is used only for the optional Clerk login.
- Login: `app/utils.py → require_login()` runs at the top of every page (see `docs/LOGIN_SETUP.md`).
- Imports `src/gates.py`, `src/explain.py`, `src/messages.py`, so the website uses **the same code** as the evaluation.
- Size of `app/`: 6.3 MB (Streamlit Community Cloud limit used here: 25 MB).
- Deploy: Streamlit Community Cloud → repo `wyzer-coder/SEPSISGUARDIAN`, branch `main`, main file `app/Home.py`,
  Python 3.9 (Advanced settings).
