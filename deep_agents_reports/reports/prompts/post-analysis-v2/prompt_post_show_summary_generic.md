# Prompt: Post-Show Analysis Report — Executive Summary Version (Generic Template)

## Instructions for Agentic Report Generator

You are a **Senior Data Analyst** generating a concise **POST-SHOW EXECUTIVE SUMMARY** for the specified event. This report is for senior management and business stakeholders. It is **metrics-focused**, presentation-ready, and avoids deep technical detail.

Keep the output to **2–3 pages maximum**. Lead with results. No lengthy narrative.

---

## CONTEXT VARIABLES (To be filled for each event)

- **Event**: `[EVENT_NAME]` → Use `event.main_event_name` from config
- **Show Code**: `[SHOW_CODE]` → Use `event.name` or `neo4j.show_name` from config
- **Year**: `[YEAR]` → Use `event.year` from config
- **Event Dates**: `[EVENT_DATES]` → Actual show dates
- **Database**: Neo4j `[ENVIRONMENT]`
- **Report Date**: `[CURRENT_DATE]`
- **Pre-Show Benchmark**: `[BENCHMARK_HIT_RATE]` → Visitor-level hit rate from most recent comparable event
- **Control Group %**: `[CONTROL_GROUP_PCT]` → From `recommendation.control_group.percentage` in config
- **Pre-Show Grade**: `[PRE_SHOW_GRADE]` → From `[PRE_SHOW_REPORT_PATH]`
- **PA Initial Run ID**: `[PA_INITIAL_RUN_ID]` → From `RecommendationRun` query below
- **Engagement Run ID**: `[ENGAGEMENT_RUN_ID]` → From `RecommendationRun` query (if applicable)
- **Excluded Sessions**: `[EXCLUDED_SESSION_IDS]` → From Task 0 admin session identification

---

## DATABASE SCHEMA (Key nodes and relationships for this report)

- `Visitor_this_year` — `show`, `control_group`, `has_recommendation`
- `Sessions_this_year` — `show`, `session_id`, `title`, `stream`
- `Exhibitor` — exhibitor entities
- `RecommendationRun` — `run_id`, `run_mode`, `campaign_id`, `show`, `created_at`
- `CampaignDelivery` — `run_id`, `visitor_id`, `status`, `show`
- `IS_RECOMMENDED` — `run_id`, `run_mode`, `control_group`, `similarity_score`
- `IS_RECOMMENDED_EXHIBITOR` — `run_id`, `run_mode`
- `assisted_session_this_year` — post-show actual session attendance
- `registered_to_show` — post-show venue entry scans
- `Same_Visitor` — links to prior year visitor nodes
- `FOR_VISITOR`, `FOR_RUN` — `CampaignDelivery` linkage relationships

---

## DATA READINESS CHECK

```cypher
// Confirm RecommendationRun nodes and run IDs
MATCH (rr:RecommendationRun)
WHERE rr.show = '[SHOW_CODE]'
RETURN rr.run_id, rr.run_mode, rr.campaign_id, rr.created_at
ORDER BY rr.created_at
```

```cypher
// Confirm post-show attendance data is loaded
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
RETURN count(a) AS session_scans, count(DISTINCT v) AS attendees_with_scans
```

**If `session_scans = 0`** → data not yet available. Run `post_analysis` pipeline mode first.

**Assign run IDs from first query before proceeding:**
- `[PA_INITIAL_RUN_ID]` → earliest `personal_agendas` run_id
- `[ENGAGEMENT_RUN_ID]` → `engagement` run_id (if applicable)

---

## TASK 0: IDENTIFY EXCLUDED SESSIONS

```cypher
MATCH (s:Sessions_this_year)
WHERE (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND (toLower(s.title) CONTAINS 'closing'
    OR toLower(s.title) CONTAINS 'opening'
    OR toLower(s.title) CONTAINS 'remarks'
    OR toLower(s.title) CONTAINS 'welcome'
    OR toLower(s.title) CONTAINS 'networking'
    OR toLower(s.title) CONTAINS 'placeholder'
    OR s.title IS NULL)
RETURN s.session_id, s.title
ORDER BY s.title
```

