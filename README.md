# AI-Powered Google Search MCP Integration Platform

A comprehensive full-stack application that provides AI-powered interactions with Google Search through Model Context Protocol (MCP) servers. This platform enables seamless web search and content extraction with optional HTTPS security and user authentication.

## 🚀 System Overview

This application consists of two integrated components:

1. **Streamlit Client** - AI chat interface with multi-provider support, authentication, and SSL support
2. **Google Search MCP Server** - Web search and content extraction via Google Custom Search API

### Architecture Diagram

```
┌─────────────────────┐    ┌─────────────────────┐
│   Streamlit Client  │    │  Google Search API  │
│                     │    │                     │
│  - AI Chat UI       │    │  - Web Search       │
│  - Authentication   │◄──►│  - Content Extract  │
│  - Multi-Provider   │    │  - Custom Search    │
│  - Tool Management  │    │                     │
│  - Conversation     │    └─────────────────────┘
│    History          │              ▲
│  - SSL Support      │              │
└─────────────────────┘              │
           ▲                    ┌────┴─────┐
           │                    │ Server 2 │
           │                    │ Google   │
           │                    │ Search   │
           │                    │ MCP      │
           │                    │ Server   │
           │                    └──────────┘
           │                         ▲
           │                         │
           └─────────────────────────┼────────────────
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
- Google Custom Search API key
- Google Custom Search Engine ID
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

# Google Search Configuration
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_custom_search_engine_id

# SSL Configuration (Optional)
SSL_ENABLED=true              # Enable HTTPS with self-signed certificates
```

### 2. Google Custom Search Setup

1. **Get API Key**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Custom Search API
   - Create credentials (API Key)

