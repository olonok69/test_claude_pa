# Google Search MCP Client - AI Chat Interface with Authentication & SSL Support

A secure Streamlit-based chat application that connects to Google Search MCP servers to provide AI-powered web search and content extraction capabilities. Features comprehensive user authentication, session management, SSL/HTTPS support, and multi-provider AI integration.

## 🚀 Features

### **Security & Authentication**
- **User Authentication System**: Secure login with bcrypt password hashing
- **Session Management**: Persistent user sessions with configurable expiry
- **SSL/HTTPS Support**: Secure connections with self-signed certificates on port 8503
- **Role-Based Access**: Pre-authorized email domains and user management
- **Secure Cookies**: Configurable authentication cookies with custom keys

### **AI & Google Search Integration**
- **Multi-Provider AI Support**: Compatible with OpenAI and Anthropic
- **Google Search MCP Integration**: Connect to Google Search MCP server
- **Real-time Chat Interface**: Interactive chat with conversation history
- **Web Search Tools**: Google Custom Search API integration
- **Content Extraction**: Clean webpage content extraction and analysis
- **Tool Execution Tracking**: Monitor and debug tool usage

### **User Experience**
- **Modern Tabbed Interface**: Configuration, Connections, Tools, and Chat tabs
- **Responsive Design**: Modern UI with customizable themes and animations
- **User Dashboard**: Personal information and session management
- **Conversation Management**: Create, switch, and delete chat sessions
- **Research Workflows**: Multi-step search and analysis capabilities

## 📋 Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- Active Google Search MCP server
- Google Custom Search API key and Search Engine ID
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
   
   # Google Search Configuration
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_SEARCH_ENGINE_ID=your_custom_search_engine_id
   
   # SSL Configuration (Optional)
   SSL_ENABLED=true
   ```

4. **Set up user authentication**
   
   Generate user credentials:
   ```bash
   python simple_generate_password.py
   ```
   
   This creates `keys/config.yaml` with default users:
   - **admin**: very_Secure_p@ssword_123!
   - **juan**: Larisa1000@
   - **giovanni_romero**: MrRomero2024!
   - **demo_user**: strong_password_123!

5. **Update MCP server configuration**
   
   Edit `servers_config.json` to match your Google Search MCP server endpoint:
   ```json
   {
     "mcpServers": {
       "Google Search": {
         "transport": "sse",
         "url": "http://your-google-search-mcp-server:8002/sse",
         "timeout": 600,
         "headers": null,
         "sse_read_timeout": 900
       }
     }
   }
   ```

6. **Run the application**
   ```bash
   # HTTP mode
   streamlit run app.py
   
   # HTTPS mode (if SSL certificates are set up)
   streamlit run app.py --server.port=8503 --server.sslCertFile=ssl/cert.pem --server.sslKeyFile=ssl/private.key
   ```

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t google-search-mcp-client .
   ```

2. **Run with environment variables**
   ```bash
   docker run -p 8501:8501 -p 8503:8503 \
     -e OPENAI_API_KEY=your_key \
     -e GOOGLE_API_KEY=your_google_key \
     -e GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id \
     -e SSL_ENABLED=true \
     -v $(pwd)/.env:/app/.env \
     -v $(pwd)/keys:/app/keys \
     google-search-mcp-client
   ```

## 🎯 Usage

### Getting Started

1. **Launch the application** and navigate to:
   - **HTTP**: `http://localhost:8501`
   - **HTTPS**: `https://localhost:8503` (accept browser security warning)

2. **Authenticate**:
   - Use the sidebar authentication panel
   - Login with generated credentials (default: admin/very_Secure_p@ssword_123!)
   - View welcome message and user information

3. **Configure your AI provider** (Configuration tab):
   - Select between OpenAI or Azure OpenAI
   - Verify your credentials are loaded (green checkmark)
   - Adjust model parameters (temperature, max tokens)

