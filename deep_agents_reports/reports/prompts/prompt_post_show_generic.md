# Prompt: Post-Show Analysis Report - Generic Template

## Instructions for Agentic Report Generator

You are a **Senior Data Analyst** generating the **POST-SHOW ANALYSIS** report for the specified event. This report analyzes recommendation system performance by comparing pre-show recommendations against actual post-show attendance data collected through badge scan systems.

---

## CONTEXT VARIABLES (To be filled for each event)

### Configuration File Mappings
Each placeholder should be replaced with values from the event's configuration YAML file:

- **Event**: `[EVENT_NAME]` → Use `event.main_event_name` from config (e.g., "lva", "cpcn", "ecomm")
- **Year**: `[YEAR]` → Use `event.year` from config (e.g., 2025)
- **Show Code**: `[SHOW_CODE]` → Use `event.name` or `neo4j.show_name` from config
- **Database**: Neo4j `[ENVIRONMENT]` → Specify environment (Production/Test/Dev)
- **Database Connection**: `[DATABASE_CONNECTION]` → Use connection string (e.g., "neo4j-prod", "neo4j-test")
- **Configuration File**: `[CONFIG_FILE_PATH]` → Path to config file (e.g., "config/config_vet_lva.yaml")
- **Processing Mode**: `[MODE]` → Use `mode` from config (should be "post_analysis")
- **Analysis Date**: `[CURRENT_DATE]` → Current date of analysis
- **Pre-Show Report Reference**: `[PRE_SHOW_REPORT_PATH]` → Path to the last pre-show report for comparison
- **Pre-Show Report Date**: `[PRE_SHOW_REPORT_DATE]` → Date of the last pre-show report
- **Scan Data Processed Date**: `[SCAN_DATA_DATE]` → Date badge scan data was processed

This is an analysis of **POST-SHOW** performance. The event has concluded and badge scan data has been processed and loaded into Neo4j.

### Quick Configuration Reference Table

| Placeholder | Config Path | Example Values | Usage |
|-------------|------------|----------------|-------|
| `[SHOW_CODE]` | `event.name` or `neo4j.show_name` | "lva", "cpcn", "ecomm" | Query filtering |
| `[EVENT_NAME]` | `event.main_event_name` | "London Vet Show", "Clinical Pharmacy Congress North" | Report title |
| `[YEAR]` | `event.year` | 2025 | Year reference |
| `[MODE]` | `mode` | "post_analysis" | Processing type |
| `[ATTRIBUTE_NAME]` | Keys from `recommendation.similarity_attributes` | "job_role", "workplace", etc. | Demographics |
| `[MAX_RECOMMENDATIONS]` | `recommendation.max_recommendations` | 10 | Target comparison |
| `[MIN_SIMILARITY_SCORE]` | `recommendation.min_similarity_score` | 0.3 | Threshold |
| `[SIMILAR_VISITORS_COUNT]` | `recommendation.similar_visitors_count` | 3, 5, 7 | Collaborative filtering |
| `[FILTERING_ENABLED]` | `recommendation.enable_filtering` | true/false | Event rules |
| `[CAPACITY_ENABLED]` | `recommendation.theatre_capacity_limits.enabled` | true/false | Capacity planning |
| `[OVERLAP_RESOLUTION]` | `recommendation.resolve_overlapping_sessions_by_similarity` | true/false | Overlap handling |

---

## DATABASE SCHEMA

Connected to Neo4j with:
- `Visitor_this_year` nodes (current event registrations)
- `Sessions_this_year` nodes (current event sessions)
- `Stream` nodes (session categories/topics)
- `IS_RECOMMENDED` relationships (generated recommendations)
- **`assisted_session_this_year` relationships (actual session attendance from badge scans)**
- **`registered_to_show` relationships (venue entry scans)**
- `Same_Visitor` relationships (linking current to past attendees)
- `HAS_STREAM` relationships (session → stream assignments)
- Historical data: `Visitor_last_year_*`, `attended_session` relationships

Note: Node label naming may reflect legacy conventions, not actual event allocation.

---

## CRITICAL: SPECIAL EVENTS EXCLUSION METHODOLOGY

