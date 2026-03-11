# Prompt: Post-Show Analysis Report — Full Technical Version (Generic Template)

## Instructions for Agentic Report Generator

You are a **Senior Data Analyst** generating the **POST-SHOW** recommendation system analysis report for the specified event.

This prompt covers the **complete event journey**: all pre-show campaigns (personal agendas + optional engagement), optional incremental runs, and the actual post-show attendance outcomes. It is designed for use after the event, once badge scan data has been loaded into Neo4j via `post_analysis` mode.

---

## CONTEXT VARIABLES (To be filled for each event)

### Configuration File Mappings
Each placeholder should be replaced with values from the event's configuration YAML file and from Neo4j:

- **Event**: `[EVENT_NAME]` → Use `event.main_event_name` from config
- **Show Code**: `[SHOW_CODE]` → Use `event.name` or `neo4j.show_name` from config
- **Year**: `[YEAR]` → Use `event.year` from config
- **Database**: Neo4j `[ENVIRONMENT]` → Specify environment (Production/Test/Dev)
- **Database Connection**: `[DATABASE_CONNECTION]` → Use connection string (e.g., "neo4j-prod")
- **Configuration File**: `[CONFIG_FILE_PATH]` → Path to event config file
- **Analysis Date**: `[CURRENT_DATE]` → Current date of analysis
- **Pre-Show Report Path**: `[PRE_SHOW_REPORT_PATH]` → From `pre_show_report` in reporting_pipeline.yaml profile
- **Control Group %**: `[CONTROL_GROUP_PCT]` → From `recommendation.control_group.percentage` in config
- **Control Group Skew Note**: `[CONTROL_SKEW_NOTE]` → From pre-show report demographic balance analysis

### Quick Configuration Reference Table

| Placeholder | Config Path | Example Values | Usage |
|-------------|------------|----------------|-------|
| `[SHOW_CODE]` | `event.name` or `neo4j.show_name` | "lva", "cpcn", "tsl" | Query filtering |
| `[EVENT_NAME]` | `event.main_event_name` | "London Vet Show", "Tech Show London" | Report title |
| `[YEAR]` | `event.year` | 2025, 2026 | Reference |
| `[CONTROL_GROUP_PCT]` | `recommendation.control_group.percentage` | 5, 15 | A/B test design |
| `[MAX_RECOMMENDATIONS]` | `recommendation.max_recommendations` | 10 | Target comparison |
| `[MIN_SIMILARITY_SCORE]` | `recommendation.min_similarity_score` | 0.3 | Score threshold |
| `[SIMILARITY_ATTRIBUTES]` | Keys from `recommendation.similarity_attributes` | "sector", "job_role" | Segment analysis |
| `[PA_INITIAL_RUN_ID]` | Queried from `RecommendationRun` | auto-generated ID | Query filter |
| `[ENGAGEMENT_RUN_ID]` | Queried from `RecommendationRun` | auto-generated ID | Query filter |
| `[PA_INCREMENT_RUN_ID]` | Queried from `RecommendationRun` | auto-generated ID | Query filter |

---

## DATABASE SCHEMA

Connected to Neo4j with:
- `Visitor_this_year` nodes (current event registrations; `show` property = `[SHOW_CODE]`)
- `Visitor_last_year_main` nodes (main event prior year attendees — renamed from `Visitor_last_year_bva`)
- `Visitor_last_year_secondary` nodes (secondary event prior year attendees — renamed from `Visitor_last_year_lva`)
- `Sessions_this_year` nodes (current event sessions)
- `Stream` nodes (session categories/topics)
- `Exhibitor` nodes (exhibition stand entities)
- `RecommendationRun` nodes (one per pipeline execution; properties: `run_id`, `run_mode`, `campaign_id`, `show`, `created_at`)
- `CampaignDelivery` nodes (delivery record per visitor per run; properties: `run_id`, `visitor_id`, `status`, `run_mode`, `campaign_id`, `show`)
- `IS_RECOMMENDED` relationships (session recommendations; properties: `run_id`, `run_mode`, `control_group`, `similarity_score`)
- `IS_RECOMMENDED_EXHIBITOR` relationships (exhibitor recommendations; properties: `run_id`, `run_mode`)
- `assisted_session_this_year` relationships (post-show: actual session attendance)
- `registered_to_show` relationships (post-show: venue entry scans)
- `Same_Visitor` relationships (linking current to past visitor nodes)
- `attended_session` relationships (historical session attendance from prior years)
- `HAS_STREAM` relationships (session → stream assignments)
- `FOR_VISITOR` relationships (`CampaignDelivery` → `Visitor_this_year`)
- `FOR_RUN` relationships (`CampaignDelivery` → `RecommendationRun`)

**Note on node label naming:** `Visitor_last_year_main` and `Visitor_last_year_secondary` replace legacy `Visitor_last_year_bva` / `Visitor_last_year_lva`. Use the generic labels in all queries unless the schema shows otherwise.

