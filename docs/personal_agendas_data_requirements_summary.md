# Personal Agendas – Minimal File Checklist
Source of truth for detailed paths: [docs/personal_agendas_data_requirements.md](docs/personal_agendas_data_requirements.md).

## Core Inputs Per Step
- **Step 1 – Registration**: For each personal_agendas config, stage main/secondary registration JSON plus matching demographic JSON (see each config’s `input_files` block) and the optional `practices_missing.csv` lookup.
- **Step 2 – Scans**: Provide current-year session export CSV, both last-year exports, and the seminar reference + scans CSV pairs for main and secondary events (paths come from each `scan_files` block). Post-analysis runs also need any `entry_scan_files` declared.
- **Step 3 – Sessions**: Ensure the three `session_files` exports (this year + two historical) exist alongside the shared `streams.json` seed referenced under `session_output_files.streams_catalog`.
- **Step 4–5 – Neo4j Nodes**: No extra raw files beyond processed outputs from Steps 1–3 plus valid Neo4j credentials supplied via each config’s `env_file` (defaults to keys/.env).
- **Step 6 – Job→Stream**: Only configs with `neo4j.job_stream_mapping.enabled: true` (currently vet shows) require `job_to_stream.csv`.
- **Step 7 – Specialization→Stream**: When `neo4j.specialization_stream_mapping.enabled: true`, provide `spezialization_to_stream.csv`.
- **Step 8 – Visitor Relationships**: Retain intermediates emitted earlier (`scan_bva_past.csv`, `scan_lva_past.csv`, `df_reg_demo_last_bva.csv`, `df_reg_demo_last_lva.csv`) because Neo4j relationship creation reuses those filenames per `scan_output_files.attended_session_inputs`.
- **Step 9 – Embeddings**: Depends on the `session_output_files.processed_sessions.this_year` CSV generated in Step 3; no extra source files.
- **Step 10 – Recommendations**: Always consumes prior outputs; only additional assets are the theatre-capacity CSV + session file whenever `recommendation.theatre_capacity_limits.enabled` is true (LVA + optional ECOMM capacity template).

## Shared Prereqs
- `keys/.env` (or equivalent) must hold Neo4j/API/MLflow secrets referenced by every config’s `env_file`.
- Documentation SVGs under `documentation` help MLflow lineage but are optional.
- If `post_analysis_mode` appears in a config, copy the listed scan and entry-scan CSVs before executing.