### Identifying Pure Special Events (MUST DO FIRST)

**BEFORE calculating any performance metrics**, identify and exclude sessions that have **ONLY** the "Awards and Special Events" stream (no other streams) AND have ZERO recommendations.

**Query 0.1: Identify Pure Special Events (Excluded)**
```cypher
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]' OR s.show IS NULL
OPTIONAL MATCH (s)-[:HAS_STREAM]->(stream:Stream)
WITH s, COLLECT(DISTINCT stream.stream) AS streams
WHERE SIZE(streams) = 1 AND 'Awards and Special Events' IN streams
OPTIONAL MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WITH s, streams, COUNT(r) AS rec_count
WHERE rec_count = 0
RETURN s.session_id AS session_id, s.title AS title, streams, rec_count
```

**Inclusion Rules:**
- ✅ **INCLUDE** sessions with "Awards and Special Events" + other streams
- ✅ **INCLUDE** sessions with "Awards and Special Events" that HAVE recommendations (in the funnel)
- ❌ **EXCLUDE** sessions with ONLY "Awards and Special Events" stream AND ZERO recommendations

**Rationale for Exclusion:**
- Pure special events (keynotes, ceremonies, private events) with zero recommendations are non-targetable content
- They appeal universally regardless of role/specialization
- Visitors discover them through event marketing, not recommendations
- Including them would skew metrics (e.g., 1,500+ attendee keynote with 0 recs would inflate "missed" statistics)

**Report Requirement:**
Document excluded special events separately with attendance counts and explanation.

---

## TASK LIST FOR REPORT GENERATION

### TASK 0: SPECIAL EVENTS IDENTIFICATION (PREREQUISITE)

**Query 0.1: Identify Sessions to Exclude**
```cypher
// Sessions with ONLY "Awards and Special Events" stream AND zero recommendations
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]' OR s.show IS NULL
OPTIONAL MATCH (s)-[:HAS_STREAM]->(stream:Stream)
WITH s, COLLECT(DISTINCT stream.stream) AS streams
WHERE SIZE(streams) = 1 AND 'Awards and Special Events' IN streams
OPTIONAL MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WITH s, streams, COUNT(r) AS rec_count
WHERE rec_count = 0
OPTIONAL MATCH (v2:Visitor_this_year)-[a:assisted_session_this_year]->(s)
RETURN s.session_id AS session_id, s.title AS title, COUNT(DISTINCT v2) AS attendance, rec_count
ORDER BY attendance DESC
```

**Query 0.2: Identify Special Events IN the Funnel (Not Excluded)**
```cypher
// Special events that WERE recommended (keep in analysis)
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]' OR s.show IS NULL
OPTIONAL MATCH (s)-[:HAS_STREAM]->(stream:Stream)
WITH s, COLLECT(DISTINCT stream.stream) AS streams
WHERE 'Awards and Special Events' IN streams
OPTIONAL MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WITH s, streams, COUNT(r) AS rec_count
WHERE rec_count > 0
OPTIONAL MATCH (v2:Visitor_this_year)-[a:assisted_session_this_year]->(s)
RETURN s.session_id AS session_id, s.title AS title, COUNT(DISTINCT v2) AS attendance, rec_count
ORDER BY attendance DESC
```

**Output Requirements:**
- List of excluded session IDs (use in subsequent queries with `NOT IN`)
- List of included special events with recommendation counts
- Total excluded vs included special events

---

### TASK 1: EXECUTIVE SUMMARY & KEY METRICS

**Query 1.1: Total Registered Visitors**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
RETURN count(v) AS total_registered
```

**Query 1.2: Visitors with Recommendations**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED]->()
WITH v, COUNT(r) AS rec_count
RETURN 
  COUNT(CASE WHEN rec_count > 0 THEN 1 END) AS visitors_with_recs,
  COUNT(CASE WHEN rec_count = 0 THEN 1 END) AS visitors_without_recs,
  COUNT(v) AS total
```

**Query 1.3: Venue Attendance (registered_to_show)**
```cypher
MATCH (v:Visitor_this_year)-[r:registered_to_show]->()
WHERE v.show = '[SHOW_CODE]'
RETURN count(DISTINCT v) AS venue_attendance
```

