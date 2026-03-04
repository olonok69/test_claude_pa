#!/usr/bin/env python3
"""Reconcile definitive control group across Neo4j and recommendation exports.

Inputs (defaults match current TSL files):
- Definitive control list CSV (badge_id column)
- Existing recommendation/control CSV exports
- Existing recommendation/control JSON exports
- Existing recommendation/control unified JSON exports

Outputs (new files, originals kept):
- Reconciled main/control CSV
- Reconciled main/control JSON
- Reconciled unified main/control JSON
- Reconciliation report JSON
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import ijson
from dotenv import load_dotenv
from neo4j import GraphDatabase


CURRENT_FILE = Path(__file__).resolve()
PA_ROOT = CURRENT_FILE.parents[1]
if str(PA_ROOT) not in sys.path:
    sys.path.insert(0, str(PA_ROOT))

from utils.config_utils import load_config
from utils.neo4j_utils import resolve_neo4j_credentials


LOGGER = logging.getLogger("control_group_reconciler")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def chunked(items: List[str], size: int) -> Iterable[List[str]]:
    step = max(1, size)
    for idx in range(0, len(items), step):
        yield items[idx : idx + step]


def _str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    if isinstance(value, dict):
        return {k: normalize_json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_json_value(v) for v in value]
    return value


def resolve_env_file_path(config_path: Path, env_file_value: str) -> Optional[Path]:
    env_file_value = _str(env_file_value)
    if not env_file_value:
        return None

    candidate = Path(env_file_value)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    for path in [
        Path.cwd() / candidate,
        config_path.parent / candidate,
        PA_ROOT / candidate,
        PA_ROOT.parent / candidate,
    ]:
        if path.exists():
            return path
    return None


def load_control_ids(control_csv: Path) -> Set[str]:
    if not control_csv.exists():
        raise FileNotFoundError(f"Control group file not found: {control_csv}")

    control_ids: Set[str] = set()
    with control_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            control_id = _str(
                row.get("badge_id")
                or row.get("badgeID")
                or row.get("BadgeId")
                or row.get("visitor_id")
            )
            if control_id:
                control_ids.add(control_id)
    return control_ids


def reconcile_csv(
    main_csv: Path,
    control_csv: Path,
    control_ids: Set[str],
    out_main_csv: Path,
    out_control_csv: Path,
) -> Dict[str, Any]:
    def read_rows(path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            rows = list(reader)
        return rows, fieldnames

    main_rows, main_fields = read_rows(main_csv)
    control_rows, control_fields = read_rows(control_csv)
    fieldnames = main_fields or control_fields

    merged_rows = main_rows + control_rows
    seen_pairs: Set[Tuple[str, str]] = set()
    split_main: List[Dict[str, Any]] = []
    split_control: List[Dict[str, Any]] = []

    for row in merged_rows:
        visitor_id = _str(row.get("visitor_id"))
        session_id = _str(row.get("session_id"))
        key = (visitor_id, session_id)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)

        if visitor_id in control_ids:
            split_control.append(row)
        else:
            split_main.append(row)

    out_main_csv.parent.mkdir(parents=True, exist_ok=True)
    out_control_csv.parent.mkdir(parents=True, exist_ok=True)

    with out_main_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(split_main)

    with out_control_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(split_control)

    main_unique_visitors = { _str(row.get("visitor_id")) for row in split_main if _str(row.get("visitor_id")) }
    control_unique_visitors = { _str(row.get("visitor_id")) for row in split_control if _str(row.get("visitor_id")) }

    return {
        "rows_main": len(split_main),
        "rows_control": len(split_control),
        "unique_visitors_main": len(main_unique_visitors),
        "unique_visitors_control": len(control_unique_visitors),
    }


def stream_split_regular_json(
    main_json: Path,
    control_json: Path,
    control_ids: Set[str],
    out_main_json: Path,
    out_control_json: Path,
) -> Dict[str, Any]:
    out_main_json.parent.mkdir(parents=True, exist_ok=True)
    out_control_json.parent.mkdir(parents=True, exist_ok=True)

    seen_main: Set[str] = set()
    seen_control: Set[str] = set()
    main_count = 0
    control_count = 0

    metadata_payload = {
        "generated_at": now_iso(),
        "reconciled": True,
        "control_source": "definitive_control_group_csv",
        "source_files": [str(main_json), str(control_json)],
    }

    with out_main_json.open("w", encoding="utf-8") as f_main, out_control_json.open("w", encoding="utf-8") as f_control:
        f_main.write('{"metadata":')
        f_main.write(json.dumps(metadata_payload, ensure_ascii=False))
        f_main.write(',"recommendations":{')

        f_control.write('{"metadata":')
        f_control.write(json.dumps(metadata_payload, ensure_ascii=False))
        f_control.write(',"recommendations":{')

        first_main = True
        first_control = True

        for source_file in [main_json, control_json]:
            with source_file.open("rb") as handle:
                for visitor_id, payload in ijson.kvitems(handle, "recommendations"):
                    vid = _str(visitor_id)
                    if not vid:
                        continue
                    payload = normalize_json_value(payload)

                    if vid in control_ids:
                        if vid in seen_control:
                            continue
                        if not first_control:
                            f_control.write(',')
                        first_control = False
                        f_control.write(json.dumps(vid, ensure_ascii=False))
                        f_control.write(':')
                        f_control.write(json.dumps(payload, ensure_ascii=False))
                        seen_control.add(vid)
                        control_count += 1
                    else:
                        if vid in seen_main:
                            continue
                        if not first_main:
                            f_main.write(',')
                        first_main = False
                        f_main.write(json.dumps(vid, ensure_ascii=False))
                        f_main.write(':')
                        f_main.write(json.dumps(payload, ensure_ascii=False))
                        seen_main.add(vid)
                        main_count += 1

        f_main.write('},"statistics":')
        f_main.write(
            json.dumps(
                {
                    "reconciled_at": now_iso(),
                    "visitors": main_count,
                    "split": "main",
                },
                ensure_ascii=False,
            )
        )
        f_main.write('}')

        f_control.write('},"statistics":')
        f_control.write(
            json.dumps(
                {
                    "reconciled_at": now_iso(),
                    "visitors": control_count,
                    "split": "control",
                },
                ensure_ascii=False,
            )
        )
        f_control.write('}')

    return {
        "regular_json_visitors_main": main_count,
        "regular_json_visitors_control": control_count,
    }


def stream_split_unified_json(
    main_unified_json: Path,
    control_unified_json: Path,
    control_ids: Set[str],
    out_main_unified_json: Path,
    out_control_unified_json: Path,
) -> Dict[str, Any]:
    def collect(path: Path, target_main: Dict[str, Dict[str, Any]], target_control: Dict[str, Dict[str, Any]]) -> None:
        with path.open("rb") as handle:
            for item in ijson.items(handle, "recommendations.item"):
                if not isinstance(item, dict):
                    continue
                item = normalize_json_value(item)
                visitor_id = _str(item.get("visitor_id"))
                if not visitor_id:
                    continue
                if visitor_id in control_ids:
                    target_control.setdefault(visitor_id, item)
                else:
                    target_main.setdefault(visitor_id, item)

    merged_main: Dict[str, Dict[str, Any]] = {}
    merged_control: Dict[str, Dict[str, Any]] = {}
    collect(main_unified_json, merged_main, merged_control)
    collect(control_unified_json, merged_main, merged_control)

    payload_main = {
        "generated_at": now_iso(),
        "dataset": "recommendations_reconciled",
        "recommendations": [merged_main[k] for k in sorted(merged_main.keys())],
        "metadata": {
            "reconciled": True,
            "source_files": [str(main_unified_json), str(control_unified_json)],
        },
    }
    payload_control = {
        "generated_at": now_iso(),
        "dataset": "control_reconciled",
        "recommendations": [merged_control[k] for k in sorted(merged_control.keys())],
        "metadata": {
            "reconciled": True,
            "source_files": [str(main_unified_json), str(control_unified_json)],
        },
    }

    out_main_unified_json.parent.mkdir(parents=True, exist_ok=True)
    out_control_unified_json.parent.mkdir(parents=True, exist_ok=True)
    with out_main_unified_json.open("w", encoding="utf-8") as handle:
        json.dump(payload_main, handle, ensure_ascii=False, indent=2)
    with out_control_unified_json.open("w", encoding="utf-8") as handle:
        json.dump(payload_control, handle, ensure_ascii=False, indent=2)

    return {
        "unified_visitors_main": len(payload_main["recommendations"]),
        "unified_visitors_control": len(payload_control["recommendations"]),
    }


def reconcile_neo4j(
    config: Dict[str, Any],
    control_ids: Set[str],
    batch_size: int,
    apply_changes: bool,
) -> Dict[str, Any]:
    credentials = resolve_neo4j_credentials(config, logger=LOGGER)
    uri = credentials["uri"]
    username = credentials["username"]
    password = credentials["password"]

    neo4j_cfg = config.get("neo4j", {}) or {}
    labels = neo4j_cfg.get("node_labels", {}) or {}
    visitor_label = labels.get("visitor_this_year", "Visitor_this_year")
    show_name = _str(neo4j_cfg.get("show_name"))

    driver = GraphDatabase.driver(uri, auth=(username, password))
    stats = {
        "neo4j_uri": uri,
        "visitor_label": visitor_label,
        "show_name": show_name,
        "control_ids_total": len(control_ids),
        "control_ids_found": 0,
        "control_ids_missing": 0,
        "control_ids_missing_sample": [],
        "reset_to_non_control": 0,
        "set_to_control": 0,
        "applied": apply_changes,
    }

    try:
        existing: Set[str] = set()
        query_find = f"""
        UNWIND $badge_ids AS badge_id
        MATCH (v:{visitor_label} {{BadgeId: badge_id}})
        WHERE ($show_name = '' OR coalesce(v.show,'') = $show_name)
        RETURN badge_id
        """
        with driver.session() as session:
            for batch in chunked(sorted(control_ids), batch_size):
                result = session.run(query_find, {"badge_ids": batch, "show_name": show_name})
                for rec in result:
                    existing.add(_str(rec.get("badge_id")))

        missing = sorted(control_ids - existing)
        stats["control_ids_found"] = len(existing)
        stats["control_ids_missing"] = len(missing)
        stats["control_ids_missing_sample"] = missing[:50]

        if not apply_changes:
            return stats

        query_reset = f"""
        MATCH (v:{visitor_label})
        WHERE ($show_name = '' OR coalesce(v.show,'') = $show_name)
          AND coalesce(v.control_group, 0) <> 0
          AND NOT v.BadgeId IN $control_ids
        SET v.control_group = 0
        RETURN count(v) AS reset_count
        """
        query_set = f"""
        UNWIND $badge_ids AS badge_id
        MATCH (v:{visitor_label} {{BadgeId: badge_id}})
        WHERE ($show_name = '' OR coalesce(v.show,'') = $show_name)
        SET v.control_group = 1
        RETURN count(v) AS set_count
        """

        with driver.session() as session:
            reset_count = session.run(
                query_reset,
                {"control_ids": sorted(control_ids), "show_name": show_name},
            ).single()["reset_count"]
            stats["reset_to_non_control"] = int(reset_count)

            set_total = 0
            for batch in chunked(sorted(control_ids), batch_size):
                set_count = session.run(
                    query_set,
                    {"badge_ids": batch, "show_name": show_name},
                ).single()["set_count"]
                set_total += int(set_count)
            stats["set_to_control"] = set_total

    finally:
        driver.close()

    return stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reconcile TSL definitive control group")
    parser.add_argument("--config", default="PA/config/config_tsl.yaml")
    parser.add_argument(
        "--definitive-control-csv",
        default="PA/data/tsl/recommendations/control/20260217_exclusion_list_control_groups 1.csv",
    )
    parser.add_argument(
        "--main-csv",
        default="PA/data/tsl/recommendations/visitor_recommendations_tsl_20260214_144216.csv",
    )
    parser.add_argument(
        "--control-csv",
        default="PA/data/tsl/recommendations/control/visitor_recommendations_tsl_20260214_144216_control.csv",
    )
    parser.add_argument(
        "--main-json",
        default="PA/data/tsl/recommendations/visitor_recommendations_tsl_20260214_144216.json",
    )
    parser.add_argument(
        "--control-json",
        default="PA/data/tsl/recommendations/control/visitor_recommendations_tsl_20260214_144216_control.json",
    )
    parser.add_argument(
        "--main-unified-json",
        default="PA/data/tsl/recommendations/visitor_recommendations_tsl_20260214_144216_unified.json",
    )
    parser.add_argument(
        "--control-unified-json",
        default="PA/data/tsl/recommendations/visitor_recommendations_tsl_20260214_144216_control_unified.json",
    )
    parser.add_argument(
        "--output-main-csv",
        default="PA/data/tsl/recommendations/visitor_recommendations_tsl_20260214_144216_reconciled.csv",
    )
    parser.add_argument(
        "--output-control-csv",
        default="PA/data/tsl/recommendations/control/visitor_recommendations_tsl_20260214_144216_control_reconciled.csv",
    )
    parser.add_argument(
        "--output-main-json",
        default="PA/data/tsl/recommendations/visitor_recommendations_tsl_20260214_144216_reconciled.json",
    )
    parser.add_argument(
        "--output-control-json",
        default="PA/data/tsl/recommendations/control/visitor_recommendations_tsl_20260214_144216_control_reconciled.json",
    )
    parser.add_argument(
        "--output-main-unified-json",
        default="PA/data/tsl/recommendations/visitor_recommendations_tsl_20260214_144216_unified_reconciled.json",
    )
    parser.add_argument(
        "--output-control-unified-json",
        default="PA/data/tsl/recommendations/visitor_recommendations_tsl_20260214_144216_control_unified_reconciled.json",
    )
    parser.add_argument(
        "--report-json",
        default="PA/data/tsl/recommendations/control_group_reconciliation_report.json",
    )
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main() -> None:
    configure_logging()
    args = build_parser().parse_args()

    config_path = Path(args.config)
    config = load_config(str(config_path))
    env_file_path = resolve_env_file_path(config_path, config.get("env_file", ""))
    if env_file_path:
        load_dotenv(env_file_path)
        LOGGER.info("Loaded env file: %s", env_file_path)
    else:
        load_dotenv()

    control_ids = load_control_ids(Path(args.definitive_control_csv))
    LOGGER.info("Loaded definitive control IDs: %d", len(control_ids))

    csv_stats = reconcile_csv(
        main_csv=Path(args.main_csv),
        control_csv=Path(args.control_csv),
        control_ids=control_ids,
        out_main_csv=Path(args.output_main_csv),
        out_control_csv=Path(args.output_control_csv),
    )

    json_stats = stream_split_regular_json(
        main_json=Path(args.main_json),
        control_json=Path(args.control_json),
        control_ids=control_ids,
        out_main_json=Path(args.output_main_json),
        out_control_json=Path(args.output_control_json),
    )

    unified_stats = stream_split_unified_json(
        main_unified_json=Path(args.main_unified_json),
        control_unified_json=Path(args.control_unified_json),
        control_ids=control_ids,
        out_main_unified_json=Path(args.output_main_unified_json),
        out_control_unified_json=Path(args.output_control_unified_json),
    )

    neo4j_stats = reconcile_neo4j(
        config=config,
        control_ids=control_ids,
        batch_size=args.batch_size,
        apply_changes=not args.dry_run,
    )

    report = {
        "generated_at": now_iso(),
        "dry_run": bool(args.dry_run),
        "inputs": {
            "definitive_control_csv": args.definitive_control_csv,
            "main_csv": args.main_csv,
            "control_csv": args.control_csv,
            "main_json": args.main_json,
            "control_json": args.control_json,
            "main_unified_json": args.main_unified_json,
            "control_unified_json": args.control_unified_json,
        },
        "outputs": {
            "main_csv": args.output_main_csv,
            "control_csv": args.output_control_csv,
            "main_json": args.output_main_json,
            "control_json": args.output_control_json,
            "main_unified_json": args.output_main_unified_json,
            "control_unified_json": args.output_control_unified_json,
        },
        "definitive_control_ids": len(control_ids),
        "csv": csv_stats,
        "json": json_stats,
        "unified": unified_stats,
        "neo4j": neo4j_stats,
    }

    report_path = Path(args.report_json)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    print("Control group reconciliation completed")
    print(f"Report: {report_path}")
    print(f"Definitive control IDs: {len(control_ids)}")
    print(f"CSV main/control rows: {csv_stats['rows_main']}/{csv_stats['rows_control']}")
    print(
        "JSON visitors main/control:",
        f"{json_stats['regular_json_visitors_main']}/{json_stats['regular_json_visitors_control']}",
    )
    print(
        "Unified visitors main/control:",
        f"{unified_stats['unified_visitors_main']}/{unified_stats['unified_visitors_control']}",
    )
    print(
        "Neo4j found/missing control IDs:",
        f"{neo4j_stats['control_ids_found']}/{neo4j_stats['control_ids_missing']}",
    )
    if args.dry_run:
        print("Dry-run: Neo4j updates not applied")


if __name__ == "__main__":
    main()