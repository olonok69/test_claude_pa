#!/usr/bin/env python3
"""Import v2e exhibitor recommendations into Neo4j.

Creates:
- `Exhibitor` nodes with attributes:
  `uuid`, `name`, `stand_location_number`, `relevant_show`, `extra_company_info`
- Relationships from `Visitor_this_year` to `Exhibitor`, matching visitors by:
  `Visitor_this_year.BadgeId == badgeID` from JSON payload
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase


CURRENT_FILE = Path(__file__).resolve()
PA_ROOT = CURRENT_FILE.parents[1]
if str(PA_ROOT) not in sys.path:
    sys.path.insert(0, str(PA_ROOT))

from utils.config_utils import load_config
from utils.neo4j_utils import resolve_neo4j_credentials


LOGGER = logging.getLogger("v2e_to_neo4j")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_env_file_path(config_path: Path, env_file_value: str) -> Path | None:
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
        PA_ROOT.parent / env_path,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def chunked(items: List[Any], size: int) -> Iterable[List[Any]]:
    step = max(1, size)
    for idx in range(0, len(items), step):
        yield items[idx : idx + step]


def _str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def load_v2e_payload(json_path: Path) -> Dict[str, Any]:
    if not json_path.exists():
        raise FileNotFoundError(f"v2e JSON not found: {json_path}")

    with json_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_badge_ids_from_csv(csv_path: Path) -> Set[str]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    badge_ids: Set[str] = set()
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            visitor_id = _str(row.get("visitor_id"))
            if visitor_id:
                badge_ids.add(visitor_id)
    return badge_ids


def transform_payload(payload: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], Dict[str, Any]]:
    recommendations = payload.get("recommendations", []) or []

    exhibitor_by_uuid: Dict[str, Dict[str, str]] = {}
    relationship_pairs: Set[Tuple[str, str]] = set()

    visitors_missing_badge = 0
    exhibitors_missing_uuid = 0
    malformed_exhibitor_rows = 0

    for item in recommendations:
        badge_id = _str(item.get("badgeID"))
        exhibitors = item.get("exhibitors", []) or []

        if not badge_id:
            visitors_missing_badge += 1
            continue

        if not isinstance(exhibitors, list):
            malformed_exhibitor_rows += 1
            continue

        for exhibitor in exhibitors:
            if not isinstance(exhibitor, dict):
                malformed_exhibitor_rows += 1
                continue

            uuid = _str(exhibitor.get("uuid"))
            if not uuid:
                exhibitors_missing_uuid += 1
                continue

            exhibitor_by_uuid[uuid] = {
                "uuid": uuid,
                "name": _str(exhibitor.get("name")),
                "stand_location_number": _str(exhibitor.get("stand_location_number")),
                "relevant_show": _str(exhibitor.get("relevant_show")),
                "extra_company_info": _str(exhibitor.get("extra_company_info")),
            }
            relationship_pairs.add((badge_id, uuid))

    exhibitor_rows = list(exhibitor_by_uuid.values())
    relationship_rows = [
        {"badge_id": badge_id, "uuid": uuid}
        for badge_id, uuid in sorted(relationship_pairs)
    ]

    stats = {
        "recommendation_entries": len(recommendations),
        "unique_exhibitors": len(exhibitor_rows),
        "unique_visitor_exhibitor_pairs": len(relationship_rows),
        "visitors_missing_badge_id": visitors_missing_badge,
        "exhibitors_missing_uuid": exhibitors_missing_uuid,
        "malformed_exhibitor_rows": malformed_exhibitor_rows,
    }
    return exhibitor_rows, relationship_rows, stats


def fetch_existing_visitors(driver: Driver, visitor_label: str, badge_ids: List[str], batch_size: int) -> Set[str]:
    existing: Set[str] = set()
    query = f"""
    UNWIND $badge_ids AS badge_id
    MATCH (v:{visitor_label} {{BadgeId: badge_id}})
    RETURN badge_id
    """

    with driver.session() as session:
        for batch in chunked(badge_ids, batch_size):
            records = session.run(query, {"badge_ids": batch})
            for record in records:
                existing.add(_str(record.get("badge_id")))
    return existing


def fetch_recommendation_run_context(driver: Driver, run_id: str) -> Dict[str, str]:
    query = """
    MATCH (rr:RecommendationRun {run_id: $run_id})
    RETURN rr.run_id AS run_id,
           coalesce(rr.run_mode, '') AS run_mode,
           coalesce(rr.campaign_id, '') AS campaign_id,
           coalesce(rr.show, '') AS show
    LIMIT 1
    """
    with driver.session() as session:
        record = session.run(query, {"run_id": run_id}).single()
    if not record:
        raise ValueError(f"RecommendationRun not found for run_id={run_id}")
    return {
        "run_id": _str(record.get("run_id")),
        "run_mode": _str(record.get("run_mode")),
        "campaign_id": _str(record.get("campaign_id")),
        "show": _str(record.get("show")),
    }


def fetch_run_scoped_visitor_badge_ids(driver: Driver, visitor_label: str, run_id: str) -> Set[str]:
    """Collect visitor BadgeIds scoped to a RecommendationRun.

    Sources:
    - CampaignDelivery FOR_RUN/FOR_VISITOR links
    - IS_RECOMMENDED relationships with matching run_id
    """
    badge_ids: Set[str] = set()

    delivery_query = f"""
    MATCH (rr:RecommendationRun {{run_id: $run_id}})
    MATCH (d:CampaignDelivery {{run_id: $run_id}})-[:FOR_RUN]->(rr)
    MATCH (d)-[:FOR_VISITOR]->(v:{visitor_label})
    RETURN DISTINCT v.BadgeId AS badge_id
    """

    recommendation_query = f"""
    MATCH (v:{visitor_label})-[r:IS_RECOMMENDED {{run_id: $run_id}}]->(:Sessions_this_year)
    RETURN DISTINCT v.BadgeId AS badge_id
    """

    with driver.session() as session:
        for record in session.run(delivery_query, {"run_id": run_id}):
            badge_id = _str(record.get("badge_id"))
            if badge_id:
                badge_ids.add(badge_id)

        for record in session.run(recommendation_query, {"run_id": run_id}):
            badge_id = _str(record.get("badge_id"))
            if badge_id:
                badge_ids.add(badge_id)

    return badge_ids


def upsert_exhibitors(driver: Driver, exhibitor_rows: List[Dict[str, str]], batch_size: int) -> int:
    if not exhibitor_rows:
        return 0

    query = """
    UNWIND $rows AS row
    MERGE (e:Exhibitor {uuid: row.uuid})
    ON CREATE SET e.created_at = $timestamp
    SET e.name = row.name,
        e.stand_location_number = row.stand_location_number,
        e.relevant_show = row.relevant_show,
        e.extra_company_info = row.extra_company_info,
        e.updated_at = $timestamp
    """

    with driver.session() as session:
        for batch in chunked(exhibitor_rows, batch_size):
            session.run(
                query,
                {
                    "rows": batch,
                    "timestamp": utc_now_iso(),
                },
            ).consume()
    return len(exhibitor_rows)


def create_relationships(
    driver: Driver,
    visitor_label: str,
    relationship_type: str,
    relationship_rows: List[Dict[str, str]],
    batch_size: int,
    recommendation_run_context: Dict[str, str] | None = None,
) -> int:
    if not relationship_rows:
        return 0

    if recommendation_run_context and recommendation_run_context.get("run_id"):
        query = f"""
        UNWIND $rows AS row
        MATCH (v:{visitor_label} {{BadgeId: row.badge_id}})
        MATCH (e:Exhibitor {{uuid: row.uuid}})
        MERGE (v)-[r:{relationship_type} {{run_id: $run_id}}]->(e)
        ON CREATE SET r.created_at = $timestamp
        SET r.updated_at = $timestamp,
            r.run_id = $run_id,
            r.run_mode = $run_mode,
            r.campaign_id = $campaign_id,
            r.show = $show
        """
    else:
        query = f"""
        UNWIND $rows AS row
        MATCH (v:{visitor_label} {{BadgeId: row.badge_id}})
        MATCH (e:Exhibitor {{uuid: row.uuid}})
        MERGE (v)-[r:{relationship_type}]->(e)
        ON CREATE SET r.created_at = $timestamp
        SET r.updated_at = $timestamp
        """

    with driver.session() as session:
        for batch in chunked(relationship_rows, batch_size):
            session.run(
                query,
                {
                    "rows": batch,
                    "timestamp": utc_now_iso(),
                    "run_id": _str((recommendation_run_context or {}).get("run_id")),
                    "run_mode": _str((recommendation_run_context or {}).get("run_mode")),
                    "campaign_id": _str((recommendation_run_context or {}).get("campaign_id")),
                    "show": _str((recommendation_run_context or {}).get("show")),
                },
            ).consume()
    return len(relationship_rows)


def ensure_campaign_delivery_links(
    driver: Driver,
    visitor_label: str,
    badge_ids: List[str],
    recommendation_run_context: Dict[str, str],
    batch_size: int,
    default_status: str,
) -> Dict[str, int]:
    if not badge_ids:
        return {
            "rows_submitted": 0,
            "matched_visitors": 0,
            "delivery_nodes_touched": 0,
            "delivery_nodes_created": 0,
            "for_visitor_links_touched": 0,
            "for_visitor_links_created": 0,
            "for_run_links_touched": 0,
            "for_run_links_created": 0,
        }

    query = f"""
    UNWIND $rows AS row
    MATCH (rr:RecommendationRun {{run_id: $run_id}})
    MATCH (v:{visitor_label} {{BadgeId: row.badge_id}})

    OPTIONAL MATCH (d_existing:CampaignDelivery {{run_id: $run_id, visitor_id: row.badge_id}})
    WITH row, rr, v, d_existing, d_existing IS NULL AS d_created

    MERGE (d:CampaignDelivery {{run_id: $run_id, visitor_id: row.badge_id}})
    ON CREATE SET d.delivery_id = randomUUID(),
                  d.created_at = datetime()
    SET d.updated_at = datetime(),
        d.run_mode = $run_mode,
        d.campaign_id = $campaign_id,
        d.show = $show,
        d.status = CASE
            WHEN trim(coalesce(toString(d.status), '')) = '' THEN $default_status
            ELSE d.status
        END

    WITH row, rr, v, d, d_created
    OPTIONAL MATCH (d)-[fv_existing:FOR_VISITOR]->(v)
    WITH row, rr, v, d, d_created, fv_existing IS NULL AS fv_created
    MERGE (d)-[fv:FOR_VISITOR]->(v)

    WITH row, rr, v, d, d_created, fv, fv_created
    OPTIONAL MATCH (d)-[fr_existing:FOR_RUN]->(rr)
    WITH row, rr, v, d, d_created, fv, fv_created, fr_existing IS NULL AS fr_created
    MERGE (d)-[fr:FOR_RUN]->(rr)

    RETURN count(v) AS matched_visitors,
           count(d) AS delivery_nodes_touched,
           sum(CASE WHEN d_created THEN 1 ELSE 0 END) AS delivery_nodes_created,
           count(fv) AS for_visitor_links_touched,
           sum(CASE WHEN fv_created THEN 1 ELSE 0 END) AS for_visitor_links_created,
           count(fr) AS for_run_links_touched,
           sum(CASE WHEN fr_created THEN 1 ELSE 0 END) AS for_run_links_created
    """

    totals = {
        "rows_submitted": len(badge_ids),
        "matched_visitors": 0,
        "delivery_nodes_touched": 0,
        "delivery_nodes_created": 0,
        "for_visitor_links_touched": 0,
        "for_visitor_links_created": 0,
        "for_run_links_touched": 0,
        "for_run_links_created": 0,
    }

    with driver.session() as session:
        for batch in chunked(badge_ids, batch_size):
            record = session.run(
                query,
                {
                    "rows": [{"badge_id": badge_id} for badge_id in batch],
                    "run_id": _str(recommendation_run_context.get("run_id")),
                    "run_mode": _str(recommendation_run_context.get("run_mode")),
                    "campaign_id": _str(recommendation_run_context.get("campaign_id")),
                    "show": _str(recommendation_run_context.get("show")),
                    "default_status": _str(default_status) or "sent",
                },
            ).single()
            if not record:
                continue
            totals["matched_visitors"] += int(record.get("matched_visitors", 0) or 0)
            totals["delivery_nodes_touched"] += int(record.get("delivery_nodes_touched", 0) or 0)
            totals["delivery_nodes_created"] += int(record.get("delivery_nodes_created", 0) or 0)
            totals["for_visitor_links_touched"] += int(record.get("for_visitor_links_touched", 0) or 0)
            totals["for_visitor_links_created"] += int(record.get("for_visitor_links_created", 0) or 0)
            totals["for_run_links_touched"] += int(record.get("for_run_links_touched", 0) or 0)
            totals["for_run_links_created"] += int(record.get("for_run_links_created", 0) or 0)

    return totals


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import v2e exhibitor recommendations into Neo4j",
    )
    parser.add_argument(
        "--config",
        default="PA/config/config_tsl.yaml",
        help="Path to YAML config used for Neo4j settings.",
    )
    parser.add_argument(
        "--v2e-json",
        default="PA/data/tsl/v2e_recommendations_3.json",
        help="Path to v2e recommendations JSON.",
    )
    parser.add_argument(
        "--visitor-label",
        default="Visitor_this_year",
        help="Visitor label in Neo4j.",
    )
    parser.add_argument(
        "--relationship-type",
        default="IS_RECOMMENDED_EXHIBITOR",
        help="Relationship type from visitor to exhibitor.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=2000,
        help="Batch size for Neo4j writes.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and report stats without writing to Neo4j.",
    )
    parser.add_argument(
        "--recommendation-run-id",
        default="",
        help=(
            "Optional RecommendationRun.run_id scope. When provided, only visitors belonging "
            "to that run are eligible for IS_RECOMMENDED_EXHIBITOR writes."
        ),
    )
    parser.add_argument(
        "--only-badgeids-from-csv",
        action="store_true",
        help=(
            "Restrict import to badge IDs present in recommendation CSV files "
            "(useful to compare with unify incidence report)."
        ),
    )
    parser.add_argument(
        "--recommendations-csv",
        default="PA/data/tsl/recommendations/visitor_recommendations_tsl_20260214_144216.csv",
        help="Main recommendation CSV used when --only-badgeids-from-csv is enabled.",
    )
    parser.add_argument(
        "--control-csv",
        default="PA/data/tsl/recommendations/control/visitor_recommendations_tsl_20260214_144216_control.csv",
        help="Control recommendation CSV used when --only-badgeids-from-csv is enabled.",
    )
    parser.add_argument(
        "--ensure-delivery-links",
        action="store_true",
        help=(
            "When --recommendation-run-id is provided, also enforce CampaignDelivery + "
            "FOR_VISITOR + FOR_RUN links for scoped visitors."
        ),
    )
    parser.add_argument(
        "--delivery-status",
        default="sent",
        help="Default CampaignDelivery.status value when creating missing delivery nodes (default: sent).",
    )
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
        LOGGER.info("Loaded environment file: %s", env_file_path)
    else:
        load_dotenv()
        if config.get("env_file"):
            LOGGER.warning(
                "Configured env_file '%s' was not found. Falling back to ambient environment variables.",
                config.get("env_file"),
            )

    payload = load_v2e_payload(Path(args.v2e_json))
    exhibitor_rows, relationship_rows, stats = transform_payload(payload)

    if args.only_badgeids_from_csv:
        main_badge_ids = load_badge_ids_from_csv(Path(args.recommendations_csv))
        control_badge_ids = load_badge_ids_from_csv(Path(args.control_csv))
        allowed_badge_ids = main_badge_ids | control_badge_ids

        relationship_rows = [
            row for row in relationship_rows if row["badge_id"] in allowed_badge_ids
        ]
        LOGGER.info(
            "CSV filter enabled: badge_ids main=%d control=%d combined=%d",
            len(main_badge_ids),
            len(control_badge_ids),
            len(allowed_badge_ids),
        )
        LOGGER.info(
            "CSV filter enabled: visitor-exhibitor pairs after filter=%d",
            len(relationship_rows),
        )

    badge_ids = sorted({_str(row["badge_id"]) for row in relationship_rows if _str(row.get("badge_id"))})

    neo4j_cfg = config.get("neo4j", {}) or {}
    labels_cfg = neo4j_cfg.get("node_labels", {}) or {}
    visitor_label = labels_cfg.get("visitor_this_year", args.visitor_label)

    credentials = resolve_neo4j_credentials(config, logger=LOGGER)
    uri = credentials["uri"]
    username = credentials["username"]
    password = credentials["password"]
    recommendation_run_id = _str(args.recommendation_run_id)

    LOGGER.info("Connecting to Neo4j (%s)", uri)
    driver = GraphDatabase.driver(uri, auth=(username, password))

    try:
        recommendation_run_context: Dict[str, str] | None = None
        run_scoped_badge_ids: Set[str] | None = None
        if recommendation_run_id:
            recommendation_run_context = fetch_recommendation_run_context(driver, recommendation_run_id)
            run_scoped_badge_ids = fetch_run_scoped_visitor_badge_ids(
                driver=driver,
                visitor_label=visitor_label,
                run_id=recommendation_run_id,
            )
            LOGGER.info(
                "RecommendationRun scope enabled: run_id=%s mode=%s campaign_id=%s show=%s",
                recommendation_run_context.get("run_id"),
                recommendation_run_context.get("run_mode"),
                recommendation_run_context.get("campaign_id"),
                recommendation_run_context.get("show"),
            )
            LOGGER.info(
                "RecommendationRun scope visitor candidates found: %d",
                len(run_scoped_badge_ids),
            )

            payload_badge_ids = set(badge_ids)
            payload_in_run_scope = payload_badge_ids & run_scoped_badge_ids
            payload_outside_run_scope = payload_badge_ids - run_scoped_badge_ids
            run_scope_missing_from_payload = run_scoped_badge_ids - payload_badge_ids

            LOGGER.info(
                "Run scope vs payload: payload_in_scope=%d payload_outside_scope=%d run_scope_missing_from_payload=%d",
                len(payload_in_run_scope),
                len(payload_outside_run_scope),
                len(run_scope_missing_from_payload),
            )
            if run_scope_missing_from_payload:
                LOGGER.info(
                    "Run scope missing from payload sample (up to 25): %s",
                    sorted(run_scope_missing_from_payload)[:25],
                )

        existing_visitors = fetch_existing_visitors(
            driver=driver,
            visitor_label=visitor_label,
            badge_ids=badge_ids,
            batch_size=args.batch_size,
        )

        if run_scoped_badge_ids is not None:
            existing_before_scope = len(existing_visitors)
            existing_visitors = existing_visitors & run_scoped_badge_ids
            LOGGER.info(
                "Applied run scope to matched visitors: before=%d after=%d",
                existing_before_scope,
                len(existing_visitors),
            )

        missing_visitors = sorted(set(badge_ids) - existing_visitors)

        relationship_rows_filtered = [
            row for row in relationship_rows if row["badge_id"] in existing_visitors
        ]
        scoped_exhibitor_uuids = {
            _str(row.get("uuid")) for row in relationship_rows_filtered if _str(row.get("uuid"))
        }
        exhibitor_rows_filtered = [
            row for row in exhibitor_rows if _str(row.get("uuid")) in scoped_exhibitor_uuids
        ]

        LOGGER.info("Payload entries: %d", stats["recommendation_entries"])
        LOGGER.info("Unique exhibitors to upsert: %d", len(exhibitor_rows))
        LOGGER.info("Unique visitor-exhibitor pairs: %d", len(relationship_rows))
        LOGGER.info("Visitors matched in Neo4j: %d", len(existing_visitors))
        LOGGER.info("Visitors missing in Neo4j: %d", len(missing_visitors))
        LOGGER.info("Run-scoped exhibitors to upsert: %d", len(exhibitor_rows_filtered))
        LOGGER.info("Run-scoped visitor-exhibitor pairs to write: %d", len(relationship_rows_filtered))

        if missing_visitors:
            LOGGER.warning("Missing BadgeId sample (up to 25): %s", missing_visitors[:25])

        if args.dry_run:
            LOGGER.info("Dry run enabled. No writes executed.")
            return

        exhibitors_written = upsert_exhibitors(
            driver=driver,
            exhibitor_rows=exhibitor_rows_filtered,
            batch_size=args.batch_size,
        )
        relationships_written = create_relationships(
            driver=driver,
            visitor_label=visitor_label,
            relationship_type=args.relationship_type,
            relationship_rows=relationship_rows_filtered,
            batch_size=args.batch_size,
            recommendation_run_context=recommendation_run_context,
        )

        delivery_enforcement = None
        if args.ensure_delivery_links:
            if not recommendation_run_context:
                raise ValueError(
                    "--ensure-delivery-links requires --recommendation-run-id so FOR_RUN can be attached correctly."
                )
            scoped_badge_ids = sorted({row["badge_id"] for row in relationship_rows_filtered if _str(row.get("badge_id"))})
            delivery_enforcement = ensure_campaign_delivery_links(
                driver=driver,
                visitor_label=visitor_label,
                badge_ids=scoped_badge_ids,
                recommendation_run_context=recommendation_run_context,
                batch_size=args.batch_size,
                default_status=args.delivery_status,
            )

        print("Import completed")
        print(f"Exhibitor nodes upserted: {exhibitors_written}")
        print(f"Visitor->Exhibitor relationships merged: {relationships_written}")
        if delivery_enforcement is not None:
            print("CampaignDelivery enforcement:", delivery_enforcement)
        print(f"Visitors missing in Neo4j: {len(missing_visitors)}")
        print(f"Visitors missing sample: {missing_visitors[:25]}")
        print(f"Visitors missing badgeID in JSON: {stats['visitors_missing_badge_id']}")
        print(f"Exhibitors missing uuid in JSON: {stats['exhibitors_missing_uuid']}")
        print(f"Malformed exhibitor rows: {stats['malformed_exhibitor_rows']}")

    finally:
        driver.close()


if __name__ == "__main__":
    main()