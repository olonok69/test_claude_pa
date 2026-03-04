#!/usr/bin/env python3
"""Dry-run validator for M4 engagement control-group behavior.

This script performs read-only checks:
- Verifies control-group is active for the current mode.
- Loads visitors eligible for recommendation processing.
- Builds the deterministic run-scoped control assignment map.
- Produces split counts and a small sample of control IDs.

No Neo4j writes are performed.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PA_ROOT = CURRENT_FILE.parents[1]
if str(PA_ROOT) not in sys.path:
    sys.path.insert(0, str(PA_ROOT))

from output_processor import OutputProcessor
from session_recommendation_processor import SessionRecommendationProcessor
from utils.config_utils import load_config


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only dry-run for M4 engagement control")
    parser.add_argument(
        "--config",
        default="PA/config/config_tsl.yaml",
        help="Path to config YAML",
    )
    parser.add_argument(
        "--create-only-new",
        action="store_true",
        help="Use incremental visitor scope when evaluating control split",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=25,
        help="How many control visitor IDs to include in sample output",
    )
    parser.add_argument(
        "--report-file",
        default="large_tool_results/m4_engagement_control_dry_run_report.json",
        help="Output report path",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config)
    config.setdefault("project_root", str(PA_ROOT))

    srp = SessionRecommendationProcessor(config)
    out = OutputProcessor(config)

    visitors_to_process = srp._get_visitors_to_process(create_only_new=args.create_only_new)
    control_map = srp._build_control_assignment_map(list(visitors_to_process))
    selected_control_ids = sorted([badge_id for badge_id, flag in control_map.items() if int(flag) == 1])

    report = {
        "generated_at": utc_now_iso(),
        "config": args.config,
        "mode": srp.mode,
        "create_only_new": bool(args.create_only_new),
        "control_group_enabled": bool(srp.control_group_enabled),
        "control_group_enabled_modes": sorted(list(srp.control_group_enabled_modes)),
        "control_group_active_for_mode": bool(srp._should_apply_control_group()),
        "output_control_active_for_mode": bool(out._control_group_active_for_mode()),
        "control_group_percentage": srp.control_group_percentage,
        "campaign_id": srp.current_campaign_id,
        "run_mode": srp.current_run_mode,
        "legacy_seed_run_id": srp.control_group_legacy_seed_run_id,
        "counts": {
            "visitors_to_process": len(visitors_to_process),
            "control_assigned_in_run_scope": len(selected_control_ids),
            "treatment_assigned_in_run_scope": max(len(visitors_to_process) - len(selected_control_ids), 0),
        },
        "control_id_sample": selected_control_ids[: max(0, int(args.sample_size))],
    }

    report_path = Path(args.report_file)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
