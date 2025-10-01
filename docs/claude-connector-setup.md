# Claude.ai Connector Setup for MSSQL MCP Server

This comprehensive guide explains how to connect Claude.ai to the MSSQL MCP server using Server-Sent Events (SSE) and OAuth 2.0, via the `/demo` scope fronted by NGINX.

## Table of Contents
- [Scope and Capabilities](#scope-and-capabilities)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [NGINX Configuration](#nginx-configuration)
- [Deployment Steps](#deployment-steps)
- [Adding Server in Claude.ai](#adding-server-in-claudeai)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)
- [Testing and Verification](#testing-and-verification)

## Scope and Capabilities

### Protocol Specifications
- **Protocol**: MCP 2025-06-18
- **Transport**: Server-Sent Events (SSE)
- **Authentication**: OAuth 2.0 with dynamic client registration
- **Server**: `server_oauth.py` (Full SQL toolkit implementation)
- **Scope Path**: `/demo` (can be customized for production, marketing, etc.)

### Available Tools

Claude.ai has access to the complete SQL toolkit:

#### 1. list_tables
Lists all tables in the database using INFORMATION_SCHEMA.
```json
{
  "name": "list_tables",
  "description": "List all tables in the database",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

#### 2. describe_table
Get complete table structure including columns, types, and constraints.
```json
{
  "name": "describe_table",
  "description": "Get table structure and metadata",
  "inputSchema": {
    "type": "object",
    "properties": {
      "table_name": {"type": "string", "description": "Name of the table"}
    },
    "required": ["table_name"]
  }
}
```

#### 3. get_table_sample
Retrieve sample data from a table with configurable row limit.
```json
{
  "name": "get_table_sample",
  "description": "Get sample data from a table",
  "inputSchema": {
    "type": "object",
    "properties": {
      "table_name": {"type": "string", "description": "Name of the table"},
      "limit": {"type": "integer", "description": "Number of rows", "default": 10}
    },
    "required": ["table_name"]
  }
}
```

#### 4. execute_sql
Execute arbitrary SQL queries (SELECT/INSERT/UPDATE/DELETE depending on READ_ONLY_MODE).
```json
{
  "name": "execute_sql",
  "description": "Execute SQL query",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "SQL query to execute"}
    },
    "required": ["query"]
  }
}
```

## Architecture

### High-Level Architecture
```
Claude.ai ◄──HTTPS 443──► NGINX ◄──HTTP 8008──► mcp-server (server_oauth.py)
                           │                            │
                      (SSL/TLS)                   (OAuth 2.0)
                      (CORS/SSE)                        │
                           │                            ▼
                           └──────────────────► SQL Server Database
```

### Routing with /demo Scope

```
Request Flow:
1. Claude.ai → /demo/.well-known/oauth-authorization-server
2. NGINX → mcp-server:8008 (with X-Environment-Path: /demo)
3. Server → Returns issuer: https://domain.com/demo
4. Claude.ai → /demo/sse (SSE endpoint)
5. OAuth flow → /demo/register, /demo/authorize, /demo/token
```

### Key NGINX Behaviors

Configured in `nginx/conf.d/default.conf`:

1. **Proxies `/demo/*` traffic** to backend MCP server
2. **Scoped OAuth discovery** under `/demo/.well-known/`:
   - `oauth-authorization-server`
   - `oauth-protected-resource`
   - `openid-configuration`
3. **Handles Claude.ai quirks**:
   - Requests may append `/sse` after `.well-known` path
   - Example: `/demo/.well-known/oauth-authorization-server/sse`
   - NGINX redirects these back to proper discovery endpoint
4. **Root-level discovery fallback**:
   - `/.well-known/*` also proxied with `/demo` scope
   - Ensures Claude can discover regardless of probe location
5. **SSE optimization**: Disables buffering, extends timeouts to 24 hours
6. **Environment context**: Sends `X-Environment-Path: /demo` header

## Prerequisites

### Infrastructure Requirements
- Public domain with DNS A record (e.g., data.forensic-bot.com)
- Valid TLS certificates (Let's Encrypt via Certbot included)
- Docker Engine 20.10+
- Docker Compose 2.0+

### Database Requirements
- Microsoft SQL Server instance (2019+)
- Network connectivity from server to MSSQL
- Database user with appropriate permissions
- ODBC Driver 18 for SQL Server

### Access Requirements
- Claude.ai account (Pro or Team)
- Claude Desktop app (for local MCP servers) OR
- Claude Web interface (for remote MCP servers)
- Ability to configure custom MCP servers

## Environment Configuration

### Required Environment Variables

Create/update `.env` file with configuration for the demo environment:

```bash
# ==============================================
# Database Configuration (Required)
# ==============================================
MSSQL_HOST=your-sql-server.database.windows.net
MSSQL_USER=demo_user
MSSQL_PASSWORD=DemoPassword123!
MSSQL_DATABASE=DemoDB
MSSQL_DRIVER=ODBC Driver 18 for SQL Server

# ==============================================
# Database Connection Settings
# ==============================================
TrustServerCertificate=yes
Trusted_Connection=no

# ==============================================
# Security Configuration (Production)
# ==============================================
READ_ONLY_MODE=true
ALLOWED_REDIRECT_HOSTS=claude.ai,anthropic.com

# ==============================================
# Development/Testing Only (Set to false in production)
# ==============================================
ALLOW_UNAUTH_METHODS=false
ALLOW_UNAUTH_TOOLS_CALL=false

# ==============================================
# Optional: Environment Path Override
# (Not needed when using NGINX with X-Environment-Path header)
# ==============================================
# ENVIRONMENT_PATH=/demo
```

### Multi-Tenant Configuration

For multiple environments (demo, production, marketing):

```bash
# Demo environment (already configured above)
MSSQL_DATABASE=DemoDB
MSSQL_USER=demo_user
MSSQL_PASSWORD=DemoPassword123!

# Production environment (add separate service in docker-compose)
MSSQL_DATABASE_PROD=ProductionDB
MSSQL_USER_PROD=prod_user
MSSQL_PASSWORD_PROD=ProdPassword123!

# Marketing environment
MSSQL_DATABASE_MKT=MarketingDB
MSSQL_USER_MKT=mkt_user
MSSQL_PASSWORD_MKT=MktPassword123!
```

See [Multi-Tenant Implementation Guide](./multi-tenant-implementation-guide.md) for complete setup.

### Environment Variable Descriptions

| Variable | Purpose | Default | Production Value |
|----------|---------|---------|------------------|
| `MSSQL_HOST` | SQL Server hostname | - | Your server FQDN |
| `MSSQL_USER` | Database username | - | Service account |
| `MSSQL_PASSWORD` | Database password | - | Strong password |
| `MSSQL_DATABASE` | Database name | - | Your database |
| `MSSQL_DRIVER` | ODBC driver | ODBC Driver 18 for SQL Server | Keep default |
| `TrustServerCertificate` | SSL trust mode | yes | yes/no per environment |
| `READ_ONLY_MODE` | Restrict to SELECT only | true | **true** (recommended) |
| `ALLOWED_REDIRECT_HOSTS` | OAuth redirect whitelist | claude.ai,anthropic.com | Keep default |
| `ALLOW_UNAUTH_METHODS` | Bypass OAuth (testing) | false | **false** |
| `ALLOW_UNAUTH_TOOLS_CALL` | Bypass tool auth (testing) | false | **false** |
| `ENVIRONMENT_PATH` | Scope path override | - | Not needed with NGINX |

## Backend Endpoints (server_oauth.py)

### Discovery Endpoints (RFC 9728)
| Endpoint | Purpose | Scope |
|----------|---------|-------|
| `/.well-known/oauth-authorization-server` | OAuth AS metadata | Root (fallback) |
| `/.well-known/oauth-protected-resource` | Resource metadata | Root (fallback) |
| `/demo/.well-known/oauth-authorization-server` | OAuth AS metadata | Scoped (primary) |
| `/demo/.well-known/oauth-protected-resource` | Resource metadata | Scoped (primary) |
| `/demo/.well-known/openid-configuration` | OIDC discovery | Scoped |

### OAuth 2.0 Endpoints
| Endpoint | Method | Purpose | Request Body |
|----------|--------|---------|--------------|
| `/demo/register` | POST | Dynamic client registration | `{client_name, redirect_uris}` |
| `/demo/authorize` | GET | Authorization code grant | Query params |
| `/demo/token` | POST | Token exchange | Form or JSON |

### MCP Transport
| Endpoint | Methods | Purpose | Authentication |
|----------|---------|---------|----------------|
| `/demo/sse` | HEAD/GET/OPTIONS | Capability checks, CORS | Optional |
| `/demo/sse` | POST | MCP JSON-RPC over SSE | Required (Bearer) |
| `/demo/health` | GET | Health status | None |

### Environment Path Handling

The server prioritizes `X-Environment-Path` header from NGINX:

```python
# In server_oauth.py
env_path = request.headers.get("x-environment-path") or os.getenv("ENVIRONMENT_PATH", "")
base_url = f"{forwarded_proto}://{host}"
if env_path:
    base_url = f"{base_url}{env_path}"

# Result: issuer = "https://domain.com/demo"
```

**Note**: `ENVIRONMENT_PATH` env var is only a fallback. When behind NGINX, the header is always used.

## NGINX Configuration

### Essential Configuration Snippets

These snippets are already present in `nginx/conf.d/default.conf`:

#### 1. Health Check Endpoint
```nginx
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
```

#### 2. Scoped OAuth Discovery
```nginx
# Main discovery endpoints under /demo
location ~ ^/demo/\.well-known/(oauth-authorization-server|oauth-protected-resource|openid-configuration)$ {
    rewrite ^/demo(/.*)$ $1 break;
    proxy_pass http://mcp-server-demo:8008;
    proxy_http_version 1.1;
    
    # Standard headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-Host $host;
    
    # CRITICAL: Tell backend this is for /demo scope
    proxy_set_header X-Environment-Path /demo;
    
    # CORS headers
    add_header Access-Control-Allow-Origin * always;
    add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS' always;
    add_header Access-Control-Allow-Headers 'Authorization, Content-Type' always;
}
```

#### 3. Root-Level Discovery (Fallback)
```nginx
# Claude may probe root-level discovery first
location ~ ^/\.well-known/(oauth-authorization-server|oauth-protected-resource)$ {
    proxy_pass http://mcp-server-demo:8008;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-Host $host;
    
    # Still set demo scope for proper issuer
    proxy_set_header X-Environment-Path /demo;
    
    add_header Access-Control-Allow-Origin * always;
    add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS' always;
    add_header Access-Control-Allow-Headers 'Authorization, Content-Type' always;
}
```

#### 4. Claude.ai Quirk Handling
```nginx
# Handle /demo/.well-known/{endpoint}/sse → redirect to /demo/.well-known/{endpoint}
location ~ ^/demo/\.well-known/(oauth-authorization-server|oauth-protected-resource|openid-configuration)/sse$ {
    rewrite ^/demo/\.well-known/(.*)/sse$ /demo/.well-known/$1 redirect;
}

# Handle /.well-known/{endpoint}/demo/sse → redirect to /demo/.well-known/{endpoint}
location ~ ^/\.well-known/(oauth-authorization-server|oauth-protected-resource)/demo/sse$ {
    return 302 /demo/.well-known/$1;
}

# Handle /demo/sse/.well-known/{endpoint} → redirect to /demo/.well-known/{endpoint}
location ~ ^/demo/sse/\.well-known/(oauth-authorization-server|oauth-protected-resource)$ {
    return 302 /demo/.well-known/$1;
}
```

#### 5. SSE Endpoint Configuration
```nginx
location = /demo/sse {
    # Handle OPTIONS for CORS preflight
    if ($request_method = 'OPTIONS') {
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods 'GET, POST, HEAD, OPTIONS' always;
        add_header Access-Control-Allow-Headers 'Authorization, Content-Type' always;
        add_header Access-Control-Max-Age 1728000;
        add_header Content-Type 'text/plain; charset=utf-8';
        add_header Content-Length 0;
        return 204;
    }
    
    # Strip /demo prefix
    rewrite ^/demo(/.*)$ $1 break;
    proxy_pass http://mcp-server-demo:8008;
    
    # SSE-specific settings (CRITICAL for long-lived connections)
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 86400s;  # 24 hours
    proxy_send_timeout 86400s;  # 24 hours
    chunked_transfer_encoding off;
    
    # Forward authorization
    proxy_set_header Authorization $http_authorization;
    
    # Standard headers
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
```

#### 6. OAuth Endpoints
```nginx
# Registration
location = /demo/register {
    rewrite ^/demo(/.*)$ $1 break;
    proxy_pass http://mcp-server-demo:8008;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header Content-Type $content_type;
    proxy_set_header X-Environment-Path /demo;
    add_header Access-Control-Allow-Origin * always;
}

# Authorization
location = /demo/authorize {
    rewrite ^/demo(/.*)$ $1 break;
    proxy_pass http://mcp-server-demo:8008;
    proxy_set_header X-Environment-Path /demo;
}

# Token Exchange
location = /demo/token {
    rewrite ^/demo(/.*)$ $1 break;
    proxy_pass http://mcp-server-demo:8008;
    proxy_set_header Content-Type $content_type;
    proxy_set_header X-Environment-Path /demo;
}
```

## Deployment Steps

### Step 1: Build Services

```powershell
# From repository root
docker compose build mcp-server-demo nginx

# Or use specific docker-compose file
docker compose -f docker-compose.prod.yml build mcp-server-demo nginx
```

### Step 2: Start Services

```powershell
# Start in detached mode
docker compose up -d mcp-server-demo nginx

# Or start with logs
docker compose up mcp-server-demo nginx
```

### Step 3: Verify Deployment

```powershell
# Check service status
docker compose ps

# View logs
docker compose logs -f mcp-server-demo
docker compose logs -f nginx

# Test specific service
docker compose logs mcp-server-demo | Select-String "OAuth\|SSE\|MCP"
```

## Testing and Verification

### 1. Health Check
```powershell
# Basic health check
curl https://data.forensic-bot.com/demo/health

# Expected response:
{
  "status": "healthy",
  "transport": "sse",
  "oauth": "enabled",
  "database": "DemoDB",
  "mcp_version": "2025-06-18",
  "tools": ["list_tables", "describe_table", "get_table_sample", "execute_sql"],
  "read_only": true
}
```

### 2. OAuth Discovery
```powershell
# Test scoped discovery (primary)
curl https://data.forensic-bot.com/demo/.well-known/oauth-authorization-server

# Test root-level discovery (fallback)
curl https://data.forensic-bot.com/.well-known/oauth-authorization-server

# Both should return issuer with /demo scope:
{
  "issuer": "https://data.forensic-bot.com/demo",
  "authorization_endpoint": "https://data.forensic-bot.com/demo/authorize",
  "token_endpoint": "https://data.forensic-bot.com/demo/token",
  "registration_endpoint": "https://data.forensic-bot.com/demo/register",
  ...
}
```

### 3. SSE Capability Check
```powershell
# HEAD request should return 200 with SSE headers
curl -I https://data.forensic-bot.com/demo/sse

# Expected headers:
HTTP/2 200
content-type: text/event-stream
cache-control: no-cache
x-accel-buffering: no
...
```

### 4. CORS Verification
```powershell
# OPTIONS preflight request
curl -X OPTIONS https://data.forensic-bot.com/demo/sse `
     -H "Origin: https://claude.ai" `
     -H "Access-Control-Request-Method: POST" `
     -H "Access-Control-Request-Headers: Authorization"

# Should return 204 with CORS headers
```

## Adding Server in Claude.ai

### Option 1: Claude Desktop App

#### Step 1: Locate Configuration File

Configuration location varies by OS:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

#### Step 2: Add MCP Server Configuration

```json
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

#### Step 3: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Relaunch the application
3. Claude will automatically initiate OAuth flow on first use

#### Step 4: Authorize Connection

1. Claude will prompt for authorization
2. Click "Authorize" or similar button
3. OAuth flow executes:
   - POST `/demo/register` → Get client credentials (auto-populated in config)
   - GET `/demo/authorize` → Redirect with code
   - POST `/demo/token` → Receive Bearer token
4. Connection established and tools become available

### Option 2: Claude Web Interface

*Note: Remote MCP server support varies by Claude.ai plan*

1. **Access Settings**
   - Navigate to Claude.ai
   - Click Settings → Integrations or MCP Servers

2. **Add Remote MCP Server**
   - Click "Add Remote MCP Server" or similar
   - Enter Base URL: `https://data.forensic-bot.com/demo/sse`

3. **OAuth Configuration**
   - Authentication: OAuth 2.0
   - Discovery: Automatic (via `.well-known/*`)
   - Click "Connect" or "Authorize"

4. **Complete Authorization**
   - Follow OAuth prompts
   - Grant necessary permissions
   - Verify connection success

### Verification in Claude

After setup, verify tools are available:

```text
User: "What tools do you have available?"
Claude: I have access to the following database tools:
- list_tables: List all tables in the database
- describe_table: Get table structure and metadata
- get_table_sample: Retrieve sample data from a table
- execute_sql: Execute SQL queries
```

## Usage Examples

### Basic Database Exploration

```text
User: "List all tables in the database"
Claude: [Calls list_tables tool]
Response: Shows complete list of tables

User: "Describe the structure of the Customers table"
Claude: [Calls describe_table with table_name="Customers"]
Response: Shows columns, data types, primary keys, foreign keys

User: "Show me 10 sample records from Orders"
Claude: [Calls get_table_sample with table_name="Orders", limit=10]
Response: Returns 10 rows from Orders table
```

### SQL Query Execution

```text
User: "Find all customers from California"
Claude: [Calls execute_sql with query]
Query: SELECT * FROM Customers WHERE State = 'CA'
Response: Returns matching customers

User: "Get total revenue by product category"
Claude: [Calls execute_sql with aggregation query]
Query: SELECT Category, SUM(Revenue) as TotalRevenue
       FROM Products p
       JOIN OrderDetails od ON p.ProductID = od.ProductID
       GROUP BY Category
       ORDER BY TotalRevenue DESC
Response: Aggregated revenue by category
```

### Complex Data Analysis

```text
User: "Analyze customer purchase patterns over the last 6 months"
Claude: [Calls multiple tools in sequence]
1. describe_table("Orders")
2. execute_sql("SELECT ...")
3. Further analysis based on results
Response: Comprehensive analysis with insights
```

### Multi-Step Workflows

```text
User: "Create a report showing top 10 customers by revenue with their order details"
Claude: [Orchestrates multiple tool calls]
1. list_tables → Identify relevant tables
2. describe_table("Customers") → Understand structure
3. describe_table("Orders") → Understand relationships
4. execute_sql(complex JOIN query) → Get top customers
5. Synthesizes results into formatted report
Response: Formatted report with customer analysis
```

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: 404 on Discovery URLs

**Symptoms:**
```
GET /demo/.well-known/oauth-authorization-server → 404
GET /.well-known/oauth-authorization-server → 404
```

**Solutions:**
1. Verify scoped discovery proxy exists: `/demo/.well-known/...`
2. Check root-level fallback proxy: `/.well-known/...`
3. Ensure `X-Environment-Path: /demo` header is set
4. Verify backend server is running: `docker compose ps mcp-server-demo`
5. Check NGINX config syntax: `docker compose exec nginx nginx -t`
6. Restart NGINX: `docker compose restart nginx`

**Verification:**
```powershell
# Test both paths
curl -v https://data.forensic-bot.com/demo/.well-known/oauth-authorization-server
curl -v https://data.forensic-bot.com/.well-known/oauth-authorization-server

# Check NGINX logs for routing
docker compose logs nginx | Select-String "demo"
```

#### Issue 2: 401 Unauthorized on /sse

**Symptoms:**
```
POST /demo/sse → 401 Unauthorized
Connection rejected by server
```

**Solutions:**
1. Ensure OAuth flow completed successfully
2. Verify Bearer token is valid and not expired
3. Check token is included in Authorization header
4. For testing only: set `ALLOW_UNAUTH_METHODS=true`
5. Verify `ALLOWED_REDIRECT_HOSTS` includes `claude.ai`

**Debug Commands:**
```powershell
# Check server OAuth logs
docker compose logs mcp-server-demo | Select-String "OAuth\|token\|401"

# Verify environment variables
docker compose exec mcp-server-demo env | Select-String "ALLOW_UNAUTH"

# Test with manual token (if available)
curl -H "Authorization: Bearer YOUR_TOKEN" `
     https://data.forensic-bot.com/demo/sse
```

#### Issue 3: 405 Method Not Allowed

**Symptoms:**
```
HEAD /demo/sse → 405
OPTIONS /demo/sse → 405
```

**Solutions:**
1. Verify server_oauth.py implements HEAD/OPTIONS handlers
2. Check NGINX doesn't block these methods
3. Ensure CORS configuration allows all methods
4. Review NGINX location block for method restrictions

**Verification:**
```powershell
# Test each method
curl -X HEAD https://data.forensic-bot.com/demo/sse
curl -X OPTIONS https://data.forensic-bot.com/demo/sse
curl -X GET https://data.forensic-bot.com/demo/sse
```

#### Issue 4: Redirect Blocked / OAuth Loop

**Symptoms:**
```
GET /authorize → Redirect blocked
OAuth flow stuck in redirect loop
```

**Solutions:**
1. Verify `ALLOWED_REDIRECT_HOSTS` includes `claude.ai`
2. Check redirect_uri validation in server_oauth.py
3. Ensure redirect_uri uses HTTPS
4. Verify domain matching is case-insensitive

**Configuration Check:**
```bash
# In .env
ALLOWED_REDIRECT_HOSTS=claude.ai,anthropic.com

# Or check default in server_oauth.py
# Should include claude.ai in default list
```

**Debug:**
```powershell
# Check OAuth authorization logs
docker compose logs mcp-server-demo | Select-String "authorize\|redirect"

# Test redirect validation
# Look for "Blocked authorization due to untrusted redirect" messages
```

#### Issue 5: SSE Connection Drops

**Symptoms:**
```
Connection established → Works briefly → Connection lost
SSE stream terminates unexpectedly
Timeout errors after period of inactivity
```

**Solutions:**
1. Verify NGINX SSE timeouts are set correctly:
   - `proxy_read_timeout 86400s;` (24 hours)
   - `proxy_send_timeout 86400s;` (24 hours)
2. Ensure `proxy_buffering off;` is set
3. Check `chunked_transfer_encoding off;`
4. Verify no intermediate proxies are buffering
5. Check server keepalive settings

**NGINX Configuration Check:**
```nginx
location = /demo/sse {
    # These are CRITICAL for long-lived SSE connections
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 86400s;  # Must be long
    proxy_send_timeout 86400s;  # Must be long
    chunked_transfer_encoding off;
    
    proxy_set_header Connection '';
    # ... rest of config
}
```

**Verification:**
```powershell
# Monitor connection duration
curl -N -H "Authorization: Bearer TOKEN" `
     https://data.forensic-bot.com/demo/sse

# Check NGINX error logs for timeout issues
docker compose logs nginx | Select-String "timeout\|upstream"
```

#### Issue 6: Database Connection Failures

**Symptoms:**
```
Error: Cannot connect to database
pyodbc.Error: ('08001', ...)
Tools return connection errors
```

**Solutions:**
1. Verify MSSQL_HOST is reachable from container
2. Check database credentials in .env
3. Test ODBC driver installation
4. Verify firewall allows connection
5. Check TrustServerCertificate setting

**Debug Commands:**
```powershell
# Test connection from container
docker compose exec mcp-server-demo python -c "
import pyodbc
import os
from dotenv import load_dotenv
load_dotenv()
conn_str = f\"Driver={{ODBC Driver 18 for SQL Server}};Server={os.getenv('MSSQL_HOST')};UID={os.getenv('MSSQL_USER')};PWD={os.getenv('MSSQL_PASSWORD')};Database={os.getenv('MSSQL_DATABASE')};TrustServerCertificate=yes\"
conn = pyodbc.connect(conn_str)
print('Connection successful!')
conn.close()
"

# Check ODBC drivers available
docker compose exec mcp-server-demo odbcinst -j
```

#### Issue 7: Tool Execution Failures

**Symptoms:**
```
Tool calls return errors
"Tool execution failed" messages
SQL syntax errors
```

**Solutions:**
1. Check SQL syntax for SQL Server (not MySQL)
2. Verify table/column names are correct
3. Ensure user has necessary permissions
4. Check READ_ONLY_MODE if trying write operations
5. Review server logs for detailed errors

**SQL Server Syntax Reminders:**
```sql
-- Use TOP instead of LIMIT
SELECT TOP 10 * FROM table;  -- ✓ Correct
SELECT * FROM table LIMIT 10;  -- ✗ Wrong

-- Use LEN() instead of LENGTH()
SELECT LEN(column) FROM table;  -- ✓ Correct

-- Use GETDATE() for current timestamp
SELECT GETDATE();  -- ✓ Correct
```

**Debug:**
```powershell
# Check tool execution logs
docker compose logs mcp-server-demo | Select-String "execute_sql\|tool\|ERROR"

# Test query manually
docker compose exec mcp-server-demo python -c "
from server_oauth import execute_sql_impl
result = execute_sql_impl('SELECT TOP 5 * FROM YourTable')
print(result)
"
```

## Security Best Practices

### Production Security Checklist

- [ ] **Enable READ_ONLY_MODE=true**
  - Prevents INSERT/UPDATE/DELETE operations
  - Restricts to SELECT queries only
  - Essential for demo and read-only environments

- [ ] **Disable Testing Flags**
  ```bash
  ALLOW_UNAUTH_METHODS=false
  ALLOW_UNAUTH_TOOLS_CALL=false
  ```
  - Never bypass OAuth in production
  - Always require Bearer token authentication

- [ ] **Restrict Redirect Hosts**
  ```bash
  ALLOWED_REDIRECT_HOSTS=claude.ai,anthropic.com
  ```
  - Only allow trusted OAuth redirect URIs
  - Prevents authorization hijacking
  - Add company SSO if applicable

- [ ] **Use Least-Privilege Database User**
  ```sql
  -- Create read-only user for demo
  CREATE LOGIN claude_demo WITH PASSWORD = 'SecurePassword123!';
  CREATE USER claude_demo FOR LOGIN claude_demo;
  GRANT CONNECT ON DATABASE::DemoDB TO claude_demo;
  GRANT SELECT ON SCHEMA::dbo TO claude_demo;
  
  -- For production with write access
  CREATE LOGIN claude_prod WITH PASSWORD = 'ProdPassword123!';
  CREATE USER claude_prod FOR LOGIN claude_prod;
  GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO claude_prod;
  ```

- [ ] **Implement Row-Level Security** (if needed)
  ```sql
  -- Example: User can only see their own data
  CREATE FUNCTION dbo.fn_securitypredicate(@UserID AS int)
      RETURNS TABLE
      WITH SCHEMABINDING
  AS
      RETURN SELECT 1 AS fn_securitypredicate_result
      WHERE @UserID = CAST(SESSION_CONTEXT(N'UserId') AS int);
  
  CREATE SECURITY POLICY UserFilter
      ADD FILTER PREDICATE dbo.fn_securitypredicate(UserID)
      ON dbo.SensitiveData
      WITH (STATE = ON);
  ```

- [ ] **Enable SQL Server Auditing**
  ```sql
  -- Create audit specification
  CREATE SERVER AUDIT MCP_Audit
  TO FILE (FILEPATH = 'C:\Audits\')
  WITH (ON_FAILURE = CONTINUE);
  
  ALTER SERVER AUDIT MCP_Audit WITH (STATE = ON);
  
  -- Audit SELECT statements
  CREATE DATABASE AUDIT SPECIFICATION MCP_Database_Audit
  FOR SERVER AUDIT MCP_Audit
      ADD (SELECT ON DATABASE::DemoDB BY claude_demo)
  WITH (STATE = ON);
  ```

- [ ] **Monitor and Log Access**
  ```nginx
  # In NGINX config
  access_log /var/log/nginx/demo-mcp.access.log combined;
  error_log /var/log/nginx/demo-mcp.error.log warn;
  ```

- [ ] **Rotate Logs Regularly**
  ```bash
  # Logrotate configuration
  /var/log/nginx/demo-mcp.*.log {
      daily
      missingok
      rotate 30
      compress
      delaycompress
      notifempty
      create 0640 www-data adm
      sharedscripts
      postrotate
          docker compose exec nginx nginx -s reload
      endscript
  }
  ```

- [ ] **Use TLS 1.2+ Only**
  ```nginx
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers HIGH:!aNULL:!MD5;
  ssl_prefer_server_ciphers off;
  ```

- [ ] **Implement Rate Limiting** (if needed)
  ```nginx
  limit_req_zone $binary_remote_addr zone=demo:10m rate=10r/s;
  
  location /demo/sse {
      limit_req zone=demo burst=20 nodelay;
      # ... rest of config
  }
  ```

### Multi-Environment Security

For multi-tenant setups (demo, production, marketing):

1. **Separate Databases**: Use different databases for each environment
2. **Different Users**: Each environment has its own database user
3. **Scope Isolation**: Different paths (/demo, /production, /marketing)
4. **Environment-Specific Configs**: Separate .env configurations
5. **Access Controls**: Different READ_ONLY_MODE settings per environment

Example:
```bash
# Demo: Read-only access to demo database
MSSQL_DATABASE=DemoDB
MSSQL_USER=demo_user
READ_ONLY_MODE=true

# Production: Full access to production database
MSSQL_DATABASE_PROD=ProductionDB
MSSQL_USER_PROD=prod_user
READ_ONLY_MODE_PROD=false  # Write operations allowed
```

## Advanced Configuration

### Custom Scope Paths

To add additional environments beyond `/demo`:

1. **Update docker-compose.yml**:
```yaml
services:
  mcp-server-production:
    build: .
    container_name: mcp-server-production
    environment:
      - MSSQL_DATABASE=${MSSQL_DATABASE_PROD}
      - MSSQL_USER=${MSSQL_USER_PROD}
      - MSSQL_PASSWORD=${MSSQL_PASSWORD_PROD}
      # Other settings...
```

2. **Add NGINX locations**:
```nginx
# Production environment at /production/*
location ~ ^/production/\.well-known/(.*)$ {
    rewrite ^/production(/.*)$ $1 break;
    proxy_pass http://mcp-server-production:8008;
    proxy_set_header X-Environment-Path /production;
    # ... rest of config
}

location = /production/sse {
    rewrite ^/production(/.*)$ $1 break;
    proxy_pass http://mcp-server-production:8008;
    proxy_set_header X-Environment-Path /production;
    # ... SSE config
}
```

3. **Configure Claude Desktop**:
```json
{
  "mcpServers": {
    "mssql-demo": {
      "url": "https://data.forensic-bot.com/demo/sse",
      "oauth": { ... }
    },
    "mssql-production": {
      "url": "https://data.forensic-bot.com/production/sse",
      "oauth": { ... }
    }
  }
}
```

See [Multi-Tenant Implementation Guide](./multi-tenant-implementation-guide.md) for complete details.

### Custom Tool Configuration

Modify available tools in `server_oauth.py`:

```python
# Add custom tool
@server.call_tool()
async def custom_analysis(arguments: dict) -> list[types.TextContent]:
    """Custom data analysis tool"""
    query = arguments.get("query")
    # Custom logic here
    return [types.TextContent(
        type="text",
        text=json.dumps(result)
    )]

# Register in tools list
async def handle_list_tools():
    return types.ListToolsResult(
        tools=[
            # ... existing tools
            types.Tool(
                name="custom_analysis",
                description="Perform custom data analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            )
        ]
    )
```

### Enhanced Logging

Add structured logging:

```python
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/demo-mcp.log'),
        logging.StreamHandler()
    ]
)

# Log tool execution
logger.info(json.dumps({
    "timestamp": datetime.utcnow().isoformat(),
    "event": "tool_execution",
    "tool": "execute_sql",
    "user": "claude_user",
    "query": query,
    "duration_ms": execution_time
}))
```

## Monitoring and Maintenance

### Health Monitoring Script

```powershell
# automated-health-check.ps1
$endpoint = "https://data.forensic-bot.com/demo/health"
$alertEmail = "admin@domain.com"

while ($true) {
    try {
        $response = Invoke-RestMethod -Uri $endpoint -TimeoutSec 10
        
        if ($response.status -ne "healthy") {
            # Send alert
            Send-MailMessage `
                -To $alertEmail `
                -Subject "Demo MCP Server Health Alert" `
                -Body "Status: $($response.status)" `
                -SmtpServer "smtp.domain.com"
        }
        
        Write-Host "$(Get-Date): Healthy - Database: $($response.database)"
    }
    catch {
        Write-Host "$(Get-Date): Health check failed - $($_.Exception.Message)"
        # Send alert
    }
    
    Start-Sleep -Seconds 300  # Check every 5 minutes
}
```

### Log Analysis

```powershell
# Analyze logs for patterns
# Error analysis
docker compose logs mcp-server-demo | Select-String "ERROR" | Group-Object

# OAuth flow tracking
docker compose logs mcp-server-demo | Select-String "OAuth" | 
    Select-String "register|authorize|token"

# Tool usage statistics
docker compose logs mcp-server-demo | Select-String "tool_execution" |
    ForEach-Object { 
        $_ -match '"tool":"([^"]+)"' 
        $Matches[1] 
    } | Group-Object | Sort-Object Count -Descending

# Connection duration tracking
docker compose logs nginx | Select-String "/demo/sse" | 
    Measure-Object | Select-Object Count
```

### Performance Metrics

Monitor these key indicators:

1. **Response Times**
   - Health check latency
   - OAuth token generation time
   - Tool execution duration
   - SSE connection establishment time

2. **Connection Stats**
   - Active SSE connections
   - OAuth token refresh rate
   - Failed authentication attempts
   - Average session duration

3. **Database Performance**
   - Query execution time
   - Connection pool utilization
   - Failed connection attempts
   - Query complexity distribution

4. **System Resources**
   - Container CPU usage
   - Memory consumption
   - Network I/O
   - Disk space (logs)

```powershell
# Monitor container resources
docker stats mcp-server-demo nginx --no-stream

# Check disk space
docker compose exec mcp-server-demo df -h

# Monitor connections
docker compose exec nginx netstat -an | Select-String "ESTABLISHED" | 
    Select-String ":443"
```

## Appendix

### Complete Endpoint Reference

**Root-Level Discovery (Fallback):**
- `GET /.well-known/oauth-authorization-server`
- `GET /.well-known/oauth-protected-resource`

**Scoped Discovery (Primary):**
- `GET /demo/.well-known/oauth-authorization-server`
- `GET /demo/.well-known/oauth-protected-resource`
- `GET /demo/.well-known/openid-configuration`

**OAuth Endpoints:**
- `POST /demo/register` - Client registration
- `GET /demo/authorize` - Authorization request
- `POST /demo/token` - Token exchange

**MCP Endpoints:**
- `HEAD /demo/sse` - Capability check
- `GET /demo/sse` - SSE probe
- `OPTIONS /demo/sse` - CORS preflight
- `POST /demo/sse` - MCP JSON-RPC

**Utility Endpoints:**
- `GET /demo/health` - Health status

### Quick Reference Commands

```powershell
# Build
docker compose build mcp-server-demo

# Start
docker compose up -d mcp-server-demo nginx

# Stop
docker compose stop mcp-server-demo nginx

# Restart
docker compose restart mcp-server-demo nginx

# Logs (real-time)
docker compose logs -f mcp-server-demo

# Logs (last 100 lines)
docker compose logs --tail=100 mcp-server-demo

# Health check
curl https://data.forensic-bot.com/demo/health

# Discovery
curl https://data.forensic-bot.com/demo/.well-known/oauth-authorization-server

# Shell access
docker compose exec mcp-server-demo /bin/bash

# Check NGINX config
docker compose exec nginx nginx -t

# Reload NGINX
docker compose exec nginx nginx -s reload

# View environment variables
docker compose exec mcp-server-demo env | Select-String "MSSQL"
```

### Configuration File Locations

```
Project Root/
├── .env                              # Environment variables
├── docker-compose.yml                # Service definitions
├── docker-compose.prod.yml           # Production config
├── server_oauth.py                   # MCP server code
├── nginx/
│   ├── nginx.conf                   # Main NGINX config
│   └── conf.d/
│       └── default.conf             # Site configuration
├── certbot/
│   ├── conf/                        # SSL certificates
│   └── www/                         # ACME challenge
└── logs/
    └── nginx/                       # NGINX logs
```

### Troubleshooting Decision Tree

```
Connection Issue?
├── Can't reach server
│   ├── Check DNS: nslookup data.forensic-bot.com
│   ├── Check firewall: telnet data.forensic-bot.com 443
│   └── Check NGINX: docker compose ps nginx
│
├── 404 on discovery
│   ├── Check NGINX config: nginx -t
│   ├── Verify proxy_pass targets
│   └── Check X-Environment-Path header
│
├── 401 Unauthorized
│   ├── Verify OAuth flow completed
│   ├── Check token expiration
│   └── Review ALLOWED_REDIRECT_HOSTS
│
├── 405 Method Not Allowed
│   ├── Check server implements method
│   ├── Verify NGINX allows method
│   └── Review CORS configuration
│
└── 500 Server Error
    ├── Check server logs: docker compose logs
    ├── Verify database connection
    └── Review environment variables
```

### Support and Resources

- **MCP Specification**: https://spec.modelcontextprotocol.io
- **OAuth 2.0 RFC**: https://tools.ietf.org/html/rfc6749
- **OAuth 2.0 Discovery**: https://tools.ietf.org/html/rfc8414
- **Server-Sent Events**: https://html.spec.whatwg.org/multipage/server-sent-events.html
- **NGINX SSE Guide**: https://nginx.org/en/docs/http/ngx_http_proxy_module.html
- **Claude.ai MCP Docs**: https://docs.anthropic.com/claude/docs/mcp

### Related Documentation

- [ChatGPT Connector Setup](./chatgpt-connector-setup.md)
- [Multi-Tenant Implementation Guide](./multi-tenant-implementation-guide.md)
- [Security Best Practices](./security.md)
- [Read-Only Mode Configuration](./read_only.md)

---

**Document Version**: 2.0.0  
**Last Updated**: October 2025  
**Compatibility**: Claude.ai, Claude Desktop, MCP 2025-06-18  
**Server**: server_oauth.py  
**Tested With**: Docker 20.10+, NGINX 1.24+, SQL Server 2019+  
**Scope**: /demo (customizable for multi-tenant deployments)**