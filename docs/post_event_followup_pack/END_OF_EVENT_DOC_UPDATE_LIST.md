# End-of-Event Documentation Update List

Use this checklist after post-event data lands and final analysis is completed.

## A) Must update (final closure)

1) `docs/plan_b_implementation_milestones.md`
- Replace pre-event wording with final post-event outcomes.
- Update M6/M8 status from deferred/in-progress to completed (if complete).
- Add final run IDs, strict gate result, and final reconciliation/report evidence.

2) `docs/post_event_followup_pack/post_event_handoff_2026-02-21.md`
- Add closure note with actual execution date and final status.
- Mark open items as resolved (or carry forward explicitly).

3) `docs/post_event_followup_pack/post_event_day0_runsheet.md`
- Mark execution result and any command deltas observed in production.

4) `docs/post_event_followup_pack/FOLLOWUP_CHANGELOG.md`
- Add a dated final entry describing what changed and where the final artifacts are.

5) `docs/neo4j_database_map.svg`
- Refresh graph map to reflect final post-event state and validated relationships:
  - `assisted_session_this_year`
  - `registered_to_show`
  - run-scoped traceability entities/links used in final reporting

6) Snapshot refresh in `docs/post_event_followup_pack/reference_docs/`
- Refresh copied snapshots at least for:
  - `plan_b_implementation_milestones.md`
  - `post_analysis_mode.md` (if changed)
  - `application_overview.md` (if changed)

## B) Likely update (recommended)

1) `docs/post_analysis_mode.md`
- Ensure strict validation gate (`--require-post-event-data`) is documented.
- Include final operator sequence now that post-event run is proven.

2) `docs/application_overview.md`
- Update any mode/flow notes if final operational behavior differs from current narrative.

3) `docs/phase_d_execution_plan.md`
- Add final execution notes/results once Phase D is actually completed.

4) `docs/phase_d_execution_plan_full_traceability.md`
- Add final evidence references and any query/report deltas used at closure.

## C) Update only if materially changed

1) `docs/m5_delivery_reconciliation_runbook.md`
- Update only if reconciliation process/commands changed.

2) `docs/run_traceability_schema_contract.md`
- Update only if schema contract/constraints changed.

3) `docs/engagement_mode.md`
- Update only if engagement control/write-path behavior changed.

## D) Images reviewed (update decision)

- `docs/neo4j_database_map.svg` -> **Update at end** (high priority).
- `docs/vet_pipeline_map.svg` -> Update only if pipeline topology changed.
- `docs/generic_pipeline_map.svg` -> Update only if generic flow changed.
- `docs/azureml_pipeline_flow.svg` -> Update only if AzureML orchestration changed.
- `docs/ecomm_pipeline_complete.svg` -> Not needed for this TSL/Plan B closure unless cross-event flow changed.

## E) Final doc QA before closing follow-up

- Ensure all links in `docs/post_event_followup_pack/README.md` resolve.
- Ensure milestones and handoff docs reference final artifact paths in `large_tool_results/`.
- Confirm no pre-event placeholders remain in closure sections.
