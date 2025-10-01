# Extended Technical Guide: Building an MCP Server for ChatGPT Database Integration

## Table of Contents
- [Part 1: Introduction and Concepts (0:00-5:00)](#part-1-introduction-and-concepts-000-500)
- [Part 2: Architecture and Design (5:00-15:00)](#part-2-architecture-and-design-500-1500)
- [Part 3: Security Implementation (15:00-25:00)](#part-3-security-implementation-1500-2500)
- [Part 4: Development & Implementation (25:00-40:00)](#part-4-development--implementation-2500-4000)
- [Part 5: Deployment & Infrastructure (40:00-55:00)](#part-5-deployment--infrastructure-4000-5500)
- [Part 6: Testing and Validation (55:00-65:00)](#part-6-testing-and-validation-5500-6500)
- [Part 7: Production Operations (65:00-80:00)](#part-7-production-operations-6500-8000)
- [Part 8: Advanced Topics and Best Practices (80:00-90:00)](#part-8-advanced-topics-and-best-practices-8000-9000)

---

## Part 1: Introduction and Concepts (0:00-5:00)

### 0:00 — Opening and Hook
**"Welcome to this comprehensive technical guide on building a production-ready MCP server that securely connects your Microsoft SQL Server database with ChatGPT's Deep Research feature."**

In this extended tutorial, you'll learn to build an enterprise-grade bridge between your database and AI, implementing industry-standard security with OAuth 2.0, TLS encryption, and containerized deployment specifically optimized for ChatGPT integration.

### 0:30 — What We're Building
By the end of this guide, you'll have:
- A fully functional MCP (Model Context Protocol) server for ChatGPT
- Secure OAuth 2.0 authentication with dynamic client registration
- Server-Sent Events (SSE) for bidirectional real-time communication
- Production-ready deployment with Docker, NGINX, and Let's Encrypt
- Specialized tools (`search` and `fetch`) optimized for ChatGPT's Deep Research
- Complete monitoring, logging, and troubleshooting capabilities

### 1:00 — Why This Matters

**Traditional Approach Problems:**
- Manual data exports (time-consuming, error-prone)
- Copy-paste workflows (no audit trail)
- Stale data (snapshots become outdated)
- Security risks (credentials in emails/documents)
- No access control (all-or-nothing approach)
- ChatGPT cannot access real-time database information

**MCP Server Benefits:**
- **Real-Time Access**: Live database queries through natural language via ChatGPT
- **Security**: OAuth 2.0 tokens, TLS encryption, short-lived credentials
- **Audit Trail**: Every query logged with user attribution
- **Access Control**: Granular permissions (read-only, specific tables, etc.)
- **Scalability**: Handle multiple concurrent ChatGPT sessions
- **Deep Research Integration**: Purpose-built for ChatGPT's advanced research capabilities

### 2:00 — ChatGPT-Specific Architecture

**ChatGPT Deep Research Features:**
- Multi-step research queries
- Iterative data exploration
- Result caching and record fetching
- Natural language to SQL translation
- Structured output formatting

**Key Differences from Claude.ai:**
```
ChatGPT Connector          vs          Claude.ai Connector
├── search tool                        ├── list_tables
├── fetch tool                         ├── describe_table
├── Result caching                     ├── execute_sql
├── ID-based retrieval                 ├── get_table_sample
└── Deep Research optimized            └── Direct tool mapping
```

### 3:00 — Model Context Protocol (MCP) Overview

**What is MCP?**
- Specification: `2025-06-18` version
- Purpose: Standardized way for AI models to interact with external systems
- Transport: Server-Sent Events (SSE) for persistent connections
- Format: JSON-RPC 2.0 messages
- Security: OAuth 2.0 bearer tokens

**MCP Request Flow:**
```
ChatGPT → initialize → Server responds with capabilities
ChatGPT → tools/list → Server describes available tools
ChatGPT → tools/call → Server executes and returns results
```

### 4:00 — Server-Sent Events (SSE) Explained

**Why SSE for ChatGPT?**
- **Persistent Connection**: Keeps channel open for multiple requests
- **Unidirectional**: Server→Client streaming (perfect for AI responses)
- **HTTP-based**: Works through firewalls and proxies
- **Automatic Reconnection**: Built-in retry mechanism
- **ChatGPT Compatible**: Native SSE support in Deep Research

**SSE vs WebSockets:**
```
SSE (Our Choice)                WebSockets
├── Simpler implementation      ├── Full duplex
├── Automatic reconnection      ├── Lower overhead
├── HTTP/1.1 compatible         ├── Requires upgrade
├── Native browser support      ├── More complex setup
└── Perfect for AI queries      └── Better for chat apps
```

---

## Part 2: Architecture and Design (5:00-15:00)

### 5:00 — System Architecture Overview

**Three-Tier Architecture:**
```
┌─────────────┐         HTTPS 443        ┌─────────────┐
│   ChatGPT   │◄────────────────────────►│    NGINX    │
│ (Deep Res.) │      SSL/TLS, CORS       │   Reverse   │
└─────────────┘                           │    Proxy    │
                                          └──────┬──────┘
                                                 │ HTTP 8008
                                                 │ SSE Proxy
                                          ┌──────▼──────┐
                                          │     MCP     │
                                          │   Server    │
                                          │  (Python)   │
                                          └──────┬──────┘
                                                 │ ODBC
                                                 │
                                          ┌──────▼──────┐
                                          │  SQL Server │
                                          │  Database   │
                                          └─────────────┘
```

**Component Responsibilities:**

**1. NGINX (Frontend)**
- SSL/TLS termination with Let's Encrypt certificates
- Request routing with path-based scoping (`/chatgpt/*`)
- SSE-optimized configuration (no buffering, long timeouts)
- CORS headers for ChatGPT domain
- Security headers (HSTS, X-Frame-Options, etc.)
- Rate limiting and DDoS protection

**2. MCP Server (Application)**
- OAuth 2.0 server implementation
- MCP protocol handler (initialize, tools/list, tools/call)
- Tool implementations (search, fetch)
- Database connection pooling
- Request validation and sanitization
- Logging and audit trail
- Token management and validation

**3. SQL Server (Data)**
- Data storage and retrieval
- Query execution with read-only application intent
- Row-level security (optional)
- Audit logging (optional)

### 6:30 — Path-Based Routing Strategy

**Why `/chatgpt/*` Scope?**
- Isolates ChatGPT traffic from other services
- Enables multi-tenant deployments (different scopes for different clients)
- Simplifies firewall rules and monitoring
- Allows scope-specific configuration
- Clear separation in logs and metrics

**NGINX Routing Configuration:**
```nginx
# Root-level discovery for initial ChatGPT probes
location ~ ^/\.well-known/(oauth-authorization-server|openid-configuration|oauth-protected-resource)$ {
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_set_header X-Environment-Path /chatgpt;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Host $host;
}

# Scoped ChatGPT endpoints
location ~ ^/chatgpt/(.*)$ {
    # Strip /chatgpt prefix before passing to server
    rewrite ^/chatgpt(/.*)$ $1 break;
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_set_header X-Environment-Path /chatgpt;
    
    # SSE-specific settings
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 3600s;
    proxy_connect_timeout 60s;
    proxy_send_timeout 3600s;
    
    # Headers
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding off;
}
```

**Server Uses X-Environment-Path:**
```python
def get_base_url(request: Request) -> str:
    """Build base URL with environment path from proxy header."""
    env_path = request.headers.get("x-environment-path", "")
    proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("host", "data.forensic-bot.com")
    
    base = f"{proto}://{host}"
    if env_path:
        base += env_path
    
    return base  # e.g., "https://data.forensic-bot.com/chatgpt"
```

### 8:00 — Tool Architecture for ChatGPT

**ChatGPT's Tool Requirements:**
Unlike Claude.ai which uses multiple specific tools, ChatGPT Deep Research expects:
1. **Broad-purpose tools** that can handle multiple operations
2. **Intelligent parameter interpretation**
3. **Result caching** for iterative exploration
4. **ID-based record retrieval**

**Tool Design:**

#### 1. `search` Tool (Multi-Purpose)
```python
{
    "name": "search",
    "description": """Multi-purpose database search supporting:
    - List all tables: query="list tables"
    - Describe table schema: query="describe TableName"
    - Sample data: query="sample TableName limit 10"
    - Execute SQL: query="SELECT * FROM Table WHERE condition"
    """,
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query or SQL statement"
            }
        },
        "required": ["query"]
    }
}
```

**Search Implementation Logic:**
```python
def handle_search(query: str) -> str:
    """
    Intelligently route query to appropriate handler:
    1. Check for "list tables" → call list_tables_impl()
    2. Check for "describe TableName" → call describe_table_impl()
    3. Check for "sample TableName" → call get_table_sample_impl()
    4. Otherwise → call execute_sql_impl()
    
    Cache results with TTL for fetch tool.
    """
    query_lower = query.lower().strip()
    
    # List tables
    if query_lower == "list tables":
        return list_tables_impl()
    
    # Describe table
    if query_lower.startswith("describe "):
        table_name = query.split("describe ", 1)[1].strip()
        return describe_table_impl(table_name)
    
    # Sample data
    if query_lower.startswith("sample "):
        # Extract table name and limit
        parts = query.split("sample ", 1)[1].strip().split()
        table_name = parts[0]
        limit = 10
        if len(parts) > 2 and parts[1].lower() == "limit":
            limit = int(parts[2])
        return get_table_sample_impl(table_name, limit)
    
    # Default: execute as SQL
    return execute_sql_impl(query)
```

#### 2. `fetch` Tool (Record Retrieval)
```python
{
    "name": "fetch",
    "description": """Retrieve specific records by ID from cached search results.
    Use IDs returned by the search tool.""",
    "inputSchema": {
        "type": "object",
        "properties": {
            "record_id": {
                "type": "string",
                "description": "Record ID from search results"
            }
        },
        "required": ["record_id"]
    }
}
```

**Fetch Implementation:**
```python
def handle_fetch(record_id: str) -> str:
    """
    Retrieve record from:
    1. Memory cache (if recently searched)
    2. Database (if cache miss)
    
    Returns full record details.
    """
    # Check cache first
    if record_id in search_cache:
        cached = search_cache[record_id]
        # Verify TTL
        if is_cache_valid(cached['cached_at']):
            return json.dumps({
                'id': record_id,
                'data': cached['data'],
                'source': 'cache'
            })
    
    # Cache miss - query database
    # Try to extract table and ID from record_id format: "TableName_123"
    table, pk_value = parse_record_id(record_id)
    return fetch_from_database(table, pk_value)
```

### 10:00 — Result Caching Strategy

**Why Caching for ChatGPT?**
- Deep Research performs iterative queries
- Fetches individual records after initial search
- Reduces database load
- Improves response time for follow-up queries

**Cache Structure:**
```python
search_cache: Dict[str, Any] = {}

# Cache entry format:
{
    "TableName_123": {
        "table": "Customers",
        "data": {
            "CustomerID": 123,
            "Name": "Acme Corp",
            "Email": "contact@acme.com"
        },
        "cached_at": "2025-10-01T12:00:00.000000"
    }
}
```

**Cache Management:**
```python
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

def is_cache_valid(cached_at: str) -> bool:
    """Check if cache entry is still valid based on TTL."""
    cached_time = datetime.fromisoformat(cached_at)
    age_seconds = (datetime.utcnow() - cached_time).total_seconds()
    return age_seconds < CACHE_TTL_SECONDS

def clean_expired_cache():
    """Remove expired entries from cache."""
    now = datetime.utcnow()
    expired_keys = []
    
    for key, value in search_cache.items():
        cached_time = datetime.fromisoformat(value['cached_at'])
        if (now - cached_time).total_seconds() >= CACHE_TTL_SECONDS:
            expired_keys.append(key)
    
    for key in expired_keys:
        del search_cache[key]
```

### 12:00 — OAuth Flow Specific to ChatGPT

**ChatGPT OAuth Discovery:**
```
1. ChatGPT probes: GET /.well-known/oauth-authorization-server
2. Server responds with issuer: https://domain.com/chatgpt
3. ChatGPT follows scoped endpoints:
   - POST /chatgpt/register → client credentials
   - GET /chatgpt/authorize → authorization code
   - POST /chatgpt/token → bearer token
4. ChatGPT uses token for all /chatgpt/sse requests
```

**Key Differences from Claude.ai:**
- ChatGPT requires both root-level and scoped discovery
- Uses `chatgpt.com` as redirect URI
- May retry authorization multiple times
- Expects consistent issuer URLs

### 14:00 — Environment Path Scoping

**Multi-Scope Architecture:**
```
Production Setup:
├── /chatgpt/* → mcp-server-chatgpt:8008 (ChatGPT scope)
├── /claude/*  → mcp-server-claude:8009 (Claude.ai scope)
└── /demo/*    → mcp-server-demo:8010 (Demo scope)
```

**Benefits:**
- Separate OAuth issuers per scope
- Independent token storage
- Scope-specific logging
- Different database users per scope
- Isolated security policies

---

## Part 3: Security Implementation (15:00-25:00)

### 15:00 — OAuth 2.0 for ChatGPT

**ChatGPT OAuth Flow:**

```
┌──────────┐                               ┌──────────┐
│ ChatGPT  │                               │   MCP    │
│   Deep   │                               │  Server  │
│ Research │                               └────┬─────┘
└────┬─────┘                                    │
     │                                          │
     │  1. Client Registration                  │
     ├─────────────────────────────────────────>│
     │     POST /chatgpt/register               │
     │     {client_name, redirect_uris}         │
     │                                          │
     │<─────────────────────────────────────────┤
     │     200 OK                               │
     │     {client_id, client_secret}           │
     │                                          │
     │  2. Authorization Request                │
     ├─────────────────────────────────────────>│
     │     GET /chatgpt/authorize?              │
     │       client_id=xxx&                     │
     │       redirect_uri=chatgpt.com/callback& │
     │       state=random                       │
     │                                          │
     │<─────────────────────────────────────────┤
     │     302 Redirect                         │
     │     Location: redirect_uri?              │
     │       code=auth_code&state=random        │
     │                                          │
     │  3. Token Exchange                       │
     ├─────────────────────────────────────────>│
     │     POST /chatgpt/token                  │
     │     grant_type=authorization_code&       │
     │     code=auth_code&                      │
     │     client_id=xxx&                       │
     │     client_secret=yyy                    │
     │                                          │
     │<─────────────────────────────────────────┤
     │     200 OK                               │
     │     {                                    │
     │       access_token: "eyJ...",            │
     │       token_type: "Bearer",              │
     │       expires_in: 3600,                  │
     │       refresh_token: "refresh..."        │
     │     }                                    │
     │                                          │
     │  4. Authenticated SSE Connection         │
     ├─────────────────────────────────────────>│
     │     POST /chatgpt/sse                    │
     │     Authorization: Bearer eyJ...         │
     │                                          │
     │<═════════════════════════════════════════│
     │     SSE Stream (persistent)              │
     │                                          │
```

### 17:00 — Token Management

**Token Storage:**
```python
# In-memory token store (production should use Redis)
valid_tokens: Dict[str, Dict[str, Any]] = {}

# Token structure:
{
    "bearer_token_abc123": {
        "client_id": "client_xyz",
        "scope": "mcp:read",
        "issued_at": "2025-10-01T12:00:00",
        "expires_at": "2025-10-01T13:00:00",
        "refresh_token": "refresh_token_def456"
    }
}
```

**Token Validation:**
```python
def _is_token_valid(token: str) -> bool:
    """
    Validate bearer token:
    1. Check if token exists in storage
    2. Verify expiration time
    3. Return True if valid, False otherwise
    """
    data = valid_tokens.get(token)
    if not data:
        logger.warning(f"Token not found: {token[:10]}...")
        return False
    
    try:
        expires_at = datetime.fromisoformat(data.get("expires_at"))
    except Exception as e:
        logger.error(f"Invalid expiration format: {e}")
        return False
    
    is_valid = datetime.utcnow() < expires_at
    if not is_valid:
        logger.info(f"Token expired: {token[:10]}...")
    
    return is_valid

def _extract_bearer_token(request: Request) -> Optional[str]:
    """
    Extract bearer token from Authorization header.
    Format: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    return auth.split(" ", 1)[1].strip()
```

### 19:00 — Redirect URI Validation

**Security Critical: Prevent Open Redirects**
```python
ALLOWED_REDIRECT_HOSTS = [h.strip().lower() for h in os.getenv(
    "ALLOWED_REDIRECT_HOSTS",
    "chatgpt.com,openai.com,claude.ai,anthropic.com"
).split(",") if h.strip()]

def _is_host_allowed(redirect_uri: Optional[str]) -> bool:
    """
    Validate redirect URI to prevent authorization code interception.
    
    Security considerations:
    - Must be exact domain match or subdomain
    - Case-insensitive comparison
    - Prevents open redirect attacks
    """
    if not redirect_uri:
        return False
    
    try:
        parsed = urlparse(redirect_uri)
        host = parsed.hostname or ""
        host = host.lower()
        
        # Check exact match or subdomain
        return any(
            host == h or host.endswith("." + h)
            for h in ALLOWED_REDIRECT_HOSTS
        )
    except Exception as e:
        logger.error(f"Failed to parse redirect URI: {e}")
        return False
```

**Example Validations:**
```python
# Valid redirects:
_is_host_allowed("https://chatgpt.com/callback")  # True
_is_host_allowed("https://www.chatgpt.com/callback")  # True
_is_host_allowed("https://openai.com/oauth")  # True

# Invalid redirects:
_is_host_allowed("https://evil.com/callback")  # False
_is_host_allowed("https://chatgpt.com.evil.com/callback")  # False
_is_host_allowed("https://notchatgpt.com/callback")  # False
```

### 21:00 — TLS Configuration

**NGINX SSL Setup:**
```nginx
server {
    listen 443 ssl http2;
    server_name data.forensic-bot.com;
    
    # Let's Encrypt certificates
    ssl_certificate /etc/letsencrypt/live/data.forensic-bot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/data.forensic-bot.com/privkey.pem;
    
    # Modern TLS configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    
    # SSL session caching
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/data.forensic-bot.com/chain.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

### 23:00 — Database Security (Read-Only Mode)

**Why Read-Only for ChatGPT?**
- Prevents accidental data modification
- Reduces attack surface
- Satisfies compliance requirements
- Safe for AI-driven queries

**Implementation:**
```python
READ_ONLY_MODE = os.getenv("READ_ONLY_MODE", "true").lower() == "true"

def get_db_config():
    """Configure database connection with read-only application intent."""
    config = {
        "driver": os.getenv("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server"),
        "server": os.getenv("MSSQL_HOST"),
        "user": os.getenv("MSSQL_USER"),
        "password": os.getenv("MSSQL_PASSWORD"),
        "database": os.getenv("MSSQL_DATABASE"),
        "application_intent": "ReadOnly" if READ_ONLY_MODE else "ReadWrite"
    }
    
    connection_string = (
        f"Driver={{{config['driver']}}};Server={config['server']};"
        f"UID={config['user']};PWD={config['password']};"
        f"Database={config['database']};"
        f"ApplicationIntent={config['application_intent']};"
        f"TrustServerCertificate=yes;"
    )
    
    return config, connection_string

def execute_sql_impl(query: str) -> str:
    """
    Execute SQL with read-only safety checks.
    """
    if READ_ONLY_MODE:
        # Block write operations
        dangerous_keywords = ["insert", "update", "delete", "drop", "alter", 
                             "create", "truncate", "grant", "revoke"]
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in dangerous_keywords):
            return json.dumps({
                "error": "Write operations not allowed in read-only mode",
                "query": query
            })
    
    # Execute query...
```

### 24:00 — IP Whitelisting for ChatGPT

**ChatGPT IP Ranges (as of October 2025):**
```
23.102.140.112/28
13.66.11.96/28
23.98.142.176/28
40.84.180.224/28
76.16.33.0/24
128.252.147.0/24
```

**NGINX IP Restriction:**
```nginx
# Define allowed IPs
geo $chatgpt_allowed {
    default 0;
    23.102.140.112/28 1;
    13.66.11.96/28 1;
    23.98.142.176/28 1;
    40.84.180.224/28 1;
    76.16.33.0/24 1;
    128.252.147.0/24 1;
}

# Apply to ChatGPT endpoints
location ~ ^/chatgpt/ {
    if ($chatgpt_allowed = 0) {
        return 403 "Access denied - IP not whitelisted";
    }
    # ... rest of configuration
}
```

**Important:** OpenAI may update these IP ranges without notice. Monitor logs for legitimate blocked requests.

---

## Part 4: Development & Implementation (25:00-40:00)

### 25:00 — Project Structure

```
mssql-mcp-server/
├── server_chatgpt.py           # ChatGPT-specific MCP server
├── server_oauth.py             # Shared OAuth/DB logic
├── requirements.txt            # Python dependencies
├── Dockerfile.chatgpt          # ChatGPT server container
├── docker-compose.yml          # Development orchestration
├── docker-compose.prod.yml     # Production orchestration
├── .env                        # Environment variables (gitignored)
├── .env.example                # Environment template
├── nginx/
│   ├── nginx.conf              # Main NGINX config
│   └── conf.d/
│       └── default.conf        # Site configuration with ChatGPT routing
├── certbot/
│   ├── conf/                   # SSL certificates
│   └── www/                    # ACME challenge files
├── logs/
│   ├── nginx/                  # NGINX access/error logs
│   └── mcp/                    # Application logs
├── docs/
│   ├── chatgpt-connector-setup.md
│   ├── explanation_chatgpt_en.md  # This document
│   ├── security.md
│   └── architecture.svg
├── tests/
│   ├── test_chatgpt_oauth.py
│   ├── test_tools.py
│   └── test_search_fetch.py
└── scripts/
    ├── setup-letsencrypt.sh
    ├── monitor-chatgpt.sh
    └── cache-cleanup.sh
```

### 26:30 — Core Dependencies

**requirements.txt:**
```txt
# ASGI Framework
starlette==0.35.1
uvicorn[standard]==0.27.0

# Database
pyodbc==5.0.1

# Environment
python-dotenv==1.0.0

# Development/Testing
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.12.1
mypy==1.7.1
```

### 27:00 — Database Configuration

**Connection Management:**
```python
from typing import Tuple, Dict, Any
import os
import pyodbc
from dotenv import load_dotenv

load_dotenv(".env")

def get_db_config() -> Tuple[Dict[str, str], str]:
    """
    Build ODBC connection string from environment variables.
    
    Returns:
        Tuple of (config dict, connection string)
    """
    config = {
        "driver": os.getenv("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server"),
        "server": os.getenv("MSSQL_HOST", "localhost"),
        "user": os.getenv("MSSQL_USER"),
        "password": os.getenv("MSSQL_PASSWORD"),
        "database": os.getenv("MSSQL_DATABASE"),
        "trusted_server_certificate": os.getenv("TrustServerCertificate", "yes"),
        "application_intent": "ReadOnly" if READ_ONLY_MODE else "ReadWrite"
    }
    
    # Validate required fields
    if not all([config["user"], config["password"], config["database"]]):
        raise ValueError("Missing required database configuration")
    
    # Build connection string
    connection_string = (
        f"Driver={{{config['driver']}}};Server={config['server']};"
        f"UID={config['user']};PWD={config['password']};"
        f"Database={config['database']};"
        f"TrustServerCertificate={config['trusted_server_certificate']};"
        f"ApplicationIntent={config['application_intent']};"
    )
    
    return config, connection_string

def test_connection() -> bool:
    """Test database connectivity."""
    try:
        _, conn_string = get_db_config()
        conn = pyodbc.connect(conn_string)
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"Connected to: {version}")
        conn.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
```

### 28:30 — Data Serialization

**Handling SQL Server Data Types:**
```python
from decimal import Decimal
from datetime import datetime, date
import base64
import json

def serialize_row_data(data):
    """
    Convert pyodbc Row objects and non-JSON types to JSON-compatible format.
    
    Handles:
    - Decimal → float
    - datetime → ISO 8601 string
    - date → ISO 8601 string
    - bytes → base64 string
    - None → null
    
    Args:
        data: Database row value
        
    Returns:
        JSON-serializable value
    """
    if data is None:
        return None
    elif isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, date):
        return data.isoformat()
    elif isinstance(data, bytes):
        return base64.b64encode(data).decode('utf-8')
    elif isinstance(data, (int, float, str, bool)):
        return data
    else:
        # Fallback: convert to string
        return str(data)

def serialize_results(rows) -> List[Dict[str, Any]]:
    """
    Serialize entire result set.
    
    Args:
        rows: List of pyodbc Row objects
        
    Returns:
        List of dictionaries with serialized values
    """
    if not rows:
        return []
    
    # Get column names from first row
    columns = list(rows[0].cursor_description)
    column_names = [col[0] for col in columns]
    
    # Serialize each row
    serialized = []
    for row in rows:
        row_dict = {}
        for col_name, value in zip(column_names, row):
            row_dict[col_name] = serialize_row_data(value)
        serialized.append(row_dict)
    
    return serialized
```

### 30:00 — Search Tool Implementation

**Complete Search Handler:**
```python
def handle_search(query: str) -> str:
    """
    Multi-purpose search tool for ChatGPT.
    
    Supports:
    1. List tables: "list tables"
    2. Describe table: "describe TableName"
    3. Sample data: "sample TableName limit 10"
    4. Execute SQL: Any valid SELECT statement
    
    Results are cached for fetch tool.
    
    Args:
        query: Natural language query or SQL statement
        
    Returns:
        JSON string with results
    """
    try:
        query_lower = query.lower().strip()
        
        # Route 1: List all tables
        if query_lower == "list tables":
            result = list_tables_impl()
            logger.info("Listed tables")
            return result
        
        # Route 2: Describe table schema
        if query_lower.startswith("describe "):
            table_name = query.split("describe ", 1)[1].strip()
            result = describe_table_impl(table_name)
            logger.info(f"Described table: {table_name}")
            return result
        
        # Route 3: Sample data from table
        if query_lower.startswith("sample "):
            # Parse: "sample TableName limit 10"
            parts = query.split("sample ", 1)[1].strip().split()
            table_name = parts[0]
            limit = 10  # default
            
            if len(parts) > 2 and parts[1].lower() == "limit":
                try:
                    limit = int(parts[2])
                    limit = min(limit, MAX_SEARCH_RESULTS)  # enforce max
                except ValueError:
                    pass
            
            result = get_table_sample_impl(table_name, limit)
            logger.info(f"Sampled {table_name} with limit {limit}")
            
            # Cache results for fetch
            cache_search_results(result, table_name)
            return result
        
        # Route 4: Execute SQL query
        result = execute_sql_impl(query)
        logger.info(f"Executed SQL: {query[:100]}...")
        
        # Cache results for fetch
        cache_search_results(result, extract_table_from_query(query))
        return result
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return json.dumps({
            "error": f"Search failed: {str(e)}",
            "query": query
        })

def cache_search_results(result_json: str, table_name: str):
    """
    Cache search results for fetch tool.
    
    Generates record IDs in format: TableName_PrimaryKeyValue
    """
    try:
        result = json.loads(result_json)
        if "results" in result:
            for row in result["results"]:
                # Try to find primary key column
                record_id = generate_record_id(table_name, row)
                search_cache[record_id] = {
                    'table': table_name,
                    'data': row,
                    'cached_at': datetime.utcnow().isoformat()
                }
    except Exception as e:
        logger.warning(f"Failed to cache results: {e}")

def generate_record_id(table_name: str, row: Dict) -> str:
    """
    Generate unique record ID from table name and row data.
    
    Strategy:
    1. Look for common PK columns (ID, TableNameID, etc.)
    2. Use first column if no PK found
    3. Format: TableName_Value
    """
    # Common primary key column names
    pk_candidates = [
        f"{table_name}ID",
        "ID",
        f"{table_name}_ID",
        "RecordID",
        "RowID"
    ]
    
    # Try to find PK column
    for pk in pk_candidates:
        if pk in row:
            return f"{table_name}_{row[pk]}"
    
    # Fallback: use first column
    if row:
        first_col = list(row.keys())[0]
        return f"{table_name}_{row[first_col]}"
    
    # Last resort: random ID
    return f"{table_name}_{uuid.uuid4().hex[:8]}"
```

### 33:00 — Fetch Tool Implementation

**Complete Fetch Handler:**
```python
def handle_fetch(record_id: str) -> str:
    """
    Retrieve specific record by ID from cache or database.
    
    Args:
        record_id: Record identifier in format "TableName_PrimaryKeyValue"
        
    Returns:
        JSON string with record details
    """
    try:
        logger.info(f"Fetching record: {record_id}")
        
        # Check cache first
        if record_id in search_cache:
            cached = search_cache[record_id]
            # Verify TTL
            if is_cache_valid(cached['cached_at']):
                logger.info(f"Cache hit: {record_id}")
                return json.dumps({
                    'id': record_id,
                    'table': cached['table'],
                    'data': cached['data'],
                    'source': 'cache',
                    'cached_at': cached['cached_at']
                }, indent=2)
        
        # Cache miss - query database
        logger.info(f"Cache miss: {record_id}, querying database")
        
        # Parse record ID: "TableName_123"
        if "_" not in record_id:
            return json.dumps({
                'error': f'Invalid record ID format: {record_id}',
                'expected': 'TableName_PrimaryKeyValue'
            })
        
        table_name = record_id.rsplit("_", 1)[0]
        pk_value = record_id.rsplit("_", 1)[1]
        
        # Query database
        _, conn_string = get_db_config()
        conn = pyodbc.connect(conn_string)
        cursor = conn.cursor()
        
        # Try common PK column names
        pk_columns = [
            f"{table_name}ID",
            "ID",
            f"{table_name}_ID"
        ]
        
        for pk_col in pk_columns:
            try:
                query = f"SELECT * FROM [{table_name}] WHERE [{pk_col}] = ?"
                cursor.execute(query, (pk_value,))
                
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    row = cursor.fetchone()
                    
                    if row:
                        record = dict(zip(columns, row))
                        serialized = serialize_row_data(record)
                        
                        # Update cache
                        search_cache[record_id] = {
                            'table': table_name,
                            'data': serialized,
                            'cached_at': datetime.utcnow().isoformat()
                        }
                        
                        logger.info(f"Fetched from database: {record_id}")
                        return json.dumps({
                            'id': record_id,
                            'table': table_name,
                            'data': serialized,
                            'source': 'database'
                        }, indent=2)
            except Exception:
                continue
        
        conn.close()
        
        # Not found
        return json.dumps({
            'error': f'Record not found: {record_id}',
            'table': table_name,
            'pk_value': pk_value
        })
        
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        return json.dumps({
            'error': f'Fetch failed: {str(e)}',
            'record_id': record_id
        })
```

### 36:00 — MCP Protocol Handler

**SSE Endpoint Implementation:**
```python
async def handle_sse(request: Request) -> Response:
    """
    Main SSE endpoint for MCP protocol.
    
    Handles:
    - HEAD: Capability check
    - OPTIONS: CORS preflight
    - GET: SSE connection probe
    - POST: MCP JSON-RPC messages
    """
    method = request.method
    
    # HEAD: Capability check
    if method == "HEAD":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS, HEAD",
                "Access-Control-Allow-Headers": "Authorization, Content-Type"
            }
        )
    
    # OPTIONS: CORS preflight
    if method == "OPTIONS":
        return Response(
            status_code=204,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS, HEAD",
                "Access-Control-Allow-Headers": "Authorization, Content-Type",
                "Access-Control-Max-Age": "3600"
            }
        )
    
    # GET: SSE probe (simple response)
    if method == "GET":
        return Response(
            content="SSE endpoint ready\n",
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
    
    # POST: MCP JSON-RPC
    if method == "POST":
        # Validate authentication
        token = _extract_bearer_token(request)
        if not token or not _is_token_valid(token):
            return JSONResponse(
                {"error": "Unauthorized"},
                status_code=401,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        # Parse JSON-RPC request
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                {"error": "Invalid JSON"},
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        jsonrpc_method = body.get("method", "")
        jsonrpc_id = body.get("id")
        params = body.get("params", {})
        
        # Route to handler
        if jsonrpc_method == "initialize":
            return await handle_initialize(jsonrpc_id)
        elif jsonrpc_method == "tools/list":
            return await handle_tools_list(jsonrpc_id)
        elif jsonrpc_method == "tools/call":
            return await handle_tools_call(jsonrpc_id, params)
        else:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": jsonrpc_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {jsonrpc_method}"
                    }
                },
                headers={"Access-Control-Allow-Origin": "*"}
            )
    
    return Response(status_code=405)

async def handle_initialize(request_id) -> JSONResponse:
    """MCP initialize response."""
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "mssql-mcp-chatgpt",
                "version": "1.0.0"
            }
        }
    }, headers={"Access-Control-Allow-Origin": "*"})

