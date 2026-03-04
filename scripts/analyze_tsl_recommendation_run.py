#!/usr/bin/env python3
"""Analyze a completed TSL recommendation run and validate engagement theatre filter behavior.

Outputs:
- Timestamped JSON report in large_tool_results/
- Timestamped log file in large_tool_results/
- Optional console logs
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import yaml


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def normalize_show_ref(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def normalize_theatre_name(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def find_latest_recommendations(recommendations_dir: Path) -> Optional[Path]:
    candidates = sorted(
        recommendations_dir.glob("visitor_recommendations_tsl_*.csv"),
        key=lambda p: p.stat().st_mtime,
    )
    return candidates[-1] if candidates else None


def setup_logger(log_file: Path, verbose: bool) -> logging.Logger:
    logger = logging.getLogger("tsl_recommendation_run_analysis")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    if verbose:
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(sh)

    return logger


def resolve_path(project_root: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (project_root / candidate).resolve()


def load_mapping(
    mapping_path: Path,
    include_show_last_values: Set[str],
) -> Tuple[Dict[str, Set[str]], Set[str], Dict[str, Any]]:
    show_to_theatres: Dict[str, Set[str]] = defaultdict(set)
    global_theatres: Set[str] = set()
    rows = 0
    valid_rows = 0

    with mapping_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = {name.lower(): name for name in (reader.fieldnames or [])}
        show_col = fieldnames.get("show_last") or fieldnames.get("showlast") or fieldnames.get("show_last_year")
        theatre_col = fieldnames.get("theatre_name") or fieldnames.get("theatre__name") or fieldnames.get("theatre")

        if not show_col or not theatre_col:
            raise ValueError("Mapping CSV must include show_last and theatre_name columns")

        for row in reader:
            rows += 1
            show_last = normalize_show_ref(row.get(show_col))
            theatre = normalize_theatre_name(row.get(theatre_col))
            if not show_last or not theatre:
                continue
            valid_rows += 1
            if show_last in include_show_last_values:
                global_theatres.add(theatre)
            else:
                show_to_theatres[show_last].add(theatre)

    meta = {
        "rows_total": rows,
        "rows_valid": valid_rows,
        "show_groups": len(show_to_theatres),
        "global_theatres": len(global_theatres),
    }
    return dict(show_to_theatres), global_theatres, meta


def load_visitor_show_map(registration_path: Path, visitor_show_field: str) -> Dict[str, str]:
    visitor_map: Dict[str, str] = {}
    with registration_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        if "BadgeId" not in fieldnames:
            raise ValueError("Registration CSV must include BadgeId")

        candidates = [visitor_show_field, "ShowRef", "show_ref", "show"]
        show_col = next((name for name in candidates if name in fieldnames), None)
        if not show_col:
            raise ValueError("Registration CSV must include one of: ShowRef, show_ref, show")

        for row in reader:
            visitor_id = str(row.get("BadgeId", "")).strip()
            if not visitor_id:
                continue
            show_ref = normalize_show_ref(row.get(show_col))
            if show_ref:
                visitor_map[visitor_id] = show_ref

    return visitor_map


def pick_theatre_column(fieldnames: Iterable[str]) -> Optional[str]:
    names = list(fieldnames)
    for candidate in ("session_theatre_name", "theatre__name", "theatre_name"):
        if candidate in names:
            return candidate
    return None


def analyze_recommendations(
    recommendations_path: Path,
    visitor_show_map: Dict[str, str],
    show_to_theatres: Dict[str, Set[str]],
    global_theatres: Set[str],
    exclude_unknown_theatre: bool,
    strict_when_no_mapping: bool,
    sample_limit: int,
) -> Dict[str, Any]:
    stats = {
        "rows_total": 0,
        "rows_with_visitor": 0,
        "rows_missing_visitor": 0,
        "rows_missing_show_ref": 0,
        "rows_without_mapping": 0,
        "rows_unknown_theatre": 0,
        "rows_evaluable": 0,
        "rows_violating_rule": 0,
    }
    violations_sample: List[Dict[str, Any]] = []
    violations_by_show = Counter()
    violations_by_theatre = Counter()
    visitor_counts = Counter()

    with recommendations_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if "visitor_id" not in (reader.fieldnames or []):
            raise ValueError("Recommendations CSV must include visitor_id")

        theatre_col = pick_theatre_column(reader.fieldnames or [])
        if not theatre_col:
            raise ValueError("Recommendations CSV must include session_theatre_name/theatre__name/theatre_name")

        for row in reader:
            stats["rows_total"] += 1
            visitor_id = str(row.get("visitor_id", "")).strip()
            if not visitor_id:
                stats["rows_missing_visitor"] += 1
                continue

            stats["rows_with_visitor"] += 1
            visitor_counts[visitor_id] += 1
            show_last = visitor_show_map.get(visitor_id, "")
            if not show_last:
                stats["rows_missing_show_ref"] += 1
                continue

            allowed = set(global_theatres)
            allowed.update(show_to_theatres.get(show_last, set()))
            if not allowed:
                stats["rows_without_mapping"] += 1
                if strict_when_no_mapping:
                    stats["rows_violating_rule"] += 1
                continue

            theatre_raw = row.get(theatre_col)
            theatre_norm = normalize_theatre_name(theatre_raw)
            if not theatre_norm:
                stats["rows_unknown_theatre"] += 1
                if exclude_unknown_theatre:
                    stats["rows_violating_rule"] += 1
                    if len(violations_sample) < sample_limit:
                        violations_sample.append(
                            {
                                "visitor_id": visitor_id,
                                "show_last": show_last,
                                "session_id": row.get("session_id"),
                                "session_theatre_name": theatre_raw,
                                "reason": "unknown_theatre_excluded",
                            }
                        )
                continue

            stats["rows_evaluable"] += 1
            if theatre_norm not in allowed:
                stats["rows_violating_rule"] += 1
                violations_by_show[show_last] += 1
                violations_by_theatre[str(theatre_raw)] += 1
                if len(violations_sample) < sample_limit:
                    violations_sample.append(
                        {
                            "visitor_id": visitor_id,
                            "show_last": show_last,
                            "session_id": row.get("session_id"),
                            "session_theatre_name": theatre_raw,
                            "allowed_theatres_normalized": sorted(allowed),
                            "reason": "theatre_not_allowed_for_show_last",
                        }
                    )

    unique_visitors = len(visitor_counts)
    visitors_with_show_ref = sum(1 for visitor in visitor_counts if visitor in visitor_show_map)

    return {
        "stats": stats,
        "unique_visitors_in_recommendations": unique_visitors,
        "visitors_with_show_ref": visitors_with_show_ref,
        "violations_by_show_last": dict(violations_by_show.most_common(20)),
        "violations_by_theatre": dict(violations_by_theatre.most_common(20)),
        "violations_sample": violations_sample,
        "rule_passed": stats["rows_violating_rule"] == 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze TSL recommendation run and engagement theatre filter compliance")
    parser.add_argument("--config", default="config/config_tsl.yaml", help="Config path relative to PA/")
    parser.add_argument("--recommendations", default="", help="Optional recommendation CSV path")
    parser.add_argument(
        "--registration-file",
        default="data/tsl/output/df_reg_demo_this.csv",
        help="Registration+demographic CSV containing BadgeId and ShowRef",
    )
    parser.add_argument("--mapping-file", default="", help="Override mapping file path")
    parser.add_argument("--sample-limit", type=int, default=30, help="Violation sample size in report")
    parser.add_argument("--quiet", action="store_true", help="Disable console logging (file logging remains enabled)")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    config_path = resolve_path(project_root, args.config)
    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")

    config = load_yaml(config_path)
    recommendation_cfg = (config.get("recommendation") or {})
    filter_cfg = recommendation_cfg.get("engagement_show_theatre_filter", {}) or {}

    stamp = utc_stamp()
    results_dir = (project_root / "large_tool_results").resolve()
    results_dir.mkdir(parents=True, exist_ok=True)
    log_path = results_dir / f"tsl_recommendation_run_analysis_{stamp}.log"
    report_path = results_dir / f"tsl_recommendation_run_analysis_{stamp}.json"
    logger = setup_logger(log_path, verbose=not args.quiet)

    logger.info("Starting TSL recommendation run analysis")
    logger.info("Using config: %s", config_path)

    mode = str(config.get("mode", "")).strip().lower()
    apply_modes = filter_cfg.get("apply_modes", ["engagement"])
    if isinstance(apply_modes, str):
        apply_modes = [apply_modes]
    apply_modes_norm = {str(value).strip().lower() for value in apply_modes if str(value).strip()} or {"engagement"}

    include_values = filter_cfg.get("include_show_last_values", ["ALL"])
    if isinstance(include_values, str):
        include_values = [include_values]
    include_show_last_values = {normalize_show_ref(value) for value in include_values if str(value).strip()} or {"ALL"}

    recommendations_path: Optional[Path]
    if args.recommendations:
        recommendations_path = resolve_path(project_root, args.recommendations)
    else:
        recommendations_dir = resolve_path(project_root, "data/tsl/recommendations")
        recommendations_path = find_latest_recommendations(recommendations_dir)

    if not recommendations_path or not recommendations_path.exists():
        raise SystemExit("No recommendations CSV found. Use --recommendations to provide a file.")

    registration_path = resolve_path(project_root, args.registration_file)
    if not registration_path.exists():
        raise SystemExit(f"Registration file not found: {registration_path}")

    mapping_file_cfg = args.mapping_file or str(filter_cfg.get("mapping_file", "")).strip()
    if not mapping_file_cfg:
        raise SystemExit("No mapping file configured. Provide --mapping-file or set recommendation.engagement_show_theatre_filter.mapping_file")
    mapping_path = resolve_path(project_root, mapping_file_cfg)
    if not mapping_path.exists():
        raise SystemExit(f"Mapping file not found: {mapping_path}")

    visitor_show_field = str(filter_cfg.get("visitor_show_last_field", "ShowRef"))
    exclude_unknown_theatre = bool(filter_cfg.get("exclude_unknown_theatre", False))
    strict_when_no_mapping = bool(filter_cfg.get("strict_when_no_mapping", False))
    filter_enabled = bool(filter_cfg.get("enabled", False))
    filter_should_apply = filter_enabled and mode in apply_modes_norm

    logger.info("Recommendations file: %s", recommendations_path)
    logger.info("Registration file: %s", registration_path)
    logger.info("Mapping file: %s", mapping_path)
    logger.info("Filter enabled=%s mode=%s applies_in_mode=%s", filter_enabled, mode, filter_should_apply)

    show_to_theatres, global_theatres, mapping_meta = load_mapping(mapping_path, include_show_last_values)
    visitor_show_map = load_visitor_show_map(registration_path, visitor_show_field)
    analysis = analyze_recommendations(
        recommendations_path=recommendations_path,
        visitor_show_map=visitor_show_map,
        show_to_theatres=show_to_theatres,
        global_theatres=global_theatres,
        exclude_unknown_theatre=exclude_unknown_theatre,
        strict_when_no_mapping=strict_when_no_mapping,
        sample_limit=max(args.sample_limit, 0),
    )

    stats = analysis["stats"]
    rows_total = int(stats["rows_total"])
    rows_violating = int(stats["rows_violating_rule"])
    violation_rate = (rows_violating / rows_total) if rows_total else 0.0

    status = "PASS" if analysis["rule_passed"] else "FAIL"
    if not filter_should_apply:
        status = "WARN"

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "mode": mode,
        "filter_enabled": filter_enabled,
        "filter_apply_modes": sorted(apply_modes_norm),
        "filter_should_apply_in_mode": filter_should_apply,
        "paths": {
            "config": str(config_path),
            "recommendations": str(recommendations_path),
            "registration": str(registration_path),
            "mapping": str(mapping_path),
            "log": str(log_path),
            "report": str(report_path),
        },
        "mapping": {
            **mapping_meta,
            "include_show_last_values": sorted(include_show_last_values),
        },
        "visitor_show_map_size": len(visitor_show_map),
        "analysis": analysis,
        "violation_rate": violation_rate,
        "notes": [
            "rows_without_mapping and rows_missing_show_ref are not treated as violations unless strict settings enforce exclusion",
            "rule validation checks recommendation row theatres against (show_last theatres + global ALL theatres)",
        ],
    }

    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    logger.info("Analysis complete. status=%s", status)
    logger.info("Rows total=%d, violating=%d, violation_rate=%.6f", rows_total, rows_violating, violation_rate)
    logger.info("Report written to %s", report_path)
    logger.info("Log written to %s", log_path)

    print(f"STATUS: {status}")
    print(f"REPORT: {report_path}")
    print(f"LOG: {log_path}")

    if status == "FAIL":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
