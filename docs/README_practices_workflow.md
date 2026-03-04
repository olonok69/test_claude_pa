# Practice Matching Workflow

This note explains how `PA/scripts/find_missing_practices.py` supports the practice-type enrichment used by the registration pipeline. It covers when to run it, which files it inspects, and how its output feeds back into the pipeline via the practice matching configuration in `registration_processor.py`.

---

## Why this exists

Vet shows use the practices catalogue (`practices_missing.csv`) to backfill missing practice types by company name. The `RegistrationProcessor` will:
- Read the practices file from `input_files.practices` in the event config.
- Fill blank practice-type columns using exact and fuzzy matches (score threshold from `practice_matching.match_threshold`).
- Write any remaining unmatched companies to `output/<missing_companies_output>` so you can expand the catalogue.

`find_missing_practices.py` is a helper that pre-computes which registration companies are absent from the practices catalogue, so you can update it before rerunning the pipeline.

---

## Inputs and outputs

- Registration CSVs: defaults are `PA/data/lva/csv/Registration_data_bva.csv` and `PA/data/lva/csv/Registration_data_lva.csv` (produced by the registration step under the event `output_dir`).
- Practices catalogue: defaults to `PA/data/lva/practices_missing.csv` (same file the pipeline reads).
- Output: optional `missing_companies.csv` listing companies not yet present in the catalogue (original name, normalised token, and source dataset). Without `--output`, the script prints the list to STDOUT.

Normalisation strips punctuation and whitespace and lowercases company names before comparison, matching the logic used in the registration processor.

---

## How to run

From the repo root after a registration run has produced the CSVs:

```powershell
# Check against the current catalogue and print results
python -m PA.scripts.find_missing_practices

# Write a CSV report
python -m PA.scripts.find_missing_practices \
  --bva "PA/data/lva/csv/Registration_data_bva.csv" \
  --lva "PA/data/lva/csv/Registration_data_lva.csv" \
  --practices "PA/data/lva/practices_missing.csv" \
  --output "PA/data/lva/csv/missing_companies.csv"
```

You can point the flags at another event folder if your `output_dir` differs.

---

## Feeding results back into the pipeline

1. Open the generated `missing_companies.csv` (or STDOUT list) and add the new companies to your practices catalogue (the file referenced by `input_files.practices`). Keep the `Company Name` and practice-type columns aligned with `practice_matching.company_column` and `practice_matching.practice_type_column` in your config.
2. Optionally adjust the match sensitivity via `practice_matching.match_threshold` if fuzzy matches are too strict or too loose.
3. Rerun the registration pipeline. During `combine_demographic_with_registration()`, the processor will:
   - Load the updated practices file.
   - Fill missing practice types via exact/fuzzy matching.
   - Emit any still-unmatched companies to `output/<missing_companies_output>` (name from `practice_matching`).

Iterate until the unmatched list is empty or acceptable.

---

## Configuration knobs (event config)

- `input_files.practices`: path to the practices catalogue the processor loads.
- `practice_matching.company_column`: column name in the practices file containing company names (default `Company Name`).
- `practice_matching.practice_type_column`: column with the practice type to inject (default `Main Type of Veterinary Practice`).
- `practice_matching.match_threshold`: fuzzy match score (0-100) required to accept a suggestion (default 95).
- `practice_matching.missing_companies_output`: filename written under `output_dir/output` with any still-unmatched companies.
- `practice_type_columns`: target columns in the registration data that receive filled practice types (current and past-year columns vary by show).

Keep these aligned with the columns in your practices CSV; otherwise, the processor will log warnings and skip filling.

---

## Tips

- Run the script after each new registration drop and before committing an updated practices catalogue.
- If the unmatched list explodes, check for leading/trailing spaces, punctuation variants, or renamed practice columns in the source files.
- The helper is idempotent—rerun it whenever you refresh registration outputs or the catalogue.
