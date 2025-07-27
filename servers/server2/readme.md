# Google Search MCP Server

A high-performance Model Context Protocol (MCP) server implementation for Google Search integration, featuring intelligent caching, webpage content extraction, and real-time communication through Server-Sent Events (SSE).

## 🌟 Key Features

### **Intelligent Caching System**
- **30-minute cache** for Google Search API results
- **2-hour cache** for webpage content
- **Automatic cache cleanup** and memory management
- **LRU eviction** for optimal memory usage
- **Request deduplication** to prevent redundant API calls

### **Core Capabilities**
- **Google Custom Search Integration**: Perform web searches with customizable result counts
- **Webpage Content Extraction**: Clean, readable text extraction from any URL
- **Cache Management Tools**: Monitor and control cache behavior
- **Health Monitoring**: Optimized health checks without API calls
- **Docker Support**: Production-ready containerized deployment

### **Performance Optimizations**
- **API Cost Reduction**: Cached responses reduce API usage by up to 80%
- **Response Time**: Cached results served in <10ms vs 500-2000ms for API calls
- **Memory Efficient**: Automatic cleanup of expired entries
- **Smart Health Checks**: No external API calls during health monitoring

## 📊 Architecture Overview

```
google-search-mcp-server/
├── main.js                 # Express server with SSE transport
├── tools/                  # MCP tool implementations
│   ├── searchTool.js      # Google Search with caching
│   ├── readWebpageTool.js # Webpage extraction with caching
│   └── cacheManagementTools.js # Cache control utilities
├── utils/                  # Utility functions
│   └── optimizedHealthCheck.js # API-free health monitoring
├── prompts/               # MCP prompt system (extensible)
└── categories/            # Data classifications
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ or Docker
- Google Custom Search API credentials
- MCP-compatible client (Claude Desktop, etc.)

### 1. Google API Setup

#### Get API Key:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the **Custom Search API**
4. Create credentials → API Key
5. (Optional) Restrict key to Custom Search API

#### Create Search Engine:
1. Go to [Google Custom Search](https://cse.google.com/cse/)
2. Click "New search engine"
3. Configure:
   - Search the entire web: ON
   - Or specify specific sites to search
4. Get the Search Engine ID (cx parameter)

### 2. Environment Configuration

Create a `.env` file:
```env
# Required - Google API credentials
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here

# Optional - Server configuration
PORT=8002
HOST=0.0.0.0
```

### 3. Installation

#### Option A: Docker (Recommended)
```bash
# Using Docker Compose
docker-compose up mcpserver2

# Or standalone Docker
docker build -t google-search-mcp-server .
docker run -p 8002:8002 --env-file .env google-search-mcp-server
```

#### Option B: Node.js
```bash
# Install dependencies
npm install

# Start production server
npm start

# Development mode with auto-reload
npm run dev
```

### 4. MCP Client Configuration

Add to your MCP client config (e.g., Claude Desktop):
```json
{
  "mcpServers": {
    "google_search": {
      "transport": "sse",
      "url": "http://localhost:8002/sse",
      "timeout": 600,
      "sse_read_timeout": 900
    }
  }
}
```

## 🛠️ Available Tools

### 1. **google-search** - Web Search with Caching
Performs Google searches with intelligent result caching.

**Parameters:**
- `query` (string, required): Search query
- `num` (number, optional): Results to return (1-10, default: 5)

**Example:**
```javascript
{
  "query": "latest AI developments 2024",
  "num": 10
}
```

**Returns:**
```json
{
  "query": "latest AI developments 2024",
  "results": [
    {
      "title": "Article Title",
      "link": "https://example.com/article",
      "snippet": "Brief description..."
    }
  ],
  "totalResults": "2,340,000",
  "cached": false,
  "cacheInfo": "Results cached for 30 minutes"
}
```

### 2. **read-webpage** - Content Extraction with Caching
Extracts clean, readable content from web pages.

**Parameters:**
- `url` (string, required): Webpage URL
- `skipCache` (boolean, optional): Force fresh fetch (default: false)

**Example:**
```javascript
{
  "url": "https://example.com/article",
  "skipCache": false
}
```

**Returns:**
```json
{
  "title": "Page Title",
  "description": "Meta description",
  "author": "Author Name",
  "text": "Clean article content...",
  "url": "https://example.com/article",
  "contentLength": 5234,
  "fetchedAt": "2024-01-15T10:30:00Z",
  "cached": true,
  "truncated": false
}
```

### 3. **clear-cache** - Cache Management
Clears cached search results and webpage content.

**Parameters:**
- `cacheType` (enum, optional): 'search', 'webpage', or 'all' (default: 'all')

**Example:**
```javascript
{
  "cacheType": "all"
}
```

### 4. **cache-stats** - Cache Monitoring
Provides detailed cache usage statistics.

**Parameters:**
- `detailed` (boolean, optional): Include detailed stats (default: false)

**Example Response:**
```json
{
  "overview": {
    "totalCachedItems": 45,
    "totalValidItems": 38,
    "totalExpiredItems": 7,
    "estimatedMemoryKB": 1245
  },
  "efficiency": {
    "cacheUtilization": "84%",
    "apiCallsAvoided": 38,
    "memoryEfficiency": "28 KB per item"
  },
  "recommendations": [
    "Cache is working effectively - good API usage reduction"
  ]
}
```

## 📋 Common Workflows

### Research Workflow
```javascript
// 1. Search for information
google-search {
  "query": "climate change impact 2024 report",
  "num": 5
}

