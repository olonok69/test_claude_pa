#!/usr/bin/env python
"""Split legacy TSL 24/25 registration and demographic bundles into year-specific files.

This is a light utility to pre-stage inputs for transform_tsl_data.py when
you need distinct 2024 (secondary) and 2025 (main) datasets.
"""
from __future__ import annotations

import json
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

LOGGER = logging.getLogger("split_tsl_legacy")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ROOT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data" / "tsl"

INPUT_REG = DATA_DIR / "Reg_Tech_Lnd_24_25.json"
INPUT_DEMO = DATA_DIR / "Demographics_Tech_Lnd_24_25.json"

OUTPUTS = {
    "reg_2024": DATA_DIR / "Reg_Tech_Lnd_24.json",
    "reg_2025": DATA_DIR / "Reg_Tech_Lnd_25.json",
    "demo_2024": DATA_DIR / "Demographics_Tech_Lnd_24.json",
    "demo_2025": DATA_DIR / "Demographics_Tech_Lnd_25.json",
}


def load_json_array(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json_array(path: Path, rows: Iterable[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(list(rows), handle, ensure_ascii=False, indent=2)


def _extract_showref(record: Dict) -> Optional[str]:
    # Accept both legacy ShowRef fields and newer eventId keys
    for key in ("ShowRef", "showref", "show_ref", "eventId", "event_id", "EventId"):
        if key in record and record[key] not in (None, ""):
            return str(record[key]).strip()
    return None


def _infer_year(show_ref: str) -> Optional[str]:
    show_ref = show_ref.strip()
    for suffix in ("24", "25"):
        if show_ref.upper().endswith(suffix):
            return suffix
    return None


def _split_records(rows: List[Dict], label: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    bucket_24: List[Dict] = []
    bucket_25: List[Dict] = []
    unknown: List[Dict] = []

    for row in rows:
        show_ref = _extract_showref(row)
        year_suffix = _infer_year(show_ref or "") if show_ref else None
        if year_suffix == "24":
            bucket_24.append(row)
        elif year_suffix == "25":
            bucket_25.append(row)
        else:
            unknown.append(row)

    LOGGER.info(
        "%s split -> 2024: %s | 2025: %s | unknown: %s",
        label,
        len(bucket_24),
        len(bucket_25),
        len(unknown),
    )
    return bucket_24, bucket_25, unknown


def main(force: bool = False) -> int:
    if not INPUT_REG.exists() or not INPUT_DEMO.exists():
        LOGGER.error("Input files not found. Expected %s and %s", INPUT_REG.name, INPUT_DEMO.name)
        return 1

    if not force and all(path.exists() for path in OUTPUTS.values()):
        LOGGER.info(
            "Split outputs already exist (%s). Skipping split. Use --force to regenerate.",
            ", ".join(path.name for path in OUTPUTS.values()),
        )
        return 0

    reg_rows = load_json_array(INPUT_REG)
    demo_rows = load_json_array(INPUT_DEMO)

    reg24, reg25, reg_unknown = _split_records(reg_rows, "Registration")
    demo24, demo25, demo_unknown = _split_records(demo_rows, "Demographics")

    save_json_array(OUTPUTS["reg_2024"], reg24)
    save_json_array(OUTPUTS["reg_2025"], reg25)
    save_json_array(OUTPUTS["demo_2024"], demo24)
    save_json_array(OUTPUTS["demo_2025"], demo25)

    if reg_unknown or demo_unknown:
        LOGGER.warning(
            "Some records could not be assigned to 2024/2025 (registration: %s, demographics: %s)." \
            " Review showrefs and re-run if needed.",
            len(reg_unknown),
            len(demo_unknown),
        )

    LOGGER.info("Outputs written: %s", ", ".join(path.name for path in OUTPUTS.values()))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split legacy TSL 24/25 bundle into per-year files")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate split output files even if they already exist",
    )
    args = parser.parse_args()
    sys.exit(main(force=args.force))
