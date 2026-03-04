#!/usr/bin/env python3
"""Run engagement reconciliation from unified files using engagement defaults.

This is a thin, conservative wrapper around
`reconcile_legacy_delivery_from_unified.py` with defaults for:
- engagement unified input files
- engagement run metadata
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconcile engagement RecommendationRun/relationships from unified files",
    )
    parser.add_argument("--config", default="config/config_tsl.yaml", help="Path to YAML config")
    parser.add_argument(
        "--main-unified",
        default="data/tsl/recommendations/visitor_recommendations_tsl_20260219_205354_unified_v2e5.json",
        help="Main engagement unified recommendations JSON",
    )
    parser.add_argument(
        "--control-unified",
        default="data/tsl/recommendations/visitor_recommendations_tsl_20260219_205354_control_unified_v2e5.json",
        help="Control engagement unified recommendations JSON",
    )
    parser.add_argument(
        "--run-id",
        default="tsl_engagement_20260219T205354Z_c3f8fb55",
        help="RecommendationRun.run_id",
    )
    parser.add_argument("--run-mode", default="engagement", help="RecommendationRun.run_mode")
    parser.add_argument("--campaign-id", default="tsl_engagement", help="RecommendationRun.campaign_id")
    parser.add_argument("--show", default="tsl", help="RecommendationRun.show")
    parser.add_argument(
        "--created-at",
        default="2026-02-19T20:53:54.687643+00:00",
        help="RecommendationRun.created_at ISO timestamp",
    )
    parser.add_argument(
        "--updated-at",
        default="2026-02-19T20:53:54.687643+00:00",
        help="RecommendationRun.updated_at ISO timestamp",
    )
    parser.add_argument("--pipeline-version", default="pa_pipeline", help="RecommendationRun.pipeline_version")
    parser.add_argument("--allocation-version", default="full", help="RecommendationRun.allocation_version")
    parser.add_argument(
        "--run-id-suffix",
        default="",
        help="Optional suffix appended to --run-id",
    )
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
        "--skip-verify-after-when-dry-run",
        action="store_true",
        help="Skip second verification pass when --apply is not set",
    )
    parser.add_argument(
        "--report-file",
        default="large_tool_results/reconcile_engagement_delivery_from_unified_report.json",
        help="Output report JSON path",
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit with code 2 when verify_after still has blockers",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    script_path = Path(__file__).resolve().parent / "reconcile_legacy_delivery_from_unified.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Base reconciler not found: {script_path}")

    command = [
        sys.executable,
        str(script_path),
        "--config",
        args.config,
        "--main-unified",
        args.main_unified,
        "--control-unified",
        args.control_unified,
        "--run-id",
        args.run_id,
        "--run-mode",
        args.run_mode,
        "--campaign-id",
        args.campaign_id,
        "--show",
        args.show,
        "--created-at",
        args.created_at,
        "--updated-at",
        args.updated_at,
        "--pipeline-version",
        args.pipeline_version,
        "--allocation-version",
        args.allocation_version,
        "--batch-size",
        str(args.batch_size),
        "--sample-size",
        str(args.sample_size),
        "--neo4j-retry-attempts",
        str(args.neo4j_retry_attempts),
        "--neo4j-retry-backoff-seconds",
        str(args.neo4j_retry_backoff_seconds),
        "--report-file",
        args.report_file,
    ]

    if args.run_id_suffix:
        command.extend(["--run-id-suffix", args.run_id_suffix])
    if args.env_file:
        command.extend(["--env-file", args.env_file])
    if args.apply:
        command.append("--apply")
    if args.skip_verify_after_when_dry_run:
        command.append("--skip-verify-after-when-dry-run")
    if args.fail_on_issues:
        command.append("--fail-on-issues")

    completed = subprocess.run(command, check=False)
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