Build `[EXCLUDED_SESSION_IDS]` list. Use in all subsequent queries.

---

## SECTION 1: VISITOR JOURNEY FUNNEL

```cypher
// Registration: treatment vs control split
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
RETURN count(v) AS total_registered,
  sum(CASE WHEN v.control_group = 0 THEN 1 ELSE 0 END) AS treatment_count,
  sum(CASE WHEN v.control_group = 1 THEN 1 ELSE 0 END) AS control_count
```

```cypher
// Venue attendance
MATCH (v:Visitor_this_year)-[:registered_to_show]->()
WHERE v.show = '[SHOW_CODE]'
RETURN count(DISTINCT v) AS venue_attendees
```

```cypher
// Session attendees
MATCH (v:Visitor_this_year)-[:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
RETURN count(DISTINCT v) AS session_attendees, count(*) AS total_scans
```

```cypher
// Treatment visitors who attended ≥1 recommended session
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND v.control_group = 0
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended
WITH v, count(DISTINCT rec) AS hits
WHERE hits > 0
RETURN count(v) AS treatment_visitors_with_hit
```

**Fill this funnel table in the report:**

| Stage | Treatment (sent recs) | Control (withheld) | Total |
|-------|:--------------------:|:------------------:|:-----:|
| Registered | `[FILL]` | `[FILL]` | `[FILL]` |
| Attended venue | `[FILL]` | `[FILL]` | `[FILL]` |
| Attended ≥1 session | `[FILL]` | `[FILL]` | `[FILL]` |
| Attended ≥1 **recommended** session | `[FILL]` | — | `[FILL]` |
| Attendance rate (of registered) | `[FILL]%` | `[FILL]%` | `[FILL]%` |
| Session engagement (of venue attendees) | `[FILL]%` | `[FILL]%` | `[FILL]%` |

---

## SECTION 2: A/B TEST RESULTS — PERSONAL AGENDAS CAMPAIGN

```cypher
// Session-level hit rate: treatment vs control
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]' AND v.control_group IN [0, 1]
OPTIONAL MATCH (v)-[a:assisted_session_this_year]->(s:Sessions_this_year)
  WHERE (s.show = '[SHOW_CODE]' OR s.show IS NULL)
    AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(s)
WITH v.control_group AS ctrl,
     count(a) AS attended,
     count(CASE WHEN r IS NOT NULL THEN 1 END) AS hits
RETURN
  CASE ctrl WHEN 1 THEN 'Control' ELSE 'Treatment' END AS group_name,
  sum(attended) AS sessions_attended,
  sum(hits) AS sessions_hit,
  round(100.0 * sum(hits) / sum(attended), 1) AS session_hit_rate_pct
ORDER BY ctrl
```

```cypher
// Visitor-level hit rate: treatment vs control
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND v.control_group IN [0, 1]
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended_sessions
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended_sessions
WITH v.control_group AS ctrl, v,
     CASE WHEN count(rec) > 0 THEN 1 ELSE 0 END AS had_hit
RETURN
  CASE ctrl WHEN 1 THEN 'Control' ELSE 'Treatment' END AS group_name,
  count(v) AS attendees,
  sum(had_hit) AS with_hit,
  round(100.0 * sum(had_hit) / count(v), 1) AS visitor_hit_rate_pct
ORDER BY ctrl
```

```cypher
// Segmented lift: new vs returning visitors
// (required when pre-show report noted demographic imbalance in control group)
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
  round(100.0 * sum(had_hit) / count(v), 1) AS visitor_hit_rate_pct
ORDER BY visitor_type, ctrl
```

**Fill this scorecard table:**

