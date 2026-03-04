# V2E Run Execution Log — 2026-02-25

## Purpose

Track the run-scoped V2E import work and evidence for TSL engagement run continuity.

## Scope

- Event: `tsl`
- Mode: `engagement`
- Run ID: `tsl_engagement_20260224T195335Z_0166ba44`
- V2E input: `PA/data/tsl/v2e_recommendations_4.json`

---

## Scripts involved

- `PA/scripts/import_v2e_recommendations_to_neo4j.py`
- `PA/scripts/analyze_tsl_recommendation_run.py`
- `PA/scripts/unify_recommendations_with_v2e.py` (optional; mainly for reconciliation/unified artifacts)

---

## Key implementation updates completed

1. Added run-scoped import support to V2E importer:
   - New flag: `--recommendation-run-id`
   - Scopes eligible visitors to the selected `RecommendationRun`
   - Writes `IS_RECOMMENDED_EXHIBITOR` with run metadata (`run_id`, `run_mode`, `campaign_id`, `show`)

2. Added recommendation run analyzer script:
   - Validates engagement theatre mapping rule from generated recommendation CSV
   - Outputs JSON + log evidence under `PA/large_tool_results/`

3. Added run-scoped support to unifier script (optional use path):
   - `PA/scripts/unify_recommendations_with_v2e.py` now accepts `--recommendation-run-id`

---

## Commands executed (successful path)

### A) Validate recommendation theatre rule (post-run)

```bash
python scripts/analyze_tsl_recommendation_run.py --config config/config_tsl.yaml
```

Result summary:
- `STATUS: PASS`
- `rows_total=253560`
- `rows_violating_rule=0`

Artifacts:
- `PA/large_tool_results/tsl_recommendation_run_analysis_20260225_074631.json`
- `PA/large_tool_results/tsl_recommendation_run_analysis_20260225_074631.log`

### B) Run-scoped V2E import (write)

```bash
python scripts/import_v2e_recommendations_to_neo4j.py \
  --config config/config_tsl.yaml \
  --v2e-json data/tsl/v2e_recommendations_4.json \
  --recommendation-run-id tsl_engagement_20260224T195335Z_0166ba44
```

Result summary:
- `Exhibitor nodes upserted: 439`
- `Visitor->Exhibitor relationships merged: 145930`
- `Visitors missing in Neo4j: 8729`
- `Visitors missing badgeID in JSON: 0`
- `Exhibitors missing uuid in JSON: 0`
- `Malformed exhibitor rows: 0`

---

## Neo4j verification checks and outputs

### 1) Volume check

Query output:
- `relationships: 145930`
- `visitors: 29186`
- `exhibitors: 439`

### 2) Scope integrity

Query output:
- `relationships_outside_run_scope: 0`

### 3) Metadata integrity

Query output:
- `total: 145930`
- `missing_run_mode: 0`
- `missing_campaign_id: 0`
- `missing_show: 0`

Interpretation:
- Run-scoped import succeeded and metadata is fully populated.

---

## Operational notes

- Current importer includes both sent and withheld-control visitors unless an explicit exclusion rule is added.
- `PA/scripts/unify_recommendations_with_v2e.py` is optional for this flow and typically used for unified/reconciliation artifacts rather than core Neo4j import.

---

## Delivery bundle (current)

- `docs/post_event_followup_pack/v2e_run_scoped_import_commands.md`
- `docs/post_event_followup_pack/v2e_run_execution_log_2026-02-25.md`
- `PA/scripts/import_v2e_recommendations_to_neo4j.py`
- `PA/scripts/analyze_tsl_recommendation_run.py`
- `PA/scripts/unify_recommendations_with_v2e.py`
- `PA/large_tool_results/tsl_recommendation_run_analysis_20260225_074631.json`
- `PA/large_tool_results/tsl_recommendation_run_analysis_20260225_074631.log`
- `PA/data/tsl/v2e_recommendations_4.json`
