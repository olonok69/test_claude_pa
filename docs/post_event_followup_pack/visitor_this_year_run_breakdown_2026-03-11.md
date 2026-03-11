# Visitor_this_year Breakdown per RecommendationRun (TSL)

Date: 2026-03-11

Related tracking:
- For post-analysis exhibitor attendance counters (`assisted_exhibitor_this_year`) and latest run-scoped totals, see `docs/post_event_followup_pack/README.md` under `Latest status (2026-03-11)`.

## 1) Baseline breakdown (no suppression filter)

| run_id | run_mode | visitors_this_year |
|---|---|---:|
| tsl_engagement_20260219T205354Z_c3f8fb55 | engagement | 46,555 |
| tsl_personal_agendas_20260219T124351 | personal_agendas | 16,656 |
| tsl_personal_agendas_20260227T224725Z_37b21c42 | personal_agendas | 8,902 |
| tsl_post_analysis_20260310_151951Z_ccfa80c9 | post_analysis | 6,188 |

Total across runs (non-deduped): **78,301**

## 2) Engagement filtered variant (`suppressed_hubspot = '0'`)

Applied only to run `tsl_engagement_20260219T205354Z_c3f8fb55`:

- Filtered engagement visitors_this_year: **26,334**
- Baseline engagement visitors_this_year: **46,555**
- Delta: **-20,221**
- Relative change: **-43.44%**

## 3) Comparable table (other runs unchanged)

| run_id | run_mode | visitors_this_year |
|---|---|---:|
| tsl_engagement_20260219T205354Z_c3f8fb55 *(suppressed_hubspot='0')* | engagement | 26,334 |
| tsl_personal_agendas_20260219T124351 | personal_agendas | 16,656 |
| tsl_personal_agendas_20260227T224725Z_37b21c42 | personal_agendas | 8,902 |
| tsl_post_analysis_20260310_151951Z_ccfa80c9 | post_analysis | 6,188 |

Total across runs (non-deduped, filtered engagement variant): **58,080**

## 4) Query references

Baseline per-run breakdown:

```cypher
MATCH (rr:RecommendationRun)<-[:FOR_RUN]-(d:CampaignDelivery)-[:FOR_VISITOR]->(v:Visitor_this_year)
RETURN rr.run_id AS run_id, rr.run_mode AS run_mode, count(DISTINCT v) AS visitors_this_year
ORDER BY visitors_this_year DESC, run_id;
```

Filtered engagement count only:

```cypher
MATCH (:CampaignDelivery {run_id:'tsl_engagement_20260219T205354Z_c3f8fb55'})-[:FOR_VISITOR]->(v:Visitor_this_year)
WHERE coalesce(toString(v.suppressed_hubspot),'0')='0'
RETURN count(DISTINCT v) AS visitors_this_year;
```