---

## PRE-REQUISITES — Data Readiness Check

Before generating the report, verify the following data is available:

```cypher
// Check 1: Post-show attendance relationships exist
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
RETURN count(a) AS session_attendance_records, count(DISTINCT v) AS unique_attendees
```

```cypher
// Check 2: Venue entry scan relationships exist
MATCH (v:Visitor_this_year)-[r:registered_to_show]->()
WHERE v.show = '[SHOW_CODE]'
RETURN count(DISTINCT v) AS venue_attendees
```

```cypher
// Check 3: All RecommendationRun nodes for this show
MATCH (rr:RecommendationRun)
WHERE rr.show = '[SHOW_CODE]'
RETURN rr.run_id, rr.run_mode, rr.campaign_id, rr.created_at
ORDER BY rr.created_at
```

**If `session_attendance_records = 0`** → post-analysis pipeline has not been run. Stop here. Set `mode: "post_analysis"` in the event config file and run the pipeline first.

**From Query 3 output, assign run IDs to placeholders:**
- `[PA_INITIAL_RUN_ID]` → the earliest `personal_agendas` run_id
- `[ENGAGEMENT_RUN_ID]` → the `engagement` run_id (if applicable)
- `[PA_INCREMENT_RUN_ID]` → any subsequent `personal_agendas` run_id (if applicable)

---

## TASK 0: IDENTIFY SESSIONS TO EXCLUDE (Special / Admin Events)

Before all metric calculations, identify non-content sessions to exclude from hit rate and conversion analysis.

```cypher
// Administrative or placeholder sessions by title pattern
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]' OR s.show IS NULL
  AND (toLower(s.title) CONTAINS 'closing'
    OR toLower(s.title) CONTAINS 'opening'
    OR toLower(s.title) CONTAINS 'remarks'
    OR toLower(s.title) CONTAINS 'welcome'
    OR toLower(s.title) CONTAINS 'networking'
    OR toLower(s.title) CONTAINS 'placeholder'
    OR s.title IS NULL)
RETURN s.session_id, s.title, s.stream
ORDER BY s.title
```

```cypher
// Sessions with anomalously high recommendation count relative to others
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
WITH s, count(r) AS rec_count
ORDER BY rec_count DESC
LIMIT 10
RETURN s.session_id, s.title, s.stream, rec_count
```

**Build the exclusion list `[EXCLUDED_SESSION_IDS]` and use it in all subsequent Tasks.**
Document the reasoning for each excluded session.

---

## TASK 1: CAMPAIGN JOURNEY & RUN LEDGER

Build the complete pre-show recommendation journey to frame the post-show analysis.

**Query 1.1: Full Run Ledger**
```cypher
MATCH (rr:RecommendationRun)
WHERE rr.show = '[SHOW_CODE]'
OPTIONAL MATCH (d:CampaignDelivery)-[:FOR_RUN]->(rr)
RETURN
  rr.run_id,
  rr.run_mode,
  rr.campaign_id,
  rr.created_at,
  count(CASE WHEN d.status = 'sent' THEN 1 END) AS sent,
  count(CASE WHEN d.status = 'withheld_control' THEN 1 END) AS withheld_control,
  count(d) AS total_eligible
ORDER BY rr.created_at
```

**Query 1.2: IS_RECOMMENDED Counts per Run**
```cypher
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
RETURN r.run_id, r.run_mode, count(r) AS total_recs, count(DISTINCT v) AS visitors_covered
ORDER BY r.run_id
```

**Query 1.3: V2E Exhibitor Recommendations (if applicable)**
```cypher
// Check if IS_RECOMMENDED_EXHIBITOR exists for this show
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED_EXHIBITOR]->(e:Exhibitor)
WHERE v.show = '[SHOW_CODE]'
RETURN r.run_id, r.run_mode,
       count(r) AS v2e_recs,
       count(DISTINCT v) AS v2e_visitors,
       count(DISTINCT e) AS exhibitors_covered
ORDER BY r.run_id
```

**Output Requirements:**
- Campaign Journey Summary table: run ID, mode, campaign, date, sent, withheld, total
- Narrative framing the campaign sequence (engagement → PA initial → PA increment, as applicable)
- Note any runs not followed by a delivery (e.g., legacy records)
- V2E summary if relationships exist

---

## TASK 2: VISITOR REGISTRATION & ATTENDANCE FUNNEL

**Query 2.1: Registration Final State**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
RETURN
  count(v) AS total_registered,
  sum(CASE WHEN v.control_group = 1 THEN 1 ELSE 0 END) AS control_group_count,
  sum(CASE WHEN v.control_group = 0 THEN 1 ELSE 0 END) AS treatment_group_count,
  sum(CASE WHEN v.control_group IS NULL THEN 1 ELSE 0 END) AS unassigned_count,
  sum(CASE WHEN v.has_recommendation = '1' THEN 1 ELSE 0 END) AS with_recommendations
