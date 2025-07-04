# AI-Powered Search MCP Integration Platform

A comprehensive full-stack application that provides AI-powered interactions with Google Search and Perplexity AI through Model Context Protocol (MCP) servers. This platform enables seamless web search, AI-powered analysis, and content extraction with optional HTTPS security and user authentication.

## 🚀 System Overview

This application consists of three integrated components:

1. **Streamlit Client** - AI chat interface with multi-provider support, authentication, and SSL support
2. **Google Search MCP Server** - Web search and content extraction via Google Custom Search API
3. **Perplexity MCP Server** - AI-powered search with intelligent analysis via Perplexity API

### Architecture Diagram

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Streamlit Client  │    │  Google Search API  │    │  Perplexity AI API  │
│                     │    │                     │    │                     │
│  - AI Chat UI       │    │  - Web Search       │    │  - AI Search        │
│  - Authentication   │◄──►│  - Content Extract  │    │  - Smart Analysis   │
│  - Multi-Provider   │    │  - Custom Search    │    │  - Multiple Models  │
│  - Tool Management  │    │                     │    │                     │
│  - Conversation     │    └─────────────────────┘    └─────────────────────┘
│    History          │              ▲                          ▲
│  - SSL Support      │              │                          │
└─────────────────────┘              │                          │
           ▲                    ┌────┴─────┐              ┌────┴─────┐
           │                    │ Server 2 │              │ Server 1 │
           │                    │ Google   │              │Perplexity│
           │                    │ Search   │              │ Search   │
           │                    │ MCP      │              │ MCP      │
           │                    │ Server   │              │ Server   │
           │                    └──────────┘              └──────────┘
           │                         ▲                          ▲
           │                         │                          │
           └─────────────────────────┼──────────────────────────┼────────────────
                                     │                          │
                              ┌───────────────┐          ┌───────────────┐
                              │     MCP       │          │     MCP       │
                              │  Protocol     │          │  Protocol     │
                              │ Communication │          │ Communication │
                              └───────────────┘          └───────────────┘
```

## ⚡ Quick Start

### Prerequisites
- Docker & Docker Compose
- Google Custom Search API key & Search Engine ID
- Perplexity API key
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

# Perplexity Configuration
PERPLEXITY_API_KEY=your_perplexity_api_key
PERPLEXITY_MODEL=sonar

# SSL Configuration (Optional)
SSL_ENABLED=true
```

### 2. API Setup