**Query 1.4: Session Attendance (excluding specified sessions)**
```cypher
// Replace [EXCLUDED_SESSION_IDS] with comma-separated list from Task 0
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' 
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
RETURN 
  COUNT(DISTINCT v) AS visitors_attended_sessions,
  COUNT(a) AS total_attendances
```

**Query 1.5: Total Recommendations Generated**
```cypher
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
RETURN count(r) AS total_recommendations
```

**Query 1.6: Session-Level Hit Rate**
```cypher
// Sessions attended that were recommended / Total sessions attended
// Exclude special events from analysis
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' 
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED]->(s)
WITH v, s, a, CASE WHEN r IS NOT NULL THEN 1 ELSE 0 END AS was_recommended
RETURN 
  COUNT(a) AS total_attended,
  SUM(was_recommended) AS attended_and_recommended,
  toFloat(SUM(was_recommended)) / COUNT(a) * 100 AS session_hit_rate_pct
```

**Query 1.7: Visitor-Level Hit Rate**
```cypher
// Visitors who attended at least one recommended session
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' 
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, COLLECT(DISTINCT s.session_id) AS attended_sessions
MATCH (v)-[r:IS_RECOMMENDED]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended_sessions
WITH v, COUNT(DISTINCT rec) AS recommended_attended
RETURN COUNT(DISTINCT v) AS visitors_with_hit
```

**Query 1.8: Average Sessions per Attendee**
```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' 
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, COUNT(a) AS sessions_attended
RETURN 
  AVG(sessions_attended) AS avg_sessions_per_attendee,
  MIN(sessions_attended) AS min_sessions,
  MAX(sessions_attended) AS max_sessions,
  percentileCont(sessions_attended, 0.25) AS p25,
  percentileCont(sessions_attended, 0.5) AS median,
  percentileCont(sessions_attended, 0.75) AS p75
```