async def handle_tools_list(request_id) -> JSONResponse:
    """MCP tools/list response."""
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "tools": [
                {
                    "name": "search",
                    "description": "Multi-purpose database search supporting: list tables, describe table, sample data, execute SQL",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query or SQL statement"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "fetch",
                    "description": "Retrieve specific record by ID from cached search results",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "record_id": {
                                "type": "string",
                                "description": "Record ID from search results"
                            }
                        },
                        "required": ["record_id"]
                    }
                }
            ]
        }
    }, headers={"Access-Control-Allow-Origin": "*"})

async def handle_tools_call(request_id, params) -> JSONResponse:
    """MCP tools/call response."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if tool_name == "search":
        query = arguments.get("query", "")
        result = handle_search(query)
    elif tool_name == "fetch":
        record_id = arguments.get("record_id", "")
        result = handle_fetch(record_id)
    else:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32602,
                "message": f"Unknown tool: {tool_name}"
            }
        }, headers={"Access-Control-Allow-Origin": "*"})
    
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": result
                }
            ]
        }
    }, headers={"Access-Control-Allow-Origin": "*"})
```

---

## Part 5: Deployment & Infrastructure (40:00-55:00)

### 40:00 — Docker Configuration

**Dockerfile.chatgpt:**
```dockerfile
FROM python:3.11-slim

# Install ODBC Driver for SQL Server
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server_chatgpt.py .
COPY server_oauth.py .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

USER mcpuser

# Expose port
EXPOSE 8008

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8008/health', timeout=5)"

# Run server
CMD ["python", "server_chatgpt.py"]
```

**docker-compose.prod.yml (ChatGPT section):**
```yaml
version: '3.8'

services:
  mcp-server-chatgpt:
    build:
      context: .
      dockerfile: Dockerfile.chatgpt
    container_name: mcp-server-chatgpt
    env_file: .env
    environment:
      - MSSQL_HOST=${MSSQL_HOST}
      - MSSQL_USER=${MSSQL_USER}
      - MSSQL_PASSWORD=${MSSQL_PASSWORD}
      - MSSQL_DATABASE=${MSSQL_DATABASE}
      - READ_ONLY_MODE=true
      - ALLOWED_REDIRECT_HOSTS=chatgpt.com,openai.com
      - MAX_SEARCH_RESULTS=50
      - CACHE_TTL_SECONDS=3600
    networks:
      - mcp-network
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  nginx:
    image: nginx:1.24-alpine
    container_name: nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - mcp-server-chatgpt
    networks:
      - mcp-network
    restart: unless-stopped

  certbot:
    image: certbot/certbot:latest
    container_name: certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    command: certonly --webroot --webroot-path=/var/www/certbot --email your-email@example.com --agree-tos --no-eff-email -d data.forensic-bot.com
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: bridge
```

### 43:00 — NGINX Configuration for ChatGPT

**nginx/conf.d/default.conf (ChatGPT-specific):**
```nginx
# Enable slash merging to prevent double-slash 404s
merge_slashes on;

upstream mcp-server-chatgpt {
    server mcp-server-chatgpt:8008;
    keepalive 32;
}

server {
    listen 80;
    server_name data.forensic-bot.com;
    
    # ACME challenge for Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name data.forensic-bot.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/data.forensic-bot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/data.forensic-bot.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    
    # Root-level OAuth discovery (for initial ChatGPT probes)
    location ~ ^/\.well-known/(oauth-authorization-server|openid-configuration|oauth-protected-resource)$ {
        proxy_pass http://mcp-server-chatgpt;
        proxy_set_header X-Environment-Path /chatgpt;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # CORS for ChatGPT
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
    }
    
    # Scoped ChatGPT endpoints
    location ~ ^/chatgpt/(.*)$ {
        # Strip /chatgpt prefix
        rewrite ^/chatgpt(/.*)$ $1 break;
        
        proxy_pass http://mcp-server-chatgpt;
        proxy_set_header X-Environment-Path /chatgpt;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # SSE-specific configuration
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 3600s;
        
        # Keep connection alive for SSE
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        
        # CORS for ChatGPT
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS, HEAD" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        add_header Access-Control-Max-Age "3600" always;
    }
    
    # Health check
    location = /health {
        proxy_pass http://mcp-server-chatgpt;
        proxy_set_header Host $host;
    }
}
```

### 46:00 — Environment Configuration

**.env Template:**
```bash
# Database Configuration
MSSQL_HOST=your-sql-server.database.windows.net
MSSQL_USER=chatgpt_readonly_user
MSSQL_PASSWORD=your_secure_password_here
MSSQL_DATABASE=your_database_name
MSSQL_DRIVER=ODBC Driver 18 for SQL Server

# Security Settings
TrustServerCertificate=yes
Trusted_Connection=no
READ_ONLY_MODE=true

# OAuth Configuration
ALLOWED_REDIRECT_HOSTS=chatgpt.com,openai.com
# Note: Never enable these in production
ALLOW_UNAUTH_METHODS=false
ALLOW_UNAUTH_TOOLS_CALL=false

# ChatGPT-Specific Settings
MAX_SEARCH_RESULTS=50
CACHE_TTL_SECONDS=3600

# Environment Path (optional, set by NGINX)
ENVIRONMENT_PATH=/chatgpt

# Logging
LOG_LEVEL=INFO
```

### 48:00 — SSL Certificate Setup

**setup-letsencrypt.sh:**
```bash
#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Let's Encrypt SSL Setup for ChatGPT MCP Server${NC}"

# Prompt for domain
read -p "Enter your domain (e.g., data.forensic-bot.com): " DOMAIN
read -p "Enter your email: " EMAIL
read -p "Use production (0) or staging (1) certificates? " STAGING

# Set paths
DATA_PATH="./certbot"
mkdir -p "$DATA_PATH/conf"
mkdir -p "$DATA_PATH/www"

# Download recommended TLS parameters
if [ ! -e "$DATA_PATH/conf/options-ssl-nginx.conf" ]; then
    echo -e "${YELLOW}Downloading recommended TLS parameters...${NC}"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$DATA_PATH/conf/options-ssl-nginx.conf"
fi

if [ ! -e "$DATA_PATH/conf/ssl-dhparams.pem" ]; then
    echo -e "${YELLOW}Downloading DH parameters...${NC}"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$DATA_PATH/conf/ssl-dhparams.pem"
fi

# Update domain in docker-compose and nginx config
echo -e "${YELLOW}Updating configuration files...${NC}"
sed -i.bak "s/data.forensic-bot.com/$DOMAIN/g" docker-compose.prod.yml
sed -i.bak "s/data.forensic-bot.com/$DOMAIN/g" nginx/conf.d/default.conf

# Start nginx with HTTP only (for ACME challenge)
echo -e "${YELLOW}Starting nginx for ACME challenge...${NC}"
docker-compose -f docker-compose.prod.yml up -d nginx

# Wait for nginx
sleep 5

# Request certificate
if [ "$STAGING" == "1" ]; then
    STAGING_ARG="--staging"
    echo -e "${YELLOW}Using Let's Encrypt STAGING environment${NC}"
else
    STAGING_ARG=""
    echo -e "${YELLOW}Using Let's Encrypt PRODUCTION environment${NC}"
fi

echo -e "${YELLOW}Requesting certificate from Let's Encrypt...${NC}"
docker-compose -f docker-compose.prod.yml run --rm certbot \
    certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    $STAGING_ARG \
    -d "$DOMAIN"

# Verify certificate
if [ ! -f "$DATA_PATH/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo -e "${RED}Failed to obtain certificate!${NC}"
    exit 1
fi

# Reload nginx with SSL
echo -e "${YELLOW}Reloading nginx with SSL...${NC}"
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Start all services
echo -e "${YELLOW}Starting all services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

echo -e "${GREEN}Setup Complete!${NC}"
echo -e "Your ChatGPT MCP server is now available at: ${GREEN}https://$DOMAIN${NC}"
echo -e "Discovery endpoint: ${GREEN}https://$DOMAIN/.well-known/oauth-authorization-server${NC}"
```

### 50:00 — Deployment Steps

**Complete Deployment Process:**
```bash
# 1. Clone repository
git clone https://github.com/your-org/mssql-mcp-server.git
cd mssql-mcp-server

# 2. Configure environment
cp .env.example .env
nano .env  # Edit with your database credentials

# 3. Run SSL setup
chmod +x setup-letsencrypt.sh
./setup-letsencrypt.sh

# 4. Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify deployment
curl https://your-domain.com/health
curl https://your-domain.com/.well-known/oauth-authorization-server

# 6. Check logs
docker-compose -f docker-compose.prod.yml logs -f mcp-server-chatgpt
```

### 52:00 — Monitoring and Health Checks

**Health Check Endpoint:**
```python
@app.route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """
    Comprehensive health check for monitoring systems.
    
    Checks:
    - Server uptime
    - Database connectivity
    - OAuth functionality
    - Cache status
    
    Returns:
        JSON with health status
    """
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check database
    try:
        _, conn_string = get_db_config()
        conn = pyodbc.connect(conn_string, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        status["checks"]["database"] = "ok"
    except Exception as e:
        status["checks"]["database"] = f"error: {str(e)}"
        status["status"] = "unhealthy"
    
    # Check OAuth
    status["checks"]["oauth"] = {
        "active_tokens": len(valid_tokens),
        "auth_codes": len(auth_codes)
    }
    
    # Check cache
    status["checks"]["cache"] = {
        "entries": len(search_cache),
        "ttl_seconds": CACHE_TTL_SECONDS
    }
    
    return JSONResponse(status)
```

**Monitoring Script:**
```bash
#!/bin/bash
# monitor-chatgpt.sh

LOG_FILE="/var/log/mcp/chatgpt-server.log"

echo "=== ChatGPT MCP Server Health Monitor ==="
echo "Date: $(date)"
echo ""

# Health check
echo "=== Health Status ==="
curl -s https://data.forensic-bot.com/chatgpt/health | jq '.'
echo ""

# Error analysis
echo "=== Error Summary (Last 24h) ==="
grep "ERROR" $LOG_FILE | grep "$(date -d '24 hours ago' '+%Y-%m-%d')" | wc -l | xargs echo "Total errors:"
grep "ERROR" $LOG_FILE | tail -5
echo ""

# OAuth activity
echo "=== OAuth Activity ==="
grep "oauth" $LOG_FILE | grep "register" | wc -l | xargs echo "Client registrations:"
grep "oauth" $LOG_FILE | grep "token" | wc -l | xargs echo "Token exchanges:"
echo ""

# Tool usage
echo "=== Tool Usage Statistics ==="
grep "tool_execution" $LOG_FILE | \
    jq -r '.tool' 2>/dev/null | \
    sort | uniq -c | sort -rn
echo ""

# Cache statistics
echo "=== Cache Performance ==="
grep "Cache" $LOG_FILE | tail -10
echo ""

# Recent queries
echo "=== Recent Search Queries (Last 10) ==="
grep "handle_search" $LOG_FILE | tail -10 | \
    grep -oP '(?<=query: ).*' | head -10
```

---

## Part 6: Testing and Validation (55:00-65:00)

### 55:00 — Unit Testing

**test_chatgpt_oauth.py:**
```python
import pytest
import json
from unittest.mock import Mock, patch
from server_chatgpt import (
    _is_host_allowed,
    _is_token_valid,
    _extract_bearer_token,
    serialize_row_data,
    valid_tokens,
    ALLOWED_REDIRECT_HOSTS
)
from datetime import datetime, timedelta
from decimal import Decimal

class TestOAuthHelpers:
    """Test OAuth helper functions."""
    
    def test_extract_bearer_token_valid(self):
        """Test extracting valid bearer token."""
        request = Mock()
        request.headers.get.return_value = "Bearer abc123token"
        
        token = _extract_bearer_token(request)
        assert token == "abc123token"
    
    def test_extract_bearer_token_invalid(self):
        """Test invalid authorization headers."""
        request = Mock()
        
        # No bearer prefix
        request.headers.get.return_value = "abc123token"
        assert _extract_bearer_token(request) is None
        
        # Empty header
        request.headers.get.return_value = ""
        assert _extract_bearer_token(request) is None
        
        # None header
        request.headers.get.return_value = None
        assert _extract_bearer_token(request) is None
    
    def test_is_host_allowed_valid(self):
        """Test valid redirect URIs."""
        assert _is_host_allowed("https://chatgpt.com/callback") == True
        assert _is_host_allowed("https://www.chatgpt.com/callback") == True
        assert _is_host_allowed("https://openai.com/oauth") == True
    
    def test_is_host_allowed_invalid(self):
        """Test invalid redirect URIs."""
        assert _is_host_allowed("https://evil.com/callback") == False
        assert _is_host_allowed("https://chatgpt.com.evil.com/callback") == False
        assert _is_host_allowed("") == False
        assert _is_host_allowed(None) == False
    
    def test_is_token_valid(self):
        """Test token validation with expiration."""
        # Setup valid token
        token = "test_token_123"
        valid_tokens[token] = {
            "client_id": "test_client",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        assert _is_token_valid(token) == True
        
        # Setup expired token
        expired_token = "expired_token_456"
        valid_tokens[expired_token] = {
            "client_id": "test_client",
            "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
        }
        
        assert _is_token_valid(expired_token) == False
        
        # Non-existent token
        assert _is_token_valid("nonexistent") == False

class TestDataSerialization:
    """Test data serialization for SQL Server types."""
    
    def test_serialize_decimal(self):
        """Test Decimal to float conversion."""
        result = serialize_row_data(Decimal("123.45"))
        assert result == 123.45
        assert isinstance(result, float)
    
    def test_serialize_datetime(self):
        """Test datetime to ISO string."""
        dt = datetime(2025, 10, 1, 12, 30, 45)
        result = serialize_row_data(dt)
        assert result == "2025-10-01T12:30:45"
    
    def test_serialize_bytes(self):
        """Test bytes to base64 string."""
        data = b"Hello World"
        result = serialize_row_data(data)
        assert result == "SGVsbG8gV29ybGQ="
    
    def test_serialize_none(self):
        """Test None handling."""
        assert serialize_row_data(None) is None
    
    def test_serialize_primitives(self):
        """Test primitive types pass through."""
        assert serialize_row_data(123) == 123
        assert serialize_row_data(123.45) == 123.45
        assert serialize_row_data("test") == "test"
        assert serialize_row_data(True) == True

@pytest.mark.asyncio
class TestEndpoints:
    """Test HTTP endpoints."""
    
    async def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "checks" in data
        assert "database" in data["checks"]
    
    async def test_oauth_discovery(self, client):
        """Test OAuth discovery endpoint."""
        response = await client.get("/.well-known/oauth-authorization-server")
        assert response.status_code == 200
        
        data = response.json()
        assert "issuer" in data
        assert "authorization_endpoint" in data
        assert "token_endpoint" in data
    
    async def test_sse_unauthorized(self, client):
        """Test SSE endpoint without auth."""
        response = await client.post("/sse")
        assert response.status_code == 401
    
    async def test_sse_with_valid_token(self, client):
        """Test SSE endpoint with valid token."""
        # Create valid token
        token = "test_valid_token"
        valid_tokens[token] = {
            "client_id": "test_client",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        response = await client.post(
            "/sse",
            headers={"Authorization": f"Bearer {token}"},
            json={"jsonrpc": "2.0", "method": "initialize", "id": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert "result" in data

@pytest.fixture
def client():
    """Create test client."""
    from starlette.testclient import TestClient
    from server_chatgpt import app
    return TestClient(app)
```

**test_tools.py:**
```python
import pytest
import json
from unittest.mock import Mock, patch
from server_chatgpt import (
    handle_search,
    handle_fetch,
    search_cache,
    generate_record_id
)

class TestSearchTool:
    """Test search tool functionality."""
    
    @patch('server_chatgpt.list_tables_impl')
    def test_search_list_tables(self, mock_list):
        """Test 'list tables' query routing."""
        mock_list.return_value = json.dumps({"tables": ["Customers", "Orders"]})
        
        result = handle_search("list tables")
        result_data = json.loads(result)
        
        assert "tables" in result_data
        mock_list.assert_called_once()
    
    @patch('server_chatgpt.describe_table_impl')
    def test_search_describe_table(self, mock_describe):
        """Test 'describe TableName' query routing."""
        mock_describe.return_value = json.dumps({
            "columns": [
                {"name": "CustomerID", "type": "int"},
                {"name": "Name", "type": "varchar"}
            ]
        })
        
        result = handle_search("describe Customers")
        result_data = json.loads(result)
        
        assert "columns" in result_data
        mock_describe.assert_called_once_with("Customers")
    
    @patch('server_chatgpt.get_table_sample_impl')
    def test_search_sample_data(self, mock_sample):
        """Test 'sample TableName limit N' query routing."""
        mock_sample.return_value = json.dumps({
            "results": [
                {"CustomerID": 1, "Name": "Acme"},
                {"CustomerID": 2, "Name": "TechCorp"}
            ]
        })
        
        result = handle_search("sample Customers limit 10")
        result_data = json.loads(result)
        
        assert "results" in result_data
        mock_sample.assert_called_once_with("Customers", 10)
    
    @patch('server_chatgpt.execute_sql_impl')
    def test_search_sql_query(self, mock_execute):
        """Test SQL query execution."""
        mock_execute.return_value = json.dumps({
            "results": [{"CustomerID": 1, "Name": "Acme"}],
            "row_count": 1
        })
        
        query = "SELECT * FROM Customers WHERE CustomerID = 1"
        result = handle_search(query)
        result_data = json.loads(result)
        
        assert "results" in result_data
        mock_execute.assert_called_once_with(query)

class TestFetchTool:
    """Test fetch tool functionality."""
    
    def test_fetch_from_cache(self):
        """Test fetching record from cache."""
        # Setup cache
        record_id = "Customers_123"
        search_cache[record_id] = {
            'table': 'Customers',
            'data': {'CustomerID': 123, 'Name': 'Acme'},
            'cached_at': datetime.utcnow().isoformat()
        }
        
        result = handle_fetch(record_id)
        result_data = json.loads(result)
        
        assert result_data['id'] == record_id
        assert result_data['source'] == 'cache'
        assert result_data['data']['CustomerID'] == 123
    
    @patch('server_chatgpt.pyodbc.connect')
    def test_fetch_from_database(self, mock_connect):
        """Test fetching record from database on cache miss."""
        # Mock database connection
        mock_cursor = Mock()
        mock_cursor.description = [('CustomerID',), ('Name',)]
        mock_cursor.fetchone.return_value = (123, 'Acme')
        
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        result = handle_fetch("Customers_123")
        result_data = json.loads(result)
        
        assert result_data['table'] == 'Customers'
        assert result_data['source'] == 'database'
    
    def test_fetch_invalid_record_id(self):
        """Test fetch with invalid record ID format."""
        result = handle_fetch("invalid_format")
        result_data = json.loads(result)
        
        # Should handle gracefully
        assert 'error' in result_data or 'data' in result_data

class TestUtilities:
    """Test utility functions."""
    
    def test_generate_record_id(self):
        """Test record ID generation."""
        row = {'CustomerID': 123, 'Name': 'Acme'}
        record_id = generate_record_id('Customers', row)
        
        assert record_id == 'Customers_123'
    
    def test_generate_record_id_fallback(self):
        """Test record ID generation with no PK column."""
        row = {'FirstName': 'John', 'LastName': 'Doe'}
        record_id = generate_record_id('Employees', row)
        
        # Should use first column
        assert record_id.startswith('Employees_')
```

### 58:00 — Integration Testing

**test_integration.py:**
```python
import pytest
import requests
import json
from time import sleep

BASE_URL = "https://data.forensic-bot.com/chatgpt"

class TestOAuthFlow:
    """Test complete OAuth flow."""
    
    def test_client_registration(self):
        """Test client registration."""
        response = requests.post(
            f"{BASE_URL}/register",
            json={
                "client_name": "Test Client",
                "redirect_uris": ["https://chatgpt.com/callback"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "client_id" in data
        assert "client_secret" in data
        assert data["client_name"] == "Test Client"
        
        return data["client_id"], data["client_secret"]
    
    def test_authorization_flow(self):
        """Test authorization code flow."""
        # Register client
        client_id, client_secret = self.test_client_registration()
        
        # Authorization request
        auth_response = requests.get(
            f"{BASE_URL}/authorize",
            params={
                "client_id": client_id,
                "redirect_uri": "https://chatgpt.com/callback",
                "response_type": "code",
                "state": "random_state_123"
            },
            allow_redirects=False
        )
        
        assert auth_response.status_code == 302
        
        # Extract code from redirect
        location = auth_response.headers.get("Location")
        assert "code=" in location
        assert "state=random_state_123" in location
        
        # Parse authorization code
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(location)
        params = parse_qs(parsed.query)
        auth_code = params["code"][0]
        
        # Exchange code for token
        token_response = requests.post(
            f"{BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": auth_code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": "https://chatgpt.com/callback"
            }
        )
        
        assert token_response.status_code == 200
        token_data = token_response.json()
        
        assert "access_token" in token_data
        assert "token_type" in token_data
        assert token_data["token_type"] == "Bearer"
        
        return token_data["access_token"]

class TestMCPProtocol:
    """Test MCP protocol implementation."""
    
    def get_valid_token(self):
        """Helper to get valid OAuth token."""
        oauth_test = TestOAuthFlow()
        return oauth_test.test_authorization_flow()
    
    def test_initialize(self):
        """Test MCP initialize method."""
        token = self.get_valid_token()
        
        response = requests.post(
            f"{BASE_URL}/sse",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "id": 1,
                "params": {}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["jsonrpc"] == "2.0"
        assert "result" in data
        assert data["result"]["protocolVersion"] == "2025-06-18"
    
    def test_tools_list(self):
        """Test MCP tools/list method."""
        token = self.get_valid_token()
        
        response = requests.post(
            f"{BASE_URL}/sse",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 2,
                "params": {}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "result" in data
        assert "tools" in data["result"]
        
        tools = data["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        
        assert "search" in tool_names
        assert "fetch" in tool_names
    
    def test_search_tool(self):
        """Test search tool execution."""
        token = self.get_valid_token()
        
        response = requests.post(
            f"{BASE_URL}/sse",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 3,
                "params": {
                    "name": "search",
                    "arguments": {
                        "query": "list tables"
                    }
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "result" in data
        assert "content" in data["result"]
        
        content = data["result"]["content"][0]["text"]
        content_data = json.loads(content)
        
        assert "tables" in content_data or "results" in content_data
    
    def test_fetch_tool(self):
        """Test fetch tool execution."""
        token = self.get_valid_token()
        
        # First, search to populate cache
        search_response = requests.post(
            f"{BASE_URL}/sse",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 4,
                "params": {
                    "name": "search",
                    "arguments": {
                        "query": "sample Customers limit 1"
                    }
                }
            }
        )
        
        search_data = search_response.json()
        search_content = json.loads(search_data["result"]["content"][0]["text"])
        
        if "results" in search_content and search_content["results"]:
            # Get first record ID (would be in cache)
            first_record = search_content["results"][0]
            # Assume CustomerID exists
            record_id = f"Customers_{first_record.get('CustomerID', 1)}"
            
            # Now fetch it
            fetch_response = requests.post(
                f"{BASE_URL}/sse",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "id": 5,
                    "params": {
                        "name": "fetch",
                        "arguments": {
                            "record_id": record_id
                        }
                    }
                }
            )
            
            assert fetch_response.status_code == 200
            fetch_data = fetch_response.json()
            assert "result" in fetch_data

class TestSecurity:
    """Test security measures."""
    
    def test_unauthorized_access(self):
        """Test that endpoints require authentication."""
        response = requests.post(
            f"{BASE_URL}/sse",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }
        )
        
        assert response.status_code == 401
    
    def test_invalid_token(self):
        """Test with invalid bearer token."""
        response = requests.post(
            f"{BASE_URL}/sse",
            headers={"Authorization": "Bearer invalid_token_12345"},
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }
        )
        
        assert response.status_code == 401
    
    def test_read_only_enforcement(self):
        """Test that write operations are blocked."""
        token = TestOAuthFlow().test_authorization_flow()
        
        response = requests.post(
            f"{BASE_URL}/sse",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 6,
                "params": {
                    "name": "search",
                    "arguments": {
                        "query": "DELETE FROM Customers WHERE CustomerID = 1"
                    }
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        result_text = data["result"]["content"][0]["text"]
        result_data = json.loads(result_text)
        
        assert "error" in result_data
        assert "not allowed" in result_data["error"].lower()

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**test_tools.py:**
```python
import pytest
import json
from unittest.mock import Mock, patch
from server_chatgpt import (
    handle_search,
    handle_fetch,
    search_cache,
    generate_record_id
)

class TestSearchTool:
    """Test search tool functionality."""
    
    @patch('server_chatgpt.list_tables_impl')
    def test_search_list_tables(self, mock_list):
        """Test 'list tables' query routing."""
        mock_list.return_value = json.dumps({"tables": ["Customers", "Orders"]})
        
        result = handle_search("list tables")
        result_data = json.loads(result)
        
        assert "tables" in result_data
        mock_list.assert_called_once()
    
    @patch('server_chatgpt.describe_table_impl')
    def test_search_describe_table(self, mock_describe):
        """Test 'describe TableName' query routing."""
        mock_describe.return_value = json.dumps({
            "columns": [
                {"name": "CustomerID", "type": "int"},
                {"name": "Name", "type": "varchar"}
            ]
        })
        
        result = handle_search("describe Customers")
        result_data = json.loads(result)
        
        assert "columns" in result_data
        mock_describe.assert_called_once_with("Customers")
    
    @patch('server_chatgpt.get_table_sample_impl')
    def test_search_sample_data(self, mock_sample):
        """Test 'sample TableName limit N' query routing."""
        mock_sample.return_value = json.dumps({
            "results": [
                {"CustomerID": 1, "Name": "Acme"},
                {"CustomerID": 2, "Name": "TechCorp"}
            ]
        })
        
        result = handle_search("sample Customers limit 10")
        result_data = json.loads(result)
        
        assert "results" in result_data
        mock_sample.assert_called_once_with("Customers", 10)
    
    @patch('server_chatgpt.execute_sql_impl')
    def test_search_sql_query(self, mock_execute):
        """Test SQL query execution."""
        mock_execute.return_value = json.dumps({
            "results": [{"CustomerID": 1, "Name": "Acme"}],
            "row_count": 1
        })
        
        query = "SELECT * FROM Customers WHERE CustomerID = 1"
        result = handle_search(query)
        result_data = json.loads(result)
        
        assert "results" in result_data
        mock_execute.assert_called_once_with(query)

class TestFetchTool:
    """Test fetch tool functionality."""
    
    def test_fetch_from_cache(self):
        """Test fetching record from cache."""
        from datetime import datetime
        # Setup cache
        record_id = "Customers_123"
        search_cache[record_id] = {
            'table': 'Customers',
            'data': {'CustomerID': 123, 'Name': 'Acme'},
            'cached_at': datetime.utcnow().isoformat()
        }
        
        result = handle_fetch(record_id)
        result_data = json.loads(result)
        
        assert result_data['id'] == record_id
        assert result_data['source'] == 'cache'
        assert result_data['data']['CustomerID'] == 123
    
    def test_generate_record_id(self):
        """Test record ID generation."""
        row = {'CustomerID': 123, 'Name': 'Acme'}
        record_id = generate_record_id('Customers', row)
        
        assert record_id == 'Customers_123'
```

### 61:00 — Manual Testing with cURL

**Test OAuth Discovery:**
```bash
# Test root-level discovery
curl -v https://data.forensic-bot.com/.well-known/oauth-authorization-server

# Expected: 200 OK with OAuth metadata
# {
#   "issuer": "https://data.forensic-bot.com/chatgpt",
#   "authorization_endpoint": "https://data.forensic-bot.com/chatgpt/authorize",
#   ...
# }

# Test scoped discovery
curl -v https://data.forensic-bot.com/chatgpt/.well-known/oauth-authorization-server
```

**Test Client Registration:**
```bash
curl -X POST https://data.forensic-bot.com/chatgpt/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test Client",
    "redirect_uris": ["https://chatgpt.com/callback"]
  }'

# Save client_id and client_secret from response
CLIENT_ID="client_abc123"
CLIENT_SECRET="secret_xyz789"
```

**Test Authorization:**
```bash
# Visit in browser or use curl:
curl -v "https://data.forensic-bot.com/chatgpt/authorize?\
client_id=$CLIENT_ID&\
redirect_uri=https://chatgpt.com/callback&\
response_type=code&\
state=random123"

# Expected: 302 redirect with authorization code
# Extract code from Location header
AUTH_CODE="code_from_redirect"
```

**Test Token Exchange:**
```bash
curl -X POST https://data.forensic-bot.com/chatgpt/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=$AUTH_CODE" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "redirect_uri=https://chatgpt.com/callback"

# Save access_token from response
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Test MCP Endpoints:**
```bash
# Initialize
curl -X POST https://data.forensic-bot.com/chatgpt/sse \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "id": 1,
    "params": {}
  }'

# List tools
curl -X POST https://data.forensic-bot.com/chatgpt/sse \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 2,
    "params": {}
  }'

# Call search tool
curl -X POST https://data.forensic-bot.com/chatgpt/sse \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "id": 3,
    "params": {
      "name": "search",
      "arguments": {
        "query": "list tables"
      }
    }
  }'
```

### 63:00 — Performance Testing

**Load Testing Script:**
```python
#!/usr/bin/env python3
"""
Load test for ChatGPT MCP server.
"""
import asyncio
import aiohttp
import time
from statistics import mean, median

BASE_URL = "https://data.forensic-bot.com/chatgpt"
CONCURRENT_REQUESTS = 10
TOTAL_REQUESTS = 100

async def get_token(session):
    """Get OAuth token."""
    # Register client
    async with session.post(
        f"{BASE_URL}/register",
        json={"client_name": "Load Test", "redirect_uris": ["https://test.com"]}
    ) as resp:
        data = await resp.json()
        client_id = data["client_id"]
        client_secret = data["client_secret"]
    
    # Get auth code
    async with session.get(
        f"{BASE_URL}/authorize",
        params={
            "client_id": client_id,
            "redirect_uri": "https://test.com",
            "response_type": "code"
        },
        allow_redirects=False
    ) as resp:
        location = resp.headers.get("Location")
        code = location.split("code=")[1].split("&")[0]
    
    # Exchange for token
    async with session.post(
        f"{BASE_URL}/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret
        }
    ) as resp:
        data = await resp.json()
        return data["access_token"]

async def search_query(session, token, query):
    """Execute search query and measure time."""
    start = time.time()
    
    async with session.post(
        f"{BASE_URL}/sse",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {
                "name": "search",
                "arguments": {"query": query}
            }
        }
    ) as resp:
        await resp.json()
        duration = time.time() - start
        return duration, resp.status

async def load_test():
    """Run load test."""
    async with aiohttp.ClientSession() as session:
        # Get token
        print("Getting OAuth token...")
        token = await get_token(session)
        print("Token obtained")
        
        # Prepare queries
        queries = [
            "list tables",
            "describe Customers",
            "sample Orders limit 10",
            "SELECT TOP 5 * FROM Products"
        ]
        
        # Run concurrent requests
        tasks = []
        for i in range(TOTAL_REQUESTS):
            query = queries[i % len(queries)]
            tasks.append(search_query(session, token, query))
            
            # Limit concurrency
            if len(tasks) >= CONCURRENT_REQUESTS:
                results = await asyncio.gather(*tasks)
                tasks = []
        
        # Run remaining tasks
        if tasks:
            results = await asyncio.gather(*tasks)
        
        # Aggregate results
        durations = [r[0] for r in results]
        statuses = [r[1] for r in results]
        
        print(f"\n=== Load Test Results ===")
        print(f"Total requests: {TOTAL_REQUESTS}")
        print(f"Concurrent: {CONCURRENT_REQUESTS}")
        print(f"Success rate: {statuses.count(200)/len(statuses)*100:.1f}%")
        print(f"Average response time: {mean(durations):.3f}s")
        print(f"Median response time: {median(durations):.3f}s")
        print(f"Min response time: {min(durations):.3f}s")
        print(f"Max response time: {max(durations):.3f}s")

if __name__ == "__main__":
    asyncio.run(load_test())
```

---

## Part 7: Production Operations (65:00-80:00)

### 65:00 — Logging Configuration

**Enhanced Logging Setup:**
```python
import logging
import json
from datetime import datetime

# Configure structured logging
class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easier parsing."""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add custom fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        return json.dumps(log_data)

