# Prompt: Initial Pre-Show Run Report - Generic Template

## Instructions for Agentic Report Generator

You are a **Senior Data Analyst** generating the **INITIAL PRE-SHOW** recommendation system analysis report for the specified event.

---

## CONTEXT VARIABLES (To be filled for each event)

### Configuration File Mappings
Each placeholder should be replaced with values from the event's configuration YAML file:

- **Event**: `[EVENT_NAME]` → Use `event.main_event_name` from config (e.g., "lva", "cpcn", "ecomm")
- **Show Code**: `[SHOW_CODE]` → Use `event.name` or `neo4j.show_name` from config
- **Database**: Neo4j `[ENVIRONMENT]` → Specify environment (Production/Test/Dev)
- **Database Connection**: `[DATABASE_CONNECTION]` → Use connection string (e.g., "neo4j-prod", "neo4j-test")
- **Configuration File**: `[CONFIG_FILE_PATH]` → Path to config file (e.g., "config/config_cpcn.yaml")
- **Processing Mode**: `[MODE]` → Use `mode` from config (typically "personal_agendas" or "engagement")
- **Analysis Date**: `[CURRENT_DATE]` → Current date of analysis
- **Last Pipeline Run**: `[PIPELINE_RUN_DATE]` → Date/time of last pipeline execution
- **Pipeline Duration**: `[DURATION]` → Execution time (e.g., "17 minutes", "25 minutes")

This is an analysis of the **LATEST** recommendation run. The system generated personalized session recommendations for all registered visitors using event-specific filtering rules and attribute mappings.

### Quick Configuration Reference Table

| Placeholder | Config Path | Example Values | Usage |
|-------------|------------|----------------|-------|
| `[SHOW_CODE]` | `event.name` or `neo4j.show_name` | "lva", "cpcn", "ecomm" | Query filtering |
| `[EVENT_NAME]` | `event.main_event_name` | "London Vet Show", "Clinical Pharmacy Congress North" | Report title |
| `[MODE]` | `mode` | "personal_agendas", "engagement" | Processing type |
| `[ATTRIBUTE_NAME]` | Keys from `recommendation.similarity_attributes` | "job_role", "workplace", etc. | Demographics |
| `[MAX_RECOMMENDATIONS]` | `recommendation.max_recommendations` | 10 | Target comparison |
| `[MIN_SIMILARITY_SCORE]` | `recommendation.min_similarity_score` | 0.3 | Threshold |
| `[SIMILAR_VISITORS_COUNT]` | `recommendation.similar_visitors_count` | 3, 5, 7 | Collaborative filtering |
| `[FILTERING_ENABLED]` | `recommendation.enable_filtering` | true/false | Event rules |

---

## DATABASE SCHEMA

Connected to Neo4j with:
- `Visitor_this_year` nodes (current event registrations)
- `Visitor_last_year_bva` nodes (main event prior year attendees)
- `Visitor_last_year_lva` nodes (secondary event prior year attendees)
- `Sessions_this_year` nodes (current event sessions)
- `Sessions_past_year` nodes (mixed legacy sessions from prior events)
- `Stream` nodes (session categories/topics)
- `IS_RECOMMENDED` relationships (generated recommendations)
- `Same_Visitor` relationships (linking current to past attendees)
- `attended_session` relationships (historical attendance)
- `HAS_STREAM` relationships (session → stream assignments)

Note: Node label naming may reflect legacy conventions, not actual event allocation.

---

## TASK LIST FOR REPORT GENERATION

### TASK 1: EVENT OVERVIEW & EXECUTIVE SUMMARY

**Query 1.1: Total Visitors**
```cypher
MATCH (v:Visitor_this_year) 
WHERE v.show = '[SHOW_CODE]' 
RETURN count(v) as total_visitors
```

**Query 1.2: Visitors with Recommendations**
```cypher
MATCH (v:Visitor_this_year)-[:IS_RECOMMENDED]->() 
WHERE v.show = '[SHOW_CODE]' 
RETURN count(DISTINCT v) as visitors_with_recommendations
```

**Query 1.3: Total Recommendations**
```cypher
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s:Sessions_this_year) 
WHERE v.show = '[SHOW_CODE]' AND s.show = '[SHOW_CODE]' 
RETURN count(r) as total_recommendations
```

