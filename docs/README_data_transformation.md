# Data Transformation Overview

This guide explains how the scripts in `PA/data_transformation` convert raw show exports into the shapes expected by the Personal Agendas pipeline. It links the per-show adapters, helper utilities, and the dry-run checker used to validate changes before committing.

---

## Common concepts

- Target schemas: GraphQL-style outputs are the default for `old_format: false`; optional legacy outputs mirror the flattened headers used when `old_format: true`.
- Header aliases: `PA/data_transformation/config/header_mappings.json` holds field-name mappings shared by all transformers.
- Reference schemas: adapters reuse the reference GraphQL files under `PA/data/cpcn/reference/` to keep output columns consistent across shows.
- Entry point: run scripts from the repo root so relative data paths resolve correctly.

---

## Show adapters

### CPCN / CPC
- Script: `PA/data_transformation/transform_cpc_data.py`.
- Inputs: merged 2024/2025 registration and demographic drops under `PA/data/cpcn/`.
- Outputs: GraphQL files for combined 24/25 plus CPC25-only; optional legacy companions when `--legacy` is passed.
- Run: `python PA/data_transformation/transform_cpc_data.py [--legacy]`.
- Notes: update `SHOW_DETAILS` inside the script if CPCN/CPC event IDs or dates change.

### LVS / LVA
- Script: `PA/data_transformation/transform_lva_data.py`.
- Inputs: LVS24, LVS25 registration and demographic JSON under `PA/data/lva/`.
- Outputs: year-specific GraphQL files, combined 24/25 GraphQL files, and optional legacy variants.
- Run: `python PA/data_transformation/transform_lva_data.py [--legacy]`.
- Notes: keep raw filenames stable; combined outputs are keyed off the current naming pattern.

### Tech Show London (TSL)
- Script: `PA/data_transformation/transform_tsl_data.py`.
- Inputs: legacy-shaped 24/25 bundles plus nested 2026 GraphQL-style files under `PA/data/tsl/`.
- Outputs: per-year GraphQL for 26, combined GraphQL 24/25/26, and legacy variants for all when `--legacy` is passed.
- Run: `python PA/data_transformation/transform_tsl_data.py [--legacy]`.
- Notes: `SHOW_DETAILS` leaves `event_id` and `show_date` empty for TSL26 until upstream provides them.

---

## TSL helpers

### split_tsl_legacy.py
- Purpose: split the combined legacy 24/25 registration and demographic bundles into year-specific files before running the main TSL transformer.
- Inputs: `PA/data/tsl/Reg_Tech_Lnd_24_25.json`, `PA/data/tsl/Demographics_Tech_Lnd_24_25.json`.
- Outputs: `Reg_Tech_Lnd_24.json`, `Reg_Tech_Lnd_25.json`, `Demographics_Tech_Lnd_24.json`, `Demographics_Tech_Lnd_25.json` in the same folder.
- Run: `python PA/data_transformation/split_tsl_legacy.py`.

### split_tsl_sessions.py
- Purpose: split the `20250305_speaker_exports_TL24_TL25.json` session export into year-specific CSVs using the CPCN session header order as a reference.
- Inputs: `PA/data/tsl/20250305_speaker_exports_TL24_TL25.json` and reference `PA/data/cpcn/CPCN25_session_export.csv`.
- Outputs: `PA/data/tsl/TSL2024_session_export.csv` and `PA/data/tsl/TSL2025_session_export.csv`.
- Run: `python PA/data_transformation/split_tsl_sessions.py`.

---

## Dry-run comparison

### dry_run_compare.py
- Purpose: run the CPC and LVA transformers (with optional legacy mode), compare regenerated outputs to existing files, and report differences without leaving changes on disk.
- Run:
  - Default: `python PA/data_transformation/dry_run_compare.py`
  - Include legacy outputs: `python PA/data_transformation/dry_run_compare.py --legacy`
  - Keep regenerated files instead of restoring backups: add `--keep-new`.
- Output: prints a summary of changed, new, or missing files, plus sample field diffs when they occur.

---

## Operational tips

- All adapters are idempotent; rerun them whenever upstream JSON drops are refreshed.
- When `old_format` is true in a pipeline config, point to the `_legacy.json` outputs; otherwise use the default `_graphql.json` files.
- If upstream files rename headers, update `config/header_mappings.json` first, then rerun the transformers.
- Commit regenerated outputs only after reviewing differences with `dry_run_compare.py` or manual inspection.