```

**Query 2.2: New vs Returning Visitors**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
OPTIONAL MATCH (v)-[sr:Same_Visitor]->()
WITH v, collect(sr.type) AS return_types
RETURN
  CASE
    WHEN size(return_types) = 0 THEN 'New'
    WHEN size(return_types) = 1 THEN return_types[0]
    ELSE 'Multiple (both events)'
  END AS visitor_type,
  count(v) AS visitor_count
ORDER BY visitor_count DESC
```

**Query 2.3: Venue Attendance Rate**
```cypher
MATCH (v:Visitor_this_year)-[:registered_to_show]->()
WHERE v.show = '[SHOW_CODE]'
WITH count(DISTINCT v) AS venue_attendees
MATCH (v2:Visitor_this_year) WHERE v2.show = '[SHOW_CODE]'
RETURN venue_attendees,
       count(v2) AS total_registered,
       round(toFloat(venue_attendees) / count(v2) * 100, 1) AS attendance_rate_pct
```

**Query 2.4: Session Attendance**
```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
RETURN count(DISTINCT v) AS session_attendees,
       count(a) AS total_session_scans
```

**Query 2.5: Funnel by Treatment / Control Group**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]' AND v.control_group IN [0, 1]
OPTIONAL MATCH (v)-[a:assisted_session_this_year]->(s:Sessions_this_year)
  WHERE (s.show = '[SHOW_CODE]' OR s.show IS NULL)
    AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
RETURN
  CASE v.control_group WHEN 1 THEN 'Control (withheld)' ELSE 'Treatment (sent)' END AS group_name,
  count(DISTINCT v) AS registered,
  count(DISTINCT CASE WHEN EXISTS((v)-[:registered_to_show]->()) THEN v END) AS attended_venue,
  count(DISTINCT CASE WHEN a IS NOT NULL THEN v END) AS attended_sessions
ORDER BY v.control_group
```

**Query 2.6: Late Registrant Impact**
```cypher
// Visitors registered after the final PA run — no recommendations received
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (v.has_recommendation IS NULL OR v.has_recommendation = '0')
RETURN count(v) AS late_registrants_without_recs
```

**Output Requirements:**
- Full funnel table: registered → venue → sessions, by treatment/control and new/returning
- Late registrant count and their attendance rate vs. those with recommendations
- Note any known demographic skew in control group from pre-show report

---

## TASK 3: A/B TEST — PERSONAL AGENDAS CAMPAIGN (PRIMARY CAUSAL ANALYSIS)

**Background:**
- Treatment group received personal agenda email (IS_RECOMMENDED with `control_group = 0`)
- Control group (`control_group = 1`) had recommendations generated but not sent
- Control group size: `[CONTROL_GROUP_PCT]%` of eligible visitors
- Note any demographic imbalance from `[CONTROL_SKEW_NOTE]` in the pre-show report

### 3.1 Session-Level Hit Rate: Treatment vs Control

```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]' AND v.control_group IN [0, 1]
OPTIONAL MATCH (v)-[a:assisted_session_this_year]->(s:Sessions_this_year)
  WHERE (s.show = '[SHOW_CODE]' OR s.show IS NULL)
    AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(s)
WITH v.control_group AS ctrl,
     count(a) AS total_attended,
     count(CASE WHEN r IS NOT NULL THEN 1 END) AS attended_recommended
RETURN
  CASE ctrl WHEN 1 THEN 'Control' ELSE 'Treatment' END AS group_name,
  sum(total_attended) AS sessions_attended,
  sum(attended_recommended) AS sessions_hit,
  round(100.0 * sum(attended_recommended) / sum(total_attended), 2) AS session_hit_rate_pct
ORDER BY ctrl
```

### 3.2 Visitor-Level Hit Rate: Treatment vs Control

```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND v.control_group IN [0, 1]
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended_sessions
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended_sessions
WITH v.control_group AS ctrl, v,
     CASE WHEN count(rec) > 0 THEN 1 ELSE 0 END AS had_hit
RETURN
  CASE ctrl WHEN 1 THEN 'Control' ELSE 'Treatment' END AS group_name,
  count(v) AS session_attendees,
  sum(had_hit) AS visitors_with_hit,
  round(100.0 * sum(had_hit) / count(v), 2) AS visitor_hit_rate_pct
ORDER BY ctrl
```

### 3.3 Recommendation Lift (Absolute & Relative)

```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND v.control_group IN [0, 1]
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(s)
WITH v.control_group AS ctrl,
     count(a) AS attended,
     count(CASE WHEN r IS NOT NULL THEN 1 END) AS hits
WITH ctrl, sum(attended) AS total_attended, sum(hits) AS total_hits,
     100.0 * sum(hits) / sum(attended) AS hit_rate
WITH collect({flag: ctrl, rate: hit_rate}) AS rates
WITH
  [x IN rates WHERE x.flag = 0][0].rate AS treatment_rate,
  [x IN rates WHERE x.flag = 1][0].rate AS control_rate