# Setup logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())

logger = logging.getLogger("chatgpt_mcp")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage examples
def log_oauth_event(event_type, client_id, details=None):
    """Log OAuth events with context."""
    extra = {'user_id': client_id}
    logger.info(f"OAuth event: {event_type}", extra=extra)
    if details:
        logger.debug(f"Details: {json.dumps(details)}", extra=extra)

def log_tool_execution(tool_name, query, duration_ms, success=True):
    """Log tool execution metrics."""
    logger.info(
        f"Tool execution: {tool_name}",
        extra={
            'tool': tool_name,
            'query': query[:100],
            'duration_ms': duration_ms,
            'success': success
        }
    )
```

### 67:00 — Backup and Recovery

**Database Backup Script:**
```bash
#!/bin/bash
# backup-database.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mssql"
DATABASE="your_database"
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR

# Create backup using SQL Server native backup
docker-compose exec -T mcp-server-chatgpt python << EOF
import pyodbc
from server_chatgpt import get_db_config

_, conn_string = get_db_config()
# Modify for backup: remove read-only intent
conn_string = conn_string.replace("ApplicationIntent=ReadOnly", "ApplicationIntent=ReadWrite")

conn = pyodbc.connect(conn_string)
cursor = conn.cursor()

backup_path = f"/var/opt/mssql/backup/${DATABASE}_${TIMESTAMP}.bak"
cursor.execute(f"BACKUP DATABASE [{DATABASE}] TO DISK = '{backup_path}' WITH COMPRESSION, INIT")
conn.commit()
print(f"Backup created: {backup_path}")
EOF

