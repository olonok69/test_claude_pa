# Recommendation System — Event Evaluation Framework

**Scope:** This document explains **how events are evaluated** across the full recommendation pipeline lifecycle: what metrics are collected, how the visitor journey funnel is structured, how A/B testing works, and how post-show performance is scored.

It applies to all events using this pipeline (LVA, CPCN, TSL, ECOMM, and future shows).

---

## 1. Overview: Three Evaluation Phases

Each event is evaluated across three distinct phases, each with its own report type and prompt template.

| Phase | Mode | Prompt Template | Timing |
|-------|------|-----------------|--------|
| **Pre-show (initial)** | `personal_agendas` | `prompt_initial_run_generic.md` | First pipeline run, weeks before event |
| **Pre-show (increment)** | `personal_agendas` | `prompt_increment_run.md` | Each subsequent run as registrations grow |
| **Post-show** | `post_analysis` | `prompt_post_show_generic.md` | After event, once badge scans are loaded |
| **Post-show executive** | `post_analysis` | `prompt_post_show_summary_generic.md` | Same time; condensed for management |

The pipeline also supports an **engagement campaign** (mode: `engagement`) targeting prior-year attendees before current-year registration opens. Engagement results are measured in the post-show phase alongside personal agendas.

---

## 2. The Visitor Journey Funnel

