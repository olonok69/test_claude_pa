# MCP Client - AI Chat Interface with Enhanced Security & Multi-Server Integration

A secure Streamlit-based chat application that connects to Model Context Protocol (MCP) servers to provide AI-powered interactions with MSSQL databases. Features comprehensive user authentication, session management, and multi-provider AI support with enhanced security.

## 🚀 Features

### **Security & Authentication**
- **Enhanced User Authentication**: Secure login with bcrypt password hashing and SQLite/YAML storage options
- **Session Management**: Persistent user sessions with configurable expiry and isolation
- **Role-Based Access**: Admin and regular user roles with permission management
- **User Management Interface**: Full admin panel for user creation, editing, and management
- **Secure Cookies**: Configurable authentication cookies with custom keys
- **Audit Logging**: Comprehensive audit trail for security compliance
- **Account Security**: Failed login tracking, account lockout, and password strength validation

### **AI & Integration**
- **Multi-Provider AI Support**: Compatible with OpenAI and Azure OpenAI
- **MCP Server Integration**: Connect to MSSQL MCP servers
- **Real-time Chat Interface**: Interactive chat with conversation history and user isolation
- **Tool Execution Tracking**: Monitor and debug tool usage with detailed execution history
- **Schema-Aware Operations**: Automatic schema retrieval for intelligent MSSQL queries

### **User Experience**
- **Modern Tabbed Interface**: Configuration, Connections, Tools, Chat, and User Management tabs
- **Responsive Design**: Modern UI with customizable themes, animations, and enhanced chat interface
- **User Dashboard**: Personal information, session management, and activity tracking
- **Conversation Management**: Create, switch, delete, and export chat sessions
- **User Session Isolation**: Complete separation of user data and conversations

### **Enterprise Features**
- **SSL/HTTPS Support**: Optional SSL certificate generation and HTTPS deployment
- **Enhanced Configuration**: Multiple storage backends (SQLite, YAML, encrypted JSON)
- **Backup & Recovery**: Secure user data backup and restoration capabilities
- **Migration Tools**: Scripts for migrating between authentication systems
- **Docker Support**: Containerized deployment with SSL support

## 📋 Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- Active MSSQL MCP server
- OpenAI API key or Azure OpenAI configuration
- SQL Server ODBC Driver (for database connectivity)

## 🛠️ Installation

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd mcp-chatbot/client
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the client directory:
   ```env
   # AI Provider Configuration (choose one)
   OPENAI_API_KEY=your_openai_api_key_here
   
   # OR Azure OpenAI Configuration
   AZURE_API_KEY=your_azure_api_key
   AZURE_ENDPOINT=https://your-endpoint.openai.azure.com/
   AZURE_DEPLOYMENT=your_deployment_name
   AZURE_API_VERSION=2023-12-01-preview
   
   # Enhanced Security (optional)
   USE_SQLITE=true
   ENCRYPTION_PASSWORD=your_secure_encryption_password
   SESSION_TIMEOUT_HOURS=24
   MAX_LOGIN_ATTEMPTS=5
   
   # SSL Configuration (optional)
   SSL_ENABLED=false
   ```

4. **Set up user authentication**
   
   Generate user credentials (creates default users):
   ```bash
   python one_time/simple_generate_password.py
   ```
   
   This creates `keys/config.yaml` with default users:
   - **admin**: -------
   - **juan**: -------
   - **giovanni_romero**: -------
   - **demo_user**: -------

5. **Configure MCP server**
   
   The `servers_config.json` is pre-configured for MSSQL:
   ```json
   {
     "mcpServers": {
       "MSSQL": {
         "transport": "sse",
         "url": "http://mcpserver3:8008/sse",
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

### Enhanced SQLite Authentication Setup

1. **Enable SQLite authentication**
   ```bash
   # Set in your .env file
   echo "USE_SQLITE=true" >> .env
   ```

2. **Migrate users to SQLite** (optional, for enhanced security)
   ```bash
   python migration_scripts/migrate_users_to_sqlite.py
   ```

3. **Test the enhanced authentication**
   ```bash
   python migration_scripts/simple_verification_script.py
   ```

### SSL/HTTPS Setup

1. **Enable SSL in environment**
   ```bash
   echo "SSL_ENABLED=true" >> .env
   ```

2. **Generate SSL certificates**
   ```bash
   # Python method (cross-platform)
   python generate_ssl_certificate.py
   
   # OR Shell method (Unix/Linux/Mac)
   chmod +x generate_ssl_certificate.sh
   ./generate_ssl_certificate.sh
   ```

3. **Start with SSL**
   ```bash
   # Using startup script
   ./startup_ssl.sh
   
   # OR manual Streamlit command
   streamlit run app.py \
     --server.port=8502 \
     --server.enableCORS=false \
     --server.enableXsrfProtection=false \
     --server.sslCertFile=ssl/cert.pem \
     --server.sslKeyFile=ssl/private.key
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
     -e USE_SQLITE=true \
     -v $(pwd)/.env:/app/.env \
     -v $(pwd)/keys:/app/keys \
     -v $(pwd)/ssl:/app/ssl \
     mcp-client
   ```

3. **Run with SSL enabled**
   ```bash
   docker run -p 8502:8502 \
     -e SSL_ENABLED=true \
     -e OPENAI_API_KEY=your_key \
     -v $(pwd)/.env:/app/.env \
     -v $(pwd)/keys:/app/keys \
     -v $(pwd)/ssl:/app/ssl \
     mcp-client
   ```

## 🎯 Usage

### Getting Started

1. **Launch the application** and navigate to:
   - HTTP: `http://localhost:8501`
   - HTTPS: `https://localhost:8502` (if SSL enabled)

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
   - Browse MSSQL database tools
   - View tool documentation and parameters
   - Search for specific tools

