#!/usr/bin/env python3
"""Rebuild a Personal Agendas run from CSV recommendation files.

Scope (conservative):
- RecommendationRun node
- IS_RECOMMENDED relationships
- CampaignDelivery nodes
- FOR_VISITOR and FOR_RUN relationships

Out of scope:
- IS_RECOMMENDED_EXHIBITOR / Exhibitor nodes
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase


CURRENT_FILE = Path(__file__).resolve()
PA_ROOT = CURRENT_FILE.parents[1]
REPO_ROOT = PA_ROOT.parent
if str(PA_ROOT) not in sys.path:
    sys.path.insert(0, str(PA_ROOT))

from utils.config_utils import load_config
from utils.neo4j_utils import resolve_neo4j_credentials


LOGGER = logging.getLogger("rebuild_pa_run_from_csv")


def _str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def chunked(items: Sequence[Any], size: int) -> Iterable[Sequence[Any]]:
    step = max(1, int(size))
    for index in range(0, len(items), step):
        yield items[index : index + step]


def resolve_env_file_path(config_path: Path, env_file_value: str) -> Optional[Path]:
    env_file_value = _str(env_file_value)
    if not env_file_value:
        return None

    env_path = Path(env_file_value)
    if env_path.is_absolute():
        return env_path if env_path.exists() else None

    for candidate in [
        Path.cwd() / env_path,
        config_path.parent / env_path,
        PA_ROOT / env_path,
        REPO_ROOT / env_path,
    ]:
        if candidate.exists():
            return candidate
    return None


def load_pairs_from_csv(path: Path, split_status: str) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    LOGGER.info("Loading recommendation CSV: split=%s path=%s", split_status, path)
    visitors: Set[str] = set()
    session_pairs: Set[Tuple[str, str]] = set()

    missing_visitor_id = 0
    missing_session_id = 0
    processed_rows = 0

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            processed_rows += 1
            if processed_rows % 5000 == 0:
                LOGGER.info("Parsed %s rows from %s", processed_rows, path.name)

            visitor_id = _str(row.get("visitor_id") or row.get("BadgeId") or row.get("badge_id"))
            session_id = _str(row.get("session_id"))

            if not visitor_id:
                missing_visitor_id += 1
                continue
            if not session_id:
                missing_session_id += 1
                continue

            visitors.add(visitor_id)
            session_pairs.add((visitor_id, session_id))

    payload = {
        "path": str(path),
        "split_status": split_status,
        "visitors": visitors,
        "session_pairs": session_pairs,
        "stats": {
            "rows": processed_rows,
            "visitors": len(visitors),
            "session_pairs": len(session_pairs),
            "rows_missing_visitor_id": missing_visitor_id,
            "rows_missing_session_id": missing_session_id,
        },
    }
    LOGGER.info(
        "Loaded split=%s rows=%s visitors=%s session_pairs=%s",
        split_status,
        payload["stats"]["rows"],
        payload["stats"]["visitors"],
        payload["stats"]["session_pairs"],
    )
    return payload


def rows_from_pairs(pairs: Set[Tuple[str, str]]) -> List[Dict[str, str]]:
    return [{"visitor_id": visitor_id, "target_id": session_id} for visitor_id, session_id in sorted(pairs)]


def rows_from_status(status_by_visitor: Dict[str, str]) -> List[Dict[str, str]]:
    return [{"visitor_id": visitor_id, "status": status} for visitor_id, status in sorted(status_by_visitor.items())]


def ensure_recommendation_run(driver: Driver, run_ctx: Dict[str, str]) -> Dict[str, Any]:
    query = """
    OPTIONAL MATCH (rr_existing:RecommendationRun {run_id: $run_id})
    WITH rr_existing, rr_existing IS NULL AS was_created
    MERGE (rr:RecommendationRun {run_id: $run_id})
    ON CREATE SET rr.created_at = CASE WHEN trim($created_at) <> '' THEN datetime($created_at) ELSE datetime() END
    SET rr.updated_at = CASE WHEN trim($updated_at) <> '' THEN datetime($updated_at) ELSE datetime() END,
        rr.run_mode = $run_mode,
        rr.campaign_id = $campaign_id,
        rr.show = $show,
        rr.pipeline_version = $pipeline_version,
        rr.allocation_version = $allocation_version,
        rr.reconciled_at = datetime()
    RETURN was_created AS was_created,
           elementId(rr) AS node_id
    """
    with driver.session() as session:
        record = session.run(query, run_ctx).single()
    return {
        "node_created": bool(record.get("was_created")) if record else False,
        "node_id": _str(record.get("node_id")) if record else "",
    }


def verify_is_recommended(
    driver: Driver,
    rows: List[Dict[str, str]],
    run_ctx: Dict[str, str],
    batch_size: int,
    sample_size: int,
) -> Dict[str, Any]:
    if not rows:
        return {
            "pairs_total": 0,
            "visitor_missing": 0,
            "target_missing": 0,
            "relationship_missing": 0,
            "relationship_found": 0,
            "metadata_mismatch_or_missing": 0,
            "samples": [],
        }

    LOGGER.info(
        "Verifying IS_RECOMMENDED for run_id=%s rows=%s batch_size=%s",
        run_ctx["run_id"],
        len(rows),
        batch_size,
    )

    query = """
    UNWIND $rows AS row
    OPTIONAL MATCH (v:Visitor_this_year {BadgeId: row.visitor_id})
    OPTIONAL MATCH (s:Sessions_this_year {session_id: row.target_id})
    OPTIONAL MATCH (v)-[r:IS_RECOMMENDED]->(s)
    RETURN row.visitor_id AS visitor_id,
           row.target_id AS target_id,
           v IS NOT NULL AS has_visitor,
           s IS NOT NULL AS has_target,
           r IS NOT NULL AS has_relationship,
           trim(coalesce(toString(r.run_id), '')) AS rel_run_id,
           trim(coalesce(toString(r.run_mode), '')) AS rel_run_mode,
           trim(coalesce(toString(r.campaign_id), '')) AS rel_campaign_id,
           trim(coalesce(toString(r.show), '')) AS rel_show
    """

    counts = {
        "pairs_total": len(rows),
        "visitor_missing": 0,
        "target_missing": 0,
        "relationship_missing": 0,
        "relationship_found": 0,
        "metadata_mismatch_or_missing": 0,
    }
    samples: List[Dict[str, Any]] = []
    total_batches = (len(rows) + batch_size - 1) // batch_size
    processed = 0

    with driver.session() as session:
        for batch_idx, batch in enumerate(chunked(rows, batch_size), start=1):
            result = session.run(query, {"rows": list(batch)})
            for record in result:
                processed += 1
                has_visitor = bool(record.get("has_visitor"))
                has_target = bool(record.get("has_target"))
                has_relationship = bool(record.get("has_relationship"))

                if not has_visitor:
                    counts["visitor_missing"] += 1
                if not has_target:
                    counts["target_missing"] += 1
                if has_visitor and has_target and not has_relationship:
                    counts["relationship_missing"] += 1
                if has_relationship:
                    counts["relationship_found"] += 1
                    mismatch = (
                        _str(record.get("rel_run_id")) != run_ctx["run_id"]
                        or _str(record.get("rel_run_mode")) != run_ctx["run_mode"]
                        or _str(record.get("rel_campaign_id")) != run_ctx["campaign_id"]
                        or _str(record.get("rel_show")) != run_ctx["show"]
                    )
                    if mismatch:
                        counts["metadata_mismatch_or_missing"] += 1
                        if len(samples) < sample_size:
                            samples.append(
                                {
                                    "visitor_id": _str(record.get("visitor_id")),
                                    "target_id": _str(record.get("target_id")),
                                    "rel_run_id": _str(record.get("rel_run_id")),
                                    "rel_run_mode": _str(record.get("rel_run_mode")),
                                    "rel_campaign_id": _str(record.get("rel_campaign_id")),
                                    "rel_show": _str(record.get("rel_show")),
                                }
                            )
                elif len(samples) < sample_size:
                    samples.append(
                        {
                            "visitor_id": _str(record.get("visitor_id")),
                            "target_id": _str(record.get("target_id")),
                            "has_visitor": has_visitor,
                            "has_target": has_target,
                            "has_relationship": has_relationship,
                        }
                    )

            if batch_idx == 1 or batch_idx % 10 == 0 or batch_idx == total_batches:
                LOGGER.info(
                    "Verify IS_RECOMMENDED progress run_id=%s batch=%s/%s (%s/%s)",
                    run_ctx["run_id"],
                    batch_idx,
                    total_batches,
                    processed,
                    len(rows),
                )

    LOGGER.info(
        "Verify IS_RECOMMENDED complete run_id=%s found=%s missing=%s mismatches=%s",
        run_ctx["run_id"],
        counts["relationship_found"],
        counts["relationship_missing"],
        counts["metadata_mismatch_or_missing"],
    )
    return {**counts, "samples": samples}


def apply_is_recommended(
    driver: Driver,
    rows: List[Dict[str, str]],
    run_ctx: Dict[str, str],
    batch_size: int,
) -> Dict[str, Any]:
    if not rows:
        return {"created_total": 0, "updated_total": 0, "relationship_changes": []}

    LOGGER.info(
        "Applying IS_RECOMMENDED for run_id=%s rows=%s batch_size=%s",
        run_ctx["run_id"],
        len(rows),
        batch_size,
    )

    create_query = """
    UNWIND $rows AS row
    MATCH (v:Visitor_this_year {BadgeId: row.visitor_id})
    MATCH (s:Sessions_this_year {session_id: row.target_id})
    WHERE NOT EXISTS { MATCH (v)-[:IS_RECOMMENDED {run_id: $run_id}]->(s) }
    CREATE (v)-[r:IS_RECOMMENDED]->(s)
    SET r.run_id = $run_id,
        r.run_mode = $run_mode,
        r.campaign_id = $campaign_id,
        r.show = $show,
        r.created_at = datetime(),
        r.updated_at = datetime(),
        r.lineage_enforced_at = datetime()
    RETURN count(r) AS created, collect(elementId(r)) AS rel_ids
    """

    update_query = """
    UNWIND $rows AS row
    MATCH (v:Visitor_this_year {BadgeId: row.visitor_id})
    MATCH (s:Sessions_this_year {session_id: row.target_id})
    MATCH (v)-[r:IS_RECOMMENDED {run_id: $run_id}]->(s)
    SET r.run_mode = $run_mode,
        r.campaign_id = $campaign_id,
        r.show = $show,
        r.updated_at = datetime(),
        r.lineage_enforced_at = datetime()
    RETURN count(r) AS updated, collect(elementId(r)) AS rel_ids
    """

    created_total = 0
    updated_total = 0
    relationship_changes: List[Dict[str, str]] = []
    total_batches = (len(rows) + batch_size - 1) // batch_size

    with driver.session() as session:
        for batch_idx, batch in enumerate(chunked(rows, batch_size), start=1):
            params = {
                "rows": list(batch),
                "run_id": run_ctx["run_id"],
                "run_mode": run_ctx["run_mode"],
                "campaign_id": run_ctx["campaign_id"],
                "show": run_ctx["show"],
            }

            created_record = session.run(create_query, params).single()
            updated_record = session.run(update_query, params).single()

            created_ids = set()
            if created_record:
                created_total += int(created_record.get("created", 0) or 0)
                for rel_id in created_record.get("rel_ids", []) or []:
                    rel_id = _str(rel_id)
                    if not rel_id:
                        continue
                    created_ids.add(rel_id)
                    relationship_changes.append(
                        {
                            "relationship_id": rel_id,
                            "relationship_type": "IS_RECOMMENDED",
                            "action": "created",
                        }
                    )

            if updated_record:
                updated_total += int(updated_record.get("updated", 0) or 0)
                for rel_id in updated_record.get("rel_ids", []) or []:
                    rel_id = _str(rel_id)
                    if not rel_id or rel_id in created_ids:
                        continue
                    relationship_changes.append(
                        {
                            "relationship_id": rel_id,
                            "relationship_type": "IS_RECOMMENDED",
                            "action": "metadata_updated",
                        }
                    )

            if batch_idx == 1 or batch_idx % 10 == 0 or batch_idx == total_batches:
                LOGGER.info(
                    "Apply IS_RECOMMENDED progress run_id=%s batch=%s/%s created=%s updated=%s",
                    run_ctx["run_id"],
                    batch_idx,
                    total_batches,
                    created_total,
                    updated_total,
                )

    LOGGER.info(
        "Apply IS_RECOMMENDED complete run_id=%s created=%s updated=%s",
        run_ctx["run_id"],
        created_total,
        updated_total,
    )
    return {
        "created_total": created_total,
        "updated_total": updated_total,
        "relationship_changes": relationship_changes,
    }


def verify_delivery_integrity(
    driver: Driver,
    rows: List[Dict[str, str]],
    run_ctx: Dict[str, str],
    batch_size: int,
    sample_size: int,
) -> Dict[str, Any]:
    if not rows:
        return {
            "expected_visitors": 0,
            "visitor_missing": 0,
            "delivery_missing": 0,
            "delivery_duplicates": 0,
            "delivery_without_for_visitor": 0,
            "delivery_without_for_run": 0,
            "delivery_metadata_mismatch": 0,
            "delivery_status_mismatch": 0,
            "samples": [],
        }

    LOGGER.info(
        "Verifying CampaignDelivery for run_id=%s rows=%s batch_size=%s",
        run_ctx["run_id"],
        len(rows),
        batch_size,
    )

    query = """
    UNWIND $rows AS row
    OPTIONAL MATCH (v:Visitor_this_year {BadgeId: row.visitor_id})
    OPTIONAL MATCH (d:CampaignDelivery {run_id: $run_id, visitor_id: row.visitor_id})
    WITH row, v, collect(DISTINCT d) AS deliveries
    RETURN row.visitor_id AS visitor_id,
           row.status AS expected_status,
           v IS NOT NULL AS has_visitor,
           size(deliveries) AS delivery_count,
           size([x IN deliveries WHERE x IS NOT NULL AND EXISTS { MATCH (x)-[:FOR_VISITOR]->(v) }]) AS linked_for_visitor_count,
           size([x IN deliveries WHERE x IS NOT NULL AND EXISTS { MATCH (x)-[:FOR_RUN]->(:RecommendationRun {run_id: $run_id}) }]) AS linked_for_run_count,
           size([x IN deliveries WHERE x IS NOT NULL AND (
             trim(coalesce(toString(x.run_mode), '')) <> $run_mode
             OR trim(coalesce(toString(x.campaign_id), '')) <> $campaign_id
             OR trim(coalesce(toString(x.show), '')) <> $show
           )]) AS metadata_mismatch_count,
           size([x IN deliveries WHERE x IS NOT NULL AND trim(coalesce(toString(x.status), '')) <> trim(coalesce(toString(row.status), ''))]) AS status_mismatch_count
    """

    counts = {
        "expected_visitors": len(rows),
        "visitor_missing": 0,
        "delivery_missing": 0,
        "delivery_duplicates": 0,
        "delivery_without_for_visitor": 0,
        "delivery_without_for_run": 0,
        "delivery_metadata_mismatch": 0,
        "delivery_status_mismatch": 0,
    }
    samples: List[Dict[str, Any]] = []
    total_batches = (len(rows) + batch_size - 1) // batch_size
    processed = 0

    with driver.session() as session:
        for batch_idx, batch in enumerate(chunked(rows, batch_size), start=1):
            result = session.run(
                query,
                {
                    "rows": list(batch),
                    "run_id": run_ctx["run_id"],
                    "run_mode": run_ctx["run_mode"],
                    "campaign_id": run_ctx["campaign_id"],
                    "show": run_ctx["show"],
                },
            )
            for record in result:
                processed += 1
                has_visitor = bool(record.get("has_visitor"))
                delivery_count = int(record.get("delivery_count", 0) or 0)
                linked_for_visitor_count = int(record.get("linked_for_visitor_count", 0) or 0)
                linked_for_run_count = int(record.get("linked_for_run_count", 0) or 0)
                metadata_mismatch_count = int(record.get("metadata_mismatch_count", 0) or 0)
                status_mismatch_count = int(record.get("status_mismatch_count", 0) or 0)

                if not has_visitor:
                    counts["visitor_missing"] += 1
                if delivery_count == 0:
                    counts["delivery_missing"] += 1
                if delivery_count > 1:
                    counts["delivery_duplicates"] += 1
                if delivery_count > 0 and linked_for_visitor_count == 0:
                    counts["delivery_without_for_visitor"] += 1
                if delivery_count > 0 and linked_for_run_count == 0:
                    counts["delivery_without_for_run"] += 1
                if metadata_mismatch_count > 0:
                    counts["delivery_metadata_mismatch"] += 1
                if status_mismatch_count > 0:
                    counts["delivery_status_mismatch"] += 1

                if len(samples) < sample_size and (
                    (not has_visitor)
                    or delivery_count == 0
                    or delivery_count > 1
                    or (delivery_count > 0 and linked_for_visitor_count == 0)
                    or (delivery_count > 0 and linked_for_run_count == 0)
                    or metadata_mismatch_count > 0
                    or status_mismatch_count > 0
                ):
                    samples.append(
                        {
                            "visitor_id": _str(record.get("visitor_id")),
                            "expected_status": _str(record.get("expected_status")),
                            "has_visitor": has_visitor,
                            "delivery_count": delivery_count,
                            "linked_for_visitor_count": linked_for_visitor_count,
                            "linked_for_run_count": linked_for_run_count,
                            "metadata_mismatch_count": metadata_mismatch_count,
                            "status_mismatch_count": status_mismatch_count,
                        }
                    )

            if batch_idx == 1 or batch_idx % 10 == 0 or batch_idx == total_batches:
                LOGGER.info(
                    "Verify CampaignDelivery progress run_id=%s batch=%s/%s (%s/%s)",
                    run_ctx["run_id"],
                    batch_idx,
                    total_batches,
                    processed,
                    len(rows),
                )

    LOGGER.info(
        "Verify CampaignDelivery complete run_id=%s missing=%s mismatches=%s",
        run_ctx["run_id"],
        counts["delivery_missing"],
        counts["delivery_metadata_mismatch"],
    )
    return {**counts, "samples": samples}


def apply_delivery_integrity(
    driver: Driver,
    rows: List[Dict[str, str]],
    run_ctx: Dict[str, str],
    batch_size: int,
) -> Dict[str, Any]:
    if not rows:
        return {
            "rows_submitted": 0,
            "rows_matched_visitors": 0,
            "delivery_nodes_touched": 0,
            "delivery_nodes_created": 0,
            "for_visitor_links_touched": 0,
            "for_visitor_links_created": 0,
            "for_run_links_touched": 0,
            "for_run_links_created": 0,
            "relationship_changes": [],
        }

    LOGGER.info(
        "Applying CampaignDelivery for run_id=%s rows=%s batch_size=%s",
        run_ctx["run_id"],
        len(rows),
        batch_size,
    )

    query = """
    UNWIND $rows AS row
    MATCH (rr:RecommendationRun {run_id: $run_id})
    MATCH (v:Visitor_this_year {BadgeId: row.visitor_id})

    OPTIONAL MATCH (d_existing:CampaignDelivery {run_id: $run_id, visitor_id: row.visitor_id})
    WITH row, rr, v, d_existing, d_existing IS NULL AS d_created

    MERGE (d:CampaignDelivery {run_id: $run_id, visitor_id: row.visitor_id})
    ON CREATE SET d.delivery_id = randomUUID(),
                  d.created_at = datetime()
    SET d.updated_at = datetime(),
        d.run_mode = $run_mode,
        d.campaign_id = $campaign_id,
        d.show = $show,
        d.status = row.status

    WITH row, rr, v, d, d_created
    OPTIONAL MATCH (d)-[fv_existing:FOR_VISITOR]->(v)
    WITH row, rr, v, d, d_created, fv_existing IS NULL AS fv_created
    MERGE (d)-[fv:FOR_VISITOR]->(v)

    WITH rr, d, d_created, fv, fv_created
    OPTIONAL MATCH (d)-[fr_existing:FOR_RUN]->(rr)
    WITH rr, d, d_created, fv, fv_created, fr_existing IS NULL AS fr_created
    MERGE (d)-[fr:FOR_RUN]->(rr)

    RETURN count(d) AS delivery_nodes_touched,
           sum(CASE WHEN d_created THEN 1 ELSE 0 END) AS delivery_nodes_created,
           count(fv) AS for_visitor_links_touched,
           sum(CASE WHEN fv_created THEN 1 ELSE 0 END) AS for_visitor_links_created,
           count(fr) AS for_run_links_touched,
           sum(CASE WHEN fr_created THEN 1 ELSE 0 END) AS for_run_links_created,
           [item IN collect(DISTINCT {relationship_id: elementId(fv), relationship_type: 'FOR_VISITOR', action: CASE WHEN fv_created THEN 'created' ELSE 'matched' END}) WHERE item.relationship_id IS NOT NULL] AS for_visitor_changes,
           [item IN collect(DISTINCT {relationship_id: elementId(fr), relationship_type: 'FOR_RUN', action: CASE WHEN fr_created THEN 'created' ELSE 'matched' END}) WHERE item.relationship_id IS NOT NULL] AS for_run_changes
    """

    totals = {
        "rows_submitted": len(rows),
        "rows_matched_visitors": 0,
        "delivery_nodes_touched": 0,
        "delivery_nodes_created": 0,
        "for_visitor_links_touched": 0,
        "for_visitor_links_created": 0,
        "for_run_links_touched": 0,
        "for_run_links_created": 0,
        "relationship_changes": [],
    }
    total_batches = (len(rows) + batch_size - 1) // batch_size

    with driver.session() as session:
        for batch_idx, batch in enumerate(chunked(rows, batch_size), start=1):
            record = session.run(
                query,
                {
                    "rows": list(batch),
                    "run_id": run_ctx["run_id"],
                    "run_mode": run_ctx["run_mode"],
                    "campaign_id": run_ctx["campaign_id"],
                    "show": run_ctx["show"],
                },
            ).single()
            if not record:
                continue

            matched_visitors = len(batch)
            totals["rows_matched_visitors"] += matched_visitors
            totals["delivery_nodes_touched"] += int(record.get("delivery_nodes_touched", 0) or 0)
            totals["delivery_nodes_created"] += int(record.get("delivery_nodes_created", 0) or 0)
            totals["for_visitor_links_touched"] += int(record.get("for_visitor_links_touched", 0) or 0)
            totals["for_visitor_links_created"] += int(record.get("for_visitor_links_created", 0) or 0)
            totals["for_run_links_touched"] += int(record.get("for_run_links_touched", 0) or 0)
            totals["for_run_links_created"] += int(record.get("for_run_links_created", 0) or 0)

            for item in record.get("for_visitor_changes", []) or []:
                rel_id = _str((item or {}).get("relationship_id"))
                if not rel_id:
                    continue
                totals["relationship_changes"].append(
                    {
                        "relationship_id": rel_id,
                        "relationship_type": "FOR_VISITOR",
                        "action": _str((item or {}).get("action")) or "matched",
                    }
                )
            for item in record.get("for_run_changes", []) or []:
                rel_id = _str((item or {}).get("relationship_id"))
                if not rel_id:
                    continue
                totals["relationship_changes"].append(
                    {
                        "relationship_id": rel_id,
                        "relationship_type": "FOR_RUN",
                        "action": _str((item or {}).get("action")) or "matched",
                    }
                )

            if batch_idx == 1 or batch_idx % 10 == 0 or batch_idx == total_batches:
                LOGGER.info(
                    "Apply CampaignDelivery progress run_id=%s batch=%s/%s touched=%s created=%s",
                    run_ctx["run_id"],
                    batch_idx,
                    total_batches,
                    totals["delivery_nodes_touched"],
                    totals["delivery_nodes_created"],
                )

    LOGGER.info(
        "Apply CampaignDelivery complete run_id=%s touched=%s created=%s",
        run_ctx["run_id"],
        totals["delivery_nodes_touched"],
        totals["delivery_nodes_created"],
    )
    return totals


def write_report(path_value: str, payload: Dict[str, Any]) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild RecommendationRun + IS_RECOMMENDED + CampaignDelivery graph artifacts from CSV files",
    )
    parser.add_argument("--config", default="config/config_tsl.yaml", help="Path to YAML config")
    parser.add_argument(
        "--main-csv",
        default="data/tsl/recommendations/visitor_recommendations_tsl_20260227_224725.csv",
        help="Main recommendation CSV",
    )
    parser.add_argument(
        "--control-csv",
        default="data/tsl/recommendations/control/visitor_recommendations_tsl_20260227_224725_control.csv",
        help="Control recommendation CSV",
    )
    parser.add_argument("--run-id", required=True, help="RecommendationRun.run_id")
    parser.add_argument("--run-mode", default="personal_agendas", help="RecommendationRun.run_mode")
    parser.add_argument("--campaign-id", default="tsl_conversion", help="RecommendationRun.campaign_id")
    parser.add_argument("--show", default="tsl", help="RecommendationRun.show")
    parser.add_argument("--created-at", default="", help="RecommendationRun.created_at ISO timestamp")
    parser.add_argument("--updated-at", default="", help="RecommendationRun.updated_at ISO timestamp")
    parser.add_argument("--pipeline-version", default="pa_pipeline", help="RecommendationRun.pipeline_version")
    parser.add_argument("--allocation-version", default="incremental", help="RecommendationRun.allocation_version")
    parser.add_argument(
        "--env-file",
        default="",
        help="Optional explicit .env path (overrides config env_file resolution)",
    )
    parser.add_argument("--batch-size", type=int, default=1000, help="Neo4j UNWIND batch size")
    parser.add_argument("--sample-size", type=int, default=30, help="Max sample records per section")
    parser.add_argument("--apply", action="store_true", help="Apply writes (default verify-only)")
    parser.add_argument(
        "--skip-verify-after-when-dry-run",
        action="store_true",
        help="Skip second verification pass when --apply is not set",
    )
    parser.add_argument(
        "--report-file",
        default="large_tool_results/rebuild_pa_run_from_csv_report.json",
        help="Output report JSON path",
    )
    parser.add_argument("--fail-on-issues", action="store_true", help="Exit code 2 if blockers remain")
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = (Path.cwd() / config_path).resolve()
    config = load_config(str(config_path))

    if _str(args.env_file):
        env_file_path = Path(args.env_file)
        if not env_file_path.is_absolute():
            env_file_path = (Path.cwd() / env_file_path).resolve()
        if not env_file_path.exists():
            raise FileNotFoundError(f"Explicit env file not found: {env_file_path}")
    else:
        env_file_path = resolve_env_file_path(config_path, config.get("env_file", ""))

    if env_file_path:
        load_dotenv(env_file_path)
        LOGGER.info("Loaded environment variables from %s", env_file_path)
    else:
        load_dotenv()

    main_csv = Path(args.main_csv)
    if not main_csv.is_absolute():
        main_csv = (Path.cwd() / main_csv).resolve()
    control_csv = Path(args.control_csv)
    if not control_csv.is_absolute():
        control_csv = (Path.cwd() / control_csv).resolve()

    main_data = load_pairs_from_csv(main_csv, split_status="sent")
    control_data = load_pairs_from_csv(control_csv, split_status="withheld_control")

    overlap_visitors = sorted(main_data["visitors"] & control_data["visitors"])

    status_by_visitor: Dict[str, str] = {}
    for visitor_id in main_data["visitors"]:
        status_by_visitor[visitor_id] = "sent"
    for visitor_id in control_data["visitors"]:
        status_by_visitor[visitor_id] = "withheld_control"

    all_session_pairs = set(main_data["session_pairs"]) | set(control_data["session_pairs"])
    is_recommended_rows = rows_from_pairs(all_session_pairs)
    delivery_rows = rows_from_status(status_by_visitor)

    run_ctx = {
        "run_id": _str(args.run_id),
        "run_mode": _str(args.run_mode),
        "campaign_id": _str(args.campaign_id),
        "show": _str(args.show),
        "created_at": _str(args.created_at) or now_iso(),
        "updated_at": _str(args.updated_at) or now_iso(),
        "pipeline_version": _str(args.pipeline_version),
        "allocation_version": _str(args.allocation_version),
    }
    LOGGER.info(
        "Resolved run context: run_id=%s run_mode=%s campaign_id=%s show=%s",
        run_ctx["run_id"],
        run_ctx["run_mode"],
        run_ctx["campaign_id"],
        run_ctx["show"],
    )

    credentials = resolve_neo4j_credentials(config, logger=LOGGER)
    driver = GraphDatabase.driver(credentials["uri"], auth=(credentials["username"], credentials["password"]))

    try:
        verify_before = {
            "is_recommended": verify_is_recommended(
                driver=driver,
                rows=is_recommended_rows,
                run_ctx=run_ctx,
                batch_size=args.batch_size,
                sample_size=args.sample_size,
            ),
            "campaign_delivery": verify_delivery_integrity(
                driver=driver,
                rows=delivery_rows,
                run_ctx=run_ctx,
                batch_size=args.batch_size,
                sample_size=args.sample_size,
            ),
        }

        apply_stats: Dict[str, Any] = {"applied": bool(args.apply)}
        if args.apply:
            LOGGER.info("Ensuring RecommendationRun exists for run_id=%s", run_ctx["run_id"])
            run_node_result = ensure_recommendation_run(driver, run_ctx)
            rec_apply = apply_is_recommended(
                driver=driver,
                rows=is_recommended_rows,
                run_ctx=run_ctx,
                batch_size=args.batch_size,
            )
            delivery_apply = apply_delivery_integrity(
                driver=driver,
                rows=delivery_rows,
                run_ctx=run_ctx,
                batch_size=args.batch_size,
            )
            relationship_changes = rec_apply.get("relationship_changes", []) + delivery_apply.get("relationship_changes", [])

            apply_stats["recommendation_run_enforcement"] = run_node_result
            apply_stats["is_recommended_created"] = int(rec_apply.get("created_total", 0) or 0)
            apply_stats["is_recommended_metadata_updates"] = int(rec_apply.get("updated_total", 0) or 0)
            apply_stats["campaign_delivery_enforcement"] = delivery_apply
            apply_stats["relationship_change_log"] = {
                "total_relationships_logged": len(relationship_changes),
                "relationships": relationship_changes,
            }

        if (not args.apply) and args.skip_verify_after_when_dry_run:
            LOGGER.info("Skipping verify_after because dry-run + skip flag")
            verify_after = verify_before
        else:
            verify_after = {
                "is_recommended": verify_is_recommended(
                    driver=driver,
                    rows=is_recommended_rows,
                    run_ctx=run_ctx,
                    batch_size=args.batch_size,
                    sample_size=args.sample_size,
                ),
                "campaign_delivery": verify_delivery_integrity(
                    driver=driver,
                    rows=delivery_rows,
                    run_ctx=run_ctx,
                    batch_size=args.batch_size,
                    sample_size=args.sample_size,
                ),
            }
    finally:
        driver.close()

    blockers = {
        "is_recommended_relationship_missing": verify_after["is_recommended"]["relationship_missing"],
        "is_recommended_metadata_mismatch": verify_after["is_recommended"]["metadata_mismatch_or_missing"],
        "campaign_delivery_missing": verify_after["campaign_delivery"]["delivery_missing"],
        "campaign_delivery_without_for_visitor": verify_after["campaign_delivery"]["delivery_without_for_visitor"],
        "campaign_delivery_without_for_run": verify_after["campaign_delivery"]["delivery_without_for_run"],
        "campaign_delivery_metadata_mismatch": verify_after["campaign_delivery"]["delivery_metadata_mismatch"],
    }
    has_blocker = any(int(v) > 0 for v in blockers.values())

    payload = {
        "generated_at": now_iso(),
        "scope": {
            "run_id": run_ctx["run_id"],
            "main_csv": str(main_csv),
            "control_csv": str(control_csv),
            "apply": bool(args.apply),
        },
        "run_context": run_ctx,
        "input_stats": {
            "main": main_data["stats"],
            "control": control_data["stats"],
            "overlap_visitors": len(overlap_visitors),
            "overlap_visitors_sample": overlap_visitors[: args.sample_size],
            "expected": {
                "visitors_total": len(status_by_visitor),
                "session_pairs_total": len(all_session_pairs),
            },
        },
        "verify_before": verify_before,
        "apply_stats": apply_stats,
        "verify_after": verify_after,
        "summary": {
            "status": "fail" if has_blocker else "pass",
            "blockers": blockers,
        },
    }

    report_path = write_report(args.report_file, payload)
    LOGGER.info("Report written to: %s", report_path)
    LOGGER.info("Rebuild finished with status=%s", payload["summary"]["status"])

    if args.fail_on_issues and has_blocker:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