The core of every post-show evaluation is the **visitor journey funnel**. It tracks every registrant from sign-up through actual session attendance.

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: Registration                                          │
│  All visitors who registered for the event                      │
│  Source: Visitor_this_year nodes (WHERE v.show = '[SHOW_CODE]') │
├─────────────────────────────────────────────────────────────────┤
│  STAGE 2: Recommendation Coverage                               │
│  Visitors who received a personal agenda recommendation email   │
│  Source: has_recommendation = '1' AND control_group = 0        │
├─────────────────────────────────────────────────────────────────┤
│  STAGE 3: Venue Attendance                                      │
│  Visitors who physically entered the show venue                 │
│  Source: (v)-[:registered_to_show]->()                          │
├─────────────────────────────────────────────────────────────────┤
│  STAGE 4: Session Engagement                                     │
│  Visitors who attended at least one content session             │
│  Source: (v)-[:assisted_session_this_year]->(s)                 │
│  (excluding admin/placeholder sessions)                         │
├─────────────────────────────────────────────────────────────────┤
│  STAGE 5: Recommendation Hit                                    │
│  Visitors who attended at least one RECOMMENDED session         │
│  Source: attended session_id ∩ IS_RECOMMENDED session_id        │
│  (treatment group only for causal measurement)                  │
└─────────────────────────────────────────────────────────────────┘
```

### Funnel Table Format (used in all post-show reports)

| Stage | Treatment (sent recs) | Control (withheld) | Total |
|-------|:--------------------:|:------------------:|:-----:|
| Registered | N₁ | N₂ | N |
| Attended venue | n₁ | n₂ | n |
| Attended ≥1 session | s₁ | s₂ | s |
| Attended ≥1 recommended session | h₁ | — | h |

**Stage conversion rates:**
- **Venue attendance rate** = Stage 3 / Stage 1
- **Session engagement rate** = Stage 4 / Stage 3
- **Recommendation hit rate (visitor-level)** = Stage 5 / Stage 4 (treatment group)

### Special Sessions Exclusion

Administrative sessions (opening remarks, networking slots, placeholders) are excluded from all attendance metrics. The exclusion list is built in **Task 0** of each post-show prompt before any metrics are calculated.

---

## 3. A/B Testing Design

### 3.1 Control Group Assignment

The pipeline assigns a **control group** at recommendation generation time:

- All visitors receive recommendation scores computed identically
- `[CONTROL_GROUP_PCT]%` of eligible visitors are randomly assigned to `control_group = 1`
- These visitors are **withheld from receiving the email** (CampaignDelivery.status = `withheld_control`)
- All visitors — treatment and control — have `IS_RECOMMENDED` relationships in Neo4j
- This preserves the ability to compute **organic hit rates** post-show

**Configuration:** `recommendation.control_group.percentage` in event YAML.
**Randomization:** `recommendation.control_group.random_seed` ensures reproducibility.

### 3.2 Campaign Traceability (New Architecture)

Since TSL 2026, all campaigns are tracked via the full traceability schema:

| Neo4j Entity | Role |
|-------------|------|
| `RecommendationRun` node | One node per pipeline execution; stores `run_id`, `run_mode`, `campaign_id`, `show`, `created_at` |
| `IS_RECOMMENDED` relationship | Carries `run_id`, `run_mode`, `control_group` per recommendation |
| `CampaignDelivery` node | Delivery record per visitor per run; `status` = `sent` or `withheld_control` |
| `FOR_VISITOR` relationship | `CampaignDelivery` → `Visitor_this_year` |
| `FOR_RUN` relationship | `CampaignDelivery` → `RecommendationRun` |

This enables:
- Run-level ledger (who was targeted per campaign)
- Visitor exposure timeline (which campaigns reached each person)
- Outcome joins (attendance outcomes per campaign)

### 3.3 Multi-Run Events

A typical event may have multiple runs. The run ledger shows all campaigns in sequence:

| Run | run_mode | Purpose | Audience |
|-----|----------|---------|----------|
| Engagement | `engagement` | Re-engage prior attendees pre-registration | Prior-year visitors |
| PA Initial | `personal_agendas` | First personal agenda to all registered | All current-year registrants |
| PA Increment | `personal_agendas` | Cover new registrations since initial run | Late registrants only |

Post-show analysis should always use the **PA Initial run** for the primary A/B test (it has the largest control group). Increment runs add coverage but have smaller, independently sampled control groups.

---

## 4. Core Performance Metrics

### 4.1 Recommendation Effectiveness Metrics

| Metric | Formula | Interpretation |
|--------|---------|---------------|
| **Session-level hit rate** | (Attended sessions that were recommended) / (Total sessions attended) | How often attended sessions were recommended |
| **Visitor-level hit rate** | (Visitors who attended ≥1 recommended session) / (Visitors who attended sessions) | % of session-attending visitors who saw relevance |
| **Organic hit rate** | Same as visitor-level hit rate, but for control group | Natural recommendation overlap without email |
| **Absolute lift** | Treatment hit rate − Organic hit rate | True causal impact of sending recommendations, in pp |
| **Relative lift** | (Treatment − Organic) / Organic × 100% | % improvement over baseline behaviour |

### 4.2 Conversion Metrics (Session Level)

| Metric | Formula | Interpretation |
|--------|---------|---------------|
| **Session conversion rate** | (Unique visitors attending session) / (Visitors recommended that session) × 100 | How many recommended visitors actually attended |
| **Under-recommendation signal** | Conversion rate > 200% | Session more popular than algorithm expected — increase recommendations |
| **Over-recommendation signal** | High recommendation count + very low conversion | Session over-recommended relative to demand |

### 4.3 Statistical Significance

The A/B test uses a **two-proportion z-test**:

```
              p̂₁ − p̂₂
z = ─────────────────────────────────
     √[ p̂(1−p̂) × (1/n₁ + 1/n₂) ]

where p̂ = (x₁ + x₂) / (n₁ + n₂)   (pooled proportion)
      p̂₁ = treatment hit rate
      p̂₂ = organic hit rate
      n₁ = treatment session attendees
      n₂ = control session attendees
