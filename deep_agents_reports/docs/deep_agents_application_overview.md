# Deep Agents Reports Application Overview

This document consolidates the operational knowledge for the `deep_agents_reports` application: what it delivers, how it is put together, which configurations and environments it depends on, and how to operate it across modes.

## 1. Scope & Objectives
- Automate the 13-task pre-show (and optional post-show) analytics package for large events such as CPCN, LVA/BVA, and ECOMM.
- Convert deterministic templates plus event configs into an executable TODO manifest for DeepAgents, ensuring every query, synthesis step, and report section is traceable to Neo4j and filesystem artifacts.
- Provide stakeholders with an auditable, repeatable report that covers registration health, session demand, visitor behavior, and recommendation performance ahead of each show.

## 2. Technology & Architecture
- **Runtime:** Python 3.13 (`deep_agents_workflow.py` is the CLI entrypoint).
- **Core orchestrator:** `arc/pre_show/generator.py` defines `ShowReportGenerator`, handling environment bootstrap, manifest creation, agent wiring, and artifact persistence.
- **Agent stack:** DeepAgents + LangChain chat models (Azure OpenAI, OpenAI, Anthropic) with two sub-agents (Neo4j analysis + critique) and direct Neo4j tooling (`get_neo4j_schema`, `read_neo4j_cypher`, `write_neo4j_cypher`).
- **Graph backend:** Neo4j 5.x accessed via the official driver; schema aliasing keeps prompt templates decoupled from concrete labels defined in config.
- **Filesystem safety:** `SafeFilesystemBackend` disables `edit_file` and mirrors every artifact into both the repo output tree and `/memories/<event><year>/<report_type>` for disaster recovery.
- **Artifacts:** Deterministic manifest/TODO plans and all agent outputs land under `reports/artifacts/` and `outputs/<event><year>/<report_type>/`.

## 3. Pipelines & Upstream Data
- The application assumes the PA pipeline has hydrated Neo4j with ten processors (Registration → Recommendation). See [`docs/readme_config.md`](readme_config.pdf) for the step map and toggles (`pipeline_steps`).
- Configured file paths under `input_files`, `scan_files`, and `session_files` supply the raw JSON/CSV exports that earlier processors ingest; their cleaned outputs feed Neo4j nodes labeled in the `neo4j.node_labels` block.
- Engagement runs reuse prior-year registrations (`mode: engagement`), while personal agenda runs process the current cohort. Both modes ultimately surface in Neo4j and are queried by the agent.

## 4. Configuration Model (`config/*.yaml`)
| Section | Purpose |
| --- | --- |
| `mode`, `pipeline_steps`, `create_only_new` | Toggle pipeline behavior (personal agendas vs. engagement, per-step activation, incremental recommendation writes). |
| `event` | Names, show codes, and years that flow into filenames, filters, and prompt placeholders. |
| `engagement_mode` | Overrides for reusing last-year cohorts, including show-code remapping and returning-flag resets. |
| `input_files`, `scan_files`, `session_files` | Raw data locations for registration, scans, seminars, and session exports. |
| `scan_output_files`, `session_output_files`, `output_files` | Canonical filenames for cleaned datasets that downstream processors and Neo4j expect. |
| `stream_processing`, `titles_to_remove`, `map_vets` | Stream enrichment controls and sponsor normalization. |
| `recommendation` | Similarity weights, filter toggles, theatre capacity enforcement, and export enrichment fields. |
| `neo4j` | Label/relationship aliases, unique identifiers, job/specialization stream mapping toggles, and visitor relationship metadata. |
| `default_visitor_properties`, `valid_badge_types`, `questions_to_keep` | Data hygiene defaults that protect Neo4j writes and downstream analytics. |

Each configuration file (e.g., `config_cpcn.yaml`, `config_ecomm.yaml`, `config_vet_lva.yaml`) follows this schema.[`docs/readme_config.md`](readme_config.pdf) describes every field and highlights per-show nuances.

## 5. Neo4j Environments & Credentials
- Profiles (`--neo4j-profile dev|test|prod`) map to env vars `NEO4J_URI_<PROFILE>` and `NEO4J_PASSWORD_<PROFILE>` with a shared `NEO4J_USERNAME`. These must be present in `keys/.env` before running the CLI.
- `ShowReportGenerator` verifies connectivity at startup and exposes `get_neo4j_schema` (APOC) plus read/write Cypher helpers. APOC must be installed; failures surface as `Neo.ClientError.Procedure.ProcedureNotFound`.
- `neo4j.node_labels` and `neo4j.relationships` drive identifier normalization so prompts can reference generic labels like `Visitor` while queries hit concrete nodes such as `Visitor_this_year`.

