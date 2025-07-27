# PPF Europe Analysis Platform

A comprehensive agricultural data analysis platform combining wheat and corn market analytics with AI-powered MCP (Model Context Protocol) tools for web search, content extraction, and intelligent data gathering.

## 🚀 Overview

The PPF Europe Analysis Platform is an enterprise-grade Streamlit application that provides:

- **Agricultural Market Analytics**: Real-time tracking and analysis of global wheat and corn supply & demand
- **AI-Powered Research Tools**: Integration with Firecrawl, Google Search, and Perplexity AI through MCP servers
- **Secure Multi-User Access**: Role-based authentication with session management
- **Interactive Dashboards**: Dynamic visualizations for production, trade, stocks, and market trends

## 🌟 Key Features

### 🌾 Agricultural Analytics

#### Wheat Supply & Demand
- **Production Analysis**: Track global wheat production with country-level breakdowns
- **Trade Monitoring**: Monitor exports and imports across major trading nations
- **Stock Management**: Analyze ending stocks and stock-to-use ratios
- **Agricultural Metrics**: Track acreage, yield, and productivity trends
- **Demand Analysis**: Understand world demand by category (Food, Feed, Industrial, Seed)

#### 🌽 Corn Supply & Demand
- **Production Tracking**: Monitor global corn production trends
- **Trade Analysis**: Export/import flows and market share analysis
- **Inventory Management**: Stock levels and usage ratios
- **Yield Analytics**: Productivity metrics and weather impact analysis
- **Consumption Patterns**: World demand breakdown by usage category

### 🤖 AI & MCP Integration

- **Multi-Provider AI Support**: OpenAI GPT-4o and Anthropic Claude integration
- **Web Intelligence Tools**:
  - 🔥 **Firecrawl**: Advanced web scraping, crawling, and content extraction
  - 🔍 **Google Search**: Web search with content extraction and caching
  - 🔮 **Perplexity AI**: AI-powered search with intelligent synthesis
- **Conversation Memory**: Persistent chat history with context awareness
- **Tool Orchestration**: Automatic tool selection based on query intent

### 🔐 Security & Authentication

- **User Authentication**: Secure login with bcrypt password hashing
- **Session Management**: Persistent sessions with configurable expiry
- **SSL/HTTPS Support**: Secure connections on port 8503
- **Role-Based Access**: Pre-authorized email domains and user management

## 📋 Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- SQLite databases (wheat_production.db, corn_production.db)
- API Keys:
  - OpenAI or Anthropic API key
  - Google Custom Search API credentials
  - Firecrawl API key
  - Perplexity API key

## 🛠️ Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ppf-europe-platform
   ```

2. **Install dependencies**
   ```bash
   cd client
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the client directory:
   ```env
   # AI Provider Configuration
   OPENAI_API_KEY=your_openai_key
   # OR
   ANTHROPIC_API_KEY=your_anthropic_key
   
   # MCP Server Tools
   FIRECRAWL_API_KEY=your_firecrawl_key
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
   PERPLEXITY_API_KEY=your_perplexity_key
   
   # Optional SSL
   SSL_ENABLED=true
   ```

4. **Set up databases**
   ```bash
   cd database_setup
   python database_setup.py  # For wheat database
   # Additional setup scripts for corn database
   ```

5. **Configure user authentication**
   ```bash
   python simple_generate_password.py
   ```
   
   Default credentials:
   - **admin**: very_Secure_p@ssword_123!
   - Additional users as configured

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t ppf-europe-platform .
   ```

2. **Run the container**
   ```bash
   docker run -p 8501:8501 -p 8503:8503 \
     -v $(pwd)/.env:/app/.env \
     -v $(pwd)/keys:/app/keys \
     -v $(pwd)/wheat_production.db:/app/wheat_production.db \
     -v $(pwd)/corn_production.db:/app/corn_production.db \
     ppf-europe-platform
   ```

## 🎯 Usage

### Getting Started

1. **Access the platform**
   - HTTP: `http://localhost:8501`
   - HTTPS: `https://localhost:8503` (if SSL enabled)

2. **Login** with your credentials

3. **Navigate** using the sidebar menu:
   - 🌾 Wheat Supply & Demand
   - 🌽 Corn Supply & Demand
   - 🤖 AI & MCP Tools

### Agricultural Analysis Features

#### Supply & Demand Dashboards
Each commodity (wheat/corn) includes:
1. **Production**: Global and country-level production metrics
2. **Exports**: Major exporter analysis and trade flows
3. **Imports**: Import patterns and major importers
4. **Ending Stocks**: Inventory levels and trends
5. **Stock-to-Use Ratio**: Market tightness indicators
6. **Acreage**: Planted and harvested area analysis
7. **Yield**: Productivity metrics and trends
8. **World Demand**: Consumption breakdown by category

#### Interactive Features
- **Data Editing**: In-line editing of projections and estimates
- **Visualizations**: Dynamic charts with Plotly
- **Export/Import**: JSON data export and import functionality
- **Historical Analysis**: Multi-year trend comparisons
- **Status Indicators**: Actual vs. estimate vs. projection markers

### AI & MCP Tools

Access the AI tools through the dedicated MCP interface:

1. **Navigate** to "🤖 AI & MCP Tools" from the main menu
2. **Connect** to MCP servers in the Connections tab
3. **Chat** with AI using natural language queries

#### Example Queries

**Agricultural Research:**
```
"Search for the latest USDA wheat production forecasts"
"Find recent news about corn export trends from Brazil"
"Analyze the impact of weather on Australian wheat yields"
```

**Market Analysis:**
```
"Search for global grain market reports and extract key insights"
"Find commodity price trends for wheat in the last quarter"
"Research the impact of Ukraine conflict on grain exports"
```

**Data Extraction:**
```
"Scrape agricultural statistics from government websites"
"Extract wheat production data from FAOSTAT"
"Find and analyze multiple sources about corn demand trends"
```

## 🏗️ Architecture

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Streamlit UI      │     │   LangChain      │     │   MCP Servers   │
│                     │◄────┤   Agent          │◄────┤                 │
│  - Dashboards       │     │  - Tool Router   │     │  - Firecrawl    │
│  - Authentication   │     │  - Memory Mgmt   │     │  - Google Search│
│  - Data Entry       │     │  - LLM Provider  │     │  - Perplexity   │
└─────────────────────┘     └──────────────────┘     └─────────────────┘
         │                                                      │
         ▼                                                      ▼
┌─────────────────────┐                              ┌─────────────────┐
│   SQLite DBs        │                              │   External APIs │
│  - wheat_production │                              │  - OpenAI/Claude│
│  - corn_production  │                              │  - Search APIs  │
└─────────────────────┘                              └─────────────────┘
```

### Key Components

- **`app.py`**: Main application entry with authentication
- **`pages/`**: Individual dashboard pages for each metric
  - `1_wheat_production.py` through `8_wheat_world_demand.py`: Wheat analytics
  - `10_corn_production.py` through `17_corn_world_demand.py`: Corn analytics
  - `9_mcp_app.py`: AI & MCP tools interface
- **`services/`**: Core business logic
  - `ai_service.py`: LLM provider management
  - `mcp_service.py`: MCP server connections
  - `chat_service.py`: Conversation management
- **`wheat_helpers/` & `corn_helpers/`**: Database operations and utilities
- **`database_setup/`**: Database initialization and management scripts

## 🔧 Configuration

### Database Management

The platform uses SQLite databases with the following tables:
- Production data
- Export/Import statistics
- Stock levels
- Stock-to-use ratios
- Acreage information
- Yield data
- World demand by category

### MCP Server Configuration

Servers are configured in `servers_config.json`:
```json
{
  "mcpServers": {
    "Firecrawl": {
      "transport": "sse",
      "url": "http://mcpserver1:8001/sse"
    },
    "Google Search": {
      "transport": "sse",
      "url": "http://mcpserver2:8002/sse"
    },
    "Perplexity Search": {
      "transport": "sse",
      "url": "http://mcpserver3:8003/sse"
    }
  }
}
```

### Year Configuration

The platform tracks multiple marketing years:
- **2022/2023**: Actual data
- **2023/2024**: Actual data
- **2024/2025**: Current estimates
- **2025/2026**: Projections

## 🔒 Security Features

- **Password Protection**: Bcrypt hashing with salt
- **Session Security**: Configurable timeout and secure cookies
- **API Key Management**: Environment variable storage
- **Access Control**: Pre-authorized email domain validation
- **SSL Support**: Optional HTTPS with self-signed certificates

## 📊 Data Management

### Import/Export
- Export dashboard data to JSON format
- Import previously saved configurations
- Bulk data updates through Excel file imports

### Audit Trail
- Track all data modifications
- User attribution for changes
- Timestamp logging

### Backup/Restore
- Full database backup capabilities
- Point-in-time restoration
- Data validation and integrity checks

## 🚀 Advanced Features

### Enhanced Configuration Mode
Enable advanced features including:
- Multiple AI provider support
- Custom model parameters
- Bulk environment variable management
- Model testing and validation

### Caching
- Smart caching for web search results
- API response caching to reduce costs
- Configurable cache expiration

### Multi-User Support
- Concurrent user sessions
- Individual conversation histories
- User-specific preferences

## 🐛 Troubleshooting

### Common Issues

**Database Connection:**
- Ensure SQLite database files exist in the root directory
- Check file permissions
- Run database setup scripts if needed

**MCP Connection Issues:**
- Verify MCP servers are running
- Check network connectivity
- Validate API credentials

**Authentication Problems:**
- Verify `keys/config.yaml` exists
- Check password requirements
- Clear browser cookies if needed

## 🔄 Updates & Maintenance

### Database Updates
Use the reload scripts in `database_setup/`:
- `reload_wheat_*.py`: Update specific wheat data tables
- Similar scripts for corn data

### Adding New Users
1. Edit `simple_generate_password.py`
2. Add users to the configuration
3. Run the script to generate new credentials

## 📝 License

[Your License Information]

## 🤝 Contributing

[Your Contributing Guidelines]

---

**Version**: 3.0.0  
**Last Updated**: January 2025  
**Platform**: Streamlit 1.44+, Python 3.11+  
**Database**: SQLite with wheat and corn production data  
**AI Integration**: OpenAI GPT-4o, Anthropic Claude, MCP Protocol