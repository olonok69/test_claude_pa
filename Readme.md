# AI-Powered CRM & Graph Database Integration Platform

A comprehensive full-stack application that provides AI-powered interactions with Neo4j graph databases and HubSpot CRM systems through Model Context Protocol (MCP) servers. This platform enables seamless data analysis, management, and automation across your database and CRM infrastructure.

## 🚀 System Overview

This application consists of three integrated components:

1. **Streamlit Client** - AI chat interface with multi-provider support and authentication
2. **Neo4j MCP Server** - Graph database operations via Cypher queries  
3. **HubSpot MCP Server** - Complete CRM integration with 25+ tools

### Architecture Diagram

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Streamlit Client  │    │   Neo4j Database    │    │   HubSpot CRM       │
│                     │    │                     │    │                     │
│  - AI Chat UI       │    │  - Graph Data       │    │  - Contacts         │
│  - Authentication   │◄──►│  - Cypher Queries   │    │  - Companies        │
│  - Multi-Provider   │    │  - Schema Discovery │    │  - Deals & Tickets  │
│  - Tool Management  │    │                     │    │                     │
│  - Conversation     │    └─────────────────────┘    └─────────────────────┘
│    History          │              ▲                          ▲
└─────────────────────┘              │                          │
           ▲                         │                          │
           │                    ┌────┴─────┐               ┌────┴─────┐
           │                    │ Server 4 │               │ Server 5 │
           │                    │ Neo4j    │               │ HubSpot  │
           │                    │ MCP      │               │ MCP      │
           │                    │ Server   │               │ Server   │
           │                    └──────────┘               └──────────┘
           │                         ▲                          ▲
           │                         │                          │
           └─────────────────────────┼──────────────────────────┘
                                     │
                              ┌───────────────┐
                              │     MCP       │
                              │  Protocol     │
                              │ Communication │
                              └───────────────┘
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
# AI Provider Configuration (choose one)
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

### 2. User Authentication Setup

Generate user credentials for the application:

```bash
cd client
python simple_generate_password.py
```

This will create `keys/config.yaml` with default users. You can modify the user credentials as needed.

### 3. Launch the Platform

```bash
# Build and start all services
docker-compose up --build

# Or start individual services
docker-compose up mcpserver4  # Neo4j MCP Server
docker-compose up mcpserver5  # HubSpot MCP Server  
docker-compose up hostclient  # Streamlit Client
```

### 4. Access the Application

- **Main Interface**: http://localhost:8501
- **Authentication**: Use the credentials generated in step 2
- **Neo4j Server Health**: http://localhost:8003/health
- **HubSpot Server Health**: http://localhost:8004/health

## 🎯 Key Features

### **AI-Powered Interactions**
- Multi-provider AI support (OpenAI, Azure OpenAI)
- Natural language queries for database and CRM operations
- Intelligent tool selection and execution
- Conversation history and context management
- User authentication and session management

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

### **Security & Authentication**
- **User Authentication**: Secure login system with bcrypt password hashing
- **Session Management**: Persistent user sessions with role-based access
- **Environment Security**: Secure credential management via environment variables
- **API Key Protection**: Safe storage and handling of sensitive tokens

### **Technical Excellence**
- **Docker Containerization**: Easy deployment and scaling
- **Real-time Communication**: Server-Sent Events (SSE) for MCP
- **Schema Validation**: Comprehensive input validation
- **Error Handling**: Robust error management and debugging
- **Health Monitoring**: Built-in health checks and monitoring

## 📚 Usage Examples

### **Authentication Workflow**

```
1. Navigate to http://localhost:8501
2. Use the sidebar authentication panel
3. Login with generated credentials:
   - Username: admin, Password: very_Secure_p@ssword_123!
   - Username: demo_user, Password: strong_password_123!
4. Access the full application features
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
"Compare customer data between our graph database and HubSpot CRM"
"Find orphaned contacts in HubSpot that don't exist in our user database"
"Create HubSpot contacts for all new users added to Neo4j this week"
```

## 🔧 Component Documentation

Each component has detailed documentation for advanced configuration and development:

### [🖥️ Streamlit Client Documentation](./client/Readme.md)
- Authentication system setup and configuration
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
cd ../servers/server4 && pip install -r requirements.txt
cd ../servers/server5 && npm install
```

### **Authentication Configuration**

```bash
# Generate new user credentials
cd client
python simple_generate_password.py

# Modify users in the script before running:
# Edit the users dictionary with your desired credentials
```

### **Adding Custom Tools**

1. **Neo4j Tools**: Extend the Neo4j server with custom Cypher operations
2. **HubSpot Tools**: Add new HubSpot API integrations
3. **Client Tools**: Integrate additional services via MCP protocol

### **Configuration Management**

- **Client**: Update `servers_config.json` for MCP server endpoints
- **Authentication**: Modify `client/simple_generate_password.py` for user management
- **Neo4j**: Modify connection parameters in environment variables
- **HubSpot**: Configure API scopes and permissions in HubSpot Developer Console

## 🔒 Security & Best Practices

### **Authentication Security**
- Bcrypt password hashing for secure credential storage
- Session-based authentication with configurable expiry
- Pre-authorized email domains for access control
- Secure cookie configuration with custom keys

### **API Security**
- Secure API key management via environment variables
- HubSpot Private App token authentication
- Neo4j database credential protection
- Input validation across all components

### **Network Security**
- Containerized deployment isolation
- Configurable port mapping
- Health check endpoints for monitoring
- CORS configuration for secure API access

### **Data Protection**
- Schema validation for database operations
- Sanitized error messages and logging
- User session isolation and management

## 📊 Monitoring & Debugging

### **Health Checks**
- **Overall System**: Streamlit interface status indicators
- **Authentication**: User session and login status monitoring
- **Neo4j Server**: http://localhost:8003/health
- **HubSpot Server**: http://localhost:8004/health

### **Debugging Tools**
- Tool execution history in Streamlit interface
- User session and authentication logging
- Comprehensive logging across all components
- Error tracking and validation feedback

### **Performance Monitoring**
- Query execution timing
- API request/response monitoring
- Resource usage tracking in Docker
- User session and authentication metrics

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
- Configure SSL/TLS certificates
- Use secure authentication configurations

### **Scaling Considerations**
- Horizontal scaling of MCP servers
- Load balancing for high-traffic scenarios
- Database connection pooling
- Caching strategies for frequently accessed data
- User session management across multiple instances

## 🐛 Troubleshooting

### **Common Issues**

**Authentication Problems**
- Verify `keys/config.yaml` exists and is properly configured
- Check user credentials and email permissions
- Ensure cookie configuration is correct

**Connection Problems**
- Verify all services are running: `docker-compose ps`
- Check network connectivity between containers
- Validate environment variables and credentials

**API Authentication Errors**
- Confirm API keys are correctly set in `.env`
- Verify HubSpot Private App permissions
- Check Neo4j database accessibility

**Tool Execution Failures**
- Review tool execution history in Streamlit
- Check individual server health endpoints
- Validate input parameters and data formats

### **Getting Help**
- Review component-specific documentation
- Check Docker logs: `docker-compose logs <service>`
- Use health check endpoints for diagnostics
- Verify authentication and user permissions

## 🤝 Contributing

### **Development Workflow**
1. Fork the repository
2. Create feature branches for each component
3. Follow component-specific development guidelines
4. Test authentication and security features
5. Submit pull requests with comprehensive testing

### **Code Standards**
- **Python**: PEP 8 compliance for client and Neo4j server
- **JavaScript**: ES6+ standards for HubSpot server
- **Docker**: Multi-stage builds and security best practices
- **Documentation**: Comprehensive README and inline comments
- **Security**: Follow authentication and security best practices

## 🔗 Additional Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [HubSpot API Documentation](https://developers.hubspot.com/docs/api/overview)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Authenticator Documentation](https://github.com/mkhorasani/Streamlit-Authenticator)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

**Version**: 2.0.0  
**Last Updated**: June 2025  
**Compatibility**: Docker 20+, Python 3.11+, Node.js 18+, Neo4j 5.0+  
**Security**: Streamlit Authenticator 0.3.2, bcrypt password hashing