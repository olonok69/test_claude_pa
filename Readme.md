# AI-Powered Search MCP Integration Platform

A comprehensive full-stack application that provides AI-powered interactions with Google Search and Perplexity AI through Model Context Protocol (MCP) servers. This platform enables seamless web search, AI-powered analysis, and content extraction with optional HTTPS security and user authentication.

## 🚀 System Overview

This application consists of three integrated components working together to provide comprehensive AI-powered search capabilities:

1. **Streamlit Client** - AI chat interface with multi-provider support, authentication, and SSL support
2. **Google Search MCP Server** - Web search and content extraction via Google Custom Search API
3. **Perplexity MCP Server** - AI-powered search with intelligent analysis via Perplexity API

## 🏗️ System Architecture

![Architecture Diagram](docs/mcp_platform_architecture.svg)

## 📋 Port Reference Table

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| **Streamlit HTTP** | 8501 | HTTP | Main web interface |
| **Streamlit HTTPS** | 8503 | HTTPS | Secure web interface (recommended) |
| **Google Search MCP** | 8002 | HTTP/SSE | Web search server |
| **Perplexity MCP** | 8001 | HTTP/SSE | AI search server |
| **Company Tagging** | - | stdio | Embedded MCP server |

## 🔧 Core Technologies & Dependencies

This platform is built using modern, robust technologies that enable scalable AI-powered search capabilities. Here's a comprehensive overview of the key technologies and their roles:

### **🌐 Frontend & User Interface**

