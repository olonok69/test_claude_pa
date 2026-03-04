# Deep Agents Reports Refactor Plan (Post-Event Alignment)

Prepared: 2026-02-21

## 1) Purpose
Align `deep_agents_reports` with the latest pipeline contracts so post-show reporting is:
- run-scoped (traceable to campaign runs),
- identity-aware (badge churn resilient),
- gated by strict post-event readiness checks,
- reproducible across resume windows.

---

## 2) Current-state findings

### What is already good
- Pre-show and post-show modes are both supported in workflow and pipeline runner.
- Report output segregation (`pre_show` vs `post_show`) is in place.
- Post-show context placeholders (`PRE_SHOW_REPORT_DATE`, `SCAN_DATA_DATE`, pre-show report path) are supported.
- Artifact persistence and recovery model are strong (`reports/artifacts`, `memory/`, `outputs/...`).

### Gaps to close
1. Prompt/query layer is still mostly relationship-centric (`IS_RECOMMENDED`) and not run-scoped by default.
2. Reporting does not enforce strict post-event data readiness before launching heavy post-show generation.
3. No canonical post-show profile pattern tied to strict gate evidence (`identity_validation_*.json`).
4. Prompt packs do not explicitly require identity match quality breakdown (`identity_match_mode`).
5. Runbook-level output contract (what must be attached for final closure) is implicit rather than enforced.

---

## 3) Refactor goals
1. Make post-show analytics explicitly run-scoped (`run_id`, `campaign_id`, `run_mode`) when data exists.
2. Require strict post-event gate pass before post-show profile execution.
3. Add identity attribution quality section as first-class output in post-show reports.
4. Standardize profile templates and artifact naming for deterministic reruns.
5. Keep backward compatibility for legacy datasets where run-scoped entities may be incomplete.

---

## 4) Target design

## 4.1 Reporting entry contract
For post-show runs, require these inputs in profile (or CLI overrides):
- `report_type: post_show`
- `pre_show_report`
- `strict_validation_report` (path to `large_tool_results/identity_validation_*.json`)
- optional `target_run_id` / `target_campaign_id`

## 4.2 Query strategy hierarchy
In post-show prompts/manifests, use this priority:
1. Run-scoped query path (prefer `run_id` where available)
2. Campaign-scoped fallback (`campaign_id`, `run_mode`)
3. Legacy fallback (relationship-level only), with explicit warning in report

## 4.3 Identity quality block (mandatory)
Every post-show report should include:
- relationship totals for `assisted_session_this_year`, `registered_to_show`
- match mode distribution from `identity_match_mode`
- unresolved/zero-case diagnostics

## 4.4 Gate coupling
Before Phase 1 post-show generation:
- verify strict validation report exists and `ok=true`
- fail fast with actionable message when strict checks are not satisfied

---

## 5) Work plan (phased)

## Phase A — Profile schema hardening
Deliverables:
- extend `deep_agents_reports/config/reporting_pipeline.yaml` profile contract for post-show runs
- add optional/required keys (`strict_validation_report`, `target_run_id`, `target_campaign_id`)
- validation logic in `reporting_pipeline.py`

## Phase B — Prompt + manifest modernization
Deliverables:
- update post-show prompt templates to include run-scoped query variants
- add mandatory identity quality task(s)
- include explicit fallback language when run-scoped fields are absent

Likely files:
- `deep_agents_reports/reports/prompts/prompt_post_show_generic.md`
- `deep_agents_reports/reports/prompts/prompt_post_show_summary_generic.md`
- `deep_agents_reports/arc/pre_show/manifest.py`

## Phase C — Strict gate integration
Deliverables:
- require strict validation report for post-show pipeline profile
- ingest and surface validation summary in report intro/appendix

Likely files:
- `deep_agents_reports/reporting_pipeline.py`
- `deep_agents_reports/arc/pre_show/generator.py` (context injection)

## Phase D — Artifact contract and QA
Deliverables:
- standardized post-show artifact checklist:
  - base report,
  - enriched report,
  - strict validation report copy/reference,
  - run-scoped evidence appendix
- add concise acceptance checks in docs

## Phase E — Docs + handoff consistency
Deliverables:
- update follow-up pack docs to point to the new post-show contract
- add examples for strict-gated invocation

---

## 6) Acceptance criteria
- Post-show generation aborts if strict validation is missing/failed.
- Reports include identity attribution quality by match mode.
- Reports prefer run-scoped metrics when available.
- Legacy fallback path still works and is clearly labeled.
- Output artifacts are deterministic and linked for closure review.

---

## 7) Suggested implementation order (next PR)
1. Phase A (profile validation) + Phase C (strict gate integration) in one PR.
2. Phase B (prompt/manifest query updates) in next PR.
3. Phase D/E (artifact QA + docs) as final cleanup PR.

---

## 8) Related references
- `docs/post_event_followup_pack/post_event_handoff_2026-02-21.md`
- `docs/post_event_followup_pack/AZUREML_PIPELINE_REFACTOR_PLAN.md`
- `docs/post_event_followup_pack/END_OF_EVENT_DOC_UPDATE_LIST.md`
- `deep_agents_reports/reporting_pipeline.py`
- `deep_agents_reports/deep_agents_workflow.py`
- `deep_agents_reports/arc/pre_show/generator.py`
