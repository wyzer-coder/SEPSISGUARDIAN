"""Train on hospital A, calibrate, choose the alert threshold, save the model.

Hospital B is NOT loaded here. It is used only once, in Phase 4 (src/evaluate.py).

The official threshold is chosen with the full three-gate policy (src/gates.py),
so gates.py must be written before this script can finish.

Run it:
    .venv/bin/python -m src.train
"""

import json
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src import config
from src.evaluate import GATE_COLUMNS, choose_gated_threshold
from src.features import build_features
from src.load_data import load_set, patient_summary


# ---------------------------------------------------------------------------
# Step 1: split hospital A by patient
# ---------------------------------------------------------------------------
def split_patients(summary: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Split patient ids into train (80%) and validation (20%).

    The split is by PATIENT, so all hours of one patient land on the same side.
    It is stratified, so both sides get about the same share of sepsis patients.
    """
    train_ids, val_ids = train_test_split(
        summary["patient_id"],
        train_size=config.TRAIN_FRACTION,
        stratify=summary["has_sepsis"],
        random_state=config.SEED,
    )
    return sorted(train_ids), sorted(val_ids)


# ---------------------------------------------------------------------------
# Step 2: the two models
# ---------------------------------------------------------------------------
def make_baseline():
    """Simple baseline: fill gaps with the median, scale, then logistic regression."""
    return make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=1000, random_state=config.SEED),
    )


def make_main_model() -> HistGradientBoostingClassifier:
    """Main model: gradient-boosted trees. They handle empty values on their own."""
    return HistGradientBoostingClassifier(
        max_iter=config.HGB_MAX_ITER,
        learning_rate=config.HGB_LEARNING_RATE,
        max_leaf_nodes=config.HGB_MAX_LEAF_NODES,
        l2_regularization=config.HGB_L2_REGULARIZATION,
        early_stopping=False,
        random_state=config.SEED,
    )


def calibrate(model, features: pd.DataFrame, labels: pd.Series, patients: pd.Series) -> CalibratedClassifierCV:
    """Fit the model and an isotonic calibrator on the TRAIN patients only.

    The train patients are cut into folds by patient. Each fold's model is
    calibrated on patients it did not see. Validation stays untouched,
    so we can still use it fairly to pick the threshold.
    """
    folds = list(GroupKFold(n_splits=config.CALIBRATION_FOLDS).split(features, labels, groups=patients))
    calibrated = CalibratedClassifierCV(model, method="isotonic", cv=folds)
    calibrated.fit(features, labels)
    return calibrated


# ---------------------------------------------------------------------------
# Step 3: patient-level alert numbers for one threshold
# ---------------------------------------------------------------------------
def alert_stats(hours: pd.DataFrame, summary: pd.DataFrame, threshold: float) -> Dict[str, float]:
    """Count alerts when every hour with risk >= threshold is an alert (no gates yet).

    hours needs columns: patient_id, ICULOS, risk.
    A sepsis patient counts as "caught" if an alert fires in the window
    [onset - 12 h, onset + 2 h].
    """
    alerts = hours[hours["risk"] >= threshold].merge(summary[["patient_id", "onset_hour"]], on="patient_id")
    in_window = (
        (alerts["ICULOS"] >= alerts["onset_hour"] - config.ALERT_WINDOW_BEFORE_HOURS)
        & (alerts["ICULOS"] <= alerts["onset_hour"] + config.ALERT_WINDOW_AFTER_HOURS)
    )
    sepsis_ids = set(summary.loc[summary["has_sepsis"] == 1, "patient_id"])
    no_sepsis_ids = set(summary.loc[summary["has_sepsis"] == 0, "patient_id"])
    caught_ids = set(alerts.loc[in_window, "patient_id"])
    alerted_ids = set(alerts["patient_id"])
    patient_days = summary["n_hours"].sum() / 24
    return {
        "threshold": round(threshold, 3),
        "patient_sensitivity": len(caught_ids & sepsis_ids) / len(sepsis_ids),
        "non_sepsis_patients_alerted": len(alerted_ids & no_sepsis_ids) / len(no_sepsis_ids),
        "alert_hours_per_100_patient_days": 100 * len(alerts) / patient_days,
    }


def threshold_grid() -> np.ndarray:
    """Return the thresholds to try: 0.010, 0.011, ..., 0.200."""
    n_steps = round((config.THRESHOLD_GRID_STOP - config.THRESHOLD_GRID_START) / config.THRESHOLD_GRID_STEP)
    return np.round(config.THRESHOLD_GRID_START + config.THRESHOLD_GRID_STEP * np.arange(n_steps + 1), 3)


def gated_threshold_grid() -> np.ndarray:
    """Return the thresholds to try with the three gates: 0.010, 0.012, ..., 0.200."""
    n_steps = round((config.THRESHOLD_GRID_STOP - config.THRESHOLD_GRID_START) / config.GATED_THRESHOLD_GRID_STEP)
    return np.round(config.THRESHOLD_GRID_START + config.GATED_THRESHOLD_GRID_STEP * np.arange(n_steps + 1), 3)


def choose_threshold(hours: pd.DataFrame, summary: pd.DataFrame) -> Tuple[Dict[str, float], pd.DataFrame]:
    """Pick the HIGHEST threshold that still catches at least 60% of sepsis patients.

    Higher threshold = fewer alerts. So this is the quietest setting that still
    meets our minimum sensitivity. Returns (chosen row, full grid table).
    """
    table = pd.DataFrame([alert_stats(hours, summary, t) for t in threshold_grid()])
    good_enough = table[table["patient_sensitivity"] >= config.MIN_PATIENT_SENSITIVITY]
    if good_enough.empty:
        raise ValueError("No threshold reaches the minimum patient sensitivity on validation.")
    chosen = good_enough.iloc[-1].to_dict()
    return chosen, table


# ---------------------------------------------------------------------------
# Step 4: hour-level scores
# ---------------------------------------------------------------------------
def score(labels: pd.Series, risk: np.ndarray) -> Dict[str, float]:
    """AUROC, AUPRC and Brier score for hour-level predictions."""
    return {
        "auroc": roc_auc_score(labels, risk),
        "auprc": average_precision_score(labels, risk),
        "brier": brier_score_loss(labels, risk),
        "positive_rate": float(labels.mean()),
    }


def calibration_table(labels: pd.Series, risk: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    """Group hours into 10 equal-size risk groups; compare predicted vs real sepsis rate."""
    table = pd.DataFrame({"label": labels.to_numpy(), "risk": risk})
    table["group"] = pd.qcut(table["risk"].rank(method="first"), n_bins, labels=False)
    grouped = table.groupby("group").agg(mean_predicted=("risk", "mean"), actual_rate=("label", "mean"),
                                         hours=("label", "size"))
    return grouped.reset_index(drop=True)


# ---------------------------------------------------------------------------
# All steps together
# ---------------------------------------------------------------------------
def save_json(data: dict, path) -> None:
    """Write a dictionary to a JSON file with 4 decimal places for floats."""
    def tidy(value):
        if isinstance(value, dict):
            return {key: tidy(inner) for key, inner in value.items()}
        if isinstance(value, float):
            return None if np.isnan(value) else round(value, 4)
        return value
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tidy(data), indent=2))


def main() -> None:
    """Train both models on hospital A, report validation numbers, save outputs."""
    raw = load_set(config.HOSPITAL_FOLDERS["A"], "A")
    summary = patient_summary(raw)
    features, columns = build_features(raw)

    train_ids, val_ids = split_patients(summary)
    train = features[features["patient_id"].isin(train_ids)]
    val = features[features["patient_id"].isin(val_ids)]
    val_summary = summary[summary["patient_id"].isin(val_ids)]
    print(f"Train: {len(train_ids)} patients, {len(train)} hours | "
          f"Validation: {len(val_ids)} patients, {len(val)} hours")
    print(f"Sepsis patients: train {summary[summary['patient_id'].isin(train_ids)]['has_sepsis'].sum()}, "
          f"validation {val_summary['has_sepsis'].sum()}")

    scores = {}
    models = {"baseline_logistic": make_baseline(), "main_hgb": make_main_model()}
    for name, model in models.items():
        calibrated = calibrate(model, train[columns], train[config.LABEL], train["patient_id"])
        risk = calibrated.predict_proba(val[columns])[:, 1]
        scores[name] = score(val[config.LABEL], risk)
        models[name] = calibrated
        print(f"{name}: AUROC {scores[name]['auroc']:.3f}  AUPRC {scores[name]['auprc']:.3f}  "
              f"Brier {scores[name]['brier']:.4f}")
        if name == "main_hgb":
            main_risk = risk

    print(f"Hour-level sepsis rate in validation: {scores['main_hgb']['positive_rate']:.4f}")
    print("\nCalibration of the main model on validation (10 equal-size groups):")
    print(calibration_table(val[config.LABEL], main_risk).round(4).to_string())

    hours = val[["patient_id", "ICULOS"]].assign(risk=main_risk)
    risk_only, grid = choose_threshold(hours, val_summary)
    print("\nReference: risk-only threshold grid (every 10th row, no gates):")
    print(grid.iloc[::10].round(3).to_string(index=False))
    print(f"Risk-only choice (for reference): {risk_only['threshold']:.3f}")

    print("\nChoosing the official threshold WITH the three gates (validation only)...")
    gated_hours = val[["patient_id"] + GATE_COLUMNS].assign(risk=main_risk)
    chosen, gated_grid = choose_gated_threshold(gated_hours, val_summary, gated_threshold_grid())
    print(gated_grid.iloc[::5][["threshold", "alerts", "alert_ppv", "patient_sensitivity",
                                "alerts_per_100_patient_days"]].round(3).to_string(index=False))
    print(f"\nChosen threshold: {chosen['threshold']:.3f} -> alert PPV {chosen['alert_ppv']:.3f}, "
          f"patient sensitivity {chosen['patient_sensitivity']:.3f}, "
          f"alerts per 100 patient-days {chosen['alerts_per_100_patient_days']:.1f}")
    print(f"Rule: {chosen['rule']}")

    config.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": models["main_hgb"], "features": columns, "threshold": float(chosen["threshold"])},
                config.MODEL_PATH)
    joblib.dump(models["baseline_logistic"], config.BASELINE_MODEL_PATH)
    save_json({**chosen, "data": "hospital A validation patients",
               "risk_only_reference": risk_only}, config.THRESHOLD_PATH)
    save_json({"split": {"train_patients": len(train_ids), "validation_patients": len(val_ids)}, **scores},
              config.VALIDATION_METRICS_PATH)
    grid.to_csv(config.RESULTS_DIR / "threshold_grid.csv", index=False)
    gated_grid.to_csv(config.GATED_THRESHOLD_GRID_PATH, index=False)
    print(f"\nSaved {config.MODEL_PATH.name}, {config.BASELINE_MODEL_PATH.name}, "
          f"{config.THRESHOLD_PATH.name}, {config.VALIDATION_METRICS_PATH.name}")


if __name__ == "__main__":
    main()
