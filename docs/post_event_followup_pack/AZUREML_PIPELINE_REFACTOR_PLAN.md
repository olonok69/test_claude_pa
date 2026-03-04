# Azure ML Pipeline Refactor Plan (Aligned to Latest Changes)

Prepared: 2026-02-21

## 1) Why refactor now
The current Azure ML implementation works, but the repository has moved forward with:
- run-scoped traceability and reconciliation,
- identity-first post-analysis attribution,
- strict post-event validation gates,
- explicit multi-mode lifecycle (`personal_agendas`, `engagement`, `post_analysis`).

Azure ML scripts/notebooks should be realigned so cloud runs follow the same contracts as the core `PA/` workflow.

---

## 2) Current-state findings (from scan)

### Pipeline scripts (`azureml_pipeline/`)
- Four step scripts are present and active:
  - `azureml_step1_data_prep.py`
  - `azureml_step2_neo4j_prep.py`
  - `azureml_step3_session_embedding.py`
  - `azureml_step4_recommendations.py`
- Secret loading, config loading, path remapping, and env overrides are duplicated across steps.
- Mode control is implicit and fragmented:
  - no single top-level `mode` contract in Azure ML orchestration,
  - no first-class post-event gate step equivalent to strict validation.
- Step 1 includes post-analysis file-awareness logic, but orchestration still behaves like a generic 4-step full run.

### Azure ML config (`azureml_pipeline/pipeline_config.yaml`)
- Static pattern assumes `PA/config/config_${EVENT_TYPE}.yaml` and legacy-style event typing.
- Does not model current lifecycle gates (pre-event vs post-event strict validation).
- Does not explicitly encode mode-specific step matrix.

### Submission notebooks (`notebooks/submit_pipeline_complete_*.ipynb`)
- Four near-duplicate notebooks (`bva`, `cpcn`, `ecomm`, `lva`) with repeated logic.
- Hardcoded/forced env behavior appears in notebooks (for example setting tracking URI / Neo4j env in notebook cells).
- Orchestration definition is repeated per notebook and drifts risk is high.

### Notebook lineage (`bva/`, `cpc/`)
- Legacy operational flow is notebook-heavy and useful as historical context, but not ideal as production orchestration authority.

---

## 3) Refactor goals
1. Single source of truth for Azure ML orchestration.
2. Full parity with core runtime contracts (mode, run-scoped writes, post-event strict gate).
3. Remove duplicated submission logic across notebooks.
4. Keep event-specific behavior in event config files, not notebook code.
5. Make post-event analysis operationally safe by design.

---

## 4) Target architecture

## 4.1 Orchestration pattern
Introduce a single Azure ML entry orchestration layer that is mode-aware:
- `personal_agendas`
- `engagement`
- `post_analysis`

Each run specifies:
- config path (explicit, no inferred event type mapping),
- mode,
- incremental flag,
- Neo4j environment,
- post-event strict enforcement flag (for post-analysis closure runs).

## 4.2 Step contract model
Use a mode-to-step matrix aligned to core pipeline behavior:
- Personal agendas full: data prep -> neo4j prep -> embedding -> recommendations
- Engagement: same technical chain but engagement mode config behavior
- Post-analysis: data prep + neo4j post-analysis relationship updates + optional output refresh, with strict gate before closure reporting

## 4.3 Validation gate integration
Add explicit gate stage for post-event runs:
- run `scripts/run_post_analysis_identity_validation.py --require-post-event-data`
- fail fast when post-event scan/entry inputs or relationships are missing

## 4.4 Notebook consolidation
Replace 4 duplicated submit notebooks with:
- one parameterized submit notebook (`notebooks/submit_pipeline_unified.ipynb`) OR
- a Python submit script as primary, notebook as thin launcher.

Keep existing notebooks as archived references (read-only/deprecated label).

---

## 5) Refactor work plan (phased)

## Phase A — Design freeze
Deliverables:
- finalized Azure ML mode contract (inputs/outputs/required params),
- step matrix per mode,
- migration map from old submit notebooks to unified submit flow.

Files to update/create:
- `azureml_pipeline/README.md`
- `azureml_pipeline/pipeline_config.yaml` (or split into mode-aware config files)
- new design note in `docs/post_event_followup_pack/`.

## Phase B — Shared runtime utilities
Deliverables:
- extract shared setup utilities used by all step scripts:
  - config loader + path normalization,
  - key vault / env credential resolution,
  - Neo4j environment selection,
  - common telemetry/logging bootstrap.

Files to create:
- `azureml_pipeline/runtime/common.py`
- `azureml_pipeline/runtime/secrets.py`
- `azureml_pipeline/runtime/config.py`

Files to simplify:
- step 1–4 scripts remove duplicated bootstrap blocks.

## Phase C — Mode-aware orchestration
Deliverables:
- add explicit mode input for Azure ML submission,
- enforce mode-specific step graph,
- support explicit config path argument (not only `config_type`).

Files to update:
- unified submit notebook/script,
- command component definitions.

## Phase D — Post-event strict gate
Deliverables:
- add validation step/job before post-analysis closure,
- publish gate output artifact (JSON report) and fail conditions.

Integration point:
- invoke `scripts/run_post_analysis_identity_validation.py` in strict mode for post-event closure path.

## Phase E — Notebook cleanup
Deliverables:
- mark old submit notebooks deprecated,
- maintain one canonical submit path,
- update docs and operator runbook links.

## Phase F — Verification and cutover
Deliverables:
- dry-run per mode (`personal_agendas`, `engagement`, `post_analysis`),
- artifact parity checks vs local workflow,
- runbook with rollback path.

---

## 6) Acceptance criteria
- A single canonical Azure ML submission flow exists.
- Mode and config path are explicit user inputs.
- Post-analysis closure cannot pass without strict gate success.
- No forced environment overrides in notebook code (for example hardcoded tracking URI/environment).
- Existing outputs (recommendations, reconciliation evidence) remain compatible.

---

## 7) Suggested execution order (when work resumes)
1. Phase A + B in one PR (design + shared utilities).
2. Phase C in next PR (unified mode-aware submit flow).
3. Phase D + E in post-event PR window.
4. Phase F as final cutover verification.

---

## 8) Related documents
- `docs/post_event_followup_pack/post_event_handoff_2026-02-21.md`
- `docs/post_event_followup_pack/post_event_day0_runsheet.md`
- `docs/post_event_followup_pack/END_OF_EVENT_DOC_UPDATE_LIST.md`
- `docs/plan_b_implementation_milestones.md`
- `docs/post_analysis_mode.md`
- `azureml_pipeline/README.md`
