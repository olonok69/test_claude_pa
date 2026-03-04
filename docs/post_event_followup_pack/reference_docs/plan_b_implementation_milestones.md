# Plan B Implementation Milestones (Full Traceability)

## Goal
Implement full cross-campaign traceability in Neo4j so personal agendas and engagement runs can be analyzed together in Phase D with clear provenance.

## Conversation closure handoff (2026-02-21)
- Resume pack for next PR window: `docs/post_event_followup_pack/post_event_handoff_2026-02-21.md`
- This is the authoritative restart checklist for post-event activation after pause.

## Milestones

### M1 — Target Schema Contract (freeze)
**Objective:** Define and lock the traceability schema before any migration.

**Deliverables**
- Canonical field set for run/campaign provenance.
- Entity model for recommendation events and delivery events.
- Uniqueness rules and required constraints/indexes.
- Backward-compatibility defaults for legacy records.
- Acceptance criteria + QA checks.

**Output artifacts**
- `docs/run_traceability_schema_contract.md`

---

### M2 — One-time Neo4j migration/backfill
**Objective:** Convert current graph to target schema with idempotent migration scripts.

**Deliverables**
- Migration Cypher scripts.
- Backfill mapping rules for legacy records.
- Verification script/report (counts before/after).
- Rollback strategy.

**Implementation artifacts (current branch)**
- `PA/scripts/migrate_traceability_m2.py`
- `PA/scripts/cypher/m2_traceability_verification.cypher`
- `docs/m2_traceability_migration_runbook.md`

**Execution snapshot (2026-02-19)**
- Dry-run completed successfully.
- Apply completed successfully with report at `large_tool_results/m2_traceability_migration_report.json`.
- Backfill results:
	- `relationships_backfilled = 166489`
	- `delivery_nodes_upserted = 16656`
- Post-migration checks in report:
	- `missing_run_id = 0`
	- `missing_run_mode = 0`
	- `missing_campaign_id = 0`
	- `legacy_visitors_without_delivery = 0`
	- `legacy_run_nodes = 1`

---

### M3 — Personal agendas write-path upgrade
**Objective:** Populate target traceability fields for PA recommendations and control assignment.

**Deliverables**
- Run-scoped recommendation writes (no lineage loss).
- Delivery/control metadata persisted with `run_id`.
- Regression tests for existing PA outputs.

**Status update**
- Writer updated to append run-scoped `IS_RECOMMENDED` relationships keyed by `run_id` (no cross-run overwrite).
- Cleanup now deletes only relationships for the same `run_id` (safe reruns, preserved history).
- `RecommendationRun` + `CampaignDelivery` upserts added to write path for ongoing runs.
- Control assignment continuity now reads run-scoped history (`CampaignDelivery`/`IS_RECOMMENDED`) instead of mutable visitor node control flags.
- Legacy visitor-node control sync is now optional compatibility mode (`legacy_node_flag_sync`) and disabled by default.

---

### M4 — Engagement write-path upgrade
**Objective:** Populate the same traceability fields for engagement runs.

**Deliverables**
- Engagement run-scoped writes.
- Optional engagement-control metadata hooks (if enabled later).
- Regression tests for engagement outputs.

**Status update**
- Engagement mode now uses the same run-scoped traceability writes (`run_id`, `campaign_id`, `run_mode`, `CampaignDelivery`) as personal agendas.
- Control-group execution is now configurable by mode via `recommendation.control_group.enabled_modes`.
- TSL config enables control for both `personal_agendas` and `engagement`.
- Legacy mutable visitor control flag syncing remains disabled by default (`legacy_node_flag_sync: false`) to preserve run-scoped control history.

**Dry-run validation (2026-02-19)**
- Read-only M4 checker executed via `PA/scripts/dry_run_m4_engagement_control.py`.
- Report: `large_tool_results/m4_engagement_control_dry_run_report.json`.
- Engagement control split validated on current cohort:
	- `visitors_to_process = 16656`
	- `control_assigned_in_run_scope = 2498`
	- `treatment_assigned_in_run_scope = 14158`

---

### M5 — Exposure/delivery ledger
**Objective:** Track who was targeted/sent/withheld per campaign run.

**Deliverables**
- Delivery ledger model and writes.
- File-to-Neo4j reconciliation checks.

