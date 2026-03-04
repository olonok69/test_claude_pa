#!/usr/bin/env python3
"""One-time lineage backfill for recommendation relationships in Neo4j.

Purpose:
- Preserve a protected run (e.g., engagement run).
- Reassign all other/missing relationship lineage to a legacy run.

By default, this script only backfills missing run_id relationships.
Use --include-non-protected-run-ids to also rewrite relationships whose run_id is
present but different from the protected run_id.
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


LOGGER = logging.getLogger("backfill_relationship_run_lineage")


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


def fetch_run_context(driver: Driver, run_id: str) -> Dict[str, str]:
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


def relationship_counts(driver: Driver, relationship_type: str, protected_run_id: str, legacy_run_id: str) -> Dict[str, int]:
    query = f"""
    MATCH ()-[r:{relationship_type}]->()
    WITH r,
         trim(coalesce(toString(r.run_id), '')) AS rid
    RETURN count(r) AS total,
           sum(CASE WHEN rid = '' THEN 1 ELSE 0 END) AS missing_run_id,
           sum(CASE WHEN rid = $protected_run_id THEN 1 ELSE 0 END) AS protected_run_id,
           sum(CASE WHEN rid = $legacy_run_id THEN 1 ELSE 0 END) AS legacy_run_id,
           sum(CASE WHEN rid <> '' AND rid <> $protected_run_id AND rid <> $legacy_run_id THEN 1 ELSE 0 END) AS other_run_id
    """
    with driver.session() as session:
        record = session.run(
            query,
            {
                "protected_run_id": protected_run_id,
                "legacy_run_id": legacy_run_id,
            },
        ).single()

    if not record:
        return {
            "total": 0,
            "missing_run_id": 0,
            "protected_run_id": 0,
            "legacy_run_id": 0,
            "other_run_id": 0,
        }

    return {
        "total": int(record.get("total") or 0),
        "missing_run_id": int(record.get("missing_run_id") or 0),
        "protected_run_id": int(record.get("protected_run_id") or 0),
        "legacy_run_id": int(record.get("legacy_run_id") or 0),
        "other_run_id": int(record.get("other_run_id") or 0),
    }


def backfill_relationship_type(
    driver: Driver,
    relationship_type: str,
    protected_run_id: str,
    legacy_context: Dict[str, str],
    include_non_protected_run_ids: bool,
    batch_size: int,
    timestamp: str,
) -> int:
    if include_non_protected_run_ids:
        where_clause = "trim(coalesce(toString(r.run_id), '')) <> $protected_run_id"
    else:
        where_clause = "trim(coalesce(toString(r.run_id), '')) = ''"

    query = f"""
    MATCH ()-[r:{relationship_type}]->()
    WHERE {where_clause}
    WITH r LIMIT $batch_size
    SET r.run_id = $legacy_run_id,
        r.run_mode = $legacy_run_mode,
        r.campaign_id = $legacy_campaign_id,
        r.show = $legacy_show,
        r.migrated_at = $timestamp,
        r.updated_at = coalesce(r.updated_at, $timestamp)
    RETURN count(r) AS value
    """

    updated_total = 0
    with driver.session() as session:
        while True:
            record = session.run(
                query,
                {
                    "protected_run_id": protected_run_id,
                    "legacy_run_id": legacy_context["run_id"],
                    "legacy_run_mode": legacy_context["run_mode"],
                    "legacy_campaign_id": legacy_context["campaign_id"],
                    "legacy_show": legacy_context["show"],
                    "timestamp": timestamp,
                    "batch_size": int(batch_size),
                },
            ).single()
            changed = int(record.get("value") or 0) if record else 0
            if changed == 0:
                break
            updated_total += changed
            LOGGER.info("Updated %s: +%d", relationship_type, changed)
    return updated_total


def parser() -> argparse.ArgumentParser:
    argp = argparse.ArgumentParser(
        description="Backfill relationship run lineage while preserving one protected run_id",
    )
    argp.add_argument("--config", default="config/config_tsl.yaml", help="Path to config YAML")
    argp.add_argument("--env-file", default="", help="Optional explicit .env path override")
    argp.add_argument(
        "--protected-run-id",
        required=True,
        help="Run id that must never be reassigned (e.g. tsl_engagement_...)",
    )
    argp.add_argument(
        "--legacy-run-id",
        default="legacy_pre_traceability",
        help="Run id to assign to relationships that are backfilled",
    )
    argp.add_argument(
        "--include-non-protected-run-ids",
        action="store_true",
        help="Also rewrite relationships with run_id set and not equal to protected run_id",
    )
    argp.add_argument("--batch-size", type=int, default=50000, help="Batch size per update loop")
    argp.add_argument("--dry-run", action="store_true", help="Only print counts, do not write")
    argp.add_argument(
        "--report-file",
        default="",
        help="Optional JSON report output path",
    )
    return argp


def maybe_write_report(report_file: str, payload: Dict[str, Any]) -> None:
    if not _str(report_file):
        return
    path = Path(report_file)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    LOGGER.info("Report written to: %s", path)


def main() -> None:
    configure_logging()
    args = parser().parse_args()

    config_path = Path(args.config)
    config = load_config(str(config_path))

    env_file = _str(args.env_file) or _str(config.get("env_file"))
    env_path = resolve_env_file_path(config_path, env_file)
    if env_path:
        load_dotenv(env_path)
        LOGGER.info("Loaded environment file: %s", env_path)
    else:
        load_dotenv()
        if env_file:
            LOGGER.warning("Configured env file not found: %s", env_file)

    credentials = resolve_neo4j_credentials(config, logger=LOGGER)
    driver = GraphDatabase.driver(
        credentials["uri"],
        auth=(credentials["username"], credentials["password"]),
    )

    report: Dict[str, Any] = {
        "timestamp": utc_now_iso(),
        "dry_run": bool(args.dry_run),
        "protected_run_id": _str(args.protected_run_id),
        "legacy_run_id": _str(args.legacy_run_id),
        "include_non_protected_run_ids": bool(args.include_non_protected_run_ids),
        "before": {},
        "updated": {},
        "after": {},
    }

    try:
        protected_context = fetch_run_context(driver, _str(args.protected_run_id))
        legacy_context = fetch_run_context(driver, _str(args.legacy_run_id))

        LOGGER.info(
            "Protected run: run_id=%s mode=%s campaign_id=%s show=%s",
            protected_context["run_id"],
            protected_context["run_mode"],
            protected_context["campaign_id"],
            protected_context["show"],
        )
        LOGGER.info(
            "Legacy run target: run_id=%s mode=%s campaign_id=%s show=%s",
            legacy_context["run_id"],
            legacy_context["run_mode"],
            legacy_context["campaign_id"],
            legacy_context["show"],
        )

        rel_types = ["IS_RECOMMENDED", "IS_RECOMMENDED_EXHIBITOR"]
        for rel_type in rel_types:
            report["before"][rel_type] = relationship_counts(
                driver,
                rel_type,
                _str(args.protected_run_id),
                _str(args.legacy_run_id),
            )

        if args.dry_run:
            print(json.dumps(report, indent=2, ensure_ascii=False))
            maybe_write_report(args.report_file, report)
            return

        ts = utc_now_iso()
        for rel_type in rel_types:
            updated = backfill_relationship_type(
                driver=driver,
                relationship_type=rel_type,
                protected_run_id=_str(args.protected_run_id),
                legacy_context=legacy_context,
                include_non_protected_run_ids=bool(args.include_non_protected_run_ids),
                batch_size=int(args.batch_size),
                timestamp=ts,
            )
            report["updated"][rel_type] = updated

        for rel_type in rel_types:
            report["after"][rel_type] = relationship_counts(
                driver,
                rel_type,
                _str(args.protected_run_id),
                _str(args.legacy_run_id),
            )

        print(json.dumps(report, indent=2, ensure_ascii=False))
        maybe_write_report(args.report_file, report)

    finally:
        driver.close()


if __name__ == "__main__":
    main()