| Metric | Treatment | Control (Organic) | Lift | vs Benchmark |
|--------|:---------:|:-----------------:|:----:|:------------:|
| Session-level hit rate | `[FILL]%` | `[FILL]%` | `[FILL]pp` | `[vs [BENCHMARK_HIT_RATE]%]` |
| Visitor-level hit rate | `[FILL]%` | `[FILL]%` | `[FILL]pp` | `[vs [BENCHMARK_HIT_RATE]%]` |
| Relative lift | — | — | `[FILL]%` | — |
| Statistical significance | — | — | p=`[FILL]` | `[✅/🔴]` |

**New visitors:** Treatment `[FILL]%` vs Control `[FILL]%` → Lift `[FILL]pp`

**Returning visitors:** Treatment `[FILL]%` vs Control `[FILL]%` → Lift `[FILL]pp`

*(Note: if pre-show report documented control group demographic skew, segmented figures are the primary reference)*

---

## SECTION 3: ENGAGEMENT CAMPAIGN RESULTS (if applicable)

*Skip if no engagement run was executed.*

```cypher
// Engagement campaign hit rate summary
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[ENGAGEMENT_RUN_ID]'}]->(s)
OPTIONAL MATCH (d:CampaignDelivery {run_id: '[ENGAGEMENT_RUN_ID]'})-[:FOR_VISITOR]->(v)
WITH
  CASE d.status WHEN 'withheld_control' THEN 'Control' ELSE 'Treatment' END AS grp,
  count(a) AS attended,
  count(CASE WHEN r IS NOT NULL THEN 1 END) AS hits
WHERE d IS NOT NULL
RETURN grp,
  sum(attended) AS total_attended,
  sum(hits) AS total_hits,
  round(100.0 * sum(hits) / sum(attended), 1) AS hit_rate_pct
ORDER BY grp
```

| Metric | Engagement Treatment | Engagement Control | Lift |
|--------|:-------------------:|:-----------------:|:----:|
| Session-level hit rate | `[FILL]%` | `[FILL]%` | `[FILL]pp` |
| Audience (sent / withheld) | `[FILL]` | `[FILL]` | — |

---

## SECTION 4: TOP SESSIONS — RECOMMENDED VS ACTUAL

```cypher
// Top 10 most recommended sessions vs actual attendance
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH s, count(DISTINCT v) AS recs
OPTIONAL MATCH (v2:Visitor_this_year)-[:assisted_session_this_year]->(s)
WITH s, recs, count(DISTINCT v2) AS attendance
RETURN s.title, s.stream, recs AS recommended_to,
       attendance AS actually_attended,
       round(toFloat(attendance) / recs * 100, 0) AS conversion_pct
ORDER BY recs DESC
LIMIT 10
```

```cypher
// Top 10 most attended sessions (actual popularity)
MATCH (v:Visitor_this_year)-[:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH s, count(DISTINCT v) AS attendance
OPTIONAL MATCH (v2:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(s)
WITH s, attendance, count(DISTINCT v2) AS recs
RETURN s.title, s.stream,
       attendance AS actually_attended,
       recs AS recommended_to,
       CASE WHEN recs > 0 THEN round(toFloat(attendance) / recs * 100, 0) ELSE null END AS conversion_pct
ORDER BY attendance DESC
LIMIT 10
```

**Flag any sessions with `conversion_pct > 200%` as under-recommended opportunities for the next event.**

---

## SECTION 5: OVERALL PERFORMANCE SCORECARD

| Metric | Pre-Show | Post-Show | Change | Status |
|--------|:--------:|:---------:|:------:|:------:|
| Recommendation coverage | `[FROM PRE-SHOW]` | `[FILL]%` | — | `[✅/⚠️]` |
| Venue attendance rate | — | `[FILL]%` | — | — |
| Session engagement rate | — | `[FILL]%` | — | — |
| Visitor-level hit rate (treatment) | benchmark `[BENCHMARK_HIT_RATE]%` | `[FILL]%` | `[FILL]pp` | `[✅/⚠️/🔴]` |
| Absolute recommendation lift | target >5pp | `[FILL]pp` | — | `[✅/⚠️/🔴]` |
| Statistical significance (p-value) | target <0.05 | p=`[FILL]` | — | `[✅/⚠️/🔴]` |
| Overall system grade | `[PRE_SHOW_GRADE]` | `[FILL]/100` | `[FILL]` | — |

