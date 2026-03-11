# TSL Post-Analysis Execution Plan (Instance 6643cf08) — 2026-03-10

## Purpose
Operational plan to run post-analysis with 20260308 registration/demographic ground-truth data and 20260306 scan files, preserving run lineage and avoiding unintended recommendation regeneration.

## Confirmed decisions and constraints
- CampaignDelivery scope: Option B (all entry-scan visitors matched to existing Visitor_this_year).
- Visitor ground truth: registration/demographic data only (no scan-only visitor node creation).
- Session title policy: strict alignment required (Seminar Title must match Sessions_this_year.title for session_like mismatches).
- Post-analysis run lineage must be isolated in a dedicated RecommendationRun with run_mode=post_analysis.
- Current database already has 3 historical RecommendationRun nodes (2 personal_agendas, 1 engagement).

## Pros and cons: CampaignDelivery scope in post-analysis
### Option A: only seminar-scan visitors
- Pros:
  - Smaller write volume.
  - Tighter direct alignment to session attendance.
- Cons:
  - Excludes venue attendees without seminar scans.
  - Biases funnel denominators.
  - Weakens registered_to_show interpretation.

### Option B: all entry-scan visitors (accepted)
- Pros:
  - Best venue-level audience coverage.
  - Supports full entry-to-session funnel.
  - Consistent denominator across conversion, engagement, and post-analysis.
- Cons:
  - More CampaignDelivery rows.
  - Requires segmentation in downstream reporting.

## Critical gaps found before execution
1. Dedicated post-analysis run is missing on instance 6643cf08.
   - Verified: run_id tsl_post_analysis_20260309T145600Z_0b7f2a1d does not exist there.
   - Impact: create_post_analysis_delivery_from_entry_scans.py fails unless RecommendationRun exists.

2. Current config has create_only_new: false in PA/config/config_tsl.yaml.
   - Risk: if full pipeline (including step 10) is executed, recommendation regeneration can occur.
   - Mitigation: execute scoped steps (2,3,5,8) and skip recommendation steps.

3. Exhibitor scan relationships are not part of the standard post-analysis pipeline step path today.
   - Current post-analysis relationship processor handles assisted_session_this_year, assisted_session_this_year_run, registered_to_show.
   - assisted_exhibitor_this_year and assisted_exhibitor_this_year_run require explicit implementation or one-time script workflow.

## Behavioral clarifications (requested)
### Visitors and recommendations in post-analysis
- Yes, Visitor_this_year is refreshed/loaded from registration + demographics.
- To avoid generating recommendations for newly loaded visitors, do not run steps 9 and 10.
- Recommended run scope: only steps 2,3,5,8 (optionally 11 for export refresh if needed).

### Minimal node defaults for missing visitors from exhibitor scans
- Decision: no visitor creation from scan-only records.
- Only visitors present in 20260308 registration/demographic files are valid for Visitor_this_year creation/update.
- Scan rows unmatched to those visitors remain unresolved and are reported.

### assisted_session_this_year_run proposal (code-aligned)
- Keep projection logic from assisted_session_this_year + CampaignDelivery/FOR_RUN, filtered to post-analysis run_id.
- Maintain strict run isolation so no cross-run contamination with conversion/engagement runs.

### assisted_exhibitor_this_year_run proposal
- Implement analogous projection pattern to assisted_session_this_year_run:
  - Base rel: Visitor_this_year-[assisted_exhibitor_this_year]->Exhibitor
  - Run-scoped rel: Visitor_this_year-[assisted_exhibitor_this_year_run {run_id,...}]->Exhibitor
  - Projection source: assisted_exhibitor_this_year + CampaignDelivery/FOR_RUN filtered by post-analysis run_id.

