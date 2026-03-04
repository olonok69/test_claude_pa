# V2E Run-Scoped Import Commands (TSL)

## Important behavior note

The current importer scopes by `RecommendationRun.run_id` when `--recommendation-run-id` is provided, but it does **not** exclude control-group visitors by default.

- Included: visitors in the selected run scope (from `CampaignDelivery` and/or `IS_RECOMMENDED` for that run)
- Not automatically excluded: `CampaignDelivery.status = withheld_control`

If control-group exclusion is required, add that rule before production write.

---

## Latest run ID used

- `tsl_engagement_20260224T195335Z_0166ba44`

## Dry-run command (from repo root: `/mnt/wolverine/home/samtukra/juan/repos/PA`)

```bash
/mnt/wolverine/home/samtukra/juan/repos/PA/.venv/bin/python PA/scripts/import_v2e_recommendations_to_neo4j.py \
  --config PA/config/config_tsl.yaml \
  --v2e-json PA/data/tsl/v2e_recommendations_4.json \
  --recommendation-run-id tsl_engagement_20260224T195335Z_0166ba44 \
  --dry-run
```

## Write command (same scope)

```bash
/mnt/wolverine/home/samtukra/juan/repos/PA/.venv/bin/python PA/scripts/import_v2e_recommendations_to_neo4j.py \
  --config PA/config/config_tsl.yaml \
  --v2e-json PA/data/tsl/v2e_recommendations_4.json \
  --recommendation-run-id tsl_engagement_20260224T195335Z_0166ba44
```

## Build unified recommendation JSON files for the same run

```bash
/mnt/wolverine/home/samtukra/juan/repos/PA/.venv/bin/python PA/scripts/unify_recommendations_with_v2e.py \
  --recommendation-run-id tsl_engagement_20260224T195335Z_0166ba44 \
  --recommendations-root PA/data/tsl/recommendations \
  --v2e-json PA/data/tsl/v2e_recommendations_4.json \
  --output-main-json PA/data/tsl/recommendations/visitor_recommendations_tsl_20260224_195335_unified.json \
  --output-control-json PA/data/tsl/recommendations/visitor_recommendations_tsl_20260224_195335_control_unified.json \
  --incidence-report PA/data/tsl/recommendations/unify_recommendations_incidence_report_20260224_195335.json \
  --unmatched-visitors-csv PA/data/tsl/recommendations/unmatched_visitors_not_found_in_v2e_20260224_195335.csv
```

---

## Post-write verification queries

### 1) Volume check

```cypher
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED_EXHIBITOR {run_id: "tsl_engagement_20260224T195335Z_0166ba44"}]->(e:Exhibitor)
RETURN
  count(r) AS relationships,
  count(DISTINCT v) AS visitors,
  count(DISTINCT e) AS exhibitors;
```

### 2) Scope integrity (should be 0)

```cypher
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED_EXHIBITOR {run_id: "tsl_engagement_20260224T195335Z_0166ba44"}]->(:Exhibitor)
WHERE NOT EXISTS {
  MATCH (rr:RecommendationRun {run_id: "tsl_engagement_20260224T195335Z_0166ba44"})
  MATCH (:CampaignDelivery)-[:FOR_RUN]->(rr)
  MATCH (:CampaignDelivery)-[:FOR_VISITOR]->(v)
}
RETURN count(r) AS relationships_outside_run_scope;
```

### 3) Metadata integrity

```cypher
MATCH ()-[r:IS_RECOMMENDED_EXHIBITOR {run_id: "tsl_engagement_20260224T195335Z_0166ba44"}]->()
RETURN
  count(r) AS total,
  sum(CASE WHEN coalesce(r.run_mode, "") = "" THEN 1 ELSE 0 END) AS missing_run_mode,
  sum(CASE WHEN coalesce(r.campaign_id, "") = "" THEN 1 ELSE 0 END) AS missing_campaign_id,
  sum(CASE WHEN coalesce(r.show, "") = "" THEN 1 ELSE 0 END) AS missing_show;
```

### 4) Control-group reconciliation (included vs withheld)

```cypher
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED_EXHIBITOR {run_id: "tsl_engagement_20260224T195335Z_0166ba44"}]->(:Exhibitor)
OPTIONAL MATCH (d:CampaignDelivery {run_id: "tsl_engagement_20260224T195335Z_0166ba44"})-[:FOR_VISITOR]->(v)
RETURN
  coalesce(d.status, "missing_delivery_status") AS delivery_status,
  count(r) AS relationships,
  count(DISTINCT v) AS visitors
ORDER BY relationships DESC;
```

---

## Files to deliver

### Core execution files
- `PA/scripts/import_v2e_recommendations_to_neo4j.py`
- `PA/scripts/unify_recommendations_with_v2e.py`
- `PA/config/config_tsl.yaml`
- `PA/data/tsl/v2e_recommendations_4.json`

### Validation runbook
- `docs/post_event_followup_pack/v2e_run_scoped_import_commands.md`

### Recommended evidence artifacts
- `PA/large_tool_results/tsl_recommendation_run_analysis_20260225_074631.json`
- `PA/large_tool_results/tsl_recommendation_run_analysis_20260225_074631.log`
- `PA/data/tsl/recommendations/visitor_recommendations_tsl_20260224_195335_unified.json`
- `PA/data/tsl/recommendations/visitor_recommendations_tsl_20260224_195335_control_unified.json`
- `PA/data/tsl/recommendations/unify_recommendations_incidence_report_20260224_195335.json`
- `PA/data/tsl/recommendations/unmatched_visitors_not_found_in_v2e_20260224_195335.csv`

### Follow-up tracking docs
- `docs/post_event_followup_pack/FOLLOWUP_CHANGELOG.md`
- `docs/post_event_followup_pack/post_event_day0_runsheet.md`
- `docs/post_event_followup_pack/post_event_handoff_2026-02-21.md`