**Output Requirements:**
- Executive summary with all key metrics
- Special events exclusion summary (3 excluded, 6 included, etc.)
- Critical gaps identified (visitors without recs, sessions never rec'd)
- Success indicators (returning visitor boost, new features performance)
- Bottom line assessment

---

### TASK 2: PRE-SHOW VS POST-SHOW COMPARISON

**Query 2.1: Database Growth After Final Run**
```cypher
// Compare current visitor count to pre-show report
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
RETURN count(v) AS post_show_visitors
// Compare to [PRE_SHOW_VISITOR_COUNT] from pre-show report
```

**Query 2.2: Sessions Added After Final Run**
```cypher
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]' OR s.show IS NULL
RETURN count(s) AS total_sessions
// Compare to [PRE_SHOW_SESSION_COUNT] from pre-show report
```

**Query 2.3: Sessions Never Recommended**
```cypher
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]' OR s.show IS NULL
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WITH s, COUNT(r) AS rec_count
WHERE rec_count = 0
RETURN COUNT(s) AS sessions_never_recommended, COLLECT(s.title)[0..10] AS sample_titles
```

**Output Requirements:**
- Pre-show vs post-show comparison table
- Visitor growth after final run (count and percentage)
- Session catalog changes (added sessions)
- Gap analysis: late registrations, late sessions

---

### TASK 3: COMPLETE VISITOR JOURNEY FUNNEL

**Query 3.1: Full Funnel Analysis**
```cypher
// Stage 1: Total Registered
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
WITH COUNT(v) AS total_registered
// Stage 2: With Recommendations
MATCH (v:Visitor_this_year)-[:IS_RECOMMENDED]->()
WHERE v.show = '[SHOW_CODE]'
WITH total_registered, COUNT(DISTINCT v) AS with_recommendations
// Stage 3: Venue Attendance
MATCH (v:Visitor_this_year)-[:registered_to_show]->()
WHERE v.show = '[SHOW_CODE]'
WITH total_registered, with_recommendations, COUNT(DISTINCT v) AS venue_attendance
// Stage 4: Session Attendance
MATCH (v:Visitor_this_year)-[:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH total_registered, with_recommendations, venue_attendance, COUNT(DISTINCT v) AS session_attendance
// Stage 5: Recommended Session Attendance (Hit)
MATCH (v:Visitor_this_year)-[:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
MATCH (v)-[:IS_RECOMMENDED]->(s)
WITH total_registered, with_recommendations, venue_attendance, session_attendance, COUNT(DISTINCT v) AS hit_visitors
RETURN total_registered, with_recommendations, venue_attendance, session_attendance, hit_visitors
```

**Query 3.2: Venue-to-Session Gap Analysis**
```cypher
// Visitors who attended venue but NO sessions
MATCH (v:Visitor_this_year)-[:registered_to_show]->()
WHERE v.show = '[SHOW_CODE]'
WITH COLLECT(DISTINCT v.BadgeId) AS venue_visitors
MATCH (v2:Visitor_this_year)-[:assisted_session_this_year]->()
WHERE v2.show = '[SHOW_CODE]'
WITH venue_visitors, COLLECT(DISTINCT v2.BadgeId) AS session_visitors
RETURN 
  SIZE(venue_visitors) AS venue_count,
  SIZE(session_visitors) AS session_count,
  SIZE([x IN venue_visitors WHERE NOT x IN session_visitors]) AS venue_only
```

**Output Requirements:**
- Visual funnel diagram with percentages at each stage
- Conversion rates between stages
- Venue-to-session gap analysis
- Insights on why visitors may not attend sessions

---

### TASK 4: RECOMMENDATION PERFORMANCE ANALYSIS

**Query 4.1: Hit Rate by Visitor Segment (Returning vs New)**
```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[sv:Same_Visitor]->()
WITH v, s, a, CASE WHEN sv IS NOT NULL THEN 'Returning' ELSE 'New' END AS visitor_type
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED]->(s)
WITH visitor_type, COUNT(a) AS total_attended, 
     SUM(CASE WHEN r IS NOT NULL THEN 1 ELSE 0 END) AS hits
RETURN visitor_type, total_attended, hits,
       toFloat(hits) / total_attended * 100 AS hit_rate_pct
ORDER BY visitor_type
```

**Query 4.2: Session-Level Performance (Top 20 Most Recommended)**
```cypher
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]' OR s.show IS NULL
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WITH s, COUNT(r) AS rec_count
OPTIONAL MATCH (v2:Visitor_this_year)-[a:assisted_session_this_year]->(s)
WITH s, rec_count, COUNT(DISTINCT v2) AS attendance
WHERE rec_count > 0
RETURN s.session_id, s.title, s.sponsored_session, rec_count, attendance,
       toFloat(attendance) / rec_count * 100 AS conversion_pct
ORDER BY rec_count DESC
LIMIT 20
```

**Query 4.3: Best Converting Sessions (min 50 recommendations)**
```cypher
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]' OR s.show IS NULL
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WITH s, COUNT(r) AS rec_count
WHERE rec_count >= 50
OPTIONAL MATCH (v2:Visitor_this_year)-[a:assisted_session_this_year]->(s)
WITH s, rec_count, COUNT(DISTINCT v2) AS attendance
RETURN s.session_id, s.title, rec_count, attendance,
       toFloat(attendance) / rec_count * 100 AS conversion_pct
ORDER BY conversion_pct DESC
LIMIT 20
```

**Query 4.4: Most Attended Sessions (Actual Popularity)**
```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' 
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH s, COUNT(a) AS attendance
OPTIONAL MATCH (v2:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WITH s, attendance, COUNT(r) AS rec_count
RETURN s.session_id, s.title, attendance, rec_count,
       CASE WHEN rec_count > 0 THEN toFloat(attendance) / rec_count * 100 ELSE 0 END AS conversion_pct
ORDER BY attendance DESC
LIMIT 20
```

**Query 4.5: Concentration Analysis**
```cypher
// Most recommended session vs visitor reach
MATCH (s:Sessions_this_year)<-[r:IS_RECOMMENDED]-(v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]' AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
WITH s, COUNT(DISTINCT v) AS visitors_reached
ORDER BY visitors_reached DESC
LIMIT 1
MATCH (v2:Visitor_this_year)-[:IS_RECOMMENDED]->()
WHERE v2.show = '[SHOW_CODE]'
WITH s, visitors_reached, COUNT(DISTINCT v2) AS total_visitors_with_recs
RETURN s.title, visitors_reached, total_visitors_with_recs,
       toFloat(visitors_reached) / total_visitors_with_recs * 100 AS concentration_pct
```

**Output Requirements:**
- Hit rate comparison table (returning vs new visitors)
- Top 20 most recommended sessions with conversion rates
- Best converting sessions
- Most attended sessions (popularity analysis)
- Concentration analysis vs previous events

---

### TASK 5: GAP ANALYSIS

**Query 5.1: Visitors Without Recommendations Who Attended**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED]->()
WITH v, COUNT(r) AS rec_count
WHERE rec_count = 0
OPTIONAL MATCH (v)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, COUNT(a) AS sessions_attended
RETURN 
  COUNT(v) AS total_without_recs,
  COUNT(CASE WHEN sessions_attended > 0 THEN 1 END) AS attended_anyway,
  SUM(sessions_attended) AS total_attendances_without_recs
