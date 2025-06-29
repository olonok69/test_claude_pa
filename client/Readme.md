# MCP Client - Secure AI Chat Interface with Enterprise Authentication & Multi-Server Integration

A comprehensive Streamlit-based chat application that connects to Model Context Protocol (MCP) servers to provide AI-powered interactions with Yahoo Finance, Neo4j graph databases, and HubSpot CRM systems. Features enterprise-grade user authentication, session management, SSL support, and multi-provider AI capabilities.

## 🚀 Features

### **Enterprise Security & Authentication**
- **Secure User Authentication**: bcrypt password hashing with salt-based encryption
- **Session Management**: Persistent user sessions with configurable expiry (30 days default)
- **Role-Based Access Control**: Pre-authorized email domains and user management
- **SSL/TLS Support**: Optional HTTPS with self-signed certificate generation
- **Secure Cookies**: Configurable authentication cookies with custom encryption keys
- **User Isolation**: Separate conversation histories and session data per user

### **Advanced AI & Integration**
- **Multi-Provider AI Support**: Seamless switching between OpenAI and Azure OpenAI
- **Triple MCP Server Integration**: Yahoo Finance, Neo4j, and HubSpot MCP servers
- **Real-time Chat Interface**: Interactive conversations with full context memory
- **Tool Execution Tracking**: Comprehensive monitoring and debugging of tool usage
- **Schema-Aware Operations**: Automatic schema retrieval for intelligent query validation
- **Context-Aware Conversations**: Maintains conversation history and builds upon previous interactions

### **Modern User Experience**
- **Tabbed Interface**: Organized into Chat, Configuration, Connections, and Tools tabs
- **Responsive Design**: Modern UI with customizable themes, animations, and mobile support
- **User Dashboard**: Personal information, session management, and activity tracking
- **Conversation Management**: Create, switch, delete, and organize chat sessions
- **Tool Discovery**: Interactive exploration of available MCP tools with documentation
- **Real-time Status**: Live connection status and health monitoring

## 📋 Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- Active MCP servers for Yahoo Finance, Neo4j, and/or HubSpot
- OpenAI API key or Azure OpenAI configuration

## 🛠️ Installation

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd client
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the client directory:
   ```env
   # OpenAI Configuration (choose one)
   OPENAI_API_KEY=your_openai_api_key_here
   
   # OR Azure OpenAI Configuration
   AZURE_API_KEY=your_azure_api_key
   AZURE_ENDPOINT=https://your-endpoint.openai.azure.com/
   AZURE_DEPLOYMENT=your_deployment_name
   AZURE_API_VERSION=2023-12-01-preview
   
   # Optional: Enable SSL
   SSL_ENABLED=false
   ```

4. **Set up user authentication**
   
   Generate user credentials with default accounts:
   ```bash
   python simple_generate_password.py
   ```
   
   This creates `keys/config.yaml` with pre-configured users:
   - **admin**: very_Secure_p@ssword_123!
   - **juan**: Larisa1000@
   - **giovanni_romero**: MrRomero2024!
   - **demo_user**: strong_password_123!

5. **Update MCP server configuration**
   
   Edit `servers_config.json` to match your MCP server endpoints:
   ```json
   {
     "mcpServers": {
       "Yahoo Finance": {
         "transport": "sse",
         "url": "http://mcpserver3:8002/sse",
         "timeout": 600,
         "headers": null,
         "sse_read_timeout": 900
       },
       "Neo4j": {
         "transport": "sse",
         "url": "http://mcpserver4:8003/sse",
         "timeout": 600,
         "headers": null,
         "sse_read_timeout": 900
       },
       "HubSpot": {
         "transport": "sse",
         "url": "http://mcpserver5:8004/sse",
         "timeout": 600,
         "headers": null,
         "sse_read_timeout": 900
       }
     }
   }
   ```

