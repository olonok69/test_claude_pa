# Post-Event Follow-Up Pack

This folder centralizes the restart materials for reopening this topic later.

## Folder structure
- `post_event_handoff_2026-02-21.md` (restart context + gates)
- `post_event_day0_runsheet.md` (execution checklist)
- `pre_show_incremental_runbook_2026-02-26.md` (next pre-show incremental execution checklist)
- `pre_show_incremental_execution_handoff_2026-02-26.md` (post-run restart handoff + next-session verification steps)
- `reference_docs/` (snapshot copies of related plans/runbooks)
- `FOLLOWUP_CHANGELOG.md` (ongoing updates after closure)
- `AZUREML_PIPELINE_REFACTOR_PLAN.md` (mode-aligned Azure ML modernization plan)
- `DEEP_AGENTS_REPORTS_REFACTOR_PLAN.md` (post-show reporting alignment plan)

## Start here
1. `post_event_handoff_2026-02-21.md`
2. `post_event_day0_runsheet.md`
	- use section `Copy/Paste kickoff block (post-show day 0)` for fastest operator start.
3. `FOLLOWUP_CHANGELOG.md`
4. `END_OF_EVENT_DOC_UPDATE_LIST.md`
5. `AZUREML_PIPELINE_REFACTOR_PLAN.md`
6. `DEEP_AGENTS_REPORTS_REFACTOR_PLAN.md`
7. `POST_MERGE_SANITY_CHECKLIST.md`
8. `pre_show_incremental_runbook_2026-02-26.md`
9. `pre_show_incremental_execution_handoff_2026-02-26.md`

## Baseline recovery default path
- For “restore to baseline campaign state” (initial conversion + engagement only, excluding incremental simulation), use the manual restore track in `POST_MERGE_SANITY_CHECKLIST.md` section `7) New topic: recover baseline campaign state (manual restore)`.
- Treat Aura CLI / MCP automation as backlog until stabilized.

## Latest status (2026-02-25)
- Engagement-mode theatre mapping filter was validated on latest TSL recommendation run.
- Validation command:
	- `python scripts/analyze_tsl_recommendation_run.py --config config/config_tsl.yaml`
- Latest evidence artifacts:
	- `PA/large_tool_results/tsl_recommendation_run_analysis_20260225_074631.json`
	- `PA/large_tool_results/tsl_recommendation_run_analysis_20260225_074631.log`
- Historical decision context remains in `FOLLOWUP_CHANGELOG.md` under:
	- `2026-02-24 (pending approval: engagement theatre mapping filter)`
	- `2026-02-25 (engagement theatre filter validated on latest run)`

## Latest status (2026-02-26)
- Historical note: previous execution handoff exists in `pre_show_incremental_execution_handoff_2026-02-26.md`.
- Current cycle status: do **not** assume a new pre-show incremental `personal_agendas` run has started.

## Latest status (2026-02-27)
- Campaign/run traceability and lineage work advanced with evidence-driven verification/enforcement:
	- mode-aware campaign id alignment (`personal_agendas` => `tsl_conversion`, `engagement` => `tsl_engagement`),
	- run-scoped V2E import validation,
	- one-time relationship run-lineage verification/enforcement for mapped datasets,
	- progress-logged verifier runs and post-apply Neo4j audits.
- Current confirmed execution state:
	- **personal_agendas increment has not been started in this active cycle yet**.
- Recommended next action:
	- run the incremental pipeline only after final preflight checks, then capture new `RecommendationRun` + reconciliation evidence.

## Latest status (2026-03-02)
- Pre-show `personal_agendas` incremental cycle is now considered complete and closed for this event.
- Completed run lineage + delivery path for increment run:
	- `run_id=tsl_personal_agendas_20260227T224725Z_37b21c42`
	- run-scoped V2E import completed successfully (idempotent merge path verified).
- Completed pre-reconciliation unification artifacts for this run:
	- `data/tsl/recommendations/visitor_recommendations_tsl_20260227_224725_unified.json`
	- `data/tsl/recommendations/visitor_recommendations_tsl_20260227_224725_control_unified.json`
	- `data/tsl/recommendations/unify_recommendations_incidence_report_20260227_224725.json`
- Engagement reconciliation is currently running; dry-run behavior and blockers observed so far are consistent with expected pre-apply state.
- Operational decision before show:
	- no further `personal_agendas` pre-show execution planned.
	- next major execution focus moves to post-show analysis preparation using current schema + logic.

## Latest status (2026-03-03)
- Engagement reconciliation completed with final verify status `pass` after verifier scope alignment.
- Key validated outcomes for run `tsl_engagement_20260219T205354Z_c3f8fb55`:
	- `IS_RECOMMENDED: found=465479, missing=0, metadata_mismatch=0`
	- `IS_RECOMMENDED_EXHIBITOR: found=145930, missing=0, metadata_mismatch=0`
	- `CampaignDelivery: missing=0, duplicates=0, metadata_mismatch=0`
- Report artifact:
	- `PA/large_tool_results/reconcile_engagement_delivery_from_unified_verify_after_patch.json`
- Runtime hardening now active in reconciler:
	- transient Neo4j retry/backoff support (`--neo4j-retry-attempts`, `--neo4j-retry-backoff-seconds`)
	- run-scoped `IS_RECOMMENDED` verifier semantics to avoid cross-run mismatch noise.

## Next execution step (updated 2026-03-03)
- Archive engagement reconciliation evidence bundle and keep reconciler defaults for future long runs.
- Hold pre-show execution scope stable (no further incremental `personal_agendas` runs planned).
- After show closes, execute post-analysis kickoff using the active run-traceability schema and updated reconciliation logic.

## Curated references (snapshot copy -> source original)
- `reference_docs/plan_b_implementation_milestones.md` -> `../plan_b_implementation_milestones.md`
- `reference_docs/m2_traceability_migration_runbook.md` -> `../m2_traceability_migration_runbook.md`
- `reference_docs/m5_delivery_reconciliation_runbook.md` -> `../m5_delivery_reconciliation_runbook.md`
- `reference_docs/post_analysis_mode.md` -> `../post_analysis_mode.md`
- `reference_docs/application_overview.md` -> `../application_overview.md`
- `reference_docs/engagement_mode.md` -> `../engagement_mode.md`
- `reference_docs/run_traceability_schema_contract.md` -> `../run_traceability_schema_contract.md`
- `reference_docs/phase_d_execution_plan_full_traceability.md` -> `../phase_d_execution_plan_full_traceability.md`

## Consistency rule
- Treat files in `reference_docs/` as restart snapshots for quick navigation.
- When making new edits after resuming, edit source originals under `docs/` first.
- Optionally refresh snapshots after major updates.

## Operational scripts and config
- `../../PA/scripts/run_post_analysis_identity_validation.py`
- `../../PA/scripts/analyze_tsl_recommendation_run.py`
- `../../PA/config/config_tsl.yaml`

## Recommended resume sequence (1 month later)
1. Read `post_event_handoff_2026-02-21.md`.
2. Execute `post_event_day0_runsheet.md`.
3. Use `--require-post-event-data` strict validation gate.
4. Complete post-analysis + reporting and archive evidence.
