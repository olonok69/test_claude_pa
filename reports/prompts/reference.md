# Report Generation Prompts - Quick Reference Guide

## Overview

This document provides quick access to the three report generation prompts for your recommendation system pipeline.

---

## 📋 Three Report Scenarios

### 1️⃣ **Prompt 1: Initial Pre-Show Run Report**
**Use for:** First recommendation run before the event

**When:**
- ✅ First time running recommendations
- ✅ `create_only_new=False` in config
- ✅ No previous reports exist

**Output:** `PA/reports/report_ecomm_20082025.md`

**Sections:**
- Executive Summary
- Visitor Demographics and Retention
- Data Completeness and Quality
- Recommendation System Analysis
- Attribute Correlations and Patterns
- System Performance Issues
- Recommendations for Improvement
- Conclusion

---

### 2️⃣ **Prompt 2: Incremental Pre-Show Run Report**
**Use for:** Subsequent runs with new visitor additions

**When:**
- ✅ New visitors registered since last run
- ✅ `create_only_new=True` in config
- ✅ One or more previous reports exist

**Output:** `PA/reports/report_ecomm_22092025.md`

**Key Differences:**
- Progressive analysis (tracks trends across ALL runs)
- Implementation tracking (were previous recommendations applied?)
- Comparison tables showing timeline
- Focus on what's improving/worsening/stagnant

**Sections:**
- Executive Summary (with comparison)
- Progressive Demographics Analysis
- Progressive Recommendation Performance
- Sessions Never Recommended Tracking
- Key Insights from Progressive Analysis
- Recommendations Building on Previous Analysis
- Growth Rate and Scaling Analysis
- Conclusion (three-period summary)

---

### 3️⃣ **Prompt 3: Post-Show Analysis Report**
**Use for:** After event with badge scan data

**When:**
- ✅ Event has concluded
- ✅ Badge scan data processed
- ✅ `mode: "post_analysis"` in config
- ✅ `assisted_this_year` relationships created in Neo4j

**Output:** `PA/reports/post_show_analysis_ecomm_2025.md`

**Key Features:**
- Complete visitor journey funnel
- Recommendation hit rates and conversion rates
- Pre-show predictions vs actual reality
- Root cause analysis
- Business impact quantification
- Success metrics for next event

**Sections:**
- Executive Summary (performance assessment)
- Complete Visitor Journey
- Recommendation System Performance
- Pre-Show Predictions vs Post-Show Reality
- Show-Specific Breakdown
- Critical Issues Deep Dive (6 major issues)
- What Worked Well
- Root Cause Analysis (pattern of inaction)
- Actionable Recommendations for Next Event
- Success Metrics for Next Event
- Conclusion (bottom line assessment)
- Technical Notes
- Appendices (evolution tracking, predictions vs reality)

---

## 🎯 Quick Decision Tree

```
START
  ↓
Has the event occurred?
  ├─ NO → Continue
  │   ↓
  │   Is this the first recommendation run?
  │   ├─ YES → Use Prompt 1 (Initial Run)
  │   └─ NO → Use Prompt 2 (Increment Run)
  │
  └─ YES → Use Prompt 3 (Post-Show Analysis)
```

---

## 📁 File Naming Conventions

**Pre-Show Reports:**
```
PA/reports/report_[event]_[DDMMYYYY].md
```
Examples:
- `report_ecomm_20082025.md` (August 20, 2025)
- `report_ecomm_22092025.md` (September 22, 2025)

**Post-Show Reports:**
```
PA/reports/post_show_analysis_[event]_[year].md
```
Example:
- `post_show_analysis_ecomm_2025.md`

---

## ⚙️ Configuration Requirements

### For ALL Reports:
```yaml
event:
  name: "ecomm"
  year: 2025
  
recommendation:
  min_similarity_score: 0.5
  max_recommendations: 20
```

### For Post-Show ONLY:
```yaml
mode: "post_analysis"

post_analysis_mode:
  registration_shows:
    this_year_main:
      - ["ECE25", "TFM25"]
  scan_files:
    seminars_scan_reference_this: "path/to/file.csv"
    seminars_scans_this: "path/to/file.csv"
```

---

## 🗄️ Neo4j Requirements

### Pre-Show Reports (Prompts 1 & 2):
**Nodes:**
- `Visitor_this_year`
- `Sessions_this_year`
- `Visitor_last_year_bva`
- `Visitor_last_year_lva`
- `Stream`

**Relationships:**
- `IS_RECOMMENDED`
- `Same_Visitor`
- `attended_session`

### Post-Show Reports (Prompt 3):
**Additional Relationship Required:**
- `assisted_this_year` (actual attendance from badge scans)

**Verification:**
```cypher
// Check recommendations
MATCH ()-[r:IS_RECOMMENDED]->() 
RETURN COUNT(r)

// Check post-show attendance
MATCH ()-[r:assisted_this_year]->() 
RETURN COUNT(r)
```

---

## 📊 Report Content Comparison

| Section | Prompt 1 | Prompt 2 | Prompt 3 |
|---------|----------|----------|----------|
| Executive Summary | ✓ | ✓ | ✓ |
| Visitor Demographics | ✓ | ✓ Progressive | ✓ + Journey |
| Data Quality | ✓ | ✓ Trends | ✓ |
| Recommendation Analysis | ✓ | ✓ Evolution | ✓ Performance |
| Coverage Metrics | ✓ | ✓ Timeline | ✓ Hit Rates |
| Implementation Tracking | ✗ | ✓ | ✓ Complete |
| Predictions vs Reality | ✗ | ✗ | ✓ |
| Root Cause Analysis | ✗ | Partial | ✓ Deep Dive |
| Business Impact | Basic | ✓ | ✓ Quantified |
| Success Metrics | ✗ | ✗ | ✓ Next Event |