6. **Run the application**
   ```bash
   # Standard HTTP mode
   streamlit run app.py
   
   # Or with SSL enabled
   SSL_ENABLED=true python start_streamlit.py
   ```

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t mcp-client .
   ```

2. **Run with environment variables**
   ```bash
   # HTTP mode
   docker run -p 8501:8501 \
     -e OPENAI_API_KEY=your_key \
     -v $(pwd)/.env:/app/.env \
     -v $(pwd)/keys:/app/keys \
     mcp-client
   
   # HTTPS mode
   docker run -p 8501:8501 -p 8502:8502 \
     -e OPENAI_API_KEY=your_key \
     -e SSL_ENABLED=true \
     -v $(pwd)/.env:/app/.env \
     -v $(pwd)/keys:/app/keys \
     -v $(pwd)/ssl:/app/ssl \
     mcp-client
   ```

3. **SSL Certificate Generation** (automatic in Docker)
   ```bash
   # Certificates are auto-generated when SSL_ENABLED=true
   # Or manually generate:
   python generate_ssl_certificate.py
   # Or using shell script:
   ./generate_ssl_certificate.sh
   ```

## 🎯 Usage

### Getting Started

1. **Launch the application**
   - HTTP: `http://localhost:8501`
   - HTTPS: `https://localhost:8502` (if SSL enabled)

2. **Authenticate**:
   - Use the sidebar authentication panel
   - Login with default credentials:
     - Username: `admin` / Password: `very_Secure_p@ssword_123!`
     - Username: `juan` / Password: `Larisa1000@`
     - Username: `giovanni_romero` / Password: `MrRomero2024!`
     - Username: `demo_user` / Password: `strong_password_123!`
   - View welcome message and user session information

3. **Configure your AI provider** (Configuration tab):
   - Select between OpenAI or Azure OpenAI
   - Verify credentials are loaded (green checkmark indicates success)
   - Adjust model parameters (temperature: 0.0-1.0, max tokens: 1024-10240)

4. **Connect to MCP servers** (Connections tab):
   - Click "Connect to MCP Servers"
   - Verify successful connections (shows available tool count)
   - Check individual server health status
   - Monitor connection metrics and performance

5. **Explore available tools** (Tools tab):
   - Browse tools by category: Yahoo Finance, Neo4j, HubSpot
   - View detailed tool documentation and parameters
   - Search for specific tools by name or description
   - Understand tool requirements and usage examples

6. **Start chatting** (Chat tab):
   - Ask questions about financial markets, databases, or CRM data
   - The AI automatically selects and uses appropriate tools
   - View detailed tool execution history
   - Monitor conversation context and memory

### Example Queries

**Financial Analysis Operations:**
```
"What's the current MACD score for AAPL?"
"Calculate the Bollinger-Fibonacci strategy for Tesla stock over 1 year"
"Give me a combined technical analysis score for Microsoft using multiple indicators"
"Compare trading signals for AAPL, TSLA, and MSFT"
```

**Neo4j Database Operations:**
```
"Show me the complete database schema and explain the structure"
"How many visitors converted to customers this year?"
"Find all relationships between person nodes and company nodes"
"Create a new person node with name 'Alice' and link to existing company"
"Validate this Cypher query against the current schema"
```

**HubSpot CRM Operations:**
```
"Get my HubSpot user details and permissions"
"Show me all contacts created this month with their engagement history"
"Find companies in the technology industry and their associated deals"
"Create a new contact and company, then associate them together"
"List all open deals above $10,000 and generate HubSpot links to view them"
"Add a follow-up task for the Amazon deal and track its progress"
```

**Advanced Multi-System Workflows:**
```
"Analyze AAPL stock performance and create a HubSpot task to review our tech investments"
"Compare customer data between our Neo4j database and HubSpot CRM"
"Find high-value deals in HubSpot and cross-reference with graph database relationships"
"Create a comprehensive report combining financial analysis, database insights, and CRM data"
```

### Advanced Configuration

**Model Parameters:**
- **Temperature**: Control response creativity and randomness (0.0 = deterministic, 1.0 = creative)
- **Max Tokens**: Set response length limit (1024-10240 tokens)
- **Provider Selection**: Dynamic switching between OpenAI and Azure OpenAI

**Chat Management:**
- **New Conversations**: Create fresh chat sessions with "New Chat"
- **History Access**: Browse and switch between previous conversations
- **Context Management**: Each conversation maintains its own memory and context
- **Session Isolation**: Conversations are isolated per authenticated user

**User Session Management:**
- **Session Tracking**: Monitor login time and session duration
- **Activity Monitoring**: Track tool usage and conversation patterns
- **Secure Logout**: Proper session cleanup and security
- **Multi-User Support**: Separate data and sessions for each authenticated user

## 🏗️ Architecture

