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
  --main-json data/tsl/recommendations/visitor_recommendations_tsl_<timestamp>.json \
  --control-json data/tsl/recommendations/control/visitor_recommendations_tsl_<timestamp>_control.json
```

Optional overrides:
```bash
python PA/scripts/reconcile_campaign_delivery.py \
  --config PA/config/config_tsl.yaml \
  --main-json data/tsl/recommendations/visitor_recommendations_tsl_<timestamp>.json \
  --control-json data/tsl/recommendations/control/visitor_recommendations_tsl_<timestamp>_control.json \
  --run-id tsl_engagement_20260226T090000Z_ab12cd34 \
  --campaign-id tsl_engagement \
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
:param campaign_id => 'tsl_engagement'
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

## Multi-run interpretation note (2026-03-03)
- In environments with multiple campaign runs, the legacy relationship verifier could report false `IS_RECOMMENDED metadata_mismatch` by reading a relationship from another run for the same `(visitor, session)` pair.
- Current reconciler behavior is run-scoped for relationship verification: it evaluates relationship presence and metadata against the target `run_id` before mismatch checks.
- Operational effect: a non-zero relationship metadata mismatch after this update should be treated as a real run-scoped issue, not cross-run noise.

## Long-run resilience note
- For heavy reconciliations, use transient retry flags to tolerate temporary Neo4j unavailability:

```bash
python PA/scripts/reconcile_engagement_delivery_from_unified.py \
  --config PA/config/config_tsl.yaml \
  --report-file PA/large_tool_results/reconcile_engagement_delivery_from_unified_verify_after_patch.json \
  --neo4j-retry-attempts 8 \
  --neo4j-retry-backoff-seconds 3.0
```

- Recommended baseline for large runs:
  - `--neo4j-retry-attempts 8`
  - `--neo4j-retry-backoff-seconds 3.0`
