# BVA Data Processing Notebooks

This folder contains Jupyter notebooks for processing and analyzing data from veterinary conferences: BVA (British Veterinary Association) and LVA (London Vet Show) events for 2024 and 2025.

## Overview

The notebooks handle registration data, demographic information, session data, and scan data to create comprehensive datasets for analysis and personalized attendee experiences.

## Notebooks

### 1. `BVA_Data.ipynb`
**Purpose**: Main data processing pipeline for registration and demographic data

**Key Functions**:
- Loads and processes registration data from JSON files for BVA 2024/2025 and LVA 2024
- Cleans and standardizes badge types (filters for "Delegate" and "Delegate - Group" only)
- Identifies returning visitors (attended both 2024 and 2025 events)
- Extracts email domains and calculates days since registration
- Processes demographic questionnaire responses (job roles, specializations, organization types)
- Creates consolidated datasets linking registration and demographic data
- Generates output files for downstream analysis

**Key Outputs**:
- Registration data CSVs (separate files for each event year)
- Demographic data CSVs
- JSON files with formatted registration and demographic data
- Combined registration + demographic data files

### 2. `bva_2025.ipynb`
**Purpose**: Enriches HPI (High Priority Individual) data with registration details

**Key Functions**:
- Loads HPI data containing visitor segments and interests
- Merges with 2025 registration data to add contact information
- Standardizes phone number formats (adds '+' prefix)
- Creates enriched dataset for targeted marketing/outreach

**Key Outputs**:
- `hpi_extended.csv` - Enhanced HPI data with full contact details

### 3. `scan_data_bva.ipynb`
**Purpose**: Processes seminar scan data to track session attendance

**Key Functions**:
- Loads seminar scan data and reference files
- Maps short seminar codes to full seminar names
- Creates standardized keys for joining with session data
- Identifies which registered attendees attended which seminars
- Validates badge IDs against registration data

**Key Outputs**:
- `scan_bva_past.csv` - Processed BVA 2024 scan data
- `scan_lva_past.csv` - Processed LVA 2024 scan data

### 4. `session_data.ipynb`
**Purpose**: Processes and enriches session/seminar information

**Key Functions**:
- Loads session export data for all events
- Filters out placeholder sessions (e.g., "TBC session")
- Extracts and processes session streams/categories
- Uses OpenAI GPT-4 to generate descriptive summaries of each stream category
- Maps sponsor abbreviations to full names
- Creates consolidated session datasets

**Key Outputs**:
- Filtered session CSVs for each event
- `streams.json` - Dictionary of stream categories with AI-generated descriptions
- Cleaned session data with standardized sponsor names

## Data Flow

1. **Registration & Demographics** → `BVA_Data.ipynb` processes raw JSON data into structured CSVs
2. **Session Information** → `session_data.ipynb` cleans and enriches session metadata
3. **Attendance Tracking** → `scan_data_bva.ipynb` links attendees to sessions they attended
4. **VIP Processing** → `bva_2025.ipynb` creates targeted lists for high-value attendees

## Key Data Points Tracked

- **Registration**: Badge ID, email, company, job title, country, registration date
- **Demographics**: Job role, practice specialization, organization type
- **Attendance**: Which sessions/seminars each attendee participated in
- **Returning Visitors**: Flags for attendees who came to previous year's events
- **Segments**: HPI classifications for targeted engagement

## Usage Notes

- All notebooks use pandas for data manipulation
- Date calculations assume event dates: BVA 2025 (June 12, 2025), BVA 2024 (June 12, 2024)
- Data privacy: Email addresses and personal information are processed but should be handled securely
- The notebooks are designed to run sequentially as listed above

## Dependencies

- pandas
- json
- warnings
- logging
- python-dotenv (for session_data.ipynb)
- langchain_openai (for AI-powered stream descriptions)
- OpenAI API key required for stream description generation