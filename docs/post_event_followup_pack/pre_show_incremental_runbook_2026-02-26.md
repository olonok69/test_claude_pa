# Pre-Show Incremental Runbook (Personal Agendas) — 2026-02-26

## Purpose

Operational checklist for the final pre-show incremental run in `personal_agendas` mode, with traceability and reconciliation evidence ready for post-show continuation (M6/M8/M9).

## Scope

- Event: `tsl`
- Campaign mode: `personal_agendas`
- Run type: incremental (`create_only_new: true`)
- Primary config: `PA/config/config_tsl.yaml`

## Current state (2026-02-27)

- This active cycle has **not started** a new `personal_agendas` incremental run yet.
- Recommendation: execute preflight baseline checks first, then run the incremental pipeline, then capture reconciliation evidence.

### Next command to run (from workspace root)

```bash
python PA/main.py --config PA/config/config_tsl.yaml --only-steps 10 --create-only-new
```

### Immediate post-run check

```bash
python PA/scripts/reconcile_campaign_delivery.py \
   --config PA/config/config_tsl.yaml \
   --env-file PA/keys/.env \
   --main-json PA/data/tsl/recommendations/visitor_recommendations_tsl_<run_timestamp>.json \
   --control-json PA/data/tsl/recommendations/control/visitor_recommendations_tsl_<run_timestamp>_control.json \
   --campaign-id tsl_conversion \
   --report-file PA/large_tool_results/m5_delivery_reconciliation_incremental_<run_timestamp>.json \
   --fail-on-mismatch
```

### Paste output here (30-second reviewer check)

Copy/fill these fields immediately after execution:

- `run_id:`
- `campaign_id:` `tsl_conversion`
- `mode:` `personal_agendas`
- `main_json:`
- `control_json:`
- `reconciliation_report:`
- `reconciliation_ok:` (`true/false`)
- `mismatch_total:`

---

## Quick commands (copy/paste)

```bash
# 1) Create temporary personal_agendas config copy
CFG_TMP="/tmp/config_tsl_personal_$(date +%Y%m%d_%H%M%S).yaml"
cp PA/config/config_tsl.yaml "$CFG_TMP"
python - <<'PY'
from pathlib import Path
import yaml
paths = sorted(Path('/tmp').glob('config_tsl_personal_*.yaml'))
path = paths[-1]
cfg = yaml.safe_load(path.read_text())
cfg['mode'] = 'personal_agendas'
path.write_text(yaml.safe_dump(cfg, sort_keys=False))
print(path)
PY

# 2) Run incremental pipeline steps 1..11
python PA/main.py --config "$CFG_TMP" --only-steps 1,2,3,4,5,6,7,8,9,10,11 --skip-mlflow

# 3) Set token used for reconciliation filenames (adjust if needed)
TOKEN="$(date +%Y%m%d_%H%M%S)"

# 4) Reconcile outputs vs CampaignDelivery
python PA/scripts/reconcile_campaign_delivery.py \
   --config PA/config/config_tsl.yaml \
   --env-file PA/keys/.env \
   --main-json PA/data/tsl/recommendations/visitor_recommendations_tsl_<run_timestamp>.json \
   --control-json PA/data/tsl/recommendations/control/visitor_recommendations_tsl_<run_timestamp>_control.json \
   --campaign-id tsl_conversion \
   --report-file PA/large_tool_results/m5_delivery_reconciliation_incremental_${TOKEN}.json \
   --fail-on-mismatch
```

Replace `<run_timestamp>` with the timestamp from generated recommendation files.

---

## 0) Pre-flight checks (before pipeline)

1. Confirm config readiness:
   - `create_only_new: true`
   - recommendation traceability fields are enabled by default write path
   - Neo4j credentials available in configured env file

2. Confirm input freshness:
   - latest registration and demographics files staged
   - latest session export files staged

3. Confirm output target paths:
   - `PA/data/tsl/recommendations/`
   - `PA/data/tsl/recommendations/control/`

4. Keep VM-console-first evidence capture:
   - save full command logs
   - capture output artifact paths

