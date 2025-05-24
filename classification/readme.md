# PII/PHI Detection and Classification System

## Overview

This application is a sophisticated Personal Identifiable Information (PII) and Protected Health Information (PHI) detection and classification system built with Python. It uses advanced Natural Language Processing (NLP) techniques and machine learning models to identify, classify, and assess the risk levels of sensitive information in various document types.

## Key Features

- **Multi-language Support**: Supports English (EN), Spanish (ES), German (DE), and Italian (IT)
- **Risk Assessment Models**: Implements both GDPR and PII risk scoring frameworks (v1 and v2)
- **Document Processing**: Handles various file types including HTML, plain text, and more
- **Scalable Architecture**: Built with FastAPI for high-performance async processing
- **Docker Support**: Fully containerized with language-specific analysis engines
- **Advanced NLP**: Uses spaCy models and Microsoft Presidio for entity recognition
- **Custom Entity Recognition**: Includes specialized recognizers for various PII types

## Architecture

### Core Components

1. **Classification Engine** (`endpoint_classification.py`)
   - Main API endpoint for document processing
   - Orchestrates the PII detection workflow
   - Manages job queuing and status tracking

2. **PII Codex Module** (`pii_codex/`)
   - Core library for PII detection and risk assessment
   - Contains models, services, and utilities for analysis
   - Implements risk mapping based on GDPR, NIST, HIPAA, and DHS categories

3. **Language-Specific Analyzers**
   - Separate Docker containers for each supported language
   - Custom recognizers for language-specific patterns
   - Optimized NLP models for each language

### Risk Assessment Framework

The system uses two risk assessment versions:

- **Version 1**: Basic risk classification (Non-Identifiable, Semi-Identifiable, Identifiable)
- **Version 2**: Advanced GDPR and PII risk scoring with multiple factors:
  - Sensitivity scores (1-5)
  - Likelihood scores (1-5)
  - Impact scores (1-5)
  - Importance weighting
  - Calculated risk scores

## Installation

### Using Docker (Recommended)

1. **Build the proxy container**:
```bash
docker build -f Dockerfile -t pii-classification-proxy .
```

2. **Build language-specific containers**:
```bash
docker build -f Dockerfile_en -t pii-classification-en .
docker build -f Dockerfile_es -t pii-classification-es .
docker build -f Dockerfile_de -t pii-classification-de .
docker build -f Dockerfile_it -t pii-classification-it .
```

3. **Run with Docker Compose**:
```bash
docker-compose up
```

### Local Development

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Download required spaCy models**:
```bash
python -m spacy download en_core_web_lg
python -m spacy download es_core_news_lg
python -m spacy download de_core_news_lg
python -m spacy download it_core_news_lg
```

3. **Set up environment variables**:
```bash
cp keys/.env.example keys/.env
# Edit keys/.env with your configuration
```

## API Endpoints

### Main Processing Endpoint
- **POST** `/process` - Process documents for PII detection
  - Request body:
    ```json
    {
      "documents": [...],
      "weights": [],
      "score": 0.4,
      "version": "v2",
      "ocr": 0
    }
    ```

### Text Processing Endpoint
- **POST** `/process/process_text` - Process raw text
  - Request body:
    ```json
    {
      "text": "Sample text...",
      "weights": [],
      "score": 0.4,
      "filter_detection": true
    }
    ```

### Health Check
- **GET** `/health-check` - Check service status

### Job Status
- **GET** `/work/status` - Get status of processing jobs

## Supported PII Types

The system detects various PII types including:

- Personal identifiers (SSN, passport numbers, driver's licenses)
- Financial information (credit cards, bank accounts, IBAN, SWIFT codes)
- Contact information (email, phone, addresses)
- Demographic data (age, gender, race, marital status)
- Health insurance IDs
- Professional licenses
- Social network profiles
- Biometric data (height, weight)
- Country-specific identifiers (NHS, NIE, DNI, etc.)

## Configuration

### Risk Model Configuration
The risk model mappings are defined in CSV files:
- `v1/pii_type_mappings.csv` - Version 1 mappings
- `v2/pii_gdpr_mapping.csv` - Version 2 with GDPR categories

### Language Configuration
Each language has specific configuration in `pii_codex/config.py`:
- Supported entities
- NLP model specifications
- Custom recognizers

### Docker Configuration
- Proxy routes: `config/config_docker.json`
- Environment variables: Set in Dockerfile or docker-compose.yml

## Custom Recognizers

The system includes custom recognizers for:
- SWIFT codes (using tekswift library)
- Social network profiles (regex-based)
- Age patterns
- Gender and sexual orientation
- Occupations and job titles
- Physical attributes (height, weight)
- Country-specific patterns (zip codes, phone numbers)

## Processing Flow

1. **Document Ingestion**: Receives documents via API
2. **Text Extraction**: Extracts text based on MIME type
3. **Language Detection**: Determines document language
4. **Chunking**: Splits large documents into manageable chunks
5. **PII Detection**: Runs NLP models and custom recognizers
6. **Risk Assessment**: Calculates risk scores based on detected entities
7. **Post-processing**: Filters and validates results
8. **Response Generation**: Returns structured JSON with findings

## Performance Considerations

- **Document Size**: Automatically chunks documents larger than 499,999 characters
- **Parallel Processing**: Uses async processing for better performance
- **Worker Configuration**: Configurable number of workers per language engine
- **Memory Management**: Implements cleanup after processing to prevent memory leaks

## Security Features

- PII anonymization capabilities
- Configurable score thresholds
- Post-processing filters to reduce false positives
- Support for custom weight configurations
- Sanitized text output options

## Monitoring and Logging

- Comprehensive logging at multiple levels
- Job tracking with unique IDs
- Processing status updates
- Error tracking with stack traces
- Performance metrics for timed operations

## Development

### Adding New Languages
1. Create a new Dockerfile (e.g., `Dockerfile_fr`)
2. Add language configuration in `config.py`
3. Create custom recognizers in `pii_codex/services/analyzers/`
4. Update the configuration files

### Adding New PII Types
1. Update the risk mapping CSV files
2. Add recognizer patterns
3. Update the PIIType enum
4. Test with sample data

## Testing

The application includes test configurations accessible via environment variables:
- Set `IS_TEST=1` to use test configurations
- Test-specific mappings available for validation

## License and Compliance

This system is designed to help with GDPR, HIPAA, and other privacy regulation compliance. Always ensure your use case aligns with local privacy laws and regulations.

---

For more information or support, please refer to the inline documentation or contact the development team.