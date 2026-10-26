"""Shared loading, colours, language and the safety footer for the Streamlit pages."""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

# Make "src" importable: the website reuses the same gates, explanations and messages.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import config  # noqa: E402
from src.gates import NO_ALERT, REVIEW, SUPPRESSED, WATCH, is_worsening  # noqa: E402
from src.messages import LANGUAGE_NAMES, LANGUAGES, text  # noqa: E402

DEMO_DIR = PROJECT_ROOT / "app" / "demo_data"
STATUS_ORDER = [REVIEW, WATCH, SUPPRESSED, NO_ALERT]
GITHUB_URL = "https://github.com/wyzer-coder/SEPSISGUARDIAN"
PHYSIONET_URL = "https://physionet.org/content/challenge-2019/1.0.0/"


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
AUTH_KEYS = ["redirect_uri", "cookie_secret", "client_id", "client_secret", "server_metadata_url"]


def login_configured() -> bool:
    """True if the secrets have a complete [auth] section (local secrets.toml or Streamlit Cloud secrets).

    Without it the app runs as an open demo, so it never breaks for someone who has no keys.
    """
    try:
        auth = st.secrets.get("auth", {})
    except FileNotFoundError:  # no secrets file at all
        return False
    return all(auth.get(key) for key in AUTH_KEYS)


def require_login() -> None:
    """Show a sign-in screen (Clerk) and stop the page until the user is logged in."""
    if not login_configured():
        st.sidebar.caption("🔓 Open demo: login is not configured.")
        return
    if not st.user.get("is_logged_in", False):  # missing = not signed in (safe default)
        st.title("🩺 SepsisGuardian")
        st.markdown("#### Sepsis early-warning dashboard for ward staff")
        st.write("Please sign in to see the ward. Sign-in is handled by Clerk; this app never sees your password.")
        st.button("Sign in", type="primary", on_click=st.login)
        st.caption(f"⚠️ {text('safety_line', 'en')}")
        st.stop()
    who = st.user.get("email") or st.user.get("name") or "signed-in user"
    st.sidebar.caption(f"👤 Signed in as {who}")
    st.sidebar.button("Sign out", on_click=st.logout)


def setup_page(title: str) -> str:
    """Set the page layout, check login, draw the sidebar and return the chosen language code."""
    st.set_page_config(page_title=f"SepsisGuardian · {title}", page_icon="🩺", layout="wide")
    require_login()
    st.sidebar.title("SepsisGuardian")
    current = st.session_state.get("lang", "en")
    chosen = st.sidebar.selectbox("Alert language", LANGUAGES, index=LANGUAGES.index(current),
                                  format_func=lambda code: LANGUAGE_NAMES[code])
    st.session_state["lang"] = chosen
    st.sidebar.caption("Changes the alert text, reasons and status names.")
    st.sidebar.caption("Demo data: 50 patients from hospital B, never used for training.")
    return chosen


def footer(lang: str) -> None:
    """Show the safety line at the bottom of every page (English + chosen language)."""
    st.divider()
    line = text("safety_line", "en")
    if lang != "en":
        line += "  \n" + text("safety_line", lang)
    st.caption(f"⚠️ {line}")


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data
def load_demo() -> pd.DataFrame:
    """All patient-hours of the 50 demo beds."""
    return pd.read_csv(DEMO_DIR / "demo_patients.csv.gz")


@st.cache_data
def load_metrics() -> Dict:
    """Hospital B results written by src/evaluate.py."""
    return json.loads((DEMO_DIR / "metrics.json").read_text())


@st.cache_data
def load_gate_comparison() -> pd.DataFrame:
    """The P0-P3 + NEWS2-lite comparison table."""
    return pd.read_csv(DEMO_DIR / "gate_comparison.csv")


def threshold() -> float:
    """The alert threshold chosen on hospital A validation."""
    return float(load_metrics()["threshold"])


def rows_at_hour(demo: pd.DataFrame, hour: int) -> pd.DataFrame:
    """One row per bed: the patient's state at this ICU hour (only beds in the ICU at that hour)."""
    return demo[demo["ICULOS"] == hour]


