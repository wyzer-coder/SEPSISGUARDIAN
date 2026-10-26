"""Pick 50 hospital-B patients and save the small demo file for the website.

Hospital B was never used for training or choosing the threshold, so the demo shows
how the system behaves on patients it has not seen.

Run it (after src/train.py):
    .venv/bin/python scripts/build_demo_data.py
"""

import random
import sys
from pathlib import Path
from typing import List

import joblib
import pandas as pd

# Make "src" importable when this script is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config  # noqa: E402
from src.explain import why_now  # noqa: E402
from src.features import build_features  # noqa: E402
from src.gates import REVIEW, SUPPRESSED, WATCH, run_policy  # noqa: E402
from src.load_data import load_set, patient_summary  # noqa: E402

N_SEPSIS = 15
N_WATCH_ONLY = 3       # non-sepsis patients with WATCH hours but never a REVIEW
N_WITH_SUPPRESSED = 3  # patients with at least one SUPPRESSED hour
DEMO_PATH = config.DEMO_DATA_DIR / "demo_patients.csv.gz"

KEEP_COLUMNS = ["patient_id", "ICULOS", "Age", "Gender", "HR", "O2Sat", "Temp", "SBP", "MAP", "Resp",
                "Lactate", "hours_since_Lactate", "MAP_delta_3h", "HR_delta_3h", "Lactate_delta_3h",
                "news2_lite"]


def score_patients(features: pd.DataFrame) -> pd.DataFrame:
    """Add risk and the three-gate status to every hour of every patient."""
    saved = joblib.load(config.MODEL_PATH)
    hours = features[KEEP_COLUMNS].copy()
    hours["risk"] = saved["model"].predict_proba(features[saved["features"]])[:, 1]
    statuses = pd.Series("", index=hours.index, dtype=object)
    for _, patient in hours.groupby("patient_id", sort=False):
        statuses.loc[patient.index] = run_policy(patient, patient["risk"].tolist(), saved["threshold"])
    hours["status"] = statuses
    return hours


def pick_random(candidates: List[str], n: int, already: List[str], rng: random.Random) -> List[str]:
    """Pick n ids at random from candidates, skipping ids that are already chosen."""
    remaining = sorted(set(candidates) - set(already))
    return rng.sample(remaining, min(n, len(remaining)))


def choose_patients(hours: pd.DataFrame, summary: pd.DataFrame) -> List[str]:
    """Choose 50 patients: 15 sepsis (random) + 35 non-sepsis, with the required examples.

    Sepsis patients are picked at random (seed 42), so missed cases appear too: the demo is not cherry-picked.
    Then we make sure at least 3 patients show SUPPRESSED and at least 3 non-sepsis patients are WATCH-only.
    """
    rng = random.Random(config.SEED)
    per_patient = hours.groupby("patient_id")["status"].agg(set)
    sepsis_ids = list(summary.loc[summary["has_sepsis"] == 1, "patient_id"])
    non_sepsis_ids = list(summary.loc[summary["has_sepsis"] == 0, "patient_id"])

    chosen = pick_random(sepsis_ids, N_SEPSIS, [], rng)

    watch_only = [pid for pid in non_sepsis_ids if WATCH in per_patient[pid] and REVIEW not in per_patient[pid]]
    chosen += pick_random(watch_only, N_WATCH_ONLY, chosen, rng)

    n_suppressed = sum(SUPPRESSED in per_patient[pid] for pid in chosen)
    if n_suppressed < N_WITH_SUPPRESSED:
        with_suppressed = [pid for pid in non_sepsis_ids if SUPPRESSED in per_patient[pid]]
        chosen += pick_random(with_suppressed, N_WITH_SUPPRESSED - n_suppressed, chosen, rng)

    n_non_sepsis_left = config.N_DEMO_PATIENTS - len(chosen)
    chosen += pick_random(non_sepsis_ids, n_non_sepsis_left, chosen, rng)
    return chosen


def main() -> None:
    """Build app/demo_data/demo_patients.csv.gz and print what is inside."""
    raw = load_set(config.HOSPITAL_FOLDERS["B"], "B")
    summary = patient_summary(raw)
    features, _ = build_features(raw)
    hours = score_patients(features)

    chosen = choose_patients(hours, summary)
    rng = random.Random(config.SEED)
    rng.shuffle(chosen)  # so sepsis patients are not all on the first beds
    beds = {patient_id: bed for bed, patient_id in enumerate(chosen, start=1)}

    demo = hours[hours["patient_id"].isin(chosen)].copy()
    demo = demo.merge(summary[["patient_id", "has_sepsis", "onset_hour"]], on="patient_id")
    demo["bed"] = demo["patient_id"].map(beds)
    demo["reason_keys"] = [";".join(why_now(row)) for _, row in demo.iterrows()]
    demo = demo.sort_values(["bed", "ICULOS"]).reset_index(drop=True)

    config.DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    demo.to_csv(DEMO_PATH, index=False, compression="gzip")

    per_patient = demo.groupby("bed").agg(sepsis=("has_sepsis", "max"), statuses=("status", lambda s: set(s)))
    print(f"Saved {DEMO_PATH.name}: {demo['bed'].nunique()} beds, {len(demo)} patient-hours, "
          f"{DEMO_PATH.stat().st_size / 1024:.0f} KB")
    print(f"Sepsis patients: {int(per_patient['sepsis'].sum())}")
    print(f"Beds with a REVIEW: {sum(REVIEW in s for s in per_patient['statuses'])}")
    print(f"Beds with a SUPPRESSED hour: {sum(SUPPRESSED in s for s in per_patient['statuses'])}")
    watch_only = per_patient[[WATCH in s and REVIEW not in s for s in per_patient["statuses"]]]
    print(f"Beds with WATCH but never REVIEW: {len(watch_only)}")
    print(f"Longest stay: {demo['ICULOS'].max():.0f} ICU hours")


if __name__ == "__main__":
    main()
