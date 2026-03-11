# Post-Analysis Run Lineage Plan (TSL) — 2026-03-09

## Scope and confirmed decisions

This plan covers post-analysis processing using:
- `PA/data/tsl/20260308_postshow_tsl26_registration_legacy.json`
- `PA/data/tsl/20260308_postshow_tsl26_demographics_legacy.json`
- `PA/data/tsl/20260308_postshow_tsl25_26_registration_legacy.json`
- `PA/data/tsl/20260308_postshow_tsl25_26_demographics_legacy.json`
- `PA/data/tsl/20260308_postshow_tsl24_registration_legacy.json`
- `PA/data/tsl/20260308_postshow_tsl24_demographics_legacy.json`

And post-show scans:
- `PA/data/tsl/post/20260306_tsl26_entry_scans.csv`
- `PA/data/tsl/post/20260306_tsl26_seminar_scans.csv`
- `PA/data/tsl/post/20260306_tsl26_exhibitor_scans.csv`

Confirmed by stakeholder:
1. **Visitor ground truth** is registration/demographics (20260308 legacy outputs).  
   Visitors only in scan files are **not uploaded as new Visitor nodes**.
2. Session titles in scan CSV and Neo4j must be **identical**.
3. Identity key for scan matching uses lowercased concat:
   - `forename + "_" + surname + "_" + email`

---

## Decision review: CampaignDelivery scope for post-analysis run

Question: for the post-analysis `RecommendationRun`, should `CampaignDelivery` be created for only seminar-scan visitors or all entry-scan visitors?

### Option A — Only visitors with seminar scans

Pros:
- Tighter lineage for attended-session analytics (`assisted_session_this_year_run` scope aligns to session attendees).
- Fewer delivery rows; lower write volume and less graph noise.
- Easier to explain when KPI is session attendance fidelity.

Cons:
- Excludes valid on-site visitors who entered but did not scan sessions.
- Weak for funnel analysis (entry -> session conversion denominators become biased).
- `registered_to_show` run-scoped interpretation is incomplete for post-analysis audience.

### Option B — All entry-scan visitors (**recommended**)

Pros:
- Best reflects observed post-show audience at venue level.
- Supports full funnel analytics: entry attendance + session attendance.
- Consistent denominator for cross-run comparison (conversion/engagement/post-analysis).
- Allows `registered_to_show` and `assisted_session_this_year` to coexist under one run scope cleanly.

Cons:
- More `CampaignDelivery` rows.
- Includes visitors with no seminar scans, which may require explicit metric segmentation.

### Recommendation

Use **Option B (all entry-scan visitors)** for the post-analysis run lineage.  
This preserves full audience coverage and avoids undercounting in attendance funnel reporting.

### Decision status (2026-03-09)

- Stakeholder confirmed: **Option B accepted**.
- Implementation target: populate post-analysis `CampaignDelivery` from all matched entry-scan visitors via `PA/scripts/create_post_analysis_delivery_from_entry_scans.py`.

---

## Target behavior by relationship

## `registered_to_show`
- Source: `20260306_tsl26_entry_scans.csv`
- Visitor match key: identity concat from file (`First Name`, `Last Name`, `Email`) -> `id_both_years`
- Visitor population: existing `Visitor_this_year` only (from 20260308 reg/demo outputs)
- Run scope: link to post-analysis run lineage model

## `assisted_session_this_year`
- Source: `20260306_tsl26_seminar_scans.csv`
- Session match key: `Seminar Title` mapped to `Sessions_this_year.title` (exact)
- Visitor match key: identity concat from file (`First Name`, `Last Name`, `Email`) -> `id_both_years`
- Run scope projection via `assisted_session_this_year_run`

## `assisted_session_this_year_run`
- Source of truth: projection from `assisted_session_this_year` + `CampaignDelivery/FOR_RUN`
- Scope: **post-analysis RecommendationRun only** (do not mix with prior conversion/engagement runs)

