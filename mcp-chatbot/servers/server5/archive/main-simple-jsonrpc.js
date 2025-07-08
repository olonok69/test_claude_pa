#!/usr/bin/env node
import dotenv from 'dotenv';
dotenv.config();

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

// Store active SSE connections
const activeConnections = new Set();

// Helper function to send JSON-RPC message via SSE
function sendSSEMessage(res, message) {
    if (!res.destroyed) {
        try {
            const jsonData = JSON.stringify(message);
            res.write(`data: ${jsonData}\n\n`);
        } catch (error) {
            console.error('Error sending SSE message:', error);
        }
    }
}

// Handle JSON-RPC requests
async function handleJSONRPCRequest(message) {
    try {
        console.error(`Handling JSON-RPC method: ${message.method}, id: ${message.id}`);
        
        switch (message.method) {
            case 'initialize':
                const initResult = {
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
                console.error('Sending initialize response:', JSON.stringify(initResult, null, 2));
                return initResult;
                
            case 'initialized':
                // This is a notification, no response needed
                console.error('Received initialized notification');
                return null;
                
            case 'tools/list':
                const toolsResult = {
                    jsonrpc: "2.0",
                    id: message.id,
                    result: { tools: getTools() }
                };
                console.error(`Returning ${getTools().length} tools`);
                return toolsResult;
                
            case 'tools/call':
                console.error(`Calling tool: ${message.params.name}`);
                const toolResult = await handleToolCall(message.params.name, message.params.arguments);
                return {
                    jsonrpc: "2.0",
                    id: message.id,
                    result: toolResult
                };
                
            case 'prompts/list':
                return {
                    jsonrpc: "2.0",
                    id: message.id,
                    result: { prompts: getPrompts() }
                };
                
            case 'prompts/get':
                try {
                    const promptResult = getPromptMessages(message.params.name, message.params.arguments);
                    return {
                        jsonrpc: "2.0",
                        id: message.id,
                        result: promptResult
                    };
                } catch (error) {
                    return {
                        jsonrpc: "2.0",
                        id: message.id,
                        error: {
                            code: -32603,
                            message: error.message
                        }
                    };
                }
                
            default:
                console.error(`Unknown method: ${message.method}`);
                return {
                    jsonrpc: "2.0",
                    id: message.id,
                    error: {
                        code: -32601,
                        message: `Method not found: ${message.method}`
                    }
                };
        }
    } catch (error) {
        console.error('Error in JSON-RPC handler:', error);
        return {
            jsonrpc: "2.0",
            id: message.id || null,
            error: {
                code: -32603,
                message: "Internal error",
                data: error.message
            }
        };
    }
}

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
            
            // Set SSE headers
            res.writeHead(200, {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control',
                'X-Accel-Buffering': 'no'
            });
            
            // Add to active connections
            activeConnections.add(res);
            
            console.error('SSE connection established');
            
            // Keep connection alive with comments (not data messages)
            const pingInterval = setInterval(() => {
                if (!res.destroyed) {
                    res.write(': keepalive\n\n');
                } else {
                    clearInterval(pingInterval);
                }
            }, 30000);
            
            req.on('close', () => {
                console.error('SSE connection closed');
                activeConnections.delete(res);
                clearInterval(pingInterval);
            });
            
            req.on('error', (err) => {
                console.error('SSE connection error:', err);
                activeConnections.delete(res);
                clearInterval(pingInterval);
            });
            
        } else if (req.method === 'POST') {
            // Handle POST messages for MCP communication
            let body = '';
            req.on('data', chunk => {
                body += chunk.toString();
            });
            
            req.on('end', async () => {
                try {
                    console.error('Received POST body:', body);
                    const message = JSON.parse(body);
                    console.error('Parsed JSON-RPC message:', JSON.stringify(message, null, 2));
                    
                    const response = await handleJSONRPCRequest(message);
                    
                    if (response) {
                        console.error('Sending response:', JSON.stringify(response, null, 2));
                        res.writeHead(200, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify(response));
                    } else {
                        // For notifications, return 204 No Content
                        console.error('No response needed (notification)');
                        res.writeHead(204);
                        res.end();
                    }
                    
                } catch (error) {
                    console.error('Error handling POST message:', error);
                    console.error('Raw body was:', body);
                    const errorResponse = {
                        jsonrpc: "2.0",
                        id: null,
                        error: {
                            code: -32700,
                            message: "Parse error",
                            data: error.message
                        }
                    };
                    res.writeHead(400, { 'Content-Type': 'application/json' });
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
        // Close all active connections
        for (const connection of activeConnections) {
            if (!connection.destroyed) {
                connection.end();
            }
        }
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
        for (const connection of activeConnections) {
            if (!connection.destroyed) {
                connection.end();
            }
        }
        httpServer.close();
        process.exit(0);
    } catch (error) {
        console.error('Error during shutdown:', error);
        process.exit(1);
    }
});

// Start the server
main();