"""Streamlit entry page (About / overview).

Run:  .venv/bin/streamlit run app/Home.py
"""

import streamlit as st

from utils import GITHUB_URL, PHYSIONET_URL, footer, load_metrics, setup_page

lang = setup_page("About")
metrics = load_metrics()
naive = metrics["policies"][0]
gated = metrics["policies"][3]

st.title("🩺 SepsisGuardian")
st.markdown("#### Calibrated sepsis risk + a three-gate alert controller + plain-language reasons "
            "in English, தமிழ் and हिन्दी. Decision support, not diagnosis.")

st.subheader("The problem")
st.markdown(
    "- **Sepsis** is the body's extreme response to an infection. Every hour of delay raises the risk of death.\n"
    "- Hospital alert tools fire so often that nurses learn to ignore them (**alert fatigue**).\n"
    "- One widely used sepsis model missed **67%** of sepsis patients, and only **12%** of its alerts were correct "
    "(Wong et al., 2021)."
)

st.subheader("Our result on an unseen hospital")
col1, col2, col3 = st.columns(3)
col1.metric("Alerts per 100 patient-days, risk only", f"{naive['alerts_per_100_patient_days']:.1f}")
col2.metric("Alerts per 100 patient-days, three gates", f"{gated['alerts_per_100_patient_days']:.1f}",
            delta=f"{gated['alerts_per_100_patient_days'] - naive['alerts_per_100_patient_days']:.1f}",
            delta_color="inverse")
col3.metric("Sepsis patients warned before onset", f"{100 * gated['patient_sensitivity']:.1f}%")
st.caption(f"Hospital B: {metrics['patients']:,} patients, {metrics['sepsis_patients']} with sepsis, "
           f"never used for training. Full details on the Results page.")

st.subheader("How it works")
st.code(
    "1. ICU data      PhysioNet 2019: real, de-identified, hourly vitals and labs\n"
    "        ↓\n"
    "2. Features      trends from PAST hours only (e.g. 'MAP fell 14 mmHg in 3 h')\n"
    "        ↓\n"
    "3. Risk model    gradient-boosted trees → calibrated risk %\n"
    "        ↓\n"
    "4. Three gates   page the nurse only if: risk high + getting worse + not paged recently\n"
    "        ↓\n"
    "5. Explain       'why now' in English / தமிழ் / हिन्दी + data-quality notes",
    language=None,
)

st.subheader("The three gates")
st.markdown(
    "| Gate | Question | Rule (editable) | If it fails |\n"
    "|---|---|---|---|\n"
    f"| 1 · Risk | Is the risk high? | risk ≥ {100 * metrics['threshold']:.1f}% (chosen on validation data) "
    "| 🟢 NO ALERT |\n"
    "| 2 · Worsening | Is the patient getting worse now? | any of: MAP fell ≥ 10 mmHg in 3 h · heart rate rose "
    "≥ 15 bpm in 3 h · lactate rose ≥ 0.5 mmol/L in 3 h · breathing ≥ 24/min · oxygen ≤ 92% | 🟡 WATCH (no page) |\n"
    "| 3 · New | Not paged recently? | no REVIEW alert in the previous 6 hours | ⚪ SUPPRESSED (logged) |\n"
    "| All pass | | | 🔴 REVIEW (nurse paged) |"
)
st.caption("Thresholds are heuristics for a prototype. They are not clinically validated. "
           "A missing measurement never counts as 'getting worse'.")

st.subheader("Try it")
st.markdown("👉 **Ward Overview**: replay the ward hour by hour.  \n"
            "👉 **Patient Detail**: charts, the why-now message and how each gate decided.  \n"
            "👉 **Results**: honest numbers on the unseen hospital.")

st.subheader("Team and links")
st.markdown(f"**HackNovacX** · Team ID DEX26048 · DEXATHON 2026, Healthcare track  \n"
            f"[GitHub repository]({GITHUB_URL}) · [PhysioNet/CinC Challenge 2019 data]({PHYSIONET_URL})")

footer(lang)
