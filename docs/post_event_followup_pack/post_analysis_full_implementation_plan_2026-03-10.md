# TSL Post-Analysis Full Implementation Plan — 2026-03-10

## Goal
Implement and run `post_analysis` mode so it fully matches the agreed behavior for:
- visitor refresh from new 20260308 registration/demographic ground truth,
- entry/seminar/exhibitor scan linkage,
- strict title/name alignment for session/exhibitor entities,
- run-scoped lineage under a dedicated post-analysis `RecommendationRun`.

---

## Confirmed data inputs

### Ground-truth registration/demographic inputs (authoritative for Visitor creation)
- `PA/data/tsl/20260308_postshow_tsl26_registration_legacy.json`
- `PA/data/tsl/20260308_postshow_tsl26_demographics_legacy.json`
- `PA/data/tsl/20260308_postshow_tsl25_26_registration_legacy.json`
- `PA/data/tsl/20260308_postshow_tsl25_26_demographics_legacy.json`
- `PA/data/tsl/20260308_postshow_tsl24_registration_legacy.json`
- `PA/data/tsl/20260308_postshow_tsl24_demographics_legacy.json`

### Post-show scan inputs
- Entry scans: `PA/data/tsl/post/20260306_tsl26_entry_scans.csv`
- Seminar scans: `PA/data/tsl/post/20260306_tsl26_seminar_scans.csv`
- Exhibitor scans: `PA/data/tsl/post/20260306_tsl26_exhibitor_scans.csv`

---

## Resolved requirement clarifications

1. **CampaignDelivery scope for post-analysis run**
   - Decision: **Option B (all entry-scan visitors matched to existing Visitor_this_year)**.
   - Rationale: preserves venue-level denominator and full funnel (entry -> session/exhibitor).

2. **Missing visitors from exhibitor/session scans**
   - Decision: **Do not create visitors from scan-only records**.
   - Ground truth remains registration+demographic inputs only.

3. **Session title alignment policy**
   - Decision: **Strict identity required**.
   - `Seminar Title` in scan CSV must be identical to `Sessions_this_year.title` for `session_like` rows.

4. **Conflict found and resolved**
   - One instruction said "create any Visitor appearing in exhibitor scan file that we don't have".
   - Later instruction says scan-only visitors are not uploaded; reg/demo is ground truth.
   - This plan uses the latter as authoritative policy.

---

## Pros and cons: CampaignDelivery scope

### Option A: seminar-scan visitors only
**Pros**
- Lower write volume and faster apply.
- Attendance lineage tightly focused on seminar behavior.

**Cons**
- Excludes attendees who entered but did not scan seminars.
- Biases conversion/engagement denominator.
- Weakens `registered_to_show` audience interpretation.

### Option B: all entry-scan visitors (accepted)
**Pros**
- Best venue-level population coverage.
- Supports consistent funnel analytics across conversion, engagement, post-analysis.
- Keeps post-analysis denominator aligned with observed attendance.

**Cons**
- More `CampaignDelivery` rows.
- Requires segmentation in downstream reporting.

---

## Current pipeline gap analysis (post_analysis mode)

### Already implemented
- Step 8 executes post-analysis relationship logic (`assisted_session_this_year`, `assisted_session_this_year_run`, `registered_to_show`).
- Identity fallback using lowercase `forename_surname_email` is implemented in visitor relationship processing.
- Run-scoped projection for `assisted_session_this_year_run` exists via `CampaignDelivery` + `FOR_RUN`.

### Missing / incomplete vs requested behavior
1. `verify_seminar_scan_titles_vs_sessions.py` is validation only; it does not create/update sessions.
2. No implemented writer to auto-create missing `Sessions_this_year` from seminar reconciliation (`title_neo4j` blank) in post-analysis flow.
3. No strict write enforcement to overwrite non-exact `session_like` titles to exact CSV canonical title.
4. No `assisted_exhibitor_this_year` and no `assisted_exhibitor_this_year_run` in pipeline processors.
5. `assisted_session_this_year_run` projection should be explicitly filtered to post-analysis run scope (`run_mode='post_analysis'` and/or selected run_id) to avoid ambiguity with existing 3 runs.
6. New visitor identity attribute for all `Visitor_this_year` (new + existing) is not explicitly backfilled as a dedicated field in Neo4j.

---

## Implementation design decisions