# Copy backup from container
docker cp $(docker-compose ps -q mcp-server-chatgpt):/var/opt/mssql/backup/${DATABASE}_${TIMESTAMP}.bak \
    ${BACKUP_DIR}/

# Compress backup
gzip ${BACKUP_DIR}/${DATABASE}_${TIMESTAMP}.bak

# Upload to cloud storage (optional)
# aws s3 cp ${BACKUP_DIR}/${DATABASE}_${TIMESTAMP}.bak.gz s3://your-bucket/backups/

# Clean old backups
find $BACKUP_DIR -name "*.bak.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup complete: ${DATABASE}_${TIMESTAMP}.bak.gz"
```

**Recovery Procedure:**
```bash
#!/bin/bash
# restore-database.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.bak.gz>"
    exit 1
fi

# Decompress
gunzip -c $BACKUP_FILE > /tmp/restore.bak

# Copy to container
docker cp /tmp/restore.bak $(docker-compose ps -q mcp-server-chatgpt):/var/opt/mssql/backup/

# Restore
docker-compose exec -T mcp-server-chatgpt python << EOF
import pyodbc
from server_chatgpt import get_db_config

_, conn_string = get_db_config()
conn = pyodbc.connect(conn_string)
cursor = conn.cursor()

cursor.execute("RESTORE DATABASE [your_database] FROM DISK = '/var/opt/mssql/backup/restore.bak' WITH REPLACE")
conn.commit()
print("Database restored successfully")
EOF

