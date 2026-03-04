#!/usr/bin/env python3
"""Reconcile legacy recommendation lineage and delivery integrity from unified JSON files.

Scope:
- Reads main/control unified reconciled JSON files.
- Verifies expected recommendation edges exist in Neo4j:
  - (:Visitor_this_year {BadgeId})-[:IS_RECOMMENDED]->(:Sessions_this_year {session_id})
  - (:Visitor_this_year {BadgeId})-[:IS_RECOMMENDED_EXHIBITOR]->(:Exhibitor {uuid})
- Enforces run metadata on existing recommendation edges.
- Enforces CampaignDelivery integrity per expected visitor:
  - MERGE CampaignDelivery(run_id, visitor_id)
  - MERGE (d)-[:FOR_VISITOR]->(v)
  - MERGE (d)-[:FOR_RUN]->(rr)
  - set metadata/status (sent vs withheld_control) according to input files.

Notes:
- IS_RECOMMENDED / IS_RECOMMENDED_EXHIBITOR edges are created when missing (apply mode).
- Default mode is verify-only; pass --apply to enforce writes.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import ijson
from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase
from neo4j import exceptions as neo4j_exceptions


CURRENT_FILE = Path(__file__).resolve()
PA_ROOT = CURRENT_FILE.parents[1]
REPO_ROOT = PA_ROOT.parent
if str(PA_ROOT) not in sys.path:
    sys.path.insert(0, str(PA_ROOT))

from utils.config_utils import load_config
from utils.neo4j_utils import resolve_neo4j_credentials


LOGGER = logging.getLogger("reconcile_legacy_delivery_from_unified")


def _build_transient_exception_types() -> Tuple[type, ...]:
    candidates = [
        getattr(neo4j_exceptions, "ServiceUnavailable", None),
        getattr(neo4j_exceptions, "SessionExpired", None),
        getattr(neo4j_exceptions, "DatabaseUnavailable", None),
        getattr(neo4j_exceptions, "TransientError", None),
    ]
    return tuple(item for item in candidates if isinstance(item, type))


TRANSIENT_NEO4J_EXCEPTIONS = _build_transient_exception_types()


def is_transient_neo4j_exception(exc: Exception) -> bool:
    if TRANSIENT_NEO4J_EXCEPTIONS and isinstance(exc, TRANSIENT_NEO4J_EXCEPTIONS):
        return True
    if isinstance(exc, neo4j_exceptions.Neo4jError):
        code = _str(getattr(exc, "code", ""))
        if "TransientError" in code or "DatabaseUnavailable" in code:
            return True
    message = _str(exc)
    return (
        "DatabaseUnavailable" in message
        or "ServiceUnavailable" in message
        or "session expired" in message.lower()
    )


def run_batch_with_retry(
    operation: str,
    batch_idx: int,
    total_batches: int,
    max_attempts: int,
    backoff_seconds: float,
    fn,
):
    attempts = max(1, int(max_attempts))
    base_backoff = max(0.0, float(backoff_seconds))

    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:
            is_retryable = is_transient_neo4j_exception(exc)
            if (not is_retryable) or attempt >= attempts:
                raise
            sleep_seconds = base_backoff * attempt
            LOGGER.warning(
                "Transient Neo4j error during %s batch %s/%s (attempt %s/%s): %s. Retrying in %.1fs",
                operation,
                batch_idx,
                total_batches,
                attempt,
                attempts,
                exc,
                sleep_seconds,
            )
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)


def _str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def chunked(items: Sequence[Any], size: int) -> Iterable[Sequence[Any]]:
    step = max(1, int(size))
    for index in range(0, len(items), step):
        yield items[index : index + step]


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

    for candidate in [
        Path.cwd() / env_path,
        config_path.parent / env_path,
        PA_ROOT / env_path,
        REPO_ROOT / env_path,
    ]:
        if candidate.exists():
            return candidate
    return None


def load_unified_expectations(path: Path, split_status: str) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Unified JSON not found: {path}")

    LOGGER.info("Loading unified expectations: split=%s path=%s", split_status, path)

    visitors: Set[str] = set()
    session_pairs: Set[Tuple[str, str]] = set()
    exhibitor_pairs: Set[Tuple[str, str]] = set()

    missing_visitor_id = 0
    missing_session_id = 0
    missing_exhibitor_uuid = 0
    processed_rows = 0

    with path.open("rb") as handle:
        for item in ijson.items(handle, "recommendations.item"):
            if not isinstance(item, dict):
                continue
            processed_rows += 1
            if processed_rows % 2000 == 0:
                LOGGER.info(
                    "Parsed %s rows from %s (split=%s)",
                    processed_rows,
                    path.name,
                    split_status,
                )

            visitor_id = _str(item.get("visitor_id") or item.get("BadgeId") or item.get("badge_id"))
            if not visitor_id:
                missing_visitor_id += 1
                continue
            visitors.add(visitor_id)

            for session in item.get("sessions", []) or []:
                session_id = _str((session or {}).get("session_id"))
                if not session_id:
                    missing_session_id += 1
                    continue
                session_pairs.add((visitor_id, session_id))

            for exhibitor in item.get("v2e_exhibitors", []) or []:
                exhibitor_uuid = _str((exhibitor or {}).get("uuid"))
                if not exhibitor_uuid:
                    missing_exhibitor_uuid += 1
                    continue
                exhibitor_pairs.add((visitor_id, exhibitor_uuid))

    payload = {
        "path": str(path),
        "split_status": split_status,
        "visitors": visitors,
        "session_pairs": session_pairs,
        "exhibitor_pairs": exhibitor_pairs,
        "stats": {
            "visitors": len(visitors),
            "session_pairs": len(session_pairs),
            "exhibitor_pairs": len(exhibitor_pairs),
            "rows_missing_visitor_id": missing_visitor_id,
            "rows_missing_session_id": missing_session_id,
            "rows_missing_exhibitor_uuid": missing_exhibitor_uuid,
        },
    }
    LOGGER.info(
        "Loaded split=%s rows=%s visitors=%s session_pairs=%s exhibitor_pairs=%s",
        split_status,
        processed_rows,
        payload["stats"]["visitors"],
        payload["stats"]["session_pairs"],
        payload["stats"]["exhibitor_pairs"],
    )
    return payload


def rows_from_pairs(pairs: Set[Tuple[str, str]]) -> List[Dict[str, str]]:
    return [{"visitor_id": v, "target_id": t} for v, t in sorted(pairs)]


def rows_from_status(status_map: Dict[str, str]) -> List[Dict[str, str]]:
    return [{"visitor_id": v, "status": s} for v, s in sorted(status_map.items())]


def fetch_run_context(driver: Driver, run_id: str) -> Dict[str, str]:
    query = """
    MATCH (rr:RecommendationRun {run_id: $run_id})
    RETURN rr.run_id AS run_id,
           coalesce(rr.run_mode, '') AS run_mode,
           coalesce(rr.campaign_id, '') AS campaign_id,
           coalesce(rr.show, '') AS show,
           coalesce(toString(rr.created_at), '') AS created_at,
        coalesce(toString(rr.updated_at), '') AS updated_at,
           coalesce(toString(rr.migrated_at), '') AS migrated_at,
        coalesce(rr.pipeline_version, '') AS pipeline_version,
        coalesce(rr.allocation_version, '') AS allocation_version
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
        "created_at": _str(record.get("created_at")),
        "updated_at": _str(record.get("updated_at")),
        "migrated_at": _str(record.get("migrated_at")),
        "pipeline_version": _str(record.get("pipeline_version")),
        "allocation_version": _str(record.get("allocation_version")),
    }


