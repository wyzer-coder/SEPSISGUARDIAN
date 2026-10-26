"""Patient Detail: vitals, risk line, why-now and the gate decisions."""

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils import (fmt, footer, gate_table, last_review_before, load_demo, setup_page, sex_label,
                   status_chip, threshold)
from src import config
from src.explain import data_quality_items, reason_items
from src.gates import REVIEW, SUPPRESSED, WATCH
from src.messages import render_alert, text

lang = setup_page("Patient Detail")
demo = load_demo()
limit = threshold()
beds = sorted(demo["bed"].unique())

st.title("Patient Detail")

# --- Choose bed and hour ---------------------------------------------------------
current_bed = st.session_state.get("bed", beds[0])
col_bed, col_hour = st.columns([1, 3])
bed = col_bed.selectbox("Bed", beds, index=beds.index(current_bed), format_func=lambda b: f"Bed {b}")
st.session_state["bed"] = int(bed)

patient = demo[demo["bed"] == bed].sort_values("ICULOS")
first_hour = int(patient["ICULOS"].min())
last_hour = int(patient["ICULOS"].max())
wanted = int(st.session_state.get("replay_hour", last_hour))
start_hour = min(max(wanted, first_hour), last_hour)  # keep the hour inside this patient's stay
if first_hour == last_hour:
    hour = first_hour
    col_hour.caption(f"This patient has only one ICU hour ({hour}).")
else:
    hour = col_hour.slider("ICU hour", min_value=first_hour, max_value=last_hour, value=start_hour)
st.session_state["replay_hour"] = hour

row = patient[patient["ICULOS"] == hour].iloc[0]

# --- Header ----------------------------------------------------------------------
st.markdown(
    f"### Bed {bed} &nbsp; {status_chip(row['status'], lang)}",
    unsafe_allow_html=True,
)
head = st.columns(5)
head[0].metric("Age", f"{fmt(row['Age'])} years")
head[1].metric("Sex", sex_label(row["Gender"]))
head[2].metric("Risk now", f"{100 * row['risk']:.1f}%")
head[3].metric("Threshold", f"{100 * limit:.1f}%")
head[4].metric("ICU hour", f"{hour} of {last_hour}")
if row["has_sepsis"] == 1:
    st.caption(f"From the data: this patient developed sepsis (onset at ICU hour {row['onset_hour']:.0f}). "
               "The system never sees this label while running; it is shown only to judge the alerts.")
else:
    st.caption("From the data: this patient did not develop sepsis during the stay.")

# --- Charts ----------------------------------------------------------------------
figure = make_subplots(rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                       subplot_titles=("Heart rate (bpm)", "MAP (mmHg)", "Breathing rate (/min)",
                                       "Oxygen saturation (%)", "Sepsis risk (%)"))
vitals = [("HR", 1), ("MAP", 2), ("Resp", 3), ("O2Sat", 4)]
for column, chart_row in vitals:
    figure.add_trace(go.Scatter(x=patient["ICULOS"], y=patient[column], mode="lines", name=column,
                                line=dict(color="#4A6FA5"), showlegend=False), row=chart_row, col=1)
figure.add_trace(go.Scatter(x=patient["ICULOS"], y=100 * patient["risk"], mode="lines", name="Risk",
                            line=dict(color="#333333"), showlegend=False), row=5, col=1)
figure.add_hline(y=100 * limit, line_dash="dash", line_color="#D64545", row=5, col=1,
                 annotation_text=f"threshold {100 * limit:.1f}%", annotation_position="top left")

markers = [(WATCH, "diamond", 8, "WATCH (high risk, not worsening)"),
           (SUPPRESSED, "circle", 9, "SUPPRESSED (paged recently)"),
           (REVIEW, "triangle-up", 16, "REVIEW (nurse paged)")]  # REVIEW drawn last and biggest, so it is on top
for status, symbol, size, label in markers:
    hours = patient[patient["status"] == status]
    figure.add_trace(go.Scatter(x=hours["ICULOS"], y=100 * hours["risk"], mode="markers", name=label,
                                marker=dict(symbol=symbol, size=size, color=config.STATUS_COLOURS[status],
                                            line=dict(width=1, color="white"))), row=5, col=1)

for chart_row in range(1, 6):
    figure.add_vline(x=hour, line_color="#888888", line_width=1, row=chart_row, col=1)
    if row["has_sepsis"] == 1:
        figure.add_vline(x=row["onset_hour"], line_dash="dot", line_color="#D64545", row=chart_row, col=1)
if row["has_sepsis"] == 1:
    figure.add_annotation(x=row["onset_hour"], y=1.0, xref="x", yref="paper", text="Sepsis onset (from data)",
                          showarrow=False, font=dict(color="#D64545"), xanchor="left", yanchor="bottom")

figure.update_xaxes(title_text="ICU hour", row=5, col=1)
figure.update_layout(height=900, margin=dict(l=40, r=20, t=60, b=40),
                     legend=dict(orientation="h", yanchor="bottom", y=-0.12, x=0))
st.plotly_chart(figure)  # fills the page width by default
st.caption("Grey vertical line = the selected hour. Values between measurements are the last known value.")

# --- Why now ------------------------------------------------------------------------
st.subheader(text("why_now_title", lang).rstrip("?:"))
items = reason_items(row) + data_quality_items(row)
if row["status"] == REVIEW:
    st.error(render_alert(int(bed), 100 * row["risk"], items, lang).replace("\n", "  \n"))
else:
    lines = [f"{text('status_' + row['status'], lang)}"]
    for key, values in reason_items(row):
        lines.append("• " + text(key, lang, values))
    if not reason_items(row):
        lines.append("• " + text("no_reason", lang))
    notes = data_quality_items(row)
    if notes:
        lines.append(text("data_quality_title", lang))
        for key, values in notes:
            lines.append("• " + text(key, lang, values))
    st.info("  \n".join(lines))
    st.caption("No page at this hour. The full alert message is shown only for REVIEW hours.")

# --- How the gates decided (full width, so no column is squeezed) -------------------
st.subheader("How the gates decided")
st.table(gate_table(row, last_review_before(patient, hour), limit).set_index("Gate"))
review_hours = patient[patient["status"] == REVIEW]["ICULOS"].astype(int).tolist()
st.caption("REVIEW alerts for this patient at ICU hours: "
           + (", ".join(str(h) for h in review_hours) if review_hours else "none"))

footer(lang)
