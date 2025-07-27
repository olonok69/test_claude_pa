# Firecrawl MCP Server

A Model Context Protocol (MCP) server that provides web scraping, crawling, and content extraction capabilities through the Firecrawl API. This server enables AI assistants to interact with web content intelligently.

## Overview

The Firecrawl MCP Server acts as a bridge between AI assistants (like Claude) and the Firecrawl web scraping service. It provides tools for scraping individual pages, crawling entire websites, searching the web, extracting structured data, and performing deep research on topics.

## Features

- **Single Page Scraping** - Extract content from individual URLs in multiple formats
- **Batch Scraping** - Efficiently scrape multiple URLs in parallel
- **Website Mapping** - Discover all URLs on a website
- **Website Crawling** - Recursively crawl websites with configurable depth
- **Web Search** - Search the web and optionally scrape results
- **Structured Data Extraction** - Extract specific data using LLM-powered extraction
- **Deep Research** - Conduct comprehensive research on topics
- **LLMs.txt Generation** - Create standardized AI interaction guidelines for websites
- **Multiple Transport Options** - Supports stdio and SSE transports
- **Self-Hosted Support** - Compatible with self-hosted Firecrawl instances

## Installation

### Prerequisites

- Node.js 22 or higher
- npm or yarn
- Firecrawl API key (for cloud service) or self-hosted Firecrawl instance

### Install from npm

```bash
npm install -g @modelcontextprotocol/server-firecrawl
```

### Build from Source

```bash
git clone <repository-url>
cd firecrawl-mcp-server
npm install
npm run build
```

## Configuration

### Environment Variables

Create a `.env` file or set the following environment variables:

```bash
# Required for cloud service
FIRECRAWL_API_KEY=your_api_key_here

# Optional: For self-hosted Firecrawl instances
FIRECRAWL_API_URL=https://your-firecrawl-instance.com

# Optional: Retry configuration
FIRECRAWL_RETRY_MAX_ATTEMPTS=3
FIRECRAWL_RETRY_INITIAL_DELAY=1000
FIRECRAWL_RETRY_MAX_DELAY=10000
FIRECRAWL_RETRY_BACKOFF_FACTOR=2

# Optional: Credit monitoring thresholds
FIRECRAWL_CREDIT_WARNING_THRESHOLD=1000
FIRECRAWL_CREDIT_CRITICAL_THRESHOLD=100

# Optional: Server configuration
PORT=8001
SSE_LOCAL=true  # For SSE transport
CLOUD_SERVICE=true  # For cloud service mode
```

### Claude Desktop Configuration

Add to your Claude Desktop configuration file:

#### For stdio transport (default):
```json
{
  "mcpServers": {
    "firecrawl": {
      "command": "node",
      "args": ["/path/to/firecrawl-mcp-server/dist/index.js"],
      "env": {
        "FIRECRAWL_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

#### For SSE transport:
```json
{
  "mcpServers": {
    "firecrawl": {
      "command": "node",
      "args": ["/path/to/firecrawl-mcp-server/dist/index.js"],
      "env": {
        "FIRECRAWL_API_KEY": "your_api_key_here",
        "SSE_LOCAL": "true",
        "PORT": "8001"
      }
    }
  }
}
```

## Available Tools

### 1. `firecrawl_scrape`
Scrape content from a single URL with advanced options.

**Best for:** Single page content extraction when you know the exact URL.

**Parameters:**
- `url` (required): The URL to scrape
- `formats`: Content formats (markdown, html, rawHtml, screenshot, links, extract)
- `onlyMainContent`: Extract only main content
- `includeTags`: HTML tags to include
- `excludeTags`: HTML tags to exclude
- `waitFor`: Time to wait for dynamic content (ms)
- `timeout`: Maximum page load time (ms)
- `maxAge`: Max age for cached content (ms) - enables 500% faster scrapes
- `actions`: List of actions to perform before scraping
- `extract`: Configuration for structured data extraction
- `mobile`: Use mobile viewport
- `location`: Location settings for scraping

**Example:**
```json
{
  "name": "firecrawl_scrape",
  "arguments": {
    "url": "https://example.com",
    "formats": ["markdown"],
    "onlyMainContent": true,
    "maxAge": 3600000
  }
}
```

### 2. `firecrawl_map`
Map a website to discover all indexed URLs.

**Best for:** Discovering URLs on a website before deciding what to scrape.

**Parameters:**
- `url` (required): Starting URL for discovery
- `search`: Search term to filter URLs
- `ignoreSitemap`: Skip sitemap.xml discovery
- `includeSubdomains`: Include subdomain URLs
- `limit`: Maximum number of URLs to return

**Example:**
```json
{
  "name": "firecrawl_map",
  "arguments": {
    "url": "https://example.com",
    "limit": 100
  }
}
```

### 3. `firecrawl_crawl`
Start an asynchronous crawl job on a website.

**Best for:** Extracting content from multiple related pages.

**Warning:** Crawl responses can be very large. Limit depth and page count.

**Parameters:**
- `url` (required): Starting URL for crawl
- `excludePaths`: URL paths to exclude
- `includePaths`: Only crawl these paths
- `maxDepth`: Maximum link depth
- `limit`: Maximum pages to crawl
- `allowBackwardLinks`: Allow crawling parent directories
- `allowExternalLinks`: Allow external domain crawling
- `deduplicateSimilarURLs`: Remove similar URLs
- `webhook`: Webhook URL for completion notification

**Example:**
```json
{
  "name": "firecrawl_crawl",
  "arguments": {
    "url": "https://example.com/blog/*",
    "maxDepth": 2,
    "limit": 50
  }
}
```

### 4. `firecrawl_check_crawl_status`
Check the status of a crawl job.

**Parameters:**
- `id` (required): Crawl job ID

### 5. `firecrawl_search`
Search the web and optionally extract content from results.

**Best for:** Finding information across multiple websites.

**Parameters:**
- `query` (required): Search query
- `limit`: Maximum results (default: 5)
- `lang`: Language code (default: en)
- `country`: Country code (default: us)
- `scrapeOptions`: Options for scraping results

**Example:**
```json
{
  "name": "firecrawl_search",
  "arguments": {
    "query": "latest AI research 2024",
    "limit": 5,
    "scrapeOptions": {
      "formats": ["markdown"],
      "onlyMainContent": true
    }
  }
}
```

### 6. `firecrawl_extract`
Extract structured information from web pages using LLM.

**Best for:** Extracting specific structured data like prices, names, or details.

**Parameters:**
- `urls` (required): Array of URLs to extract from
- `prompt`: Custom prompt for extraction
- `systemPrompt`: System prompt for LLM
- `schema`: JSON schema for structured extraction
- `allowExternalLinks`: Allow external link extraction
- `enableWebSearch`: Enable web search for context

**Example:**
```json
{
  "name": "firecrawl_extract",
  "arguments": {
    "urls": ["https://example.com/product"],
    "schema": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "price": { "type": "number" },
        "description": { "type": "string" }
      }
    }
  }
}
```

### 7. `firecrawl_deep_research`
Conduct deep web research on a query.

**Best for:** Complex research questions requiring multiple sources.

**Parameters:**
- `query` (required): Research question/topic
- `maxDepth`: Maximum recursive depth (default: 3)
- `timeLimit`: Time limit in seconds (default: 120)
- `maxUrls`: Maximum URLs to analyze (default: 50)

### 8. `firecrawl_generate_llmstxt`
Generate LLMs.txt file for a website.

**Best for:** Creating machine-readable permission guidelines for AI models.

**Parameters:**
- `url` (required): Website URL
- `maxUrls`: Max URLs to process (default: 10)
- `showFullText`: Show full LLMs-full.txt content

## Running the Server

### Stdio Mode (Default)
```bash
node dist/index.js
```

### SSE Server Mode
```bash
SSE_LOCAL=true node dist/index.js
# Or
node dist/sse-server.js
```

### Docker
```bash
docker build -t firecrawl-mcp .
docker run -e FIRECRAWL_API_KEY=your_key -p 8001:8001 firecrawl-mcp
```

## Advanced Features

### Retry Logic
The server implements automatic retry with exponential backoff for rate-limited requests:
- Default: 3 attempts
- Initial delay: 1 second
- Maximum delay: 10 seconds
- Backoff factor: 2x

### Response Management
- Maximum response length: 100KB per response
- Content preview limit: 5KB for listings
- Automatic truncation with notification

### Transport-Aware Logging
- Stdio transport: Logs to stderr to avoid protocol interference
- SSE transport: Uses standard logging mechanism

### Caching Support
Use the `maxAge` parameter in scrape requests for cached content:
- Enables 500% faster scrapes for recently cached pages
- Default: 0 (always scrape fresh)

## Error Handling

The server provides detailed error messages for:
- Invalid API keys
- Rate limiting
- Network errors
- Invalid arguments
- Self-hosted instance compatibility issues

## Development

### Running Tests
```bash
npm test
```

### Building
```bash
npm run build
```

### Type Checking
```bash
npx tsc --noEmit
```

## Troubleshooting

### Common Issues

1. **API Key Not Working**
   - Ensure `FIRECRAWL_API_KEY` is set correctly
   - Check if using cloud service without `CLOUD_SERVICE=true`

2. **Rate Limiting**
   - Adjust retry configuration
   - Consider batching requests
   - Monitor credit usage

3. **Large Response Errors**
   - Use pagination for crawls
   - Limit depth and page count
   - Enable content truncation

4. **Self-Hosted Issues**
   - Verify `FIRECRAWL_API_URL` is correct
   - Check if endpoint supports required features
   - Enable debug logging

### Debug Mode
Set debug logging:
```bash
DEBUG=* node dist/index.js
```

## License

MIT License - See LICENSE file for details

## Changelog

See CHANGELOG.md for version history and updates.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

- Issues: GitHub Issues
- Documentation: https://docs.firecrawl.dev
- MCP Documentation: https://modelcontextprotocol.io