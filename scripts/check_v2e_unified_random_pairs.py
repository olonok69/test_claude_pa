#!/usr/bin/env python3
"""Verify V2E unified recommendations against Neo4j.

This script can either sample random pairs or full-scan all pairs from unified JSON
files (main/control), then check whether
(:Visitor_this_year)-[:IS_RECOMMENDED_EXHIBITOR]->(:Exhibitor) exists.

Optional: verify relationship metadata run_id equals an expected run id.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import ijson
from dotenv import load_dotenv
from neo4j import GraphDatabase

CURRENT_FILE = Path(__file__).resolve()
PA_ROOT = CURRENT_FILE.parents[1]
REPO_ROOT = PA_ROOT.parent
if str(PA_ROOT) not in sys.path:
    sys.path.insert(0, str(PA_ROOT))

from utils.config_utils import load_config
from utils.neo4j_utils import resolve_neo4j_credentials

LOGGER = logging.getLogger("check_v2e_unified_random_pairs")


@dataclass
class PairSample:
    source: str
    visitor_id: str
    exhibitor_uuid: str
    exhibitor_name: str


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def _str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def utc_now_iso() -> str:
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


def stream_pairs_from_unified_json(file_path: Path, source_label: str) -> Iterable[PairSample]:
    with file_path.open("rb") as handle:
        for rec in ijson.items(handle, "recommendations.item"):
            visitor_id = _str(rec.get("visitor_id"))
            if not visitor_id:
                continue
            exhibitors = rec.get("v2e_exhibitors") or []
            if not isinstance(exhibitors, list):
                continue
            for exhibitor in exhibitors:
                if not isinstance(exhibitor, dict):
                    continue
                exhibitor_uuid = _str(exhibitor.get("uuid"))
                if not exhibitor_uuid:
                    continue
                yield PairSample(
                    source=source_label,
                    visitor_id=visitor_id,
                    exhibitor_uuid=exhibitor_uuid,
                    exhibitor_name=_str(exhibitor.get("name")),
                )


def reservoir_sample_pairs(
    file_path: Path,
    source_label: str,
    sample_size: int,
    seed: int,
) -> Dict[str, Any]:
    rng = random.Random(seed)
    sample: List[PairSample] = []
    seen = 0

    for pair in stream_pairs_from_unified_json(file_path, source_label):
        seen += 1
        if len(sample) < sample_size:
            sample.append(pair)
        else:
            idx = rng.randint(1, seen)
            if idx <= sample_size:
                sample[idx - 1] = pair

    return {
        "seen_pairs": seen,
        "sample": sample,
    }


def verify_pairs_in_neo4j(driver, pairs: List[PairSample], expected_run_id: str = "") -> List[Dict[str, Any]]:
    rows = [
        {
            "source": p.source,
            "visitor_id": p.visitor_id,
            "uuid": p.exhibitor_uuid,
            "exhibitor_name": p.exhibitor_name,
        }
        for p in pairs
    ]

    query = """
    UNWIND $rows AS row
    OPTIONAL MATCH (v:Visitor_this_year {BadgeId: row.visitor_id})
    OPTIONAL MATCH (e:Exhibitor {uuid: row.uuid})
    OPTIONAL MATCH (v)-[r:IS_RECOMMENDED_EXHIBITOR]->(e)
    RETURN
      row.source AS source,
      row.visitor_id AS visitor_id,
      row.uuid AS exhibitor_uuid,
      row.exhibitor_name AS exhibitor_name,
      v IS NOT NULL AS visitor_exists,
      e IS NOT NULL AS exhibitor_exists,
      r IS NOT NULL AS relationship_exists,
      coalesce(r.run_id, '') AS rel_run_id,
      coalesce(r.campaign_id, '') AS rel_campaign_id,
      coalesce(r.run_mode, '') AS rel_run_mode,
      coalesce(r.show, '') AS rel_show
    """

    results: List[Dict[str, Any]] = []
    with driver.session() as session:
        for record in session.run(query, {"rows": rows}):
            item = {
                "source": _str(record.get("source")),
                "visitor_id": _str(record.get("visitor_id")),
                "exhibitor_uuid": _str(record.get("exhibitor_uuid")),
                "exhibitor_name": _str(record.get("exhibitor_name")),
                "visitor_exists": bool(record.get("visitor_exists")),
                "exhibitor_exists": bool(record.get("exhibitor_exists")),
                "relationship_exists": bool(record.get("relationship_exists")),
                "rel_run_id": _str(record.get("rel_run_id")),
                "rel_campaign_id": _str(record.get("rel_campaign_id")),
                "rel_run_mode": _str(record.get("rel_run_mode")),
                "rel_show": _str(record.get("rel_show")),
            }
            if expected_run_id:
                item["expected_run_id"] = expected_run_id
                item["relationship_run_id_matches"] = (
                    item["relationship_exists"] and item["rel_run_id"] == expected_run_id
                )
            results.append(item)

    return results


def _new_counter() -> Dict[str, int]:
    return {
        "sampled": 0,
        "relationship_hits": 0,
        "visitor_missing": 0,
        "exhibitor_missing": 0,
    }


def init_aggregate(expected_run_id: str = "") -> Dict[str, Any]:
    aggregate: Dict[str, Any] = {
        "sampled_pairs_total": 0,
        "relationship_hits": 0,
        "relationship_misses": 0,
        "visitor_missing": 0,
        "exhibitor_missing": 0,
        "by_source": {},
    }
    if expected_run_id:
        aggregate["expected_run_id"] = expected_run_id
        aggregate["relationship_run_id_matches"] = 0
        aggregate["relationship_run_id_mismatches_or_missing"] = 0
    return aggregate


def update_aggregate(aggregate: Dict[str, Any], rows: List[Dict[str, Any]], expected_run_id: str = "") -> None:
    for row in rows:
        aggregate["sampled_pairs_total"] += 1
        source = row.get("source", "unknown")
        bucket = aggregate["by_source"].setdefault(source, _new_counter())
        bucket["sampled"] += 1

        if row.get("relationship_exists"):
            aggregate["relationship_hits"] += 1
            bucket["relationship_hits"] += 1
        else:
            aggregate["relationship_misses"] += 1

        if not row.get("visitor_exists"):
            aggregate["visitor_missing"] += 1
            bucket["visitor_missing"] += 1

        if not row.get("exhibitor_exists"):
            aggregate["exhibitor_missing"] += 1
            bucket["exhibitor_missing"] += 1

        if expected_run_id:
            if row.get("relationship_run_id_matches") is True:
                aggregate["relationship_run_id_matches"] += 1
            else:
                aggregate["relationship_run_id_mismatches_or_missing"] += 1


def stream_pairs_in_batches(file_path: Path, source_label: str, batch_size: int) -> Iterable[List[PairSample]]:
    batch: List[PairSample] = []
    for pair in stream_pairs_from_unified_json(file_path, source_label):
        batch.append(pair)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def summarize(results: List[Dict[str, Any]], expected_run_id: str = "") -> Dict[str, Any]:
    total = len(results)
    relationship_hits = sum(1 for x in results if x["relationship_exists"])
    visitor_missing = sum(1 for x in results if not x["visitor_exists"])
    exhibitor_missing = sum(1 for x in results if not x["exhibitor_exists"])

    by_source: Dict[str, Dict[str, int]] = {}
    for row in results:
        source = row["source"]
        bucket = by_source.setdefault(
            source,
            {
                "sampled": 0,
                "relationship_hits": 0,
                "visitor_missing": 0,
                "exhibitor_missing": 0,
            },
        )
        bucket["sampled"] += 1
        if row["relationship_exists"]:
            bucket["relationship_hits"] += 1
        if not row["visitor_exists"]:
            bucket["visitor_missing"] += 1
        if not row["exhibitor_exists"]:
            bucket["exhibitor_missing"] += 1

    summary = {
        "sampled_pairs_total": total,
        "relationship_hits": relationship_hits,
        "relationship_misses": total - relationship_hits,
        "visitor_missing": visitor_missing,
        "exhibitor_missing": exhibitor_missing,
        "by_source": by_source,
    }

    if expected_run_id:
        run_id_matches = sum(
            1
            for x in results
            if x.get("relationship_run_id_matches") is True
        )
        summary["expected_run_id"] = expected_run_id
        summary["relationship_run_id_matches"] = run_id_matches
        summary["relationship_run_id_mismatches_or_missing"] = total - run_id_matches

    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Randomly verify V2E unified recommendations against Neo4j",
    )
    parser.add_argument("--config", default="PA/config/config_tsl.yaml", help="Path to YAML config")
    parser.add_argument(
        "--main-json",
        default="PA/data/tsl/recommendations/visitor_recommendations_tsl_20260224_195335_unified.json",
        help="Path to main unified recommendations JSON",
    )
    parser.add_argument(
        "--control-json",
        default="PA/data/tsl/recommendations/visitor_recommendations_tsl_20260224_195335_control_unified.json",
        help="Path to control unified recommendations JSON",
    )
    parser.add_argument("--sample-size", type=int, default=10, help="Random samples per file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--full-scan",
        action="store_true",
        help="Check all visitor->exhibitor pairs from both JSON files (streamed in batches)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=2000,
        help="Batch size for Neo4j checks in full-scan mode",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=25,
        help="Max missing-pair examples to store in report",
    )
    parser.add_argument(
        "--expected-run-id",
        default="",
        help="Optional run_id to validate on IS_RECOMMENDED_EXHIBITOR relationship metadata",
    )
    parser.add_argument(
        "--env-file",
        default="",
        help="Optional explicit .env path (overrides config env_file resolution)",
    )
    parser.add_argument(
        "--report-file",
        default="PA/large_tool_results/v2e_random_pair_neo4j_check_report.json",
        help="Path to output JSON report",
    )
    return parser


def main() -> None:
    configure_logging()
    args = build_parser().parse_args()

    config_path = Path(args.config)
    config = load_config(str(config_path))

    env_file_path = None
    if _str(args.env_file):
        explicit = Path(args.env_file)
        candidates = [
            explicit,
            Path.cwd() / explicit,
            PA_ROOT / explicit,
            REPO_ROOT / explicit,
        ]
        for candidate in candidates:
            if candidate.is_absolute() and candidate.exists():
                env_file_path = candidate
                break
            if candidate.exists():
                env_file_path = candidate.resolve()
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

    main_json = Path(args.main_json)
    control_json = Path(args.control_json)
    if not main_json.exists():
        raise FileNotFoundError(f"Main unified JSON not found: {main_json}")
    if not control_json.exists():
        raise FileNotFoundError(f"Control unified JSON not found: {control_json}")

    sample_size = max(1, int(args.sample_size))
    seed = int(args.seed)
    batch_size = max(100, int(args.batch_size))
    max_examples = max(0, int(args.max_examples))
    expected_run_id = _str(args.expected_run_id)

    credentials = resolve_neo4j_credentials(config, logger=LOGGER)
    driver = GraphDatabase.driver(
        credentials["uri"],
        auth=(credentials["username"], credentials["password"]),
    )

    try:
        if args.full_scan:
            aggregate = init_aggregate(expected_run_id=expected_run_id)
            missing_examples: List[Dict[str, Any]] = []
            seen_pairs = {"main": 0, "control": 0}

            for source_label, file_path in (("main", main_json), ("control", control_json)):
                LOGGER.info("Starting full scan for %s: %s", source_label, file_path)
                for batch in stream_pairs_in_batches(file_path, source_label, batch_size):
                    seen_pairs[source_label] += len(batch)
                    verification_rows = verify_pairs_in_neo4j(
                        driver,
                        batch,
                        expected_run_id=expected_run_id,
                    )
                    update_aggregate(aggregate, verification_rows, expected_run_id=expected_run_id)

                    if max_examples > 0 and len(missing_examples) < max_examples:
                        for row in verification_rows:
                            if row.get("relationship_exists"):
                                continue
                            missing_examples.append(row)
                            if len(missing_examples) >= max_examples:
                                break

                    if aggregate["sampled_pairs_total"] % (batch_size * 20) == 0:
                        LOGGER.info(
                            "Progress: checked=%s hits=%s misses=%s",
                            aggregate["sampled_pairs_total"],
                            aggregate["relationship_hits"],
                            aggregate["relationship_misses"],
                        )

            summary = aggregate
            report = {
                "generated_at": utc_now_iso(),
                "mode": "full_scan",
                "inputs": {
                    "config": str(config_path),
                    "main_json": str(main_json),
                    "control_json": str(control_json),
                    "batch_size": batch_size,
                    "expected_run_id": expected_run_id,
                },
                "scan": {
                    "main_seen_pairs": int(seen_pairs["main"]),
                    "control_seen_pairs": int(seen_pairs["control"]),
                    "checked_pairs_total": int(summary["sampled_pairs_total"]),
                },
                "summary": summary,
                "missing_examples": missing_examples,
            }
        else:
            main_sample = reservoir_sample_pairs(main_json, "main", sample_size, seed)
            control_sample = reservoir_sample_pairs(control_json, "control", sample_size, seed + 1)

            sampled_pairs: List[PairSample] = []
            sampled_pairs.extend(main_sample["sample"])
            sampled_pairs.extend(control_sample["sample"])

            verification = verify_pairs_in_neo4j(
                driver,
                sampled_pairs,
                expected_run_id=expected_run_id,
            )
            summary = summarize(verification, expected_run_id=expected_run_id)

            report = {
                "generated_at": utc_now_iso(),
                "mode": "sample",
                "inputs": {
                    "config": str(config_path),
                    "main_json": str(main_json),
                    "control_json": str(control_json),
                    "sample_size_per_file": sample_size,
                    "seed": seed,
                    "expected_run_id": expected_run_id,
                },
                "sampling": {
                    "main_seen_pairs": int(main_sample["seen_pairs"]),
                    "control_seen_pairs": int(control_sample["seen_pairs"]),
                    "sampled_pairs_total": len(sampled_pairs),
                },
                "summary": summary,
                "samples": verification,
            }
    finally:
        driver.close()

    report_path = Path(args.report_file)
    if not report_path.is_absolute():
        report_path = REPO_ROOT / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report["summary"], indent=2))
    print(f"Report written to: {report_path}")


if __name__ == "__main__":
    main()
