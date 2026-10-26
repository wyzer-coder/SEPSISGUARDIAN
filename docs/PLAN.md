# PLAN — 8 working hours (2 days × 4 hours)

Deadline: 30 Oct 2026, 11:00 PM IST (aim for 29 Oct).

## Day 1 — 19 Oct
- [x] **Phase 1 — Setup + plan**: venv, requirements, folders, .gitignore, doc skeletons, download started.
- [x] **Phase 2 — Data + features**: loader, patient summary, features, no-leakage test.
- [x] **Phase 3 — Model + threshold**: baseline + main model, calibration, threshold on validation.
- [ ] ~~Phase 4~~ → moved to Day 2 (not finished on Day 1).

## Day 2 — 20 Oct (re-planned: 5 phases in ~4 hours)
| Time box | Phase | Must-have | Can cut |
|---|---|---|---|
| 60 min | - [x] **Phase 4 — Gates + evaluation on B** | Student writes `gates.py` until `tests/test_gates.py` passes · re-choose the threshold on validation WITH the gates · P0–P3 on B · `metrics.json` | NEWS2-lite baseline row |
| 35 min | - [x] **Phase 5 — Explanations + messages** | `why_now`, data-quality notes, English + **Tamil (student)**, message tests | Hindi |
| 60 min | - [x] **Phase 6 — Website** | Demo data (50 beds) · Home, Ward Overview, Patient Detail, Results | ▶ Play button, marker polish |
| 40 min | - [ ] **Phase 7 — Docs + GitHub** | README with real numbers + screenshots · first push (student's own login) | Polishing secondary docs |
| 45 min | - [ ] **Phase 8 — Deploy + video + submit** | Streamlit Cloud link · demo video · checklist | — (the portal can be done by 29 Oct) |

If Day 2 runs out, Phases 7–8 move to the next session. The deadline (30 Oct) still leaves room.

## Cut list if behind (drop in this order)
1. ▶ Play button
2. Plotly marker polish
3. Hindi (keep English + Tamil)
4. Baseline logistic regression
5. Smaller subset (already at 2,000 per hospital)
