#!/usr/bin/env python
"""Normalize Tech Show London (TSL) registration/demographics datasets (2024/25 legacy, 2026 nested).

Outputs GraphQL-style JSON plus optional legacy JSON; produces combined multi-year files similar to CPC/LVA.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from header_mapping_utils import get_mapped_value, load_header_mappings

LOGGER = logging.getLogger("transform_tsl_data")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

RUN_TIMESTAMP = datetime.utcnow().replace(microsecond=0).isoformat()
RUN_ID = str(uuid.uuid4()).upper()
ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://closerstillmedia.com/schema-adapter")
PROVIDER_SOURCE = "schema_adapter"
DEFAULT_RECORD_END_DATE = "9999-12-31T00:00:00"

SHOW_DETAILS: Dict[str, Dict[str, Optional[str]]] = {
    "TSL26": {
        "event_id": None,  # not provided; leave as None
        "show_date": None,
    },
}

ROOT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data" / "tsl"
# Reuse CPC reference exports; schema matches GraphQL target.
REFERENCE_DIR = PROJECT_ROOT / "data" / "cpcn" / "reference"
CONFIG_PATH = ROOT_DIR / "config" / "header_mappings.json"

REFERENCE_DEMOGRAPHICS = REFERENCE_DIR / "30092025_CPC25_demographics_graphql.json"
REFERENCE_REGISTRATION = REFERENCE_DIR / "30092025_CPCN25_registration_graphql.json"
REFERENCE_SESSIONS = REFERENCE_DIR / "CPCN25_session_export.csv"



ID_SUFFIX_DELIMITER = "|"


HEADER_MAPPINGS = load_header_mappings(CONFIG_PATH)
REGISTRATION_MAP = HEADER_MAPPINGS["registration"]
DEMO_FLAT_MAP = HEADER_MAPPINGS["demographics"]["flat"]
DEMO_NESTED_BASE_MAP = HEADER_MAPPINGS["demographics"]["nested_base"]
DEMO_NESTED_RESPONSE_MAP = HEADER_MAPPINGS["demographics"]["nested_response"]


def load_json_array(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json_array(path: Path, payload: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(list(payload), handle, ensure_ascii=False, indent=2)


def bool_to_flag(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return "1" if bool(value) else "0"
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y"}:
            return "1"
        if normalized in {"0", "false", "no", "n"}:
            return "0"
    return None


def flag_to_yes_no(value: Any) -> Optional[str]:
    if value is None:
        return None
    str_val = str(value).strip().lower()
    if str_val in {"1", "true", "yes", "y"}:
        return "Yes"
    if str_val in {"0", "false", "no", "n"}:
        return "No"
    return str(value)


def safe_int(value: Any) -> Optional[int]:
    if value in (None, "", "null"):
        return None
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


def normalize_timestamp(raw: Any) -> Optional[str]:
    if raw in (None, ""):
        return None
    text = str(raw).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    for suffix in (".000", ".000000"):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    try:
        dt_obj = datetime.fromisoformat(text)
    except ValueError:
        return str(raw)
    return dt_obj.replace(tzinfo=None).isoformat(timespec="seconds")


def infer_show_ref(source: Optional[str], default: Optional[str]) -> Optional[str]:
    if source:
        matches = re.findall(r"[A-Za-z]{2,}\d{2,}", source)
        if matches:
            return matches[0].upper()
    return default


def load_reference_keys(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8") as handle:
        buffer: List[str] = []
        depth = 0
        inside_object = False
        while True:
            chunk = handle.read(1024)
            if not chunk:
                break
            for char in chunk:
                if not inside_object:
                    if char == "{":
                        inside_object = True
                        depth = 1
                        buffer.append(char)
                    elif char in "[{\n\r\t ":
                        continue
                    else:
                        continue
                else:
                    buffer.append(char)
                    if char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth == 0:
                            obj = json.loads("".join(buffer))
                            keys = list(obj.keys())
                            LOGGER.info("Loaded %s reference keys from %s", len(keys), path.name)
                            return keys
        raise ValueError(f"Unable to locate first object in reference file {path}")


def build_template(keys: Iterable[str]) -> Dict[str, Any]:
    return {key: None for key in keys}


def apply_metadata(record: Dict[str, Any], show_ref: Optional[str], seq_key: str, seq_value: int, source_filename: str) -> None:
    record["metadata_source_filename"] = source_filename
    record["metadata_provider_source"] = PROVIDER_SOURCE
    record["metadata_pipeline_run_id"] = RUN_ID
    record["metadata_pipeline_trigger_date"] = RUN_TIMESTAMP
    record["metadata_record_start_date"] = RUN_TIMESTAMP
    record["metadata_record_end_date"] = DEFAULT_RECORD_END_DATE
    record["metadata_is_current"] = "1"
    record["metadata_is_updated"] = "0"
    if seq_key:
        record[seq_key] = seq_value
    if "metadata_show_date" in record and not record.get("metadata_show_date"):
        details = SHOW_DETAILS.get((show_ref or "").upper())
        if details:
            record["metadata_show_date"] = details.get("show_date")


def resequence(records: Sequence[Dict[str, Any]], seq_key: str) -> None:
    for idx, record in enumerate(records, start=1):
        record[seq_key] = idx


def make_demographic_id(badge_id: Optional[str], question_id: Optional[int], answer_id: Optional[int], show_ref: Optional[str]) -> str:
    parts = [badge_id or "", str(question_id or ""), str(answer_id or ""), show_ref or ""]
    return str(uuid.uuid5(ID_NAMESPACE, ID_SUFFIX_DELIMITER.join(parts)))


def transform_nested_demographics(records: Sequence[Dict[str, Any]], template_keys: Sequence[str], show_ref: str, source_filename: str) -> List[Dict[str, Any]]:
    template = build_template(template_keys)
    event_id = SHOW_DETAILS.get(show_ref.upper(), {}).get("event_id")
    transformed: List[Dict[str, Any]] = []
    counter = 0
    for base in records:
        badge_id = get_mapped_value(base, DEMO_NESTED_BASE_MAP, "badge_id")
        inferred_show = infer_show_ref(get_mapped_value(base, DEMO_NESTED_BASE_MAP, "event_id"), None)
        responses = get_mapped_value(base, DEMO_NESTED_BASE_MAP, "question_responses", []) or []
        for response in responses:
            counter += 1
            record = template.copy()
            question_id = safe_int(get_mapped_value(response, DEMO_NESTED_RESPONSE_MAP, "question_id"))
            answer_id = safe_int(get_mapped_value(response, DEMO_NESTED_RESPONSE_MAP, "answer_id"))
            record["id"] = make_demographic_id(badge_id, question_id, answer_id, inferred_show)
            record["badge_id"] = badge_id
            record["event_id"] = get_mapped_value(base, DEMO_NESTED_BASE_MAP, "event_id") or event_id
            record["show_ref"] = (inferred_show or event_id or "UNKNOWN").upper()
            record["question_type"] = get_mapped_value(response, DEMO_NESTED_RESPONSE_MAP, "question_type")
            record["question_id"] = question_id
            record["question_text"] = get_mapped_value(response, DEMO_NESTED_RESPONSE_MAP, "question_text")
            record["answer_id"] = answer_id
            record["answer_text"] = get_mapped_value(response, DEMO_NESTED_RESPONSE_MAP, "answer_text")
            record["is_positive"] = bool_to_flag(get_mapped_value(response, DEMO_NESTED_RESPONSE_MAP, "is_positive"))
            record["response_text"] = get_mapped_value(response, DEMO_NESTED_RESPONSE_MAP, "response_text")
            record.setdefault("metadata_demographics_dimension_checksum", 0)
            apply_metadata(record, record["show_ref"], "demographics_seq", counter, source_filename)
            transformed.append(record)
    return transformed


def transform_registration(records: Sequence[Dict[str, Any]], template_keys: Sequence[str], show_ref: str, source_filename: str) -> List[Dict[str, Any]]:
    template = build_template(template_keys)
    event_id = SHOW_DETAILS.get(show_ref.upper(), {}).get("event_id")
    transformed: List[Dict[str, Any]] = []

    for idx, item in enumerate(records, start=1):
        record = template.copy()
        record["id"] = get_mapped_value(item, REGISTRATION_MAP, "id")
        record["title"] = get_mapped_value(item, REGISTRATION_MAP, "title")
        record["forename"] = get_mapped_value(item, REGISTRATION_MAP, "forename")
        record["surname"] = get_mapped_value(item, REGISTRATION_MAP, "surname")
        record["email"] = get_mapped_value(item, REGISTRATION_MAP, "email")
        record["tel"] = get_mapped_value(item, REGISTRATION_MAP, "tel")
        record["mobile"] = get_mapped_value(item, REGISTRATION_MAP, "mobile")
        record["fax"] = get_mapped_value(item, REGISTRATION_MAP, "fax")
        record["company"] = get_mapped_value(item, REGISTRATION_MAP, "company")
        record["job_title"] = get_mapped_value(item, REGISTRATION_MAP, "job_title")
        record["addr1"] = get_mapped_value(item, REGISTRATION_MAP, "addr1")
        record["addr2"] = get_mapped_value(item, REGISTRATION_MAP, "addr2")
        record["addr3"] = get_mapped_value(item, REGISTRATION_MAP, "addr3")
        record["town"] = get_mapped_value(item, REGISTRATION_MAP, "town")
        record["county"] = get_mapped_value(item, REGISTRATION_MAP, "county")
        record["postcode"] = get_mapped_value(item, REGISTRATION_MAP, "postcode")
        record["country"] = get_mapped_value(item, REGISTRATION_MAP, "country")
        record["status"] = get_mapped_value(item, REGISTRATION_MAP, "status")
        record["badge_type"] = get_mapped_value(item, REGISTRATION_MAP, "badge_type")
        event_id_value = get_mapped_value(item, REGISTRATION_MAP, "event_id")
        event_identifier_value = get_mapped_value(item, REGISTRATION_MAP, "event_identifier")
        # Drop records that do not carry an event id/identifier
        if not event_id_value and not event_identifier_value:
            LOGGER.warning("Skipping registration with no event id/identifier: %s", record.get("id"))
            continue
        record["event_id"] = event_id_value or event_id
        record["registration_date"] = normalize_timestamp(get_mapped_value(item, REGISTRATION_MAP, "registration_date"))
        record["badge_id"] = get_mapped_value(item, REGISTRATION_MAP, "badge_id")
        record["reg_code"] = get_mapped_value(item, REGISTRATION_MAP, "reg_code")
        record["source"] = get_mapped_value(item, REGISTRATION_MAP, "source")
        record["attended"] = bool_to_flag(get_mapped_value(item, REGISTRATION_MAP, "attended"))
        record["segment_from_reg"] = get_mapped_value(item, REGISTRATION_MAP, "segment_from_reg")
        record["upgrade"] = get_mapped_value(item, REGISTRATION_MAP, "upgrade")
        record["last_modified_date"] = normalize_timestamp(get_mapped_value(item, REGISTRATION_MAP, "last_modified_date"))
        inferred_show = infer_show_ref(event_identifier_value, None) or infer_show_ref(event_id_value, None)
        # Prefer explicit event values; avoid defaulting to a blanket show_ref like "TSL26"
        record["show_ref"] = (inferred_show or event_id_value or "UNKNOWN").upper()
        record.setdefault("metadata_dimension_checksum", 0)
        apply_metadata(record, record["show_ref"], "registration_seq", idx, source_filename)
        transformed.append(record)
    return transformed


def legacy_registration_to_graphql(records: Sequence[Dict[str, Any]], template_keys: Sequence[str], source_filename: str) -> List[Dict[str, Any]]:
    template = build_template(template_keys)
    transformed: List[Dict[str, Any]] = []
    for idx, item in enumerate(records, start=1):
        record = template.copy()
        record["id"] = get_mapped_value(item, REGISTRATION_MAP, "id")
        record["title"] = get_mapped_value(item, REGISTRATION_MAP, "title")
        record["forename"] = get_mapped_value(item, REGISTRATION_MAP, "forename")
        record["surname"] = get_mapped_value(item, REGISTRATION_MAP, "surname")
        record["email"] = get_mapped_value(item, REGISTRATION_MAP, "email")
        record["tel"] = get_mapped_value(item, REGISTRATION_MAP, "tel")
        record["mobile"] = get_mapped_value(item, REGISTRATION_MAP, "mobile")
        record["fax"] = get_mapped_value(item, REGISTRATION_MAP, "fax")
        record["company"] = get_mapped_value(item, REGISTRATION_MAP, "company")
        record["job_title"] = get_mapped_value(item, REGISTRATION_MAP, "job_title")
        record["addr1"] = get_mapped_value(item, REGISTRATION_MAP, "addr1")
        record["addr2"] = get_mapped_value(item, REGISTRATION_MAP, "addr2")
        record["addr3"] = get_mapped_value(item, REGISTRATION_MAP, "addr3")
        record["town"] = get_mapped_value(item, REGISTRATION_MAP, "town")
        record["county"] = get_mapped_value(item, REGISTRATION_MAP, "county")
        record["postcode"] = get_mapped_value(item, REGISTRATION_MAP, "postcode")
        record["country"] = get_mapped_value(item, REGISTRATION_MAP, "country")
        record["status"] = get_mapped_value(item, REGISTRATION_MAP, "status")
        record["badge_type"] = get_mapped_value(item, REGISTRATION_MAP, "badge_type")
        record["event_id"] = get_mapped_value(item, REGISTRATION_MAP, "event_id")
        record["registration_date"] = normalize_timestamp(get_mapped_value(item, REGISTRATION_MAP, "registration_date"))
        record["badge_id"] = get_mapped_value(item, REGISTRATION_MAP, "badge_id")
        record["reg_code"] = get_mapped_value(item, REGISTRATION_MAP, "reg_code")
        record["source"] = get_mapped_value(item, REGISTRATION_MAP, "source")
        record["attended"] = bool_to_flag(get_mapped_value(item, REGISTRATION_MAP, "attended"))
        record["segment_from_reg"] = get_mapped_value(item, REGISTRATION_MAP, "segment_from_reg")
        record["upgrade"] = get_mapped_value(item, REGISTRATION_MAP, "upgrade")
        record["last_modified_date"] = normalize_timestamp(get_mapped_value(item, REGISTRATION_MAP, "last_modified_date"))
        # Prefer explicit show_ref or event_id; do not fall back to source-derived codes
        show_ref = get_mapped_value(item, REGISTRATION_MAP, "show_ref") or record.get("event_id") or "UNKNOWN"
        show_ref = str(show_ref).upper()
        record["show_ref"] = show_ref
        record.setdefault("metadata_dimension_checksum", 0)
        apply_metadata(record, show_ref, "registration_seq", idx, source_filename)
        transformed.append(record)
    return transformed


def legacy_demographics_to_graphql(records: Sequence[Dict[str, Any]], template_keys: Sequence[str], source_filename: str) -> List[Dict[str, Any]]:
    template = build_template(template_keys)
    transformed: List[Dict[str, Any]] = []
    for idx, item in enumerate(records, start=1):
        record = template.copy()
        badge_id = item.get("BadgeId")
        question_text = item.get("QuestionText")
        answer_text = item.get("AnswerText")
        record["id"] = make_demographic_id(badge_id, None, None, item.get("showref"))
        record["badge_id"] = badge_id
        record["event_id"] = None
        record["show_ref"] = (item.get("showref") or "UNKNOWN").upper()
        record["question_type"] = None
        record["question_id"] = None
        record["question_text"] = question_text
        record["answer_id"] = None
        record["answer_text"] = answer_text
        record["is_positive"] = None
        record["response_text"] = None
        record.setdefault("metadata_demographics_dimension_checksum", 0)
        apply_metadata(record, record["show_ref"], "demographics_seq", idx, source_filename)
        transformed.append(record)
    return transformed


def convert_registration_to_legacy(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    legacy_fields = [
        "Id",
        "Title",
        "Forename",
        "Surname",
        "Email",
        "Tel",
        "Mobile",
        "Fax",
        "Company",
        "JobTitle",
        "Addr1",
        "Addr2",
        "Addr3",
        "Town",
        "County",
        "Postcode",
        "Country",
        "Status",
        "BadgeType",
        "ShowRef",
        "RegistrationDate",
        "BadgeId",
        "RegCode",
        "Source",
        "Attended",
        "SegmentFromReg",
        "Upgrade",
    ]
    legacy_records: List[Dict[str, Any]] = []
    for item in records:
        def _as_str(key: str) -> Optional[str]:
            value = item.get(key)
            if value is None:
                return None
            return str(value)
        mapped = {
            "Id": item.get("id"),
            "Title": item.get("title"),
            "Forename": item.get("forename"),
            "Surname": item.get("surname"),
            "Email": item.get("email"),
            "Tel": _as_str("tel"),
            "Mobile": _as_str("mobile"),
            "Fax": _as_str("fax"),
            "Company": item.get("company"),
            "JobTitle": item.get("job_title"),
            "Addr1": item.get("addr1"),
            "Addr2": item.get("addr2"),
            "Addr3": item.get("addr3"),
            "Town": item.get("town"),
            "County": item.get("county"),
            "Postcode": item.get("postcode"),
            "Country": item.get("country"),
            "Status": item.get("status"),
            "BadgeType": item.get("badge_type"),
            "ShowRef": item.get("show_ref"),
            "RegistrationDate": item.get("registration_date"),
            "BadgeId": item.get("badge_id"),
            "RegCode": item.get("reg_code"),
            "Source": item.get("source"),
            "Attended": flag_to_yes_no(item.get("attended")),
            "SegmentFromReg": item.get("segment_from_reg"),
            "Upgrade": item.get("upgrade"),
            "METADATA_fileName": item.get("metadata_source_filename"),
        }
        # Ensure all legacy fields are present even if missing in input
        for key in legacy_fields:
            mapped.setdefault(key, None)
        legacy_records.append(mapped)
    return legacy_records


def convert_demographics_to_legacy(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    legacy_records: List[Dict[str, Any]] = []
    for item in records:
        answer_text = item.get("answer_text")
        response_text = item.get("response_text")
        legacy_records.append(
            {
                "showref": (item.get("show_ref") or "").upper(),
                "BadgeId": item.get("badge_id"),
                "QuestionText": item.get("question_text") or "",
                "AnswerText": answer_text if answer_text not in (None, "") else (response_text or ""),
                "METADATA_fileName": item.get("metadata_source_filename"),
            }
        )
    return legacy_records


def validate_against_reference(
    records: Sequence[Dict[str, Any]],
    reference_keys: Sequence[str],
    dataset_name: str,
    allow_extra: Optional[Sequence[str]] = None,
) -> None:
    if not records:
        LOGGER.warning("%s: no records available for validation", dataset_name)
        return
    ref_set = set(reference_keys)
    record_keys = set(records[0].keys())
    missing = ref_set - record_keys
    if missing:
        raise ValueError(f"{dataset_name}: missing keys compared to reference: {sorted(missing)}")
    allowed = set(allow_extra or [])
    extra = record_keys - ref_set - allowed
    if extra:
        LOGGER.warning("%s: additional keys not in reference: %s", dataset_name, sorted(extra))


def ensure_registration_processor_compatibility(records: Sequence[Dict[str, Any]], required_keys: Sequence[str], dataset_name: str) -> None:
    sample = records[0] if records else {}
    missing = [key for key in required_keys if key not in sample]
    if missing:
        raise ValueError(f"{dataset_name}: missing required keys for registration processor {missing}")


def _copy_records(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [deepcopy(item) for item in records]


def main(
    include_legacy: bool = False,
    tsl26_registration_path: Optional[str] = None,
    tsl26_demographics_path: Optional[str] = None,
    tsl24_registration_legacy_path: Optional[str] = None,
    tsl24_demographics_legacy_path: Optional[str] = None,
    tsl25_registration_legacy_path: Optional[str] = None,
    tsl25_demographics_legacy_path: Optional[str] = None,
    output_prefix: Optional[str] = None,
) -> None:
    LOGGER.info("Run id %s triggered at %s", RUN_ID, RUN_TIMESTAMP)
    ref_demo_keys = load_reference_keys(REFERENCE_DEMOGRAPHICS)
    ref_reg_keys = load_reference_keys(REFERENCE_REGISTRATION)
    if "show_ref" not in ref_reg_keys:
        ref_reg_keys.append("show_ref")

    input_files = {
        "tsl24_registration_legacy": DATA_DIR / "Reg_Tech_Lnd_24.json",
        "tsl25_registration_legacy": DATA_DIR / "Reg_Tech_Lnd_25.json",
        "tsl24_demographics_legacy": DATA_DIR / "Demographics_Tech_Lnd_24.json",
        "tsl25_demographics_legacy": DATA_DIR / "Demographics_Tech_Lnd_25.json",
        "tsl26_registration": DATA_DIR / "20260120_tsl26_registration.json",
        "tsl26_demographics": DATA_DIR / "20260120_tsl26_demographics.json",
    }

    if tsl24_registration_legacy_path:
        input_files["tsl24_registration_legacy"] = Path(tsl24_registration_legacy_path)
    if tsl24_demographics_legacy_path:
        input_files["tsl24_demographics_legacy"] = Path(tsl24_demographics_legacy_path)
    if tsl25_registration_legacy_path:
        input_files["tsl25_registration_legacy"] = Path(tsl25_registration_legacy_path)
    if tsl25_demographics_legacy_path:
        input_files["tsl25_demographics_legacy"] = Path(tsl25_demographics_legacy_path)

    if tsl26_registration_path:
        input_files["tsl26_registration"] = Path(tsl26_registration_path)
    if tsl26_demographics_path:
        input_files["tsl26_demographics"] = Path(tsl26_demographics_path)

    resolved_prefix = (output_prefix or datetime.utcnow().strftime("%Y%m%d")).strip()

    LOGGER.info(
        "Using TSL26 inputs: registration=%s demographics=%s",
        input_files["tsl26_registration"],
        input_files["tsl26_demographics"],
    )

    output_files = {
        "main_registration": DATA_DIR / f"{resolved_prefix}_tsl25_26_registration_graphql.json",
        "main_demographics": DATA_DIR / f"{resolved_prefix}_tsl25_26_demographics_graphql.json",
        "secondary_registration": DATA_DIR / f"{resolved_prefix}_tsl24_registration_graphql.json",
        "secondary_demographics": DATA_DIR / f"{resolved_prefix}_tsl24_demographics_graphql.json",
    }

    legacy_output_files = {
        "main_registration": DATA_DIR / f"{resolved_prefix}_tsl25_26_registration_legacy.json",
        "main_demographics": DATA_DIR / f"{resolved_prefix}_tsl25_26_demographics_legacy.json",
        "secondary_registration": DATA_DIR / f"{resolved_prefix}_tsl24_registration_legacy.json",
        "secondary_demographics": DATA_DIR / f"{resolved_prefix}_tsl24_demographics_legacy.json",
        "tsl26_registration": DATA_DIR / f"{resolved_prefix}_tsl26_registration_legacy.json",
        "tsl26_demographics": DATA_DIR / f"{resolved_prefix}_tsl26_demographics_legacy.json",
    }

    LOGGER.info("Using output prefix: %s", resolved_prefix)

    # Load legacy 24/25 (already legacy shaped) from split files
    reg24_raw = load_json_array(input_files["tsl24_registration_legacy"])
    reg25_raw = load_json_array(input_files["tsl25_registration_legacy"])
    demo24_raw = load_json_array(input_files["tsl24_demographics_legacy"])
    demo25_raw = load_json_array(input_files["tsl25_demographics_legacy"])

    # Convert legacy to GraphQL for outputs
    reg24_graphql = legacy_registration_to_graphql(reg24_raw, ref_reg_keys, input_files["tsl24_registration_legacy"].name)
    reg25_graphql = legacy_registration_to_graphql(reg25_raw, ref_reg_keys, input_files["tsl25_registration_legacy"].name)
    demo24_graphql = legacy_demographics_to_graphql(demo24_raw, ref_demo_keys, input_files["tsl24_demographics_legacy"].name)
    demo25_graphql = legacy_demographics_to_graphql(demo25_raw, ref_demo_keys, input_files["tsl25_demographics_legacy"].name)
    resequence(reg24_graphql, "registration_seq")
    resequence(reg25_graphql, "registration_seq")
    resequence(demo24_graphql, "demographics_seq")
    resequence(demo25_graphql, "demographics_seq")

    # Process 2026 registration/demographics (GraphQL target)
    reg26_raw = load_json_array(input_files["tsl26_registration"])
    reg26_graphql = transform_registration(reg26_raw, ref_reg_keys, "TSL26", input_files["tsl26_registration"].name)
    resequence(reg26_graphql, "registration_seq")
    validate_against_reference(reg26_graphql, [k for k in ref_reg_keys if k != "show_ref"], "TSL26 registration", allow_extra=["show_ref"])
    ensure_registration_processor_compatibility(
        reg26_graphql,
        ["id", "forename", "surname", "email", "company", "job_title", "badge_type", "badge_id", "reg_code", "source", "attended", "show_ref"],
        "TSL26 registration",
    )

    demo26_raw = load_json_array(input_files["tsl26_demographics"])
    demo26_graphql = transform_nested_demographics(demo26_raw, ref_demo_keys, "TSL26", input_files["tsl26_demographics"].name)
    resequence(demo26_graphql, "demographics_seq")
    validate_against_reference(demo26_graphql, ref_demo_keys, "TSL26 demographics")
    ensure_registration_processor_compatibility(
        demo26_graphql,
        ["badge_id", "question_text", "answer_text", "show_ref", "metadata_source_filename"],
        "TSL26 demographics",
    )

    # GraphQL outputs per requirement
    main_reg = _copy_records(reg25_graphql) + _copy_records(reg26_graphql)
    resequence(main_reg, "registration_seq")
    save_json_array(output_files["main_registration"], main_reg)
    LOGGER.info("Saved %s records to %s", len(main_reg), output_files["main_registration"].name)

    main_demo = _copy_records(demo25_graphql) + _copy_records(demo26_graphql)
    resequence(main_demo, "demographics_seq")
    save_json_array(output_files["main_demographics"], main_demo)
    LOGGER.info("Saved %s records to %s", len(main_demo), output_files["main_demographics"].name)

    secondary_reg = _copy_records(reg24_graphql)
    resequence(secondary_reg, "registration_seq")
    save_json_array(output_files["secondary_registration"], secondary_reg)
    LOGGER.info("Saved %s records to %s", len(secondary_reg), output_files["secondary_registration"].name)

    secondary_demo = _copy_records(demo24_graphql)
    resequence(secondary_demo, "demographics_seq")
    save_json_array(output_files["secondary_demographics"], secondary_demo)
    LOGGER.info("Saved %s records to %s", len(secondary_demo), output_files["secondary_demographics"].name)

    if include_legacy:
        LOGGER.info("Generating legacy-format datasets")
        reg26_legacy = convert_registration_to_legacy(reg26_graphql)
        demo26_legacy = convert_demographics_to_legacy(demo26_graphql)

        save_json_array(legacy_output_files["tsl26_registration"], reg26_legacy)
        save_json_array(legacy_output_files["tsl26_demographics"], demo26_legacy)

        main_reg_legacy = convert_registration_to_legacy(_copy_records(reg25_graphql) + _copy_records(reg26_graphql))
        save_json_array(legacy_output_files["main_registration"], main_reg_legacy)

        main_demo_legacy = _copy_records(demo25_raw) + demo26_legacy
        save_json_array(legacy_output_files["main_demographics"], main_demo_legacy)

        secondary_reg_legacy = convert_registration_to_legacy(_copy_records(reg24_graphql))
        save_json_array(legacy_output_files["secondary_registration"], secondary_reg_legacy)

        secondary_demo_legacy = _copy_records(demo24_raw)
        save_json_array(legacy_output_files["secondary_demographics"], secondary_demo_legacy)

    LOGGER.info("Transformation completed successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize Tech Show London registration datasets")
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Also emit datasets using the legacy schema expected when old_format=true",
    )
    parser.add_argument(
        "--tsl26-registration",
        type=str,
        default=None,
        help="Optional path to TSL26 registration input JSON (overrides default 20260120 file)",
    )
    parser.add_argument(
        "--tsl26-demographics",
        type=str,
        default=None,
        help="Optional path to TSL26 demographics input JSON (overrides default 20260120 file)",
    )
    parser.add_argument(
        "--tsl24-registration-legacy",
        type=str,
        default=None,
        help="Optional path to TSL24 legacy registration input (default: Reg_Tech_Lnd_24.json)",
    )
    parser.add_argument(
        "--tsl24-demographics-legacy",
        type=str,
        default=None,
        help="Optional path to TSL24 legacy demographics input (default: Demographics_Tech_Lnd_24.json)",
    )
    parser.add_argument(
        "--tsl25-registration-legacy",
        type=str,
        default=None,
        help="Optional path to TSL25 legacy registration input (default: Reg_Tech_Lnd_25.json)",
    )
    parser.add_argument(
        "--tsl25-demographics-legacy",
        type=str,
        default=None,
        help="Optional path to TSL25 legacy demographics input (default: Demographics_Tech_Lnd_25.json)",
    )
    parser.add_argument(
        "--output-prefix",
        type=str,
        default=None,
        help="Output filename prefix (default: current UTC date YYYYMMDD)",
    )
    args = parser.parse_args()
    main(
        include_legacy=args.legacy,
        tsl26_registration_path=args.tsl26_registration,
        tsl26_demographics_path=args.tsl26_demographics,
        tsl24_registration_legacy_path=args.tsl24_registration_legacy,
        tsl24_demographics_legacy_path=args.tsl24_demographics_legacy,
        tsl25_registration_legacy_path=args.tsl25_registration_legacy,
        tsl25_demographics_legacy_path=args.tsl25_demographics_legacy,
        output_prefix=args.output_prefix,
    )
