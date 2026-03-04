# Personal Agendas Pipeline – Local Data Requirements

## Scope
- All four show configurations that declare `mode: "personal_agendas"` feed this pipeline: [config_vet_bva.yaml](PA/config/config_vet_bva.yaml#L1-L35), [config_vet_lva.yaml](PA/config/config_vet_lva.yaml#L1-L35), [config_cpcn.yaml](PA/config/config_cpcn.yaml#L1-L60), and [config_ecomm.yaml](PA/config/config_ecomm.yaml#L1-L60).
- Execution follows the ten steps orchestrated in [PA/main.py](PA/main.py#L310-L362) for stages 1‑3 and [PA/pipeline.py](PA/pipeline.py#L153-L240) for stages 4‑10.
- This document lists every external input file that must exist before running `python -m PA.main --config <file>` locally in personal_agendas mode.

## Step Overview
| Step | Processor | Purpose | Raw Inputs |
| --- | --- | --- | --- |
| 1 | `RegistrationProcessor` | Clean and enrich registration + demographic data | `input_files.*` JSON/CSV plus optional practices lookup |
| 2 | `ScanProcessor` | Harmonize historical and current scan exports | `scan_files.*` session exports + seminar scan CSVs (and `post_analysis_mode.entry_scan_files` when used) |
| 3 | `SessionProcessor` | Filter session catalogue and streams | `session_files.*` exports plus optional `session_output_files.streams_catalog` seed |
| 4 | `Neo4jVisitorProcessor` | Push visitor nodes | Outputs from Steps 1‑2 + Neo4j connection defined in config |
| 5 | `Neo4jSessionProcessor` | Push session + stream nodes | Outputs from Step 3 |
| 6 | `Neo4jJobStreamProcessor` | Create `job_to_stream` relationships | `neo4j.job_stream_mapping.file` when enabled |
| 7 | `Neo4jSpecializationStreamProcessor` | Create `specialization_to_stream` links | `neo4j.specialization_stream_mapping.file` when enabled |
| 8 | `Neo4jVisitorRelationshipProcessor` | Build visitor ↔ visitor & attendance edges | `scan_output_files.attended_session_inputs.*` produced in Steps 1‑2 |
| 9 | `SessionEmbeddingProcessor` | Generate embeddings for sessions | `session_output_files.processed_sessions.this_year` (Step 3 result) |
| 10 | `SessionRecommendationProcessor` | Export personal agendas | Step 1‑9 outputs plus optional `recommendation.theatre_capacity_limits.*` files |

## Step 1 – Registration Processing
Source paths come from each configuration’s `input_files` block ([BVA](PA/config/config_vet_bva.yaml#L119-L142), [LVA](PA/config/config_vet_lva.yaml#L121-L139), [CPCN](PA/config/config_cpcn.yaml#L145-L154), [ECOMM](PA/config/config_ecomm.yaml#L128-L136)).

| Config | Main Registration | Secondary Registration | Main Demographic | Secondary Demographic | Practices Lookup | Format Flag |
| --- | --- | --- | --- | --- | --- | --- |
| BVA | [data/bva/20250609_registration_BVA24_BVA25.json](data/bva/20250609_registration_BVA24_BVA25.json) | [data/bva/20250428_registration_LVS24.json](data/bva/20250428_registration_LVS24.json) | [data/bva/20250609_demographics_BVA24_BVA25.json](data/bva/20250609_demographics_BVA24_BVA25.json) | [data/bva/20250428_demographics_LVS24.json](data/bva/20250428_demographics_LVS24.json) | [data/bva/practices_missing.csv](data/bva/practices_missing.csv) | `old_format: true` |
| LVA | [data/lva/20251127_eventregistration_LVS24_25_legacy.json](data/lva/20251127_eventregistration_LVS24_25_legacy.json) | [data/lva/20250922_registration_BVA_25.json](data/lva/20250922_registration_BVA_25.json) | [data/lva/20251127_eventregistration_LVS24_25_demographics_legacy.json](data/lva/20251127_eventregistration_LVS24_25_demographics_legacy.json) | [data/lva/20250922_demographics_BVA_25.json](data/lva/20250922_demographics_BVA_25.json) | [data/lva/practices_missing.csv](data/lva/practices_missing.csv) | `old_format: true` |
| CPCN | [data/cpcn/20251201_eventregistration_CPCN24_25_graphql.json](data/cpcn/20251201_eventregistration_CPCN24_25_graphql.json) | [data/cpcn/20251006_eventregistration_CPC25_graphql.json](data/cpcn/20251006_eventregistration_CPC25_graphql.json) | [data/cpcn/20251201_CPCN24_25_demographics_graphql.json](data/cpcn/20251201_CPCN24_25_demographics_graphql.json) | [data/cpcn/20251006_eventregistration_CPC25_demographics_graphql.json](data/cpcn/20251006_eventregistration_CPC25_demographics_graphql.json) | [data/cpcn/practices_missing.csv](data/cpcn/practices_missing.csv) | `old_format: false` |
| ECOMM | [data/ecomm/20250923_registration_ECE_TFM_24_25.json](data/ecomm/20250923_registration_ECE_TFM_24_25.json) | [data/ecomm/20250722_registration_TFM24.json](data/ecomm/20250722_registration_TFM24.json) | [data/ecomm/20250923_demographics_ECE_TFM_24_25.json](data/ecomm/20250923_demographics_ECE_TFM_24_25.json) | [data/ecomm/20250722_demographics_TFM24.json](data/ecomm/20250722_demographics_TFM24.json) | _not configured_ | `old_format: true` |

## Step 2 – Scan Processing
Paths originate from each `scan_files` block ([BVA](PA/config/config_vet_bva.yaml#L131-L144), [LVA](PA/config/config_vet_lva.yaml#L130-L143), [CPCN](PA/config/config_cpcn.yaml#L154-L167), [ECOMM](PA/config/config_ecomm.yaml#L136-L145)). `post_analysis_mode.entry_scan_files` (where present) add further CSVs for late-stage runs.

| Config | This-Year Session Export | Last-Year Main | Last-Year Secondary | Seminar Ref (Main) | Seminar Scans (Main) | Seminar Ref (Secondary) | Seminar Scans (Secondary) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BVA | [data/bva/BVA25_session_export.csv](data/bva/BVA25_session_export.csv) | [data/bva/BVA24_session_export.csv](data/bva/BVA24_session_export.csv) | [data/bva/LVA24_session_export.csv](data/bva/LVA24_session_export.csv) | [data/bva/bva2024 seminar scans reference.csv](data/bva/bva2024%20seminar%20scans%20reference.csv) | [data/bva/bva2024 seminar scans.csv](data/bva/bva2024%20seminar%20scans.csv) | [data/bva/lvs2024 seminar scans reference.csv](data/bva/lvs2024%20seminar%20scans%20reference.csv) | [data/bva/lvs2024 seminar scans.csv](data/bva/lvs2024%20seminar%20scans.csv) |
| LVA | [data/lva/LVS25_session_export.csv](data/lva/LVS25_session_export.csv) | [data/lva/LVS24_session_export.csv](data/lva/LVS24_session_export.csv) | [data/lva/BVA25_session_export.csv](data/lva/BVA25_session_export.csv) | [data/lva/lvs2024 seminar scans reference.csv](data/lva/lvs2024%20seminar%20scans%20reference.csv) | [data/lva/lvs2024 seminar scans.csv](data/lva/lvs2024%20seminar%20scans.csv) | [data/lva/bva25 seminar scans reference.csv](data/lva/bva25%20seminar%20scans%20reference.csv) | [data/lva/bva25 seminar scans.csv](data/lva/bva25%20seminar%20scans.csv) |
| CPCN | [data/cpcn/CPCN25_session_export.csv](data/cpcn/CPCN25_session_export.csv) | [data/cpcn/CPCN24_session_export.csv](data/cpcn/CPCN24_session_export.csv) | [data/cpcn/CPC2025_session_export.csv](data/cpcn/CPC2025_session_export.csv) | [data/cpcn/cpcn24 seminar scans reference.csv](data/cpcn/cpcn24%20seminar%20scans%20reference.csv) | [data/cpcn/cpcn24 seminar scans.csv](data/cpcn/cpcn24%20seminar%20scans.csv) | [data/cpcn/cpc25 seminar scans reference.csv](data/cpcn/cpc25%20seminar%20scans%20reference.csv) | [data/cpcn/cpc25 seminar scans.csv](data/cpcn/cpc25%20seminar%20scans.csv) |
| ECOMM | [data/ecomm/ECE_TFM_25_session_export.csv](data/ecomm/ECE_TFM_25_session_export.csv) | [data/ecomm/ECE24_session_export.csv](data/ecomm/ECE24_session_export.csv) | [data/ecomm/TFM24_session_export.csv](data/ecomm/TFM24_session_export.csv) | [data/ecomm/ece2024 seminar scans reference.csv](data/ecomm/ece2024%20seminar%20scans%20reference.csv) | [data/ecomm/ece2024 seminar scans.csv](data/ecomm/ece2024%20seminar%20scans.csv) | [data/ecomm/tfm2024 seminar scans reference.csv](data/ecomm/tfm2024%20seminar%20scans%20reference.csv) | [data/ecomm/tfm2024 seminar scans.csv](data/ecomm/tfm2024%20seminar%20scans.csv) |

## Step 3 – Session Processing
`session_files` determine the raw catalogues, and `session_output_files.streams_catalog` seeds stream metadata ([BVA](PA/config/config_vet_bva.yaml#L144-L158), [LVA](PA/config/config_vet_lva.yaml#L143-L157), [CPCN](PA/config/config_cpcn.yaml#L159-L178), [ECOMM](PA/config/config_ecomm.yaml#L145-L168)).

| Config | This-Year Sessions | Last-Year Main | Last-Year Secondary | Streams Catalog |
| --- | --- | --- | --- | --- |
| BVA | [data/bva/BVA25_session_export.csv](data/bva/BVA25_session_export.csv) | [data/bva/BVA24_session_export.csv](data/bva/BVA24_session_export.csv) | [data/bva/LVA24_session_export.csv](data/bva/LVA24_session_export.csv) | [streams.json](streams.json) |
| LVA | [data/lva/LVS25_session_export.csv](data/lva/LVS25_session_export.csv) | [data/lva/LVS24_session_export.csv](data/lva/LVS24_session_export.csv) | [data/lva/BVA25_session_export.csv](data/lva/BVA25_session_export.csv) | [streams.json](streams.json) |
| CPCN | [data/cpcn/CPCN25_session_export.csv](data/cpcn/CPCN25_session_export.csv) | [data/cpcn/CPCN24_session_export.csv](data/cpcn/CPCN24_session_export.csv) | [data/cpcn/CPC2025_session_export.csv](data/cpcn/CPC2025_session_export.csv) | [streams.json](streams.json) |
| ECOMM | [data/ecomm/ECE25_session_export.csv](data/ecomm/ECE25_session_export.csv) | [data/ecomm/ECE24_session_export.csv](data/ecomm/ECE24_session_export.csv) | [data/ecomm/TFM24_session_export.csv](data/ecomm/TFM24_session_export.csv) | [streams.json](streams.json) |

## Steps 4–5 – Neo4j Node Loads
Visitor and session loads do not pull in additional raw files beyond the processed artifacts from Steps 1‑3 plus the Neo4j connection details under each configuration’s `neo4j` section ([example](PA/config/config_vet_bva.yaml#L320-L374)). Ensure the target database referenced by `neo4j.environment` is reachable and credentials are supplied via `env_file` (see Shared prerequisites).

## Step 6 – Job→Stream Relationships
Only shows with `neo4j.job_stream_mapping.enabled: true` consume the mapping CSV ([BVA](PA/config/config_vet_bva.yaml#L352-L357), [LVA](PA/config/config_vet_lva.yaml#L353-L358), [CPCN](PA/config/config_cpcn.yaml#L307-L312), [ECOMM](PA/config/config_ecomm.yaml#L286-L291)).

| Config | Enabled | Mapping File |
| --- | --- | --- |
| BVA | true | [job_to_stream.csv](job_to_stream.csv) |
| LVA | true | [job_to_stream.csv](job_to_stream.csv) |
| CPCN | false | [job_to_stream.csv](job_to_stream.csv) |
| ECOMM | false | [job_to_stream.csv](job_to_stream.csv) |

## Step 7 – Specialization→Stream Relationships
Similar requirements apply to specialization mappings ([BVA](PA/config/config_vet_bva.yaml#L358-L388), [LVA](PA/config/config_vet_lva.yaml#L359-L402), [CPCN](PA/config/config_cpcn.yaml#L313-L341), [ECOMM](PA/config/config_ecomm.yaml#L292-L319)).

| Config | Enabled | Mapping File |
| --- | --- | --- |
| BVA | true | [spezialization_to_stream.csv](spezialization_to_stream.csv) |
| LVA | true | [spezialization_to_stream.csv](spezialization_to_stream.csv) |
| CPCN | false | [spezialization_to_stream.csv](spezialization_to_stream.csv) |
| ECOMM | false | [spezialization_to_stream.csv](spezialization_to_stream.csv) |

## Step 8 – Visitor Relationships
This step relies on the canonical filenames emitted from registration and scan processing, as declared under `scan_output_files.attended_session_inputs` ([BVA](PA/config/config_vet_bva.yaml#L170-L189), [LVA](PA/config/config_vet_lva.yaml#L168-L185), [CPCN](PA/config/config_cpcn.yaml#L178-L198), [ECOMM](PA/config/config_ecomm.yaml#L168-L188)). When rerunning only Neo4j steps, ensure the following intermediate CSVs exist in the working directory:
- `scan_bva_past.csv`, `scan_lva_past.csv`
- `df_reg_demo_last_bva.csv`, `df_reg_demo_last_lva.csv`

## Step 9 – Session Embeddings
`SessionEmbeddingProcessor` consumes the Step 3 outputs pointed to by `session_output_files.processed_sessions.this_year` ([PA/config/config_vet_bva.yaml#L140-L147] etc.) plus the selected embedding model from `embeddings.model`. No extra source files are required; models are downloaded via the configured backend.

## Step 10 – Recommendations
Recommendations run on the merged visitor + embedding data and optionally read theatre-capacity inputs when `theatre_capacity_limits.enabled` is true ([BVA](PA/config/config_vet_bva.yaml#L239-L255), [LVA](PA/config/config_vet_lva.yaml#L239-L257), [CPCN](PA/config/config_cpcn.yaml#L231-L248), [ECOMM](PA/config/config_ecomm.yaml#L214-L233)).

| Config | Capacity Checks Enabled | Capacity File | Session File |
| --- | --- | --- | --- |
| BVA | false | — | — |
| LVA | true | [data/lva/teatres.csv](data/lva/teatres.csv) | [data/lva/LVS25_session_export.csv](data/lva/LVS25_session_export.csv) |
| CPCN | false | — | — |
| ECOMM | false | [data/ecomm/theatre_capacity.csv](data/ecomm/theatre_capacity.csv) | [data/ecomm/ECE25_session_export.csv](data/ecomm/ECE25_session_export.csv) |

The recommendation block also defines `recommendations.output_directory` for exports, but no additional source data is needed beyond previous steps.

## Shared Prerequisites
- Secrets for Azure, Neo4j, and MLflow are loaded from each config’s `env_file`, which points to [keys/.env](PA/config/config_vet_bva.yaml#L395-L406). Populate that file (or override via environment variables) before invoking the pipeline.
- Optional documentation artifacts referenced under `documentation` help with MLflow lineage but are not required for processing.
- When enabling post-analysis mode in any config, also stage the files listed under `post_analysis_mode.scan_files` and `post_analysis_mode.entry_scan_files`.

With these inputs staged, the local pipeline can execute every step without prompting for additional data files.
