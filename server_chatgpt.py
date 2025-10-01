#!/usr/bin/env python3
"""
ChatGPT-compatible MSSQL MCP Server
Implements search and fetch tools required by ChatGPT Deep Research
Wraps existing database functionality into ChatGPT's required interface
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
import hashlib

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.requests import Request
import uvicorn

# Reuse read-only tool implementations from server_oauth
try:
    from server_oauth import (
        list_tables_impl as _list_tables_impl,
        describe_table_impl as _describe_table_impl,
        execute_sql_impl as _execute_sql_impl,
        get_table_sample_impl as _get_table_sample_impl,
    )
except Exception:
    _list_tables_impl = _describe_table_impl = _execute_sql_impl = _get_table_sample_impl = None

# Load environment variables
load_dotenv(".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chatgpt_mssql_mcp_server")

# OAuth storage
valid_tokens: Dict[str, Dict[str, Any]] = {}
auth_codes: Dict[str, Dict[str, Any]] = {}

# Cache for search results (to support fetch)
search_cache: Dict[str, Any] = {}

# Configuration
READ_ONLY_MODE = os.getenv("READ_ONLY_MODE", "true").lower() == "true"
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "50"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
# Note: OAuth is required for all POST /sse methods (initialize, tools/list, tools/call, etc.)
# Keeping flags defined for compatibility, but they're not used to bypass auth anymore.
ALLOW_UNAUTH_METHODS = os.getenv("ALLOW_UNAUTH_METHODS", "false").lower() == "true"
ALLOW_UNAUTH_TOOLS_CALL = os.getenv("ALLOW_UNAUTH_TOOLS_CALL", "false").lower() == "true"

# Security: restrict OAuth redirect URIs to trusted domains
ALLOWED_REDIRECT_HOSTS = [h.strip().lower() for h in os.getenv(
    "ALLOWED_REDIRECT_HOSTS",
    "chatgpt.com,openai.com,claude.ai,anthropic.com"
).split(",") if h.strip()]

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

def generate_record_id(table_name: str, record: Dict[str, Any]) -> str:
    """Generate a unique ID for a database record."""
    # Try to use primary key if available
    for key in ['id', 'ID', 'Id', 'pk', 'PK']:
        if key in record:
            return f"{table_name}:{record[key]}"
    
    # Otherwise, create a hash of the record
    record_str = json.dumps(record, sort_keys=True, default=str)
    record_hash = hashlib.md5(record_str.encode()).hexdigest()[:8]
    return f"{table_name}:{record_hash}"

def parse_search_query(query: str) -> Dict[str, Any]:
    """
    Parse natural language search query and extract database search parameters.
    Returns a dict with search strategy and parameters.
    """
    query_lower = query.lower()
    
    # Check for table-specific queries
    table_patterns = {
        'customers': ['customer', 'client', 'buyer'],
        'orders': ['order', 'purchase', 'transaction'],
        'products': ['product', 'item', 'merchandise'],
        'employees': ['employee', 'staff', 'worker'],
    }
    
    target_tables = []
    for table, patterns in table_patterns.items():
        if any(pattern in query_lower for pattern in patterns):
            target_tables.append(table)
    
    # Extract potential filter conditions
    filters = []
    
    # Date patterns
    if 'today' in query_lower or 'recent' in query_lower:
        filters.append("date_filter:recent")
    elif 'last month' in query_lower:
        filters.append("date_filter:last_month")
    elif 'this year' in query_lower:
        filters.append("date_filter:this_year")
    
    # Numeric patterns (e.g., "over 1000", "more than 50")
    numeric_pattern = r'(over|more than|greater than|less than|under)\s+(\d+)'
    numeric_matches = re.findall(numeric_pattern, query_lower)
    for match in numeric_matches:
        filters.append(f"numeric:{match[0]}:{match[1]}")
    
    # Status patterns
    status_keywords = ['active', 'inactive', 'pending', 'completed', 'cancelled']
    for status in status_keywords:
        if status in query_lower:
            filters.append(f"status:{status}")
    
    return {
        'original_query': query,
        'tables': target_tables if target_tables else ['all'],
        'filters': filters,
        'search_terms': query.split()
    }

# ---------- Command-style parsing for ChatGPT two-tool constraint ----------
_TABLE_NAME_RE = r'[A-Za-z0-9_\.\[\]]+'

def _detect_command(query: str) -> Dict[str, Any]:
    """Detects high-level intent to map to list/describe/sample/execute SQL.
    Returns dict with keys: action, args.
    """
    q = query.strip()
    q_lower = q.lower()

    # Execute SQL when starting with SELECT/WITH
    if re.match(r'^\s*(select|with)\b', q_lower):
        return { 'action': 'execute_sql', 'args': { 'query': q } }

    # List tables
    if re.search(r'\b(list|show)\s+(all\s+)?tables\b', q_lower):
        return { 'action': 'list_tables', 'args': {} }

    # Describe table
    m = re.search(r'\b(describe|schema|structure|columns?)\s+(?:table\s+)?(' + _TABLE_NAME_RE + r')', q_lower, re.IGNORECASE)
    if m:
        table = m.group(2)
        return { 'action': 'describe_table', 'args': { 'table_name': table } }

    # Get sample
    m = re.search(r'\b(sample|examples?|top|get\s+sample)\b.*?(' + _TABLE_NAME_RE + r')', q_lower, re.IGNORECASE)
    if m:
        table = m.group(2)
        lim = 5
        m2 = re.search(r'\b(limit|top)\s+(\d{1,4})\b', q_lower)
        if m2:
            try:
                lim = max(1, min(1000, int(m2.group(2))))
            except Exception:
                lim = 5
        return { 'action': 'get_table_sample', 'args': { 'table_name': table, 'limit': lim } }

    # Fallback: generic search semantics
    return { 'action': 'generic_search', 'args': { 'original': q } }

def build_sql_from_search(search_params: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    Build SQL queries based on parsed search parameters.
    Returns list of (query, table_name) tuples.
    """
    queries = []
    
    if search_params['tables'] == ['all']:
        # Get all tables and search them
        try:
            config, connection_string = get_db_config()
            with connect(connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT TABLE_NAME 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_TYPE = 'BASE TABLE'
                    """)
                    tables = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get tables: {e}")
            tables = []
    else:
        tables = search_params['tables']
    
    # Build queries for each table
    for table in tables:
        # Start with basic SELECT
        query = f"SELECT TOP {MAX_SEARCH_RESULTS} * FROM {table}"
        where_conditions = []
        
        # Add filters
        for filter_str in search_params['filters']:
            if filter_str.startswith('date_filter:'):
                # Add date filtering if table has date columns
                if filter_str == 'date_filter:recent':
                    where_conditions.append("1=1")  # Placeholder for date logic
            elif filter_str.startswith('status:'):
                status = filter_str.split(':')[1]
                where_conditions.append(f"status = '{status}'")
        
        # Add text search conditions (simple LIKE for now)
        text_conditions = []
        for term in search_params['search_terms']:
            if len(term) > 2:  # Skip very short terms
                # This is simplified - in production, you'd check column types
                text_conditions.append(f"1=1")  # Placeholder for text search
        
        # Combine conditions
        if where_conditions or text_conditions:
            all_conditions = where_conditions + text_conditions
            query += " WHERE " + " AND ".join(all_conditions) if all_conditions else ""
        
        queries.append((query, table))
    
    return queries

# -----------------------------
# Local fallbacks when server_oauth helpers aren't importable
# -----------------------------
_SAFE_IDENT_RE = re.compile(r"^[A-Za-z0-9_]+$")

def _parse_schema_table(name: str) -> Tuple[str, str]:
    """Split a possibly schema-qualified table name into (schema, table). Defaults to dbo."""
    raw = name.strip().strip("[]")
    if "." in raw:
        schema, table = raw.split(".", 1)
    else:
        schema, table = "dbo", raw
    return schema.strip("[]"), table.strip("[]")

def _quote_ident(schema: str, table: str) -> str:
    # Very conservative quoting; optionally sanitize if weird chars
    s = schema or "dbo"
    t = table
    if not _SAFE_IDENT_RE.match(s) or not _SAFE_IDENT_RE.match(t):
        # Fallback by removing non word chars
        s = re.sub(r"[^A-Za-z0-9_]", "", s) or "dbo"
        t = re.sub(r"[^A-Za-z0-9_]", "", t)
    return f"[{s}].[{t}]"

def _describe_table_fallback(table_name: str) -> str:
    """Return column metadata for a table using INFORMATION_SCHEMA as JSON string."""
    try:
        schema, table = _parse_schema_table(table_name)
        _, cs = get_db_config()
        rows_out: List[Dict[str, Any]] = []
        with connect(cs) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT c.ORDINAL_POSITION,
                           c.COLUMN_NAME,
                           c.DATA_TYPE,
                           c.IS_NULLABLE,
                           c.CHARACTER_MAXIMUM_LENGTH,
                           c.NUMERIC_PRECISION,
                           c.NUMERIC_SCALE,
                           c.COLUMN_DEFAULT,
                           CASE WHEN tc.CONSTRAINT_TYPE = 'PRIMARY KEY' THEN 1 ELSE 0 END AS IS_PRIMARY_KEY
                    FROM INFORMATION_SCHEMA.COLUMNS c
                    LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                      ON kcu.TABLE_SCHEMA = c.TABLE_SCHEMA
                     AND kcu.TABLE_NAME = c.TABLE_NAME
                     AND kcu.COLUMN_NAME = c.COLUMN_NAME
                    LEFT JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                      ON tc.CONSTRAINT_SCHEMA = kcu.CONSTRAINT_SCHEMA
                     AND tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                     AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                    WHERE c.TABLE_SCHEMA = ? AND c.TABLE_NAME = ?
                    ORDER BY c.ORDINAL_POSITION
                    """,
                    (schema, table),
                )
                for r in cur.fetchall():
                    rows_out.append(
                        {
                            "ordinal": r[0],
                            "name": r[1],
                            "type": r[2],
                            "nullable": True if str(r[3]).upper() == "YES" else False,
                            "max_length": r[4],
                            "numeric_precision": r[5],
                            "numeric_scale": r[6],
                            "default": r[7],
                            "primary_key": bool(r[8]),
                        }
                    )
        result = {
            "table": table,
            "schema": schema,
            "qualified_name": _quote_ident(schema, table),
            "columns": rows_out,
        }
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error(f"Describe fallback failed for {table_name}: {e}")
        return json.dumps({"error": f"Failed to describe table {table_name}: {str(e)}"})

