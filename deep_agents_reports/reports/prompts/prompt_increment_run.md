# Prompt 2: Incremental Pre-Show Run Report

## Instructions for Claude

You are a Senior Data Analyst creating an **INCREMENTAL PRE-SHOW** recommendation system analysis report for **[EVENT_NAME] [YEAR]**.

### CONTEXT

This is an incremental update run using `create_only_new=True`. New visitors have been added since the last run, and new recommendations have been generated. This report should compare current state to **PREVIOUS runs** and track progression.

### DATABASE ACCESS

You have access to a Neo4j database (neo4j-dev) containing:
- `Visitor_this_year` nodes (growing population)
- `Sessions_this_year` nodes
- `IS_RECOMMENDED` relationships (cumulative)
- `Stream` nodes
- Historical visitor nodes (`Visitor_last_year_*`)
- `Same_Visitor` and `attended_session` relationships

### PROJECT KNOWLEDGE ACCESS

You have access to:
- **PREVIOUS REPORTS** (dated earlier) showing baseline and prior increments
- Current configuration files
- Growth metrics from prior runs

---

## REPORT REQUIREMENTS

Generate a comprehensive markdown report with the following sections:

### 1. EXECUTIVE SUMMARY

Include:
- Current vs previous run comparison table showing:
  * Total visitors (with % change)
  * Returning visitors % (with change in percentage points)
  * Total recommendations (with % change)
  * Top session concentration % (with change)
  * Sessions with recommendations (unchanged or changed)
  * Sessions never recommended (unchanged or changed)
- Critical observation about growth rate trends
- Key findings about whether issues improved or worsened

---

### 2. VISITOR DEMOGRAPHICS AND RETENTION - PROGRESSIVE ANALYSIS

#### 2.1 Overall Visitor Statistics Evolution
Create comparison table across **ALL runs to date**:
- Baseline date
- Each increment date
- Current date

Show for each: Total visitors, Returning %, New %, Growth rate

#### 2.2 Returning Visitor Analysis - Progressive Changes
Table showing returning visitor sources across all runs:
- BVA Only, LVA Only, Both Events (or equivalent for your event)
- Growth trends
- Insights about which segments growing fastest

#### 2.3 Demographics Evolution
Track changes in key attributes:
- Industry distribution changes
- Job role distribution changes
- Geographic distribution changes
- Solution interest changes

---

### 3. RECOMMENDATION SYSTEM ANALYSIS - PROGRESSIVE PERFORMANCE

#### 3.1 Coverage Metrics Evolution
Table comparing across all runs:
- Sessions Available
- Sessions with Recommendations
- Sessions without Recommendations
- Total Recommendations
- Avg per Visitor

#### 3.2 Concentration Analysis - Trend Analysis
Table showing top 5-10 sessions' recommendation percentages across all runs:
- Is concentration improving (↓) or worsening (↗)?
- By how much?
- Identify if ANY progress made on concentration issue

Example format:
| Rank | Session | Baseline % | Increment 1 % | Current % | Trend |
|------|---------|------------|---------------|-----------|-------|
| 1 | Session A | 95.5% | 97.2% | 98.7% | ↗️ Worsening |
| 2 | Session B | 92.1% | 94.5% | 96.3% | ↗️ Worsening |

#### 3.3 Similarity Configuration Analysis
Document current weights and compare to previous recommendations:
- Were any changes implemented since last report?
- Current threshold vs recommended threshold
- Why concentration persists despite recommendations
- Analysis of why implemented changes (if any) did/didn't work

---

### 4. SESSIONS NEVER RECOMMENDED - PERSISTENT ISSUE

Track across all runs:
- Total never recommended (unchanged?)
- Sponsored sessions never recommended (unchanged?)
- Document if this issue has ANY progress or remains stagnant
- If unchanged, emphasize this as critical unresolved issue

Create table:
| Run Date | Total Never Recommended | Sponsored Never Recommended | Status |
|----------|------------------------|----------------------------|--------|
| Baseline | 18 (15.5%) | 12 (10.3%) | ⚠️ Issue identified |
| Increment 1 | 18 (15.5%) | 12 (10.3%) | ✗ No change |
| Current | 18 (15.5%) | 12 (10.3%) | ✗ Still unresolved |

---

### 5. KEY INSIGHTS FROM PROGRESSIVE ANALYSIS

#### 5.1 What's Getting Worse
List issues that deteriorated:
- Concentration percentages increasing
- Returning visitor percentage dilution
- Any other degrading metrics
- Rate of deterioration

#### 5.2 What's Stable (The Problems)
List issues unchanged across increments:
- Sessions never recommended (if unchanged)
- Sponsored coverage (if unchanged)
- Average recommendations per visitor
- AI cluster dominance (or other clusters)
- Threshold and weights (if not adjusted)

#### 5.3 What's Improving
List any positive trends:
- Absolute visitor numbers growing
- Country diversity increasing
- Any metric showing improvement
- Data quality improvements

---

### 6. DATA QUALITY ANALYSIS - PROGRESSIVE VIEW

#### 6.1 Attribute Completeness Evolution
Table showing fill rates across runs:
| Attribute | Baseline NA% | Increment 1 NA% | Current NA% | Trend |
|-----------|--------------|-----------------|-------------|-------|
| Industry | 7.0% | 8.1% | 8.4% | ↗️ Worsening |
| Job Role | 6.8% | 6.2% | 6.0% | ↘️ Improving |

#### 6.2 Clustering Analysis
- Track dominant clusters across runs
- Identify if clustering getting worse or better
- Impact on recommendation diversity

---

### 7. RECOMMENDATIONS - BUILDING ON PREVIOUS ANALYSIS

