# AI-Powered CRM & Graph Database Integration Platform

A comprehensive full-stack application that provides AI-powered interactions with Neo4j graph databases and HubSpot CRM systems through Model Context Protocol (MCP) servers. This platform enables seamless data analysis, management, and automation across your database and CRM infrastructure with optional HTTPS security.

## 🚀 System Overview

This application consists of three integrated components:

1. **Streamlit Client** - AI chat interface with multi-provider support, authentication, and SSL support
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
│  - Tool Management  │    │  - SSL/HTTPS        │    │                     │
│  - Conversation     │    └─────────────────────┘    └─────────────────────┘
│    History          │              ▲                          ▲
│  - SSL Support      │              │                          │
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

### 4. Update Docker Configuration

Ensure your `client/Dockerfile` uses the startup script:

```dockerfile
# Add this to your Dockerfile after copying files
COPY startup_ssl.sh generate_ssl_certificate.sh ./
RUN chmod +x startup_ssl.sh generate_ssl_certificate.sh

# Replace the CMD line with:
CMD ["./startup_ssl.sh"]
```

Update `docker-compose.yml` for the hostclient service:

```yaml
hostclient:
  # ... other configuration ...
  command: ["./startup_ssl.sh"]
```

```bash
# Build and start all services
docker-compose up --build

# Or start individual services
docker-compose up mcpserver4  # Neo4j MCP Server
docker-compose up mcpserver5  # HubSpot MCP Server  
docker-compose up hostclient  # Streamlit Client
```

### 5. Launch the Platform

### 6. Access the Application
- **Main Interface**: https://localhost:8502
- **Security**: Self-signed certificate (accept browser warning)

#### HTTP Mode (Default)
- **Main Interface**: http://localhost:8501
- **Alternative**: http://127.0.0.1:8501

#### Health Checks
- **Neo4j Server Health**: http://localhost:8003/health
- **HubSpot Server Health**: http://localhost:8004/health

#### Authentication
Use the credentials generated in step 2 (default: admin/very_Secure_p@ssword_123!)

## 🔒 SSL/HTTPS Configuration

### Security Features
- **Self-signed SSL certificates** for development and testing
- **RSA 2048-bit encryption** with SHA-256 hashing
- **Multiple domain support** (localhost, 127.0.0.1, 0.0.0.0)
- **365-day certificate validity**
- **Automatic certificate generation**

### SSL Setup Options

#### Docker Compose (Recommended)
```bash
# Enable SSL in environment
echo "SSL_ENABLED=true" >> .env

# Start with SSL support - certificates generated automatically
docker-compose up --build

# Access via HTTPS
# URL: https://localhost:8502
```

#### Local Development
```bash
# Ensure startup script exists and is executable
cd client
chmod +x startup_ssl.sh

# Start with SSL
SSL_ENABLED=true ./startup_ssl.sh

# Access via HTTPS
# URL: https://localhost:8502
```

#### Manual Certificate Generation
```bash
# Cross-platform Python method
cd client
python generate_ssl_certificate.py

# Linux/Mac shell script method (after creating startup script)
./generate_ssl_certificate.sh

# Windows PowerShell method
mkdir ssl
openssl genrsa -out ssl/private.key 2048
openssl req -new -x509 -key ssl/private.key -out ssl/cert.pem -days 365 -subj "/CN=localhost"
```

### Browser Security Warnings

Self-signed certificates will trigger browser security warnings:

- **Chrome/Edge**: Click "Advanced" → "Proceed to localhost (unsafe)"
- **Firefox**: Click "Advanced" → "Accept the Risk and Continue"  
- **Safari**: Click "Show Details" → "Visit this website"

This is expected behavior and safe for development environments.

### SSL File Structure
```
client/
├── ssl/
│   ├── cert.pem              # SSL certificate
│   └── private.key           # Private key (600 permissions)
├── startup_ssl.sh            # Main startup script (executable)
├── generate_ssl_certificate.py
├── generate_ssl_certificate.sh
└── debug_ssl.sh              # Debug script (optional)
```

## 🎯 Key Features

### **AI-Powered Interactions**
- Multi-provider AI support (OpenAI, Azure OpenAI)
- Natural language queries for database and CRM operations
- Intelligent tool selection and execution
- Conversation history and context management
- User authentication and session management