**Query 1.4: Average Recommendations per Visitor**
```cypher
MATCH (v:Visitor_this_year) 
WHERE v.show = '[SHOW_CODE]'
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED]->(s:Sessions_this_year) 
WHERE s.show = '[SHOW_CODE]'
WITH v, count(r) as rec_count
RETURN avg(rec_count) as avg_recommendations_per_visitor
```

**Query 1.5: Returning Visitors Count**
```cypher
MATCH (v:Visitor_this_year)-[r:Same_Visitor]->() 
WHERE v.show = '[SHOW_CODE]' 
RETURN r.type as event_type, count(DISTINCT v) as returning_visitors
```

**Output Requirements:**
- Executive summary table with key metrics
- Recommendation coverage percentage calculation
- Critical findings identification (successes vs. issues)
- Comparison to target metrics

---

### TASK 2: VISITOR DEMOGRAPHICS & RETENTION

**Query 2.1: Visitor Types (New vs Returning)**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]' 
OPTIONAL MATCH (v)-[sr:Same_Visitor]->()
WITH v, collect(sr.type) as return_types
RETURN 
  CASE 
    WHEN size(return_types) = 0 THEN 'New'
    WHEN size(return_types) = 1 THEN return_types[0]
    ELSE 'Multiple'
  END as visitor_type,
  count(v) as count
```

**Query 2.2: Demographic Attributes Analysis**
For each configured demographic attribute from `recommendation.similarity_attributes` in config:
```cypher
-- Replace [ATTRIBUTE_NAME] with each key from recommendation.similarity_attributes
-- Examples from config files:
-- Veterinary: job_role, what_type_does_your_practice_specialise_in, organisation_type
-- Pharmacy: you_are_a, which_of_the_following_best_describes_your_primary_place_of_work
-- Generic pattern:
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
RETURN v.[ATTRIBUTE_NAME] as value, count(v) as count
ORDER BY count DESC
LIMIT 15
```

**Configuration Mapping for Attributes:**
- Look in `recommendation.similarity_attributes` section
- Each key is a visitor attribute to analyze
- Weight values indicate importance (higher weight = more important for analysis)

**Query 2.3: Geographic Distribution**
```cypher
-- Country field is typically standard across events
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
RETURN v.Country as country, count(v) as count
ORDER BY count DESC
LIMIT 15
```

**Output Requirements:**
- Overall visitor metrics table
- Returning visitor analysis with percentages
- Demographic distribution tables for each key attribute
- Geographic distribution table

---

### TASK 3: DATA QUALITY & COMPLETENESS

**Query 3.1: Attribute Completeness Check**
For each key attribute from `recommendation.similarity_attributes`:
```cypher
-- Replace [ATTRIBUTE_NAME] with each attribute from config
-- Example: for config key "job_role" with weight 0.8
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
RETURN 
  '[ATTRIBUTE_NAME]' as attribute,
  count(DISTINCT v.[ATTRIBUTE_NAME]) as unique_values,
  count(CASE WHEN v.[ATTRIBUTE_NAME] IS NOT NULL AND v.[ATTRIBUTE_NAME] <> 'NA' THEN 1 END) as filled_count,
  count(CASE WHEN v.[ATTRIBUTE_NAME] IS NULL OR v.[ATTRIBUTE_NAME] = 'NA' THEN 1 END) as na_count,
  count(v) as total,
  toFloat(count(CASE WHEN v.[ATTRIBUTE_NAME] IS NOT NULL AND v.[ATTRIBUTE_NAME] <> 'NA' THEN 1 END)) / count(v) * 100 as fill_rate
```

**Configuration Source:**
- Primary attributes: `recommendation.similarity_attributes` keys
- Default NA value: Check `default_visitor_properties` for NA patterns
- Additional fields: `recommendation.export_additional_visitor_fields` (if needed)

**Query 3.2: Identify "Other" Categories**
```cypher
-- Check for "Other" values in key demographic fields
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]' 
  AND v.[ATTRIBUTE_NAME] CONTAINS 'Other'
