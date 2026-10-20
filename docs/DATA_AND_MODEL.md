# DATA AND MODEL

## Dataset
- PhysioNet/CinC Challenge 2019, training sets A and B (two different US hospital systems).
- One file per ICU stay; one row per hour; 40 measurements + `SepsisLabel`.
- Real, de-identified, open-access data.
- We use a random subset of 2,000 patients per hospital (seed 42). See DECISIONS.md.

## Labels
- `SepsisLabel` is already shifted by PhysioNet: it turns 1 six hours **before** clinical onset.
  We never shift it again.
- Clinical onset hour = first hour with `SepsisLabel = 1`, plus 6.

## Data checks (hospital A subset, 2,000 patients)
- Every patient has exactly one row per ICU hour (no gaps in `ICULOS`), so "3 rows back" = "3 hours back".
- 7.8% of patients have sepsis; median stay in the data is 38 hours.

## Leakage rules
"Leakage" = the model secretly sees information it would not have at that moment.
1. Features for hour *t* use only hours ≤ *t* of the **same** patient.
2. Forward-fill only inside one patient; never backward-fill (that copies the future).
3. Missing flags and `hours_since_<lab>` are computed **before** filling.
4. Hospital A is split by patient (no patient in both train and validation). Hospital B is test only.
5. Tested in `tests/test_features_no_leakage.py`: scrambling or deleting hours after *t* leaves the
   features at *t* unchanged; patient 2 never receives patient 1's values.

## Features (51, in `FEATURE_COLUMNS`, `src/features.py`)
| Group | Columns | Formula |
|---|---|---|
| Vitals now | HR, O2Sat, Temp, SBP, MAP, Resp | last known value (forward-filled within patient) |
| Labs now | Lactate, WBC, Creatinine, Bilirubin_total, Platelets | last known value (forward-filled) |
| Missing flags | `<lab>_missing` | 1 if the lab was not measured in this hour (before filling) |
| Time since lab | `hours_since_<lab>` | ICULOS(t) − ICULOS(last measurement); 48 if never; capped at 48 |
| 3-hour change | `<vital>_delta_3h`, `Lactate_delta_3h` | v(t) − v(t−3); empty for the first 3 hours |
| 6-hour window | `<vital>_min_6h`, `_max_6h`, `_mean_6h` | over hours t−5 … t (min_periods = 1) |
| NEWS2-lite | `news2_lite` | points table below |
| Static | Age, Gender, HospAdmTime, ICULOS | as given (HospAdmTime forward-filled) |

The model (gradient-boosted trees) accepts empty values directly, so we do not invent numbers for them.

### NEWS2-lite point table
NEWS2 is the UK's standard bedside early-warning score. "Lite" = we leave out consciousness
and supplemental oxygen (not in the data). A missing vital scores 0 points.

| Points | 3 | 2 | 1 | 0 | 1 | 2 | 3 |
|---|---|---|---|---|---|---|---|
| Resp (/min) | ≤ 8 | | 9–11 | 12–20 | | 21–24 | ≥ 25 |
| O2Sat (%) | ≤ 91 | 92–93 | 94–95 | ≥ 96 | | | |
| SBP (mmHg) | ≤ 90 | 91–100 | 101–110 | 111–219 | | | ≥ 220 |
| HR (bpm) | ≤ 40 | | 41–50 | 51–90 | 91–110 | 111–130 | ≥ 131 |
| Temp (°C) | ≤ 35.0 | | 35.1–36.0 | 36.1–38.0 | 38.1–39.0 | ≥ 39.1 | |

## Split
- Hospital A, split **by patient**: 80% train, 20% validation (seed 42).
- Hospital B = test. Used only once, for the final evaluation.

## Models (`src/train.py`)
- **Baseline:** median fill → scaling → logistic regression.
- **Main:** HistGradientBoostingClassifier (200 trees, learning rate 0.05, seed 42). Settings in `src/config.py`.
- Both use the same 51 features and the same isotonic calibration, so the comparison is fair.

## Calibration
- "Calibrated" = when the model says 5%, about 5 in 100 such hours really are sepsis hours.
- Method: **isotonic calibration** on the TRAIN patients, with 5 folds grouped by patient
  (`CalibratedClassifierCV`). Each fold is calibrated on patients its model never saw.
- Validation patients are not used for calibration, so they stay clean for choosing the threshold.
- Because only 2% of hours are sepsis hours, honest hourly risks are small (validation max 0.19).

## Threshold rule
- Every hour with risk ≥ threshold counts as an alert (before any gates).
- A sepsis patient is "caught" if an alert fires in [onset − 12 h, onset + 2 h].
- Grid: 0.010 to 0.200 in steps of 0.001, searched on **hospital A validation only**.
- Rule: the **highest** threshold that still catches ≥ 60% of validation sepsis patients
  (the quietest setting that meets the minimum).

## Phase 3 results (hospital A validation: 400 patients, 31 with sepsis, 14,797 hours)
| Model | AUROC | AUPRC | Brier |
|---|---|---|---|
| Baseline logistic | 0.680 | 0.048 | 0.0193 |
| Main HGB | 0.714 | 0.060 | 0.0191 |

