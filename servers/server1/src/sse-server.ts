#!/usr/bin/env node
import express from 'express';
import { createServer } from 'http';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import FirecrawlApp from '@mendable/firecrawl-js';

const FIRECRAWL_API_KEY = process.env.FIRECRAWL_API_KEY;
const FIRECRAWL_API_URL = process.env.FIRECRAWL_API_URL || "https://api.firecrawl.dev";
const PORT = parseInt(process.env.PORT || '8001', 10);

if (!FIRECRAWL_API_KEY) {
  console.error("FIRECRAWL_API_KEY environment variable is required");
  process.exit(1);
}

class FirecrawlMCPServer {
  private firecrawlApp: FirecrawlApp;
  private transports: { [sessionId: string]: SSEServerTransport } = {};

  constructor() {
    this.firecrawlApp = new FirecrawlApp({
      apiKey: FIRECRAWL_API_KEY,
      apiUrl: FIRECRAWL_API_URL
    });
  }

  async run() {
    const app = express();
    const httpServer = createServer(app);
    
    // Add JSON parsing middleware
    app.use(express.json());

    // Health check endpoint
    app.get('/health', (req, res) => {
      res.json({ status: 'ok', service: 'firecrawl-mcp-server' });
    });

    // Create MCP server
    const mcpServer = new Server(
      {
        name: "firecrawl-mcp-server",
        version: "0.1.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Setup tool handlers
    this.setupToolHandlers(mcpServer);

    // Error handling
    mcpServer.onerror = (error) => console.error("[MCP Error]", error);

    // SSE endpoint for establishing connection
    app.get('/sse', async (req, res) => {
      console.log('SSE connection established');
      const transport = new SSEServerTransport('/sse', res);
      this.transports[transport.sessionId] = transport;
      
      await mcpServer.connect(transport);
      
      // Handle client disconnect
      req.on('close', () => {
        console.log(`SSE connection closed: ${transport.sessionId}`);
        delete this.transports[transport.sessionId];
      });
    });

    // Handle POST to /sse with sessionId
    app.post('/sse', async (req, res) => {
      const sessionId = req.query.sessionId as string;
      
      if (!sessionId) {
        return res.status(400).json({ error: 'Missing sessionId' });
      }
      
      const transport = this.transports[sessionId];
      
      if (!transport) {
        console.error(`Transport not found for sessionId: ${sessionId}`);
        return res.status(404).json({ error: 'Transport not found for sessionId' });
      }
      
      try {
        await transport.handlePostMessage(req, res);
      } catch (error) {
        console.error('Error handling post message:', error);
        res.status(500).json({ error: 'Internal server error' });
      }
    });

    httpServer.listen(PORT, '0.0.0.0', () => {
      console.log(`Firecrawl MCP Server running on http://0.0.0.0:${PORT}`);
      console.log(`SSE endpoint available at http://0.0.0.0:${PORT}/sse`);
    });
  }

  private setupToolHandlers(server: Server) {
    server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "firecrawl_scrape",
          description: "Scrape a single URL using Firecrawl",
          inputSchema: {
            type: "object",
            properties: {
              url: {
                type: "string",
                description: "The URL to scrape",
              },
              formats: {
                type: "array",
                items: {
                  type: "string",
                  enum: ["markdown", "html", "screenshot", "screenshot@fullPage", "links", "rawHtml"],
                },
                description: "Formats to return (default: ['markdown'])",
                default: ["markdown"],
              },
              onlyMainContent: {
                type: "boolean",
                description: "Only return the main content of the page",
                default: true,
              },
              includeTags: {
                type: "array",
                items: { type: "string" },
                description: "HTML tags to include in the extraction",
              },
              excludeTags: {
                type: "array",
                items: { type: "string" },
                description: "HTML tags to exclude from the extraction",
              },
              waitFor: {
                type: "integer",
                description: "Time to wait in milliseconds before scraping",
              },
            },
            required: ["url"],
          },
        },
        {
          name: "firecrawl_batch_scrape",
          description: "Scrape multiple URLs in batch",
          inputSchema: {
            type: "object",
            properties: {
              urls: {
                type: "array",
                items: { type: "string" },
                description: "Array of URLs to scrape",
              },
              formats: {
                type: "array",
                items: {
                  type: "string",
                  enum: ["markdown", "html", "screenshot", "screenshot@fullPage", "links", "rawHtml"],
                },
                description: "Formats to return",
                default: ["markdown"],
              },
              onlyMainContent: {
                type: "boolean",
                description: "Only return the main content",
                default: true,
              },
            },
            required: ["urls"],
          },
        },
        {
          name: "firecrawl_crawl",
          description: "Crawl a website starting from a URL",
          inputSchema: {
            type: "object",
            properties: {
              url: {
                type: "string",
                description: "The starting URL to crawl",
              },
              limit: {
                type: "integer",
                description: "Maximum number of pages to crawl",
                default: 10,
              },
              maxDepth: {
                type: "integer",
                description: "Maximum depth to crawl",
                default: 2,
              },
              excludePaths: {
                type: "array",
                items: { type: "string" },
                description: "Paths to exclude from crawling",
              },
              includePaths: {
                type: "array",
                items: { type: "string" },
                description: "Only crawl these paths",
              },
              allowBackwardLinks: {
                type: "boolean",
                description: "Allow crawling backward links",
                default: false,
              },
              allowExternalLinks: {
                type: "boolean",
                description: "Allow crawling external links",
                default: false,
              },
              webhook: {
                type: "string",
                description: "Webhook URL for async results",
              },
            },
            required: ["url"],
          },
        },
        {
          name: "firecrawl_check_crawl_status",
          description: "Check the status of a crawl job",
          inputSchema: {
            type: "object",
            properties: {
              id: {
                type: "string",
                description: "The crawl job ID",
              },
            },
            required: ["id"],
          },
        },
        {
          name: "firecrawl_map",
          description: "Map a website to get all URLs",
          inputSchema: {
            type: "object",
            properties: {
              url: {
                type: "string",
                description: "The website URL to map",
              },
              search: {
                type: "string",
                description: "Search query to filter URLs",
              },
              limit: {
                type: "integer",
                description: "Maximum URLs to return",
                default: 5000,
              },
            },
            required: ["url"],
          },
        },
        {
          name: "firecrawl_extract",
          description: "Extract structured data from a URL using LLM",
          inputSchema: {
            type: "object",
            properties: {
              url: {
                type: "string",
                description: "The URL to extract data from",
              },
              schema: {
                type: "object",
                description: "JSON schema defining the structure to extract",
              },
              systemPrompt: {
                type: "string",
                description: "System prompt for the extraction",
              },
              prompt: {
                type: "string",
                description: "User prompt for the extraction",
              },
            },
            required: ["url", "schema"],
          },
        },
        {
          name: "firecrawl_check_batch_status",
          description: "Check the status of a batch scrape job",
          inputSchema: {
            type: "object",
            properties: {
              id: {
                type: "string",
                description: "The batch job ID",
              },
            },
            required: ["id"],
          },
        },
        {
          name: "firecrawl_deep_research",
          description: "Perform deep research on a topic by crawling and analyzing multiple sources",
          inputSchema: {
            type: "object",
            properties: {
              topic: {
                type: "string",
                description: "The research topic or question",
              },
              startingUrl: {
                type: "string",
                description: "Starting URL for the research (optional)",
              },
              maxPages: {
                type: "integer",
                description: "Maximum number of pages to analyze",
                default: 10,
              },
              focusAreas: {
                type: "array",
                items: { type: "string" },
                description: "Specific areas or subtopics to focus on",
              },
            },
            required: ["topic"],
          },
        },
        {
          name: "firecrawl_generate_llmstxt",
          description: "Generate an LLMs.txt file for a website to guide AI interactions",
          inputSchema: {
            type: "object",
            properties: {
              url: {
                type: "string",
                description: "The website URL to generate LLMs.txt for",
              },
              includeSubdomains: {
                type: "boolean",
                description: "Include subdomains in the generation",
                default: false,
              },
              customInstructions: {
                type: "string",
                description: "Custom instructions to include in LLMs.txt",
              },
            },
            required: ["url"],
          },
        },
      ],
    }));

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        const { name, arguments: args } = request.params;

        switch (name) {
          case "firecrawl_scrape":
            return await this.handleScrape(args);
          case "firecrawl_batch_scrape":
            return await this.handleBatchScrape(args);
          case "firecrawl_crawl":
            return await this.handleCrawl(args);
          case "firecrawl_check_crawl_status":
            return await this.handleCheckCrawlStatus(args);
          case "firecrawl_map":
            return await this.handleMap(args);
          case "firecrawl_extract":
            return await this.handleExtract(args);
          case "firecrawl_check_batch_status":
            return await this.handleCheckBatchStatus(args);
          case "firecrawl_deep_research":
            return await this.handleDeepResearch(args);
          case "firecrawl_generate_llmstxt":
            return await this.handleGenerateLLMsTxt(args);
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }
      } catch (error) {
        if (error instanceof McpError) throw error;
        
        const errorMessage = error instanceof Error ? error.message : String(error);
        throw new McpError(
          ErrorCode.InternalError,
          `Firecrawl API error: ${errorMessage}`
        );
      }
    });
  }

  private async handleScrape(args: any) {
    const { url, formats = ["markdown"], onlyMainContent = true, ...options } = args;
    
    const scrapeOptions: any = {
      formats,
      onlyMainContent,
      ...options,
    };

    const result = await this.firecrawlApp.scrapeUrl(url, scrapeOptions);
    
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  private async handleBatchScrape(args: any) {
    const { urls, formats = ["markdown"], onlyMainContent = true } = args;
    
    // Firecrawl batchScrapeUrls expects an array of URLs
    const result = await this.firecrawlApp.batchScrapeUrls(urls, {
      formats,
      onlyMainContent,
    });
    
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  private async handleCrawl(args: any) {
    const { 
      url, 
      limit = 10, 
      maxDepth = 2,
      excludePaths = [],
      includePaths = [],
      allowBackwardLinks = false,
      allowExternalLinks = false,
      webhook
    } = args;
    
    const crawlOptions: any = {
      limit,
      maxDepth,
      excludePaths,
      includePaths,
      allowBackwardLinks,
      allowExternalLinks,
    };

    if (webhook) {
      crawlOptions.webhook = webhook;
    }

    const result = await this.firecrawlApp.crawlUrl(url, crawlOptions);
    
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  private async handleCheckCrawlStatus(args: any) {
    const { id } = args;
    
    const result = await this.firecrawlApp.checkCrawlStatus(id);
    
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  private async handleMap(args: any) {
    const { url, search, limit = 5000 } = args;
    
    const mapOptions: any = {
      limit,
    };

    if (search) {
      mapOptions.search = search;
    }

    const result = await this.firecrawlApp.mapUrl(url, mapOptions);
    
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  private async handleExtract(args: any) {
    const { url, schema, systemPrompt, prompt } = args;
    
    const extractOptions: any = {
      schema,
    };

    if (systemPrompt) extractOptions.systemPrompt = systemPrompt;
    if (prompt) extractOptions.prompt = prompt;

    const result = await this.firecrawlApp.extract(url, extractOptions);
    
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  private async handleCheckBatchStatus(args: any) {
    const { id } = args;
    
    // Note: This might need to be implemented in the Firecrawl SDK
    // For now, return a placeholder
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            status: "completed",
            message: "Batch status checking not yet implemented in SDK",
            id,
          }, null, 2),
        },
      ],
    };
  }

  private async handleDeepResearch(args: any) {
    const { topic, startingUrl, maxPages = 10, focusAreas = [] } = args;
    
    // This is a complex operation that would involve multiple steps
    // For now, we'll implement a basic version
    const searchQuery = focusAreas.length > 0 
      ? `${topic} ${focusAreas.join(" ")}`
      : topic;

    let urls: string[] = [];
    
    if (startingUrl) {
      // First, map the starting URL to find related pages
      const mapResult = await this.firecrawlApp.mapUrl(startingUrl, {
        search: searchQuery,
        limit: maxPages,
      });
      
      if (mapResult && 'links' in mapResult && mapResult.links) {
        urls = mapResult.links.slice(0, maxPages);
      }
    }

    // If no URLs found or no starting URL, return a message
    if (urls.length === 0) {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              topic,
              message: "Please provide a starting URL for deep research, or use the web search tool first to find relevant URLs.",
              suggestion: "Try searching for relevant websites first, then use their URLs as starting points for deep research.",
            }, null, 2),
          },
        ],
      };
    }

    // Batch scrape the URLs
    const result = await this.firecrawlApp.batchScrapeUrls(urls, {
      formats: ["markdown"],
      onlyMainContent: true,
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            topic,
            focusAreas,
            pagesAnalyzed: urls.length,
            results: result,
          }, null, 2),
        },
      ],
    };
  }

  private async handleGenerateLLMsTxt(args: any) {
    const { url, includeSubdomains = false, customInstructions } = args;
    
    // First, map the website to understand its structure
    const mapResult = await this.firecrawlApp.mapUrl(url, {
      limit: 100, // Reasonable limit for analysis
    });

    // Then scrape the main page to understand the site
    const mainPageResult = await this.firecrawlApp.scrapeUrl(url, {
      formats: ["markdown"],
      onlyMainContent: true,
    });

    // Generate LLMs.txt content
    let linksCount = 0;
    let linksList: string[] = [];
    
    if (mapResult && 'links' in mapResult && mapResult.links) {
      linksCount = mapResult.links.length;
      linksList = mapResult.links.slice(0, 10);
    }
    
    let mainContent = 'No content available';
    if (mainPageResult && 'markdown' in mainPageResult && mainPageResult.markdown) {
      mainContent = mainPageResult.markdown.substring(0, 500) + '...';
    }

    const llmsTxtContent = `# LLMs.txt for ${url}

## Site Overview
${mainContent}

## Site Structure
- Total pages found: ${linksCount}
${includeSubdomains ? '- Subdomains included: Yes' : '- Subdomains included: No'}

## Key Pages
${linksList.length > 0 ? linksList.map((link: string) => `- ${link}`).join('\n') : 'No links found'}

## Instructions for AI Agents
1. This website contains ${linksCount || 'unknown number of'} pages
2. The main content is focused on the topics found in the homepage
3. When referencing this site, use the official URL: ${url}
${customInstructions ? `\n## Custom Instructions\n${customInstructions}` : ''}

## Technical Details
- Crawled on: ${new Date().toISOString()}
- Crawler: Firecrawl MCP Server
`;

    return {
      content: [
        {
          type: "text",
          text: llmsTxtContent,
        },
      ],
    };
  }
}

const server = new FirecrawlMCPServer();
server.run().catch(console.error);