```
┌───────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Streamlit UI    │    │   LangChain      │    │   MCP Servers       │
│                   │◄──►│   Agent          │◄──►│                     │
│  - Authentication │    │  - Tool Routing  │    │  - Yahoo Finance    │
│  - Chat Interface │    │  - LLM Provider  │    │  - Neo4j Database   │
│  - Config Panel   │    │  - Memory Mgmt   │    │  - HubSpot CRM      │
│  - Tool Display   │    │  - Context Aware │    │  - Custom Tools     │
│  - Session Mgmt   │    │                  │    │                     │
└───────────────────┘    └──────────────────┘    └─────────────────────┘
```

### Key Components

- **`app.py`**: Main Streamlit application with authentication middleware
- **`services/`**: Core business logic (AI services, MCP management, Chat services)
- **`ui_components/`**: Reusable UI components (tabs, sidebar, main components)
- **`utils/`**: Helper functions (async handlers, tool parsing, AI prompts)
- **`config.py`**: Centralized configuration management
- **`simple_generate_password.py`**: User credential generation and management

### Authentication System

- **Password Security**: bcrypt hashing with salt for secure credential storage
- **Session Management**: Streamlit-authenticator integration with persistent sessions
- **Cookie Security**: Secure, HTTPOnly cookies with configurable expiration
- **Access Control**: Pre-authorized email domains with user validation
- **Multi-User Support**: Complete user isolation with separate conversation histories

### SSL/TLS Support

- **Certificate Generation**: Automatic self-signed certificate creation
- **HTTPS Server**: Streamlit HTTPS mode with proper SSL configuration
- **Cross-Platform**: Python-based certificate generation for compatibility
- **Production Ready**: Configurable SSL settings for production deployment

## 🔧 Configuration

### Model Providers

The application supports multiple AI providers configured in `config.py`:

```python
MODEL_OPTIONS = {
    'OpenAI': 'gpt-4o',
    'Azure OpenAI': 'o3-mini',  # Using deployment from environment
}
```

### User Management

User credentials are managed in `keys/config.yaml`. To add/modify users:

1. **Edit the password generation script**:
   ```python
   # Edit simple_generate_password.py
   users = {
       'new_user': {
           'password': 'secure_password_123!',
           'name': 'New User Name',
           'email': 'user@company.com'
       }
   }
   ```

2. **Generate new configuration**:
   ```bash
   python simple_generate_password.py
   ```

3. **Restart the application** to load new users

### MCP Server Configuration

Server endpoints are defined in `servers_config.json`. Each server requires:
- **transport**: Connection method (typically "sse")
- **url**: Server endpoint URL with proper protocol and port
- **timeout**: Connection timeout in seconds
- **sse_read_timeout**: Server-sent events timeout for long-running operations

### SSL Configuration

SSL is configured through environment variables and certificate files:

```env
# Enable SSL/HTTPS mode
SSL_ENABLED=true
```

Certificates are automatically generated in the `ssl/` directory:
- `ssl/cert.pem` - SSL certificate
- `ssl/private.key` - Private key (secure permissions)

### Styling and Themes

Custom CSS is located in `.streamlit/style.css` for UI customization:
- **Modern Design**: Contemporary UI with dark/light theme support
- **Responsive Layout**: Mobile-friendly design with adaptive layouts
- **Interactive Elements**: Hover effects, animations, and smooth transitions
- **Accessibility**: High contrast ratios and semantic markup

## 🔒 Security Features

### Authentication Security
- **Enterprise Encryption**: bcrypt password hashing with configurable salt rounds
- **Session Security**: Secure session tokens with configurable expiry
- **Cookie Protection**: HTTPOnly, Secure, and SameSite cookie attributes
- **Access Control**: Domain-based authorization and user validation
- **Brute Force Protection**: Rate limiting and account lockout mechanisms

### API and Data Security
- **Environment Variables**: Secure credential storage outside code repository
- **Token Validation**: Real-time API key verification and health checks
- **Input Sanitization**: Comprehensive XSS and injection protection
- **Error Handling**: Secure error messages without sensitive data exposure
- **SSL/TLS Encryption**: End-to-end encryption for data in transit

### Session and User Security
- **User Isolation**: Complete separation of user data and conversations
- **Session Tracking**: Detailed logging of user activity and access patterns
- **Automatic Cleanup**: Secure session data management and cleanup
- **Cross-Session Protection**: Prevention of session hijacking and CSRF attacks

## 🐛 Troubleshooting

### Authentication Problems

**Login Issues:**
- Verify `keys/config.yaml` exists and is properly formatted
- Check that user credentials match the generated passwords
- Ensure email domains are in the preauthorized list
- Clear browser cookies if experiencing persistent login issues

