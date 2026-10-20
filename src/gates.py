"""Three-gate alert controller.

Gate 1 Risk      : risk >= threshold?                     fail -> NO_ALERT  (green)
Gate 2 Worsening : any worsening sign in the last 3 h?    fail -> WATCH     (yellow, no page)
Gate 3 New       : no REVIEW alert in the previous 6 h?   fail -> SUPPRESSED (grey, logged)
All pass                                                       -> REVIEW    (red, nurse alerted)

A missing value never makes Gate 2 pass on its own.
All thresholds live in src/config.py. They are heuristics, not clinically validated.

How to check it:
    .venv/bin/pytest tests/test_gates.py -v
"""

from typing import List, Optional

import pandas as pd

from src import config

NO_ALERT = "NO_ALERT"
WATCH = "WATCH"
SUPPRESSED = "SUPPRESSED"
REVIEW = "REVIEW"


def is_worsening(row) -> bool:
    """Gate 2: return True if ANY ONE worsening sign is present in this hour.

    The signs (thresholds come from src/config.py):
      MAP_delta_3h     <= config.GATE2_MAP_DROP      (MAP fell 10 mmHg or more in 3 h)
      HR_delta_3h      >= config.GATE2_HR_RISE       (heart rate rose 15 bpm or more)
      Lactate_delta_3h >= config.GATE2_LACTATE_RISE  (lactate rose 0.5 mmol/L or more)
      Resp             >= config.GATE2_RESP_HIGH     (24 breaths/min or more)
      O2Sat            <= config.GATE2_O2SAT_LOW     (92% or less)

    `row` works like a dictionary: row["Resp"] gives the value.
    A missing value (NaN) counts as "this sign is NOT present".
    """
    # Sign 1: MAP (blood pressure) fell by 10 mmHg or more in the last 3 hours.
    value = row["MAP_delta_3h"]
    if not pd.isna(value) and value <= config.GATE2_MAP_DROP:
        return True

    # Sign 2: heart rate rose by 15 bpm or more in the last 3 hours.
    value = row["HR_delta_3h"]
    if not pd.isna(value) and value >= config.GATE2_HR_RISE:
        return True

    # Sign 3: lactate rose by 0.5 mmol/L or more in the last 3 hours.
    value = row["Lactate_delta_3h"]
    if not pd.isna(value) and value >= config.GATE2_LACTATE_RISE:
        return True

    # Sign 4: breathing rate is 24 per minute or more.
    value = row["Resp"]
    if not pd.isna(value) and value >= config.GATE2_RESP_HIGH:
        return True

    # Sign 5: oxygen saturation is 92% or less.
    value = row["O2Sat"]
    if not pd.isna(value) and value <= config.GATE2_O2SAT_LOW:
        return True

    # No sign found (or the values were missing): the patient is not worsening right now.
    return False


def decide(risk: float, row, last_alert_hour: Optional[float], current_hour: float,
           threshold: float, use_gate2: bool = True, use_gate3: bool = True) -> str:
    """Return 'NO_ALERT' | 'WATCH' | 'SUPPRESSED' | 'REVIEW' using the three gates, in order.

    risk            : calibrated risk for this hour (0 to 1)
    row             : this hour's features (see is_worsening)
    last_alert_hour : the ICU hour of this patient's last REVIEW, or None if there was none
    current_hour    : this ICU hour (ICULOS)
    threshold       : Gate 1 threshold
    use_gate2       : False = skip Gate 2 (treat it as passed). Used to compare policies.
    use_gate3       : False = skip Gate 3 (treat it as passed). Used to compare policies.

    Gate 3 rule: blocked while fewer than config.GATE3_COOLDOWN_HOURS have passed
    since the last REVIEW. Example: REVIEW at hour 10 -> hours 11..15 blocked, hour 16 allowed.
    """
    # Gate 1 - Risk: is the risk high enough?
    if risk < threshold:
        return NO_ALERT

    # Gate 2 - Worsening: is the patient getting worse right now?
    if use_gate2 and not is_worsening(row):
        return WATCH

    # Gate 3 - New: did we already page the nurse in the last 6 hours?
    if use_gate3 and last_alert_hour is not None:
        hours_since_last_alert = current_hour - last_alert_hour
        if hours_since_last_alert < config.GATE3_COOLDOWN_HOURS:
            return SUPPRESSED

    # All gates passed: page the nurse.
    return REVIEW


def run_policy(patient_df: pd.DataFrame, risks: List[float], threshold: float,
               use_gate2: bool = True, use_gate3: bool = True) -> List[str]:
    """Run decide() on every hour of ONE patient, in time order. Return one status per hour.

    patient_df : this patient's rows, sorted by ICULOS (one row per hour)
    risks      : the risk for each row, same order and same length as patient_df

    Only a REVIEW starts a new cooldown; WATCH and SUPPRESSED do not.
    """
    statuses = []
    last_alert_hour = None  # no alert yet for this patient

    for position in range(len(patient_df)):
        row = patient_df.iloc[position]
        current_hour = row["ICULOS"]
        status = decide(risks[position], row, last_alert_hour, current_hour, threshold,
                        use_gate2=use_gate2, use_gate3=use_gate3)
        if status == REVIEW:
            last_alert_hour = current_hour  # remember when we last paged the nurse
        statuses.append(status)

    return statuses