def last_review_before(patient: pd.DataFrame, hour: int) -> Optional[float]:
    """The ICU hour of this patient's last REVIEW before `hour`, or None."""
    earlier = patient[(patient["ICULOS"] < hour) & (patient["status"] == REVIEW)]
    if earlier.empty:
        return None
    return float(earlier["ICULOS"].max())


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------
def status_label(status: str, lang: str) -> str:
    """The status name in the chosen language."""
    return text(f"status_{status}", lang)


def status_chip(status: str, lang: str) -> str:
    """A small coloured label (HTML) for a status."""
    colour = config.STATUS_COLOURS[status]
    return (f"<span style='background:{colour};color:white;padding:3px 10px;border-radius:12px;"
            f"font-weight:600;display:inline-block;line-height:1.4'>{status_label(status, lang)}</span>")


def sex_label(gender) -> str:
    """PhysioNet Gender: 0 = female, 1 = male."""
    if pd.isna(gender):
        return "–"
    return "M" if int(gender) == 1 else "F"


def fmt(value, digits: int = 0, unit: str = "") -> str:
    """Format a number for display, or a dash if it is missing."""
    if pd.isna(value):
        return "–"
    return f"{value:.{digits}f}{unit}"


def gate2_signs(row) -> List[str]:
    """The Gate-2 worsening signs present in this hour, in plain English with values."""
    signs = []
    if not pd.isna(row["MAP_delta_3h"]) and row["MAP_delta_3h"] <= config.GATE2_MAP_DROP:
        signs.append(f"MAP {row['MAP_delta_3h']:+.0f} mmHg / 3 h")
    if not pd.isna(row["HR_delta_3h"]) and row["HR_delta_3h"] >= config.GATE2_HR_RISE:
        signs.append(f"HR {row['HR_delta_3h']:+.0f} bpm / 3 h")
    if not pd.isna(row["Lactate_delta_3h"]) and row["Lactate_delta_3h"] >= config.GATE2_LACTATE_RISE:
        signs.append(f"Lactate {row['Lactate_delta_3h']:+.1f} mmol/L / 3 h")
    if not pd.isna(row["Resp"]) and row["Resp"] >= config.GATE2_RESP_HIGH:
        signs.append(f"Resp {row['Resp']:.0f} /min")
    if not pd.isna(row["O2Sat"]) and row["O2Sat"] <= config.GATE2_O2SAT_LOW:
        signs.append(f"O2Sat {row['O2Sat']:.0f}%")
    return signs


def gate_table(row, last_review: Optional[float], limit: float) -> pd.DataFrame:
    """How the three gates decided for one hour: result and the values behind it."""
    gate1 = row["risk"] >= limit
    worsening = is_worsening(row)
    signs = gate2_signs(row)
    if last_review is None:
        gate3 = True
        gate3_detail = "No REVIEW alert before this hour"
    else:
        hours_since = row["ICULOS"] - last_review
        gate3 = hours_since >= config.GATE3_COOLDOWN_HOURS
        gate3_detail = f"Last REVIEW at hour {last_review:.0f} ({hours_since:.0f} h ago; needs ≥ {config.GATE3_COOLDOWN_HOURS} h)"

    def mark(passed: bool, reached: bool) -> str:
        if not reached:
            return "– not reached"
        return "✓ pass" if passed else "✗ fail"

    return pd.DataFrame([
        {"Gate": "1 · Risk high?", "Result": mark(gate1, True),
         "Values": f"risk {100 * row['risk']:.1f}% vs threshold {100 * limit:.1f}%"},
        {"Gate": "2 · Getting worse now?", "Result": mark(worsening, gate1),
         "Values": ", ".join(signs) if signs else "No worsening sign (missing values never count)"},
        {"Gate": "3 · Not alerted in last 6 h?", "Result": mark(gate3, gate1 and worsening),
         "Values": gate3_detail},
    ])