RETURN
  round(treatment_rate, 2) AS treatment_hit_rate_pct,
  round(control_rate, 2) AS organic_hit_rate_pct,
  round(treatment_rate - control_rate, 2) AS absolute_lift_pp,
  round(100.0 * (treatment_rate - control_rate) / control_rate, 2) AS relative_lift_pct
```

### 3.4 Segmented Lift: New vs Returning Visitors

**Required** if pre-show report documented a demographic skew in the control group.

```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND v.control_group IN [0, 1]
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended_sessions
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended_sessions
OPTIONAL MATCH (v)-[:Same_Visitor]->()
WITH v.control_group AS ctrl,
     CASE WHEN EXISTS((v)-[:Same_Visitor]->()) THEN 'Returning' ELSE 'New' END AS visitor_type,
     v,
     CASE WHEN count(rec) > 0 THEN 1 ELSE 0 END AS had_hit
RETURN visitor_type,
  CASE ctrl WHEN 1 THEN 'Control' ELSE 'Treatment' END AS group_name,
  count(v) AS attendees,
  sum(had_hit) AS with_hit,
  round(100.0 * sum(had_hit) / count(v), 2) AS visitor_hit_rate_pct
ORDER BY visitor_type, ctrl
```

### 3.5 Segmented Lift by Key Similarity Attribute

Run for the highest-weight attribute from `recommendation.similarity_attributes`:

```cypher
// Replace [PRIMARY_SIMILARITY_ATTRIBUTE] with the highest-weight attribute from config
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND v.control_group IN [0, 1]
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended_sessions
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended_sessions
WITH v.control_group AS ctrl,
     v.[PRIMARY_SIMILARITY_ATTRIBUTE] AS segment,
     v,
     CASE WHEN count(rec) > 0 THEN 1 ELSE 0 END AS had_hit
WHERE segment IS NOT NULL AND segment <> 'NA'
RETURN segment,
  CASE ctrl WHEN 1 THEN 'Control' ELSE 'Treatment' END AS group_name,
  count(v) AS attendees,
  sum(had_hit) AS with_hit,
  round(100.0 * sum(had_hit) / count(v), 2) AS visitor_hit_rate_pct
ORDER BY segment, ctrl
LIMIT 30
```

**Output Requirements:**
- A/B test results scorecard: treatment rate, organic rate, absolute lift (pp), relative lift (%), z-score, p-value, 95% confidence interval
- Segmented results (new vs returning, primary attribute) clearly labelled
- Statistical significance determination (two-proportion z-test: if |z| > 1.96, p < 0.05)
- Formula reminder: `z = (p̂₁ - p̂₂) / √[p̂(1-p̂)(1/n₁ + 1/n₂)]`; `CI = (p̂₁ - p̂₂) ± 1.96 × √[p̂₁(1-p̂₁)/n₁ + p̂₂(1-p̂₂)/n₂]`
- If pre-show control group skew was noted, explain its effect on the organic rate

---

## TASK 4: A/B TEST — ENGAGEMENT CAMPAIGN (if applicable)

*Skip this task if no engagement run exists for this event (Query 1.1 returns no engagement run).*

**Background:** Engagement campaign targets prior-year attendees. Control assignment is stored via `CampaignDelivery.status = 'withheld_control'` for run `[ENGAGEMENT_RUN_ID]`.

**Query 4.1: Engagement Session-Level Hit Rate**
```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[ENGAGEMENT_RUN_ID]'}]->(s)
OPTIONAL MATCH (d:CampaignDelivery {run_id: '[ENGAGEMENT_RUN_ID]'})-[:FOR_VISITOR]->(v)
WITH
  CASE d.status WHEN 'withheld_control' THEN 1 ELSE 0 END AS eng_ctrl,
  count(a) AS attended,
  count(CASE WHEN r IS NOT NULL THEN 1 END) AS hits
WHERE d IS NOT NULL
RETURN
  CASE eng_ctrl WHEN 1 THEN 'Engagement Control' ELSE 'Engagement Treatment' END AS group_name,
  sum(attended) AS total_attended,
  sum(hits) AS total_hits,
  round(100.0 * sum(hits) / sum(attended), 2) AS hit_rate_pct
ORDER BY eng_ctrl
```

**Query 4.2: Engagement Visitor-Level Hit Rate**
```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended_sessions
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[ENGAGEMENT_RUN_ID]'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended_sessions
OPTIONAL MATCH (d:CampaignDelivery {run_id: '[ENGAGEMENT_RUN_ID]'})-[:FOR_VISITOR]->(v)
WHERE d IS NOT NULL
WITH
  CASE d.status WHEN 'withheld_control' THEN 1 ELSE 0 END AS eng_ctrl,
  v,
  CASE WHEN count(rec) > 0 THEN 1 ELSE 0 END AS had_hit