### Identity key strategy
- Keep `id_both_years` as canonical identity source.
- Add a dedicated explicit attribute on `Visitor_this_year`:
  - `identity_key = lower(Forename) + '_' + lower(Surname) + '_' + lower(Email)`
- Backfill for existing nodes when components are present.
- Populate for newly loaded/updated visitors in post-analysis run.

### registered_to_show matching
- Use identity-first matching from entry scans (`First Name`, `Last Name`, `Email`) -> `identity_key`/`id_both_years`.
- Badge fallback only when available.
- Apply to any `Visitor_this_year` regardless of prior campaign membership.

### Session reconciliation behavior
- Use reconciliation output from `verify_seminar_scan_titles_vs_sessions.py`.
- For `session_like`:
  - `status=missing` (`title_neo4j` blank): create `Sessions_this_year` with exact `Seminar Title`.
  - `status=normalized` or near-match but not exact: overwrite canonical `Sessions_this_year.title` to exact CSV value.
- Non-session categories (`vip_lounge_duration`, `networking`) remain excluded unless explicitly reclassified.

### Exhibitor reconciliation behavior
- Use `verify_exhibitor_scan_names_vs_neo4j.py` report.
- For `status in {missing_in_neo4j, no_exact}` and `category=csv_only`: create/align `Exhibitor` nodes to exact CSV `Exhibitor Name`.
- Do not create visitors from exhibitor scan-only identities.

### Run-scoped attendance/exhibitor relationships
- `assisted_session_this_year_run` and new `assisted_exhibitor_this_year_run` must be projected from base rel + `CampaignDelivery/FOR_RUN` filtered to post-analysis run.
- Required properties: `run_id`, `run_mode`, `campaign_id`, `show`, provenance fields, `updated_at`.

---

## `create_only_new` behavior and impact

- `create_only_new=true`
  - Safer for avoiding broad rewrites.
  - Good for adding missing nodes/relationships incrementally.
  - Needs explicit update paths where strict overwrite is required (session/exhibitor title normalization).

- `create_only_new=false`
  - Can update existing records broadly and may trigger unintended side effects.
  - Higher risk in post-analysis when recommendation paths (steps 9/10) are not fully isolated.

**Plan decision**
- Keep post-analysis run commands scoped to `--only-steps 2,3,5,8`.
- Execute explicit reconciliation writers for strict title/name alignment.
- Do not run steps 9/10.

---

## Complete TODO list (implementation + verify + run)

- [ ] T0. Freeze config and confirm `AURA_INSTANCEID` target, input file paths, and post-analysis mode in `PA/config/config_tsl.yaml`.
- [ ] T1. Add/confirm visitor `identity_key` generation and backfill for `Visitor_this_year` (new + existing).
- [ ] T2. Ensure `registered_to_show` matching prioritizes lowercase identity concat from entry scans.
- [ ] T3. Implement session reconciliation writer (create missing + strict exact title overwrite for `session_like`).
- [ ] T4. Implement exhibitor reconciliation writer (create missing + strict exact name alignment).
- [ ] T5. Implement `assisted_exhibitor_this_year` base relationship build from exhibitor scans via identity matching.
- [ ] T6. Implement `assisted_exhibitor_this_year_run` projection linked to post-analysis run lineage.
- [ ] T7. Tighten `assisted_session_this_year_run` projection filter to post-analysis run scope.
- [ ] T8. Update `config_tsl.yaml` keys/paths if needed for new reconciliation and exhibitor relationship steps.
- [ ] T9. Add post-analysis verification scripts/queries for session/exhibitor exact-match gates and run-scope integrity.
- [ ] T10. Execute dry-run sequence (verification-only + report artifacts).
- [ ] T11. Execute apply sequence (writers + pipeline steps 2,3,5,8).
- [ ] T12. Run final strict gate checks and archive evidence artifacts.
- [ ] T13. Update follow-up docs (`FOLLOWUP_CHANGELOG.md`, lineage/runbook docs) with run_id, counters, and evidence paths.

---

## Execution plan by phase

### Phase A — Code/config implementation
1. Implement missing writers and exhibitor relationship processors.
2. Add/adjust config blocks for post-analysis session/exhibitor reconciliation.
3. Validate imports/lint for changed modules.

### Phase B — Preflight and checkpoints
1. Confirm run context and export `RUN_ID`, `STAMP`.
2. Snapshot pre-state counters (visitors/sessions/exhibitors/relationships/runs).
3. Verify reconciliation scripts produce deterministic reports.