def fetch_existing_run_context(driver: Driver, run_id: str) -> Optional[Dict[str, str]]:
    query = """
    MATCH (rr:RecommendationRun {run_id: $run_id})
    RETURN rr.run_id AS run_id,
           coalesce(rr.run_mode, '') AS run_mode,
           coalesce(rr.campaign_id, '') AS campaign_id,
           coalesce(rr.show, '') AS show,
           coalesce(toString(rr.created_at), '') AS created_at,
           coalesce(toString(rr.updated_at), '') AS updated_at,
           coalesce(toString(rr.migrated_at), '') AS migrated_at,
           coalesce(rr.pipeline_version, '') AS pipeline_version,
           coalesce(rr.allocation_version, '') AS allocation_version
    LIMIT 1
    """
    with driver.session() as session:
        record = session.run(query, {"run_id": run_id}).single()
    if not record:
        return None
    return {
        "run_id": _str(record.get("run_id")),
        "run_mode": _str(record.get("run_mode")),
        "campaign_id": _str(record.get("campaign_id")),
        "show": _str(record.get("show")),
        "created_at": _str(record.get("created_at")),
        "updated_at": _str(record.get("updated_at")),
        "migrated_at": _str(record.get("migrated_at")),
        "pipeline_version": _str(record.get("pipeline_version")),
        "allocation_version": _str(record.get("allocation_version")),
    }


def build_run_context(args: argparse.Namespace, config: Dict[str, Any], existing_ctx: Optional[Dict[str, str]]) -> Dict[str, str]:
    base_run_id = _str(args.run_id)
    suffix = _str(args.run_id_suffix)
    run_id = f"{base_run_id}_{suffix}" if suffix else base_run_id

    default_show = _str((config.get("show") or {}).get("name") if isinstance(config.get("show"), dict) else config.get("show"))
    created_default = _str(existing_ctx.get("created_at") if existing_ctx else "") or now_iso()

    run_ctx = {
        "run_id": run_id,
        "run_mode": _str(args.run_mode) or _str(existing_ctx.get("run_mode") if existing_ctx else "") or "personal_agendas",
        "campaign_id": _str(args.campaign_id) or _str(existing_ctx.get("campaign_id") if existing_ctx else "") or "tsl_conversion",
        "show": _str(args.show) or _str(existing_ctx.get("show") if existing_ctx else "") or default_show,
        "created_at": _str(args.created_at) or created_default,
        "updated_at": _str(args.updated_at)
        or _str(existing_ctx.get("updated_at") if existing_ctx else "")
        or created_default,
        "migrated_at": _str(existing_ctx.get("migrated_at") if existing_ctx else ""),
        "pipeline_version": _str(args.pipeline_version)
        or _str(existing_ctx.get("pipeline_version") if existing_ctx else "")
        or "pa_pipeline",
        "allocation_version": _str(args.allocation_version)
        or _str(existing_ctx.get("allocation_version") if existing_ctx else "")
        or "full",
    }
    return run_ctx


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
        record = session.run(
            query,
            {
                "run_id": run_ctx["run_id"],
                "run_mode": run_ctx["run_mode"],
                "campaign_id": run_ctx["campaign_id"],
                "show": run_ctx["show"],
                "created_at": run_ctx["created_at"],
                "updated_at": run_ctx["updated_at"],
                "pipeline_version": run_ctx["pipeline_version"],
                "allocation_version": run_ctx["allocation_version"],
            },
        ).single()
    return {
        "node_created": bool(record.get("was_created")) if record else False,
        "node_id": _str(record.get("node_id")) if record else "",
    }


