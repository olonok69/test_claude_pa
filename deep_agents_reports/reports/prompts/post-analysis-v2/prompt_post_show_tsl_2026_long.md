# Prompt: TSL 2026 Post-Show Analysis Report — Full Technical Version

## Instructions for Agentic Report Generator

You are a **Senior Data Analyst** generating the **POST-SHOW** recommendation system analysis report for **Tech Show London (TSL) 2026**.

This prompt is designed to be used after the show (4–5 March 2026) once badge scan data has been loaded into Neo4j via `post_analysis` mode. It covers the **complete event journey**: two pre-show campaigns (personal agendas + engagement), an incremental run, and the actual attendance outcomes.

---

## CONTEXT — TSL 2026 Specifics

| Parameter | Value |
|-----------|-------|
| **Event** | Tech Show London (TSL) 2026 |
| **Show Code** | `tsl` |
| **Event Dates** | 4–5 March 2026 (2 days) |
| **Database** | Neo4j Production (`neo4j-prod`) |
| **Config File** | `config/config_tsl.yaml` (deep_agents_reports) or `PA/config/config_tsl.yaml` |
| **Analysis Date** | `[CURRENT_DATE]` |
| **Analyst** | `[ANALYST_NAME]` |

### Co-located Shows (TSL 2026 umbrella)
| Show | Code | Primary Audience |
|------|------|-----------------|
| Data Centre World | DCWL26 | Data centre infrastructure |
| Cloud & AI Infrastructure | CAIL26 | Cloud/AI infra engineers |
| DevOps Live London | DAILS26 | DevOps/platform engineers |
| Cloud & Cyber Security Expo | CCSEL26 | Cybersecurity practitioners |
| Big Data & AI World | DOLL26 | Data/analytics professionals |

### Known Pre-Show Run Inventory (from Neo4j — do NOT re-query to discover these)
| Run | run_id | run_mode | campaign_id | Date | Sent | Withheld (Control) | Total Eligible |
|-----|--------|----------|-------------|------|------|--------------------|----------------|
| PA Initial | `tsl_personal_agendas_20260219T124351` | personal_agendas | tsl_conversion | 2026-02-19 | 14,160 | 2,496 | 16,656 |
| Engagement | `tsl_engagement_20260219T205354Z_c3f8fb55` | engagement | tsl_engagement | 2026-02-19 | 39,572 | 6,983 | 46,555 |
| PA Increment | `tsl_personal_agendas_20260227T224725Z_37b21c42` | personal_agendas | tsl_conversion | 2026-02-27 | 7,954 | 948 | 8,902 |

### Key Pre-Show Baselines (from report dated 18 February 2026)
- Total registered visitors at final run: **16,656**
- Treatment group: **14,160** (85.0%) | Control group: **2,496** (15.0%)
- Total session recs (PA): **166,489** | V2E recs: **83,045**
- Control group demographic skew: **5.9pp** new/returning imbalance (control over-represents returning visitors: 41.9% vs 36.0% treatment) → **always segment by new/returning in A/B analysis**
- Pre-show algorithm grade: **B+ (85/100)**
- Weighted data quality: **96.5%**
- Max session concentration pre-show: **39.3%**

---

## PRE-REQUISITES — Data Readiness Check

Before generating the report, verify the following data is available in Neo4j:

```cypher
// Check 1: Post-show attendance relationships exist
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl'
RETURN count(a) AS session_attendance_records, count(DISTINCT v) AS unique_attendees
```

```cypher
// Check 2: Venue entry scan relationships exist
MATCH (v:Visitor_this_year)-[r:registered_to_show]->()
WHERE v.show = 'tsl'
RETURN count(DISTINCT v) AS venue_attendees
```

```cypher
// Check 3: All pre-show RecommendationRun nodes present
MATCH (rr:RecommendationRun)
WHERE rr.show = 'tsl'
RETURN rr.run_id, rr.run_mode, rr.campaign_id, rr.created_at
ORDER BY rr.created_at
```

**If `assisted_session_this_year` records are 0** → post-analysis pipeline has not yet been run. Stop here and run steps 1–6 in `PA/config/config_tsl.yaml` with `mode: "post_analysis"` first.

---