### Phase C — Reconciliation apply
1. Session reconciliation apply (strict exact alignment for `session_like`).
2. Exhibitor reconciliation apply (strict exact exhibitor names).
3. Confirm no unresolved strict-gap rows remain for required categories.

### Phase D — Lineage + relationship build
1. Ensure dedicated post-analysis `RecommendationRun` exists.
2. Option B delivery apply from entry scans.
3. Run pipeline steps `2,3,5,8`.
4. Build and verify run-scoped session/exhibitor attendance relationships.

### Phase E — Final verification gates
1. Gate 1: `CampaignDelivery` count for post-analysis run_id > 0.
2. Gate 2: `registered_to_show` > 0 via identity matching.
3. Gate 3: `assisted_session_this_year` and `assisted_session_this_year_run` > 0.
4. Gate 4: `assisted_exhibitor_this_year` and `assisted_exhibitor_this_year_run` > 0.
5. Gate 5: strict title/name identity checks pass for required categories.
6. Gate 6: no cross-run contamination for run-scoped relationships.

---

## Verification checklist (must pass)

- [ ] `RecommendationRun(run_mode='post_analysis')` exists for active `RUN_ID`.
- [ ] `CampaignDelivery` nodes exist and are linked by `FOR_RUN` and `FOR_VISITOR`.
- [ ] `registered_to_show` created using identity concat from entry scans.
- [ ] Session strict alignment passes for `session_like` (exact title identity).
- [ ] Exhibitor strict alignment passes for requested statuses/categories.
- [ ] `assisted_session_this_year_run.run_id == RUN_ID` for projected relationships.
- [ ] `assisted_exhibitor_this_year_run.run_id == RUN_ID` for projected relationships.
- [ ] No new visitors created from scan-only identities.

---

## Risk notes

1. Strict title overwrite can affect downstream references.
   - Mitigation: store pre/post reconciliation reports and changed-node audit list.

2. Identity collisions on forename/surname/email are possible.
   - Mitigation: keep provenance (`file`, `scan_date`, match mode) on relationships and audit ambiguous identities.

3. Multi-run graph already contains conversion + engagement + post-analysis runs.
   - Mitigation: enforce run_id and run_mode filters in all run-scoped projections.

---

## Expected outcome

After implementation and run, post-analysis mode will:
- honor registration/demographic ground truth for visitors,
- enforce strict session/exhibitor name identity from scan sources where required,
- create base and run-scoped attendance relationships (session + exhibitor),
- preserve clean lineage in a dedicated post-analysis run without recommendation regeneration.

---

## Plan extension: Step-4 visitor refresh and run linkage tracking

Use this extension when step 1 is already complete and you want to refresh/create missing `Visitor_this_year` from 20260308 legacy registration/demographic outputs without generating recommendations.

### Fixed run context
- `RUN_ID=tsl_post_analysis_20260310_151951Z_ccfa80c9`
- Scope: post-analysis, step 4 only, then explicit run-linking for newly created visitors.

### Tracking checklist
- [ ] E1. Export `RUN_ID` and `STAMP`.
- [ ] E2. Capture pre-step4 missing identity snapshot from legacy reg file vs Neo4j.
- [ ] E3. Run `main.py --only-steps 4 --skip-mlflow`.
- [ ] E4. Link newly created visitors to post-analysis run (`CampaignDelivery` + `FOR_VISITOR` + `FOR_RUN`).
- [ ] E5. Verify coverage + linkage + no recommendations created for this run.
- [ ] E6. Archive logs and json artifacts.

### Commands (copy/paste)

```bash
cd /mnt/wolverine/home/samtukra/juan/repos/PA/PA
export RUN_ID=tsl_post_analysis_20260310_151951Z_ccfa80c9
export STAMP=$(date +%Y%m%d_%H%M%S)
```

