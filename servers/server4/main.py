import json
import logging
import re
import os
from typing import Any, Literal, Optional
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.routing import Route, Mount

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

# Set up minimal logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("mcp_neo4j_cypher")

# Get Neo4j connection details from environment
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

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

# Initialize Neo4j driver
neo4j_driver = AsyncGraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
)

# Initialize the MCP server
mcp = FastMCP("Neo4j Cypher MCP", host="0.0.0.0", port=8003)

# Initialize SSE transport
transport = SseServerTransport("/messages/")

@mcp.tool()
async def get_neo4j_schema() -> list[types.TextContent]:
    """List all node, their attributes and their relationships to other nodes in the neo4j database.
    If this fails with a message that includes "Neo.ClientError.Procedure.ProcedureNotFound"
    suggest that the user install and enable the APOC plugin.
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
        async with neo4j_driver.session(database=NEO4J_DATABASE) as session:
            results_json_str = await session.execute_read(
                _read, get_schema_query, dict()
            )
            return [types.TextContent(type="text", text=results_json_str)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]

@mcp.tool()
async def read_neo4j_cypher(
    query: str = Field(..., description="The Cypher query to execute."),
    params: Optional[dict[str, Any]] = Field(
        None, description="The parameters to pass to the Cypher query."
    ),
) -> list[types.TextContent]:
    """Execute a read Cypher query on the neo4j database."""
    if _is_write_query(query):
        raise ValueError("Only MATCH queries are allowed for read-query")

    try:
        async with neo4j_driver.session(database=NEO4J_DATABASE) as session:
            results_json_str = await session.execute_read(_read, query, params)
            return [types.TextContent(type="text", text=results_json_str)]
    except Exception as e:
        return [
            types.TextContent(type="text", text=f"Error: {e}\n{query}\n{params}")
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
        async with neo4j_driver.session(database=NEO4J_DATABASE) as session:
            raw_results = await session.execute_write(_write, query, params)
            counters_json_str = json.dumps(
                raw_results._summary.counters.__dict__, default=str
            )
        return [types.TextContent(type="text", text=counters_json_str)]
    except Exception as e:
        return [
            types.TextContent(type="text", text=f"Error: {e}\n{query}\n{params}")
        ]

async def handle_sse(request):
    """Handle SSE connections for MCP"""
    async with transport.connect_sse(request.scope, request.receive, request._send) as (
        in_stream,
        out_stream,
    ):
        await mcp._mcp_server.run(
            in_stream, out_stream, mcp._mcp_server.create_initialization_options()
        )

# Build a Starlette app for the MCP endpoints
sse_app = Starlette(
    routes=[
        Route("/sse", handle_sse, methods=["GET"]),
        Mount("/messages/", app=transport.handle_post_message),
    ]
)

# Create FastAPI app and mount the SSE app
app = FastAPI()
app.mount("/", sse_app)

@app.get("/health")
def health_check():
    return {"message": "Neo4j MCP Server is running", "database": NEO4J_DATABASE}

if __name__ == "__main__":
    import uvicorn
    print("Starting Neo4j MCP server on port 8003...")
    print(f"Connect to this server using http://localhost:8003/sse")
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="warning")