Hour-level sepsis rate is 0.0199, so a random guess has AUPRC ≈ 0.020.

**Chosen threshold: 0.038.** At this threshold: 19 of 31 sepsis patients caught (61.3%),
40.1% of non-sepsis patients get at least one alert, and 264.2 alert-hours per 100 patient-days.
That alert load is far too high for a ward, which is the problem the three gates (Phase 4) must fix.

Limits: only 31 validation sepsis patients, so one patient = 3.2 points of sensitivity
and the threshold is noisy. Hospital B has not been used yet.

## Threshold rule — Phase 4 update (official)
- The Phase 3 threshold (0.038) used risk alone. The master prompt asks for the **full three-gate policy**.
- `src/train.py` now runs the three gates (the student's `src/gates.py`) on the validation patients
  for every threshold 0.010–0.200 (step 0.002).
- Rule: among thresholds that catch ≥ 60% of validation sepsis patients, the **highest alert PPV**
  (tie → higher threshold). If none reaches 60%: the best F1 of alert PPV and patient sensitivity.
- The risk-only result is kept in `results/threshold.json` as `risk_only_reference`.
- "Caught" now follows the master prompt: a true alert **at or before onset** (Phase 3 also counted
  the 2 hours after onset).

## Metric definitions (plain English) — `src/evaluate.py`
| Metric | Meaning |
|---|---|
| AUROC | Pick a random sepsis hour and a random non-sepsis hour. How often does the sepsis hour get the higher risk? 0.5 = coin flip, 1.0 = perfect. |
| AUPRC | How clean the top of the risk ranking is. Compare with the base rate (share of sepsis hours). |
| Brier score | Average squared gap between predicted risk and what happened (0/1). Lower = better. |
| TRUE alert | An alert (REVIEW) for a sepsis patient in [onset − 12 h, onset + 2 h]. Everything else is FALSE. |
| Alert PPV | True alerts ÷ all alerts. "When the nurse is paged, how often is it real?" |
| Patient sensitivity | Sepsis patients with ≥ 1 true alert **at or before onset** ÷ all sepsis patients. |
| Median lead time | Onset − first true alert (hours), median over caught patients. |
| Alerts per 100 patient-days | Alerts ÷ total patient-hours × 2,400. |

## Policies compared on hospital B (same threshold)
| Policy | Gate 1 risk | Gate 2 worsening | Gate 3 cooldown |
|---|---|---|---|
| P0 naive | ✓ | – | – |
| P1 | ✓ | – | ✓ |
| P2 | ✓ | ✓ | – |
| P3 SepsisGuardian | ✓ | ✓ | ✓ |
| NEWS2-lite ≥ 5 | rule only: alert every hour the score is ≥ 5 | | |

## Phase 4 results — hospital B (2,000 patients, 108 sepsis, 77,220 hours), run once
Threshold **0.018**, chosen on hospital A validation with all three gates (validation: PPV 0.054, sensitivity 61.3%).

### Model scores (hour level)
| Model | AUROC | AUPRC | Brier |
|---|---|---|---|
| Baseline logistic | 0.761 | 0.069 | 0.0129 |
| Main HGB | 0.744 | 0.054 | 0.0130 |

Base rate (share of sepsis hours) = see `results/metrics.json`. **Honest note:** on hospital B the simple
baseline scored *higher* than the main model, although the main model was better on validation (0.714 vs 0.680).
We report this as it is and do not switch models after seeing B (that would be tuning on the test set).

### Alert policies (same threshold 0.018)
| Policy | Alerts | Alerts / 100 patient-days | Alert PPV | Patients caught (≤ onset) | Median lead time |
|---|---|---|---|---|---|
| P0 naive (risk only) | 17,518 | 544.5 | 5.0% | 79 / 108 (73.1%) | 12.0 h |
| P1 risk + cooldown | 4,216 | 131.0 | 4.0% | 78 / 108 (72.2%) | 8.0 h |
| P2 risk + worsening | 6,729 | 209.1 | 6.4% | 72 / 108 (66.7%) | 9.0 h |
| **P3 SepsisGuardian** | **2,447** | **76.1** | **5.1%** | **70 / 108 (64.8%)** | **7.5 h** |
| NEWS2-lite ≥ 5 | 8,660 | 269.2 | 4.8% | 69 / 108 (63.9%) | 7.0 h |

**Headline:** Three gates cut alerts from 544.5 to 76.1 per 100 patient-days while catching 64.8% of sepsis patients.

### What this means (honest reading)
- The gates make the alarm **7.2× quieter** (544.5 → 76.1). The cost: 9 fewer sepsis patients caught (79 → 70) and less warning time (12 → 7.5 h).
- The gates do **not** make each alert more accurate: PPV stays about 5% (5.0% → 5.1%). They remove repeated and
  stable-patient pages; they do not find new true cases. P2 has the best PPV (6.4%).
- Compared with a NEWS2-style rule: about the same sensitivity (64.8% vs 63.9%) with 3.5× fewer alerts (76.1 vs 269.2).
- About 1 in 20 alerts is a true early-warning alert. This is a prototype, not ready for a ward.