```bash
/mnt/wolverine/home/samtukra/juan/repos/PA/.venv/bin/python - <<'PY' 2>&1 | tee logs/20_pre_step4_missing_visitors_${STAMP}.log
import json
from pathlib import Path
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase
from utils.neo4j_utils import resolve_neo4j_credentials

pa=Path('/mnt/wolverine/home/samtukra/juan/repos/PA/PA')
cfg=yaml.safe_load((pa/'config'/'config_tsl.yaml').read_text())
load_dotenv(pa/'keys'/'.env', override=True)
creds=resolve_neo4j_credentials(cfg)

reg_path=pa/'data'/'tsl'/'20260308_postshow_tsl25_26_registration_legacy.json'
shows={'DCWL26','DAILS26','CAIL26','CCSEL26','DOLL26'}

def n(v):
   if v is None: return ''
   s=str(v).strip().lower()
   return '' if s in {'','nan','none','null','na'} else s

def g(r, ks):
   for k in ks:
      if k in r and str(r[k]).strip()!='':
         return r[k]
   return None

rows=json.loads(reg_path.read_text())
ids=set()
for r in rows:
   if not isinstance(r,dict):
      continue
   sh=str(g(r,['ShowRef','show_ref','Show Ref','Show']) or '').strip().upper()
   if sh not in shows:
      continue
   f=n(g(r,['Forename','First Name','FirstName','forename','first_name']))
   s=n(g(r,['Surname','Last Name','LastName','surname','last_name']))
   e=n(g(r,['Email','Email Address','email','email_address','Registrant Email']))
   if f and s and e:
      ids.add(f"{f}_{s}_{e}")

with GraphDatabase.driver(creds['uri'], auth=(creds['username'],creds['password'])) as d:
   with d.session() as s:
      neo=set(s.run("""
         MATCH (v:Visitor_this_year {show:'tsl'})
         WHERE coalesce(v.id_both_years,'')<>''
         RETURN collect(toLower(v.id_both_years)) AS ids
      """).single()['ids'] or [])

missing=sorted(ids-neo)
out=pa/'large_tool_results'/f'pre_step4_missing_identities_{Path().cwd().name}.json'
out.write_text(json.dumps({
   'expected':len(ids),
   'neo_before':len(neo),
   'missing_before':len(missing),
   'missing_identities':missing
}, indent=2))

print('expected=',len(ids),'neo_before=',len(neo),'missing_before=',len(missing))
print('snapshot_file=',out)
PY
```

```bash
/mnt/wolverine/home/samtukra/juan/repos/PA/.venv/bin/python main.py --config config/config_tsl.yaml --only-steps 4 --skip-mlflow 2>&1 | tee large_tool_results/post_analysis_step4_${STAMP}.log
```

```bash
/mnt/wolverine/home/samtukra/juan/repos/PA/.venv/bin/python - <<'PY' 2>&1 | tee logs/21_link_new_visitors_to_run_${STAMP}.log
import json, yaml, os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase
from utils.neo4j_utils import resolve_neo4j_credentials

pa=Path('/mnt/wolverine/home/samtukra/juan/repos/PA/PA')
cfg=yaml.safe_load((pa/'config'/'config_tsl.yaml').read_text())
load_dotenv(pa/'keys'/'.env', override=True)
creds=resolve_neo4j_credentials(cfg)
run_id=os.environ['RUN_ID']

snap=sorted((pa/'large_tool_results').glob('pre_step4_missing_identities_*.json'))[-1]
missing=json.loads(snap.read_text())['missing_identities']

q="""
UNWIND $ids AS vid
MATCH (v:Visitor_this_year {show:'tsl'})
WHERE toLower(v.id_both_years)=vid
MATCH (rr:RecommendationRun {run_id:$run_id})
MERGE (d:CampaignDelivery {run_id:$run_id, visitor_id:coalesce(v.BadgeId, v.id_both_years)})
ON CREATE SET d.delivery_id=$run_id+'::'+coalesce(v.BadgeId, v.id_both_years),
           d.status='sent',
           d.campaign_id=coalesce(rr.campaign_id,'tsl_post_analysis'),
           d.show='tsl',
           d.run_mode='post_analysis',
           d.created_at=datetime(),
           d.updated_at=datetime()
ON MATCH SET d.updated_at=datetime()
MERGE (d)-[:FOR_VISITOR]->(v)
MERGE (d)-[:FOR_RUN]->(rr)
RETURN count(DISTINCT v) AS linked_visitors, count(DISTINCT d) AS delivery_rows
"""

with GraphDatabase.driver(creds['uri'], auth=(creds['username'],creds['password'])) as d:
   with d.session() as s:
      r=s.run(q, ids=missing, run_id=run_id).single()
      print('linked_visitors=',r['linked_visitors'],'delivery_rows=',r['delivery_rows'],'missing_input=',len(missing))
PY
```

