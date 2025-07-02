import json
import logging
import re
import os
import asyncio
from typing import Any, Literal, Optional
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from neo4j import (
    AsyncDriver,
    AsyncGraphDatabase,
    AsyncResult,
    AsyncTransaction,
)
from neo4j.exceptions import DatabaseError
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up proper logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("mcp_neo4j_cypher")

# Get Neo4j connection details from environment
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# Global driver instance
neo4j_driver: Optional[AsyncDriver] = None

async def get_neo4j_driver() -> AsyncDriver:
    """Get or create Neo4j driver instance."""
    global neo4j_driver
    if neo4j_driver is None:
        neo4j_driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
        )
    return neo4j_driver

async def close_neo4j_driver():
    """Close Neo4j driver."""
    global neo4j_driver
    if neo4j_driver is not None:
        await neo4j_driver.close()
        neo4j_driver = None

async def _read(tx: AsyncTransaction, query: str, params: dict[str, Any]) -> str:
    raw_results = await tx.run(query, params)
    eager_results = await raw_results.to_eager_result()
    return json.dumps([r.data() for r in eager_results.records], default=str)

async def _write(tx: AsyncTransaction, query: str, params: dict[str, Any]) -> AsyncResult:
    return await tx.run(query, params)

def _is_write_query(query: str) -> bool:
    """Check if the query is a write query."""
    return (
        re.search(r"\b(MERGE|CREATE|SET|DELETE|REMOVE|ADD)\b", query, re.IGNORECASE)
        is not None
    )

def validate_query_against_schema(query: str, schema_data: str) -> tuple[bool, str]:
    """Validate that a Cypher query uses only labels and properties from the schema."""
    try:
        schema = json.loads(schema_data)
        if not schema:
            return False, "Database schema is empty. No data structure available."
        
        # Extract node labels from schema
        valid_labels = set()
        valid_properties = set()
        
        for item in schema:
            if 'label' in item:
                valid_labels.add(item['label'])
                if 'attributes' in item and isinstance(item['attributes'], dict):
                    valid_properties.update(item['attributes'].keys())
        
        # Extract labels used in query (basic pattern matching)
        query_labels = re.findall(r':\s*(\w+)', query)
        query_properties = re.findall(r'\.(\w+)', query)
        
        # Check for invalid labels
        invalid_labels = [label for label in query_labels if label not in valid_labels and label != '*']
        if invalid_labels:
            return False, f"Invalid node labels in query: {invalid_labels}. Available labels: {list(valid_labels)}"
        
        # Check for invalid properties
        invalid_props = [prop for prop in query_properties if prop not in valid_properties]
        if invalid_props:
            return False, f"Invalid properties in query: {invalid_props}. Available properties: {list(valid_properties)}"
        
        return True, "Query validation passed"
        
    except Exception as e:
        return False, f"Schema validation error: {str(e)}"

async def validate_neo4j_connection():
    """Validate Neo4j connection and log status."""
    try:
        driver = await get_neo4j_driver()
        async with driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run("RETURN 1 as test")
            await result.consume()
            logger.info("✓ Neo4j connection successful")
            return True
    except Exception as e:
        logger.error(f"✗ Neo4j connection failed: {str(e)}")
        logger.error(f"Check Neo4j connection details:")
        logger.error(f"  URI: {NEO4J_URI}")
        logger.error(f"  Username: {NEO4J_USERNAME}")
        logger.error(f"  Database: {NEO4J_DATABASE}")
        return False

# Initialize the MCP server
mcp = FastMCP("Neo4j Cypher MCP", host="0.0.0.0", port=8003)

# Initialize SSE transport
transport = SseServerTransport("/messages/")

@mcp.tool()
async def get_neo4j_schema() -> list[types.TextContent]:
    """**REQUIRED FIRST STEP**: Get the complete Neo4j database schema including all node labels, 
    properties, and relationships. This tool MUST be called before any other Neo4j operations 
    to understand the database structure and avoid query errors.
    
    Returns a JSON structure with:
    - label: Node type name
    - attributes: Properties and their types
    - relationships: Connected node types
    
    If this fails with "Neo.ClientError.Procedure.ProcedureNotFound", the APOC plugin needs 
    to be installed and enabled in Neo4j.
    """
    get_schema_query = """
call apoc.meta.data() yield label, property, type, other, unique, index, elementType
where elementType = 'node' and not label starts with '_'
with label, 
    collect(case when type <> 'RELATIONSHIP' then [property, type + case when unique then " unique" else "" end + case when index then " indexed" else "" end] end) as attributes,
    collect(case when type = 'RELATIONSHIP' then [property, head(other)] end) as relationships
RETURN label, apoc.map.fromPairs(attributes) as attributes, apoc.map.fromPairs(relationships) as relationships
"""

    try:
        driver = await get_neo4j_driver()
        async with driver.session(database=NEO4J_DATABASE) as session:
            results_json_str = await session.execute_read(
                _read, get_schema_query, {}
            )
            return [types.TextContent(type="text", text=results_json_str)]
    except Exception as e:
        error_msg = f"Error getting Neo4j schema: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