```

**Query 5.2: Sessions Never Recommended But Had Attendance**
```cypher
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]' OR s.show IS NULL
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WITH s, COUNT(r) AS rec_count
WHERE rec_count = 0
OPTIONAL MATCH (v2:Visitor_this_year)-[a:assisted_session_this_year]->(s)
WITH s, COUNT(a) AS attendance
WHERE attendance > 0
RETURN s.session_id, s.title, s.sponsored_session, attendance
ORDER BY attendance DESC
```

**Query 5.3: Sponsored Session Coverage**
```cypher
MATCH (s:Sessions_this_year)
WHERE (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND s.sponsored_session IS NOT NULL AND s.sponsored_session <> ''
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WITH s, COUNT(r) AS rec_count
RETURN 
  COUNT(s) AS total_sponsored,
  COUNT(CASE WHEN rec_count > 0 THEN 1 END) AS sponsored_with_recs,
  COUNT(CASE WHEN rec_count = 0 THEN 1 END) AS sponsored_never_recommended
```

**Query 5.4: Sponsored Sessions Never Recommended**
```cypher
MATCH (s:Sessions_this_year)
WHERE (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND s.sponsored_session IS NOT NULL AND s.sponsored_session <> ''
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WITH s, COUNT(r) AS rec_count
WHERE rec_count = 0
OPTIONAL MATCH (v2:Visitor_this_year)-[a:assisted_session_this_year]->(s)
RETURN s.session_id, s.title, s.sponsored_by, COUNT(a) AS attendance
ORDER BY attendance DESC
```

**Output Requirements:**
- Visitor coverage gap analysis
- Sessions never recommended but had attendance (with counts)
- Sponsored session coverage metrics
- Root cause analysis for gaps

---

### TASK 6: NEW FEATURES IMPACT ANALYSIS

**Query 6.1: Theatre Capacity Planning Impact**
```cypher
// Analyze recommendation distribution vs theatre capacity
// Check if any sessions were capped
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]' OR s.show IS NULL
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WITH s, COUNT(r) AS rec_count
OPTIONAL MATCH (v2:Visitor_this_year)-[a:assisted_session_this_year]->(s)
WITH s, rec_count, COUNT(a) AS attendance
RETURN s.theatre__name AS theatre, s.title, rec_count, attendance,
       CASE WHEN attendance > rec_count THEN 'Under-recommended' 
            WHEN rec_count > 0 AND attendance = 0 THEN 'No attendance'
            ELSE 'Normal' END AS status
ORDER BY rec_count DESC
LIMIT 30
```

**Query 6.2: Overlapping Session Resolution Check**
```cypher
// Check for visitors with recommendations to overlapping sessions
// This should be 0 if overlap resolution is working
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s1:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' 
  AND (s1.show = '[SHOW_CODE]' OR s1.show IS NULL)
MATCH (v)-[r2:IS_RECOMMENDED]->(s2:Sessions_this_year)
WHERE s1.session_id < s2.session_id
  AND s1.date = s2.date
  AND s1.start_time = s2.start_time
  AND (s2.show = '[SHOW_CODE]' OR s2.show IS NULL)
RETURN COUNT(*) AS overlapping_recommendation_pairs,
       COUNT(DISTINCT v) AS visitors_with_overlaps
```

**Output Requirements:**
- Theatre capacity planning effectiveness assessment
- Overlapping session resolution results
- Feature status (✅ Working / ⚠️ Needs adjustment / ❌ Not effective)

---

### TASK 7: VISITOR DEMOGRAPHICS ANALYSIS

**Query 7.1: Job Role Distribution**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
RETURN v.job_role AS job_role, COUNT(v) AS count
ORDER BY count DESC
LIMIT 15
```

**Query 7.2: Specialization Distribution**
```cypher
// Replace with appropriate attribute from config
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
RETURN v.[SPECIALIZATION_ATTRIBUTE] AS specialization, COUNT(v) AS count
ORDER BY count DESC
LIMIT 15
```

**Query 7.3: Organization Type Distribution**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
RETURN v.organisation_type AS org_type, COUNT(v) AS count
ORDER BY count DESC
LIMIT 10
```

**Query 7.4: Geographic Distribution**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
RETURN v.Country AS country, COUNT(v) AS count
ORDER BY count DESC
LIMIT 15
```

**Query 7.5: Returning Visitor Analysis**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
OPTIONAL MATCH (v)-[sv:Same_Visitor]->(past)
WITH v, COLLECT(DISTINCT sv.type) AS return_types
RETURN 
  CASE 
    WHEN SIZE(return_types) = 0 THEN 'New Visitor'
    WHEN SIZE(return_types) = 1 THEN return_types[0] + ' only'
    ELSE 'Multiple Events'
  END AS visitor_type,
  COUNT(v) AS count
ORDER BY count DESC
```

**Output Requirements:**
- Final visitor demographics tables
- Returning visitor breakdown
- Comparison to pre-show demographics if changes noted

---

### TASK 8: STREAM PERFORMANCE ANALYSIS

**Query 8.1: Stream Attendance Performance**
```cypher
MATCH (s:Sessions_this_year)-[:HAS_STREAM]->(stream:Stream)
WHERE s.show = '[SHOW_CODE]' OR s.show IS NULL
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s)
WITH stream.stream AS stream_name, COUNT(DISTINCT s) AS session_count, 
     COUNT(a) AS total_attendance
