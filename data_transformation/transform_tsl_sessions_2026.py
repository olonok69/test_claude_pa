#!/usr/bin/env python
"""Build Tech Show London 2026 session export from speaker-system Excel files.

The output schema mirrors CPC/TSL session exports from prior years (see TSL2024/2025 exports).
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import re
from ast import literal_eval
from html import unescape
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd

LOGGER = logging.getLogger("transform_tsl_sessions_2026")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ROOT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT_DIR.parent
CONFIG_PATH = ROOT_DIR / "config" / "tsl_sessions_2026_schema.json"


def load_config(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_reference_headers(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            return next(reader)
        except StopIteration as exc:
            raise ValueError(f"Reference CSV {path} is empty") from exc


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False


def clean_str(value: Any) -> str | None:
    if is_missing(value):
        return None
    text = str(value).strip()
    return text if text else None


def normalize_date(value: Any) -> str | None:
    if is_missing(value):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    return text if text else None


def normalize_time(value: Any) -> str | None:
    if is_missing(value):
        return None
    if isinstance(value, datetime):
        value = value.time()
    if isinstance(value, time):
        return value.replace(microsecond=0).isoformat()
    text = str(value).strip()
    if not text:
        return None
    # Accept HH:MM or HH:MM:SS
    if re.match(r"^\d{1,2}:\d{2}$", text):
        return f"{text}:00"
    if re.match(r"^\d{1,2}:\d{2}:\d{2}$", text):
        return text
    return text


def strip_html(text: Any) -> str | None:
    raw = clean_str(text)
    if raw is None:
        return None
    without_tags = re.sub(r"<[^>]+>", " ", raw)
    collapsed = re.sub(r"\s+", " ", without_tags).strip()
    return collapsed or None


def _ascii_safe(text: str) -> str:
    translation = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\xa0": " ",
    }
    for needle, replacement in translation.items():
        text = text.replace(needle, replacement)
    # Drop remaining non-ASCII characters
    return text.encode("ascii", "ignore").decode("ascii")


def sanitize_text(value: Any, strip_tags: bool = True) -> str | None:
    if is_missing(value):
        return None
    raw = strip_html(value) if strip_tags else clean_str(value)
    if raw is None:
        return None
    unescaped = unescape(raw)
    cleaned = _ascii_safe(unescaped)
    collapsed = re.sub(r"\s+", " ", cleaned).strip()
    return collapsed if collapsed else None


def scrub_fields(row: Dict[str, Any], fields: Sequence[str]) -> None:
    for field in fields:
        val = row.get(field)
        if isinstance(val, str):
            cleaned = sanitize_text(val, strip_tags=False)
            if cleaned is not None:
                row[field] = cleaned


def parse_jsonish(value: Any, default: Any) -> Any:
    if is_missing(value):
        return default
    if isinstance(value, (dict, list)):
        return value
    text = str(value).strip()
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        try:
            return literal_eval(text)
        except Exception:
            return default


def extract_session_id(record: Dict[str, Any]) -> Any:
    if not is_missing(record.get("ss_seminar_id")):
        return record.get("ss_seminar_id")
    content_code = clean_str(record.get("content_code"))
    if content_code:
        digits = re.findall(r"\d+", content_code)
        if digits:
            return digits[0]
    return None


def extract_stream(raw_stream: Any) -> str | None:
    parsed = parse_jsonish(raw_stream, [])
    names: List[str] = []
    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict):
                name = clean_str(item.get("name"))
                if name:
                    names.append(name)
            else:
                name = clean_str(item)
                if name:
                    names.append(name)
    return "; ".join(names) if names else None


def extract_theatre_name(raw_location: Any) -> str | None:
    parsed = parse_jsonish(raw_location, {})
    if isinstance(parsed, dict):
        return clean_str(parsed.get("name"))
    return None


def extract_sponsor(raw_sponsor: Any) -> Dict[str, Any]:
    parsed = parse_jsonish(raw_sponsor, {})
    if not isinstance(parsed, dict):
        return {}
    return parsed


def extract_people(raw: Any) -> List[Dict[str, Any]]:
    parsed = parse_jsonish(raw, [])
    return parsed if isinstance(parsed, list) else []


def extract_speaker_id(value: Any) -> Any:
    code = clean_str(value)
    if not code:
        return None
    digits = re.findall(r"\d+", code)
    if digits:
        return digits[0]
    return None


def write_csv(path: Path, headers: Sequence[str], rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(headers), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            normalized = {h: ("" if row.get(h) is None else row.get(h)) for h in headers}
            writer.writerow(normalized)


def load_excel_records(source_dir: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for path in sorted(source_dir.glob("*.xlsx")):
        df = pd.read_excel(path)
        df = df.where(pd.notnull(df), None)
        payload = df.to_dict(orient="records")
        for rec in payload:
            rec["source_file"] = path.name
            records.append(rec)
        LOGGER.info("Loaded %s rows from %s", len(payload), path.name)
    return records


def build_rows(records: List[Dict[str, Any]], headers: Sequence[str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    defaults = config.get("defaults", {})
    labels = config.get("speaker_type_labels", {})
    rows: List[Dict[str, Any]] = []

    for record in records:
        base = {h: defaults.get(h) for h in headers}
        base["session_id"] = extract_session_id(record)
        base["date"] = normalize_date(record.get("date"))
        base["start_time"] = normalize_time(record.get("start_time"))
        base["end_time"] = normalize_time(record.get("end_time"))
        base["overview"] = (
            sanitize_text(record.get("abstract"))
            or sanitize_text(record.get("description"))
            or defaults.get("overview")
        )
        base["record_session"] = defaults.get("record_session")
        base["theatre__name"] = extract_theatre_name(record.get("location"))
        base["title"] = sanitize_text(record.get("title"), strip_tags=False)
        base["stream"] = extract_stream(record.get("stream"))
        base["synopsis_stripped"] = (
            sanitize_text(record.get("description"))
            or sanitize_text(record.get("abstract"))
            or defaults.get("synopsis_stripped")
        )

        sponsor = extract_sponsor(record.get("sponsor"))
        base["sponsored_session"] = sponsor.get("is_sponsored", defaults.get("sponsored_session"))
        base["sponsored_by"] = clean_str(sponsor.get("sponsored_by"))
        base["website_response_message"] = defaults.get("website_response_message")
        base["association"] = clean_str(record.get("in_association_with")) or defaults.get("association")
        base["last_edited"] = clean_str(record.get("last_edited"))
        base["sponsor_logo"] = defaults.get("sponsor_logo")
        base["company_logo"] = defaults.get("company_logo")
        base["technical_requirements"] = defaults.get("technical_requirements")
        base["notes"] = defaults.get("notes")
        base["learning_outcomes"] = defaults.get("learning_outcomes")
        base["format"] = defaults.get("format")
        base["submission_count"] = defaults.get("submission_count")
        base["status__status_x"] = defaults.get("status__status_x")
        base["prerecorded"] = defaults.get("prerecorded")

        # Speaker rows
        speakers = [(person, labels.get("speaker", "Speaker")) for person in extract_people(record.get("speaker"))]
        chairs = [(person, labels.get("chair", "Chair")) for person in extract_people(record.get("chair_person"))]
        people = speakers + chairs

        if not people:
            # If no speakers are present, still emit a row with the session details
            scrub_fields(base, ["overview", "title", "synopsis_stripped", "speaker__speaker_detail__biography"])
            rows.append(base)
            continue

        for person, speaker_type in people:
            row = dict(base)
            row["speaker_id"] = extract_speaker_id(person.get("content_code"))
            row["speaker__salutation"] = clean_str(person.get("title"))
            row["speaker_type__speaker_type"] = speaker_type
            row["speaker__first_name"] = clean_str(person.get("first_name"))
            row["speaker__Last_name"] = clean_str(person.get("last_name"))
            row["speaker__speaker_detail__credentials"] = clean_str(person.get("credentials"))
            row["speaker__Job_title__title"] = clean_str(person.get("job_title"))
            row["speaker__organisation__organisation_name"] = clean_str(person.get("company"))
            row["speaker__country__name"] = clean_str(person.get("country"))
            row["status__status_y"] = defaults.get("status__status_y")
            row["speaker__speaker_detail__biography"] = sanitize_text(person.get("description"))
            row["speaker__speaker_detail__awards"] = None
            row["speaker__email"] = clean_str(person.get("email"))
            row["speaker__speaker_detail__assistant_email"] = defaults.get("speaker__speaker_detail__assistant_email")
            row["speaker__speaker_detail__assistant_only"] = defaults.get("speaker__speaker_detail__assistant_only")
            row["welcome_email"] = defaults.get("welcome_email")
            row["speaker__speaker_detail__speaker_photo"] = clean_str(person.get("profile_img"))
            row["speaker__speaker_detail__twitter"] = defaults.get("speaker__speaker_detail__twitter")
            row["speaker__phone"] = defaults.get("speaker__phone")
            row["speaker__direct"] = defaults.get("speaker__direct")
            row["speaker__speaker_detail__dietary_requirements"] = defaults.get("speaker__speaker_detail__dietary_requirements")
            row["speaker__last_edited"] = base.get("last_edited")
            scrub_fields(row, ["overview", "title", "synopsis_stripped", "speaker__speaker_detail__biography"])
            rows.append(row)

    return rows


def main() -> int:
    config = load_config(CONFIG_PATH)
    reference_csv = PROJECT_ROOT / config["reference_csv"]
    source_dir = PROJECT_ROOT / config["source_dir"]
    output_csv = PROJECT_ROOT / config["output_csv"]

    headers = load_reference_headers(reference_csv)
    records = load_excel_records(source_dir)
    if not records:
        LOGGER.error("No records found in %s", source_dir)
        return 1

    rows = build_rows(records, headers, config)
    if not rows:
        LOGGER.error("No rows generated from input Excel files")
        return 1

    write_csv(output_csv, headers, rows)
    LOGGER.info("Wrote %s rows to %s", len(rows), output_csv)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize Tech Show London 2026 session exports from Excel")
    parser.parse_args()
    raise SystemExit(main())
