# Strategic AI CSM Applications

A comprehensive suite of AI-powered applications for data processing, visitor classification, and CRM integration designed for event management and customer analytics.

## 🏗️ Project Overview

This repository contains multiple interconnected applications that leverage artificial intelligence for:
- Event visitor behavior analysis and classification
- Graph database analytics with Neo4j
- CRM integration with HubSpot
- Recommendation systems for personalized experiences
- Multi-model AI inference and processing pipelines

## 📁 Repository Structure

```
Strategic_AI_CSM_Applications/
├── 📊 PA/                          # Personal AGENDAS - Data Processing Pipeline
├── 🤖 app/                         # CSM LLM Application - HPI Classification
├── 🏢 mcp-chatbot/                 # AI-Powered CRM & Graph Database Platform
├── 📈 phase1/                      # Conference Attendee Clustering (Phase 1)
├── 🎯 phase2/                      # Event Visitor Classification (Phase 2)
├── ⚡ inference/                   # Multi-Model Inference System
├── 📁 archive/                     # Legacy components and utilities
└── 📋 requirements.txt             # Common dependencies
```

---

## 🔧 Core Applications

### 📊 PA - Personal AGENDAS
**A comprehensive data processing and analytics pipeline for veterinary conference data**

**Purpose**: Process registration, attendance, and session information to generate personalized recommendations and insights for veterinary conferences (BVA - British Veterinary Association and LVA - London Vet Show).

**Key Features**:
- **Data Processing**: Registration, scan, and session data processing
- **Neo4j Integration**: Knowledge graph creation with visitors, sessions, and streams
- **AI-Powered Features**: Stream descriptions and session embeddings
- **Smart Recommendations**: Personalized session recommendations using visitor similarity

**Quick Start**:
```bash
cd PA/app
pip install -r requirements.txt
python main.py
```

**Architecture**:
- Pipeline coordinator with modular processors
- Neo4j graph database for relationship mapping
- Business rules engine for recommendation filtering
- Multi-year visitor tracking and analysis

---

### 🤖 app - CSM LLM Application (HPI)
**High Purchase Intention visitor classification system for technology events**

**Purpose**: Analyze and categorize technology event attendees based on their purchasing intentions and engagement patterns using multiple Large Language Models.

**Key Features**:
- **Multi-Model Support**: Llama 3.1, GPT-4o-mini, o3-mini
- **5-Category Classification**: Networking, Learning, Searching, Early Purchasing, High Purchase Intention
- **Web Interface**: Streamlit-based authentication and processing
- **Batch Processing**: Efficient handling of large datasets

**Quick Start**:
```bash
cd app
docker-compose up -d
streamlit run main.py
```

**Classification Categories**:
- **Networking**: Professional relationship building
- **Learning**: Educational opportunities seeking
- **Searching**: Information gathering on products/vendors
- **Early Purchasing Intention**: Active sourcing engagement
- **High Purchase Intention**: Final purchasing journey stages

---

### 🏢 mcp-chatbot - AI-Powered CRM & Graph Database Platform
**Full-stack application providing AI-powered interactions with Neo4j and HubSpot**

**Purpose**: Seamless data analysis, management, and automation across database and CRM infrastructure through Model Context Protocol (MCP) servers.

**Key Features**:
- **Streamlit Client**: AI chat interface with multi-provider support
- **Neo4j MCP Server**: Graph database operations via Cypher queries
- **HubSpot MCP Server**: Complete CRM integration with 25+ tools
- **Security**: User authentication and session management

**Quick Start**:
```bash
cd mcp-chatbot
docker-compose up --build
# Access: http://localhost:8501
```

**Components**:
- **Authentication System**: Secure login with bcrypt hashing
- **Graph Operations**: Schema discovery and complex queries
- **CRM Management**: Full CRUD operations across HubSpot objects
- **Real-time Communication**: Server-Sent Events for MCP

---

## 🔬 Research & Development Phases

