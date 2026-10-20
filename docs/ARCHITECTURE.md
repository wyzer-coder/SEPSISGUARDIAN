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
_To be completed in Phase 7 (final tree)._
