// M5 Delivery Ledger Verification Pack
// Usage in Neo4j Browser:
// :param run_id => 'your_run_id_here'
// :param campaign_id => 'optional_campaign_id'
// :param show => 'optional_show'

// 1) Delivery totals by status for run
MATCH (d:CampaignDelivery {run_id: $run_id})
RETURN d.status AS status, count(*) AS deliveries
ORDER BY deliveries DESC;

// 2) Duplicate delivery rows per visitor within run (should be zero)
MATCH (d:CampaignDelivery {run_id: $run_id})
WITH d.visitor_id AS visitor_id, count(*) AS c
WHERE visitor_id IS NOT NULL AND c > 1
RETURN visitor_id, c
ORDER BY c DESC;

// 3) Missing relationship integrity checks (should be zero)
MATCH (d:CampaignDelivery {run_id: $run_id})
WHERE NOT EXISTS { MATCH (d)-[:FOR_VISITOR]->(:Visitor_this_year) }
RETURN count(d) AS deliveries_without_for_visitor;

MATCH (d:CampaignDelivery {run_id: $run_id})
WHERE NOT EXISTS { MATCH (d)-[:FOR_RUN]->(:RecommendationRun {run_id: $run_id}) }
RETURN count(d) AS deliveries_without_for_run;

// 4) Optional campaign consistency check
MATCH (d:CampaignDelivery {run_id: $run_id})
WHERE $campaign_id IS NOT NULL AND trim(toString($campaign_id)) <> ''
  AND coalesce(d.campaign_id, '') <> trim(toString($campaign_id))
RETURN d.delivery_id AS delivery_id, d.visitor_id AS visitor_id, d.campaign_id AS observed_campaign_id
LIMIT 200;

// 5) Optional show consistency check
MATCH (d:CampaignDelivery {run_id: $run_id})
WHERE $show IS NOT NULL AND trim(toString($show)) <> ''
  AND coalesce(d.show, '') <> trim(toString($show))
RETURN d.delivery_id AS delivery_id, d.visitor_id AS visitor_id, d.show AS observed_show
LIMIT 200;

// 6) Recommended relationship coverage by delivery visitor (diagnostic)
MATCH (d:CampaignDelivery {run_id: $run_id})
OPTIONAL MATCH (:Visitor_this_year {BadgeId: d.visitor_id})-[r:IS_RECOMMENDED {run_id: $run_id}]->(:Sessions_this_year)
RETURN d.status AS status, count(d) AS visitors, sum(CASE WHEN r IS NULL THEN 1 ELSE 0 END) AS visitors_without_run_recommendations
ORDER BY visitors DESC;