## `assisted_exhibitor_this_year` (new)
- Source: `20260306_tsl26_exhibitor_scans.csv`
- Visitor match key: identity concat from file (`First Name`, `Last Name`, `Email`) -> `id_both_years`
- Exhibitor match key: `Exhibitor Name` == `Exhibitor.name` (exact after alignment)

## `assisted_exhibitor_this_year_run` (new)
- Run-scoped projection analogous to session run projection.
- Scope: post-analysis run only.

---

## Session title policy (confirmed)

Policy: titles in seminar scan CSV and Neo4j must be identical.

Execution rule:
- For `session_like` non-exact mismatches from `verify_seminar_scan_titles_vs_sessions.py`:
  1. If Neo4j session exists but title variant differs -> overwrite title to exact CSV `Seminar Title` canonical value.
  2. If Neo4j session missing -> create new `Sessions_this_year` node with that exact title.
- Keep non-session categories (`vip_lounge_duration`, `networking`) out of forced session-title overwrite unless explicitly reclassified.

---

## Implementation phases

### Phase 1 — Config freeze for post-analysis
1. Set `mode: post_analysis` in TSL config snapshot for run.
2. Point post-analysis scan paths to 20260306 files.
3. Ensure input registration/demographic paths use 20260308 legacy outputs.
4. Keep `create_only_new: true` (safe default) for node creation behavior.

### Phase 2 — Identity baseline
1. Ensure `id_both_years` exists on all relevant `Visitor_this_year` nodes from reg/demo source.
2. Backfill `id_both_years` for existing nodes where null and data exists.

### Phase 3 — Session title alignment
1. Run seminar title verifier and capture JSON/CSV report.
2. Apply strict title alignment for `session_like` mismatches.
3. Create missing `Sessions_this_year` for blank Neo4j matches.
4. Re-run verifier until `session_like` non-exact mismatches are cleared (or explicitly waived with documented rationale).

### Phase 4 — Exhibitor alignment
1. Run exhibitor verifier and capture JSON/CSV report.
2. Create missing exhibitors (`csv_only`) and normalize near-matches to exact names.
3. Re-run exhibitor verifier for residual gap review.

### Phase 5 — Post-analysis run lineage
1. Create a dedicated `RecommendationRun` for `post_analysis` mode.
2. Create `CampaignDelivery` + `FOR_VISITOR` for **all entry-scan visitors** matched to existing Visitor nodes.
3. Link `CampaignDelivery` to post-analysis run via `FOR_RUN`.

### Phase 6 — Relationship build
1. Build `registered_to_show` from entry scans using identity-first matching.
2. Build `assisted_session_this_year` from seminar scans using identity-first matching.
3. Project `assisted_session_this_year_run` for post-analysis run.
4. Build `assisted_exhibitor_this_year` (new) and `assisted_exhibitor_this_year_run` (new).

### Phase 7 — Verification gates
1. Counts and coverage:
   - `registered_to_show` > 0
   - `assisted_session_this_year` > 0
   - run-scoped counterparts > 0 for post-analysis run
2. Integrity checks:
   - all run-scoped attendance/exhibitor relationships reference the post-analysis run_id
   - no cross-run contamination
3. Export evidence to `large_tool_results/` and archive in follow-up pack.

---

## Risks and controls

- Risk: identity collisions (`forename_surname_email`) across people sharing name/email artifacts.  
  Control: keep raw scan provenance properties and compare against barcode where available.

- Risk: strict title overwrite may affect historical references.  
  Control: restrict overwrite to current-year session nodes and preserve an audit export before changes.

- Risk: run-scope contamination with existing conversion/engagement runs.  
  Control: enforce run-id filters in projection queries and add verifier checks.

---

## Definition of done

1. Post-analysis run created and isolated.
2. Entry attendance and seminar attendance linked via identity-first matching.
3. Exhibitor attendance relationships created (base + run-scoped).
4. Session and exhibitor naming aligned to exact CSV canonical values where required.
5. Verification reports generated (JSON + CSV) and archived in follow-up pack.
