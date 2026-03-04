// M2 verification pack (run after migration)

// 1) No recommendation relationships should be missing run metadata
MATCH ()-[r:IS_RECOMMENDED]->()
RETURN
  count(r) AS total_recommendations,
  sum(CASE WHEN r.run_id IS NULL OR trim(toString(r.run_id)) = '' THEN 1 ELSE 0 END) AS missing_run_id,
  sum(CASE WHEN r.run_mode IS NULL OR trim(toString(r.run_mode)) = '' THEN 1 ELSE 0 END) AS missing_run_mode,
  sum(CASE WHEN r.campaign_id IS NULL OR trim(toString(r.campaign_id)) = '' THEN 1 ELSE 0 END) AS missing_campaign_id,
  sum(CASE WHEN r.show IS NULL OR trim(toString(r.show)) = '' THEN 1 ELSE 0 END) AS missing_show;

// 2) Legacy run should exist exactly once
MATCH (rr:RecommendationRun {run_id: 'legacy_pre_traceability'})
RETURN count(rr) AS legacy_run_nodes, rr.run_mode AS run_mode, rr.campaign_id AS campaign_id, rr.show AS show;

// 3) RecommendationRun uniqueness sanity check
MATCH (rr:RecommendationRun)
WITH rr.run_id AS run_id, count(*) AS c
WHERE run_id IS NOT NULL AND c > 1
RETURN run_id, c
ORDER BY c DESC;

// 4) CampaignDelivery uniqueness sanity check
MATCH (d:CampaignDelivery)
WITH d.delivery_id AS delivery_id, count(*) AS c
WHERE delivery_id IS NOT NULL AND c > 1
RETURN delivery_id, c
ORDER BY c DESC;

// 5) Legacy delivery coverage: every visitor with legacy recommendations has a legacy delivery
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(:Sessions_this_year)
WHERE r.run_id = 'legacy_pre_traceability'
WITH DISTINCT v
WHERE NOT EXISTS {
  MATCH (d:CampaignDelivery)-[:FOR_VISITOR]->(v)
  WHERE d.run_id = 'legacy_pre_traceability'
}
RETURN count(v) AS legacy_visitors_missing_delivery;

// 6) Optional breakdown by run/campaign
MATCH ()-[r:IS_RECOMMENDED]->()
RETURN r.run_id AS run_id, r.campaign_id AS campaign_id, r.run_mode AS run_mode, count(*) AS recs
ORDER BY recs DESC;