## TASK 0: IDENTIFY SESSIONS TO EXCLUDE (Special Events)

Before all calculations, identify sessions that should be excluded from hit rate and conversion analysis (non-content sessions such as admin sessions, opening/closing remarks, networking slots).

```cypher
// Sessions that look like non-content administrative sessions
MATCH (s:Sessions_this_year)
WHERE s.show = 'tsl' OR s.show IS NULL
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
// High recommendation volume but low content signal
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(s:Sessions_this_year)
WHERE v.show = 'tsl'
WITH s, count(r) AS rec_count
WHERE rec_count > 5000
RETURN s.session_id, s.title, s.stream, rec_count
ORDER BY rec_count DESC
```

**Output requirement:** Produce a list `[EXCLUDED_SESSION_IDS]` — replace in all subsequent queries.

---

## TASK 1: CAMPAIGN JOURNEY & RUN LEDGER

Build the complete pre-show recommendation journey to frame the post-show analysis.

```cypher
// Full run ledger for TSL 2026
MATCH (rr:RecommendationRun)
WHERE rr.show = 'tsl'
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

```cypher
// IS_RECOMMENDED counts per run (session recommendations)
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s:Sessions_this_year)
WHERE v.show = 'tsl'
RETURN r.run_id, r.run_mode, count(r) AS total_recs, count(DISTINCT v) AS visitors_covered
ORDER BY r.run_id
```

```cypher
// V2E exhibitor recommendations summary
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED_EXHIBITOR]->(e:Exhibitor)
WHERE v.show = 'tsl'
RETURN r.run_id, r.run_mode, count(r) AS v2e_recs, count(DISTINCT v) AS v2e_visitors, count(DISTINCT e) AS exhibitors_covered
ORDER BY r.run_id
```

**Output requirement:** Campaign Journey Summary table showing the three runs, their timing, volumes, and purpose. Frame the narrative: engagement (re-engage prior attendees) → PA initial (convert registered visitors) → PA increment (late registrants).

---

## TASK 2: VISITOR REGISTRATION & ATTENDANCE FUNNEL

```cypher
// Registration final state
MATCH (v:Visitor_this_year)
WHERE v.show = 'tsl'
RETURN 
  count(v) AS total_registered,
  sum(CASE WHEN v.control_group = 1 THEN 1 ELSE 0 END) AS control_group_count,
  sum(CASE WHEN v.control_group = 0 THEN 1 ELSE 0 END) AS treatment_group_count,
  sum(CASE WHEN v.control_group IS NULL THEN 1 ELSE 0 END) AS unassigned_count,
  sum(CASE WHEN v.has_recommendation = '1' THEN 1 ELSE 0 END) AS with_recommendations
```

```cypher
// Venue attendance (who physically showed up)
MATCH (v:Visitor_this_year)-[:registered_to_show]->()
WHERE v.show = 'tsl'
WITH count(DISTINCT v) AS venue_attendees
MATCH (v2:Visitor_this_year) WHERE v2.show = 'tsl'
RETURN venue_attendees, count(v2) AS total_registered,
  toFloat(venue_attendees) / count(v2) * 100 AS attendance_rate_pct
