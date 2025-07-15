# AI-Powered CRM, Graph & SQL Database Integration Platform

A comprehensive full-stack application that provides AI-powered interactions with Neo4j graph databases, HubSpot CRM systems, and MSSQL databases through Model Context Protocol (MCP) servers. This platform enables seamless data analysis, management, and automation across your database and CRM infrastructure with optional HTTPS security.

## 🚀 System Overview

This application consists of four integrated components:

1. **Streamlit Client** - AI chat interface with multi-provider support, authentication, and SSL support
2. **Neo4j MCP Server** - Graph database operations via Cypher queries  
3. **HubSpot MCP Server** - Complete CRM integration with 25+ tools
4. **MSSQL MCP Server** - SQL Server database operations with full CRUD support

## 🏗️ System Architecture

![CSM MCP Servers Architecture](docs/csm_diagram.svg)

The diagram above shows the complete architecture of our AI-powered multi-database integration platform.

## ⚡ Quick Start

### Prerequisites
- Docker & Docker Compose
- Neo4j database (with APOC plugin)
- HubSpot Private App Access Token
- MSSQL Server database
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

# MSSQL Configuration
MSSQL_HOST=host.docker.internal
MSSQL_USER=your_mssql_username
MSSQL_PASSWORD=your_mssql_password
MSSQL_DATABASE=your_database_name
MSSQL_DRIVER=ODBC Driver 18 for SQL Server
TrustServerCertificate=yes
Trusted_Connection=no

# SSL Configuration (Optional)
SSL_ENABLED=true              # Enable HTTPS with self-signed certificates
```

### 2. User Authentication Setup

Generate user credentials for the application:

```bash
cd client
python simple_generate_password.py
```

This will create `keys/config.yaml` with default users. You can modify the user credentials as needed.

### 3. SSL Certificate Setup (Optional)

For HTTPS support, set up SSL certificates:

#### Option A: Automatic Generation (Recommended)
```bash
# Enable SSL in environment - certificates will be generated automatically
echo "SSL_ENABLED=true" >> .env
```

#### Option B: Manual Generation
```bash
cd client

# Create required startup scripts
cat > startup_ssl.sh << 'EOF'
#!/bin/bash
echo "🚀 CSM MCP Servers - Starting Application..."

if [ "$SSL_ENABLED" = "true" ]; then
    echo "🔒 SSL mode enabled"
    
    if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/private.key" ]; then
        echo "📝 Generating SSL certificates..."
        mkdir -p ssl
        
        if [ -f "generate_ssl_certificate.sh" ]; then
            chmod +x generate_ssl_certificate.sh
            ./generate_ssl_certificate.sh
        else
            echo "❌ Certificate generation script not found"
            SSL_ENABLED="false"
        fi
    fi
    
    if [ "$SSL_ENABLED" = "true" ] && [ -f "ssl/cert.pem" ] && [ -f "ssl/private.key" ]; then
        echo "🔒 Starting Streamlit with HTTPS on port 8502..."
        echo "📱 Access URL: https://localhost:8502"
        
        exec streamlit run app.py \
            --server.port=8502 \
            --server.address=0.0.0.0 \
            --server.enableCORS=false \
            --server.enableXsrfProtection=false \
            --server.sslCertFile=ssl/cert.pem \
            --server.sslKeyFile=ssl/private.key
    fi
fi

echo "🌐 Starting Streamlit with HTTP on port 8501..."
exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0
EOF

chmod +x startup_ssl.sh

# Generate certificates manually (if needed)
python generate_ssl_certificate.py
# OR (Linux/Mac only)
./generate_ssl_certificate.sh
```

### 4. Launch the Platform

```bash
# Build and start all services
docker-compose up --build

# Or start individual services
docker-compose up mcpserver3  # MSSQL MCP Server
docker-compose up mcpserver4  # Neo4j MCP Server
docker-compose up mcpserver5  # HubSpot MCP Server  
docker-compose up hostclient  # Streamlit Client
```

### 5. Access the Application

#### HTTPS Mode (Recommended)
- **Main Interface**: https://localhost:8502
- **Security**: Self-signed certificate (accept browser warning)

#### HTTP Mode (Default)
- **Main Interface**: http://localhost:8501
- **Alternative**: http://127.0.0.1:8501

#### Health Checks
- **MSSQL Server Health**: http://localhost:8008/health
- **Neo4j Server Health**: http://localhost:8003/health
- **HubSpot Server Health**: http://localhost:8004/health

#### Authentication
Use the credentials generated in step 2 (default: admin/very_Secure_p@ssword_123!)

## 🎯 Key Features

### **AI-Powered Interactions**
- Multi-provider AI support (OpenAI, Azure OpenAI)
- Natural language queries for all database and CRM operations
- Intelligent tool selection and execution
- Conversation history and context management
- User authentication and session management

### **Security & Authentication**
- **User Authentication System**: Secure login with bcrypt password hashing
- **Session Management**: Persistent user sessions with configurable expiry
- **SSL/HTTPS Support**: Optional encrypted connections with self-signed certificates
- **Role-Based Access**: Pre-authorized email domains and user management
- **Secure Cookies**: Configurable authentication cookies with custom keys

### **Multi-Database Support**
- **Graph Database Operations**: Complex Neo4j queries and schema discovery
- **SQL Database Operations**: Full MSSQL Server support with ODBC
- **CRM Integration**: Complete HubSpot operations with 25+ tools
- **Cross-Database Queries**: Compare and analyze data across systems
- **Visual Results**: Structured data presentation across all sources

### **Complete Database Operations**
- **Neo4j**: Schema discovery, read/write Cypher queries, visual results
- **MSSQL**: Table listing, SQL execution, CRUD operations, metadata queries
- **HubSpot**: Contact/company/deal management, associations, workflows
- **Cross-Platform**: Unified interface for all data sources

### **Technical Excellence**
- **Docker Containerization**: Easy deployment and scaling
- **SSL/HTTPS Support**: Secure connections with automatic certificate generation
- **Real-time Communication**: Server-Sent Events (SSE) for MCP
- **Schema Validation**: Comprehensive input validation
- **Error Handling**: Robust error management and debugging
- **Health Monitoring**: Built-in health checks and monitoring

## 📚 Usage Examples

### **Authentication Workflow**

```
1. Navigate to https://localhost:8502 (SSL) or http://localhost:8501 (HTTP)
2. Use the sidebar authentication panel
3. Login with generated credentials:
   - Username: admin, Password: very_Secure_p@ssword_123!
   - Username: demo_user, Password: strong_password_123!