def verify_relationship_pairs(
    driver: Driver,
    relationship_type: str,
    target_label: str,
    target_key: str,
    rows: List[Dict[str, str]],
    run_ctx: Dict[str, str],
    batch_size: int,
    sample_size: int,
    neo4j_retry_attempts: int,
    neo4j_retry_backoff_seconds: float,
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
        "Verifying %s pairs for %s (rows=%s, batch_size=%s)",
        relationship_type,
        run_ctx["run_id"],
        len(rows),
        batch_size,
    )

    query = f"""
        UNWIND $rows AS row
        OPTIONAL MATCH (v:Visitor_this_year {{BadgeId: row.visitor_id}})
        OPTIONAL MATCH (t:{target_label} {{{target_key}: row.target_id}})
        OPTIONAL MATCH (v)-[r:{relationship_type}]->(t)
        WITH row, v, t, collect(r) AS rels
        WITH row, v, t,
                 [rel IN rels WHERE trim(coalesce(toString(rel.run_id), '')) = $run_id] AS run_rels,
                 rels
        RETURN row.visitor_id AS visitor_id,
                     row.target_id AS target_id,
                     v IS NOT NULL AS has_visitor,
                     t IS NOT NULL AS has_target,
                     size(run_rels) > 0 AS has_relationship,
                     size(run_rels) AS run_relationship_count,
                     size(rels) AS relationship_count_any,
                     size([rel IN run_rels WHERE (
                         trim(coalesce(toString(rel.run_mode), '')) = $run_mode
                         AND trim(coalesce(toString(rel.campaign_id), '')) = $campaign_id
                         AND trim(coalesce(toString(rel.show), '')) = $show
                     )]) AS metadata_match_count,
                     coalesce(
                         head([rel IN run_rels | trim(coalesce(toString(rel.run_id), ''))]),
                         ''
                     ) AS rel_run_id,
                     coalesce(
                         head([rel IN run_rels | trim(coalesce(toString(rel.run_mode), ''))]),
                         ''
                     ) AS rel_run_mode,
                     coalesce(
                         head([rel IN run_rels | trim(coalesce(toString(rel.campaign_id), ''))]),
                         ''
                     ) AS rel_campaign_id,
                     coalesce(
                         head([rel IN run_rels | trim(coalesce(toString(rel.show), ''))]),
                         ''
                     ) AS rel_show
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
    processed_pairs = 0

    for batch_idx, batch in enumerate(chunked(rows, batch_size), start=1):
        batch_rows = list(batch)

        def _run_batch() -> List[Any]:
            with driver.session() as session:
                return list(
                    session.run(
                        query,
                        {
                            "rows": batch_rows,
                            "run_id": run_ctx["run_id"],
                            "run_mode": run_ctx["run_mode"],
                            "campaign_id": run_ctx["campaign_id"],
                            "show": run_ctx["show"],
                        },
                    )
                )

        records = run_batch_with_retry(
            operation=f"verify {relationship_type}",
            batch_idx=batch_idx,
            total_batches=total_batches,
            max_attempts=neo4j_retry_attempts,
            backoff_seconds=neo4j_retry_backoff_seconds,
            fn=_run_batch,
        )

        for rec in records:
            processed_pairs += 1
            has_visitor = bool(rec.get("has_visitor"))
            has_target = bool(rec.get("has_target"))
            has_relationship = bool(rec.get("has_relationship"))

            if not has_visitor:
                counts["visitor_missing"] += 1
            if not has_target:
                counts["target_missing"] += 1
            if has_visitor and has_target and not has_relationship:
                counts["relationship_missing"] += 1
            if has_relationship:
                counts["relationship_found"] += 1
                metadata_match_count = int(rec.get("metadata_match_count", 0) or 0)
                mismatch = metadata_match_count == 0
                if mismatch:
                    counts["metadata_mismatch_or_missing"] += 1
                    if len(samples) < sample_size:
                        samples.append(
                            {
                                "visitor_id": _str(rec.get("visitor_id")),
                                "target_id": _str(rec.get("target_id")),
                                "relationship_count_any": int(rec.get("relationship_count_any", 0) or 0),
                                "run_relationship_count": int(rec.get("run_relationship_count", 0) or 0),
                                "metadata_match_count": metadata_match_count,
                                "rel_run_id": _str(rec.get("rel_run_id")),
                                "rel_run_mode": _str(rec.get("rel_run_mode")),
                                "rel_campaign_id": _str(rec.get("rel_campaign_id")),
                                "rel_show": _str(rec.get("rel_show")),
                            }
                        )
            elif len(samples) < sample_size and (not has_visitor or not has_target or not has_relationship):
                samples.append(
                    {
                        "visitor_id": _str(rec.get("visitor_id")),
                        "target_id": _str(rec.get("target_id")),
                        "has_visitor": has_visitor,
                        "has_target": has_target,
                        "has_relationship": has_relationship,
                    }
                )
        if batch_idx == 1 or batch_idx % 10 == 0 or batch_idx == total_batches:
            LOGGER.info(
                "Verify progress %s for %s: batch %s/%s (%s/%s pairs)",
                relationship_type,
                run_ctx["run_id"],
                batch_idx,
                total_batches,
                processed_pairs,
                len(rows),
            )

    LOGGER.info(
        "Verify complete %s for %s: found=%s missing=%s metadata_mismatch=%s",
        relationship_type,
        run_ctx["run_id"],
        counts["relationship_found"],
        counts["relationship_missing"],
        counts["metadata_mismatch_or_missing"],
    )
    return {**counts, "samples": samples}


def enforce_relationship_presence_and_metadata(
    driver: Driver,
    relationship_type: str,
    target_label: str,
    target_key: str,
    rows: List[Dict[str, str]],
    run_ctx: Dict[str, str],
    batch_size: int,
    neo4j_retry_attempts: int,
    neo4j_retry_backoff_seconds: float,
) -> Dict[str, Any]:
    if not rows:
        return {
            "updated_total": 0,
            "relationship_changes": [],
        }

    LOGGER.info(
        "Applying %s enforcement for %s (rows=%s, batch_size=%s)",
        relationship_type,
        run_ctx["run_id"],
        len(rows),
        batch_size,
    )

    create_query = f"""
    UNWIND $rows AS row
    MATCH (v:Visitor_this_year {{BadgeId: row.visitor_id}})
    MATCH (t:{target_label} {{{target_key}: row.target_id}})
    WHERE NOT EXISTS {{ MATCH (v)-[:{relationship_type} {{run_id: $run_id}}]->(t) }}
    CREATE (v)-[r:{relationship_type}]->(t)
    SET r.run_id = $run_id,
        r.run_mode = $run_mode,
        r.campaign_id = $campaign_id,
        r.show = $show,
        r.created_at = datetime(),
        r.updated_at = datetime(),
        r.lineage_enforced_at = datetime()
    RETURN count(r) AS created,
           collect(elementId(r)) AS rel_ids
    """

    update_query = f"""
    UNWIND $rows AS row
    MATCH (v:Visitor_this_year {{BadgeId: row.visitor_id}})
    MATCH (t:{target_label} {{{target_key}: row.target_id}})
    MATCH (v)-[r:{relationship_type} {{run_id: $run_id}}]->(t)
    SET r.run_mode = $run_mode,
        r.campaign_id = $campaign_id,
        r.show = $show,
        r.updated_at = datetime(),
        r.lineage_enforced_at = datetime()
    RETURN count(r) AS updated,
           collect(elementId(r)) AS rel_ids
    """

    created_total = 0
    updated_total = 0
    relationship_changes: List[Dict[str, str]] = []
    total_batches = (len(rows) + batch_size - 1) // batch_size

    for batch_idx, batch in enumerate(chunked(rows, batch_size), start=1):
            batch_rows = list(batch)

            def _run_create():
                with driver.session() as session:
                    return session.run(
                        create_query,
                        {
                            "rows": batch_rows,
                            "run_id": run_ctx["run_id"],
                            "run_mode": run_ctx["run_mode"],
                            "campaign_id": run_ctx["campaign_id"],
                            "show": run_ctx["show"],
                        },
                    ).single()

            created_record = run_batch_with_retry(
                operation=f"apply create {relationship_type}",
                batch_idx=batch_idx,
                total_batches=total_batches,
                max_attempts=neo4j_retry_attempts,
                backoff_seconds=neo4j_retry_backoff_seconds,
                fn=_run_create,
            )
            if created_record:
                created_total += int(created_record.get("created", 0) or 0)
                for rel_id in created_record.get("rel_ids", []) or []:
                    rel_id = _str(rel_id)
                    if not rel_id:
                        continue
                    relationship_changes.append(
                        {
                            "relationship_id": rel_id,
                            "relationship_type": relationship_type,
                            "action": "created",
                        }
                    )

            def _run_update():
                with driver.session() as session:
                    return session.run(
                        update_query,
                        {
                            "rows": batch_rows,
                            "run_id": run_ctx["run_id"],
                            "run_mode": run_ctx["run_mode"],
                            "campaign_id": run_ctx["campaign_id"],
                            "show": run_ctx["show"],
                        },
                    ).single()

            updated_record = run_batch_with_retry(
                operation=f"apply update {relationship_type}",
                batch_idx=batch_idx,
                total_batches=total_batches,
                max_attempts=neo4j_retry_attempts,
                backoff_seconds=neo4j_retry_backoff_seconds,
                fn=_run_update,
            )
            if not updated_record:
                continue

            updated_total += int(updated_record.get("updated", 0) or 0)

            created_ids = {
                _str(item) for item in (created_record.get("rel_ids", []) if created_record else []) if _str(item)
            }
            for rel_id in updated_record.get("rel_ids", []) or []:
                rel_id = _str(rel_id)
                if not rel_id:
                    continue
                if rel_id in created_ids:
                    continue
                relationship_changes.append(
                    {
                        "relationship_id": rel_id,
                        "relationship_type": relationship_type,
                        "action": "metadata_updated",
                    }
                )

            if batch_idx == 1 or batch_idx % 10 == 0 or batch_idx == total_batches:
                LOGGER.info(
                    "Apply progress %s for %s: batch %s/%s created=%s updated=%s",
                    relationship_type,
                    run_ctx["run_id"],
                    batch_idx,
                    total_batches,
                    created_total,
                    updated_total,
                )

    LOGGER.info(
        "Apply complete %s for %s: created=%s updated=%s",
        relationship_type,
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
    delivery_rows: List[Dict[str, str]],
    run_ctx: Dict[str, str],
    sample_size: int,
    batch_size: int,
    neo4j_retry_attempts: int,
    neo4j_retry_backoff_seconds: float,
) -> Dict[str, Any]:
    if not delivery_rows:
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
        "Verifying CampaignDelivery integrity for %s (rows=%s, batch_size=%s)",
        run_ctx["run_id"],
        len(delivery_rows),
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
           size([d IN deliveries WHERE d IS NOT NULL AND EXISTS { MATCH (d)-[:FOR_VISITOR]->(v) }]) AS linked_for_visitor_count,
           size([d IN deliveries WHERE d IS NOT NULL AND EXISTS { MATCH (d)-[:FOR_RUN]->(:RecommendationRun {run_id: $run_id}) }]) AS linked_for_run_count,
           size([d IN deliveries WHERE d IS NOT NULL AND (
             trim(coalesce(toString(d.run_mode), '')) <> $run_mode
             OR trim(coalesce(toString(d.campaign_id), '')) <> $campaign_id
             OR trim(coalesce(toString(d.show), '')) <> $show
           )]) AS metadata_mismatch_count,
           size([d IN deliveries WHERE d IS NOT NULL AND trim(coalesce(toString(d.status), '')) <> trim(coalesce(toString(row.status), ''))]) AS status_mismatch_count
    """

    counts = {
        "expected_visitors": len(delivery_rows),
        "visitor_missing": 0,
        "delivery_missing": 0,
        "delivery_duplicates": 0,
        "delivery_without_for_visitor": 0,
        "delivery_without_for_run": 0,
        "delivery_metadata_mismatch": 0,
        "delivery_status_mismatch": 0,
    }
    samples: List[Dict[str, Any]] = []
    total_batches = (len(delivery_rows) + batch_size - 1) // batch_size
    processed_rows = 0

    for batch_idx, batch in enumerate(chunked(delivery_rows, batch_size), start=1):
            batch_rows = list(batch)

            def _run_batch() -> List[Any]:
                with driver.session() as session:
                    return list(
                        session.run(
                            query,
                            {
                                "rows": batch_rows,
                                "run_id": run_ctx["run_id"],
                                "run_mode": run_ctx["run_mode"],
                                "campaign_id": run_ctx["campaign_id"],
                                "show": run_ctx["show"],
                            },
                        )
                    )

            records = run_batch_with_retry(
                operation="verify CampaignDelivery",
                batch_idx=batch_idx,
                total_batches=total_batches,
                max_attempts=neo4j_retry_attempts,
                backoff_seconds=neo4j_retry_backoff_seconds,
                fn=_run_batch,
            )
            for rec in records:
                processed_rows += 1
                has_visitor = bool(rec.get("has_visitor"))
                delivery_count = int(rec.get("delivery_count", 0) or 0)
                linked_for_visitor_count = int(rec.get("linked_for_visitor_count", 0) or 0)
                linked_for_run_count = int(rec.get("linked_for_run_count", 0) or 0)
                metadata_mismatch_count = int(rec.get("metadata_mismatch_count", 0) or 0)
                status_mismatch_count = int(rec.get("status_mismatch_count", 0) or 0)

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
                            "visitor_id": _str(rec.get("visitor_id")),
                            "expected_status": _str(rec.get("expected_status")),
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
                    "Verify CampaignDelivery progress for %s: batch %s/%s (%s/%s rows)",
                    run_ctx["run_id"],
                    batch_idx,
                    total_batches,
                    processed_rows,
                    len(delivery_rows),
                )

    LOGGER.info(
        "Verify CampaignDelivery complete for %s: missing=%s duplicates=%s metadata_mismatch=%s",
        run_ctx["run_id"],
        counts["delivery_missing"],
        counts["delivery_duplicates"],
        counts["delivery_metadata_mismatch"],
    )
    return {**counts, "samples": samples}


