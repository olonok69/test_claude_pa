# M5 Runbook: Delivery Ledger Reconciliation

This runbook validates that campaign output files and Neo4j `CampaignDelivery` are aligned for a given `run_id`.

## Artifacts
- Reconciliation script: `PA/scripts/reconcile_campaign_delivery.py`
- Cypher checks: `PA/scripts/cypher/m5_delivery_reconciliation_checks.cypher`
- Report output (default): `large_tool_results/m5_delivery_reconciliation_report.json`

## Inputs
- Main recommendations JSON (non-control export)
- Optional control recommendations JSON
- Config file with Neo4j connectivity

## Step 1 — Run reconciliation script
```bash
python PA/scripts/reconcile_campaign_delivery.py \
  --config PA/config/config_tsl.yaml \
  --env-file PA/keys/.env \
  --main-json data/tsl/recommendations/visitor_recommendations_tsl_<timestamp>.json \
  --control-json data/tsl/recommendations/control/visitor_recommendations_tsl_<timestamp>_control.json
```

Optional overrides:
```bash
python PA/scripts/reconcile_campaign_delivery.py \
  --config PA/config/config_tsl.yaml \
  --env-file PA/keys/.env \
  --main-json data/tsl/recommendations/visitor_recommendations_tsl_<timestamp>.json \
  --control-json data/tsl/recommendations/control/visitor_recommendations_tsl_<timestamp>_control.json \
  --run-id tsl_personal_agendas_20260226T160736Z_1b8f65e8 \
  --campaign-id tsl_conversion \
  --show tsl \
  --fail-on-mismatch
```

## Step 2 — Review report
Open:
- `large_tool_results/m5_delivery_reconciliation_report.json`

Key fields:
- `reconciliation.ok`
- `reconciliation.mismatch_total`
- `missing_in_neo4j_count`
- `extra_in_neo4j_count`
- `status_mismatch_count`
- `neo4j.integrity.deliveries_without_for_visitor`
- `neo4j.integrity.deliveries_without_for_run`

## Step 3 — DB-side verification (optional)
Run:
- `PA/scripts/cypher/m5_delivery_reconciliation_checks.cypher`

Set params first in Neo4j Browser:
```cypher
:param run_id => 'your_run_id_here'
:param campaign_id => 'tsl_conversion'
:param show => 'tsl'
```

## Success criteria
- `reconciliation.ok = true`
- `mismatch_total = 0`
- no duplicate delivery visitors for the run
- no missing `FOR_VISITOR` / `FOR_RUN` links

## Notes
- Script is read-only against Neo4j.
- `control_json` is optional; without it, expected status is `sent` for all visitors in `main_json`.
- Use mode-aligned campaign IDs when passing `--campaign-id`:
  - `personal_agendas` -> `tsl_conversion`
  - `engagement` -> `tsl_engagement`