## 6. Operating Modes
- **Pipeline mode (`mode` in config):**
  - `personal_agendas` (default) runs the current-year cohort end-to-end.
  - `engagement` replays last-year attendees using `engagement_mode.registration_shows` and optional returning-flag resets.
- **Workflow type (`report_type` argument, default `pre_show`):**
  - `pre_show` generates TODOs and artifacts for upcoming events.
  - `post_show` reuses the same machinery but adds capacity/attendance context and can compare against a provided pre-show report.
- The CLI supports both modes directly via `--report-type` and `--pre-show-report`.

## 7. Operational Lifecycle
![Execution Lifecycle](./execution_lifecycle.svg)

1. **Initialize (`deep_agents_workflow.py`):** parse CLI args, instantiate `ShowReportGenerator`, connect to Neo4j.
2. **Template & Config fusion:** load the prompt (`reports/prompts/*.md`), replace placeholders with config values, and persist the resolved copy.
3. **Manifest & TODO synthesis:** `build_task_manifest` parses the template into per-task metadata; `build_prebuilt_todos` and `build_todo_state_entries` turn that manifest into the canonical 50+ TODO plan plus state seed.
4. **Recovery scan:** `collect_existing_artifacts` mirrors any pre-existing outputs into `/memories` and writes a recovery inventory for the agent.
5. **Agent execution:** DeepAgents loads TODOs in ≤10-item batches, executes each query via the Neo4j sub-agent, saves results with mirrored copies, runs critiques, and assembles section summaries followed by the final report.
6. **Completion checks:** the generator enforces full TODO completion, artifact existence under `outputs/...`, and raises actionable errors if counts drift or files are missing.
7. **Persistence:** `_persist_artifacts` stores TODO status snapshots, agent responses, and any sub-agent files under timestamped `reports/artifacts/todo_generation_*` directories.

Typical PowerShell run (pre-show):
```powershell
python deep_agents_workflow.py `
  --event CPCN `
  --year 2025 `
  --config config\config_cpcn.yaml `
  --prompt-template reports\prompts\prompt_initial_run_generic_short.md `
  --neo4j-profile test `
  --neo4j-database neo4j `
  --provider anthropic `
  --model claude-haiku-4-5 `
  --temperature 0.1 `
  --report-type pre_show `
  --example-report reports\report_cpcn_13112025_short.md `
  --verbose
```

Typical profile-based run (pre/post + enrichment):
```powershell
python -m deep_agents_reports.reporting_pipeline --profile lva2025
python -m deep_agents_reports.reporting_pipeline --profile lva2025_post
```

## 8. Artifacts, Memory, and Recovery
- **Output root:** `outputs/<event><year>/<report_type>/` stores schema snapshots, query JSON outputs, per-task summaries, and the final markdown report (e.g., `final_report_cpcn2025_pre_show.md`).
- **Artifacts:** `reports/artifacts/` contains manifests, TODO plans, processed prompts, recovery inventories, and timestamped agent-run folders with TODO snapshots and chat transcripts.
- **Memory mirror:** `/memories/<event><year>/<report_type>/` (backed by `SafeFilesystemBackend`) must contain byte-identical copies of every artifact written to the output directory so reruns can resume via the recovery inventory.
- **Protocol:** `docs/pre_show_agent_protocol.md` codifies TODO management, mirroring rules, and failure recovery steps; the agent is instructed to consult it during execution.

## 9. Observability & Troubleshooting
- Use `--verbose` to enable debug logging from `ShowReportGenerator` (including Neo4j query diagnostics and TODO reconciliation messages).
- If TODO counts diverge from the canonical plan, the generator halts with a retry directive that forces the agent to reload TODO batches from the markdown plan.
- Schema or permission issues manifest as Neo4j driver errors; confirm APOC availability for `get_neo4j_schema` and validate credentials in `keys/.env`.
- If no files appear under the output directory, the run aborts—verify that the agent is using `write_file` rather than `edit_file`, and that filesystem mirroring succeeds.
- Reference the recovery inventory to skip already-completed TODOs safely by validating both the local artifact and `/memories` copy before marking tasks complete.

Keep this overview alongside [`README.md`](README.pdf), and the Pesonal Agendas application_overview.pdf so new operators can onboard quickly and experienced users have a single reference for scope, technologies, pipelines, configs, environments, modes, and day-to-day operations.