def _get_table_sample_fallback(table_name: str, limit: int = 5) -> str:
    """Return a small sample of rows from a table as JSON string."""
    try:
        schema, table = _parse_schema_table(table_name)
        limit = max(1, min(1000, int(limit or 5)))
        _, cs = get_db_config()
        qname = _quote_ident(schema, table)
        with connect(cs) as conn:
            with conn.cursor() as cur:
                # Note: TOP cannot be parameterized; limit is sanitized integer
                cur.execute(f"SELECT TOP {limit} * FROM {qname}")
                cols = [c[0] for c in (cur.description or [])]
                data_rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        return json.dumps(
            {
                "table": table,
                "schema": schema,
                "qualified_name": qname,
                "limit": limit,
                "rows": serialize_row_data(data_rows),
            },
            indent=2,
            default=str,
        )
    except Exception as e:
        logger.error(f"Sample fallback failed for {table_name}: {e}")
        return json.dumps({"error": f"Failed to sample table {table_name}: {str(e)}"})

def _execute_sql_readonly_fallback(query: str) -> str:
    """Execute a read-only SELECT/WITH query and return JSON rows. Reject mutating statements."""
    q = (query or "").strip()
    if not re.match(r"^(select|with)\b", q, re.IGNORECASE):
        return json.dumps({"error": "Only SELECT/WITH queries are allowed in read-only mode"})
    try:
        _, cs = get_db_config()
        with connect(cs) as conn:
            with conn.cursor() as cur:
                cur.execute(q)
                cols = [c[0] for c in (cur.description or [])]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return json.dumps({"rows": serialize_row_data(rows), "rowcount": len(rows)}, indent=2, default=str)
    except Exception as e:
        logger.error(f"Execute SQL fallback failed: {e}")
        return json.dumps({"error": f"Failed to execute query: {str(e)}"})

