# AI-Powered Search MCP Integration Platform

A comprehensive full-stack application that provides AI-powered interactions with Google Search and Perplexity AI through Model Context Protocol (MCP) servers. This platform enables seamless web search, AI-powered analysis, and content extraction with optional HTTPS security and user authentication.

## 🚀 System Overview

This application consists of three integrated components working together to provide comprehensive AI-powered search capabilities:

1. **Streamlit Client** - AI chat interface with multi-provider support, authentication, and SSL support
2. **Google Search MCP Server** - Web search and content extraction via Google Custom Search API
3. **Perplexity MCP Server** - AI-powered search with intelligent analysis via Perplexity API

## 🏗️ System Architecture

![Architecture Diagram](docs/mcp_platform_architecture.svg)

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

#### **Category-Based Research**
```
"Search for companies in Cloud and AI Infrastructure categories"
# Uses search_show_categories with show filtering
```

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

## 📊 Monitoring & Debugging

### **Health Checks**
- **Overall System**: Streamlit interface status indicators
- **Google Search Server**: http://localhost:8002/health
- **Perplexity Server**: http://localhost:8001/health
- **Company Tagging**: Integrated stdio server testing

### **Search Monitoring**
- API usage tracking for both Google and Perplexity
- Search query performance and response times
- Error rates and failed requests
- Content extraction success rates
- Tool execution history with detailed logging

### **Authentication Monitoring**
- User session tracking and activity monitoring
- Login success/failure rates
- Security event logging

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
- Configure user authentication with production credentials

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

---

**Version**: 2.0.0  
**Last Updated**: January 2025  
**Compatibility**: Docker 20+, Python 3.11+, Node.js 18+, Google Custom Search API v1, Perplexity API v1  
**Security**: Streamlit Authenticator 0.3.2, bcrypt password hashing, SSL/HTTPS support  
**Total Tools**: 6 tools (2 Google Search, 3 Perplexity AI, 1 Company Tagging)  
**Servers**: 3 services (Client with embedded stdio MCP, Google Search MCP, Perplexity MCP)  
**Architecture**: SSE + stdio MCP transport with comprehensive authentication