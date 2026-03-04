# Follow-Up Changelog

Purpose: track changes made after conversation closure so restart context stays current.

## 2026-02-21 (initial closure pack)
- Created follow-up folder: `docs/post_event_followup_pack/`.
- Added restart handoff pack:
  - `post_event_handoff_2026-02-21.md`
  - `post_event_day0_runsheet.md`
- Added curated snapshots under `reference_docs/`:
  - `plan_b_implementation_milestones.md`
  - `m2_traceability_migration_runbook.md`
  - `m5_delivery_reconciliation_runbook.md`
  - `post_analysis_mode.md`
  - `application_overview.md`
  - `engagement_mode.md`
  - `run_traceability_schema_contract.md`
  - `phase_d_execution_plan_full_traceability.md`
- Added folder index and consistency rules in `README.md`.

## 2026-02-21 (deep agents + azureml planning)
- Added Azure ML refactor planning document:
  - `AZUREML_PIPELINE_REFACTOR_PLAN.md`
- Added Deep Agents reporting refactor planning document:
  - `DEEP_AGENTS_REPORTS_REFACTOR_PLAN.md`
- Updated follow-up pack index to include both planning documents.

## 2026-02-21 (visitor label rename + go/no-go evidence)
- Runtime naming migration prepared for last-year visitor labels:
  - `Visitor_last_year_bva` -> `Visitor_last_year_main`
  - `Visitor_last_year_lva` -> `Visitor_last_year_secondary`
- Updated active runtime config label values:
  - `PA/config/config_tsl.yaml`
  - `PA/config/config_cpcn.yaml`
  - `PA/config/config_ecomm.yaml`
  - `PA/config/config_vet_bva.yaml`
  - `PA/config/config_vet_lva.yaml`
- Updated runtime fallback defaults to match new naming:
  - `PA/neo4j_visitor_processor.py`
  - `PA/neo4j_visitor_relationship_processor.py`
  - `PA/neo4j_specialization_stream_processor.py`
  - `PA/session_recommendation_processor.py`
- Added post-rename go/no-go section to:
  - `POST_MERGE_SANITY_CHECKLIST.md`
- Execution evidence (prod) after relabel + dry run:
  - Label integrity:
    - `new_main=5201`
    - `new_secondary=8809`
    - `old_main_remaining=0`
    - `old_secondary_remaining=0`
  - Relationship continuity:
    - `same_main=5043`
    - `same_secondary=10714`
    - `attended_main=3976`
    - `attended_secondary=4079`
  - Runtime smoke:
    - `python scripts/import_v2e_recommendations_to_neo4j.py --config config/config_tsl.yaml --v2e-json data/tsl/v2e_recommendations_3.json --dry-run` completed without label-not-found errors.

## 2026-02-24 (pending approval: engagement theatre mapping filter)
- Scope under review:
  - Add engagement-only recommendation filter so visitors are restricted to sessions in theatres mapped from last-year `ShowRef` plus `ALL` theatres.
  - Mapping source: `PA/data/tsl/theatre_name_x_show_ref_mapping_tsl26.csv`.
- Runtime implementation prepared (not yet approved for production run):
  - `PA/session_recommendation_processor.py`
  - `PA/config/config_tsl.yaml` (new `recommendation.engagement_show_theatre_filter` block)
- Current config intent:
  - Keep `recommendation.enable_filtering: false`.
  - Use only `recommendation.engagement_show_theatre_filter.enabled: true` in `mode: engagement`.
- Smoke evidence:
  - Processor compile check passed.
  - Mapping init check passed (`show_groups=5`, `global_theatres=1`, mode gate=`engagement`).
- Decision gate for tomorrow:
  - **Green flag:** restore pre-run backup, run engagement pipeline, execute post-run validation pack.
  - **Red flag:** disable `engagement_show_theatre_filter.enabled`, keep previous behavior, postpone rerun.
- Rollback safety:
  - Database backup available prior to rerun window.

## 2026-02-25 (engagement theatre filter validated on latest run)
- Summary:
  - Added and executed a dedicated post-run analyzer for TSL recommendation outputs.
  - Confirmed engagement theatre mapping rule is applied and passing on latest generated recommendations.
- Changed files:
  - `PA/scripts/analyze_tsl_recommendation_run.py`
  - `docs/post_event_followup_pack/FOLLOWUP_CHANGELOG.md`
  - `docs/post_event_followup_pack/README.md`
  - `docs/post_event_followup_pack/post_event_day0_runsheet.md`
  - `docs/post_event_followup_pack/post_event_handoff_2026-02-21.md`
- Why changed:
  - Need a repeatable console check to validate that recommendation outputs respect show-to-theatre restriction rules before downstream post-event actions.