### **Security & Authentication**
- **User Authentication System**: Secure login with bcrypt password hashing
- **Session Management**: Persistent user sessions with configurable expiry
- **SSL/HTTPS Support**: Optional encrypted connections with self-signed certificates
- **Role-Based Access**: Pre-authorized email domains and user management
- **Secure Cookies**: Configurable authentication cookies with custom keys

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

### **SSL Certificate Management**

```bash
# Check certificate status
cd client
./debug_ssl.sh    # If you created the debug script

# Generate new certificates
python generate_ssl_certificate.py

# Manual verification
openssl x509 -in ssl/cert.pem -text -noout | head -10

# Check certificate expiry
openssl x509 -in ssl/cert.pem -enddate -noout

# Test SSL connection
curl -k https://localhost:8502

# Renew certificates (after 365 days)
rm ssl/*.pem ssl/*.key
python generate_ssl_certificate.py
docker-compose restart hostclient
```

### **Adding Custom Tools**

1. **Neo4j Tools**: Extend the Neo4j server with custom Cypher operations
2. **HubSpot Tools**: Add new HubSpot API integrations
3. **Client Tools**: Integrate additional services via MCP protocol

### **Configuration Management**

- **Client**: Update `servers_config.json` for MCP server endpoints
- **Authentication**: Modify `client/simple_generate_password.py` for user management
- **SSL**: Configure certificate paths in environment variables
- **Neo4j**: Modify connection parameters in environment variables
- **HubSpot**: Configure API scopes and permissions in HubSpot Developer Console

## 🔒 Security & Best Practices

### **SSL/HTTPS Security**
- Self-signed certificates for development environments
- RSA 2048-bit encryption with SHA-256 hashing
- Automatic certificate generation and validation
- Secure file permissions (600 for private keys)
- Browser security warning handling

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
- Configurable port mapping (8501 HTTP, 8502 HTTPS)
- Health check endpoints for monitoring
- CORS configuration for secure API access

### **Data Protection**
- Schema validation for database operations
- Sanitized error messages and logging
- User session isolation and management
- SSL certificate management and rotation

### **Production Security Considerations**

⚠️ **Important for Production**:
- Replace self-signed certificates with CA-signed certificates
- Use Let's Encrypt for free SSL certificates
- Implement proper certificate management and rotation
- Use a reverse proxy (nginx, traefik) for SSL termination
- Enable security headers and HSTS
- Regular security audits and updates

## 📊 Monitoring & Debugging

### **Health Checks**
- **Overall System**: Streamlit interface status indicators
- **Authentication**: User session and login status monitoring
- **SSL Status**: Certificate validity and expiration monitoring
- **Neo4j Server**: http://localhost:8003/health
- **HubSpot Server**: http://localhost:8004/health

### **SSL Certificate Monitoring**
```bash
# Check certificate validity
openssl x509 -in client/ssl/cert.pem -text -noout

# Check certificate expiration
openssl x509 -in client/ssl/cert.pem -enddate -noout

# Test SSL connection
openssl s_client -connect localhost:8502 -verify_return_error
```

### **Debugging Tools**
- Tool execution history in Streamlit interface
- User session and authentication logging
- SSL connection debugging and certificate validation
- Comprehensive logging across all components
- Error tracking and validation feedback

### **Performance Monitoring**
- Query execution timing
- API request/response monitoring
- SSL handshake performance
- Resource usage tracking in Docker
- User session and authentication metrics

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
- Configure reverse proxy (nginx, traefik) with proper SSL certificates
- Implement proper secret management
- Set up monitoring and alerting
- Configure SSL/TLS certificates from trusted CA
- Use secure authentication configurations
- Enable security headers and HSTS