**Session Problems:**
- Check session cookie configuration and expiry settings
- Verify authentication key matches between sessions
- Monitor session state in browser developer tools

### Connection Problems

**MCP Server Connection:**
- Verify all MCP servers are running and accessible
- Check `servers_config.json` for correct server URLs and ports
- Test individual server health endpoints
- Monitor Docker container status with `docker-compose ps`

**Network Issues:**
- Ensure proper network connectivity between containers
- Verify firewall settings don't block required ports
- Check DNS resolution for server hostnames

### SSL/HTTPS Issues

**Certificate Problems:**
- Verify SSL certificates are properly generated in `ssl/` directory
- Check certificate validity and expiration dates
- Ensure proper file permissions on private key (600)

**Browser Security Warnings:**
- Accept self-signed certificate warnings in browser
- Add certificate exception for localhost development
- Use HTTP mode if SSL issues persist in development

### API Key Issues

**OpenAI Configuration:**
- Confirm `OPENAI_API_KEY` is set in environment variables
- Test API key validity through OpenAI dashboard
- Check API usage limits and quotas

**Azure OpenAI Configuration:**
- Verify all four Azure environment variables are set
- Test endpoint accessibility and deployment name
- Confirm API version compatibility

### Tool Execution Errors

**Schema Validation Failures:**
- Always call `get_neo4j_schema` before database operations
- Start HubSpot workflows with `hubspot-get-user-details`
- Check tool execution history for detailed error information

**Permission Errors:**
- Verify HubSpot token has required scopes and permissions
- Check Neo4j database authentication and access rights
- Monitor rate limiting and API quota usage

### Performance Issues

**Slow Response Times:**
- Monitor tool execution timing in the debug panels
- Check network latency to external APIs
- Optimize query complexity and data volume

**Memory Usage:**
- Monitor Docker container resource utilization
- Clear conversation history if memory usage is high
- Restart containers periodically for optimal performance

### Debug Mode

Enable comprehensive debugging by:
1. Using the "Tool Execution History" expander in the Chat tab
2. Checking browser console for JavaScript errors and network issues
3. Monitoring Streamlit logs in terminal for server-side errors
4. Reviewing authentication logs for login and session issues

## 🔄 User Management

### Adding New Users

1. **Edit the password generation script**:
   ```bash
   nano simple_generate_password.py
   # Add new users to the users dictionary with secure passwords
   ```

2. **Generate new configuration**:
   ```bash
   python simple_generate_password.py
   ```

3. **Restart the application** to load new user accounts

### Managing Existing Users

- **Password Updates**: Regenerate `config.yaml` with new passwords
- **Email Changes**: Modify user information in the generation script
- **Access Management**: Add/remove emails from preauthorized list
- **Role Changes**: Update user names and access levels

### Session Administration

- **Active Sessions**: Monitor current user sessions in sidebar
- **Session Configuration**: Adjust expiry times in `config.yaml`
- **Security Policies**: Configure cookie settings and security parameters
- **User Activity**: Track login times and conversation usage

## 🔄 Version History

- **v2.0.0**: Enterprise authentication system, SSL support, enhanced UI with tabs
- **v1.5.0**: Multi-provider AI support, comprehensive tool integration
- **v1.0.0**: Initial release with basic MCP integration and chat interface

## 🤝 Contributing

### Development Guidelines

1. **Security First**: Always follow authentication patterns when adding features
2. **Multi-User Testing**: Test with multiple user accounts to ensure proper isolation
3. **SSL Compatibility**: Ensure new features work in both HTTP and HTTPS modes
4. **Documentation**: Update README and inline documentation for new features

### Security Considerations

- Never log or expose user passwords, session tokens, or API keys
- Validate all user inputs for security vulnerabilities and injection attacks
- Follow secure coding practices for authentication flows and session management
- Test authentication edge cases, error conditions, and security boundaries

### Testing Procedures

- **Authentication Testing**: Verify login/logout flows for all user types
- **Session Testing**: Test session persistence, expiry, and isolation
- **SSL Testing**: Verify HTTPS functionality and certificate handling
- **Multi-User Testing**: Ensure proper data separation between users
- **Tool Integration**: Test all MCP server connections and tool functionality

---

**Version**: 2.0.0  
**Last Updated**: June 2025  
**Security**: Streamlit Authenticator 0.3.2, bcrypt password hashing, SSL/TLS support  
**Compatibility**: Python 3.11+, Streamlit 1.44+, Docker 20+  
**Authentication**: Enterprise-grade user management with session isolation