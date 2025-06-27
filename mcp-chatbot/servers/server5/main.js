#!/usr/bin/env node
import dotenv from 'dotenv';
dotenv.config();

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { 
    CallToolRequestSchema, 
    GetPromptRequestSchema, 
    ListPromptsRequestSchema, 
    ListToolsRequestSchema 
} from '@modelcontextprotocol/sdk/types.js';
import express from 'express';

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

// To support multiple simultaneous connections we have a lookup object from
// sessionId to transport
const transports = {};

const app = express();
app.use(express.json());

// CORS middleware
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    if (req.method === 'OPTIONS') {
        res.sendStatus(200);
        return;
    }
    next();
});

const router = express.Router();

// Endpoint for the client to use for sending messages
const POST_ENDPOINT = "/messages";

router.post(POST_ENDPOINT, async (req, res) => {
    const sessionId = req.query.sessionId;
    if (typeof (sessionId) != "string") {
        res.status(400).send({ message: "Bad session id." });
        return;
    }
    
    const transport = transports[sessionId];
    if (!transport) {
        res.status(400).send({ message: "No transport found for sessionId." });
        return;
    }
    
    // IMPORTANT! Use the three-parameter version to avoid stream errors
    await transport.handlePostMessage(req, res, req.body);
    return;
});

// SSE endpoint - this is what the client connects to first
router.get("/sse", async (req, res) => {
    try {
        // Create a new transport to connect and send an endpoint event
        // containing a URI for the client to use for sending messages
        const transport = new SSEServerTransport(POST_ENDPOINT, res);
        
        // Store the transport for message routing
        transports[transport.sessionId] = transport;
        
        // Clean up when connection closes
        res.on("close", () => {
            delete transports[transport.sessionId];
        });
        
        res.on("error", (err) => {
            console.error("SSE connection error:", err);
            delete transports[transport.sessionId];
        });
        
        // Connect the MCP server to this transport
        await server.connect(transport);
        
        return;
    } catch (error) {
        console.error("Error setting up SSE connection:", error);
        res.status(500).send("Internal Server Error");
    }
});

// Health check endpoint
router.get("/health", (req, res) => {
    res.json({
        status: 'healthy',
        server: APP_NAME,
        version: APP_VERSION,
        timestamp: new Date().toISOString(),
        activeConnections: Object.keys(transports).length
    });
});

app.use('/', router);

// Start the server
async function main() {
    try {
        console.log(`Starting ${APP_NAME} v${APP_VERSION}...`);
        
        // Verify HubSpot access token
        if (!process.env.PRIVATE_APP_ACCESS_TOKEN) {
            console.warn('Warning: PRIVATE_APP_ACCESS_TOKEN not found in environment variables');
        }
        
        app.listen(PORT, HOST, () => {
            console.log(`HubSpot MCP Server running on http://${HOST}:${PORT}`);
            console.log(`Health check: http://${HOST}:${PORT}/health`);
        });
        
    } catch (error) {
        console.error('Error starting server:', error);
        process.exit(1);
    }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
    console.log('Shutting down server...');
    try {
        // Close all active transports
        for (const [sessionId, transport] of Object.entries(transports)) {
            try {
                await transport.close();
            } catch (error) {
                console.error(`Error closing transport ${sessionId}:`, error);
            }
        }
        await server.close();
        process.exit(0);
    } catch (error) {
        console.error('Error during shutdown:', error);
        process.exit(1);
    }
});

process.on('SIGTERM', async () => {
    console.log('Received SIGTERM, shutting down...');
    try {
        for (const [sessionId, transport] of Object.entries(transports)) {
            try {
                await transport.close();
            } catch (error) {
                console.error(`Error closing transport ${sessionId}:`, error);
            }
        }
        await server.close();
        process.exit(0);
    } catch (error) {
        console.error('Error during shutdown:', error);
        process.exit(1);
    }
});

// Start the server
main();