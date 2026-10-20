"""Leakage-safe features.

The one rule: the features for hour t use ONLY hour t and earlier hours of the SAME patient.
Nothing from the future, nothing from other patients.

Run it to print one patient's features:
    .venv/bin/python -m src.features
"""

from typing import List, Tuple

import pandas as pd

from src import config

ID_COLUMNS = ["patient_id", "hospital", "ICULOS"]


# ---------------------------------------------------------------------------
# Feature names (fixed and documented in docs/DATA_AND_MODEL.md)
# ---------------------------------------------------------------------------
def feature_column_names() -> List[str]:
    """Return the fixed, ordered list of feature names the model uses."""
    names = []
    names += config.VITALS                                     # current value (forward-filled)
    names += config.LABS                                       # current value (forward-filled)
    names += [f"{lab}_missing" for lab in config.LABS]         # 1 = not measured this hour
    names += [f"hours_since_{lab}" for lab in config.LABS]     # hours since last measurement
    for vital in config.VITALS:
        names += [f"{vital}_delta_3h", f"{vital}_min_6h", f"{vital}_max_6h", f"{vital}_mean_6h"]
    names += ["Lactate_delta_3h", "news2_lite"]
    names += config.STATIC
    return names


FEATURE_COLUMNS = feature_column_names()


# ---------------------------------------------------------------------------
# Step 1: missing flags and hours since last lab (BEFORE filling)
# ---------------------------------------------------------------------------
def add_missing_flags(data: pd.DataFrame) -> pd.DataFrame:
    """Add <lab>_missing = 1 when the lab was not measured in that hour."""
    for lab in config.LABS:
        data[f"{lab}_missing"] = data[lab].isna().astype(int)
    return data


def add_hours_since(data: pd.DataFrame) -> pd.DataFrame:
    """Add hours_since_<lab>: hours since the lab was last measured (capped at 48).

    If the lab was never measured so far, the value is 48.
    """
    patients = data["patient_id"]
    for lab in config.LABS:
        measured_hour = data["ICULOS"].where(data[lab].notna())
        last_measured_hour = measured_hour.groupby(patients).ffill()
        hours_since = data["ICULOS"] - last_measured_hour
        data[f"hours_since_{lab}"] = hours_since.fillna(config.HOURS_SINCE_CAP).clip(upper=config.HOURS_SINCE_CAP)
    return data


# ---------------------------------------------------------------------------
# Step 2: forward-fill inside each patient
# ---------------------------------------------------------------------------
def forward_fill(data: pd.DataFrame) -> pd.DataFrame:
    """Carry the last known value forward, inside each patient only.

    Never across patients and never backward (backward would use the future).
    """
    columns = config.VITALS + config.LABS + ["HospAdmTime"]
    data[columns] = data.groupby("patient_id")[columns].ffill()
    return data


# ---------------------------------------------------------------------------
# Step 3: trends (3-hour change, 6-hour window)
# ---------------------------------------------------------------------------
def add_trends(data: pd.DataFrame) -> pd.DataFrame:
    """Add 3-hour changes and 6-hour min / max / mean for each vital, plus Lactate_delta_3h.

    <v>_delta_3h = v(t) - v(t-3). It is empty for the first 3 hours of a stay.
    The 6-hour window is hours t-5 .. t (only the past).
    """
    grouped = data.groupby("patient_id")
    for vital in config.VITALS:
        data[f"{vital}_delta_3h"] = data[vital] - grouped[vital].shift(3)
        window = grouped[vital].rolling(6, min_periods=1)
        data[f"{vital}_min_6h"] = window.min().reset_index(level=0, drop=True)
        data[f"{vital}_max_6h"] = window.max().reset_index(level=0, drop=True)
        data[f"{vital}_mean_6h"] = window.mean().reset_index(level=0, drop=True)
    data["Lactate_delta_3h"] = data["Lactate"] - grouped["Lactate"].shift(3)
    return data


# ---------------------------------------------------------------------------
# Step 4: NEWS2-lite score
# ---------------------------------------------------------------------------
def points(value: float, limits: List[Tuple[float, int]], above_all: int) -> int:
    """Return the points for a value using (upper_limit, points) pairs checked in order.

    Example: limits [(8, 3), (11, 1)] means "<= 8 gives 3 points, <= 11 gives 1 point".
    A value above every limit gets above_all points. A missing value gets 0 points.
    """
    if pd.isna(value):
        return 0
    for upper_limit, score in limits:
        if value <= upper_limit:
            return score
    return above_all