## Execution todo checklist
- [ ] T0. Confirm environment targets 6643cf08 (keys/.env + resolved Neo4j credentials).
- [ ] T1. Freeze config for post-analysis inputs (20260308 reg/demo + 20260306 scans).
- [ ] T2. Create dedicated RecommendationRun for post-analysis run_id.
- [ ] T3. Run seminar title verification and apply strict alignment policy.
- [ ] T4. Run exhibitor name verification and resolve missing/non-exact exhibitor names.
- [ ] T5. Run Option B CampaignDelivery dry-run, review counts.
- [ ] T6. Run Option B CampaignDelivery apply.
- [ ] T7. Execute pipeline steps 2,3,5,8 only (skip 9,10).
- [ ] T8. Verify post-analysis relationship gates.
- [ ] T9. Archive evidence JSON/logs in PA/large_tool_results and update follow-up docs.

## Suggested command sequence (operator runbook)
Run from repo root, then switch to `PA/` as below.

### 0) Session setup
```bash
cd /mnt/wolverine/home/samtukra/juan/repos/PA
source .venv/bin/activate
cd PA
mkdir -p logs large_tool_results

STAMP=$(date +%Y%m%d_%H%M%S)
RUN_ID=tsl_post_analysis_${STAMP}Z_$(python - <<'PY'
import uuid
print(uuid.uuid4().hex[:8])
PY
)
echo "RUN_ID=${RUN_ID}" | tee logs/post_analysis_run_id_${STAMP}.log
```

### 1) Snapshot before changes (checkpoint A)
```bash
python - <<'PY' 2>&1 | tee logs/00_pre_snapshot_${STAMP}.log
from pathlib import Path
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase
from utils.neo4j_utils import resolve_neo4j_credentials

repo=Path('/mnt/wolverine/home/samtukra/juan/repos/PA')
load_dotenv(repo/'PA'/'keys'/'.env', override=True)
cfg=yaml.safe_load((repo/'PA'/'config'/'config_tsl.yaml').read_text())
creds=resolve_neo4j_credentials(cfg)
show='tsl'
queries={
  'visitor_this_year':'MATCH (n:Visitor_this_year {show:$show}) RETURN count(n) AS c',
  'sessions_this_year':'MATCH (n:Sessions_this_year {show:$show}) RETURN count(n) AS c',
  'reco_runs':'MATCH (n:RecommendationRun {show:$show}) RETURN count(n) AS c',
  'post_runs':'MATCH (n:RecommendationRun {show:$show,run_mode:"post_analysis"}) RETURN count(n) AS c',
  'reg_to_show':'MATCH (:Visitor_this_year {show:$show})-[r:registered_to_show]->(:Show_this_year {show:$show}) RETURN count(r) AS c',
  'assist_session':'MATCH (:Visitor_this_year {show:$show})-[r:assisted_session_this_year]->(:Sessions_this_year {show:$show}) RETURN count(r) AS c'
}
print('uri=',creds['uri'])
with GraphDatabase.driver(creds['uri'], auth=(creds['username'],creds['password'])) as d:
  with d.session() as s:
    for k,q in queries.items():
      print(k,'=',s.run(q,show=show).single()['c'])
PY
```

Expected at this stage:
- `post_runs = 0`, `reg_to_show = 0`, `assist_session = 0` on a clean pre-post-analysis state.
- Neo4j warnings like `UnknownRelationshipTypeWarning` / `UnknownLabelWarning` for `registered_to_show`, `assisted_session_this_year`, or `Show_this_year` are normal before step 9 creates those structures.

### 2) Identity precheck (fast, no pipeline)
```bash
python scripts/run_post_analysis_identity_validation.py --config config/config_tsl.yaml --skip-pipeline 2>&1 | tee logs/01_identity_precheck_${STAMP}.log
```

Note:
- Do not use `--require-post-event-data` at this early point because post-analysis relationships are intentionally still zero.
- The strict gate is executed after step 10.