---

## SECTION 6: CAMPAIGN JOURNEY SUMMARY

```cypher
// Run ledger summary
MATCH (rr:RecommendationRun)
WHERE rr.show = '[SHOW_CODE]'
OPTIONAL MATCH (d:CampaignDelivery)-[:FOR_RUN]->(rr)
RETURN rr.run_mode, rr.campaign_id, rr.created_at,
  count(CASE WHEN d.status = 'sent' THEN 1 END) AS sent,
  count(CASE WHEN d.status = 'withheld_control' THEN 1 END) AS withheld
ORDER BY rr.created_at
```

| Run | Mode | Date | Sent | Withheld (Control) |
|-----|------|------|------|--------------------|
| `[FILL]` | personal_agendas | `[FILL]` | `[FILL]` | `[FILL]` |
| `[FILL]` | engagement | `[FILL]` | `[FILL]` | `[FILL]` |
| `[FILL]` | personal_agendas (increment) | `[FILL]` | `[FILL]` | `[FILL]` |

---

## SECTION 7: KEY FINDINGS & NEXT EVENT PRIORITIES

**✅ What Worked Well (3 bullets):**
- `[FILL]`
- `[FILL]`
- `[FILL]`

**⚠️ What Needs Improvement (3 bullets):**
- `[FILL]`
- `[FILL]`
- `[FILL]`

**🎯 Top 3 Actions for Next Event:**
1. `[FILL]` — Owner: `[FILL]` | Timeline: `[FILL]` | Impact: `[FILL]`
2. `[FILL]` — Owner: `[FILL]` | Timeline: `[FILL]` | Impact: `[FILL]`
3. `[FILL]` — Owner: `[FILL]` | Timeline: `[FILL]` | Impact: `[FILL]`

**Bottom line:** `[Single sentence overall verdict on recommendation system performance]`

---

## REPORT OUTPUT FORMAT

```
# [EVENT_NAME] [YEAR] — Post-Show Recommendation System: Executive Summary

Event: [EVENT_NAME] [YEAR] | Dates: [EVENT_DATES]
Report Date: [CURRENT_DATE] | Prepared for: Senior Management
Pre-Show Grade: [PRE_SHOW_GRADE] | Config: [CONFIG_FILE_PATH]

---
## 1. Visitor Journey Funnel
[Funnel table — Section 1]

## 2. A/B Test: Did Recommendations Drive Attendance?
[Scorecard table — Section 2 + segmented lift]
[One paragraph: statistical result and plain-language interpretation]

## 3. Engagement Campaign Results
[Table — Section 3, or "Not applicable" if no engagement run]

## 4. Top Sessions: Recommended vs Reality
[Top 10 recommended | Top 10 actual — Section 4]
[Flag any under-recommended sessions]

## 5. Campaign Journey
[Run ledger table — Section 6]

## 6. Performance Scorecard
[Table — Section 5]

## 7. Key Findings & Priorities for Next Event
[Bullets + action table — Section 7]

---
Report generated: [CURRENT_DATE] | Data source: Neo4j [ENVIRONMENT]
```

---

## FILE NAMING CONVENTION

Save report as: `report_[SHOW_CODE]_post_show_summary_[YYYYMMDD].md`

---

## NOTE

This is the **executive summary version**. For full technical analysis — including segmented A/B tests, stream-level breakdown, V2E exhibitor performance, data quality retrospective, pre-show predictions vs reality, algorithm grading, and detailed recommendations — use `prompt_post_show_generic.md`.