RETURN stream_name, session_count, total_attendance,
       toFloat(total_attendance) / session_count AS avg_per_session
ORDER BY total_attendance DESC
```

**Output Requirements:**
- Stream performance table
- Key insights on clinical vs business content
- Dominant streams analysis

---

### TASK 9: CRITICAL ISSUES DEEP DIVE

**Query 9.1: Under-Recommendation Analysis (Conversion >200%)**
```cypher
// Sessions with massive conversion rates indicate under-recommendation
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]' OR s.show IS NULL
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WITH s, COUNT(r) AS rec_count
WHERE rec_count > 0
OPTIONAL MATCH (v2:Visitor_this_year)-[a:assisted_session_this_year]->(s)
WITH s, rec_count, COUNT(a) AS attendance
WHERE toFloat(attendance) / rec_count > 2.0
RETURN s.session_id, s.title, rec_count, attendance,
       toFloat(attendance) / rec_count * 100 AS conversion_pct
ORDER BY attendance DESC
LIMIT 20
```

**Output Requirements:**
- Under-recommendation problem analysis
- Sponsored session disparity analysis
- Root cause identification
- Other critical issues discovered

---

### TASK 10: SUCCESSES ANALYSIS

**Query 10.1: Well-Converting Sessions**
```cypher
// Sessions where recommendations matched attendance well (40-80% conversion)
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]' OR s.show IS NULL
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WITH s, COUNT(r) AS rec_count
WHERE rec_count >= 30
OPTIONAL MATCH (v2:Visitor_this_year)-[a:assisted_session_this_year]->(s)
WITH s, rec_count, COUNT(a) AS attendance
WITH s, rec_count, attendance, toFloat(attendance) / rec_count * 100 AS conversion
WHERE conversion >= 40 AND conversion <= 80
RETURN s.title, rec_count, attendance, conversion
ORDER BY attendance DESC
LIMIT 15
```

**Output Requirements:**
- List of successes with quantitative evidence
- Feature successes (capacity planning, overlap resolution)
- Algorithm successes (returning visitor boost)

---

### TASK 11: SPECIAL EVENTS ANALYSIS (EXCLUDED SESSIONS)

**Query 11.1: Excluded Sessions Detail**
```cypher
// Already identified in Task 0 - document fully here
MATCH (s:Sessions_this_year)
WHERE s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s)
RETURN s.session_id, s.title, COUNT(a) AS attendance
ORDER BY attendance DESC
```

**Query 11.2: Included Special Events Performance**
```cypher
// Special events that WERE recommended - how did they perform?
// Use session IDs from Task 0.2
MATCH (s:Sessions_this_year)
WHERE s.session_id IN [INCLUDED_SPECIAL_SESSION_IDS]
OPTIONAL MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s)
WITH s, COUNT(r) AS rec_count
OPTIONAL MATCH (v2:Visitor_this_year)-[a:assisted_session_this_year]->(s)
RETURN s.title, rec_count, COUNT(a) AS attendance,
       toFloat(COUNT(a)) / rec_count * 100 AS conversion_pct
