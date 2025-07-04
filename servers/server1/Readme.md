# Perplexity MCP Server with SSE Protocol & CSV Categories

A Model Context Protocol (MCP) server that provides AI-powered web search capabilities using the Perplexity API, plus access to categorized show/industry data from CSV files. This version uses Server-Sent Events (SSE) for real-time communication, making it compatible with web-based MCP clients and browsers.

## 🚀 Features

### **Web Search Capabilities**
- **Intelligent Search**: Leverage Perplexity's AI-powered search across the web
- **Recency Filtering**: Filter results by time period (day, week, month, year)
- **Multiple Models**: Support for all Perplexity AI models
- **Citation Support**: Automatic source citations for all results
- **Advanced Parameters**: Fine-tune search with custom parameters

### **CSV Categories Data Access**
- **Show Categories**: Access categorized data organized by shows (CAI, DOL, CCSE, BDAIW, DCW)
- **Industry Organization**: Browse categories by industry and product classifications
- **Search Functionality**: Search across all category data with flexible filtering
- **Dynamic Resources**: Real-time access to CSV data through MCP resources

### **Technical Features**
- **SSE Protocol**: Real-time communication using Server-Sent Events
- **Health Monitoring**: Built-in health check endpoints with CSV status
- **Async Operations**: High-performance async/await architecture
- **Error Handling**: Comprehensive error management and logging
- **Environment Configuration**: Flexible configuration via environment variables

### **Available Models**
- **sonar-deep-research**: 128k context - Enhanced research capabilities
- **sonar-reasoning-pro**: 128k context - Advanced reasoning with professional focus
- **sonar-reasoning**: 128k context - Enhanced reasoning capabilities
- **sonar-pro**: 200k context - Professional grade model
- **sonar**: 128k context - Default model (recommended)
- **r1-1776**: 128k context - Alternative architecture

## 📋 Prerequisites

