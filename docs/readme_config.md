# Configuration Playbook for PA Pipeline

Reference guide for every section of the YAML files under `PA/config`. It maps each setting to the processor that consumes it and calls out differences across the five maintained examples:

- `config/config_cpcn.yaml` → CPCN 2025 personal agendas (GraphQL-style inputs)
- `config/config_ecomm.yaml` → ECOMM 2025 personal agendas (legacy-style inputs)
- `config/config_vet_bva.yaml` → BVA 2025 personal agendas
- `config/config_vet_lva.yaml` → LVA 2025 personal agendas (paired with BVA)
- `config/config_tsl.yaml` → TSL 2026 personal agendas

Use this when onboarding a new event or troubleshooting a run.

---

## 1. Global Pipeline Controls

| Key | Description | CPCN | ECOMM | BVA | LVA | TSL |
| --- | --- | --- | --- | --- | --- | --- |
| `mode` | `personal_agendas` (default), `engagement`, or `post_analysis`. | `personal_agendas` (engagement overrides present but off) | `personal_agendas` | `personal_agendas` | `personal_agendas` | `personal_agendas` |
| `create_only_new` | Skip visitors that already have recommendations. | `false` | `true` | `false` | `false` | `false` |
| `old_format` | Legacy header mode for registration/demographic JSON. | `false` | `true` | `true` | `true` | `true` |
| `pipeline_steps` | Enables processors 1–11. Job/specialization steps are disabled for CPCN/ECOMM and enabled for BVA/LVA/TSL. Output processing can be run independently or as part of session recommendations. | session/job/specialization off where noted | same | on | on | on |

**Processor map (steps 1–11):** 1 `RegistrationProcessor`; 2 `ScanProcessor`; 3 `SessionProcessor`; 4 `Neo4jVisitorProcessor`; 5 `Neo4jSessionProcessor`; 6 `Neo4jJobStreamProcessor`; 7 `Neo4jSpecializationStreamProcessor`; 8 `Neo4jVisitorRelationshipProcessor`; 9 `SessionEmbeddingProcessor`; 10 `SessionRecommendationProcessor`; 11 `OutputProcessor`.

`main.py` honours `pipeline_steps` and CLI `--only-steps`; the CLI wins when both are supplied.

---

## 2. Event Metadata (`event` block)

Defines how processors label visitors, sessions, and outputs.

| Field | CPCN | ECOMM | BVA | LVA | TSL |
| --- | --- | --- | --- | --- | --- |
| `name` / `main_event` | `cpcn` | `ecomm` | `bva` | `lva` | `tsl` |
| `main_event_name` | `cpcn` (non-vet) | `ecomm` (non-vet) | `bva` (triggers vet helpers) | `lva` (triggers vet helpers) | `tsl` (triggers vet helpers) |
| `secondary_event_name` | `cpc` | `tfm` | `lva` | `bva` | `tsl_secondary` |
| `year` | `2025` | `2025` | `2025` | `2025` | `2026` |
| `shows_this_year` | `CPCN25` | `ECE25`, `TFM25` | `BVA2025` | `LVS25` | `DCWL26`, `DAILS26`, `CAIL26`, `CCSEL26`, `DOLL26` |
| `shows_last_year_main` | `CPCN24`, `CPCN2024` | `ECE24` | `BVA2024` | `LVS24` | `CCSEL25`, `DCWL25`, `BDAWL25`, `DL25`, `CEEL25` |
| `shows_last_year_secondary` | `CPC2025`, `CPC25` | `TFM24` | `LVS2024` | `BVA2025` | `DCWL24`, `CCSEL24`, `BDAWL24`, `CEEL24`, `DL24` |

Vet-specific helpers load when `main_event_name` contains `bva`, `lva`, `tsl`, or `vet`.

Badge/practice metadata (primarily for vet shows, retained for compatibility elsewhere): `badge_history_columns`, `practice_type_columns`, `practice_matching`, and `job_role_question` define how to match last-year badges, normalise practice names, and select the canonical job-role field.

---

## 3. Documentation & Post-Analysis

- `documentation`: points to generic and show-specific pipeline maps (SVGs). All configs populate this.
- `post_analysis_mode`: used for entry-scan and seminar postmortems; provides `registration_shows`, `scan_files.seminars_*`, and `entry_scan_files`. Present in CPCN/ECOMM/LVA for optional reruns.

