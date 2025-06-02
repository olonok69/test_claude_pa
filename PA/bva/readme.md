# BVA Event Analytics and Personal Agenda System

This repository contains a comprehensive data analysis and recommendation system for the British Veterinary Association (BVA) events, including both BVA Live and Large Veterinary Show (LVS) conferences. The system processes registration data, demographic information, session attendance, and generates personalized session recommendations using machine learning and graph database technologies.

## 📋 Overview

The BVA system is designed to:
- Process and analyze visitor registration and demographic data
- Track session attendance through scan data
- Build a knowledge graph in Neo4j to represent relationships between visitors, sessions, and streams
- Generate personalized session recommendations using semantic similarity and collaborative filtering
- Apply business rules to filter recommendations based on visitor profiles

## 🗂️ Project Structure

### Data Processing Pipeline (Notebooks 1-2)

#### `1_BVA_Data.ipynb` - Registration and Demographic Data Processing
**Purpose**: Core data preprocessing for visitor registration and demographic information

**Key Features**:
- Processes JSON registration data for BVA 2024/2025 and LVS 2024
- Handles demographic questionnaire responses
- Creates visitor profiles with job roles, practice specializations, and organization types
- Identifies returning visitors who attended previous events
- Generates clean CSV outputs for downstream processing

**Required Files**:
- `registration_BVA24_BVA25.json`
- `registration_LVS24.json` 
- `demographics_BVA24_BVA25.json`
- `demographics_LVS24.json`

**Key Outputs**:
- `df_reg_demo_this.csv` - Current year visitor profiles
- `df_reg_demo_last_bva.csv` - Previous BVA attendees
- `df_reg_demo_last_lva.csv` - Previous LVS attendees

#### `2_scan_data_bva.ipynb` - Session Attendance Processing
**Purpose**: Processes QR code scan data to track which sessions visitors attended

**Key Features**:
- Merges scan data with session reference information
- Links attendance records to visitor demographic data
- Creates attendance history for recommendation engine

**Required Files**:
- `BVA24_session_export.csv`
- `LVA24_session_export.csv`
- Seminar scan reference files

### Neo4j Graph Database Setup (Notebooks 1-5 Neo4j series)

#### `1_Neo4J_dva_registration.ipynb` - Visitor Node Creation
**Purpose**: Loads visitor registration data into Neo4j as nodes

**Key Features**:
- Creates `Visitor_this_year`, `Visitor_last_year_bva`, and `Visitor_last_year_lva` nodes
- Establishes the foundation for the knowledge graph

#### `2_Neo4J_dva_sessions.ipynb` - Session and Stream Management
**Purpose**: Creates session nodes and stream relationships

**Key Features**:
- Loads session data for current and past years
- Creates `Stream` nodes with AI-generated descriptions
- Establishes `HAS_STREAM` relationships between sessions and topics

#### `3_Neo4J_stream_to_job.ipynb` - Job Role Relationships
**Purpose**: Creates relationships between job roles and relevant streams

**Key Features**:
- Maps visitor job roles to applicable content streams
- Uses predefined mapping file: `job_to_stream.csv`

#### `4_Neo4J_stream_to_spezialization.ipynb` - Practice Specialization Links
**Purpose**: Links practice specializations to relevant content streams

**Key Features**:
- Maps practice types (equine, small animal, mixed, etc.) to content streams
- Uses mapping file: `spezialization_to_stream.csv`

#### `5_Neo4J_dva_scan_data.ipynb` - Attendance Relationships
**Purpose**: Creates visitor-session attendance relationships

**Key Features**:
- Links visitors to sessions they attended via `attended_session` relationships
- Creates `Same_Visitor` relationships for returning attendees
- Enables collaborative filtering recommendations

### Session Data Processing (Notebook 3)

#### `3_session_data.ipynb` - Session Content Processing
**Purpose**: Processes and enriches session information

**Key Features**:
- Cleans and standardizes session titles and descriptions
- Maps sponsor abbreviations to full company names
- Generates AI-powered stream descriptions using OpenAI GPT
- Creates session embeddings for semantic similarity