---

## 🎨 Report Formatting Standards

All reports use consistent markdown formatting:

**Headers:**
- `##` for main sections
- `###` for subsections
- `####` for detailed breakdowns

**Tables:**
- Used extensively for data presentation
- Include comparison columns in incremental reports
- Show trends and changes

**Visual Indicators:**
- ✓ Success/Correct
- ✗ Failure/Incorrect
- ⚠️ Critical priority
- 🔴 High priority
- 🟡 Medium priority
- ↗️ Worsening trend
- ↘️ Improving trend
- → Stable/No change
- ⭐ Excellent performance
- 🚫 Never recommended

**Bold Text:**
- **Critical metrics**
- **Key findings**
- **Priority actions**

---

## 🔄 Usage Workflow

### For Pre-Show Runs:

```
1. Run recommendation pipeline
   ↓
2. Verify Neo4j relationships created
   ↓
3. Select appropriate prompt (1 or 2)
   ↓
4. Replace [EVENT_NAME] and [YEAR] placeholders
   ↓
5. Provide prompt to Claude with MCP access
   ↓
6. Review generated report
   ↓
7. Save to PA/reports/ with correct filename
   ↓
8. Commit to version control
   ↓
9. Review recommendations
   ↓
10. Update config if implementing changes
```

### For Post-Show Analysis:

```
1. Event concludes
   ↓
2. Process badge scan data
   ↓
3. Run pipeline in post_analysis mode
   ↓
4. Verify assisted_this_year relationships
   ↓
5. Gather ALL pre-show reports
   ↓
6. Use Prompt 3
   ↓
7. Replace placeholders
   ↓
8. Provide prompt to Claude with MCP access
   ↓
9. Review comprehensive post-show report
   ↓
10. Extract actionable recommendations
   ↓
11. Plan next event improvements
   ↓
12. Document implementation decisions
```

---

## 📝 Customization Notes

### Replacing Placeholders:

In all prompts, replace:
- `[EVENT_NAME]` → e.g., "ECOMM" or "BVA"
- `[YEAR]` → e.g., "2025"
- Event-specific names in examples → your actual event names

### Adapting for Different Events:

The prompts are generic and work for:
- ✅ ECOMM events (ECE/TFM)
- ✅ BVA events (BVA/LVA)
- ✅ Any future events with similar structure

Key areas that may need adjustment:
- Event names (BVA/LVA vs ECE/TFM)
- Attribute names (industry vs specialty)
- Specific business rules (sponsors, sessions)

---

## 🚨 Common Issues & Solutions

### Issue: Report lacks historical comparison
**Solution:** Ensure all previous reports are in `PA/reports/` directory

### Issue: Missing Neo4j data
**Solution:** Run verification queries, check pipeline logs

### Issue: Post-show report fails
**Solution:** Verify `mode: "post_analysis"` and `assisted_this_year` relationships exist

### Issue: Placeholder not replaced
**Solution:** Search and replace ALL instances of `[EVENT_NAME]` and `[YEAR]`

---

## ✅ Pre-Generation Checklist

### Before Using Prompt 1:
- [ ] Neo4j populated with visitor and session data
- [ ] Recommendations generated (IS_RECOMMENDED exists)
- [ ] Configuration file accessible
- [ ] Placeholders replaced

### Before Using Prompt 2:
- [ ] All Prompt 1 prerequisites
- [ ] Previous report(s) available
- [ ] New visitors processed
- [ ] New recommendations generated

### Before Using Prompt 3:
- [ ] All Prompt 2 prerequisites
- [ ] Event completed
- [ ] Badge scan data processed
- [ ] Config set to post_analysis mode
- [ ] assisted_this_year relationships exist
- [ ] ALL pre-show reports available

---

## 📚 Additional Resources

**Full Implementation Guide:**
See separate artifact "Implementation Guide - Report Generation Prompts"

**Configuration Examples:**
- `config/config_ecomm.yaml`
- `config/config_vet.yaml`

**Example Reports:**
- `PA/reports/report_ecomm_20082025.md`
- `PA/reports/report_ecomm_22092025.md`
- `PA/reports/report_ecomm_post_10102025.md`

**Neo4j Schema Documentation:**
Use MCP tool `neo4j-dev:get_neo4j_schema` to view current schema

---

## 🎯 Key Success Factors

1. **Use the right prompt for the right scenario**
2. **Ensure all prerequisites are met**
3. **Keep all previous reports for comparison**
4. **Review reports before implementation**
5. **Document configuration changes**
6. **Track recommendation implementation**
7. **Commit reports to version control**

---

**Document Version:** 1.0  
**Last Updated:** October 2025  
**Maintained By:** Data Analytics Team

---

## Quick Links to Prompts

- **Prompt 1:** See artifact "Prompt 1: Initial Pre-Show Run Report"
- **Prompt 2:** See artifact "Prompt 2: Incremental Pre-Show Run Report"
- **Prompt 3:** See artifact "Prompt 3: Post-Show Analysis Report"
- **Implementation Guide:** See artifact "Implementation Guide - Report Generation Prompts"