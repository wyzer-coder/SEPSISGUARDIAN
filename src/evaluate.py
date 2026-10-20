"""Evaluate on hospital B only: model scores and the P0-P3 gate comparison.

Hospital B was never used for training, calibration or choosing the threshold.

Run it (after src/train.py):
    .venv/bin/python -m src.evaluate
"""

import json
import shutil
from typing import Dict, Tuple

import joblib
import matplotlib
import numpy as np
import pandas as pd

from src import config
from src.features import build_features
from src.gates import REVIEW, NO_ALERT, run_policy
from src.load_data import load_set, patient_summary

matplotlib.use("Agg")  # draw charts to files, no window
import matplotlib.pyplot as plt  # noqa: E402

# The columns run_policy needs for every hour (Gate 2 inputs + the hour itself).
GATE_COLUMNS = ["ICULOS", "MAP_delta_3h", "HR_delta_3h", "Lactate_delta_3h", "Resp", "O2Sat"]

# The four policies we compare, all at the same threshold.
POLICIES = {
    "P0 naive (risk only)": {"use_gate2": False, "use_gate3": False},
    "P1 risk + cooldown": {"use_gate2": False, "use_gate3": True},
    "P2 risk + worsening": {"use_gate2": True, "use_gate3": False},
    "P3 SepsisGuardian (3 gates)": {"use_gate2": True, "use_gate3": True},
}


# ---------------------------------------------------------------------------
# Run a policy over many patients
# ---------------------------------------------------------------------------
def policy_statuses(hours: pd.DataFrame, threshold: float, use_gate2: bool = True,
                    use_gate3: bool = True) -> pd.Series:
    """Return one status per row of `hours`, using the student's run_policy patient by patient.

    hours needs: patient_id, risk and GATE_COLUMNS, sorted by patient_id and ICULOS.
    Speed-up: if a patient's risk never reaches the threshold, Gate 1 fails every hour,
    so every status is NO_ALERT and we do not need to call run_policy.
    """
    statuses = pd.Series(NO_ALERT, index=hours.index, dtype=object)
    for _, patient in hours.groupby("patient_id", sort=False):
        if patient["risk"].max() < threshold:
            continue
        result = run_policy(patient[GATE_COLUMNS], patient["risk"].tolist(), threshold,
                            use_gate2=use_gate2, use_gate3=use_gate3)
        statuses.loc[patient.index] = result
    return statuses


# ---------------------------------------------------------------------------
# Alert metrics (definitions in docs/DATA_AND_MODEL.md)
# ---------------------------------------------------------------------------
def alert_metrics(hours: pd.DataFrame, alert_flags: pd.Series, summary: pd.DataFrame) -> Dict[str, float]:
    """Measure a set of alerts.

    hours       : patient_id and ICULOS for every patient-hour
    alert_flags : True where an alert (a nurse page) fired, same index as hours
    summary     : one row per patient with has_sepsis, onset_hour, n_hours

    TRUE alert   = sepsis patient, alert hour in [onset - 12 h, onset + 2 h].
    PPV          = true alerts / all alerts.
    Sensitivity  = sepsis patients with >= 1 true alert AT OR BEFORE onset / all sepsis patients.
    Lead time    = onset - first true alert (hours), median over caught patients.
    Alert rate   = alerts / total patient-hours x 2,400  (= per 100 patient-days).
    """
    alerts = hours.loc[alert_flags, ["patient_id", "ICULOS"]].merge(
        summary[["patient_id", "has_sepsis", "onset_hour"]], on="patient_id")
    in_window = (
        (alerts["has_sepsis"] == 1)
        & (alerts["ICULOS"] >= alerts["onset_hour"] - config.ALERT_WINDOW_BEFORE_HOURS)
        & (alerts["ICULOS"] <= alerts["onset_hour"] + config.ALERT_WINDOW_AFTER_HOURS)
    )
    early_true = alerts[in_window & (alerts["ICULOS"] <= alerts["onset_hour"])]
    first_early = early_true.groupby("patient_id").agg(first_hour=("ICULOS", "min"), onset=("onset_hour", "first"))

    n_alerts = len(alerts)
    n_sepsis = int(summary["has_sepsis"].sum())
    non_sepsis_ids = set(summary.loc[summary["has_sepsis"] == 0, "patient_id"])
    alerted_non_sepsis = set(alerts["patient_id"]) & non_sepsis_ids
    total_hours = summary["n_hours"].sum()

    return {
        "alerts": n_alerts,
        "true_alerts": int(in_window.sum()),
        "alert_ppv": in_window.sum() / n_alerts if n_alerts else 0.0,
        "patients_caught": len(first_early),
        "sepsis_patients": n_sepsis,
        "patient_sensitivity": len(first_early) / n_sepsis if n_sepsis else 0.0,
        "median_lead_time_hours": float((first_early["onset"] - first_early["first_hour"]).median())
        if len(first_early) else float("nan"),
        "alerts_per_100_patient_days": n_alerts / total_hours * 2400,
        "non_sepsis_patients_alerted": len(alerted_non_sepsis) / len(non_sepsis_ids) if non_sepsis_ids else 0.0,
    }


