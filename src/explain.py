"""Why-now reasons and data-quality notes, returned as message keys.

This file decides WHAT to say. src/messages.py decides HOW to say it (English / Tamil / Hindi).

Run it to see 3 real alerts from hospital B in all languages:
    .venv/bin/python -m src.explain
"""

from typing import Dict, List, Tuple

import pandas as pd

from src import config

MAX_REASONS = 3
# A change is mentioned only if it is at least half-way to its Gate-2 limit (avoids tiny, noisy changes).
MIN_REASON_SIZE = 0.5
LACTATE_STALE_HOURS = 6


def value_or_none(row, column: str):
    """Return row[column], or None if it is missing."""
    value = row[column]
    if pd.isna(value):
        return None
    return float(value)


def reason_sizes(row) -> Dict[str, float]:
    """Score each possible reason. 1.0 = exactly at its Gate-2 limit, 2.0 = twice as far.

    Only changes in the WORSE direction get a score. Missing values get no score.
    Dividing by the limit puts mmHg, bpm and mmol/L on one scale, so we can rank them.
    """
    sizes = {}
    map_change = value_or_none(row, "MAP_delta_3h")
    if map_change is not None and map_change < 0:
        sizes["map_fell"] = map_change / config.GATE2_MAP_DROP           # both negative -> positive
    hr_change = value_or_none(row, "HR_delta_3h")
    if hr_change is not None and hr_change > 0:
        sizes["hr_rose"] = hr_change / config.GATE2_HR_RISE
    lactate_change = value_or_none(row, "Lactate_delta_3h")
    if lactate_change is not None and lactate_change > 0:
        sizes["lactate_rose"] = lactate_change / config.GATE2_LACTATE_RISE
    # Breathing rate and oxygen are LEVELS, not changes: mention them only when they break the Gate-2 limit.
    resp = value_or_none(row, "Resp")
    if resp is not None and resp >= config.GATE2_RESP_HIGH:
        sizes["resp_high"] = resp / config.GATE2_RESP_HIGH
    o2sat = value_or_none(row, "O2Sat")
    if o2sat is not None and o2sat <= config.GATE2_O2SAT_LOW:
        # Distance below 100%, compared with the Gate-2 distance (100 - 92 = 8 points).
        sizes["o2_low"] = (100 - o2sat) / (100 - config.GATE2_O2SAT_LOW)
    return sizes


def why_now(row) -> List[str]:
    """Return up to 3 reason keys, biggest first.

    Gate-2 triggers (size >= 1) always rank above smaller changes.
    Changes smaller than MIN_REASON_SIZE are not mentioned.
    """
    sizes = reason_sizes(row)
    keys = [key for key, size in sizes.items() if size >= MIN_REASON_SIZE]
    keys.sort(key=lambda key: sizes[key], reverse=True)
    return keys[:MAX_REASONS]


def reason_value(row, key: str) -> str:
    """Return the number to show for a reason, already rounded for display."""
    if key == "map_fell":
        return f"{abs(row['MAP_delta_3h']):.0f}"
    if key == "hr_rose":
        return f"{row['HR_delta_3h']:.0f}"
    if key == "lactate_rose":
        return f"{row['Lactate_delta_3h']:.1f}"
    if key == "resp_high":
        return f"{row['Resp']:.0f}"
    if key == "o2_low":
        return f"{row['O2Sat']:.0f}"
    raise KeyError(key)


def reason_items(row) -> List[Tuple[str, Dict[str, str]]]:
    """why_now() keys plus the values to fill in, e.g. [("map_fell", {"value": "14"})]."""
    return [(key, {"value": reason_value(row, key)}) for key in why_now(row)]


def data_quality(row) -> List[str]:
    """Return note keys about missing or old data that lowers confidence."""
    notes = []
    if pd.isna(row["Lactate"]):
        notes.append("lactate_never")
    elif row["hours_since_Lactate"] > LACTATE_STALE_HOURS:
        notes.append("lactate_stale")
    if pd.isna(row["MAP_delta_3h"]) and pd.isna(row["HR_delta_3h"]):
        notes.append("trends_not_ready")
    return notes


def data_quality_items(row) -> List[Tuple[str, Dict[str, str]]]:
    """data_quality() keys plus the values to fill in."""
    items = []
    for key in data_quality(row):
        values = {}
        if key == "lactate_stale":
            values["hours"] = f"{row['hours_since_Lactate']:.0f}"
        items.append((key, values))
    return items


def main() -> None:
    """Print 3 real REVIEW alerts from hospital B in every language."""
    from src.features import build_features
    from src.gates import REVIEW, run_policy
    from src.load_data import load_set
    from src.messages import LANGUAGES, render_alert
    import joblib

    saved = joblib.load(config.MODEL_PATH)
    raw = load_set(config.HOSPITAL_FOLDERS["B"], "B")
    features, _ = build_features(raw)
    shown = 0
    for _, patient in features.groupby("patient_id"):
        risks = saved["model"].predict_proba(patient[saved["features"]])[:, 1]
        statuses = run_policy(patient, list(risks), saved["threshold"])
        for position, status in enumerate(statuses):
            if status != REVIEW:
                continue
            row = patient.iloc[position]
            reasons = reason_items(row) + data_quality_items(row)
            print(f"--- patient {row['patient_id']}, ICU hour {row['ICULOS']:.0f} ---")
            for language in LANGUAGES:
                print(render_alert(shown + 1, round(100 * risks[position], 1), reasons, language))
                print()
            shown += 1
            break
        if shown == 3:
            break


if __name__ == "__main__":
    main()
