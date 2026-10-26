"""Tests for the why-now reasons and data-quality notes (src/explain.py)."""

import numpy as np

from src.explain import data_quality, data_quality_items, reason_items, why_now


def calm_row() -> dict:
    """Normal values: nothing worth mentioning."""
    return {"MAP_delta_3h": 0.0, "HR_delta_3h": 0.0, "Lactate_delta_3h": 0.0, "Resp": 16.0, "O2Sat": 97.0,
            "Lactate": 1.2, "hours_since_Lactate": 1.0}


def test_calm_patient_has_no_reasons():
    assert why_now(calm_row()) == []


def test_reasons_ordered_by_size_and_capped_at_three():
    row = calm_row()
    row.update({"MAP_delta_3h": -14.0,     # 1.4 x limit
                "HR_delta_3h": 18.0,       # 1.2 x limit
                "Lactate_delta_3h": 0.8,   # 1.6 x limit
                "Resp": 26.0,              # 1.08 x limit -> 4th, cut off
                "O2Sat": 97.0})
    assert why_now(row) == ["lactate_rose", "map_fell", "hr_rose"]


def test_normal_levels_are_not_reasons():
    row = calm_row()
    row.update({"Resp": 23.0, "O2Sat": 93.0})  # just inside the Gate-2 limits
    assert why_now(row) == []


def test_improving_values_are_not_reasons():
    row = calm_row()
    row.update({"MAP_delta_3h": 20.0, "HR_delta_3h": -20.0, "Lactate_delta_3h": -1.0})
    assert why_now(row) == []


def test_missing_values_are_not_reasons():
    row = {key: np.nan for key in calm_row()}
    assert why_now(row) == []


def test_reason_values_are_rounded_for_display():
    row = calm_row()
    row["MAP_delta_3h"] = -14.3
    assert reason_items(row) == [("map_fell", {"value": "14"})]


def test_data_quality_notes():
    never = calm_row()
    never.update({"Lactate": np.nan, "hours_since_Lactate": 48.0, "MAP_delta_3h": np.nan, "HR_delta_3h": np.nan})
    assert data_quality(never) == ["lactate_never", "trends_not_ready"]

    stale = calm_row()
    stale["hours_since_Lactate"] = 7.0
    assert data_quality_items(stale) == [("lactate_stale", {"hours": "7"})]

    assert data_quality(calm_row()) == []
