#!/usr/bin/env python3
"""
Fixed MSSQL MCP Server that properly implements the MCP protocol for Claude.ai
"""

import os
import json
import logging
import secrets
import uuid
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pyodbc import connect
from decimal import Decimal
from datetime import datetime, date, timedelta
from urllib.parse import urlencode

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.requests import Request
import uvicorn

# Load environment variables
load_dotenv(".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mssql_mcp_server")

# OAuth storage
valid_tokens: Dict[str, Dict[str, Any]] = {}
auth_codes: Dict[str, Dict[str, Any]] = {}

# Database configuration
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
    elif hasattr(data, '_asdict'):
        return dict(data._asdict())
    elif isinstance(data, (list, tuple)):
        return [serialize_row_data(item) for item in data]
    elif isinstance(data, dict):
        return {key: serialize_row_data(value) for key, value in data.items()}
    else:
        return str(data)

# Tool implementations
def list_tables_impl():
    """Implementation of list_tables tool."""
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
                
                return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        return f"Error listing tables: {str(e)}"

def describe_table_impl(table_name: str):
    """Implementation of describe_table tool."""
    try:
        config, connection_string = get_db_config()
        with connect(connection_string) as conn:
            with conn.cursor() as cursor:
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                cursor.execute(count_query)
                row_count = cursor.fetchone()[0]
                
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
                
                return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Failed to describe table {table_name}: {e}")
        return f"Error describing table: {str(e)}"

def execute_sql_impl(query: str):
    """Implementation of execute_sql tool."""
    try:
        config, connection_string = get_db_config()
        with connect(connection_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                
                if query.strip().upper().startswith('SELECT'):
                    columns = [column[0] for column in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    
                    result = {
                        "query": query,
                        "columns": columns,
                        "rows": [serialize_row_data(dict(zip(columns, row))) for row in rows],
                        "row_count": len(rows)
                    }
                    
                    return json.dumps(result, indent=2, default=str)
                else:
                    conn.commit()
                    result = {
                        "query": query,
                        "rows_affected": cursor.rowcount,
                        "status": "success"
                    }
                    
                    return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Failed to execute query: {e}")
        return f"Error executing query: {str(e)}"

def get_table_sample_impl(table_name: str, limit: int = 5):
    """Implementation of get_table_sample tool."""
    query = f"SELECT TOP {limit} * FROM {table_name}"
    return execute_sql_impl(query)

# OAuth endpoints
async def oauth_authorization_server(request: Request):
    """OAuth authorization server discovery endpoint."""
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("host", "data.forensic-bot.com")
    base_url = f"{forwarded_proto}://{host}"
    
    return JSONResponse({
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "registration_endpoint": f"{base_url}/register",
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"]
    })

async def oauth_protected_resource(request: Request):
    """OAuth protected resource discovery endpoint."""
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("host", "data.forensic-bot.com")
    base_url = f"{forwarded_proto}://{host}"
    
    return JSONResponse({
        "resource": f"{base_url}/sse",
        "oauth_authorization_server": base_url,
        "bearer_methods_supported": ["header"],
        "resource_documentation": f"{base_url}/docs"
    })

async def register(request: Request):
    """Dynamic client registration endpoint."""
    try:
        body = await request.json()
    except:
        body = {}
    
    client_id = f"client_{uuid.uuid4().hex[:16]}"
    client_secret = secrets.token_urlsafe(32)
    
    logger.info(f"Registered new OAuth client: {client_id}")
    
    return JSONResponse({
        "client_id": client_id,
        "client_secret": client_secret,
        "client_id_issued_at": int(datetime.utcnow().timestamp()),
        "grant_types": ["authorization_code", "refresh_token"],
        "redirect_uris": body.get("redirect_uris", ["https://claude.ai/api/mcp/auth_callback"]),
        "client_name": body.get("client_name", "Claude.ai")
    })

async def authorize(request: Request):
    """Authorization endpoint."""
    client_id = request.query_params.get("client_id")
    redirect_uri = request.query_params.get("redirect_uri")
    state = request.query_params.get("state", "")
    
    auth_code = secrets.token_urlsafe(32)
    
    auth_codes[auth_code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    }
    
    logger.info(f"Authorization request from client: {client_id}")
    
    if redirect_uri:
        params = {"code": auth_code, "state": state}
        redirect_url = f"{redirect_uri}?{urlencode(params)}"
        return RedirectResponse(url=redirect_url, status_code=302)
    
    return JSONResponse({"authorization_code": auth_code, "state": state})

async def token(request: Request):
    """Token endpoint."""
    content_type = request.headers.get("content-type", "")
    
    if "application/x-www-form-urlencoded" in content_type:
        form_data = await request.form()
        data = dict(form_data)
    elif "application/json" in content_type:
        data = await request.json()
    else:
        data = {}
    
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)
    
    valid_tokens[access_token] = {
        "client_id": data.get("client_id", "unknown"),
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }
    
    logger.info(f"Issued tokens for client: {data.get('client_id', 'unknown')}")
    
    return JSONResponse({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": refresh_token,
        "scope": "mcp:read mcp:write"
    })

async def health_check(request: Request):
    """Health check endpoint."""
    try:
        config, connection_string = get_db_config()
        return JSONResponse({
            "status": "healthy",
            "transport": "sse",
            "oauth": "enabled",
            "database": config["database"]
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status_code=500)

# SSE handlers
async def handle_sse_head(request: Request):
    """Handle HEAD requests to /sse endpoint."""
    logger.info("Handling HEAD request for /sse")
    return Response(
        content="",
        status_code=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*"
        }
    )

async def handle_sse_post(request: Request):
    """Handle POST requests to /sse - Main MCP handler."""
    logger.info("Handling POST request to /sse")
    
    try:
        body = await request.json()
        method = body.get("method")
        request_id = body.get("id")
        
        logger.info(f"MCP method: {method}, id: {request_id}")
        logger.info(f"Full request body: {json.dumps(body)}")
        
        # Handle different MCP methods
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "tools": {},  # Empty object means tools are supported
                        "resources": {},
                        "prompts": {}
                    },
                    "serverInfo": {
                        "name": "MSSQL MCP Server",
                        "version": "1.0.0"
                    }
                }
            }
            
        elif method == "notifications/initialized":
            # This is a notification - NO response needed!
            # Claude.ai will call tools/list separately
            logger.info("Received initialized notification")
            return Response(content="", status_code=204)  # No content
            
        elif method == "tools/list":
            # THIS is where we return the tools list
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "list_tables",
                            "title": "List Database Tables",
                            "description": "List all tables in the database",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        },
                        {
                            "name": "describe_table",
                            "title": "Describe Table Structure",
                            "description": "Get detailed information about a table including columns, data types, and constraints",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "table_name": {
                                        "type": "string",
                                        "description": "Name of the table to describe"
                                    }
                                },
                                "required": ["table_name"]
                            }
                        },
                        {
                            "name": "execute_sql",
                            "title": "Execute SQL Query",
                            "description": "Execute an SQL query on the MSSQL database. Supports SELECT, INSERT, UPDATE, DELETE",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "SQL query to execute"
                                    }
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "get_table_sample",
                            "title": "Get Table Sample Data",
                            "description": "Get a sample of records from a specific table",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "table_name": {
                                        "type": "string",
                                        "description": "Name of the table"
                                    },
                                    "limit": {
                                        "type": "integer",
                                        "description": "Number of records to retrieve",
                                        "default": 5
                                    }
                                },
                                "required": ["table_name"]
                            }
                        }
                    ]
                }
            }
            
        elif method == "tools/call":
            # THIS is the correct method for tool execution
            params = body.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            logger.info(f"Tool call: {tool_name} with args: {arguments}")
            
            # Execute the appropriate tool
            if tool_name == "list_tables":
                result = list_tables_impl()
            elif tool_name == "describe_table":
                result = describe_table_impl(arguments.get("table_name"))
            elif tool_name == "execute_sql":
                result = execute_sql_impl(arguments.get("query"))
            elif tool_name == "get_table_sample":
                result = get_table_sample_impl(
                    arguments.get("table_name"),
                    arguments.get("limit", 5)
                )
            else:
                result = f"Unknown tool: {tool_name}"
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ],
                    "isError": False
                }
            }
            
        elif method == "tools/listChanged":
            # Notification that tools have changed
            logger.info("Received tools/listChanged notification")
            return Response(content="", status_code=204)
            
        elif method == "resources/list":
            # Return empty resources list if requested
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "resources": []
                }
            }
            
        elif method == "prompts/list":
            # Return empty prompts list if requested
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "prompts": []
                }
            }
            
        else:
            # Unknown method
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        logger.info(f"Returning response for {method}: {len(json.dumps(response))} bytes")
        return JSONResponse(response)
        
    except Exception as e:
        logger.error(f"Error handling SSE POST: {e}", exc_info=True)
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": body.get("id") if 'body' in locals() else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }, status_code=500)

