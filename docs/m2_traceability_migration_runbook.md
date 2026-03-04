# M2 Runbook: Traceability Migration & Backfill

This runbook executes Milestone M2 against Neo4j using idempotent scripts.

## Prerequisites
- Database backup already taken (confirmed).
- Valid Neo4j credentials available via `.env` and config.
- Config file available (example): `PA/config/config_tsl.yaml`.

## Artifacts
- Migration runner: `PA/scripts/migrate_traceability_m2.py`
- Verification query pack: `PA/scripts/cypher/m2_traceability_verification.cypher`
- Migration report output (default): `large_tool_results/m2_traceability_migration_report.json`

## Step 1 — Dry run (impact only)
```bash
python PA/scripts/migrate_traceability_m2.py \
  --config PA/config/config_tsl.yaml \
  --dry-run
```

Expected:
- No writes performed.
- Prints `before` and `after` counts (should be identical in dry-run).
- Writes JSON report for audit.

## Step 2 — Apply migration
```bash
python PA/scripts/migrate_traceability_m2.py \
  --config PA/config/config_tsl.yaml
```

What it applies:
1. Constraints + indexes (`RecommendationRun`, `CampaignDelivery`).
2. Legacy run node upsert (`run_id=legacy_pre_traceability`).
3. Backfill on `IS_RECOMMENDED` when `run_id` is missing.
4. Delivery ledger backfill for legacy run visitors.

## Step 3 — Verify in Neo4j
Execute queries from:
- `PA/scripts/cypher/m2_traceability_verification.cypher`

Success criteria:
- `missing_run_id = 0`
- `missing_run_mode = 0`
- `missing_campaign_id = 0`
- `missing_show = 0`
- `legacy_visitors_missing_delivery = 0`
- no duplicates returned by uniqueness sanity checks.

## Optional flags
- Override show code:
```bash
python PA/scripts/migrate_traceability_m2.py --config PA/config/config_tsl.yaml --show tsl
```
- Override batch size:
```bash
python PA/scripts/migrate_traceability_m2.py --config PA/config/config_tsl.yaml --batch-size 20000
```
- Override report path:
```bash
python PA/scripts/migrate_traceability_m2.py --config PA/config/config_tsl.yaml --report-file large_tool_results/m2_tsl_report.json
```

## Rollback
If validation fails and rollback is required, restore Neo4j from your backup snapshot and rerun dry-run checks before another apply attempt.
