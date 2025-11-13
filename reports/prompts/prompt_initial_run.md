# Prompt: Initial Pre-Show Run Report - LVA 2025 (Latest Run)

## Instructions for Agentic Report Generator

You are a **Senior Data Analyst** generating the **INITIAL PRE-SHOW** recommendation system analysis report for **London Vet Show (LVA) 2025**.

---

## CONTEXT

- **Event**: London Vet Show (LVA) 2025
- **Show Code**: `lva`
- **Database**: Neo4j Production (`neo4j-prod`)
- **Configuration File**: `config_vet_lva.yaml`
- Always reference the current settings in `config_vet_lva.yaml`; legacy Neo4j node labels still reflect older BVA naming.
- **Processing Mode**: Personal Agendas
- **Analysis Date**: October 31, 2025
- **Last Pipeline Run**: October 15, 2025 (17 minutes duration)

This is an analysis of the **LATEST** recommendation run. The system generated personalized session recommendations for all registered visitors using veterinary-specific filtering rules, job role mappings, and specialization mappings.

---

## DATABASE ACCESS

Connected to Neo4j Production with:
- `Visitor_this_year` nodes (LVS25 registrations from `LVS25_session_export`)
- `Visitor_last_year_bva` nodes (LVS24 attendees treated as prior-year main event)
- `Visitor_last_year_lva` nodes (BVA2025 attendees treated as prior-year secondary event)
- `Sessions_this_year` nodes (LVS25 sessions; data source `LVS25_session_export`)
- `Sessions_past_year` nodes (mixed legacy: LVS24 and BVA2025 sessions)
- `Stream` nodes (session categories/topics)
- `IS_RECOMMENDED` relationships (generated recommendations)
- `Same_Visitor` relationships (linking current to past attendees)
- `attended_session_this_year` / `attended_session_last_year_bva` / `attended_session_last_year_lva` relationships
- `HAS_JOB_TO_STREAM` relationships (job role â†’ stream mappings)
- `HAS_SPECIALIZATION_TO_STREAM` relationships (specialization â†’ stream mappings)
- `HAS_STREAM` relationships (session â†’ stream assignments)

---

## CONCISE TASK LIST FOR REPORT GENERATION

### TASK 1: EVENT OVERVIEW & EXECUTIVE SUMMARY
**Queries Required:**
1. Count total visitors: `MATCH (v:Visitor_this_year) WHERE v.show = 'lva' RETURN count(v)`
2. Count visitors with recommendations: `MATCH (v:Visitor_this_year)-[:IS_RECOMMENDED]->() WHERE v.show = 'lva' RETURN count(DISTINCT v)`
3. Count total recommendations: `MATCH (v:Visitor_this_year)-[r:IS_RECOMMENDED]->(s:Sessions_this_year) WHERE v.show = 'lva' AND s.show = 'lva' RETURN count(r)`
4. Calculate average recommendations per visitor
5. Count returning visitors from BVA 2024 and LVA 2024

**Output:**
- Executive summary table with key metrics
- Recommendation coverage percentage
- Critical findings (successes vs. issues)

---

### TASK 2: VISITOR DEMOGRAPHICS & RETENTION
**Queries Required:**
1. Total visitors by type: new vs returning (BVA 2024, LVA 2024, both)
2. Count unique job roles: `MATCH (v:Visitor_this_year) WHERE v.show = 'lva' RETURN count(DISTINCT v.job_role)`
3. Count unique specializations: `MATCH (v:Visitor_this_year) WHERE v.show = 'lva' RETURN count(DISTINCT v.what_type_does_your_practice_specialise_in)`
4. Count unique organization types: `MATCH (v:Visitor_this_year) WHERE v.show = 'lva' RETURN count(DISTINCT v.organisation_type)`
5. Top 15 job roles with visitor counts
6. Top 15 specializations with visitor counts
7. Top 10 organization types with visitor counts
8. Geographic distribution (top 15 countries)

**Output:**
- Overall visitor metrics table
- Returning visitor analysis with percentages
- Job role distribution table
- Specialization distribution table
- Organization type distribution table
- Geographic distribution table

---

### TASK 3: DATA QUALITY & COMPLETENESS
**Queries Required:**
1. Count visitors with NA/null job roles
2. Count visitors with NA/null specializations
3. Count visitors with NA/null organization types
4. Count visitors with incomplete email domains
5. Identify job roles with "Other", "NA", or null values
6. Identify specializations with "Other", "NA", or null values

