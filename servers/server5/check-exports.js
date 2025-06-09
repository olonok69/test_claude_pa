#!/usr/bin/env node

// Check what exports are available in the MCP SDK
console.log('Checking MCP SDK exports...');

try {
    console.log('\n=== @modelcontextprotocol/sdk/server/index.js ===');
    const serverIndex = await import('@modelcontextprotocol/sdk/server/index.js');
    console.log('Available exports:', Object.keys(serverIndex));
    
    console.log('\n=== @modelcontextprotocol/sdk/types.js ===');
    const types = await import('@modelcontextprotocol/sdk/types.js');
    console.log('Available exports:', Object.keys(types));
    
    // Try to check if SSE transport exists in different locations
    try {
        console.log('\n=== Trying @modelcontextprotocol/sdk/server/sse.js ===');
        const sse = await import('@modelcontextprotocol/sdk/server/sse.js');
        console.log('SSE exports:', Object.keys(sse));
    } catch (e) {
        console.log('SSE module not found or has no exports:', e.message);
    }
    
    // Try alternative locations
    try {
        console.log('\n=== Trying @modelcontextprotocol/sdk/transport/sse.js ===');
        const sseTransport = await import('@modelcontextprotocol/sdk/transport/sse.js');
        console.log('SSE transport exports:', Object.keys(sseTransport));
    } catch (e) {
        console.log('SSE transport module not found:', e.message);
    }
    
    // Check the main SDK
    try {
        console.log('\n=== Trying @modelcontextprotocol/sdk ===');
        const sdk = await import('@modelcontextprotocol/sdk');
        console.log('Main SDK exports:', Object.keys(sdk));
    } catch (e) {
        console.log('Main SDK not accessible:', e.message);
    }
    
} catch (error) {
    console.error('Error checking exports:', error);
}

console.log('\nExport check completed.');