import os
import json
import logging
from typing import Optional
from dotenv import load_dotenv
from pyodbc import connect, Error

from mcp.types import TextContent
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from fastapi import FastAPI

# Load environment variables
load_dotenv("mcp-chatbot/servers/server_mssql/mssql_mcp_server/.env4test")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mssql_mcp_server")

# Create MCP server and transport
mcp = FastMCP("MSSQL MCP Server", host="0.0.0.0", port=8008)
transport = SseServerTransport("/messages/")

def get_db_config():
    config = {
        "driver": os.getenv("MSSQL_DRIVER", "SQL Server"),
        "server": os.getenv("MSSQL_HOST", "localhost"),
        "user": os.getenv("MSSQL_USER"),
        "password": os.getenv("MSSQL_PASSWORD"),
        "database": os.getenv("MSSQL_DATABASE"),
        "trusted_server_certificate": os.getenv("TrustServerCertificate", "yes"),
        "trusted_connection": os.getenv("Trusted_Connection", "no")
    }
    if not all([config["user"], config["password"], config["database"]]):
        logger.error("Missing required database configuration.")
        raise ValueError("Missing required database configuration")

    connection_string = (
        f"Driver={config['driver']};Server={config['server']};"
        f"UID={config['user']};PWD={config['password']};"
        f"Database={config['database']};"
        f"TrustServerCertificate={config['trusted_server_certificate']};"
        f"Trusted_Connection={config['trusted_connection']};"
    )

    return config, connection_string

@mcp.tool()
async def list_tables() -> list[TextContent]:
    config, connection_string = get_db_config()
    try:
        with connect(connection_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';")
                tables = [table[0] for table in cursor.fetchall()]
                return [TextContent(type="text", text=json.dumps(tables))]
    except Error as e:
        logger.error(f"Failed to list tables: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

@mcp.tool()
async def execute_sql(query: str) -> list[TextContent]:
    config, connection_string = get_db_config()
    try:
        with connect(connection_string) as conn:
            with conn.cursor() as cursor:
                if query.strip().upper() == "SHOW TABLES":
                    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';")
                    tables = [table[0] for table in cursor.fetchall()]
                    return [TextContent(type="text", text=json.dumps(tables))]
                elif query.strip().upper().startswith("SELECT"):
                    cursor.execute(query)
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    return [TextContent(type="text", text=json.dumps({"columns": columns, "rows": rows}))]
                else:
                    cursor.execute(query)
                    conn.commit()
                    return [TextContent(type="text", text=f"Query executed successfully. Rows affected: {cursor.rowcount}")]
    except Exception as e:
        logger.error(f"SQL Error: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def handle_sse(request):
    async with transport.connect_sse(request.scope, request.receive, request._send) as (
        in_stream, out_stream,
    ):
        await mcp._mcp_server.run(
            in_stream, out_stream, mcp._mcp_server.create_initialization_options()
        )

# Build and expose full app with SSE wiring
sse_app = Starlette(
    routes=[
        Route("/sse", handle_sse, methods=["GET"]),
        Mount("/messages/", app=transport.handle_post_message),
    ]
)

app = FastAPI()
app.mount("/", sse_app)

@app.get("/health")
async def health():
    try:
        config, _ = get_db_config()
        return {"status": "ok", "database": config["database"]}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting MSSQL MCP Server with SSE transport...")
    logger.info(f"MSSQL HOST: {os.getenv('MSSQL_HOST')}")
    logger.info(f"MSSQL DB: {os.getenv('MSSQL_DATABASE')}")
    logger.info(f"MSSQL username : {os.getenv('MSSQL_USER')}")
    logger.info("MSSQL MCP Server running on http://0.0.0.0:8008")
    logger.info("SSE endpoint: http://0.0.0.0:8008/mcp/sse")
    logger.info("Health check: http://0.0.0.0:8008/health")
    uvicorn.run(app, host="0.0.0.0", port=8008, log_level="info")