### 3) Create dedicated post-analysis RecommendationRun
```bash
python - <<'PY' 2>&1 | tee logs/02_create_post_run_${STAMP}.log
from pathlib import Path
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase
from utils.neo4j_utils import resolve_neo4j_credentials
import os

repo=Path('/mnt/wolverine/home/samtukra/juan/repos/PA')
load_dotenv(repo/'PA'/'keys'/'.env', override=True)
cfg=yaml.safe_load((repo/'PA'/'config'/'config_tsl.yaml').read_text())
creds=resolve_neo4j_credentials(cfg)
run_id=os.environ['RUN_ID']

q='''
MERGE (rr:RecommendationRun {run_id:$run_id})
SET rr.show='tsl', rr.run_mode='post_analysis', rr.campaign_id='tsl_post_analysis',
  rr.pipeline_version='pa_pipeline', rr.allocation_version='full',
  rr.created_at=coalesce(rr.created_at, datetime()), rr.updated_at=datetime()
RETURN rr.run_id as run_id, rr.run_mode as run_mode, rr.show as show
'''
with GraphDatabase.driver(creds['uri'], auth=(creds['username'],creds['password'])) as d:
  with d.session() as s:
    print(s.run(q,run_id=run_id).single().data())
print('RUN_ID=',run_id)
PY
```

### 4) Session title verification
```bash
python scripts/verify_seminar_scan_titles_vs_sessions.py --config config/config_tsl.yaml --csv-path data/tsl/post/20260306_tsl26_seminar_scans.csv 2>&1 | tee logs/03_verify_session_titles_${STAMP}.log
```

### 5) Exhibitor name verification
```bash
python scripts/verify_exhibitor_scan_names_vs_neo4j.py --config config/config_tsl.yaml --csv-path data/tsl/post/20260306_tsl26_exhibitor_scans.csv 2>&1 | tee logs/04_verify_exhibitors_${STAMP}.log
```

### 6) Option B CampaignDelivery dry-run
```bash
python scripts/create_post_analysis_delivery_from_entry_scans.py --config config/config_tsl.yaml --run-id "${RUN_ID}" --env-file keys/.env --batch-size 500 --report-file large_tool_results/post_analysis_delivery_option_b_dry_run_${STAMP}.json --log-every-records 5000 --log-every-batches 2 2>&1 | tee logs/05_delivery_dry_run_${STAMP}.log
```

### 7) Option B CampaignDelivery apply
```bash
python scripts/create_post_analysis_delivery_from_entry_scans.py --config config/config_tsl.yaml --run-id "${RUN_ID}" --env-file keys/.env --batch-size 500 --report-file large_tool_results/post_analysis_delivery_option_b_apply_${STAMP}.json --apply --log-every-records 5000 --log-every-batches 2 2>&1 | tee logs/06_delivery_apply_${STAMP}.log
```

### 8) Verify delivery (checkpoint B)
```bash
python - <<'PY' 2>&1 | tee logs/07_verify_delivery_${STAMP}.log
from pathlib import Path
import yaml, os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from utils.neo4j_utils import resolve_neo4j_credentials

repo=Path('/mnt/wolverine/home/samtukra/juan/repos/PA')
load_dotenv(repo/'PA'/'keys'/'.env', override=True)
cfg=yaml.safe_load((repo/'PA'/'config'/'config_tsl.yaml').read_text())
creds=resolve_neo4j_credentials(cfg)
run_id=os.environ['RUN_ID']

with GraphDatabase.driver(creds['uri'], auth=(creds['username'],creds['password'])) as d:
  with d.session() as s:
    c=s.run('MATCH (d:CampaignDelivery {run_id:$run_id}) RETURN count(d) AS c', run_id=run_id).single()['c']
    print('run_id=',run_id)
    print('campaign_delivery_count=',c)
PY
```

### 9) Post-analysis pipeline only (no recommendation regeneration)
```bash
python main.py --config config/config_tsl.yaml --only-steps 2,3,5,8 --skip-mlflow 2>&1 | tee large_tool_results/post_analysis_pipeline_${STAMP}.log
```

