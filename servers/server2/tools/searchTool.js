import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';
import { BaseTool } from './baseTool.js';
import axios from 'axios';

const SearchSchema = z.object({
    query: z.string().describe('Search query to execute'),
    num: z
        .number()
        .int()
        .min(1)
        .max(10)
        .default(5)
        .describe('Number of results to return (1-10)'),
});

const ToolDefinition = {
    name: 'google-search',
    description: `
    🎯 Purpose:
      1. Performs web searches using Google Custom Search API.
      2. Returns relevant search results with titles, links, and snippets.

    🧭 Usage Guidance:
      1. Use for finding current information on the web.
      2. Ideal for research, fact-checking, and gathering recent data.
      3. Combine with read-webpage tool to get full content from search results.

    📋 Prerequisites:
      1. GOOGLE_API_KEY must be set in environment variables.
      2. GOOGLE_SEARCH_ENGINE_ID must be configured.
  `,
    inputSchema: zodToJsonSchema(SearchSchema),
    annotations: {
        title: 'Google Web Search',
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: false,
        openWorldHint: true,
    },
};

export class SearchTool extends BaseTool {
    apiKey;
    searchEngineId;
    axiosInstance;

    constructor() {
        super(SearchSchema, ToolDefinition);
        
        this.apiKey = process.env.GOOGLE_API_KEY;
        this.searchEngineId = process.env.GOOGLE_SEARCH_ENGINE_ID;
        
        if (!this.apiKey) {
            throw new Error('GOOGLE_API_KEY environment variable is required');
        }
        
        if (!this.searchEngineId) {
            throw new Error('GOOGLE_SEARCH_ENGINE_ID environment variable is required');
        }

        this.axiosInstance = axios.create({
            baseURL: 'https://www.googleapis.com/customsearch/v1',
            params: {
                key: this.apiKey,
                cx: this.searchEngineId,
            },
        });
    }

    async process(args) {
        try {
            const { query, num } = args;

            const response = await this.axiosInstance.get('', {
                params: {
                    q: query,
                    num: Math.min(num, 10),
                },
            });

            if (!response.data.items) {
                return {
                    content: [
                        {
                            type: 'text',
                            text: JSON.stringify({
                                query: query,
                                results: [],
                                message: 'No search results found'
                            }, null, 2),
                        },
                    ],
                };
            }

            const results = response.data.items.map((item) => ({
                title: item.title,
                link: item.link,
                snippet: item.snippet,
            }));

            return {
                content: [
                    {
                        type: 'text',
                        text: JSON.stringify({
                            query: query,
                            results: results,
                            totalResults: response.data.searchInformation?.totalResults || '0',
                        }, null, 2),
                    },
                ],
            };
        } catch (error) {
            if (axios.isAxiosError(error)) {
                return {
                    content: [
                        {
                            type: 'text',
                            text: `Search API error: ${
                                error.response?.data?.error?.message ?? error.message
                            }`,
                        },
                    ],
                    isError: true,
                };
            }
            
            return {
                content: [
                    {
                        type: 'text',
                        text: `Error performing search: ${error instanceof Error ? error.message : String(error)}`,
                    },
                ],
                isError: true,
            };
        }
    }
}