### **SSL Production Setup**
```bash
# Use Let's Encrypt certificates
certbot certonly --standalone -d yourdomain.com

# Configure reverse proxy (nginx example)
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **Scaling Considerations**
- Horizontal scaling of MCP servers
- Load balancing for high-traffic scenarios
- Database connection pooling
- SSL termination at load balancer level
- Caching strategies for frequently accessed data
- User session management across multiple instances

## 🐛 Troubleshooting

### **Common Issues**

**Authentication Problems**
- Verify `keys/config.yaml` exists and is properly configured
- Check user credentials and email permissions
- Ensure cookie configuration is correct

**SSL/HTTPS Issues**
- **Certificate not found**: 
  ```bash
  cd client
  python generate_ssl_certificate.py
  chmod +x startup_ssl.sh
  ```
- **Browser security warning**: Click "Advanced" → "Proceed to localhost (unsafe)"
- **Connection refused on 8502**: 
  ```bash
  # Ensure SSL is enabled and startup script is executable
  echo "SSL_ENABLED=true" >> .env
  chmod +x client/startup_ssl.sh
  docker-compose down && docker-compose up --build
  ```
- **Port 8501 instead of 8502**: 
  ```bash
  # Check if startup script is being used
  docker-compose logs hostclient | grep "Starting Streamlit"
  # Should show port 8502 for HTTPS mode
  ```
- **Certificate expired**: 
  ```bash
  # Regenerate certificates after 365 days
  rm client/ssl/*.pem client/ssl/*.key
  docker-compose restart hostclient
  ```

**Connection Problems**
- Verify all services are running: `docker-compose ps`
- Check network connectivity between containers
- Validate environment variables and credentials
- Test both HTTP (8501) and HTTPS (8502) ports

**API Authentication Errors**
- Confirm API keys are correctly set in `.env`
- Verify HubSpot Private App permissions
- Check Neo4j database accessibility

**Tool Execution Failures**
- Review tool execution history in Streamlit
- Check individual server health endpoints
- Validate input parameters and data formats

### **SSL Troubleshooting Commands**

```bash
# Debug SSL setup
cd client
./debug_ssl.sh  # If debug script exists

# Check container logs
docker-compose logs hostclient

# Verify startup script
docker-compose exec hostclient cat startup_ssl.sh

# Test certificate generation manually
docker-compose exec hostclient ./generate_ssl_certificate.sh

# Verify certificate details
docker-compose exec hostclient openssl x509 -in ssl/cert.pem -text -noout

# Test SSL connection
curl -k https://localhost:8502

# Check file permissions
docker-compose exec hostclient ls -la ssl/

# Restart with fresh certificates
docker-compose exec hostclient rm -rf ssl/
docker-compose restart hostclient
```

### **Getting Help**
- Review component-specific documentation
- Check Docker logs: `docker-compose logs <service>`
- Use health check endpoints for diagnostics
- Verify authentication and user permissions
- Test both HTTP and HTTPS modes
- Check SSL certificate validity and permissions

## 🤝 Contributing

### **Development Workflow**
1. Fork the repository
2. Create feature branches for each component
3. Follow component-specific development guidelines
4. Test authentication and security features
5. Test both HTTP and HTTPS modes
6. Submit pull requests with comprehensive testing

### **Code Standards**
- **Python**: PEP 8 compliance for client and Neo4j server
- **JavaScript**: ES6+ standards for HubSpot server
- **Docker**: Multi-stage builds and security best practices
- **Documentation**: Comprehensive README and inline comments
- **Security**: Follow authentication and SSL security best practices

### **SSL Development Guidelines**
- Test certificate generation on multiple platforms
- Verify SSL functionality in different browsers  
- Document certificate renewal procedures
- Follow security best practices for certificate storage
- Test fallback mechanisms for SSL failures
- Ensure startup scripts are executable (`chmod +x`)
- Verify proper Docker command configuration
- Test both HTTP (8501) and HTTPS (8502) modes

### **Required Files for SSL Support**

Ensure these files exist in your `client/` directory:

```bash
# Check required files
ls -la client/startup_ssl.sh              # Main startup script
ls -la client/generate_ssl_certificate.sh # Certificate generation
ls -la client/generate_ssl_certificate.py # Python alternative
ls -la client/ssl/                        # SSL certificates directory

# Create missing files if needed
cd client

# Create startup script (if missing)
cat > startup_ssl.sh << 'EOF'
#!/bin/bash
# [Full script content from artifacts above]
EOF
chmod +x startup_ssl.sh

# Ensure Docker configuration uses startup script
grep "startup_ssl.sh" Dockerfile || echo "Add startup_ssl.sh to Dockerfile CMD"
grep "startup_ssl.sh" ../docker-compose.yml || echo "Update docker-compose.yml command"
```

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [HubSpot API Documentation](https://developers.hubspot.com/docs/api/overview)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Authenticator Documentation](https://github.com/mkhorasani/Streamlit-Authenticator)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [OpenSSL Documentation](https://www.openssl.org/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

## 🔗 Additional Resources

**Version**: 2.1.0  
**Last Updated**: June 2025  
**Compatibility**: Docker 20+, Python 3.11+, Node.js 18+, Neo4j 5.0+  
**Security**: Streamlit Authenticator 0.3.2, bcrypt password hashing, SSL/HTTPS support  
**SSL Support**: Self-signed certificates for development, production-ready SSL configuration