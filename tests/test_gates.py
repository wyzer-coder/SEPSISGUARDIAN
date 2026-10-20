"""Tests for the three-gate alert controller (src/gates.py).

Run:  .venv/bin/pytest tests/test_gates.py -v
They all fail until gates.py is written. Make them pass one by one.
"""

import numpy as np
import pandas as pd

from src.gates import NO_ALERT, REVIEW, SUPPRESSED, WATCH, decide, is_worsening, run_policy

THRESHOLD = 0.04
HIGH_RISK = 0.10
LOW_RISK = 0.01


def calm_row() -> dict:
    """An hour with normal values: no worsening sign at all."""
    return {"MAP_delta_3h": 0.0, "HR_delta_3h": 0.0, "Lactate_delta_3h": 0.0, "Resp": 16.0, "O2Sat": 98.0}


def worse_row() -> dict:
    """An hour where MAP fell 14 mmHg in 3 hours (one worsening sign)."""
    row = calm_row()
    row["MAP_delta_3h"] = -14.0
    return row


# --- Gate 1: risk -----------------------------------------------------------
def test_gate1_low_risk_is_no_alert_even_if_worsening():
    assert decide(LOW_RISK, worse_row(), None, 10, THRESHOLD) == NO_ALERT


def test_gate1_risk_exactly_at_threshold_passes():
    assert decide(THRESHOLD, worse_row(), None, 10, THRESHOLD) == REVIEW


# --- Gate 2: worsening ------------------------------------------------------
def test_gate2_high_risk_but_stable_is_watch():
    assert decide(HIGH_RISK, calm_row(), None, 10, THRESHOLD) == WATCH


def test_gate2_each_sign_alone_counts():
    changes = {"MAP_delta_3h": -10.0, "HR_delta_3h": 15.0, "Lactate_delta_3h": 0.5, "Resp": 24.0, "O2Sat": 92.0}
    for column, value in changes.items():
        row = calm_row()
        row[column] = value  # exactly on the limit must count
        assert is_worsening(row), f"{column} = {value} should count as worsening"


def test_gate2_just_inside_the_limits_does_not_count():
    changes = {"MAP_delta_3h": -9.9, "HR_delta_3h": 14.9, "Lactate_delta_3h": 0.4, "Resp": 23.9, "O2Sat": 92.1}
    for column, value in changes.items():
        row = calm_row()
        row[column] = value
        assert not is_worsening(row), f"{column} = {value} should NOT count as worsening"


def test_gate2_all_missing_is_not_worsening():
    row = {column: np.nan for column in calm_row()}
    assert not is_worsening(row)
    assert decide(HIGH_RISK, row, None, 10, THRESHOLD) == WATCH


def test_gate2_one_sign_present_others_missing_still_counts():
    row = {column: np.nan for column in calm_row()}
    row["O2Sat"] = 90.0
    assert is_worsening(row)


def test_gate2_works_with_a_pandas_row():
    assert is_worsening(pd.Series(worse_row()))


# --- Gate 3: new (6-hour cooldown) ------------------------------------------
def test_gate3_no_previous_alert_gives_review():
    assert decide(HIGH_RISK, worse_row(), None, 10, THRESHOLD) == REVIEW


def test_gate3_alert_5_hours_ago_is_suppressed():
    assert decide(HIGH_RISK, worse_row(), 10, 15, THRESHOLD) == SUPPRESSED


def test_gate3_alert_exactly_6_hours_ago_is_allowed():
    assert decide(HIGH_RISK, worse_row(), 10, 16, THRESHOLD) == REVIEW


def test_gate3_is_checked_after_gate2():
    # Stable patient inside the cooldown: Gate 2 fails first, so WATCH (not SUPPRESSED).
    assert decide(HIGH_RISK, calm_row(), 10, 12, THRESHOLD) == WATCH


# --- Switching gates off (used for the P0-P3 comparison) --------------------
def test_without_gate2_stable_high_risk_is_review():
    assert decide(HIGH_RISK, calm_row(), None, 10, THRESHOLD, use_gate2=False) == REVIEW


def test_without_gate3_repeat_alert_is_review():
    assert decide(HIGH_RISK, worse_row(), 10, 11, THRESHOLD, use_gate3=False) == REVIEW


# --- run_policy: a whole patient --------------------------------------------
def make_patient(n_hours: int) -> pd.DataFrame:
    """A patient whose MAP is falling every hour (always worsening), ICU hours 1..n."""
    rows = [worse_row() for _ in range(n_hours)]
    table = pd.DataFrame(rows)
    table["ICULOS"] = range(1, n_hours + 1)
    return table


def test_run_policy_cooldown_over_a_stay():
    patient = make_patient(8)
    statuses = run_policy(patient, [HIGH_RISK] * 8, THRESHOLD)
    assert statuses == [REVIEW, SUPPRESSED, SUPPRESSED, SUPPRESSED, SUPPRESSED, SUPPRESSED, REVIEW, SUPPRESSED]


def test_run_policy_suppressed_does_not_restart_cooldown():
    patient = make_patient(8)
    risks = [HIGH_RISK, LOW_RISK, HIGH_RISK, LOW_RISK, HIGH_RISK, LOW_RISK, HIGH_RISK, HIGH_RISK]
    statuses = run_policy(patient, risks, THRESHOLD)
    # hour 1 REVIEW; hours 3 and 5 SUPPRESSED; hour 7 is 6 h after hour 1 -> REVIEW again
    assert statuses == [REVIEW, NO_ALERT, SUPPRESSED, NO_ALERT, SUPPRESSED, NO_ALERT, REVIEW, SUPPRESSED]


def test_run_policy_naive_alerts_every_high_hour():
    patient = make_patient(5)
    statuses = run_policy(patient, [HIGH_RISK] * 5, THRESHOLD, use_gate2=False, use_gate3=False)
    assert statuses == [REVIEW] * 5


def test_run_policy_returns_one_status_per_hour():
    patient = make_patient(12)
    assert len(run_policy(patient, [LOW_RISK] * 12, THRESHOLD)) == 12
