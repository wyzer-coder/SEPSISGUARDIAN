"""All settings for SepsisGuardian in ONE place.

Every threshold below is a heuristic for a prototype.
None of them is clinically validated.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
DEMO_DATA_DIR = PROJECT_ROOT / "app" / "demo_data"
DOCS_DIR = PROJECT_ROOT / "docs"

# One folder per hospital system. A = training/validation, B = test only.
HOSPITAL_FOLDERS = {
    "A": DATA_DIR / "training_setA",
    "B": DATA_DIR / "training_setB",
}
MANIFEST_PATH = DATA_DIR / "manifest.csv"

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
SEED = 42

# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------
PHYSIONET_BASE_URL = "https://physionet.org/files/challenge-2019/1.0.0/training"
# Master-prompt default is 5,000; the team chose 2,000 per hospital (see docs/DECISIONS.md).
PATIENTS_PER_SET = 2000
DOWNLOAD_WORKERS = 12
DOWNLOAD_RETRIES = 3

# ---------------------------------------------------------------------------
# Data columns
# ---------------------------------------------------------------------------
VITALS = ["HR", "O2Sat", "Temp", "SBP", "MAP", "Resp"]
LABS = ["Lactate", "WBC", "Creatinine", "Bilirubin_total", "Platelets"]
STATIC = ["Age", "Gender", "HospAdmTime", "ICULOS"]
LABEL = "SepsisLabel"

# SepsisLabel is already shifted: it turns 1 six hours BEFORE clinical onset.
LABEL_SHIFT_HOURS = 6
HOURS_SINCE_CAP = 48

# ---------------------------------------------------------------------------
# Model split
# ---------------------------------------------------------------------------
TRAIN_FRACTION = 0.80  # of hospital A patients; the rest is validation

# Threshold grid searched on validation only.
# Calibrated hourly risks are small (about 2% of hours are sepsis hours), so the grid is low and fine.
THRESHOLD_GRID_START = 0.010
THRESHOLD_GRID_STOP = 0.200
THRESHOLD_GRID_STEP = 0.001
MIN_PATIENT_SENSITIVITY = 0.60

# Main model: HistGradientBoostingClassifier settings
HGB_MAX_ITER = 200
HGB_LEARNING_RATE = 0.05
HGB_MAX_LEAF_NODES = 31
HGB_L2_REGULARIZATION = 1.0

# Isotonic calibration uses this many folds of the TRAIN patients (grouped by patient).
CALIBRATION_FOLDS = 5

# Phase 3 outputs
MODEL_PATH = DEMO_DATA_DIR / "model.joblib"
THRESHOLD_PATH = RESULTS_DIR / "threshold.json"
VALIDATION_METRICS_PATH = RESULTS_DIR / "validation_metrics.json"
BASELINE_MODEL_PATH = RESULTS_DIR / "baseline_model.joblib"

# Phase 4 outputs
METRICS_PATH = RESULTS_DIR / "metrics.json"
GATE_COMPARISON_PATH = RESULTS_DIR / "gate_comparison.csv"
GATED_THRESHOLD_GRID_PATH = RESULTS_DIR / "threshold_grid_gated.csv"
TEST_HOURS_PATH = DATA_DIR / "test_hours_B.csv.gz"  # per-hour results; stays out of Git
# The gated threshold search runs every policy hour by hour, so it uses a coarser step.
GATED_THRESHOLD_GRID_STEP = 0.002

# ---------------------------------------------------------------------------
# Three-gate alert controller (heuristics, editable)
# ---------------------------------------------------------------------------
# Gate 2 "Worsening": ANY one of these makes the gate pass.
GATE2_MAP_DROP = -10.0       # MAP_delta_3h <= -10 mmHg
GATE2_HR_RISE = 15.0         # HR_delta_3h >= +15 bpm
GATE2_LACTATE_RISE = 0.5     # Lactate_delta_3h >= +0.5 mmol/L
GATE2_RESP_HIGH = 24.0       # Resp >= 24 breaths/min
GATE2_O2SAT_LOW = 92.0       # O2Sat <= 92 %

# Gate 3 "New": no REVIEW alert for this patient in the previous 6 hours.
GATE3_COOLDOWN_HOURS = 6

# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
# An alert is TRUE if it fires in [onset - 12 h, onset + 2 h] for a sepsis patient.
ALERT_WINDOW_BEFORE_HOURS = 12
ALERT_WINDOW_AFTER_HOURS = 2
NEWS2_LITE_ALERT_SCORE = 5

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
STATUS_COLOURS = {
    "NO_ALERT": "#2E9E5B",
    "WATCH": "#E0A800",
    "SUPPRESSED": "#8A8F98",
    "REVIEW": "#D64545",
}
SAFETY_LINE = "Clinical decision support — not a diagnosis. A clinician must confirm."
N_DEMO_PATIENTS = 50