**Status update**
- Delivery ledger writes are active in output processing (`CampaignDelivery` + `FOR_VISITOR` + `FOR_RUN`).
- Reconciliation utility implemented: `PA/scripts/reconcile_campaign_delivery.py`.
- DB verification pack implemented: `PA/scripts/cypher/m5_delivery_reconciliation_checks.cypher`.
- Operational runbook added: `docs/m5_delivery_reconciliation_runbook.md`.
- One-time legacy correction utility added: `PA/scripts/fix_legacy_campaign_delivery_status.py`.
- One-time engagement reconciliation utility added: `PA/scripts/reconcile_one_time_delivery_run.py` (CSV-to-ledger parity with Neo4j connectivity check + run-id auto-resolution).
- Legacy status correction executed (2026-02-19): `withheld_control` updated from `0` to `2496` for `run_id=legacy_pre_traceability`.
- Full initial conversion reconciliation now passes with `mismatch_total=0` (report: `large_tool_results/m5_initial_conversion_full_reconciled_report_after_fix.json`).

**Engagement execution snapshot (2026-02-20)**
- Completed staged execution for steps 4–11 using engagement mode.
- Authoritative run log: `PA/logs/engagement_steps_4_11_20260219_162932.log`.
- Output artifacts generated for run timestamp `20260219_205354`:
	- `PA/data/tsl/recommendations/visitor_recommendations_tsl_20260219_205354.csv`
	- `PA/data/tsl/recommendations/visitor_recommendations_tsl_20260219_205354.json`
	- `PA/data/tsl/recommendations/control/visitor_recommendations_tsl_20260219_205354_control.csv`
	- `PA/data/tsl/recommendations/control/visitor_recommendations_tsl_20260219_205354_control.json`
- Log summary metrics:
	- `Total visitors processed = 46555`
	- `Total recommendations generated = 465479`
	- Control target selection: `eligible=46555`, `target=6983`, `selected=6983`.
- One-time reconciliation executed against Neo4j from VM console:
	- Command input run token: `20260219_205354`
	- Resolved run id: `tsl_engagement_20260219T205354Z_c3f8fb55`
	- Report: `PA/large_tool_results/one_time_delivery_reconciliation_20260219_205354_vm.json`
	- Result: `ok=true`, `mismatch_total=0`, `delivery_nodes_for_run=46555`, `status_counts={sent:39572, withheld_control:6983}`.
- Decision from reconciliation: **no rerun required**.

**Incremental conversion execution snapshot (2026-02-20)**
- New input transforms completed for registration/demographic and sessions feeds (TSL 2025/2026 update set).
- Incremental run completed successfully through steps 1–11 in `personal_agendas` mode with `create_only_new: true`.
- Reconciliation completed for run token `20260220_151828` after script hardening:
	- Resolved run id: `tsl_personal_agendas_20260220T151828Z_72918232`
	- Report parity result: `mismatch_total=0`
	- Delivery/recommendation integrity checks: pass.

**Operational status (pre-show)**
- Cross-campaign traceability is now active and validated for:
	1. initial conversion (legacy backfilled),
	2. engagement,
	3. incremental conversion.
- Current focus is execution readiness and reconciliation discipline during live event operations.

## Campaign timeline mapping for TSL (agreed target)
1. **Initial conversion campaign** (already in DB): preserved as legacy run (`legacy_pre_traceability`) from M2 backfill.
2. **Engagement campaign** (next week): new run writes with its own `run_id`; control/treatment captured via run-scoped metadata.
3. **Incremental conversion campaign** (2 weeks before show): new run writes for incremental registrants; global control scope remains at full eligible population.

This sequence guarantees that post-analysis can compare outcomes across all three phases without overwriting initial conversion records.

---

### M6 — Phase D query layer
**Objective:** Build run-scoped analytical views for causal/descriptive reporting.

**Deliverables**
- Run ledger query.
- Visitor exposure timeline query.
- Outcome join query (attendance vs recommendation).

**Status update (2026-02-20)**
- Deferred to post-show execution window (after scan ingestion in `post_analysis_mode`).
- Preparation completed in `deep_agents_reports` so post-show runs are operationally ready:
	- pre/post final report filename/path consistency fixed across manifest/generator/pipeline runner,
	- post-show placeholders completed (`PRE_SHOW_REPORT_DATE`, `SCAN_DATA_DATE`),
	- direct workflow CLI supports post-show args (`--report-type post_show`, `--pre-show-report ...`).
- Decision: do not spend more cycles on post-show report generation now; trigger after show data lands.