### 10) Final relationship verification (checkpoint C)
```bash
python - <<'PY' 2>&1 | tee logs/09_post_analysis_verify_${STAMP}.log
from pathlib import Path
import yaml, os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from utils.neo4j_utils import resolve_neo4j_credentials

repo=Path('/mnt/wolverine/home/samtukra/juan/repos/PA')
load_dotenv(repo/'PA'/'keys'/'.env', override=True)
cfg=yaml.safe_load((repo/'PA'/'config'/'config_tsl.yaml').read_text())
creds=resolve_neo4j_credentials(cfg)
show='tsl'
run_id=os.environ['RUN_ID']
queries={
  'registered_to_show':'MATCH (:Visitor_this_year {show:$show})-[r:registered_to_show]->(:Show_this_year {show:$show}) RETURN count(r) AS c',
  'assisted_session_this_year':'MATCH (:Visitor_this_year {show:$show})-[r:assisted_session_this_year]->(:Sessions_this_year {show:$show}) RETURN count(r) AS c',
  'assisted_session_this_year_run':'MATCH ()-[r:assisted_session_this_year_run {run_id:$run_id}]->() RETURN count(r) AS c',
  'post_run':'MATCH (r:RecommendationRun {run_id:$run_id}) RETURN count(r) AS c',
  'delivery_for_run':'MATCH (d:CampaignDelivery {run_id:$run_id}) RETURN count(d) AS c'
}
with GraphDatabase.driver(creds['uri'], auth=(creds['username'],creds['password'])) as d:
  with d.session() as s:
    for k,q in queries.items():
      print(k,'=',s.run(q,show=show,run_id=run_id).single()['c'])
PY
```

### 10b) Final strict gate (must pass)
```bash
python scripts/run_post_analysis_identity_validation.py --config config/config_tsl.yaml --skip-pipeline --require-post-event-data 2>&1 | tee logs/10b_identity_strict_gate_${STAMP}.log
```

### 10c) Rebuild assisted_session_this_year from seminar scans (identity-key flow)

Purpose:
- Use `PA/data/tsl/post/20260306_tsl26_seminar_scans.csv` to rebuild `assisted_session_this_year` for post-analysis run lineage.
- Visitor matching key is strict identity pattern:
  - node side: `forename_surname_email`
  - file side: `First Name_Last Name_Email`
- Session reconciliation policy for `session_like` titles:
  - exact title match first,
  - normalized/unicode-repaired comparison,
  - high-similarity fallback,
  - create new `Sessions_this_year` only when still unresolved.

Dry-run:
```bash
python scripts/rebuild_assisted_sessions_from_seminar_scans.py \
  --config config/config_tsl.yaml \
  --seminar-scan-csv data/tsl/post/20260306_tsl26_seminar_scans.csv \
  --post-run-id tsl_post_analysis_20260310_151951Z_ccfa80c9 \
  --show-ref TSL26 \
  --dry-run \
  2>&1 | tee logs/10c_assisted_session_dry_run_${STAMP}.log
```

Apply:
```bash
python scripts/rebuild_assisted_sessions_from_seminar_scans.py \
  --config config/config_tsl.yaml \
  --seminar-scan-csv data/tsl/post/20260306_tsl26_seminar_scans.csv \
  --post-run-id tsl_post_analysis_20260310_151951Z_ccfa80c9 \
  --show-ref TSL26 \
  --report-file large_tool_results/assisted_session_rebuild_apply_latest.json \
  2>&1 | tee logs/10c_assisted_session_apply_${STAMP}.log
```

Executed outcome (2026-03-11):
- Evidence:
  - `large_tool_results/assisted_session_rebuild_20260311_142751.json` (dry-run)
  - `large_tool_results/assisted_session_rebuild_apply_latest.json` (apply)
  - `logs/rebuild_assisted_session_20260311_apply.log` (apply log capture)
- Dry-run summary:
  - `scan_rows_total=30618`
  - `skipped_non_session_like=4496`
  - `matched_visitor_rows=23477`
  - `unmatched_visitor_rows=2645`
  - `unique_session_like_titles=273`
  - `title_status_counts={exact:243, normalized:30}`