```

**Decision rule:** If |z| > 1.96, the lift is statistically significant at the 5% level (p < 0.05).

**95% Confidence interval on lift:**

```
CI = (p̂₁ − p̂₂) ± 1.96 × √[ p̂₁(1−p̂₁)/n₁ + p̂₂(1−p̂₂)/n₂ ]
```

### 4.4 Statistical Power

Control group size determines the **minimum detectable effect (MDE)**:

| Control % | Approx. Control Visitors (at 15K total) | MDE (α=0.05, power=0.80) |
|:---------:|:--------------------------------------:|:-------------------------:|
| 5% | ~750 | ~3.5pp |
| 10% | ~1,500 | ~2.5pp |
| 15% | ~2,250 | ~2.0pp |

Larger control groups detect smaller effects with the same confidence. The current recommended allocation is **15%** for events with ≥ 5,000 registered visitors.

---

## 5. Pre-Show Quality Metrics

Pre-show reports assess system readiness before the event. Key metrics:

### 5.1 Data Quality (Weighted Coverage)

For each attribute in `recommendation.similarity_attributes`:

```
Weighted coverage = Σ (weight_i × fill_rate_i) / Σ weight_i
```

Where `fill_rate_i` = % of visitors where attribute_i is non-null and not "NA".

**Targets:**
- Overall weighted coverage ≥ 90%: ✅ Good
- Overall weighted coverage 80–89%: ⚠️ Acceptable
- Overall weighted coverage < 80%: 🔴 Action required

### 5.2 Recommendation Coverage

```
Coverage = Visitors with IS_RECOMMENDED relationships / Total registered visitors
```

Target: **100%** for all eligible visitors before final pipeline run.

### 5.3 Session Concentration

```
Max concentration = Most-recommended session's unique visitor reach / Total visitors with recommendations
```

**Thresholds:**
- < 20%: ✅ Well diversified
- 20–40%: ⚠️ Moderate — monitor
- > 40%: 🔴 Concentration risk — review algorithm weights

### 5.4 Stream Coverage

```
Stream coverage = Sessions with HAS_STREAM relationship / Total sessions
```

Target: > 95%. Sessions without streams cannot contribute to stream-weighted collaborative filtering.

### 5.5 Control Group Demographic Balance

The control group should mirror the treatment group's demographics. A delta > 3pp on any key dimension (new/returning ratio, top segment) indicates a skew that **must be corrected in post-show segmented analysis**.

Common skew sources:
- Small control group (< 5%) exaggerates random demographic variance
- Non-stratified random sampling over-/under-samples returning visitors

---

## 6. Pre-Show Report Sections (Tasks 1–14)

| Task | Section | Key Output |
|------|---------|------------|
| 1 | Event Overview & Executive Summary | Metrics scorecard, coverage %, grade |
| 2 | Visitor Demographics & Retention | New/returning split, attribute distributions |
| 3 | Data Quality & Completeness | Weighted fill rate per attribute |
| 4 | Session Analysis & Stream Coverage | Stream distribution, orphaned sessions |
| 5 | Recommendation Generation Analysis | Avg recs, score distribution, coverage |
| 6 | Top Recommended Sessions & Concentration | Max concentration, diversity metrics |
| 7 | Historical Attendance Integration | Collaborative filtering data quality |
| 8 | Configuration Analysis | Attribute weights, feature flags |
| 9 | Sample Recommendation Walkthrough | 3 visitor examples |
| 10 | System Performance Assessment | Pipeline timing, throughput |
| 11 | Data Quality Scorecard | Aggregated quality grade |
| 12 | Priority Actions & Recommendations | P1/P2/P3 action list |
| 13 | Conclusion & Overall System Assessment | Final grade, bottom line |
| 14 | Report Enrichment & Executive Wrap-Up | Cross-check, business implications |

---

## 7. Post-Show Report Sections (Tasks 0–14)

| Task | Section | Key Output |
|------|---------|------------|
| 0 | Excluded Sessions Identification | Admin session exclusion list |
| 1 | Campaign Journey & Run Ledger | Run-by-run delivery table |
| 2 | Visitor Registration & Attendance Funnel | 5-stage funnel table, late registrant impact |
| 3 | A/B Test — Personal Agendas | Treatment/control hit rates, lift, CI, significance |
| 4 | A/B Test — Engagement Campaign | Engagement treatment/control results |
| 5 | Session Hit Rate & Conversion Analysis | Top sessions, under-rec, best converters |
| 6 | Visitor-Level Performance Analysis | Overall hit rate, sessions-per-attendee |
| 7 | Stream-Level Analysis | Recommendations vs attendance by stream |
| 8 | V2E Exhibitor Recommendations | Exhibitor hit rate (if scan data available) |
| 9 | Pre-Show Predictions vs Reality | Prediction/reality table with root causes |
| 10 | Data Quality Retrospective | Fill rates for attendees, profile completeness effect |
| 11 | Algorithm Assessment & Grade | 6-dimension scoring, pre/post comparison |
| 12 | Priority Actions for Next Event | P1/P2/P3 table with Owner + Timeline |
| 13 | Conclusion & Overall Assessment | Final grade, business implications |
| 14 | Report Enrichment & Executive Wrap-Up | Cross-check, bottom line sentence |

---

## 8. Algorithm Grading System

All reports assign a 0–100 score across 6 dimensions. The weights differ between pre-show and post-show.

| Dimension | Pre-Show Weight | Post-Show Weight | What is Measured |
|-----------|:--------------:|:----------------:|------------------|
| Coverage | 25% | 20% | % visitors with recommendations + late registrant gap |
| Hit Rate Quality | N/A (pre-show) | 25% | Treatment visitor hit rate vs event benchmark |
| Causal Lift | N/A (pre-show) | 20% | Statistical significance + absolute lift size |
| Calibration | 25% | 15% | Session concentration + under/over-recommendation balance |
| Data Quality | 25% | 10% | Weighted attribute fill rate |
| Engagement | N/A (pre-show) | 10% | Engagement campaign hit rate (if applicable) |
| Algorithm | 25% | N/A (post-show) | Similarity score distribution, diversity metrics |

**Grade scale:**

| Score | Grade | Assessment |
|:-----:|:-----:|:----------:|
| 90–100 | A | Outstanding |
| 80–89 | B+ / B | Good — minor issues |
| 70–79 | C+ / C | Adequate — improvements needed |
| 60–69 | D | Below average — significant gaps |
| < 60 | F | Poor — critical failures |

---

## 9. Benchmarks & Baselines

| Metric | Typical Range | Strong Performance |
|--------|:-------------:|:-----------------:|
| Venue attendance rate | 50–75% of registered | > 65% |
| Session engagement rate (of venue attendees) | 30–60% | > 50% |
| Visitor-level hit rate (treatment) | 25–40% | > 35% |
| Organic hit rate (control) | 15–30% | — |
| Absolute lift | 5–15pp | > 10pp |
| Relative lift | 15–50% | > 30% |
| Recommendation coverage | 90–100% | 100% |
| Weighted data quality | 85–97% | > 93% |
| Max session concentration | 15–40% | < 25% |
| Stream coverage | 90–100% | > 95% |

**Cross-event benchmarks (from existing reports):**

| Event | Year | Visitor-Level Hit Rate | Absolute Lift | Notes |
|-------|:----:|:---------------------:|:------------:|-------|
| LVS (London Vet Show) | 2025 | 34.4% | Not yet measured | Pre-traceability |
| CPCN | 2025 | ~30% | Not yet measured | Estimated |
| TSL | 2026 | TBD post-show | TBD | First full A/B test with 15% control |

*Update this table after each post-show report.*

---

## 10. Segmented Analysis Requirements

### When Segmentation is Required

Segmented lift analysis is **required** (not optional) when:
1. The pre-show report documents a control group demographic skew > 3pp on any dimension
2. The event serves distinct audience types (e.g., new vs returning, multiple co-located shows)
3. Engagement and PA campaigns overlap on the same visitor population

### Standard Segmentation Dimensions

| Segment | Source | Purpose |
|---------|--------|---------|
| New vs Returning | `Same_Visitor` relationship existence | Controls for retention effect |
| Primary similarity attribute | Highest-weight field in `similarity_attributes` | Validates algorithm targeting |
| Co-located show (if applicable) | `Sessions_this_year.show` or theatre field | Multi-show lift comparison |

### Weighted Average Lift

When the control group is demographically imbalanced, report a **weighted average lift** alongside the overall figure:

```
Weighted lift = (new_treatment_proportion × new_lift) + (returning_treatment_proportion × returning_lift)
```

Use **treatment group proportions** as weights (not control group proportions).

---

## 11. V2E (Visitor-to-Exhibitor) Recommendations

V2E recommendations match visitors to exhibitor stands. They run via a separate pipeline and are imported into Neo4j via `import_v2e_recommendations_to_neo4j.py`.

**Neo4j representation:** `(Visitor_this_year)-[:IS_RECOMMENDED_EXHIBITOR {run_id, run_mode}]->(Exhibitor)`

**Post-show measurement** (when exhibitor scan data is available):
- V2E visitor-level hit rate = % of visitors who attended at least one recommended exhibitor stand
- Requires `(Visitor_this_year)-[:visited_exhibitor_this_year]->(Exhibitor)` relationships

**Pre-show coverage metrics:**
- Visitor coverage: % of registrants with ≥1 V2E recommendation
- Exhibitor coverage: % of exhibitors recommended to ≥1 visitor
- Concentration: distribution of recommendations per exhibitor (watch for top-heavy distribution)

---

## 12. Report Configuration Checklist

Before generating any post-show report, verify:

### Data Readiness
- [ ] `assisted_session_this_year` relationships exist (badge scan data loaded)
- [ ] `registered_to_show` relationships exist (venue entry scan data loaded)
- [ ] All `RecommendationRun` nodes present for this show
- [ ] `CampaignDelivery` nodes present with correct status values
- [ ] `post_analysis_mode.scan_files` paths updated in config YAML for this year's files
- [ ] `post_analysis_mode.registration_shows.this_year_main` codes updated

### Report Setup
- [ ] Pre-show report path available at `[PRE_SHOW_REPORT_PATH]`
- [ ] `reporting_pipeline.yaml` profile configured with `report_type: "post_show"`
- [ ] Run IDs identified from `RecommendationRun` nodes
- [ ] `[EXCLUDED_SESSION_IDS]` list built from Task 0

### Configuration YAML Reference
- [ ] `recommendation.similarity_attributes` — for segmentation and data quality analysis
- [ ] `recommendation.control_group.percentage` — for A/B test design documentation
- [ ] `recommendation.control_group.random_seed` — for reproducibility reference
- [ ] `default_visitor_properties` — for NA value pattern identification

---

## 13. File Naming Conventions

| Report Type | File Name Pattern | Example |
|-------------|------------------|---------|
| Pre-show initial | `report_[show]_[YYYYMMDD].md` | `report_lva_07112025.md` |
| Pre-show increment | `report_[show]_[YYYYMMDD].md` | `report_lva_23092025.md` |
| Post-show full | `report_[show]_post_show_[YYYYMMDD].md` | `report_lva_post_show_28112025.md` |
| Post-show summary | `report_[show]_post_show_summary_[YYYYMMDD].md` | `report_lva_post_show_summary_28112025.md` |

All reports saved to: `deep_agents_reports/reports/`

---

## 14. Reporting Pipeline Integration

Reports are generated via `reporting_pipeline.py` using profiles in `config/reporting_pipeline.yaml`.

### Post-show profile example
```yaml
[show][year]_post:
  event: "[show]"
  year: [year]
  mode: "post_analysis"
  report_type: "post_show"
  neo4j_env: "prod"
  config_path: "config/config_[show].yaml"
  prompt_template: "reports/prompts/prompt_post_show_generic.md"
  neo4j_profile: "prod"
  neo4j_database: "neo4j"
  provider_phase1: "anthropic"
  model_phase1: "claude-sonnet-4-5"       # Use capable model for post-analysis
  temperature_phase1: 0.1
  max_tokens_phase1: 12000                 # Higher limit for comprehensive analysis
  pre_show_report: "reports/report_[show]_[YYYYMMDD].md"
  example_report: "reports/report_[show]_post_show_[YYYYMMDD].md"  # Prior year if available
  enable_enrichment: true
  provider_phase2: "anthropic"
  model_phase2: "claude-sonnet-4-5"
  temperature_phase2: 0.1
  max_tokens_phase2: 16000
