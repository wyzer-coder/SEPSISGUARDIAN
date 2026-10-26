"""Results: model scores on hospital B and the gate comparison."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils import footer, load_gate_comparison, load_metrics, setup_page

lang = setup_page("Results")
metrics = load_metrics()
table = load_gate_comparison()
naive = table.iloc[0]
gated = table.iloc[3]

st.title("Results on an unseen hospital")
st.success(
    f"**Three gates cut alerts from {naive['alerts_per_100_patient_days']:.1f} to "
    f"{gated['alerts_per_100_patient_days']:.1f} per 100 patient-days while catching "
    f"{100 * gated['patient_sensitivity']:.1f}% of sepsis patients.**"
)
st.caption(f"Hospital B: {metrics['patients']:,} patients, {metrics['sepsis_patients']} with sepsis, "
           f"{metrics['patient_hours']:,} patient-hours. Never used for training, calibration or the threshold. "
           f"Threshold {100 * metrics['threshold']:.1f}% chosen on hospital A validation data.")

# --- Gate comparison -----------------------------------------------------------------
st.subheader("Same threshold, different alert policies")
short_names = [name.split(" (")[0] for name in table["policy"]]
colours = ["#8A8F98", "#8A8F98", "#8A8F98", "#D64545", "#4A6FA5"]
figure = make_subplots(rows=1, cols=2, subplot_titles=("Alerts per 100 patient-days (lower = quieter)",
                                                       "Alert PPV: % of alerts that were true (higher = better)"))
figure.add_trace(go.Bar(x=short_names, y=table["alerts_per_100_patient_days"], marker_color=colours,
                        texttemplate="%{y:.1f}", textposition="outside",
                        showlegend=False), row=1, col=1)
figure.add_trace(go.Bar(x=short_names, y=100 * table["alert_ppv"], marker_color=colours,
                        texttemplate="%{y:.1f}", textposition="outside",
                        showlegend=False), row=1, col=2)
figure.update_layout(height=430, margin=dict(l=20, r=20, t=60, b=20))
st.plotly_chart(figure)  # fills the page width by default

shown = pd.DataFrame({
    "Policy": table["policy"],
    "Alerts": table["alerts"],
    "Alerts / 100 patient-days": table["alerts_per_100_patient_days"].round(1),
    "Alert PPV (%)": (100 * table["alert_ppv"]).round(1),
    "Sepsis patients caught": [f"{caught} / {total}" for caught, total in
                               zip(table["patients_caught"], table["sepsis_patients"])],
    "Sensitivity (%)": (100 * table["patient_sensitivity"]).round(1),
    "Median lead time (h)": table["median_lead_time_hours"].round(1),
})
one_decimal = st.column_config.NumberColumn(format="%.1f")
st.dataframe(shown, hide_index=True, width="stretch",
             column_config={"Alerts / 100 patient-days": one_decimal, "Alert PPV (%)": one_decimal,
                            "Sensitivity (%)": one_decimal, "Median lead time (h)": one_decimal})
st.caption("P0 = alert every hour risk ≥ threshold · P1 = + 6-hour cooldown · P2 = + worsening check · "
           "P3 = all three gates (SepsisGuardian) · NEWS2-lite ≥ 5 = a bedside score rule, no model.")

with st.expander("What these words mean"):
    st.markdown(
        "- **True alert:** an alert for a sepsis patient between 12 hours before and 2 hours after onset.\n"
        "- **Alert PPV:** of all alerts, the share that were true. \"When the nurse is paged, how often is it real?\"\n"
        "- **Sensitivity:** of all sepsis patients, the share who got a true alert at or before onset.\n"
        "- **Median lead time:** how many hours before onset the first true alert came (middle value).\n"
        "- **Alerts per 100 patient-days:** how noisy the system is. 100 patient-days = e.g. 10 beds for 10 days."
    )

# --- Model scores --------------------------------------------------------------------
st.subheader("Risk model scores (hour level, hospital B)")
models = metrics["models"]
scores = pd.DataFrame([
    {"Model": "Baseline: logistic regression", "AUROC": models["baseline_logistic"]["auroc"],
     "AUPRC": models["baseline_logistic"]["auprc"], "Brier score": models["baseline_logistic"]["brier"]},
    {"Model": "Main: gradient-boosted trees (used)", "AUROC": models["main_hgb"]["auroc"],
     "AUPRC": models["main_hgb"]["auprc"], "Brier score": models["main_hgb"]["brier"]},
])
four_decimals = st.column_config.NumberColumn(format="%.4f")
st.dataframe(scores, hide_index=True, width="stretch",
             column_config={"AUROC": four_decimals, "AUPRC": four_decimals, "Brier score": four_decimals})
st.caption(f"Share of sepsis hours (what a random guess scores for AUPRC): "
           f"{models['main_hgb']['positive_rate']:.4f}. AUROC: 0.5 = coin flip, 1.0 = perfect. "
           "Brier: lower is better.")

# --- Honest limits -------------------------------------------------------------------
st.subheader("Honest limits")
st.warning(
    f"- **The gates make the alarm quieter, not smarter.** Alert PPV stays about 5% "
    f"({100 * naive['alert_ppv']:.1f}% → {100 * gated['alert_ppv']:.1f}%): roughly 1 alert in 20 is a true early warning.\n"
    f"- **Fewer patients caught:** {int(naive['patients_caught'])} → {int(gated['patients_caught'])} of "
    f"{int(gated['sepsis_patients'])}, and less warning time "
    f"({naive['median_lead_time_hours']:.1f} → {gated['median_lead_time_hours']:.1f} h).\n"
    "- **The simple baseline scored higher than our main model on hospital B.** We chose the model on hospital A "
    "and did not switch after seeing B, because that would be tuning on the test set.\n"
    "- **PhysioNet data comes from US ICUs.** Indian hospitals may differ.\n"
    "- **No patient-history features** (past illnesses, medicines).\n"
    "- **Gate thresholds are heuristics**, not clinically validated.\n"
    "- **This is a hackathon prototype**, not a medical device."
)

footer(lang)