---

## 4. Engagement Overrides (`engagement_mode`)

Defined in all files but typically unused unless `mode: engagement` is set. Keys:

- `registration_shows.this_year_main/secondary`: treat last-year shows as current-year registrants.
- `registration_shows.last_year_*`: optional deeper history.
- `drop_last_year_when_missing`: skip placeholder visitors when no badge match exists.
- `reset_returning_flags`: clear returning indicators before processing.

---

## 5. Input File Paths (`input_files`)

RegistrationProcessor inputs. Examples mirror the current configs:

- CPCN: `data/cpcn/20251201_eventregistration_CPCN24_25_graphql.json` and matching demographics; GraphQL layout (`old_format: false`).
- ECOMM: `data/ecomm/20250923_registration_ECE_TFM_24_25.json` plus TFM24 legacy files; legacy layout (`old_format: true`).
- BVA: `data/bva/20250609_registration_BVA24_BVA25.json` and demographics; legacy layout.
- LVA: `data/lva/20251127_eventregistration_LVS24_25_legacy.json` and demographics; legacy layout.
- TSL: `data/tsl/20260120_tsl25_26_registration_legacy.json` and demographics; legacy layout.
- `practices`: optional missing-company CSV (present in CPCN/BVA/LVA/TSL).

Keep paths under the event folder for tidy outputs.

---

## 6. Scan Configuration (`scan_files` and `scan_output_files`)

### Inputs (`scan_files`)

Each config supplies current and past scan CSVs plus seminar lookup files. Post-analysis blocks add `entry_scan_files` for entry-gate scans.

### Outputs (`scan_output_files`)

Uniform structure across configs:

- `processed_scans`: `scan_bva_past.csv`, `scan_lva_past.csv`, and `scan_this_post.csv` (post-run artifact).
- `sessions_visited`: per-show visit summaries, plus `sessions_visited_this_year.csv` for post analysis.
- `attended_session_inputs`: explicit filenames for the relationship builder (`past_year_*_scan` and `past_year_*_filter`).

---

## 7. Session Configuration (`session_files` and `session_output_files`)

- CPCN: `CPCN25_session_export.csv` (this year), `CPCN24_session_export.csv` (past main), `CPC2025_session_export.csv` (past secondary).
- ECOMM: `ECE25_session_export.csv`, `ECE24_session_export.csv`, `TFM24_session_export.csv`.
- BVA: `BVA25_session_export.csv`, `BVA24_session_export.csv`, `LVA24_session_export.csv`.
- LVA: `LVS25_session_export.csv`, `LVS24_session_export.csv`, `BVA25_session_export.csv`.
- TSL: `TSL2026_session_export.csv`, `TSL2025_session_export.csv`, `TSL2024_session_export.csv`.

Outputs are fixed: `session_this_filtered_valid_cols.csv`, `session_last_filtered_valid_cols_bva.csv`, `session_last_filtered_valid_cols_lva.csv`, plus `streams.json`.

`stream_processing` adds `create_missing_streams` and `use_enhanced_streams_catalog` across all configs; caching stays off (`use_cached_descriptions: false`).

---

## 8. Stream Descriptions and Sponsor Maps

- `titles_to_remove`: shared list of placeholders (“Session title to be confirmed”, “session tbc”, etc.).
- `map_vets`: sponsor/abbreviation mapping. Even non-vet shows keep this key for compatibility (ECOMM populates agency/vendor names; CPCN keeps a minimal map; vet configs have extended mappings).

These lists also gate auto-generated streams when `create_missing_streams` is enabled.

---

## 9. Registration Outputs (`output_files`)

Shape is identical across configs and required by downstream processors:

- Enrichment artifacts: `professions_list`, `specializations`, `job_roles`.
- Raw/processed registration and demographic CSVs (this/past/returning variants).
- Joined tables: `registration_with_demographic`, `combined_demographic_registration` (`df_reg_demo_*`).
- Snapshots: `concatenated_registration_data` JSONs.
- Processed demographic JSONs for MLflow QA.
- `recommendations`: `{output_directory, filename_pattern, save_csv, save_json}` consumed by the recommendation processor (default folder `recommendations`, pattern `visitor_recommendations_{timestamp}`). `save_csv` controls CSV export (default `true`), `save_json` controls JSON export (default `true`).

