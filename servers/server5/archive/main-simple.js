#!/usr/bin/env node
import dotenv from 'dotenv';
dotenv.config();

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SseServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { 
    CallToolRequestSchema, 
    GetPromptRequestSchema, 
    ListPromptsRequestSchema, 
    ListToolsRequestSchema 
} from '@modelcontextprotocol/sdk/types.js';
import http from 'http';
import url from 'url';

// Import HubSpot tools and prompts
import { getTools, handleToolCall } from './tools/index.js';
import { getPrompts, getPromptMessages } from './prompts/index.js';

// Import tool and prompt registries to auto-register everything
import './tools/toolsRegistry.js';
import './prompts/promptsRegistry.js';

const APP_NAME = 'hubspot-mcp-sse-server';
const APP_VERSION = '1.0.0';
const PORT = parseInt(process.env.PORT || '8004');
const HOST = process.env.HOST || '0.0.0.0';

// Create MCP server
const server = new Server({
    name: APP_NAME,
    version: APP_VERSION,
}, {
    capabilities: {
        tools: {},
        prompts: {},
        resources: {},
    },
});

// Handler for listing tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: getTools(),
    };
});

// Handler for calling tools
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    return handleToolCall(name, args);
});

// Handler for listing prompts
server.setRequestHandler(ListPromptsRequestSchema, async () => {
    return {
        prompts: getPrompts(),
    };
});

// Handler for getting specific prompt
server.setRequestHandler(GetPromptRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    return getPromptMessages(name, args);
});

// Create HTTP server
const httpServer = http.createServer(async (req, res) => {
    const parsedUrl = url.parse(req.url, true);
    
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
    
    if (parsedUrl.pathname === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status: 'healthy',
            server: APP_NAME,
            version: APP_VERSION,
            timestamp: new Date().toISOString()
        }));
        return;
    }
    
    if (parsedUrl.pathname === '/sse') {
        if (req.method === 'GET') {
            // Handle SSE connection
            console.error('SSE connection request received');
            
            res.writeHead(200, {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control',
            });
            
            try {
                // Create SSE transport
                const transport = new SseServerTransport('/sse', res);
                
                // Connect the MCP server
                await server.connect(transport);
                
                console.error('MCP server connected via SSE');
                
                req.on('close', () => {
                    console.error('SSE connection closed');
                });
                
                req.on('error', (err) => {
                    console.error('SSE connection error:', err);
                });
                
            } catch (error) {
                console.error('Error setting up SSE connection:', error);
                res.writeHead(500, { 'Content-Type': 'text/plain' });
                res.end('Internal Server Error');
            }
            
        } else if (req.method === 'POST') {
            // Handle POST messages
            let body = '';
            req.on('data', chunk => {
                body += chunk.toString();
            });
            
            req.on('end', async () => {
                try {
                    const message = JSON.parse(body);
                    let response;
                    
                    switch (message.method) {
                        case 'tools/list':
                            response = {
                                jsonrpc: "2.0",
                                id: message.id,
                                result: { tools: getTools() }
                            };
                            break;
                            
                        case 'tools/call':
                            const toolResult = await handleToolCall(message.params.name, message.params.arguments);
                            response = {
                                jsonrpc: "2.0",
                                id: message.id,
                                result: toolResult
                            };
                            break;
                            
                        case 'prompts/list':
                            response = {
                                jsonrpc: "2.0",
                                id: message.id,
                                result: { prompts: getPrompts() }
                            };
                            break;
                            
                        case 'prompts/get':
                            try {
                                const promptResult = getPromptMessages(message.params.name, message.params.arguments);
                                response = {
                                    jsonrpc: "2.0",
                                    id: message.id,
                                    result: promptResult
                                };
                            } catch (error) {
                                response = {
                                    jsonrpc: "2.0",
                                    id: message.id,
                                    error: {
                                        code: -32603,
                                        message: error.message
                                    }
                                };
                            }
                            break;
                            
                        case 'initialize':
                            response = {
                                jsonrpc: "2.0",
                                id: message.id,
                                result: {
                                    protocolVersion: "2024-11-05",
                                    capabilities: {
                                        tools: {},
                                        prompts: {},
                                        resources: {}
                                    },
                                    serverInfo: {
                                        name: APP_NAME,
                                        version: APP_VERSION
                                    }
                                }
                            };
                            break;
                            
                        default:
                            response = {
                                jsonrpc: "2.0",
                                id: message.id,
                                error: {
                                    code: -32601,
                                    message: `Method not found: ${message.method}`
                                }
                            };
                    }
                    
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify(response));
                    
                } catch (error) {
                    console.error('Error handling POST message:', error);
                    const errorResponse = {
                        jsonrpc: "2.0",
                        id: null,
                        error: {
                            code: -32603,
                            message: "Internal error",
                            data: error.message
                        }
                    };
                    res.writeHead(500, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify(errorResponse));
                }
            });
        }
        return;
    }
    
    // 404 for other paths
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
});

// Start the server
async function main() {
    try {
        console.error(`Starting ${APP_NAME} v${APP_VERSION}...`);
        
        // Verify HubSpot access token
        if (!process.env.PRIVATE_APP_ACCESS_TOKEN) {
            console.error('Warning: PRIVATE_APP_ACCESS_TOKEN not found in environment variables');
        } else {
            console.error('HubSpot access token found');
        }
        
        httpServer.listen(PORT, HOST, () => {
            console.error(`HubSpot MCP SSE Server running on http://${HOST}:${PORT}`);
            console.error(`SSE endpoint: http://${HOST}:${PORT}/sse`);
            console.error(`Health check: http://${HOST}:${PORT}/health`);
        });
        
    } catch (error) {
        console.error('Error starting server:', error);
        process.exit(1);
    }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
    console.error('Shutting down server...');
    try {
        await server.close();
        httpServer.close();
        process.exit(0);
    } catch (error) {
        console.error('Error during shutdown:', error);
        process.exit(1);
    }
});

process.on('SIGTERM', async () => {
    console.error('Received SIGTERM, shutting down...');
    try {
        await server.close();
        httpServer.close();
        process.exit(0);
    } catch (error) {
        console.error('Error during shutdown:', error);
        process.exit(1);
    }
});

// Start the server
main();