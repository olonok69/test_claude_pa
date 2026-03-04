# MLflow Reporting in PA

This note describes how the PA CLI reports to Databricks MLflow: what is logged, when it runs, the required environment, and how to opt out.

---

## Prerequisites

Set these environment variables before running `python PA/main.py` (or the AzureML steps):
- `MLFLOW_EXPERIMENT_ID`
- `DATABRICKS_HOST`
- `MLFLOW_TRACKING_URI`

If any are missing, MLflow is disabled and the pipeline continues with a warning.

---

## How logging is wired

- Entry point: `PA/main.py` creates an `MLflowManager` unless `--skip-mlflow` is passed.
- Run start: `MLflowManager.start_run()` opens a single run named `{event}_{timestamp}`.
- Parameters:
  - Full config recursively (sensitive keys redacted) via `log_config_as_params`.
  - Core flags: `pipeline_type`, `event_name`, `processing_mode` (vet vs generic), `pipeline_version`, `create_only_new`, `skip_neo4j`, `steps_to_run`, command-line args, and the config file path.
  - Pipeline step toggles (`pipeline_steps.*`).
  - Documentation asset paths (`documentation_*`).
- Artifacts:
  - Sanitized config YAML snapshot per run.
  - Documentation assets (SVGs) when present.
  - Processing summary JSON (see below) and any other artifacts logged by processors.
- Metrics:
  - Per-step timings (e.g., `step1_registration_time_seconds`, `step2_scan_time_seconds`).
  - Aggregated processor metrics from `mlflow_utils.log_summary_metrics` for steps 1–10 (registration, scan, sessions, Neo4j steps, embeddings, recommendations).
  - Neo4j step-specific counts from `log_neo4j_step_metrics` (nodes/relationships created, skipped, etc.).
  - Total processing time and steps completed from the summary JSON.

---

## What gets logged (high level)

- **Registration**: raw and processed row counts, unique badges, with/without demographics, returning visitor counts.
- **Scan**: total scans, unique seminars, unique attendees per show.
- **Sessions**: total sessions by year/stream, stream backfill stats.
- **Neo4j (steps 4–8)**: nodes created/skipped/updated, relationships created/skipped/failed, job/specialization mappings, visitor relationship breakdowns (including assisted_session_this_year).
- **Embeddings**: sessions processed/embedded, with/without stream descriptions, errors.
- **Recommendations**: visitors processed, with/without recommendations, totals generated/filtered, errors, processing time.
- **Timing**: per-step durations and total processing time.

These values are pulled from each processor’s `statistics` attributes where available; legacy attribute names are handled for backward compatibility.

---

## Processing summary artifact

`generate_and_save_summary()` writes `processing_summary.json`. `MLflowManager.log_processing_summary()` uploads it and flattens numeric fields into metrics (`summary_*`). This captures any metrics not already emitted via `log_summary_metrics`.

---

## Documentation assets

If the config `documentation` block lists SVGs (e.g., `docs/generic_pipeline_map.svg`), their paths are logged as params and the files are uploaded as artifacts when present.

---

## Opting out / testing

- Use `--skip-mlflow` to run the pipeline without any MLflow calls.
- Fail-safe: if Databricks/MLflow settings are missing or a logging error occurs, logging is disabled for the rest of the run and the pipeline continues.

---

## Quick recipe

```powershell
# Ensure env vars are set (example)
$env:MLFLOW_EXPERIMENT_ID = "123"
$env:DATABRICKS_HOST = "https://<workspace>.databricks.com"
$env:MLFLOW_TRACKING_URI = "databricks"

# Run full pipeline with MLflow on
python PA/main.py --config config/config_cpcn.yaml

# Run without MLflow
python PA/main.py --config config/config_cpcn.yaml --skip-mlflow
```

Artifacts and metrics will appear in the configured Databricks MLflow experiment for the chosen event run.