```bash
/mnt/wolverine/home/samtukra/juan/repos/PA/.venv/bin/python - <<'PY' 2>&1 | tee logs/22_verify_step4_requirements_${STAMP}.log
import yaml, os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase
from utils.neo4j_utils import resolve_neo4j_credentials

pa=Path('/mnt/wolverine/home/samtukra/juan/repos/PA/PA')
cfg=yaml.safe_load((pa/'config'/'config_tsl.yaml').read_text())
load_dotenv(pa/'keys'/'.env', override=True)
creds=resolve_neo4j_credentials(cfg)
run_id=os.environ['RUN_ID']

queries={
 'visitors_total':"MATCH (v:Visitor_this_year {show:'tsl'}) RETURN count(v) AS c",
 'with_id_both_years':"MATCH (v:Visitor_this_year {show:'tsl'}) WHERE coalesce(v.id_both_years,'')<>'' RETURN count(v) AS c",
 'with_identity_key':"MATCH (v:Visitor_this_year {show:'tsl'}) WHERE coalesce(v.identity_key,'')<>'' RETURN count(v) AS c",
 'run_delivery':"MATCH (d:CampaignDelivery {run_id:$run_id}) RETURN count(d) AS c",
 'run_for_run':"MATCH (d:CampaignDelivery {run_id:$run_id})-[:FOR_RUN]->(:RecommendationRun {run_id:$run_id}) RETURN count(d) AS c",
 'run_for_visitor':"MATCH (d:CampaignDelivery {run_id:$run_id})-[:FOR_VISITOR]->(:Visitor_this_year {show:'tsl'}) RETURN count(d) AS c",
 'new_reco_written':"MATCH (:Visitor_this_year)-[r:IS_RECOMMENDED {run_id:$run_id}]->(:Sessions_this_year) RETURN count(r) AS c"
}

with GraphDatabase.driver(creds['uri'], auth=(creds['username'],creds['password'])) as d:
   with d.session() as s:
      for k,q in queries.items():
         print(k,'=',s.run(q,run_id=run_id).single()['c'])
PY
```

### Artifact locations
- Logs: `PA/logs/20_pre_step4_missing_visitors_<STAMP>.log`, `21_link_new_visitors_to_run_<STAMP>.log`, `22_verify_step4_requirements_<STAMP>.log`
- Results: `PA/large_tool_results/pre_step4_missing_identities_*.json`, `post_analysis_step4_<STAMP>.log`

### Execution update (2026-03-11)
- One-time closure executed for remaining valid-badge identity gap using post-analysis-only backfill.
- Run scope: `tsl_post_analysis_20260310_151951Z_ccfa80c9`
- Evidence artifacts:
   - `PA/large_tool_results/tsl_post_analysis_backfill_apply_20260311_084340.json`
   - `PA/large_tool_results/tsl_post_analysis_backfill_apply_20260311_084416.json`
- Outcome:
   - `candidate_identities=31807`
   - `missing_before_apply=122`
   - `insert_touched=122`
   - `linked_deliveries=122`
   - `missing_after_apply=0`

### Console execution (full logging) — strict post-analysis rebuild

Use this when running manually from terminal to capture complete logs for troubleshooting.

```bash
cd /mnt/wolverine/home/samtukra/juan/repos/PA/PA
source /mnt/wolverine/home/samtukra/juan/repos/PA/.venv/bin/activate
export PYTHONUNBUFFERED=1
PYTHONPATH=/mnt/wolverine/home/samtukra/juan/repos/PA/PA \
python scripts/rebuild_post_analysis_scope_from_step1.py \
--config config/config_tsl.yaml \
--step1-csv data/tsl/output/df_reg_demo_this.csv \
--post-run-id tsl_post_analysis_20260310_151951Z_ccfa80c9 \
--exclude-run-id tsl_personal_agendas_20260219T124351 \
--exclude-run-id tsl_personal_agendas_20260227T224725Z_37b21c42 \
2>&1 | tee \
/mnt/wolverine/home/samtukra/juan/repos/PA/logs/rebuild_post_scope_$(date -u +%Y%m%dT%H%M%SZ).log
```

Optional Neo4j connectivity precheck (prints resolved URI and validates `RETURN 1`):

