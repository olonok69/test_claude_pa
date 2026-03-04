#!/usr/bin/env python3
"""One-time reconciliation for a specific recommendation run.

Compares generated main/control recommendation CSV files against Neo4j
CampaignDelivery records for a run_id and writes a JSON report.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from dotenv import load_dotenv
from neo4j import GraphDatabase


CURRENT_FILE = Path(__file__).resolve()
PA_ROOT = CURRENT_FILE.parents[1]
REPO_ROOT = PA_ROOT.parent
if str(PA_ROOT) not in sys.path:
    sys.path.insert(0, str(PA_ROOT))

from utils.config_utils import load_config
from utils.neo4j_utils import resolve_neo4j_credentials


LOGGER = logging.getLogger("one_time_delivery_reconciliation")


def _str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def read_expected_status_map(main_csv: Path, control_csv: Path) -> Tuple[Dict[str, str], Dict[str, int]]:
    expected: Dict[str, str] = {}
    main_rows = 0
    control_rows = 0

    def _visitor_id(row: Dict[str, Any]) -> str:
        return _str(row.get("visitor_id") or row.get("BadgeId") or row.get("badge_id"))

    with main_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            main_rows += 1
            visitor_id = _visitor_id(row)
            if visitor_id and visitor_id not in expected:
                expected[visitor_id] = "sent"

    with control_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            control_rows += 1
            visitor_id = _visitor_id(row)
            if visitor_id:
                expected[visitor_id] = "withheld_control"

    return expected, {
        "main_rows": main_rows,
        "control_rows": control_rows,
        "expected_unique_visitors": len(expected),
    }


def resolve_recommendation_csv_paths(
    provided_main_csv: str,
    provided_control_csv: str,
    run_id_input: str,
    show: str,
) -> Tuple[Path, Path]:
    """Resolve main/control CSV paths.

    Priority:
    1) Explicit arguments when both provided.
    2) Timestamp token in run_id_input: YYYYMMDD_HHMMSS.
    3) Most recent recommendation CSV pair for show.
    """

    if _str(provided_main_csv) and _str(provided_control_csv):
        main_csv = Path(provided_main_csv)
        control_csv = Path(provided_control_csv)
        if not main_csv.is_absolute():
            main_csv = Path.cwd() / main_csv
        if not control_csv.is_absolute():
            control_csv = Path.cwd() / control_csv
        return main_csv, control_csv

    base = Path.cwd() / "data" / "tsl" / "recommendations"
    control_base = base / "control"
    show = _str(show) or "tsl"

    token = _str(run_id_input)
    if re.match(r"^\d{8}_\d{6}$", token):
        candidate_main = base / f"visitor_recommendations_{show}_{token}.csv"
        candidate_control = control_base / f"visitor_recommendations_{show}_{token}_control.csv"
        if candidate_main.exists() and candidate_control.exists():
            return candidate_main, candidate_control

    main_candidates = sorted(
        base.glob(f"visitor_recommendations_{show}_*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for candidate_main in main_candidates:
        name = candidate_main.name
        if not name.startswith(f"visitor_recommendations_{show}_"):
            continue
        token_part = name.replace(f"visitor_recommendations_{show}_", "", 1).replace(".csv", "")
        candidate_control = control_base / f"visitor_recommendations_{show}_{token_part}_control.csv"
        if candidate_control.exists():
            return candidate_main, candidate_control

    raise FileNotFoundError(
        "Unable to resolve recommendation CSV files. "
        "Provide --main-csv and --control-csv or ensure timestamped outputs exist."
    )


def fetch_delivery_rows(driver: Any, run_id: str) -> List[Dict[str, str]]:
    query = """
    MATCH (d:CampaignDelivery {run_id: $run_id})
    RETURN d.visitor_id AS visitor_id,
           d.status AS status,
           d.campaign_id AS campaign_id,
           d.show AS show,
           d.run_mode AS run_mode,
           d.delivery_id AS delivery_id
    """
    rows: List[Dict[str, str]] = []
    with driver.session() as session:
        result = session.run(query, {"run_id": run_id})
        for record in result:
            rows.append(
                {
                    "visitor_id": _str(record.get("visitor_id")),
                    "status": _str(record.get("status")),
                    "campaign_id": _str(record.get("campaign_id")),
                    "show": _str(record.get("show")),
                    "run_mode": _str(record.get("run_mode")),
                    "delivery_id": _str(record.get("delivery_id")),
                }
            )
    return rows


def fetch_integrity_counts(driver: Any, run_id: str) -> Dict[str, int]:
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


def resolve_effective_run_id(
    driver: Any,
    provided_run_id: str,
    show: str,
    run_mode: str,
) -> str:
    provided_run_id = _str(provided_run_id)
    show = _str(show)
    run_mode = _str(run_mode)

    with driver.session() as session:
        if provided_run_id:
            if (
                len(provided_run_id) == 15
                and provided_run_id[8] == "_"
                and provided_run_id.replace("_", "").isdigit()
            ):
                ts_token = provided_run_id.replace("_", "T") + "Z"
                record = session.run(
                    """
                    MATCH (r:RecommendationRun)
                    WHERE r.show = $show
                      AND r.run_mode = $run_mode
                      AND r.run_id CONTAINS $ts_token
                    RETURN r.run_id AS run_id
                    ORDER BY r.created_at DESC
                    LIMIT 1
                    """,
                    {"show": show, "run_mode": run_mode, "ts_token": ts_token},
                ).single()
                if record and _str(record.get("run_id")):
                    return _str(record.get("run_id"))

            return provided_run_id

        record = session.run(
            """
            MATCH (r:RecommendationRun)
            WHERE r.show = $show
              AND r.run_mode = $run_mode
            RETURN r.run_id AS run_id
            ORDER BY r.created_at DESC
            LIMIT 1
            """,
            {"show": show, "run_mode": run_mode},
        ).single()
        resolved = _str(record.get("run_id") if record else "")
        if not resolved:
            raise RuntimeError(
                f"Unable to resolve run_id automatically for show='{show}' run_mode='{run_mode}'"
            )
        return resolved


def summarize_db(rows: List[Dict[str, str]]) -> Tuple[Dict[str, str], Dict[str, int], List[str]]:
    by_visitor: Dict[str, str] = {}
    status_counts: Dict[str, int] = {}
    duplicates: List[str] = []

    seen: Set[str] = set()
    for row in rows:
        visitor_id = _str(row.get("visitor_id"))
        status = _str(row.get("status")) or "<missing>"
        status_counts[status] = status_counts.get(status, 0) + 1
        if not visitor_id:
            continue
        if visitor_id in seen:
            duplicates.append(visitor_id)
            continue
        seen.add(visitor_id)
        by_visitor[visitor_id] = _str(row.get("status"))

    return by_visitor, status_counts, sorted(set(duplicates))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="One-time reconciliation: recommendation CSVs vs CampaignDelivery")
    parser.add_argument("--config", default="config/config_tsl.yaml", help="Path to YAML config")
    parser.add_argument(
        "--run-id",
        default="20260219_205354",
        help="Run identifier: full run_id or shorthand timestamp like 20260219_205354",
    )
    parser.add_argument(
        "--main-csv",
        default="",
        help="Main recommendation CSV",
    )
    parser.add_argument(
        "--control-csv",
        default="",
        help="Control recommendation CSV",
    )
    parser.add_argument("--campaign-id", default="", help="Expected campaign_id")
    parser.add_argument("--show", default="tsl", help="Expected show")
    parser.add_argument("--sample-size", type=int, default=25, help="Max mismatches to include in samples")
    parser.add_argument(
        "--report-file",
        default="large_tool_results/one_time_delivery_reconciliation_20260219_205354.json",
        help="Output report JSON path",
    )
    parser.add_argument("--fail-on-mismatch", action="store_true", help="Exit with code 2 if mismatches found")
    return parser


def main() -> None:
    configure_logging()
    args = build_parser().parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    config = load_config(str(config_path))

    env_file_path = resolve_env_file_path(config_path, config.get("env_file", ""))
    if env_file_path:
        load_dotenv(env_file_path)
        LOGGER.info("Loaded environment file: %s", env_file_path)
    else:
        load_dotenv()

    main_csv, control_csv = resolve_recommendation_csv_paths(
        provided_main_csv=args.main_csv,
        provided_control_csv=args.control_csv,
        run_id_input=args.run_id,
        show=args.show,
    )

    if not main_csv.exists():
        raise FileNotFoundError(f"Main CSV not found: {main_csv}")
    if not control_csv.exists():
        raise FileNotFoundError(f"Control CSV not found: {control_csv}")

    expected_status_by_visitor, file_stats = read_expected_status_map(main_csv, control_csv)
    expected_ids = set(expected_status_by_visitor.keys())

    credentials = resolve_neo4j_credentials(config, logger=LOGGER)
    driver = GraphDatabase.driver(
        credentials["uri"],
        auth=(credentials["username"], credentials["password"]),
    )

    try:
        with driver.session() as session:
            ping = session.run("RETURN 1 AS ok").single()
            if not ping or int(ping["ok"]) != 1:
                raise RuntimeError("Neo4j connectivity check failed")

        effective_run_id = resolve_effective_run_id(
            driver=driver,
            provided_run_id=args.run_id,
            show=args.show,
            run_mode=_str(config.get("mode", "")) or "engagement",
        )

        db_rows = fetch_delivery_rows(driver, effective_run_id)
        integrity = fetch_integrity_counts(driver, effective_run_id)
    finally:
        driver.close()

    db_status_by_visitor, db_status_counts, duplicate_visitors = summarize_db(db_rows)
    db_ids = set(db_status_by_visitor.keys())

    missing_in_neo4j = sorted(expected_ids - db_ids)
    extra_in_neo4j = sorted(db_ids - expected_ids)

    status_mismatches: List[Dict[str, str]] = []
    for visitor_id in sorted(expected_ids & db_ids):
        expected_status = expected_status_by_visitor.get(visitor_id, "")
        observed_status = db_status_by_visitor.get(visitor_id, "")
        if expected_status != observed_status:
            status_mismatches.append(
                {
                    "visitor_id": visitor_id,
                    "expected_status": expected_status,
                    "observed_status": observed_status,
                }
            )

    campaign_mismatches: List[Dict[str, str]] = []
    show_mismatches: List[Dict[str, str]] = []
    expected_campaign = _str(args.campaign_id)
    expected_show = _str(args.show)
    if expected_campaign or expected_show:
        for row in db_rows:
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
        len(missing_in_neo4j)
        + len(extra_in_neo4j)
        + len(status_mismatches)
        + len(duplicate_visitors)
        + len(campaign_mismatches)
        + len(show_mismatches)
        + int(integrity.get("deliveries_without_for_visitor", 0))
        + int(integrity.get("deliveries_without_for_run", 0))
    )

    sample_size = max(0, int(args.sample_size))
    report: Dict[str, Any] = {
        "generated_at": now_iso(),
        "run_id": _str(effective_run_id),
        "run_id_input": _str(args.run_id),
        "inputs": {
            "main_csv": str(main_csv),
            "control_csv": str(control_csv),
            **file_stats,
        },
        "neo4j": {
            "delivery_nodes_for_run": len(db_rows),
            "unique_delivery_visitors": len(db_ids),
            "status_counts": db_status_counts,
            "integrity": integrity,
        },
        "reconciliation": {
            "ok": mismatch_total == 0,
            "mismatch_total": mismatch_total,
            "missing_in_neo4j_count": len(missing_in_neo4j),
            "extra_in_neo4j_count": len(extra_in_neo4j),
            "status_mismatch_count": len(status_mismatches),
            "duplicate_delivery_visitor_count": len(duplicate_visitors),
            "campaign_mismatch_count": len(campaign_mismatches),
            "show_mismatch_count": len(show_mismatches),
            "samples": {
                "missing_in_neo4j": missing_in_neo4j[:sample_size],
                "extra_in_neo4j": extra_in_neo4j[:sample_size],
                "status_mismatches": status_mismatches[:sample_size],
                "duplicate_delivery_visitors": duplicate_visitors[:sample_size],
                "campaign_mismatches": campaign_mismatches[:sample_size],
                "show_mismatches": show_mismatches[:sample_size],
            },
        },
    }

    report_path = Path(args.report_file)
    if not report_path.is_absolute():
        report_path = Path.cwd() / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    LOGGER.info("One-time reconciliation report written to %s", report_path)

    if args.fail_on_mismatch and mismatch_total > 0:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
