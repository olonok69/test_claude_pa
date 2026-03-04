# Post-Event Handoff Pack (Prepared 2026-02-21)

## Purpose
This document is the restart package for resuming Plan B and post-event analysis after a pause.

Primary outcome expected when resuming:
- run strict post-event identity validation,
- complete post-analysis pipeline,
- execute post-show reporting,
- close M6/M8 evidence with final run artifacts.

---

## Current state at handoff (2026-02-21)
- Pre-event operations are complete and stable.
- Identity continuity patch is implemented (identity-first matching with badge fallback for post-analysis joins).
- Validation script is hardened and warning-free in pre-event state.
- Strict gate is available via `--require-post-event-data`.
- Current expected pre-event informational result is either `STATUS: PRE-EVENT OK` or `STATUS: POST-EVENT READY` depending on data state, with no blocking strict errors.

Key files already updated:
- `PA/scripts/run_post_analysis_identity_validation.py`
- `PA/config/config_tsl.yaml`
- `docs/plan_b_implementation_milestones.md`
- `docs/post_event_followup_pack/post_event_day0_runsheet.md`

## Latest update after handoff (2026-02-25)
- Added run-level recommendation analyzer:
  - `PA/scripts/analyze_tsl_recommendation_run.py`
- Executed validation on latest engagement recommendations output:
  - `STATUS: PASS`
  - `rows_total=253560`
  - `rows_violating_rule=0`
- Evidence artifacts:
  - `PA/large_tool_results/tsl_recommendation_run_analysis_20260225_074631.json`
  - `PA/large_tool_results/tsl_recommendation_run_analysis_20260225_074631.log`

---

## Read-first document pack (for restart in ~1 month)
Read in this order:

1. `docs/post_event_handoff_2026-02-21.md`
  - Full restart context, gates, and evidence expectations.
2. `docs/post_event_followup_pack/post_event_day0_runsheet.md`
  - Single-page execution checklist for first post-event run day.
3. `docs/post_event_followup_pack/reference_docs/plan_b_implementation_milestones.md`
  - Program-level status, sequencing, and go/no-go logic.
4. `docs/post_event_followup_pack/reference_docs/post_analysis_mode.md`
  - Post-analysis processing behavior and data flow assumptions.
5. `docs/post_event_followup_pack/reference_docs/application_overview.md`
  - End-to-end architecture and processor responsibilities.
6. `docs/post_event_followup_pack/reference_docs/m5_delivery_reconciliation_runbook.md`
  - Reconciliation standards and validation posture.
7. `docs/post_event_followup_pack/reference_docs/engagement_mode.md`
  - Context for campaign-side behavior that precedes post-analysis.

---

## Required inputs before post-event run
Do not run strict post-event gate until these are available.

1) Post-event seminar scans
- Config key: `post_analysis_mode.scan_files.seminars_scans_this`
- File must exist and be readable.

2) Entry scans
- Config key: `post_analysis_mode.entry_scan_files.entry_scans_this`
- Must contain one or more file paths (not empty list).
- Every listed file must exist and be readable.

3) Optional but recommended seminar reference
- Config key: `post_analysis_mode.scan_files.seminars_scan_reference_this`
- If absent, scans-only enrichment still runs.

---

## One-month restart checklist

### A) Data staging and config update
1. Copy final post-event exports into expected data directory.
2. Update `PA/config/config_tsl.yaml`:
   - keep `post_analysis_mode.scan_files.seminars_scans_this` correct,
   - set `post_analysis_mode.entry_scan_files.entry_scans_this` to actual file path(s),
   - verify path spelling and casing.
3. Confirm environment and secrets are loaded for Neo4j.

### B) Hard gate validation (must pass)
Run:
- `python scripts/run_post_analysis_identity_validation.py --config config/config_tsl.yaml --require-post-event-data`

Expected:
- Exit code 0.
- Console includes `STATUS: POST-EVENT READY`.
- JSON report written in `PA/large_tool_results/identity_validation_<timestamp>.json`.
- `strict_post_event_errors` is empty.
- Non-zero relationship totals for both:
  - `assisted_session_this_year`
  - `registered_to_show`

If it fails:
- Fix missing files/config paths first.
- Re-run the same command until strict checks pass.

### C) Post-analysis pipeline execution
After strict gate passes, run post-analysis flow according to plan sequence.

Minimum operational run:
- `python main.py --config config/config_tsl.yaml --only-steps 2,3,5,8 --skip-mlflow`

Optional output refresh:
- `python main.py --config config/config_tsl.yaml --only-steps 11 --skip-mlflow`

### D) Post-show reporting
Execute `deep_agents_reports` post-show profile using the post-analysis outputs.

Required references:
- pre-show report path,
- scan data date,
- current run identifiers from post-analysis.

### E) Closure evidence package
Archive these artifacts for final sign-off:
- strict validation JSON report,
- post-analysis run logs,
- post-show report outputs,
- recommendation rule validation JSON/log from `analyze_tsl_recommendation_run.py`,
- final milestone note with run IDs and timestamps.

---

## Go / No-Go gates

### Gate 1: Data readiness
GO only if post-event seminars and entry scans are both present and configured.

### Gate 2: Strict identity validation
GO only if strict gate returns `STATUS: POST-EVENT READY`.

### Gate 3: Post-analysis completion
GO only if steps 2/3/5/8 complete without blocking errors.

### Gate 4: Reporting completion
GO only if post-show report generation succeeds with expected artifacts.

---

## Known expected behaviors
- Pre-event run (without strict flag) can legitimately show:
  - `STATUS: PRE-EVENT OK` or `STATUS: POST-EVENT READY`,
  - `none found` for post-event relationship match modes.
- This is not a defect before post-event files are staged.

## Baseline recovery default path (manual)
- If switching topics to recover baseline campaign state (initial conversion + engagement only, excluding incremental simulation), use manual restore via Aura Console.
- Follow `docs/post_event_followup_pack/POST_MERGE_SANITY_CHECKLIST.md` section `7) New topic: recover baseline campaign state (manual restore)`.
- Aura CLI / MCP automation remains backlog until stable.

---

## Operator quick commands
From `PA/`:

- Pre-event informational check:
  - `python scripts/run_post_analysis_identity_validation.py --config config/config_tsl.yaml`

- Post-event hard gate:
  - `python scripts/run_post_analysis_identity_validation.py --config config/config_tsl.yaml --require-post-event-data`

- Post-analysis step batch:
  - `python main.py --config config/config_tsl.yaml --only-steps 2,3,5,8 --skip-mlflow`

- Optional output step:
  - `python main.py --config config/config_tsl.yaml --only-steps 11 --skip-mlflow`

- Recommendation rule validation:
  - `python scripts/analyze_tsl_recommendation_run.py --config config/config_tsl.yaml`

---

## Open items to verify at resume time
- Exact final entry scan export filenames and arrival location.
- Whether reporting requires additional post-show prompt/template tuning after first run.
- Final M6/M8 evidence capture format for closure report.
