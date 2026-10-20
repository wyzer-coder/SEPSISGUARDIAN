# DECISIONS — dated log of important choices

## 2026-10-19 — Data source: PhysioNet/CinC Challenge 2019
- The team asked for a free source of **real** patient data.
- PhysioNet 2019 is real, de-identified ICU data from two hospital systems, open access, no login.
- Rejected: FHIR sandboxes and Synthea (computer-generated, not real patients);
  MIMIC (real, but needs weeks of credentialing).

## 2026-10-19 — Subset size: 2,000 patients per hospital
- Master-prompt default was 5,000 per hospital.
- Measured speed from our laptop: about 2.5 files per second with 12 parallel downloads.
- 5,000 per set ≈ 63 MB and ≈ 1 hour; 2,000 per set ≈ 25 MB and ≈ 25 minutes.
- The team chose 2,000 per hospital (random sample, seed 42) to save time.
- Trade-off: fewer sepsis cases to learn from. Change `PATIENTS_PER_SET` in `src/config.py`
  and re-run the download to use more.

## 2026-10-19 — Main model: HistGradientBoostingClassifier (not LightGBM)
- `pip install lightgbm` worked, but `import lightgbm` failed: `Library not loaded: @rpath/libomp.dylib`.
- libomp normally comes from Homebrew, which this Mac does not have.
- scikit-learn's HistGradientBoostingClassifier is the same family of model (gradient-boosted
  trees), handles missing values, and needs no extra system library. LightGBM was uninstalled.

## 2026-10-19 — Streamlit version 1.39.1
- Matches the master prompt (1.39.x). Newest for Python 3.9 is 1.50.0; not needed.

## 2026-10-19 — Separate git repository
- Git on this laptop was tracking the whole home folder (including `.ssh/`).
- We created a new repository inside `SepsisGuardian/` only, so private files can never be pushed.

## 2026-10-19 — Calibration: isotonic, on grouped folds of the train patients
- Keeps validation clean for the threshold. Hospital B is still untouched.

## 2026-10-19 — Threshold grid lowered to 0.010–0.200 (step 0.001); threshold = 0.038
- First run failed: no threshold in the old grid (0.05–0.90) reached 60% patient sensitivity.
- Cause: calibrated hourly risks are small (2% of hours are sepsis hours; max risk 0.19).
  At 0.05 only 41.9% of validation sepsis patients were caught.
- Fix: a lower, finer grid. Same rule: highest threshold with validation sensitivity ≥ 60%.
- Result on validation: 0.038 → 61.3% (19/31) of sepsis patients caught.

## 2026-10-20 — Official threshold = 0.018 (three-gate policy, validation only)
- Master-prompt rule: highest alert PPV with validation patient sensitivity ≥ 60%, running all three gates.
- Result on validation: PPV 0.054, sensitivity 61.3% (19/31), 99.6 alerts per 100 patient-days.
- Lower than the risk-only 0.038, because Gate 2 removes many alerts, so Gate 1 must let more through
  to keep 60% sensitivity. Risk-only result kept in `results/threshold.json` as a reference.
- "Caught" = true alert at or before onset (master-prompt definition).

## 2026-10-20 — `src/gates.py` written by Claude, not the student
- The master prompt planned for the student to write it. The student asked twice for Claude to write it
  (allowed by the prompt's "unless they ask twice"). The student must review it and explain it line by line.

## 2026-10-20 — Hospital B evaluated once; main model kept although the baseline scored higher on B
- B: baseline AUROC 0.761 vs main 0.744. Validation had chosen the main model (0.714 vs 0.680).
- We do not switch models after seeing B; that would be tuning on the test set. Reported as a limitation.
