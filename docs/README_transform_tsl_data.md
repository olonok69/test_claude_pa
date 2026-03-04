# Tech Show London (TSL) Schema Adapter

`PA/data_transformation/transform_tsl_data.py` normalises Tech Show London registration and demographic datasets. It covers the legacy 2024/25 drops and the newer nested 2026 format, emitting GraphQL-style outputs plus optional legacy outputs. Combined multi-year files mirror the CPC/LVA approach.

## Inputs

- Legacy 2024/25 (already legacy-shaped):
  - `PA/data/tsl/Reg_Tech_Lnd_24_25.json`
  - `PA/data/tsl/Demographics_Tech_Lnd_24_25.json`
- 2026 (nested GraphQL-style):
  - `PA/data/tsl/20260108_eventregistration_tsl26.json`
  - `PA/data/tsl/20260108_eventregistration_TSL26_demographics.json`

## Outputs

- GraphQL per-year:
  - `20260108_eventregistration_TSL26_graphql.json`
  - `20260108_eventregistration_TSL26_demographics_graphql.json`
- Combined GraphQL (24/25/26):
  - `20260108_eventregistration_TSL24_25_26_graphql.json`
  - `20260108_eventregistration_TSL24_25_26_demographics_graphql.json`
- Legacy (when `--legacy`):
  - `20260108_eventregistration_TSL24_25_legacy.json`
  - `20260108_eventregistration_TSL24_25_demographics_legacy.json`
  - `20260108_eventregistration_TSL26_legacy.json`
  - `20260108_eventregistration_TSL26_demographics_legacy.json`
  - `20260108_eventregistration_TSL24_25_26_legacy.json`
  - `20260108_eventregistration_TSL24_25_26_demographics_legacy.json`

## Usage

Run from the repository root:

```powershell
# Emit GraphQL-format outputs (default)
python PA/data_transformation/transform_tsl_data.py

# Emit GraphQL + legacy-format outputs (for old_format=true runs)
python PA/data_transformation/transform_tsl_data.py --legacy
```

## Notes

- Header aliases live in `PA/data_transformation/config/header_mappings.json`; update if the TSL feeds rename fields.
- `SHOW_DETAILS` leaves `TSL26` `event_id` and `show_date` as `None` (not provided in the source). Fill these if IDs/dates become available.
- Reference schemas reuse `data/cpcn/reference/` keys, matching other shows’ GraphQL targets.
- Combined outputs merge 24/25 legacy data with 26 GraphQL-transformed data, matching the CPC/LVA pattern.