ORDER BY attendance DESC
```

**Output Requirements:**
- Full table of excluded sessions with attendance
- Included special events performance
- Recommendations for future handling of special events

---

### TASK 12: PRE-SHOW PREDICTIONS VS REALITY

**Output Requirements:**
- Reference pre-show report concerns and validate them
- Prediction accuracy matrix (what was predicted, what happened)
- What pre-show reports got right/wrong
- Surprises not predicted

---

### TASK 13: CONCLUSIONS AND RECOMMENDATIONS

**Output Requirements:**
- What worked well (with evidence)
- Critical issues identified (with evidence)
- Root cause analysis
- Actionable recommendations for next event:
  - Immediate actions (CRITICAL)
  - Algorithm improvements
  - Process improvements

---

### TASK 14: SUCCESS METRICS FOR NEXT EVENT

**Output Requirements:**
- Metrics table with:
  - Current year values
  - Target for next year
  - Stretch goals
- Metrics to include:
  - Session-level hit rate
  - Visitor hit rate
  - Visitor coverage
  - Sponsored coverage
  - Sessions never recommended
  - Overlapping recommendations
  - Capacity overruns

---

### TASK 15: FINAL ASSESSMENT

**Output Requirements:**
- Bottom line assessment
- System grade (X/100) with breakdown:
  - Algorithm quality
  - Coverage
  - Calibration
  - Business alignment
  - New features
  - Special events handling
- The path forward summary
- Report metadata footer

---

## OUTPUT FORMAT REQUIREMENTS

- **Format**: Markdown with clear hierarchical headers (##, ###, ####)
- **Tables**: Use for all quantitative data presentation
- **Emphasis**: Use **bold** for key metrics and critical findings
- **Icons**: Use ✅ for successes, ⚠️ for issues, 🔴 for critical problems
- **Language**: Clear, actionable, insight-focused
- **Sections**: Follow the 15-task structure (Task 0-15)

---

## CRITICAL FOCUS AREAS

**Post-Show Specific Checks:**
1. ✅ **Hit Rate Analysis**: Session-level and visitor-level hit rates
2. ✅ **Gap Analysis**: Visitors without recs, sessions never recommended
3. ✅ **Conversion Analysis**: Which recommendations led to attendance
4. ✅ **Feature Validation**: Capacity planning, overlap resolution effectiveness
5. ✅ **Sponsor Coverage**: % of sponsored sessions that received recommendations
6. ✅ **Pre-Show Validation**: Compare predictions to reality

**Event-Specific Checks:**
- Review configuration file for event-specific rules and features
- Validate filtering rule effectiveness through actual attendance
- Check if returning visitor boost delivered results

---

## COMPARISON TO PRE-SHOW REPORT

Compare against `[PRE_SHOW_REPORT_PATH]`:
- Visitor growth after final run
- Session catalog changes
- Prediction accuracy
- Concerns validated or disproven

**Identify:**
- Accurate predictions (✅)
- Inaccurate predictions (🔴)
- Surprises (⚠️)

---

## FILE NAMING CONVENTION

Save report as: `post_show_analysis_[SHOW_CODE]_[YYYYMMDD].md`
- Replace `[SHOW_CODE]` with `event.name` or `neo4j.show_name` from config
- Replace `[YYYYMMDD]` with analysis date

---

## CONFIGURATION FILE ATTRIBUTE MAPPING GUIDE

### Essential Configuration Sections for Post-Show Analysis

#### 1. Event Identification
```yaml
event:
  name: "show_code"           # → Use for [SHOW_CODE] in queries
  main_event_name: "event"    # → Use for [EVENT_NAME] in report title
  year: 2025                  # → Use for [YEAR]

