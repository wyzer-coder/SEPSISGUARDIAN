# SepsisGuardian — Progress Update

Team HackNovacX (DEX26048) · DEXATHON 2026 Round 2
Deadline: **30 Oct 2026, 11:00 PM IST** (aim for 29 Oct) · Last updated: **20 Oct 2026**

**Status: Phases 1–4 of 8 done. `pytest` → 32 passed. Next: Phase 5 (messages; you write Tamil).**

---

## 🎯 Phase 4 RESULTS — hospital B (unseen, run once) — 20 Oct

**`gates.py`** was written by Claude at your request (asked twice). This is logged honestly in `docs/DECISIONS.md`.
**You must be able to explain it line by line.** Every step has a comment.
**Tests:** `pytest -q` → **32 passed, 0 failed** (18 gate tests now green).

**Threshold (validation, with all 3 gates): 0.018.** It was 0.038 without gates; Gate 2 removes alerts, so Gate 1 must let more through.

| Policy (hospital B, threshold 0.018) | Alerts / 100 patient-days | Alert PPV | Sepsis patients caught | Median lead time |
|---|---|---|---|---|
| P0 naive (risk only) | 544.5 | 5.0% | 79 / 108 (73.1%) | 12.0 h |
| P1 risk + cooldown | 131.0 | 4.0% | 78 / 108 (72.2%) | 8.0 h |
| P2 risk + worsening | 209.1 | 6.4% | 72 / 108 (66.7%) | 9.0 h |
| **P3 SepsisGuardian** | **76.1** | **5.1%** | **70 / 108 (64.8%)** | **7.5 h** |
| NEWS2-lite ≥ 5 | 269.2 | 4.8% | 69 / 108 (63.9%) | 7.0 h |

> **Headline (real):** Three gates cut alerts from 544.5 to 76.1 per 100 patient-days while catching 64.8% of sepsis patients.

| Model (hospital B) | AUROC | AUPRC | Brier |
|---|---|---|---|
| Baseline logistic | 0.761 | 0.069 | 0.0129 |
| Main HGB | 0.744 | 0.054 | 0.0130 |

**Honest reading:**
- ✅ **7.2× quieter** alarm, and fewer alerts than a NEWS2-style rule (76.1 vs 269.2) at about the same sensitivity.
- ⚠️ **Cost:** 9 fewer patients caught (79 → 70) and less warning time (12 → 7.5 h).
- ⚠️ **PPV barely moves** (5.0% → 5.1%): about 1 alert in 20 is real. The gates cut *repeat and stable* pages; they don't make each page smarter.
- ⚠️ **The simple baseline beat the main model on hospital B.** We don't switch now; that would be tuning on the test set.
- Files: `results/metrics.json`, `results/gate_comparison.csv`, `results/gate_comparison.png` (copied to `app/demo_data/`).

**Phase 4 judge questions** (model answers Q6–Q10 in `docs/LEARNING_AND_QA.md`):
1. Explain each of your three gates.
2. What does PPV mean, and why is yours only 5%?
3. Your baseline scored higher on hospital B. Why didn't you switch?

---

## 📅 Day 2 — 20 Oct 2026 (started)

**Morning health check:** `pytest -q` → 9 passed · 2,000 + 2,000 patient files present · nothing broken overnight.
⚠️ **No Git commit exists yet.** We need a local save point before changing more (see "Waiting on you").

**Re-plan:** Phase 4 didn't finish on Day 1, so today is **5 phases in ~4 hours**
(full time boxes in `docs/PLAN.md`):

| Time | Phase | Must-have |
|---|---|---|
| 60 min | 4 — Gates + evaluation on B | **You write `gates.py`**; threshold re-chosen WITH gates; P0–P3 on B |
| 35 min | 5 — Messages | English + **Tamil (you)**; Hindi can be cut |
| 60 min | 6 — Website | 4 pages, 50 demo beds |
| 40 min | 7 — Docs + GitHub | README with real numbers, first push |
| 45 min | 8 — Deploy + video | Public link + video |

**Phase 4 is set up for you:**
- `src/gates.py`: 3 functions with signatures, plain-English instructions and hints. The bodies are yours to write.
  - `is_worsening(row)`: Gate 2. Is any of the 5 worsening signs present?
  - `decide(risk, row, last_alert_hour, current_hour, threshold)`: all 3 gates, in order.
  - `run_policy(patient_df, risks, threshold)`: runs `decide` hour by hour and remembers the last REVIEW.
- `tests/test_gates.py`: **18 tests** (master prompt asked for ≥ 8). They cover each gate passing and failing,
  exact boundary values, missing values, the 6-hour cooldown boundary (5 h → SUPPRESSED, 6 h → REVIEW),
  and policies with gates switched off.