6. **Start chatting** (Chat tab):
   - Ask questions about your MSSQL database
   - The AI will automatically use appropriate tools to answer
   - View tool execution history

### User Management (Admin Only)

1. **Access User Management** (Admin users only):
   - Navigate to the "User Management" tab
   - View all users, their roles, and activity

2. **Add new users**:
   - Fill in username, full name, and email
   - Choose to generate secure password or set manually
   - Assign admin privileges if needed

3. **Manage existing users**:
   - Edit user information
   - Reset passwords
   - Enable/disable accounts
   - View audit logs

### Example Queries

**MSSQL Database Operations:**
```
"Show me all tables in the database"
"Get the structure of the users table"
"Count all records in the orders table"
"Get 5 sample records from the customers table"
"Find all orders from the last 30 days"
"Show me the top 10 customers by order value"
```

**General Queries:**
```
"What tables are available in the database?"
"Help me understand the database structure"
"Show me some sample data from the main tables"
"What tools are available for database operations?"
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
- Export chat history as JSON

**User Session Management:**
- View current user information in the sidebar
- Monitor session time and activity
- Secure logout functionality
- Data isolation between users

## 🏗️ Architecture

```
┌───────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI    │    │   LangChain      │    │   MCP Servers   │
│                   │◄──►│   Agent          │◄──►│                 │
│  - Chat Interface │    │  - Tool Routing  │    │  - MSSQL        │
│  - Authentication │    │  - LLM Provider  │    │  - Custom Tools │
│  - Config Panel   │    │  - Memory Mgmt   │    │                 │
│  - User Mgmt      │    │                  │    │                 │
└───────────────────┘    └──────────────────┘    └─────────────────┘
        │                           │
        └─────────────┬─────────────┘
                      │
            ┌─────────────────┐
            │ Security Layer  │
            │ - SQLite Auth   │
            │ - Session Mgmt  │
            │ - Audit Logs    │
            │ - User Isolation│
            └─────────────────┘
