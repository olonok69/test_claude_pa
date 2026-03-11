# Prompt: TSL 2026 Post-Show Analysis — Executive Summary Version

## Instructions for Agentic Report Generator

You are a **Senior Data Analyst** generating a concise **POST-SHOW EXECUTIVE SUMMARY** for **Tech Show London (TSL) 2026**. This report is for senior management and business stakeholders. It is **metrics-focused**, presentation-ready, and avoids deep technical detail.

Keep the output to **2–3 pages maximum**. Lead with results. No lengthy narrative.

---

## CONTEXT

| Parameter | Value |
|-----------|-------|
| **Event** | Tech Show London (TSL) 2026 |
| **Show Code** | `tsl` |
| **Event Dates** | 4–5 March 2026 |
| **Database** | Neo4j Production (`neo4j-prod`) |
| **Report Date** | `[CURRENT_DATE]` |
| **Report Type** | Post-Show Executive Summary |

### Pre-Show Baseline (for comparison)
- Registered visitors: **16,656** | Control group: **2,496 (15%)**
- Pre-show recommendation system grade: **B+ (85/100)**
- Expected visitor-level hit rate: **30–35%** (LVS 2025 benchmark: 34.4%)
- Expected absolute lift: **>5 percentage points**

---

## DATA READINESS CHECK

```cypher
// Confirm post-show data is loaded
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(:Sessions_this_year)
WHERE v.show = 'tsl'
RETURN count(a) AS session_scans, count(DISTINCT v) AS attendees_with_scans
```

If `session_scans = 0`, stop — data is not yet available.

---

## SECTION 1: VISITOR ATTENDANCE FUNNEL

Run these queries and fill the funnel table below.

```cypher
// Total registered
MATCH (v:Visitor_this_year) WHERE v.show = 'tsl'
RETURN count(v) AS total_registered,
  sum(CASE WHEN v.control_group = 0 THEN 1 ELSE 0 END) AS treatment,
  sum(CASE WHEN v.control_group = 1 THEN 1 ELSE 0 END) AS control_group
```

```cypher
// Venue attendance
MATCH (v:Visitor_this_year)-[:registered_to_show]->()
WHERE v.show = 'tsl'
RETURN count(DISTINCT v) AS venue_attendees
```

```cypher
// Session attendees (exclude admin sessions identified in EXCLUDED_SESSION_IDS)
MATCH (v:Visitor_this_year)-[:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl' AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
RETURN count(DISTINCT v) AS session_attendees, count(*) AS total_scans
```

```cypher
// Visitors who attended ≥1 recommended session (treatment only)
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl' AND v.control_group = 0
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended
MATCH (v)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended
RETURN count(DISTINCT v) AS treatment_visitors_with_hit
```

**Fill this table in the report:**

| Stage | Treatment (sent recs) | Control (withheld) | Total |
|-------|:--------------------:|:------------------:|:-----:|
| Registered | 14,160 | 2,496 | 16,656 |
| Attended venue | `[FILL]` | `[FILL]` | `[FILL]` |
| Attended ≥1 session | `[FILL]` | `[FILL]` | `[FILL]` |
| Attended ≥1 **recommended** session | `[FILL]` | — | `[FILL]` |

---

## SECTION 2: CORE A/B TEST RESULTS — PERSONAL AGENDAS

```cypher
// Session-level hit rate: treatment vs control
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl' AND v.control_group IN [0, 1]
  AND (s.show = 'tsl' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(s)
WITH v.control_group AS ctrl, count(a) AS attended, count(CASE WHEN r IS NOT NULL THEN 1 END) AS hits
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
WHERE v.show = 'tsl' AND v.control_group IN [0, 1]
  AND (s.show = 'tsl' OR s.show IS NULL) AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended_sessions
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended_sessions
WITH v.control_group AS ctrl, v, CASE WHEN count(rec) > 0 THEN 1 ELSE 0 END AS had_hit
RETURN 
  CASE ctrl WHEN 1 THEN 'Control' ELSE 'Treatment' END AS group_name,
  count(v) AS attendees,
  sum(had_hit) AS with_hit,
  round(100.0 * sum(had_hit) / count(v), 1) AS visitor_hit_rate_pct
ORDER BY ctrl
```

```cypher
// Segmented hit rate: new vs returning (required due to 5.9pp control group skew)
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl' AND v.control_group IN [0, 1]
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended_sessions
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended_sessions
OPTIONAL MATCH (v)-[:Same_Visitor]->()
WITH v.control_group AS ctrl,
     CASE WHEN EXISTS((v)-[:Same_Visitor]->()) THEN 'Returning' ELSE 'New' END AS visitor_type,
     v, CASE WHEN count(rec) > 0 THEN 1 ELSE 0 END AS had_hit
RETURN visitor_type,
  CASE ctrl WHEN 1 THEN 'Control' ELSE 'Treatment' END AS group_name,
  count(v) AS attendees, sum(had_hit) AS with_hit,
  round(100.0 * sum(had_hit) / count(v), 1) AS visitor_hit_rate_pct
ORDER BY visitor_type, ctrl
```

**Fill this scorecard table:**

| Metric | Treatment | Control (Organic) | Lift | vs Benchmark |
|--------|:---------:|:-----------------:|:----:|:------------:|
| Session-level hit rate | `[FILL]%` | `[FILL]%` | `[FILL]pp` | `[vs 34.4% LVS]` |
| Visitor-level hit rate | `[FILL]%` | `[FILL]%` | `[FILL]pp` | `[vs 34.4% LVS]` |
| Relative lift | — | — | `[FILL]%` | — |
| Statistical significance | — | — | p=`[FILL]` | `[✅/🔴]` |