**Identity continuity hardening (new, in progress)**
- Problem being addressed: post-analysis attendance joins were badge-based; if badge IDs changed between campaign and event scans, outcome attribution could be undercounted.
- Patch implemented:
	- registration combined outputs now persist canonical identity fields (`Forename`, `Surname`, `id_both_years`) so Neo4j `Visitor_*` nodes carry identity keys,
	- post-analysis relationship writers now try badge match first, then fallback to `id_both_years` identity match,
	- relationship properties now record matching mode (`badge` vs `identity_fallback`) for auditability.
- Expected impact: improved attribution continuity across campaign and post-analysis when badge re-issuance occurs.
- Remaining validation tasks:
	1. run post-analysis dry run and capture match-mode counts,
	2. compare unresolved scan rows before/after patch,
	3. confirm reporting queries include/acknowledge identity-fallback matched outcomes.

---

### M7 — QA & reconciliation automation
**Objective:** Automate hard checks so every run is auditable.

**Deliverables**
- Duplicate/provenance/integrity checks.
- Control split checks.
- Join-rate and drift alerts.

---

### M8 — Sequence UAT
**Objective:** Validate full lifecycle: PA full -> Engagement -> PA incremental -> Post-analysis.

**Deliverables**
- End-to-end UAT report with pass/fail per phase.

---

### M9 — Production runbook + handoff
**Objective:** Operationalize with clear ownership and rollback.

**Deliverables**
- Runbook, on-call checklist, rollback drill notes.

## Operator preference (agreed)
- For heavy/long-running commands and Neo4j checks, execute scripts from VM console first and share log/report output here for validation.
- Copilot support mode: prepare command lines, generate scripts, and validate results from posted logs/artifacts.

## Event operations checklist (live run)

### 1) Engagement campaign run
- Execute pipeline in engagement mode using staged steps (VM console first).
- Capture evidence:
	- run log path,
	- generated treatment/control files (CSV + JSON),
	- reconciliation report JSON.
- Go/No-Go rule:
	- **GO** if reconciliation returns `mismatch_total=0` and status counts align with files,
	- **NO-GO** if mismatch/integrity checks fail (stop and remediate before next run).

### 2) Incremental conversion campaign run
- Execute incremental run in `personal_agendas` mode with `create_only_new: true`.
- Capture evidence:
	- run log path,
	- generated treatment/control files (CSV + JSON),
	- reconciliation report JSON with resolved run id.
- Go/No-Go rule:
	- **GO** if reconciliation returns `mismatch_total=0` and run-scoped parity checks pass,
	- **NO-GO** if any file-vs-ledger mismatch or missing provenance links is detected.

### 3) Post-show (after event closes)
- Switch to `post_analysis_mode` and run post-analysis pipeline once scan ingestion is complete.
- Then execute `deep_agents_reports` post-show profile for final analytical reporting.
- Capture evidence:
	- post-analysis run log,
	- post-show report outputs,
	- final validation notes referencing run ids used in analysis.
- Go/No-Go rule:
	- **GO** to handoff only when post-analysis completes and report artifacts are generated without blocking errors.

### 4) Identity validation gate (pre-event vs post-event)
- Script: `python scripts/run_post_analysis_identity_validation.py --config config/config_tsl.yaml`
- Pre-event expected output:
	- `STATUS: PRE-EVENT OK`,
	- no Neo4j warnings,
	- possible `none found` for `assisted_session_this_year` and `registered_to_show` while scans are not landed.
- Post-event strict gate command:
	- `python scripts/run_post_analysis_identity_validation.py --config config/config_tsl.yaml --require-post-event-data`
- Strict mode behavior:
	- exits non-zero if `seminars_scans_this` is unavailable,
	- exits non-zero if `entry_scans_this` is empty or files are missing,
	- exits non-zero if either `assisted_session_this_year` or `registered_to_show` has zero relationships,
	- writes details in `large_tool_results/identity_validation_<timestamp>.json` under `strict_post_event_errors`.

## Suggested order now
1. Continue event-time campaign operations using the validated run-scoped write paths and reconciliation checks (engagement + incremental cadence as scheduled).
2. Keep **M7** reconciliation gate active after each campaign write and retain VM-console-first evidence capture.
3. During pre-event checks, run identity validation in standard mode and expect `STATUS: PRE-EVENT OK` if post-event scans are not yet available.
4. After the show, ingest scans and run identity validation with `--require-post-event-data` as the hard gate.
5. Then run pipeline in `post_analysis_mode`, followed by `deep_agents_reports` post-show reporting profile(s).
6. Execute **M6** and **M8** together in the post-show window using real attendance outcomes (final causal/descriptive reporting + full-lifecycle UAT).