RETURN v.[ATTRIBUTE_NAME] as value, count(v) as count
ORDER BY count DESC
```

**Output Requirements:**
- Attribute completeness table (attribute name, unique values, fill rate, NA count)
- Data quality assessment for each key attribute
- Concentration metrics (flag if >20% visitors in single category)
- "Other" category analysis

---

### TASK 4: SESSION ANALYSIS & STREAM COVERAGE

**Query 4.1: Session Inventory**
```cypher
-- Sessions are filtered by show code from event.name or neo4j.show_name
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]'
RETURN count(s) as total_sessions
```

**Query 4.2: Sessions with Stream Relationships**
```cypher
-- HAS_STREAM relationship name from neo4j.relationships.session_stream
MATCH (s:Sessions_this_year)-[:HAS_STREAM]->()
WHERE s.show = '[SHOW_CODE]'
RETURN count(DISTINCT s) as sessions_with_streams
```

**Query 4.3: Stream Distribution**
```cypher
-- Stream node label from neo4j.node_labels.stream
-- Stream relationship from neo4j.relationships.session_stream
MATCH (s:Sessions_this_year)-[:HAS_STREAM]->(st:Stream)
WHERE s.show = '[SHOW_CODE]'
RETURN st.stream as stream_name, count(s) as session_count
ORDER BY session_count DESC
LIMIT 15
```

**Query 4.4: Orphaned Streams**
```cypher
-- Check for streams without any session relationships
MATCH (st:Stream)
WHERE NOT exists((st)<-[:HAS_STREAM]-())
RETURN st.stream as orphaned_stream
```

**Query 4.5: Session Metadata Analysis**
```cypher
-- Session properties vary by event, check actual data model
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]'
RETURN 
  count(DISTINCT s.theatre__name) as unique_theatres,
  count(CASE WHEN s.sponsored_session = 'true' THEN 1 END) as sponsored_sessions
```

**Configuration Notes:**
- Stream processing settings: `stream_processing.use_enhanced_streams_catalog`
- Stream creation: `stream_processing.create_missing_streams`
- Session filtering: Check `titles_to_remove` for excluded session titles

**Output Requirements:**
- Session metrics table
- Stream coverage percentage calculation
- Top streams by session count
- Orphaned streams list
- Theatre and sponsorship analysis

---

### TASK 5: RECOMMENDATION GENERATION ANALYSIS

**Query 5.1: Recommendation Statistics**
```cypher
-- IS_RECOMMENDED relationship from neo4j.relationships (typically standard)
-- Filter by show from event.name or neo4j.show_name
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED]->(s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]'
WITH v, count(r) as rec_count, collect(r.similarity_score) as scores
RETURN 
  count(v) as total_visitors,
  count(CASE WHEN rec_count > 0 THEN 1 END) as visitors_with_recs,
  sum(rec_count) as total_recommendations,
  avg(rec_count) as avg_recs_per_visitor,
  min(rec_count) as min_recs,
  max(rec_count) as max_recs
```

**Configuration Context:**
- Target recommendations: `recommendation.max_recommendations` (typically 10)
- Minimum score threshold: `recommendation.min_similarity_score` (typically 0.3)
- Compare avg_recs_per_visitor to max_recommendations target

**Query 5.2: Recommendation Distribution**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED]->(s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]'
WITH v, count(r) as rec_count
RETURN rec_count, count(v) as visitor_count
ORDER BY rec_count
```

**Query 5.3: Similarity Score Analysis**
```cypher
-- Analyze against min_similarity_score threshold from config
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND s.show = '[SHOW_CODE]'
RETURN 
  min(r.similarity_score) as min_score,
  percentileCont(r.similarity_score, 0.25) as q1,
  percentileCont(r.similarity_score, 0.5) as median,
  avg(r.similarity_score) as avg_score,
  percentileCont(r.similarity_score, 0.75) as q3,
  max(r.similarity_score) as max_score
```

**Query 5.4: Similarity Score Distribution by Range**
```cypher
-- Ranges start at recommendation.min_similarity_score (e.g., 0.3)
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND s.show = '[SHOW_CODE]'
WITH r.similarity_score as score
RETURN 
  CASE
    WHEN score >= 0.3 AND score < 0.4 THEN '0.30-0.39'
    WHEN score >= 0.4 AND score < 0.5 THEN '0.40-0.49'
    WHEN score >= 0.5 AND score < 0.6 THEN '0.50-0.59'
    WHEN score >= 0.6 AND score < 0.7 THEN '0.60-0.69'
    WHEN score >= 0.7 AND score < 0.8 THEN '0.70-0.79'
    WHEN score >= 0.8 AND score < 0.9 THEN '0.80-0.89'
    WHEN score >= 0.9 THEN '0.90-1.00'
    ELSE 'Below threshold'
  END as score_range,
  count(*) as count
ORDER BY score_range
```

