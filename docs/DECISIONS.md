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

## 2026-10-23 — Tamil messages added
- Tamil text provided by the team. The `{bed}`, `{risk}`, `{value}` and `{hours}` placeholders had been lost
  when pasting, so Claude put them back. The long Tamil "Suppressed" label was kept as written (it wraps on screen).

## 2026-10-23 — Why-now reasons: levels only when they break the limit
- Breathing rate and oxygen are levels, not changes. They are listed as a reason only when they break the Gate-2 limit,
  so a normal value is never shown as a "reason". Changes (MAP, HR, lactate) are listed from half the limit upwards.

## 2026-10-23 — Website
- Streamlit, 4 pages; demo of 50 random hospital-B patients (constraints above); light theme fixed in `.streamlit/config.toml`.
- Tested: 529 automatic page loads (all pages, all 3 languages, every bed, many hours) with 0 errors,
  plus a real-browser click-through (table row click opens the patient).
- Team decision: the team handles GitHub upload, deployment, the video and the portal submission themselves.

## 2026-10-23 — No login in Round 2
- Considered Clerk. Its setup tool targets JavaScript frameworks (Next.js); our app is Python/Streamlit.
- A sign-in wall would slow judges down, and the demo uses public de-identified data. Added to the final-round backlog (#8).

## 2026-10-23 — Login connected (replaces "No login in Round 2" above)
- The team asked to connect login after all. Clerk's CLI targets JavaScript apps, so we use **Streamlit's built-in
  `st.login`** with **Clerk as the OpenID Connect provider**.
- Streamlit upgraded 1.39.1 → **1.50.0** (`streamlit[auth]`, Authlib 1.6.12); the newest version that still runs on Python 3.9.
  Follow-ups: `use_container_width` → `width="stretch"`; the gate table moved to full width (it was squeezed in 1.50).
- **Safe by design:** no `[auth]` settings → open demo; complete settings → every page shows only "Sign in".
  A missing `is_logged_in` value counts as *not* signed in.
- Secrets live in `.streamlit/secrets.toml` (git-ignored); a template is committed. Claude never saw or handled real keys.
- Tested: 3 automatic login tests; a real browser with fake Clerk settings (all 4 pages hidden, Sign in goes to `/auth/login`).
  **Not tested:** a real Clerk sign-in, because that needs the team's own Clerk keys.

## 2026-10-23 — No database (Neon) in Round 2
- The app only reads fixed demo files; nothing needs saving yet. Node.js is not installed, and the Neon CLI steps assume a JavaScript app.
- The first real use of a database is nurse feedback (backlog #1), which belongs in the 24-hour final. Neon is planned there.

## 2026-10-23 — Authlib pinned to 1.6.5 (sign-in bug found in full testing)
- Symptom: clicking **Sign in** gave `400: 'NoneType' object does not support item assignment`; Clerk was never reached.
- Cause: Streamlit 1.50 keeps the sign-in state in a cache and passes no session. Authlib 1.6.6+ also writes into that
  missing session. Streamlit only requires `Authlib>=1.3.2`, so pip had installed the newest, broken 1.6.12.
- Fix: `Authlib==1.6.5`, the newest version whose state code skips the session when a cache is used (checked 1.6.0–1.6.12).
- Proof: a real browser now reaches our Clerk instance's `/oauth/authorize` with `scope=openid email profile`;
  regression test `test_installed_authlib_works_with_streamlit_sign_in` passes on 1.6.5 and fails on 1.6.12.
- Note: newer Authlib releases may carry security fixes; revisit when Streamlit supports them.

## 2026-10-26 — Streamlit Cloud must use Python 3.12
- First deploy used the Cloud default, Python 3.14.9. Our pinned pandas, numpy, scikit-learn and matplotlib have no
  ready-made wheels for 3.14, so Cloud tried to build them from source; the app started without plotly (ModuleNotFoundError).
- Checked with `pip download --only-binary=:all:` for Linux: Python 3.12 has wheels for all 60 files; 3.13 fails (numpy 1.26.4).
- Fix: redeploy with Python 3.12 in Advanced settings. No code change. The laptop stays on Python 3.9.