Top-level `output_dir` must match the on-disk root used in these paths.

---

## 10. Recommendation Logic (`recommendation` block)

Shared controls plus event-specific tweaks:

- Scores/limits: CPCN/BVA/LVA/TSL use `min_similarity_score: 0.3`, `max_recommendations: 10`, `similar_visitors_count: 3`; ECOMM raises similarity to `0.5` and limit to `20`.
- `resolve_overlapping_sessions_by_similarity`: enabled everywhere.
- `control_group`: enabled (5% default) for personal-agendas runs; writes to `recommendations/control` and adds a `control_group` Neo4j property.
- `save_csv` and `save_json`: control output format - `save_csv` enables CSV export (default `true`), `save_json` enables JSON export (default `true`).
- `returning_without_history`: boosts returning visitors missing scans (enabled in all configs).
- `enable_filtering`: vet configs `true`; CPCN/ECOMM `false`.
- `theatre_capacity_limits`: on for LVA (capacity CSV and multiplier), off elsewhere.
- `similarity_attributes`: event-specific weights (vet configs use `job_role` and practice type; CPCN uses pharmacy questions; ECOMM uses commerce questions and attendance motivations).
- `field_mappings` and `rules_config`: vet-specific filtering and custom rules; empty for CPCN/ECOMM.

---

## 11. Neo4j Configuration (`neo4j` block)

Common structure with environment-specific targets: CPCN → `dev`, ECOMM → `test`, BVA/LVA/TSL → `prod`.

- `node_labels`, `unique_identifiers`, `relationships`: stable across configs and must match the graph schema. Relationships include `assisted_session_this_year` and `registered_to_show` for post-analysis flows.
- `job_stream_mapping` and `specialization_stream_mapping`: gated by `enabled`. Enabled for vet configs; disabled for CPCN/ECOMM. Field names map to the event-specific survey questions.
- `visitor_relationship.same_visitor_properties`: retains legacy `bva`/`lva` keys even for non-vet shows but adjusts the `type` metadata per event.

---

## 12. Default Visitor Properties

Event-specific fallbacks merged into visitor rows before Neo4j upload. Examples: CPCN sets `Email_domain: cpcn.co.uk`; ECOMM sets `Source: ECOMM Key Stakeholders`; vet configs default practice-related fields to `NA` and set `Email_domain: vetpractice.co.uk`.

---

## 13. Logging, Models, and Misc

- `env_file`: always `keys/.env`.
- `language_model`: CPCN/BVA use `gpt-4o-mini`; ECOMM uses `gpt-4.1-mini` (temperature/top_p shared).
- `embeddings`: `all-MiniLM-L6-v2`, `batch_size: 100`, `include_stream_descriptions: false`.
- `logging`: level/file; defaults to `INFO` / `data_processing.log` (see ECOMM config).
- `event_date_this_year` / `event_date_last_year`: used by reporting helpers for clash detection.
- `valid_badge_types`: whitelists per event (CPCN delegates/speakers; ECOMM visitor/VIP; vet configs inherit defaults).
- Top-level `shows_this_year` mirrors `event.shows_this_year` for consumers that do not read nested metadata.
- `questions_to_keep` and `question_text_corrections`: limit/correct demographic columns per event.

---

## 14. Checklist for New Config Creation

1. Copy the closest config file and rename it under `config/`.
2. Update `event` (names, show codes, year) and align top-level `shows_this_year`.
3. Point `input_files`, `scan_files`, `session_files`, and optional `post_analysis_mode` paths to new datasets.
4. Keep `session_output_files` and `scan_output_files` filenames unchanged unless processors are updated.
5. Decide `mode` (`personal_agendas`, `engagement`, or `post_analysis`) and adjust `engagement_mode`/`control_group` accordingly.
6. Set Neo4j `environment`/`show_name` and toggle job/specialization mappings via `pipeline_steps` and `neo4j.*.enabled` flags.
7. Tune `similarity_attributes`, `field_mappings`, and `rules_config` to match available survey questions; adjust capacity limits if needed.
8. Run `python main.py --config config/<file>.yaml` and monitor `logs/data_processing.log` for warnings.

Following this checklist keeps processors aligned with the current PA pipeline defaults.
