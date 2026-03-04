# Pre-Show Agent Protocol

This checklist applies to every DeepAgents pre-show report run. Keep the prompts lean by opening this file with `read_file` whenever you need the detailed instructions.

## Core Configuration Reminders
- Open the processed prompt template for placeholder wording and manual-substitution hints.
- Read the event configuration YAML whenever you need SHOW_CODE, filters, or similarity attributes; do not rely on cached memory.
- Before drafting Cypher, open the Neo4j schema snapshot (or call `get_neo4j_schema`) so labels and property names are correct.

## TODO Management Rules
- The canonical TODO plan is generated per run and stored in `reports/artifacts/prebuilt_todos_<event><year>.md`.
- Load the plan in batches of **≤10 items per `write_todos` call** to keep the conversation small. Start with TODO 01‑10, confirm via `read_todos`, then append 11‑20, etc., until all entries exist.
- Never invent new TODO text. When you need the exact wording or Cypher, re-open the markdown plan and copy the entry verbatim.
- Only update TODO statuses (pending → in_progress → completed). If the count drops below the generated plan count, halt, reload the missing items from the markdown file, and confirm via `read_todos` before resuming.

## Recovery Protocol
- Check the recovery inventory markdown first. If a TODO’s output already exists locally or under `/memories`, verify the file and mark the task completed without rerunning Neo4j queries.
- Whenever you save a file under `/outputs/...`, immediately mirror the same content under `/memories/<event><year>/pre_show/...` so future runs can recover quickly.
- After any crash or rate-limit retry, inspect `/memories` with `ls`/`read_file` to understand what is already persisted before resuming work.

## Execution Protocol
1. After loading TODO 01‑10, mark the first actionable item `in_progress` and continue updating statuses as you work.
2. Before each query, read the schema snapshot and the relevant instructions in the markdown TODO plan.
3. Use `read_neo4j_cypher` for every Neo4j task, then immediately save the full JSON payload via `write_file` to the manifest path listed in the TODO. Mirror the same JSON into `/memories`.
4. When a TODO calls for Neo4j analysis, spawn the `neo4j-analysis` sub-agent with the TODO text plus schema path. Sub-agents must save their outputs before returning control.
5. If a query returns zero rows or warnings, capture that context in the saved file and `/memories` copy, fix the Cypher if needed, then complete the TODO.
6. Use filesystem middleware tools exactly as documented: `write_file` for bulk writes, `read_file` to reopen artifacts, `ls`/`glob` to discover files. Never use `edit_file`.
7. After every group of query TODOs for a numbered task, execute the corresponding synthesis TODO and save the markdown summary (again mirrored to `/memories`).
8. The final TODO assembles the report. Mirror the example report’s tone, cite the saved files by path, and ensure every statistic references both the local and `/memories` artifacts.
9. Do not finish the run until all TODOs are `completed` and every referenced file exists in both locations.

Keep this document handy and reference it instead of copying these instructions back into the conversation history.