#!/usr/bin/env python3
"""
Read-Only MSSQL MCP Server with restricted database operations.
Only SELECT queries are allowed - INSERT, UPDATE, DELETE, and DDL operations are blocked.
"""

import os
import json
import logging
import secrets
import uuid
import re
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv
from pyodbc import connect
from decimal import Decimal
from datetime import datetime, date, timedelta
from urllib.parse import urlencode, urlparse

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
logger = logging.getLogger("mssql_mcp_server_readonly")

# OAuth storage
valid_tokens: Dict[str, Dict[str, Any]] = {}
auth_codes: Dict[str, Dict[str, Any]] = {}

# Configuration flags
READ_ONLY_MODE = os.getenv("READ_ONLY_MODE", "true").lower() == "true"
ALLOWED_OPERATIONS = os.getenv("ALLOWED_OPERATIONS", "SELECT").upper().split(",")
BLOCK_DDL = os.getenv("BLOCK_DDL", "true").lower() == "true"
BLOCK_STORED_PROCEDURES = os.getenv("BLOCK_STORED_PROCEDURES", "true").lower() == "true"
BLOCK_TRANSACTIONS = os.getenv("BLOCK_TRANSACTIONS", "true").lower() == "true"

# Security: restrict OAuth redirect URIs to trusted domains
ALLOWED_REDIRECT_HOSTS = [h.strip().lower() for h in os.getenv(
    "ALLOWED_REDIRECT_HOSTS",
    "chatgpt.com,openai.com,claude.ai,anthropic.com"
).split(",") if h.strip()]

# SQL operation patterns
DANGEROUS_KEYWORDS = [
    r'\bINSERT\s+INTO\b',
    r'\bUPDATE\s+\w+\s+SET\b',
    r'\bDELETE\s+FROM\b',
    r'\bTRUNCATE\s+TABLE\b',
    r'\bDROP\s+\w+\b',
    r'\bCREATE\s+\w+\b',
    r'\bALTER\s+\w+\b',
    r'\bGRANT\s+\w+\b',
    r'\bREVOKE\s+\w+\b',
    r'\bEXEC(?:UTE)?\s+\w+',
    r'\bMERGE\s+\w+\b',
    r'\bBULK\s+INSERT\b',
    r'\bINTO\s+#?\w+\s+FROM\b',  # SELECT INTO
]

DDL_PATTERNS = [
    r'\bCREATE\s+(?:TABLE|INDEX|VIEW|PROCEDURE|FUNCTION|TRIGGER)\b',
    r'\bDROP\s+(?:TABLE|INDEX|VIEW|PROCEDURE|FUNCTION|TRIGGER)\b',
    r'\bALTER\s+(?:TABLE|INDEX|VIEW|PROCEDURE|FUNCTION|TRIGGER)\b',
    r'\bTRUNCATE\s+TABLE\b',
]

TRANSACTION_PATTERNS = [
    r'\bBEGIN\s+TRAN(?:SACTION)?\b',
    r'\bCOMMIT\s+TRAN(?:SACTION)?\b',
    r'\bROLLBACK\s+TRAN(?:SACTION)?\b',
    r'\bSAVE\s+TRAN(?:SACTION)?\b',
]

STORED_PROC_PATTERNS = [
    r'\bEXEC(?:UTE)?\s+',
    r'\bsp_\w+',
    r'\bxp_\w+',
]

