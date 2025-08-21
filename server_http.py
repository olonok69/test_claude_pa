#!/usr/bin/env python3
"""
MSSQL MCP Server with Streamable HTTP Transport
Compatible with Claude.ai custom connectors
"""

import os
import json
import logging
import uuid
import secrets
import asyncio
import contextlib
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pyodbc import connect, Error
from decimal import Decimal
from datetime import datetime, date, timedelta

from mcp.types import TextContent
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, StreamingResponse, RedirectResponse
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

# Load environment variables
load_dotenv(".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mssql_mcp_server")

# Create MCP server with stateless HTTP mode for Claude.ai
# Setting the transport and mount path properly
mcp = FastMCP("MSSQL MCP Server", stateless_http=True)

# Simple in-memory token storage (in production, use Redis or database)
valid_tokens: Dict[str, Dict[str, Any]] = {}
client_registry: Dict[str, Dict[str, Any]] = {}

def get_db_config():
    """Get database configuration from environment variables."""
    config = {
        "driver": os.getenv("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server"),
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
        f"Driver={{{config['driver']}}};Server={config['server']};"
        f"UID={config['user']};PWD={config['password']};"
        f"Database={config['database']};"
        f"TrustServerCertificate={config['trusted_server_certificate']};"
        f"Trusted_Connection={config['trusted_connection']};"
    )

    return config, connection_string

def serialize_row_data(data):
    """Convert pyodbc Row objects and other non-JSON serializable types to JSON-compatible format."""
    if data is None:
        return None
    elif isinstance(data, (str, int, float, bool)):
        return data
    elif isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    elif hasattr(data, '_asdict'):  # pyodbc Row object
        return dict(data._asdict())
    elif isinstance(data, (list, tuple)):
        return [serialize_row_data(item) for item in data]
    elif isinstance(data, dict):
        return {key: serialize_row_data(value) for key, value in data.items()}
    else:
        return str(data)