**Output:**
- Attribute completeness table (attribute name, unique values, fill rate, NA count)
- Data quality assessment for each key attribute
- Concentration metrics (identify if >20% visitors in single category)

---

### TASK 4: SESSION ANALYSIS & STREAM COVERAGE
**Queries Required:**
1. Count total sessions: `MATCH (s:Sessions_this_year) WHERE s.show = 'lva' RETURN count(s)`
2. Count sessions WITH stream relationships: `MATCH (s:Sessions_this_year)-[:HAS_STREAM]->() WHERE s.show = 'lva' RETURN count(DISTINCT s)`
3. Count sessions WITHOUT stream relationships: Calculate as (total - with_streams)
4. Count sessions with stream property values vs. null/NA/empty
5. Count unique stream values from session properties
6. Count unique theatres/stages
7. Count sponsored sessions: `MATCH (s:Sessions_this_year) WHERE s.show = 'lva' AND s.Sponsored = true RETURN count(s)`
8. Top 15 streams by session count
9. Orphaned streams (streams with no sessions): `MATCH (st:Stream) WHERE NOT exists((st)<-[:HAS_STREAM]-()) RETURN st.stream_name`

**Output:**
- Session metrics table
- Stream coverage percentage (critical finding)
- Top streams by session count
- Orphaned streams list
- Analysis of data degradation (compare to October 15 report: 64.9%)

---

### TASK 5: VISITOR-STREAM MAPPING ANALYSIS
**Queries Required:**
1. Count visitors with job-to-stream mappings: `MATCH (v:Visitor_this_year)-[:HAS_JOB_TO_STREAM]->() WHERE v.show = 'lva' RETURN count(DISTINCT v)`
2. Total job-to-stream relationships: `MATCH (v:Visitor_this_year)-[r:HAS_JOB_TO_STREAM]->() WHERE v.show = 'lva' RETURN count(r)`
3. Average streams per visitor via job mapping
4. Min/max streams per visitor via job mapping
5. Count unmapped job roles (visitors without job-to-stream relationships)
6. List unmapped job roles with visitor counts

**Repeat for Specialization Mappings:**
7. Count visitors with specialization-to-stream mappings
8. Total specialization-to-stream relationships
9. Average streams per visitor via specialization mapping
10. Min/max streams per visitor via specialization mapping
11. Count unmapped specializations
12. List unmapped specializations with visitor counts

**Output:**
- Job role mapping table (status, coverage %, average streams, unmapped roles)
- Specialization mapping table (status, coverage %, average streams, unmapped specializations)
- **Critical Analysis**: Flag if average streams >50 (over-broad mapping issue)
- Unmapped roles/specializations tables

---

### TASK 6: RECOMMENDATION GENERATION ANALYSIS
**Queries Required:**
1. Total recommendations generated
2. Visitors with recommendations (should be 100%)
3. Unique sessions recommended: `MATCH (v:Visitor_this_year)-[:IS_RECOMMENDED]->(s:Sessions_this_year) WHERE v.show = 'lva' RETURN count(DISTINCT s)`
4. Sessions never recommended: `MATCH (s:Sessions_this_year) WHERE s.show = 'lva' AND NOT exists(()-[:IS_RECOMMENDED]->(s)) RETURN s`
5. Distribution of recommendation counts per visitor (1-5, 6-9, exactly 10)
6. Similarity score statistics: min, Q1, median, Q3, max, average
7. Similarity score distribution by ranges (0.30-0.39, 0.40-0.49, etc.)
8. Top 20 most recommended sessions with times recommended and percentage of visitors
9. Pipeline execution timestamps (start/end from relationship properties or system logs)

**Output:**
- Overall recommendation statistics table
- Recommendation distribution table
- Similarity score distribution table and histogram analysis
- Top recommended sessions table
- Sessions never recommended analysis
- Generation time metrics

---

### TASK 7: HISTORICAL ATTENDANCE INTEGRATION
**Queries Required:**
1. Count returning visitors from BVA 2024 with attendance data: `MATCH (v:Visitor_this_year)-[:Same_Visitor]->(vl:Visitor_last_year_bva)-[:attended_session_last_year_bva]->() WHERE v.show = 'lva' RETURN count(DISTINCT v)`
2. Total session attendances for BVA 2024
3. Average sessions per attendee for BVA 2024
4. Count returning visitors from LVA 2024 with attendance data
5. Total session attendances for LVA 2024
6. Average sessions per attendee for LVA 2024