```

```cypher
// Session attendance — visitors who went to ≥1 session (excluding special events)
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl' 
  AND (s.show = 'tsl' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
RETURN count(DISTINCT v) AS session_attendees, count(a) AS total_session_scans
```

```cypher
// Funnel: Treatment vs Control groups at each stage
MATCH (v:Visitor_this_year)
WHERE v.show = 'tsl' AND v.control_group IN [0, 1]
OPTIONAL MATCH (v)-[:registered_to_show]->()
OPTIONAL MATCH (v)-[a:assisted_session_this_year]->(s:Sessions_this_year)
  WHERE (s.show = 'tsl' OR s.show IS NULL) 
    AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
RETURN 
  CASE v.control_group WHEN 1 THEN 'Control (withheld)' ELSE 'Treatment (sent)' END AS group_name,
  count(DISTINCT v) AS registered,
  count(DISTINCT CASE WHEN EXISTS((v)-[:registered_to_show]->()) THEN v END) AS attended_venue,
  count(DISTINCT CASE WHEN a IS NOT NULL THEN v END) AS attended_sessions
ORDER BY v.control_group
```

```cypher
// Late registrant analysis — visitors registered after PA increment (after 2026-02-27)
MATCH (v:Visitor_this_year)
WHERE v.show = 'tsl' AND v.has_recommendation IS NULL OR v.has_recommendation = '0'
RETURN count(v) AS late_registrants_no_recs
```

**Output requirement:** Full visitor journey funnel table, broken down by treatment/control and new/returning. Note the 5.9pp new/returning imbalance in control group and flag its impact on organic rate estimates.

---

## TASK 3: A/B TEST — PERSONAL AGENDAS CAMPAIGN (PRIMARY CAUSAL ANALYSIS)

**Context:** 15% control group (2,496 visitors) withheld from personal agendas. The control group over-represents returning visitors (41.9% vs 36.0% treatment) — all lift calculations MUST be segmented by new/returning status.

### 3.1 Session-Level Hit Rate: Treatment vs Control

```cypher
// Session-level hit rate by group (all visitors)
MATCH (v:Visitor_this_year)
WHERE v.show = 'tsl' AND v.control_group IN [0, 1]
OPTIONAL MATCH (v)-[a:assisted_session_this_year]->(s:Sessions_this_year)
  WHERE (s.show = 'tsl' OR s.show IS NULL) AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(s)
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
// Visitor-level hit rate — visitors who attended ≥1 recommended session
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl' 
  AND v.control_group IN [0, 1]
  AND (s.show = 'tsl' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended_sessions
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(rec:Sessions_this_year)
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
// Calculate lift: treatment hit rate - organic (control) hit rate
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl'
  AND v.control_group IN [0, 1]
  AND (s.show = 'tsl' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(s)
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

⚠️ **REQUIRED** — due to 5.9pp new/returning skew in control group, report lift separately for each segment and a weighted composite.

```cypher
// Segment lift by new/returning visitor status
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl' AND v.control_group IN [0, 1]
  AND (s.show = 'tsl' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(s)
OPTIONAL MATCH (v)-[:Same_Visitor]->()
WITH v.control_group AS ctrl,
     CASE WHEN EXISTS((v)-[:Same_Visitor]->()) THEN 'Returning' ELSE 'New' END AS visitor_type,
     count(a) AS attended,
     count(CASE WHEN r IS NOT NULL THEN 1 END) AS hits
RETURN 
  visitor_type,
  CASE ctrl WHEN 1 THEN 'Control' ELSE 'Treatment' END AS group_name,
  sum(attended) AS total_attended,
  sum(hits) AS total_hits,
  round(100.0 * sum(hits) / sum(attended), 2) AS hit_rate_pct
ORDER BY visitor_type, ctrl
```

**Output requirement:** A/B test results table including treatment rate, organic rate, absolute lift (pp), relative lift (%), statistical significance test result (two-proportion z-test: z-score, p-value), and 95% confidence interval. Present segmented results (new vs returning) prominently. Compare against pre-show expected range (30–35% visitor-level hit rate). State clearly whether the lift is statistically significant.

---

## TASK 4: A/B TEST — ENGAGEMENT CAMPAIGN

**Context:** Engagement campaign targeted prior attendees from TSL 2025/2024. Control group: 6,983 withheld out of 46,555 eligible. Use `run_id = 'tsl_engagement_20260219T205354Z_c3f8fb55'`.

```cypher
// Engagement hit rate: treatment vs control
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl'
  AND (s.show = 'tsl' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: 'tsl_engagement_20260219T205354Z_c3f8fb55'}]->(s)
OPTIONAL MATCH (d:CampaignDelivery {run_id: 'tsl_engagement_20260219T205354Z_c3f8fb55'})-[:FOR_VISITOR]->(v)
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

```cypher
// Visitor-level engagement hit rate
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl'
  AND (s.show = 'tsl' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended_sessions
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: 'tsl_engagement_20260219T205354Z_c3f8fb55'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended_sessions
OPTIONAL MATCH (d:CampaignDelivery {run_id: 'tsl_engagement_20260219T205354Z_c3f8fb55'})-[:FOR_VISITOR]->(v)
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

**Output requirement:** Engagement A/B results. Note that engagement targeted prior-year attendees (returning audience) — organic rates may be higher than PA campaign. Compare with PA lift for cross-campaign insights.

---

## TASK 5: OVERALL SESSION HIT RATE & CONVERSION ANALYSIS

### 5.1 Top Recommended Sessions — Did People Actually Attend?

```cypher
// Top 20 most recommended sessions vs actual attendance
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(s:Sessions_this_year)
WHERE v.show = 'tsl' AND (s.show = 'tsl' OR s.show IS NULL)
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

### 5.2 Under-Recommended Popular Sessions

```cypher
// Sessions with high actual attendance but low recommendation counts
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl'
  AND (s.show = 'tsl' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH s, count(DISTINCT v) AS actual_attendance
OPTIONAL MATCH (v2:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(s)
WITH s, actual_attendance, count(DISTINCT v2) AS rec_count
WHERE actual_attendance >= 30
RETURN 
  s.session_id, s.title, s.stream,
  actual_attendance,
  rec_count AS times_recommended,
  CASE WHEN rec_count > 0 THEN round(toFloat(actual_attendance) / rec_count * 100, 1) ELSE null END AS conversion_pct
ORDER BY actual_attendance DESC
LIMIT 20
```

### 5.3 Best Converting Sessions (Min 30 Recommendations)

```cypher
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(s:Sessions_this_year)
WHERE v.show = 'tsl' AND (s.show = 'tsl' OR s.show IS NULL)
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

### 5.4 Sessions Never Attended (Zero Scan Records)

```cypher
MATCH (s:Sessions_this_year)
WHERE (s.show = 'tsl' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
  AND NOT EXISTS((v:Visitor_this_year)-[:assisted_session_this_year]->(s))
OPTIONAL MATCH (v2:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WHERE v2.show = 'tsl'
RETURN s.session_id, s.title, s.stream, count(r) AS times_recommended
ORDER BY times_recommended DESC
```

**Output requirement:** Tables for top recommended vs attended sessions, under-recommended popular sessions (missed opportunities), best converters, and zero-attendance sessions. Highlight any sessions with conversion > 200% (indicates under-recommendation).

---

## TASK 6: VISITOR-LEVEL PERFORMANCE ANALYSIS

### 6.1 Overall Visitor Hit Rate (All Attendees)

```cypher
// Overall: visitors who attended ≥1 recommended session
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl'
  AND (s.show = 'tsl' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended_sessions
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended_sessions
RETURN 
  count(DISTINCT v) AS total_session_attendees,
  count(DISTINCT CASE WHEN count(rec) > 0 THEN v END) AS visitors_with_hit,
  round(100.0 * count(DISTINCT CASE WHEN count(rec) > 0 THEN v END) / count(DISTINCT v), 2) AS overall_visitor_hit_rate
```

### 6.2 Sessions per Attendee Distribution

```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl'
  AND (s.show = 'tsl' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, count(a) AS sessions_attended
RETURN 
  avg(sessions_attended) AS avg_sessions,
  min(sessions_attended) AS min_sessions,
  max(sessions_attended) AS max_sessions,
  percentileCont(sessions_attended, 0.25) AS p25,
  percentileCont(sessions_attended, 0.5) AS median,
  percentileCont(sessions_attended, 0.75) AS p75
```

### 6.3 Visitors with Most Recommended Sessions Attended

```cypher
// Top visitors by recommendation hit count
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl'
  AND (s.show = 'tsl' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended_sessions, count(a) AS sessions_attended
MATCH (v)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended_sessions
WITH v, sessions_attended, count(DISTINCT rec) AS hits
RETURN count(v) AS visitors_by_hit_count, hits
ORDER BY hits DESC
LIMIT 10
```

**Output requirement:** Overall visitor-level hit rate with comparison to pre-show benchmark (LVS 2025: 34.4%). Sessions-per-attendee distribution table. Commentary on engagement depth.

---

## TASK 7: CO-LOCATED SHOW BREAKDOWN

Analyse which co-located shows drove the most session attendance and whether recommendations aligned with actual show interest.

```cypher
// Session attendance by co-located show (via theatre or show code on session)
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl'
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(s)
RETURN 
  s.show AS co_located_show,
  count(DISTINCT v) AS unique_attendees,
  count(a) AS total_scans,
  count(CASE WHEN r IS NOT NULL THEN 1 END) AS recommended_scans,
  round(100.0 * count(CASE WHEN r IS NOT NULL THEN 1 END) / count(a), 2) AS hit_rate_pct
ORDER BY total_scans DESC
```

```cypher
// Visitor primary sector vs most attended co-located show
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl' AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v.which_sector_does_your_company_primarily_operate_in AS sector, s.show AS show_attended, count(a) AS cnt
WHERE sector IS NOT NULL
RETURN sector, show_attended, cnt
ORDER BY cnt DESC
LIMIT 30
```

**Output requirement:** Per-co-located-show table with attendance, hit rate, and recommendation alignment. Note alignment between sector (primary similarity attribute, weight 0.8) and actual show attendance patterns.

---

## TASK 8: ENGAGEMENT CAMPAIGN — THEATRE FILTER VALIDATION

The engagement run used `engagement_show_theatre_filter` to map visitor prior-year show codes to specific theatres. Validate this worked correctly.

```cypher
// Engagement visitors who attended their mapped theatre
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: 'tsl_engagement_20260219T205354Z_c3f8fb55'}]->(s:Sessions_this_year)
WHERE v.show = 'tsl'
WITH v, count(r) AS eng_recs
OPTIONAL MATCH (v)-[a:assisted_session_this_year]->(s2:Sessions_this_year)
  WHERE (s2.show = 'tsl' OR s2.show IS NULL)
  AND NOT s2.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r2:IS_RECOMMENDED {run_id: 'tsl_engagement_20260219T205354Z_c3f8fb55'}]->(s2)
WITH v, eng_recs, count(DISTINCT a) AS sessions_attended, count(DISTINCT r2) AS sessions_recommended_and_attended
WHERE sessions_attended > 0
RETURN count(v) AS eligible_visitors, 
       avg(eng_recs) AS avg_eng_recs,
       avg(sessions_recommended_and_attended) AS avg_hits
```

**Output requirement:** Validate engagement theatre filter effectiveness. Note that `include_show_last_values: ["ALL"]` was configured — interpret whether theatre-aligned recommendations led to better conversion vs PA recommendations.

---

## TASK 9: V2E EXHIBITOR RECOMMENDATIONS (if scan data available)

If exhibitor stand scan data is available in Neo4j as `visited_exhibitor_this_year` (or equivalent), run exhibitor hit rate analysis. If not, document that this analysis is deferred.

```cypher
// Check if exhibitor visit data exists
MATCH (v:Visitor_this_year)-[r:visited_exhibitor_this_year]->(e:Exhibitor)
WHERE v.show = 'tsl'
RETURN count(r) AS exhibitor_visits, count(DISTINCT v) AS visitors_who_visited_stands
LIMIT 1
```

**If data exists:**

```cypher
// V2E hit rate: visitors who visited a recommended exhibitor
MATCH (v:Visitor_this_year)-[:visited_exhibitor_this_year]->(e:Exhibitor)
WHERE v.show = 'tsl'
WITH v, collect(DISTINCT e.uuid) AS visited_exhibitors
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED_EXHIBITOR]->(rec_e:Exhibitor)
WHERE rec_e.uuid IN visited_exhibitors
RETURN 
  count(DISTINCT v) AS visitors_who_visited_stands,
  count(DISTINCT CASE WHEN count(r) > 0 THEN v END) AS visitors_with_v2e_hit,
  round(100.0 * count(DISTINCT CASE WHEN count(r) > 0 THEN v END) / count(DISTINCT v), 2) AS v2e_visitor_hit_rate_pct
```

**If data does not exist:** Note that V2E performance measurement is deferred pending exhibitor scan data export. Reference pre-show V2E coverage: 99.7% of visitors (16,609) received 5 exhibitor recommendations; 98.5% of 391 exhibitors were recommended.

---

## TASK 10: PRE-SHOW PREDICTIONS VS POST-SHOW REALITY

Compare the key predictions from the final pre-show report (18 February 2026) against actual outcomes.

| Prediction | Pre-Show Expectation | Actual Result | Verdict |
|------------|---------------------|---------------|---------|
| Visitor-level hit rate | 30–35% (LVS benchmark) | `[FILL]` | ✅/⚠️/🔴 |
| Control group organic rate | 20–25% | `[FILL]` | ✅/⚠️/🔴 |
| Recommendation lift | >5pp absolute | `[FILL]` | ✅/⚠️/🔴 |
| Statistical significance | p < 0.05 | `[FILL]` | ✅/⚠️/🔴 |
| Late registrant impact | Higher engagement rate expected | `[FILL]` | ✅/⚠️/🔴 |
| New/returning skew correction needed | Yes (5.9pp delta) | `[FILL]` | — |
| Top co-located show by attendance | Data Centre World (expected) | `[FILL]` | ✅/⚠️/🔴 |
| Session concentration (39.3% pre-show) | Similar or lower post-show | `[FILL]` | ✅/⚠️/🔴 |

**Output requirement:** Complete the prediction/reality table. For each significant discrepancy (🔴), provide root cause analysis. For accurate predictions (✅), provide confirmation and notes.

---

## TASK 11: DATA QUALITY RETROSPECTIVE

Compare pre-show data quality expectations against post-show findings.

```cypher
// Check post-show attribute fill rates for session attendees
MATCH (v:Visitor_this_year)-[:assisted_session_this_year]->(:Sessions_this_year)
WHERE v.show = 'tsl'
WITH DISTINCT v
RETURN 
  count(v) AS session_attendees,
  round(100.0 * count(CASE WHEN v.which_sector_does_your_company_primarily_operate_in IS NOT NULL 
    AND v.which_sector_does_your_company_primarily_operate_in <> 'NA' THEN 1 END) / count(v), 1) AS sector_fill_pct,
  round(100.0 * count(CASE WHEN v.which_of_the_following_best_describes_your_primary_professional_function_if_you_are_a_consultant_please_select_the_main_area_in_which_you_provide_expertise_or_services_select_one IS NOT NULL THEN 1 END) / count(v), 1) AS function_fill_pct,
  round(100.0 * count(CASE WHEN v.which_of_the_following_best_describes_your_current_seniority_level IS NOT NULL THEN 1 END) / count(v), 1) AS seniority_fill_pct
```

**Output requirement:** Compare pre-show weighted fill rate (96.5%) against the actual session-attending population. Note whether visitors with lower data quality had lower hit rates (hypothesis: sparse profiles → weaker recommendations → lower hit rates).

---

## TASK 12: ALGORITHM ASSESSMENT & GRADE

Score the recommendation system on a 0–100 scale across these dimensions, comparing against the pre-show grade of **B+ (85/100)**:

| Dimension | Weight | Pre-Show Score | Post-Show Score | Notes |
|-----------|--------|---------------|-----------------|-------|
| **Coverage** | 20% | 10/10 | `[FILL]` | 100% session rec coverage pre-show |
| **Hit Rate Quality** | 25% | N/A | `[FILL]` | Treatment vs benchmark |
| **Causal Lift** | 20% | N/A | `[FILL]` | Statistically significant lift |
| **Calibration** | 15% | 7/10 | `[FILL]` | Concentration (39.3%) + under-rec |
| **Data Quality** | 10% | 9/10 | `[FILL]` | 96.5% weighted fill rate |
| **Engagement Effectiveness** | 10% | N/A | `[FILL]` | Engagement campaign hit rate |

**Overall Post-Show Grade: `[X]`/100 (`[LETTER GRADE]`)**

---

## TASK 13: ACTIONABLE RECOMMENDATIONS FOR TSL 2027

Based on post-show findings, produce a prioritised action list:

**P1 — Critical (implement before next event):**
- [ ] Address identified under-recommended popular sessions (if any exceeded 300% conversion)
- [ ] Implement stratified control group allocation to eliminate new/returning skew
- [ ] Update scan file references in `config_tsl.yaml` post_analysis_mode to 2026 files

**P2 — High (target for next pipeline cycle):**
- [ ] `[FILL based on findings]`

**P3 — Enhancement (nice to have):**
- [ ] `[FILL based on findings]`

**Success Metrics for TSL 2027 Benchmarks:**

| Metric | TSL 2026 Actual | TSL 2027 Target |
|--------|----------------|-----------------|
| Visitor-level hit rate | `[FILL]` | `[FILL + 2pp]` |
| Absolute lift (pp) | `[FILL]` | `[FILL]` |
| Relative lift (%) | `[FILL]` | `[FILL]` |
| Statistical significance | `[FILL]` | p < 0.05 |
| Control group skew | 5.9pp | < 2pp (stratified) |

---

## REPORT STRUCTURE

Produce the final report following this structure:

```
# Tech Show London 2026 — Post-Show Recommendation Analysis Report

Event: Tech Show London 2026 | Event Dates: 4–5 March 2026
Report Date: [CURRENT_DATE] | Database: Neo4j Production (neo4j-prod)
Mode: post_analysis | Configuration: config/config_tsl.yaml

## 1. Executive Summary
   - Key metrics scorecard table
   - Pre-show grade vs post-show grade
   - 3-sentence bottom line

## 2. Campaign Journey — TSL 2026 Timeline
   - Run ledger table
   - Narrative: engagement → PA → increment

## 3. Visitor Registration & Attendance Funnel
   - Funnel table (registered → venue → sessions)
   - Treatment/control split
   - Late registrant impact

## 4. A/B Test: Personal Agendas Campaign (Primary)
   4.1 Session-level hit rate (treatment vs control)
   4.2 Visitor-level hit rate (treatment vs control)
   4.3 Recommendation lift (absolute, relative, CI)
   4.4 Segmented lift (new vs returning) — REQUIRED
   4.5 Statistical significance test results

## 5. A/B Test: Engagement Campaign
   5.1 Hit rate results
   5.2 Lift vs organic
   5.3 Cross-campaign comparison

## 6. Session Performance Analysis
   6.1 Top recommended sessions vs actual attendance
   6.2 Under-recommended popular sessions (missed opportunities)
   6.3 Best converting sessions
   6.4 Zero-attendance sessions

## 7. Visitor-Level Performance
   7.1 Overall visitor hit rate
   7.2 Sessions per attendee distribution
   7.3 High-engagement visitors profile

## 8. Co-located Show Breakdown
   - Per-show attendance and hit rate table
   - Sector-to-show alignment

## 9. Engagement Theatre Filter Validation

## 10. V2E Exhibitor Recommendations
    (if exhibitor scan data available, else deferred section)

## 11. Pre-Show Predictions vs Post-Show Reality
    - Prediction/reality table
    - Root cause analysis for discrepancies

## 12. Data Quality Retrospective

## 13. Algorithm Assessment & Grade
    - Scoring table
    - Final grade with justification

## 14. Recommendations for TSL 2027
    - P1/P2/P3 action list
    - Success metrics benchmarks

## Technical Appendix
    A. Database Schema Summary (node counts, relationship counts)
    B. Excluded Sessions List
    C. Run Traceability Log (RecommendationRun nodes summary)
    D. Similarity Score Distribution (post-show context)
    E. Configuration Key Parameters Reference
```

---

## FILE NAMING CONVENTION

Save report as: `report_tsl_post_show_[YYYYMMDD].md`

---

## IMPORTANT NOTES FOR ANALYST

1. **Control group skew is known:** The 5.9pp new/returning imbalance (returning over-represented in control) means organic rates will be slightly inflated. Always report segmented lift (§4.4) alongside the overall figure.
2. **Run ID awareness:** Use the specific `run_id` values for each analysis task — do not mix runs. PA analysis = `tsl_personal_agendas_20260219T124351` (initial) or include increment if applicable. Engagement = `tsl_engagement_20260219T205354Z_c3f8fb55`.
3. **TSL has no specialization mapping** (unlike vet shows) — similarity is sector + professional function based.
4. **Visitor_last_year_main** = TSL 2025 prior attendees; **Visitor_last_year_secondary** = TSL 2024 prior attendees.
5. **Engagement audience** (~46,555 eligible) is larger than PA audience (16,656) because it targets prior-year registrants regardless of current-year registration.
6. If `assisted_session_this_year` data is missing, note in report and provide a partial analysis using only the data available.