**AI Integration**:
- Uses OpenAI API to generate comprehensive stream descriptions
- Each stream gets a 3-4 sentence description based on associated sessions

### Recommendation Engine (Notebooks 6-9)

#### `6_Propose Sessions-v4.ipynb` - Advanced Recommendation System
**Purpose**: Main recommendation engine with comprehensive business rule implementation

**Key Features**:
- **Collaborative Filtering**: Recommends based on similar visitor behavior
- **Content-Based Filtering**: Uses semantic similarity between sessions
- **Business Rule Engine**: Implements complex filtering rules:
  - Practice type restrictions (equine/mixed vs small animal)
  - Job role limitations (vet vs nurse content)
  - Stream relationship filtering
- **Embedding-Based Similarity**: Uses SentenceTransformers for semantic matching
- **Overlap Detection**: Identifies scheduling conflicts

**Business Rules**:
1. **Practice Type Rules**:
   - Equine/Mixed practices: Exclude small animal, feline, exotics content
   - Small Animal practices: Exclude equine, farm, large animal content

2. **Job Role Rules**:
   - Veterinarians: Exclude nursing-specific content
   - Nurses: Limit to nursing, wellbeing, welfare content
   - Business roles: No content restrictions

3. **Quality Filters**:
   - Minimum similarity thresholds
   - Stream relationship requirements
   - Scheduling conflict detection

#### `7_Create_embeddings.ipynb` - Semantic Embeddings
**Purpose**: Pre-computes semantic embeddings for all sessions

**Key Features**:
- Uses SentenceTransformers to create vector representations
- Incorporates session titles, descriptions, and stream context
- Stores embeddings in Neo4j for fast similarity computation

#### `8_propose_session_raw.ipynb` - Optimized Recommendation Engine
**Purpose**: High-performance version of the recommendation system

**Key Features**:
- Caching mechanisms for improved performance
- Parallel processing for similarity calculations
- Batch processing capabilities
- Memory-efficient embedding handling

#### `9_propose_session_and_llm_filter.ipynb` - LLM-Enhanced Filtering
**Purpose**: Combines traditional rules with AI-powered filtering

**Key Features**:
- Integrates Azure OpenAI for intelligent rule application
- Flexible rule configuration system
- Hybrid approach: rules + AI validation

### Supporting Utilities

#### `mock_recomendations.ipynb` - Testing Framework
**Purpose**: Provides mock data for testing without Neo4j dependency

**Key Features**:
- Sample session data for development
- Testing scenarios for different visitor types
- Standalone recommendation validation

## 🛠️ Technical Stack

### Core Technologies
- **Python 3.11+** - Primary programming language
- **Neo4j** - Graph database for relationship modeling
- **SentenceTransformers** - Semantic similarity computation
- **scikit-learn** - Machine learning utilities
- **pandas** - Data manipulation and analysis

### AI/ML Components
- **OpenAI GPT** - Content generation and rule processing
- **Azure OpenAI** - Enterprise AI integration
- **Sentence Transformers** - Text embedding generation
- **Collaborative Filtering** - User behavior analysis

### Data Processing
- **JSON/CSV Processing** - Multi-format data ingestion
- **Text Preprocessing** - Content cleaning and standardization
- **Feature Engineering** - Visitor profile enhancement

## 📊 Data Flow

```
Raw Data (JSON/CSV)
    ↓
Registration & Demographic Processing (Notebook 1)
    ↓
Session & Scan Data Processing (Notebooks 2-3)
    ↓
Neo4j Graph Construction (Notebooks 1-5 Neo4j series)
    ↓
Embedding Generation (Notebook 7)
    ↓
Recommendation Engine (Notebooks 6, 8, 9)
    ↓
Personalized Session Recommendations
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Neo4j Database (local or cloud)
- OpenAI/Azure OpenAI API access
- Required Python packages (see individual notebooks)

### Setup Steps
1. **Install Dependencies**:
   ```bash
   pip install pandas numpy scikit-learn sentence-transformers neo4j openai langchain
   ```

2. **Configure Neo4j**:
   - Update connection parameters in Neo4j notebooks
   - Ensure database is running and accessible

3. **Set API Keys**:
   - Create `.env` file with OpenAI/Azure credentials
   - Configure API endpoints and deployment names

4. **Run Data Pipeline**:
   - Execute notebooks in numerical order (1 → 2 → 3 → etc.)
   - Ensure data files are available in `data/bva/` directory

### Quick Start Example
```python
# Generate recommendations for a visitor
from recommend_sessions import get_recommendations_and_filter