- Python 3.11+
- Perplexity API key (get one at [perplexity.ai](https://perplexity.ai))
- Docker (optional, for containerized deployment)
- CSV file with categories data (included: `src/perplexity_mcp/categories/classes.csv`)

## 🛠️ Installation & Setup

### 1. Environment Configuration

Create a `.env` file in the server directory:

```env
# Perplexity API Configuration
PERPLEXITY_API_KEY=your_perplexity_api_key_here
PERPLEXITY_MODEL=sonar
```

### 2. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python perplexity_sse_server.py
```

### 3. Docker Deployment

```bash
# Build the Docker image
docker build -t perplexity-mcp-sse .

# Run the container
docker run -p 8001:8001 \
  -e PERPLEXITY_API_KEY=your_api_key_here \
  -e PERPLEXITY_MODEL=sonar \
  perplexity-mcp-sse
```

## 🔧 Available Tools (3 Tools)

### **perplexity_search_web**
Standard web search with recency filtering.

**Parameters:**
- `query` (string, required): The search query
- `recency` (string, optional): Time filter - "day", "week", "month", "year" (default: "month")

**Example:**
```python
await perplexity_search_web(
    query="latest developments in AI",
    recency="week"
)
```

### **perplexity_advanced_search**
Advanced search with custom parameters for fine-tuned control.

**Parameters:**
- `query` (string, required): The search query
- `recency` (string, optional): Time filter (default: "month")
- `model` (string, optional): Override the default model
- `max_tokens` (int, optional): Maximum response tokens (default: 512, max: 2048)
- `temperature` (float, optional): Response randomness 0.0-1.0 (default: 0.2)

### **search_show_categories** ⭐ NEW
Search and filter show categories from the CSV data.

**Parameters:**
- `show_name` (string, optional): Filter by specific show (CAI, DOL, CCSE, BDAIW, DCW)
- `industry_filter` (string, optional): Filter by industry name (partial match)
- `product_filter` (string, optional): Filter by product name (partial match)

**Example:**
```python
await search_show_categories(
    show_name="CAI",
    industry_filter="Cloud",
    product_filter="AI"
)
```

## 🗂️ Available Resources (6 Resources)

### **categories://all**
Get complete CSV data with all show categories.

**Returns:**
- Total count of categories
- Complete dataset with Show, Industry, Product columns
- Structured JSON format

### **categories://shows**
Get categories organized by show with statistics.

**Returns:**
- Overview of all shows (CAI, DOL, CCSE, BDAIW, DCW)
- Categories count per show
- Industry breakdown per show

### **categories://shows/{show_name}**
Get categories for a specific show.

**Parameters:**
- `show_name`: Show identifier (CAI, DOL, CCSE, BDAIW, DCW)

**Example URLs:**
- `categories://shows/CAI` - Cloud and AI Infrastructure categories
- `categories://shows/DOL` - DevOps Lifecycle categories
- `categories://shows/CCSE` - Cloud and Cyber Security Expo categories
- `categories://shows/BDAIW` - Big Data & AI World categories
- `categories://shows/DCW` - Data Centre World categories

### **categories://industries**
Get categories organized by industry.

**Returns:**
- All industries with their products
- Show associations for each industry
- Product counts per industry

### **categories://industries/{industry_name}**
Get categories for a specific industry.

**Parameters:**
- `industry_name`: Industry name (case-insensitive, partial match)

**Example URLs:**
- `categories://industries/cloud` - Cloud-related categories
- `categories://industries/security` - Security-related categories
- `categories://industries/ai` - AI-related categories

### **categories://search/{query}**
Search across all category data.

**Parameters:**
- `query`: Search term to find in Show, Industry, or Product fields

**Example URLs:**
- `categories://search/artificial intelligence` - Find AI-related categories
- `categories://search/security` - Find security-related entries
- `categories://search/cloud` - Find cloud-related categories

## 🎯 CSV Data Structure

The CSV file contains show categories with the following structure:

```csv
Show,Industry,Product
CAI,IT Infrastructure & Hardware,Semiconductor Technologies
CAI,Cloud and AI Infrastructure Services,Hyperscale Cloud Solutions
DOL,Application Delivery & Runtime,Application Delivery
CCSE,Application Security,Application Security
BDAIW,AI & ML Platforms,Cloud AI Platform
DCW,Building Equipment,Electrical Systems
```

**Show Categories:**
- **CAI**: Cloud and AI Infrastructure
- **DOL**: DevOps Lifecycle  
- **CCSE**: Cloud and Cyber Security Expo
- **BDAIW**: Big Data & AI World
- **DCW**: Data Centre World

## 🔌 API Endpoints

### Health Check
```
GET /health
```

**Healthy Response:**
```json
{
  "status": "healthy",
  "version": "0.1.7",
  "model": "sonar",
  "api_key_configured": true,
  "test_query_successful": true,
  "csv_data": {
    "available": true,
    "total_records": 45,
    "shows": ["CAI", "DOL", "CCSE", "BDAIW", "DCW"]
  },
  "available_models": [...],
  "available_resources": [
    "categories://all",
    "categories://shows",
    "categories://shows/{show_name}",
    "categories://industries",
    "categories://industries/{industry_name}",
    "categories://search/{query}"
  ]
}
```

### Server-Sent Events
```
GET /sse
```
Main endpoint for MCP communication via Server-Sent Events.

### Message Handling
```
POST /messages/
```
Handles MCP protocol messages.

## 🎯 Usage Examples

### Basic Web Search
```python
# Search for recent news
result = await perplexity_search_web(
    query="breaking news today",
    recency="day"
)

# Search for technical information
result = await perplexity_search_web(
    query="Python async best practices",
    recency="month"
)
```

### CSV Categories Usage
```python
# Get all CAI show categories
result = await search_show_categories(show_name="CAI")

# Find AI-related categories across all shows
result = await search_show_categories(product_filter="AI")

# Search for cloud security categories
result = await search_show_categories(
    industry_filter="security", 
    product_filter="cloud"
)
```

### Resource Access Examples
```python
# Access via MCP client resources
all_categories = client.read_resource("categories://all")
cai_categories = client.read_resource("categories://shows/CAI")
cloud_categories = client.read_resource("categories://search/cloud")
```

### Advanced Research with Categories
```python
# 1. Search categories for context
categories = await search_show_categories(
    show_name="BDAIW",
    industry_filter="AI"
)

# 2. Use category info in Perplexity search
result = await perplexity_advanced_search(
    query="latest AI platform developments for enterprise",
    recency="month",
    model="sonar-pro",
    max_tokens=1024
)
```

## 🔒 Security & Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PERPLEXITY_API_KEY` | Your Perplexity API key | None | Yes |
| `PERPLEXITY_MODEL` | Default model to use | `sonar` | No |

### CSV File Requirements
- Located at: `src/perplexity_mcp/categories/classes.csv`
- Headers: `Show,Industry,Product`
- UTF-8 encoding
- Automatically loaded on server startup

## 🐛 Troubleshooting

### Common Issues

**CSV File Not Found**
```
Warning: CSV file not found at src/perplexity_mcp/categories/classes.csv
```
Solution: Ensure the CSV file exists at the correct path with proper headers.

**Empty CSV Data**
```
Info: CSV data loaded successfully: 0 records
```
Solution: Check CSV file format and ensure it contains data rows.

**Resource Not Found**
```
Error: Show 'INVALID' not found
```
Solution: Use valid show names (CAI, DOL, CCSE, BDAIW, DCW) or check available shows.

**API Key Not Configured**
```
Error: PERPLEXITY_API_KEY environment variable is required
```
Solution: Set the `PERPLEXITY_API_KEY` environment variable.

### Debug Mode

Enable debug logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Health Check with CSV Status
Monitor server and CSV data health:
```bash
curl http://localhost:8001/health
```

## 🚀 Production Deployment

### Docker Compose with CSV Mount
```yaml
services:
  perplexity-mcp:
    build: .
    ports:
      - "8001:8001"
    environment:
      - PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
      - PERPLEXITY_MODEL=sonar-pro
    volumes:
      - ./src/perplexity_mcp/categories:/app/src/perplexity_mcp/categories:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
```

### CSV Data Management
- **Version Control**: Keep CSV file in version control
- **Data Updates**: Restart server after CSV updates
- **Backup**: Regular backup of category data
- **Validation**: Ensure CSV integrity before deployment

## 🔄 Integration with MCP Clients

### Web-based Clients
Access both search and category data:

```javascript
// Access Perplexity search
const searchResult = await client.callTool('perplexity_search_web', {
    query: 'AI trends 2024',
    recency: 'month'
});

// Access category resources
const caiCategories = await client.readResource('categories://shows/CAI');
const aiCategories = await client.readResource('categories://search/artificial intelligence');

// Search categories with tool
const categoryResult = await client.callTool('search_show_categories', {
    show_name: 'BDAIW',
    product_filter: 'AI'
});
```

### MCP Client Configuration
```json
{
  "mcpServers": {
    "perplexity-search": {
      "command": "python",
      "args": ["perplexity_sse_server.py"],
      "cwd": "/path/to/server",
      "env": {
        "PERPLEXITY_API_KEY": "your_api_key"
      }
    }
  }
}
```

## 📈 Performance Optimization

### CSV Data Caching
- CSV data loaded once at startup
- In-memory processing for fast access
- Minimal overhead for category operations

### Resource Access Patterns
- **Static Resources**: `categories://all`, `categories://shows`
- **Dynamic Resources**: `categories://shows/{show}`, `categories://search/{query}`
- **Cached Responses**: Industry and show summaries

### Search Optimization
- Combine category context with Perplexity searches
- Use category data to refine search queries
- Filter results using industry/product knowledge

## 🤝 Contributing

### Adding New CSV Resources

1. **Extend Resource Functions**: Add new `@mcp.resource()` decorators
2. **Update Health Check**: Include new resources in health response
3. **Add Documentation**: Update this README with new resource info
4. **Test Resource Access**: Verify resources work with MCP clients

### CSV Data Extensions

1. **Add New Columns**: Extend CSV structure as needed
2. **Update Parsing Logic**: Modify `load_csv_data()` function
3. **Create New Filters**: Add filtering options to search tool
4. **Update Resources**: Extend resource responses with new data

## 📄 License

This project is licensed under the MIT License.

---

**Version**: 0.1.7  
**Last Updated**: July 2025  
**Compatibility**: Perplexity API v1, MCP 1.0+, Python 3.11+  
**Tools**: 3 (Perplexity search + CSV categories)  
**Resources**: 6 (Complete CSV data access)