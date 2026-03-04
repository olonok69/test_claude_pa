# Deep Agents Show Report Workflow – Executive Summary

The `deep_agents_reports` application automates a complex show analytics reports for large events (e.g. CPCN, BVA, LVS), turning raw Neo4j data into a consistent, decision‑ready insight package with minimal manual effort.

At a high level, it:

- Reads event configuration and a standardised prompt template.
- Generates a deterministic **task manifest** of all analyses to run (Cypher queries, aggregations, and synthesis tasks).
- Uses an AI agent, tightly constrained by that manifest, to execute the tasks, save all results to disk, and assemble a final narrative report.

This gives marketing, operations, and leadership teams a reliable way to answer key questions before an event: who is registered, how segments compare with last year, which sessions are most critical, and where risk or opportunity is emerging.

---

## Business Value

- **Faster pre‑show intelligence:** What previously took analysts days of ad‑hoc querying and slide building is reduced to a single, scriptable run.
- **Consistent decisions:** Every run follows the same manifest and TODO plan, making reports comparable across events and years.
- **Lower risk with AI:** The LLM is not "inventing" the analysis; it is executing a predefined checklist, reading real data from Neo4j and file outputs, and citing where each number came from.
- **Auditability:** All intermediate artifacts (queries, JSON exports, summaries) are written to version‑controlled folders so results can be inspected, rerun, or extended.

---

## What the Application Does

1. **Initialize environment & data access**
   - Loads event config (e.g. `config_cpcn.yaml`) and a pre‑show report prompt.
   - Connects securely to the Neo4j graph that already holds registrations, scans, sessions, and recommendations.
   - Selects an LLM provider (Azure OpenAI, OpenAI, or Anthropic Claude) with conservative settings for cost and safety.

2. **Plan the analysis deterministically**
   - Resolves the prompt template with event‑specific values (show code, year, thresholds).
   - Parses that resolved template into a **task manifest**: a structured list of all queries and synthesis steps the agent must perform (e.g. "Task 01 – registration overview", "Task 05 – at‑risk segments").
   - Builds a corresponding **TODO plan** so the agent’s task list is explicit and trackable.

3. **Run a supervised AI agent**
   - Spins up a DeepAgents workflow that exposes only a small toolset:
     - Read/write TODOs,
     - Read/write files in a sandboxed filesystem,
     - Direct Neo4j tools (`get_neo4j_schema`, `read_neo4j_cypher`, `write_neo4j_cypher`).
   - The agent walks through the TODOs:
     - Executes each Cypher query,
     - Saves full results to JSON files,
     - Writes human‑readable markdown summaries for each task.

4. **Assemble the final pre‑show report**
   - Once all tasks are complete and outputs exist on disk, the agent compiles a structured markdown report (executive summary, key metrics, strengths/risks, section‑by‑section insights).
   - The report references the saved files, so analysts can drill down from narrative into raw data when needed.

5. **Persist artifacts for governance & reuse**
   - Stores:
     - The resolved prompt and manifest,
     - The TODO plan and its final status,
     - All query outputs and per‑task summaries,
     - The final report.
   - Mirrors key files into a `/memories` namespace to support reruns, recovery, or post‑event analysis.

---

## Technical Overview (for Engineers)

- **Language & runtime:** Python 3.13, packaged as `deep_agents_reports`.
- **Orchestration:** Custom workflow class `ShowReportGenerator` (`arc/pre_show/generator.py`) drives initialization, manifest creation, DeepAgents setup, and execution.
- **Graph backend:** Neo4j 5.x via the official Neo4j Python driver, using APOC for schema discovery; Cypher identifiers are normalized from template aliases to concrete labels/relationships defined in config.
- **LLM integration:** DeepAgents + LangChain adapters for Azure/OpenAI/Anthropic; TODO planning and execution run through a single, supervised agent with a dedicated Neo4j sub‑agent and a critique sub‑agent for QA.
- **Filesystem safety:** A `SafeFilesystemBackend` constrains file operations to the repo root and a `/memories/<event><year>/<report_type>` namespace.
- **Outputs:** Artifacts and final reports live under `reports/artifacts/` and `outputs/<event><year>/<report_type>/`, making the pipeline easy to monitor in Git and in file explorers.
- **Pipeline runner:** `reporting_pipeline.py` can execute profile-driven pre-show/post-show generation plus optional phase-2 enrichment.