result = get_recommendations_and_filter(
    badge_id="VISITOR123",
    min_score=0.5,
    max_recommendations=10,
    use_neo4j=True,
    use_langchain=True
)

print(f"Found {len(result['filtered_recommendations'])} recommendations")
```

## 🔧 Configuration

### Business Rules Configuration
Rules can be customized via configuration dictionaries:

```python
custom_rules = {
    "equine_mixed_exclusions": ["exotics", "feline", "small animal"],
    "small_animal_exclusions": ["equine", "farm", "large animal"],
    "vet_exclusions": ["nursing"],
    "nurse_streams": ["nursing", "wellbeing", "welfare"]
}
```

### Performance Tuning
- **Embedding Cache**: Pre-compute and store embeddings
- **Batch Processing**: Process multiple visitors simultaneously
- **Similarity Thresholds**: Adjust for precision vs recall
- **Neo4j Indexing**: Add indexes for frequently queried properties

## 📈 Key Metrics and Outputs

### Recommendation Quality Metrics
- **Similarity Scores**: Semantic similarity between sessions (0.0-1.0)
- **Business Rule Compliance**: Percentage passing all filters
- **Coverage**: Percentage of visitors receiving recommendations
- **Diversity**: Variety of recommended streams and topics

### Output Formats
- **JSON**: Structured recommendation data with metadata
- **CSV**: Tabular format for analysis and reporting
- **Neo4j Relationships**: Graph-based recommendation storage

## 🔍 Business Intelligence Features

### Visitor Segmentation
- Job role analysis (Vets, Nurses, Business roles)
- Practice type distribution (Small Animal, Equine, Mixed)
- Geographic analysis by country/region
- Return visitor identification and behavior

### Content Analytics
- Popular session identification
- Stream engagement analysis
- Sponsor content performance
- Theatre utilization metrics

### Recommendation Analytics
- Algorithm performance comparison
- A/B testing framework for rule variations
- Personalization effectiveness measurement

## 📝 Usage Examples

### Generate Recommendations for Single Visitor
```python
# Process single visitor
visitor_recs = get_recommendations_and_filter(
    badge_id="ABC123",
    min_score=0.6,
    max_recommendations=8,
    visitor_data=visitor_df
)
```

### Batch Process Multiple Visitors
```python
# Process all visitors
all_visitors = df['BadgeId'].unique()
batch_results = {}

for visitor_id in all_visitors:
    batch_results[visitor_id] = get_recommendations_and_filter(
        badge_id=visitor_id,
        min_score=0.5,
        max_recommendations=10
    )
```

### Custom Rule Implementation
```python
# Define custom filtering rule
def exclude_sponsored_sessions(visitor, sessions):
    filtered = [s for s in sessions if s.get('sponsored_session') != 'True']
    return filtered, ['excluded_sponsored_content']

# Apply custom rule
session_filter = SessionFilter()
session_filter.add_rule_implementation('no_sponsors', exclude_sponsored_sessions)
```

## 🐛 Troubleshooting

### Common Issues
1. **Neo4j Connection**: Verify database is running and credentials are correct
2. **Missing Data**: Ensure all required input files are present
3. **API Limits**: Monitor OpenAI API usage and rate limits
4. **Memory Usage**: Large datasets may require batch processing
5. **Embedding Errors**: Check SentenceTransformers model availability

### Performance Optimization
- Use caching for frequently accessed data
- Implement parallel processing for large datasets
- Optimize Neo4j queries with appropriate indexes
- Consider using faster embedding models for production

## 📚 Additional Resources

### Documentation
- **Neo4j Cypher**: Query language documentation
- **SentenceTransformers**: Model selection and usage
- **OpenAI API**: Integration best practices

### Data Sources
- BVA Event Management System
- Registration platform exports
- QR code scanning system data
- Demographic survey responses

---