**Output:**
- Past attendance metrics table (by event: BVA 2024, LVA 2024, Total)
- Historical data coverage percentages
- Analysis of how historical data enriches recommendations

---

### TASK 8: CONFIGURATION ANALYSIS
**Reference:** `config_vet_lva.yaml`

- Incorporate recently implemented theatre capacity handling; see `docs/README_theatre_capacity_limits.md` for functionality tied to `recommendation.theatre_capacity_limits`.

**Extract and Document:**
1. Similarity attributes and weights:
   - job_role: 0.8
   - what_type_does_your_practice_specialise_in: 0.8
   - organisation_type: 0.8
   - Country: 0.5
   - are_you_a_distributor_to_the_profession: 0.6
   - are_you_a: 0.6

2. Recommendation settings:
   - min_similarity_score: 0.3
   - max_recommendations: 10
   - similar_visitors_count: 3
   - enable_filtering: true
   - returning_without_history (enabled: true, similarity_exponent: 1.5)

3. Role groups:
   - vet_roles
   - nurse_roles
   - business_roles
   - other_roles

4. Enabled features:
   - Specialization stream mapping (enabled: true)
   - Job role stream mapping (enabled: true)
   - Veterinary filtering rules (enable_filtering: true)
   - Practice type transformations for past year data

**Output:**
- Configuration parameters table
- Vet-specific processing status checklist
- Field mappings documentation
- Assessment of configuration appropriateness

---

### TASK 9: FILTERING RULES VERIFICATION
**Queries Required:**
1. Verify equine/mixed practice exclusions: Check if any equine/mixed visitors received small animal exclusive sessions
2. Verify small animal practice exclusions: Check if any small animal visitors received equine/large animal sessions
3. Verify vet role exclusions: Check if any vet roles received nursing-only sessions
4. Verify nurse stream preferences: Check if nurses received nursing/wellbeing/welfare sessions

**Expected:** Zero violations (perfect compliance as per October 15 report)

**Output:**
- Filtering rules compliance table (rule name, status, violations, impact)
- Overall assessment: EXCELLENT or flag issues if violations found

---

### TASK 10: RECOMMENDATION CONCENTRATION ANALYSIS
**Queries Required:**
1. Top 10 most recommended sessions with percentage of visitors
2. Identify if any single session recommended to >95% of visitors (concentration problem)
3. Calculate recommendation diversity metrics
4. Analyze stream distribution of top recommended sessions

**Output:**
- Top recommended sessions table with concentration percentages
- Concentration problem assessment (flag if top session >95%)
- Analysis of recommendation diversity
- Comparison to target thresholds

---

### TASK 11: SAMPLE RECOMMENDATION WALKTHROUGH
**Queries Required:**
1. Select 2-3 sample visitors (different profiles: small animal vet, nurse, equine vet)
2. For each sample, retrieve:
   - Visitor profile (job role, specialization, organization type)
   - Top 10 recommendations with similarity scores
   - Stream assignments for recommended sessions
   - Filtering rule application verification

**Output:**
- Sample recommendation tables (one per visitor profile)
- Analysis of recommendation quality and relevance
- Stream coverage assessment for recommendations
- Filtering compliance verification

---

### TASK 12: SYSTEM PERFORMANCE ASSESSMENT
**Queries Required:**
1. Pipeline execution time (from processing summary or logs)
2. Calculate visitors processed per minute
3. Calculate recommendations generated per second
4. Database response time (if measurable)

**Output:**
- Pipeline performance table (execution time, throughput metrics)
- Performance status (Good/Excellent/Needs Improvement)

---

### TASK 13: DATA QUALITY SCORECARD
**Calculate Scores:**
1. Visitor Data Completeness: (visitors with complete profiles / total visitors) Ã— 100
2. Session Data Completeness: (sessions with streams / total sessions) Ã— 100
3. Job Role Mapping Coverage: (mapped visitors / total visitors) Ã— 100
4. Specialization Mapping Coverage: (mapped visitors / total visitors) Ã— 100
5. Stream Taxonomy Utilization: (active streams / total streams) Ã— 100
6. Filtering Rules Compliance: 100% if zero violations
7. Recommendation Generation: (visitors with recommendations / total visitors) Ã— 100
8. Overall Data Quality: Average of all scores

**Output:**
- Data quality scorecard table (category, score, grade)
- System strengths (âœ…)
- System weaknesses (âš ï¸)
- Overall recommendation quality grade

---