### 📈 phase1 - Conference Attendee Clustering
**Machine learning system for clustering conference attendees based on behavior patterns**

**Purpose**: Identify six main behavioral clusters using various embedding models (Mistral, LLaMA, Nomic) and classification techniques.

**Behavioral Clusters**:
1. **Networking** - Connection-focused attendees
2. **Learning** - Educational content seekers
3. **Searching** - Option explorers
4. **Sourcing: Early** - Early-stage procurement
5. **Sourcing: In Process** - Mid-stage sourcing
6. **Sourcing: Deciding** - Late-stage decision making

**Technical Implementation**:
- Custom BadgeNet neural network (4-layer architecture)
- Multiple embedding models comparison
- Focal loss for class imbalance handling
- Cosine similarity cluster assignment

---

### 🎯 phase2 - Event Visitor Classification System
**Advanced visitor classification using multiple LLM models**

**Purpose**: Categorize event visitors into five purchasing intention categories using LLama, Phi3, and DeepSeek models.

**Classification Categories**:
1. **Networking** - Professional relationship building
2. **Learning** - Educational motivation
3. **Searching** - Product/vendor exploration
4. **Early Purchasing Intention** - Active sourcing
5. **High Purchase Intention** - Final purchasing stages

**Data Flow**:
- Registration data processing from multiple events
- Demographic data integration with questionnaire responses
- Profile generation combining all data sources
- Multi-model classification with confidence scoring

---

### ⚡ inference - Multi-Model Inference System
**High-performance LLM inference implementations with focus on profile classification**

**Purpose**: Various implementations for running large language model inference with support for multiple backends including vLLM, Ollama, OpenAI, Azure OpenAI, and Google Gemini.

**Key Components**:
- **vLLM Framework**: High-performance serving with Paged Attention
- **Async Processing**: Multiple concurrent inference implementations
- **Cost Tracking**: Token usage monitoring and optimization
- **Load Balancing**: Multi-server deployment support

**Supported Models**:
- Llama 3.1 (8B, various quantizations)
- GPT-4o-mini (OpenAI/Azure)
- Gemini 2.0 Flash Lite
- Custom model deployments

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Neo4j Database (with APOC plugin)
- API Keys (OpenAI, Azure OpenAI, HubSpot, etc.)

### Environment Setup
1. Clone the repository:
```bash
git clone <repository-url>
cd Strategic_AI_CSM_Applications
```

2. Install common dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (`.env` file):
```env
# AI Provider Configuration
OPENAI_API_KEY=your_openai_api_key
AZURE_API_KEY=your_azure_api_key
AZURE_ENDPOINT=your_azure_endpoint
AZURE_DEPLOYMENT=your_deployment_name

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# HubSpot Configuration
PRIVATE_APP_ACCESS_TOKEN=your_hubspot_token
```

### Running Individual Applications

**PA - Data Processing Pipeline**:
```bash
cd PA/app
python main.py
```

**CSM LLM Application**:
```bash
cd app
docker-compose up -d
streamlit run main.py
```

**MCP Chatbot Platform**:
```bash
cd mcp-chatbot
docker-compose up --build
```

---

## 🔧 Configuration & Customization

### Data Processing (PA)
- Configure input/output paths in `PA/app/config/config.yaml`
- Set up Neo4j credentials and connection parameters
- Customize business rules for recommendations

### Classification Systems (app/phase1/phase2)
- Model selection and parameters in configuration files
- Prompt templates for different classification approaches
- Batch processing settings for large datasets

### CRM Integration (mcp-chatbot)
- User authentication in `client/keys/config.yaml`
- MCP server endpoints in `servers_config.json`
- HubSpot API scopes and permissions

---

## 📊 Data Flow & Integration

### Typical Workflow
1. **Data Ingestion**: Events registration and demographic data
2. **Processing**: PA pipeline for data cleaning and enrichment
3. **Classification**: AI-powered visitor categorization
4. **Storage**: Neo4j graph database with relationships
5. **Analytics**: CRM integration and recommendation generation
6. **Deployment**: Real-time inference and monitoring