mode: "post_analysis"         # → Confirms post-analysis mode
```

#### 2. Post-Analysis Mode Configuration
```yaml
post_analysis_mode:
  registration_shows:
    this_year_main:
      - ['LVS25']
  scan_files:
    seminars_scan_reference_this: "data/lva/post/lvs25 seminar scans reference.csv"
    seminars_scans_this: "data/lva/post/lvs25 seminar scans.csv"
  entry_scan_files:
    entry_scans_this: ["data/lva/post/lvs25_unfiltered_entry_scans.csv"]
```

#### 3. Recommendation Parameters (for comparison)
```yaml
recommendation:
  min_similarity_score: 0.3   # → Threshold used for recommendations
  max_recommendations: 10     # → Target per visitor
  similar_visitors_count: 3   # → Collaborative filtering parameter
  enable_filtering: true      # → Event-specific rules active
  
  returning_without_history:
    enabled: true
    similarity_exponent: 1.5  # → Boost for returning visitors
  
  theatre_capacity_limits:
    enabled: true
    capacity_multiplier: 3.0  # → Capacity planning settings
  
  resolve_overlapping_sessions_by_similarity: true  # → Overlap handling
```

#### 4. Neo4j Relationships for Post-Show
```yaml
neo4j:
  relationships:
    assisted_session_this_year: "assisted_session_this_year"  # Actual attendance
    registered_to_show: "registered_to_show"  # Venue entry scans
```

### Checklist for Post-Show Analysis

Before running report generation:
- [ ] Verify badge scan data has been processed and loaded
- [ ] Confirm `assisted_session_this_year` relationships exist
- [ ] Confirm `registered_to_show` relationships exist
- [ ] Have the pre-show report available for comparison
- [ ] Verify excluded session IDs have been identified (Task 0)
- [ ] Check `mode: "post_analysis"` in config

---

## ADDITIONAL NOTES

- This is a **generic post-show template** applicable to any event type
- Special events exclusion must happen FIRST before any metrics
- Always compare against the pre-show report for validation
- Badge scan data must be fully processed before running this report
- Document all assumptions and exclusions clearly

---

### TASK 16: REPORT ENRICHMENT & EXECUTIVE WRAP-UP

After you have completed Tasks 0-15:

1. **Cross-check coverage**
   - Confirm special events exclusion methodology is documented
   - Verify all performance metrics exclude special events consistently
   - Check that pre-show predictions are validated
   - Ensure all gaps have root cause analysis

2. **Executive wrap-up subsection**
   - Under the Final Assessment section, add a short **"Executive Wrap-Up"** subsection that:
     - Summarizes 3-5 key achievements (The Good)
     - Summarizes 3-5 critical gaps (The Bad)
     - Highlights 3 clear business opportunities (The Opportunity)
     - Ends with a single bottom-line sentence starting with **"Bottom line:"**

3. **Make action items explicit**
   - Ensure each recommendation includes:
     - **Priority level** (CRITICAL, HIGH, MEDIUM)
     - **Expected impact** (short phrase)
     - **Timeline** (immediate, short-term, medium-term)

4. **Methodology notes**
   - Include a clear methodology note explaining special events exclusion
   - Document any assumptions made during analysis
   - Reference the exact session IDs excluded

---

**Generate the comprehensive post-show analysis report now, following all 16 tasks sequentially.**