4. **Connect to Google Search MCP server** (Connections tab):
   - Click "Connect to MCP Server"
   - Verify successful connection (you'll see available tools)
   - Check server health status

5. **Explore available tools** (Tools tab):
   - Browse Google Search tools (google-search, read-webpage)
   - View tool documentation and parameters
   - Search for specific tools

6. **Start chatting** (Chat tab):
   - Ask questions to search the web and extract content
   - The AI will automatically use appropriate tools to answer
   - View tool execution history

### Example Queries

**Web Search Operations:**
```
"Search for the latest developments in artificial intelligence"
"Find recent news about climate change"
"What are the current trends in web development?"
"Search for Python programming tutorials"
```

**Content Extraction Operations:**
```
"Search for climate reports and read the full content from the first result"
"Find the latest tech news and extract content from TechCrunch"
"Search for React documentation and read the official guide"
```

**Research Workflows:**
```
"Research the current state of renewable energy technology"
"Find and analyze multiple sources about cryptocurrency trends"
"Search for best practices in software engineering and summarize them"
```

**General Queries:**
```
"What tools are available for web search?"
"Help me understand how to extract content from web pages"
"Show me examples of effective search queries"
```

### Advanced Configuration

**Model Parameters:**
- **Temperature**: Control response creativity (0.0-1.0)
- **Max Tokens**: Set response length limit (1024-10240)

**Chat Management:**
- Create new conversations with "New Chat"
- Access conversation history in the sidebar
- Delete conversations as needed
- Switch between conversations seamlessly

**User Management:**
- View current user information in the sidebar
- Monitor session time and activity
- Secure logout functionality

## 🏗️ Architecture

```
┌───────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI    │    │   LangChain      │    │ Google Search   │
│                   │◄──►│   Agent          │◄──►│ MCP Server      │
│  - Chat Interface │    │  - Tool Routing  │    │                 │
│  - Authentication │    │  - LLM Provider  │    │  - Web Search   │
│  - Config Panel   │    │  - Memory Mgmt   │    │  - Content Ext  │
│  - Tool Display   │    │                  │    │                 │
└───────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Components

- **`app.py`**: Main Streamlit application with authentication
- **`services/`**: Core business logic (AI, MCP, Chat management)
- **`ui_components/`**: Reusable UI components and widgets
- **`utils/`**: Helper functions and utilities
- **`config.py`**: Configuration management
- **`simple_generate_password.py`**: User credential generation

### Authentication System

- **Password Hashing**: bcrypt with salt for secure storage
- **Session Management**: Streamlit-authenticator integration
- **Cookie Configuration**: Secure, configurable authentication cookies
- **User Validation**: Pre-authorized email domains

## 🔧 Configuration

### Model Providers

The application supports multiple AI providers configured in `config.py`:

```python
MODEL_OPTIONS = {
    'OpenAI': 'gpt-4o',
    'Azure OpenAI': 'gpt-4o-mini',
}
```

### User Management

User credentials are managed in `keys/config.yaml`. To add/modify users:

1. Edit `simple_generate_password.py`
2. Modify the `users` dictionary with desired credentials
3. Run the script to generate new `config.yaml`

### Google Search MCP Server Configuration

Server endpoints are defined in `servers_config.json`. The server requires:
- **transport**: Connection method ("sse")
- **url**: Server endpoint URL (typically http://server:8002/sse)
- **timeout**: Connection timeout in seconds
- **sse_read_timeout**: Server-sent events timeout

### SSL Configuration

For HTTPS support on port 8503:
1. Set `SSL_ENABLED=true` in environment variables
2. Certificates will be automatically generated on startup
3. Access via https://localhost:8503 (accept browser warning for self-signed cert)

### Styling

Custom CSS is located in `.streamlit/style.css` for UI customization:
- Tab styling and animations
- Modern button designs
- Responsive layout adjustments
- Color scheme and themes

## 🔒 Security Features

### Authentication Security
- **Bcrypt Hashing**: Industry-standard password protection
- **Session Timeout**: Configurable session expiry (30 days default)
- **Secure Cookies**: HTTPOnly and secure cookie attributes
- **Access Control**: Pre-authorized email validation

### SSL/HTTPS Security
- **Self-signed Certificates**: Automatic generation for development
- **Port 8503**: Dedicated HTTPS port separate from HTTP (8501)
- **Secure Headers**: Proper SSL configuration for Streamlit
- **Certificate Management**: Automatic renewal and permission handling

### API Security
- **Environment Variables**: Secure credential storage
- **Token Validation**: Real-time API key verification
- **Input Sanitization**: XSS and injection protection
- **Error Handling**: Secure error messages without data exposure

### Session Management
- **User Isolation**: Separate conversation histories per user
- **Session Tracking**: Login time and activity monitoring
- **Automatic Cleanup**: Session data management
- **Cross-Session Security**: Protected against session hijacking

## 🐛 Troubleshooting

### Common Issues

**Authentication Problems:**
- Verify `keys/config.yaml` exists and is properly formatted
- Check user credentials match the generated passwords
- Ensure email domains are in preauthorized list
- Clear browser cookies if experiencing login issues

**Connection Problems:**
- Verify Google Search MCP server is running and accessible
- Check network connectivity to server endpoint (port 8002)
- Ensure proper server configuration in `servers_config.json`
- Review Google API credentials and quotas

**SSL/HTTPS Issues:**
- Certificates are automatically generated on startup
- Accept browser security warning for self-signed certificates
- Check container logs for certificate generation errors
- Verify SSL_ENABLED environment variable is set to "true"

**API Key Issues:**
- Confirm Google API key and Search Engine ID are properly set
- Check API key permissions and quotas in Google Cloud Console
- Verify Custom Search API is enabled
- Test API connectivity outside the application

**Tool Execution Errors:**
- Review tool execution history in the expandable section
- Check Google Search MCP server logs for detailed error information
- Ensure Google Custom Search Engine is properly configured
- Verify API quotas haven't been exceeded

### Debug Mode

Enable debug information by:
1. Using the "Tool Execution History" expander
2. Checking browser console for JavaScript errors
3. Monitoring Streamlit logs in terminal
4. Reviewing authentication logs

### Performance Optimization

- Adjust `max_tokens` for faster responses
- Use appropriate search result counts (1-10) based on needs
- Monitor memory usage with multiple concurrent sessions
- Optimize conversation history management

## 🔄 User Management

### Adding New Users

1. **Edit the password generation script**:
   ```bash
   # Edit simple_generate_password.py
   # Add new users to the users dictionary
   ```

2. **Generate new configuration**:
   ```bash
   python simple_generate_password.py
   ```

3. **Restart the application** to load new users

### Managing Existing Users

- **Password Changes**: Regenerate `config.yaml` with new passwords
- **Email Updates**: Modify user information in the generation script
- **Access Revocation**: Remove users from the configuration and regenerate

### Session Management

- **View Active Sessions**: Check sidebar for current user information
- **Session Timeout**: Configure in `config.yaml` (expiry_days)
- **Forced Logout**: Clear cookies or restart application

## 🔄 Version History

- **v2.0.0**: Google Search MCP integration with SSL support
- **v1.0.0**: Initial release with authentication system
- Basic chat interface with multi-provider AI support
- Tool execution tracking and conversation management

## 🤝 Contributing

### Development Guidelines

1. **Follow authentication patterns** when adding new features
2. **Test with multiple user accounts** to ensure proper isolation
3. **Maintain security best practices** for credential handling
4. **Update documentation** for new authentication features

### Security Considerations

- Never log or expose user passwords or session tokens
- Validate all user inputs for security vulnerabilities
- Follow secure coding practices for authentication flows
- Test authentication edge cases and error conditions

---

**Version**: 2.0.0  
**Last Updated**: June 2025  
**Security**: Streamlit Authenticator 0.3.2, bcrypt password hashing, SSL/HTTPS support  
**Compatibility**: Python 3.11+, Streamlit 1.44+, Google Custom Search API v1