# Cleanup
rm /tmp/restore.bak
```

### 69:00 — Monitoring and Alerts

**Prometheus Metrics Endpoint:**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response
import time

# Define metrics
oauth_registrations = Counter('oauth_registrations_total', 'Total OAuth client registrations')
oauth_token_exchanges = Counter('oauth_token_exchanges_total', 'Total OAuth token exchanges')
tool_executions = Counter('tool_executions_total', 'Total tool executions', ['tool_name', 'status'])
tool_duration = Histogram('tool_execution_seconds', 'Tool execution duration', ['tool_name'])
active_tokens = Gauge('active_tokens', 'Number of active OAuth tokens')
cache_size = Gauge('search_cache_size', 'Number of entries in search cache')

# Update metrics in handlers
def handle_register():
    oauth_registrations.inc()
    # ... rest of handler

def handle_token():
    oauth_token_exchanges.inc()
    # ... rest of handler

def handle_tools_call(tool_name, query):
    start_time = time.time()
    try:
        result = execute_tool(tool_name, query)
        tool_executions.labels(tool_name=tool_name, status='success').inc()
        return result
    except Exception as e:
        tool_executions.labels(tool_name=tool_name, status='error').inc()
        raise
    finally:
        duration = time.time() - start_time
        tool_duration.labels(tool_name=tool_name).observe(duration)

# Metrics endpoint
@app.route("/metrics", methods=["GET"])
async def metrics(request: Request):
    """Prometheus metrics endpoint."""
    # Update gauges
    active_tokens.set(len(valid_tokens))
    cache_size.set(len(search_cache))
    
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

**Grafana Dashboard Configuration:**
```json
{
  "dashboard": {
    "title": "ChatGPT MCP Server Metrics",
    "panels": [
      {
        "title": "OAuth Activity",
        "targets": [
          {
            "expr": "rate(oauth_registrations_total[5m])",
            "legendFormat": "Registrations/min"
          },
          {
            "expr": "rate(oauth_token_exchanges_total[5m])",
            "legendFormat": "Token Exchanges/min"
          }
        ]
      },
      {
        "title": "Tool Execution Rate",
        "targets": [
          {
            "expr": "rate(tool_executions_total[5m])",
            "legendFormat": "{{tool_name}} - {{status}}"
          }
        ]
      },
      {
        "title": "Tool Execution Duration (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(tool_execution_seconds_bucket[5m]))",
            "legendFormat": "{{tool_name}}"
          }
        ]
      },
      {
        "title": "Active Tokens",
        "targets": [
          {
            "expr": "active_tokens",
            "legendFormat": "Active OAuth Tokens"
          }
        ]
      },
      {
        "title": "Cache Size",
        "targets": [
          {
            "expr": "search_cache_size",
            "legendFormat": "Search Cache Entries"
          }
        ]
      }
    ]
  }
}
```

### 72:00 — Cache Management

**Automatic Cache Cleanup:**
```python
import asyncio
from datetime import datetime, timedelta

