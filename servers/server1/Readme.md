# Perplexity MCP Server with SSE Protocol

A Model Context Protocol (MCP) server that provides AI-powered web search capabilities using the Perplexity API. This version uses Server-Sent Events (SSE) for real-time communication, making it compatible with web-based MCP clients and browsers.

## 🚀 Features

### **Web Search Capabilities**
- **Intelligent Search**: Leverage Perplexity's AI-powered search across the web
- **Recency Filtering**: Filter results by time period (day, week, month, year)
- **Multiple Models**: Support for all Perplexity AI models
- **Citation Support**: Automatic source citations for all results
- **Advanced Parameters**: Fine-tune search with custom parameters

### **Technical Features**
- **SSE Protocol**: Real-time communication using Server-Sent Events
- **Health Monitoring**: Built-in health check endpoints
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
pip install -r requirements_sse.txt

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

## 🔧 Available Tools

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

**Response Format:**
```
**Query:** latest developments in AI
**Recency Filter:** week
**Model:** sonar
**Response:** [AI-generated response based on recent web content]
**Citations:**
[1] https://example.com/ai-news-1
[2] https://example.com/ai-news-2
**Token Usage:** {"prompt_tokens": 15, "completion_tokens": 150, "total_tokens": 165}
```

### **perplexity_advanced_search**
Advanced search with custom parameters for fine-tuned control.

**Parameters:**
- `query` (string, required): The search query
- `recency` (string, optional): Time filter (default: "month")
- `model` (string, optional): Override the default model
- `max_tokens` (int, optional): Maximum response tokens (default: 512, max: 2048)
- `temperature` (float, optional): Response randomness 0.0-1.0 (default: 0.2)

**Example:**
```python
await perplexity_advanced_search(
    query="comprehensive analysis of renewable energy trends",
    recency="month",
    model="sonar-pro",
    max_tokens=1024,
    temperature=0.3
)
```

**Response Format:**
```json
{
  "query": "comprehensive analysis of renewable energy trends",
  "model": "sonar-pro",
  "recency_filter": "month",
  "parameters": {
    "max_tokens": 1024,
    "temperature": 0.3
  },
  "content": "[Detailed AI-generated analysis]",
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 800,
    "total_tokens": 825
  },
  "citations": ["https://example.com/renewable-1", "https://example.com/renewable-2"],
  "finish_reason": "stop",
  "response_metadata": {
    "timestamp": 1703123456,
    "model_version": "sonar-pro"
  }
}
```

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
  "available_models": [
    "sonar-deep-research",
    "sonar-reasoning-pro",
    "sonar-reasoning",
    "sonar-pro",
    "sonar",
    "r1-1776"
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

### Advanced Research
```python
# Comprehensive research with custom model
result = await perplexity_advanced_search(
    query="impact of climate change on agriculture",
    recency="year",
    model="sonar-deep-research",
    max_tokens=1500,
    temperature=0.1  # More focused, less creative
)

# Quick factual lookup
result = await perplexity_advanced_search(
    query="current population of Tokyo",
    recency="month",
    model="sonar",
    max_tokens=256,
    temperature=0.0  # Most deterministic
)
```

## 🔒 Security & Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PERPLEXITY_API_KEY` | Your Perplexity API key | None | Yes |
| `PERPLEXITY_MODEL` | Default model to use | `sonar` | No |

### API Key Security
- Store API keys in environment variables, never in code
- Use different API keys for development and production
- Monitor API usage and set up billing alerts
- Rotate API keys regularly

### Rate Limiting
Perplexity API has rate limits:
- Free tier: Limited requests per minute
- Pro tier: Higher limits based on subscription
- Monitor usage through the health endpoint

## 🐛 Troubleshooting

### Common Issues

**API Key Not Configured**
```
Error: PERPLEXITY_API_KEY environment variable is required
```
Solution: Set the `PERPLEXITY_API_KEY` environment variable.

**Invalid Model Name**
```
Error: HTTP 400 - Invalid model specified
```
Solution: Use one of the supported models listed in the available_models array.

**Rate Limit Exceeded**
```
Error: HTTP 429 - Rate limit exceeded
```
Solution: Wait before making more requests or upgrade your Perplexity subscription.

**Connection Timeout**
```
Error: aiohttp.ClientTimeout
```
Solution: Check your internet connection and Perplexity API status.

### Debug Mode

Enable debug logging by setting the log level:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Health Check
Monitor server health:
```bash
curl http://localhost:8001/health
```

## 🚀 Production Deployment

### Docker Compose
```yaml
services:
  perplexity-mcp:
    build: .
    ports:
      - "8001:8001"
    environment:
      - PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
      - PERPLEXITY_MODEL=sonar-pro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
```

### Production Considerations
- Use environment-specific API keys
- Implement proper monitoring and alerting
- Set up log aggregation
- Use a reverse proxy (nginx/traefik) for SSL termination
- Monitor API usage and costs
- Implement caching for repeated queries

## 🔄 Integration with MCP Clients

### Web-based Clients
The SSE protocol makes this server compatible with web browsers and web-based MCP clients:

```javascript
// Connect to SSE endpoint
const eventSource = new EventSource('http://localhost:8001/sse');

// Handle MCP messages
eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    // Process MCP protocol messages
};
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

### Caching Strategies
- Cache search results for identical queries
- Implement TTL-based cache expiration
- Use Redis for distributed caching

### Connection Management
- Reuse aiohttp sessions
- Implement connection pooling
- Set appropriate timeouts

### Monitoring
Track these metrics:
- API request latency
- Error rates by endpoint
- Token usage and costs
- Health check response times

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Version**: 0.1.7  
**Last Updated**: July 2025  
**Compatibility**: Perplexity API v1, MCP 1.0+, Python 3.11+