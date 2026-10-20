"""Tests for the patient split and the threshold rule in src/train.py."""

import numpy as np
import pandas as pd

from src import config
from src.train import alert_stats, choose_threshold, split_patients


def make_summary(n_patients: int, n_sepsis: int) -> pd.DataFrame:
    """Make a fake patient summary: the first n_sepsis patients have sepsis at hour 20."""
    ids = [f"p{i:04d}" for i in range(n_patients)]
    has_sepsis = [1 if i < n_sepsis else 0 for i in range(n_patients)]
    onset = [20.0 if flag else np.nan for flag in has_sepsis]
    return pd.DataFrame({"patient_id": ids, "hospital": "A", "n_hours": 24,
                         "has_sepsis": has_sepsis, "onset_hour": onset})


def test_split_has_no_patient_on_both_sides():
    """No patient may appear in both train and validation; together they cover everyone."""
    summary = make_summary(n_patients=200, n_sepsis=20)
    train_ids, val_ids = split_patients(summary)
    assert set(train_ids).isdisjoint(val_ids)
    assert set(train_ids) | set(val_ids) == set(summary["patient_id"])
    assert len(train_ids) == round(config.TRAIN_FRACTION * 200)


def test_split_keeps_sepsis_share():
    """Stratified split: validation gets about 20% of the sepsis patients."""
    summary = make_summary(n_patients=200, n_sepsis=20)
    _, val_ids = split_patients(summary)
    assert summary[summary["patient_id"].isin(val_ids)]["has_sepsis"].sum() == 4


def test_alert_outside_window_does_not_count():
    """An alert 20 hours before onset is too early; one 1 hour before onset counts."""
    summary = make_summary(n_patients=2, n_sepsis=1)  # p0000 sepsis (onset 20), p0001 not
    early = pd.DataFrame({"patient_id": ["p0000"], "ICULOS": [0], "risk": [0.9]})
    on_time = pd.DataFrame({"patient_id": ["p0000"], "ICULOS": [19], "risk": [0.9]})
    assert alert_stats(early, summary, 0.5)["patient_sensitivity"] == 0.0
    assert alert_stats(on_time, summary, 0.5)["patient_sensitivity"] == 1.0


def test_choose_threshold_picks_highest_that_meets_sensitivity():
    """Sepsis patients' risk is 0.05 at onset; the rule must pick 0.05, not anything higher."""
    summary = make_summary(n_patients=10, n_sepsis=5)
    hours = pd.DataFrame({"patient_id": summary["patient_id"], "ICULOS": 19,
                          "risk": [0.05] * 5 + [0.02] * 5})
    chosen, _ = choose_threshold(hours, summary)
    assert chosen["threshold"] == 0.05
    assert chosen["patient_sensitivity"] == 1.0
    assert chosen["non_sepsis_patients_alerted"] == 0.0