async def cache_cleanup_task():
    """
    Background task to clean expired cache entries.
    Runs every 5 minutes.
    """
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            
            now = datetime.utcnow()
            expired_keys = []
            
            for key, value in search_cache.items():
                cached_time = datetime.fromisoformat(value['cached_at'])
                age_seconds = (now - cached_time).total_seconds()
                
                if age_seconds >= CACHE_TTL_SECONDS:
                    expired_keys.append(key)
            
            # Remove expired entries
            for key in expired_keys:
                del search_cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")

# Start cleanup task on server startup
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks."""
    asyncio.create_task(cache_cleanup_task())
    logger.info("Started cache cleanup task")
```

**Manual Cache Management Script:**
```bash
#!/bin/bash
# cache-management.sh

COMMAND=$1

case $COMMAND in
    "clear")
        docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import search_cache
search_cache.clear()
print('Cache cleared')
"
        ;;
    
    "stats")
        docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import search_cache, CACHE_TTL_SECONDS
from datetime import datetime

print(f'Total entries: {len(search_cache)}')
print(f'TTL: {CACHE_TTL_SECONDS} seconds')

if search_cache:
    oldest = min(search_cache.values(), key=lambda x: x['cached_at'])
    newest = max(search_cache.values(), key=lambda x: x['cached_at'])
    print(f'Oldest entry: {oldest[\"cached_at\"]}')
    print(f'Newest entry: {newest[\"cached_at\"]}')
"
        ;;
    
    "warm")
        echo "Warming cache with common queries..."
        docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import handle_search
# Execute common queries to populate cache
queries = ['list tables', 'sample Customers limit 10', 'sample Orders limit 10']
for q in queries:
    handle_search(q)
    print(f'Cached: {q}')
"
        ;;
    
    *)
        echo "Usage: $0 {clear|stats|warm}"
        exit 1
        ;;
esac
```

### 75:00 — Troubleshooting Common Issues

**Issue 1: 404 Not Found on Discovery**
```bash
# Diagnosis
curl -v https://data.forensic-bot.com/.well-known/oauth-authorization-server

# Check NGINX configuration
docker-compose exec nginx nginx -t
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf | grep "well-known"

# Verify X-Environment-Path header
docker-compose logs nginx | grep "X-Environment-Path"

# Fix: Ensure NGINX proxies root-level discovery to server
# See NGINX configuration section (43:00)
```

**Issue 2: 401 Unauthorized on SSE**
```bash
# Check token validity
docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import valid_tokens
from datetime import datetime
print('Active tokens:', len(valid_tokens))
for token, data in list(valid_tokens.items())[:5]:
    expires = datetime.fromisoformat(data['expires_at'])
    print(f'{token[:10]}... expires at {expires}')
"

# Re-authenticate
# Complete new OAuth flow to get fresh token
```

**Issue 3: Database Connection Failures**
```bash
# Test connection
docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import get_db_config
import pyodbc

try:
    _, conn_string = get_db_config()
    conn = pyodbc.connect(conn_string, timeout=10)
    cursor = conn.cursor()
    cursor.execute('SELECT @@VERSION')
    print('Connection successful:', cursor.fetchone()[0][:50])
except Exception as e:
    print('Connection failed:', e)
"

# Check firewall rules
# Verify database server allows connections from Docker network

# Check credentials
docker-compose exec mcp-server-chatgpt env | grep MSSQL
```

**Issue 4: Slow Query Performance**
```bash
# Enable query logging
docker-compose exec mcp-server-chatgpt python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
"

# Analyze slow queries
docker-compose logs mcp-server-chatgpt | grep "duration_ms" | \
    awk -F'duration_ms":' '{print $2}' | \
    awk '{print $1}' | \
    sort -n | tail -10

# Check database indexes
# Review execution plans for slow queries
```

### 78:00 — Security Incident Response

**Security Checklist:**
```bash
#!/bin/bash
# security-audit.sh

echo "=== Security Audit ==="
echo ""

# Check for unauthorized access attempts
echo "1. Failed authentication attempts:"
docker-compose logs mcp-server-chatgpt | grep "401" | wc -l

# Check for unusual query patterns
echo "2. Potential SQL injection attempts:"
docker-compose logs mcp-server-chatgpt | grep -i "union\|or 1=1\|drop table"

# Check active tokens
echo "3. Active OAuth tokens:"
docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import valid_tokens
print(f'Total: {len(valid_tokens)}')
"

# Check for write operation attempts
echo "4. Blocked write operations:"
docker-compose logs mcp-server-chatgpt | grep "Write operations not allowed"

# Review recent connections
echo "5. Recent connections:"
docker-compose logs nginx | grep -E "POST /chatgpt/sse" | tail -20

# Check SSL certificate status
echo "6. SSL certificate expiration:"
docker-compose exec certbot certbot certificates

echo ""
echo "Audit complete"
```

**Incident Response Procedure:**
```markdown
## Security Incident Response

### Phase 1: Detection (0-15 minutes)
1. Alert triggered by monitoring system
2. Verify incident authenticity
3. Assess severity level
4. Notify security team

### Phase 2: Containment (15-60 minutes)
1. Revoke compromised OAuth tokens:
   ```python
   from server_chatgpt import valid_tokens
   valid_tokens.clear()
   ```

2. Block suspicious IPs in NGINX:
   ```nginx
   deny 1.2.3.4;
   ```

3. Enable enhanced logging:
   ```bash
   docker-compose exec mcp-server-chatgpt \
     python -c "import logging; logging.getLogger().setLevel(logging.DEBUG)"
   ```

### Phase 3: Investigation (1-4 hours)
1. Collect logs:
   ```bash
   docker-compose logs --since 24h > incident_logs.txt
   ```

2. Analyze access patterns
3. Identify attack vector
4. Document findings

### Phase 4: Recovery (4-24 hours)
1. Patch vulnerabilities
2. Reset credentials if compromised
3. Restore from backup if needed
4. Implement additional controls

### Phase 5: Post-Incident (24+ hours)
1. Root cause analysis
2. Update security policies
3. Improve monitoring
4. Team debrief
```

---

## Part 8: Advanced Topics and Best Practices (80:00-90:00)

### 80:00 — Multi-Tenant Architecture

**Scope-Based Isolation:**
```nginx
# In nginx/conf.d/default.conf

# ChatGPT scope
location ~ ^/chatgpt/(.*)$ {
    rewrite ^/chatgpt(/.*)$ $1 break;
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_set_header X-Environment-Path /chatgpt;
}

# Claude scope
location ~ ^/claude/(.*)$ {
    rewrite ^/claude(/.*)$ $1 break;
    proxy_pass http://mcp-server-claude:8009;
    proxy_set_header X-Environment-Path /claude;
}

# Customer A scope
location ~ ^/customer-a/(.*)$ {
    rewrite ^/customer-a(/.*)$ $1 break;
    proxy_pass http://mcp-server-customer-a:8010;
    proxy_set_header X-Environment-Path /customer-a;
}
```

**Tenant-Specific Configuration:**
```python
# server_multi_tenant.py

TENANT_CONFIG = {
    "/chatgpt": {
        "database": os.getenv("CHATGPT_DB"),
        "max_results": 50,
        "cache_ttl": 3600,
        "allowed_hosts": ["chatgpt.com", "openai.com"]
    },
    "/claude": {
        "database": os.getenv("CLAUDE_DB"),
        "max_results": 100,
        "cache_ttl": 7200,
        "allowed_hosts": ["claude.ai", "anthropic.com"]
    }
}

def get_tenant_config(env_path: str) -> dict:
    """Get configuration for specific tenant."""
    return TENANT_CONFIG.get(env_path, TENANT_CONFIG["/chatgpt"])
```

### 82:00 — Rate Limiting

**NGINX Rate Limiting:**
```nginx
# In nginx.conf http block

# Define rate limit zones
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=oauth:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=tools:10m rate=20r/s;

server {
    # Apply to OAuth endpoints
    location ~ ^/chatgpt/(register|authorize|token)$ {
        limit_req zone=oauth burst=10 nodelay;
        # ... rest of config
    }
    
    # Apply to SSE endpoint
    location = /chatgpt/sse {
        limit_req zone=tools burst=50 nodelay;
        # ... rest of config
    }
}
```

**Application-Level Rate Limiting:**
```python
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, rate_per_minute=60):
        self.rate = rate_per_minute
        self.buckets = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed for client.
        
        Args:
            client_id: OAuth client identifier
            
        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.buckets[client_id] = [
            req_time for req_time in self.buckets[client_id]
            if req_time > minute_ago
        ]
        
        # Check rate
        if len(self.buckets[client_id]) >= self.rate:
            return False
        
        # Allow and record
        self.buckets[client_id].append(now)
        return True

# Global rate limiter
rate_limiter = RateLimiter(rate_per_minute=60)

# Use in handler
async def handle_tools_call(request_id, params):
    """Handle tools/call with rate limiting."""
    # Extract client_id from token
    token = _extract_bearer_token(request)
    client_id = valid_tokens.get(token, {}).get("client_id")
    
    if not rate_limiter.is_allowed(client_id):
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": "Rate limit exceeded. Try again later."
            }
        }, status_code=429)
    
    # Process request...
```

### 84:00 — Advanced Query Optimization

**Query Result Pagination:**
```python
def handle_search_with_pagination(query: str, page: int = 1, page_size: int = 50) -> str:
    """
    Execute search with pagination support.
    
    Args:
        query: SQL query or natural language
        page: Page number (1-indexed)
        page_size: Results per page
        
    Returns:
        JSON with results and pagination metadata
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Modify query for pagination
    if "SELECT" in query.upper():
        # Add OFFSET-FETCH for SQL Server
        if "ORDER BY" not in query.upper():
            query += " ORDER BY (SELECT NULL)"  # Required for OFFSET
        
        query += f" OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY"
    
    # Execute query
    result = execute_sql_impl(query)
    result_data = json.loads(result)
    
    # Add pagination metadata
    result_data["pagination"] = {
        "page": page,
        "page_size": page_size,
        "has_more": len(result_data.get("results", [])) == page_size
    }
    
    return json.dumps(result_data)
