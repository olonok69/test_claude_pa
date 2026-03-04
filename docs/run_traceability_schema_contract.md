# M1: Run Traceability Schema Contract (Target)

## Status
Draft v1 — proposed for approval before migration.

## Scope
Applies to both campaign-producing modes:
- `personal_agendas`
- `engagement`

And to post-event analysis mode:
- `post_analysis` (reads/joins outcomes with campaign provenance)

---

## Design Principles
- Preserve lineage: never lose which run produced which recommendation.
- Keep analysis-friendly schema for Phase D.
- Be backward-compatible with current graph by adding fields and event entities.
- Keep migration idempotent and safe.

---

## Canonical IDs
- `run_id`: unique ID for each pipeline execution that writes recommendations.
- `campaign_id`: logical campaign identifier (may span one or more runs).
- `visitor_id`: canonical visitor ID (BadgeId).
- `session_id`: canonical session ID.
- `show`: event code (e.g., `tsl`).

---

## Target Model (minimum viable)

### 1) Run node
Label: `RecommendationRun`

Required properties:
- `run_id` (string, unique)
- `run_mode` (`personal_agendas` | `engagement`)
- `campaign_id` (string)
- `show` (string)
- `created_at` (datetime string)
- `pipeline_version` (string)
- `config_hash` (string, optional)
- `randomization_seed` (int/string, optional)
- `allocation_version` (string, optional)

### 2) Recommendation event relationship
Relationship: `(v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s:Sessions_this_year)`

Required properties:
- `run_id`
- `run_mode`
- `campaign_id`
- `show`
- `generated_at`
- `similarity_score`
- `control_group` (0/1)
- `control_group_type` (`personal_agendas` | `engagement` | null)

Optional:
- `source_step`
- `algorithm_version`

### 3) Delivery event node (recommended)
Label: `CampaignDelivery`

Required properties:
- `delivery_id` (unique)
- `run_id`
- `campaign_id`
- `run_mode`
- `visitor_id`
- `status` (`sent` | `withheld_control` | `failed` | `suppressed`)
- `timestamp`
- `show`

Optional:
- `channel`
- `failure_reason`

Relationships:
- `(d:CampaignDelivery)-[:FOR_VISITOR]->(v:Visitor_this_year)`
- `(d:CampaignDelivery)-[:FOR_RUN]->(rr:RecommendationRun)`

---

## Backward Compatibility / Legacy Mapping
For existing recommendation relationships without run metadata:
- set `run_id = "legacy_pre_traceability"`
- set `run_mode = "unknown"`
- set `campaign_id = "legacy"`
- keep existing score/timestamp when present

For existing visitor control flags:
- preserve as-is for historical audit
- going forward, treat control assignment as run-scoped metadata

---

## Constraints / Indexes (Cypher contract)
```cypher
// Run uniqueness
CREATE CONSTRAINT recommendation_run_id_unique IF NOT EXISTS
FOR (rr:RecommendationRun)
REQUIRE rr.run_id IS UNIQUE;

// Delivery uniqueness
CREATE CONSTRAINT campaign_delivery_id_unique IF NOT EXISTS
FOR (d:CampaignDelivery)
REQUIRE d.delivery_id IS UNIQUE;

// Lookup indexes
CREATE INDEX recommendation_run_mode_idx IF NOT EXISTS
FOR (rr:RecommendationRun)
ON (rr.run_mode);

CREATE INDEX recommendation_run_campaign_idx IF NOT EXISTS
FOR (rr:RecommendationRun)
ON (rr.campaign_id);

CREATE INDEX campaign_delivery_run_idx IF NOT EXISTS
FOR (d:CampaignDelivery)
ON (d.run_id);

CREATE INDEX campaign_delivery_visitor_idx IF NOT EXISTS
FOR (d:CampaignDelivery)
ON (d.visitor_id);
```

---

## Write-path Contract
All new recommendation writes must:
1. Upsert one `RecommendationRun` per execution.
2. Write `run_id`, `run_mode`, `campaign_id`, `show` onto each `IS_RECOMMENDED` relation.
3. Persist one `CampaignDelivery` record per visitor per run with status.
4. Never delete historical run-scoped records unless an explicit retention policy is applied.

---

## Phase D Query Expectations
This contract must enable:
- Run ledger by `run_id`/`campaign_id`.
- Visitor exposure timeline across runs.
- Causal cohorts (treatment/control) by run and campaign.
- Outcome joins to post-analysis attendance relationships.

---

## M1 Acceptance Criteria
- [ ] Field list approved by engineering + analytics.
- [ ] Constraints/indexes reviewed for target Neo4j version.
- [ ] Backward-compatibility mapping approved.
- [ ] Query examples for run ledger and exposure timeline validated on a sample graph.
- [ ] Migration readiness sign-off for M2.

---

## Open decisions (to finalize before M2)
1. Keep recommendation history on same relationship type with run properties vs create explicit `RecommendationEvent` nodes.
2. Exact retention policy (full history vs rolling window).
3. Whether engagement control is enabled in this cycle or staged for later.
