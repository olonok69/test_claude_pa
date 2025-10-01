# Extended Technical Guide: Building an MCP Server for Claude.ai Database Integration

## Table of Contents
- [Part 1: Introduction & Concepts (0:00-5:00)](#part-1-introduction--concepts-000-500)
- [Part 2: Architecture & Design (5:00-15:00)](#part-2-architecture--design-500-1500)
- [Part 3: Security Implementation (15:00-25:00)](#part-3-security-implementation-1500-2500)
- [Part 4: Development & Implementation (25:00-40:00)](#part-4-development--implementation-2500-4000)
- [Part 5: Deployment & Infrastructure (40:00-55:00)](#part-5-deployment--infrastructure-4000-5500)
- [Part 6: Testing & Validation (55:00-65:00)](#part-6-testing--validation-5500-6500)
- [Part 7: Production Operations (65:00-80:00)](#part-7-production-operations-6500-8000)
- [Part 8: Advanced Topics & Best Practices (80:00-90:00)](#part-8-advanced-topics--best-practices-8000-9000)

---

## Part 1: Introduction & Concepts (0:00-5:00)

### 0:00 — Opening & Hook
**"Welcome to this comprehensive technical guide on building a production-ready MCP server that securely connects your Microsoft SQL Server database to Claude.ai."**

In this extended tutorial, you'll learn to build an enterprise-grade bridge between your database and AI, implementing industry-standard security with OAuth 2.0, TLS encryption, and containerized deployment.

### 0:30 — What We'll Build
By the end of this guide, you'll have:
- A fully functional MCP (Model Context Protocol) server
- Secure OAuth 2.0 authentication with dynamic client registration
- Server-Sent Events (SSE) for real-time bidirectional communication
- Production-ready deployment with Docker, Nginx, and Let's Encrypt
- Complete monitoring, logging, and troubleshooting capabilities

### 1:00 — Why This Matters

**Traditional Approach Problems:**
- Manual data exports (time-consuming, error-prone)
- Copy-paste workflows (no audit trail)
- Stale data (snapshots become outdated)
- Security risks (credentials in emails/documents)
- No access control (all-or-nothing approach)

**MCP Server Benefits:**
- **Real-time Access**: Live database queries through natural language
- **Security**: OAuth 2.0 tokens, TLS encryption, short-lived credentials
- **Audit Trail**: Every query logged with user attribution
- **Access Control**: Granular permissions (read-only, specific tables, etc.)
- **Data Residency**: Your data stays in your infrastructure
- **Scalability**: Multi-tenant support for different teams/environments

### 2:00 — Real-World Use Cases

**Finance Team:**
```
Claude Query: "Show me revenue by product category for Q4 2024"
MCP Server → Execute SQL → Return formatted results
Benefits: Real-time financial analysis without exporting sensitive data
```

**Operations Team:**
```
Claude Query: "List all failed transactions in the last hour"
MCP Server → Query logs → Alert on patterns
Benefits: Immediate incident response with context
```

**Business Analysts:**
```
Claude Query: "Compare customer acquisition costs between regions"
MCP Server → Complex JOIN queries → Trend analysis
Benefits: Self-service analytics without SQL knowledge
```

### 3:00 — Understanding the Model Context Protocol (MCP)

**What is MCP?**
- Open protocol developed by Anthropic
- Specification version: 2025-06-18
- Standardizes how AI assistants consume external tools and data
- JSON-RPC based communication
- Transport agnostic (we use Server-Sent Events)

**Core Concepts:**

**1. Tools** - Actions the server can perform:
```json
{
  "name": "execute_sql",
  "description": "Execute SQL queries against database",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "SQL to execute"}
    }
  }
}
```

**2. Resources** - Data the server can provide (we focus on database tools)

**3. Prompts** - Template workflows (optional, not covered here)

**4. Sampling** - Server requesting LLM completions (optional)

### 4:00 — Why Server-Sent Events (SSE)?

**SSE Advantages:**
- Unidirectional persistent connection (server → client)
- Built on HTTP/HTTPS (works through firewalls)
- Auto-reconnection with Last-Event-ID
- Text-based (easy to debug)
- Native browser support
- Lower overhead than WebSockets for our use case

**SSE vs WebSockets:**
- SSE: Simpler, works over HTTP/2, better for server-push
- WebSockets: Bidirectional, binary support, more complex

**SSE vs Polling:**
- SSE: Real-time, efficient, single connection
- Polling: Delayed, wasteful, multiple requests

**Our Implementation:**
- SSE for transport layer
- JSON-RPC for message format
- Long-lived connections (24-hour timeout)
- OAuth Bearer token authentication

---

## Part 2: Architecture & Design (5:00-15:00)

### 5:00 — High-Level Architecture

```
┌─────────────────┐
│   CLAUDE.AI     │
│  (Web/Desktop)  │
│                 │
│ OAuth Client    │
│ SSE Consumer    │
└────────┬────────┘
         │ HTTPS (443)
         │ TLS 1.2+
         ▼
┌─────────────────┐
│     NGINX       │
│ Reverse Proxy   │
│                 │
│ - SSL Termin.   │
│ - Load Balance  │
│ - Rate Limit    │
└────────┬────────┘
         │ HTTP (8008)
         │ Internal
         ▼
┌─────────────────┐
│   MCP SERVER    │
│  (Python 3.11)  │
│                 │
│ - Starlette     │
│ - OAuth Logic   │
│ - Tool Handlers │
└────────┬────────┘
         │ ODBC
         │ TLS
         ▼
┌─────────────────┐
│  SQL SERVER     │
│   Database      │
│                 │
│ - User Mgmt     │
│ - Row Security  │
│ - Auditing      │
└─────────────────┘
```

### 6:00 — Component Deep Dive

**1. Claude.ai Client**
- Claude Desktop App (local MCP servers)
- Claude Web Interface (remote MCP servers)
- Initiates OAuth flow automatically
- Manages token refresh
- Presents tool capabilities to users

**2. NGINX Reverse Proxy**
- **Purpose**: Security boundary, SSL termination
- **Version**: 1.24+ recommended
- **Key Features**:
  - TLS 1.2/1.3 with modern ciphers
  - HTTP/2 support for performance
  - SSE-specific optimizations
  - Request/response buffering control
  - Connection timeout management

**NGINX Critical Settings for SSE:**
```nginx
location /demo/sse {
    proxy_pass http://mcp-server:8008;
    
    # CRITICAL: Disable buffering for SSE
    proxy_buffering off;
    proxy_cache off;
    
    # CRITICAL: Long timeouts for persistent connections
    proxy_read_timeout 86400s;  # 24 hours
    proxy_send_timeout 86400s;  # 24 hours
    
    # HTTP/1.1 required for SSE
    proxy_http_version 1.1;
    
    # SSE requires Connection: ''
    proxy_set_header Connection '';
    
    # Disable chunked transfer encoding
    chunked_transfer_encoding off;
    
    # Forward authentication
    proxy_set_header Authorization $http_authorization;
    
    # SSE response headers
    add_header Content-Type text/event-stream;
    add_header Cache-Control no-cache;
    add_header X-Accel-Buffering no;
}
```

**3. MCP Server (Python)**
- **Framework**: Starlette (async ASGI)
- **Language**: Python 3.11+
- **Libraries**:
  - `starlette`: ASGI framework
  - `pyodbc`: SQL Server connectivity
  - `python-dotenv`: Environment configuration
  - `secrets`: Secure token generation

**Server Responsibilities:**
- OAuth 2.0 implementation (AS + RS)
- MCP protocol handling (JSON-RPC)
- Tool execution (database operations)
- Data serialization (SQL types → JSON)
- Token validation and management
- Request logging and auditing

**4. SQL Server Database**
- **Version**: 2019+ recommended
- **Driver**: ODBC Driver 18 for SQL Server
- **Connection**: TLS encrypted
- **Authentication**: SQL Server authentication (username/password)

### 8:00 — Data Flow: Query Execution

**Step-by-Step Flow:**

```
1. User asks Claude: "Show me top 10 customers by revenue"

2. Claude analyzes and determines tool needed:
   Tool: execute_sql
   Arguments: {
     "query": "SELECT TOP 10 CustomerID, SUM(Revenue) as TotalRev..."
   }

3. Claude sends MCP request over SSE:
   POST /demo/sse
   Authorization: Bearer eyJ0eXAiOiJKV1Q...
   Content-Type: application/json
   
   {
     "jsonrpc": "2.0",
     "id": "req-123",
     "method": "tools/call",
     "params": {
       "name": "execute_sql",
       "arguments": {
         "query": "SELECT TOP 10..."
       }
     }
   }

4. MCP Server validates:
   - Bearer token valid and not expired?
   - User has permission for execute_sql?
   - Query is safe (if READ_ONLY_MODE, check for SELECT only)?

5. Execute query:
   - Open database connection (pooled)
   - Execute parameterized query
   - Fetch results
   - Serialize data types (Decimal, DateTime → JSON)
   - Close cursor

6. Send response:
   {
     "jsonrpc": "2.0",
     "id": "req-123",
     "result": {
       "content": [
         {
           "type": "text",
           "text": "[{\"CustomerID\": 1, \"TotalRev\": 150000}, ...]"
         }
       ]
     }
   }

7. Claude receives results, formats for user:
   "Here are your top 10 customers by revenue:
    1. CustomerID 1: $150,000
    2. CustomerID 2: $125,000
    ..."
```

### 10:00 — Request/Response Formats

**MCP Protocol Messages:**

**Initialize (Capability Negotiation):**
```json
// Client → Server
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {
      "roots": {"listChanged": true}
    },
    "clientInfo": {
      "name": "Claude Desktop",
      "version": "1.0.0"
    }
  }
}

// Server → Client
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-06-18",
    "capabilities": {
      "tools": {},
      "logging": {}
    },
    "serverInfo": {
      "name": "MSSQL MCP Server",
      "version": "2.0.0"
    }
  }
}
```

**List Tools:**
```json
// Client → Server
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}

// Server → Client
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "list_tables",
        "description": "List all tables in the database",
        "inputSchema": {
          "type": "object",
          "properties": {},
          "required": []
        }
      },
      {
        "name": "describe_table",
        "description": "Get table structure and metadata",
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
        "description": "Execute SQL query (SELECT only in read-only mode)",
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
        "description": "Get sample data from a table",
        "inputSchema": {
          "type": "object",
          "properties": {
            "table_name": {
              "type": "string",
              "description": "Name of the table"
            },
            "limit": {
              "type": "integer",
              "description": "Number of rows to return",
              "default": 10
            }
          },
          "required": ["table_name"]
        }
      }
    ]
  }
}
```

### 12:00 — Multi-Tenant Architecture

**Supporting Multiple Environments:**

```
Production Setup:
├── /demo/sse         → Demo environment (DemoDB, read-only)
├── /production/sse   → Production environment (ProdDB, read-write)
└── /analytics/sse    → Analytics environment (AnalyticsDB, read-only)

Each environment has:
- Separate database connection
- Different credentials
- Isolated OAuth scopes
- Custom tool permissions
- Independent monitoring
```

**Benefits:**
- Secure separation of concerns
- Different access levels per environment
- Team-specific configurations
- Safe testing environment
- Gradual rollout capability

**Implementation Pattern:**
```yaml
# docker-compose.yml
services:
  mcp-server-demo:
    environment:
      - MSSQL_DATABASE=DemoDB
      - READ_ONLY_MODE=true
      
  mcp-server-production:
    environment:
      - MSSQL_DATABASE=ProductionDB
      - READ_ONLY_MODE=false
      
  mcp-server-analytics:
    environment:
      - MSSQL_DATABASE=AnalyticsDB
      - READ_ONLY_MODE=true
```

### 14:00 — Scoping and Path Management

**Why Scoped Paths?**
- `/demo/sse` vs `/production/sse`
- Each scope has its own OAuth issuer
- Prevents token reuse across environments
- Clear separation in logs and monitoring

**NGINX Path Rewriting:**
```nginx
# Demo environment
location ~ ^/demo/(.*)$ {
    rewrite ^/demo(/.*)$ $1 break;
    proxy_pass http://mcp-server-demo:8008;
    proxy_set_header X-Environment-Path /demo;
}

# Production environment
location ~ ^/production/(.*)$ {
    rewrite ^/production(/.*)$ $1 break;
    proxy_pass http://mcp-server-production:8008;
    proxy_set_header X-Environment-Path /production;
}
```

**Server Uses X-Environment-Path:**
```python
# In server_oauth.py
def get_base_url(request: Request) -> str:
    env_path = request.headers.get("x-environment-path", "")
    proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("host", "domain.com")
    
    base = f"{proto}://{host}"
    if env_path:
        base += env_path
    
    return base  # e.g., "https://domain.com/demo"
```

---

## Part 3: Security Implementation (15:00-25:00)

### 15:00 — OAuth 2.0 Authorization Code Flow

**Why OAuth 2.0?**
- Industry standard (RFC 6749)
- Delegated authorization (no password sharing)
- Short-lived tokens (1-hour default)
- Refresh capability
- Scope-based permissions
- Auditable (who accessed what, when)

**Flow Diagram:**

```
┌──────────┐                               ┌──────────┐
│  Claude  │                               │   MCP    │
│ Desktop  │                               │  Server  │
└────┬─────┘                               └────┬─────┘
     │                                          │
     │  1. Initiate OAuth                       │
     ├─────────────────────────────────────────>│
     │     POST /demo/register                  │
     │     {client_name, redirect_uris}         │
     │                                          │
     │<─────────────────────────────────────────┤
     │     200 OK                               │
     │     {client_id, client_secret}           │
     │                                          │
     │  2. Authorization Request                │
     ├─────────────────────────────────────────>│
     │     GET /demo/authorize?                 │
     │       client_id=xxx&                     │
     │       redirect_uri=claude.ai/callback&   │
     │       state=random                       │
     │                                          │
     │<─────────────────────────────────────────┤
     │     302 Redirect                         │
     │     Location: redirect_uri?              │
     │       code=auth_code&state=random        │
     │                                          │
     │  3. Token Exchange                       │
     ├─────────────────────────────────────────>│
     │     POST /demo/token                     │
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
     │     POST /demo/sse                       │
     │     Authorization: Bearer eyJ...         │
     │                                          │
     │<═════════════════════════════════════════│
     │     SSE Stream (persistent)              │
     │                                          │
```

### 17:00 — OAuth Discovery (RFC 8414)

**Why Discovery?**
- Claude automatically finds OAuth endpoints
- No manual configuration needed
- Supports standard OAuth clients
- Version compatibility

**Discovery Endpoint Response:**
```json
GET /.well-known/oauth-authorization-server
Host: data.forensic-bot.com

{
  "issuer": "https://data.forensic-bot.com/demo",
  "authorization_endpoint": "https://data.forensic-bot.com/demo/authorize",
  "token_endpoint": "https://data.forensic-bot.com/demo/token",
  "registration_endpoint": "https://data.forensic-bot.com/demo/register",
  "token_endpoint_auth_methods_supported": [
    "client_secret_post",
    "client_secret_basic"
  ],
  "response_types_supported": ["code"],
  "grant_types_supported": [
    "authorization_code",
    "refresh_token"
  ],
  "code_challenge_methods_supported": ["S256"]
}
```

**Protected Resource Metadata:**
```json
GET /.well-known/oauth-protected-resource

{
  "resource": "https://data.forensic-bot.com/demo/sse",
  "oauth_authorization_server": "https://data.forensic-bot.com/demo",
  "bearer_methods_supported": ["header"],
  "resource_documentation": "https://data.forensic-bot.com/docs"
}
```

### 19:00 — Token Management

**Token Generation (Secure):**
```python
import secrets

def generate_token() -> str:
    """Generate cryptographically secure random token"""
    return secrets.token_urlsafe(32)  # 256 bits of entropy

# Example output: "dGhpcyBpcyBhIHJhbmRvbSB0b2tlbg"
```

**Token Storage (In-Memory for Demo):**
```python
from datetime import datetime, timedelta
from typing import Dict, Any

# Global token store
valid_tokens: Dict[str, Dict[str, Any]] = {}

def store_token(access_token: str, client_id: str) -> None:
    """Store token with expiration"""
    valid_tokens[access_token] = {
        "client_id": client_id,
        "issued_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }

def validate_token(access_token: str) -> bool:
    """Check if token exists and is not expired"""
    if access_token not in valid_tokens:
        return False
    
    token_data = valid_tokens[access_token]
    expires_at = datetime.fromisoformat(token_data["expires_at"])
    
    return datetime.utcnow() < expires_at
```

**Production Token Storage:**
```python
# For production, use persistent storage:
# - Redis (fast, in-memory, TTL support)
# - PostgreSQL (persistent, transactional)
# - DynamoDB (AWS, managed, scalable)

# Example with Redis:
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def store_token_redis(access_token: str, client_id: str) -> None:
    redis_client.setex(
        name=f"token:{access_token}",
        time=3600,  # 1 hour TTL
        value=json.dumps({"client_id": client_id})
    )
```

### 21:00 — Security Best Practices

**1. Read-Only Mode (Highly Recommended):**
```python
READ_ONLY_MODE = os.getenv("READ_ONLY_MODE", "true").lower() == "true"

def execute_sql_impl(query: str) -> str:
    if READ_ONLY_MODE:
        # Check query only contains SELECT
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT") and \
           not query_upper.startswith("WITH"):
            raise ValueError("Only SELECT queries allowed in read-only mode")
    
    # Execute query...
```

**2. Least Privilege Database User:**
```sql
-- Create read-only user for demo environment
CREATE LOGIN claude_demo WITH PASSWORD = 'SecurePassword123!';
CREATE USER claude_demo FOR LOGIN claude_demo;

-- Grant minimal permissions
GRANT CONNECT ON DATABASE::DemoDB TO claude_demo;
GRANT SELECT ON SCHEMA::dbo TO claude_demo;

-- For specific tables only
GRANT SELECT ON dbo.Customers TO claude_demo;
GRANT SELECT ON dbo.Orders TO claude_demo;

-- Deny dangerous operations
DENY INSERT, UPDATE, DELETE, EXECUTE ON SCHEMA::dbo TO claude_demo;
```

**3. Row-Level Security:**
```sql
-- Example: Users can only see their department's data
CREATE FUNCTION dbo.fn_securitypredicate(@DepartmentID AS int)
    RETURNS TABLE
    WITH SCHEMABINDING
AS
    RETURN SELECT 1 AS fn_securitypredicate_result
    WHERE @DepartmentID = CAST(SESSION_CONTEXT(N'DepartmentID') AS int)
        OR IS_MEMBER('db_owner') = 1;

CREATE SECURITY POLICY DepartmentFilter
    ADD FILTER PREDICATE dbo.fn_securitypredicate(DepartmentID)
    ON dbo.SensitiveData
    WITH (STATE = ON);
```

**4. SQL Server Auditing:**
```sql
-- Create audit specification
CREATE SERVER AUDIT MCP_Audit
TO FILE (FILEPATH = 'C:\Audits\', MAXSIZE = 100 MB)
WITH (ON_FAILURE = CONTINUE);

ALTER SERVER AUDIT MCP_Audit WITH (STATE = ON);

-- Audit all SELECT statements
CREATE DATABASE AUDIT SPECIFICATION MCP_DB_Audit
FOR SERVER AUDIT MCP_Audit
    ADD (SELECT ON DATABASE::DemoDB BY claude_demo)
WITH (STATE = ON);
```

### 23:00 — TLS/SSL Configuration

**Let's Encrypt Certificate Issuance:**
```bash
# Certbot command for certificate issuance
certbot certonly --webroot \
    -w /var/www/certbot \
    --email admin@domain.com \
    -d data.forensic-bot.com \
    --rsa-key-size 4096 \
    --agree-tos \
    --non-interactive

# Certificate files generated:
# /etc/letsencrypt/live/data.forensic-bot.com/fullchain.pem
# /etc/letsencrypt/live/data.forensic-bot.com/privkey.pem
```

**NGINX SSL Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name data.forensic-bot.com;
    
    # SSL Certificate
    ssl_certificate /etc/letsencrypt/live/data.forensic-bot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/data.forensic-bot.com/privkey.pem;
    
    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/data.forensic-bot.com/chain.pem;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

### 24:00 — Security Checklist

**Pre-Production Security Audit:**

✅ **Authentication & Authorization**
- [ ] OAuth 2.0 fully implemented
- [ ] Token expiration set to 1 hour or less
- [ ] Refresh token rotation enabled
- [ ] ALLOWED_REDIRECT_HOSTS configured correctly
- [ ] No test/development flags enabled

✅ **Database Security**
- [ ] READ_ONLY_MODE enabled (if applicable)
- [ ] Least-privilege database user
- [ ] No sa or admin accounts
- [ ] Row-level security implemented (if needed)
- [ ] Audit logging enabled
- [ ] Connection string in environment variables (not code)

✅ **Network Security**
- [ ] TLS 1.2+ enforced
- [ ] Strong cipher suites only
- [ ] HSTS header configured
- [ ] Firewall rules restrictive
- [ ] Rate limiting implemented
- [ ] CORS properly configured

✅ **Application Security**
- [ ] Input validation on all queries
- [ ] SQL injection prevention (parameterized queries)
- [ ] Error messages don't leak sensitive info
- [ ] Logging excludes passwords/tokens
- [ ] Dependencies updated and scanned
- [ ] Secrets in environment variables

---

## Part 4: Development & Implementation (25:00-40:00)

### 25:00 — Project Structure

**Repository Organization:**
```
mssql-mcp-server/
├── server_oauth.py          # Main MCP server for Claude.ai
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container build
├── docker-compose.yml      # Service orchestration
├── .env                    # Environment variables (gitignored)
├── .env.example            # Template for .env
├── nginx/
│   ├── nginx.conf          # Main NGINX config
│   └── conf.d/
│       └── default.conf    # Site configuration
├── certbot/
│   ├── conf/              # SSL certificates
│   └── www/               # ACME challenge
├── logs/
│   ├── nginx/             # NGINX logs
│   └── mcp/               # Application logs
├── docs/
│   ├── claude-connector-setup.md
│   ├── explanation_en.md
│   └── architecture.svg
├── tests/
│   ├── test_oauth.py
│   ├── test_tools.py
│   └── test_database.py
└── scripts/
    ├── setup-letsencrypt.sh
    ├── backup.sh
    └── health-check.sh
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

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.12.1
mypy==1.7.1
```

### 27:00 — Database Connection Management

**Connection String Builder:**
```python
from typing import Tuple, Dict
import os
import pyodbc

def get_db_config() -> Tuple[Dict[str, str], str]:
    """
    Build ODBC connection string from environment variables.
    
    Returns:
        Tuple of (config dict, connection string)
    
    Raises:
        ValueError: If required environment variables missing
    """
    config = {
        "driver": os.getenv("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server"),
        "server": os.getenv("MSSQL_HOST"),
        "user": os.getenv("MSSQL_USER"),
        "password": os.getenv("MSSQL_PASSWORD"),
        "database": os.getenv("MSSQL_DATABASE"),
        "trust_server_certificate": os.getenv("TrustServerCertificate", "yes"),
        "trusted_connection": os.getenv("Trusted_Connection", "no"),
        "application_intent": "ReadOnly" if READ_ONLY_MODE else "ReadWrite"
    }
    
    # Validate required fields
    if not all([config["server"], config["user"], 
                config["password"], config["database"]]):
        raise ValueError("Missing required database configuration")
    
    # Build connection string
    connection_string = (
        f"Driver={{{config['driver']}}};"
        f"Server={config['server']};"
        f"UID={config['user']};"
        f"PWD={config['password']};"
        f"Database={config['database']};"
        f"TrustServerCertificate={config['trust_server_certificate']};"
        f"Trusted_Connection={config['trusted_connection']};"
        f"ApplicationIntent={config['application_intent']};"
    )
    
    return config, connection_string
```

**Connection Pool (Production):**
```python
from contextlib import contextmanager
import queue
import threading

class ConnectionPool:
    """Simple connection pool for database connections"""
    
    def __init__(self, connection_string: str, pool_size: int = 5):
        self.connection_string = connection_string
        self.pool = queue.Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        
        # Initialize pool
        for _ in range(pool_size):
            conn = pyodbc.connect(connection_string)
            self.pool.put(conn)
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        conn = self.pool.get()
        try:
            yield conn
        finally:
            self.pool.put(conn)
    
    def close_all(self):
        """Close all connections in pool"""
        while not self.pool.empty():
            conn = self.pool.get()
            conn.close()
```

### 29:00 — Tool Implementation Details

**Tool 1: list_tables**
```python
def list_tables_impl() -> str:
    """
    List all tables in the database using INFORMATION_SCHEMA.
    
    Returns:
        JSON string of table list with schema info
    """
    _, connection_string = get_db_config()
    
    query = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """
    
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        
        tables = []
        for row in cursor.fetchall():
            tables.append({
                "schema": row.TABLE_SCHEMA,
                "name": row.TABLE_NAME,
                "type": row.TABLE_TYPE
            })
        
        return json.dumps({
            "tables": tables,
            "count": len(tables)
        }, indent=2)
```

**Tool 2: describe_table**
```python
def describe_table_impl(table_name: str) -> str:
    """
    Get detailed table structure including columns, types, constraints.
    
    Args:
        table_name: Name of table to describe
        
    Returns:
        JSON string with table metadata
    """
    _, connection_string = get_db_config()
    
    # Get columns
    columns_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """
    
    # Get primary keys
    pk_query = """
        SELECT 
            COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_NAME = ?
        AND CONSTRAINT_NAME LIKE 'PK_%'
    """
    
    # Get foreign keys
    fk_query = """
        SELECT 
            fk.name AS FK_NAME,
            COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS FK_COLUMN,
            OBJECT_NAME(fkc.referenced_object_id) AS REFERENCED_TABLE,
            COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS REFERENCED_COLUMN
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.foreign_key_columns AS fkc 
            ON fk.object_id = fkc.constraint_object_id
        WHERE OBJECT_NAME(fk.parent_object_id) = ?
    """
    
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        
        # Get columns
        cursor.execute(columns_query, (table_name,))
        columns = []
        for row in cursor.fetchall():
            col_info = {
                "name": row.COLUMN_NAME,
                "type": row.DATA_TYPE,
                "nullable": row.IS_NULLABLE == 'YES',
                "default": row.COLUMN_DEFAULT
            }
            if row.CHARACTER_MAXIMUM_LENGTH:
                col_info["max_length"] = row.CHARACTER_MAXIMUM_LENGTH
            columns.append(col_info)
        
        # Get primary keys
        cursor.execute(pk_query, (table_name,))
        primary_keys = [row.COLUMN_NAME for row in cursor.fetchall()]
        
        # Get foreign keys
        cursor.execute(fk_query, (table_name,))
        foreign_keys = []
        for row in cursor.fetchall():
            foreign_keys.append({
                "name": row.FK_NAME,
                "column": row.FK_COLUMN,
                "references": {
                    "table": row.REFERENCED_TABLE,
                    "column": row.REFERENCED_COLUMN
                }
            })
        
        return json.dumps({
            "table": table_name,
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
            "column_count": len(columns)
        }, indent=2)
```

**Tool 3: execute_sql (with safety checks)**
```python
def execute_sql_impl(query: str) -> str:
    """
    Execute SQL query with safety checks and proper error handling.
    
    Args:
        query: SQL query to execute
        
    Returns:
        JSON string with results or row count
        
    Raises:
        ValueError: If query violates read-only mode
        pyodbc.Error: If database error occurs
    """
    # Safety check: Read-only mode
    if READ_ONLY_MODE:
        query_upper = query.strip().upper()
        if not (query_upper.startswith("SELECT") or 
                query_upper.startswith("WITH")):
            raise ValueError(
                "Only SELECT/WITH queries allowed in read-only mode. "
                f"Query starts with: {query_upper.split()[0]}"
            )
    
    _, connection_string = get_db_config()
    
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(query)
            
            # Check if query returns results
            if cursor.description:
                # SELECT query - return results
                columns = [column[0] for column in cursor.description]
                rows = []
                
                for row in cursor.fetchall():
                    row_dict = {}
                    for idx, value in enumerate(row):
                        # Serialize complex types
                        row_dict[columns[idx]] = serialize_row_data(value)
                    rows.append(row_dict)
                
                return json.dumps({
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows)
                }, indent=2)
            else:
                # DML query - return affected rows
                conn.commit()
                return json.dumps({
                    "affected_rows": cursor.rowcount,
                    "operation": "success"
                }, indent=2)
                
        except pyodbc.Error as e:
            conn.rollback()
            logger.error(f"SQL Error: {str(e)}")
            raise
```

**Tool 4: get_table_sample**
```python
def get_table_sample_impl(table_name: str, limit: int = 10) -> str:
    """
    Get sample rows from a table.
    
    Args:
        table_name: Name of table
        limit: Number of rows to return (default 10)
        
    Returns:
        JSON string with sample data
    """
    # Validate limit
    if limit < 1 or limit > 1000:
        raise ValueError("Limit must be between 1 and 1000")
    
    # Build query
    query = f"SELECT TOP {limit} * FROM {table_name}"
    
    # Reuse execute_sql logic
    return execute_sql_impl(query)
```

### 33:00 — Data Serialization

**Handling SQL Server Data Types:**
```python
from decimal import Decimal
from datetime import datetime, date
import json

def serialize_row_data(data):
    """
    Convert pyodbc Row data to JSON-serializable format.
    
    Handles:
    - Decimal → float
    - datetime → ISO 8601 string
    - date → ISO 8601 string
    - bytes → base64 string
    - None → null
    
    Args:
        data: Value from database row
        
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
        import base64
        return base64.b64encode(data).decode('utf-8')
    elif isinstance(data, (int, float, str, bool)):
        return data
    else:
        # Fallback: convert to string
        return str(data)
```

### 35:00 — Error Handling Strategy

**Comprehensive Error Management:**
```python
from typing import Dict, Any
import traceback

class MCPError(Exception):
    """Base exception for MCP server errors"""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

class ToolExecutionError(MCPError):
    """Error during tool execution"""
    def __init__(self, message: str, tool_name: str, original_error: Exception):
        super().__init__(
            code=-32000,
            message=f"Tool execution failed: {message}",
            data={
                "tool": tool_name,
                "error_type": type(original_error).__name__,
                "error_message": str(original_error)
            }
        )

def safe_tool_execution(tool_name: str, tool_func, *args, **kwargs) -> Dict[str, Any]:
    """
    Execute tool with comprehensive error handling.
    
    Returns:
        MCP-compliant result or error response
    """
    try:
        result = tool_func(*args, **kwargs)
        return {
            "content": [
                {
                    "type": "text",
                    "text": result
                }
            ]
        }
    
    except ValueError as e:
        # Validation errors (e.g., read-only mode violation)
        logger.warning(f"Validation error in {tool_name}: {str(e)}")
        raise MCPError(
            code=-32602,
            message="Invalid parameters",
            data={"details": str(e)}
        )
    
    except pyodbc.Error as e:
        # Database errors
        logger.error(f"Database error in {tool_name}: {str(e)}")
        raise ToolExecutionError(
            message="Database operation failed",
            tool_name=tool_name,
            original_error=e
        )
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error in {tool_name}: {str(e)}")
        logger.error(traceback.format_exc())
        raise ToolExecutionError(
            message="Internal server error",
            tool_name=tool_name,
            original_error=e
        )
```

### 37:00 — Logging Configuration

**Structured Logging:**
```python
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/mcp-server.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("mcp_server")

def log_tool_execution(tool_name: str, args: Dict, duration_ms: float, success: bool):
    """Log tool execution for audit trail"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "tool_execution",
        "tool": tool_name,
        "arguments": args,
        "duration_ms": duration_ms,
        "success": success
    }
    
    if success:
        logger.info(json.dumps(log_entry))
    else:
        logger.error(json.dumps(log_entry))

def log_oauth_event(event_type: str, client_id: str, details: Dict):
    """Log OAuth-related events"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "oauth",
        "oauth_event": event_type,
        "client_id": client_id,
        "details": details
    }
    logger.info(json.dumps(log_entry))
```

### 39:00 — Environment Configuration

**.env Structure:**
```bash
# ==============================================
# DATABASE CONFIGURATION
# ==============================================
MSSQL_HOST=sql-server.database.windows.net
MSSQL_USER=claude_demo
MSSQL_PASSWORD=SecurePassword123!
MSSQL_DATABASE=DemoDB
MSSQL_DRIVER=ODBC Driver 18 for SQL Server

# ==============================================
# SQL SERVER CONNECTION SETTINGS
# ==============================================
TrustServerCertificate=yes
Trusted_Connection=no

# ==============================================
# SECURITY SETTINGS
# ==============================================
READ_ONLY_MODE=true
ALLOWED_REDIRECT_HOSTS=claude.ai,anthropic.com

# ==============================================
# SERVER CONFIGURATION
# ==============================================
SERVER_HOST=0.0.0.0
SERVER_PORT=8008
LOG_LEVEL=INFO

# ==============================================
# DEVELOPMENT/TESTING ONLY
# (Set to false in production)
# ==============================================
ALLOW_UNAUTH_METHODS=false
ALLOW_UNAUTH_TOOLS_CALL=false
DEBUG_MODE=false
```

---

## Part 5: Deployment & Infrastructure (40:00-55:00)

### 40:00 — Docker Containerization

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    apt-transport-https \
    gcc \
    g++ \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft repository for ODBC Driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list

# Install ODBC Driver 18 for SQL Server
RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get install -y unixodbc unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify ODBC installation
RUN odbcinst -j

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server_oauth.py .
COPY .env .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8008

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8008/health || exit 1

# Run server
CMD ["python", "server_oauth.py"]
```

### 42:00 — Docker Compose Orchestration

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  # MCP Server (Demo Environment)
  mcp-server-demo:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: mcp-server-demo
    expose:
      - "8008"
    environment:
      - MSSQL_HOST=${MSSQL_HOST}
      - MSSQL_USER=${MSSQL_USER}
      - MSSQL_PASSWORD=${MSSQL_PASSWORD}
      - MSSQL_DATABASE=${MSSQL_DATABASE}
      - MSSQL_DRIVER=ODBC Driver 18 for SQL Server
      - Trust_ServerCertificate=yes
      - Trusted_Connection=no
      - READ_ONLY_MODE=true
      - ALLOWED_REDIRECT_HOSTS=claude.ai,anthropic.com
    volumes:
      - ./logs/mcp:/app/logs
    networks:
      - mcp-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # NGINX Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: nginx-mcp
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
      - mcp-server-demo
    networks:
      - mcp-network
    restart: unless-stopped
    command: "/bin/sh -c 'while :; do sleep 6h & wait $${!}; nginx -s reload; done & nginx -g \"daemon off;\"'"

  # Certbot for SSL Certificate Management
  certbot:
    image: certbot/certbot
    container_name: certbot-mcp
    volumes:
      - ./certbot/conf:/etc/letsencrypt:rw
      - ./certbot/www:/var/www/certbot:rw
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    networks:
      - mcp-network
    restart: unless-stopped

networks:
  mcp-network:
    driver: bridge

volumes:
  mcp_logs:
    driver: local
  nginx_logs:
    driver: local
```

### 45:00 — NGINX Configuration Deep Dive

**nginx.conf (Main Configuration):**
```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 2048;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    
    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # CRITICAL: Enable slash merging to handle double slashes
    merge_slashes on;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss;
    
    # Include site configurations
    include /etc/nginx/conf.d/*.conf;
}
```

**conf.d/default.conf (Site Configuration):**
```nginx
# HTTP Server - Redirect to HTTPS
server {
    listen 80;
    server_name data.forensic-bot.com;
    
    # Let's Encrypt ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name data.forensic-bot.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/data.forensic-bot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/data.forensic-bot.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Demo Environment - Health Check
    location = /demo/health {
        rewrite ^/demo(/.*)$ $1 break;
        proxy_pass http://mcp-server-demo:8008;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Environment-Path /demo;
    }
    
    # Demo Environment - OAuth Discovery
    location ~ ^/demo/\.well-known/(oauth-authorization-server|oauth-protected-resource|openid-configuration)$ {
        rewrite ^/demo(/.*)$ $1 break;
        proxy_pass http://mcp-server-demo:8008;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Environment-Path /demo;
        add_header Access-Control-Allow-Origin * always;
    }
    
    # Demo Environment - SSE Endpoint
    location = /demo/sse {
        # OPTIONS for CORS preflight
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin * always;
            add_header Access-Control-Allow-Methods 'GET, POST, HEAD, OPTIONS' always;
            add_header Access-Control-Allow-Headers 'Authorization, Content-Type' always;
            return 204;
        }
        
        rewrite ^/demo(/.*)$ $1 break;
        proxy_pass http://mcp-server-demo:8008;
        
        # SSE-specific configuration (CRITICAL)
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        chunked_transfer_encoding off;
        
        # Forward headers
        proxy_set_header Authorization $http_authorization;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Environment-Path /demo;
        
        # SSE response headers
        add_header Content-Type text/event-stream;
        add_header Cache-Control no-cache;
        add_header X-Accel-Buffering no;
        add_header Access-Control-Allow-Origin * always;
    }
    
    # OAuth Endpoints
    location ~ ^/demo/(register|authorize|token)$ {
        rewrite ^/demo(/.*)$ $1 break;
        proxy_pass http://mcp-server-demo:8008;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header Content-Type $content_type;
        proxy_set_header X-Environment-Path /demo;
    }
}
```

### 48:00 — Let's Encrypt Setup

**Automated Setup Script (setup-letsencrypt.sh):**
```bash
#!/bin/bash
set -e

# Configuration
DOMAIN="data.forensic-bot.com"
EMAIL="admin@domain.com"
RSA_KEY_SIZE=4096
DATA_PATH="./certbot"
STAGING=0  # Set to 1 for testing

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Let's Encrypt Setup for $DOMAIN${NC}"

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Please install Docker first."
    exit 1
fi

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose down || true

# Create directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p "$DATA_PATH/conf"
mkdir -p "$DATA_PATH/www"

# Download recommended TLS parameters
echo -e "${YELLOW}Downloading TLS parameters...${NC}"
if [ ! -e "$DATA_PATH/conf/options-ssl-nginx.conf" ]; then
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$DATA_PATH/conf/options-ssl-nginx.conf"
fi

if [ ! -e "$DATA_PATH/conf/ssl-dhparams.pem" ]; then
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$DATA_PATH/conf/ssl-dhparams.pem"
fi

# Create dummy certificate for nginx to start
echo -e "${YELLOW}Creating dummy certificate...${NC}"
path="/etc/letsencrypt/live/$DOMAIN"
mkdir -p "$DATA_PATH/conf/live/$DOMAIN"
docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    --entrypoint "openssl" \
    certbot/certbot \
    req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "$path/privkey.pem" \
    -out "$path/fullchain.pem" \
    -subj "/CN=localhost"

# Start nginx with dummy certificate
echo -e "${YELLOW}Starting nginx...${NC}"
docker-compose up -d nginx
sleep 5

# Delete dummy certificate
echo -e "${YELLOW}Removing dummy certificate...${NC}"
docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    --entrypoint "rm" \
    certbot/certbot \
    -rf "/etc/letsencrypt/live/$DOMAIN" \
    "/etc/letsencrypt/archive/$DOMAIN" \
    "/etc/letsencrypt/renewal/$DOMAIN.conf"

# Request Let's Encrypt certificate
echo -e "${YELLOW}Requesting Let's Encrypt certificate...${NC}"
if [ $STAGING != "0" ]; then
    STAGING_ARG="--staging"
else
    STAGING_ARG=""
fi

docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    certbot/certbot \
    certonly --webroot \
    -w /var/www/certbot \
    $STAGING_ARG \
    --email $EMAIL \
    -d $DOMAIN \
    --rsa-key-size $RSA_KEY_SIZE \
    --agree-tos \
    --no-eff-email \
    --force-renewal

# Check if certificate was obtained
if [ ! -f "$DATA_PATH/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo -e "${RED}Failed to obtain certificate!${NC}"
    exit 1
fi

# Reload nginx with new certificate
echo -e "${YELLOW}Reloading nginx...${NC}"
docker-compose exec nginx nginx -s reload

# Start all services
echo -e "${YELLOW}Starting all services...${NC}"
docker-compose up -d

echo -e "${GREEN}Setup Complete!${NC}"
echo -e "Your server is now available at: ${GREEN}https://$DOMAIN${NC}"
```

### 50:00 — Health Checks & Monitoring

**Health Check Endpoint:**
```python
@app.route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """
    Health check endpoint for monitoring systems.
    
    Returns:
        JSON with server status and metadata
    """
    try:
        # Test database connection
        config, connection_string = get_db_config()
        with pyodbc.connect(connection_string, timeout=5) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            db_status = "connected"
    except Exception as e:
        logger.error(f"Health check database error: {str(e)}")
        db_status = "disconnected"
    
    # Calculate uptime
    uptime_seconds = int((datetime.utcnow() - server_start_time).total_seconds())
    
    return JSONResponse({
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime_seconds,
        "version": "2.0.0",
        "protocol": "MCP 2025-06-18",
        "transport": "sse",
        "oauth": "enabled",
        "database": {
            "status": db_status,
            "name": config.get("database"),
            "read_only": READ_ONLY_MODE
        },
        "tools": [
            "list_tables",
            "describe_table",
            "execute_sql",
            "get_table_sample"
        ]
    })
```

### 52:00 — Deployment Commands

**Initial Deployment:**
```bash
# Clone repository
git clone https://github.com/your-org/mssql-mcp-server.git
cd mssql-mcp-server

# Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# Run SSL setup
chmod +x setup-letsencrypt.sh
./setup-letsencrypt.sh

# Verify deployment
curl https://data.forensic-bot.com/demo/health
```

**Update Deployment:**
```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose build

# Zero-downtime restart
docker-compose up -d

# Verify
docker-compose ps
docker-compose logs -f mcp-server-demo
```

**Rollback Procedure:**
```bash
# Stop current deployment
docker-compose down

# Checkout previous version
git log --oneline -10  # Find commit to rollback to
git checkout <commit-hash>

# Redeploy
docker-compose up --build -d
```

### 54:00 — Infrastructure Checklist

**Pre-Production Checklist:**

✅ **DNS Configuration**
- [ ] A record points to server IP
- [ ] DNS propagation complete (24-48 hours)
- [ ] Test with `nslookup data.forensic-bot.com`

✅ **Firewall Rules**
- [ ] Port 80 open (Let's Encrypt validation)
- [ ] Port 443 open (HTTPS traffic)
- [ ] Port 22 restricted (SSH - your IP only)
- [ ] All other ports closed

✅ **SSL/TLS**
- [ ] Certificate obtained successfully
- [ ] Certificate chain valid
- [ ] Auto-renewal configured
- [ ] Test with SSL Labs (https://www.ssllabs.com/ssltest/)

✅ **Application**
- [ ] Health check endpoint responding
- [ ] OAuth discovery endpoints accessible
- [ ] Database connectivity verified
- [ ] Environment variables validated

✅ **Monitoring**
- [ ] Log rotation configured
- [ ] Health check monitoring enabled
- [ ] Alert system configured
- [ ] Backup strategy defined

---

## Part 6: Testing & Validation (55:00-65:00)

### 55:00 — Testing Strategy

**Test Pyramid:**
```
         ┌─────────────┐
         │   E2E Tests │  ← Full OAuth + SSE + Database
         └─────────────┘
        ┌───────────────┐
        │ Integration   │   ← Tool execution + Database
        │     Tests     │
        └───────────────┘
      ┌───────────────────┐
      │   Unit Tests      │    ← Individual functions
      └───────────────────┘
```

### 56:00 — Unit Tests

**test_database.py:**
```python
import pytest
import pyodbc
from unittest.mock import Mock, patch
from server_oauth import (
    get_db_config,
    serialize_row_data,
    list_tables_impl,
    execute_sql_impl
)

class TestDatabaseConnection:
    """Test database connection and configuration"""
    
    def test_get_db_config_success(self, monkeypatch):
        """Test successful database config retrieval"""
        monkeypatch.setenv("MSSQL_HOST", "testserver")
        monkeypatch.setenv("MSSQL_USER", "testuser")
        monkeypatch.setenv("MSSQL_PASSWORD", "testpass")
        monkeypatch.setenv("MSSQL_DATABASE", "testdb")
        
        config, conn_string = get_db_config()
        
        assert config["server"] == "testserver"
        assert config["user"] == "testuser"
        assert "testserver" in conn_string
        assert "testuser" in conn_string
    
    def test_get_db_config_missing_vars(self, monkeypatch):
        """Test error when required vars missing"""
        monkeypatch.delenv("MSSQL_HOST", raising=False)
        
        with pytest.raises(ValueError, match="Missing required"):
            get_db_config()

class TestDataSerialization:
    """Test data type serialization"""
    
    def test_serialize_decimal(self):
        """Test Decimal to float conversion"""
        from decimal import Decimal
        result = serialize_row_data(Decimal("123.45"))
        assert result == 123.45
        assert isinstance(result, float)
    
    def test_serialize_datetime(self):
        """Test datetime to ISO string"""
        from datetime import datetime
        dt = datetime(2025, 10, 1, 12, 30, 45)
        result = serialize_row_data(dt)
        assert result == "2025-10-01T12:30:45"
        assert isinstance(result, str)
    
    def test_serialize_none(self):
        """Test None handling"""
        result = serialize_row_data(None)
        assert result is None
    
    def test_serialize_bytes(self):
        """Test bytes to base64"""
        import base64
        data = b"test data"
        result = serialize_row_data(data)
        assert result == base64.b64encode(data).decode('utf-8')

class TestToolExecution:
    """Test individual tool functions"""
    
    @patch('server_oauth.pyodbc.connect')
    def test_list_tables_success(self, mock_connect):
        """Test list_tables returns valid JSON"""
        # Mock database response
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            Mock(TABLE_SCHEMA="dbo", TABLE_NAME="Customers", TABLE_TYPE="BASE TABLE"),
            Mock(TABLE_SCHEMA="dbo", TABLE_NAME="Orders", TABLE_TYPE="BASE TABLE")
        ]
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        result = list_tables_impl()
        
        import json
        data = json.loads(result)
        assert "tables" in data
        assert len(data["tables"]) == 2
        assert data["tables"][0]["name"] == "Customers"
    
    @patch('server_oauth.pyodbc.connect')
    def test_execute_sql_read_only_enforcement(self, mock_connect, monkeypatch):
        """Test read-only mode blocks writes"""
        monkeypatch.setenv("READ_ONLY_MODE", "true")
        
        with pytest.raises(ValueError, match="Only SELECT"):
            execute_sql_impl("DELETE FROM Customers")
    
    @patch('server_oauth.pyodbc.connect')
    def test_execute_sql_select_allowed(self, mock_connect, monkeypatch):
        """Test SELECT query is allowed in read-only mode"""
        monkeypatch.setenv("READ_ONLY_MODE", "true")
        
        mock_cursor = Mock()
        mock_cursor.description = [("CustomerID",), ("Name",)]
        mock_cursor.fetchall.return_value = [
            (1, "Test Customer")
        ]
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        result = execute_sql_impl("SELECT * FROM Customers")
        
        import json
        data = json.loads(result)
        assert "rows" in data
        assert len(data["rows"]) == 1
```

**test_oauth.py:**
```python
import pytest
from datetime import datetime, timedelta
from server_oauth import (
    generate_token,
    validate_token,
    store_token,
    is_redirect_uri_allowed
)

class TestTokenGeneration:
    """Test secure token generation"""
    
    def test_generate_token_uniqueness(self):
        """Tokens should be unique"""
        tokens = {generate_token() for _ in range(100)}
        assert len(tokens) == 100  # All unique
    
    def test_generate_token_length(self):
        """Token should have sufficient entropy"""
        token = generate_token()
        assert len(token) >= 32  # At least 32 characters

class TestTokenValidation:
    """Test token validation logic"""
    
    def test_validate_token_expired(self, monkeypatch):
        """Expired tokens should fail validation"""
        token = "test_token_123"
        
        # Store token with past expiration
        from server_oauth import valid_tokens
        valid_tokens[token] = {
            "client_id": "test_client",
            "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
        }
        
        assert validate_token(token) is False
    
    def test_validate_token_valid(self):
        """Valid tokens should pass"""
        token = "test_token_456"
        
        from server_oauth import valid_tokens
        valid_tokens[token] = {
            "client_id": "test_client",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        assert validate_token(token) is True

class TestRedirectValidation:
    """Test OAuth redirect URI validation"""
    
    def test_allowed_redirect(self, monkeypatch):
        """Claude.ai should be allowed"""
        monkeypatch.setenv("ALLOWED_REDIRECT_HOSTS", "claude.ai,anthropic.com")
        
        assert is_redirect_uri_allowed("https://claude.ai/callback") is True
    
    def test_disallowed_redirect(self, monkeypatch):
        """Unknown hosts should be blocked"""
        monkeypatch.setenv("ALLOWED_REDIRECT_HOSTS", "claude.ai")
        
        assert is_redirect_uri_allowed("https://evil.com/callback") is False
    
    def test_subdomain_allowed(self, monkeypatch):
        """Subdomains should be allowed"""
        monkeypatch.setenv("ALLOWED_REDIRECT_HOSTS", "claude.ai")
        
        assert is_redirect_uri_allowed("https://app.claude.ai/callback") is True
```

### 58:00 — Integration Tests

**test_integration.py:**
```python
import pytest
import json
from starlette.testclient import TestClient
from server_oauth import app

class TestOAuthFlow:
    """Test complete OAuth 2.0 flow"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_full_oauth_flow(self, client):
        """Test client registration → authorization → token"""
        
        # Step 1: Register client
        response = client.post("/demo/register", json={
            "client_name": "Test Client",
            "redirect_uris": ["https://claude.ai/callback"]
        })
        assert response.status_code == 200
        data = response.json()
        client_id = data["client_id"]
        client_secret = data["client_secret"]
        
        # Step 2: Request authorization
        response = client.get(f"/demo/authorize", params={
            "client_id": client_id,
            "redirect_uri": "https://claude.ai/callback",
            "state": "random_state"
        })
        assert response.status_code in [200, 302]
        
        # Extract authorization code from response
        if response.status_code == 302:
            location = response.headers["location"]
            assert "code=" in location
            code = location.split("code=")[1].split("&")[0]
        else:
            code = response.json()["authorization_code"]
        
        # Step 3: Exchange code for token
        response = client.post("/demo/token", data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret
        })
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "Bearer"
        assert token_data["expires_in"] == 3600

class TestMCPProtocol:
    """Test MCP protocol implementation"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def auth_token(self, client):
        """Get valid auth token"""
        # Register and get token
        reg_response = client.post("/demo/register", json={
            "client_name": "Test",
            "redirect_uris": ["https://claude.ai/callback"]
        })
        client_data = reg_response.json()
        
        auth_response = client.get("/demo/authorize", params={
            "client_id": client_data["client_id"],
            "redirect_uri": "https://claude.ai/callback",
            "state": "test"
        })
        code = auth_response.json()["authorization_code"]
        
        token_response = client.post("/demo/token", data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_data["client_id"],
            "client_secret": client_data["client_secret"]
        })
        return token_response.json()["access_token"]
    
    def test_initialize(self, client, auth_token):
        """Test MCP initialize method"""
        response = client.post("/demo/sse",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "Test", "version": "1.0"}
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert "result" in data
    
    def test_tools_list(self, client, auth_token):
        """Test tools/list method"""
        response = client.post("/demo/sse",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "tools" in data["result"]
        
        tool_names = [t["name"] for t in data["result"]["tools"]]
        assert "list_tables" in tool_names
        assert "describe_table" in tool_names
        assert "execute_sql" in tool_names
```

### 60:00 — End-to-End Testing

**Manual E2E Test Script:**
```bash
#!/bin/bash
# e2e-test.sh - End-to-end testing script

BASE_URL="https://data.forensic-bot.com/demo"

echo "=== E2E Testing: MCP Server ==="

# Test 1: Health Check
echo -e "\n1. Testing health endpoint..."
HEALTH=$(curl -s $BASE_URL/health)
echo $HEALTH | jq '.'
if echo $HEALTH | jq -e '.status == "healthy"' > /dev/null; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    exit 1
fi

# Test 2: OAuth Discovery
echo -e "\n2. Testing OAuth discovery..."
DISCOVERY=$(curl -s $BASE_URL/.well-known/oauth-authorization-server)
echo $DISCOVERY | jq '.'
if echo $DISCOVERY | jq -e '.issuer' > /dev/null; then
    echo "✓ OAuth discovery passed"
else
    echo "✗ OAuth discovery failed"
    exit 1
fi

# Test 3: Client Registration
echo -e "\n3. Testing client registration..."
REGISTER=$(curl -s -X POST $BASE_URL/register \
    -H "Content-Type: application/json" \
    -d '{"client_name":"E2E Test","redirect_uris":["https://claude.ai/callback"]}')
echo $REGISTER | jq '.'
CLIENT_ID=$(echo $REGISTER | jq -r '.client_id')
CLIENT_SECRET=$(echo $REGISTER | jq -r '.client_secret')

if [ -n "$CLIENT_ID" ] && [ -n "$CLIENT_SECRET" ]; then
    echo "✓ Client registration passed"
    echo "  Client ID: $CLIENT_ID"
else
    echo "✗ Client registration failed"
    exit 1
fi

# Test 4: Authorization
echo -e "\n4. Testing authorization..."
AUTH_RESPONSE=$(curl -s "$BASE_URL/authorize?client_id=$CLIENT_ID&redirect_uri=https://claude.ai/callback&state=test")
AUTH_CODE=$(echo $AUTH_RESPONSE | jq -r '.authorization_code // empty')

if [ -n "$AUTH_CODE" ]; then
    echo "✓ Authorization passed"
    echo "  Auth Code: $AUTH_CODE"
else
    echo "✗ Authorization failed"
    exit 1
fi

# Test 5: Token Exchange
echo -e "\n5. Testing token exchange..."
TOKEN_RESPONSE=$(curl -s -X POST $BASE_URL/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=authorization_code&code=$AUTH_CODE&client_id=$CLIENT_ID&client_secret=$CLIENT_SECRET")
echo $TOKEN_RESPONSE | jq '.'
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ -n "$ACCESS_TOKEN" ]; then
    echo "✓ Token exchange passed"
    echo "  Access Token: ${ACCESS_TOKEN:0:20}..."
else
    echo "✗ Token exchange failed"
    exit 1
fi

# Test 6: SSE Connection (HEAD)
echo -e "\n6. Testing SSE capability..."
SSE_HEAD=$(curl -I -s $BASE_URL/sse)
if echo "$SSE_HEAD" | grep -q "text/event-stream"; then
    echo "✓ SSE capability check passed"
else
    echo "✗ SSE capability check failed"
fi

# Test 7: MCP Initialize
echo -e "\n7. Testing MCP initialize..."
INIT_RESPONSE=$(curl -s -X POST $BASE_URL/sse \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "E2E Test", "version": "1.0"}
        }
    }')
echo $INIT_RESPONSE | jq '.'

if echo $INIT_RESPONSE | jq -e '.result' > /dev/null; then
    echo "✓ MCP initialize passed"
else
    echo "✗ MCP initialize failed"
    exit 1
fi

# Test 8: List Tools
echo -e "\n8. Testing tools/list..."
TOOLS_RESPONSE=$(curl -s -X POST $BASE_URL/sse \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    }')
echo $TOOLS_RESPONSE | jq '.'

TOOL_COUNT=$(echo $TOOLS_RESPONSE | jq '.result.tools | length')
if [ "$TOOL_COUNT" -ge 4 ]; then
    echo "✓ Tools list passed ($TOOL_COUNT tools available)"
else
    echo "✗ Tools list failed"
    exit 1
fi

echo -e "\n=== All E2E Tests Passed ✓ ==="
```

### 62:00 — Load Testing

**Load Test with Apache Bench:**
```bash
# Test concurrent SSE connections
ab -n 100 -c 10 \
   -H "Authorization: Bearer $TOKEN" \
   -p initialize.json \
   -T "application/json" \
   https://data.forensic-bot.com/demo/sse

# Where initialize.json contains:
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {"name": "Load Test", "version": "1.0"}
  }
}
```

**Results Analysis:**
```
Concurrency Level:      10
Time taken for tests:   5.234 seconds
Complete requests:      100
Failed requests:        0
Total transferred:      25600 bytes
Requests per second:    19.11 [#/sec]
Time per request:       523.4 [ms] (mean)
Time per request:       52.3 [ms] (mean, across all concurrent requests)
```

### 64:00 — Claude Desktop Integration Test

**Setup Claude Desktop:**
```json
// ~/.config/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "mssql-demo": {
      "url": "https://data.forensic-bot.com/demo/sse",
      "oauth": {
        "authorization_url": "https://data.forensic-bot.com/demo/authorize",
        "token_url": "https://data.forensic-bot.com/demo/token",
        "client_id": "",
        "client_secret": ""
      }
    }
  }
}
```

**Test Queries in Claude:**
```
1. "What tools do you have available?"
   Expected: Claude lists database tools

2. "List all tables in the database"
   Expected: Tool call to list_tables, results displayed

3. "Describe the Customers table"
   Expected: Tool call to describe_table, schema displayed

4. "Show me 5 sample records from Orders"
   Expected: Tool call to get_table_sample, data displayed

5. "Find customers from California"
   Expected: Tool call to execute_sql with WHERE clause

6. "Calculate total revenue by product category"
   Expected: Complex SQL with aggregation and grouping
```

---

## Part 7: Production Operations (65:00-80:00)

### 65:00 — Monitoring Setup

**Health Check Monitoring Script:**
```python
#!/usr/bin/env python3
# monitor_health.py

import requests
import time
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

HEALTH_URL = "https://data.forensic-bot.com/demo/health"
CHECK_INTERVAL = 300  # 5 minutes
ALERT_EMAIL = "admin@domain.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "alerts@domain.com"
SMTP_PASSWORD = "your_password"

def send_alert(subject: str, body: str):
    """Send email alert"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = ALERT_EMAIL
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Alert sent: {subject}")
    except Exception as e:
        print(f"Failed to send alert: {e}")

def check_health():
    """Check server health"""
    try:
        response = requests.get(HEALTH_URL, timeout=10)
        
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"
        
        data = response.json()
        
        if data.get("status") != "healthy":
            return False, f"Status: {data.get('status')}"
        
        if data.get("database", {}).get("status") != "connected":
            return False, "Database disconnected"
        
        return True, "All systems operational"
    
    except requests.exceptions.Timeout:
        return False, "Timeout after 10 seconds"
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def main():
    """Main monitoring loop"""
    print("Starting health monitoring...")
    consecutive_failures = 0
    last_alert_time = None
    
    while True:
        is_healthy, message = check_health()
        timestamp = datetime.now().isoformat()
        
        if is_healthy:
            print(f"[{timestamp}] ✓ {message}")
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            print(f"[{timestamp}] ✗ {message} (failures: {consecutive_failures})")
            
            # Alert after 3 consecutive failures
            if consecutive_failures >= 3:
                # Don't spam alerts - wait 1 hour between alerts
                if last_alert_time is None or \
                   (datetime.now() - last_alert_time).seconds > 3600:
                    send_alert(
                        subject="MCP Server Health Alert",
                        body=f"Server unhealthy for {consecutive_failures} checks.\n"
                             f"Last status: {message}\n"
                             f"Time: {timestamp}"
                    )
                    last_alert_time = datetime.now()
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
```

### 67:00 — Log Management

**Log Rotation Configuration:**
```bash
# /etc/logrotate.d/mcp-server
/app/logs/mcp/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        docker-compose exec mcp-server-demo kill -USR1 1
    endscript
}

/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 nginx nginx
    sharedscripts
    postrotate
        docker-compose exec nginx nginx -s reopen
    endscript
}
```

**Log Analysis Script:**
```bash
#!/bin/bash
# analyze_logs.sh

LOG_FILE="/app/logs/mcp/mcp-server.log"

echo "=== MCP Server Log Analysis ==="
echo "Date: $(date)"
echo ""

# Error analysis
echo "=== Error Summary ==="
grep "ERROR" $LOG_FILE | wc -l | xargs echo "Total errors:"
grep "ERROR" $LOG_FILE | tail -5
echo ""

# OAuth events
echo "=== OAuth Activity ==="
grep "oauth" $LOG_FILE | grep "register" | wc -l | xargs echo "Registrations:"
grep "oauth" $LOG_FILE | grep "token" | wc -l | xargs echo "Token exchanges:"
echo ""

# Tool usage
echo "=== Tool Usage Statistics ==="
grep "tool_execution" $LOG_FILE | \
    jq -r '.tool' 2>/dev/null | \
    sort | uniq -c | sort -rn
echo ""

# Performance
echo "=== Average Tool Execution Time ==="
grep "tool_execution" $LOG_FILE | \
    jq '.duration_ms' 2>/dev/null | \
    awk '{sum+=$1; count++} END {if(count>0) print sum/count " ms"}'
echo ""

# Database queries
echo "=== Top SQL Queries (Last 24h) ==="
grep "execute_sql" $LOG_FILE | \
    grep -A 1 "$(date -d '24 hours ago' '+%Y-%m-%d')" | \
    head -10
```

### 69:00 — Backup Strategy

**Database Backup Script:**
```bash
#!/bin/bash
# backup_database.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mssql"
DATABASE="DemoDB"
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR

# Backup using SQL Server native backup
docker-compose exec -T mcp-server-demo python << EOF
import pyodbc
from server_oauth import get_db_config

_, conn_string = get_db_config()
conn = pyodbc.connect(conn_string)
cursor = conn.cursor()

backup_path = f"/var/opt/mssql/backup/${DATABASE}_${TIMESTAMP}.bak"
cursor.execute(f"BACKUP DATABASE {DATABASE} TO DISK = '{backup_path}' WITH COMPRESSION")
conn.commit()
print(f"Backup created: {backup_path}")
EOF

# Copy backup from container
docker cp mcp-server-demo:/var/opt/mssql/backup/${DATABASE}_${TIMESTAMP}.bak \
    ${BACKUP_DIR}/

# Compress backup
gzip ${BACKUP_DIR}/${DATABASE}_${TIMESTAMP}.bak

# Clean old backups
find $BACKUP_DIR -name "*.bak.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup complete: ${DATABASE}_${TIMESTAMP}.bak.gz"
```

**Configuration Backup:**
```bash
#!/bin/bash
# backup_config.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/config"

mkdir -p $BACKUP_DIR

# Backup configuration files
tar -czf ${BACKUP_DIR}/config_${TIMESTAMP}.tar.gz \
    .env \
    docker-compose.yml \
    nginx/nginx.conf \
    nginx/conf.d/*.conf \
    server_oauth.py

# Backup certificates
tar -czf ${BACKUP_DIR}/certs_${TIMESTAMP}.tar.gz \
    certbot/conf/

echo "Configuration backup complete"
```

### 71:00 — Performance Optimization

**Database Query Optimization:**
```sql
-- Create indexes for frequently queried columns
CREATE NONCLUSTERED INDEX IX_Customers_State 
    ON Customers(State)
    INCLUDE (CustomerID, Name);

CREATE NONCLUSTERED INDEX IX_Orders_Date 
    ON Orders(OrderDate DESC)
    INCLUDE (CustomerID, TotalAmount);

-- Update statistics
UPDATE STATISTICS Customers WITH FULLSCAN;
UPDATE STATISTICS Orders WITH FULLSCAN;

-- Monitor query performance
SELECT 
    TOP 10
    qs.execution_count,
    qs.total_elapsed_time / qs.execution_count AS avg_elapsed_time,
    qt.text AS query_text
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) qt
WHERE qt.text NOT LIKE '%sys.%'
ORDER BY qs.total_elapsed_time DESC;
```

**NGINX Performance Tuning:**
```nginx
# nginx.conf

worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # Connection pooling
    keepalive_timeout 65;
    keepalive_requests 100;
    
    # Compression
    gzip on;
    gzip_comp_level 5;
    gzip_min_length 256;
    
    # Caching (for static content)
    open_file_cache max=10000 inactive=30s;
    open_file_cache_valid 60s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
}
```

### 73:00 — Disaster Recovery

**Disaster Recovery Plan:**

**1. System Failure**
```bash
# Restore from backup
cd /backups/config
tar -xzf config_latest.tar.gz

# Redeploy
docker-compose down
docker-compose up --build -d

# Verify
curl https://data.forensic-bot.com/demo/health
```

**2. Database Corruption**
```bash
# Restore database from backup
docker cp /backups/mssql/DemoDB_latest.bak.gz mcp-server-demo:/tmp/
docker-compose exec mcp-server-demo bash

# Inside container:
gunzip /tmp/DemoDB_latest.bak.gz
sqlcmd -S localhost -U sa -P $SA_PASSWORD -Q \
    "RESTORE DATABASE DemoDB FROM DISK = '/tmp/DemoDB_latest.bak' WITH REPLACE"
```

**3. Certificate Expiration**
```bash
# Force certificate renewal
docker-compose run --rm certbot renew --force-renewal

# Reload NGINX
docker-compose exec nginx nginx -s reload

# Verify
echo | openssl s_client -connect data.forensic-bot.com:443 -servername data.forensic-bot.com 2>/dev/null | openssl x509 -noout -dates
```

### 75:00 — Scaling Strategies

**Horizontal Scaling (Multiple Instances):**
```yaml
# docker-compose.yml

services:
  mcp-server-demo-1:
    # ... config
  
  mcp-server-demo-2:
    # ... config
  
  nginx:
    # Load balancer configuration
```

**NGINX Load Balancing:**
```nginx
upstream mcp_backend {
    least_conn;
    server mcp-server-demo-1:8008 max_fails=3 fail_timeout=30s;
    server mcp-server-demo-2:8008 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    location /demo/sse {
        proxy_pass http://mcp_backend;
        # ... SSE config
    }
}
```

### 77:00 — Security Auditing

**Audit Trail Query:**
```sql
-- View all database activity
SELECT 
    session_id,
    event_time,
    action_id,
    succeeded,
    database_name,
    statement,
    client_ip
FROM sys.fn_get_audit_file('/Audits/*.sqlaudit', DEFAULT, DEFAULT)
WHERE database_name = 'DemoDB'
AND event_time >= DATEADD(day, -7, GETUTCDATE())
ORDER BY event_time DESC;
```

**Access Log Analysis:**
```bash
# Analyze NGINX access logs
cat /var/log/nginx/access.log | \
    awk '{print $1}' | \
    sort | uniq -c | sort -rn | \
    head -20

# Failed authentication attempts
grep "401" /var/log/nginx/access.log | \
    awk '{print $1}' | \
    sort | uniq -c

# SSE connection duration
grep "/demo/sse" /var/log/nginx/access.log | \
    awk '{print $NF}' | \
    awk '{sum+=$1; count++} END {print "Average: " sum/count " seconds"}'
```

### 79:00 — Documentation & Runbooks

**Operational Runbook Template:**

**Runbook: Server Restart**
```markdown
## Procedure: Restart MCP Server

### Prerequisites
- SSH access to server
- Docker permissions
- Backup completed (last 24h)

### Steps
1. Verify current status
   ```bash
   docker-compose ps
   curl https://data.forensic-bot.com/demo/health
   ```

2. Notify users (if applicable)
   - Post maintenance window
   - Expected downtime: 2-3 minutes

3. Graceful shutdown
   ```bash
   docker-compose stop mcp-server-demo
   # Wait for connections to drain (30 seconds)
   ```

4. Start server
   ```bash
   docker-compose up -d mcp-server-demo
   ```

5. Verify health
   ```bash
   sleep 10  # Wait for startup
   curl https://data.forensic-bot.com/demo/health
   docker-compose logs --tail=50 mcp-server-demo
   ```

6. Test functionality
   - OAuth discovery accessible
   - SSE endpoint responsive
   - Database connectivity OK

### Rollback
If issues occur:
```bash
docker-compose down
git checkout <previous-stable-commit>
docker-compose up --build -d
```

### Post-Restart
- Monitor logs for 15 minutes
- Check error rates
- Verify client connections
```

---

## Part 8: Advanced Topics & Best Practices (80:00-90:00)

### 80:00 — Advanced OAuth Patterns

**Token Refresh Implementation:**
```python
def handle_token_refresh(refresh_token: str, client_id: str, client_secret: str) -> dict:
    """
    Handle refresh token grant.
    
    OAuth 2.0 RFC 6749 Section 6
    """
    # Validate refresh token
    if refresh_token not in refresh_tokens:
        raise MCPError(code=-32000, message="Invalid refresh token")
    
    token_data = refresh_tokens[refresh_token]
    
    # Verify client
    if token_data["client_id"] != client_id:
        raise MCPError(code=-32000, message="Client mismatch")
    
    # Generate new access token
    new_access_token = generate_token()
    new_refresh_token = generate_token()
    
    # Store tokens
    store_token(new_access_token, client_id)
    refresh_tokens[new_refresh_token] = {
        "client_id": client_id,
        "issued_at": datetime.utcnow().isoformat()
    }
    
    # Invalidate old refresh token (rotation)
    del refresh_tokens[refresh_token]
    
    return {
        "access_token": new_access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": new_refresh_token
    }
```

**PKCE Support (OAuth 2.0 Extension):**
```python
import hashlib
import base64

def verify_code_challenge(code_verifier: str, code_challenge: str, method: str = "S256") -> bool:
    """
    Verify PKCE code challenge.
    
    RFC 7636 - Proof Key for Code Exchange
    """
    if method == "plain":
        return code_verifier == code_challenge
    
    elif method == "S256":
        # SHA256 hash
        hash_bytes = hashlib.sha256(code_verifier.encode()).digest()
        # Base64 URL-safe encoding
        computed_challenge = base64.urlsafe_b64encode(hash_bytes).decode().rstrip('=')
        return computed_challenge == code_challenge
    
    return False
```

### 82:00 — Custom Tool Development

**Adding a Custom Analytics Tool:**
```python
@server.call_tool()
async def analyze_trends(arguments: dict) -> list[types.TextContent]:
    """
    Custom tool: Analyze sales trends with ML insights
    
    Args:
        arguments: {
            "table": str,
            "date_column": str,
            "metric_column": str,
            "period_days": int
        }
    """
    table = arguments.get("table")
    date_col = arguments.get("date_column")
    metric_col = arguments.get("metric_column")
    period = arguments.get("period_days", 30)
    
    query = f"""
        WITH DailyMetrics AS (
            SELECT 
                CAST({date_col} AS DATE) as MetricDate,
                SUM({metric_col}) as DailyTotal,
                AVG({metric_col}) as DailyAvg
            FROM {table}
            WHERE {date_col} >= DATEADD(day, -{period}, GETUTCDATE())
            GROUP BY CAST({date_col} AS DATE)
        ),
        Trends AS (
            SELECT
                MetricDate,
                DailyTotal,
                DailyAvg,
                AVG(DailyTotal) OVER (
                    ORDER BY MetricDate 
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ) as MovingAvg7Day,
                PERCENT_RANK() OVER (ORDER BY DailyTotal) as Percentile
            FROM DailyMetrics
        )
        SELECT
            MetricDate,
            DailyTotal,
            MovingAvg7Day,
            CASE 
                WHEN Percentile >= 0.9 THEN 'High'
                WHEN Percentile >= 0.5 THEN 'Normal'
                ELSE 'Low'
            END as TrendCategory
        FROM Trends
        ORDER BY MetricDate DESC
    """
    
    result = execute_sql_impl(query)
    
    # Add ML insights
    import json
    data = json.loads(result)
    
    analysis = {
        "data": data,
        "insights": {
            "trend": "increasing" if data["rows"][0]["MovingAvg7Day"] > 
                     data["rows"][-1]["MovingAvg7Day"] else "decreasing",
            "volatility": "high" if max(r["DailyTotal"] for r in data["rows"]) / 
                          min(r["DailyTotal"] for r in data["rows"]) > 2 else "normal"
        },
        "recommendations": [
            "Consider seasonal adjustments",
            "Monitor anomalies in high/low categories"
        ]
    }
    
    return [types.TextContent(
        type="text",
        text=json.dumps(analysis, indent=2)
    )]

# Register in tools list
tools.append(types.Tool(
    name="analyze_trends",
    description="Analyze trends with ML insights",
    inputSchema={
        "type": "object",
        "properties": {
            "table": {"type": "string"},
            "date_column": {"type": "string"},
            "metric_column": {"type": "string"},
            "period_days": {"type": "integer", "default": 30}
        },
        "required": ["table", "date_column", "metric_column"]
    }
))
```

### 84:00 — Performance Profiling

**Application Profiling:**
```python
import cProfile
import pstats
from functools import wraps

def profile_tool(func):
    """Decorator to profile tool execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        
        # Log top 10 time-consuming functions
        logger.info(f"Profile for {func.__name__}:")
        stats.print_stats(10)
        
        return result
    return wrapper

# Usage
@profile_tool
def execute_sql_impl(query: str) -> str:
    # ... implementation
```

### 86:00 — Compliance & Governance

**GDPR Data Access Request Handler:**
```python
def handle_data_access_request(user_id: str) -> dict:
    """
    Handle GDPR Article 15 - Right of Access
    
    Returns all data associated with a user
    """
    queries = {
        "personal_info": f"SELECT * FROM Customers WHERE UserID = ?",
        "orders": f"SELECT * FROM Orders WHERE CustomerID IN "
                 f"(SELECT CustomerID FROM Customers WHERE UserID = ?)",
        "logs": f"SELECT * FROM ActivityLogs WHERE UserID = ?"
    }
    
    _, conn_string = get_db_config()
    results = {}
    
    with pyodbc.connect(conn_string) as conn:
        for category, query in queries.items():
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                results[category] = rows
    
    return {
        "user_id": user_id,
        "request_date": datetime.utcnow().isoformat(),
        "data": results,
        "format": "JSON",
        "retention_policy": "30 days for logs, indefinite for personal info"
    }
```

### 88:00 — Future Enhancements

**Roadmap Ideas:**

1. **GraphQL Support**
   - Alternative to SQL for more flexible queries
   - Better for nested data structures

2. **Query Result Caching**
   - Redis integration
   - Configurable TTL
   - Cache invalidation strategies

3. **Advanced Security**
   - JWT tokens (self-contained)
   - mTLS for client authentication
   - Role-based access control (RBAC)

4. **Observability**
   - OpenTelemetry integration
   - Distributed tracing
   - Metrics export (Prometheus)

5. **Multi-Database Support**
   - PostgreSQL connector
   - MySQL connector
   - MongoDB connector

### 89:00 — Best Practices Summary

**Security:**
✓ Always use READ_ONLY_MODE in production
✓ Implement least-privilege database users
✓ Enable row-level security where needed
✓ Use short-lived tokens (1 hour max)
✓ Validate and whitelist redirect URIs
✓ Keep dependencies updated
✓ Enable comprehensive auditing

**Performance:**
✓ Implement connection pooling
✓ Use database indexes strategically
✓ Set appropriate timeout values
✓ Monitor query performance
✓ Implement caching where beneficial
✓ Use async/await properly

**Reliability:**
✓ Implement comprehensive error handling
✓ Add health checks and monitoring
✓ Configure log rotation
✓ Implement backup strategies
✓ Test disaster recovery procedures
✓ Document operational procedures

**Scalability:**
✓ Use stateless server design
✓ Implement horizontal scaling
✓ Use load balancing
✓ Monitor resource usage
✓ Plan capacity growth
✓ Implement rate limiting

### 90:00 — Conclusion

**Congratulations!** You now have a production-ready MCP server that:

✅ Securely connects Claude.ai to SQL Server
✅ Implements OAuth 2.0 authorization
✅ Uses Server-Sent Events for efficient communication
✅ Deploys with Docker and Docker Compose
✅ Has SSL/TLS encryption with Let's Encrypt
✅ Includes comprehensive monitoring and logging
✅ Supports multi-tenant architectures
✅ Follows security best practices

**Next Steps:**
1. Review and harden your security configuration
2. Implement comprehensive monitoring
3. Set up automated backups
4. Test disaster recovery procedures
5. Document your specific setup
6. Train your team on operations
7. Plan for scaling and growth

**Resources:**
- MCP Specification: https://spec.modelcontextprotocol.io
- OAuth 2.0 RFC: https://tools.ietf.org/html/rfc6749
- Let's Encrypt Docs: https://letsencrypt.org/docs/
- Docker Docs: https://docs.docker.com/
- SQL Server Docs: https://docs.microsoft.com/sql/

**Thank you for following this guide!**

---

**Document Version**: 2.0.0  
**Last Updated**: October 2025  
**Total Duration**: 90 minutes  
**Complexity**: Advanced  
**Target Audience**: DevOps Engineers, Backend Developers, Security Engineers  
**Prerequisites**: Python, Docker, SQL, OAuth 2.0, TLS/SSL concepts