
Team HackNovacX (DEX26048) · DEXATHON 2026 Round 2
Deadline: **30 Oct 2026, 11:00 PM IST** (aim for 29 Oct) · Last updated: **23 Oct 2026**

**Status: Claude's building work is DONE. The team now handles GitHub, deployment, the video and the submission.**

```
✅ 1 Data   ✅ 2 Features   ✅ 3 Model   ✅ 4 Gates + results   ✅ 5 Messages   ✅ 6 Website
✅ 7 README + docs (written)          ⬜ GitHub push · deploy · video · submit  ← the team
```

---

## ✅ What is built

| Part | Files | Status |
|---|---|---|
| Data download (2,000 + 2,000 real ICU patients) | `scripts/download_data.py` | ✅ |
| Leakage-safe features (51 per patient-hour) | `src/load_data.py`, `src/features.py` | ✅ |
| Calibrated risk model, threshold chosen with the gates | `src/train.py` | ✅ |
| Three-gate alert controller | `src/gates.py` | ✅ (written by Claude at your request) |
| Hospital B evaluation, P0–P3 comparison | `src/evaluate.py`, `results/` | ✅ |
| Why-now reasons + data-quality notes | `src/explain.py` | ✅ |
| English / **Tamil (yours)** / Hindi messages | `src/messages.py` | ✅ |
| 50 demo beds | `scripts/build_demo_data.py` → `app/demo_data/demo_patients.csv.gz` | ✅ |
| **Website: 4 pages** | `app/Home.py`, `app/pages/`, `app/utils.py` | ✅ |
| README with real numbers + screenshots | `README.md`, `docs/screenshots/` | ✅ |
| All docs (15 judge Q&As, demo script, checklist…) | `docs/` | ✅ |

## 🎯 The result (hospital B, never seen in training)
> **Three gates cut alerts from 544.5 to 76.1 per 100 patient-days while catching 64.8% of sepsis patients.**

| Policy | Alerts / 100 patient-days | Alert PPV | Sepsis patients caught |
|---|---|---|---|
| Risk only | 544.5 | 5.0% | 79 / 108 (73.1%) |
| **SepsisGuardian (3 gates)** | **76.1** | **5.1%** | **70 / 108 (64.8%)** |
| NEWS2-lite bedside score | 269.2 | 4.8% | 69 / 108 (63.9%) |

Honest limits: about 1 alert in 20 is real (PPV 5%). The gates make the alarm quieter, not smarter.
The simple baseline beat our main model on hospital B (AUROC 0.761 vs 0.744). All of this is stated openly on the
Results page and in the README.

## 🌐 The website (4 pages)
| Page | What judges see |
|---|---|
| **Home** | Problem, headline numbers, 5-step pipeline, the three-gates table, team and links |
| **Ward Overview** | "Replay ICU hour" slider · count tiles · bed table with coloured status and top reason · **click a row** to open the patient |
| **Patient Detail** | Heart rate, MAP, breathing, oxygen and risk charts · ▲ REVIEW, ● SUPPRESSED, ◆ WATCH markers · sepsis-onset line · why-now message · "How the gates decided" table |
| **Results** | Headline · P0–P3 chart and table · model scores · honest-limits box |

The sidebar switches the language: English / தமிழ் / हिन्दी. The safety line is on every page.

## 🧪 Testing (23 Oct)
| Check | Result |
|---|---|
| Unit tests `pytest -q` | **45 passed, 0 failed** |
| Automatic page test (all 4 pages × 3 languages × every bed × many hours) | **529 page loads, 0 errors** |
| Real browser click-through (Chrome) | ✅ table row click opens the patient · language switch works · no errors |
| Screenshots checked by eye | ✅ Home, Ward, Patient (Tamil REVIEW + SUPPRESSED), Results |
| App size | 6.3 MB (limit 25 MB) |
| Raw data or `.venv` in Git | **none** |
| Every number in the README and demo script | checked against `results/metrics.json` and the demo data |
| **Fresh-copy test** (only the 57 files Git will upload, new environment, no raw data) | packages install · 45 tests pass · 529 page loads, 0 errors · all 4 pages respond on a real server |

Fixes made while testing: the gate table was cut off (now wraps), REVIEW markers were too small (now bigger),
the ward table scrolled (now shows every bed), decimals were inconsistent (now one decimal everywhere),
and the theme is fixed to light so every viewer sees the same colours.

---

## ⏳ Your part (the team)

**1. Save your work locally first.** Phases 5–6 are **not committed yet**:
```bash
git add -A
git commit -m "Phase 5-6: messages, website, README, docs"
```

**2. Push to GitHub** (with your own login; GitHub Desktop is easiest):
repo `https://github.com/wyzer-coder/SEPSISGUARDIAN`, branch `main`. Make the repo **public**.

**3. Deploy** on Streamlit Community Cloud (share.streamlit.io):
- Repository `wyzer-coder/SEPSISGUARDIAN` · Branch `main` · Main file **`app/Home.py`**
- Advanced settings → Python **3.9**
- Open the link in a **private window** to check it works.

**4. Record the video** with `docs/DEMO_SCRIPT.md` (about 2 min 40 s; the key moment is Bed 20 at hour 39 in Tamil).

**5. Add both links** to the top of `README.md` (the lines say "_link to be added_"), commit and push again.

**6. Practise the 15 questions** in `docs/LEARNING_AND_QA.md`, especially Q6 (the gates), Q7 (why PPV is 5%) and Q10 (AI use).

**7. Submit on the portal** by 29 Oct. Tick `docs/SUBMISSION_CHECKLIST.md`.

## ❓ Two small things still open
- **Did a tool help with the Tamil?** The README says "the Tamil text was provided by the team". If a translation or AI tool
  helped, change that line so it stays true.
- **Short Tamil label for "Suppressed"?** Your full sentence is kept and wraps on screen. If you want it shorter, edit
  `"status_SUPPRESSED"` in `src/messages.py`, e.g. `"தடுக்கப்பட்டது (சமீபத்திய எச்சரிக்கை)"`.

## 🔒 Saved for the 24-hour final (not built)
Nurse "Reviewed / False alarm" buttons · live replay with FastAPI · "try it yourself" vitals input · fairness page ·
spoken alerts · LLM shift summary · phone notifications. See `docs/FINAL_ROUND_BACKLOG.md`.