#### **[Streamlit](https://streamlit.io/)** - Web Application Framework
- **Purpose**: Primary web interface for user interactions
- **Version**: 1.44+
- **Why**: Rapid development of data applications with built-in authentication
- **Features**: Real-time updates, component system, session management
- **Documentation**: [Streamlit Docs](https://docs.streamlit.io/)

#### **[Streamlit Authenticator](https://github.com/mkhorasani/Streamlit-Authenticator)** - Authentication System
- **Purpose**: Secure user login and session management
- **Version**: 0.3.2
- **Why**: bcrypt password hashing, role-based access control
- **Features**: Session persistence, secure cookies, user management
- **Security**: Industry-standard password hashing and validation

### **🧠 AI & Language Models**

#### **[LangChain](https://python.langchain.com/)** - AI Framework
- **Purpose**: AI agent orchestration and tool routing
- **Version**: 0.3.20+
- **Why**: Standardized AI model integration with tool calling
- **Features**: ReAct agents, memory management, tool execution
- **Documentation**: [LangChain Docs](https://python.langchain.com/docs/introduction/)

#### **[OpenAI API](https://openai.com/api/)** - AI Language Models
- **Purpose**: Primary AI provider for intelligent responses
- **Models**: GPT-4o, GPT-4o-mini
- **Why**: State-of-the-art language understanding and generation
- **Features**: Tool calling, streaming responses, context handling
- **Documentation**: [OpenAI API Docs](https://platform.openai.com/docs)

#### **[Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)** - Enterprise AI
- **Purpose**: Alternative AI provider for enterprise deployments
- **Models**: GPT-4o, o3-mini
- **Why**: Enterprise features, data residency, enhanced security
- **Features**: Private endpoints, compliance, SLA guarantees
- **Documentation**: [Azure OpenAI Docs](https://learn.microsoft.com/en-us/azure/ai-services/openai/)

### **🔍 Search & Data Sources**

#### **[Google Custom Search API](https://developers.google.com/custom-search)** - Web Search Engine
- **Purpose**: Comprehensive web search capabilities
- **Version**: v1
- **Why**: Reliable, high-quality search results with customization
- **Features**: Custom search engines, result filtering, metadata
- **Documentation**: [Google Custom Search Docs](https://developers.google.com/custom-search/v1/overview)

#### **[Perplexity AI API](https://www.perplexity.ai/)** - AI-Powered Search
- **Purpose**: Intelligent search with AI-generated responses
- **Models**: sonar, sonar-pro, sonar-reasoning
- **Why**: Combines search with AI analysis and citations
- **Features**: Recency filtering, model selection, advanced parameters
- **Documentation**: [Perplexity API Docs](https://docs.perplexity.ai/)

### **🔗 Communication Protocols**

#### **[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)** - Standardized AI Communication
- **Purpose**: Universal protocol for AI tool integration
- **Version**: 1.0+
- **Why**: Vendor-agnostic standard for AI tool communication
- **Features**: Tool discovery, schema validation, transport flexibility
- **Documentation**: [MCP Specification](https://spec.modelcontextprotocol.io/)

#### **[Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)** - Real-time Communication
- **Purpose**: Real-time bidirectional communication for external MCP servers
- **Why**: Efficient streaming, browser-compatible, low latency
- **Features**: Automatic reconnection, message ordering, multiplexing
- **Documentation**: [MDN SSE Docs](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

#### **stdio Transport** - Local Process Communication
- **Purpose**: Embedded MCP server communication within containers
- **Why**: Zero network latency, simplified deployment, better security
- **Features**: Process isolation, error handling, lifecycle management

### **🐳 Infrastructure & Deployment**

#### **[Docker](https://www.docker.com/)** - Containerization Platform
- **Purpose**: Consistent deployment across environments
- **Version**: 20+
- **Why**: Environment isolation, scalability, dependency management
- **Features**: Multi-container orchestration, health checks, volume mounting
- **Documentation**: [Docker Docs](https://docs.docker.com/)

#### **[Docker Compose](https://docs.docker.com/compose/)** - Multi-Container Orchestration
- **Purpose**: Coordinated deployment of multiple services
- **Why**: Service dependencies, networking, environment management
- **Features**: Service scaling, configuration management, logging
- **Documentation**: [Docker Compose Docs](https://docs.docker.com/compose/)

### **🐍 Backend Technologies (Python)**

#### **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python Web Framework
- **Purpose**: High-performance API servers for MCP services
- **Why**: Automatic OpenAPI generation, type validation, async support
- **Features**: Dependency injection, middleware, authentication
- **Documentation**: [FastAPI Docs](https://fastapi.tiangolo.com/)

#### **[asyncio](https://docs.python.org/3/library/asyncio.html)** - Asynchronous Programming
- **Purpose**: Concurrent request handling and I/O operations
- **Why**: High performance, scalable concurrent operations
- **Features**: Event loops, coroutines, task management
- **Documentation**: [asyncio Docs](https://docs.python.org/3/library/asyncio.html)

#### **[Pydantic](https://pydantic.dev/)** - Data Validation
- **Purpose**: Type-safe data validation and serialization
- **Version**: 2.0+
- **Why**: Runtime type checking, automatic validation, JSON schema
- **Features**: Custom validators, error handling, serialization
- **Documentation**: [Pydantic Docs](https://docs.pydantic.dev/)

### **🟢 Backend Technologies (Node.js)**

#### **[Node.js](https://nodejs.org/)** - JavaScript Runtime
- **Purpose**: High-performance server for Google Search MCP server
- **Version**: 18+
- **Why**: Fast I/O operations, npm ecosystem, V8 engine
- **Features**: Event-driven architecture, non-blocking I/O
- **Documentation**: [Node.js Docs](https://nodejs.org/docs/)

#### **[Express.js](https://expressjs.com/)** - Web Application Framework
- **Purpose**: HTTP server framework for MCP SSE endpoints
- **Version**: 5.1+
- **Why**: Lightweight, flexible, extensive middleware ecosystem
- **Features**: Routing, middleware, template engines
- **Documentation**: [Express.js Docs](https://expressjs.com/)

#### **[Cheerio](https://cheerio.js.org/)** - Server-side HTML Parsing
- **Purpose**: Extract and clean content from web pages
- **Version**: 1.0+
- **Why**: jQuery-like server-side HTML manipulation
- **Features**: CSS selectors, DOM manipulation, text extraction
- **Documentation**: [Cheerio Docs](https://cheerio.js.org/)

### **🔒 Security Technologies**

#### **[bcrypt](https://github.com/pyca/bcrypt/)** - Password Hashing
- **Purpose**: Secure password storage and validation
- **Version**: 4.0+
- **Why**: Industry-standard password hashing with salt
- **Features**: Adaptive hashing, configurable cost, timing attack resistance
- **Documentation**: [bcrypt Docs](https://github.com/pyca/bcrypt/)

#### **[OpenSSL](https://www.openssl.org/)** - SSL/TLS Encryption
- **Purpose**: HTTPS support and certificate generation
- **Why**: Industry-standard encryption, certificate management
- **Features**: Self-signed certificates, key generation, encryption
- **Documentation**: [OpenSSL Docs](https://www.openssl.org/docs/)

#### **[cryptography](https://cryptography.io/)** - Python Cryptographic Library
- **Purpose**: Certificate generation and cryptographic operations
- **Version**: 42.0+
- **Why**: High-level cryptographic recipes and primitives
- **Features**: X.509 certificates, key generation, secure random
- **Documentation**: [Cryptography Docs](https://cryptography.io/)

## 🏗️ Technology Integration Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Streamlit UI   │    │   LangChain     │    │  External APIs  │
│                 │    │                 │    │                 │
│ • Python 3.11+  │◄──►│ • AI Agents     │◄──►│ • Google Search │
│ • Authentication│    │ • Tool Routing  │    │ • Perplexity AI │
│ • SSL/HTTPS     │    │ • Memory Mgmt   │    │ • OpenAI/Azure  │
│ • Session Mgmt  │    │ • React Agents  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │              ┌────────┴────────┐              │
         │              │  MCP Protocol   │              │
         │              │                 │              │
         │              │ • SSE Transport │              │
         │              │ • stdio Transport│             │
         │              │ • Tool Discovery│              │
         │              │ • Schema Valid. │              │
         │              └─────────────────┘              │
         ▼                                               ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Google MCP    │    │ Perplexity MCP  │    │ Company Tagging │
│                 │    │                 │    │                 │
│ • Node.js 18+   │    │ • Python 3.11+  │    │ • Python 3.11+  │
│ • Express.js    │    │ • FastAPI       │    │ • stdio MCP     │
│ • Cheerio       │    │ • aiohttp       │    │ • CSV Processing│
│ • Zod Validation│    │ • Pydantic      │    │ • Embedded      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
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
Use the credentials generated in step 3 (default: admin/very_Secure_p@ssword_123!)

## 🎯 Key Features

### **Dual Search Engine Integration**
- **Google Search Tools**: Comprehensive web search and content extraction using Google Custom Search API
- **Perplexity AI Tools**: AI-powered search with intelligent analysis and synthesis
- **Multi-provider AI support** (OpenAI, Azure OpenAI with enhanced configuration support)
- **Intelligent tool selection** based on query type and requirements

### **Advanced Search Capabilities**

#### **Google Search Operations (2 Tools)**
- **google-search**: Comprehensive Google Custom Search API integration with 1-10 configurable results
- **read-webpage**: Clean webpage content extraction with Cheerio parsing and automatic cleanup
- **Research Workflows**: Combined search and content extraction for comprehensive research
- **Visual Results**: Structured data presentation with JSON formatting

#### **Perplexity AI Operations (3 Tools)**
- **perplexity_search_web**: Standard AI-powered web search with intelligent responses and citations
- **perplexity_advanced_search**: Advanced search with custom model parameters, temperature control, and token limits
- **search_show_categories**: Access to comprehensive CSV-based category taxonomy for trade shows
- **Recency Filtering**: Filter results by time period (day, week, month, year)
- **Multiple Models**: Support for sonar, sonar-pro, sonar-reasoning, and other Perplexity models

#### **Company Tagging Operations (Embedded MCP Server)**
- **Company Research & Categorization**: Specialized stdio-based MCP server for trade show exhibitor analysis
- **Taxonomy Management**: Access to structured industry/product categories for 5 major trade shows
- **CSV Data Access**: Real-time access to categories data with filtering and search capabilities
- **Integrated Workflow**: Seamless company analysis using both Google Search and Perplexity tools

### **Security & Authentication**
- **User Authentication System**: Secure login with bcrypt password hashing
- **Session Management**: Persistent user sessions with configurable expiry (30 days default)
- **SSL/HTTPS Support**: Optional encrypted connections with self-signed certificates on port 8503
- **Role-Based Access**: Pre-authorized email domains and user management

### **Technical Excellence**
- **Docker Containerization**: Easy deployment and scaling with 3 services
- **SSL/HTTPS Support**: Secure connections with automatic certificate generation
- **Real-time Communication**: Server-Sent Events (SSE) for both external MCP servers
- **Stdio Integration**: Embedded Company Tagging MCP server for specialized workflows
- **Schema Validation**: Comprehensive input validation with Zod
- **Error Handling**: Robust error management and debugging
- **Health Monitoring**: Built-in health checks for all services

## 📚 Available Tools & Capabilities

### **Total Tools Available: 6 Tools**

#### **Google Search MCP Server (2 Tools)**
1. **google-search**
   - Perform Google searches with 1-10 configurable results
   - Returns titles, links, snippets, and total result counts
   - Uses Google Custom Search API with full web coverage

2. **read-webpage**
   - Extract clean content from any accessible webpage
   - Automatic HTML parsing and cleanup (removes scripts, ads, navigation)
   - Content truncation handling for large pages
   - Returns title, clean text, URL, and content metadata

#### **Perplexity Search MCP Server (3 Tools)**
1. **perplexity_search_web**
   - Standard AI-powered web search with recency filtering
   - Returns AI-synthesized responses with automatic citations
   - Supports day/week/month/year recency filters

2. **perplexity_advanced_search**
   - Advanced search with custom parameters
   - Model selection, temperature control (0.0-1.0), max tokens (1-2048)
   - Detailed response metadata and comprehensive result formatting

3. **search_show_categories**
   - Search and filter CSV-based category taxonomy
   - Filter by show (CAI, DOL, CCSE, BDAIW, DCW), industry, or product
   - Structured results with comprehensive category information

#### **Company Tagging MCP Server (1 Tool - Embedded Stdio)**
1. **search_show_categories** (Additional Instance)
   - Specialized company tagging and categorization workflow
   - Access to trade show taxonomy with industry/product pairs
   - Integrated with Google Search and Perplexity for company research

### **Available Resources: 7+ Resources**

#### **CSV Category Resources**
- **categories://all**: Complete CSV data with all show categories
- **categories://shows**: Categories organized by show with statistics
- **categories://shows/{show_name}**: Categories for specific shows
- **categories://industries**: Categories organized by industry
- **categories://industries/{industry_name}**: Industry-specific categories
- **categories://search/{query}**: Search across all category data

## 📝 Usage Examples

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

#### **Company Research & Categorization**
```
"Search for show categories for CAI"
"Find all categories related to Cloud infrastructure"
"What companies would fit in the Data Centre World show?"
```
*Uses CSV category tools and integrated research capabilities*

#### **Hybrid Research Workflows**
```
"Compare different approaches to renewable energy and analyze their effectiveness"
"Research current cybersecurity threats and provide analysis of mitigation strategies"
"Find companies in the AI space and categorize them for trade shows"
```
*Uses both tool sets for comprehensive coverage and analysis*

## 🔧 Component Documentation

### [🖥️ Streamlit Client Documentation](./client/Readme.md)
- Authentication system setup and configuration
- SSL/HTTPS configuration and certificate management
- AI provider setup and management (OpenAI, Azure OpenAI, Enhanced Configuration)
- Tool execution monitoring and conversation management
- Company tagging workflow integration

### [🔍 Google Search MCP Server Documentation](./servers/server2/readme.md)
- Google Custom Search API integration
- Web search and content extraction tools (2 tools)
- Performance optimization and troubleshooting
- SSE transport implementation

### [🔮 Perplexity MCP Server Documentation](./servers/server1/Readme.md)
- Perplexity AI API integration
- AI-powered search with multiple models (3 tools)
- Advanced search parameters and filtering
- CSV category data management and access

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
2. **Perplexity Tools**: Add new Perplexity-powered analysis tools in server1
3. **Company Tagging Tools**: Extend the embedded stdio MCP server
4. **Client Tools**: Integrate additional services via MCP protocol

## 🔒 Security & Best Practices

### **API Security**
- Use secure API keys with proper scoping
- Implement rate limiting for search requests
- Enable SSL/TLS for all communications
- Regularly rotate API keys and credentials

### **Authentication Security**
- Bcrypt password hashing with salt
- Secure session management with configurable expiry
- Pre-authorized email domain validation
- HTTPOnly and secure cookie attributes

### **Search Security**
- Validate all search queries and URLs
- Implement content filtering for extracted text
- Monitor API usage and quotas for both services
- Use proper error handling that doesn't expose sensitive data

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

**Company Tagging Issues**
- Verify CSV data is accessible in the embedded stdio server
- Check that Company Tagging tools appear in the Tools tab
- Test stdio server connectivity using the "Test Company Tagging Server" button

### **Port Conflict Resolution**
If you encounter "port already in use" errors:
```bash
# Check what's using the ports
sudo lsof -i :8501
sudo lsof -i :8502
sudo lsof -i :8503

# Stop Docker services
docker-compose down

# Clean up containers
docker system prune -f
```

### **SSL Certificate Issues**
For HTTPS certificate problems:
```bash
# Regenerate SSL certificates
cd client
rm -rf ssl/
./generate_ssl_certificate.sh

# Or use Python script
python generate_ssl_certificate.py
```

## 📈 Performance Metrics

### **Current Performance Characteristics**
- **Search Response Time**: Google Search ~1-3s, Perplexity ~2-5s
- **Content Extraction**: ~2-8s depending on page size
- **Authentication**: <1s login/logout operations
- **Tool Discovery**: <2s for MCP server connection
- **Company Tagging**: Integrated stdio performance

### **Scalability Features**
- Docker containerization for horizontal scaling
- Async operations for concurrent request handling
- Connection pooling for database and API connections
- Content caching where appropriate

## 🤝 Contributing

### **Development Workflow**
1. Fork the repository
2. Create feature branches for each component
3. Test authentication and security features
4. Test both Google and Perplexity search functionality
5. Verify company tagging and CSV data access
6. Submit pull requests with comprehensive testing

### **Search Testing**
- Test various search queries and scenarios with both engines
- Verify content extraction from different websites
- Test error handling and edge cases
- Validate API quota management for both services
- Test company categorization workflows

---

**Version**: 2.0.0  
**Last Updated**: January 2025  
**Compatibility**: Docker 20+, Python 3.11+, Node.js 18+, Google Custom Search API v1, Perplexity API v1  
**Security**: Streamlit Authenticator 0.3.2, bcrypt password hashing, SSL/HTTPS support  
**Total Tools**: 6 tools (2 Google Search, 3 Perplexity AI, 1 Company Tagging)  
**Servers**: 3 services (Client with embedded stdio MCP, Google Search MCP, Perplexity MCP)  
**Architecture**: SSE + stdio MCP transport with comprehensive authentication