- Apply summary:
  - `title_status_counts={exact:273}` after reconciliation
  - `deleted_existing_run_relationships=15000`
  - `recreated_assisted_relationships_touched=22868`
  - `assisted_session_this_year_for_run=22868`
  - `match_mode_breakdown=[identity:22868]`

Validation note:
- Relationship writes are scoped to `run_id=tsl_post_analysis_20260310_151951Z_ccfa80c9`.
- Session node updates only modify title metadata; existing run provenance is not reassigned.

### 10d) Rebuild assisted_exhibitor_this_year from exhibitor scans (identity-key flow)

Purpose:
- Use `PA/data/tsl/post/20260306_tsl26_exhibitor_scans.csv` to rebuild `assisted_exhibitor_this_year` for post-analysis run lineage.
- Visitor matching key is strict identity pattern:
  - node side: `forename_surname_email`
  - file side: `First Name_Last Name_Email`
- Exhibitor reconciliation policy follows verification approach and strict similarity guard:
  - exact (case-insensitive) match first,
  - normalized/unicode-repaired comparison (`â€‘` and related mojibake cleanup),
  - strict similarity fallback (`SequenceMatcher` + token overlap) only when practically the same,
  - otherwise treat as `missing_in_neo4j` and create new `Exhibitor` with file-exact `Exhibitor Name`.

Dry-run:
```bash
python scripts/rebuild_assisted_exhibitors_from_exhibitor_scans.py \
  --config config/config_tsl.yaml \
  --exhibitor-scan-csv data/tsl/post/20260306_tsl26_exhibitor_scans.csv \
  --post-run-id tsl_post_analysis_20260310_151951Z_ccfa80c9 \
  --show-ref TSL26 \
  --dry-run \
  2>&1 | tee logs/10d_assisted_exhibitor_dry_run_${STAMP}.log
```

Apply:
```bash
python scripts/rebuild_assisted_exhibitors_from_exhibitor_scans.py \
  --config config/config_tsl.yaml \
  --exhibitor-scan-csv data/tsl/post/20260306_tsl26_exhibitor_scans.csv \
  --post-run-id tsl_post_analysis_20260310_151951Z_ccfa80c9 \
  --show-ref TSL26 \
  --report-file large_tool_results/assisted_exhibitor_rebuild_apply_latest.json \
  2>&1 | tee logs/10d_assisted_exhibitor_apply_${STAMP}.log
```

Executed outcome (2026-03-11):
- Script:
  - `PA/scripts/rebuild_assisted_exhibitors_from_exhibitor_scans.py`
- Evidence:
  - `large_tool_results/assisted_exhibitor_rebuild_20260311_160545.json` (dry-run)
  - `large_tool_results/assisted_exhibitor_rebuild_apply_latest.json` (apply)
  - `logs/rebuild_assisted_exhibitor_dry_run_20260311T160538Z.log` (dry-run log)
  - `logs/rebuild_assisted_exhibitor_apply_20260311T160631Z.log` (apply log)
- Dry-run summary:
  - `scan_rows_total=60929`
  - `matched_visitor_rows=51718`
  - `unmatched_visitor_rows=9211`
  - `unique_file_exhibitor_names=450`
  - `name_status_counts={exact_case_insensitive:450}`
  - `relationship_rows_candidate=48702`
- Apply summary:
  - `renamed_existing_exhibitors=0`
  - `created_missing_exhibitors=0`
  - `recreated_assisted_exhibitor_relationships_touched=50451`
  - `assisted_exhibitor_this_year_for_run=50448`
  - `match_mode_breakdown=[identity:50448]`

Validation note:
- Relationship writes are scoped to `run_id=tsl_post_analysis_20260310_151951Z_ccfa80c9`.
- Run-scoped metadata integrity check passed:
  - `non_identity_for_run=0`
  - `non_post_mode_for_run=0`
