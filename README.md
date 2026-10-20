# SepsisGuardian

**Calibrated sepsis risk + a three-gate alert controller + plain-language, multilingual reasons —
decision support, not diagnosis.**

DEXATHON 2026 · Healthcare (MedTech & Clinical Intelligence) · Team HackNovacX (DEX26048)

> ⚠️ Clinical decision support — not a diagnosis. A clinician must confirm.

## The problem
Sepsis kills when it is caught late. Existing hospital alert tools fire so often that nurses
start ignoring them ("alert fatigue"). An external check of one widely used sepsis model
missed 67% of sepsis patients, and only about 12% of its alerts were correct (Wong 2021).

## Our solution
_To be completed in Phase 7._

## How it works
```
 PhysioNet ICU data ─► Features (past hours only) ─► Calibrated risk model
        ─► Three-gate alert controller ─► Why-now reasons in EN / தமிழ் / हिन्दी
```

## The three gates
| Gate | Question | Rule (editable in `src/config.py`) | If it fails |
|---|---|---|---|
| 1 Risk | Is risk high? | risk ≥ threshold (chosen on validation data) | NO_ALERT (green) |
| 2 Worsening | Is the patient getting worse now? | any of: MAP fell ≥ 10 mmHg in 3 h · HR rose ≥ 15 bpm in 3 h · lactate rose ≥ 0.5 mmol/L in 3 h · Resp ≥ 24/min · O2Sat ≤ 92% | WATCH (yellow, no page) |
| 3 New | Not alerted recently? | no REVIEW alert in the previous 6 h | SUPPRESSED (grey, logged) |
| All pass | | | REVIEW (red, nurse alerted) |

These rules are heuristics. They are **not clinically validated**.

## Results (hospital B — never seen in training)
_To be filled from `results/metrics.json` in Phase 7. Real numbers only._

## Screenshots
_To be added in Phase 7._

## Tech stack
Python 3.9 · pandas · NumPy · scikit-learn (HistGradientBoosting, isotonic calibration) ·
Streamlit · Plotly · Matplotlib · pytest

## Run it locally
_Copy-paste commands to be finalised in Phase 7._
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/download_data.py
.venv/bin/streamlit run app/Home.py
```

## Project structure
_See `docs/ARCHITECTURE.md`._

## Limitations and safety
- PhysioNet data comes from US ICUs; Indian hospitals may differ.
- Gate thresholds are heuristics, not clinically validated.
- This is a hackathon prototype, not a medical device.

## Team
HackNovacX — DEX26048

## References
- Wong A. et al. External validation of a widely implemented proprietary sepsis prediction model. *JAMA Internal Medicine*, 2021.
- Reyna M. A. et al. Early prediction of sepsis from clinical data: the PhysioNet/Computing in Cardiology Challenge 2019. *Critical Care Medicine*, 2020.
- Singer M. et al. The Third International Consensus Definitions for Sepsis and Septic Shock (Sepsis-3). *JAMA*, 2016.
- Adams R. et al. Prospective, multi-site study of patient outcomes after implementation of the TREWS machine learning-based early warning system for sepsis. *Nature Medicine*, 2022.

## AI assistance
_One honest line to be written with the team in Phase 7._