### TASK 14: PRIORITY ACTIONS & RECOMMENDATIONS
**Based on Analysis, Identify:**

**Immediate Actions (Week 1):**
1. Session stream gap remediation (target top 20 most-recommended sessions without streams)
2. Define default mappings for "NA" and "Other" categories
3. Implement session stream validation in import process

**Short-term Actions (Month 1):**
1. Refine job and specialization mapping files (reduce over-broad connections)
2. Review and consolidate stream taxonomy
3. Implement data quality monitoring dashboard
4. Address specialization mapping gap (24.8% unmapped)

**Medium-term Actions (Quarter 1):**
1. Consider increasing similarity threshold from 0.3 to 0.4
2. Implement weighted stream associations
3. Add session diversity requirements (prevent single session >95% recommendation)
4. Enhance collaborative filtering (increase similar_visitors_count from 3 to 5-7)

**Algorithm Optimization:**
1. Assess if similarity weights are appropriate (current: 0.5-0.8 range)
2. Consider increasing specialization weight to 1.0
3. Evaluate session popularity dampening
4. Implement temporal factors (session time preferences)

**Output:**
- Priority actions organized by timeframe
- Specific parameter adjustment recommendations
- Business opportunities (retention programs, cross-event promotion)
- Expected impact assessment

---

### TASK 15: CONCLUSION & OVERALL SYSTEM ASSESSMENT
**Synthesize:**
1. Overall system readiness grade (A-F)
2. Strengths summary (âœ…)
3. Critical issues summary (ðŸ”´)
4. Priority actions before event
5. Success metrics to track post-event
6. Bottom line assessment

**Output:**
- Key achievements list
- Critical gaps requiring attention
- System status by category (algorithm, data quality, performance, configuration)
- Overall grade with justification
- Final recommendation

---

## OUTPUT FORMAT REQUIREMENTS

- **Format**: Markdown with clear hierarchical headers (##, ###, ####)
- **Tables**: Use for all quantitative data presentation
- **Emphasis**: Use **bold** for key metrics and critical findings
- **Icons**: Use âœ… for strengths, âŒ for issues, âš ï¸ for warnings, ðŸ”´ for critical problems
- **Language**: Clear, actionable, insight-focused (not just data dumps)
- **Sections**: Follow the structure from the original report (14 main sections + Appendix)

---

## CRITICAL FOCUS AREAS

**Must Address:**
1. âœ… **Recommendation concentration**: Document if top session >95% of visitors
2. âœ… **Session stream gap**: Critical issue - 64.9% sessions lack streams (WORSENED from previous run)
3. âœ… **Specialization mapping gap**: 24.8% visitors unmapped
4. âœ… **Over-broad mappings**: Average 50-57 streams per visitor (reduces differentiation)
5. âœ… **Filtering rules compliance**: Verify perfect adherence (zero violations)
6. âœ… **Sponsored session coverage**: Check if sponsors getting recommendations
7. âœ… **Data quality degradation**: Session stream coverage worsened (61.1% â†’ 64.9%)
8. âœ… **Algorithm configuration**: Assess if min_similarity_score=0.3 is too low

---

## COMPARISON TO PREVIOUS REPORT

**Reference Baseline (October 15, 2025 Report):**
- Total visitors: 4,667
- Recommendation coverage: 100%
- Session stream gap: 64.9% (239 out of 368 sessions)
- Job role mapping: 95.3% coverage
- Specialization mapping: 75.2% coverage
- Filtering compliance: Perfect (zero violations)
- Average streams per visitor: 56.8 (job), 50.8 (specialization)

**Your Task:** Compare latest run metrics to these baselines and identify:
- Improvements (green flag âœ…)
- Degradations (red flag ðŸ”´)
- Unchanged issues (amber flag âš ï¸)

---

## FILE NAMING CONVENTION

Save report as: `report_lva_31102025.md`

---

## ADDITIONAL CONTEXT

- This is a **veterinary event** using vet-specific processing (filtering rules, practice type mapping, role groups)
- Configuration file: `config_vet_lva.yaml` in project knowledge
- Previous report: `report_lva_15102025.md` in project knowledge
- Database: `neo4j-prod` (production environment)
- Pipeline processed in 17 minutes with excellent throughput
- Theatre capacity limits are enforced when capacity settings are enabled in configuration; summarise impacts per `docs/README_theatre_capacity_limits.md` when relevant.

---

**Generate the comprehensive report now, following all 15 tasks sequentially.**