# ChatGPT-required tool implementations
def search_impl(query: str) -> str:
    """Search tool that multiplexes list/describe/sample/execute SQL into a single API.
    Returns a list of result IDs and brief previews; full content via fetch.
    """
    try:
        logger.info(f"Search query: {query}")

        intent = _detect_command(query)
        action = intent['action']
        args = intent['args']

        results: List[Dict[str, Any]] = []

        if action == 'list_tables':
            content = None
            if _list_tables_impl:
                content = _list_tables_impl()
            else:
                # Fallback: run a minimal query here
                try:
                    _, cs = get_db_config()
                    with connect(cs) as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT TABLE_SCHEMA, TABLE_NAME
                                FROM INFORMATION_SCHEMA.TABLES
                                WHERE TABLE_TYPE = 'BASE TABLE'
                                ORDER BY TABLE_SCHEMA, TABLE_NAME
                            """)
                            rows = cur.fetchall()
                            content = json.dumps({
                                'total_tables': len(rows),
                                'tables': [f"{r[0]}.{r[1]}" if r[0] != 'dbo' else r[1] for r in rows]
                            }, indent=2)
                except Exception as e:
                    content = json.dumps({'error': f'Failed to list tables: {str(e)}'})

            rid = 'list_tables'
            search_cache[rid] = { 'type': 'list_tables', 'data': content, 'cached_at': datetime.utcnow().isoformat() }
            results.append({ 'id': rid, 'preview': 'List of database tables' })

        elif action == 'describe_table':
            table = args['table_name']
            content = _describe_table_impl(table) if _describe_table_impl else _describe_table_fallback(table)
            rid = f"describe:{table}"
            search_cache[rid] = { 'type': 'describe_table', 'table': table, 'data': content, 'cached_at': datetime.utcnow().isoformat() }
            results.append({ 'id': rid, 'preview': f"Schema for {table}" })

        elif action == 'get_table_sample':
            table = args['table_name']
            limit = args.get('limit', 5)
            content = _get_table_sample_impl(table, limit) if _get_table_sample_impl else _get_table_sample_fallback(table, limit)
            rid = f"sample:{table}:{limit}"
            search_cache[rid] = { 'type': 'get_table_sample', 'table': table, 'limit': limit, 'data': content, 'cached_at': datetime.utcnow().isoformat() }
            results.append({ 'id': rid, 'preview': f"Sample of {table} (limit {limit})" })

        elif action == 'execute_sql':
            q = args['query']
            q_hash = hashlib.md5(q.encode()).hexdigest()[:12]
            content = _execute_sql_impl(q) if _execute_sql_impl else _execute_sql_readonly_fallback(q)
            rid = f"sql:{q_hash}"
            search_cache[rid] = { 'type': 'execute_sql', 'query': q, 'data': content, 'cached_at': datetime.utcnow().isoformat() }
            # Give a compact preview based on query start
            prev = (q.strip()[:80] + '...') if len(q.strip()) > 80 else q.strip()
            results.append({ 'id': rid, 'preview': f"Query result for: {prev}" })

        else:
            # Generic help to guide usage within ChatGPT’s two-tool restriction
            help_text = {
                'message': 'Specify one of: list tables, describe <table>, sample <table> limit N, or provide a SELECT query.'
            }
            rid = 'help'
            search_cache[rid] = { 'type': 'help', 'data': json.dumps(help_text), 'cached_at': datetime.utcnow().isoformat() }
            results.append({ 'id': rid, 'preview': 'Usage help' })

        return json.dumps({ 'query': query, 'total_results': len(results), 'results': results }, indent=2)
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return json.dumps({
            'error': f'Search failed: {str(e)}',
            'query': query
        })

def fetch_impl(record_id: str) -> str:
    """
    Implementation of fetch tool required by ChatGPT.
    Retrieves full record details by ID.
    """
    try:
        logger.info(f"Fetching record: {record_id}")
        
        # Check cache first (works for list/describe/sample/sql/help)
        if record_id in search_cache:
            cached = search_cache[record_id]
            cached_time = datetime.fromisoformat(cached['cached_at'])
            if (datetime.utcnow() - cached_time).total_seconds() < CACHE_TTL_SECONDS:
                # If cached content is an error, attempt to recompute with fallbacks
                data = cached.get('data')
                try:
                    parsed = json.loads(data) if isinstance(data, str) else data
                except Exception:
                    parsed = None
                if isinstance(parsed, dict) and parsed.get('error'):
                    ctype = cached.get('type')
                    if ctype == 'describe_table':
                        table = cached.get('table')
                        fresh = _describe_table_fallback(table)
                        search_cache[record_id]['data'] = fresh
                        return json.dumps({ 'id': record_id, 'data': fresh, 'source': 'fallback' }, indent=2)
                    if ctype == 'get_table_sample':
                        table = cached.get('table')
                        limit = cached.get('limit', 5)
                        fresh = _get_table_sample_fallback(table, limit)
                        search_cache[record_id]['data'] = fresh
                        return json.dumps({ 'id': record_id, 'data': fresh, 'source': 'fallback' }, indent=2)
                    if ctype == 'execute_sql':
                        q = cached.get('query', '')
                        fresh = _execute_sql_readonly_fallback(q)
                        search_cache[record_id]['data'] = fresh
                        return json.dumps({ 'id': record_id, 'data': fresh, 'source': 'fallback' }, indent=2)
                return json.dumps({ 'id': record_id, 'data': data, 'source': 'cache' }, indent=2)
        
        # Handle aggregated IDs
        if record_id == 'list_tables':
            return _list_tables_impl() if _list_tables_impl else json.dumps({'error': 'list_tables not available'})

        if record_id.startswith('describe:'):
            table = record_id.split(':', 1)[1]
            return _describe_table_impl(table) if _describe_table_impl else _describe_table_fallback(table)

        if record_id.startswith('sample:'):
            _, table, limit_str = record_id.split(':', 2)
            try:
                lim = int(limit_str)
            except Exception:
                lim = 5
            return _get_table_sample_impl(table, lim) if _get_table_sample_impl else _get_table_sample_fallback(table, lim)

        if record_id.startswith('sql:'):
            item = search_cache.get(record_id, {})
            q = item.get('query')
            if q and _execute_sql_impl:
                return _execute_sql_impl(q)
            return json.dumps({'error': 'query not found in cache; resubmit via search'})

        # Backward-compatible row IDs (table:<id>) if any were produced
        parts = record_id.split(':', 1)
        if len(parts) != 2:
            return json.dumps({'error': f'Invalid record ID: {record_id}'})
        table_name, identifier = parts
        
        # Try to fetch from database
        config, connection_string = get_db_config()
        
        with connect(connection_string) as conn:
            with conn.cursor() as cursor:
                # Try to find by common ID columns
                for id_column in ['id', 'ID', 'Id', 'pk', 'PK']:
                    try:
                        query = f"SELECT * FROM {table_name} WHERE {id_column} = ?"
                        cursor.execute(query, (identifier,))
                        
                        if cursor.description:
                            columns = [column[0] for column in cursor.description]
                            row = cursor.fetchone()
                            
                            if row:
                                record = dict(zip(columns, row))
                                
                                # Update cache
                                search_cache[record_id] = {
                                    'table': table_name,
                                    'data': serialize_row_data(record),
                                    'cached_at': datetime.utcnow().isoformat()
                                }
                                
                                result = {
                                    'id': record_id,
                                    'table': table_name,
                                    'data': serialize_row_data(record),
                                    'source': 'database'
                                }
                                
                                return json.dumps(result, indent=2, default=str)
                    except:
                        continue
                
                # If not found by ID, return error
                return json.dumps({
                    'error': f'Record not found: {record_id}',
                    'id': record_id
                })
                
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        return json.dumps({
            'error': f'Fetch failed: {str(e)}',
            'id': record_id
        })

# OAuth endpoints (mostly unchanged from original)
async def oauth_authorization_server(request: Request):
    """OAuth authorization server discovery endpoint."""
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("host", "data.forensic-bot.com")
    base_url = f"{forwarded_proto}://{host}"
    
    # Get the environment path if configured (prefer proxy header)
    env_path = request.headers.get("x-environment-path") or os.getenv("ENVIRONMENT_PATH", "")
    if env_path:
        base_url = f"{base_url}{env_path}"
    
    return JSONResponse({
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "registration_endpoint": f"{base_url}/register",
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"]
    })

async def openid_configuration(request: Request):
    """OpenID Connect discovery endpoint (alias to oauth-authorization-server metadata)."""
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("host", "data.forensic-bot.com")
    base_url = f"{forwarded_proto}://{host}"

    env_path = request.headers.get("x-environment-path") or os.getenv("ENVIRONMENT_PATH", "")
    if env_path:
        base_url = f"{base_url}{env_path}"

    # Provide a basic OIDC discovery doc mapping to our OAuth endpoints
    return JSONResponse({
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "registration_endpoint": f"{base_url}/register",
        "jwks_uri": f"{base_url}/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "scopes_supported": ["mcp:read"],
        "claims_supported": ["sub"],
    })

async def oauth_protected_resource(request: Request):
    """OAuth protected resource discovery endpoint."""
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("host", "data.forensic-bot.com")
    base_url = f"{forwarded_proto}://{host}"
    
    env_path = request.headers.get("x-environment-path") or os.getenv("ENVIRONMENT_PATH", "")
    if env_path:
        base_url = f"{base_url}{env_path}"
    
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
        "redirect_uris": body.get("redirect_uris", ["https://chatgpt.com/backend-api/aip/connectors/links/oauth/callback"]),
        "client_name": body.get("client_name", "ChatGPT")
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
        "expires_at": (_now_utc() + timedelta(hours=1)).isoformat()
    }
    
    logger.info(f"Issued tokens for client: {data.get('client_id', 'unknown')}")
    
    return JSONResponse({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": refresh_token,
        "scope": "mcp:read"
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
            "mcp_version": "2025-06-18",
            "tools": ["search", "fetch"],
            "compatible_with": "ChatGPT Deep Research"
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

async def handle_sse_get(request: Request):
    """Handle GET requests to /sse for compatibility probes.
    Returns 200 with SSE headers but no stream until POST is used.
    """
    logger.info("Handling GET request for /sse (probe)")
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

async def handle_sse_options(request: Request):
    """Handle OPTIONS preflight requests to /sse."""
    logger.info("Handling OPTIONS request for /sse (preflight)")
    return Response(
        content="",
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept",
            "Access-Control-Max-Age": "86400"
        }
    )

async def handle_sse_post(request: Request):
    """Handle POST requests to /sse - Main MCP handler for ChatGPT."""
    logger.info("Handling POST request to /sse")
    body: Optional[Dict[str, Any]] = None
    # Require OAuth bearer token unless explicitly allowed via ALLOW_UNAUTH_* flags
    token = _extract_bearer_token(request)
    if not token or not _is_token_valid(token):
        # Check if method is allowed without auth based on env flags
        try:
            body = await request.json()
            method_name = body.get("method")
        except Exception:
            body = {}
            method_name = None

        allowed_unauth: set = set()
        if ALLOW_UNAUTH_METHODS:
            allowed_unauth.update({
                "initialize",
                "notifications/initialized",
                "tools/list",
                "resources/list",
                "prompts/list",
            })
        if ALLOW_UNAUTH_TOOLS_CALL:
            allowed_unauth.add("tools/call")

        if method_name not in allowed_unauth:
            logger.warning(f"Unauthorized /sse access attempt: missing or invalid token (chatgpt); method={method_name}")
            return JSONResponse({"error": "unauthorized"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})

    try:
        # body may be already parsed above
        if not body:
            try:
                body = await request.json()
            except Exception:
                body = {}
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
                        "name": "MSSQL MCP Server for ChatGPT",
                        "version": "1.0.0",
                        "description": "Database search and fetch for ChatGPT Deep Research"
                    }
                }
            }
            
        elif method == "notifications/initialized":
            logger.info("Received initialized notification")
            return Response(content="", status_code=204)
            
        elif method == "tools/list":
            # ChatGPT requires exactly these two tools
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "search",
                            "title": "Search Database",
                            "description": "Search the MSSQL database for records matching a query. Returns a list of record IDs with previews. Supports natural language queries like 'find all customers from New York' or 'show recent orders over $1000'.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "Natural language search query to find database records"
                                    }
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "fetch",
                            "title": "Fetch Record Details",
                            "description": "Retrieve complete details for a specific database record using its ID. IDs are obtained from the search tool results.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "description": "Record ID obtained from search results (format: table:identifier)"
                                    }
                                },
                                "required": ["id"]
                            }
                        }
                    ]
                }
            }
            
        elif method == "tools/call":
            params = body.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            logger.info(f"Tool call: {tool_name} with args: {arguments}")
            
            # Execute the appropriate tool
            if tool_name == "search":
                result = search_impl(arguments.get("query", ""))
            elif tool_name == "fetch":
                result = fetch_impl(arguments.get("id", ""))
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
    Route("/.well-known/openid-configuration", openid_configuration, methods=["GET"]),
        
        # OAuth flow endpoints
        Route("/register", register, methods=["POST"]),
        Route("/authorize", authorize, methods=["GET", "POST"]),
        Route("/token", token, methods=["POST"]),
        
        # Health check
        Route("/health", health_check, methods=["GET"]),
        
        # SSE endpoints
    Route("/sse", handle_sse_head, methods=["HEAD"]),
    Route("/sse", handle_sse_get, methods=["GET"]),
    Route("/sse", handle_sse_options, methods=["OPTIONS"]),
    Route("/sse", handle_sse_post, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("Starting ChatGPT-Compatible MSSQL MCP Server")
    logger.info("=" * 70)
    logger.info(f"Configuration:")
    logger.info(f"  Protocol: MCP 2025-06-18")
    logger.info(f"  Tools: search, fetch (ChatGPT Deep Research compatible)")
    logger.info(f"  Read-Only Mode: {READ_ONLY_MODE}")
    logger.info(f"  Max Search Results: {MAX_SEARCH_RESULTS}")
    logger.info(f"  Cache TTL: {CACHE_TTL_SECONDS} seconds")
    logger.info(f"  MSSQL Host: {os.getenv('MSSQL_HOST')}")
    logger.info(f"  MSSQL Database: {os.getenv('MSSQL_DATABASE')}")
    logger.info("=" * 70)
    logger.info("ChatGPT Integration:")
    logger.info("  1. Add as custom connector in ChatGPT settings")
    logger.info("  2. Use with Deep Research feature")
    logger.info("  3. OAuth authentication required")
    logger.info("=" * 70)
    logger.info("Server running on http://0.0.0.0:8008")
    logger.info("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8008, log_level="info")