```

### Key Components

- **`app.py`**: Main Streamlit application with enhanced authentication
- **`services/`**: Core business logic (AI, MCP, Chat management)
- **`ui_components/`**: Reusable UI components and enhanced interfaces
- **`utils/`**: Helper functions, security config, and utilities
- **`config.py`**: Configuration management
- **`migration_scripts/`**: Database migration and setup utilities
- **`one_time/`**: One-time setup and configuration scripts

### Directory Structure

```
mcp-chatbot/client/
├── .streamlit/               # Streamlit configuration and CSS
│   ├── config.toml          # Server configuration
│   └── style.css            # Enhanced UI styling
├── apps/                    # Application modules
├── icons/                   # Application icons and logos
│   ├── Logo.png            # Main application logo
│   └── playground.png      # Page icon
├── keys/                    # Security and authentication
│   ├── config.yaml         # User authentication config
│   ├── users.db           # SQLite user database (when enabled)
│   └── migration_backup/   # Migration backups
├── migration_scripts/       # Database migration tools
├── one_time/               # Setup and configuration scripts
├── services/               # Core business logic
├── ssl/                    # SSL certificates (when generated)
│   ├── cert.pem           # SSL certificate
│   └── private.key        # SSL private key
├── ui_components/          # UI components and interfaces
├── utils/                  # Utilities and helpers
├── app.py                 # Main application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── servers_config.json    # MCP server configuration
└── Dockerfile            # Docker configuration
```

### Authentication System

- **Multi-Backend Support**: SQLite, YAML, encrypted JSON storage options
- **Password Security**: bcrypt hashing with salt
- **Session Management**: Secure token-based sessions
- **User Isolation**: Complete separation of user data and conversations
- **Audit Logging**: Comprehensive security event tracking

## 🔧 Configuration

### Model Providers

The application supports multiple AI providers configured in `config.py`:

```python
MODEL_OPTIONS = {
    'Azure OpenAI': 'gpt-4.1',
    'OpenAI': 'gpt-4o',
}
```

### User Management

User credentials are managed through multiple backends:

**SQLite (Recommended):**
- Set `USE_SQLITE=true` in `.env`
- Users stored in `keys/users.db`
- Full user management interface for admins

**YAML (Legacy):**
- Users defined in `keys/config.yaml`
- Generated using `one_time/simple_generate_password.py`

**Enhanced JSON (Advanced):**
- Encrypted JSON storage
- Set `USE_ENCRYPTION=true` in `.env`

### MCP Server Configuration

Server endpoints are defined in `servers_config.json`:
```json
{
  "mcpServers": {
    "MSSQL": {
      "transport": "sse",
      "url": "http://mcpserver3:8008/sse",
      "timeout": 600,
      "headers": null,
      "sse_read_timeout": 900
    }
  }
}
```

### Styling and UI

Custom CSS is located in `.streamlit/style.css` for UI customization:
- Enhanced chat interface with animations
- Modern tab styling and layouts
- Responsive design adjustments
- Dark mode support

## 🔒 Security Features

### Authentication Security
- **Multiple Storage Backends**: SQLite, YAML, encrypted JSON
- **Bcrypt Hashing**: Industry-standard password protection
- **Session Management**: Configurable session expiry and secure tokens
- **Account Security**: Failed login tracking and account lockout
- **User Isolation**: Complete separation of user data and conversations

### Application Security
- **SSL/HTTPS Support**: Optional SSL certificate generation
- **Environment Variables**: Secure credential storage
- **Input Validation**: XSS and injection protection
- **Audit Logging**: Comprehensive security event tracking
- **Role-Based Access**: Admin and user permission levels

### Data Security
- **User Session Isolation**: Complete separation between users
- **Encrypted Storage Options**: Multiple encryption backends
- **Secure Backup**: Encrypted backup and recovery system
- **Migration Tools**: Secure data migration between backends

## 🐛 Troubleshooting

### Common Issues

**Authentication Problems:**
- Verify `keys/config.yaml` exists and is properly formatted
- Check user credentials match the generated passwords
- For SQLite: ensure `USE_SQLITE=true` in `.env`
- Clear browser cookies if experiencing login issues

**Connection Problems:**
- Verify MSSQL MCP server is running and accessible
- Check network connectivity to server endpoints
- Ensure proper MSSQL authentication credentials
- Review `servers_config.json` for correct URLs

**API Key Issues:**
- Confirm environment variables are properly set
- Check API key permissions and quotas
- Verify endpoint URLs for Azure OpenAI
- Test API connectivity outside the application

**SSL Certificate Issues:**
- Run certificate generation script: `python generate_ssl_certificate.py`
- Check file permissions on `ssl/` directory
- Verify certificate and key files exist in `ssl/` folder
- Use debug script: `./one_time/debug_ssl.sh`

### Debug Tools

**Authentication Debugging:**
```bash
# Test SQLite authentication
python migration_scripts/sqlite_auth_debug.py

# Verify user migration
python migration_scripts/simple_verification_script.py

# Check password issues
python one_time/password_debug.py
```

**SSL Debugging:**
```bash
# Debug SSL configuration
./one_time/debug_ssl.sh

# Test certificate generation
python generate_ssl_certificate.py
```

**General Debugging:**
- Enable debug mode in the User Management tab
- Check browser console for JavaScript errors
- Monitor Streamlit logs in terminal
- Review authentication and audit logs

## 🔄 Migration and Setup

### Database Migration

**From YAML to SQLite:**
```bash
# Full migration with backup
python migration_scripts/migrate_users_to_sqlite.py

# Quick verification
python migration_scripts/simple_verification_script.py
```

**Fix Authentication Issues:**
```bash
# Comprehensive authentication fix
python one_time/comprehensive_fix.py

# Manual password reset
python one_time/fix_sqlite_auth.py
```

### User Management

**Add New Users:**
- Use the User Management tab as admin
- Or run: `python one_time/promote_admin.py`

**Reset Passwords:**
- Through User Management interface
- Or manually using debug scripts

## 📊 Monitoring and Maintenance

### User Activity
- View user statistics in the sidebar
- Monitor session activity and login patterns
- Export user data for analysis
- Track conversation and message counts

### System Health
- Monitor MCP server connections
- Check AI provider status
- Review audit logs regularly
- Monitor failed login attempts

### Backup and Recovery
- Enable automatic backups in User Management
- Export user data regularly
- Test backup restoration procedures
- Monitor backup file encryption

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

**Version**: 2.1.0  
**Last Updated**: January 2025  
**Security**: Enhanced SQLite authentication, bcrypt password hashing, user session isolation  
**Compatibility**: Python 3.11+, Streamlit 1.44+, MSSQL Server integration

**Enterprise Features**: SSL/HTTPS support, user management interface, audit logging, backup/recovery, migration tools