**New visitors — Visitor hit rate:** Treatment `[FILL]%` vs Control `[FILL]%` → **Lift `[FILL]pp`**

**Returning visitors — Visitor hit rate:** Treatment `[FILL]%` vs Control `[FILL]%` → **Lift `[FILL]pp`**

*(Note: control group slightly over-represents returning visitors — 41.9% vs 36.0% treatment — so segmented lift figures are the primary reference)*

---

## SECTION 3: ENGAGEMENT CAMPAIGN RESULTS

```cypher
// Engagement hit rate summary
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl' AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: 'tsl_engagement_20260219T205354Z_c3f8fb55'}]->(s)
OPTIONAL MATCH (d:CampaignDelivery {run_id: 'tsl_engagement_20260219T205354Z_c3f8fb55'})-[:FOR_VISITOR]->(v)
WITH CASE d.status WHEN 'withheld_control' THEN 'Control' ELSE 'Treatment' END AS grp,
     count(a) AS attended, count(CASE WHEN r IS NOT NULL THEN 1 END) AS hits
WHERE d IS NOT NULL
RETURN grp, sum(attended) AS total_attended, sum(hits) AS total_hits,
  round(100.0 * sum(hits) / sum(attended), 1) AS hit_rate_pct
ORDER BY grp
```

| Metric | Engagement Treatment | Engagement Control | Lift |
|--------|:-------------------:|:-----------------:|:----:|
| Session-level hit rate | `[FILL]%` | `[FILL]%` | `[FILL]pp` |
| Audience | 39,572 sent | 6,983 withheld | — |

---

## SECTION 4: TOP SESSIONS — RECOMMENDED VS ACTUAL

```cypher
// Top 10 most recommended vs attendance
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(s:Sessions_this_year)
WHERE v.show = 'tsl' AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH s, count(DISTINCT v) AS recs
OPTIONAL MATCH (v2:Visitor_this_year)-[:assisted_session_this_year]->(s)
WITH s, recs, count(DISTINCT v2) AS attendance
RETURN s.title, s.stream, recs, attendance,
  round(toFloat(attendance)/recs*100, 0) AS conversion_pct
ORDER BY recs DESC LIMIT 10
```

```cypher
// Top 10 most attended sessions (actual popularity)
MATCH (v:Visitor_this_year)-[:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = 'tsl' AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH s, count(DISTINCT v) AS attendance
OPTIONAL MATCH (v2:Visitor_this_year)-[r:IS_RECOMMENDED {run_id: 'tsl_personal_agendas_20260219T124351'}]->(s)
WITH s, attendance, count(DISTINCT v2) AS recs
RETURN s.title, s.stream, attendance, recs,
  CASE WHEN recs > 0 THEN round(toFloat(attendance)/recs*100, 0) ELSE null END AS conversion_pct
ORDER BY attendance DESC LIMIT 10
```

**Flag any sessions with conversion_pct > 200% as under-recommended opportunities for TSL 2027.**

---

## SECTION 5: SYSTEM PERFORMANCE SCORECARD

| Metric | Pre-Show | Post-Show | Change | Status |
|--------|:--------:|:---------:|:------:|:------:|
| Recommendation coverage | 100% | `[FILL]%` | — | `[✅/⚠️]` |
| Venue attendance rate | — | `[FILL]%` | — | — |
| Session engagement rate | — | `[FILL]%` | — | — |
| Visitor-level hit rate (treatment) | benchmark 34.4% | `[FILL]%` | `[FILL]pp` | `[✅/⚠️/🔴]` |
| Absolute recommendation lift | target >5pp | `[FILL]pp` | — | `[✅/⚠️/🔴]` |
| Statistical significance (p-value) | target <0.05 | `[FILL]` | — | `[✅/⚠️/🔴]` |
| Overall system grade | B+ (85/100) | `[FILL]/100` | `[FILL]` | — |

---

## SECTION 6: KEY FINDINGS & NEXT EVENT PRIORITIES

Summarise in **3 bullet points per category**:

**✅ What Worked:**
- `[FILL]`
- `[FILL]`
- `[FILL]`

**⚠️ What Needs Improvement:**
- `[FILL]`
- `[FILL]`
- `[FILL]`

**🎯 Top 3 Actions for TSL 2027:**
1. `[FILL]`
2. `[FILL]`
3. `[FILL]`

---

## REPORT OUTPUT FORMAT

```
# Tech Show London 2026 — Post-Show Recommendation System: Executive Summary

Event: Tech Show London 2026 | Dates: 4–5 March 2026
Report Date: [CURRENT_DATE] | Prepared for: Senior Management

---

## Visitor Journey Funnel
[Funnel table — Section 1]

---

## A/B Test Results: Did Recommendations Work?
[Scorecard table — Section 2, with segmented results]
[One paragraph: bottom line on whether recommendations drove attendance]

---

## Engagement Campaign Results
[Table — Section 3]

---

## Top Sessions: Recommended vs Reality
[Top 10 recommended | Top 10 actual — Section 4]
[Flag under-recommended sessions]

---

## System Performance Scorecard
[Table — Section 5]

---

## Key Findings & Priorities for TSL 2027
[Bullet points — Section 6]

---
Report generated: [DATE] | Data source: Neo4j Production
```

---

## FILE NAMING CONVENTION

Save report as: `report_tsl_post_show_summary_[YYYYMMDD].md`

---

## NOTE

This is the **summary version**. For full technical analysis including segmented A/B tests, co-located show breakdown, V2E exhibitor performance, algorithm grading, and TSL 2027 detailed recommendations, use `prompt_post_show_tsl_2026_long.md`.