### Integration Points
- **Neo4j ↔ HubSpot**: Sync visitor data between graph DB and CRM
- **Classification ↔ Recommendations**: Use categories for personalized suggestions
- **Inference ↔ Applications**: Real-time model serving for web interfaces

---

## 🔒 Security & Best Practices

### Authentication & Authorization
- **User Management**: Secure authentication with bcrypt hashing
- **API Security**: Environment-based credential management
- **Session Control**: Configurable session timeouts and policies

### Data Protection
- **Input Validation**: Schema validation across all components
- **Error Handling**: Sanitized error messages and comprehensive logging
- **Privacy Compliance**: Data anonymization and protection measures

### Deployment Security
- **Containerization**: Isolated service deployment
- **Network Security**: Configurable port mapping and CORS
- **Monitoring**: Health checks and performance tracking

---

## 📈 Performance & Scalability

### Optimization Strategies
- **Async Processing**: Concurrent inference for improved throughput
- **Batch Operations**: Efficient handling of large datasets
- **Caching**: Strategic caching of embeddings and classifications
- **Load Balancing**: Multi-server deployment support

### Monitoring & Debugging
- **Health Checks**: Service availability monitoring
- **Logging**: Comprehensive logging across all components
- **Metrics**: Performance tracking and resource usage
- **Error Tracking**: Detailed error reporting and debugging tools

---

## 🤝 Contributing

### Development Guidelines
1. **Component-Specific**: Follow individual component development guides
2. **Code Standards**: PEP 8 for Python, ES6+ for JavaScript
3. **Documentation**: Comprehensive README and inline comments
4. **Testing**: Unit tests and integration testing for all components
5. **Security**: Follow authentication and security best practices

### Adding New Features
- **New Models**: Extend inference system with additional LLM models
- **Custom Tools**: Add new integrations via MCP protocol
- **Data Sources**: Integrate additional event or CRM data sources
- **Analytics**: Extend reporting and visualization capabilities

---

## 📚 Documentation Links

### Component-Specific Documentation
- **[PA - Data Processing Pipeline](./PA/readme.md)**: Comprehensive data processing and Neo4j integration
- **[CSM LLM Application](./app/readme.md)**: HPI classification system with multi-model support
- **[MCP Chatbot Platform](./mcp-chatbot/Readme.md)**: AI-powered CRM and graph database integration
- **[Phase 1 - Clustering](./phase1/readme.md)**: Conference attendee clustering and classification
- **[Phase 2 - Classification](./phase2/readme.md)**: Event visitor classification system
- **[Inference System](./inference/readme.md)**: Multi-model inference implementations

### External Resources
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [HubSpot API Documentation](https://developers.hubspot.com/docs/api/overview)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [LangChain Documentation](https://python.langchain.com/)

---

## 🐛 Troubleshooting

### Common Issues
**Environment Setup**:
- Verify all required API keys are configured
- Check Docker service availability
- Ensure Neo4j database connectivity

**Model Inference**:
- Verify model availability and compatibility
- Check GPU/CPU resource allocation
- Monitor token usage and rate limits

**Data Processing**:
- Validate input data formats and schemas
- Check file permissions and access rights
- Verify Neo4j schema and constraints

### Getting Help
- Review component-specific documentation
- Check service logs: `docker-compose logs <service>`
- Use health check endpoints for diagnostics
- Verify authentication and permissions

---

## 📄 License & Version Information

**Version**: 2.0.0  
**Last Updated**: June 2025  
**Compatibility**: 
- Python 3.11+
- Docker 20+
- Neo4j 5.0+
- Node.js 18+

**Dependencies**: See individual component requirements and `requirements.txt`

---

**For detailed usage instructions and advanced configuration, please refer to the individual component documentation linked above.**