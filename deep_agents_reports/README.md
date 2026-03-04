# Deep Agents Show Report Workflow

An automation layer that scaffolds and executes the 13-task pre-show analytics report using [DeepAgents](https://github.com/deepagents/deepagents), Neo4j, and LangChain-compatible LLMs. The workflow compiles a deterministic TODO plan, primes the agent with schema/config context, and drives the full report generation loop for any supported event configuration.

## Core Capabilities
- **Deterministic orchestration** – builds a task manifest, TODO plan, schema snapshot, and recovery inventory before an LLM is contacted (`arc/pre_show/manifest.py`).
- **Safety-first filesystem access** – proxies DeepAgents file operations through a sandboxed backend that mirrors artifacts into `/memories/<event><year>/pre_show` for disaster recovery (`arc/pre_show/backends.py`).
- **Direct Neo4j tooling** – exposes `get_neo4j_schema`, `read_neo4j_cypher`, and `write_neo4j_cypher` directly to the agent with identifier normalization and query rewriting (`arc/pre_show/generator.py`).
- **LLM provider flexibility** – supports Azure OpenAI, OpenAI, and Anthropic (Claude 4.5) via a unified `ModelSettings` abstraction (`arc/models.py`).
- **Artifact persistence** – archives TODO states, agent responses, result files, and schema snapshots under `reports/artifacts/` and `outputs/<event><year>/<report_type>/`.

## High-Level Architecture
```
CLI (deep_agents_workflow.py)
    │
    └── ShowReportGenerator (arc/pre_show/generator.py)
          ├─ load_event_config / prompt template resolution
          ├─ manifest + TODO builders (arc/pre_show/manifest.py)
          ├─ prompt/context assembly (arc/pre_show/prompts.py)
          ├─ DeepAgents + SubAgents + Neo4j tools
          ├─ TODO reconciliation + execution loop
          └─ artifact/memory persistence
```
- **CLI** – `deep_agents_workflow.py` parses runtime options and instantiates `ShowReportGenerator`.
- **Generator** – encapsulates init (config, prompt, Neo4j, model), manifest production, DeepAgent creation, execution, and error handling.
- **Backends** – `SafeFilesystemBackend` enforces repo-relative IO with explicit `/memories/` routing for long-term storage.
- **Prompts** – `arc/pre_show/prompts.py` produces the main agent instructions plus sub-agent system prompts (Neo4j analysis + critique QA).

## Technology Stack
- **Language runtime** – Python 3.13 (see `.python-version`).
- **Orchestration** – DeepAgents 0.2.x (task tooling, TODO middleware, sub-agent delegation).
- **LLM access** – LangChain, `langchain-openai`, `langchain-anthropic`, `langchain-mcp-adapters`.
- **Graph layer** – Neo4j 5.x via the official Neo4j Python driver.
- **Configuration** – YAML-driven event configs in `config/` and Markdown prompt templates under `reports/prompts/`.
- **Package/dependency management** – `requirements.txt` (pip / uv) + `pyproject.toml` for editable installs.

## Repository Layout
| Path | Description |
| --- | --- |
| `deep_agents_workflow.py` | CLI entrypoint that wires args into the generator and prints run summaries. |
| `arc/pre_show/` | Modularized workflow components (generator, manifest helpers, prompts, filesystem backends). |
| `config/` | Event-level YAML files consumed by both the data pipeline and this workflow. |
| `docs/` | Authoring aids (prompt reference, protocol checklists, config guide). |
| `reports/prompts/` | Generic and event-specific instruction templates. |
| `reports/artifacts/` | Auto-generated manifest/TODO/response snapshots per run. |
| `outputs/<event><year>/pre_show/` | Resulting Neo4j schema dumps, JSON exports, and mirrored agent files. |
| `memory/` | Long-term sandbox used by the filesystem backend to persist artifacts across DeepAgents sessions. |

## Prerequisites
1. **Python** – 3.11.x (match `.python-version`).
2. **Neo4j** – Access to a Neo4j instance (4.4+ recommended, 5.x tested) with APOC installed for schema discovery.
3. **Environment variables** – Stored in `keys/.env` or exported prior to launch:
   - `NEO4J_URI_<PROFILE>` (e.g., `NEO4J_URI_TEST=bolt://...`).
   - `NEO4J_PASSWORD_<PROFILE>` and optional global `NEO4J_USERNAME` (defaults to `neo4j`).
   - `OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY`/`AZURE_OPENAI_ENDPOINT`/`AZURE_OPENAI_DEPLOYMENT`, or `ANTHROPIC_API_KEY` depending on provider.
4. **Event configuration** – copy or adjust one of the YAML files in `config/`. See `docs/readme_config.md` for field-by-field guidance.
5. **Prompt template** – typically `reports/prompts/prompt_initial_run_generic_short.md` or an event-specific variant.

## Installation
```bash
python -m venv .venv
. .venv/Scripts/activate            # PowerShell: ./.venv/Scripts/Activate.ps1
pip install -U pip
pip install -r requirements.txt
# optional editable install for shared libs
pip install -e .
```
> Prefer `uv pip sync requirements.txt` if the `uv` CLI is available; it matches the checked-in `uv.lock`.

## Configuration
### Environment Variables
Create `keys/.env` (or export in your shell):
```env
# Neo4j profiles consumed via --neo4j-profile
NEO4J_URI_DEV=bolt://localhost:7687
NEO4J_URI_TEST=neo4j+s://test.db.neo4j.io
NEO4J_URI_PROD=neo4j+s://prod.db.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD_DEV=dev-password
NEO4J_PASSWORD_TEST=test-password
NEO4J_PASSWORD_PROD=prod-password

# LLM providers
OPENAI_API_KEY=sk-...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
ANTHROPIC_API_KEY=...
```
`ShowReportGenerator` selects the correct URI/password pair based on `--neo4j-profile` and falls back to `NEO4J_USERNAME` if a profile-specific username is not provided.

### Event YAML
Each config under `config/` mirrors the broader PA pipeline options (registration/scans/sessions/recommendations). This workflow mainly consumes:
- `mode`, `event.*`, and `neo4j.*` metadata to format prompts and normalize Cypher identifiers.
- `recommendation.similarity_attributes` to expand placeholder queries in the manifest.
- File path hints for output mirroring.
Refer to `docs/readme_config.md` for exhaustive explanations.

### Prompt Templates
Prompt markdown lives in `reports/prompts/`. The workflow reads the template, replaces `[PLACEHOLDER]` tokens using config values, and saves the resolved version under `reports/artifacts/processed_prompt_<event><year>.md`. Keep the template synchronized with the TODO manifest expectations (sections labeled `### TASK n` etc.).

## Running the Workflow
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
**Key flags**
- `--provider` / `--model` – switch between Azure/OpenAI/Anthropic deployments.
- `--example-report` – optional tone/style reference included in the agent context.
- `--neo4j-profile` – selects the credential set via env vars.
- `--report-type` – choose `pre_show` or `post_show`.
- `--pre-show-report` – required context file for post-show comparisons.
- `--verbose` – raises logging level for troubleshooting.

## Reporting Pipeline (Phase 1 + Phase 2)
Use `reporting_pipeline.py` to run generation plus optional enrichment from a profile in `config/reporting_pipeline.yaml`.

```powershell
# Pre-show profile
python -m deep_agents_reports.reporting_pipeline --profile lva2025

# Post-show profile
python -m deep_agents_reports.reporting_pipeline --profile lva2025_post

# Skip phase-2 enrichment
python -m deep_agents_reports.reporting_pipeline --profile cpcn2025 --skip-enrichment
```

What it does:
- **Phase 1**: runs `ShowReportGenerator` with profile-specific event/config/prompt/model settings.
- **Phase 2**: runs `enrich_report.py` when `enable_enrichment: true`.
- **Outputs**: writes base report in `outputs/<event><year>/<report_type>/` and optional `_enriched` version.

## Execution Lifecycle
![Execution Lifecycle Diagram](docs/execution_lifecycle.svg)

1. **Initialization** – loads `.env`, resolves paths relative to repo root, mounts filesystem and memory backends, configures the selected LLM, and verifies Neo4j connectivity.
2. **Template resolution** – injects config-derived values into the prompt template and writes a processed copy to `reports/artifacts/`.
3. **Manifest & TODO synthesis** – parses the template, emits a JSON manifest plus Markdown TODO plan, builds canonical TODO state expectations, and computes recovery inventory data.
4. **Agent bootstrap** – constructs the DeepAgent with direct Neo4j tool bindings, a Neo4j-analysis sub-agent (Cypher author), and a critique sub-agent for QA.
5. **TODO alignment loop** – runs the agent, reconciles the emitted TODO list against the canonical plan (`_align_todos_with_manifest`), and retries up to `max_todo_plan_attempts` with explicit corrective instructions.
6. **Execution monitoring** – enforces completion of all TODOs, checks for actual filesystem artifacts, and raises actionable runtime errors when the agent halts prematurely.
7. **Artifact persistence** – saves TODO summaries, JSON payloads, schema snapshots, recovery inventories, and final agent replies under `reports/artifacts/<timestamp>` plus the memory namespace.

## Generated Artifacts
| Artifact | Location | Purpose |
| --- | --- | --- |
| Processed prompt | `reports/artifacts/processed_prompt_<event><year>.md` | Exact instructions agent followed (with placeholders resolved). |
| Task manifest | `reports/artifacts/task_manifest_<event><year>.json` | Deterministic list of queries & synthesis tasks. |
| TODO plan | `reports/artifacts/prebuilt_todos_<event><year>.md` | Markdown version fed into `write_todos`. |
| Schema snapshot | `outputs/<event><year>/<report_type>/neo4j_schema_<event><year>.json` | Fresh APOC schema export for every run. |
| Recovery inventory | `reports/artifacts/recovery_inventory_<event><year>.md` | Links to artifacts already on disk or in `/memories`. |
| Agent files | `reports/artifacts/todo_generation_<timestamp>/agent_files/` | Files created by DeepAgents via filesystem tools. |
| Memory mirrors | `/memories/<event><year>/<report_type>/` | Redundant copies for subsequent reruns/recovery steps. |

## Observability & Troubleshooting
- **Logging** – the generator logs via the root logger; run with `--verbose` to see per-step debug output in the console.
- **Neo4j issues** – look for `Neo4j Error executing read query` messages; `_normalize_cypher_identifiers` auto-maps labels/relationships, but invalid config values will surface here.
- **TODO drift** – if the agent overwrites the canonical TODO list, the retry directive instructs it to reload the markdown plan; failures raise `RuntimeError` with diagnostic summaries.
- **Filesystem writes** – the workflow guards against empty output directories; if no files land under `outputs/<event><year>/<report_type>`, the run aborts to avoid silent failures.

## Extending & Customizing
- **New events** – duplicate a YAML config, update event metadata/paths, and point the CLI at the new file.
- **Prompt evolutions** – adjust `reports/prompts/*.md` and ensure the task manifest regexes in `arc/pre_show/manifest.py` still match section headings.
- **Additional tools** – register more DeepAgents tools (e.g., HTTP clients) inside `_create_agent` in `arc/pre_show/generator.py`.
- **Alternate storage** – extend `SafeFilesystemBackend` if you need to expose additional sandbox roots or cloud storage adapters.

## Maintenance Checklist
1. Keep `requirements.txt` and `uv.lock` in sync after dependency bumps.
2. Rotate API keys and Neo4j passwords in the `.env` store for each environment.
3. Periodically prune `reports/artifacts/` and `/memories/` to avoid unbounded disk growth.
4. Validate new configs by running `python -m py_compile arc/pre_show/*.py` and a dry-run CLI invocation against a staging Neo4j profile.
5. Monitor Neo4j schema changes: if node labels/relationship names change, update `label_aliases` and `relationships` in the config or adjust `_normalize_cypher_identifiers` accordingly.
