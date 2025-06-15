#!/usr/bin/env node

// Test if dependencies can be imported
console.log('Testing dependency imports...');

try {
    console.log('Testing dotenv...');
    await import('dotenv');
    console.log('✓ dotenv imported successfully');
} catch (error) {
    console.error('✗ Failed to import dotenv:', error.message);
}

try {
    console.log('Testing @modelcontextprotocol/sdk...');
    await import('@modelcontextprotocol/sdk/server/index.js');
    console.log('✓ MCP SDK imported successfully');
} catch (error) {
    console.error('✗ Failed to import MCP SDK:', error.message);
}

try {
    console.log('Testing fastify...');
    await import('fastify');
    console.log('✓ Fastify imported successfully');
} catch (error) {
    console.error('✗ Failed to import Fastify:', error.message);
}

try {
    console.log('Testing zod...');
    await import('zod');
    console.log('✓ Zod imported successfully');
} catch (error) {
    console.error('✗ Failed to import Zod:', error.message);
}

console.log('Dependency test completed.');
process.exit(0);