```

**Query Caching with Redis:**
```python
import redis
import hashlib

# Connect to Redis
redis_client = redis.Redis(host='redis', port=6379, db=0)

def get_query_cache_key(query: str) -> str:
    """Generate cache key from query."""
    return f"query:{hashlib.sha256(query.encode()).hexdigest()}"

def handle_search_with_redis_cache(query: str) -> str:
    """Execute search with Redis caching."""
    cache_key = get_query_cache_key(query)
    
    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        logger.info(f"Redis cache hit: {query[:50]}")
        return cached.decode()
    
    # Execute query
    result = handle_search(query)
    
    # Cache result
    redis_client.setex(cache_key, CACHE_TTL_SECONDS, result)
    logger.info(f"Cached query result: {query[:50]}")
    
    return result
```

### 86:00 — Observability Best Practices

**Distributed Tracing:**
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

tracer = trace.get_tracer(__name__)

# Use in handlers
async def handle_tools_call_with_tracing(request_id, params):
    """Handle tools/call with distributed tracing."""
    with tracer.start_as_current_span("tools_call") as span:
        span.set_attribute("request_id", request_id)
        span.set_attribute("tool_name", params.get("name"))
        
        try:
            result = await handle_tools_call(request_id, params)
            span.set_attribute("status", "success")
            return result
        except Exception as e:
            span.set_attribute("status", "error")
            span.record_exception(e)
            raise
```

### 88:00 — Disaster Recovery

**Backup Strategy:**
```markdown
## Backup Strategy

### Daily Backups
- Database: Full backup at 02:00 UTC
- Configuration: /etc, .env files
- Logs: Last 7 days
- Retention: 30 days

### Weekly Backups
- Full system snapshot
- Certificate backups
- Retention: 90 days

### Monthly Backups
- Archive to cloud storage (S3/Azure Blob)
- Retention: 1 year

### Recovery Time Objectives (RTO)
- Database: 1 hour
- Application: 30 minutes
- SSL Certificates: 2 hours

### Recovery Point Objectives (RPO)
- Database: 24 hours
- Configuration: 1 hour
```

**Disaster Recovery Runbook:**
```bash
#!/bin/bash
# disaster-recovery.sh

echo "=== Disaster Recovery Procedure ==="

# Step 1: Assess damage
echo "1. Assessing system status..."
docker-compose ps
curl -f https://data.forensic-bot.com/health || echo "Server unreachable"

# Step 2: Stop all services
echo "2. Stopping services..."
docker-compose down

# Step 3: Restore database
echo "3. Restoring database..."
./restore-database.sh /backups/latest.bak.gz

# Step 4: Restore configuration
echo "4. Restoring configuration..."
cp /backups/config/.env .
cp /backups/config/nginx.conf nginx/

# Step 5: Restore certificates
echo "5. Restoring SSL certificates..."
cp -r /backups/certbot/* certbot/

# Step 6: Start services
echo "6. Starting services..."
docker-compose up -d

# Step 7: Verify
echo "7. Verifying recovery..."
sleep 10
curl -f https://data.forensic-bot.com/health && echo "Recovery successful!"

# Step 8: Notify
echo "8. Notifying team..."
# Send notification to team
```

### 90:00 — Conclusion and Resources

**Key Takeaways:**
1. **Security First**: OAuth 2.0, TLS, read-only mode, IP whitelisting
2. **ChatGPT Integration**: Purpose-built tools (search/fetch) with caching
3. **Scalability**: Containerized deployment, rate limiting, caching
4. **Operations**: Monitoring, logging, backup, incident response
5. **Best Practices**: Testing, documentation, observability

**Additional Resources:**
- MCP Specification: https://spec.modelcontextprotocol.io
- OAuth 2.0 RFC 6749: https://tools.ietf.org/html/rfc6749
- ChatGPT Connectors: https://platform.openai.com/docs/actions
- SQL Server ODBC: https://learn.microsoft.com/en-us/sql/connect/odbc/
- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices/
- NGINX SSE Configuration: https://nginx.org/en/docs/http/ngx_http_proxy_module.html

**Next Steps:**
1. Review project knowledge base for complete code
2. Configure .env with your database credentials
3. Run setup-letsencrypt.sh for SSL
4. Deploy using docker-compose.prod.yml
5. Add connector in ChatGPT settings
6. Monitor logs and metrics
7. Iterate and improve based on usage

---

**Document Version**: 1.0.0  
**Last Updated**: October 2025  
**Compatibility**: ChatGPT (Deep Research), MCP 2025-06-18  
**Server**: server_chatgpt.py  
**Tested With**: Docker 20.10+, NGINX 1.24+, SQL Server 2019+, Python 3.11+

---

## Part 7: Production Operations (65:00-80:00)

### 65:00 — Logging Configuration

**Enhanced Logging Setup:**
```python
import logging
import json
from datetime import datetime

# Configure structured logging
class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easier parsing."""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add custom fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        return json.dumps(log_data)

# Setup logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())

logger = logging.getLogger("chatgpt_mcp")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage examples
def log_oauth_event(event_type, client_id, details=None):
    """Log OAuth events with context."""
    extra = {'user_id': client_id}
    logger.info(f"OAuth event: {event_type}", extra=extra)
    if details:
        logger.debug(f"Details: {json.dumps(details)}", extra=extra)

def log_tool_execution(tool_name, query, duration_ms, success=True):
    """Log tool execution metrics."""
    logger.info(
        f"Tool execution: {tool_name}",
        extra={
            'tool': tool_name,
            'query': query[:100],
            'duration_ms': duration_ms,
            'success': success
        }
    )

def log_error(error_msg, exception=None):
    """Log errors with full context."""
    logger.error(error_msg, exc_info=exception)
```

### 67:00 — Backup and Recovery

**Database Backup Script:**
```bash
#!/bin/bash
# backup-database.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mssql"
DATABASE="your_database"
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR

# Create backup using SQL Server native backup
docker-compose exec -T mcp-server-chatgpt python << EOF
import pyodbc
from server_chatgpt import get_db_config

_, conn_string = get_db_config()
# Modify for backup: remove read-only intent
conn_string = conn_string.replace("ApplicationIntent=ReadOnly", "ApplicationIntent=ReadWrite")

conn = pyodbc.connect(conn_string)
cursor = conn.cursor()

backup_path = f"/var/opt/mssql/backup/${DATABASE}_${TIMESTAMP}.bak"
cursor.execute(f"BACKUP DATABASE [{DATABASE}] TO DISK = '{backup_path}' WITH COMPRESSION, INIT")
conn.commit()
print(f"Backup created: {backup_path}")
EOF

# Copy backup from container
docker cp $(docker-compose ps -q mcp-server-chatgpt):/var/opt/mssql/backup/${DATABASE}_${TIMESTAMP}.bak \
    ${BACKUP_DIR}/

# Compress backup
gzip ${BACKUP_DIR}/${DATABASE}_${TIMESTAMP}.bak

# Upload to cloud storage (optional)
# aws s3 cp ${BACKUP_DIR}/${DATABASE}_${TIMESTAMP}.bak.gz s3://your-bucket/backups/

# Clean old backups
find $BACKUP_DIR -name "*.bak.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup complete: ${DATABASE}_${TIMESTAMP}.bak.gz"
```

**Recovery Procedure:**
```bash
#!/bin/bash
# restore-database.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.bak.gz>"
    exit 1
fi

# Decompress
gunzip -c $BACKUP_FILE > /tmp/restore.bak

# Copy to container
docker cp /tmp/restore.bak $(docker-compose ps -q mcp-server-chatgpt):/var/opt/mssql/backup/

# Restore
docker-compose exec -T mcp-server-chatgpt python << EOF
import pyodbc
from server_chatgpt import get_db_config

_, conn_string = get_db_config()
conn = pyodbc.connect(conn_string)
cursor = conn.cursor()

cursor.execute("RESTORE DATABASE [your_database] FROM DISK = '/var/opt/mssql/backup/restore.bak' WITH REPLACE")
conn.commit()
print("Database restored successfully")
EOF

# Cleanup
rm /tmp/restore.bak
```

### 69:00 — Monitoring and Alerts

**Prometheus Metrics Endpoint:**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response

# Define metrics
oauth_registrations = Counter('oauth_registrations_total', 'Total OAuth client registrations')
oauth_token_exchanges = Counter('oauth_token_exchanges_total', 'Total OAuth token exchanges')
tool_executions = Counter('tool_executions_total', 'Total tool executions', ['tool_name', 'status'])
tool_duration = Histogram('tool_execution_seconds', 'Tool execution duration', ['tool_name'])
active_tokens = Gauge('active_tokens', 'Number of active OAuth tokens')
cache_size = Gauge('search_cache_size', 'Number of entries in search cache')

# Update metrics in handlers
def handle_register():
    oauth_registrations.inc()
    # ... rest of handler

def handle_token():
    oauth_token_exchanges.inc()
    # ... rest of handler

def handle_tools_call(tool_name, query):
    start_time = time.time()
    try:
        result = execute_tool(tool_name, query)
        tool_executions.labels(tool_name=tool_name, status='success').inc()
        return result
    except Exception as e:
        tool_executions.labels(tool_name=tool_name, status='error').inc()
        raise
    finally:
        duration = time.time() - start_time
        tool_duration.labels(tool_name=tool_name).observe(duration)

# Metrics endpoint
@app.route("/metrics", methods=["GET"])
async def metrics(request: Request):
    """Prometheus metrics endpoint."""
    # Update gauges
    active_tokens.set(len(valid_tokens))
    cache_size.set(len(search_cache))
    
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

**Grafana Dashboard Configuration:**
```json
{
  "dashboard": {
    "title": "ChatGPT MCP Server Metrics",
    "panels": [
      {
        "title": "OAuth Activity",
        "targets": [
          {
            "expr": "rate(oauth_registrations_total[5m])",
            "legendFormat": "Registrations/min"
          },
          {
            "expr": "rate(oauth_token_exchanges_total[5m])",
            "legendFormat": "Token Exchanges/min"
          }
        ]
      },
      {
        "title": "Tool Execution Rate",
        "targets": [
          {
            "expr": "rate(tool_executions_total[5m])",
            "legendFormat": "{{tool_name}} - {{status}}"
          }
        ]
      },
      {
        "title": "Tool Execution Duration (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(tool_execution_seconds_bucket[5m]))",
            "legendFormat": "{{tool_name}}"
          }
        ]
      },
      {
        "title": "Active Tokens",
        "targets": [
          {
            "expr": "active_tokens",
            "legendFormat": "Active OAuth Tokens"
          }
        ]
      },
      {
        "title": "Cache Size",
        "targets": [
          {
            "expr": "search_cache_size",
            "legendFormat": "Search Cache Entries"
          }
        ]
      }
    ]
  }
}
```

### 72:00 — Cache Management

**Automatic Cache Cleanup:**
```python
import asyncio
from datetime import datetime, timedelta

async def cache_cleanup_task():
    """
    Background task to clean expired cache entries.
    Runs every 5 minutes.
    """
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            
            now = datetime.utcnow()
            expired_keys = []
            
            for key, value in search_cache.items():
                cached_time = datetime.fromisoformat(value['cached_at'])
                age_seconds = (now - cached_time).total_seconds()
                
                if age_seconds >= CACHE_TTL_SECONDS:
                    expired_keys.append(key)
            
            # Remove expired entries
            for key in expired_keys:
                del search_cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")

# Start cleanup task on server startup
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks."""
    asyncio.create_task(cache_cleanup_task())
    logger.info("Started cache cleanup task")
```