#### 7.1 Implementation Status of Previous Recommendations

For EACH previous recommendation, create table:

| Original Recommendation | Report Date | Priority | Status | Current Data Validation |
|------------------------|-------------|----------|--------|------------------------|
| Raise threshold 0.5 → 0.6 | 20/08/2025 | ⚠️ CRITICAL | ✗ Not Implemented | Concentration now 98.7% (worse) |
| Increase Country weight | 20/08/2025 | 🔴 HIGH | ✗ Not Implemented | UK concentration still 91% |
| Force sponsor inclusion | 20/08/2025 | 🔴 HIGH | ✗ Not Implemented | Still 12 sponsors with 0 recommendations |

#### 7.2 Updated Recommendations Based on Current Data

For each unimplemented recommendation:
- **Reaffirm** if current data confirms need
- **Update** if current data suggests different approach
- **Escalate priority** if issue worsening

For each implemented recommendation:
- **Assess effectiveness** based on current data
- **Refine** if needed
- **Continue** if working

#### 7.3 New Recommendations Based on Current Increment

Any NEW issues discovered in this increment requiring action

#### 7.4 Progressive Personalization Strategy

Suggestions for staged rollout:
- Phase 1: Fix critical issues (concentration, sponsors)
- Phase 2: Refine weights based on phase 1 results
- Phase 3: Advanced features (time-slot awareness, etc.)

---

### 8. GROWTH RATE AND SCALING ANALYSIS

#### 8.1 Registration Growth Pattern
- Growth rate slowing, accelerating, or stable?
- Expected final registration count
- Implications for recommendation system

#### 8.2 System Performance at Scale
- Is recommendation quality degrading with growth?
- Are there scaling issues emerging?
- Infrastructure readiness

---

### 9. CONCLUSION

#### 9.1 Three-Period (or More) Summary

Timeline table:
| Metric | Baseline | Increment 1 | Current | Overall Trend |
|--------|----------|-------------|---------|---------------|
| Visitors | 2,974 | 5,475 | 7,420 | ↗️ Growing |
| Returning % | 23.8% | 17.4% | 14.85% | ↘️ Declining |
| Top Session % | 98.12% | 98.52% | 98.71% | ↗️ Worsening |

#### 9.2 Pattern Analysis

**What's Consistently Observed:**
- List patterns seen in every report

**What's Changing:**
- Metrics that show variation

**What's Stagnant:**
- Persistent issues with no change
- Unimplemented recommendations

#### 9.3 Critical Assessment

**The System Status:**
- Is it getting better or worse overall?
- Are we on track for a successful event?
- What's the biggest risk?

#### 9.4 Immediate Priority

Based on ALL accumulated evidence, what is THE most critical action?
- Justify with trend data across all runs
- Show progression of the issue
- Emphasize urgency if issue worsened
- Provide specific parameters for fix

**Example:**
```
IMMEDIATE PRIORITY: Raise similarity threshold to 0.6

JUSTIFICATION:
- Baseline (20/08): Top session 98.12%
- Increment 1 (11/09): Top session 98.52% (+0.4 pts)
- Current (22/09): Top session 98.71% (+0.19 pts)
- Trend: Consistently worsening
- Recommended 3 times, never implemented
- Impact: 98.7% of visitors get identical recommendation
- Risk: Complete personalization failure
```

---

## OUTPUT FORMAT

- Use markdown with clear headers
- Extensive use of comparison tables showing ALL runs
- Use trend indicators consistently:
  * ↗️ Worsening (getting worse)
  * ↘️ Improving (getting better)
  * → Stable (no change)
- Highlight metrics with "No change" or "Unchanged" across runs
- Use **bold** for critical findings
- Include "Confirmed:" or "Validated:" when data supports previous hypotheses
- Use "⚠️ CRITICAL", "🔴 HIGH PRIORITY", "🟡 MEDIUM" for priorities

---

## CRITICAL FOCUS AREAS

1. **Implementation Tracking**: Were previous recommendations implemented?
2. **Concentration Trend**: Compare across ALL runs - improving or worsening?
3. **Persistent Issues**: Sessions never recommended, sponsor coverage - any change?
4. **Growth Rate Analysis**: Slowing, accelerating, or saturating?
5. **Validation**: Does current data confirm previous hypotheses?
6. **Pattern Recognition**: What consistently happens? What's random?

---

## COMPARISON EMPHASIS

**Every section should show progression:**
- "Baseline → Increment 1 → Increment 2 → Current"
- Not just "then vs now" but complete timeline
- Focus on **TRENDS and PATTERNS**, not just current state
- Identify inflection points (where trends changed)

---

## TONE

- Objective and data-driven
- Direct about persistent issues
- Acknowledge improvements where they exist
- Emphasize urgency for worsening trends
- Balance criticism with constructive recommendations
- Use phrases like:
  * "Confirmed:" when data validates hypothesis
  * "Validated:" when trend matches prediction
  * "Critical finding:" for urgent issues
  * "No progress:" when issue persists
  * "Worsening trend:" when metrics degrade

---

**Generate the complete incremental report now.**

---

## Usage Instructions

1. Replace `[EVENT_NAME]` and `[YEAR]` with actual values (e.g., "ECOMM 2025")
2. Ensure access to ALL previous reports for comparison
3. Use when `create_only_new=True`
4. Run as many times as needed before event
5. Save output to: `PA/reports/report_[event]_[DDMMYYYY].md`

**Example**: `PA/reports/report_ecomm_22092025.md`

---

## Notes for Report Generator

- Search project knowledge for ALL previous reports
- Query Neo4j for current metrics
- Calculate all trend indicators
- Build comparison tables automatically
- Track implementation status of recommendations
- Identify patterns across time periods