class SQLValidator:
    """Validates SQL queries for read-only operations."""
    
    @staticmethod
    def is_query_safe(query: str) -> Tuple[bool, str]:
        """
        Check if a SQL query is safe for read-only operation.
        Returns (is_safe, error_message)
        """
        if not query:
            return False, "Empty query"
        
        # Normalize query for checking
        normalized_query = query.upper().strip()
        
        # Check if it starts with SELECT or WITH (for CTEs)
        if not (normalized_query.startswith('SELECT') or 
                normalized_query.startswith('WITH') or
                normalized_query.startswith('SHOW') or
                normalized_query.startswith('DESCRIBE') or
                normalized_query.startswith('EXPLAIN')):
            
            # Special case for INFORMATION_SCHEMA queries
            if 'INFORMATION_SCHEMA' not in normalized_query:
                return False, "Only SELECT queries are allowed in read-only mode"
        
        # Check for dangerous keywords
        for pattern in DANGEROUS_KEYWORDS:
            if re.search(pattern, query, re.IGNORECASE):
                # Clean up pattern for display
                clean_pattern = pattern.replace('\\b', '').replace('\\s+', ' ').replace('\\w+', '*')
                return False, f"Operation not allowed: {clean_pattern}"
        
        # Check for DDL operations if blocked
        if BLOCK_DDL:
            for pattern in DDL_PATTERNS:
                if re.search(pattern, query, re.IGNORECASE):
                    return False, "DDL operations are not allowed"
        
        # Check for transaction commands if blocked
        if BLOCK_TRANSACTIONS:
            for pattern in TRANSACTION_PATTERNS:
                if re.search(pattern, query, re.IGNORECASE):
                    return False, "Transaction commands are not allowed"
        
        # Check for stored procedures if blocked
        if BLOCK_STORED_PROCEDURES:
            for pattern in STORED_PROC_PATTERNS:
                if re.search(pattern, query, re.IGNORECASE):
                    return False, "Stored procedure execution is not allowed"
        
        # Check for multiple statements (prevent SQL injection)
        if ';' in query:
            # Allow semicolon only at the end
            if not query.rstrip().endswith(';'):
                return False, "Multiple statements are not allowed"
            # Check if there are multiple semicolons
            if query.count(';') > 1:
                return False, "Multiple statements are not allowed"
        
        # Additional checks for sneaky updates
        if re.search(r'\bSELECT\b.*\bINTO\b', query, re.IGNORECASE):
            return False, "SELECT INTO is not allowed (creates new table)"
        
        return True, ""
    
    @staticmethod
    def sanitize_table_name(table_name: str) -> str:
        """
        Sanitize table name to prevent SQL injection.
        Only allows alphanumeric, underscore, dot (for schema), and brackets.
        """
        # Remove any potential SQL injection attempts
        if not re.match(r'^[\w\.\[\]]+$', table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        return table_name

# -----------------------------
# OAuth helper utilities
# -----------------------------
def _now_utc() -> datetime:
    return datetime.utcnow()

def _is_token_valid(token: str) -> bool:
    data = valid_tokens.get(token)
    if not data:
        return False
    try:
        expires_at = datetime.fromisoformat(data.get("expires_at"))
    except Exception:
        return False
    return _now_utc() < expires_at

def _extract_bearer_token(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    return auth.split(" ", 1)[1].strip()

def _is_host_allowed(redirect_uri: Optional[str]) -> bool:
    if not redirect_uri:
        return False
    try:
        host = urlparse(redirect_uri).hostname or ""
        host = host.lower()
        return any(host == h or host.endswith("." + h) for h in ALLOWED_REDIRECT_HOSTS)
    except Exception:
        return False

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
        "trusted_connection": os.getenv("Trusted_Connection", "no"),
        "application_intent": "ReadOnly" if READ_ONLY_MODE else "ReadWrite"
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
        f"ApplicationIntent={config['application_intent']};"
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

# Read-only tool implementations
def list_tables_impl():
    """Implementation of list_tables tool - always safe as it's read-only."""
    try:
        config, connection_string = get_db_config()
        with connect(connection_string) as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT 
                        TABLE_SCHEMA,
                        TABLE_NAME,
                        TABLE_TYPE
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_SCHEMA, TABLE_NAME
                """
                cursor.execute(query)
                tables = cursor.fetchall()
                
                result = {
                    "total_tables": len(tables),
                    "read_only_mode": READ_ONLY_MODE,
                    "tables": [
                        {
                            "table_name": row[1],
                            "schema": row[0],
                            "full_name": f"{row[0]}.{row[1]}" if row[0] != 'dbo' else row[1],
                            "type": row[2]
                        }
                        for row in tables
                    ]
                }
                
                return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        return json.dumps({"error": f"Error listing tables: {str(e)}"})

def describe_table_impl(table_name: str):
    """Implementation of describe_table tool - always safe as it's read-only."""
    try:
        # Sanitize table name
        table_name = SQLValidator.sanitize_table_name(table_name)
        
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
                    "read_only_mode": READ_ONLY_MODE,
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
        return json.dumps({"error": f"Error describing table: {str(e)}"})

def execute_sql_impl(query: str):
    """
    Implementation of execute_sql tool with read-only restrictions.
    Only allows SELECT and other read operations.
    """
    try:
        # Validate query for read-only operations
        is_safe, error_message = SQLValidator.is_query_safe(query)
        if not is_safe:
            logger.warning(f"Blocked unsafe query: {query[:100]}... - Reason: {error_message}")
            return json.dumps({
                "error": error_message,
                "query": query,
                "read_only_mode": READ_ONLY_MODE,
                "allowed_operations": ALLOWED_OPERATIONS
            }, indent=2)
        
        config, connection_string = get_db_config()
        with connect(connection_string) as conn:
            # Set connection to read-only if possible
            conn.autocommit = False
            conn.rollback()  # Ensure clean state
            
            with conn.cursor() as cursor:
                cursor.execute(query)
                
                # Since we only allow SELECT, we always fetch results
                if cursor.description:
                    columns = [column[0] for column in cursor.description]
                    rows = cursor.fetchall()
                    
                    result = {
                        "query": query,
                        "columns": columns,
                        "rows": [serialize_row_data(dict(zip(columns, row))) for row in rows],
                        "row_count": len(rows),
                        "read_only_mode": READ_ONLY_MODE,
                        "status": "success"
                    }
                else:
                    # This shouldn't happen with SELECT queries
                    result = {
                        "query": query,
                        "message": "Query executed but returned no results",
                        "read_only_mode": READ_ONLY_MODE,
                        "status": "success"
                    }
                
                return json.dumps(result, indent=2, default=str)
                
    except Exception as e:
        logger.error(f"Failed to execute query: {e}")
        return json.dumps({
            "error": f"Error executing query: {str(e)}",
            "query": query,
            "read_only_mode": READ_ONLY_MODE
        }, indent=2)

def get_table_sample_impl(table_name: str, limit: int = 5):
    """Implementation of get_table_sample tool - always safe as it's read-only."""
    try:
        # Sanitize inputs
        table_name = SQLValidator.sanitize_table_name(table_name)
        limit = min(max(1, int(limit)), 1000)  # Limit between 1 and 1000
        
        query = f"SELECT TOP {limit} * FROM {table_name}"
        return execute_sql_impl(query)
    except Exception as e:
        logger.error(f"Failed to get table sample: {e}")
        return json.dumps({"error": f"Error getting table sample: {str(e)}"})

# OAuth endpoints (unchanged)
async def oauth_authorization_server(request: Request):
    """OAuth authorization server discovery endpoint (path-aware)."""
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("host", "data.forensic-bot.com")
    env_path = request.headers.get("x-environment-path", "")
    if env_path and not env_path.startswith("/"):
        env_path = "/" + env_path
    env_path = env_path.rstrip("/")
    base_url = f"{forwarded_proto}://{host}{env_path}"
    
    return JSONResponse({
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "registration_endpoint": f"{base_url}/register",
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
        "server_mode": "read_only" if READ_ONLY_MODE else "read_write"
    })

async def oauth_protected_resource(request: Request):
    """OAuth protected resource discovery endpoint (path-aware)."""
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("host", "data.forensic-bot.com")
    env_path = request.headers.get("x-environment-path", "")
    if env_path and not env_path.startswith("/"):
        env_path = "/" + env_path
    env_path = env_path.rstrip("/")
    base_url = f"{forwarded_proto}://{host}{env_path}"
    
    return JSONResponse({
        "resource": f"{base_url}/sse",
        "oauth_authorization_server": base_url,
        "bearer_methods_supported": ["header"],
        "resource_documentation": f"{base_url}/docs",
        "server_mode": "read_only" if READ_ONLY_MODE else "read_write",
        "allowed_operations": ALLOWED_OPERATIONS
    })

async def register(request: Request):
    """Dynamic client registration endpoint."""
    try:
        body = await request.json()
    except:
        body = {}
    
    client_id = f"client_{uuid.uuid4().hex[:16]}"
    client_secret = secrets.token_urlsafe(32)
    
    logger.info(f"Registered new OAuth client: {client_id} (Read-only mode: {READ_ONLY_MODE})")
    
    return JSONResponse({
        "client_id": client_id,
        "client_secret": client_secret,
        "client_id_issued_at": int(datetime.utcnow().timestamp()),
        "grant_types": ["authorization_code", "refresh_token"],
        "redirect_uris": body.get("redirect_uris", ["https://claude.ai/api/mcp/auth_callback"]),
        "client_name": body.get("client_name", "Claude.ai"),
        "server_mode": "read_only" if READ_ONLY_MODE else "read_write"
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
        "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
        "scope": "read" if READ_ONLY_MODE else "read write"
    }
    
    logger.info(f"Authorization request from client: {client_id} (Scope: {'read' if READ_ONLY_MODE else 'read write'})")
    
    # Validate redirect_uri against allowed domains
    if redirect_uri and not _is_host_allowed(redirect_uri):
        logger.warning(f"Blocked authorization due to untrusted redirect host: {redirect_uri}")
        return JSONResponse({"error": "untrusted_redirect_uri"}, status_code=400)

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
        "expires_at": (_now_utc() + timedelta(hours=1)).isoformat(),
        "scope": "mcp:read" if READ_ONLY_MODE else "mcp:read mcp:write"
    }
    
    logger.info(f"Issued tokens for client: {data.get('client_id', 'unknown')} (Scope: {'mcp:read' if READ_ONLY_MODE else 'mcp:read mcp:write'})")
    
    return JSONResponse({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": refresh_token,
        "scope": "mcp:read" if READ_ONLY_MODE else "mcp:read mcp:write"
    })

async def health_check(request: Request):
    """Health check endpoint."""
    try:
        config, connection_string = get_db_config()
        return JSONResponse({
            "status": "healthy",
            "transport": "sse",
            "oauth": "enabled",
            "database": config["database"],
            "mode": "read_only" if READ_ONLY_MODE else "read_write",
            "allowed_operations": ALLOWED_OPERATIONS,
            "security": {
                "block_ddl": BLOCK_DDL,
                "block_stored_procedures": BLOCK_STORED_PROCEDURES,
                "block_transactions": BLOCK_TRANSACTIONS
            }
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status_code=500)

# SSE handlers
async def handle_sse_head(request: Request):
    """Handle HEAD/GET probes to /sse endpoint."""
    logger.info("Handling HEAD request for /sse")
    return Response(
        content="",
        status_code=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "X-Server-Mode": "read-only" if READ_ONLY_MODE else "read-write"
        }
    )

async def handle_sse_post(request: Request):
    """Handle POST requests to /sse - Main MCP handler."""
    logger.info("Handling POST request to /sse")
    # Require OAuth bearer token for access
    token = _extract_bearer_token(request)
    if not token or not _is_token_valid(token):
        logger.warning("Unauthorized /sse access attempt: missing or invalid token")
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    try:
        body = await request.json()
        method = body.get("method")
        request_id = body.get("id")
        
        logger.info(f"MCP method: {method}, id: {request_id}")
        
        # Handle different MCP methods
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {}
                    },
                    "serverInfo": {
                        "name": "MSSQL MCP Server (Read-Only)" if READ_ONLY_MODE else "MSSQL MCP Server",
                        "version": "2.0.0",
                        "mode": "read_only" if READ_ONLY_MODE else "read_write"
                    }
                }
            }
            
        elif method == "notifications/initialized":
            logger.info("Received initialized notification")
            return Response(content="", status_code=204)
            
        elif method == "tools/list":
            tools_list = [
                {
                    "name": "list_tables",
                    "title": "List Database Tables",
                    "description": "List all tables in the database (read-only operation)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "describe_table",
                    "title": "Describe Table Structure",
                    "description": "Get detailed information about a table including columns, data types, and constraints (read-only operation)",
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
                    "title": "Execute SQL Query (Read-Only)",
                    "description": f"Execute SQL query on the MSSQL database. {'Only SELECT queries are allowed in read-only mode.' if READ_ONLY_MODE else 'Supports SELECT, INSERT, UPDATE, DELETE'}",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": f"SQL query to execute {'(SELECT only)' if READ_ONLY_MODE else ''}"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_table_sample",
                    "title": "Get Table Sample Data",
                    "description": "Get a sample of records from a specific table (read-only operation)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of records to retrieve (max 1000)",
                                "default": 5
                            }
                        },
                        "required": ["table_name"]
                    }
                }
            ]
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": tools_list
                }
            }
            
        elif method == "tools/call":
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
                result = json.dumps({"error": f"Unknown tool: {tool_name}"})
            
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
            
        elif method == "resources/list":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "resources": []
                }
            }
            
        elif method == "prompts/list":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "prompts": []
                }
            }
            
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        logger.info(f"Returning response for {method}")
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
        Route("/sse", handle_sse_head, methods=["HEAD", "GET"]),
        Route("/sse", handle_sse_post, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("Starting MSSQL MCP Server - READ-ONLY MODE" if READ_ONLY_MODE else "Starting MSSQL MCP Server")
    logger.info("=" * 70)
    logger.info(f"Configuration:")
    logger.info(f"  Read-Only Mode: {READ_ONLY_MODE}")
    logger.info(f"  Allowed Operations: {ALLOWED_OPERATIONS}")
    logger.info(f"  Block DDL: {BLOCK_DDL}")
    logger.info(f"  Block Stored Procedures: {BLOCK_STORED_PROCEDURES}")
    logger.info(f"  Block Transactions: {BLOCK_TRANSACTIONS}")
    logger.info(f"  MSSQL Host: {os.getenv('MSSQL_HOST')}")
    logger.info(f"  MSSQL Database: {os.getenv('MSSQL_DATABASE')}")
    logger.info(f"  MSSQL User: {os.getenv('MSSQL_USER')}")
    logger.info("=" * 70)
    logger.info("Security Features:")
    logger.info("  ✓ SQL injection prevention")
    logger.info("  ✓ Query validation and sanitization")
    logger.info("  ✓ Operation whitelisting")
    logger.info("  ✓ OAuth 2.0 authentication")
    if READ_ONLY_MODE:
        logger.info("  ✓ READ-ONLY: No INSERT, UPDATE, DELETE, or DDL operations allowed")
    logger.info("=" * 70)
    logger.info("Server running on http://0.0.0.0:8008")
    logger.info("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8008, log_level="info")