4. Access the full application features
```

### **Database Analysis Workflows**

```
"Show me the Neo4j database schema and explain the data structure"
"How many visitors converted to customers this year?"
"List all tables in the MSSQL database"
"Execute a SQL query to find top customers by revenue"
"Find all connections between person nodes and company nodes in Neo4j"
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

### **MSSQL Database Workflows**

```
"Show me all tables in the database"
"Describe the structure of the customers table"
"Get 5 sample records from the orders table"
"Find all customers with orders over $1000"
"Count the total number of products in inventory"
"Show me the top 10 best-selling products"
```

### **Cross-Platform Integration Workflows**

```
"Compare customer data between Neo4j graph database and MSSQL tables"
"Find customers in HubSpot that don't exist in our SQL database"
"Create HubSpot contacts for all new users added to Neo4j this week"
"Show me sales data from MSSQL and corresponding deal information from HubSpot"
"Analyze customer journey data across all three systems"
```

## 🔧 Component Documentation

Each component has detailed documentation for advanced configuration and development:

### [🖥️ Streamlit Client Documentation](./client/Readme.md)
- Authentication system setup and configuration
- SSL/HTTPS configuration and certificate management
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

### [🗃️ MSSQL MCP Server Documentation](./servers/server3/Readme.md)
- MSSQL Server connection configuration
- SQL query examples and patterns
- ODBC driver setup and troubleshooting
- Security considerations
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

### **MSSQL Server Setup**

For MSSQL integration, ensure you have:
- MSSQL Server instance running
- ODBC Driver 18 for SQL Server installed
- Appropriate database permissions
- Network connectivity to the database

### **Adding Custom Tools**

1. **Neo4j Tools**: Extend the Neo4j server with custom Cypher operations
2. **HubSpot Tools**: Add new HubSpot API integrations
3. **MSSQL Tools**: Add custom SQL operations and stored procedures
4. **Client Tools**: Integrate additional services via MCP protocol

## 🔒 Security & Best Practices

### **Database Security**
- Use secure connection strings with proper authentication
- Implement least-privilege access for database users
- Enable SSL/TLS for database connections where possible
- Regularly update ODBC drivers and database clients

### **Cross-Database Security**
- Separate credentials for each database system
- Use environment variables for all sensitive data
- Implement proper error handling that doesn't expose credentials
- Regular security audits across all connected systems

## 📊 Monitoring & Debugging

### **Health Checks**
- **Overall System**: Streamlit interface status indicators
- **MSSQL Server**: http://localhost:8008/health
- **Neo4j Server**: http://localhost:8003/health
- **HubSpot Server**: http://localhost:8004/health

### **Database Monitoring**
- Connection pool status across all databases
- Query execution timing and performance metrics
- Error rates and connection failures
- Resource usage tracking

## 🚀 Deployment Options

### **Development Deployment**
```bash
# HTTP mode (default)
docker-compose up --build

# HTTPS mode
echo "SSL_ENABLED=true" >> .env
docker-compose up --build
```

### **Production Deployment**
- Use environment-specific `.env` files
- Configure proper SSL certificates for all database connections
- Implement proper secret management
- Set up monitoring and alerting
- Use connection pooling for high-traffic scenarios

## 🐛 Troubleshooting

### **Common Issues**

**MSSQL Connection Problems**
- Verify ODBC driver installation: `odbcinst -j`
- Check SQL Server connectivity: `telnet [host] 1433`
- Verify database permissions and user access
- Check firewall settings and network connectivity

**Multi-Database Sync Issues**
- Monitor connection pools across all databases
- Check for conflicting transactions
- Verify data consistency across systems
- Use proper transaction isolation levels

**Performance Issues**
- Monitor query execution times across all databases
- Implement connection pooling
- Use appropriate indexes in SQL databases
- Optimize Cypher queries in Neo4j

## 🤝 Contributing

### **Development Workflow**
1. Fork the repository
2. Create feature branches for each component
3. Test authentication and security features
4. Test all database connections and operations
5. Submit pull requests with comprehensive testing

### **Database Testing**
- Test all database connections in different environments
- Verify cross-database query functionality
- Test failover and recovery scenarios
- Validate data consistency across systems

---

**Version**: 3.0.0  
**Last Updated**: June 2025  
**Compatibility**: Docker 20+, Python 3.11+, Node.js 18+, Neo4j 5.0+, MSSQL Server 2019+, HubSpot API v3  
**Security**: Streamlit Authenticator 0.3.2, bcrypt password hashing, SSL/HTTPS support, ODBC 18+