- Right now: **18 failed, 9 passed**. That's expected, because the code isn't written yet. Your goal: **27 passed**.
- The tests were checked against a private correct version, which passes all 18, so they're fair.

**Phase 4 progress: everything around your gates is built and ready.**
| File | What it does | Status |
|---|---|---|
| `src/evaluate.py` | Runs **your** `run_policy` on every hospital-B patient. Measures alert PPV, sensitivity, lead time and alerts per 100 patient-days. Compares P0–P3 + NEWS2-lite. Writes `metrics.json`, `gate_comparison.csv` and a chart. | ✅ built |
| `src/train.py` | Now chooses the **official threshold with all three gates** on validation (master-prompt rule: highest PPV with ≥ 60% sensitivity). Also saves the baseline model for hospital B. | ✅ updated |
| `tests/test_evaluate.py` | 5 hand-worked examples prove the metric maths (true/false alerts, window edges, PPV, lead time, alert rate). | ✅ 5 passed |
| `docs/DATA_AND_MODEL.md` | Metric definitions in plain English + the policy table | ✅ |

- **Correction:** "caught" now means a true alert **at or before onset**, as the master prompt says.
  Phase 3 also counted alerts up to 2 h after onset.
- **Dry run:** I ran train + evaluate in a scratch copy with my private reference gates. No errors.
  Train takes 16 s and evaluate 9 s, and the JSON and chart are valid. **I didn't look at the hospital-B numbers.**
  The official results must come from *your* `gates.py`, run once.
- **Tests now:** 14 passed (9 old + 5 new), 18 waiting for your `gates.py`.

**Test run — 20 Oct (latest): `pytest -v` → 14 passed, 18 failed**
| Test file | Result | Why |
|---|---|---|
| `test_features_no_leakage.py` | ✅ 5 / 5 | — |
| `test_train.py` | ✅ 4 / 4 | — |
| `test_evaluate.py` | ✅ 5 / 5 | — |
| `test_gates.py` | ❌ 0 / 18 | **Not a bug:** `src/gates.py` is still empty. All 3 functions raise `NotImplementedError`. |

Phase 4 is **blocked on `gates.py`**. Nothing else can move until it's written (it's the student's file).

**When your 18 gate tests pass, run these two commands for the real Phase 4 results:**
```bash
.venv/bin/python -m src.train      # re-chooses the threshold WITH your gates (validation only)
.venv/bin/python -m src.evaluate   # hospital B, once: P0–P3 comparison + headline
```

---

## ✅ What is done

### Phase 1 — Setup
| Item | Result |
|---|---|
| Git safety | Git was tracking your whole home folder, including `.ssh/` private keys. We made a **new clean repo inside `SepsisGuardian/` only**. The old `/Users/visveshwaran/.git` is unused; we'll remove it later, only with your OK. |
| `.gitignore` | Keeps `data/`, `.venv/`, `work/`, `deliverables/` and `.vscode/` out of GitHub |
| Python | Virtual environment `.venv` with Python 3.9.6 |
| Packages | Pinned and verified: pandas 2.2.3 · numpy 1.26.4 · scikit-learn 1.5.2 · joblib 1.4.2 · streamlit 1.39.1 · plotly 5.24.1 · matplotlib 3.9.4 · requests · tqdm · pytest 8.4.2 |
| Model choice | LightGBM failed (needs `libomp`; no Homebrew) → we use scikit-learn **HistGradientBoostingClassifier** |
| Settings | Every threshold, path and seed lives in `src/config.py` (seed 42) |
| Folders | `scripts/ src/ app/ results/ tests/ docs/`. Unfinished files are placeholders. `src/gates.py` is left for **you** to write. |
| Docs | `README.md`, `CLAUDE.md` and 9 files in `docs/`. `DECISIONS.md` logs every choice. |

### Phase 2 — Data + features
**Download** (`scripts/download_data.py`): real, de-identified ICU data from PhysioNet 2019, free with no login.
2,000 random patients per hospital (seed 42). Your phone hotspot dropped 3 times. Each time, the
resume feature continued where it stopped, and the file list now retries for about 2 minutes. **All 4,000 files arrived.**

**Loader** (`src/load_data.py`): real output:

| Hospital | Role | Patients | With sepsis | Patient-hours | Median stay |
|---|---|---|---|---|---|
| A | train + validation | 2,000 | 157 (7.8%) | 76,567 | 38 h |
| B | test only (untouched) | 2,000 | 108 (5.4%) | 77,220 | 38 h |

Check: every patient has exactly one row per hour (no gaps).