# Create Starlette app
app = Starlette(
    routes=[
        # OAuth discovery endpoints
        Route("/.well-known/oauth-authorization-server", oauth_authorization_server, methods=["GET"]),
        Route("/.well-known/oauth-protected-resource", oauth_protected_resource, methods=["GET"]),
        
        # OAuth flow endpoints
        Route("/register", register, methods=["POST"]),
        Route("/authorize", authorize, methods=["GET", "POST"]),
        Route("/token", token, methods=["POST"]),
        
        # Health check
        Route("/health", health_check, methods=["GET"]),
        
        # SSE endpoints
        Route("/sse", handle_sse_head, methods=["HEAD"]),
        Route("/sse", handle_sse_post, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    logger.info("Starting Fixed MSSQL MCP Server...")
    logger.info(f"MSSQL HOST: {os.getenv('MSSQL_HOST')}")
    logger.info(f"MSSQL DB: {os.getenv('MSSQL_DATABASE')}")
    logger.info(f"MSSQL USER: {os.getenv('MSSQL_USER')}")
    logger.info("=" * 50)
    logger.info("Server running on http://0.0.0.0:8008")
    logger.info("OAuth enabled with dynamic client registration")
    logger.info("MCP Protocol:")
    logger.info("  - initialize: Returns server capabilities")
    logger.info("  - tools/list: Returns available tools")
    logger.info("  - tools/call: Executes a tool")
    logger.info("  - notifications/initialized: No response")
    logger.info("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8008, log_level="info")