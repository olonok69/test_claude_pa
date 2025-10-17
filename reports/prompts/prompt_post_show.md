# Prompt 3: Post-Show Analysis Report

## Instructions for Claude

You are a Senior Data Analyst creating a **POST-SHOW ANALYSIS** report for **[EVENT_NAME] [YEAR]**.

### CONTEXT

The event has concluded. Badge scan data has been processed and loaded into Neo4j. This report analyzes:
1. How well recommendations performed
2. Complete visitor journey from registration to actual attendance
3. Which pre-show predictions came true
4. Specific failures and successes
5. Actionable insights for next year

Configuration setting: `mode: "post_analysis"` in config file.

### DATABASE ACCESS

You have access to a Neo4j database (neo4j-dev) containing:
- `Visitor_this_year` nodes (current year registrations)
- `Sessions_this_year` nodes (this year's sessions)
- `IS_RECOMMENDED` relationships (pre-show recommendations)
- **`assisted_this_year` relationships (actual session attendance from badge scans)**
- `Stream` nodes
- Historical data: `Visitor_last_year_*`, `attended_session` relationships

### PROJECT KNOWLEDGE ACCESS

You have access to:
- **ALL PRE-SHOW REPORTS** (initial run + all increments)
- Configuration files showing recommendation algorithm parameters
- Post-analysis scan files and processing logs

---

## REPORT REQUIREMENTS

Generate a comprehensive markdown report with the following sections:

### 1. EXECUTIVE SUMMARY

Include:
- **Event Attendance Overview**
  * Total pre-registered visitors
  * Total venue visitors (badge scans)
  * Registration → venue conversion rate
- **Recommendation Performance**
  * Total recommendations sent
  * Visitors who attended ≥1 recommended session (hit rate %)
  * Email delivery → recommended session conversion rate
- **Top Issues Identified** (3-5 critical problems)
- **Key Successes** (what worked well)
- **Bottom Line Assessment**: Was the recommendation system effective? Yes/No and why

---

### 2. THE COMPLETE VISITOR JOURNEY

#### 2.1 Registration → Email → Attendance Funnel

Create detailed funnel showing:

```
┌─────────────────────────────────────────────────┐
│ Total Registered: X visitors                    │
└─────────────────────────────────────────────────┘
                    ↓ [Y%]
┌─────────────────────────────────────────────────┐
│ Recommendations Sent: Z visitors                │
│ (email delivery successful)                     │
└─────────────────────────────────────────────────┘
                    ↓ [Y%]
┌─────────────────────────────────────────────────┐
│ Venue Attendance: A visitors                    │
│ (badge scanned at venue)                        │
└─────────────────────────────────────────────────┘
                    ↓ [Y%]
┌─────────────────────────────────────────────────┐
│ Session Attendance: B visitors                  │
│ (attended any session)                          │
└─────────────────────────────────────────────────┘
                    ↓ [Y%]
┌─────────────────────────────────────────────────┐
│ Recommended Session Attendance: C visitors      │
│ (attended ≥1 recommended session)               │
└─────────────────────────────────────────────────┘
```

Calculate and highlight conversion rates at each stage.

#### 2.2 The Venue-to-Session Gap

**Analysis:**
- X visitors scanned badges at venue
- Y visitors attended at least one session (Y/X = Z%)
- Gap: (X-Y) visitors attended venue but NO sessions

**Why This Matters:**
- Wasted recommendations
- Lost engagement opportunity
- Sponsor exposure issues

**Pre-Show Warning Status:**
- Was this predicted? (Yes/No)
- Which report? (Date)
- Recommendation status: Implemented/Ignored

---

### 3. RECOMMENDATION SYSTEM PERFORMANCE

#### 3.1 Overall Hit Rate Analysis

**Primary Metrics:**
| Metric | Count | Percentage |
|--------|-------|------------|
| Visitors with recommendations | X | 100% |
| Attended ≥1 recommended session | Y | Z% ← **HIT RATE** |
| Attended NO recommended sessions | A | B% ← **MISS RATE** |

**Segmentation Analysis:**
| Segment | Total | Hit Rate | Miss Rate | Avg Sessions Attended |
|---------|-------|----------|-----------|---------------------|
| **Returning Visitors** | X | Y% | Z% | A |
| **New Visitors** | X | Y% | Z% | A |
| **Difference** | - | +/- X pts | +/- X pts | +/- A |

**Key Finding:** Returning visitors performed [better/worse/same] than new visitors

#### 3.2 Session-Level Recommendation Performance

Create comprehensive table for ALL sessions:

| Session Title | Times Recommended | Actual Attendance | Conversion Rate | Performance | Sponsor? |
|--------------|------------------|-------------------|-----------------|-------------|----------|
| Session A | 7,325 (98.7%) | 145 | 1.98% | ✗ Failed | No |
| Session B | 3,250 (43.8%) | 89 | 2.74% | ⚠️ Poor | Yes |
| Session C | 150 (2.0%) | 95 | 63.3% | ⭐ Excellent | No |
| Session D | 0 | 87 | N/A | 🚫 Never Recommended | Yes |

**Performance Categories:**
- ⭐ **Excellent**: >50% conversion (highly effective targeting)
- ✓ **Good**: 25-50% conversion (solid performance)
- ⚠️ **Poor**: <25% conversion (weak targeting)
- ✗ **Failed**: <5% conversion (complete failure)
- 🚫 **Never Recommended**: 0 recommendations (missed opportunity)

#### 3.3 Concentration Problem - Reality Check

**Pre-Show vs Post-Show Comparison:**

| Session | Pre-Show Recommendation % | Actual Attendance | Conversion Rate | Analysis |
|---------|--------------------------|-------------------|-----------------|----------|
| Top Session | 98.7% recommended | 145 attended | 1.98% | Massive over-recommendation |
| 2nd Session | 97.5% recommended | 132 attended | 1.85% | Massive over-recommendation |
| Mid Session | 45.2% recommended | 89 attended | 26.8% | Better targeting |
| Bottom Session | 2.1% recommended | 95 attended | 615% | Under-recommended success |

**Critical Finding:**
- Did over-recommendation correlate with actual attendance?
- Were pre-show concentration warnings accurate?
- Impact of ignoring concentration issue

#### 3.4 Sessions Never Recommended - Business Impact

**The Complete Picture:**

| Session Title | Session Type | Sponsor | Actual Attendance | Lost Recommendations | Business Impact |
|--------------|--------------|---------|-------------------|---------------------|-----------------|
| Session X | Content | Sponsor A | 87 | 7,420 possible | $XX,XXX lost value |
| Session Y | Social | None | 65 | 7,420 possible | Missed engagement |

**Total Impact:**
- X sessions never recommended
- Y of these were sponsored (financial impact)
- Z total attendees who might have been reached
- Estimated sponsor dissatisfaction risk: HIGH/MEDIUM/LOW

**Pre-Show Warning:**
- First identified: [Date]
- Repeated in: [X] reports
- Status: Never addressed
- Result: Predicted outcome occurred

---

### 4. PRE-SHOW PREDICTIONS VS POST-SHOW REALITY

#### 4.1 Prediction Accuracy Matrix

For EACH major issue raised in pre-show reports:

| Issue | First Identified | Prediction Made | Recommendation Given | Implemented? | Actual Outcome | Accuracy |
|-------|-----------------|-----------------|---------------------|--------------|----------------|----------|
| Over-concentration | 20/08/2025 | Top session will be over-recommended | Raise threshold to 0.6 | ✗ NO | Top session 1.98% conversion | ✓ Correct |
| Sponsor exclusion | 20/08/2025 | Sponsored sessions won't get recommendations | Force inclusion | ✗ NO | 31 sponsors got 0 recommendations | ✓ Correct |
| Venue-session gap | 11/09/2025 | Many will scan but not attend sessions | Track and analyze | ✗ NO | 50% gap confirmed | ✓ Correct |

**Prediction Accuracy Summary:**
- Total predictions: X
- Correct predictions: Y (Z%)
- Incorrect predictions: A (B%)
- Pattern: System accurately analyzed problems but recommendations ignored

#### 4.2 The Pattern of Accurate Analysis Without Action

**Timeline:**
1. **August 20**: Issues identified, recommendations made
2. **September 11**: Same issues worsening, recommendations repeated
3. **September 22**: Issues continuing to worsen, urgent recommendations
4. **Post-Show**: All predicted problems materialized

**The Disconnect:**
- Analysis quality: **EXCELLENT** (predicted outcomes accurately)
- Implementation rate: **POOR** (0% of critical recommendations implemented)
- Result: Predictable failure

---

### 5. SHOW-SPECIFIC BREAKDOWN

#### 5.1 Main Event (ECE/BVA) Performance

**Registration & Attendance:**
| Metric | Count | Percentage |
|--------|-------|------------|
| Pre-registered | X | - |
| Venue attendance | Y | Z% of registered |
| Session attendance | A | B% of venue |
| Recommended session attendance | C | D% of registered |

**Top Performing Sessions:**
[List top 5 by conversion rate]

**Problem Sessions:**
[List bottom 5 by conversion rate]

#### 5.2 Secondary Event (TFM/LVA) Performance

[Same structure as Main Event]

#### 5.3 Cross-Event Analysis

**Visitors Who Attended Both:**
- Count: X
- Recommendation hit rate: Y%
- Engagement level: [HIGH/MEDIUM/LOW]

#### 5.4 Returning Visitor Deep Dive

**Performance Comparison:**
| Metric | Returning Visitors | New Visitors | Difference |
|--------|-------------------|--------------|------------|
| Hit rate | 29.5% | 24.3% | +5.2 pts ✓ |
| Avg sessions attended | 3.2 | 2.7 | +0.5 ✓ |
| Conversion rate | 15.8% | 11.2% | +4.6 pts ✓ |

**Validation:** Pre-show hypothesis that returning visitors would perform better was **CORRECT**

---

### 6. CRITICAL ISSUES - DEEP DIVE

#### 6.1 The Venue-to-Session Gap

**The Problem:**
- X visitors scanned badges (came to venue)
- Y visitors attended at least one session
- Gap: Z visitors (Z%) came but attended NOTHING
- Impact: Wasted X recommendations

**Root Causes:**
1. Late arrivals missing scheduled sessions
2. Venue attractions (exhibit hall) vs sessions
3. Poor session timing
4. Recommendation timing (too early/late)
5. Room capacity/finding issues

**Evidence:**
[Specific data supporting each cause]

**Pre-Show Warning:**
- Report [DATE]: "Concern about venue vs session attendance"
- Recommendation: "Track separately and analyze"
- Status: Tracked post-event, could have been monitored real-time

**Impact:**
- Recommendation waste: Z recommendations sent but never had chance
- Sponsor exposure loss
- Engagement opportunity loss

#### 6.2 The Over-Recommendation Problem

**The Problem:**
- Top 5 sessions recommended to >90% of visitors
- Actual conversion rates: 1.5-2.5%
- Result: 98% of recommendations wasted on these sessions

**Reality Check:**
```
Session: "Where eCommerce is Headed"
Recommended to: 7,325 visitors (98.7%)
Actually attended: 145 visitors
Conversion rate: 1.98%
Waste: 7,180 (98%) recommendations had no effect
```

**Root Cause:**
- Similarity threshold too low (0.5)
- Insufficient diversity constraints
- Dominant cluster (AI interest) overwhelmed algorithm
- Weights not optimized for differentiation

**Pre-Show Warning:**
- First identified: August 20, 2025
- Repeated in: 3 reports
- Recommendation: Raise threshold to 0.6-0.7
- Status: ✗ Never implemented
- Predicted outcome: "Complete personalization failure"
- Actual outcome: **Prediction 100% accurate**

**Impact:**
- Personalization effectively failed
- All visitors got nearly identical recommendations
- Defeats entire purpose of recommendation system

#### 6.3 The Sponsor Problem

**The Problem:**
- 31 sponsored sessions received ZERO recommendations
- Sponsors paid for exposure
- System excluded them entirely

**Financial Impact:**
- Estimated sponsor value: $XX,XXX per session
- Total at risk: $XXX,XXX
- Reputational damage: HIGH

**Sponsor Sessions That Performed Well (Despite No Recommendations):**
| Session | Sponsor | Attendance | Conversion if Recommended |
|---------|---------|------------|--------------------------|
| Session X | Sponsor A | 87 | Could have been 2,000+ |

**The Bitter Irony:**
- Some never-recommended sessions had EXCELLENT organic attendance
- If recommended, could have been major successes
- Proves recommendation system works when used correctly

**Pre-Show Warning:**
- First identified: August 20, 2025
- Recommendation: "Force inclusion for sponsored sessions"
- Status: ✗ Never implemented
- Business risk: **CRITICAL** - sponsor contracts at risk

#### 6.4 The Recommendation Conversion Problem

**The Problem:**
- Overall email → recommended session attendance: 12.8%
- Wide variance: 0% to >100% conversion
- Indicates broken targeting calibration

**Evidence:**
- 45% of sessions: <10% conversion (too broadly recommended)
- 15% of sessions: >50% conversion (well targeted)
- 20% of sessions: 0% conversion (complete failure)

**Possible Causes:**
1. Poor similarity matching
2. Threshold too low (over-recommendation)
3. Timing issues (recommendations too early/late)
4. Lack of diversity in recommendations
5. Not considering capacity/popularity

**Impact:**
- System credibility damaged
- User trust in recommendations low
- Sponsor ROI questionable

#### 6.5 The Calibration Problem

**The Problem:**
- Massive variance in conversion rates
- No consistent performance pattern
- Suggests algorithm not properly tuned

**Evidence:**
- Best session: 615% conversion (under-recommended by 84%)
- Worst sessions: 0% conversion (should never have been recommended)
- Top recommended: 1.98% conversion (over-recommended by 98%)

**Root Cause:**
- No calibration against historical attendance
- No capacity awareness
- No popularity adjustment
- Pure similarity matching without business logic

**Impact:**
- Resource allocation failures
- Overcrowding risk in under-recommended popular sessions
- Empty rooms in over-recommended niche sessions

#### 6.6 The Late Registration Gap

**The Problem:**
- Visitors who registered in last 2 weeks: X
- These received fewer/no recommendations
- Attended Y% fewer sessions than early registrants

**Evidence:**
| Registration Period | Count | Avg Recommendations | Hit Rate | Sessions Attended |
|--------------------|-------|-------------------|----------|-------------------|
| Early (>30 days) | X | 20.5 | 28.3% | 3.4 |
| Mid (15-30 days) | Y | 20.2 | 26.1% | 3.1 |
| Late (<15 days) | Z | 12.3 | 18.7% | 2.3 |

**Impact:**
- Late registrants underserved
- Missed engagement opportunity
- System not optimized for continuous registration

---

### 7. WHAT WORKED WELL

#### 7.1 Successes (With Quantitative Evidence)

✓ **Well-Targeted Sessions:**
- 12 sessions achieved >50% conversion
- Proves system CAN work when properly calibrated
- Examples: [List top 3 with metrics]

✓ **Returning Visitor Performance:**
- 19.5% better hit rate than new visitors
- Validates value of historical data
- Proves returning visitor algorithm works

✓ **Data Infrastructure:**
- Pipeline processed X records reliably
- Neo4j scaling handled growth well
- No technical failures

✓ **Small Batch Success:**
- Sessions recommended to <30% had 45% avg conversion
- Shows targeting works when not over-diluted

✓ **Cross-Event Patterns:**
- Visitors attending both events: X% higher engagement
- Validates multi-event recommendation strategy

---

### 8. ROOT CAUSE ANALYSIS - PATTERN OF INACTION

#### 8.1 Complete Implementation Tracking

| Report Date | Recommendation | Category | Priority | Implemented? | Result if Not Implemented |
|-------------|---------------|----------|----------|--------------|--------------------------|
| 20/08/2025 | Raise threshold 0.5 → 0.6 | Algorithm | ⚠️ CRITICAL | ✗ NO | Concentration 98.7%, 1.98% conversion |
| 20/08/2025 | Force sponsor inclusion | Business | ⚠️ CRITICAL | ✗ NO | 31 sponsors excluded |
| 11/09/2025 | Implement diversity constraints | Algorithm | 🔴 HIGH | ✗ NO | Top 5 all >95% |

**Implementation Rate: 0% for CRITICAL priorities**

#### 8.2 What Went Right vs What Went Wrong

**What Went Right:**
- ✓ Excellent analysis
- ✓ Accurate predictions
- ✓ Clear recommendations
- ✓ Early identification

**What Went Wrong:**
- ✗ Zero implementation
- ✗ Ignored warnings
- ✗ No feedback loop
- ✗ Predictable failure occurred

---

### 9. ACTIONABLE RECOMMENDATIONS FOR NEXT EVENT

#### 9.1 Immediate Actions ⚠️ CRITICAL

**1. ⚠️ CRITICAL: Fix Similarity Threshold**
- Current: 0.5
- Required: 0.7
- Expected impact: Reduce top session to <80%

**2. ⚠️ CRITICAL: Mandatory Sponsor Inclusion**
- Rule: ALL sponsored sessions must appear
- Minimum: 15% of visitors per sponsored session

**3. 🔴 HIGH PRIORITY: Increase Country Weight**
- Current: 0.3
- Required: 0.6

**4. 🔴 HIGH PRIORITY: Implement Diversity Constraints**
- Rule: Max 80% of visitors per session

**5. 🔴 HIGH PRIORITY: Earlier Recommendation Timing**
- Current: 1 week before
- Required: 2-3 weeks before

---

### 10. SUCCESS METRICS FOR NEXT EVENT

| Metric | Current (2025) | Target (2026) | Stretch Goal |
|--------|----------------|---------------|--------------|
| Recommendation Hit Rate | 25.3% | 40% | 50% |
| Email → Session Conversion | 12.8% | 25% | 35% |
| Sponsor Coverage | 73.3% | 100% | 100% |
| Top Session Concentration | 98.7% | <80% | <70% |

---

### 11. CONCLUSION

**Bottom Line:** Strong potential but poor execution.

**The Good:**
- Data infrastructure performed flawlessly
- Analysis was accurate and predictive
- Well-targeted sessions achieved 50%+ conversion

**The Bad:**
- Only 25.3% hit rate
- 12.8% email → session conversion
- Top session over-recommended by 98%

**The Ugly:**
- 31 sponsored sessions got ZERO recommendations
- Every critical issue predicted came true
- Zero implementation of recommendations

**The Path Forward:**
If recommendations implemented → 40-45% hit rate achievable next year

---

**Generate the complete post-show analysis report now.**

---

## Usage Instructions

1. Replace `[EVENT_NAME]` and `[YEAR]` with actual values
2. Ensure `mode: "post_analysis"` in config
3. Run after event with badge scan data processed
4. Ensure access to ALL pre-show reports
5. Save to: `PA/reports/post_show_analysis_[event]_[year].md`