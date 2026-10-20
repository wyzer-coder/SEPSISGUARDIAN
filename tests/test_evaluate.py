"""Tests for the alert metrics in src/evaluate.py, on tiny examples worked out by hand."""

import numpy as np
import pandas as pd

from src.evaluate import alert_metrics, f1


def make_case():
    """Two patients, 24 hours each.

    p1 has sepsis with onset at hour 20, so the true-alert window is hours 8..22.
    p2 has no sepsis.
    """
    hours = pd.DataFrame({
        "patient_id": ["p1"] * 24 + ["p2"] * 24,
        "ICULOS": list(range(1, 25)) * 2,
    })
    summary = pd.DataFrame({
        "patient_id": ["p1", "p2"],
        "has_sepsis": [1, 0],
        "onset_hour": [20.0, np.nan],
        "n_hours": [24, 24],
    })
    return hours, summary


def flags_at(hours: pd.DataFrame, alerts: list) -> pd.Series:
    """Alert flags that are True at the given (patient_id, hour) pairs."""
    pairs = set(alerts)
    return pd.Series([(p, h) in pairs for p, h in zip(hours["patient_id"], hours["ICULOS"])], index=hours.index)


def test_true_false_ppv_and_lead_time():
    hours, summary = make_case()
    # p1 hour 5: too early (false). p1 hour 10: true, 10 h before onset. p1 hour 22: true (after onset).
    # p2 hour 3: false (no sepsis).
    flags = flags_at(hours, [("p1", 5), ("p1", 10), ("p1", 22), ("p2", 3)])
    metrics = alert_metrics(hours, flags, summary)
    assert metrics["alerts"] == 4
    assert metrics["true_alerts"] == 2
    assert metrics["alert_ppv"] == 0.5
    assert metrics["patient_sensitivity"] == 1.0
    assert metrics["median_lead_time_hours"] == 10.0
    assert metrics["non_sepsis_patients_alerted"] == 1.0
    # 4 alerts / 48 patient-hours x 2400 = 200 per 100 patient-days
    assert metrics["alerts_per_100_patient_days"] == 200.0


def test_alert_only_after_onset_is_true_but_not_caught():
    hours, summary = make_case()
    flags = flags_at(hours, [("p1", 21)])  # inside the window, but after onset
    metrics = alert_metrics(hours, flags, summary)
    assert metrics["true_alerts"] == 1
    assert metrics["patient_sensitivity"] == 0.0


def test_window_edges():
    hours, summary = make_case()
    edges = alert_metrics(hours, flags_at(hours, [("p1", 8), ("p1", 22)]), summary)
    outside = alert_metrics(hours, flags_at(hours, [("p1", 7), ("p1", 23)]), summary)
    assert edges["true_alerts"] == 2   # onset - 12 and onset + 2 count
    assert outside["true_alerts"] == 0  # one hour outside each edge does not


def test_no_alerts_at_all():
    hours, summary = make_case()
    metrics = alert_metrics(hours, flags_at(hours, []), summary)
    assert metrics["alerts"] == 0
    assert metrics["alert_ppv"] == 0.0
    assert metrics["patient_sensitivity"] == 0.0


def test_f1():
    assert f1(0.0, 0.0) == 0.0
    assert f1(0.5, 0.5) == 0.5
