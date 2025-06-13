# MCP Client - AI Chat Interface with Neo4j & HubSpot Integration

A Streamlit-based chat application that connects to Model Context Protocol (MCP) servers to provide AI-powered interactions with Neo4j graph databases and HubSpot CRM systems.

## 🚀 Features

- **Multi-Provider AI Support**: Compatible with OpenAI and Azure OpenAI
- **MCP Server Integration**: Connect to Neo4j and HubSpot MCP servers
- **Real-time Chat Interface**: Interactive chat with conversation history
- **Tool Execution Tracking**: Monitor and debug tool usage
- **Schema-Aware Operations**: Automatic schema retrieval for intelligent queries
- **Responsive Design**: Modern UI with customizable themes

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

4. **Update MCP server configuration**
   
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

5. **Run the application**
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
     mcp-client
   ```

## 🎯 Usage

### Getting Started

1. **Launch the application** and navigate to `http://localhost:8501`

2. **Configure your AI provider**:
   - Select between OpenAI or Azure OpenAI in the sidebar
   - Verify your credentials are loaded (green checkmark)

3. **Connect to MCP servers**:
   - Click "Connect to MCP Servers" in the sidebar
   - Verify successful connection (you'll see available tools)

4. **Start chatting**:
   - Ask questions about your Neo4j database or HubSpot CRM
   - The AI will automatically use appropriate tools to answer

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

## 🏗️ Architecture

```
┌───────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI    │    │   LangChain      │    │   MCP Servers   │
│                   │◄──►│   Agent          │◄──►│                 │
│  - Chat Interface │    │  - Tool Routing  │    │  - Neo4j        │
│  - Config Panel   │    │  - LLM Provider  │    │  - HubSpot      │
│  - Tool Display   │    │  - Memory Mgmt   │    │  - Custom Tools │
└───────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Components

- **`app.py`**: Main Streamlit application entry point
- **`services/`**: Core business logic (AI, MCP, Chat management)
- **`ui_components/`**: Reusable UI components and widgets
- **`utils/`**: Helper functions and utilities
- **`config.py`**: Configuration management

## 🔧 Configuration

### Model Providers

The application supports multiple AI providers configured in `config.py`:

```python
MODEL_OPTIONS = {
    'OpenAI': 'gpt-4o',
    'Azure OpenAI': 'gpt-4o-mini',
}
```

### MCP Server Configuration

Server endpoints are defined in `servers_config.json`. Each server requires:
- **transport**: Connection method (typically "sse")
- **url**: Server endpoint URL
- **timeout**: Connection timeout in seconds
- **sse_read_timeout**: Server-sent events timeout

### Styling

Custom CSS is located in `.streamlit/style.css` for UI customization.

## 🐛 Troubleshooting

### Common Issues

**Connection Problems:**
- Verify MCP servers are running and accessible
- Check network connectivity to server endpoints
- Ensure proper authentication credentials

**API Key Issues:**
- Confirm environment variables are properly set
- Check API key permissions and quotas
- Verify endpoint URLs for Azure OpenAI

**Tool Execution Errors:**
- Review tool execution history in the expandable section
- Check MCP server logs for detailed error information
- Ensure database/CRM permissions are properly configured

### Debug Mode

Enable debug information by:
1. Using the "Tool Execution History" expander
2. Checking browser console for JavaScript errors
3. Monitoring Streamlit logs in terminal

### Performance Optimization

- Adjust `max_tokens` for faster responses
- Use connection pooling for high-traffic scenarios
- Monitor memory usage with multiple concurrent sessions


## 🔄 Version History

- **v1.0.0**: Initial release with Neo4j and HubSpot MCP integration
- Basic chat interface with multi-provider AI support
- Tool execution tracking and conversation management

---
