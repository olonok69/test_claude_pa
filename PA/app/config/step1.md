# Registration and Demographic Data Processor

A Python application for processing event registration data, identifying returning visitors, and preparing datasets for further analysis.

## Overview

This tool processes JSON registration data files for events, identifies returning visitors across multiple events, and prepares cleaned datasets for analysis. Key features include:

- Processing registration data from multiple events (BVA and LVS)
- Identifying returning visitors across years and events
- Calculating days between registration and event dates
- Extracting email domains for organization analysis
- Normalizing and cleaning registration data
- Saving processed data in CSV format for analysis

## Requirements

- Python 3.7+
- Required packages: pandas, pyyaml

Install dependencies:

```bash
pip install pandas pyyaml
```

## Usage

1. Create a YAML configuration file (see `config.yaml` example)
2. Run the script:

```bash
python data_processor.py -c config.yaml
```

## Configuration

The script is configured using a YAML file that specifies:

- Input file paths
- Output directory
- Event dates
- Valid badge types
- Shows for the current year
- Questions to keep for demographic analysis

Example configuration:

```yaml
# Input file paths
input_files:
  bva_registration: "data/bva/20250428_registration_BVA24_BVA25.json"
  lvs_registration: "data/bva/20250428_registration_LVS24.json"

# Output directory
output_dir: "data/bva"

# Event dates
event_date_this_year: "2025-06-12"
event_date_last_year: "2024-06-12"

# Valid badge types
valid_badge_types:
  - "Delegate"
  - "Delegate - Group"

# Shows for this year (for filtering)
shows_this_year:
  - "BVA2025"
```

## Output Files

The script generates several CSV files in the specified output directory:

- `Registration_data_bva_25_only_valid.csv`: Current year's BVA registration data
- `Registration_data_bva_24_only_valid.csv`: Last year's BVA registration data
- `Registration_data_bva_24_25_only_valid.csv`: Data for visitors who attended both BVA events
- `Registration_data_lva_24_25_only_valid.csv`: Data for visitors who attended LVS last year and BVA this year

## Process Flow

1. Load JSON registration data from input files
2. Clean and preprocess data (remove duplicates, handle missing values)
3. Split data by event and year
4. Identify returning visitors across years and events
5. Add badge history information for returning visitors
6. Calculate days until event for all records
7. Flag returning visitors in current year data
8. Select relevant columns and save final processed data

## Logging

The script logs all operations to both stdout and a log file. Logging level and file can be configured in the YAML file.