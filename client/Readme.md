# MCP Client - AI Chat Interface with Authentication & Multi-Server Integration

A secure Streamlit-based chat application that connects to Model Context Protocol (MCP) servers to provide AI-powered interactions with Neo4j graph databases and HubSpot CRM systems. Features comprehensive user authentication, session management, and multi-provider AI support.

## 🚀 Features

### **Security & Authentication**
- **User Authentication System**: Secure login with bcrypt password hashing
- **Session Management**: Persistent user sessions with configurable expiry
- **Role-Based Access**: Pre-authorized email domains and user management
- **Secure Cookies**: Configurable authentication cookies with custom keys

### **AI & Integration**
- **Multi-Provider AI Support**: Compatible with OpenAI and Azure OpenAI
- **MCP Server Integration**: Connect to Neo4j and HubSpot MCP servers
- **Real-time Chat Interface**: Interactive chat with conversation history
- **Tool Execution Tracking**: Monitor and debug tool usage
- **Schema-Aware Operations**: Automatic schema retrieval for intelligent queries

### **User Experience**
- **Modern Tabbed Interface**: Configuration, Connections, Tools, and Chat tabs
- **Responsive Design**: Modern UI with customizable themes and animations
- **User Dashboard**: Personal information and session management
- **Conversation Management**: Create, switch, and delete chat sessions

## 📋 Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- Active MCP servers for Neo4j and/or HubSpot
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
   
   Edit `servers_config.json` to match your MCP server endpoints:
   ```json
   {
     "mcpServers": {
       "Neo4j": {
         "transport": "sse",
         "url": "http://your-neo4j-mcp-server:8003/sse",
         "timeout": 600,
         "headers": null,
         "sse_read_timeout": 900
       },
       "HubSpot": {
         "transport": "sse",
         "url": "http://your-hubspot-mcp-server:8004/sse",
         "timeout": 600,
         "headers": null,
         "sse_read_timeout": 900
       }
     }
   }
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t mcp-client .
   ```

2. **Run with environment variables**
   ```bash
   docker run -p 8501:8501 \
     -e OPENAI_API_KEY=your_key \
     -v $(pwd)/.env:/app/.env \
     -v $(pwd)/keys:/app/keys \
     mcp-client
   ```

## 🎯 Usage

### Getting Started

1. **Launch the application** and navigate to `http://localhost:8501`

2. **Authenticate**:
   - Use the sidebar authentication panel
   - Login with generated credentials (default: admin/very_Secure_p@ssword_123!)
   - View welcome message and user information

3. **Configure your AI provider** (Configuration tab):
   - Select between OpenAI or Azure OpenAI
   - Verify your credentials are loaded (green checkmark)
   - Adjust model parameters (temperature, max tokens)

4. **Connect to MCP servers** (Connections tab):
   - Click "Connect to MCP Servers"
   - Verify successful connection (you'll see available tools)
   - Check server health status

5. **Explore available tools** (Tools tab):
   - Browse Neo4j and HubSpot tools
   - View tool documentation and parameters
   - Search for specific tools

6. **Start chatting** (Chat tab):
   - Ask questions about your Neo4j database or HubSpot CRM
   - The AI will automatically use appropriate tools to answer
   - View tool execution history

### Example Queries

**Neo4j Database Operations:**
```
"Show me the database schema"
"How many visitors do we have this year?"
"Find all nodes connected to user John"
"Create a new person node with name 'Alice'"
```

**HubSpot CRM Operations:**
```
"Get my user details"
"Show me all contacts from this month"
"Find companies in the technology industry"
"List all open deals"
```

**General Queries:**
```
"What tools are available?"
"Explain the database structure"
"Help me understand my CRM data"
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
│   Streamlit UI    │    │   LangChain      │    │   MCP Servers   │
│                   │◄──►│   Agent          │◄──►│                 │
│  - Chat Interface │    │  - Tool Routing  │    │  - Neo4j        │
│  - Authentication │    │  - LLM Provider  │    │  - HubSpot      │
│  - Config Panel   │    │  - Memory Mgmt   │    │  - Custom Tools │
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

Example user configuration:
```python
users = {
    'new_user': {
        'password': 'secure_password_123!',
        'name': 'New User',
        'email': 'newuser@company.com'
    }
}
```

### MCP Server Configuration

Server endpoints are defined in `servers_config.json`. Each server requires:
- **transport**: Connection method (typically "sse")
- **url**: Server endpoint URL
- **timeout**: Connection timeout in seconds
- **sse_read_timeout**: Server-sent events timeout

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
- Verify MCP servers are running and accessible
- Check network connectivity to server endpoints
- Ensure proper authentication credentials
- Review `servers_config.json` for correct URLs

**API Key Issues:**
- Confirm environment variables are properly set
- Check API key permissions and quotas
- Verify endpoint URLs for Azure OpenAI
- Test API connectivity outside the application

**Tool Execution Errors:**
- Review tool execution history in the expandable section
- Check MCP server logs for detailed error information
- Ensure database/CRM permissions are properly configured
- Verify user has necessary access rights

### Debug Mode

Enable debug information by:
1. Using the "Tool Execution History" expander
2. Checking browser console for JavaScript errors
3. Monitoring Streamlit logs in terminal
4. Reviewing authentication logs

### Performance Optimization

- Adjust `max_tokens` for faster responses
- Use connection pooling for high-traffic scenarios
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

- **v2.0.0**: Added comprehensive authentication system, enhanced UI
- **v1.0.0**: Initial release with Neo4j and HubSpot MCP integration
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
**Security**: Streamlit Authenticator 0.3.2, bcrypt password hashing  
**Compatibility**: Python 3.11+, Streamlit 1.44+