```

### Executive summary profile example
```yaml
[show][year]_post_summary:
  event: "[show]"
  year: [year]
  mode: "post_analysis"
  report_type: "post_show_summary"
  neo4j_env: "prod"
  config_path: "config/config_[show].yaml"
  prompt_template: "reports/prompts/prompt_post_show_summary_generic.md"
  neo4j_profile: "prod"
  neo4j_database: "neo4j"
  provider_phase1: "anthropic"
  model_phase1: "claude-sonnet-4-5"
  temperature_phase1: 0.1
  max_tokens_phase1: 6000
  pre_show_report: "reports/report_[show]_[YYYYMMDD].md"
  enable_enrichment: false                 # No enrichment needed for summary
```

---

## 15. Quick Reference: Key Cypher Patterns

### Funnel Stage 3 — Venue Attendance
```cypher
MATCH (v:Visitor_this_year)-[:registered_to_show]->()
WHERE v.show = '[SHOW_CODE]'
RETURN count(DISTINCT v) AS venue_attendees
```

### Funnel Stage 4 — Session Attendance (excluding admin)
```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]'
  AND (s.show = '[SHOW_CODE]' OR s.show IS NULL)
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
RETURN count(DISTINCT v) AS session_attendees
```

### Visitor-Level Hit Rate (Treatment)
```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND v.control_group = 0
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
WITH v, collect(DISTINCT s.session_id) AS attended
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(rec:Sessions_this_year)
WHERE rec.session_id IN attended
WITH v, CASE WHEN count(rec) > 0 THEN 1 ELSE 0 END AS had_hit
RETURN count(v) AS attendees,
       sum(had_hit) AS with_hit,
       round(100.0 * sum(had_hit) / count(v), 2) AS visitor_hit_rate_pct
