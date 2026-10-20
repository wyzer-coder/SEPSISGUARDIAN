# CLAUDE.md — working rules for SepsisGuardian (short form of the master prompt)

## Who and what
- Hackathon prototype for DEXATHON 2026 (team HackNovacX, DEX26048), built WITH a first-year
  CSE student who knows basic Python. Explain simply; one idea per sentence.
- Product: calibrated sepsis risk + three-gate alert controller + EN/TA/HI reasons.
  Decision support, NOT diagnosis.

## How we work
- 8 phases (docs/PLAN.md). Stop at each checkpoint: show results, explain, ask 2–3 judge
  questions, wait for "next".
- Max 2 fixes per failure, then use the backup in the failure playbook.
- The student writes the Tamil messages. Give hints, not answers.
- `src/gates.py` was written by Claude at the student's request (2026-10-20); the student must be able to explain it.

## Non-negotiable
1. Real numbers only, from code output. Never round in our favour.
2. No leakage. Hospital B is used only for final evaluation. Split A by patient.
3. Never call it a diagnostic tool.
4. Never ask for passwords, tokens or portal logins.
5. Raw data (`data/`) never goes to Git.
6. Do NOT build the final-round features (docs/FINAL_ROUND_BACKLOG.md).

## Engineering
- Python 3.9.6 in `.venv` (`python3 -m venv .venv`). No `match`, no `X | Y` hints.
- All thresholds, paths, seeds in `src/config.py`. Seed 42 everywhere.
- Model: sklearn HistGradientBoostingClassifier (LightGBM needs libomp; not available).
- Small functions, plain-English docstrings, type hints, no clever one-liners.
- `pytest -q` must pass before every checkpoint from Phase 2 on.
- `app/` stays under 25 MB (Streamlit Community Cloud).

## Commands
```bash
.venv/bin/python scripts/download_data.py      # resume-safe download (2,000 per hospital)
.venv/bin/pytest -q                              # tests
.venv/bin/streamlit run app/Home.py              # website
```