def f1(ppv: float, sensitivity: float) -> float:
    """Balance of alert PPV and patient sensitivity (0 if both are 0)."""
    if ppv + sensitivity == 0:
        return 0.0
    return 2 * ppv * sensitivity / (ppv + sensitivity)


def choose_gated_threshold(hours: pd.DataFrame, summary: pd.DataFrame,
                           grid: np.ndarray) -> Tuple[Dict[str, float], pd.DataFrame]:
    """Pick the threshold for the full three-gate policy (used on VALIDATION only).

    Rule: among thresholds with patient sensitivity >= 60%, the one with the highest alert PPV
    (ties -> the higher threshold, fewer alerts). If none reaches 60%, the best F1 of PPV and sensitivity.
    """
    rows = []
    for threshold in grid:
        statuses = policy_statuses(hours, float(threshold))
        metrics = alert_metrics(hours, statuses == REVIEW, summary)
        rows.append({"threshold": float(threshold), **metrics,
                     "f1": f1(metrics["alert_ppv"], metrics["patient_sensitivity"])})
    table = pd.DataFrame(rows)
    good_enough = table[table["patient_sensitivity"] >= config.MIN_PATIENT_SENSITIVITY]
    if not good_enough.empty:
        best = good_enough.sort_values(["alert_ppv", "threshold"]).iloc[-1]
        rule = (f"highest alert PPV with validation patient sensitivity >= {config.MIN_PATIENT_SENSITIVITY} "
                "(three-gate policy)")
    else:
        best = table.sort_values(["f1", "threshold"]).iloc[-1]
        rule = (f"no threshold reached sensitivity {config.MIN_PATIENT_SENSITIVITY}; "
                "best F1 of alert PPV and patient sensitivity (three-gate policy)")
    chosen = best.to_dict()
    chosen["rule"] = rule
    return chosen, table


# ---------------------------------------------------------------------------
# Hospital B evaluation
# ---------------------------------------------------------------------------
def hour_scores(labels: pd.Series, risk: np.ndarray) -> Dict[str, float]:
    """AUROC, AUPRC and Brier score (same as in train.py)."""
    from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
    return {
        "auroc": roc_auc_score(labels, risk),
        "auprc": average_precision_score(labels, risk),
        "brier": brier_score_loss(labels, risk),
        "positive_rate": float(labels.mean()),
    }