@mcp.tool()
async def read_neo4j_cypher(
    query: str = Field(..., description="The Cypher query to execute."),
    params: Optional[dict[str, Any]] = Field(
        None, description="The parameters to pass to the Cypher query."
    ),
) -> list[types.TextContent]:
    """Execute a read Cypher query on the neo4j database.
    
    IMPORTANT: Always call get_neo4j_schema first to understand the database structure.
    Only use node labels and properties that exist in the schema.
    """
    if _is_write_query(query):
        raise ValueError("Only MATCH queries are allowed for read-query")

    try:
        driver = await get_neo4j_driver()
        async with driver.session(database=NEO4J_DATABASE) as session:
            results_json_str = await session.execute_read(_read, query, params or {})
            return [types.TextContent(type="text", text=results_json_str)]
    except Exception as e:
        error_msg = f"Error executing Neo4j query: {str(e)}\n\nQuery: {query}\nParams: {params}\n\nTip: Make sure to call get_neo4j_schema first to understand available labels and properties."
        logger.error(error_msg)
        return [
            types.TextContent(type="text", text=error_msg)
        ]

@mcp.tool()
async def write_neo4j_cypher(
    query: str = Field(..., description="The Cypher query to execute."),
    params: Optional[dict[str, Any]] = Field(
        None, description="The parameters to pass to the Cypher query."
    ),
) -> list[types.TextContent]:
    """Execute a write Cypher query on the neo4j database."""
    if not _is_write_query(query):
        raise ValueError("Only write queries are allowed for write-query")

    try:
        driver = await get_neo4j_driver()
        async with driver.session(database=NEO4J_DATABASE) as session:
            raw_results = await session.execute_write(_write, query, params or {})
            counters_json_str = json.dumps(
                raw_results._summary.counters.__dict__, default=str
            )
        return [types.TextContent(type="text", text=counters_json_str)]
    except Exception as e:
        error_msg = f"Error executing Neo4j write query: {str(e)}\n\nQuery: {query}\nParams: {params}"
        logger.error(error_msg)
        return [
            types.TextContent(type="text", text=error_msg)
        ]

async def health_check(request):
    """Health check endpoint that also verifies Neo4j connection."""
    try:
        connection_ok = await validate_neo4j_connection()
        if connection_ok:
            return JSONResponse({
                "message": "Neo4j MCP Server is running", 
                "database": NEO4J_DATABASE,
                "neo4j_connection": "healthy"
            })
        else:
            return JSONResponse({
                "message": "Neo4j MCP Server is running", 
                "database": NEO4J_DATABASE,
                "neo4j_connection": "error",
                "error": "Failed to connect to Neo4j"
            })
    except Exception as e:
        return JSONResponse({
            "message": "Neo4j MCP Server is running", 
            "database": NEO4J_DATABASE,
            "neo4j_connection": "error",
            "error": str(e)
        })

async def handle_sse(request):
    """Handle SSE connections for MCP"""
    async with transport.connect_sse(request.scope, request.receive, request._send) as (
        in_stream,
        out_stream,
    ):
        await mcp._mcp_server.run(
            in_stream, out_stream, mcp._mcp_server.create_initialization_options()
        )

# Build a complete Starlette app with all routes
app = Starlette(
    routes=[
        Route("/health", health_check, methods=["GET"]),
        Route("/sse", handle_sse, methods=["GET"]),
        Mount("/messages/", app=transport.handle_post_message),
    ]
)

if __name__ == "__main__":
    import uvicorn
    
    # Log startup information
    logger.info("Starting Neo4j MCP Cypher Server v1.0.0...")
    logger.info(f"Neo4j URI: {NEO4J_URI}")
    logger.info(f"Neo4j Database: {NEO4J_DATABASE}")
    logger.info(f"Neo4j Username: {NEO4J_USERNAME}")
    logger.info("Neo4j MCP Server running on http://0.0.0.0:8003")
    logger.info("SSE endpoint: http://0.0.0.0:8003/sse")
    logger.info("Health check: http://0.0.0.0:8003/health")
    
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")