**Query 5.5: Unique Sessions Recommended**
```cypher
MATCH (v:Visitor_this_year)-[:IS_RECOMMENDED]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND s.show = '[SHOW_CODE]'
RETURN count(DISTINCT s) as unique_sessions_recommended
```

**Query 5.6: Sessions Never Recommended**
```cypher
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]'
  AND NOT exists(()-[:IS_RECOMMENDED]->(s))
RETURN s.title as session_title, s.stream as stream
ORDER BY s.title
```

**Output Requirements:**
- Overall recommendation statistics table
- Recommendation distribution table and histogram
- Similarity score statistics and distribution
- Sessions coverage analysis
- List of sessions never recommended

---

### TASK 6: TOP RECOMMENDED SESSIONS & CONCENTRATION

**Query 6.1: Top 20 Most Recommended Sessions**
```cypher
MATCH (v:Visitor_this_year)-[:IS_RECOMMENDED]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND s.show = '[SHOW_CODE]'
WITH s, count(DISTINCT v) as rec_count
MATCH (total:Visitor_this_year)
WHERE total.show = '[SHOW_CODE]'
WITH s, rec_count, count(DISTINCT total) as total_visitors
OPTIONAL MATCH (s)-[:HAS_STREAM]->(st:Stream)
RETURN 
  s.title as session_title,
  rec_count as times_recommended,
  toFloat(rec_count) / total_visitors * 100 as percentage_of_visitors,
  collect(DISTINCT st.stream) as streams
ORDER BY rec_count DESC
LIMIT 20
```

**Query 6.2: Concentration Analysis**
```cypher
MATCH (v:Visitor_this_year)-[:IS_RECOMMENDED]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND s.show = '[SHOW_CODE]'
WITH s, count(DISTINCT v) as rec_count
MATCH (total:Visitor_this_year)
WHERE total.show = '[SHOW_CODE]'
WITH s.title as session, 
     toFloat(rec_count) / count(DISTINCT total) * 100 as percentage
ORDER BY percentage DESC
LIMIT 1
RETURN session as most_recommended_session, percentage as max_concentration_percentage
```

**Output Requirements:**
- Top 20 recommended sessions table with visitor percentages
- Concentration problem assessment (flag if any session >95%)
- Stream distribution analysis of top sessions
- Recommendation diversity metrics

---

### TASK 7: HISTORICAL ATTENDANCE INTEGRATION

**Query 7.1: Returning Visitors with Attendance Data**
```cypher
-- Same_Visitor relationship from neo4j.relationships.same_visitor
-- Past visitor node labels from neo4j.node_labels.visitor_last_year_bva/lva
-- attended_session relationship from neo4j.relationships.attended_session
MATCH (v:Visitor_this_year)-[:Same_Visitor]->(vp)
WHERE v.show = '[SHOW_CODE]'
OPTIONAL MATCH (vp)-[a:attended_session]->()
WITH v, labels(vp)[0] as past_visitor_type, 
     CASE WHEN a IS NOT NULL THEN 1 ELSE 0 END as has_attendance
RETURN 
  past_visitor_type,
  count(DISTINCT v) as returning_visitors,
  sum(has_attendance) as with_attendance_data,
  toFloat(sum(has_attendance)) / count(DISTINCT v) * 100 as coverage_percentage
```

**Configuration Context:**
- Main event label: `neo4j.node_labels.visitor_last_year_bva` 
- Secondary event label: `neo4j.node_labels.visitor_last_year_lva`
- Relationship properties: `neo4j.visitor_relationship.same_visitor_properties`
- Historical boost: `recommendation.returning_without_history.enabled`

**Query 7.2: Historical Attendance Statistics**
```cypher
MATCH (v:Visitor_this_year)-[:Same_Visitor]->(vp)-[a:attended_session]->(s)
WHERE v.show = '[SHOW_CODE]'
WITH labels(vp)[0] as visitor_type, v, count(a) as sessions_attended
RETURN 
  visitor_type,
  count(DISTINCT v) as visitors,
  sum(sessions_attended) as total_attendances,
  avg(sessions_attended) as avg_sessions_per_attendee
```

