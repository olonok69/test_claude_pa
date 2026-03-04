# PA Script Reference (scripts + one_time)

This document summarizes all Python scripts under:
- `PA/scripts`
- `PA/one_time`

Run commands from repo root (`/mnt/wolverine/home/samtukra/juan/repos/PA`) unless noted.

## General usage pattern

- Inspect script options:
  - `python PA/scripts/<script_name>.py --help`
  - `python PA/one_time/<script_name>.py --help`
- Most scripts are operational and may read/write Neo4j or output files.
- Prefer dry-run/verify modes first when available.

---

## PA/scripts

### Analysis / Audit

| Script | What it is for | Typical use |
|---|---|---|
| [PA/scripts/analyze_tsl_recommendation_run.py](PA/scripts/analyze_tsl_recommendation_run.py) | Analyze a completed TSL recommendation run and validate engagement theatre-filter behavior. | Post-run QA of recommendation quality and filter compliance. |
| [PA/scripts/audit_recommendation_runs_post_analysis.py](PA/scripts/audit_recommendation_runs_post_analysis.py) | Audit RecommendationRun integrity for post-analysis readiness. | Pre post-analysis gate to check run consistency and blockers. |
| [PA/scripts/check_v2e_unified_random_pairs.py](PA/scripts/check_v2e_unified_random_pairs.py) | Randomly verify unified V2E recommendations against Neo4j. | Sanity sample checks before/after imports. |
| [PA/scripts/dry_run_m4_engagement_control.py](PA/scripts/dry_run_m4_engagement_control.py) | Read-only dry-run validator for M4 engagement control-group behavior. | Validate M4 control logic without writes. |
| [PA/scripts/run_post_analysis_identity_validation.py](PA/scripts/run_post_analysis_identity_validation.py) | Run identity continuity activation + validation in one command. | Final identity checks before post-analysis reporting. |

### Reconciliation / Restore / Migration

| Script | What it is for | Typical use |
|---|---|---|
| [PA/scripts/reconcile_legacy_delivery_from_unified.py](PA/scripts/reconcile_legacy_delivery_from_unified.py) | Reconcile recommendation lineage and CampaignDelivery integrity from unified JSON files. | Main verify/apply reconciler for session+exhibitor pairs and delivery links. |
| [PA/scripts/reconcile_engagement_delivery_from_unified.py](PA/scripts/reconcile_engagement_delivery_from_unified.py) | Wrapper around legacy reconciler with engagement defaults. | Engagement-specific reconcile run with fewer required flags. |
| [PA/scripts/reconcile_campaign_delivery.py](PA/scripts/reconcile_campaign_delivery.py) | M5 reconciliation of output files vs CampaignDelivery ledger. | Check delivery ledger consistency against exports. |
| [PA/scripts/reconcile_one_time_delivery_run.py](PA/scripts/reconcile_one_time_delivery_run.py) | One-time reconciliation for one recommendation run. | Surgical reconciliation for a specific historical run. |
| [PA/scripts/reconcile_tsl_control_group.py](PA/scripts/reconcile_tsl_control_group.py) | Reconcile definitive control group across Neo4j and exports. | Validate/repair control-group continuity and percentages. |
| [PA/scripts/restore_recommendations_from_export.py](PA/scripts/restore_recommendations_from_export.py) | Rebuild Neo4j recommendation flags/relationships from exported files. | Disaster recovery or targeted reconstruction from exports. |
| [PA/scripts/rebuild_pa_run_from_csv.py](PA/scripts/rebuild_pa_run_from_csv.py) | Rebuild RecommendationRun + IS_RECOMMENDED + CampaignDelivery from CSV inputs. | Incremental PA rebuild path from main/control CSV outputs. |
| [PA/scripts/verify_enforce_relationship_run_mapping.py](PA/scripts/verify_enforce_relationship_run_mapping.py) | Verify and enforce run lineage on recommendation relationships. | Backfill/repair run metadata on existing relationships. |
| [PA/scripts/backfill_relationship_run_lineage.py](PA/scripts/backfill_relationship_run_lineage.py) | One-time lineage backfill while preserving a protected run_id. | Historical migration where relationships lack proper run lineage. |
| [PA/scripts/migrate_traceability_m2.py](PA/scripts/migrate_traceability_m2.py) | M2 migration for run traceability schema/backfill in Neo4j. | Apply traceability migration and metadata normalization. |
| [PA/scripts/fix_legacy_campaign_delivery_status.py](PA/scripts/fix_legacy_campaign_delivery_status.py) | One-time fixer for legacy CampaignDelivery control statuses. | Correct old delivery statuses (e.g., control/sent mismatches). |

### Import / Unify / Utilities

| Script | What it is for | Typical use |
|---|---|---|
| [PA/scripts/import_v2e_recommendations_to_neo4j.py](PA/scripts/import_v2e_recommendations_to_neo4j.py) | Import V2E exhibitor recommendations into Neo4j. | Upsert exhibitor recommendations and optional delivery links for a run. |
| [PA/scripts/unify_recommendations_with_v2e.py](PA/scripts/unify_recommendations_with_v2e.py) | Unify session recommendation CSVs with V2E exhibitor JSON. | Produce `_unified.json` and control-unified outputs before reconciliation. |
| [PA/scripts/control_group_calculator.py](PA/scripts/control_group_calculator.py) | Control-group size calculator for recommendation A/B testing. | Compute/control expected control-group sizing. |
| [PA/scripts/find_missing_practices.py](PA/scripts/find_missing_practices.py) | Identify registration companies absent from the practices catalogue. | Data-quality pass for practices mapping completeness. |
| [PA/scripts/neo4j_backup_cli.py](PA/scripts/neo4j_backup_cli.py) | CLI wrapper around Neo4j backup manager. | Manage Aura snapshots/backup operations for project databases. |

---

## PA/one_time

| Script | What it is for | Typical use |
|---|---|---|
| [PA/one_time/delete_show_data.py](PA/one_time/delete_show_data.py) | Delete all nodes/relationships for a specific show from Neo4j. | One-off environment cleanup/reset for a show. |
| [PA/one_time/post_show_analysis.py](PA/one_time/post_show_analysis.py) | Generate post-show recommendation analysis (legacy one-time analysis flow). | Historical post-show analytics run. |

---

## Suggested execution order for current TSL workflow

1. Run generator pipelines (session/control outputs).
2. Run [PA/scripts/unify_recommendations_with_v2e.py](PA/scripts/unify_recommendations_with_v2e.py).
3. Run reconciliation scripts (`--dry-run` first, then `--apply`).
4. Run audit/analysis scripts and generate documentation.

---

## Notes

- If unsure which script to use, start with:
  - [PA/scripts/unify_recommendations_with_v2e.py](PA/scripts/unify_recommendations_with_v2e.py)
  - [PA/scripts/reconcile_legacy_delivery_from_unified.py](PA/scripts/reconcile_legacy_delivery_from_unified.py)
  - [PA/scripts/audit_recommendation_runs_post_analysis.py](PA/scripts/audit_recommendation_runs_post_analysis.py)
- For any script that writes to Neo4j, snapshot/backup first when possible.
