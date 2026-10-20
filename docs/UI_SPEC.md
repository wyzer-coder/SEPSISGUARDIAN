# UI SPEC (Streamlit)

## Global
- Wide layout, title "SepsisGuardian".
- Sidebar language selector: English / தமிழ் / हिन्दी (changes alert text).
- Status colours: NO_ALERT green `#2E9E5B` · WATCH yellow `#E0A800` · SUPPRESSED grey `#8A8F98` · REVIEW red `#D64545`.
- Footer on every page: "Clinical decision support — not a diagnosis. A clinician must confirm."
- Data loaded with `st.cache_data` / `st.cache_resource`.

## Home (About)
Problem in 3 lines · 5-step pipeline diagram · three gates table · team · links (GitHub, PhysioNet) · safety note.

## 1 Ward Overview
- Slider "Replay ICU hour" (1 → max). Optional ▶ Play button.
- Count tiles: Review / Watch / Suppressed / No alert at the selected hour.
- Patient table: bed, age, sex, current risk %, coloured status chip, top reason (selected language).
  Sorted Review first, then by risk.
- Selecting a bed opens Patient Detail (via `st.session_state`).

## 2 Patient Detail
- Header: bed, age, sex, status chip, risk %.
- Plotly charts with a shared ICU-hour x-axis: HR, MAP, Resp, O2Sat, and risk with a dashed threshold line.
- Risk markers: red ▲ REVIEW · grey ● SUPPRESSED · yellow ◆ WATCH.
  Vertical line "Sepsis onset (from data)" for sepsis patients.
- "Why now" box for the selected hour in the chosen language + data-quality notes.
- "How the gates decided" mini-table: Gate 1/2/3 ✓/✗ with values.

## 3 Results
- Model table (hospital B): AUROC, AUPRC, Brier — baseline vs main model.
- Gate comparison chart + table (P0–P3).
- Headline: "Three gates cut alerts from X to Y per 100 patient-days while catching Z% of sepsis patients" (from metrics.json).
- Honest-limits box.

## Acceptance
No errors with any bed or hour · works at laptop width · every number has a label and unit.