**Configuration Notes:**
- Check `event.shows_last_year_main` for main event history
- Check `event.shows_last_year_secondary` for secondary event history
- Returning visitor boost: `recommendation.returning_without_history.similarity_exponent`

**Output Requirements:**
- Past attendance metrics table by event type
- Historical data coverage percentages
- Analysis of historical data value for recommendations

---

### TASK 8: CONFIGURATION ANALYSIS

**Reference:** Configuration file specified in context

**Extract and Document from Config File:**

1. **Similarity Attributes and Weights** (`recommendation.similarity_attributes`):
   - List each attribute with its weight
   - Example: `job_role: 0.8` means job role matching has 0.8 weight

2. **Recommendation Settings** (`recommendation` section):
   - `min_similarity_score`: Minimum threshold for recommendations
   - `max_recommendations`: Target recommendations per visitor
   - `similar_visitors_count`: Number of similar visitors for collaborative filtering
   - `enable_filtering`: Whether event-specific filtering is active
   - `returning_without_history.enabled`: Boost for returning visitors
   - `returning_without_history.similarity_exponent`: Boost multiplier
   - `theatre_capacity_limits.enabled`: Venue capacity management
   - `resolve_overlapping_sessions_by_similarity`: Clash resolution method

3. **Event-Specific Features**:
   - `neo4j.job_stream_mapping.enabled`: Job to stream mapping active
   - `neo4j.specialization_stream_mapping.enabled`: Specialization mapping active
   - `recommendation.role_groups`: Role categorizations (if defined)
   - `recommendation.field_mappings`: Field name mappings
   - `recommendation.rules_config`: Custom filtering rules

4. **Data Field Mappings**:
   - `neo4j.unique_identifiers.visitor`: Visitor ID field (typically "BadgeId")
   - `neo4j.unique_identifiers.session`: Session ID field
   - `neo4j.unique_identifiers.stream`: Stream ID field
   - `neo4j.node_labels`: Node label names in database

**Output Requirements:**
- Configuration parameters table
- Processing status checklist
- Field mappings documentation
- Assessment of configuration appropriateness

---

### TASK 9: SAMPLE RECOMMENDATION WALKTHROUGH

**Query 9.1: Select Sample Visitors**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND v.has_recommendation = 'true'
RETURN v
LIMIT 3
```

**Query 9.2: For Each Sample Visitor**
```cypher
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s:Sessions_this_year)
WHERE v.BadgeId = '[BADGE_ID]' 
  AND v.show = '[SHOW_CODE]'
  AND s.show = '[SHOW_CODE]'
OPTIONAL MATCH (s)-[:HAS_STREAM]->(st:Stream)
RETURN 
  s.title as session_title,
  r.similarity_score as score,
  collect(st.stream) as streams
ORDER BY r.similarity_score DESC
LIMIT 10
```

**Output Requirements:**
- Sample recommendation tables (one per visitor profile)
- Analysis of recommendation quality and relevance
- Stream coverage assessment

---

### TASK 10: SYSTEM PERFORMANCE ASSESSMENT

**Query 10.1: Processing Metrics**
```cypher
MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->()
WHERE v.show = '[SHOW_CODE]'
RETURN 
  min(r.generated_at) as earliest_generation,
  max(r.generated_at) as latest_generation,
  count(r) as total_relationships_created
