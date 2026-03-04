#!/usr/bin/env python3
"""Run post-analysis identity continuity activation + validation in one command.

This script:
1) Runs steps 1,4 in personal_agendas mode to refresh Visitor nodes with id_both_years
2) Runs steps 2,3,5,8 in post_analysis mode to build attendance relationships
3) Queries Neo4j for identity-match diagnostics
4) Writes a timestamped JSON report in large_tool_results/
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.neo4j_utils import resolve_neo4j_credentials


@dataclass
class CommandResult:
    name: str
    command: List[str]
    returncode: int
    stdout_tail: str
    stderr_tail: str


@dataclass
class PreflightStatus:
    post_analysis_ready: bool
    seminars_scans_this_path: str
    seminars_scans_this_exists: bool
    seminars_scan_reference_this_path: str
    seminars_scan_reference_this_exists: bool
    entry_scans_this_paths: List[str]
    entry_scans_this_existing: List[str]
    notes: List[str]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def write_yaml(path: Path, data: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def run_command(name: str, command: List[str], cwd: Path) -> CommandResult:
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    stdout_tail = "\n".join(proc.stdout.splitlines()[-80:])
    stderr_tail = "\n".join(proc.stderr.splitlines()[-80:])
    return CommandResult(
        name=name,
        command=command,
        returncode=proc.returncode,
        stdout_tail=stdout_tail,
        stderr_tail=stderr_tail,
    )


def preflight_post_analysis_inputs(config: Dict[str, Any], project_root: Path) -> PreflightStatus:
    post_cfg = config.get("post_analysis_mode", {}) or {}
    scan_cfg = post_cfg.get("scan_files", {}) or {}
    entry_cfg = post_cfg.get("entry_scan_files", {}) or {}

    def _resolve(path_value: str) -> Path:
        candidate = Path(path_value)
        if candidate.is_absolute():
            return candidate
        return (project_root / candidate).resolve()

    seminars_scans_this = str(scan_cfg.get("seminars_scans_this", "") or "").strip()
    seminars_scan_reference_this = str(scan_cfg.get("seminars_scan_reference_this", "") or "").strip()

    seminars_scans_this_exists = False
    seminars_scan_reference_this_exists = False

    seminars_scans_this_path = ""
    seminars_scan_reference_this_path = ""

    notes: List[str] = []

    if seminars_scans_this:
        resolved = _resolve(seminars_scans_this)
        seminars_scans_this_path = str(resolved)
        seminars_scans_this_exists = resolved.exists()
    else:
        notes.append("post_analysis_mode.scan_files.seminars_scans_this is not configured")

    if seminars_scan_reference_this:
        resolved = _resolve(seminars_scan_reference_this)
        seminars_scan_reference_this_path = str(resolved)
        seminars_scan_reference_this_exists = resolved.exists()
    else:
        notes.append("post_analysis_mode.scan_files.seminars_scan_reference_this is not configured (optional)")

    entry_scans = entry_cfg.get("entry_scans_this", [])
    if isinstance(entry_scans, str):
        entry_scans = [entry_scans]
    entry_scans = [str(p).strip() for p in entry_scans if str(p).strip()]

    entry_existing: List[str] = []
    for entry in entry_scans:
        resolved = _resolve(entry)
        if resolved.exists():
            entry_existing.append(str(resolved))

    if not entry_scans:
        notes.append("post_analysis_mode.entry_scan_files.entry_scans_this is empty (registered_to_show will be skipped)")

    # Minimum readiness for post-analysis relationship processing is seminars_scans_this.
    post_analysis_ready = seminars_scans_this_exists
    if not seminars_scans_this_exists:
        notes.append("post-analysis steps require seminars_scans_this file; run will skip post-analysis phase until event scan exports are available")

    if seminars_scans_this_exists and not seminars_scan_reference_this_exists:
        notes.append("seminars_scan_reference_this missing; processor will continue with scans-only enrichment")

    return PreflightStatus(
        post_analysis_ready=post_analysis_ready,
        seminars_scans_this_path=seminars_scans_this_path,
        seminars_scans_this_exists=seminars_scans_this_exists,
        seminars_scan_reference_this_path=seminars_scan_reference_this_path,
        seminars_scan_reference_this_exists=seminars_scan_reference_this_exists,
        entry_scans_this_paths=entry_scans,
        entry_scans_this_existing=entry_existing,
        notes=notes,
    )


def query_neo4j(config: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from neo4j import GraphDatabase
    except ModuleNotFoundError as exc:  # pragma: no cover - runtime env dependent
        raise SystemExit(
            "Missing dependency 'neo4j'. Install with: pip install neo4j"
        ) from exc

    if config.get("env_file"):
        load_dotenv(config["env_file"], override=False)

    creds = resolve_neo4j_credentials(config)
    driver = GraphDatabase.driver(creds["uri"], auth=(creds["username"], creds["password"]))

    queries = {
        "assisted_session_match_modes": """
            MATCH ()-[r]->()
            WHERE type(r) = 'assisted_session_this_year'
            WITH r, 'identity_match_mode' AS mode_key
            RETURN coalesce(r[mode_key], 'missing') AS mode, count(*) AS relationships
            ORDER BY relationships DESC
        """,
        "registered_to_show_match_modes": """
            MATCH ()-[r]->()
            WHERE type(r) = 'registered_to_show'
            WITH r, 'identity_match_mode' AS mode_key
            RETURN coalesce(r[mode_key], 'missing') AS mode, count(*) AS relationships
            ORDER BY relationships DESC
        """,
        "visitor_identity_coverage": """
            MATCH (v:Visitor_this_year)
            RETURN
              count(v) AS visitors_total,
              count(v.id_both_years) AS visitors_with_identity,
              count(v.BadgeId) AS visitors_with_badge
        """,
    }

    out: Dict[str, Any] = {}
    try:
        with driver.session() as session:
            for key, q in queries.items():
                rows = [dict(r) for r in session.run(q)]
                out[key] = rows
    finally:
        driver.close()

    return out


def _relationship_total(rows: List[Dict[str, Any]]) -> int:
    total = 0
    for row in rows:
        try:
            total += int(row.get("relationships", 0) or 0)
        except (TypeError, ValueError):
            continue
    return total


def print_expected_pre_event_summary(preflight: PreflightStatus, validation: Dict[str, Any]) -> None:
    assisted_total = _relationship_total(validation.get("assisted_session_match_modes", []))
    registered_total = _relationship_total(validation.get("registered_to_show_match_modes", []))

    expected_conditions: List[str] = []
    if not preflight.post_analysis_ready:
        expected_conditions.append("post-analysis pipeline steps were skipped (missing seminars_scans_this)")
    if not preflight.entry_scans_this_paths:
        expected_conditions.append("entry_scans_this is not configured")
    elif not preflight.entry_scans_this_existing:
        expected_conditions.append("entry_scans_this is configured but files are not present yet")
    if assisted_total == 0:
        expected_conditions.append("assisted_session_this_year has no relationships yet")
    if registered_total == 0:
        expected_conditions.append("registered_to_show has no relationships yet")

    if not expected_conditions:
        return

    print("expected pre-event state summary:")
    for condition in expected_conditions:
        print(f"  - {condition}")


def evaluate_post_event_requirements(preflight: PreflightStatus, validation: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    assisted_total = _relationship_total(validation.get("assisted_session_match_modes", []))
    registered_total = _relationship_total(validation.get("registered_to_show_match_modes", []))

    if not preflight.post_analysis_ready:
        errors.append("post_analysis_mode.scan_files.seminars_scans_this is missing or not found")
    if not preflight.entry_scans_this_paths:
        errors.append("post_analysis_mode.entry_scan_files.entry_scans_this is empty")
    elif not preflight.entry_scans_this_existing:
        errors.append("entry_scans_this paths are configured but files are not found")

    if assisted_total <= 0:
        errors.append("assisted_session_this_year has zero relationships")
    if registered_total <= 0:
        errors.append("registered_to_show has zero relationships")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Run identity-first post-analysis activation + validation")
    parser.add_argument("--config", default="config/config_tsl.yaml", help="Base pipeline config path")
    parser.add_argument(
        "--include-step-11",
        action="store_true",
        help="Also run step 11 output processing after post-analysis relationship steps",
    )
    parser.add_argument(
        "--skip-pipeline",
        action="store_true",
        help="Skip pipeline execution and only run Neo4j validation queries",
    )
    parser.add_argument(
        "--require-post-event-data",
        action="store_true",
        help=(
            "Fail with non-zero exit when post-event inputs/relationships are missing "
            "(requires non-empty assisted_session_this_year and registered_to_show)."
        ),
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    config_path = (project_root / args.config).resolve() if not Path(args.config).is_absolute() else Path(args.config)
    if not config_path.exists():
        raise SystemExit(f"Config file not found: {config_path}")

    base_config = load_yaml(config_path)
    stamp = utc_stamp()
    large_results = project_root / "large_tool_results"
    large_results.mkdir(parents=True, exist_ok=True)
    preflight = preflight_post_analysis_inputs(base_config, project_root)

    command_results: List[CommandResult] = []

    with tempfile.TemporaryDirectory(prefix="pa_identity_validation_") as tmpdir:
        tmpdir_path = Path(tmpdir)

        cfg_personal = dict(base_config)
        cfg_personal["mode"] = "personal_agendas"
        personal_cfg_path = tmpdir_path / f"{config_path.stem}_personal.yaml"
        write_yaml(personal_cfg_path, cfg_personal)

        cfg_post = dict(base_config)
        cfg_post["mode"] = "post_analysis"
        post_cfg_path = tmpdir_path / f"{config_path.stem}_post.yaml"
        write_yaml(post_cfg_path, cfg_post)

        if not args.skip_pipeline:
            cmd1 = [
                sys.executable,
                "main.py",
                "--config",
                str(personal_cfg_path),
                "--only-steps",
                "1,4",
                "--skip-mlflow",
            ]
            res1 = run_command("identity_refresh_steps_1_4", cmd1, project_root)
            command_results.append(res1)
            if res1.returncode != 0:
                report_path = large_results / f"identity_validation_{stamp}.json"
                payload = {
                    "ok": False,
                    "stage": "identity_refresh_steps_1_4",
                    "config": str(config_path),
                    "commands": [asdict(r) for r in command_results],
                }
                report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                raise SystemExit(f"Step 1 failed; report written to {report_path}")

            if preflight.post_analysis_ready:
                cmd2 = [
                    sys.executable,
                    "main.py",
                    "--config",
                    str(post_cfg_path),
                    "--only-steps",
                    "2,3,5,8",
                    "--skip-mlflow",
                ]
                res2 = run_command("post_analysis_steps_2_3_5_8", cmd2, project_root)
                command_results.append(res2)
                if res2.returncode != 0:
                    report_path = large_results / f"identity_validation_{stamp}.json"
                    payload = {
                        "ok": False,
                        "stage": "post_analysis_steps_2_3_5_8",
                        "config": str(config_path),
                        "preflight": asdict(preflight),
                        "commands": [asdict(r) for r in command_results],
                    }
                    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                    raise SystemExit(f"Step 2 failed; report written to {report_path}")

                if args.include_step_11:
                    cmd3 = [
                        sys.executable,
                        "main.py",
                        "--config",
                        str(post_cfg_path),
                        "--only-steps",
                        "11",
                        "--skip-mlflow",
                    ]
                    res3 = run_command("post_analysis_step_11", cmd3, project_root)
                    command_results.append(res3)
                    if res3.returncode != 0:
                        report_path = large_results / f"identity_validation_{stamp}.json"
                        payload = {
                            "ok": False,
                            "stage": "post_analysis_step_11",
                            "config": str(config_path),
                            "preflight": asdict(preflight),
                            "commands": [asdict(r) for r in command_results],
                        }
                        report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                        raise SystemExit(f"Step 3 failed; report written to {report_path}")
            else:
                command_results.append(
                    CommandResult(
                        name="post_analysis_steps_2_3_5_8",
                        command=[],
                        returncode=0,
                        stdout_tail="Skipped: post-analysis source scan files are not available yet.",
                        stderr_tail="",
                    )
                )

        validation = query_neo4j(cfg_post)

    strict_errors = evaluate_post_event_requirements(preflight, validation) if args.require_post_event_data else []
    strict_ok = len(strict_errors) == 0
    status = "POST-EVENT READY" if strict_ok else "PRE-EVENT OK"
    overall_ok = strict_ok if args.require_post_event_data else True

    report_path = large_results / f"identity_validation_{stamp}.json"
    report = {
        "ok": overall_ok,
        "timestamp_utc": stamp,
        "config": str(config_path),
        "require_post_event_data": args.require_post_event_data,
        "status": status,
        "strict_post_event_errors": strict_errors,
        "preflight": asdict(preflight),
        "commands": [asdict(r) for r in command_results],
        "validation": validation,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Validation report written: {report_path}")
    print(f"STATUS: {status}")
    print("assisted_session_this_year match modes:")
    assisted_rows = validation.get("assisted_session_match_modes", [])
    if not assisted_rows:
        print("  - none found")
    for row in assisted_rows:
        print(f"  - {row.get('mode')}: {row.get('relationships')}")

    print("registered_to_show match modes:")
    registered_rows = validation.get("registered_to_show_match_modes", [])
    if not registered_rows:
        print("  - none found")
    for row in registered_rows:
        print(f"  - {row.get('mode')}: {row.get('relationships')}")

    print_expected_pre_event_summary(preflight, validation)

    if strict_errors:
        print("strict post-event checks:")
        for err in strict_errors:
            print(f"  - {err}")

    if not preflight.post_analysis_ready:
        print("post-analysis phase skipped: required this-year seminar scan exports are not available yet")

    if args.require_post_event_data and strict_errors:
        raise SystemExit("Post-event required data checks failed; see report for details")


if __name__ == "__main__":
    main()
