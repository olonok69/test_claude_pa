# Strategic AI CSM Applications

A comprehensive suite of AI-powered applications for data processing, visitor classification, CRM integration, and multi-database analytics designed for event management and customer analytics.

## 🏗️ Project Overview

This repository contains multiple interconnected applications that leverage artificial intelligence for:
- Event visitor behavior analysis and classification
- Graph database analytics with Neo4j
- CRM integration with HubSpot
- SQL database operations with MSSQL Server
- Recommendation systems for personalized experiences
- Multi-model AI inference and processing pipelines
- Cross-platform data analytics and integration

## 📁 Repository Structure

```
Strategic_AI_CSM_Applications/
├── 📊 PA/                          # Personal AGENDAS - Data Processing Pipeline
├── 🤖 app/                         # CSM LLM Application - HPI Classification
├── 🏢 mcp-chatbot/                 # AI-Powered Multi-Database & CRM Platform
│   ├── client/                     # Streamlit AI Chat Interface
│   └── servers/                    # MCP Protocol Servers
│       ├── server3/                # MSSQL Database Server
│       ├── server4/                # Neo4j Graph Database Server
│       └── server5/                # HubSpot CRM Server
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

### 🏢 mcp-chatbot - AI-Powered Multi-Database & CRM Platform
**Full-stack application providing AI-powered interactions with Neo4j, MSSQL, and HubSpot through unified interface**

**Purpose**: Seamless data analysis, management, and automation across multiple database and CRM systems through Model Context Protocol (MCP) servers with comprehensive authentication and SSL support.

**Key Features**:
- **Streamlit Client**: AI chat interface with multi-provider support and authentication
- **Neo4j MCP Server**: Graph database operations via Cypher queries
- **MSSQL MCP Server**: SQL Server database operations with ODBC integration
- **HubSpot MCP Server**: Complete CRM integration with 25+ tools
- **Security**: User authentication, SSL/HTTPS support, and session management
- **Cross-Database Integration**: Unified queries across all data sources

**Quick Start**:
```bash
cd mcp-chatbot
docker-compose up --build
# Access: http://localhost:8501 or https://localhost:8502 (SSL)
```

**Components**:
- **Authentication System**: Secure login with bcrypt hashing
- **Multi-Database Operations**: Neo4j graph queries, MSSQL operations, HubSpot CRM
- **Cross-Platform Analytics**: Compare and analyze data across all systems
- **Real-time Communication**: Server-Sent Events for MCP protocol
- **SSL/HTTPS Support**: Secure connections with automatic certificate generation

**Database Support**:
- **Neo4j**: Schema discovery, Cypher queries, relationship mapping
- **MSSQL Server**: Table operations, SQL execution, CRUD operations
- **HubSpot CRM**: Contacts, companies, deals, tickets, workflows

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
- MSSQL Server with ODBC Driver 18
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

# MSSQL Configuration
MSSQL_HOST=your_sql_server_host
MSSQL_USER=your_username
MSSQL_PASSWORD=your_password
MSSQL_DATABASE=your_database
MSSQL_DRIVER=ODBC Driver 18 for SQL Server

# HubSpot Configuration
PRIVATE_APP_ACCESS_TOKEN=your_hubspot_token

# SSL Configuration (Optional)
SSL_ENABLED=true
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

**MCP Multi-Database Platform**:
```bash
cd mcp-chatbot
docker-compose up --build
# Access: http://localhost:8501 or https://localhost:8502
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

### Multi-Database Integration (mcp-chatbot)
- User authentication in `client/keys/config.yaml`
- MCP server endpoints in `servers_config.json`
- Database connections for Neo4j, MSSQL, and HubSpot
- SSL certificate generation and management

---

## 📊 Data Flow & Integration

### Typical Workflow
1. **Data Ingestion**: Events registration and demographic data
2. **Processing**: PA pipeline for data cleaning and enrichment
3. **Classification**: AI-powered visitor categorization
4. **Storage**: Neo4j graph database with relationships
5. **Analytics**: Multi-database integration and recommendation generation
6. **CRM Integration**: HubSpot synchronization and workflow automation
7. **Deployment**: Real-time inference and monitoring

### Integration Points
- **Neo4j ↔ HubSpot**: Sync visitor data between graph DB and CRM
- **MSSQL ↔ Analytics**: Structured data analysis and reporting
- **Classification ↔ Recommendations**: Use categories for personalized suggestions
- **Cross-Database Queries**: Unified analytics across all data sources
- **Inference ↔ Applications**: Real-time model serving for web interfaces

---

## 🔒 Security & Best Practices

### Authentication & Authorization
- **User Management**: Secure authentication with bcrypt hashing
- **API Security**: Environment-based credential management
- **Session Control**: Configurable session timeouts and policies
- **SSL/HTTPS Support**: Encrypted connections with certificate management

### Data Protection
- **Input Validation**: Schema validation across all components
- **Error Handling**: Sanitized error messages and comprehensive logging
- **Privacy Compliance**: Data anonymization and protection measures
- **Cross-Database Security**: Separate credentials for each system

### Deployment Security
- **Containerization**: Isolated service deployment
- **Network Security**: Configurable port mapping and CORS
- **Monitoring**: Health checks and performance tracking
- **Database Security**: Encrypted connections and proper access controls

---

## 📈 Performance & Scalability

### Optimization Strategies
- **Async Processing**: Concurrent inference for improved throughput
- **Batch Operations**: Efficient handling of large datasets
- **Caching**: Strategic caching of embeddings and classifications
- **Load Balancing**: Multi-server deployment support
- **Connection Pooling**: Efficient database connection management

### Monitoring & Debugging
- **Health Checks**: Service availability monitoring across all components
- **Logging**: Comprehensive logging across all applications
- **Metrics**: Performance tracking and resource usage
- **Error Tracking**: Detailed error reporting and debugging tools
- **Cross-Database Monitoring**: Unified monitoring across all data sources

---

## 🤝 Contributing

### Development Guidelines
1. **Component-Specific**: Follow individual component development guides
2. **Code Standards**: PEP 8 for Python, ES6+ for JavaScript
3. **Documentation**: Comprehensive README and inline comments
4. **Testing**: Unit tests and integration testing for all components
5. **Security**: Follow authentication and security best practices
6. **Cross-Platform Testing**: Validate multi-database integrations

### Adding New Features
- **New Models**: Extend inference system with additional LLM models
- **Custom Tools**: Add new integrations via MCP protocol
- **Data Sources**: Integrate additional event or CRM data sources
- **Analytics**: Extend reporting and visualization capabilities
- **Database Support**: Add support for additional database systems

---

## 📚 Documentation Links

### Component-Specific Documentation
- **[PA - Data Processing Pipeline](./PA/readme.md)**: Comprehensive data processing and Neo4j integration
- **[CSM LLM Application](./app/readme.md)**: HPI classification system with multi-model support
- **[MCP Multi-Database Platform](./mcp-chatbot/Readme.md)**: AI-powered multi-database and CRM integration
  - **[Streamlit Client](./mcp-chatbot/client/Readme.md)**: Authentication, SSL, and UI documentation
  - **[Neo4j MCP Server](./mcp-chatbot/servers/server4/Readme.md)**: Graph database operations
  - **[MSSQL MCP Server](./mcp-chatbot/servers/server3/readme.md)**: SQL Server database integration
  - **[HubSpot MCP Server](./mcp-chatbot/servers/server5/Readme.md)**: Complete CRM integration
- **[Phase 1 - Clustering](./phase1/readme.md)**: Conference attendee clustering and classification
- **[Phase 2 - Classification](./phase2/readme.md)**: Event visitor classification system
- **[Inference System](./inference/readme.md)**: Multi-model inference implementations

### External Resources
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [HubSpot API Documentation](https://developers.hubspot.com/docs/api/overview)
- [MSSQL Server Documentation](https://docs.microsoft.com/en-us/sql/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [LangChain Documentation](https://python.langchain.com/)

---

## 🐛 Troubleshooting

### Common Issues
**Environment Setup**:
- Verify all required API keys are configured
- Check Docker service availability
- Ensure database connectivity (Neo4j, MSSQL)
- Verify ODBC driver installation

**Model Inference**:
- Verify model availability and compatibility
- Check GPU/CPU resource allocation
- Monitor token usage and rate limits

**Data Processing**:
- Validate input data formats and schemas
- Check file permissions and access rights
- Verify database schemas and constraints

**Multi-Database Issues**:
- Check all database connections independently
- Verify authentication credentials for each system
- Monitor cross-database query performance
- Validate SSL/TLS configurations

### Getting Help
- Review component-specific documentation
- Check service logs: `docker-compose logs <service>`
- Use health check endpoints for diagnostics
- Verify authentication and permissions
- Test database connections individually

---

## 📄 License & Version Information

**Version**: 3.0.0  
**Last Updated**: June 2025  
**Compatibility**: 
- Python 3.11+
- Docker 20+
- Neo4j 5.0+
- MSSQL Server 2019+
- Node.js 18+

**Major Updates in v3.0.0**:
- Added MSSQL MCP Server for SQL database integration
- Enhanced multi-database analytics and cross-platform queries
- Improved authentication and SSL/HTTPS support
- Expanded CRM integration with 25+ HubSpot tools
- Performance optimizations and monitoring enhancements

**Dependencies**: See individual component requirements and `requirements.txt`

---

**For detailed usage instructions and advanced configuration, please refer to the individual component documentation linked above.**