#### Google Custom Search Setup
1. **Get API Key**: Go to [Google Cloud Console](https://console.cloud.google.com/), enable Custom Search API, create credentials
2. **Create Custom Search Engine**: Go to [Google Custom Search](https://cse.google.com/cse/), create new search engine, get Search Engine ID

#### Perplexity API Setup
1. **Get API Key**: Sign up at [Perplexity AI](https://perplexity.ai) and get your API key
2. **Choose Model**: Select from available models (sonar, sonar-pro, sonar-reasoning, etc.)

### 3. User Authentication Setup

Generate user credentials for the application:

```bash
cd client
python simple_generate_password.py
```

This creates `keys/config.yaml` with default users. You can modify user credentials as needed.

### 4. SSL Certificate Setup (Optional)

For HTTPS support, certificates will be generated automatically when `SSL_ENABLED=true`.

### 5. Launch the Platform

```bash
# Build and start all services
docker-compose up --build

# Or start individual services
docker-compose up mcpserver1    # Perplexity MCP Server
docker-compose up mcpserver2    # Google Search MCP Server  
docker-compose up hostclient    # Streamlit Client
```

### 6. Access the Application

#### HTTPS Mode (Recommended)
- **Main Interface**: https://localhost:8503
- **Security**: Self-signed certificate (accept browser warning)

#### HTTP Mode (Default)
- **Main Interface**: http://localhost:8501
- **Alternative**: http://127.0.0.1:8501

#### Health Checks
- **Google Search Server**: http://localhost:8002/health
- **Perplexity Server**: http://localhost:8001/health

#### Authentication
Use the credentials generated in step 2 (default: admin/very_Secure_p@ssword_123!)

## 🎯 Key Features

### **Dual Search Engine Integration**
- **Google Search Tools**: Comprehensive web search and content extraction
- **Perplexity AI Tools**: AI-powered search with intelligent analysis and synthesis
- **Multi-provider AI support** (OpenAI, Azure OpenAI)
- **Intelligent tool selection** based on query type and requirements

### **Advanced Search Capabilities**

#### **Google Search Operations**
- **Web Search**: Comprehensive Google Custom Search API integration
- **Content Extraction**: Clean webpage content extraction with Cheerio
- **Research Workflows**: Combined search and content extraction
- **Visual Results**: Structured data presentation

#### **Perplexity AI Operations**
- **AI-Powered Search**: Intelligent web search with AI analysis
- **Multiple Models**: Support for all Perplexity models (sonar, sonar-pro, sonar-reasoning, etc.)
- **Recency Filtering**: Filter results by time period (day, week, month, year)
- **Advanced Parameters**: Fine-tune search with temperature, max tokens, etc.

### **Security & Authentication**
- **User Authentication System**: Secure login with bcrypt password hashing
- **Session Management**: Persistent user sessions with configurable expiry
- **SSL/HTTPS Support**: Optional encrypted connections with self-signed certificates
- **Role-Based Access**: Pre-authorized email domains and user management

### **Technical Excellence**
- **Docker Containerization**: Easy deployment and scaling with 3 services
- **SSL/HTTPS Support**: Secure connections with automatic certificate generation
- **Real-time Communication**: Server-Sent Events (SSE) for both MCP servers
- **Schema Validation**: Comprehensive input validation with Zod
- **Error Handling**: Robust error management and debugging
- **Health Monitoring**: Built-in health checks for all services

## 📚 Usage Examples

### **Authentication Workflow**
```
1. Navigate to https://localhost:8503 (SSL) or http://localhost:8501 (HTTP)
2. Use the sidebar authentication panel
3. Login with generated credentials
4. Access the full application features
```

### **Search Workflows**

#### **Quick Facts and Current Information**
```
"What are the latest developments in artificial intelligence?"
"Find recent news about climate change"
"What's the current status of renewable energy adoption?"
```
*Uses Perplexity tools for AI-synthesized responses with citations*

#### **Comprehensive Research**
```
"Research the impact of AI on healthcare industry"
"Find detailed information about sustainable farming practices"
"Analyze market trends in electric vehicles"
```
*Uses Google Search to find sources, then extracts detailed content*

#### **Hybrid Research Workflows**
```
"Compare different approaches to renewable energy and analyze their effectiveness"
"Research current cybersecurity threats and provide analysis of mitigation strategies"
```
*Uses both tool sets for comprehensive coverage and analysis*

### **Advanced Search Parameters**

#### **Perplexity Advanced Search**
```
"Search for climate change research with high detail and recent sources"
# Uses perplexity_advanced_search with:
# - recency: "month"
# - max_tokens: 1500
# - temperature: 0.2 (for factual accuracy)
```

#### **Google Search with Content Extraction**
```
"Find the latest React documentation and read the full getting started guide"
# Uses google-search followed by read-webpage for detailed content
```

## 🔧 Component Documentation

### [🖥️ Streamlit Client Documentation](./client/Readme.md)
- Authentication system setup and configuration
- SSL/HTTPS configuration and certificate management
- AI provider setup and management
- Tool execution monitoring

### [🔍 Google Search MCP Server Documentation](./servers/server2/readme.md)
- Google Custom Search API integration
- Web search and content extraction tools
- Performance optimization and troubleshooting

### [🔮 Perplexity MCP Server Documentation](./servers/server1/readme.md)
- Perplexity AI API integration
- AI-powered search with multiple models
- Advanced search parameters and filtering

## 🛠️ Development & Customization

### **Local Development Setup**
```bash
# Clone the repository
git clone <your-repo-url>
cd <project-directory>

# Install dependencies for each component
cd client && pip install -r requirements.txt
cd ../servers/server1 && pip install -r requirements.txt
cd ../servers/server2 && npm install
```

### **API Configuration**
Ensure you have:
- **Google Cloud Console project** with Custom Search API enabled
- **Google Custom Search Engine** configured for web search
- **Perplexity API account** with valid API key
- **OpenAI or Azure OpenAI** credentials for the AI client

### **Adding Custom Tools**
1. **Google Search Tools**: Extend server2 with additional search operations
2. **Perplexity Tools**: Add new Perplexity-powered analysis tools
3. **Client Tools**: Integrate additional services via MCP protocol

## 🔒 Security & Best Practices

### **API Security**
- Use secure API keys with proper scoping
- Implement rate limiting for search requests
- Enable SSL/TLS for all communications
- Regularly rotate API keys and credentials

### **Search Security**
- Validate all search queries and URLs
- Implement content filtering for extracted text
- Monitor API usage and quotas for both services
- Use proper error handling that doesn't expose sensitive data

## 📊 Monitoring & Debugging

### **Health Checks**
- **Overall System**: Streamlit interface status indicators
- **Google Search Server**: http://localhost:8002/health
- **Perplexity Server**: http://localhost:8001/health

### **Search Monitoring**
- API usage tracking for both Google and Perplexity
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
- Set up monitoring and alerting for all 3 services
- Use connection pooling for high-traffic scenarios

## 🐛 Troubleshooting

### **Common Issues**

**Google API Connection Problems**
- Verify GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID
- Check Custom Search API quota and billing
- Ensure Custom Search Engine is configured for web search

**Perplexity API Issues**
- Verify PERPLEXITY_API_KEY is correct and active
- Check API quotas and billing status
- Ensure selected PERPLEXITY_MODEL is available

**MCP Server Connection Issues**
- Check that both servers are running (ports 8001 and 8002)
- Verify network connectivity between services
- Review server logs for detailed error information

**Authentication Problems**
- Verify `keys/config.yaml` exists and is properly formatted
- Check user credentials match generated passwords
- Clear browser cookies if experiencing login issues

## 🤝 Contributing

### **Development Workflow**
1. Fork the repository
2. Create feature branches for each component
3. Test authentication and security features
4. Test both Google and Perplexity search functionality
5. Submit pull requests with comprehensive testing

### **Search Testing**
- Test various search queries and scenarios with both engines
- Verify content extraction from different websites
- Test error handling and edge cases
- Validate API quota management for both services

---

**Version**: 2.0.0  
**Last Updated**: July 2025  
**Compatibility**: Docker 20+, Python 3.11+, Node.js 18+, Google Custom Search API v1, Perplexity API v1  
**Security**: Streamlit Authenticator 0.3.2, bcrypt password hashing, SSL/HTTPS support  
**Tools**: 4 total tools (2 Google Search, 2 Perplexity AI)  
**Servers**: 3 services (Client, Google Search MCP, Perplexity MCP)