- Validation/evidence:
  - Command executed:
    - `python scripts/analyze_tsl_recommendation_run.py --config config/config_tsl.yaml`
  - Result:
    - `STATUS: PASS`
    - `rows_total=253560`
    - `rows_violating_rule=0`
    - `violation_rate=0.0`
  - Artifacts:
    - `PA/large_tool_results/tsl_recommendation_run_analysis_20260225_074631.json`
    - `PA/large_tool_results/tsl_recommendation_run_analysis_20260225_074631.log`
  - Mapping sanity:
    - `rows_valid=14`, `show_groups=5`, `global_theatres=1`, `include_show_last_values=[ALL]`
- Follow-up actions:
  - Re-run the analyzer after each engagement recommendation regeneration.
  - Add analyzer JSON/log artifact paths to final post-event evidence bundle.

## 2026-02-25 (v2e run-scoped import execution log)
- Added run log document with commands, results, and Neo4j verification outputs:
  - `docs/post_event_followup_pack/v2e_run_execution_log_2026-02-25.md`
- Captured verified outcomes for run:
  - `run_id=tsl_engagement_20260224T195335Z_0166ba44`
  - `IS_RECOMMENDED_EXHIBITOR relationships=145930`
  - `scope integrity violations=0`
  - `metadata missing fields=0`

## 2026-02-25 (pre-show incremental run readiness pack)
- Added dedicated checklist for tomorrow's final pre-show incremental run (`personal_agendas`):
  - `docs/post_event_followup_pack/pre_show_incremental_runbook_2026-02-26.md`
- Updated pack index/start-here flow with the new runbook:
  - `docs/post_event_followup_pack/README.md`
- Tracking intent:
  - enforce run-scoped reconciliation evidence immediately after incremental run,
  - preserve a clean bridge into post-show strict identity gate and M6/M8 execution.

## 2026-02-26 (incremental run completed; restart handoff added)
- Summary:
  - Final pre-show incremental `personal_agendas` pipeline run completed.
  - Added a lightweight resume handoff to continue verification in a new session without repeating heavy checks.
- Changed files:
  - `docs/post_event_followup_pack/pre_show_incremental_execution_handoff_2026-02-26.md`
  - `docs/post_event_followup_pack/FOLLOWUP_CHANGELOG.md`
  - `docs/post_event_followup_pack/README.md`
- Why changed:
  - Session instability/OOM risk required a compact continuation package focused on reconciliation-first validation.
- Validation/evidence:
  - Operator-reported pipeline summary indicates successful completion at `2026-02-26T17:04:14.368378`.
  - Summary file path reported by pipeline: `logs/processing_summary.json`.
- Follow-up actions:
  - Resolve exact output `<timestamp>` files (main/control),
  - run `PA/scripts/reconcile_campaign_delivery.py --fail-on-mismatch`,
  - capture final `run_id` + reconciliation report path in follow-up pack.

## 2026-02-26 (campaign-id reconciliation alignment fix)
- Summary:
  - Resolved pre-show incremental reconciliation failure caused by expected campaign mismatch (`tsl_engagement` vs actual `tsl_conversion` for `personal_agendas`).
  - Added explicit env-file override support in reconciliation script to avoid runtime env resolution drift.
  - Reconciliation rerun passed with zero mismatches.
- Changed files:
  - `PA/config/config_tsl.yaml`
  - `PA/output_processor.py`
  - `PA/session_recommendation_processor.py`
  - `PA/scripts/reconcile_campaign_delivery.py`
  - `docs/post_event_followup_pack/pre_show_incremental_runbook_2026-02-26.md`
  - `docs/post_event_followup_pack/pre_show_incremental_execution_handoff_2026-02-26.md`
  - `docs/post_event_followup_pack/reference_docs/m5_delivery_reconciliation_runbook.md`
- Why changed:
  - Campaign id defaults are mode-dependent by design (`personal_agendas` => `tsl_conversion`, `engagement` => `tsl_engagement`).
  - Docs and commands were updated to enforce mode-aligned reconciliation inputs.
- Validation/evidence:
  - Command executed:
    - `python scripts/reconcile_campaign_delivery.py --config config/config_tsl.yaml --env-file keys/.env --main-json data/tsl/recommendations/visitor_recommendations_tsl_20260226_160736.json --control-json data/tsl/recommendations/control/visitor_recommendations_tsl_20260226_160736_control.json --run-id tsl_personal_agendas_20260226T160736Z_1b8f65e8 --campaign-id tsl_conversion --show tsl --report-file large_tool_results/m5_delivery_reconciliation_incremental_20260226_160736.json --fail-on-mismatch`
  - Result:
    - `reconciliation.ok=true`
    - `mismatch_total=0`
    - all mismatch counters and integrity violations = `0`
  - Artifact:
    - `large_tool_results/m5_delivery_reconciliation_incremental_20260226_160736.json`

