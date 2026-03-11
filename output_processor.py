#!/usr/bin/env python3
"""
Output Processor - Handles all file serialization and output operations for the PA system.

This processor is responsible for:
- Writing recommendation data to JSON and CSV files
- Converting recommendation payloads to DataFrames
- Updating Neo4j with recommendation metadata
- Managing control group outputs
- Generating output metadata and statistics

This separation reduces complexity in the main recommendation processor and allows
for easier testing and maintenance of output logic.
"""

import json
import time
import logging
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

from utils.neo4j_utils import resolve_neo4j_credentials


class OutputProcessor:
    """Handles all output operations for recommendation processing."""

    def __init__(self, config: Dict, logger: Optional[logging.Logger] = None):
        """
        Initialize the output processor.

        Args:
            config: Configuration dictionary
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.mode = str(config.get("mode", "personal_agendas")).strip().lower()

        # Extract configuration
        self.show_name = config.get("neo4j", {}).get("show_name", "bva")
        self.recommendation_config = config.get("recommendation", {})
        self.output_dir = Path(config.get("output_dir", "data/output"))
        self.project_root = Path(config.get("project_root", ".")).resolve()
        self.write_is_recommended_relationships = bool(
            self.recommendation_config.get(
                "write_is_recommended_relationships",
                self.mode != "post_analysis",
            )
        )

        # Neo4j connection for updates
        env_file = config.get("env_file", "keys/.env")
        env_path = Path(env_file)
        if not env_path.is_absolute():
            env_path = self.project_root.joinpath(env_file)
        load_dotenv(env_path)
        neo4j_config = config.get("neo4j", {})
        credentials = resolve_neo4j_credentials(config, logger=self.logger)
        self.uri = credentials["uri"]
        self.username = credentials["username"]
        self.password = credentials["password"]

        # Node labels
        node_labels = neo4j_config.get("node_labels", {})
        self.visitor_this_year_label = node_labels.get("visitor_this_year", "Visitor_this_year")
        self.session_this_year_label = node_labels.get("session_this_year", "Sessions_this_year")

        # Control group settings
        control_cfg = self.recommendation_config.get("control_group", {})
        self.control_group_property_name = control_cfg.get("neo4j_property", "control_group")
        self.control_group_enabled = bool(control_cfg.get("enabled", False))
        configured_control_modes = control_cfg.get("enabled_modes", ["personal_agendas"])
        if isinstance(configured_control_modes, str):
            configured_control_modes = [configured_control_modes]
        if not isinstance(configured_control_modes, list):
            configured_control_modes = ["personal_agendas"]
        self.control_group_enabled_modes = {
            str(mode).strip().lower()
            for mode in configured_control_modes
            if str(mode).strip()
        } or {"personal_agendas"}
        self.control_group_global_target_enabled = bool(
            control_cfg.get("global_target_enabled", True)
        )
        self.control_group_legacy_node_flag_sync = bool(
            control_cfg.get("legacy_node_flag_sync", False)
        )

        # Similarity attributes for DataFrame generation
        self.similarity_attributes = self.recommendation_config.get("similarity_attributes", {})

        # CSV enrichment fields
        self._csv_enrichment_fields = [
            "Email", "Forename", "Surname", "Tel", "Mobile", "Company",
            "JobTitle", "Email_domain", "Country", "Source"
        ]

    def _control_group_active_for_mode(self) -> bool:
        """Return True when control logic is enabled for the current mode."""
        return self.control_group_enabled and self.mode in self.control_group_enabled_modes

    def _resolve_traceability_context(self, create_only_new: bool) -> Dict[str, Any]:
        """Resolve run-scoped traceability metadata for current output execution."""
        trace_cfg = self.recommendation_config.get("traceability", {}) or {}

        run_mode = self.mode
        show = self.show_name

        configured_run_id = str(trace_cfg.get("run_id", "")).strip()
        run_id = configured_run_id or (
            f"{show}_{run_mode}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
        )

        campaign_id_cfg = trace_cfg.get("campaign_id", "")
        if isinstance(campaign_id_cfg, dict):
            configured_campaign_id = str(campaign_id_cfg.get(run_mode, "")).strip()
        else:
            configured_campaign_id = str(campaign_id_cfg).strip()
        if configured_campaign_id:
            campaign_id = configured_campaign_id
        elif run_mode == "engagement":
            campaign_id = f"{show}_engagement"
        else:
            campaign_id = f"{show}_conversion"

        return {
            "run_id": run_id,
            "campaign_id": campaign_id,
            "run_mode": run_mode,
            "show": show,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "pipeline_version": str(trace_cfg.get("pipeline_version", "pa_pipeline")),
            "allocation_version": str(
                trace_cfg.get("allocation_version", "incremental") if create_only_new else trace_cfg.get("allocation_version", "full")
            ),
            "write_delivery_events": bool(trace_cfg.get("write_delivery_events", True)),
        }

    def _upsert_recommendation_run(self, session, traceability_context: Dict[str, Any]) -> None:
        """Upsert the RecommendationRun node for the active run."""
        query = """
        MERGE (rr:RecommendationRun {run_id: $run_id})
        ON CREATE SET rr.created_at = $created_at
        SET rr.run_mode = $run_mode,
            rr.campaign_id = $campaign_id,
            rr.show = $show,
            rr.pipeline_version = $pipeline_version,
            rr.allocation_version = $allocation_version,
            rr.updated_at = $created_at
        """
        session.run(query, traceability_context)

    def process_outputs(
        self,
        recommendations_dict: Dict[str, Any],
        all_recommendations: List[Dict],
        statistics: Dict[str, Any],
        theatre_stats: Optional[Dict] = None,
        create_only_new: bool = False,
        control_assignment_map: Optional[Dict[str, int]] = None,
        external_recommendations_attached: int = 0,
        global_control_target_ids: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """
        Main method to process and save all recommendation outputs.

        Args:
            recommendations_dict: Main recommendations payload
            all_recommendations: All recommendations for Neo4j updates
            statistics: Processing statistics
            theatre_stats: Theatre capacity enforcement statistics
            create_only_new: Whether only new recommendations were processed
            control_assignment_map: Control group assignments
            external_recommendations_attached: Count of external recommendations

        Returns:
            Updated statistics dictionary
        """
        start_time = time.time()

        try:
            traceability_context = self._resolve_traceability_context(create_only_new)

            # Generate timestamp and output paths
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"recommendations/visitor_recommendations_{self.show_name}_{timestamp}.json"
            output_file.parent.mkdir(exist_ok=True)

            # Split control group data
            (
                main_recommendations,
                control_recommendations,
                control_summary,
                control_assignment_map,
            ) = self._split_control_group(recommendations_dict, control_assignment_map or {})

            # Guardrail checks: ensure final payloads respect per-visitor limits and have no time clashes
            guardrail_summary = self._evaluate_recommendation_guardrails(recommendations_dict)
            statistics["recommendation_guardrails"] = guardrail_summary

            # Update statistics with control group info
            self._update_statistics_with_control_group(
                statistics, main_recommendations, control_recommendations, control_summary
            )

            # Generate output metadata
            output_metadata = self._generate_output_metadata(
                len(recommendations_dict) + len(control_recommendations),
                main_recommendations,
                control_recommendations,
                statistics,
                theatre_stats,
                create_only_new,
                external_recommendations_attached,
                control_summary,
                traceability_context,
            )

            # Update Neo4j with recommendations
            if all_recommendations:
                self.logger.info("Updating Neo4j with recommendation data")
                self._update_visitor_recommendations(
                    all_recommendations,
                    control_assignment_map,
                    traceability_context,
                )
                self.logger.info("Completed Neo4j updates")

            # Enforce global control-group percentage target across full eligible population.
            if (
                self._control_group_active_for_mode()
                and self.control_group_global_target_enabled
                and self.control_group_legacy_node_flag_sync
            ):
                if global_control_target_ids is None:
                    self.logger.warning(
                        "Global control-group sync skipped: no target IDs were provided to output processing"
                    )
                else:
                    self._sync_global_control_group_assignments(global_control_target_ids)

            # Save main recommendations JSON if configured
            if self.recommendation_config.get("save_json", True):
                self._save_recommendations_json(
                    output_file, output_metadata, theatre_stats, main_recommendations, statistics
                )
                self.logger.info(f"Saved recommendations JSON to {output_file}")
            else:
                self.logger.info("Skipping JSON export (save_json disabled in config)")

            # Save CSV if configured
            if self.recommendation_config.get("save_csv", True):
                df = self._recommendations_to_dataframe(main_recommendations)
                csv_file = str(output_file).replace(".json", ".csv")
                df.to_csv(csv_file, index=False)
                self.logger.info(f"Saved recommendations DataFrame to {csv_file}")

            # Save control group outputs if applicable and JSON saving is enabled
            if control_recommendations and self.recommendation_config.get("save_json", True):
                self._save_control_group_outputs(
                    output_file, output_metadata, theatre_stats,
                    control_recommendations, statistics, control_summary
                )

            # Calculate processing time
            statistics["processing_time"] = time.time() - start_time
            self.logger.info(
                f"Completed output processing in {statistics['processing_time']:.2f} seconds"
            )

            return statistics

        except Exception as e:
            self.logger.error(f"Error in output processing: {str(e)}", exc_info=True)
            statistics["processing_time"] = time.time() - start_time
            return statistics

    def _evaluate_recommendation_guardrails(
        self,
        recommendations_dict: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run hard guardrails over final recommendation payloads and log violations."""

        max_recommendations = int(self.recommendation_config.get("max_recommendations", 10) or 10)
        over_limit_violations: List[Dict[str, Any]] = []
        overlap_violations: List[Dict[str, Any]] = []

        for visitor_id, payload in recommendations_dict.items():
            recs = payload.get("filtered_recommendations", []) or []
            rec_count = len(recs)

            if rec_count > max_recommendations:
                over_limit_violations.append(
                    {
                        "visitor_id": visitor_id,
                        "recommendation_count": rec_count,
                        "max_recommendations": max_recommendations,
                    }
                )

            overlap_pairs = self._count_overlapping_pairs(recs)
            if overlap_pairs > 0:
                overlap_violations.append(
                    {
                        "visitor_id": visitor_id,
                        "overlap_pairs": overlap_pairs,
                        "recommendation_count": rec_count,
                    }
                )

        if over_limit_violations:
            self.logger.warning(
                "GUARDRAIL: %d visitor(s) exceed max_recommendations=%d",
                len(over_limit_violations),
                max_recommendations,
            )
            for violation in over_limit_violations[:20]:
                self.logger.warning(
                    "GUARDRAIL over-limit visitor=%s recommendations=%d max=%d",
                    violation["visitor_id"],
                    violation["recommendation_count"],
                    violation["max_recommendations"],
                )
            if len(over_limit_violations) > 20:
                self.logger.warning(
                    "GUARDRAIL over-limit additional visitors not shown: %d",
                    len(over_limit_violations) - 20,
                )

        if overlap_violations:
            self.logger.warning(
                "GUARDRAIL: %d visitor(s) still have overlapping recommendation slots",
                len(overlap_violations),
            )
            for violation in overlap_violations[:20]:
                self.logger.warning(
                    "GUARDRAIL overlap visitor=%s overlap_pairs=%d recommendations=%d",
                    violation["visitor_id"],
                    violation["overlap_pairs"],
                    violation["recommendation_count"],
                )
            if len(overlap_violations) > 20:
                self.logger.warning(
                    "GUARDRAIL overlap additional visitors not shown: %d",
                    len(overlap_violations) - 20,
                )

        return {
            "max_recommendations": max_recommendations,
            "visitors_checked": len(recommendations_dict),
            "violations": {
                "over_limit": len(over_limit_violations),
                "overlap_conflicts": len(overlap_violations),
                "total": len(over_limit_violations) + len(overlap_violations),
            },
            "over_limit_visitors": over_limit_violations,
            "overlap_visitors": overlap_violations,
        }

    def _count_overlapping_pairs(self, recommendations: List[Dict[str, Any]]) -> int:
        """Count time-overlap pairs inside a single visitor recommendation list."""

        if len(recommendations) <= 1:
            return 0

        intervals: List[Tuple[pd.Timestamp, pd.Timestamp]] = []
        for rec in recommendations:
            date_value = rec.get("date") or rec.get("session_date")
            start_value = rec.get("start_time") or rec.get("session_start_time")
            end_value = rec.get("end_time") or rec.get("session_end_time")

            if not date_value or not start_value or not end_value:
                continue

            start_dt = pd.to_datetime(f"{date_value} {start_value}", errors="coerce")
            end_dt = pd.to_datetime(f"{date_value} {end_value}", errors="coerce")
            if pd.isna(start_dt) or pd.isna(end_dt):
                continue

            intervals.append((start_dt, end_dt))

        overlap_pairs = 0
        for i in range(len(intervals)):
            start_a, end_a = intervals[i]
            for j in range(i + 1, len(intervals)):
                start_b, end_b = intervals[j]
                if start_a < end_b and end_a > start_b:
                    overlap_pairs += 1

        return overlap_pairs

    def _split_control_group(
        self,
        recommendations_dict: Dict[str, Any],
        control_assignment_map: Dict[str, int]
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, int]]:
        """Split recommendations into main and control groups."""
        main_recommendations = {}
        control_recommendations = {}
        control_summary = {"enabled": False}

        control_cfg = self.recommendation_config.get("control_group", {})
        if not self._control_group_active_for_mode():
            return main_recommendations, control_recommendations, control_summary, control_assignment_map

        # Split based on control assignment map
        for visitor_id, payload in recommendations_dict.items():
            if control_assignment_map.get(visitor_id, 0) == 1:
                control_recommendations[visitor_id] = payload
            else:
                main_recommendations[visitor_id] = payload

        control_summary = {
            "enabled": True,
            "percentage": control_cfg.get("percentage", 0),
            "random_seed": control_cfg.get("random_seed"),
            "withheld_visitors": len(control_recommendations),
        }

        return main_recommendations, control_recommendations, control_summary, control_assignment_map

    def _update_statistics_with_control_group(
        self,
        statistics: Dict[str, Any],
        main_recommendations: Dict[str, Any],
        control_recommendations: Dict[str, Any],
        control_summary: Dict[str, Any]
    ) -> None:
        """Update statistics with control group information."""
        main_total_recommendations = sum(
            len(payload.get("filtered_recommendations", [])) for payload in main_recommendations.values()
        )
        main_unique_sessions = set()
        main_successful = 0
        for payload in main_recommendations.values():
            recs = payload.get("filtered_recommendations", [])
            if recs:
                main_successful += 1
            for rec in recs:
                if rec.get("session_id"):
                    main_unique_sessions.add(rec["session_id"])

        control_total_recommendations = sum(
            len(payload.get("filtered_recommendations", [])) for payload in control_recommendations.values()
        )
        control_unique_sessions = set()
        control_successful = 0
        for payload in control_recommendations.values():
            recs = payload.get("filtered_recommendations", [])
            if recs:
                control_successful += 1
            for rec in recs:
                if rec.get("session_id"):
                    control_unique_sessions.add(rec["session_id"])

        control_summary.update({
            "withheld_recommendations": control_total_recommendations,
            "withheld_successful": control_successful,
        })

        statistics["control_group"] = control_summary

    def _generate_output_metadata(
        self,
        total_visitors_processed: int,
        main_recommendations: Dict[str, Any],
        control_recommendations: Dict[str, Any],
        statistics: Dict[str, Any],
        theatre_stats: Optional[Dict],
        create_only_new: bool,
        external_recommendations_attached: int,
        control_summary: Dict[str, Any],
        traceability_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate metadata for output files."""
        main_successful = sum(1 for payload in main_recommendations.values()
                             if payload.get("filtered_recommendations"))
        main_total_recommendations = sum(
            len(payload.get("filtered_recommendations", [])) for payload in main_recommendations.values()
        )
        main_unique_sessions = len(set(
            rec["session_id"] for payload in main_recommendations.values()
            for rec in payload.get("filtered_recommendations", []) if rec.get("session_id")
        ))

        control_successful = sum(1 for payload in control_recommendations.values()
                                if payload.get("filtered_recommendations"))
        control_total_recommendations = sum(
            len(payload.get("filtered_recommendations", [])) for payload in control_recommendations.values()
        )

        return {
            "generated_at": datetime.now().isoformat(),
            "show": self.show_name,
            "visitors_processed": total_visitors_processed,
            "successful": main_successful,
            "successful_before_control": statistics.get("visitors_with_recommendations", 0),
            "errors": statistics.get("errors", 0),
            "total_recommendations": main_total_recommendations,
            "total_recommendations_before_control": statistics.get("total_recommendations_generated", 0),
            "unique_sessions": main_unique_sessions,
            "filtering_enabled": self.recommendation_config.get("enable_filtering", False),
            "create_only_new": create_only_new,
            "external_recommendations_attached": external_recommendations_attached,
            "control_group": control_summary,
            "traceability": {
                "run_id": traceability_context.get("run_id"),
                "campaign_id": traceability_context.get("campaign_id"),
                "run_mode": traceability_context.get("run_mode"),
                "show": traceability_context.get("show"),
                "pipeline_version": traceability_context.get("pipeline_version"),
                "allocation_version": traceability_context.get("allocation_version"),
            },
            "configuration": {
                "min_similarity_score": self.recommendation_config.get("min_similarity_score", 0.3),
                "max_recommendations": self.recommendation_config.get("max_recommendations", 10),
                "similar_visitors_count": self.recommendation_config.get("similar_visitors_count", 3),
                "theatre_capacity_enforced": self.recommendation_config.get("theatre_capacity_limits", {}).get("enabled", False),
                "theatre_capacity_multiplier": self.recommendation_config.get("theatre_capacity_limits", {}).get("capacity_multiplier", 3.0),
            },
        }

    def _save_recommendations_json(
        self,
        output_file: Path,
        metadata: Dict[str, Any],
        theatre_stats: Optional[Dict],
        recommendations: Dict[str, Any],
        statistics: Dict[str, Any]
    ) -> None:
        """Save recommendations to JSON file."""
        output_data = {
            "metadata": metadata,
            "theatre_capacity_stats": theatre_stats,
            "recommendations": recommendations,
            "statistics": statistics,
        }

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2, default=str)

        self.logger.info(f"Saved recommendations to {output_file}")

    def _save_control_group_outputs(
        self,
        base_output_file: Path,
        base_metadata: Dict[str, Any],
        theatre_stats: Optional[Dict],
        control_recommendations: Dict[str, Any],
        statistics: Dict[str, Any],
        control_summary: Dict[str, Any]
    ) -> None:
        """Save control group outputs separately."""
        control_output_file = self._get_control_output_path(base_output_file)

        control_metadata = base_metadata.copy()
        control_metadata.update({
            "control_group_dataset": True,
            "successful": sum(1 for payload in control_recommendations.values()
                             if payload.get("filtered_recommendations")),
            "total_recommendations": sum(
                len(payload.get("filtered_recommendations", []))
                for payload in control_recommendations.values()
            ),
            "unique_sessions": len(set(
                rec["session_id"] for payload in control_recommendations.values()
                for rec in payload.get("filtered_recommendations", []) if rec.get("session_id")
            )),
        })

        control_output = {
            "metadata": control_metadata,
            "theatre_capacity_stats": theatre_stats,
            "recommendations": control_recommendations,
            "statistics": statistics,
        }

        with open(control_output_file, "w") as f:
            json.dump(control_output, f, indent=2, default=str)

        self.logger.info(f"Saved control group recommendations to {control_output_file}")

        # Save CSV if configured
        if self.recommendation_config.get("save_csv", True):
            df_control = self._recommendations_to_dataframe(control_recommendations)
            control_csv = str(control_output_file).replace(".json", ".csv")
            df_control.to_csv(control_csv, index=False)
            self.logger.info(f"Saved control group DataFrame to {control_csv}")

    def _get_control_output_path(self, base_output_file: Path) -> Path:
        """Generate control group output file path."""
        control_cfg = self.recommendation_config.get("control_group", {})
        file_suffix = control_cfg.get("file_suffix", "_control")
        output_directory = control_cfg.get("output_directory", "recommendations/control")

        # Create control directory
        control_dir = self.output_dir / output_directory
        control_dir.mkdir(exist_ok=True)

        # Generate filename with suffix
        base_name = base_output_file.name
        if base_name.endswith('.json'):
            control_name = base_name.replace('.json', f'{file_suffix}.json')
        else:
            control_name = f"{base_name}{file_suffix}"

        return control_dir / control_name

    def _recommendations_to_dataframe(self, recommendations: Dict[str, Any]) -> pd.DataFrame:
        """Build a recommendations DataFrame from an in-memory payload."""
        try:
            rows = []

            extra_fields = self.recommendation_config.get("export_additional_visitor_fields", [])
            extra_fields = [f for f in extra_fields if isinstance(f, str) and f]
            for f in ["Email", "Forename", "Surname", "Tel", "Mobile"]:
                if f not in extra_fields:
                    extra_fields.append(f)

            for visitor_id, recs in recommendations.items():
                visitor_info = recs.get("visitor", {})
                metadata = recs.get("metadata", {})
                notes = metadata.get("notes", [])
                if isinstance(notes, list):
                    metadata_list = [str(n) for n in notes if n]
                elif isinstance(notes, str):
                    metadata_list = [notes] if notes else []
                else:
                    metadata_list = []
                metadata_summary = json.dumps(metadata_list)

                for rec in recs.get("filtered_recommendations", []):
                    row = {
                        "visitor_id": visitor_id,
                        "assist_year_before": visitor_info.get("assist_year_before", "0"),
                        "show": self.show_name,
                    }

                    # Add similarity attributes
                    for attr_name in self.similarity_attributes.keys():
                        col_name = attr_name.replace(" ", "_").replace(".", "")
                        row[col_name] = visitor_info.get(attr_name, "NA")

                    # Add base context fields
                    base_context_fields = ["Company", "JobTitle", "Email_domain", "Country", "Source"]
                    for field in base_context_fields:
                        if field not in self.similarity_attributes:
                            row[field] = visitor_info.get(field, "NA")

                    # Add extra fields
                    for field in extra_fields:
                        if field not in row:
                            row[field] = visitor_info.get(field, "NA")

                    # Add session information
                    session_id_value = str(rec.get("session_id", "")).strip()
                    if not session_id_value:
                        session_id_value = "NA"

                    row.update({
                        "session_id": session_id_value,
                        "session_title": rec.get("title"),
                        "session_stream": rec.get("stream"),
                        "session_speaker_id": rec.get("speaker_id", "NA"),
                        "session_date": rec.get("date"),
                        "session_start_time": rec.get("start_time"),
                        "session_end_time": rec.get("end_time"),
                        "similarity_score": rec.get("similarity"),
                        "sponsored_by": rec.get("sponsored_by", ""),
                        "session_theatre_name": rec.get("theatre__name")
                        or rec.get("theatre_name")
                        or rec.get("theatre")
                        or "",
                        "overlapping_sessions": rec.get("overlapping_sessions", ""),
                        "recommendation_metadata": metadata_summary,
                    })

                    rows.append(row)

            if not rows:
                return pd.DataFrame()

            df = pd.DataFrame(rows)
            df = self._flag_overlapping_sessions(df)

            # Reorder columns
            priority_cols = ["visitor_id", "show", "assist_year_before"]
            similarity_cols = [
                col for col in df.columns
                if col in [attr.replace(" ", "_").replace(".", "") for attr in self.similarity_attributes.keys()]
            ]
            session_cols = [col for col in df.columns if col.startswith("session_")]
            if "overlapping_sessions" in df.columns:
                session_cols.append("overlapping_sessions")

            enrichment_cols = [
                c for c in ["Company", "JobTitle", "Email_domain", "Country", "Source"] if c in df.columns
            ]
            for f in extra_fields:
                if f in df.columns and f not in enrichment_cols:
                    enrichment_cols.append(f)

            categorized = set(priority_cols + similarity_cols + session_cols + enrichment_cols)
            other_cols = [c for c in df.columns if c not in categorized]

            ordered_cols = priority_cols + similarity_cols + enrichment_cols + other_cols + session_cols
            df = df[[col for col in ordered_cols if col in df.columns]]

            # Apply minimal CSV export if configured
            minimal_config = self.recommendation_config.get("export_csv_minimal", {})
            if minimal_config.get("enabled", False):
                minimal_fields = list(minimal_config.get("fields", []))
                if "session_id" not in minimal_fields:
                    minimal_fields.insert(0, "session_id")
                if minimal_fields:
                    missing_fields = [f for f in minimal_fields if f not in df.columns]
                    if missing_fields:
                        self.logger.warning(f"Minimal CSV export fields missing from DataFrame: {missing_fields}")
                    available_fields = [f for f in minimal_fields if f in df.columns]
                    if available_fields:
                        df = df[available_fields]
                        self.logger.info(f"Filtered CSV export to minimal fields: {available_fields}")

            return df

        except Exception as exc:
            self.logger.error("Failed to build DataFrame from recommendations", exc_info=True)
            return pd.DataFrame()

    def _flag_overlapping_sessions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Annotate each visitor's recommendations with overlapping sessions by time."""
        if df.empty:
            return df

        try:
            # Group by visitor and check for time overlaps
            for visitor_id in df['visitor_id'].unique():
                visitor_sessions = df[df['visitor_id'] == visitor_id].copy()

                if len(visitor_sessions) <= 1:
                    continue

                # Parse times and check overlaps
                overlaps = []
                for i, row in visitor_sessions.iterrows():
                    session_start = row.get('session_start_time')
                    session_end = row.get('session_end_time')
                    session_date = row.get('session_date')

                    if not all([session_start, session_end, session_date]):
                        continue

                    try:
                        start_dt = pd.to_datetime(f"{session_date} {session_start}")
                        end_dt = pd.to_datetime(f"{session_date} {session_end}")

                        # Check against other sessions
                        overlapping = []
                        for j, other_row in visitor_sessions.iterrows():
                            if i == j:
                                continue

                            other_start = other_row.get('session_start_time')
                            other_end = other_row.get('session_end_time')
                            other_date = other_row.get('session_date')

                            if not all([other_start, other_end, other_date]):
                                continue

                            try:
                                other_start_dt = pd.to_datetime(f"{other_date} {other_start}")
                                other_end_dt = pd.to_datetime(f"{other_date} {other_end}")

                                # Check for overlap
                                if (start_dt < other_end_dt) and (end_dt > other_start_dt):
                                    overlapping.append(str(other_row.get('session_id', '')))

                            except (ValueError, TypeError):
                                continue

                        if overlapping:
                            overlaps.append(f"{row.get('session_id', '')}: overlaps with {', '.join(overlapping)}")

                    except (ValueError, TypeError):
                        continue

                # Update the dataframe
                if overlaps:
                    overlap_text = "; ".join(overlaps)
                    df.loc[df['visitor_id'] == visitor_id, 'overlapping_sessions'] = overlap_text

            return df

        except Exception as e:
            self.logger.error(f"Error flagging overlapping sessions: {str(e)}")
            return df

    def _update_visitor_recommendations(
        self,
        recommendations_data: List[Dict],
        control_group_map: Optional[Dict[str, int]] = None,
        traceability_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update visitors with recommendation metadata and control group assignment."""
        try:
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
                with driver.session() as session:
                    traceability_context = traceability_context or {}
                    run_id = str(traceability_context.get("run_id", "")).strip()
                    campaign_id = str(traceability_context.get("campaign_id", "")).strip()
                    run_mode = str(traceability_context.get("run_mode", self.mode)).strip() or self.mode
                    show = str(traceability_context.get("show", self.show_name)).strip() or self.show_name
                    run_timestamp = str(traceability_context.get("created_at", datetime.now(timezone.utc).isoformat())).strip()

                    if run_id:
                        self._upsert_recommendation_run(session, traceability_context)

                    updated_with_recs = 0
                    updated_without_recs = 0
                    control_group_map = control_group_map or {}

                    for rec in recommendations_data:
                        visitor_id = rec["visitor"]["BadgeId"]
                        control_value = control_group_map.get(visitor_id, 0)
                        recommended_sessions = rec.get("filtered_recommendations", [])
                        timestamp = datetime.now().isoformat()

                        # Replace recommendation set for this visitor/show to avoid stale
                        # recommendations accumulating across reruns of the SAME run_id.
                        # In post_analysis mode, do not mutate IS_RECOMMENDED relationships.
                        if self.write_is_recommended_relationships:
                            clear_query = f"""
                            MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
                            WHERE v.show = $show_name OR v.show IS NULL
                            OPTIONAL MATCH (v)-[r:IS_RECOMMENDED]->(s:{self.session_this_year_label})
                            WHERE r.run_id = $run_id
                            DELETE r
                            """
                            session.run(
                                clear_query,
                                visitor_id=visitor_id,
                                show_name=self.show_name,
                                run_id=run_id,
                            )

                        if recommended_sessions:
                            # Update visitor with has_recommendation flag
                            control_update_clause = (
                                f",\n                                v.{self.control_group_property_name} = $control_group"
                                if self.control_group_legacy_node_flag_sync
                                else ""
                            )

                            update_query = f"""
                            MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
                            WHERE v.show = $show_name OR v.show IS NULL
                            SET v.has_recommendation = "1",
                                v.show = $show_name,
                                v.recommendations_generated_at = $timestamp,
                                v.last_recommendation_run_id = $run_id,
                                v.last_recommendation_campaign_id = $campaign_id,
                                v.last_recommendation_mode = $run_mode
                                {control_update_clause}
                            """
                            session.run(update_query,
                                       visitor_id=visitor_id,
                                       show_name=self.show_name,
                                       timestamp=timestamp,
                                       run_id=run_id,
                                       campaign_id=campaign_id,
                                       run_mode=run_mode,
                                       control_group=control_value)
                            updated_with_recs += 1

                            # Create IS_RECOMMENDED relationships (disabled by default in post_analysis mode)
                            if self.write_is_recommended_relationships:
                                for rec_session in recommended_sessions:
                                    session_id = rec_session.get("session_id")
                                    if session_id:
                                        rel_query = f"""
                                        MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
                                        WHERE v.show = $show_name
                                        MATCH (s:{self.session_this_year_label} {{session_id: $session_id}})
                                        WHERE s.title IS NOT NULL AND trim(s.title) <> ''
                                        MERGE (v)-[r:IS_RECOMMENDED {{run_id: $run_id}}]->(s)
                                        SET r.similarity_score = $score,
                                            r.generated_at = $timestamp,
                                            r.show = $show_name,
                                            r.run_mode = $run_mode,
                                            r.campaign_id = $campaign_id,
                                            r.control_group = $control_group,
                                            r.control_group_type = CASE WHEN $control_group = 1 THEN $run_mode ELSE r.control_group_type END
                                        """
                                        session.run(
                                            rel_query,
                                            visitor_id=visitor_id,
                                            show_name=self.show_name,
                                            session_id=session_id,
                                            score=rec_session.get("similarity", 0),
                                            timestamp=timestamp,
                                            run_id=run_id,
                                            run_mode=run_mode,
                                            campaign_id=campaign_id,
                                            control_group=control_value,
                                        )
                        else:
                            # Mark visitor as processed but without recommendations
                            control_update_clause = (
                                f",\n                                v.{self.control_group_property_name} = $control_group"
                                if self.control_group_legacy_node_flag_sync
                                else ""
                            )

                            update_query = f"""
                            MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
                            WHERE v.show = $show_name OR v.show IS NULL
                            SET v.has_recommendation = "0",
                                v.show = $show_name,
                                v.recommendations_generated_at = $timestamp,
                                v.last_recommendation_run_id = $run_id,
                                v.last_recommendation_campaign_id = $campaign_id,
                                v.last_recommendation_mode = $run_mode
                                {control_update_clause}
                            """
                            session.run(update_query,
                                       visitor_id=visitor_id,
                                       show_name=self.show_name,
                                       timestamp=timestamp,
                                       run_id=run_id,
                                       campaign_id=campaign_id,
                                       run_mode=run_mode,
                                       control_group=control_value)
                            updated_without_recs += 1

                        if traceability_context.get("write_delivery_events", True) and run_id:
                            delivery_id = f"{run_id}::{visitor_id}"
                            delivery_status = "withheld_control" if control_value == 1 else "sent"
                            delivery_query = f"""
                            MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
                            MERGE (rr:RecommendationRun {{run_id: $run_id}})
                            MERGE (d:CampaignDelivery {{delivery_id: $delivery_id}})
                            ON CREATE SET d.created_at = $timestamp
                            SET d.run_id = $run_id,
                                d.campaign_id = $campaign_id,
                                d.run_mode = $run_mode,
                                d.visitor_id = $visitor_id,
                                d.status = $status,
                                d.timestamp = $timestamp,
                                d.show = $show_name,
                                d.updated_at = $timestamp
                            MERGE (d)-[:FOR_VISITOR]->(v)
                            MERGE (d)-[:FOR_RUN]->(rr)
                            """
                            session.run(
                                delivery_query,
                                visitor_id=visitor_id,
                                run_id=run_id,
                                campaign_id=campaign_id,
                                run_mode=run_mode,
                                delivery_id=delivery_id,
                                status=delivery_status,
                                timestamp=run_timestamp,
                                show_name=show,
                            )

                    self.logger.info(
                        f"Updated {updated_with_recs} visitors with recommendations, "
                        f"{updated_without_recs} without recommendations"
                    )

        except Exception as e:
            self.logger.error(f"Error updating visitor recommendations: {str(e)}", exc_info=True)

    def _sync_global_control_group_assignments(self, selected_control_ids: Set[str]) -> None:
        """Sync control-group flag for all show visitors to a global target set."""
        try:
            selected_control_ids = {str(v) for v in (selected_control_ids or set()) if str(v)}
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
                with driver.session() as session:
                    reset_query = f"""
                    MATCH (v:{self.visitor_this_year_label})
                    WHERE v.show = $show_name OR v.show IS NULL
                      AND NOT v.BadgeId IN $selected_ids
                    SET v.{self.control_group_property_name} = 0
                    RETURN count(v) as reset_count
                    """
                    reset_count = session.run(
                        reset_query,
                        show_name=self.show_name,
                        selected_ids=sorted(selected_control_ids),
                    ).single()["reset_count"]

                    set_count_total = 0
                    if selected_control_ids:
                        set_query = f"""
                        UNWIND $badge_ids AS badge_id
                        MATCH (v:{self.visitor_this_year_label} {{BadgeId: badge_id}})
                        WHERE v.show = $show_name OR v.show IS NULL
                        SET v.{self.control_group_property_name} = 1
                        RETURN count(v) as set_count
                        """
                        selected_list = sorted(selected_control_ids)
                        batch_size = 2000
                        for i in range(0, len(selected_list), batch_size):
                            batch = selected_list[i : i + batch_size]
                            set_count = session.run(
                                set_query,
                                badge_ids=batch,
                                show_name=self.show_name,
                            ).single()["set_count"]
                            set_count_total += int(set_count)

                    self.logger.info(
                        "Global control-group sync applied: selected=%d, set=%d, reset=%d",
                        len(selected_control_ids),
                        set_count_total,
                        int(reset_count),
                    )
        except Exception as exc:
            self.logger.error(
                "Error syncing global control-group assignments: %s",
                str(exc),
                exc_info=True,
            )

    def json_to_dataframe(self, json_file: str) -> pd.DataFrame:
        """Convert recommendations JSON to DataFrame for analysis."""
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
            payload = data.get("recommendations", {})
            return self._recommendations_to_dataframe(payload)
        except Exception as e:
            self.logger.error(f"Error converting JSON to DataFrame: {str(e)}", exc_info=True)
            return pd.DataFrame()