```

### Absolute Lift Calculation
```cypher
MATCH (v:Visitor_this_year)-[a:assisted_session_this_year]->(s:Sessions_this_year)
WHERE v.show = '[SHOW_CODE]' AND v.control_group IN [0, 1]
  AND NOT s.session_id IN [EXCLUDED_SESSION_IDS]
OPTIONAL MATCH (v)-[r:IS_RECOMMENDED {run_id: '[PA_INITIAL_RUN_ID]'}]->(s)
WITH v.control_group AS ctrl, count(a) AS attended,
     count(CASE WHEN r IS NOT NULL THEN 1 END) AS hits
WITH ctrl, 100.0 * sum(hits) / sum(attended) AS hit_rate
WITH collect({flag: ctrl, rate: hit_rate}) AS rates
RETURN
  round([x IN rates WHERE x.flag = 0][0].rate, 2) AS treatment_rate,
  round([x IN rates WHERE x.flag = 1][0].rate, 2) AS organic_rate,
  round([x IN rates WHERE x.flag = 0][0].rate - [x IN rates WHERE x.flag = 1][0].rate, 2) AS absolute_lift_pp
```

### Run Ledger
```cypher
MATCH (rr:RecommendationRun) WHERE rr.show = '[SHOW_CODE]'
OPTIONAL MATCH (d:CampaignDelivery)-[:FOR_RUN]->(rr)
RETURN rr.run_id, rr.run_mode, rr.campaign_id, rr.created_at,
  count(CASE WHEN d.status = 'sent' THEN 1 END) AS sent,
  count(CASE WHEN d.status = 'withheld_control' THEN 1 END) AS withheld_control
ORDER BY rr.created_at
```