// 2. Read interesting results
read-webpage {
  "url": "https://example.com/climate-report"
}

// 3. Search for related topics
google-search {
  "query": "renewable energy solutions 2024"
}
```

### Cache Management Workflow
```javascript
// 1. Check cache status
cache-stats {
  "detailed": true
}

// 2. Clear if needed
clear-cache {
  "cacheType": "search"
}

// 3. Verify cleanup
cache-stats {}
```

## 🔍 Monitoring & Debugging

### Health Endpoints

**Basic Health Check** (Cached, no API calls):
```bash
curl http://localhost:8002/health
```

**Detailed Statistics**:
```bash
curl http://localhost:8002/health/detailed
```

**Response includes:**
- Server status and version
- Active connections
- Cache statistics
- Memory usage
- Optimization features

### Manual Cache Management
```bash
# Clear all caches
curl http://localhost:8002/cache/clear

# Response shows cleared entries
{
  "message": "Caches cleared successfully",
  "cleared": {
    "search": 23,
    "webpage": 15,
    "total": 38
  }
}
```

### Docker Logs
```bash
# View container logs
docker-compose logs -f mcpserver2

# Or for standalone container
docker logs -f <container_id>
```

## 🎯 Performance Benefits

### API Cost Reduction
- **Before**: Every search query = 1 API call
- **After**: Repeated queries served from cache
- **Savings**: Up to 80% reduction in API calls

### Response Time Improvements
| Operation | Without Cache | With Cache | Improvement |
|-----------|--------------|------------|-------------|
| Search Query | 500-2000ms | <10ms | 50-200x faster |
| Webpage Fetch | 1000-5000ms | <10ms | 100-500x faster |

### Memory Efficiency
- **Automatic cleanup** every 10-30 minutes
- **LRU eviction** when cache is full
- **Typical usage**: 1-5MB for moderate activity

## ⚠️ Troubleshooting

### Common Issues

#### "API key not found" Error
```bash
# Verify environment variable
echo $GOOGLE_API_KEY

# Check .env file
cat .env | grep GOOGLE_API_KEY

# Ensure API is enabled in Google Cloud Console
```

#### "403 Forbidden" from Google API
- Check API key restrictions
- Verify daily quota hasn't been exceeded
- Ensure Custom Search API is enabled

#### Connection Issues
```bash
# Check if server is running
curl http://localhost:8002/health

# Verify port availability
netstat -an | grep 8002

# Check Docker container status
docker ps | grep mcpserver2
```

#### Cache Not Working
```bash
# Check cache statistics
curl http://localhost:8002/health/detailed | jq '.cache'

# Clear cache and retry
curl http://localhost:8002/cache/clear
```

## 🔧 Advanced Configuration

### Cache TTL Customization
Modify cache durations in tool files:
```javascript
// searchTool.js
const searchCache = new SearchCache(30); // 30 minutes

// readWebpageTool.js
const webpageCache = new WebpageCacheClass(2); // 2 hours
```

### Memory Limits
Adjust maximum cache sizes:
```javascript
// readWebpageTool.js
this.maxCacheSize = 1000; // Maximum cached pages
```

### Health Check Frequency
```javascript
// optimizedHealthCheck.js
const healthCache = new HealthCheckCache(5); // 5 minutes
```

## 🏗️ Development

### Adding New Tools

1. **Create tool class** extending `BaseTool`:
```javascript
import { BaseTool } from './baseTool.js';

export class MyNewTool extends BaseTool {
  constructor() {
    super(MySchema, MyToolDefinition);
  }
  
  async process(args) {
    // Implementation
  }
}
```

2. **Register in toolsRegistry.js**:
```javascript
import { MyNewTool } from './myNewTool.js';
registerTool(new MyNewTool());
```

### Running Tests
```bash
# Start development server
npm run dev

# Test with curl
curl -X POST http://localhost:8002/messages?sessionId=test \
  -H "Content-Type: application/json" \
  -d '{"method":"tools/call","params":{"name":"google-search","arguments":{"query":"test"}}}'
```

## 📈 Optimization Features

### Intelligent Caching
- **Query normalization**: Case-insensitive, trimmed queries
- **URL cleaning**: Removes tracking parameters
- **Deduplication**: Prevents concurrent identical requests

### Resource Management
- **Connection pooling**: Efficient HTTP connections
- **Timeout handling**: 10-15 second timeouts
- **Error recovery**: Graceful degradation

### Health Check Optimization
- **No external API calls**: Prevents unnecessary usage
- **5-minute cache**: Reduces server load
- **Instant status**: Sub-millisecond response

## 🔒 Security Considerations

- **API Key Protection**: Never expose keys in logs
- **Input Validation**: Zod schemas validate all inputs
- **Content Sanitization**: Scripts/styles removed from pages
- **Error Handling**: No sensitive data in error messages

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📚 Resources

- [Google Custom Search API](https://developers.google.com/custom-search/v1/overview)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Docker Documentation](https://docs.docker.com/)
- [Express.js Guide](https://expressjs.com/en/guide/routing.html)

---

**Version**: 1.0.1  
**Last Updated**: July 2025  
**Node.js**: 18+  
**API**: Google Custom Search v1