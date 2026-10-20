"""Read the .psv patient files into one table (one row per patient-hour).

Run it to print a summary:
    .venv/bin/python -m src.load_data
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src import config


def read_patient_file(path: Path) -> pd.DataFrame:
    """Read one patient's pipe-separated file. Each row is one ICU hour."""
    return pd.read_csv(path, sep="|")


def load_set(folder: Path, hospital: str) -> pd.DataFrame:
    """Read every .psv file in a folder into one DataFrame.

    Adds two columns:
      patient_id - the file name without ".psv" (for example "p000001")
      hospital   - "A" or "B"
    Rows are sorted by patient_id, then by ICU hour (ICULOS).
    """
    tables = []
    for path in sorted(Path(folder).glob("*.psv")):
        table = read_patient_file(path)
        table["patient_id"] = path.stem
        table["hospital"] = hospital
        tables.append(table)
    if not tables:
        raise FileNotFoundError(f"No .psv files found in {folder}. Run scripts/download_data.py first.")
    data = pd.concat(tables, ignore_index=True)
    return data.sort_values(["patient_id", "ICULOS"]).reset_index(drop=True)


def onset_hour(patient: pd.DataFrame) -> float:
    """Return the clinical sepsis onset hour (ICULOS) for one patient, or NaN if no sepsis.

    PhysioNet already shifted SepsisLabel: it turns 1 six hours BEFORE onset.
    So onset = first hour with SepsisLabel = 1, plus 6. We never shift the label again.
    """
    labelled_hours = patient.loc[patient[config.LABEL] == 1, "ICULOS"]
    if labelled_hours.empty:
        return np.nan
    return float(labelled_hours.min() + config.LABEL_SHIFT_HOURS)


def patient_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Return one row per patient: patient_id, hospital, n_hours, has_sepsis, onset_hour."""
    rows = []
    for patient_id, patient in data.groupby("patient_id", sort=True):
        rows.append({
            "patient_id": patient_id,
            "hospital": patient["hospital"].iloc[0],
            "n_hours": len(patient),
            "has_sepsis": int(patient[config.LABEL].max() == 1),
            "onset_hour": onset_hour(patient),
        })
    return pd.DataFrame(rows)


def print_summary(summary: pd.DataFrame, hospital: str) -> None:
    """Print number of patients, % with sepsis and median hours per patient."""
    n_patients = len(summary)
    sepsis_percent = 100 * summary["has_sepsis"].mean()
    median_hours = summary["n_hours"].median()
    print(f"Hospital {hospital}: {n_patients} patients, "
          f"{sepsis_percent:.1f}% with sepsis, "
          f"median {median_hours:.0f} hours per patient")


def main() -> None:
    """Load every hospital folder that exists and print its summary."""
    for hospital, folder in config.HOSPITAL_FOLDERS.items():
        if not Path(folder).exists():
            print(f"Hospital {hospital}: folder not found yet ({folder})")
            continue
        data = load_set(folder, hospital)
        print_summary(patient_summary(data), hospital)


if __name__ == "__main__":
    main()