2. **Create Custom Search Engine**:
   - Go to [Google Custom Search](https://cse.google.com/cse/)
   - Create a new search engine
   - Configure to search the entire web or specific sites
   - Get the Search Engine ID (cx parameter)

### 3. User Authentication Setup

Generate user credentials for the application:

```bash
cd client
python simple_generate_password.py
```

This will create `keys/config.yaml` with default users. You can modify the user credentials as needed.

### 4. SSL Certificate Setup (Optional)

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
echo "🚀 Google Search MCP Client - Starting Application..."

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
        echo "🔒 Starting Streamlit with HTTPS on port 8503..."
        echo "📱 Access URL: https://localhost:8503"
        
        exec streamlit run app.py \
            --server.port=8503 \
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

### 5. Launch the Platform

```bash
# Build and start all services
docker-compose up --build

# Or start individual services
docker-compose up mcpserver2   # Google Search MCP Server
docker-compose up hostclient   # Streamlit Client
```

### 6. Access the Application

#### HTTPS Mode (Recommended)
- **Main Interface**: https://localhost:8503
- **Security**: Self-signed certificate (accept browser warning)

#### HTTP Mode (Default)
- **Main Interface**: http://localhost:8501
- **Alternative**: http://127.0.0.1:8501

#### Health Checks
- **Google Search Server Health**: http://localhost:8002/health

#### Authentication
Use the credentials generated in step 2 (default: admin/very_Secure_p@ssword_123!)

## 🎯 Key Features

### **AI-Powered Web Search**
- Multi-provider AI support (OpenAI, Azure OpenAI)
- Natural language queries for web search and content extraction
- Intelligent Google Search integration
- Conversation history and context management
- User authentication and session management

### **Security & Authentication**
- **User Authentication System**: Secure login with bcrypt password hashing
- **Session Management**: Persistent user sessions with configurable expiry
- **SSL/HTTPS Support**: Optional encrypted connections with self-signed certificates
- **Role-Based Access**: Pre-authorized email domains and user management
- **Secure Cookies**: Configurable authentication cookies with custom keys

### **Google Search Capabilities**
- **Web Search**: Comprehensive Google Custom Search API integration
- **Content Extraction**: Clean webpage content extraction with Cheerio
- **Research Workflows**: Combined search and content extraction
- **Real-time Results**: Current web information and news
- **Visual Results**: Structured data presentation

### **Complete Search Operations**
- **Web Search**: Query Google with customizable result counts
- **Content Reading**: Extract and clean content from web pages
- **Research Tools**: Multi-step search and analysis workflows
- **Source Validation**: URL verification and content quality checks

### **Technical Excellence**
- **Docker Containerization**: Easy deployment and scaling
- **SSL/HTTPS Support**: Secure connections with automatic certificate generation
- **Real-time Communication**: Server-Sent Events (SSE) for MCP
- **Schema Validation**: Comprehensive input validation with Zod
- **Error Handling**: Robust error management and debugging
- **Health Monitoring**: Built-in health checks and monitoring

## 📚 Usage Examples

### **Authentication Workflow**

```
1. Navigate to https://localhost:8503 (SSL) or http://localhost:8501 (HTTP)
2. Use the sidebar authentication panel
3. Login with generated credentials:
   - Username: admin, Password: very_Secure_p@ssword_123!
   - Username: demo_user, Password: strong_password_123!
4. Access the full application features
```

### **Web Search Workflows**

```
"Search for the latest developments in artificial intelligence"
"Find recent news about climate change"
"Search for Python programming tutorials"
"What are the current trends in web development?"
"Find information about the Model Context Protocol"
```

### **Content Extraction Workflows**

```
"Search for climate change reports and read the full content from the first result"
"Find the latest tech news and extract content from TechCrunch articles"
"Search for React documentation and read the official guide"
"Find research papers on machine learning and extract their abstracts"
```

### **Research Workflows**

```
"Research the current state of renewable energy technology"
"Find and analyze multiple sources about cryptocurrency trends"
"Search for the best practices in software engineering and summarize them"
"Compare different approaches to artificial intelligence from various sources"
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

### [🔍 Google Search MCP Server Documentation](./servers/server2/readme.md)
- Google Custom Search API integration
- Web search and content extraction tools
- Authentication and API key setup
- Performance optimization and troubleshooting
- Error handling and debugging

## 🛠️ Development & Customization

### **Local Development Setup**

```bash
# Clone the repository
git clone <your-repo-url>
cd <project-directory>

# Install dependencies for each component
cd client && pip install -r requirements.txt
cd ../servers/server2 && npm install
```

### **Google Custom Search Setup**

For Google Search integration, ensure you have:
- Google Cloud Console project with Custom Search API enabled
- Google Custom Search Engine configured
- API key with appropriate permissions
- Valid search engine ID (cx parameter)

### **Adding Custom Tools**

1. **Google Search Tools**: Extend the server with additional search operations
2. **Client Tools**: Integrate additional services via MCP protocol
3. **Custom Search Engines**: Configure specific search scopes

## 🔒 Security & Best Practices

### **API Security**
- Use secure API keys with proper scoping
- Implement rate limiting for search requests
- Enable SSL/TLS for all communications
- Regularly rotate API keys and credentials

### **Search Security**
- Validate all search queries and URLs
- Implement content filtering for extracted text
- Use proper error handling that doesn't expose sensitive data
- Monitor API usage and quotas

## 📊 Monitoring & Debugging

### **Health Checks**
- **Overall System**: Streamlit interface status indicators
- **Google Search Server**: http://localhost:8002/health

### **Search Monitoring**
- API usage tracking and quota monitoring
- Search query performance and response times
- Error rates and failed requests
- Content extraction success rates

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
- Configure proper SSL certificates
- Implement proper secret management
- Set up monitoring and alerting
- Use connection pooling for high-traffic scenarios

## 🐛 Troubleshooting

### **Common Issues**

**Google API Connection Problems**
- Verify GOOGLE_API_KEY is correct and active
- Check Custom Search Engine ID configuration
- Verify API quotas and billing setup
- Ensure Custom Search API is enabled in Google Cloud Console

**Search Quality Issues**
- Review Custom Search Engine configuration
- Adjust search parameters and result counts
- Check for API rate limiting
- Verify search query formatting

**Content Extraction Issues**
- Check website accessibility and robots.txt
- Verify URL formatting and validity
- Monitor request timeouts and failures
- Review content parsing and cleaning logic

## 🤝 Contributing

### **Development Workflow**
1. Fork the repository
2. Create feature branches for each component
3. Test authentication and security features
4. Test Google Search functionality and content extraction
5. Submit pull requests with comprehensive testing

### **Search Testing**
- Test various search queries and scenarios
- Verify content extraction from different websites
- Test error handling and edge cases
- Validate API quota management

---

**Version**: 2.0.0  
**Last Updated**: June 2025  
**Compatibility**: Docker 20+, Python 3.11+, Node.js 18+, Google Custom Search API v1  
**Security**: Streamlit Authenticator 0.3.2, bcrypt password hashing, SSL/HTTPS support  
**Tools**: 2 Google Search tools (web search, content extraction)