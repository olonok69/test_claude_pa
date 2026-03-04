#!/usr/bin/env python3
"""M2 migration: apply run traceability schema/backfill in Neo4j.

This script is idempotent and supports dry-run prechecks.

What it does:
1) Creates constraints/indexes for `RecommendationRun` and `CampaignDelivery`.
2) Creates/updates a legacy `RecommendationRun` node.
3) Backfills missing run metadata on existing `IS_RECOMMENDED` relationships.
4) Backfills one `CampaignDelivery` node per visitor for the legacy run.
5) Emits JSON report with before/after counts.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

CURRENT_FILE = Path(__file__).resolve()
PA_ROOT = CURRENT_FILE.parents[1]
REPO_ROOT = PA_ROOT.parent
if str(PA_ROOT) not in sys.path:
    sys.path.insert(0, str(PA_ROOT))

from utils.config_utils import load_config
from utils.neo4j_utils import resolve_neo4j_credentials


LOGGER = logging.getLogger("m2_traceability_migration")


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


def run_scalar(session, query: str, params: Optional[Dict[str, Any]] = None) -> int:
    record = session.run(query, params or {}).single()
    if not record:
        return 0
    value = record.get("value", 0)
    return int(value or 0)


def collect_precheck_counts(
    driver: Driver,
    legacy_run_id: str,
    show: str,
) -> Dict[str, int]:
    queries = {
        "total_is_recommended": """
            MATCH ()-[r:IS_RECOMMENDED]->()
            RETURN count(r) AS value
        """,
        "missing_run_id": """
            MATCH ()-[r:IS_RECOMMENDED]->()
            WHERE r.run_id IS NULL OR trim(toString(r.run_id)) = ''
            RETURN count(r) AS value
        """,
        "missing_run_mode": """
            MATCH ()-[r:IS_RECOMMENDED]->()
            WHERE r.run_mode IS NULL OR trim(toString(r.run_mode)) = ''
            RETURN count(r) AS value
        """,
        "missing_campaign_id": """
            MATCH ()-[r:IS_RECOMMENDED]->()
            WHERE r.campaign_id IS NULL OR trim(toString(r.campaign_id)) = ''
            RETURN count(r) AS value
        """,
        "missing_show": """
            MATCH ()-[r:IS_RECOMMENDED]->()
            WHERE r.show IS NULL OR trim(toString(r.show)) = ''
            RETURN count(r) AS value
        """,
        "legacy_run_relationships": """
            MATCH ()-[r:IS_RECOMMENDED]->()
            WHERE r.run_id = $legacy_run_id
            RETURN count(r) AS value
        """,
        "campaign_delivery_nodes": """
            MATCH (d:CampaignDelivery)
            RETURN count(d) AS value
        """,
        "legacy_delivery_nodes": """
            MATCH (d:CampaignDelivery)
            WHERE d.run_id = $legacy_run_id
            RETURN count(d) AS value
        """,
        "legacy_visitors_without_delivery": """
            MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(:Sessions_this_year)
            WHERE r.run_id = $legacy_run_id
            WITH DISTINCT v
            WHERE NOT EXISTS {
                MATCH (d:CampaignDelivery)-[:FOR_VISITOR]->(v)
                WHERE d.run_id = $legacy_run_id
            }
            RETURN count(v) AS value
        """,
        "legacy_run_nodes": """
            MATCH (rr:RecommendationRun {run_id: $legacy_run_id, show: $show})
            RETURN count(rr) AS value
        """,
    }

    counts: Dict[str, int] = {}
    with driver.session() as session:
        for key, query in queries.items():
            counts[key] = run_scalar(
                session,
                query,
                {"legacy_run_id": legacy_run_id, "show": show},
            )
    return counts


def apply_constraints_and_indexes(driver: Driver) -> None:
    statements = [
        """
        CREATE CONSTRAINT recommendation_run_id_unique IF NOT EXISTS
        FOR (rr:RecommendationRun)
        REQUIRE rr.run_id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT campaign_delivery_id_unique IF NOT EXISTS
        FOR (d:CampaignDelivery)
        REQUIRE d.delivery_id IS UNIQUE
        """,
        """
        CREATE INDEX recommendation_run_mode_idx IF NOT EXISTS
        FOR (rr:RecommendationRun)
        ON (rr.run_mode)
        """,
        """
        CREATE INDEX recommendation_run_campaign_idx IF NOT EXISTS
        FOR (rr:RecommendationRun)
        ON (rr.campaign_id)
        """,
        """
        CREATE INDEX campaign_delivery_run_idx IF NOT EXISTS
        FOR (d:CampaignDelivery)
        ON (d.run_id)
        """,
        """
        CREATE INDEX campaign_delivery_visitor_idx IF NOT EXISTS
        FOR (d:CampaignDelivery)
        ON (d.visitor_id)
        """,
    ]

    with driver.session() as session:
        for statement in statements:
            session.run(statement).consume()


def upsert_legacy_run_node(
    driver: Driver,
    legacy_run_id: str,
    campaign_id: str,
    show: str,
    timestamp: str,
) -> None:
    query = """
    MERGE (rr:RecommendationRun {run_id: $legacy_run_id})
    ON CREATE SET rr.created_at = $timestamp
    SET rr.run_mode = 'unknown',
        rr.campaign_id = $campaign_id,
        rr.show = $show,
        rr.pipeline_version = coalesce(rr.pipeline_version, 'legacy_migration'),
        rr.migrated_at = $timestamp
    """
    with driver.session() as session:
        session.run(
            query,
            {
                "legacy_run_id": legacy_run_id,
                "campaign_id": campaign_id,
                "show": show,
                "timestamp": timestamp,
            },
        ).consume()


def backfill_recommendation_relationships(
    driver: Driver,
    legacy_run_id: str,
    campaign_id: str,
    show: str,
    timestamp: str,
    batch_size: int,
) -> int:
    query = """
    MATCH ()-[r:IS_RECOMMENDED]->()
    WHERE r.run_id IS NULL OR trim(toString(r.run_id)) = ''
    WITH r LIMIT $batch_size
    SET r.run_id = $legacy_run_id,
        r.run_mode = coalesce(nullif(trim(toString(r.run_mode)), ''), 'unknown'),
        r.campaign_id = coalesce(nullif(trim(toString(r.campaign_id)), ''), $campaign_id),
        r.show = coalesce(nullif(trim(toString(r.show)), ''), $show),
        r.generated_at = coalesce(
            nullif(trim(toString(r.generated_at)), ''),
            nullif(trim(toString(r.created_at)), ''),
            nullif(trim(toString(r.updated_at)), ''),
            $timestamp
        ),
        r.control_group = coalesce(r.control_group, 0),
        r.control_group_type = coalesce(r.control_group_type, null),
        r.migrated_at = $timestamp
    RETURN count(r) AS value
    """

    updated_total = 0
    with driver.session() as session:
        while True:
            updated = run_scalar(
                session,
                query,
                {
                    "batch_size": int(batch_size),
                    "legacy_run_id": legacy_run_id,
                    "campaign_id": campaign_id,
                    "show": show,
                    "timestamp": timestamp,
                },
            )
            if updated == 0:
                break
            updated_total += updated
            LOGGER.info("Backfilled IS_RECOMMENDED relationships: +%d", updated)

    return updated_total


def backfill_campaign_delivery_nodes(
    driver: Driver,
    legacy_run_id: str,
    campaign_id: str,
    show: str,
    timestamp: str,
) -> int:
    query = """
    MATCH (rr:RecommendationRun {run_id: $legacy_run_id})
    MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(:Sessions_this_year)
    WHERE r.run_id = $legacy_run_id
    WITH rr, v,
         max(CASE WHEN coalesce(r.control_group, 0) = 1 THEN 1 ELSE 0 END) AS is_control
    WITH rr, v,
         CASE WHEN is_control = 1 THEN 'withheld_control' ELSE 'sent' END AS status,
         coalesce(nullif(trim(toString(v.BadgeId)), ''), 'node_' + toString(id(v))) AS visitor_id
    MERGE (d:CampaignDelivery {delivery_id: $legacy_run_id + '::' + visitor_id})
    ON CREATE SET d.created_at = $timestamp
    SET d.run_id = $legacy_run_id,
        d.campaign_id = $campaign_id,
        d.run_mode = 'unknown',
        d.visitor_id = visitor_id,
        d.status = status,
        d.timestamp = coalesce(d.timestamp, $timestamp),
        d.show = $show,
        d.migrated_at = $timestamp
    MERGE (d)-[:FOR_VISITOR]->(v)
    MERGE (d)-[:FOR_RUN]->(rr)
    RETURN count(d) AS value
    """

    with driver.session() as session:
        return run_scalar(
            session,
            query,
            {
                "legacy_run_id": legacy_run_id,
                "campaign_id": campaign_id,
                "show": show,
                "timestamp": timestamp,
            },
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run M2 traceability migration/backfill in Neo4j",
    )
    parser.add_argument(
        "--config",
        default="PA/config/config_tsl.yaml",
        help="Path to YAML config used for Neo4j settings.",
    )
    parser.add_argument(
        "--legacy-run-id",
        default="legacy_pre_traceability",
        help="Run ID used to tag legacy recommendation relationships.",
    )
    parser.add_argument(
        "--legacy-campaign-id",
        default="legacy",
        help="Campaign ID used to tag legacy recommendation relationships.",
    )
    parser.add_argument(
        "--show",
        default="",
        help="Override show/event code; defaults to event.main_event from config.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50000,
        help="Batch size for relationship backfill loop.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report impact only; no writes performed.",
    )
    parser.add_argument(
        "--report-file",
        default="large_tool_results/m2_traceability_migration_report.json",
        help="Path to write migration report JSON.",
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
        if config.get("env_file"):
            LOGGER.warning(
                "Configured env_file '%s' not found. Using ambient environment.",
                config.get("env_file"),
            )

    show = _str(args.show) or _str((config.get("event", {}) or {}).get("main_event")) or "unknown"

    credentials = resolve_neo4j_credentials(config, logger=LOGGER)
    driver = GraphDatabase.driver(
        credentials["uri"],
        auth=(credentials["username"], credentials["password"]),
    )

    started_at = utc_now_iso()
    report_path = Path(args.report_file)
    if not report_path.is_absolute():
        report_path = REPO_ROOT / report_path

    try:
        before = collect_precheck_counts(
            driver,
            legacy_run_id=args.legacy_run_id,
            show=show,
        )

        report: Dict[str, Any] = {
            "started_at": started_at,
            "dry_run": bool(args.dry_run),
            "legacy_run_id": args.legacy_run_id,
            "legacy_campaign_id": args.legacy_campaign_id,
            "show": show,
            "batch_size": int(args.batch_size),
            "before": before,
            "actions": {},
        }

        if args.dry_run:
            LOGGER.info("Dry run complete. No writes executed.")
        else:
            timestamp = utc_now_iso()
            apply_constraints_and_indexes(driver)
            report["actions"]["constraints_indexes"] = "applied"

            upsert_legacy_run_node(
                driver,
                legacy_run_id=args.legacy_run_id,
                campaign_id=args.legacy_campaign_id,
                show=show,
                timestamp=timestamp,
            )
            report["actions"]["legacy_run_node"] = "upserted"

            updated_relationships = backfill_recommendation_relationships(
                driver,
                legacy_run_id=args.legacy_run_id,
                campaign_id=args.legacy_campaign_id,
                show=show,
                timestamp=timestamp,
                batch_size=args.batch_size,
            )
            report["actions"]["relationships_backfilled"] = updated_relationships

            delivery_rows = backfill_campaign_delivery_nodes(
                driver,
                legacy_run_id=args.legacy_run_id,
                campaign_id=args.legacy_campaign_id,
                show=show,
                timestamp=timestamp,
            )
            report["actions"]["delivery_nodes_upserted"] = delivery_rows

        after = collect_precheck_counts(
            driver,
            legacy_run_id=args.legacy_run_id,
            show=show,
        )
        report["after"] = after
        report["finished_at"] = utc_now_iso()

        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        print(json.dumps(report, indent=2))
        LOGGER.info("Migration report written to %s", report_path)

    finally:
        driver.close()


if __name__ == "__main__":
    main()