```

**Calculate:**
- Pipeline execution time
- Visitors processed per minute
- Recommendations generated per second
- Database response metrics

**Output Requirements:**
- Pipeline performance table
- Performance status assessment

---

### TASK 11: DATA QUALITY SCORECARD

**Calculate Scores:**
1. **Visitor Data Completeness**: (visitors with complete profiles / total visitors) × 100
2. **Session Data Completeness**: (sessions with streams / total sessions) × 100
3. **Stream Taxonomy Utilization**: (active streams / total streams) × 100
4. **Recommendation Generation**: (visitors with recommendations / total visitors) × 100
5. **Overall Data Quality**: Average of all scores

**Output Requirements:**
- Data quality scorecard table
- System strengths (✅)
- System weaknesses (⚠️)
- Overall quality grade

---

### TASK 12: PRIORITY ACTIONS & RECOMMENDATIONS

**Based on Analysis, Identify:**

**Immediate Actions (Week 1):**
- Critical data gaps
- Configuration issues
- Processing errors

**Short-term Actions (Month 1):**
- Data quality improvements
- Algorithm refinements
- Mapping enhancements

**Medium-term Actions (Quarter 1):**
- System optimizations
- Feature additions
- Integration improvements

**Output Requirements:**
- Priority actions organized by timeframe
- Specific parameter adjustment recommendations
- Business opportunities
- Expected impact assessment

---

### TASK 13: CONCLUSION & OVERALL SYSTEM ASSESSMENT

**Synthesize:**
1. Overall system readiness grade (A-F)
2. Strengths summary (✅)
3. Critical issues summary (🔴)
4. Priority actions before event
5. Success metrics to track post-event
6. Bottom line assessment

**Output Requirements:**
- Key achievements list
- Critical gaps requiring attention
- System status by category
- Overall grade with justification
- Final recommendation

---

## OUTPUT FORMAT REQUIREMENTS

- **Format**: Markdown with clear hierarchical headers (##, ###, ####)
- **Tables**: Use for all quantitative data presentation
- **Emphasis**: Use **bold** for key metrics and critical findings
- **Icons**: Use ✅ for strengths, ⚠️ for issues, 🔴 for critical problems
- **Language**: Clear, actionable, insight-focused
- **Sections**: Follow the 13-task structure

---

## CRITICAL FOCUS AREAS

**Universal Checks (All Events):**
1. ✅ **Recommendation Coverage**: % of visitors with recommendations
2. ✅ **Average Recommendations**: Compare to target (typically 10)
3. ✅ **Session Stream Coverage**: % of sessions with stream assignments
4. ✅ **Data Quality**: Completeness of key demographic attributes
5. ✅ **Concentration Risk**: Check if top session reaches >95% of visitors
6. ✅ **Algorithm Performance**: Similarity score distribution and quality

**Event-Specific Checks:**
- Review configuration file for event-specific rules and features
- Validate field mappings and transformations
- Check for event-specific filtering or processing logic

---

## COMPARISON TO BASELINE

If previous reports exist, compare:
- Visitor growth/decline
- Recommendation coverage changes
- Data quality improvements/degradations
- Stream coverage changes
- Algorithm performance metrics

**Identify:**
- Improvements (✅)
- Degradations (🔴)
- Unchanged issues (⚠️)

---

## FILE NAMING CONVENTION

Save report as: `report_[SHOW_CODE]_[YYYYMMDD].md`
- Replace `[SHOW_CODE]` with `event.name` or `neo4j.show_name` from config
- Replace `[YYYYMMDD]` with analysis date

---

## CONFIGURATION FILE ATTRIBUTE MAPPING GUIDE

### Essential Configuration Sections and Their Usage

#### 1. Event Identification
```yaml
event:
  name: "show_code"           # → Use for [SHOW_CODE] in queries
  main_event_name: "event"    # → Use for [EVENT_NAME] in report title
  year: 2025                   # → Event year reference

mode: "personal_agendas"      # → Use for [MODE] in context
```

#### 2. Database Configuration
```yaml
neo4j:
  show_name: "show_code"       # → Alternative for [SHOW_CODE]
  node_labels:
    visitor_this_year: "Visitor_this_year"
    visitor_last_year_bva: "Visitor_last_year_bva"
    visitor_last_year_lva: "Visitor_last_year_lva"
    session_this_year: "Sessions_this_year"
    session_past_year: "Sessions_past_year"
    stream: "Stream"
  unique_identifiers:
    visitor: "BadgeId"         # → Visitor ID field name
    session: "session_id"      # → Session ID field name
```

#### 3. Demographic Attributes for Analysis
```yaml
recommendation:
  similarity_attributes:       # → Each key is an [ATTRIBUTE_NAME] to analyze
    attribute_1: 0.8          # → Include in Task 2 & 3 queries
    attribute_2: 0.6          # → Weight indicates importance
    attribute_3: 0.5          # → Higher weight = more critical to analyze
```

#### 4. Recommendation Parameters
```yaml
recommendation:
  min_similarity_score: 0.3   # → Threshold for recommendations
  max_recommendations: 10     # → Target per visitor (compare in Task 5)
  similar_visitors_count: 3   # → Collaborative filtering parameter
  enable_filtering: true      # → Event-specific rules active
  
  # Optional features
  returning_without_history:
    enabled: true
    similarity_exponent: 1.5
  
  theatre_capacity_limits:
    enabled: false
    capacity_multiplier: 3.0
