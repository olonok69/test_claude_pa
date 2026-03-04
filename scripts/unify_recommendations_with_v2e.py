#!/usr/bin/env python3
"""Unify session recommendations (CSV) with v2e exhibitor recommendations (JSON).

This script creates two JSON outputs in the recommendations folder:
1) Unified recommendations JSON
2) Unified control recommendations JSON

Join key:
- CSV: visitor_id
- v2e JSON: badgeID
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _normalize_id(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def load_v2e_recommendations(v2e_json_path: Path) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Any]]:
    with v2e_json_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    recs = payload.get("recommendations", []) or []
    by_badge: Dict[str, List[Dict[str, Any]]] = {}
    duplicate_badge_ids = []
    missing_badge_id_entries = 0

    for item in recs:
        badge_id = _normalize_id(item.get("badgeID"))
        exhibitors = item.get("exhibitors", []) or []

        if not badge_id:
            missing_badge_id_entries += 1
            continue

        if badge_id in by_badge:
            duplicate_badge_ids.append(badge_id)
            by_badge[badge_id].extend(exhibitors)
        else:
            by_badge[badge_id] = list(exhibitors)

    incidences = {
        "v2e_total_entries": len(recs),
        "v2e_unique_badge_ids": len(by_badge),
        "v2e_missing_badge_id_entries": missing_badge_id_entries,
        "v2e_duplicate_badge_id_count": len(duplicate_badge_ids),
        "v2e_duplicate_badge_id_samples": sorted(set(duplicate_badge_ids))[:25],
    }
    return by_badge, incidences


def load_and_group_session_csv(csv_path: Path) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    row_count = 0
    missing_visitor_id_rows = 0
    duplicate_session_pairs = 0
    seen_pairs = set()

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_count += 1
            visitor_id = _normalize_id(row.get("visitor_id"))
            if not visitor_id:
                missing_visitor_id_rows += 1
                continue

            session_id = _normalize_id(row.get("session_id"))
            pair = (visitor_id, session_id)
            if pair in seen_pairs:
                duplicate_session_pairs += 1
                continue
            seen_pairs.add(pair)

            if visitor_id not in grouped:
                grouped[visitor_id] = {
                    "visitor_id": visitor_id,
                    "email": _normalize_id(row.get("Email")),
                    "badge_type": _normalize_id(row.get("BadgeType")),
                    "sessions": [],
                }

            grouped[visitor_id]["sessions"].append(
                {
                    "session_id": session_id,
                    "session_title": _normalize_id(row.get("session_title")),
                    "session_speaker_id": _normalize_id(row.get("session_speaker_id")),
                    "session_date": _normalize_id(row.get("session_date")),
                    "session_start_time": _normalize_id(row.get("session_start_time")),
                    "session_theatre_name": _normalize_id(row.get("session_theatre_name")),
                }
            )

    incidences = {
        "csv_path": str(csv_path),
        "csv_rows": row_count,
        "csv_unique_visitors": len(grouped),
        "csv_rows_missing_visitor_id": missing_visitor_id_rows,
        "csv_duplicate_visitor_session_pairs": duplicate_session_pairs,
    }
    return grouped, incidences


def unify_dataset(
    grouped_visitors: Dict[str, Dict[str, Any]],
    exhibitors_by_badge: Dict[str, List[Dict[str, Any]]],
    dataset_name: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    output_recommendations: List[Dict[str, Any]] = []
    missing_in_v2e = []
    matched = 0

    for visitor_id, visitor_payload in grouped_visitors.items():
        exhibitors = exhibitors_by_badge.get(visitor_id, [])
        if exhibitors:
            matched += 1
        else:
            missing_in_v2e.append(visitor_id)

        output_recommendations.append(
            {
                "visitor_id": visitor_id,
                "email": visitor_payload.get("email", ""),
                "badge_type": visitor_payload.get("badge_type", ""),
                "sessions": visitor_payload.get("sessions", []),
                "v2e_exhibitors": exhibitors,
                "session_count": len(visitor_payload.get("sessions", [])),
                "v2e_exhibitor_count": len(exhibitors),
            }
        )

    output_recommendations.sort(key=lambda item: item["visitor_id"])

    incidence = {
        "dataset": dataset_name,
        "visitors_total": len(grouped_visitors),
        "visitors_matched_with_v2e": matched,
        "visitors_missing_in_v2e": len(missing_in_v2e),
        "visitors_missing_in_v2e_samples": missing_in_v2e[:25],
        "visitors_with_empty_sessions": sum(1 for rec in output_recommendations if rec["session_count"] == 0),
        "visitors_with_empty_exhibitors": sum(1 for rec in output_recommendations if rec["v2e_exhibitor_count"] == 0),
    }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset_name,
        "recommendations": output_recommendations,
    }
    return payload, incidence


def write_json(output_path: Path, payload: Dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def write_unmatched_csv(
    output_path: Path,
    main_missing: List[str],
    control_missing: List[str],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    in_main = set(main_missing)
    in_control = set(control_missing)
    all_missing = sorted(in_main | in_control)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["visitor_id", "in_main", "in_control", "source"],
        )
        writer.writeheader()
        for visitor_id in all_missing:
            main_flag = visitor_id in in_main
            control_flag = visitor_id in in_control
            if main_flag and control_flag:
                source = "main+control"
            elif main_flag:
                source = "main"
            else:
                source = "control"

            writer.writerow(
                {
                    "visitor_id": visitor_id,
                    "in_main": int(main_flag),
                    "in_control": int(control_flag),
                    "source": source,
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unify recommendations CSV files with v2e exhibitor JSON."
    )
    parser.add_argument(
        "--recommendation-run-id",
        default="",
        help=(
            "Optional RecommendationRun.run_id (e.g. tsl_engagement_20260224T195335Z_0166ba44). "
            "When provided, main/control CSV paths are auto-derived from run timestamp token."
        ),
    )
    parser.add_argument(
        "--recommendations-root",
        default="PA/data/tsl/recommendations",
        help="Root folder containing recommendation CSV exports.",
    )
    parser.add_argument(
        "--recommendations-csv",
        default="PA/data/tsl/recommendations/visitor_recommendations_tsl_20260214_144216.csv",
        help="Path to the main recommendations CSV.",
    )
    parser.add_argument(
        "--control-csv",
        default="PA/data/tsl/recommendations/control/visitor_recommendations_tsl_20260214_144216_control.csv",
        help="Path to the control recommendations CSV.",
    )
    parser.add_argument(
        "--v2e-json",
        default="PA/data/tsl/v2e_recommendations_3.json",
        help="Path to v2e recommendations JSON.",
    )
    parser.add_argument(
        "--output-main-json",
        default="PA/data/tsl/recommendations/visitor_recommendations_tsl_20260214_144216_unified.json",
        help="Output path for unified main recommendations JSON.",
    )
    parser.add_argument(
        "--output-control-json",
        default="PA/data/tsl/recommendations/visitor_recommendations_tsl_20260214_144216_control_unified.json",
        help="Output path for unified control recommendations JSON.",
    )
    parser.add_argument(
        "--incidence-report",
        default="PA/data/tsl/recommendations/unify_recommendations_incidence_report.json",
        help="Output path for incidence report JSON.",
    )
    parser.add_argument(
        "--unmatched-visitors-csv",
        default="PA/data/tsl/recommendations/unmatched_visitors_not_found_in_v2e.csv",
        help="Output path for unmatched visitor IDs CSV.",
    )
    return parser


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def infer_csv_paths_from_run_id(run_id: str, recommendations_root: Path) -> Tuple[Path, Path]:
    run_id = _normalize_text(run_id)
    if not run_id:
        raise ValueError("run_id is empty")

    prefix = run_id.split("_", 1)[0].strip().lower() or "tsl"
    match = re.search(r"_(\d{8})T(\d{6})Z_", run_id)
    if not match:
        raise ValueError(
            "Unable to parse timestamp token from run_id. Expected ..._YYYYMMDDTHHMMSSZ_..."
        )

    token = f"{match.group(1)}_{match.group(2)}"
    main_csv = recommendations_root / f"visitor_recommendations_{prefix}_{token}.csv"
    control_csv = recommendations_root / "control" / f"visitor_recommendations_{prefix}_{token}_control.csv"
    return main_csv, control_csv


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    recommendations_root = Path(args.recommendations_root)
    run_id = _normalize_text(args.recommendation_run_id)

    if run_id:
        recommendations_csv, control_csv = infer_csv_paths_from_run_id(run_id, recommendations_root)
    else:
        recommendations_csv = Path(args.recommendations_csv)
        control_csv = Path(args.control_csv)

    v2e_json = Path(args.v2e_json)
    output_main_json = Path(args.output_main_json)
    output_control_json = Path(args.output_control_json)
    incidence_report_path = Path(args.incidence_report)
    unmatched_visitors_csv = Path(args.unmatched_visitors_csv)

    if not recommendations_csv.exists():
        raise FileNotFoundError(f"Main recommendations CSV not found: {recommendations_csv}")
    if not control_csv.exists():
        raise FileNotFoundError(f"Control recommendations CSV not found: {control_csv}")

    exhibitors_by_badge, v2e_incidence = load_v2e_recommendations(v2e_json)

    main_grouped, main_csv_incidence = load_and_group_session_csv(recommendations_csv)
    control_grouped, control_csv_incidence = load_and_group_session_csv(control_csv)

    unified_main_payload, main_merge_incidence = unify_dataset(
        grouped_visitors=main_grouped,
        exhibitors_by_badge=exhibitors_by_badge,
        dataset_name="recommendations",
    )
    unified_control_payload, control_merge_incidence = unify_dataset(
        grouped_visitors=control_grouped,
        exhibitors_by_badge=exhibitors_by_badge,
        dataset_name="control",
    )

    write_json(output_main_json, unified_main_payload)
    write_json(output_control_json, unified_control_payload)

    all_csv_visitor_ids = set(main_grouped.keys()) | set(control_grouped.keys())
    matched_csv_visitor_ids = {
        visitor_id
        for visitor_id in all_csv_visitor_ids
        if visitor_id in exhibitors_by_badge
    }
    v2e_badge_ids = set(exhibitors_by_badge.keys())

    csv_overlap_counter = Counter(main_grouped.keys()) + Counter(control_grouped.keys())
    visitors_in_both_files = sorted(
        [visitor_id for visitor_id, count in csv_overlap_counter.items() if count > 1]
    )

    incidence_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": {
            "recommendation_run_id": run_id,
            "recommendations_root": str(recommendations_root),
            "recommendations_csv": str(recommendations_csv),
            "control_csv": str(control_csv),
            "v2e_json": str(v2e_json),
            "output_main_json": str(output_main_json),
            "output_control_json": str(output_control_json),
        },
        "v2e": v2e_incidence,
        "csv_main": main_csv_incidence,
        "csv_control": control_csv_incidence,
        "merge_main": main_merge_incidence,
        "merge_control": control_merge_incidence,
        "cross_file": {
            "csv_unique_visitors_across_both": len(all_csv_visitor_ids),
            "csv_visitors_matched_to_v2e": len(matched_csv_visitor_ids),
            "csv_visitors_not_found_in_v2e": len(all_csv_visitor_ids - v2e_badge_ids),
            "v2e_badge_ids_without_any_csv_visitor": len(v2e_badge_ids - all_csv_visitor_ids),
            "visitors_present_in_main_and_control": len(visitors_in_both_files),
            "visitors_present_in_main_and_control_samples": visitors_in_both_files[:25],
        },
    }

    write_json(incidence_report_path, incidence_report)

    write_unmatched_csv(
        output_path=unmatched_visitors_csv,
        main_missing=main_merge_incidence["visitors_missing_in_v2e_samples"]
        if main_merge_incidence["visitors_missing_in_v2e"] <= 25
        else sorted(set(main_grouped.keys()) - v2e_badge_ids),
        control_missing=control_merge_incidence["visitors_missing_in_v2e_samples"]
        if control_merge_incidence["visitors_missing_in_v2e"] <= 25
        else sorted(set(control_grouped.keys()) - v2e_badge_ids),
    )

    print("Unified main JSON:", output_main_json)
    print("Unified control JSON:", output_control_json)
    print("Incidence report:", incidence_report_path)
    print("Unmatched visitors CSV:", unmatched_visitors_csv)
    print("Main visitors:", main_merge_incidence["visitors_total"])
    print("Control visitors:", control_merge_incidence["visitors_total"])
    print(
        "Missing v2e IDs (main/control):",
        f"{main_merge_incidence['visitors_missing_in_v2e']}/{control_merge_incidence['visitors_missing_in_v2e']}",
    )


if __name__ == "__main__":
    main()