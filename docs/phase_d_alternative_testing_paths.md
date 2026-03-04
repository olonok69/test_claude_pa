# Phase D Alternative Testing Paths (Plan A vs Plan B)

## Purpose
Provide two alternative testing/analysis paths for Phase D (post-show), including:
- scope and execution approach,
- pros/cons,
- implementation effort and resource estimates when changes are required.

---

## Executive Summary
- **Plan A (Current event path):** engagement with suppression, no engagement control, personal agendas remains the only causal A/B source.
- **Plan B (Future-ready path):** no suppression, both campaigns in one Neo4j with run-level traceability, and engagement control group enabled.

If the priority is low-risk execution for this event, choose **Plan A**.
If the priority is long-term measurement maturity and auditability, invest in **Plan B**.

---

## Plan A — Suppression-Based, Fast Operational Path

### Definition
- Keep control group only for `personal_agendas`.
- In engagement mode, suppress visitors already mailed in personal agendas using file-based identity matching.
- In Phase D:
  - compute causal lift for personal agendas only,
  - compute descriptive performance for engagement.

### What is already in place
- Engagement control-group behavior disabled in output path.
- File-based engagement suppression logic available in registration flow.
- Phase D KPI template and execution plan for this approach already documented.

### Pros
- Lowest operational risk for current event.
- Minimal pipeline architecture changes.
- Clear causal story for personal agendas.
- Fast to run with current assets (files + post-analysis outputs).

### Cons
- Engagement remains non-causal (no randomized counterfactual).
- Cross-campaign attribution is limited.
- Traceability depends on archived files and joins, not native run lineage in Neo4j.

### Testing path for Phase D
1. Build cohort table from archived files + post-analysis attendance.
2. Validate identity/linkage quality.
3. Run personal agendas causal block (z-test + CI).
4. Run engagement descriptive block.
5. Publish two clearly separated result sections.

### Implementation effort estimate
- **Additional engineering needed now:** low (already largely implemented).
- **Time to stabilize and run with QA:** ~0.5–1.5 days.
- **People:** 1 data engineer/analyst.

---

## Plan B — Full Traceability in Shared Neo4j

### Definition
- No suppression between campaigns.
- Keep both campaign outputs in same Neo4j with run metadata (`run_id`, `run_mode`, `campaign_id`, timestamps, delivery status).
- Implement randomized control for engagement (with dedicated control exports and flags).
- Phase D uses exposure timelines and run-scoped analysis.

### Required changes (if not yet implemented)
1. Add run-level provenance fields to recommendation writes.
2. Preserve recommendation history per run (avoid destructive overwrite without lineage).
3. Add campaign delivery records linked to visitor and run.
4. Add engagement control assignment logic (prefer stratified randomization).
5. Add query layer/report layer filtering by run metadata.
6. Add reconciliation scripts and QA checks by `run_id`.

### Pros
- Best auditability and reproducibility.
- Stronger cross-campaign diagnostics and multi-touch analysis.
- Enables causal lift estimation for engagement as well.
- Less dependence on external file archives for attribution logic.

### Cons
- Higher implementation and migration cost.
- More QA effort to avoid regressions in current pipeline behavior.
- Requires careful control balancing and delivery governance for a second campaign.

### Testing path for Phase D
1. Build run ledger from Neo4j metadata.
2. Build visitor exposure timeline across runs.
3. Join post-analysis attendance outcomes.
4. Compute:
   - personal agendas causal lift,
  - engagement causal lift (plus descriptive KPIs),
   - cross-campaign interaction metrics.
5. Publish with explicit `causal_status` labels.

### Implementation effort estimate
- **MVP traceability + engagement control implementation:** ~5–8 dev days.
- **Production-hardened with migration + QA + docs:** ~2–3 weeks.
- **People:** 1 backend/data engineer + 1 analyst/DS (part-time QA support).

---

## Pros/Cons Comparison Table

| Dimension | Plan A (Suppression) | Plan B (Full Traceability) |
|---|---|---|
| Time to execute this event | Fast | Medium/Slow |
| Change scope | Small | Medium/Large |
| Current risk | Low | Medium |
| Personal agendas causal lift | Yes | Yes |
| Engagement causal lift | No | Yes |
| Engagement descriptive quality | Medium | High |
| Cross-campaign analysis depth | Limited | Strong |
| Auditability/reproducibility | Medium | High |
| Dependency on archived files | High | Low/Medium |

---

## Resource & Timeline Planning

### For this event (recommended baseline)
- Use **Plan A** end-to-end in Phase D.
- Reserve ~1 day for final QA + reporting.

### For next cycle (maturity upgrade)
- Start **Plan B** immediately after event closeout.
- Suggested sequence:
  1. Week 1: run metadata schema + write-path updates.
  2. Week 2: backfill/migration (if needed), QA packs, reporting adaptation.

---

## Decision guidance
- Choose **Plan A** if priority is delivery speed and low change risk.
- Choose **Plan B** if priority is long-term traceability, audit readiness, and causal measurement for both campaigns.
- Practical strategy: run Plan A now, then transition to Plan B after this event.

---

## Related docs
- `docs/phase_d_execution_plan.md`
- `docs/phase_d_execution_plan_full_traceability.md`
- `docs/phase_d_kpi_template.csv`
- `docs/control_group_sizing_methodology.md`