## 2026-02-27 (run lineage remediation + V2E mapped verification)
- Summary:
  - Completed run-lineage verification/remediation workflow for recommendation relationships using file->run mappings.
  - Added progress logging for long verification runs.
  - Validated run-scoped V2E import + mapped enforcement outcomes with post-apply audits.
  - Active-cycle execution note: personal_agendas incremental run has **not** been started yet.
- Changed files:
  - `PA/scripts/check_v2e_unified_random_pairs.py`
  - `PA/scripts/backfill_relationship_run_lineage.py`
  - `PA/scripts/verify_enforce_relationship_run_mapping.py`
  - `PA/scripts/import_v2e_recommendations_to_neo4j.py`
  - `PA/scripts/unify_recommendations_with_v2e.py`
  - `docs/post_event_followup_pack/FOLLOWUP_CHANGELOG.md`
  - `docs/post_event_followup_pack/README.md`
- Why changed:
  - Need deterministic relationship provenance per `RecommendationRun` and reproducible verification evidence for mapped personal agenda + V2E artifacts.
- Validation/evidence:
  - Dry-run -> verify -> apply -> verify_after sequence executed for mapped files.
  - Engagement V2E scoped import executed (`v2e_recommendations_5.json`) with scoped merges to engagement run.
  - Post-apply mapped checks reported zero mismatches where relationships existed.
  - Neo4j audits confirmed residual untagged exhibitor relationships remain outside mapped file scope (expected backlog, not auto-mutated).
- Follow-up actions:
  - Keep running verify-only before/after any future write operation.
  - Start personal_agendas incremental only after preflight checks; then capture new `run_id` and reconciliation artifacts.

## 2026-03-02 (pre-show incremental closure + unified artifacts completed)
- Summary:
  - Final pre-show `personal_agendas` incremental cycle is complete and no further pre-show incremental action is planned.
  - Increment run artifacts were unified with V2E delta and verified for output consistency.
  - Engagement reconciliation was initiated; dry-run output indicates expected pre-apply blockers and no abnormal behavior so far.
- Changed files:
  - `docs/post_event_followup_pack/README.md`
  - `docs/post_event_followup_pack/FOLLOWUP_CHANGELOG.md`
  - `docs/post_event_followup_pack/pre_show_incremental_execution_handoff_2026-02-26.md`
- Why changed:
  - Align the follow-up pack with actual operational state before show opening and avoid stale "next pre-show incremental run" guidance.
- Validation/evidence:
  - Increment run id: `tsl_personal_agendas_20260227T224725Z_37b21c42`
  - Unified outputs generated:
    - `data/tsl/recommendations/visitor_recommendations_tsl_20260227_224725_unified.json`
    - `data/tsl/recommendations/visitor_recommendations_tsl_20260227_224725_control_unified.json`
    - `data/tsl/recommendations/unify_recommendations_incidence_report_20260227_224725.json`
  - Incidence summary:
    - `main visitors=7954`, `control visitors=948`, `missing v2e IDs=9/1`
- Follow-up actions:
  - Let engagement reconciliation finish and archive apply report.
  - Defer additional campaign changes until post-show.
  - Begin post-show analysis prep using the current schema/logic baseline.

## 2026-03-03 (engagement reconciliation pass + verifier scope fix)
- Summary:
  - Engagement reconciliation completed successfully with final verify `status=pass`.
  - Resolved cross-run `IS_RECOMMENDED metadata_mismatch` false blockers by changing verifier semantics to run-scoped evaluation.
  - Added transient Neo4j retry/backoff handling for long-running reconciliation batches.
- Changed files:
  - `PA/scripts/reconcile_legacy_delivery_from_unified.py`
  - `PA/scripts/reconcile_engagement_delivery_from_unified.py`
  - `readme.md`
  - `docs/post_event_followup_pack/README.md`
  - `docs/post_event_followup_pack/FOLLOWUP_CHANGELOG.md`
- Why changed:
  - Multi-run relationship layering caused verifier to inspect non-target run edges and report false metadata mismatches.
  - Long Neo4j verification loops needed resilience against transient `DatabaseUnavailable` interruptions.
- Validation/evidence:
  - Verify run command completed with status pass and report:
    - `PA/large_tool_results/reconcile_engagement_delivery_from_unified_verify_after_patch.json`
  - Final counters for `run_id=tsl_engagement_20260219T205354Z_c3f8fb55`:
    - `IS_RECOMMENDED: found=465479, missing=0, metadata_mismatch=0`
    - `IS_RECOMMENDED_EXHIBITOR: found=145930, missing=0, metadata_mismatch=0`
    - `CampaignDelivery: missing=0, duplicates=0, metadata_mismatch=0`
- Follow-up actions:
  - Keep current retry flags for future heavy reconciliation runs.
  - Use run-scoped verifier output as the go/no-go source for final pre-show and post-show handoff decisions.

---

## Template for future entries
## YYYY-MM-DD
- Summary:
- Changed files:
- Why changed:
- Validation/evidence:
- Follow-up actions:
