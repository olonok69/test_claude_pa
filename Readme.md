# AI-Powered CRM & Graph Database Integration Platform

A comprehensive full-stack application that provides AI-powered interactions with Neo4j graph databases, HubSpot CRM systems, and Yahoo Finance data through Model Context Protocol (MCP) servers. This platform enables seamless data analysis, management, and automation across your database, CRM, and financial data infrastructure.

## 🚀 System Overview

This application consists of four integrated components:

1. **Streamlit Client** - AI chat interface with multi-provider support
2. **Yahoo Finance MCP Server** - Financial data analysis and technical indicators
3. **Neo4j MCP Server** - Graph database operations via Cypher queries  
4. **HubSpot MCP Server** - Complete CRM integration with 25+ tools

### Architecture Diagram

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Streamlit Client  │    │   Yahoo Finance     │    │   Neo4j Database    │    │   HubSpot CRM       │
│                     │    │                     │    │                     │    │                     │
│  - AI Chat UI       │    │  - Stock Analysis   │    │  - Graph Data       │    │  - Contacts         │
│  - Multi-Provider   │◄──►│  - Technical        │    │  - Cypher Queries   │    │  - Companies        │
│  - Tool Management  │    │    Indicators       │    │  - Schema Discovery │    │  - Deals & Tickets  │
│  - Conversation     │    │  - Market Data      │    │                     │    │                     │
│    History          │    │                     │    └─────────────────────┘    └─────────────────────┘
│                     │    └─────────────────────┘              ▲                          ▲
└─────────────────────┘              ▲                          │                          │
           ▲                         │                     ┌────┴─────┐               ┌────┴─────┐
           │                    ┌────┴─────┐               │ Server 4 │               │ Server 5 │
           │                    │ Server 3 │               │ Neo4j    │               │ HubSpot  │
           │                    │ Yahoo    │               │ MCP      │               │ MCP      │
           │                    │ Finance  │               │ Server   │               │ Server   │
           │                    │ MCP      │               └──────────┘               └──────────┘
           │                    │ Server   │                    ▲                          ▲
           │                    └──────────┘                    │                          │
           │                         ▲                          │                          │
           └─────────────────────────┼──────────────────────────┼──────────────────────────┘
                                     │                          │
                              ┌───────────────┐                 │
                              │     MCP       │                 │
                              │  Protocol     │                 │
                              │ Communication │                 │
                              └───────────────┘                 │
                                      ▲                         │
                                      └─────────────────────────┘
```

## ⚡ Quick Start

### Prerequisites
- Docker & Docker Compose
- Neo4j database (with APOC plugin)
- HubSpot Private App Access Token
- OpenAI API key or Azure OpenAI configuration

### 1. Environment Setup

Create a `.env` file in the project root:

```env
# OpenAI Configuration (choose one)
OPENAI_API_KEY=your_openai_api_key_here

# OR Azure OpenAI Configuration
AZURE_API_KEY=your_azure_api_key
AZURE_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_DEPLOYMENT=your_deployment_name
AZURE_API_VERSION=2023-12-01-preview

# Neo4j Configuration
NEO4J_URI=bolt://host.docker.internal:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j

# HubSpot Configuration
PRIVATE_APP_ACCESS_TOKEN=your_hubspot_private_app_token
```

### 2. Launch the Platform

```bash
# Build and start all services
docker-compose up --build

# Or start individual services
docker-compose up mcpserver3  # Yahoo Finance MCP Server
docker-compose up mcpserver4  # Neo4j MCP Server
docker-compose up mcpserver5  # HubSpot MCP Server  
docker-compose up hostclient  # Streamlit Client
```

### 3. Access the Application

- **Main Interface**: http://localhost:8501
- **Yahoo Finance Server Health**: http://localhost:8002/health
- **Neo4j Server Health**: http://localhost:8003/health
- **HubSpot Server Health**: http://localhost:8004/health

## 🎯 Key Features

### **AI-Powered Interactions**
- Multi-provider AI support (OpenAI, Azure OpenAI)
- Natural language queries for financial data, database operations, and CRM management
- Intelligent tool selection and execution
- Conversation history and context management

### **Financial Data Analysis**
- **Real-time Stock Data**: Access current market prices and trading information
- **Technical Analysis**: Advanced indicators including MACD, Bollinger Bands, Donchian Channels
- **Custom Scoring Systems**: Proprietary algorithms for trading signals and market analysis
- **Portfolio Analysis**: Combined indicator scoring for investment decisions

### **Graph Database Operations**
- **Schema Discovery**: Automatic Neo4j structure analysis
- **Read Operations**: Complex graph queries and data retrieval
- **Write Operations**: Node and relationship creation/modification
- **Query Validation**: Schema-aware query validation
- **Visual Results**: Structured data presentation

### **Complete CRM Integration**
- **25 HubSpot Tools**: Full CRUD operations across all object types
- **Contact Management**: Create, update, search contacts and companies
- **Deal Pipeline**: Manage sales opportunities and tickets
- **Association Management**: Link relationships between CRM objects
- **Property Management**: Custom fields and data structures
- **Engagement Tracking**: Notes, tasks, and activity logging
- **Workflow Integration**: Automation insights and management
- **UI Integration**: Direct links to HubSpot interface

### **Technical Excellence**
- **Docker Containerization**: Easy deployment and scaling
- **Real-time Communication**: Server-Sent Events (SSE) for MCP
- **Schema Validation**: Comprehensive input validation
- **Error Handling**: Robust error management and debugging
- **Health Monitoring**: Built-in health checks and monitoring

## 📚 Usage Examples

### **Financial Analysis Workflows**

```
"What's the current MACD score for AAPL?"
"Calculate the Bollinger Band position for Tesla stock"
"Give me a combined technical analysis score for Microsoft"
"Show me Donchian channel analysis for the S&P 500"
```

### **Database Analysis Workflows**

```
"Show me the database schema and explain the data structure"
"How many visitors converted to customers this year?"
"Find all connections between person nodes and company nodes"
"Create a new relationship between John and Acme Corp"
```

### **CRM Management Workflows**

```
"Show me all contacts created this month"
"Create a new company called Tech Solutions and associate it with John Smith"
"List all open deals above $10,000"
"Add a follow-up task for the Amazon deal"
"Generate a link to view the Microsoft account in HubSpot"
```

### **Advanced Integration Workflows**

```
"Analyze AAPL stock performance and create a HubSpot task to review our tech investments"
"Compare customer data between our graph database and HubSpot CRM"
"Find high-value deals in HubSpot and cross-reference with market analysis"
"Create a comprehensive investment report combining technical analysis and CRM data"
```

## 🔧 Component Documentation

Each component has detailed documentation for advanced configuration and development:

### [📈 Yahoo Finance MCP Server Documentation](./servers/server3/Readme.md)
- Financial data access and analysis tools
- Technical indicator calculations
- Market data retrieval and processing
- Trading signal generation
- Docker deployment options

### [🖥️ Streamlit Client Documentation](./client/Readme.md)
- UI configuration and customization
- AI provider setup and management
- Tool execution monitoring
- Conversation management
- Docker deployment options

### [🗄️ Neo4j MCP Server Documentation](./servers/server4/Readme.md)
- Neo4j connection configuration
- Cypher query examples and patterns
- Schema discovery and validation
- Error handling and troubleshooting
- Security considerations

### [🏢 HubSpot MCP Server Documentation](./servers/server5/Readme.md)
- Complete tool reference (25 tools)
- HubSpot API integration setup
- Advanced workflow examples
- Authentication and permissions
- Performance optimization

For comprehensive tool usage, see the [HubSpot Tools Implementation Guide](./servers/server5/HUBSPOT_TOOLS_GUIDE.md).

## 🛠️ Development & Customization

### **Local Development Setup**

```bash
# Clone the repository
git clone <your-repo-url>
cd <project-directory>

# Install dependencies for each component
cd client && pip install -r requirements.txt
cd ../servers/server3 && pip install -r requirements.txt
cd ../servers/server4 && pip install -r requirements.txt
cd ../servers/server5 && npm install
```

### **Adding Custom Tools**

1. **Yahoo Finance Tools**: Extend the server with custom financial analysis functions
2. **Neo4j Tools**: Extend the Neo4j server with custom Cypher operations
3. **HubSpot Tools**: Add new HubSpot API integrations
4. **Client Tools**: Integrate additional services via MCP protocol

### **Configuration Management**

- **Client**: Update `servers_config.json` for MCP server endpoints
- **Yahoo Finance**: Configure data sources and analysis parameters
- **Neo4j**: Modify connection parameters in environment variables
- **HubSpot**: Configure API scopes and permissions in HubSpot Developer Console

## 🔒 Security & Best Practices

### **Authentication**
- Secure API key management via environment variables
- HubSpot Private App token authentication
- Neo4j database credential protection
- No API keys required for Yahoo Finance (public data)

### **Data Protection**
- Input validation across all components
- Schema validation for database operations
- Sanitized error messages and logging
- Financial data caching considerations

### **Network Security**
- Containerized deployment isolation
- Configurable port mapping
- Health check endpoints for monitoring
- Rate limiting for external API calls

## 📊 Monitoring & Debugging

### **Health Checks**
- **Overall System**: Streamlit interface status indicators
- **Yahoo Finance Server**: http://localhost:8002/health
- **Neo4j Server**: http://localhost:8003/health
- **HubSpot Server**: http://localhost:8004/health

### **Debugging Tools**
- Tool execution history in Streamlit interface
- Comprehensive logging across all components
- Error tracking and validation feedback
- Financial data validation and error handling

### **Performance Monitoring**
- Query execution timing
- API request/response monitoring
- Resource usage tracking in Docker
- Financial data update frequencies

## 🚀 Deployment Options

### **Development Deployment**
```bash
docker-compose up --build
```

### **Production Deployment**
- Use environment-specific `.env` files
- Configure reverse proxy (nginx, traefik)
- Implement proper secret management
- Set up monitoring and alerting
- Configure financial data refresh schedules

### **Scaling Considerations**
- Horizontal scaling of MCP servers
- Load balancing for high-traffic scenarios
- Database connection pooling
- Caching strategies for frequently accessed data
- Financial data rate limiting and quotas

## 🐛 Troubleshooting

### **Common Issues**

**Connection Problems**
- Verify all services are running: `docker-compose ps`
- Check network connectivity between containers
- Validate environment variables and credentials

**API Authentication Errors**
- Confirm API keys are correctly set in `.env`
- Verify HubSpot Private App permissions
- Check Neo4j database accessibility
- Validate financial data access (no auth required)

**Tool Execution Failures**
- Review tool execution history in Streamlit
- Check individual server health endpoints
- Validate input parameters and data formats
- Monitor financial data API rate limits

**Financial Data Issues**
- Check Yahoo Finance service availability
- Verify stock symbol formatting
- Monitor technical indicator calculations
- Review market data freshness

### **Getting Help**
- Review component-specific documentation
- Check Docker logs: `docker-compose logs <service>`
- Use health check endpoints for diagnostics
- Monitor financial data service status

## 🤝 Contributing

### **Development Workflow**
1. Fork the repository
2. Create feature branches for each component
3. Follow component-specific development guidelines
4. Submit pull requests with comprehensive testing

### **Code Standards**
- **Python**: PEP 8 compliance for client, Yahoo Finance, and Neo4j servers
- **JavaScript**: ES6+ standards for HubSpot server
- **Docker**: Multi-stage builds and security best practices
- **Documentation**: Comprehensive README and inline comments

## 🔗 Additional Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Yahoo Finance API Documentation](https://pypi.org/project/yfinance/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [HubSpot API Documentation](https://developers.hubspot.com/docs/api/overview)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

**Version**: 1.0.0  
**Last Updated**: June 2025  
**Compatibility**: Docker 20+, Python 3.11+, Node.js 18+, Neo4j 5.0+