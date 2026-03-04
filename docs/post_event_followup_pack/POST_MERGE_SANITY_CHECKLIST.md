# Post-Merge and Topic-Switch Checklist

Use this lightweight checklist immediately after merging to `main`.
Then continue with the recovery topic for restoring the baseline campaign state.

## 1) Repository state
- Confirm you are on `main` and up to date.
- Confirm no unintended local modifications are pending.

Suggested commands:
- `git branch --show-current`
- `git pull --ff-only`
- `git status`

## 2) Critical config sanity
- Open `PA/config/config_tsl.yaml` and verify:
  - `mode` is expected for next operation,
  - `post_analysis_mode.entry_scan_files.entry_scans_this` reflects current phase (empty pre-event is acceptable),
  - Neo4j environment target is intentional.

## 3) Script-level smoke check
- Run strict syntax/error check on the current key validator script in editor problems pane.
- Optional CLI smoke check (pre-event expected):
  - `python scripts/run_post_analysis_identity_validation.py --config config/config_tsl.yaml`
- Confirm expected output pattern for current phase:
  - `STATUS: PRE-EVENT OK` or `STATUS: POST-EVENT READY`, with no blocking warnings/errors.

## 4) Artifact path sanity
- Confirm output folders exist and are writable:
  - `PA/large_tool_results/`
  - `deep_agents_reports/outputs/`
  - `deep_agents_reports/reports/artifacts/`

Suggested command:
- `ls -la PA/large_tool_results deep_agents_reports/outputs deep_agents_reports/reports/artifacts`

## 5) Follow-up pack integrity
- Open and quickly verify these docs are present and linked:
  - `docs/post_event_followup_pack/README.md`
  - `docs/post_event_followup_pack/post_event_handoff_2026-02-21.md`
  - `docs/post_event_followup_pack/post_event_day0_runsheet.md`
  - `docs/post_event_followup_pack/END_OF_EVENT_DOC_UPDATE_LIST.md`
  - `docs/post_event_followup_pack/AZUREML_PIPELINE_REFACTOR_PLAN.md`
  - `docs/post_event_followup_pack/DEEP_AGENTS_REPORTS_REFACTOR_PLAN.md`

## 6) Optional quick graph sanity (if Neo4j access available)
- Verify database connectivity before deeper runs.
- If in pre-event state, absence of post-event relationships is expected.

## 7) New topic: recover baseline campaign state (manual restore)
Goal: return to the baseline state with 1 initial conversion campaign + 1 engagement campaign, excluding the incremental conversion simulation.

Scope note:
- Restore is performed manually by operator.
- Aura CLI / MCP automation is deferred (tracked as future work).

### 7.1 Preconditions
- Confirm target Neo4j environment (`prod`/`test`/`dev`) and maintenance window.
- Confirm the desired restore point: snapshot taken after engagement completion and before incremental simulation writes.
- Capture a short change note before restore (who/when/why).

### 7.2 Find candidate snapshots (manual)
- In Aura Console, open backups/snapshots for the target instance.
- Pick a snapshot timestamp taken after engagement completion and before incremental simulation writes.
- Record selected snapshot id + timestamp in an ops note.

### 7.3 Restore selected snapshot (manual)
- Execute restore from Aura Console using the selected snapshot id.
- Wait until instance status is healthy/online.
- Do not run campaign write pipelines during restore window.

### 7.3a If restored snapshot uses legacy visitor labels (`Visitor_last_year_bva/lva`)
- Run relabel Cypher in Aura Console before any pipeline write:
  - `MATCH (n:Visitor_last_year_bva) SET n:Visitor_last_year_main REMOVE n:Visitor_last_year_bva;`
  - `MATCH (n:Visitor_last_year_lva) SET n:Visitor_last_year_secondary REMOVE n:Visitor_last_year_lva;`
- Verify relabel outcome:
  - `MATCH (n:Visitor_last_year_main) RETURN count(n) AS new_main;`
  - `MATCH (n:Visitor_last_year_secondary) RETURN count(n) AS new_secondary;`
  - `MATCH (n:Visitor_last_year_bva) RETURN count(n) AS old_main_remaining;`
  - `MATCH (n:Visitor_last_year_lva) RETURN count(n) AS old_secondary_remaining;`
- Proceed only when `old_main_remaining = 0` and `old_secondary_remaining = 0`.

### 7.4 Post-restore validation
- Re-run:
  - `python PA/scripts/run_post_analysis_identity_validation.py --config PA/config/config_tsl.yaml --skip-pipeline`
- Confirm run-scoped records reflect only initial conversion + engagement timeline for the chosen baseline window.
- Keep a short restore log in `PA/large_tool_results/` with selected snapshot id, timestamp, and reason.

### 7.5 Future automation (backlog)
- Revisit Aura CLI or MCP-based backup/restore automation once stable.
- Keep this checklist as the source of truth until automation is production-ready.

## 8) Post-rename go/no-go (Visitor last-year labels)
Use this after renaming labels from `Visitor_last_year_bva/lva` to `Visitor_last_year_main/secondary`.

### 8.1 Neo4j label integrity
- In Aura Console, run:
  - `MATCH (n:Visitor_last_year_main) RETURN count(n) AS new_main;`
  - `MATCH (n:Visitor_last_year_secondary) RETURN count(n) AS new_secondary;`
  - `MATCH (n:Visitor_last_year_bva) RETURN count(n) AS old_main_remaining;`
  - `MATCH (n:Visitor_last_year_lva) RETURN count(n) AS old_secondary_remaining;`
- GO if:
  - `new_main > 0` and `new_secondary > 0` (for events where both cohorts exist),
  - `old_main_remaining = 0` and `old_secondary_remaining = 0`.

### 8.2 Relationship continuity
- In Aura Console, run:
  - `MATCH (:Visitor_this_year)-[r:Same_Visitor]->(:Visitor_last_year_main) RETURN count(r) AS same_main;`
  - `MATCH (:Visitor_this_year)-[r:Same_Visitor]->(:Visitor_last_year_secondary) RETURN count(r) AS same_secondary;`
  - `MATCH (:Visitor_last_year_main)-[r:attended_session]->(:Sessions_past_year) RETURN count(r) AS attended_main;`
  - `MATCH (:Visitor_last_year_secondary)-[r:attended_session]->(:Sessions_past_year) RETURN count(r) AS attended_secondary;`
- GO if counts are non-zero where expected and not materially lower than pre-rename baseline.

### 8.3 Runtime smoke (no write-heavy campaign run)
- Run one lightweight check:
  - `python scripts/import_v2e_recommendations_to_neo4j.py --config config/config_tsl.yaml --v2e-json data/tsl/v2e_recommendations_3.json --dry-run`
- Optional validator check:
  - `python scripts/run_post_analysis_identity_validation.py --config config/config_tsl.yaml --skip-pipeline`
- GO if commands complete successfully without label-not-found errors.

## Done criteria
- `main` is clean and up to date.
- No unexpected config drift.
- Validation script behaves as expected for current event phase.
- Follow-up pack is complete and ready for next topic.
- Recovery path is documented and ready to execute once snapshot id is selected.
- Label-rename go/no-go checks pass before next campaign write.
