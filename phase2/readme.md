# Phase 2 - Event Visitor Classification System

This directory contains the implementation of an event visitor classification system that categorizes attendees based on their profiles and behaviors. The system uses various LLM models (including LLama, Phi3, and DeepSeek) to classify visitors into different purchasing intention categories.

## Overview

The project aims to classify event visitors into five main categories:
1. **Networking** - Focused on building professional relationships
2. **Learning** - Motivated by educational opportunities
3. **Searching for info on products and vendors** - Exploring solutions without immediate purchase intent
4. **Early Purchasing Intention** - Actively engaged in the sourcing process
5. **High Purchase Intention** - At final stages of purchasing journey

## Project Structure

### Data Processing Notebooks
- **`Data.ipynb`** - Main data processing pipeline for registration and demographic data
- **`Data-Visitors-two-years.ipynb`** - Analysis of visitors attending events in both 2024 and 2025
- **`Data for Classification_new_Classes.ipynb`** - Prepares data for the new classification system

### Classification Notebooks
- **`Classification_new_Classes.ipynb`** - Implements classification using LLama models with examples
- **`Classification_via_prompt.ipynb`** - Alternative classification approach using prompt engineering

### Evaluation
- **`evaluation.ipynb`** - Comprehensive evaluation of classification results
- **`evaluation_initial.ipynb`** - Initial evaluation metrics and visualizations

### Core Components
- **`classes.py`** - Contains prompt template classes for different LLM models:
  - `Deep_Seek_PromptTemplate`
  - `Phi3_PromptTemplate`
  - `LLama_PromptTemplate`
- **`llama_class.py`** - Standalone script for running LLama classification

## Data Flow

1. **Registration Data Processing**
   - Combines registration data from multiple events
   - Extracts relevant features (job title, company size, days since registration)
   - Handles data from shows: BDAWL, CEEL, CCSEL, DCWL, DL (2024-2025)

2. **Demographic Data Integration**
   - Merges questionnaire responses with registration data
   - Separates "VIP questions" (key decision-making questions) from regular questions
   - Incorporates seminar attendance data from badge scans

3. **Profile Generation**
   - Creates comprehensive visitor profiles combining all data sources
   - Formats profiles for LLM classification

## Key Features

### Multi-Model Support
The system supports multiple LLM models:
- LLama 3.2 (3B parameters)
- LLama 3 (8B parameters)
- Phi 3.5
- DeepSeek R1 (1.5B)
- Qwen 2.5

### Classification Approaches
1. **With Examples** - Provides example profiles for each category
2. **Without Examples** - Relies on category descriptions only
3. **Confidence Scoring** - Returns confidence levels (High/Mid/Low)
4. **Top-K Ranking** - Provides ranked list of all categories

### Evaluation Metrics
- Category distribution analysis
- Confidence score distribution
- Pie chart visualizations with color-coded categories

## Usage

### Prerequisites
Install required dependencies:
```bash
pip install -r requirements.txt
```

### Running Classification

1. **Prepare Data**
   ```python
   # Run Data.ipynb to process registration and demographic data
   # This creates output files in the output/ directory
   ```

2. **Run Classification**
   ```python
   # Using notebook approach
   # Open Classification_new_Classes.ipynb and run all cells
   
   # Or use the standalone script
   python llama_class.py
   ```

3. **Evaluate Results**
   ```python
   # Open evaluation.ipynb to analyze classification results
   # Generates visualizations and metrics
   ```

## Output Structure

The classification results are saved with timestamps:
- `classification/llama3_8B_YYYY-MM-DD_HH-MM-SS.json` - With examples
- `classification/llama3_8B_noexamples_YYYY-MM-DD_HH-MM-SS.json` - Without examples

Each result contains:
```json
{
  "SHOWREF_BADGEID": {
    "category": "classification_result",
    "confidence": "confidence_level",
    "top_k": {
      "1": "most_likely_category",
      "2": "second_most_likely",
      ...
    }
  },
  "input": "original_profile_text"
}
```

## Data Privacy Note

The system processes visitor data including:
- Email domains (emails are anonymized to domains only)
- Company information
- Job titles
- Event attendance patterns

All personal identifiable information should be handled according to data protection regulations.

## Model Configuration

Models are configured with:
- Temperature: 0.3-0.5 (for consistent outputs)
- Context window: 4096-16000 tokens
- JSON output format for structured results

## Future Improvements

1. Integration with real-time badge scanning systems
2. Multi-language support for international events
3. Advanced analytics dashboard
4. API endpoint for real-time classification
5. Automated retraining based on post-event feedback