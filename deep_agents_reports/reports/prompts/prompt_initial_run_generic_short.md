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


**Generate the comprehensive report now, following all 2 tasks sequentially.**