def news2_lite_row(resp: float, o2sat: float, sbp: float, hr: float, temp: float) -> int:
    """NEWS2-style score from 5 vitals (no consciousness or oxygen-therapy items).

    Point table (see docs/DATA_AND_MODEL.md):
      Resp  <=8:3   9-11:1   12-20:0   21-24:2   >=25:3
      O2Sat <=91:3  92-93:2  94-95:1   >=96:0
      SBP   <=90:3  91-100:2 101-110:1 111-219:0 >=220:3
      HR    <=40:3  41-50:1  51-90:0   91-110:1  111-130:2 >=131:3
      Temp  <=35.0:3 35.1-36.0:1 36.1-38.0:0 38.1-39.0:1 >=39.1:2
    """
    total = 0
    total += points(resp, [(8, 3), (11, 1), (20, 0), (24, 2)], above_all=3)
    total += points(o2sat, [(91, 3), (93, 2), (95, 1)], above_all=0)
    total += points(sbp, [(90, 3), (100, 2), (110, 1), (219, 0)], above_all=3)
    total += points(hr, [(40, 3), (50, 1), (90, 0), (110, 1), (130, 2)], above_all=3)
    total += points(temp, [(35.0, 3), (36.0, 1), (38.0, 0), (39.0, 1)], above_all=2)
    return total


def add_news2_lite(data: pd.DataFrame) -> pd.DataFrame:
    """Add the news2_lite score for every row (uses only that hour's filled vitals)."""
    scores = []
    for resp, o2sat, sbp, hr, temp in zip(data["Resp"], data["O2Sat"], data["SBP"], data["HR"], data["Temp"]):
        scores.append(news2_lite_row(resp, o2sat, sbp, hr, temp))
    data["news2_lite"] = scores
    return data


# ---------------------------------------------------------------------------
# All steps together
# ---------------------------------------------------------------------------
def build_features(raw: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Turn raw hourly data into the feature table.

    Returns (table, FEATURE_COLUMNS). The table also keeps patient_id, hospital,
    ICULOS and SepsisLabel so we can split, train and evaluate.
    """
    data = raw.sort_values(["patient_id", "ICULOS"]).reset_index(drop=True).copy()
    data = add_missing_flags(data)
    data = add_hours_since(data)
    data = forward_fill(data)
    data = add_trends(data)
    data = add_news2_lite(data)
    keep = ID_COLUMNS + FEATURE_COLUMNS + [config.LABEL]
    keep = list(dict.fromkeys(keep))  # ICULOS is both an id and a feature; keep it once
    return data[keep], FEATURE_COLUMNS


def main() -> None:
    """Build features for hospital A and print one sepsis patient's last hours."""
    from src.load_data import load_set, patient_summary

    raw = load_set(config.HOSPITAL_FOLDERS["A"], "A")
    features, columns = build_features(raw)
    print(f"Feature table: {features.shape[0]} rows x {len(columns)} features")

    summary = patient_summary(raw)
    # A sepsis patient whose label switches on after at least 15 ICU hours, so we see the change.
    late_onset = summary[(summary["has_sepsis"] == 1) & (summary["onset_hour"] >= 15 + config.LABEL_SHIFT_HOURS)]
    example_id = late_onset["patient_id"].iloc[0]
    onset = late_onset["onset_hour"].iloc[0]
    example = features[features["patient_id"] == example_id]
    label_start = onset - config.LABEL_SHIFT_HOURS
    example = example[(example["ICULOS"] >= label_start - 6) & (example["ICULOS"] <= label_start + 3)]
    show = ["ICULOS", "HR", "HR_delta_3h", "MAP", "MAP_delta_3h", "Resp", "O2Sat",
            "Lactate", "hours_since_Lactate", "news2_lite", config.LABEL]
    print(f"\nPatient {example_id}: SepsisLabel turns 1 at hour {label_start:.0f}, "
          f"clinical onset at hour {onset:.0f} (label + 6). Hours around the label switch:")
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(example[show].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
