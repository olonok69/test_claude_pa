# CSM LLM Application - HPI (High Purchase Intention)

## Overview

The CSM (Closer Still Media) LLM Application is a comprehensive visitor classification system designed to analyze and categorize technology event attendees based on their purchasing intentions and engagement patterns. The application leverages multiple Large Language Models (LLMs) including Llama 3.1, GPT-4o-mini, and o3-mini to classify visitors into distinct behavioral categories.

## Key Features

### 🎯 Visitor Classification
The system classifies event visitors into 5 primary categories:
- **Networking**: Focused on building professional relationships
- **Learning**: Seeking educational opportunities and industry insights
- **Searching**: Gathering information on products and vendors
- **Early Purchasing Intention**: Actively engaged in sourcing processes
- **High Purchase Intention**: At final stages of purchasing journey

### 🤖 Multi-Model Support
- **Llama 3.1 (11B)**: Local Ollama deployment
- **GPT-4o-mini**: Azure OpenAI integration
- **o3-mini**: Advanced reasoning model
- **Batch Processing**: Efficient handling of large datasets

### 📊 Data Processing Pipeline
- Registration data preprocessing
- Demographic data analysis
- Seminar attendance tracking
- Multi-year visitor comparison (2024-2025)
- Badge scan integration

## Architecture

### Docker Environment
```dockerfile
FROM python:3.11-slim
# Multi-service setup with Ollama containers
# GPU support for model inference
# Streamlit web interface
```

### Core Components

#### 1. Web Interface (`app.py`, `main.py`)
- Streamlit-based authentication system
- Multi-page application structure
- Session management and logging

#### 2. Classification Engine
- **Individual Classification** (`pages/12_1️⃣_hpi_one.py`)
- **Batch Processing** (`pages/13_👨‍👧‍👧_hpi_batch.py`)
- **Configuration Management** (`pages/1_🖥️_configuration.py`)

#### 3. Data Processing (`src/`)
- **Data Creation** (`create_dataframes.py`)
- **Visitor Inference** (`inference_visitors.py`, `inference_visitors_batch.py`)
- **Data Transformation** (`transform.py`)
- **Storage Management** (`storage.py`)

#### 4. Model Integration (`src/work_gemini.py`)
- LLM initialization and configuration
- Prompt template management
- Inference orchestration
- Batch API integration

## Configuration

### Model Configuration (`conf/config.yaml`)
```yaml
steps:
  - name: "Llama3.1:11B"
    active: true
    parameters:
      model: "llama3.1:latest"
      temperature: 0.5
      base_url: ["http://localhost:11434"]
  - name: "Gpt4o-Mini"
    active: true
    parameters:
      model: "gpt-4o-mini"
      temperature: 0.5
```

### Classification Categories (`src/conf.py`)
Detailed nomenclature definitions for each visitor category with specific behavioral patterns and decision-making criteria.

## Data Flow

### 1. Data Ingestion
- Azure Blob Storage integration
- Registration data from multiple events
- Demographic questionnaire responses
- Badge scan activity from seminars

### 2. Data Preprocessing
- Email domain extraction
- Date calculations (days since registration)
- Multi-year visitor identification
- Seminar attendance enrichment

### 3. Classification Process
- Profile concatenation (registration + demographic + seminar data)
- LLM prompt generation using custom templates
- Model inference with confidence scoring
- Results transformation and storage

### 4. Output Generation
- CSV exports with classification results
- JSON data for further processing
- Web interface visualization

## Key Classes and Templates

### LLama_PromptTemplate (`src/classes.py`)
Sophisticated prompt engineering system that:
- Generates category-specific examples
- Creates structured classification prompts
- Handles different model formats (Llama, GPT, etc.)
- Includes confidence scoring mechanisms

### Visitor Classification Schema
```python
class Visitor_Classification(BaseModel):
    category: str
    ranked_categories: List[str]
    certainty: str
```

## Deployment

### Docker Compose Setup
- **ollama1/ollama2**: GPU-enabled model servers
- **nginx**: Load balancing (optional)
- **Streamlit App**: Web interface

### Environment Requirements
- Python 3.11+
- CUDA-compatible GPU (for local models)
- Azure OpenAI API access
- Google Cloud credentials (Vertex AI)

## Installation

1. **Clone Repository**
```bash
git clone <repository-url>
cd app
```

2. **Environment Setup**
```bash
pip install -r requirements.txt
```

3. **Configuration**
- Set up `.env` file in `keys/` directory
- Configure Azure OpenAI credentials
- Set up Google Cloud service account

4. **Docker Deployment**
```bash
docker-compose up -d
```

5. **Run Application**
```bash
streamlit run main.py
```

## Usage

### Individual Classification
1. Navigate to "HPI One" page
2. Select desired model (Llama3.1, GPT-4o-mini, o3-mini)
3. Choose visitor profile from processed data
4. Review classification results with confidence scores

### Batch Processing
1. Access "HPI Batch" page
2. Upload CSV file with visitor profiles
3. Select model for batch inference
4. Monitor processing progress
5. Download results as CSV

### Configuration Management
- Modify classification nomenclature
- Adjust model parameters
- Update prompt templates

## Data Sources

### Registration Data
- Event registration information
- Contact details and company information
- Badge types and access levels

### Demographic Data
- Questionnaire responses
- Job functions and decision-making power
- Areas of interest and company size

### Seminar Data
- Badge scan activities
- Session attendance patterns
- Multi-year participation tracking

## Output Formats

### Classification Results
- Visitor category assignment
- Confidence levels (Very certain, Fairly certain, etc.)
- Ranked category preferences (1-5)
- Supporting demographic information

### Export Options
- CSV files for analysis
- JSON for programmatic access
- Web interface visualization

## Security Features

- Streamlit authentication system
- Role-based access control
- Secure credential management
- Data privacy compliance

## Monitoring and Logging

- Comprehensive logging system
- Processing progress tracking
- Error handling and recovery
- Performance metrics collection

## Neo4j Integration

Optional graph database integration for:
- Relationship mapping between visitors
- Stream-based categorization
- Advanced analytics and insights

## API Integration

### Azure OpenAI
- Batch processing capabilities
- Cost-effective inference
- Enterprise-grade security

### Google Vertex AI
- Advanced model access
- Embeddings generation
- Scalable infrastructure

## Development Notes

- Modular architecture for easy extension
- Comprehensive error handling
- Session state management
- Responsive web interface
- Docker containerization for deployment

## Contributing

The application follows standard Python development practices with:
- Type hints for better code documentation
- Comprehensive logging for debugging
- Modular design for maintainability
- Configuration-driven behavior