def enforce_delivery_integrity(
    driver: Driver,
    delivery_rows: List[Dict[str, str]],
    run_ctx: Dict[str, str],
    batch_size: int,
    neo4j_retry_attempts: int,
    neo4j_retry_backoff_seconds: float,
) -> Dict[str, Any]:
    if not delivery_rows:
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
        "Applying CampaignDelivery enforcement for %s (rows=%s, batch_size=%s)",
        run_ctx["run_id"],
        len(delivery_rows),
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

    WITH rr, v, d, d_created, fv, fv_created
    OPTIONAL MATCH (d)-[fr_existing:FOR_RUN]->(rr)
    WITH rr, v, d, d_created, fv, fv_created, fr_existing IS NULL AS fr_created
    MERGE (d)-[fr:FOR_RUN]->(rr)

    RETURN count(v) AS matched_visitors,
           count(d) AS delivery_nodes_touched,
           sum(CASE WHEN d_created THEN 1 ELSE 0 END) AS delivery_nodes_created,
           count(fv) AS for_visitor_links_touched,
           sum(CASE WHEN fv_created THEN 1 ELSE 0 END) AS for_visitor_links_created,
           count(fr) AS for_run_links_touched,
           sum(CASE WHEN fr_created THEN 1 ELSE 0 END) AS for_run_links_created,
           [item IN collect(DISTINCT {relationship_id: elementId(fv), relationship_type: 'FOR_VISITOR', action: CASE WHEN fv_created THEN 'created' ELSE 'matched' END}) WHERE item.relationship_id IS NOT NULL] AS for_visitor_changes,
           [item IN collect(DISTINCT {relationship_id: elementId(fr), relationship_type: 'FOR_RUN', action: CASE WHEN fr_created THEN 'created' ELSE 'matched' END}) WHERE item.relationship_id IS NOT NULL] AS for_run_changes
    """

    totals = {
        "rows_submitted": len(delivery_rows),
        "rows_matched_visitors": 0,
        "delivery_nodes_touched": 0,
        "delivery_nodes_created": 0,
        "for_visitor_links_touched": 0,
        "for_visitor_links_created": 0,
        "for_run_links_touched": 0,
        "for_run_links_created": 0,
        "relationship_changes": [],
    }
    total_batches = (len(delivery_rows) + batch_size - 1) // batch_size

    for batch_idx, batch in enumerate(chunked(delivery_rows, batch_size), start=1):
            batch_rows = list(batch)

            def _run_batch():
                with driver.session() as session:
                    return session.run(
                        query,
                        {
                            "rows": batch_rows,
                            "run_id": run_ctx["run_id"],
                            "run_mode": run_ctx["run_mode"],
                            "campaign_id": run_ctx["campaign_id"],
                            "show": run_ctx["show"],
                        },
                    ).single()

            record = run_batch_with_retry(
                operation="apply CampaignDelivery",
                batch_idx=batch_idx,
                total_batches=total_batches,
                max_attempts=neo4j_retry_attempts,
                backoff_seconds=neo4j_retry_backoff_seconds,
                fn=_run_batch,
            )
            if not record:
                continue
            totals["rows_matched_visitors"] += int(record.get("matched_visitors", 0) or 0)
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
                    "Apply CampaignDelivery progress for %s: batch %s/%s touched=%s created=%s",
                    run_ctx["run_id"],
                    batch_idx,
                    total_batches,
                    totals["delivery_nodes_touched"],
                    totals["delivery_nodes_created"],
                )

    LOGGER.info(
        "Apply CampaignDelivery complete for %s: touched=%s created=%s for_visitor_created=%s for_run_created=%s",
        run_ctx["run_id"],
        totals["delivery_nodes_touched"],
        totals["delivery_nodes_created"],
        totals["for_visitor_links_created"],
        totals["for_run_links_created"],
    )
    return totals


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconcile legacy recommendation relationships and CampaignDelivery links from unified files",
    )
    parser.add_argument("--config", default="config/config_tsl.yaml", help="Path to YAML config")
    parser.add_argument(
        "--main-unified",
        default="data/tsl/recommendations/visitor_recommendations_tsl_20260214_144216_unified_reconciled.json",
        help="Main unified reconciled recommendations JSON",
    )
    parser.add_argument(
        "--control-unified",
        default="data/tsl/recommendations/visitor_recommendations_tsl_20260214_144216_control_unified_reconciled.json",
        help="Control unified reconciled recommendations JSON",
    )
    parser.add_argument("--run-id", default="legacy_pre_traceability", help="RecommendationRun.run_id")
    parser.add_argument(
        "--run-id-suffix",
        default="",
        help="Optional suffix appended to --run-id (e.g. hash/timestamp fragment)",
    )
    parser.add_argument("--run-mode", default="", help="RecommendationRun.run_mode override")
    parser.add_argument("--campaign-id", default="", help="RecommendationRun.campaign_id override")
    parser.add_argument("--show", default="", help="RecommendationRun.show override")
    parser.add_argument("--created-at", default="", help="RecommendationRun.created_at ISO timestamp override")
    parser.add_argument("--updated-at", default="", help="RecommendationRun.updated_at ISO timestamp override")
    parser.add_argument("--pipeline-version", default="", help="RecommendationRun.pipeline_version override")
    parser.add_argument("--allocation-version", default="", help="RecommendationRun.allocation_version override")
    parser.add_argument(
        "--env-file",
        default="",
        help="Optional explicit .env path (overrides config env_file resolution)",
    )
    parser.add_argument("--batch-size", type=int, default=1000, help="Neo4j UNWIND batch size")
    parser.add_argument("--sample-size", type=int, default=30, help="Max sample records per section")
    parser.add_argument(
        "--neo4j-retry-attempts",
        type=int,
        default=5,
        help="Max retry attempts per Neo4j batch for transient availability errors",
    )
    parser.add_argument(
        "--neo4j-retry-backoff-seconds",
        type=float,
        default=2.0,
        help="Base backoff seconds per retry (linear: attempt * backoff)",
    )
    parser.add_argument("--apply", action="store_true", help="Apply writes (default verify-only)")
    parser.add_argument(
        "--report-file",
        default="large_tool_results/reconcile_legacy_delivery_from_unified_report.json",
        help="Output report JSON path",
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit with code 2 when verify_after still has blockers",
    )
    parser.add_argument(
        "--skip-verify-after-when-dry-run",
        action="store_true",
        help="Skip second verification pass when --apply is not set",
    )
    return parser.parse_args()


def write_report(path_value: str, payload: Dict[str, Any]) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    return path


def main() -> None:
    configure_logging()
    args = parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = (Path.cwd() / config_path).resolve()
    config = load_config(str(config_path))

    env_file_path: Optional[Path]
    if _str(args.env_file):
        explicit = Path(args.env_file)
        env_file_path = explicit if explicit.is_absolute() else (Path.cwd() / explicit).resolve()
        if not env_file_path.exists():
            raise FileNotFoundError(f"Explicit env file not found: {env_file_path}")
    else:
        env_file_path = resolve_env_file_path(config_path, config.get("env_file", ""))

    if env_file_path:
        load_dotenv(env_file_path)
        LOGGER.info("Loaded environment variables from %s", env_file_path)
    else:
        load_dotenv()

    main_path = Path(args.main_unified)
    if not main_path.is_absolute():
        main_path = (Path.cwd() / main_path).resolve()
    control_path = Path(args.control_unified)
    if not control_path.is_absolute():
        control_path = (Path.cwd() / control_path).resolve()

    main_expected = load_unified_expectations(main_path, split_status="sent")
    control_expected = load_unified_expectations(control_path, split_status="withheld_control")

    overlap_visitors = sorted(main_expected["visitors"] & control_expected["visitors"])

    expected_status_by_visitor: Dict[str, str] = {}
    for visitor_id in main_expected["visitors"]:
        expected_status_by_visitor[visitor_id] = "sent"
    for visitor_id in control_expected["visitors"]:
        expected_status_by_visitor[visitor_id] = "withheld_control"

    all_session_pairs = set(main_expected["session_pairs"]) | set(control_expected["session_pairs"])
    all_exhibitor_pairs = set(main_expected["exhibitor_pairs"]) | set(control_expected["exhibitor_pairs"])
    delivery_rows = rows_from_status(expected_status_by_visitor)

    credentials = resolve_neo4j_credentials(config, logger=LOGGER)
    driver = GraphDatabase.driver(credentials["uri"], auth=(credentials["username"], credentials["password"]))

    try:
        LOGGER.info("Building run context for requested run_id=%s", args.run_id)
        requested_run_id = _str(args.run_id)
        effective_run_id = f"{requested_run_id}_{_str(args.run_id_suffix)}" if _str(args.run_id_suffix) else requested_run_id
        existing_ctx = fetch_existing_run_context(driver, effective_run_id)
        run_ctx = build_run_context(args, config, existing_ctx)
        LOGGER.info(
            "Resolved run context: run_id=%s run_mode=%s campaign_id=%s show=%s",
            run_ctx["run_id"],
            run_ctx["run_mode"],
            run_ctx["campaign_id"],
            run_ctx["show"],
        )

        apply_stats: Dict[str, Any] = {"applied": bool(args.apply)}
        if args.apply:
            LOGGER.info("Ensuring RecommendationRun node exists for run_id=%s", run_ctx["run_id"])
            run_node_apply = ensure_recommendation_run(driver, run_ctx)
            apply_stats["recommendation_run_enforcement"] = run_node_apply

        verify_before = {
            "is_recommended": verify_relationship_pairs(
                driver=driver,
                relationship_type="IS_RECOMMENDED",
                target_label="Sessions_this_year",
                target_key="session_id",
                rows=rows_from_pairs(all_session_pairs),
                run_ctx=run_ctx,
                batch_size=args.batch_size,
                sample_size=args.sample_size,
                neo4j_retry_attempts=args.neo4j_retry_attempts,
                neo4j_retry_backoff_seconds=args.neo4j_retry_backoff_seconds,
            ),
            "is_recommended_exhibitor": verify_relationship_pairs(
                driver=driver,
                relationship_type="IS_RECOMMENDED_EXHIBITOR",
                target_label="Exhibitor",
                target_key="uuid",
                rows=rows_from_pairs(all_exhibitor_pairs),
                run_ctx=run_ctx,
                batch_size=args.batch_size,
                sample_size=args.sample_size,
                neo4j_retry_attempts=args.neo4j_retry_attempts,
                neo4j_retry_backoff_seconds=args.neo4j_retry_backoff_seconds,
            ),
            "campaign_delivery": verify_delivery_integrity(
                driver=driver,
                delivery_rows=delivery_rows,
                run_ctx=run_ctx,
                sample_size=args.sample_size,
                batch_size=args.batch_size,
                neo4j_retry_attempts=args.neo4j_retry_attempts,
                neo4j_retry_backoff_seconds=args.neo4j_retry_backoff_seconds,
            ),
        }
        if args.apply:
            rec_apply = enforce_relationship_presence_and_metadata(
                driver=driver,
                relationship_type="IS_RECOMMENDED",
                target_label="Sessions_this_year",
                target_key="session_id",
                rows=rows_from_pairs(all_session_pairs),
                run_ctx=run_ctx,
                batch_size=args.batch_size,
                neo4j_retry_attempts=args.neo4j_retry_attempts,
                neo4j_retry_backoff_seconds=args.neo4j_retry_backoff_seconds,
            )
            exh_apply = enforce_relationship_presence_and_metadata(
                driver=driver,
                relationship_type="IS_RECOMMENDED_EXHIBITOR",
                target_label="Exhibitor",
                target_key="uuid",
                rows=rows_from_pairs(all_exhibitor_pairs),
                run_ctx=run_ctx,
                batch_size=args.batch_size,
                neo4j_retry_attempts=args.neo4j_retry_attempts,
                neo4j_retry_backoff_seconds=args.neo4j_retry_backoff_seconds,
            )
            delivery_apply = enforce_delivery_integrity(
                driver=driver,
                delivery_rows=delivery_rows,
                run_ctx=run_ctx,
                batch_size=args.batch_size,
                neo4j_retry_attempts=args.neo4j_retry_attempts,
                neo4j_retry_backoff_seconds=args.neo4j_retry_backoff_seconds,
            )

            relationship_changes = (
                rec_apply.get("relationship_changes", [])
                + exh_apply.get("relationship_changes", [])
                + delivery_apply.get("relationship_changes", [])
            )

            apply_stats["is_recommended_created"] = int(rec_apply.get("created_total", 0) or 0)
            apply_stats["is_recommended_metadata_updates"] = int(rec_apply.get("updated_total", 0) or 0)
            apply_stats["is_recommended_exhibitor_created"] = int(exh_apply.get("created_total", 0) or 0)
            apply_stats["is_recommended_exhibitor_metadata_updates"] = int(exh_apply.get("updated_total", 0) or 0)
            apply_stats["campaign_delivery_enforcement"] = delivery_apply
            apply_stats["relationship_change_log"] = {
                "total_relationships_logged": len(relationship_changes),
                "relationships": relationship_changes,
            }

        if (not args.apply) and args.skip_verify_after_when_dry_run:
            LOGGER.info(
                "Skipping verify_after pass because --skip-verify-after-when-dry-run is enabled and --apply is false"
            )
            verify_after = verify_before
        else:
            verify_after = {
                "is_recommended": verify_relationship_pairs(
                    driver=driver,
                    relationship_type="IS_RECOMMENDED",
                    target_label="Sessions_this_year",
                    target_key="session_id",
                    rows=rows_from_pairs(all_session_pairs),
                    run_ctx=run_ctx,
                    batch_size=args.batch_size,
                    sample_size=args.sample_size,
                    neo4j_retry_attempts=args.neo4j_retry_attempts,
                    neo4j_retry_backoff_seconds=args.neo4j_retry_backoff_seconds,
                ),
                "is_recommended_exhibitor": verify_relationship_pairs(
                    driver=driver,
                    relationship_type="IS_RECOMMENDED_EXHIBITOR",
                    target_label="Exhibitor",
                    target_key="uuid",
                    rows=rows_from_pairs(all_exhibitor_pairs),
                    run_ctx=run_ctx,
                    batch_size=args.batch_size,
                    sample_size=args.sample_size,
                    neo4j_retry_attempts=args.neo4j_retry_attempts,
                    neo4j_retry_backoff_seconds=args.neo4j_retry_backoff_seconds,
                ),
                "campaign_delivery": verify_delivery_integrity(
                    driver=driver,
                    delivery_rows=delivery_rows,
                    run_ctx=run_ctx,
                    sample_size=args.sample_size,
                    batch_size=args.batch_size,
                    neo4j_retry_attempts=args.neo4j_retry_attempts,
                    neo4j_retry_backoff_seconds=args.neo4j_retry_backoff_seconds,
                ),
            }
    finally:
        driver.close()

    blockers = {
        "is_recommended_relationship_missing": verify_after["is_recommended"]["relationship_missing"],
        "is_recommended_metadata_mismatch": verify_after["is_recommended"]["metadata_mismatch_or_missing"],
        "is_recommended_exhibitor_relationship_missing": verify_after["is_recommended_exhibitor"]["relationship_missing"],
        "is_recommended_exhibitor_metadata_mismatch": verify_after["is_recommended_exhibitor"]["metadata_mismatch_or_missing"],
        "campaign_delivery_missing": verify_after["campaign_delivery"]["delivery_missing"],
        "campaign_delivery_without_for_visitor": verify_after["campaign_delivery"]["delivery_without_for_visitor"],
        "campaign_delivery_without_for_run": verify_after["campaign_delivery"]["delivery_without_for_run"],
        "campaign_delivery_metadata_mismatch": verify_after["campaign_delivery"]["delivery_metadata_mismatch"],
    }
    has_blocker = any(int(v) > 0 for v in blockers.values())

    payload: Dict[str, Any] = {
        "generated_at": now_iso(),
        "scope": {
            "requested_run_id": requested_run_id,
            "run_id": run_ctx["run_id"],
            "main_unified": str(main_path),
            "control_unified": str(control_path),
            "apply": bool(args.apply),
        },
        "run_context": run_ctx,
        "input_stats": {
            "main": main_expected["stats"],
            "control": control_expected["stats"],
            "overlap_visitors": len(overlap_visitors),
            "overlap_visitors_sample": overlap_visitors[: args.sample_size],
            "expected": {
                "visitors_total": len(expected_status_by_visitor),
                "session_pairs_total": len(all_session_pairs),
                "exhibitor_pairs_total": len(all_exhibitor_pairs),
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
    LOGGER.info("Reconciliation completed with status=%s", payload["summary"]["status"])

    if args.fail_on_issues and has_blocker:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
