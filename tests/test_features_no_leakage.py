"""Leakage tests: the features at hour t must not depend on the future or on other patients."""

import numpy as np
import pandas as pd

from src import config
from src.features import FEATURE_COLUMNS, build_features, news2_lite_row


def make_patient(patient_id: str, n_hours: int, seed: int) -> pd.DataFrame:
    """Make a small fake patient with random vitals and some missing labs."""
    rng = np.random.default_rng(seed)
    table = pd.DataFrame({"ICULOS": np.arange(1, n_hours + 1)})
    for column in config.VITALS + config.LABS:
        values = rng.normal(80, 10, n_hours)
        values[rng.random(n_hours) < 0.4] = np.nan  # 40% missing
        table[column] = values
    table["Age"] = 60.0
    table["Gender"] = 1
    table["HospAdmTime"] = -5.0
    table[config.LABEL] = 0
    table["patient_id"] = patient_id
    table["hospital"] = "A"
    return table


def features_at(raw: pd.DataFrame, patient_id: str, hour: int) -> pd.Series:
    """Return the feature values for one patient at one ICU hour."""
    features, _ = build_features(raw)
    row = features[(features["patient_id"] == patient_id) & (features["ICULOS"] == hour)]
    return row[FEATURE_COLUMNS].iloc[0]


def test_changing_the_future_does_not_change_hour_t():
    """Scramble every hour after t; the features at hours <= t must stay identical."""
    raw = make_patient("p1", n_hours=20, seed=1)
    changed = raw.copy()
    future = changed["ICULOS"] > 10
    for column in config.VITALS + config.LABS:
        changed.loc[future, column] = 999.0
    for hour in range(1, 11):
        before = features_at(raw, "p1", hour)
        after = features_at(changed, "p1", hour)
        pd.testing.assert_series_equal(before, after, check_names=False)


def test_deleting_the_future_does_not_change_hour_t():
    """Cutting the stay short after hour t must not change the features at hour t."""
    raw = make_patient("p1", n_hours=20, seed=2)
    short = raw[raw["ICULOS"] <= 10]
    pd.testing.assert_series_equal(features_at(raw, "p1", 10), features_at(short, "p1", 10),
                                   check_names=False)


def test_no_filling_across_patients():
    """Patient 2's first hour must not receive values from patient 1."""
    first = make_patient("p1", n_hours=5, seed=3)
    second = make_patient("p2", n_hours=5, seed=4)
    second.loc[0, config.VITALS + config.LABS] = np.nan  # nothing measured in hour 1
    features, _ = build_features(pd.concat([first, second], ignore_index=True))
    hour_one = features[(features["patient_id"] == "p2") & (features["ICULOS"] == 1)].iloc[0]
    for column in config.VITALS + config.LABS:
        assert pd.isna(hour_one[column])
    for lab in config.LABS:
        assert hour_one[f"hours_since_{lab}"] == config.HOURS_SINCE_CAP


def test_missing_flag_and_hours_since():
    """A lab measured at hour 1 then missing: flag = 1 and hours_since counts up."""
    raw = make_patient("p1", n_hours=4, seed=5)
    raw["Lactate"] = [2.0, np.nan, np.nan, 3.0]
    features, _ = build_features(raw)
    assert list(features["Lactate_missing"]) == [0, 1, 1, 0]
    assert list(features["hours_since_Lactate"]) == [0, 1, 2, 0]
    assert list(features["Lactate"]) == [2.0, 2.0, 2.0, 3.0]  # forward-filled


def test_news2_lite_examples():
    """Normal vitals score 0; very abnormal vitals score high; missing gives 0 points."""
    assert news2_lite_row(resp=16, o2sat=98, sbp=120, hr=75, temp=37.0) == 0
    assert news2_lite_row(resp=26, o2sat=90, sbp=88, hr=135, temp=39.5) == 3 + 3 + 3 + 3 + 2
    assert news2_lite_row(resp=np.nan, o2sat=np.nan, sbp=np.nan, hr=np.nan, temp=np.nan) == 0
