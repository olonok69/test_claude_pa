#!/usr/bin/env python3
"""One-time fixer for legacy CampaignDelivery control status.

Purpose:
- For a given legacy run_id (default: legacy_pre_traceability), set all delivery rows to `sent`
  and then set control visitors from a control file to `withheld_control`.

Supports control file formats:
- recommendations as object keyed by visitor_id
- recommendations as list of records with `visitor_id`/`BadgeId`/`badge_id`

Idempotent and safe to rerun.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Set

import ijson
from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

CURRENT_FILE = Path(__file__).resolve()
PA_ROOT = CURRENT_FILE.parents[1]
REPO_ROOT = PA_ROOT.parent
if str(PA_ROOT) not in sys.path:
    sys.path.insert(0, str(PA_ROOT))

from utils.config_utils import load_config
from utils.neo4j_utils import resolve_neo4j_credentials

LOGGER = logging.getLogger("fix_legacy_delivery_status")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def resolve_env_file_path(config_path: Path, env_file_value: str) -> Optional[Path]:
    env_file_value = _str(env_file_value)
    if not env_file_value:
        return None

    env_path = Path(env_file_value)
    if env_path.is_absolute():
        return env_path if env_path.exists() else None

    candidates = [
        Path.cwd() / env_path,
        config_path.parent / env_path,
        PA_ROOT / env_path,
        REPO_ROOT / env_path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def load_control_visitor_ids(control_json_path: Path) -> Set[str]:
    if not control_json_path.exists():
        raise FileNotFoundError(f"Control file not found: {control_json_path}")

    visitor_ids: Set[str] = set()
    with control_json_path.open("rb") as handle:
        shape = ""
        for prefix, event, _ in ijson.parse(handle):
            if prefix == "recommendations" and event == "start_map":
                shape = "map"
                break
            if prefix == "recommendations" and event == "start_array":
                shape = "array"
                break

    if shape == "map":
        with control_json_path.open("rb") as handle:
            for prefix, event, value in ijson.parse(handle):
                if prefix == "recommendations" and event == "map_key":
                    visitor_id = _str(value)
                    if visitor_id:
                        visitor_ids.add(visitor_id)
    elif shape == "array":
        with control_json_path.open("rb") as handle:
            for item in ijson.items(handle, "recommendations.item"):
                if not isinstance(item, dict):
                    continue
                visitor_id = _str(
                    item.get("visitor_id")
                    or item.get("BadgeId")
                    or item.get("badge_id")
                    or ((item.get("visitor") or {}).get("BadgeId") if isinstance(item.get("visitor"), dict) else "")
                )
                if visitor_id:
                    visitor_ids.add(visitor_id)
    else:
        raise ValueError(
            f"Unsupported control file format in {control_json_path}: expected recommendations map or array"
        )

    return visitor_ids


def scalar(session, query: str, params: Dict[str, Any]) -> int:
    record = session.run(query, params).single()
    if not record:
        return 0
    return int(record.get("value", 0) or 0)


def batch_set_withheld(
    driver: Driver,
    run_id: str,
    visitor_ids: Set[str],
    timestamp: str,
    batch_size: int,
    dry_run: bool,
) -> int:
    if not visitor_ids:
        return 0

    if dry_run:
        query = """
        UNWIND $badge_ids AS badge_id
        MATCH (d:CampaignDelivery {run_id: $run_id, visitor_id: badge_id})
        RETURN count(d) AS value
        """
    else:
        query = """
        UNWIND $badge_ids AS badge_id
        MATCH (d:CampaignDelivery {run_id: $run_id, visitor_id: badge_id})
        SET d.status = 'withheld_control',
            d.updated_at = $timestamp
        RETURN count(d) AS value
        """

    total = 0
    sorted_ids = sorted(visitor_ids)
    with driver.session() as session:
        for i in range(0, len(sorted_ids), batch_size):
            batch = sorted_ids[i : i + batch_size]
            total += scalar(
                session,
                query,
                {
                    "run_id": run_id,
                    "badge_ids": batch,
                    "timestamp": timestamp,
                },
            )
    return total


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fix legacy CampaignDelivery control statuses")
    parser.add_argument("--config", default="PA/config/config_tsl.yaml", help="Path to YAML config")
    parser.add_argument(
        "--control-json",
        required=True,
        help="Control visitors JSON file used to set withheld_control status",
    )
    parser.add_argument(
        "--run-id",
        default="legacy_pre_traceability",
        help="Run ID to update",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=2000,
        help="Batch size for updates",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show counts only; do not write changes",
    )
    parser.add_argument(
        "--report-file",
        default="large_tool_results/fix_legacy_delivery_status_report.json",
        help="Output report path",
    )
    return parser


def main() -> None:
    configure_logging()
    args = build_parser().parse_args()

    config_path = Path(args.config)
    config = load_config(str(config_path))

    env_file_path = resolve_env_file_path(config_path, config.get("env_file", ""))
    if env_file_path:
        load_dotenv(env_file_path)
        LOGGER.info("Loaded environment file: %s", env_file_path)
    else:
        load_dotenv()

    control_ids = load_control_visitor_ids(Path(args.control_json))

    credentials = resolve_neo4j_credentials(config, logger=LOGGER)
    driver = GraphDatabase.driver(
        credentials["uri"],
        auth=(credentials["username"], credentials["password"]),
    )

    started_at = utc_now_iso()
    timestamp = utc_now_iso()

    report: Dict[str, Any] = {
        "started_at": started_at,
        "dry_run": bool(args.dry_run),
        "run_id": args.run_id,
        "control_json": args.control_json,
        "control_visitors_in_file": len(control_ids),
    }

    try:
        with driver.session() as session:
            before_sent = scalar(
                session,
                """
                MATCH (d:CampaignDelivery {run_id: $run_id, status: 'sent'})
                RETURN count(d) AS value
                """,
                {"run_id": args.run_id},
            )
            before_withheld = scalar(
                session,
                """
                MATCH (d:CampaignDelivery {run_id: $run_id, status: 'withheld_control'})
                RETURN count(d) AS value
                """,
                {"run_id": args.run_id},
            )
            total_run = scalar(
                session,
                """
                MATCH (d:CampaignDelivery {run_id: $run_id})
                RETURN count(d) AS value
                """,
                {"run_id": args.run_id},
            )

        report["before"] = {
            "total_deliveries": total_run,
            "sent": before_sent,
            "withheld_control": before_withheld,
        }

        if args.dry_run:
            would_reset_to_sent = total_run
            would_set_withheld = batch_set_withheld(
                driver,
                run_id=args.run_id,
                visitor_ids=control_ids,
                timestamp=timestamp,
                batch_size=int(args.batch_size),
                dry_run=True,
            )
            report["actions"] = {
                "would_reset_to_sent": would_reset_to_sent,
                "would_set_withheld_control": would_set_withheld,
            }
        else:
            with driver.session() as session:
                reset_count = scalar(
                    session,
                    """
                    MATCH (d:CampaignDelivery {run_id: $run_id})
                    SET d.status = 'sent',
                        d.updated_at = $timestamp
                    RETURN count(d) AS value
                    """,
                    {"run_id": args.run_id, "timestamp": timestamp},
                )

            set_withheld_count = batch_set_withheld(
                driver,
                run_id=args.run_id,
                visitor_ids=control_ids,
                timestamp=timestamp,
                batch_size=int(args.batch_size),
                dry_run=False,
            )

            report["actions"] = {
                "reset_to_sent": reset_count,
                "set_withheld_control": set_withheld_count,
            }

        with driver.session() as session:
            after_sent = scalar(
                session,
                """
                MATCH (d:CampaignDelivery {run_id: $run_id, status: 'sent'})
                RETURN count(d) AS value
                """,
                {"run_id": args.run_id},
            )
            after_withheld = scalar(
                session,
                """
                MATCH (d:CampaignDelivery {run_id: $run_id, status: 'withheld_control'})
                RETURN count(d) AS value
                """,
                {"run_id": args.run_id},
            )

        report["after"] = {
            "sent": after_sent,
            "withheld_control": after_withheld,
        }
        report["finished_at"] = utc_now_iso()

        report_path = Path(args.report_file)
        if not report_path.is_absolute():
            report_path = REPO_ROOT / report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        print(json.dumps(report, indent=2))
        LOGGER.info("Fix report written to %s", report_path)

    finally:
        driver.close()


if __name__ == "__main__":
    main()
