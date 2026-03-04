# Prompt 3: Post-Show Analysis Report (v2.0)

## Instructions for Claude

You are a Senior Data Analyst creating a **POST-SHOW ANALYSIS** report for **[EVENT_NAME] [YEAR]**.

### CONTEXT

The event has concluded. Badge scan data has been processed and loaded into Neo4j. This report analyzes:
1. How well recommendations performed
2. Complete visitor journey from registration to actual attendance
3. Which pre-show predictions came true
4. Specific failures and successes
5. Impact of new recommendation system features (capacity planning, overlapping sessions)
6. Actionable insights for next year

Configuration setting: `mode: "post_analysis"` in config file.

### DATABASE ACCESS

You have access to a Neo4j database containing:
- `Visitor_this_year` nodes (current year registrations)
- `Sessions_this_year` nodes (this year's sessions)
- `IS_RECOMMENDED` relationships (pre-show recommendations)
- **`assisted_session_this_year` relationships (actual session attendance from badge scans)**
- `Stream` nodes and `HAS_STREAM` relationships
- Historical data: `Visitor_last_year_*`, `attended_session` relationships
- `registered_to_show` relationships (venue entry scans)

### PROJECT KNOWLEDGE ACCESS

You have access to:
- **ALL PRE-SHOW REPORTS** (initial run + all increments)
- Configuration files showing recommendation algorithm parameters
- Post-analysis scan files and processing logs
- Theatre capacity files (teatres.csv)
- Session export files with time slots

---

## CRITICAL: SPECIAL EVENTS EXCLUSION METHODOLOGY

### Identifying Pure Special Events

**BEFORE calculating any performance metrics**, identify and exclude sessions that have **ONLY** the "Awards and Special Events" stream (no other streams).

**Cypher Query to Identify Pure Special Events:**
```cypher
MATCH (s:Sessions_this_year)
WHERE s.show = '[SHOW_CODE]' OR s.show IS NULL
OPTIONAL MATCH (s)-[:HAS_STREAM]->(stream:Stream)
WITH s, COLLECT(DISTINCT stream.stream) AS streams
WHERE SIZE(streams) = 1 AND 'Awards and Special Events' IN streams
RETURN s.session_id AS session_id, s.title AS title, streams
```

**Inclusion Rules:**
- ✅ **INCLUDE** sessions with "Awards and Special Events" + other streams (e.g., Culture, Leadership)
- ❌ **EXCLUDE** sessions with ONLY "Awards and Special Events" stream

**Rationale for Exclusion:**
- Special events (keynotes, ceremonies, private events) are non-targetable content
- They appeal universally regardless of role/specialization
- Visitors discover them through event marketing, not recommendations
- Including them would skew metrics (e.g., 1,500+ attendee keynote with 0 recommendations)

**Report Requirement:**
Create a separate section documenting excluded special events with:
- Session names and attendance counts
- Explanation that these are special keynotes/ceremonies outside recommendation scope
- Note that a separate "Must-See Events" section could be created for future events

---

## REPORT REQUIREMENTS

Generate a comprehensive markdown report with the following sections:

### 1. EXECUTIVE SUMMARY

Include:
- **Event Attendance Overview**
  * Total pre-registered visitors
  * Total venue visitors (badge scans via `registered_to_show`)
  * Registration → venue conversion rate
- **Recommendation Performance (Regular Sessions Only)**
  * Total recommendations sent
  * Session-level hit rate (% of attended sessions that were recommended)
  * Visitor-level hit rate (% of visitors who attended ≥1 recommended session)
- **Special Events Summary** (excluded from main metrics)
  * Number of pure special event sessions excluded
  * Total special event attendances
- **New Features Performance**
  * Theatre capacity planning effectiveness
  * Overlapping session resolution impact
- **Top Issues Identified** (3-5 critical problems)
- **Key Successes** (what worked well)
- **Bottom Line Assessment**: Was the recommendation system effective? Yes/No and why

---

### 2. THE COMPLETE VISITOR JOURNEY

#### 2.1 Registration → Venue → Session Attendance Funnel

Create detailed funnel showing progression through stages:

```
┌─────────────────────────────────────────────────────────┐
│ Total Registered: X visitors                            │
└─────────────────────────────────────────────────────────┘
                    ↓ [Y%]
┌─────────────────────────────────────────────────────────┐
│ Recommendations Generated: Z visitors                   │
│ (pre-show pipeline processed)                           │
└─────────────────────────────────────────────────────────┘
                    ↓ [Y%]
┌─────────────────────────────────────────────────────────┐
│ Venue Attendance: A visitors                            │
│ (badge scanned at venue via registered_to_show)         │
└─────────────────────────────────────────────────────────┘
                    ↓ [Y%]
┌─────────────────────────────────────────────────────────┐
│ Regular Session Attendance: B visitors                  │
│ (attended any regular session, excl. special events)    │
└─────────────────────────────────────────────────────────┘
                    ↓ [Y%]
┌─────────────────────────────────────────────────────────┐
│ Recommended Session Attendance: C visitors              │
│ (attended ≥1 recommended regular session)               │
└─────────────────────────────────────────────────────────┘
```

Calculate and highlight conversion rates at each stage.

#### 2.2 The Venue-to-Session Gap

**Analysis:**
- X visitors scanned badges at venue
- Y visitors attended at least one regular session (Y/X = Z%)
- Gap: (X-Y) visitors attended venue but NO regular sessions
- Note: Some gap visitors may have attended only special events

**Why This Matters:**
- Wasted recommendations
- Lost engagement opportunity
- Sponsor exposure issues

---

### 3. RECOMMENDATION SYSTEM PERFORMANCE

#### 3.1 Overall Hit Rate Analysis (Regular Sessions Only)

**Primary Metrics:**
| Metric | Count | Percentage |
|--------|-------|------------|
| Visitors with recs who attended regular sessions | X | 100% (analyzed) |
| Attended ≥1 recommended session | Y | Z% ← **VISITOR HIT RATE** |
| Attended NO recommended sessions | A | B% ← **MISS RATE** |

**Session-Level Hit Rate:**
| Metric | Count | Analysis |
|--------|-------|----------|
| Total regular sessions attended (by visitors with recs) | X | 100% |
| Sessions attended that were recommended | Y | Z% ← **SESSION-LEVEL HIT RATE** |
| Sessions attended that were NOT recommended | A | B% |

**Key Insight:** Explain the difference between visitor-level and session-level hit rates

#### 3.2 Returning vs New Visitor Performance

| Metric | Returning Visitors | New Visitors | Difference |
|--------|-------------------|--------------|------------|
| **Total Analyzed** | X | Y | - |
| **Session-Level Hit Rate** | X% | Y% | +/- Z pts |
| **Total Hits** | X | Y | - |
| **Total Attended** | X | Y | - |
| **Avg Sessions/Visitor** | X | Y | +/- Z |

**Key Finding:** Did returning visitor boost (1.5× similarity exponent) deliver results?

#### 3.3 Session-Level Recommendation Performance

**Top 20 Most Recommended Sessions:**
| Rank | Session Title | Recs | Attendance | Conversion | Sponsor? |
|------|--------------|------|------------|------------|----------|
| 1 | ... | X | Y | Z% | Yes/No |

**Best Converting Sessions (min 50 recommendations):**
| Rank | Session Title | Recs | Attendance | Conversion |
|------|--------------|------|------------|------------|

**Most Attended Sessions (actual popularity):**
| Rank | Session Title | Attendance | Recs | Conversion |
|------|--------------|------------|------|------------|

#### 3.4 Concentration Analysis

Compare pre-show predicted concentration vs actual attendance:

| Session | Pre-Show Rec % | Actual Attendance | Conversion | Analysis |
|---------|---------------|-------------------|------------|----------|

**Key Finding:** Was concentration controlled compared to previous shows (e.g., ECOMM's 98.7%)?

---

### 4. NEW FEATURES IMPACT ANALYSIS

#### 4.1 Theatre Capacity Planning Effectiveness

**Feature Overview:**
- Theatre capacity limits enforced with multiplier (e.g., 3.0×)
- Recommendations capped based on theatre capacity

**Configuration Used:**
```yaml
theatre_capacity_limits:
  enabled: true/false
  capacity_file: "path/to/teatres.csv"
  capacity_multiplier: X.X
```

**Impact Analysis:**
| Theatre | Capacity | Multiplied Limit | Total Recs | Over/Under |
|---------|----------|------------------|------------|------------|

**Key Questions to Answer:**
1. Were any sessions capped due to capacity limits?
2. Did capacity planning prevent over-recommendation in small venues?
3. How many recommendations were removed due to capacity constraints?
4. Did actual attendance align with capacity predictions?

**Effectiveness Assessment:**
- ✅ Feature worked as intended / ⚠️ Needs adjustment / ❌ Not effective

#### 4.2 Overlapping Session Resolution Effectiveness

**Feature Overview:**
- System resolves overlapping sessions by keeping highest similarity score
- Prevents recommending multiple sessions at same time slot

**Configuration Used:**
```yaml
resolve_overlapping_sessions_by_similarity: true/false
```

**Impact Analysis:**

**Visitors with Multiple Recs at Same Time Slot:** X (should be 0 if feature working)

**Verification Query:**
```cypher
// Check for overlapping recommendations
MATCH (v:Visitor_this_year)-[rec:IS_RECOMMENDED]->(s:Sessions_this_year)
WHERE (v.show = '[SHOW_CODE]' OR v.show IS NULL)
WITH v, s.date AS session_date, s.start_time AS start_time, 
     COLLECT(s.session_id) AS sessions_at_slot
WHERE SIZE(sessions_at_slot) > 1
RETURN COUNT(DISTINCT v) AS visitors_with_overlapping_recs
```

**Key Questions to Answer:**
1. Did the feature successfully prevent overlapping recommendations?
2. How many potential overlaps were resolved?
3. Were the highest-similarity sessions correctly retained?
4. Did visitors actually benefit (attended recommended session instead of conflicting one)?

**Before/After Comparison:**
| Metric | Without Feature | With Feature | Improvement |
|--------|-----------------|--------------|-------------|
| Overlapping recs per visitor | X | 0 | -100% |
| Practical recommendations | X% | Y% | +Z% |

**Effectiveness Assessment:**
- ✅ Feature worked as intended / ⚠️ Needs adjustment / ❌ Not effective

---

### 5. GAP ANALYSIS

#### 5.1 Visitors Without Recommendations

**The Coverage Gap:**
- X visitors (Y%) had NO recommendations in the system
- Of these, Z visitors (A%) attended sessions anyway
- These visitors generated B total attendances

**Root Causes:**
1. Late registrations after final pipeline run
2. Database timing issues
3. Processing errors

#### 5.2 Sessions Never Recommended But Had Attendance

**Regular sessions with attendance but ZERO recommendations:**
| Session | Attendance | Sponsored? | Issue |
|---------|------------|------------|-------|

**Total Impact:**
- X regular sessions never recommended but had attendance
- Y total attendances at these sessions (Z% of regular attendances)
- Complete algorithmic failure for these sessions

#### 5.3 Sponsored Session Analysis

| Metric | Count | Status |
|--------|-------|--------|
| Total Sponsored Sessions | X | - |
| Sponsored with Recommendations | Y (Z%) | ✅/⚠️ |
| Sponsored Never Recommended | A (B%) | ⚠️ |

**Notable Sponsored Sessions Never Recommended:**
| Session | Sponsor | Attendance | Issue |
|---------|---------|------------|-------|

---

### 6. PRE-SHOW PREDICTIONS VS POST-SHOW REALITY

#### 6.1 Prediction Accuracy Matrix

| Issue | First Identified | Prediction | Actual Outcome | Accuracy |
|-------|-----------------|------------|----------------|----------|

#### 6.2 What Pre-Show Reports Got Right/Wrong

**Accurate Predictions:**
1. ...

**Surprises (Not Predicted):**
1. ...

---

### 7. SHOW-SPECIFIC DEMOGRAPHICS

#### 7.1 Final Visitor Demographics

**Job Role Distribution:**
| Job Role | Count | % |
|----------|-------|---|

**Specialization Distribution:**
| Specialization | Count | % |
|----------------|-------|---|

**Organisation Type:**
| Type | Count | % |
|------|-------|---|

**Geographic Distribution:**
| Country | Count | % |
|---------|-------|---|

#### 7.2 Returning Visitor Analysis

| Source | Count | % of Total |
|--------|-------|------------|
| [Previous Event 1] only | X | Y% |
| [Previous Event 2] only | X | Y% |
| Both events | X | Y% |
| New Visitors | X | Y% |

---

### 8. STREAM PERFORMANCE ANALYSIS

| Stream | Sessions | Total Attendance | Avg per Session |
|--------|----------|------------------|-----------------|

**Key Insights:**
- Which streams dominated actual attendance?
- Clinical vs Business content performance

---

### 9. CRITICAL ISSUES - DEEP DIVE

#### 9.1 The Under-Recommendation Problem

Sessions with massive conversion rates (>200%) indicate under-recommendation:

| Session | Recommendations | Attendance | Conversion |
|---------|----------------|------------|------------|

**Root Cause:** Algorithm failed to identify high-interest clinical content

#### 9.2 The Sponsored Session Disparity

Analysis of sponsored session coverage and business implications

#### 9.3 Other Issues

Document any additional critical issues discovered

---

### 10. WHAT WORKED WELL

#### 10.1 Successes (With Quantitative Evidence)

✅ List of what worked with supporting data

---

### 11. SPECIAL EVENTS ANALYSIS (EXCLUDED FROM MAIN METRICS)

#### 11.1 Pure Special Event Sessions

The following sessions have **ONLY** the "Awards and Special Events" stream and are excluded from the main recommendation performance analysis:

| Session | Attendance | Recommendations | Notes |
|---------|------------|-----------------|-------|

#### 11.2 Special Events Summary

**Total Special Event Metrics:**
- X sessions (Y% of total sessions)
- Z total attendances (A% of all attendances)
- B unique visitors attended at least one special event

**Key Observations:**
- Highlight any standout special events (e.g., celebrity keynotes)
- Note that these events have universal appeal regardless of specialization
- Recommendation algorithm correctly/incorrectly handled these

**Recommendation for Future:**
Consider creating a separate "Must-See Events" section in recommendations that highlights keynotes and ceremonies to all visitors, separate from personalized session recommendations.

---

### 12. CONCLUSIONS AND STRATEGIC RECOMMENDATIONS

#### 12.1 What Worked Well

✅ List strengths with evidence

#### 12.2 Critical Issues Identified

❌ List problems with evidence

#### 12.3 Root Cause Analysis

Why did the system perform as it did?

#### 12.4 Actionable Recommendations for Next Event

**Immediate Actions ⚠️ CRITICAL**
1. ...

**Algorithm Improvements**
1. ...

**Process Improvements**
1. ...

---

### 13. SUCCESS METRICS FOR NEXT EVENT

| Metric | Current ([YEAR]) | Target ([NEXT_YEAR]) | Stretch Goal |
|--------|-----------------|----------------------|--------------|
| Session-Level Hit Rate | X% | Y% | Z% |
| Visitor Hit Rate | X% | Y% | Z% |
| Visitor Coverage | X% | Y% | Z% |
| Sponsored Coverage | X% | 100% | 100% |
| Sessions Never Recommended | X% | <Y% | <Z% |

---

### 14. APPENDIX: TECHNICAL DETAILS

#### A. Database Schema Summary

Document nodes, relationships, and counts

#### B. Similarity Score Distribution

| Metric | Value |
|--------|-------|
| Minimum | X |
| Q1 | X |
| Median | X |
| Average | X |
| Q3 | X |
| Maximum | X |

#### C. Configuration File Reference

Key configuration parameters used

#### D. Pure Special Event Session IDs (Excluded)

List of session IDs excluded from main calculations

---

### 15. FINAL ASSESSMENT

**Bottom Line:** [Overall assessment]

**System Grade: [X]/100**
- Algorithm quality: [Grade]
- Coverage: [Grade]
- Calibration: [Grade]
- Business alignment: [Grade]

**The Path Forward:**
[Summary of key actions needed for improvement]

---

**Report Generated:** [DATE]
**Data Source:** Neo4j [DATABASE]
**Event:** [EVENT_NAME] [YEAR]
**Show Code:** `[SHOW_CODE]`

---

## Usage Instructions

1. Replace `[EVENT_NAME]`, `[YEAR]`, `[SHOW_CODE]` with actual values
2. Ensure `mode: "post_analysis"` in config
3. Run after event with badge scan data processed
4. **IMPORTANT:** First identify and exclude pure special events before any calculations
5. Ensure access to ALL pre-show reports
6. Verify theatre capacity file and session export file are available
7. Save to: `reports/post_show_analysis_[event]_[year].md`