# Define MCP tools
@mcp.tool()
async def list_tables() -> list[TextContent]:
    """List all tables in the database."""
    try:
        config, connection_string = get_db_config()
        with connect(connection_string) as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT 
                        TABLE_SCHEMA,
                        TABLE_NAME
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_SCHEMA, TABLE_NAME
                """
                cursor.execute(query)
                tables = cursor.fetchall()
                
                result = {
                    "total_tables": len(tables),
                    "tables": [
                        {
                            "table_name": row[1],
                            "schema": row[0],
                            "full_name": f"{row[0]}.{row[1]}" if row[0] != 'dbo' else row[1]
                        }
                        for row in tables
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        return [TextContent(type="text", text=f"Error listing tables: {str(e)}")]

@mcp.tool()
async def describe_table(table_name: str) -> list[TextContent]:
    """Get detailed information about a table including columns, data types, and constraints."""
    try:
        config, connection_string = get_db_config()
        with connect(connection_string) as conn:
            with conn.cursor() as cursor:
                # Get row count
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                cursor.execute(count_query)
                row_count = cursor.fetchone()[0]
                
                # Get column information
                columns_query = """
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        IS_NULLABLE,
                        COLUMN_DEFAULT,
                        CHARACTER_MAXIMUM_LENGTH,
                        NUMERIC_PRECISION,
                        NUMERIC_SCALE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = ?
                    ORDER BY ORDINAL_POSITION
                """
                cursor.execute(columns_query, (table_name.split('.')[-1],))
                columns = cursor.fetchall()
                
                result = {
                    "table_name": table_name,
                    "row_count": row_count,
                    "total_columns": len(columns),
                    "columns": [
                        {
                            "column_name": col[0],
                            "data_type": col[1],
                            "nullable": col[2] == 'YES',
                            "default_value": col[3],
                            "max_length": col[4],
                            "precision": col[5],
                            "scale": col[6]
                        }
                        for col in columns
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.error(f"Failed to describe table {table_name}: {e}")
        return [TextContent(type="text", text=f"Error describing table: {str(e)}")]

@mcp.tool()
async def execute_sql(query: str) -> list[TextContent]:
    """Execute an SQL query on the MSSQL database. Supports SELECT, INSERT, UPDATE, DELETE, and other SQL commands."""
    try:
        config, connection_string = get_db_config()
        with connect(connection_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                
                # Check if it's a SELECT query
                if query.strip().upper().startswith('SELECT'):
                    columns = [column[0] for column in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    
                    result = {
                        "query": query,
                        "columns": columns,
                        "rows": [serialize_row_data(dict(zip(columns, row))) for row in rows],
                        "row_count": len(rows)
                    }
                    
                    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
                else:
                    # For INSERT, UPDATE, DELETE queries
                    conn.commit()
                    result = {
                        "query": query,
                        "rows_affected": cursor.rowcount,
                        "status": "success"
                    }
                    
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.error(f"Failed to execute query: {e}")
        return [TextContent(type="text", text=f"Error executing query: {str(e)}")]

@mcp.tool()
async def get_table_sample(table_name: str, limit: int = 5) -> list[TextContent]:
    """Get a sample of records from a specific table."""
    try:
        query = f"SELECT TOP {limit} * FROM {table_name}"
        return await execute_sql(query)
    except Exception as e:
        logger.error(f"Failed to get sample from {table_name}: {e}")
        return [TextContent(type="text", text=f"Error getting sample: {str(e)}")]

# OAuth middleware to validate tokens
class OAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to validate OAuth tokens for protected endpoints."""
    
    # Endpoints that don't require authentication
    PUBLIC_ENDPOINTS = [
        "/health",
        "/.well-known/oauth-authorization-server",
        "/.well-known/oauth-protected-resource", 
        "/register",
        "/authorize",
        "/token"
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if any(request.url.path.startswith(endpoint) for endpoint in self.PUBLIC_ENDPOINTS):
            return await call_next(request)
        
        # Check for Bearer token in Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            # Validate token
            if token in valid_tokens:
                # Token is valid, add user info to request
                request.state.token_info = valid_tokens[token]
                return await call_next(request)
        
        # For MCP and SSE endpoints, allow both authenticated and unauthenticated
        # (Claude.ai might not send token immediately)
        if request.url.path in ["/mcp", "/sse", "/mcp/", "/sse/"]:
            logger.info(f"Allowing unauthenticated access to {request.url.path}")
            return await call_next(request)
        
        # Token invalid or missing
        return JSONResponse(
            {"error": "unauthorized", "error_description": "Invalid or missing token"},
            status_code=401,
            headers={"WWW-Authenticate": 'Bearer realm="MCP Server"'}
        )
async def health_check(request: Request):
    """Health check endpoint."""
    try:
        config, connection_string = get_db_config()
        # Test database connection
        with connect(connection_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        
        return JSONResponse({
            "status": "healthy",
            "database": config["database"],
            "server": config["server"],
            "driver": config["driver"],
            "transport": "streamable-http"
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status_code=500)

# OAuth mock endpoints for Claude.ai discovery
async def oauth_authorization_server(request: Request):
    """Mock OAuth authorization server discovery."""
    return JSONResponse({
        "issuer": "https://data.forensic-bot.com",
        "authorization_endpoint": "https://data.forensic-bot.com/authorize",
        "token_endpoint": "https://data.forensic-bot.com/token",
        "registration_endpoint": "https://data.forensic-bot.com/register",
        "mcp_endpoint": "https://data.forensic-bot.com/"  # Point to root
    })

async def oauth_protected_resource(request: Request):
    """Mock OAuth protected resource discovery."""
    return JSONResponse({
        "resource": "https://data.forensic-bot.com/",  # Point to root
        "oauth_authorization_server": "https://data.forensic-bot.com"
    })

async def register(request: Request):
    """Registration endpoint for OAuth clients."""
    body = await request.json() if request.method == "POST" else {}
    client_id = f"client_{uuid.uuid4().hex[:8]}"
    client_secret = secrets.token_urlsafe(32)
    
    # Store client credentials
    client_registry[client_id] = {
        "client_secret": client_secret,
        "redirect_uris": body.get("redirect_uris", []),
        "created_at": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Registered new client: {client_id}")
    
    return JSONResponse({
        "client_id": client_id,
        "client_secret": client_secret,
        "registration_access_token": secrets.token_urlsafe(32),
        "grant_types": ["client_credentials", "authorization_code"],
        "redirect_uris": body.get("redirect_uris", [])
    })

async def authorize(request: Request):
    """Authorization endpoint - handles OAuth authorization code flow."""
    # Get query parameters
    client_id = request.query_params.get("client_id")
    redirect_uri = request.query_params.get("redirect_uri")
    state = request.query_params.get("state", "")
    response_type = request.query_params.get("response_type", "code")
    
    # Generate an authorization code
    auth_code = secrets.token_urlsafe(32)
    
    # Store the auth code for later exchange
    # In production, store this with expiration and client validation
    valid_tokens[f"authcode_{auth_code}"] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    }
    
    logger.info(f"Authorization request from client: {client_id}")
    
    # Redirect back to Claude with the authorization code
    if redirect_uri:
        from urllib.parse import urlencode
        params = {
            "code": auth_code,
            "state": state
        }
        redirect_url = f"{redirect_uri}?{urlencode(params)}"
        
        # Return a redirect response
        from starlette.responses import RedirectResponse
        return RedirectResponse(url=redirect_url, status_code=302)
    
    # Fallback if no redirect_uri
    return JSONResponse({
        "authorization_code": auth_code,
        "state": state
    })

async def token(request: Request):
    """Token endpoint - handles both authorization code and client credentials flows."""
    # Handle both form data and JSON
    content_type = request.headers.get("content-type", "")
    
    if "application/x-www-form-urlencoded" in content_type:
        form_data = await request.form()
        data = dict(form_data)
    elif "application/json" in content_type:
        data = await request.json()
    else:
        data = {}
    
    grant_type = data.get("grant_type", "client_credentials")
    
    # Generate access token
    access_token = secrets.token_urlsafe(32)
    
    # Handle authorization code flow
    if grant_type == "authorization_code":
        code = data.get("code")
        # Validate the authorization code
        auth_code_key = f"authcode_{code}"
        if auth_code_key in valid_tokens:
            # Remove the used authorization code
            code_info = valid_tokens.pop(auth_code_key, {})
            client_id = code_info.get("client_id", "unknown")
        else:
            client_id = data.get("client_id", "unknown")
    else:
        client_id = data.get("client_id", "unknown")
    
    # Store the access token
    valid_tokens[access_token] = {
        "client_id": client_id,
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "scope": data.get("scope", "mcp.access")
    }
    
    logger.info(f"Issued token for client: {client_id} (grant_type: {grant_type})")
    
    return JSONResponse({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": secrets.token_urlsafe(32),
        "scope": data.get("scope", "mcp.access")
    })

# Create the Starlette app with MCP mounted at /mcp
app = Starlette(
    routes=[
        # Health check
        Route("/health", health_check, methods=["GET"]),
        
        # OAuth discovery endpoints
        Route("/.well-known/oauth-authorization-server", oauth_authorization_server, methods=["GET"]),
        Route("/.well-known/oauth-protected-resource", oauth_protected_resource, methods=["GET"]),
        Route("/register", register, methods=["POST"]),
        Route("/authorize", authorize, methods=["GET", "POST"]),
        Route("/token", token, methods=["POST"]),
    ]
)

# Mount the MCP server's streamable HTTP app at /mcp
mcp_app = mcp.streamable_http_app()  # No mount_path parameter
app.mount("/mcp", mcp_app)

# Also mount at /sse for backward compatibility
app.mount("/sse", mcp_app)

if __name__ == "__main__":
    logger.info("Starting MSSQL MCP Server with Streamable HTTP transport...")
    logger.info(f"MSSQL HOST: {os.getenv('MSSQL_HOST')}")
    logger.info(f"MSSQL DB: {os.getenv('MSSQL_DATABASE')}")
    logger.info(f"MSSQL username: {os.getenv('MSSQL_USER')}")
    logger.info("=" * 50)
    logger.info("MCP Server running on http://0.0.0.0:8008")
    logger.info("OAuth endpoints:")
    logger.info("  - Discovery: GET /.well-known/oauth-authorization-server")
    logger.info("  - Register: POST /register")
    logger.info("  - Authorize: GET /authorize")
    logger.info("  - Token: POST /token")
    logger.info("MCP endpoints:")
    logger.info("  - MCP: POST /mcp")
    logger.info("  - SSE: POST /sse")
    logger.info("  - Messages: POST /messages")
    logger.info("=" * 50)
    
    # Run with the streamable-http transport directly
    # This avoids the redirect issues
    import asyncio
    import contextlib
    
    async def run_server():
        async with contextlib.AsyncExitStack() as stack:
            # Start the session manager
            await stack.enter_async_context(mcp.session_manager.run())
            
            # Get the ASGI app
            mcp_asgi = mcp.streamable_http_app()
            
            # Create a combined app with OAuth endpoints and MCP
            from starlette.applications import Starlette
            from starlette.routing import Mount, Route
            
            combined_app = Starlette(
                routes=[
                    # OAuth and health endpoints
                    Route("/health", health_check, methods=["GET"]),
                    Route("/.well-known/oauth-authorization-server", oauth_authorization_server, methods=["GET"]),
                    Route("/.well-known/oauth-protected-resource", oauth_protected_resource, methods=["GET"]),
                    Route("/register", register, methods=["POST"]),
                    Route("/authorize", authorize, methods=["GET", "POST"]),
                    Route("/token", token, methods=["POST"]),
                    # Mount MCP app at root to handle all other paths
                    Mount("/", app=mcp_asgi),
                ]
            )
            
            # Add middleware after app creation
            combined_app.add_middleware(OAuthMiddleware)
            
            # Run the combined app
            config = uvicorn.Config(
                combined_app,
                host="0.0.0.0",
                port=8008,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
    
    # Run the async server
    asyncio.run(run_server())