**Manual Cache Management Script:**
```bash
#!/bin/bash
# cache-management.sh

COMMAND=$1

case $COMMAND in
    "clear")
        docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import search_cache
search_cache.clear()
print('Cache cleared')
"
        ;;
    
    "stats")
        docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import search_cache, CACHE_TTL_SECONDS
from datetime import datetime

print(f'Total entries: {len(search_cache)}')
print(f'TTL: {CACHE_TTL_SECONDS} seconds')

if search_cache:
    oldest = min(search_cache.values(), key=lambda x: x['cached_at'])
    newest = max(search_cache.values(), key=lambda x: x['cached_at'])
    print(f'Oldest entry: {oldest[\"cached_at\"]}')
    print(f'Newest entry: {newest[\"cached_at\"]}')
"
        ;;
    
    "warm")
        echo "Warming cache with common queries..."
        docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import handle_search
# Execute common queries to populate cache
queries = ['list tables', 'sample Customers limit 10', 'sample Orders limit 10']
for q in queries:
    handle_search(q)
    print(f'Cached: {q}')
"
        ;;
    
    *)
        echo "Usage: $0 {clear|stats|warm}"
        exit 1
        ;;
esac
```

### 75:00 — Troubleshooting Common Issues

**Issue 1: 404 Not Found on Discovery**
```bash
# Diagnosis
curl -v https://data.forensic-bot.com/.well-known/oauth-authorization-server

# Check NGINX configuration
docker-compose exec nginx nginx -t
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf | grep "well-known"

# Verify X-Environment-Path header
docker-compose logs nginx | grep "X-Environment-Path"

# Fix: Ensure NGINX proxies root-level discovery to server
# See NGINX configuration section (43:00)
```

**Issue 2: 401 Unauthorized on SSE**
```bash
# Check token validity
docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import valid_tokens
from datetime import datetime
print('Active tokens:', len(valid_tokens))
for token, data in list(valid_tokens.items())[:5]:
    expires = datetime.fromisoformat(data['expires_at'])
    print(f'{token[:10]}... expires at {expires}')
"

# Re-authenticate
# Complete new OAuth flow to get fresh token
```

**Issue 3: Database Connection Failures**
```bash
# Test connection
docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import get_db_config
import pyodbc

try:
    _, conn_string = get_db_config()
    conn = pyodbc.connect(conn_string, timeout=10)
    cursor = conn.cursor()
    cursor.execute('SELECT @@VERSION')
    print('Connection successful:', cursor.fetchone()[0][:50])
except Exception as e:
    print('Connection failed:', e)
"

# Check firewall rules
# Verify database server allows connections from Docker network

# Check credentials
docker-compose exec mcp-server-chatgpt env | grep MSSQL
```

**Issue 4: Slow Query Performance**
```bash
# Enable query logging
docker-compose exec mcp-server-chatgpt python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
"

# Analyze slow queries
docker-compose logs mcp-server-chatgpt | grep "duration_ms" | \
    awk -F'duration_ms":' '{print $2}' | \
    awk '{print $1}' | \
    sort -n | tail -10

# Check database indexes
# Review execution plans for slow queries
```

### 78:00 — Security Incident Response

**Security Checklist:**
```bash
#!/bin/bash
# security-audit.sh

echo "=== Security Audit ==="
echo ""

# Check for unauthorized access attempts
echo "1. Failed authentication attempts:"
docker-compose logs mcp-server-chatgpt | grep "401" | wc -l

# Check for unusual query patterns
echo "2. Potential SQL injection attempts:"
docker-compose logs mcp-server-chatgpt | grep -i "union\|or 1=1\|drop table"

# Check active tokens
echo "3. Active OAuth tokens:"
docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import valid_tokens
print(f'Total: {len(valid_tokens)}')
"

# Check for write operation attempts
echo "4. Blocked write operations:"
docker-compose logs mcp-server-chatgpt | grep "Write operations not allowed"

# Review recent connections
echo "5. Recent connections:"
docker-compose logs nginx | grep -E "POST /chatgpt/sse" | tail -20

# Check SSL certificate status
echo "6. SSL certificate expiration:"
docker-compose exec certbot certbot certificates

echo ""
echo "Audit complete"
```

**Incident Response Procedure:**
```markdown
## Security Incident Response

### Phase 1: Detection (0-15 minutes)
1. Alert triggered by monitoring system
2. Verify incident authenticity
3. Assess severity level
4. Notify security team

### Phase 2: Containment (15-60 minutes)
1. Revoke compromised OAuth tokens:
   ```python
   from server_chatgpt import valid_tokens
   valid_tokens.clear()
   ```

2. Block suspicious IPs in NGINX:
   ```nginx
   deny 1.2.3.4;
   ```

3. Enable enhanced logging:
   ```bash
   docker-compose exec mcp-server-chatgpt \
     python -c "import logging; logging.getLogger().setLevel(logging.DEBUG)"
   ```

### Phase 3: Investigation (1-4 hours)
1. Collect logs:
   ```bash
   docker-compose logs --since 24h > incident_logs.txt
   ```

2. Analyze access patterns
3. Identify attack vector
4. Document findings

### Phase 4: Recovery (4-24 hours)
1. Patch vulnerabilities
2. Reset credentials if compromised
3. Restore from backup if needed
4. Implement additional controls

### Phase 5: Post-Incident (24+ hours)
1. Root cause analysis
2. Update security policies
3. Improve monitoring
4. Team debrief
```

---

## Part 8: Advanced Topics and Best Practices (80:00-90:00)

### 80:00 — Multi-Tenant Architecture

**Scope-Based Isolation:**
```nginx
# In nginx/conf.d/default.conf

# ChatGPT scope
location ~ ^/chatgpt/(.*)$ {
    rewrite ^/chatgpt(/.*)$ $1 break;
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_set_header X-Environment-Path /chatgpt;
}

# Claude scope
location ~ ^/claude/(.*)$ {
    rewrite ^/claude(/.*)$ $1 break;
    proxy_pass http://mcp-server-claude:8009;
    proxy_set_header X-Environment-Path /claude;
}

# Customer A scope
location ~ ^/customer-a/(.*)$ {
    rewrite ^/customer-a(/.*)$ $1 break;
    proxy_pass http://mcp-server-customer-a:8010;
    proxy_set_header X-Environment-Path /customer-a;
}
```

**Tenant-Specific Configuration:**
```python
# server_multi_tenant.py

TENANT_CONFIG = {
    "/chatgpt": {
        "database": os.getenv("CHATGPT_DB"),
        "max_results": 50,
        "cache_ttl": 3600,
        "allowed_hosts": ["chatgpt.com", "openai.com"]
    },
    "/claude": {
        "database": os.getenv("CLAUDE_DB"),
        "max_results": 100,
        "cache_ttl": 7200,
        "allowed_hosts": ["claude.ai", "anthropic.com"]
    }
}

def get_tenant_config(env_path: str) -> dict:
    """Get configuration for specific tenant."""
    return TENANT_CONFIG.get(env_path, TENANT_CONFIG["/chatgpt"])
```

### 82:00 — Rate Limiting

**NGINX Rate Limiting:**
```nginx
# In nginx.conf http block

# Define rate limit zones
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=oauth:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=tools:10m rate=20r/s;

server {
    # Apply to OAuth endpoints
    location ~ ^/chatgpt/(register|authorize|token)$ {
        limit_req zone=oauth burst=10 nodelay;
        # ... rest of config
    }
    
    # Apply to SSE endpoint
    location = /chatgpt/sse {
        limit_req zone=tools burst=50 nodelay;
        # ... rest of config
    }
}
```

**Application-Level Rate Limiting:**
```python
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, rate_per_minute=60):
        self.rate = rate_per_minute
        self.buckets = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed for client.
        
        Args:
            client_id: OAuth client identifier
            
        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.buckets[client_id] = [
            req_time for req_time in self.buckets[client_id]
            if req_time > minute_ago
        ]
        
        # Check rate
        if len(self.buckets[client_id]) >= self.rate:
            return False
        
        # Allow and record
        self.buckets[client_id].append(now)
        return True

# Global rate limiter
rate_limiter = RateLimiter(rate_per_minute=60)

# Use in handler
async def handle_tools_call(request_id, params):
    """Handle tools/call with rate limiting."""
    # Extract client_id from token
    token = _extract_bearer_token(request)
    client_id = valid_tokens.get(token, {}).get("client_id")
    
    if not rate_limiter.is_allowed(client_id):
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": "Rate limit exceeded. Try again later."
            }
        }, status_code=429)
    
    # Process request...
```

### 84:00 — Advanced Query Optimization

**Query Result Pagination:**
```python
def handle_search_with_pagination(query: str, page: int = 1, page_size: int = 50) -> str:
    """
    Execute search with pagination support.
    
    Args:
        query: SQL query or natural language
        page: Page number (1-indexed)
        page_size: Results per page
        
    Returns:
        JSON with results and pagination metadata
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Modify query for pagination
    if "SELECT" in query.upper():
        # Add OFFSET-FETCH for SQL Server
        if "ORDER BY" not in query.upper():
            query += " ORDER BY (SELECT NULL)"  # Required for OFFSET
        
        query += f" OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY"
    
    # Execute query
    result = execute_sql_impl(query)
    result_data = json.loads(result)
    
    # Add pagination metadata
    result_data["pagination"] = {
        "page": page,
        "page_size": page_size,
        "has_more": len(result_data.get("results", [])) == page_size
    }
    
    return json.dumps(result_data)
```

**Query Caching with Redis:**
```python
import redis
import hashlib

# Connect to Redis
redis_client = redis.Redis(host='redis', port=6379, db=0)

def get_query_cache_key(query: str) -> str:
    """Generate cache key from query."""
    return f"query:{hashlib.sha256(query.encode()).hexdigest()}"

def handle_search_with_redis_cache(query: str) -> str:
    """Execute search with Redis caching."""
    cache_key = get_query_cache_key(query)
    
    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        logger.info(f"Redis cache hit: {query[:50]}")
        return cached.decode()
    
    # Execute query
    result = handle_search(query)
    
    # Cache result
    redis_client.setex(cache_key, CACHE_TTL_SECONDS, result)
    logger.info(f"Cached query result: {query[:50]}")
    
    return result
```

### 86:00 — Observability Best Practices

**Distributed Tracing:**
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

tracer = trace.get_tracer(__name__)

# Use in handlers
async def handle_tools_call_with_tracing(request_id, params):
    """Handle tools/call with distributed tracing."""
    with tracer.start_as_current_span("tools_call") as span:
        span.set_attribute("request_id", request_id)
        span.set_attribute("tool_name", params.get("name"))
        
        try:
            result = await handle_tools_call(request_id, params)
            span.set_attribute("status", "success")
            return result
        except Exception as e:
            span.set_attribute("status", "error")
            span.record_exception(e)
            raise
```

### 88:00 — Disaster Recovery

**Backup Strategy:**
```markdown
## Backup Strategy

### Daily Backups
- Database: Full backup at 02:00 UTC
- Configuration: /etc, .env files
- Logs: Last 7 days
- Retention: 30 days

### Weekly Backups
- Full system snapshot
- Certificate backups
- Retention: 90 days

### Monthly Backups
- Archive to cloud storage (S3/Azure Blob)
- Retention: 1 year

### Recovery Time Objectives (RTO)
- Database: 1 hour
- Application: 30 minutes
- SSL Certificates: 2 hours

### Recovery Point Objectives (RPO)
- Database: 24 hours
- Configuration: 1 hour
```

**Disaster Recovery Runbook:**
```bash
#!/bin/bash
# disaster-recovery.sh

echo "=== Disaster Recovery Procedure ==="

# Step 1: Assess damage
echo "1. Assessing system status..."
docker-compose ps
curl -f https://data.forensic-bot.com/health || echo "Server unreachable"

# Step 2: Stop all services
echo "2. Stopping services..."
docker-compose down

# Step 3: Restore database
echo "3. Restoring database..."
./restore-database.sh /backups/latest.bak.gz

# Step 4: Restore configuration
echo "4. Restoring configuration..."
cp /backups/config/.env .
cp /backups/config/nginx.conf nginx/

# Step 5: Restore certificates
echo "5. Restoring SSL certificates..."
cp -r /backups/certbot/* certbot/

# Step 6: Start services
echo "6. Starting services..."
docker-compose up -d

# Step 7: Verify
echo "7. Verifying recovery..."
sleep 10
curl -f https://data.forensic-bot.com/health && echo "Recovery successful!"

# Step 8: Notify
echo "8. Notifying team..."
# Send notification to team
```

### 90:00 — Conclusion and Resources

**Key Takeaways:**
1. **Security First**: OAuth 2.0, TLS, read-only mode, IP whitelisting
2. **ChatGPT Integration**: Purpose-built tools (search/fetch) with caching
3. **Scalability**: Containerized deployment, rate limiting, caching
4. **Operations**: Monitoring, logging, backup, incident response
5. **Best Practices**: Testing, documentation, observability

**Additional Resources:**
- MCP Specification: https://spec.modelcontextprotocol.io
- OAuth 2.0 RFC 6749: https://tools.ietf.org/html/rfc6749
- ChatGPT Connectors: https://platform.openai.com/docs/actions
- SQL Server ODBC: https://learn.microsoft.com/en-us/sql/connect/odbc/
- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices/
- NGINX SSE Configuration: https://nginx.org/en/docs/http/ngx_http_proxy_module.html

**Next Steps:**
1. Review project knowledge base for complete code
2. Configure .env with your database credentials
3. Run setup-letsencrypt.sh for SSL
4. Deploy using docker-compose.prod.yml
5. Add connector in ChatGPT settings
6. Monitor logs and metrics
7. Iterate and improve based on usage

---

**Document Version**: 1.0.0  
**Last Updated**: October 2025  
**Compatibility**: ChatGPT (Deep Research), MCP 2025-06-18  
**Server**: server_chatgpt.py  
**Tested With**: Docker 20.10+, NGINX 1.24+, SQL Server 2019+, Python 3.11+