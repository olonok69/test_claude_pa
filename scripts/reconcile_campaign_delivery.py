#!/usr/bin/env python3
"""M5 reconciliation: output files vs Neo4j CampaignDelivery ledger.

Checks (read-only):
- Visitor set parity between exported recommendation files and CampaignDelivery nodes for a run.
- Status parity (`sent` vs `withheld_control`) per visitor.
- Optional campaign/show consistency checks.
- Delivery link integrity (`FOR_VISITOR`, `FOR_RUN`).

Produces a JSON reconciliation report for audit.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase
import ijson

CURRENT_FILE = Path(__file__).resolve()
PA_ROOT = CURRENT_FILE.parents[1]
REPO_ROOT = PA_ROOT.parent
if str(PA_ROOT) not in sys.path:
    sys.path.insert(0, str(PA_ROOT))

from utils.config_utils import load_config
from utils.neo4j_utils import resolve_neo4j_credentials

LOGGER = logging.getLogger("m5_delivery_reconciliation")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


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


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_recommendation_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Recommendation file not found: {path}")

    metadata: Dict[str, Any] = {}
    dataset = ""
    visitor_ids: Set[str] = set()
    recommendations_shape = ""

    with path.open("rb") as handle:
        parser = ijson.parse(handle)
        for prefix, event, value in parser:
            if prefix == "dataset" and event in {"string", "number", "boolean", "null"}:
                dataset = _str(value).lower()
            elif prefix == "recommendations" and event == "start_map":
                recommendations_shape = "map"
                break
            elif prefix == "recommendations" and event == "start_array":
                recommendations_shape = "array"
                break

    if recommendations_shape == "map":
        with path.open("rb") as handle:
            for prefix, event, value in ijson.parse(handle):
                if prefix == "recommendations" and event == "map_key":
                    visitor_id = _str(value)
                    if visitor_id:
                        visitor_ids.add(visitor_id)
    elif recommendations_shape == "array":
        with path.open("rb") as handle:
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
            f"Invalid recommendations structure in {path}: expected recommendations as object or array"
        )

    default_status = "withheld_control" if "control" in dataset else "sent"

    return {
        "path": str(path),
        "metadata": metadata,
        "dataset": dataset,
        "default_status": default_status,
        "visitor_ids": visitor_ids,
        "visitor_count": len(visitor_ids),
    }


def resolve_run_context(
    main_file_data: Dict[str, Any],
    run_id_override: str,
    campaign_id_override: str,
    show_override: str,
) -> Dict[str, str]:
    metadata = main_file_data.get("metadata", {}) or {}
    traceability = metadata.get("traceability", {}) or {}

    run_id = _str(run_id_override) or _str(traceability.get("run_id"))
    campaign_id = _str(campaign_id_override) or _str(traceability.get("campaign_id"))
    show = _str(show_override) or _str(traceability.get("show")) or _str(metadata.get("show"))

    if not run_id:
        raise ValueError(
            "Unable to resolve run_id. Provide --run-id or ensure metadata.traceability.run_id exists in main JSON."
        )

    return {
        "run_id": run_id,
        "campaign_id": campaign_id,
        "show": show,
    }


def fetch_delivery_rows(driver: Driver, run_id: str) -> List[Dict[str, str]]:
    query = """
    MATCH (d:CampaignDelivery {run_id: $run_id})
    RETURN
      d.delivery_id AS delivery_id,
      d.visitor_id AS visitor_id,
      d.status AS status,
      d.campaign_id AS campaign_id,
      d.run_mode AS run_mode,
      d.show AS show
    """

    rows: List[Dict[str, str]] = []
    with driver.session() as session:
        result = session.run(query, {"run_id": run_id})
        for record in result:
            rows.append(
                {
                    "delivery_id": _str(record.get("delivery_id")),
                    "visitor_id": _str(record.get("visitor_id")),
                    "status": _str(record.get("status")),
                    "campaign_id": _str(record.get("campaign_id")),
                    "run_mode": _str(record.get("run_mode")),
                    "show": _str(record.get("show")),
                }
            )
    return rows


def fetch_integrity_counts(driver: Driver, run_id: str) -> Dict[str, int]:
    queries = {
        "deliveries_without_for_visitor": """
            MATCH (d:CampaignDelivery {run_id: $run_id})
            WHERE NOT EXISTS { MATCH (d)-[:FOR_VISITOR]->(:Visitor_this_year) }
            RETURN count(d) AS value
        """,
        "deliveries_without_for_run": """
            MATCH (d:CampaignDelivery {run_id: $run_id})
            WHERE NOT EXISTS { MATCH (d)-[:FOR_RUN]->(:RecommendationRun {run_id: $run_id}) }
            RETURN count(d) AS value
        """,
    }

    counts: Dict[str, int] = {}
    with driver.session() as session:
        for key, query in queries.items():
            record = session.run(query, {"run_id": run_id}).single()
            counts[key] = int(record.get("value", 0) if record else 0)
    return counts


def build_expected_status_map(
    main_visitors: Set[str],
    control_visitors: Set[str],
    main_default_status: str = "sent",
) -> Tuple[Dict[str, str], List[str]]:
    overlap = sorted(main_visitors & control_visitors)

    expected: Dict[str, str] = {}
    for visitor_id in main_visitors:
        expected[visitor_id] = main_default_status
    for visitor_id in control_visitors:
        expected[visitor_id] = "withheld_control"

    return expected, overlap


def summarize_db_rows(rows: List[Dict[str, str]]) -> Tuple[Dict[str, str], Dict[str, int], List[str]]:
    by_visitor: Dict[str, str] = {}
    duplicates: List[str] = []
    status_counts: Dict[str, int] = {}

    seen: Set[str] = set()
    for row in rows:
        visitor_id = _str(row.get("visitor_id"))
        status = _str(row.get("status"))
        if not visitor_id:
            continue

        status_counts[status or "<missing>"] = status_counts.get(status or "<missing>", 0) + 1

        if visitor_id in seen:
            duplicates.append(visitor_id)
            continue

        seen.add(visitor_id)
        by_visitor[visitor_id] = status

    return by_visitor, status_counts, sorted(set(duplicates))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reconcile output recommendation files with CampaignDelivery")
    parser.add_argument("--config", default="PA/config/config_tsl.yaml", help="Path to YAML config")
    parser.add_argument("--main-json", required=True, help="Path to main recommendations JSON file")
    parser.add_argument("--control-json", default="", help="Path to control recommendations JSON file (optional)")
    parser.add_argument("--run-id", default="", help="Override run_id (if not present in JSON metadata)")
    parser.add_argument("--campaign-id", default="", help="Expected campaign_id (optional)")
    parser.add_argument("--show", default="", help="Expected show (optional)")
    parser.add_argument(
        "--env-file",
        default="",
        help="Optional explicit path to .env file (overrides config env_file resolution)",
    )
    parser.add_argument(
        "--report-file",
        default="large_tool_results/m5_delivery_reconciliation_report.json",
        help="Output report JSON path",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=25,
        help="Max sample size per mismatch category in report",
    )
    parser.add_argument(
        "--fail-on-mismatch",
        action="store_true",
        help="Exit non-zero when mismatches are detected",
    )
    return parser


def main() -> None:
    configure_logging()
    args = build_parser().parse_args()

    config_path = Path(args.config)
    config = load_config(str(config_path))

    env_file_path = None
    if _str(args.env_file):
        explicit_env_path = Path(args.env_file)
        if explicit_env_path.is_absolute() and explicit_env_path.exists():
            env_file_path = explicit_env_path
        else:
            explicit_candidates = [
                Path.cwd() / explicit_env_path,
                PA_ROOT / explicit_env_path,
                REPO_ROOT / explicit_env_path,
            ]
            for candidate in explicit_candidates:
                if candidate.exists():
                    env_file_path = candidate
                    break
        if env_file_path is None:
            raise FileNotFoundError(f"Explicit env file not found: {args.env_file}")
    else:
        env_file_path = resolve_env_file_path(config_path, config.get("env_file", ""))
    if env_file_path:
        load_dotenv(env_file_path)
        LOGGER.info("Loaded environment file: %s", env_file_path)
    else:
        load_dotenv()

    main_file = load_recommendation_file(Path(args.main_json))
    control_file = (
        load_recommendation_file(Path(args.control_json))
        if _str(args.control_json)
        else {"path": "", "metadata": {}, "visitor_ids": set(), "visitor_count": 0}
    )

    run_context = resolve_run_context(
        main_file,
        run_id_override=args.run_id,
        campaign_id_override=args.campaign_id,
        show_override=args.show,
    )

    expected_status_map, file_overlap = build_expected_status_map(
        main_visitors=main_file["visitor_ids"],
        control_visitors=control_file["visitor_ids"],
        main_default_status=main_file.get("default_status", "sent"),
    )

    credentials = resolve_neo4j_credentials(config, logger=LOGGER)
    driver = GraphDatabase.driver(
        credentials["uri"],
        auth=(credentials["username"], credentials["password"]),
    )

    try:
        rows = fetch_delivery_rows(driver, run_context["run_id"])
        integrity = fetch_integrity_counts(driver, run_context["run_id"])
    finally:
        driver.close()

    db_status_by_visitor, db_status_counts, duplicate_delivery_visitors = summarize_db_rows(rows)

    expected_ids = set(expected_status_map.keys())
    db_ids = set(db_status_by_visitor.keys())

    missing_in_neo4j = sorted(expected_ids - db_ids)
    extra_in_neo4j = sorted(db_ids - expected_ids)

    status_mismatches: List[Dict[str, str]] = []
    for visitor_id in sorted(expected_ids & db_ids):
        expected_status = expected_status_map.get(visitor_id, "")
        observed_status = db_status_by_visitor.get(visitor_id, "")
        if expected_status != observed_status:
            status_mismatches.append(
                {
                    "visitor_id": visitor_id,
                    "expected_status": expected_status,
                    "observed_status": observed_status,
                }
            )

    campaign_mismatches = []
    show_mismatches = []
    expected_campaign = _str(run_context.get("campaign_id"))
    expected_show = _str(run_context.get("show"))

    for row in rows:
        visitor_id = _str(row.get("visitor_id"))
        if expected_campaign and _str(row.get("campaign_id")) != expected_campaign:
            campaign_mismatches.append(
                {
                    "visitor_id": visitor_id,
                    "observed_campaign_id": _str(row.get("campaign_id")),
                    "expected_campaign_id": expected_campaign,
                }
            )
        if expected_show and _str(row.get("show")) != expected_show:
            show_mismatches.append(
                {
                    "visitor_id": visitor_id,
                    "observed_show": _str(row.get("show")),
                    "expected_show": expected_show,
                }
            )

    mismatch_total = (
        len(file_overlap)
        + len(missing_in_neo4j)
        + len(extra_in_neo4j)
        + len(status_mismatches)
        + len(duplicate_delivery_visitors)
        + len(campaign_mismatches)
        + len(show_mismatches)
        + int(integrity.get("deliveries_without_for_visitor", 0))
        + int(integrity.get("deliveries_without_for_run", 0))
    )

    sample_size = max(0, int(args.sample_size))
    report: Dict[str, Any] = {
        "generated_at": utc_now_iso(),
        "run_context": run_context,
        "inputs": {
            "main_json": main_file["path"],
            "control_json": control_file["path"],
            "main_visitors": int(main_file["visitor_count"]),
            "control_visitors": int(control_file["visitor_count"]),
            "expected_total_visitors": len(expected_ids),
        },
        "neo4j": {
            "delivery_nodes_for_run": len(rows),
            "unique_delivery_visitors": len(db_ids),
            "status_counts": db_status_counts,
            "integrity": integrity,
        },
        "reconciliation": {
            "ok": mismatch_total == 0,
            "mismatch_total": mismatch_total,
            "file_overlap_count": len(file_overlap),
            "missing_in_neo4j_count": len(missing_in_neo4j),
            "extra_in_neo4j_count": len(extra_in_neo4j),
            "status_mismatch_count": len(status_mismatches),
            "duplicate_delivery_visitor_count": len(duplicate_delivery_visitors),
            "campaign_mismatch_count": len(campaign_mismatches),
            "show_mismatch_count": len(show_mismatches),
            "samples": {
                "file_overlap": file_overlap[:sample_size],
                "missing_in_neo4j": missing_in_neo4j[:sample_size],
                "extra_in_neo4j": extra_in_neo4j[:sample_size],
                "status_mismatches": status_mismatches[:sample_size],
                "duplicate_delivery_visitors": duplicate_delivery_visitors[:sample_size],
                "campaign_mismatches": campaign_mismatches[:sample_size],
                "show_mismatches": show_mismatches[:sample_size],
            },
        },
    }

    report_path = Path(args.report_file)
    if not report_path.is_absolute():
        report_path = REPO_ROOT / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    LOGGER.info("M5 reconciliation report written to %s", report_path)

    if args.fail_on_mismatch and mismatch_total > 0:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
