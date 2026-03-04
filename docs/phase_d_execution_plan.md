# Phase D Execution Plan (Post-Show)

## Objective
Compute post-show performance with two clear tracks:
- **Track A (Causal):** personal agendas treatment vs control.
- **Track B (Descriptive):** engagement campaign performance (no causal claim).

## Why engagement has no causal lift in this cycle
- Engagement mode runs without randomized control group.
- Suppression is rule-based (not random), so cohorts are selection-biased.
- Without random assignment, differences can come from visitor mix/timing, not campaign effect.
- Therefore, engagement results are **descriptive/associational**, not causal.

## Inputs to freeze before analysis
- Personal agendas mailed exports (initial + incremental run on March 2).
- Personal agendas control exports (initial + incremental).
- Engagement mailed export(s).
- Engagement suppression report (`engagement_previously_mailed_exclusions.csv`).
- Post-analysis attendance graph outputs (`assisted_session_this_year`, `registered_to_show`) and files.
- Config snapshots used for each run.

## Canonical cohort model
Build a visitor-level table with one row per canonical visitor identity (`BadgeId`, fallback `forename_surname_email`):
- `pa_treatment` (0/1)
- `pa_control` (0/1)
- `engagement_mailed` (0/1)
- `engagement_suppressed` (0/1)
- `attended_any` (0/1)
- `attended_recommended_pa` (count)
- `attended_recommended_engagement` (count)
- `total_attended_sessions` (count)
- segmentation fields (new/returning, sector, function, country)

Hard checks:
- `pa_treatment` and `pa_control` must be mutually exclusive.
- Identity match rate target >= 98%.
- Attendance linkage target >= 95%.

## Execution steps
1. **Ingest & normalize files**
   - Parse all campaign exports and post-analysis attendance artifacts.
   - Normalize identity fields and deduplicate.
2. **Create cohort master table**
   - Merge campaign flags and attendance outcomes.
   - Apply precedence rules and QA checks.
3. **Compute Track A (causal, personal agendas only)**
   - Treatment/control hit rates, absolute lift, relative lift.
   - Two-proportion z-test and 95% CI.
   - Repeat by segment where sample size >= threshold.
4. **Compute Track B (descriptive, engagement)**
   - Coverage, attendance rate, recommendation hit rate.
   - Suppression effectiveness and overlap with personal agendas.
5. **Publish report with strict labeling**
   - Section 1: "Causal Results (Personal Agendas)"
   - Section 2: "Descriptive Results (Engagement)"
   - Section 3: QA and data quality diagnostics.

## Statistical rules
- Causal tests apply **only** to personal agendas treatment vs control.
- Minimum sample recommendation:
  - Overall: >= 200 per PA arm.
  - Segment-level: >= 100 per arm (otherwise descriptive only).
- Report both absolute lift (pp) and relative lift (%), always with confidence interval.

## KPI source template
Use [docs/phase_d_kpi_template.csv](docs/phase_d_kpi_template.csv) as the master KPI catalog.

## Deliverables
- Cohort master dataset (versioned, timestamped).
- KPI output table (filled template).
- Final post-show report with two-track interpretation.
- Reconciliation appendix (files vs Neo4j counts).

## Runbook checkpoints
- **T-1 (before post-analysis run):** input file presence and schema checks.
- **T0 (after post-analysis ingestion):** relationship counts and identity-link QA.
- **T+1 (after KPI calc):** sign-off thresholds and narrative review.
