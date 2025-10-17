# Prompt 1: Initial Pre-Show Run Report

## Instructions for Claude

You are a Senior Data Analyst creating the **INITIAL PRE-SHOW** recommendation system analysis report for **[EVENT_NAME] [YEAR]**.

### CONTEXT

This is the **FIRST** recommendation run before the event. The system has generated personalized session recommendations for registered visitors based on their profile attributes and historical attendance patterns.

### DATABASE ACCESS

You have access to a Neo4j database (neo4j-dev) containing:
- `Visitor_this_year` nodes (current year registrations)
- `Visitor_last_year_bva` and `Visitor_last_year_lva` nodes (past year attendees)
- `Sessions_this_year` and `Sessions_past_year` nodes
- `Stream` nodes (session categories)
- `IS_RECOMMENDED` relationships (generated recommendations)
- `Same_Visitor` relationships (linking current to past attendees)
- `attended_session` relationships (past year attendance)

### PROJECT KNOWLEDGE

You have access to:
- Configuration files showing recommendation algorithm parameters
- Pre-show registration data statistics
- Session catalog information

---

## REPORT REQUIREMENTS

Generate a comprehensive markdown report with the following sections:

### 1. EXECUTIVE SUMMARY

Include:
- Total visitors in database
- Returning vs new visitor breakdown (with percentage)
- Total recommendations generated
- Average recommendations per visitor
- Session coverage (% of sessions with recommendations)
- Top session concentration metric (% of visitors recommended the top session)
- Critical concerns identified

---

### 2. VISITOR DEMOGRAPHICS AND RETENTION

#### 2.1 Overall Visitor Statistics
- Total visitors
- Returning visitors (count and %)
- New visitors (count and %)
- Comparison to previous events if available

#### 2.2 Returning Visitor Analysis
- Breakdown by source event (main event, secondary event, both)
- Retention patterns
- Key insights about returning visitor engagement

---

### 3. DATA COMPLETENESS AND QUALITY

#### 3.1 Attribute Overview
For each key visitor attribute used in recommendations:
- Attribute name
- Unique values count
- Fill rate (%)
- NA values (count and %)
- Data quality assessment

#### 3.2 Data Distribution Analysis
- Top values for key attributes (Industry, Job Role, Solution Interest, etc.)
- Concentration analysis (identify clusters)
- Diversity metrics

---

### 4. RECOMMENDATION SYSTEM ANALYSIS

#### 4.1 Coverage Metrics
- Total sessions available
- Sessions with recommendations (count and %)
- Sessions never recommended (count and %)
- Total recommendations generated
- Average recommendations per visitor
- Average recommendations per session

#### 4.2 Top Recommended Sessions
Table showing:
- Rank
- Session title
- Times recommended
- % of visitors
- Date/Stage

Analyze concentration problem (if top sessions recommended to >90% of visitors)

#### 4.3 Sessions Never Recommended
Breakdown by type:
- Sponsored sessions (count)
- Social/networking events (count)
- Regular content sessions (count)

Identify WHY sessions lack recommendations (missing embeddings, incomplete metadata, etc.)

#### 4.4 Similarity Score Distribution
If available:
- Minimum, Q1, Median, Q3, Maximum, Average similarity scores
- Current similarity threshold
- Assessment of threshold appropriateness

#### 4.5 Actual Similarity Weights
Document the current configuration:
```yaml
similarity_attributes:
  attribute_name: weight
```
Assess if weights favor high-diversity attributes

---

### 5. ATTRIBUTE CORRELATIONS AND PATTERNS

#### 5.1 Key Correlations
- Job Role × Industry combinations (top 5-10)
- Role × Solution Interest patterns
- Geographic distribution patterns
- Any clustering concerns (e.g., 24% in single interest category)

#### 5.2 Returning vs New Visitor Patterns
- Behavioral differences
- Attribute distribution differences

---

### 6. SYSTEM PERFORMANCE ISSUES AND OPPORTUNITIES

#### 6.1 Recommendation Concentration Problem
- Document if top session recommended to >95% of visitors
- Analyze root causes:
  * Low similarity thresholds
  * Insufficient weight on differentiating attributes
  * Missing embeddings
  * Dominant clusters (e.g., AI interest)

#### 6.2 Coverage Gaps
- Sessions without recommendations and their importance
- Sponsored session coverage issues
- Business impact assessment

#### 6.3 Visitor Segmentation Opportunities
- Underutilized segments
- Cross-event attendees
- International visitors

---

### 7. RECOMMENDATIONS FOR IMPROVEMENT

#### 7.1 Immediate Actions (Before Event)
Prioritized list with specific parameters:
- Similarity threshold adjustments (current → recommended)
- Weight adjustments (current → recommended)
- Sponsored session inclusion strategy
- Diversity constraint implementation

#### 7.2 Data Enhancement
- Capture additional attributes
- Form validation improvements
- Reduce NA values strategies

#### 7.3 Algorithm Improvements
- Leverage historical behavior better
- Implement diversity constraints
- Break up dominant clusters (e.g., AI interest sub-categorization)
- Time-slot awareness

#### 7.4 Business Opportunities
- Retention programs for new visitors
- Cross-event promotion strategies
- Sponsor value enhancement

---

### 8. CONCLUSION

Synthesize:
- Overall system readiness assessment
- Strengths of current configuration
- Critical issues that need addressing
- Priority actions before event
- Success metrics to track

---

## OUTPUT FORMAT

- Use markdown with clear headers (##, ###)
- Include tables for data presentation
- Use **bold** for key metrics and findings
- Use ✓ for strengths, ✗ for issues, ⚠️ for warnings
- Keep language clear and actionable
- Focus on insights, not just data dumps

---

## CRITICAL FOCUS AREAS

1. Recommendation concentration (is top session >95% of visitors?)
2. Sponsored session coverage (are sponsors getting recommendations?)
3. Data quality issues (NA values, clusters)
4. Algorithm configuration (weights, thresholds)
5. Actionable improvements before event

---

**Generate the complete report now.**

---

## Usage Instructions

1. Replace `[EVENT_NAME]` and `[YEAR]` with actual values (e.g., "ECOMM 2025")
2. Run after first recommendation generation
3. Use when `create_only_new=False` or first run
4. Save output to: `PA/reports/report_[event]_[DDMMYYYY].md`

**Example**: `PA/reports/report_ecomm_20082025.md`