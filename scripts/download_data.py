"""Download PhysioNet/CinC Challenge 2019 patient files (hospital sets A and B).

The data is real, de-identified ICU data and is open access (no login).

Usage (from the project folder):
    .venv/bin/python scripts/download_data.py            # 2,000 patients per set
    .venv/bin/python scripts/download_data.py --n 5000   # a different subset size
    .venv/bin/python scripts/download_data.py --all      # every patient (~255 MB, hours)

Running it again is safe: files that already exist are skipped (resume).
"""

import argparse
import csv
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple

import requests
from tqdm import tqdm

# Make "src" importable when this script is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config  # noqa: E402

LISTING_TIMEOUT_SECONDS = 900  # the listing pages are ~2 MB and the server is slow
FILE_TIMEOUT_SECONDS = 60
LISTING_RETRIES = 6  # waits 2+4+8+16+32+64 s, so a short Wi-Fi/hotspot drop does not stop us
FILE_NAME_PATTERN = re.compile(r'href="(p\d{6}\.psv)"')


def set_url(hospital: str) -> str:
    """Return the folder URL for hospital set 'A' or 'B'."""
    return f"{config.PHYSIONET_BASE_URL}/training_set{hospital}/"


def get_with_retries(url: str, timeout: int, retries: int = config.DOWNLOAD_RETRIES) -> bytes:
    """Download one URL, retrying with a growing wait (2 s, 4 s, 8 s, ...) if it fails."""
    last_error: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.content
        except requests.RequestException as error:
            last_error = error
            if attempt < retries:
                time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"Failed after {retries} retries: {url} ({last_error})")


def list_patient_files(hospital: str) -> List[str]:
    """Return every .psv file name in a set, read from PhysioNet's directory listing page.

    The listing is saved in data/ so later runs do not wait for it again.
    A listing is only trusted if it downloaded completely (ends with </html>).
    """
    cache_path = config.DATA_DIR / f"listing_{hospital}.html"
    if cache_path.exists():
        text = cache_path.read_text()
    else:
        print(f"Reading the file list for set {hospital} (slow server, can take a few minutes)...")
        content = get_with_retries(set_url(hospital), LISTING_TIMEOUT_SECONDS, LISTING_RETRIES)
        text = content.decode("utf-8")

    if "</html>" not in text:
        cache_path.unlink(missing_ok=True)
        raise RuntimeError(f"The listing for set {hospital} is incomplete. Please run again.")

    cache_path.write_text(text)
    names = sorted(set(FILE_NAME_PATTERN.findall(text)))
    print(f"Set {hospital}: {len(names)} patient files listed on PhysioNet.")
    return names


def choose_subset(names: List[str], n_patients: Optional[int]) -> List[str]:
    """Pick n_patients file names at random with the fixed seed (None = all files)."""
    if n_patients is None or n_patients >= len(names):
        return names
    rng = random.Random(config.SEED)
    return sorted(rng.sample(names, n_patients))


def download_one(hospital: str, name: str, folder: Path) -> str:
    """Download one patient file unless it already exists. Returns 'skipped' or 'downloaded'."""
    target = folder / name
    if target.exists() and target.stat().st_size > 0:
        return "skipped"
    content = get_with_retries(set_url(hospital) + name, FILE_TIMEOUT_SECONDS)
    # Write to a temporary name first, so a crash never leaves a half-written .psv file.
    temporary = folder / (name + ".part")
    temporary.write_bytes(content)
    temporary.rename(target)
    return "downloaded"


def download_set(hospital: str, names: List[str]) -> List[str]:
    """Download all chosen files of one set in parallel. Returns the names that failed."""
    folder = config.HOSPITAL_FOLDERS[hospital]
    folder.mkdir(parents=True, exist_ok=True)
    failed = []
    with ThreadPoolExecutor(max_workers=config.DOWNLOAD_WORKERS) as pool:
        futures = {pool.submit(download_one, hospital, name, folder): name for name in names}
        for future in tqdm(as_completed(futures), total=len(futures), desc=f"Set {hospital}"):
            try:
                future.result()
            except RuntimeError as error:
                print(error)
                failed.append(futures[future])
    return failed


def describe_file(path: Path) -> Tuple[int, int]:
    """Return (number of hourly rows, 1 if the patient ever has SepsisLabel = 1 else 0)."""
    with path.open() as handle:
        reader = csv.DictReader(handle, delimiter="|")
        rows = 0
        has_sepsis = 0
        for row in reader:
            rows += 1
            if row[config.LABEL] == "1":
                has_sepsis = 1
    return rows, has_sepsis


def write_manifest(chosen: dict) -> None:
    """Write data/manifest.csv with one line per downloaded patient file."""
    with config.MANIFEST_PATH.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["file", "set", "rows", "has_sepsis"])
        for hospital, names in chosen.items():
            folder = config.HOSPITAL_FOLDERS[hospital]
            for name in names:
                path = folder / name
                if path.exists():
                    rows, has_sepsis = describe_file(path)
                    writer.writerow([name, hospital, rows, has_sepsis])
    print(f"Manifest written: {config.MANIFEST_PATH}")


def parse_args() -> argparse.Namespace:
    """Read the command-line options."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n", type=int, default=config.PATIENTS_PER_SET,
                        help="patients per hospital set (default from src/config.py)")
    parser.add_argument("--all", action="store_true", help="download every patient file")
    return parser.parse_args()


def main() -> None:
    """List, sample, download and summarise both hospital sets."""
    args = parse_args()
    n_patients = None if args.all else args.n
    config.DATA_DIR.mkdir(exist_ok=True)

    chosen = {}
    all_failed = []
    for hospital in ["A", "B"]:
        names = choose_subset(list_patient_files(hospital), n_patients)
        chosen[hospital] = names
        all_failed += download_set(hospital, names)

    write_manifest(chosen)
    if all_failed:
        print(f"{len(all_failed)} files failed. Run the script again to retry them.")
    else:
        print("All files downloaded.")


if __name__ == "__main__":
    main()