```

#### 5. Stream Mapping Configuration
```yaml
neo4j:
  job_stream_mapping:
    enabled: true              # → Check in Task 8
    file: "job_to_stream.csv"
    job_role_field: "job_role"
  
  specialization_stream_mapping:
    enabled: true              # → Check in Task 8
    file: "specialization_to_stream.csv"
    specialization_field_this_year: "field_name"
```

#### 6. Default Values for Data Quality
```yaml
default_visitor_properties:   # → Identifies NA patterns
  attribute_1: "NA"           # → Use to detect missing data
  attribute_2: "NA"           # → Check in Task 3
  Country: "UK"               # → Default geographic value
```

### Query Variable Substitution Examples

#### Example 1: Veterinary Event (LVA)
```yaml
event:
  name: "lva"
recommendation:
  similarity_attributes:
    job_role: 0.8
    what_type_does_your_practice_specialise_in: 0.8
    organisation_type: 0.8
```

**Resulting Query for Task 2.2:**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = 'lva'
RETURN v.job_role as value, count(v) as count
ORDER BY count DESC
LIMIT 15
```

#### Example 2: Pharmacy Event (CPCN)
```yaml
event:
  name: "cpcn"
recommendation:
  similarity_attributes:
    you_are_a: 0.7
    which_of_the_following_best_describes_your_primary_place_of_work: 0.8
    as_a_pharmacist_which_of_the_following_most_closely_aligns_to_your_primary_job_role_or_function: 0.5
```

**Resulting Query for Task 2.2:**
```cypher
MATCH (v:Visitor_this_year)
WHERE v.show = 'cpcn'
RETURN v.which_of_the_following_best_describes_your_primary_place_of_work as value, count(v) as count
ORDER BY count DESC
LIMIT 15
```

### Checklist for Configuration Review

Before running report generation:
- [ ] Verify `event.name` or `neo4j.show_name` for [SHOW_CODE]
- [ ] List all keys from `recommendation.similarity_attributes` for demographic analysis
- [ ] Check `mode` value for processing mode context
- [ ] Verify `recommendation.max_recommendations` for target comparison
- [ ] Note if `recommendation.enable_filtering` is true/false
- [ ] Check if stream mappings are enabled in `neo4j` section
- [ ] Review `default_visitor_properties` for NA value patterns

---

## ADDITIONAL NOTES

- This is a **generic template** applicable to any event type
- Configuration file determines event-specific processing
- Database node labels may reflect legacy naming conventions
All queries should filter by show code for multi-event databases
- Pipeline performance and timing should be documented when available

---

### TASK 14: REPORT ENRICHMENT & EXECUTIVE WRAP-UP

After you have completed Tasks 1–13 and the COMPARISON TO BASELINE section:

1. **Cross-check coverage**
   - Confirm that your report includes, at minimum:
     - Visitor–stream mapping coverage and over-broad mapping commentary.
     - Filtering rules verification with rule-by-rule status.
     - Configuration analysis (similarity attributes, key parameters, event-specific flags).
     - Priority actions grouped by timeframe with **Owner** and **Timeline** fields.
     - Comparison to the most recent prior report (if available).

2. **Executive wrap-up subsection**
   - Under the Conclusion section, add a short **"Executive Wrap-Up"** subsection that:
     - Summarizes 3–5 key achievements.
     - Summarizes 3–5 critical risks or gaps.
     - Highlights 3 clear business implications (e.g., retention, sponsor value, cross-event growth).
     - Ends with a single bottom-line sentence starting with **"Bottom line:"**.

3. **Make action items explicit**
   - Ensure each priority action table row includes:
     - **Owner** (team or role responsible).
     - **Timeline** (date or horizon).
     - **Expected Impact** (short phrase, e.g., "increase avg recs", "reduce concentration").

4. **Match best available style and depth**
   - Use the same level of numeric detail, table density, and narrative depth as a strong prior report for this event (for example, a high-quality November 2025 pre-show LVA report), including:
     - Executive summary with metrics and status icons.
     - Detailed sectioned analysis.
     - Actionable recommendations and readiness verdict.

---

**Generate the comprehensive report now, following all 14 tasks sequentially.**