RETURN
  CASE eng_ctrl WHEN 1 THEN 'Engagement Control' ELSE 'Engagement Treatment' END AS group_name,
  count(v) AS attendees,
  sum(had_hit) AS visitors_with_hit,
  round(100.0 * sum(had_hit) / count(v), 2) AS visitor_hit_rate_pct
ORDER BY eng_ctrl
```

**Output Requirements:**
- Engagement A/B results table (treatment rate, organic rate, lift)
- Note that engagement targets returning visitors — organic rates are typically higher than PA
- Compare engagement lift vs PA lift; highlight cross-campaign differences

---

## TASK 5: SESSION HIT RATE & CONVERSION ANALYSIS

### 5.1 Overall Session-Level Hit Rate (All Visitors)

```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(s)
RETURN
  count(a) AS total_attended,
  count(CASE WHEN r IS NOT NULL THEN 1 END) AS attended_recommended,
  round(100.0 * count(CASE WHEN r IS NOT NULL THEN 1 END) / count(a), 2) AS session_hit_rate_pct
```

### 5.2 Top Recommended Sessions vs Actual Attendance

```cypher
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH s, count(DISTINCT v) AS rec_count
OPTIONAL MATCH (v2:Visitor_this_year)-[a:assisted_session_this_year]->(s)
WITH s, rec_count, count(DISTINCT v2) AS actual_attendance
RETURN
  s.session_id, s.title, s.stream,
  rec_count AS times_recommended,
  actual_attendance,
  CASE WHEN rec_count > 0 THEN round(toFloat(actual_attendance) / rec_count * 100, 1) ELSE 0 END AS conversion_pct
