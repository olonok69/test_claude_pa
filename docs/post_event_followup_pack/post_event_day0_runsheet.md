# Post-Event Day-0 Run Sheet

## Scope
Use this checklist on first day after event data lands.

## Copy/Paste kickoff block (post-show day 0)
Run from repo root:

```bash
cd /mnt/wolverine/home/samtukra/juan/repos/PA
source .venv/bin/activate
cd PA

# 1) Strict identity/data gate (must pass first)
python scripts/run_post_analysis_identity_validation.py \
	--config config/config_tsl.yaml \
	--require-post-event-data

# 2) Build post-analysis relationships
python main.py --config config/config_tsl.yaml --only-steps 2,3,5,8 --skip-mlflow

# 3) Optional output refresh (run only if immediate artifacts are needed)
# python main.py --config config/config_tsl.yaml --only-steps 11 --skip-mlflow

# 4) Re-validate engagement recommendation theatre rule (if engagement reran)
python scripts/analyze_tsl_recommendation_run.py --config config/config_tsl.yaml
```

Expected outcomes:
- Step 1 returns `STATUS: POST-EVENT READY` and writes `large_tool_results/identity_validation_<timestamp>.json`.
- Step 2 completes without blocking processor exceptions.
- Step 4 returns `STATUS: PASS` with `rows_violating_rule = 0`.
- Step 2 also projects run-scoped attendance relationships (`assisted_session_this_year_run`) for delivery-linked campaigns.

## Preconditions (must be true)
- Post-event seminar scans are available and paths are correct in `PA/config/config_tsl.yaml`.
- Entry scan exports are available and listed under `post_analysis_mode.entry_scan_files.entry_scans_this`.
- Neo4j credentials are available via configured env file.

## Step 1 — Strict identity/data gate
Run from `PA/`:
- `python scripts/run_post_analysis_identity_validation.py --config config/config_tsl.yaml --require-post-event-data`

Pass criteria:
- Exit code `0`
- Console shows `STATUS: POST-EVENT READY`
- Report exists in `large_tool_results/identity_validation_<timestamp>.json`
- `strict_post_event_errors` is empty

Stop criteria:
- Any non-zero exit, missing file error, or zero relationship totals in strict checks.

## Step 2 — Post-analysis relationship build
Run:
- `python main.py --config config/config_tsl.yaml --only-steps 2,3,5,8 --skip-mlflow`

Pass criteria:
- Command completes successfully.
- No blocking processor exceptions.

## Step 3 — Optional output refresh
Run only if output artifacts are required immediately:
- `python main.py --config config/config_tsl.yaml --only-steps 11 --skip-mlflow`

## Step 4 — Post-show reporting execution
Run post-show profile in reporting workflow using current post-analysis outputs.

Collect:
- Post-show report files
- Run IDs used for analysis joins
- Any unresolved warning/error notes

## Step 5 — Evidence bundle for closure
Store together:
- strict validation JSON,
- post-analysis logs,
- post-show report outputs,
- final milestone update note.

## Step 6 — Engagement recommendation rule validation
Run after any engagement recommendation generation/rerun:
- `python scripts/analyze_tsl_recommendation_run.py --config config/config_tsl.yaml`

Pass criteria:
- Console shows `STATUS: PASS`
- Generated report and log exist in `PA/large_tool_results/`:
	- `tsl_recommendation_run_analysis_<timestamp>.json`
	- `tsl_recommendation_run_analysis_<timestamp>.log`
- `rows_violating_rule = 0` in the JSON report.

Store these two artifacts in the closure evidence package.

## Step 7 — HubSpot suppression verify gate (if suppression import was executed)
Use this gate after any suppression import/update to confirm run-scoped integrity.

Run:
- `python scripts/verify_hubspot_suppression_in_neo4j.py --config config/config_tsl.yaml --neo4j-retry-attempts 8 --neo4j-retry-backoff-seconds 2`

Pass criteria:
- Command exits successfully (including transient retry recovery if needed).
- For each mapped run, `run_scoped_suppressed` equals `expected_matches_from_csv`.
- Global consistency check holds:
	- `suppressed_visitors = sum(run_scoped_suppressed across mapped runs)`

Optional logging:
- Re-run with shell capture for audit evidence:
	- `python scripts/verify_hubspot_suppression_in_neo4j.py --config config/config_tsl.yaml --neo4j-retry-attempts 8 --neo4j-retry-backoff-seconds 2 | tee logs/hubspot_suppression_verify_$(date +%Y%m%d_%H%M%S).log`

## Fast triage mapping
- `entry_scans_this` empty/missing -> fix config/file staging, rerun strict gate.
- `assisted_session_this_year` zero -> verify seminar scans loaded and post-analysis steps executed.
- `registered_to_show` zero -> verify entry scans staged and readable.

## Optional Neo4j check (run-scoped attendance)
Use this check after step 2 when campaign attribution analysis is required:

- `MATCH ()-[r:assisted_session_this_year_run]->() RETURN count(r) AS rels;`

Expected: `rels > 0` once post-analysis attendance exists and delivery-linked runs are present for the same visitors/show.

## Linked references
- `docs/post_event_handoff_2026-02-21.md`
- `docs/plan_b_implementation_milestones.md`
- `docs/post_analysis_mode.md`
- `docs/application_overview.md`
- `docs/m5_delivery_reconciliation_runbook.md`
