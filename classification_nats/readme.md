# PII/PHI Detection and Classification Service (NATS Version)

## Overview

This application is a cloud-native Personal Identifiable Information (PII) and Protected Health Information (PHI) detection and classification service that processes documents through NATS messaging. It uses advanced NLP techniques and multiple language models to identify sensitive information across different languages and document types.

## Architecture

The service is designed as a distributed microservice architecture with the following key components:

- **NATS Messaging**: Asynchronous message processing using NATS JetStream
- **Language-Specific Engines**: Separate containers for different languages (EN, ES, DE, IT)
- **NLP Processing**: Uses spaCy models and Presidio for entity recognition
- **Risk Assessment**: Dual risk scoring system (GDPR and PII-specific)

## Features

- **Multi-language Support**: English, Spanish, German, and Italian
- **Document Processing**: Handles text, HTML, and various document formats
- **Risk Scoring**: Implements both GDPR and PII risk assessment models
- **Scalable Architecture**: Kubernetes-ready with health checks and version endpoints
- **Chunking Support**: Processes large documents by splitting into manageable chunks
- **Custom Entity Recognition**: Extensible entity detection with custom recognizers

## Risk Model Versions

### Version 1 (v1)
- Basic risk assessment with three levels (Non-Identifiable, Semi-Identifiable, Identifiable)
- NIST, DHS, and HIPAA category mappings

### Version 2 (v2)
- Enhanced dual risk scoring:
  - **GDPR Risk Score**: 5-level scale (Very Low to Very High)
  - **PII Risk Score**: 3-level scale (Low to High)
- Weighted scoring based on sensitivity, likelihood, impact, and importance
- Country-specific considerations

## Supported PII Types

The service detects 40+ PII types including:
- Personal identifiers (SSN, passport numbers, driver's licenses)
- Financial information (credit cards, bank accounts, IBAN)
- Contact information (email, phone, addresses)
- Demographic data (age, gender, race, marital status)
- Health-related identifiers
- Online identifiers (IP addresses, social media profiles)
- Country-specific identifiers (various national ID formats)

## Installation

### Prerequisites
- Docker and Docker Compose (for containerized deployment)
- Python 3.11+ (for local development)
- NATS Server (can be run via Docker)
- Kubernetes cluster (for production deployment)

### Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd classification_nats
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download required spaCy models:
```bash
python -m spacy download en_core_web_lg
python -m spacy download es_core_news_lg
python -m spacy download de_core_news_lg
python -m spacy download it_core_news_lg
```

5. Set up environment variables:
```bash
cp keys/.env.example keys/.env
# Edit keys/.env with your configuration
```

### Docker Deployment

Build and run language-specific containers:

```bash
# Build English engine
docker build -f Dockerfile_en -t pii-engine-en .

# Build Spanish engine
docker build -f Dockerfile_es -t pii-engine-es .

# Build German engine
docker build -f Dockerfile_de -t pii-engine-de .

# Build Italian engine
docker build -f Dockerfile_it -t pii-engine-it .
```

Run with Docker Compose:
```bash
docker-compose up -d
```

## Configuration

### Environment Variables

Key environment variables in `keys/.env`:

```env
# NATS Configuration
NAT_URL=nats://nats_server:4222
INPUT_STREAM=PII-TASKS
INPUT_SUBJECT=pii.tasks.started.>
OUTPUT_STREAM=PII-RESULTS
OUTPUT_SUBJECT=pii.results.completed.>

# Language Engine
LANGUAGE_ENGINE=en  # Options: en, es, de, it

# Local Environment Flag
LOCAL_ENV=1  # 0 for production, 1 for local

# Certificates (Production only)
CERTIFICATES_PATH=/path/to/certs
```

### NATS Streams Configuration

The service creates two JetStream streams:
- **Input Stream**: Receives document processing requests
- **Output Stream**: Publishes processing results

## Usage

### Message Format

#### Input Message
```json
{
  "batchId": "batch-123",
  "source": {
    "uri": "file:///path/to/document.txt"
  },
  "state": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

The input file should contain:
```json
{
  "documents": [
    {
      "id": "doc-001",
      "content": "John Smith's SSN is 123-45-6789",
      "metadata": {}
    }
  ],
  "score": 0.4,
  "weights": [],
  "version": "v2"
}
```

#### Output Message
```json
{
  "batchId": "batch-123",
  "source": {...},
  "state": {
    "status": "COMPLETED",
    "timestamp": "2024-01-01T00:00:10Z"
  },
  "result": {
    "status": {"code": 200, "message": "Success"},
    "data": [
      {
        "document_id": "doc-001",
        "entities": [
          {
            "entity_type": "PERSON",
            "pii_text": "John Smith",
            "start": 0,
            "end": 10,
            "score": 0.95,
            "risk_level_gdpr": 9,
            "risk_level_pii": 9
          },
          {
            "entity_type": "US_SSN",
            "pii_text": "123-45-6789",
            "start": 20,
            "end": 31,
            "score": 0.99,
            "risk_level_gdpr": 9,
            "risk_level_pii": 9
          }
        ],
        "risk_score_mean_gdpr": 9,
        "risk_score_mean_pii": 9,
        "detection_count": 2
      }
    ]
  }
}
```

### Running the Service

1. Start NATS server:
```bash
docker run -d --name nats-server -p 4222:4222 nats:latest -js
```

2. Run the PII detection service:
```bash
python endpoint_classification_nats.py
```

## API Endpoints

### Health Check
- **Subject**: `pii.app.health.check.{hostname}`
- **Response**: Service health status

### Version Check
- **Subject**: `pii.app.version`
- **Response**: Application version information

## Monitoring and Logging

- Logs are written to `logs/debug.log`
- Console output with color-coded log levels
- Detailed processing metrics for each document
- Memory and performance tracking

## Performance Considerations

- Documents larger than 499,999 characters are automatically chunked
- Minimum document requirements: 100 characters or 10 words
- Concurrent processing with configurable workers
- Message acknowledgment with heartbeat mechanism (10-minute timeout)

## Security

- TLS/SSL support for NATS connections in production
- Certificate-based authentication
- No browser storage APIs used (for security in web environments)
- Sanitization of detected PII in output

## Troubleshooting

### Common Issues

1. **Language not detected**: Ensure spaCy models are installed for the target language
2. **NATS connection errors**: Verify NATS server is running and accessible
3. **Memory issues**: Adjust chunk size for large documents
4. **SSL certificate errors**: Check certificate paths and permissions

### Debug Mode

Enable detailed logging:
```python
set_up_logging(console_log_level="debug", logfile_log_level="debug")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request



## Support

For issues and questions:
- GitHub Issues: [repository-issues-url]
- Documentation: [documentation-url]