#!/usr/bin/env python
"""Split TSL session export JSON into 2024 and 2025 CSVs using reference column order."""
from __future__ import annotations

import csv
import json
import logging
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

LOGGER = logging.getLogger("split_tsl_sessions")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ROOT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data" / "tsl"
SOURCE_JSON = DATA_DIR / "20250305_speaker_exports_TL24_TL25.json"
REFERENCE_CSV = PROJECT_ROOT / "data" / "cpcn" / "CPCN25_session_export.csv"
OUTPUTS = {
    2024: DATA_DIR / "TSL2024_session_export.csv",
    2025: DATA_DIR / "TSL2025_session_export.csv",
}


def load_reference_headers(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            return next(reader)
        except StopIteration:
            raise ValueError(f"Reference CSV {path} is empty")


def load_json_array(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def infer_year(record: Dict) -> Optional[int]:
    date_val = record.get("date")
    if isinstance(date_val, str) and len(date_val) >= 4 and date_val[:4].isdigit():
        year = int(date_val[:4])
        if year in (2024, 2025):
            return year
    file_hint = record.get("File_name") or record.get("file_name")
    if isinstance(file_hint, str):
        match = re.search(r"(\d{2})", file_hint)
        if match:
            suffix = match.group(1)
            if suffix == "24":
                return 2024
            if suffix == "25":
                return 2025
    return None


def write_csv(path: Path, headers: List[str], rows: Iterable[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({h: ("" if row.get(h) is None else row.get(h)) for h in headers})


def split_sessions(records: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    bucket_2024: List[Dict] = []
    bucket_2025: List[Dict] = []
    unknown: List[Dict] = []
    for rec in records:
        year = infer_year(rec)
        if year == 2024:
            bucket_2024.append(rec)
        elif year == 2025:
            bucket_2025.append(rec)
        else:
            unknown.append(rec)
    return bucket_2024, bucket_2025, unknown


def main() -> int:
    if not SOURCE_JSON.exists():
        LOGGER.error("Source JSON not found: %s", SOURCE_JSON)
        return 1
    if not REFERENCE_CSV.exists():
        LOGGER.error("Reference CSV not found: %s", REFERENCE_CSV)
        return 1

    headers = load_reference_headers(REFERENCE_CSV)
    records = load_json_array(SOURCE_JSON)

    rec24, rec25, unknown = split_sessions(records)
    LOGGER.info("Split complete -> 2024: %s | 2025: %s | unknown: %s", len(rec24), len(rec25), len(unknown))

    write_csv(OUTPUTS[2024], headers, rec24)
    write_csv(OUTPUTS[2025], headers, rec25)
    LOGGER.info("Wrote %s", OUTPUTS[2024].name)
    LOGGER.info("Wrote %s", OUTPUTS[2025].name)

    if unknown:
        LOGGER.warning("%s records could not be assigned to 2024/2025; check input fields", len(unknown))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