**Features** (`src/features.py`): **51 leakage-safe features** per patient-hour:
current vitals and labs (forward-filled inside each patient) · missing flags · hours since each lab ·
3-hour changes · 6-hour min/max/mean · NEWS2-lite score · age, sex, time in hospital and ICU.

**Tests** (`tests/test_features_no_leakage.py`): `pytest -q` → **5 passed**.
They prove future hours never change past features and one patient's values never leak into another's.

**Docs updated:** feature formulas, leakage rules and the NEWS2-lite table are in `docs/DATA_AND_MODEL.md`.
Model answers for 5 judge questions are in `docs/LEARNING_AND_QA.md`.

### Phase 3 — Model + threshold
`src/train.py` (hospital A only, B untouched). Split by patient: 1,600 train / 400 validation (31 with sepsis).

| Model (validation) | AUROC | AUPRC | Brier |
|---|---|---|---|
| Baseline logistic regression | 0.680 | 0.048 | 0.0193 |
| Main HistGradientBoosting | **0.714** | **0.060** | **0.0191** |

- **Calibration:** isotonic, on patient-grouped folds of the train set. Predicted vs real rates are close
  (top 10% of hours: predicted 6.6%, real 7.1%).
- **Threshold: 0.038.** It's the highest threshold that catches ≥ 60% of sepsis patients: 19 of 31 (61.3%).
- **The problem it shows:** at 0.038, 40.1% of non-sepsis patients get an alert, and there are
  264.2 alert-hours per 100 patient-days. That's too noisy. The gates in Phase 4 must fix it.
- **One failure, fixed (1 of 2):** the first grid (0.05–0.90) was too high for honest calibrated risks.
  We lowered it to 0.010–0.200. Details are in `docs/DECISIONS.md`.
- Saved: `app/demo_data/model.joblib` (6.2 MB), `results/threshold.json`, `results/validation_metrics.json`.
- Tests: `pytest -q` → **9 passed** (4 new: patient split, alert window, threshold rule).

**Verified on 19 Oct:** AUROC/AUPRC/Brier, split sizes, threshold 0.038, 61.3%, 40.1% and 264.2 all match
`results/validation_metrics.json` and `results/threshold.json`. `app/demo_data/` = 6.2 MB (limit 25 MB).
Calibration (6.6% predicted vs 7.1% real, top group) was confirmed by re-running `train.py` (see the test report).

### ⚠️ Two differences from the master prompt (need fixing or explaining)
| # | Master prompt says | What `train.py` does now | Plan |
|---|---|---|---|
| 1 | Calibrate on the **validation** split (isotonic, prefit) | Calibrates on 5 patient-grouped folds of the **train** split | Keep it: validation stays clean for the threshold. Already logged in `DECISIONS.md`. Be ready to explain it to judges. |
| 2 | Choose the threshold by running the **full three-gate policy** (highest alert PPV with sensitivity ≥ 60%) | Uses **risk only, no gates**, because `gates.py` isn't written yet | **In Phase 4, after you write `gates.py`, re-run the threshold choice on validation with all three gates.** Hospital B stays untouched until then. |

**Honest note on scores:** AUROC 0.714 is modest. The best PhysioNet 2019 challenge teams used much more
data and features. AUPRC 0.060 is 3× the random level (0.020). The model ranks better than chance,
but it is far from perfect. That's why the gates and the honest-limits box matter.

---

## 🧪 Test report — 19 Oct 2026 (end of Phase 3)

**Result: everything passed. Nothing is broken.**

### 1. Unit tests: `pytest -v` → 9 passed, 0 failed
| Test | What it proves | Result |
|---|---|---|
| `test_changing_the_future_does_not_change_hour_t` | Scrambling hours after *t* doesn't change features at *t* (no leakage) | ✅ |
| `test_deleting_the_future_does_not_change_hour_t` | Cutting the stay short doesn't change earlier features | ✅ |
| `test_no_filling_across_patients` | Patient 2 never gets patient 1's values | ✅ |
| `test_missing_flag_and_hours_since` | Missing flags and "hours since lab" count correctly | ✅ |
| `test_news2_lite_examples` | NEWS2-lite gives 0 for normal vitals and 14 for very abnormal ones | ✅ |
| `test_split_has_no_patient_on_both_sides` | No patient is in both train and validation | ✅ |
| `test_split_keeps_sepsis_share` | Train and validation have a similar % of sepsis patients | ✅ |
| `test_alert_outside_window_does_not_count` | Alerts outside [onset − 12 h, onset + 2 h] don't count as "caught" | ✅ |
| `test_choose_threshold_picks_highest_that_meets_sensitivity` | The threshold rule picks what it should | ✅ |

