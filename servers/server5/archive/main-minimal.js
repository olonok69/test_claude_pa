#!/usr/bin/env node

console.log('Starting minimal server...');

// Test basic imports
try {
    console.log('Importing dotenv...');
    const dotenv = await import('dotenv');
    console.log('✓ dotenv imported');
    
    dotenv.default.config();
    console.log('✓ dotenv configured');
    
    console.log('Importing fastify...');
    const Fastify = await import('fastify');
    console.log('✓ fastify imported');
    
    const fastify = Fastify.default({
        logger: true
    });
    
    fastify.get('/health', async (request, reply) => {
        return { status: 'ok', timestamp: new Date().toISOString() };
    });
    
    const PORT = 8004;
    const HOST = '0.0.0.0';
    
    await fastify.listen({ port: PORT, host: HOST });
    console.log(`Server running on http://${HOST}:${PORT}`);
    
} catch (error) {
    console.error('Error:', error);
    process.exit(1);
}