def compare_policies(hours: pd.DataFrame, summary: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Run P0-P3 and the NEWS2-lite >= 5 rule. Return one row of metrics per policy."""
    rows = []
    for name, switches in POLICIES.items():
        statuses = policy_statuses(hours, threshold, **switches)
        hours[name] = statuses
        rows.append({"policy": name, **alert_metrics(hours, statuses == REVIEW, summary)})
    news2_flags = hours["news2_lite"] >= config.NEWS2_LITE_ALERT_SCORE
    rows.append({"policy": f"NEWS2-lite >= {config.NEWS2_LITE_ALERT_SCORE} (rule only)",
                 **alert_metrics(hours, news2_flags, summary)})
    return pd.DataFrame(rows)


def draw_comparison_chart(table: pd.DataFrame, path) -> None:
    """Bar chart: alerts per 100 patient-days and alert PPV for each policy."""
    labels = [name.split(" (")[0] for name in table["policy"]]
    figure, (left, right) = plt.subplots(1, 2, figsize=(12, 4.5))
    left.bar(labels, table["alerts_per_100_patient_days"], color="#8A8F98")
    left.set_title("Alerts per 100 patient-days (lower = quieter)")
    right.bar(labels, 100 * table["alert_ppv"], color="#D64545")
    right.set_title("Alert PPV, % of alerts that were true (higher = better)")
    for axis in (left, right):
        axis.tick_params(axis="x", rotation=25)
        for label in axis.get_xticklabels():
            label.set_ha("right")
    figure.suptitle("Hospital B (unseen): same threshold, different alert policies")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def save_json(data: dict, path) -> None:
    """Write a dictionary to JSON, rounding floats to 4 decimal places."""
    def tidy(value):
        if isinstance(value, dict):
            return {key: tidy(inner) for key, inner in value.items()}
        if isinstance(value, list):
            return [tidy(inner) for inner in value]
        if isinstance(value, (float, np.floating)):
            return None if np.isnan(value) else round(float(value), 4)
        if isinstance(value, np.integer):
            return int(value)
        return value
    path.write_text(json.dumps(tidy(data), indent=2, ensure_ascii=False))


def main() -> None:
    """Score both models on hospital B, compare the alert policies, save everything."""
    raw = load_set(config.HOSPITAL_FOLDERS["B"], "B")
    summary = patient_summary(raw)
    features, _ = build_features(raw)
    print(f"Hospital B: {len(summary)} patients, {int(summary['has_sepsis'].sum())} with sepsis, "
          f"{len(features)} patient-hours")

    saved = joblib.load(config.MODEL_PATH)
    columns = saved["features"]
    threshold = saved["threshold"]
    baseline = joblib.load(config.BASELINE_MODEL_PATH)
    main_risk = saved["model"].predict_proba(features[columns])[:, 1]
    baseline_risk = baseline.predict_proba(features[columns])[:, 1]

    model_scores = {
        "baseline_logistic": hour_scores(features[config.LABEL], baseline_risk),
        "main_hgb": hour_scores(features[config.LABEL], main_risk),
    }
    for name, scores in model_scores.items():
        print(f"{name}: AUROC {scores['auroc']:.3f}  AUPRC {scores['auprc']:.3f}  Brier {scores['brier']:.4f}")

    hours = features[["patient_id"] + GATE_COLUMNS + ["news2_lite", config.LABEL]].copy()
    hours["risk"] = main_risk
    table = compare_policies(hours, summary, threshold)
    print(f"\nPolicy comparison at threshold {threshold:.3f}:")
    print(table.round(3).to_string(index=False))

    naive = table.iloc[0]
    gated = table.iloc[3]
    headline = (f"Three gates cut alerts from {naive['alerts_per_100_patient_days']:.1f} to "
                f"{gated['alerts_per_100_patient_days']:.1f} per 100 patient-days while catching "
                f"{100 * gated['patient_sensitivity']:.1f}% of sepsis patients")
    print("\n" + headline)

    config.RESULTS_DIR.mkdir(exist_ok=True)
    table.to_csv(config.GATE_COMPARISON_PATH, index=False)
    draw_comparison_chart(table, config.RESULTS_DIR / "gate_comparison.png")
    metrics = {
        "data": "hospital B (never used for training or threshold choice)",
        "patients": len(summary),
        "sepsis_patients": int(summary["has_sepsis"].sum()),
        "patient_hours": len(features),
        "threshold": threshold,
        "models": model_scores,
        "policies": table.to_dict(orient="records"),
        "headline": headline,
    }
    save_json(metrics, config.METRICS_PATH)

    # Per-hour results for building the demo (raw-data-derived, so they stay in data/, not Git).
    hours.to_csv(config.TEST_HOURS_PATH, index=False)

    config.DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(config.METRICS_PATH, config.DEMO_DATA_DIR / "metrics.json")
    shutil.copy(config.GATE_COMPARISON_PATH, config.DEMO_DATA_DIR / "gate_comparison.csv")
    print(f"\nSaved {config.METRICS_PATH.name}, {config.GATE_COMPARISON_PATH.name}, gate_comparison.png "
          f"and copied them into app/demo_data/")


if __name__ == "__main__":
    main()
