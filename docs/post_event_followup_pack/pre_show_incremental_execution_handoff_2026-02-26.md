# Pre-Show Incremental Execution Handoff — 2026-02-26

> Status update (2026-03-02): This handoff is now in **closed/completed** state for pre-show execution.
> No additional `personal_agendas` incremental run is planned before show opening.

## Purpose

Capture the minimum restart context after the completed incremental `personal_agendas` pipeline run so work can resume in a new session without repeating heavy checks.

## Run status (reported by operator)

- Pipeline run completed successfully.
- Completion timestamp (summary): `2026-02-26T17:04:14.368378`
- Processors executed:
  - `reg_processor`
  - `scan_processor`
  - `session_processor`
  - `neo4j_visitor_processor`
  - `neo4j_session_processor`
  - `neo4j_job_stream_processor`
  - `neo4j_specialization_stream_processor`
  - `neo4j_visitor_relationship_processor`
  - `session_embedding_processor`
  - `session_recommendation_processor`
  - `output_processor`

Summary highlights from console:
- Visitors processed: `7779`
- Visitors with successful recommendations: `7779`
- Total recommendations generated: `77763`
- Unique sessions recommended: `245`
- Detailed summary artifact: `logs/processing_summary.json`

## Config/input state used

- Active config file: `PA/config/config_tsl.yaml`
- Mode: `personal_agendas`
- Incremental flag: `create_only_new: true`
- Data format pathing: `old_format: true`
- Input files point to latest transformed legacy sets:
  - `data/tsl/20260226_tsl25_26_registration_legacy.json`
  - `data/tsl/20260226_tsl25_26_demographics_legacy.json`
  - `data/tsl/20260226_tsl24_registration_legacy.json`
  - `data/tsl/20260226_tsl24_demographics_legacy.json`

## What is already aligned with the follow-up pack

- Pre-show runbook exists and was the intended execution path:
  - `docs/post_event_followup_pack/pre_show_incremental_runbook_2026-02-26.md`
- Traceability model is already present in DB from prior steps:
  - `RecommendationRun`
  - `CampaignDelivery`
  - run-scoped recommendation metadata fields
- V2E run-scoped import docs and evidence remain available for optional continuation.

## Pending verification to run first in next session (priority order)

1) Determine the exact new recommendation output file pair (main/control) from this run:
- `PA/data/tsl/recommendations/visitor_recommendations_tsl_<timestamp>.json`
- `PA/data/tsl/recommendations/control/visitor_recommendations_tsl_<timestamp>_control.json`

2) Run M5 reconciliation using those exact files:

```bash
python PA/scripts/reconcile_campaign_delivery.py \
  --config PA/config/config_tsl.yaml \
  --env-file PA/keys/.env \
  --main-json PA/data/tsl/recommendations/visitor_recommendations_tsl_<timestamp>.json \
  --control-json PA/data/tsl/recommendations/control/visitor_recommendations_tsl_<timestamp>_control.json \
  --campaign-id tsl_conversion \
  --report-file PA/large_tool_results/m5_delivery_reconciliation_incremental_<timestamp>.json \
  --fail-on-mismatch
```

GO/NO-GO gate:
- GO only if `mismatch_total=0` and reconciliation exits successfully.
- For this `personal_agendas` run, expected `campaign_id` is `tsl_conversion`.

3) Validate Neo4j run objects for this exact run_id:
- new `RecommendationRun` exists for `show='tsl'`, `run_mode='personal_agendas'`
- `CampaignDelivery` rows exist for the same `run_id`
- `IS_RECOMMENDED` relationships for that `run_id` are populated

## Suggested minimal resume script (copy/paste block)

```bash
cd /mnt/wolverine/home/samtukra/juan/repos/PA
source .venv/bin/activate

# 1) Inspect latest recommendation outputs
ls -lt PA/data/tsl/recommendations/visitor_recommendations_tsl_*.json | head -n 3
ls -lt PA/data/tsl/recommendations/control/visitor_recommendations_tsl_*_control.json | head -n 3

# 2) Reconcile (replace <timestamp>)
python PA/scripts/reconcile_campaign_delivery.py \
  --config PA/config/config_tsl.yaml \
  --env-file PA/keys/.env \
  --main-json PA/data/tsl/recommendations/visitor_recommendations_tsl_<timestamp>.json \
  --control-json PA/data/tsl/recommendations/control/visitor_recommendations_tsl_<timestamp>_control.json \
  --campaign-id tsl_conversion \
  --report-file PA/large_tool_results/m5_delivery_reconciliation_incremental_<timestamp>.json \
  --fail-on-mismatch
```

## Notes for next operator

- Keep execution conservative (small, targeted checks first) due prior session instability.
- Avoid re-running incremental `personal_agendas` pipeline before show unless a critical rollback/fix is required.
- Archive the reconciliation JSON path and resolved `run_id` in this pack once verified.

## Closure note (2026-03-02)

- Increment run path finalized with run-scoped reconciliation and V2E unification artifacts.
- Unified outputs now exist for timestamp `20260227_224725` (main + control + incidence).
- Remaining active execution before documentation freeze is engagement reconciliation completion.
- After show, resume from post-analysis track using current traceability schema and updated reconciliation logic.
