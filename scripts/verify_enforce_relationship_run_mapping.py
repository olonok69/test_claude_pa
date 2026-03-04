#!/usr/bin/env python3
"""Verify and enforce relationship run lineage from unified recommendation JSON files.

For each mapping entry (unified JSON -> RecommendationRun.run_id), this script:
1) Extracts expected relationship pairs:
   - IS_RECOMMENDED: (visitor_id, session_id)
   - IS_RECOMMENDED_EXHIBITOR: (visitor_id, exhibitor_uuid)
2) Verifies current Neo4j relationship presence and run_id alignment.
3) Optionally enforces run metadata on existing relationships via --apply.

Safety:
- Default mode is verify-only (no writes).
- Fails if the same pair is assigned to different run_ids across mapping entries.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass
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


LOGGER = logging.getLogger("verify_enforce_relationship_run_mapping")


@dataclass
class RunContext:
    run_id: str
    run_mode: str
    campaign_id: str
    show: str


def _str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def utc_now_iso() -> str:
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


def parse_mapping_entry(raw: str) -> Tuple[Path, str]:
    if "::" not in raw:
        raise ValueError(f"Invalid --mapping entry '{raw}'. Expected format: <json_path>::<run_id>")
    left, right = raw.split("::", 1)
    json_path = Path(_str(left))
    run_id = _str(right)
    if not json_path:
        raise ValueError(f"Invalid --mapping entry '{raw}': empty json path")
    if not run_id:
        raise ValueError(f"Invalid --mapping entry '{raw}': empty run_id")
    if not json_path.is_absolute():
        json_path = (Path.cwd() / json_path).resolve()
    return json_path, run_id


def load_unified_json_pairs(json_path: Path) -> Tuple[Set[Tuple[str, str]], Set[Tuple[str, str]], Dict[str, int]]:
    if not json_path.exists():
        raise FileNotFoundError(f"Unified JSON not found: {json_path}")

    with json_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    recommendations = payload.get("recommendations", []) or []

    pa_pairs: Set[Tuple[str, str]] = set()
    v2e_pairs: Set[Tuple[str, str]] = set()
    missing_visitor = 0
    missing_session = 0
    missing_exhibitor_uuid = 0

    for item in recommendations:
        visitor_id = _str(item.get("visitor_id"))
        if not visitor_id:
            missing_visitor += 1
            continue

        for session in item.get("sessions", []) or []:
            session_id = _str((session or {}).get("session_id"))
            if not session_id:
                missing_session += 1
                continue
            pa_pairs.add((visitor_id, session_id))

        for exhibitor in item.get("v2e_exhibitors", []) or []:
            exhibitor_uuid = _str((exhibitor or {}).get("uuid"))
            if not exhibitor_uuid:
                missing_exhibitor_uuid += 1
                continue
            v2e_pairs.add((visitor_id, exhibitor_uuid))

    stats = {
        "recommendation_rows": len(recommendations),
        "pa_pairs": len(pa_pairs),
        "v2e_pairs": len(v2e_pairs),
        "rows_missing_visitor_id": missing_visitor,
        "rows_missing_session_id": missing_session,
        "rows_missing_exhibitor_uuid": missing_exhibitor_uuid,
    }
    return pa_pairs, v2e_pairs, stats


def fetch_run_context(driver: Driver, run_id: str) -> RunContext:
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
    return RunContext(
        run_id=_str(record.get("run_id")),
        run_mode=_str(record.get("run_mode")),
        campaign_id=_str(record.get("campaign_id")),
        show=_str(record.get("show")),
    )


def verify_pairs(
    driver: Driver,
    relationship_type: str,
    target_label: str,
    target_key: str,
    rows: List[Dict[str, str]],
    expected_run_id: str,
    batch_size: int,
    log_every_records: int,
) -> Dict[str, int]:
    if not rows:
        return {
            "pairs_total": 0,
            "visitor_missing": 0,
            "target_missing": 0,
            "relationship_missing": 0,
            "relationship_found": 0,
            "run_id_matches": 0,
            "run_id_mismatches_or_missing": 0,
        }

    query = f"""
    UNWIND $rows AS row
    OPTIONAL MATCH (v:Visitor_this_year {{BadgeId: row.visitor_id}})
    OPTIONAL MATCH (t:{target_label} {{{target_key}: row.target_id}})
    OPTIONAL MATCH (v)-[r:{relationship_type}]->(t)
    RETURN
      sum(CASE WHEN v IS NULL THEN 1 ELSE 0 END) AS visitor_missing,
      sum(CASE WHEN t IS NULL THEN 1 ELSE 0 END) AS target_missing,
      sum(CASE WHEN v IS NOT NULL AND t IS NOT NULL AND r IS NULL THEN 1 ELSE 0 END) AS relationship_missing,
      sum(CASE WHEN r IS NOT NULL THEN 1 ELSE 0 END) AS relationship_found,
      sum(CASE WHEN r IS NOT NULL AND trim(coalesce(toString(r.run_id), '')) = $expected_run_id THEN 1 ELSE 0 END) AS run_id_matches,
      sum(CASE WHEN r IS NOT NULL AND trim(coalesce(toString(r.run_id), '')) <> $expected_run_id THEN 1 ELSE 0 END) AS run_id_mismatches_or_missing
    """

    aggregate = defaultdict(int)
    processed_rows = 0
    next_log_at = max(1, int(log_every_records))
    total_rows = len(rows)
    with driver.session() as session:
        for batch in chunked(rows, batch_size):
            batch_len = len(batch)
            record = session.run(
                query,
                {
                    "rows": list(batch),
                    "expected_run_id": expected_run_id,
                },
            ).single()
            if not record:
                processed_rows += batch_len
                while processed_rows >= next_log_at and next_log_at <= total_rows:
                    LOGGER.info(
                        "Verify progress [%s]: processed=%d/%d",
                        relationship_type,
                        processed_rows,
                        total_rows,
                    )
                    next_log_at += max(1, int(log_every_records))
                continue
            for key in [
                "visitor_missing",
                "target_missing",
                "relationship_missing",
                "relationship_found",
                "run_id_matches",
                "run_id_mismatches_or_missing",
            ]:
                aggregate[key] += int(record.get(key) or 0)
            processed_rows += batch_len
            while processed_rows >= next_log_at and next_log_at <= total_rows:
                LOGGER.info(
                    "Verify progress [%s]: processed=%d/%d",
                    relationship_type,
                    processed_rows,
                    total_rows,
                )
                next_log_at += max(1, int(log_every_records))

    LOGGER.info("Verify complete [%s]: processed=%d/%d", relationship_type, processed_rows, total_rows)

    return {
        "pairs_total": len(rows),
        "visitor_missing": int(aggregate["visitor_missing"]),
        "target_missing": int(aggregate["target_missing"]),
        "relationship_missing": int(aggregate["relationship_missing"]),
        "relationship_found": int(aggregate["relationship_found"]),
        "run_id_matches": int(aggregate["run_id_matches"]),
        "run_id_mismatches_or_missing": int(aggregate["run_id_mismatches_or_missing"]),
    }


def enforce_pairs(
    driver: Driver,
    relationship_type: str,
    target_label: str,
    target_key: str,
    rows: List[Dict[str, str]],
    run_context: RunContext,
    batch_size: int,
    log_every_records: int,
) -> int:
    if not rows:
        return 0

    query = f"""
    UNWIND $rows AS row
    MATCH (v:Visitor_this_year {{BadgeId: row.visitor_id}})
    MATCH (t:{target_label} {{{target_key}: row.target_id}})
    MATCH (v)-[r:{relationship_type}]->(t)
    SET r.run_id = $run_id,
        r.run_mode = $run_mode,
        r.campaign_id = $campaign_id,
        r.show = $show,
        r.updated_at = $timestamp,
        r.lineage_enforced_at = $timestamp
    RETURN count(r) AS value
    """

    updated_total = 0
    processed_rows = 0
    next_log_at = max(1, int(log_every_records))
    total_rows = len(rows)
    with driver.session() as session:
        for batch in chunked(rows, batch_size):
            batch_len = len(batch)
            record = session.run(
                query,
                {
                    "rows": list(batch),
                    "run_id": run_context.run_id,
                    "run_mode": run_context.run_mode,
                    "campaign_id": run_context.campaign_id,
                    "show": run_context.show,
                    "timestamp": utc_now_iso(),
                },
            ).single()
            updated_total += int(record.get("value") or 0) if record else 0
            processed_rows += batch_len
            while processed_rows >= next_log_at and next_log_at <= total_rows:
                LOGGER.info(
                    "Apply progress [%s -> %s]: processed=%d/%d updated_so_far=%d",
                    relationship_type,
                    run_context.run_id,
                    processed_rows,
                    total_rows,
                    updated_total,
                )
                next_log_at += max(1, int(log_every_records))

    LOGGER.info(
        "Apply complete [%s -> %s]: processed=%d/%d updated_total=%d",
        relationship_type,
        run_context.run_id,
        processed_rows,
        total_rows,
        updated_total,
    )

    return updated_total


def build_rows(pairs: Set[Tuple[str, str]]) -> List[Dict[str, str]]:
    return [{"visitor_id": visitor_id, "target_id": target_id} for visitor_id, target_id in sorted(pairs)]


def write_report(path_value: str, payload: Dict[str, Any]) -> None:
    path = Path(path_value)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    LOGGER.info("Report written to: %s", path)


def parser() -> argparse.ArgumentParser:
    argp = argparse.ArgumentParser(
        description="Verify and enforce run lineage on IS_RECOMMENDED and IS_RECOMMENDED_EXHIBITOR",
    )
    argp.add_argument("--config", default="config/config_tsl.yaml", help="Path to YAML config")
    argp.add_argument("--env-file", default="", help="Optional explicit .env file")
    argp.add_argument(
        "--mapping",
        action="append",
        required=True,
        help=(
            "Unified JSON to run mapping entry: <json_path>::<run_id>. "
            "Repeat for each file."
        ),
    )
    argp.add_argument("--batch-size", type=int, default=2000, help="Neo4j batch size")
    argp.add_argument(
        "--log-every-records",
        type=int,
        default=50000,
        help="Emit progress logs every N processed pairs per phase",
    )
    argp.add_argument("--apply", action="store_true", help="Apply updates (default is verify-only)")
    argp.add_argument(
        "--report-file",
        default="large_tool_results/verify_enforce_relationship_run_mapping.json",
        help="JSON report output path",
    )
    return argp


def main() -> None:
    configure_logging()
    args = parser().parse_args()

    config_path = Path(args.config)
    config = load_config(str(config_path))
    env_file_value = _str(args.env_file) or _str(config.get("env_file"))
    env_path = resolve_env_file_path(config_path, env_file_value)
    if env_path:
        load_dotenv(env_path)
        LOGGER.info("Loaded environment file: %s", env_path)
    else:
        load_dotenv()
        if env_file_value:
            LOGGER.warning("Configured env_file '%s' not found; using ambient env", env_file_value)

    credentials = resolve_neo4j_credentials(config, logger=LOGGER)
    driver = GraphDatabase.driver(
        credentials["uri"],
        auth=(credentials["username"], credentials["password"]),
    )

    report: Dict[str, Any] = {
        "timestamp": utc_now_iso(),
        "apply": bool(args.apply),
        "mappings": [],
        "conflicts": [],
    }

    try:
        parsed_mappings: List[Tuple[Path, str]] = [parse_mapping_entry(item) for item in args.mapping]

        # Prevent ambiguous ownership assignments across mappings.
        pa_pair_owner: Dict[Tuple[str, str], str] = {}
        v2e_pair_owner: Dict[Tuple[str, str], str] = {}

        mapping_payloads: List[Dict[str, Any]] = []
        for json_path, run_id in parsed_mappings:
            pa_pairs, v2e_pairs, source_stats = load_unified_json_pairs(json_path)
            mapping_payload = {
                "json_path": str(json_path),
                "run_id": run_id,
                "source_stats": source_stats,
                "pa_pairs": pa_pairs,
                "v2e_pairs": v2e_pairs,
            }
            mapping_payloads.append(mapping_payload)

            for pair in pa_pairs:
                previous = pa_pair_owner.get(pair)
                if previous and previous != run_id:
                    report["conflicts"].append(
                        {
                            "relationship_type": "IS_RECOMMENDED",
                            "pair": {"visitor_id": pair[0], "target_id": pair[1]},
                            "run_id_a": previous,
                            "run_id_b": run_id,
                        }
                    )
                pa_pair_owner[pair] = run_id

            for pair in v2e_pairs:
                previous = v2e_pair_owner.get(pair)
                if previous and previous != run_id:
                    report["conflicts"].append(
                        {
                            "relationship_type": "IS_RECOMMENDED_EXHIBITOR",
                            "pair": {"visitor_id": pair[0], "target_id": pair[1]},
                            "run_id_a": previous,
                            "run_id_b": run_id,
                        }
                    )
                v2e_pair_owner[pair] = run_id

        if report["conflicts"]:
            sample = report["conflicts"][:20]
            raise RuntimeError(
                "Found conflicting pair ownership across mappings. "
                f"Total conflicts={len(report['conflicts'])}. Sample={sample}"
            )

        run_context_cache: Dict[str, RunContext] = {}
        for entry in mapping_payloads:
            run_id = _str(entry["run_id"])
            if run_id not in run_context_cache:
                run_context_cache[run_id] = fetch_run_context(driver, run_id)

            pa_rows = build_rows(entry["pa_pairs"])
            v2e_rows = build_rows(entry["v2e_pairs"])

            LOGGER.info(
                "Processing mapping: file=%s run_id=%s pa_pairs=%d v2e_pairs=%d",
                entry["json_path"],
                run_id,
                len(pa_rows),
                len(v2e_rows),
            )

            verify_pa = verify_pairs(
                driver=driver,
                relationship_type="IS_RECOMMENDED",
                target_label="Sessions_this_year",
                target_key="session_id",
                rows=pa_rows,
                expected_run_id=run_id,
                batch_size=int(args.batch_size),
                log_every_records=int(args.log_every_records),
            )
            verify_v2e = verify_pairs(
                driver=driver,
                relationship_type="IS_RECOMMENDED_EXHIBITOR",
                target_label="Exhibitor",
                target_key="uuid",
                rows=v2e_rows,
                expected_run_id=run_id,
                batch_size=int(args.batch_size),
                log_every_records=int(args.log_every_records),
            )

            mapping_report: Dict[str, Any] = {
                "json_path": entry["json_path"],
                "run_id": run_id,
                "run_context": {
                    "run_mode": run_context_cache[run_id].run_mode,
                    "campaign_id": run_context_cache[run_id].campaign_id,
                    "show": run_context_cache[run_id].show,
                },
                "source_stats": entry["source_stats"],
                "verify": {
                    "IS_RECOMMENDED": verify_pa,
                    "IS_RECOMMENDED_EXHIBITOR": verify_v2e,
                },
                "enforced": {
                    "IS_RECOMMENDED": 0,
                    "IS_RECOMMENDED_EXHIBITOR": 0,
                },
            }

            if args.apply:
                ctx = run_context_cache[run_id]
                mapping_report["enforced"]["IS_RECOMMENDED"] = enforce_pairs(
                    driver=driver,
                    relationship_type="IS_RECOMMENDED",
                    target_label="Sessions_this_year",
                    target_key="session_id",
                    rows=pa_rows,
                    run_context=ctx,
                    batch_size=int(args.batch_size),
                    log_every_records=int(args.log_every_records),
                )
                mapping_report["enforced"]["IS_RECOMMENDED_EXHIBITOR"] = enforce_pairs(
                    driver=driver,
                    relationship_type="IS_RECOMMENDED_EXHIBITOR",
                    target_label="Exhibitor",
                    target_key="uuid",
                    rows=v2e_rows,
                    run_context=ctx,
                    batch_size=int(args.batch_size),
                    log_every_records=int(args.log_every_records),
                )

                mapping_report["verify_after"] = {
                    "IS_RECOMMENDED": verify_pairs(
                        driver=driver,
                        relationship_type="IS_RECOMMENDED",
                        target_label="Sessions_this_year",
                        target_key="session_id",
                        rows=pa_rows,
                        expected_run_id=run_id,
                        batch_size=int(args.batch_size),
                        log_every_records=int(args.log_every_records),
                    ),
                    "IS_RECOMMENDED_EXHIBITOR": verify_pairs(
                        driver=driver,
                        relationship_type="IS_RECOMMENDED_EXHIBITOR",
                        target_label="Exhibitor",
                        target_key="uuid",
                        rows=v2e_rows,
                        expected_run_id=run_id,
                        batch_size=int(args.batch_size),
                        log_every_records=int(args.log_every_records),
                    ),
                }

            report["mappings"].append(mapping_report)

        write_report(args.report_file, report)
        print(json.dumps(report, indent=2, ensure_ascii=False))

    finally:
        driver.close()


if __name__ == "__main__":
    main()