ORDER BY rec_count DESC
LIMIT 20
```

### 5.3 Under-Recommended Popular Sessions (Missed Opportunities)

```cypher
// Sessions with high actual attendance but low recommendation counts
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH s, count(DISTINCT v) AS actual_attendance
OPTIONAL MATCH (v2:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(s)
WITH s, actual_attendance, count(DISTINCT v2) AS rec_count
WHERE actual_attendance >= 20
RETURN
  s.session_id, s.title, s.stream,
  actual_attendance,
  rec_count AS times_recommended,
  CASE WHEN rec_count > 0 THEN round(toFloat(actual_attendance) / rec_count * 100, 1) ELSE null END AS conversion_pct
ORDER BY actual_attendance DESC
LIMIT 20
```

### 5.4 Best Converting Sessions (Minimum 30 Recommendations)

```cypher
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH s, count(DISTINCT v) AS rec_count
WHERE rec_count >= 30
OPTIONAL MATCH (v2:Visitor_this_year)-[a:assisted_session_this_year]->(s)
WITH s, rec_count, count(DISTINCT v2) AS actual_attendance
RETURN s.session_id, s.title, s.stream, rec_count, actual_attendance,
       round(toFloat(actual_attendance) / rec_count * 100, 1) AS conversion_pct
ORDER BY conversion_pct DESC
LIMIT 20
```

### 5.5 Sessions Never Attended

```cypher
MATCH (s:Sessions_this_year)
WHERE (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
  AND NOT EXISTS((v:Visitor_this_year)-[:assisted_session_this_year]->(s))
OPTIONAL MATCH (v2:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(s)
WHERE v2.show = '[SHOW_CODE]'
RETURN s.session_id, s.title, s.stream, count(r) AS times_recommended
ORDER BY times_recommended DESC
```

**Output Requirements:**
- Overall session hit rate
- Top recommended vs attended table (flag sessions with conversion > 200% as under-recommended)
- Under-recommended popular sessions — these are **missed opportunities** for next event
- Best converters table
- Zero-attendance sessions list

---

## TASK 6: VISITOR-LEVEL PERFORMANCE ANALYSIS

**Query 6.1: Overall Visitor Hit Rate**
```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended_sessions
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended_sessions
WITH v, CASE WHEN count(rec) > 0 THEN 1 ELSE 0 END AS had_hit
RETURN
  count(v) AS total_session_attendees,
  sum(had_hit) AS visitors_with_hit,
  round(100.0 * sum(had_hit) / count(v), 2) AS visitor_hit_rate_pct
```

**Query 6.2: Sessions per Attendee Distribution**
```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, count(a) AS sessions_attended
RETURN
  count(v) AS total_attendees,
  avg(sessions_attended) AS avg_sessions,
  min(sessions_attended) AS min_sessions,
  max(sessions_attended) AS max_sessions,
  percentileCont(sessions_attended, 0.25) AS p25,
  percentileCont(sessions_attended, 0.5) AS median,
  percentileCont(sessions_attended, 0.75) AS p75
```

**Query 6.3: Visitors with Highest Hit Counts (distribution)**
```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended_sessions, count(a) AS sessions_attended
MATCH (v)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended_sessions
WITH v, sessions_attended, count(DISTINCT rec) AS hits
RETURN hits, count(v) AS visitor_count
ORDER BY hits DESC
LIMIT 10
```

**Output Requirements:**
- Overall visitor-level hit rate vs benchmarks from previous events (reference `[PRE_SHOW_REPORT_PATH]`)
- Sessions-per-attendee distribution table
- Hit count distribution — understand depth of engagement

---

## TASK 7: STREAM-LEVEL ANALYSIS

**Query 7.1: Recommendations vs Attendance by Stream**
```cypher
MATCH (s:Sessions_this_year)-[:HAS_STREAM]->(st:Stream)
WHERE s.show = '[SHOW_CODE]' AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(s)
WHERE v.show = '[SHOW_CODE]'
OPTIONAL MATCH (v2:Visitor_this_year)-[a:assisted_session_this_year]->(s)
WHERE v2.show = '[SHOW_CODE]'
RETURN st.stream AS stream,
       count(DISTINCT s) AS sessions,
       count(DISTINCT r) AS total_recs,
       count(DISTINCT a) AS total_attendances,
       CASE WHEN count(DISTINCT r) > 0
            THEN round(toFloat(count(DISTINCT a)) / count(DISTINCT r) * 100, 1)
            ELSE 0 END AS conversion_pct
ORDER BY total_recs DESC
```

**Query 7.2: Most Attended Streams**
```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)-[:HAS_STREAM]->(st:Stream)
WHERE v.show = '[SHOW_CODE]' AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
RETURN st.stream AS stream,
       count(DISTINCT v) AS unique_attendees,
       count(a) AS total_scans
ORDER BY total_scans DESC
```

**Output Requirements:**
- Stream performance table: sessions, recommendations, attendance, conversion %
- Identify over-recommended vs under-recommended streams relative to actual demand
- Check alignment between stream weights in config and actual attendance patterns

---

## TASK 8: V2E EXHIBITOR RECOMMENDATIONS (if applicable)

*First check whether exhibitor visit data exists in Neo4j.*

**Query 8.1: Check Exhibitor Visit Data Availability**
```cypher
MATCH (v:Visitor_this_year)-[r:visited_exhibitor_this_year]->(e:Exhibitor)
WHERE v.show = '[SHOW_CODE]'
RETURN count(r) AS exhibitor_visits, count(DISTINCT v) AS visitors_who_visited_stands
LIMIT 1
```

**If exhibitor visit data exists, run:**

**Query 8.2: V2E Hit Rate**
```cypher
MATCH (v:Visitor_this_year)-[:visited_exhibitor_this_year]->(e:Exhibitor)
WHERE v.show = '[SHOW_CODE]'
WITH v, collect(DISTINCT e.uuid) AS visited_exhibitors
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED_EXHIBITOR]->(rec_e:Exhibitor)
WHERE rec_e.uuid IN visited_exhibitors
WITH v,
     size(visited_exhibitors) AS stands_visited,
     count(DISTINCT rec_e) AS recommended_stands_visited,
     CASE WHEN count(DISTINCT rec_e) > 0 THEN 1 ELSE 0 END AS had_hit
RETURN
  count(v) AS visitors_who_visited_stands,
  sum(had_hit) AS visitors_with_v2e_hit,
  round(100.0 * sum(had_hit) / count(v), 2) AS v2e_visitor_hit_rate_pct,
  avg(stands_visited) AS avg_stands_visited
```

**If exhibitor visit data does not exist:**
Document that V2E performance measurement is deferred. Reference pre-show V2E coverage statistics from `[PRE_SHOW_REPORT_PATH]`.

**Output Requirements:**
- V2E hit rate if data available
- Or: deferred note with pre-show V2E coverage reference
- Comparison vs session recommendation hit rates (is V2E more or less effective?)

---

## TASK 9: PRE-SHOW PREDICTIONS VS POST-SHOW REALITY

Compare key predictions from the pre-show report at `[PRE_SHOW_REPORT_PATH]` against actual outcomes.

**Pre-show report checklist — extract these values before filling the table:**
- Expected visitor-level hit rate (benchmark from prior events)
- Expected absolute lift
- Predicted control group organic rate
- Any flagged concentration risks
- Any flagged data quality warnings

| Prediction | Pre-Show Expectation | Actual Result | Verdict |
|------------|---------------------|---------------|---------|
| Visitor-level hit rate | `[FROM PRE-SHOW REPORT]` | `[FILL]` | ✅/⚠️/🔴 |
| Control group organic rate | `[FROM PRE-SHOW REPORT]` | `[FILL]` | ✅/⚠️/🔴 |
| Absolute recommendation lift | `[FROM PRE-SHOW REPORT]` | `[FILL]` | ✅/⚠️/🔴 |
| Statistical significance | target p < 0.05 | `[FILL]` | ✅/⚠️/🔴 |
| Late registrant higher engagement | expected yes | `[FILL]` | ✅/⚠️/🔴 |
| Top stream by actual attendance | `[FROM PRE-SHOW REPORT]` | `[FILL]` | ✅/⚠️/🔴 |
| Any concentration concern pre-show | `[FROM PRE-SHOW REPORT]` | `[FILL]` | ✅/⚠️/🔴 |
| Data quality impact | `[FROM PRE-SHOW REPORT]` | `[FILL]` | ✅/⚠️/🔴 |

**Output Requirements:**
- Complete prediction/reality table
- For each 🔴 discrepancy: 2-3 sentence root cause analysis
- For each ✅ accurate prediction: brief confirmation note

---

## TASK 10: DATA QUALITY RETROSPECTIVE

**Query 10.1: Attribute Fill Rates for Session Attendees**
```cypher
// Run for each key attribute from recommendation.similarity_attributes
MATCH (v:Visitor_this_year)-[:assisted_session_this_year]->(:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
WITH DISTINCT v
RETURN
  count(v) AS session_attendees,
  round(100.0 * count(CASE WHEN v.[ATTRIBUTE_1] IS NOT NULL
    AND v.[ATTRIBUTE_1] <> 'NA' THEN 1 END) / count(v), 1) AS attr1_fill_pct,
  round(100.0 * count(CASE WHEN v.[ATTRIBUTE_2] IS NOT NULL
    AND v.[ATTRIBUTE_2] <> 'NA' THEN 1 END) / count(v), 1) AS attr2_fill_pct
```

**Query 10.2: Hit Rate by Profile Completeness**
```cypher
// Visitors with all attributes vs sparse profiles — compare hit rates
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended_sessions
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended_sessions
WITH v,
  CASE WHEN count(rec) > 0 THEN 1 ELSE 0 END AS had_hit,
  // Count non-null, non-NA attributes (adjust attribute list per config)
  (CASE WHEN v.[ATTRIBUTE_1] IS NOT NULL AND v.[ATTRIBUTE_1] <> 'NA' THEN 1 ELSE 0 END
   + CASE WHEN v.[ATTRIBUTE_2] IS NOT NULL AND v.[ATTRIBUTE_2] <> 'NA' THEN 1 ELSE 0 END) AS filled_attrs
RETURN
  CASE WHEN filled_attrs >= 2 THEN 'Complete profile' ELSE 'Sparse profile' END AS profile_type,
  count(v) AS visitors,
  sum(had_hit) AS with_hit,
  round(100.0 * sum(had_hit) / count(v), 2) AS hit_rate_pct
ORDER BY profile_type
```

**Output Requirements:**
- Attribute fill rates for the session-attending population vs. all registrants (pre-show comparison)
- Hit rate difference between complete and sparse profiles (validates data quality hypothesis)
- Specific recommendations for improving low fill-rate attributes

---

## TASK 11: ALGORITHM ASSESSMENT & GRADE

Score the recommendation system on a 0–100 scale. Compare against the pre-show grade in `[PRE_SHOW_REPORT_PATH]`.

**Configuration source:** `recommendation.similarity_attributes` weights from config.

| Dimension | Weight | Pre-Show Score | Post-Show Score | Notes |
|-----------|--------|---------------|-----------------|-------|
| **Coverage** | 20% | `[FROM PRE-SHOW]` | `[FILL]` | % visitors with recs + late registrants |
| **Hit Rate Quality** | 25% | N/A (pre-show) | `[FILL]` | Treatment rate vs benchmark |
| **Causal Lift** | 20% | N/A (pre-show) | `[FILL]` | Statistically significant lift |
| **Calibration** | 15% | `[FROM PRE-SHOW]` | `[FILL]` | Concentration + under-rec issues |
| **Data Quality** | 10% | `[FROM PRE-SHOW]` | `[FILL]` | Weighted attribute fill rate |
| **Engagement** | 10% | N/A (pre-show) | `[FILL]` | Engagement campaign performance |

**Scoring guide:**
- 90–100: Outstanding — exceeds targets on all dimensions
- 80–89: Good — minor issues, system performing well
- 70–79: Adequate — several improvement areas, no critical failures
- 60–69: Below average — significant issues affecting recommendation quality
- < 60: Poor — critical failures requiring immediate action

**Overall Post-Show Grade: `[X]`/100 (`[LETTER]`)**

---

## TASK 12: PRIORITY ACTIONS & RECOMMENDATIONS FOR NEXT EVENT

Based on post-show findings, produce a prioritised action list.

**Configuration reference:**
- Similarity attribute weights: `recommendation.similarity_attributes`
- Control group settings: `recommendation.control_group`
- Post-analysis config: `post_analysis_mode` section in config

| Priority | Action | Owner | Timeline | Expected Impact |
|----------|--------|-------|----------|-----------------|
| P1 | `[FILL based on findings]` | Analytics | Before next pipeline run | `[FILL]` |
| P1 | `[FILL based on findings]` | Data Engineering | `[FILL]` | `[FILL]` |
| P2 | `[FILL based on findings]` | `[FILL]` | `[FILL]` | `[FILL]` |
| P3 | `[FILL based on findings]` | `[FILL]` | `[FILL]` | `[FILL]` |

**Standard checks to consider for every post-show:**
- [ ] Update `post_analysis_mode.scan_files` in config with this year's scan file paths
- [ ] Update `post_analysis_mode.registration_shows.this_year_main` show codes for next year
- [ ] Review any under-recommended sessions (conversion > 200%) for popularity-boosting
- [ ] Address control group demographic skew if > 3pp new/returning imbalance
- [ ] Improve fill rate for any attribute below 85% weighted coverage

**Success Metrics for Next Event:**

| Metric | This Event Actual | Next Event Target |
|--------|-------------------|-------------------|
| Visitor-level hit rate (treatment) | `[FILL]` | `[FILL + improvement]` |
| Absolute lift (pp) | `[FILL]` | Maintain or improve |
| Statistical significance | `[FILL]` | p < 0.05 |
| Control group skew | `[FILL]pp` | < 2pp (use stratified sampling) |
| Late registrant coverage | `[FILL]%` | Target 100% via continuous processing |

---

## TASK 13: CONCLUSION & OVERALL SYSTEM ASSESSMENT

**Synthesize:**
1. Overall post-show system grade (with comparison to pre-show grade)
2. Top 3–5 achievements ✅
3. Top 3–5 issues or misses 🔴
4. Business implications (retention, session attendance lift, sponsor value)
5. Bottom line assessment

**Executive Wrap-Up (3–5 sentences):**
- Were recommendations effective? (Lift: statistically significant yes/no)
- What was the biggest missed opportunity?
- What single change would most improve next event?
- Bottom line: `[single-sentence verdict]`

---

## OUTPUT FORMAT REQUIREMENTS

- **Format**: Markdown with hierarchical headers (##, ###, ####)
- **Tables**: Use for all quantitative data; no inline lists for numbers
- **Icons**: ✅ strengths, ⚠️ issues, 🔴 critical problems
- **Sections**: Follow the 13-task structure (+ Task 0 exclusions)
- **Language**: Clear, insight-focused, executive-ready

---

## FILE NAMING CONVENTION

Save report as: `report_[SHOW_CODE]_post_show_[YYYYMMDD].md`
- Replace `[SHOW_CODE]` with `event.name` from config
- Replace `[YYYYMMDD]` with analysis date

---

## COMPARISON TO PRE-SHOW REPORT

Reference `[PRE_SHOW_REPORT_PATH]` throughout to:
- State pre-show grade and compare to post-show grade
- Identify whether flagged pre-show issues materialized
- Validate or refute pre-show predictions
- Note visitor count growth between final pre-show run and actual attendance

---

## CONFIGURATION FILE ATTRIBUTE MAPPING GUIDE

### Essential Post-Show Configuration Sections

#### 1. Post-Analysis Mode Settings
```yaml
post_analysis_mode:
  registration_shows:
    this_year_main:
      - ['SHOW_CODE_26']        # → Codes for this year's entry scan filtering
  scan_files:
    seminars_scan_reference_this: "data/[event]/post/scans_reference.csv"
    seminars_scans_this: "data/[event]/post/scans.csv"
  entry_scan_files:
    entry_scans_this: ["data/[event]/post/entry_scans.csv"]
```

#### 2. Control Group Settings
```yaml
recommendation:
  control_group:
    enabled: true
    percentage: [CONTROL_GROUP_PCT]       # → A/B test design
    random_seed: 42                       # → Reproducibility
    enabled_modes:
      - personal_agendas
      # - engagement (if enabled)
```

#### 3. Similarity Attributes (for segmentation in Tasks 3.5, 7, 10)
```yaml
recommendation:
  similarity_attributes:
    [attribute_1]: [weight_1]    # → Use for [PRIMARY_SIMILARITY_ATTRIBUTE]
    [attribute_2]: [weight_2]    # → Use for segmentation in Task 3.5
```

---

**Generate the comprehensive report now, following all tasks (0 through 13) sequentially.**

### TASK 14: REPORT ENRICHMENT & EXECUTIVE WRAP-UP

After completing Tasks 0–13:

1. **Cross-check coverage** — confirm report includes:
   - Campaign journey (run ledger, delivery counts)
   - Full A/B test with segmented lift (new/returning required)
   - Session conversion analysis with under-recommended opportunities
   - Predictions vs reality table with root causes
   - Priority actions with Owner and Timeline fields
   - Pre-show grade comparison

2. **Executive wrap-up** — Under the Conclusion section, add:
   - 3–5 key achievements
   - 3–5 critical risks or gaps
   - 3 business implications (e.g., attendance lift, sponsor ROI, future retention)
   - Single bottom-line sentence starting with **"Bottom line:"**

3. **Match prior report style** — use the same numeric density, table structure, and narrative depth as the best prior report for this event (referenced in `[PRE_SHOW_REPORT_PATH]`)

---

**Generate the comprehensive report now, following all 14 tasks sequentially.**
