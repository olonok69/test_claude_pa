import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';
import { BaseTool } from './baseTool.js';
import axios from 'axios';
import * as cheerio from 'cheerio';

const ReadWebpageSchema = z.object({
    url: z.string().url().describe('URL of the webpage to read and extract content from'),
});

const ToolDefinition = {
    name: 'read-webpage',
    description: `
    🎯 Purpose:
      1. Fetches and extracts text content from web pages.
      2. Removes scripts, styles, and other non-content elements.
      3. Returns clean, readable text content with title and URL.

    🧭 Usage Guidance:
      1. Use after google-search to get full content from interesting results.
      2. Ideal for reading articles, blog posts, and documentation.
      3. Automatically handles basic HTML parsing and cleanup.

    📦 Returns:
      1. Page title, clean text content, and source URL.
      2. Content is processed to remove formatting and focus on readable text.
  `,
    inputSchema: zodToJsonSchema(ReadWebpageSchema),
    annotations: {
        title: 'Read Webpage Content',
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true,
    },
};

export class ReadWebpageTool extends BaseTool {
    constructor() {
        super(ReadWebpageSchema, ToolDefinition);
    }

    async process(args) {
        try {
            const { url } = args;

            const response = await axios.get(url, {
                timeout: 10000,
                headers: {
                    'User-Agent': 'Mozilla/5.0 (compatible; Google Search MCP Server/1.0)',
                },
            });

            const $ = cheerio.load(response.data);

            // Remove script and style elements
            $('script, style, nav, header, footer, aside, .advertisement, .ads').remove();

            const content = {
                title: $('title').text().trim() || 'No title found',
                text: $('body').text().trim().replace(/\s+/g, ' '),
                url: url,
                contentLength: $('body').text().trim().length,
            };

            // Limit content length to prevent token overflow
            if (content.text.length > 10000) {
                content.text = content.text.substring(0, 10000) + '... [Content truncated]';
                content.truncated = true;
            }

            return {
                content: [
                    {
                        type: 'text',
                        text: JSON.stringify(content, null, 2),
                    },
                ],
            };
        } catch (error) {
            if (axios.isAxiosError(error)) {
                return {
                    content: [
                        {
                            type: 'text',
                            text: `Webpage fetch error: ${error.message}. Status: ${error.response?.status || 'Unknown'}`,
                        },
                    ],
                    isError: true,
                };
            }
            
            return {
                content: [
                    {
                        type: 'text',
                        text: `Error reading webpage: ${error instanceof Error ? error.message : String(error)}`,
                    },
                ],
                isError: true,
            };
        }
    }
}