---

## 1) Run incremental recommendations (steps 1–11)

Use a temporary config copy with mode switched to `personal_agendas` for this run.

```bash
cp PA/config/config_tsl.yaml /tmp/config_tsl_personal_$(date +%Y%m%d_%H%M%S).yaml
python - <<'PY'
from pathlib import Path
import yaml
path = Path(sorted(Path('/tmp').glob('config_tsl_personal_*.yaml'))[-1])
cfg = yaml.safe_load(path.read_text())
cfg['mode'] = 'personal_agendas'
path.write_text(yaml.safe_dump(cfg, sort_keys=False))
print(path)
PY
```

Run pipeline:

```bash
python PA/main.py --config /tmp/config_tsl_personal_<timestamp>.yaml --only-steps 1,2,3,4,5,6,7,8,9,10,11 --skip-mlflow
```

Expected outputs:
- `PA/data/tsl/recommendations/visitor_recommendations_tsl_<timestamp>.csv`
- `PA/data/tsl/recommendations/visitor_recommendations_tsl_<timestamp>.json`
- `PA/data/tsl/recommendations/control/visitor_recommendations_tsl_<timestamp>_control.csv`
- `PA/data/tsl/recommendations/control/visitor_recommendations_tsl_<timestamp>_control.json`

---

## 2) Reconcile file outputs vs delivery ledger (must pass)

Preferred reconciliation command (run-scoped from JSON metadata):

```bash
python PA/scripts/reconcile_campaign_delivery.py \
  --config PA/config/config_tsl.yaml \
   --env-file PA/keys/.env \
  --main-json PA/data/tsl/recommendations/visitor_recommendations_tsl_<timestamp>.json \
  --control-json PA/data/tsl/recommendations/control/visitor_recommendations_tsl_<timestamp>_control.json \
   --campaign-id tsl_conversion \
  --report-file PA/large_tool_results/m5_delivery_reconciliation_incremental_<timestamp>.json \
  --fail-on-mismatch
```

Go/No-Go:
- GO only if `mismatch_total=0` and report exits successfully.
- NO-GO if any mismatches, duplicate delivery rows, or missing run links are reported.
- For `mode: personal_agendas`, expected campaign id is `tsl_conversion`.

---

## 3) Optional V2E run-scoped import for this run

If V2E import is required for this incremental run, use the run id from recommendation metadata/Neo4j:

```bash
python PA/scripts/import_v2e_recommendations_to_neo4j.py \
  --config PA/config/config_tsl.yaml \
  --v2e-json PA/data/tsl/v2e_recommendations_4.json \
  --recommendation-run-id <resolved_run_id>
```

Verification queries are documented in:
- `docs/post_event_followup_pack/v2e_run_scoped_import_commands.md`

---

## 4) Evidence package to archive today

- pipeline run log path
- recommendation CSV/JSON output paths (main + control)
- reconciliation report JSON path
- resolved run identifiers (`run_id`, `campaign_id`, mode)
- any V2E import evidence (if executed)

---

## 5) Post-show continuation bridge (M6/M8)

After event close and scans ingestion:

1. strict identity gate:

```bash
python PA/scripts/run_post_analysis_identity_validation.py --config PA/config/config_tsl.yaml --require-post-event-data
```

2. post-analysis relationships:

```bash
python PA/main.py --config PA/config/config_tsl.yaml --only-steps 2,3,5,8 --skip-mlflow
```

3. optional output refresh:

```bash
python PA/main.py --config PA/config/config_tsl.yaml --only-steps 11 --skip-mlflow
```

4. post-show reporting and final UAT evidence:
- execute deep agents post-show profile
- complete M6 query evidence and M8 lifecycle UAT evidence

---

## Related docs

- `docs/post_event_followup_pack/reference_docs/plan_b_implementation_milestones.md`
- `docs/post_event_followup_pack/post_event_handoff_2026-02-21.md`
- `docs/post_event_followup_pack/post_event_day0_runsheet.md`
- `docs/post_event_followup_pack/v2e_run_execution_log_2026-02-25.md`