- Name policy requirement satisfied on this execution snapshot:
  - all 450 file exhibitor names resolved as `exact_case_insensitive`, so no risky similarity rename was applied.
- Provenance rule respected:
  - no exhibitor rename/create was needed; therefore no existing `created_in_run` provenance was reassigned.

### 11) Optional output refresh only if needed immediately
```bash
python main.py --config config/config_tsl.yaml --only-steps 11 --skip-mlflow 2>&1 | tee logs/10_output_refresh_${STAMP}.log
```

## Resume from checkpoint (A/B/C)

Use this section to restart safely without repeating successful steps.

### If failure happens before checkpoint A
- Restart from section `0) Session setup`.
- Recreate `STAMP` and `RUN_ID` and continue normally.

### If failure happens after checkpoint A but before checkpoint B
- Reuse the same `RUN_ID` from `logs/post_analysis_run_id_<STAMP>.log`.
- Re-run from section `2) Identity strict gate` onward.
- Mandatory pre-apply check before continuing:
  - confirm `logs/05_delivery_dry_run_<STAMP>.log` looks correct,
  - then run section `7) Option B CampaignDelivery apply`.

### If failure happens after checkpoint B but before checkpoint C
- Reuse same `RUN_ID`.
- Do **not** rerun delivery apply unless `logs/07_verify_delivery_<STAMP>.log` shows `campaign_delivery_count=0`.
- Resume from section `9) Post-analysis pipeline only`.

### If pipeline finishes but checkpoint C fails
- Keep artifacts and do not run new write commands immediately.
- First inspect:
  - `large_tool_results/post_analysis_pipeline_<STAMP>.log`
  - `logs/09_post_analysis_verify_<STAMP>.log`
  - `logs/07_verify_delivery_<STAMP>.log`
- Then run targeted repairs only (avoid full rerun) based on failing counter.

### Fast continuity checklist on resume
- Export and reuse original run id:
```bash
export RUN_ID=<copied_from_logs/post_analysis_run_id_*.log>
```
- Ensure same environment target:
```bash
grep -E '^NEO4J_URI_PROD=|^AURA_INSTANCEID=' keys/.env
```
- Confirm run node still exists:
```bash
python - <<'PY'
from pathlib import Path
import yaml, os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from utils.neo4j_utils import resolve_neo4j_credentials
repo=Path('/mnt/wolverine/home/samtukra/juan/repos/PA')
load_dotenv(repo/'PA'/'keys'/'.env', override=True)
cfg=yaml.safe_load((repo/'PA'/'config'/'config_tsl.yaml').read_text())
creds=resolve_neo4j_credentials(cfg)
run_id=os.environ['RUN_ID']
with GraphDatabase.driver(creds['uri'], auth=(creds['username'],creds['password'])) as d:
    with d.session() as s:
        c=s.run('MATCH (r:RecommendationRun {run_id:$run_id}) RETURN count(r) AS c', run_id=run_id).single()['c']
        print('run_exists=', c)
PY
```

## Verification gates (must pass)
- RecommendationRun exists for post-analysis run_id.
- CampaignDelivery count for that run_id > 0.
- MATCH (d:CampaignDelivery {run_id:'<POST_ANALYSIS_RUN_ID>'}) RETURN count(d);
- registered_to_show > 0.
- assisted_session_this_year > 0.
- assisted_session_this_year_run > 0 and run-scoped to post-analysis run.
- No cross-run contamination in run-scoped relationship metadata.

## What not to run in this cycle
- Do not run steps 9 and 10 unless you intentionally want new embeddings/recommendations.
- Do not create Visitor_this_year from scan-only identities.

## Documentation update after run
- Update docs/post_event_followup_pack/post_analysis_lineage_plan_2026-03-09.md with actual run_id and evidence links.
- Update docs/post_event_followup_pack/FOLLOWUP_CHANGELOG.md with final applied commands and counters.