### 2. Scripts run on the real data
| Command | Real output | Result |
|---|---|---|
| `python -m src.load_data` | A: 2,000 patients, 7.8% sepsis · B: 2,000 patients, 5.4% sepsis | ✅ |
| `python -m src.features` | 76,567 rows × 51 features | ✅ |
| `python scripts/download_data.py` (re-run) | Listed 20,336 (A) and 20,000 (B); downloaded nothing new; "All files downloaded." | ✅ resume works |
| `python -m src.train` | Finished in 10 s | ✅ |

### 3. Reproducibility (same seed → same answer)
`train.py` was run a second time and the new outputs were compared with the old ones:
`threshold.json`, `validation_metrics.json`, `threshold_grid.csv` → **identical**; `model.joblib` → **byte-identical**.

### 4. Calibration check (validation, 10 equal groups of ~1,480 hours)
| Group | Predicted risk | Real sepsis rate |
|---|---|---|
| Lowest 10% | 0.24% | 0.88% |
| Middle (5th) | 0.95% | 1.01% |
| Highest 10% | 6.64% | 7.09% |

Close in the middle and at the top. At the very bottom, the model **under-estimates** a little (0.24% vs 0.88%).
That doesn't affect alerts, which only fire at ≥ 3.8%. Honest note for the docs.

### 5. Repo safety and code quality
| Check | Result |
|---|---|
| Files Git would upload | 41: only code, docs, results and config. **No `data/`, `.venv/`, `work/`, `deliverables/`.** ✅ |
| `app/` size | 6.3 MB (limit 25 MB) ✅ |
| Passwords / keys / tokens in code | None ✅ |
| Hard-coded personal paths (`/Users/...`) | None ✅ |
| All files compile on Python 3.9 | Yes, with no 3.10-only syntax ✅ |

### Not tested yet (because not built yet)
`tests/test_gates.py` (Phase 4, your `gates.py`) and `tests/test_messages.py` (Phase 5) are still empty.
Hospital B has **not** been used for any model decision. ✅

---

## ⏳ Waiting on you
**Do these first (Day 2):**
1. **Save point:** say "yes, commit" and I'll make the first **local** Git commit. It stays on your laptop;
   nothing is pushed to GitHub. You can also do it yourself: `git add . && git commit -m "Phases 1-3"`.
2. **Write `src/gates.py`.** Start with `is_worsening`, then `decide`, then `run_policy`.
   Check with `.venv/bin/pytest tests/test_gates.py -v`. Ask me for a hint any time.

Phase 3 judge questions (Phase 2 questions are still below; practise both):
1. Your AUROC is 0.714. Is that good? What does AUPRC 0.060 mean when the base rate is 0.020?
2. Why calibrate, and why isn't calibration done on the validation set?
3. Why is the threshold 0.038 and not 0.5?

Phase 2 questions:
1. What is data leakage, and how did you prevent it?
2. How do you fill the hours when lactate isn't measured, and why only forward and only within one patient?
3. Patient p000639 never had lactate measured. What does the model see, and why is that honest?

You skipped the Phase 1 questions. Their model answers are in `docs/LEARNING_AND_QA.md`. Practise them too.

---

## 🔜 What comes next

| Phase | When | What we build | Who | Checkpoint |
|---|---|---|---|---|
| ~~3 — Model + threshold~~ ✅ | Day 1, hour 3 | `train.py`: baseline logistic regression + HistGradientBoosting, calibration, alert threshold chosen on validation only | Claude, you review | Validation numbers |
| **4 — Gates + evaluation** | Day 1, hour 4 | `gates.py` (**you write it**), gate tests, `evaluate.py` on hospital B, P0–P3 comparison | **You** + Claude | "Three gates cut alerts from X to Y" |
| **5 — Explanations + messages** | Day 2, hour 5 | Why-now reasons, data-quality notes, English / **Tamil (you)** / Hindi messages | You + Claude | 3 sample alerts in 3 languages |
| **6 — Website** | Day 2, hour 6 | 50 demo beds + Streamlit pages: Home, Ward Overview, Patient Detail, Results | Claude, you click through | App running locally |
| **7 — Docs + GitHub** | Day 2, hour 7 | README with real results + screenshots, first push with **your** login | You + Claude | Repo online |
| **8 — Deploy + video + submit** | Day 2, hour 8 | Streamlit Cloud link, demo video, checklist | You + Claude | You submit on the portal |

**Saved for the 24-hour final (not built now):** live streaming with FastAPI · nurse feedback buttons ·
"try it yourself" input · fairness page · spoken alerts · LLM shift summary · phone notifications.

**If we fall behind (drop in this order):** ▶ Play button → chart marker polish → Hindi → baseline model.
