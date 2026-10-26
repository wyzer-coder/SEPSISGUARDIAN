"""Ward Overview: replay an ICU hour and see every bed's status."""

import pandas as pd
import streamlit as st

from utils import (STATUS_ORDER, footer, fmt, load_demo, rows_at_hour, setup_page, sex_label, status_chip,
                   status_label)
from src import config
from src.explain import reason_items
from src.gates import NO_ALERT, REVIEW, SUPPRESSED, WATCH
from src.messages import text

lang = setup_page("Ward Overview")
demo = load_demo()
max_hour = int(demo["ICULOS"].max())

st.title("Ward Overview")
st.caption("Replay the ICU hour by hour. Each bed is one real hospital-B patient; bed numbers are made up.")

# Start at the hour with the most REVIEW alerts, unless the user already picked one.
if "replay_hour" not in st.session_state:
    review_hours = demo[demo["status"] == REVIEW]["ICULOS"].value_counts()
    st.session_state["replay_hour"] = int(review_hours.idxmax()) if not review_hours.empty else 1

hour = st.slider("Replay ICU hour", min_value=1, max_value=max_hour, value=st.session_state["replay_hour"],
                 help="Hours since ICU admission. Every patient is shown at the same ICU hour.")
st.session_state["replay_hour"] = hour
now = rows_at_hour(demo, hour)

# --- Count tiles ---------------------------------------------------------------
tiles = st.columns(4)
icons = {REVIEW: "🔴", WATCH: "🟡", SUPPRESSED: "⚪", NO_ALERT: "🟢"}
for column, status in zip(tiles, STATUS_ORDER):
    column.metric(f"{icons[status]} {status_label(status, lang)}", int((now["status"] == status).sum()))
st.caption(f"{len(now)} of 50 beds are in the ICU at hour {hour}. "
           "Patients whose stay is shorter (or longer) are not shown at this hour.")

if now.empty:
    st.info("No demo patient is in the ICU at this hour. Move the slider to an earlier hour.")
    footer(lang)
    st.stop()


# --- Patient table ---------------------------------------------------------------
def top_reason(row) -> str:
    """The biggest why-now reason at this hour, in the chosen language."""
    items = reason_items(row)
    if not items:
        return text("no_reason", lang)
    key, values = items[0]
    return text(key, lang, values)


table = now.copy()
table["order"] = table["status"].map({status: rank for rank, status in enumerate(STATUS_ORDER)})
table = table.sort_values(["order", "risk"], ascending=[True, False])
shown = pd.DataFrame({
    "Bed": table["bed"].to_numpy(),
    "Age (years)": [fmt(age) for age in table["Age"]],
    "Sex": [sex_label(gender) for gender in table["Gender"]],
    "Risk (%)": (100 * table["risk"]).round(1).to_numpy(),
    "Status": [status_label(status, lang) for status in table["status"]],
    "Top reason": [top_reason(row) for _, row in table.iterrows()],
})
status_of_row = list(table["status"])


def colour_status(_column: pd.Series):
    """Colour each Status cell with its status colour."""
    return [f"background-color: {config.STATUS_COLOURS[status]}; color: white; font-weight: 600"
            for status in status_of_row]


styled = shown.style.apply(colour_status, subset=["Status"]).format({"Risk (%)": "{:.1f}"})
st.subheader(f"Beds at ICU hour {hour}")
st.caption("Sorted: REVIEW first, then by risk. **Click a row** to open that patient.")
table_height = 35 * (len(shown) + 1) + 3  # tall enough to show every bed without scrolling
event = st.dataframe(styled, hide_index=True, width="stretch", on_select="rerun",
                     selection_mode="single-row", key="ward_table", height=table_height)

selected_rows = event.selection.rows if event is not None else []
if selected_rows:
    st.session_state["bed"] = int(shown.iloc[selected_rows[0]]["Bed"])
    st.switch_page("pages/2_Patient_Detail.py")

# A fallback for people who prefer a drop-down.
col_pick, col_button = st.columns([3, 1])
bed_choice = col_pick.selectbox("Or choose a bed", list(shown["Bed"]),
                                format_func=lambda bed: f"Bed {bed}")
if col_button.button("Open patient", width="stretch"):
    st.session_state["bed"] = int(bed_choice)
    st.switch_page("pages/2_Patient_Detail.py")

st.markdown("**Status colours:** " + " ".join(status_chip(status, lang) for status in STATUS_ORDER),
            unsafe_allow_html=True)
footer(lang)
