#!/usr/bin/env python3
"""Audit RecommendationRun integrity for post-analysis readiness.

This script evaluates all (or selected) RecommendationRun records and reports
potential issues that could affect post-analysis reliability:

Per-run checks:
- RecommendationRun uniqueness by run_id
- CampaignDelivery integrity (missing FOR_VISITOR / FOR_RUN links)
- CampaignDelivery metadata alignment with run context (run_mode/campaign/show)
- IS_RECOMMENDED metadata alignment with run context
- IS_RECOMMENDED_EXHIBITOR metadata alignment with run context
- Basic coverage stats (relationship and delivery counts)

Global checks:
- Relationships missing run_id metadata (IS_RECOMMENDED / IS_RECOMMENDED_EXHIBITOR)

Output:
- JSON report with `overall_status` (pass|warning|fail), per-run findings,
  and global findings.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

CURRENT_FILE = Path(__file__).resolve()
PA_ROOT = CURRENT_FILE.parents[1]
REPO_ROOT = PA_ROOT.parent
if str(PA_ROOT) not in sys.path:
    sys.path.insert(0, str(PA_ROOT))

from utils.config_utils import load_config
from utils.neo4j_utils import resolve_neo4j_credentials


LOGGER = logging.getLogger("audit_recommendation_runs_post_analysis")


@dataclass
class RunContext:
    run_id: str
    run_mode: str
    campaign_id: str
    show: str
    created_at: str
    updated_at: str
    pipeline_version: str
    allocation_version: str


def _str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def fetch_runs(driver: Driver, show_filter: str, run_ids: Sequence[str]) -> List[RunContext]:
    params: Dict[str, Any] = {}
    where_parts: List[str] = []

    if _str(show_filter):
        where_parts.append("coalesce(rr.show, '') = $show")
        params["show"] = _str(show_filter)

    cleaned_run_ids = [_str(value) for value in run_ids if _str(value)]
    if cleaned_run_ids:
        where_parts.append("rr.run_id IN $run_ids")
        params["run_ids"] = cleaned_run_ids

    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    query = f"""
    MATCH (rr:RecommendationRun)
    {where_clause}
    RETURN rr.run_id AS run_id,
           coalesce(rr.run_mode, '') AS run_mode,
           coalesce(rr.campaign_id, '') AS campaign_id,
           coalesce(rr.show, '') AS show,
           coalesce(toString(rr.created_at), '') AS created_at,
           coalesce(toString(rr.updated_at), '') AS updated_at,
           coalesce(rr.pipeline_version, '') AS pipeline_version,
           coalesce(rr.allocation_version, '') AS allocation_version
    ORDER BY coalesce(rr.updated_at, rr.created_at) DESC
    """

    runs: List[RunContext] = []
    with driver.session() as session:
        for record in session.run(query, params):
            runs.append(
                RunContext(
                    run_id=_str(record.get("run_id")),
                    run_mode=_str(record.get("run_mode")),
                    campaign_id=_str(record.get("campaign_id")),
                    show=_str(record.get("show")),
                    created_at=_str(record.get("created_at")),
                    updated_at=_str(record.get("updated_at")),
                    pipeline_version=_str(record.get("pipeline_version")),
                    allocation_version=_str(record.get("allocation_version")),
                )
            )
    return runs


def count_run_node_duplicates(driver: Driver, run_id: str) -> int:
    query = """
    MATCH (rr:RecommendationRun {run_id: $run_id})
    RETURN count(rr) AS value
    """
    with driver.session() as session:
        record = session.run(query, {"run_id": run_id}).single()
    return int(record.get("value", 0) if record else 0)


def collect_per_run_stats(driver: Driver, run: RunContext) -> Dict[str, int]:
    query = """
    MATCH (rr:RecommendationRun {run_id: $run_id})

    OPTIONAL MATCH (:Visitor_this_year)-[r1:IS_RECOMMENDED {run_id: $run_id}]->(:Sessions_this_year)
    WITH rr, count(r1) AS is_recommended_count

    OPTIONAL MATCH (:Visitor_this_year)-[r2:IS_RECOMMENDED_EXHIBITOR {run_id: $run_id}]->(:Exhibitor)
    WITH rr, is_recommended_count, count(r2) AS is_recommended_exhibitor_count

    OPTIONAL MATCH (d:CampaignDelivery {run_id: $run_id})
    WITH rr, is_recommended_count, is_recommended_exhibitor_count, collect(d) AS deliveries

    WITH rr,
         is_recommended_count,
         is_recommended_exhibitor_count,
         deliveries,
         size(deliveries) AS delivery_count,
         size([d IN deliveries WHERE d IS NOT NULL AND NOT EXISTS { MATCH (d)-[:FOR_VISITOR]->(:Visitor_this_year) }]) AS deliveries_without_for_visitor,
         size([d IN deliveries WHERE d IS NOT NULL AND NOT EXISTS { MATCH (d)-[:FOR_RUN]->(:RecommendationRun {run_id: $run_id}) }]) AS deliveries_without_for_run,
         size([d IN deliveries WHERE d IS NOT NULL
               AND (
                 trim(coalesce(toString(d.run_mode), '')) <> trim(coalesce(toString(rr.run_mode), ''))
                 OR trim(coalesce(toString(d.campaign_id), '')) <> trim(coalesce(toString(rr.campaign_id), ''))
                 OR trim(coalesce(toString(d.show), '')) <> trim(coalesce(toString(rr.show), ''))
               )
         ]) AS delivery_metadata_mismatch

    OPTIONAL MATCH (:Visitor_this_year)-[r3:IS_RECOMMENDED {run_id: $run_id}]->(:Sessions_this_year)
    WITH rr,
         is_recommended_count,
         is_recommended_exhibitor_count,
         delivery_count,
         deliveries_without_for_visitor,
         deliveries_without_for_run,
         delivery_metadata_mismatch,
            sum(CASE WHEN r3 IS NULL THEN 0
                    WHEN trim(coalesce(toString(r3.run_mode), '')) = trim(coalesce(toString(rr.run_mode), ''))
                    AND trim(coalesce(toString(r3.campaign_id), '')) = trim(coalesce(toString(rr.campaign_id), ''))
                    AND trim(coalesce(toString(r3.show), '')) = trim(coalesce(toString(rr.show), ''))
                    THEN 0 ELSE 1 END) AS is_recommended_metadata_mismatch

    OPTIONAL MATCH (:Visitor_this_year)-[r4:IS_RECOMMENDED_EXHIBITOR {run_id: $run_id}]->(:Exhibitor)
    RETURN
      is_recommended_count,
      is_recommended_exhibitor_count,
      delivery_count,
      deliveries_without_for_visitor,
      deliveries_without_for_run,
      delivery_metadata_mismatch,
      is_recommended_metadata_mismatch,
    sum(CASE WHEN r4 IS NULL THEN 0
            WHEN trim(coalesce(toString(r4.run_mode), '')) = trim(coalesce(toString(rr.run_mode), ''))
             AND trim(coalesce(toString(r4.campaign_id), '')) = trim(coalesce(toString(rr.campaign_id), ''))
             AND trim(coalesce(toString(r4.show), '')) = trim(coalesce(toString(rr.show), ''))
            THEN 0 ELSE 1 END) AS is_recommended_exhibitor_metadata_mismatch
    """

    with driver.session() as session:
        record = session.run(query, {"run_id": run.run_id}).single()

    if not record:
        return {
            "is_recommended_count": 0,
            "is_recommended_exhibitor_count": 0,
            "delivery_count": 0,
            "deliveries_without_for_visitor": 0,
            "deliveries_without_for_run": 0,
            "delivery_metadata_mismatch": 0,
            "is_recommended_metadata_mismatch": 0,
            "is_recommended_exhibitor_metadata_mismatch": 0,
        }

    keys = [
        "is_recommended_count",
        "is_recommended_exhibitor_count",
        "delivery_count",
        "deliveries_without_for_visitor",
        "deliveries_without_for_run",
        "delivery_metadata_mismatch",
        "is_recommended_metadata_mismatch",
        "is_recommended_exhibitor_metadata_mismatch",
    ]
    return {key: int(record.get(key, 0) or 0) for key in keys}


def collect_global_stats(driver: Driver, show_filter: str) -> Dict[str, int]:
        params: Dict[str, Any] = {"show": _str(show_filter)}

        query = """
        CALL () {
            MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(:Sessions_this_year)
            WHERE trim(coalesce(toString(r.run_id), '')) = ''
                AND ($show = '' OR trim(coalesce(toString(r.show), toString(v.show), '')) = $show)
            RETURN count(r) AS missing_run_id_is_recommended
        }
        CALL () {
            MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED_EXHIBITOR]->(:Exhibitor)
            WHERE trim(coalesce(toString(r.run_id), '')) = ''
                AND ($show = '' OR trim(coalesce(toString(r.show), toString(v.show), '')) = $show)
            RETURN count(r) AS missing_run_id_is_recommended_exhibitor
        }
        CALL () {
            MATCH (d:CampaignDelivery)
            OPTIONAL MATCH (d)-[:FOR_VISITOR]->(v:Visitor_this_year)
            WHERE trim(coalesce(toString(d.run_id), '')) = ''
                AND ($show = '' OR trim(coalesce(toString(d.show), toString(v.show), '')) = $show)
            RETURN count(d) AS missing_run_id_campaign_delivery
        }
        RETURN missing_run_id_is_recommended,
                     missing_run_id_is_recommended_exhibitor,
                     missing_run_id_campaign_delivery
        """

        with driver.session() as session:
            record = session.run(query, params).single()

        if not record:
            return {
                "missing_run_id_is_recommended": 0,
                "missing_run_id_is_recommended_exhibitor": 0,
                "missing_run_id_campaign_delivery": 0,
            }

        return {
            "missing_run_id_is_recommended": int(record.get("missing_run_id_is_recommended", 0) or 0),
            "missing_run_id_is_recommended_exhibitor": int(record.get("missing_run_id_is_recommended_exhibitor", 0) or 0),
            "missing_run_id_campaign_delivery": int(record.get("missing_run_id_campaign_delivery", 0) or 0),
        }


def classify_run_issues(run: RunContext, stats: Dict[str, int], duplicate_count: int) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []

    def add(code: str, severity: str, detail: str) -> None:
        issues.append({"code": code, "severity": severity, "detail": detail})

    if duplicate_count != 1:
        add(
            "run_node_duplicate_count",
            "blocker",
            f"Expected exactly 1 RecommendationRun node for run_id; found {duplicate_count}",
        )

    if stats["deliveries_without_for_visitor"] > 0:
        add(
            "delivery_missing_for_visitor",
            "blocker",
            f"CampaignDelivery rows missing FOR_VISITOR link: {stats['deliveries_without_for_visitor']}",
        )

    if stats["deliveries_without_for_run"] > 0:
        add(
            "delivery_missing_for_run",
            "blocker",
            f"CampaignDelivery rows missing FOR_RUN link: {stats['deliveries_without_for_run']}",
        )

    if stats["delivery_metadata_mismatch"] > 0:
        add(
            "delivery_metadata_mismatch",
            "blocker",
            f"CampaignDelivery rows with metadata mismatch vs RecommendationRun: {stats['delivery_metadata_mismatch']}",
        )

    if stats["is_recommended_metadata_mismatch"] > 0:
        add(
            "is_recommended_metadata_mismatch",
            "blocker",
            f"IS_RECOMMENDED metadata mismatch vs RecommendationRun: {stats['is_recommended_metadata_mismatch']}",
        )

    if stats["is_recommended_exhibitor_metadata_mismatch"] > 0:
        add(
            "is_recommended_exhibitor_metadata_mismatch",
            "blocker",
            f"IS_RECOMMENDED_EXHIBITOR metadata mismatch vs RecommendationRun: {stats['is_recommended_exhibitor_metadata_mismatch']}",
        )

    if (
        stats["delivery_count"] == 0
        and stats["is_recommended_count"] == 0
        and stats["is_recommended_exhibitor_count"] == 0
    ):
        add(
            "run_without_delivery_or_relationships",
            "warning",
            "Run has no CampaignDelivery, IS_RECOMMENDED, or IS_RECOMMENDED_EXHIBITOR relationships",
        )

    if run.run_mode == "personal_agendas" and stats["delivery_count"] == 0:
        add(
            "personal_agendas_without_delivery",
            "warning",
            "personal_agendas run has zero CampaignDelivery rows",
        )

    return issues


def summarize_status(per_run: List[Dict[str, Any]], global_issues: List[Dict[str, str]]) -> str:
    has_blocker = any(
        issue.get("severity") == "blocker"
        for run in per_run
        for issue in run.get("issues", [])
    ) or any(issue.get("severity") == "blocker" for issue in global_issues)

    if has_blocker:
        return "fail"

    has_warning = any(
        issue.get("severity") == "warning"
        for run in per_run
        for issue in run.get("issues", [])
    ) or any(issue.get("severity") == "warning" for issue in global_issues)

    return "warning" if has_warning else "pass"


def build_global_issues(global_stats: Dict[str, int]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []

    def add(code: str, severity: str, detail: str) -> None:
        issues.append({"code": code, "severity": severity, "detail": detail})

    if global_stats["missing_run_id_is_recommended"] > 0:
        add(
            "global_missing_run_id_is_recommended",
            "warning",
            f"IS_RECOMMENDED relationships without run_id: {global_stats['missing_run_id_is_recommended']}",
        )

    if global_stats["missing_run_id_is_recommended_exhibitor"] > 0:
        add(
            "global_missing_run_id_is_recommended_exhibitor",
            "warning",
            (
                "IS_RECOMMENDED_EXHIBITOR relationships without run_id: "
                f"{global_stats['missing_run_id_is_recommended_exhibitor']}"
            ),
        )

    if global_stats["missing_run_id_campaign_delivery"] > 0:
        add(
            "global_missing_run_id_campaign_delivery",
            "warning",
            f"CampaignDelivery rows without run_id: {global_stats['missing_run_id_campaign_delivery']}",
        )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit RecommendationRun integrity and post-analysis readiness",
    )
    parser.add_argument(
        "--config",
        default="config/config_tsl.yaml",
        help="Path to YAML config file",
    )
    parser.add_argument(
        "--env-file",
        default="",
        help="Optional .env file path override",
    )
    parser.add_argument(
        "--show",
        default="",
        help="Optional show filter for RecommendationRun.show (default from config event.name)",
    )
    parser.add_argument(
        "--run-id",
        action="append",
        default=[],
        help="Optional run_id filter (repeatable)",
    )
    parser.add_argument(
        "--report-file",
        default="",
        help="Optional report file output path",
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit non-zero when blocker issues are found",
    )
    return parser.parse_args()


def main() -> int:
    configure_logging()
    args = parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = (Path.cwd() / config_path).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    config = load_config(str(config_path))

    env_override = _str(args.env_file)
    env_value = env_override or _str(config.get("env_file"))
    env_path = resolve_env_file_path(config_path, env_value)
    if env_path:
        load_dotenv(env_path, override=True)
        LOGGER.info("Loaded environment variables from %s", env_path)
    else:
        LOGGER.info("No env file loaded (override=%s, config env_file=%s)", env_override, _str(config.get("env_file")))

    creds = resolve_neo4j_credentials(config)

    show_filter = _str(args.show) or _str((config.get("event") or {}).get("name"))
    report_path = _str(args.report_file)
    if report_path:
        report_file = Path(report_path)
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_file = PA_ROOT / "large_tool_results" / f"recommendation_runs_post_analysis_audit_{timestamp}.json"
    if not report_file.is_absolute():
        report_file = (Path.cwd() / report_file).resolve()

    run_ids = [_str(value) for value in args.run_id if _str(value)]

    LOGGER.info("Starting RecommendationRun audit: show_filter=%s run_ids=%s", show_filter or "<none>", run_ids or "<all>")

    with GraphDatabase.driver(creds["uri"], auth=(creds["username"], creds["password"])) as driver:
        runs = fetch_runs(driver, show_filter, run_ids)
        LOGGER.info("Found %d RecommendationRun nodes for evaluation", len(runs))

        per_run: List[Dict[str, Any]] = []
        for run in runs:
            duplicate_count = count_run_node_duplicates(driver, run.run_id)
            stats = collect_per_run_stats(driver, run)
            issues = classify_run_issues(run, stats, duplicate_count)
            run_status = "fail" if any(i["severity"] == "blocker" for i in issues) else ("warning" if issues else "pass")

            per_run.append(
                {
                    "run": asdict(run),
                    "status": run_status,
                    "stats": {
                        **stats,
                        "run_node_count": duplicate_count,
                    },
                    "issues": issues,
                }
            )

        global_stats = collect_global_stats(driver, show_filter)
        global_issues = build_global_issues(global_stats)

    overall_status = summarize_status(per_run, global_issues)

    report: Dict[str, Any] = {
        "timestamp": _now_iso(),
        "scope": {
            "show_filter": show_filter,
            "run_ids": run_ids,
        },
        "summary": {
            "overall_status": overall_status,
            "runs_evaluated": len(per_run),
            "runs_fail": sum(1 for item in per_run if item["status"] == "fail"),
            "runs_warning": sum(1 for item in per_run if item["status"] == "warning"),
            "runs_pass": sum(1 for item in per_run if item["status"] == "pass"),
            "global_issue_count": len(global_issues),
        },
        "global_stats": global_stats,
        "global_issues": global_issues,
        "runs": per_run,
    }

    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    LOGGER.info("RecommendationRun audit completed with overall_status=%s", overall_status)
    LOGGER.info("Report written to: %s", report_file)

    if args.fail_on_issues and overall_status == "fail":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