```bash
python - <<'PY'
from neo4j import GraphDatabase
from dotenv import load_dotenv
import yaml
from utils.neo4j_utils import resolve_neo4j_credentials

load_dotenv('/mnt/wolverine/home/samtukra/juan/repos/PA/keys/.env', override=False)
cfg = yaml.safe_load(open('/mnt/wolverine/home/samtukra/juan/repos/PA/PA/config/config_tsl.yaml'))
creds = resolve_neo4j_credentials(cfg)

print('URI:', creds['uri'])
d = GraphDatabase.driver(creds['uri'], auth=(creds['username'], creds['password']))
with d.session() as s:
    print('ping:', s.run('RETURN 1 AS ok').single()['ok'])
d.close()
PY
```

### Final execution result (2026-03-11)

- Apply completed successfully using Step 1 processed dataframe source (`df_reg_demo_this.csv`).
- Run scope updated: `tsl_post_analysis_20260310_151951Z_ccfa80c9`.
- Evidence artifacts:
   - `PA/logs/rebuild_post_scope_20260311T103837Z.log`
   - `PA/large_tool_results/post_analysis_scope_rebuild_step1_20260311_104632.json`

Key outcomes:
- `target_badges_excluding_runs=6188`
- `post_delivery_deleted=6411`
- `post_delivery_created_touched=6188`
- `verify.post_total=6188`
- `verify.overlap_count=0` (vs personal_agendas exclusion runs)
- `IS_RECOMMENDED {run_id=tsl_post_analysis_20260310_151951Z_ccfa80c9}=0`

Visitor_this_year breakdown per RecommendationRun (distinct visitors via `CampaignDelivery -> FOR_VISITOR`):
- Definition: counts are `count(DISTINCT v:Visitor_this_year)` from `(d:CampaignDelivery {run_id})-[:FOR_VISITOR]->(v)`.
- `tsl_engagement_20260219T205354Z_c3f8fb55` (`engagement`): `46555`
- `tsl_personal_agendas_20260219T124351` (`personal_agendas`): `16656`
- `tsl_personal_agendas_20260227T224725Z_37b21c42` (`personal_agendas`): `8902`
- `tsl_post_analysis_20260310_151951Z_ccfa80c9` (`post_analysis`): `6188`
- Breakdown artifact: `PA/large_tool_results/tsl_visitor_breakdown_per_run_20260311_104838.json`

### registered_to_show rebuild + verification (2026-03-11)

Objective:
- Rebuild `registered_to_show` from entry scans for `TSL26` with run-scoped lineage on `run_id=tsl_post_analysis_20260310_151951Z_ccfa80c9`.

Command (apply):

```bash
cd /mnt/wolverine/home/samtukra/juan/repos/PA/PA
source /mnt/wolverine/home/samtukra/juan/repos/PA/.venv/bin/activate
PYTHONPATH=/mnt/wolverine/home/samtukra/juan/repos/PA/PA \
python scripts/rebuild_registered_to_show_from_entry_scans.py \
   --config config/config_tsl.yaml \
   --entry-scan-csv data/tsl/post/20260306_tsl26_entry_scans.csv \
   --post-run-id tsl_post_analysis_20260310_151951Z_ccfa80c9 \
   --show-ref TSL26 \
   --report-file large_tool_results/registered_to_show_rebuild_apply_latest.json
```

Implemented matching policy:
- Identity key concatenation pattern is aligned across sources:
   - node side: `forename_surname_email`
   - file side: `First Name_Last Name_Email`
- Matching uses all `Visitor_this_year` as candidate ground truth.
- Barcode is fallback only for visitors observed in runs with `run_mode IN ['personal_agendas','post_analysis']`.

Execution evidence:
- `PA/large_tool_results/registered_to_show_rebuild_apply_latest.json`

Execution results:
- `registered_to_show_for_run_and_show=18261`
- DB match-mode breakdown for `run_id=tsl_post_analysis_20260310_151951Z_ccfa80c9` + `show_ref=TSL26`:
   - `badge=18102`
   - `identity=159`

Campaign/run membership for this `18261` population (overlapping by visitor):
- `tsl_engagement_20260219T205354Z_c3f8fb55`: `8344`
- `tsl_personal_agendas_20260219T124351`: `8344`
- `tsl_personal_agendas_20260227T224725Z_37b21c42`: `5284`
- `tsl_post_analysis_20260310_151951Z_ccfa80c9`: `4564`

Interpretation note:
- Per-run counts above are not additive because a visitor can appear in multiple runs.
- Separate overlap check on full personal_agendas delivery populations confirms:
   - `pa_20260219=16656`, `pa_20260227=8902`, `intersection=0`.

