# ChatGPT Connector Setup (Deep Research) for MSSQL MCP Server

This comprehensive guide explains how to expose the MSSQL MCP server to ChatGPT as a custom connector with OAuth 2.0 authentication, including NGINX routing, discovery endpoints, security controls, and troubleshooting.

## Table of Contents
- [Scope and Capabilities](#scope-and-capabilities)
- [Architecture and Routing](#architecture-and-routing)
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [NGINX Configuration](#nginx-configuration)
- [Deployment Steps](#deployment-steps)
- [Adding Connector in ChatGPT](#adding-connector-in-chatgpt)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)
- [Testing and Verification](#testing-and-verification)

## Scope and Capabilities

### Protocol Specifications
- **Protocol**: MCP 2025-06-18
- **Transport**: Server-Sent Events (SSE)
- **Authentication**: OAuth 2.0 with dynamic client registration
- **Server**: `server_chatgpt.py` (ChatGPT-specific implementation)

### Available Tools

ChatGPT has access to two powerful tools:

#### 1. search Tool
Multi-purpose database search that intelligently handles:
- **List tables**: `"list tables"` → Returns all tables from INFORMATION_SCHEMA
- **Describe table**: `"describe Customers"` → Returns columns, types, primary keys
- **Sample data**: `"sample Orders limit 10"` → Returns SELECT TOP N rows
- **SQL queries**: `"SELECT TOP 5 * FROM Products WHERE Price > 100"` → Executes read-only queries

#### 2. fetch Tool
Retrieves specific records by ID from cached search results:
- Takes record IDs returned by search tool
- Returns full record details
- Uses TTL-based caching for performance
- Cache default: 3600 seconds (1 hour)

## Architecture and Routing

### High-Level Architecture
```
ChatGPT ◄──HTTPS 443──► NGINX ◄──HTTP 8008──► mcp-server-chatgpt
                         │                            │
                    (SSL/TLS)                   (OAuth 2.0)
                    (CORS/SSE)                        │
                         │                            ▼
                         └──────────────────► SQL Server Database
```

### Routing Strategy

NGINX provides dual-scope discovery:
1. **Root-level discovery** (`/.well-known/*`) - For initial ChatGPT probes
2. **Scoped discovery** (`/chatgpt/.well-known/*`) - For scoped operations

```
Client Request Flow:
1. ChatGPT → /.well-known/openid-configuration
2. NGINX → mcp-server-chatgpt:8008 (with X-Environment-Path: /chatgpt)
3. Server → Returns issuer: https://domain.com/chatgpt
4. ChatGPT → /chatgpt/sse (SSE endpoint)
5. OAuth flow → /chatgpt/register, /authorize, /token
```

### Key NGINX Behaviors

Configured in `nginx/conf.d/default.conf`:

1. **Proxies ChatGPT traffic** under `/chatgpt/*` to `mcp-server-chatgpt:8008`
2. **Dual discovery endpoints** at both root and `/chatgpt` scopes:
   - `/.well-known/oauth-authorization-server`
   - `/.well-known/openid-configuration`
   - `/.well-known/oauth-protected-resource`
3. **Handles ChatGPT quirks**:
   - `/.well-known/{endpoint}/chatgpt/sse` → 302 to `/.well-known/{endpoint}`
   - `/chatgpt/sse/.well-known/{endpoint}` → 302 to `/chatgpt/.well-known/{endpoint}`
4. **Normalizes paths**: `merge_slashes on;` prevents `//` causing 404
5. **SSE optimization**: Disables buffering, extends timeouts
6. **Environment context**: Sends `X-Environment-Path: /chatgpt` header

## Prerequisites

### Infrastructure Requirements
- Public domain with DNS A record (e.g., data.forensic-bot.com)
- Valid TLS certificates (Let's Encrypt via Certbot included in repo)
- Docker Engine 20.10+
- Docker Compose 2.0+

### Database Requirements
- Microsoft SQL Server instance (2019+)
- Network connectivity from server to MSSQL
- Database user with appropriate permissions
- ODBC Driver 18 for SQL Server

### Access Requirements
- ChatGPT Plus or Enterprise subscription
- Access to ChatGPT connector settings
- Ability to configure custom connectors

## Environment Configuration

### Required Environment Variables

Create/update `.env` file with minimum configuration:

```bash
# ==============================================
# Database Configuration (Required)
# ==============================================
MSSQL_HOST=your-sql-server.database.windows.net
MSSQL_USER=your_username
MSSQL_PASSWORD=your_secure_password
MSSQL_DATABASE=your_database
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
ALLOWED_REDIRECT_HOSTS=chatgpt.com,openai.com

# ==============================================
# ChatGPT-Specific Settings
# ==============================================
MAX_SEARCH_RESULTS=50
CACHE_TTL_SECONDS=3600

# ==============================================
# Development/Testing Only (Set to false in production)
# ==============================================
ALLOW_UNAUTH_METHODS=false
ALLOW_UNAUTH_TOOLS_CALL=false
```

### Environment Variable Descriptions

| Variable | Purpose | Default | Production Value |
|----------|---------|---------|------------------|
| `MSSQL_HOST` | SQL Server hostname | - | Your server FQDN |
| `MSSQL_USER` | Database username | - | Service account |
| `MSSQL_PASSWORD` | Database password | - | Strong password |
| `MSSQL_DATABASE` | Database name | - | Your database |
| `MSSQL_DRIVER` | ODBC driver | ODBC Driver 18 for SQL Server | Keep default |
| `TrustServerCertificate` | SSL trust mode | yes | yes (or no for valid certs) |
| `READ_ONLY_MODE` | Restrict to SELECT only | true | **true** (recommended) |
| `ALLOWED_REDIRECT_HOSTS` | OAuth redirect whitelist | chatgpt.com,openai.com | Keep default |
| `MAX_SEARCH_RESULTS` | Search result limit | 50 | 50-100 |
| `CACHE_TTL_SECONDS` | Result cache duration | 3600 | 3600-7200 |
| `ALLOW_UNAUTH_METHODS` | Bypass OAuth (testing) | false | **false** |
| `ALLOW_UNAUTH_TOOLS_CALL` | Bypass tool auth (testing) | false | **false** |

## Backend Endpoints (server_chatgpt.py)

### Discovery Endpoints
| Endpoint | Purpose | Scope |
|----------|---------|-------|
| `/.well-known/oauth-authorization-server` | OAuth AS metadata | Root |
| `/.well-known/openid-configuration` | OIDC discovery (alias) | Root |
| `/.well-known/oauth-protected-resource` | Resource metadata | Root |
| `/chatgpt/.well-known/oauth-authorization-server` | OAuth AS metadata | Scoped |
| `/chatgpt/.well-known/openid-configuration` | OIDC discovery | Scoped |
| `/chatgpt/.well-known/oauth-protected-resource` | Resource metadata | Scoped |

### OAuth 2.0 Endpoints
| Endpoint | Method | Purpose | Request Body |
|----------|--------|---------|--------------|
| `/chatgpt/register` | POST | Dynamic client registration | `{client_name, redirect_uris}` |
| `/chatgpt/authorize` | GET | Authorization code grant | Query params |
| `/chatgpt/token` | POST | Token exchange | Form or JSON |

### MCP Transport
| Endpoint | Methods | Purpose | Authentication |
|----------|---------|---------|----------------|
| `/chatgpt/sse` | HEAD/GET/OPTIONS | Capability checks, CORS | Optional |
| `/chatgpt/sse` | POST | MCP JSON-RPC over SSE | Required (Bearer) |
| `/chatgpt/health` | GET | Health status | None |

### Environment Path Handling

The server uses `X-Environment-Path` header from NGINX:
```python
# In server_chatgpt.py
env_path = request.headers.get("x-environment-path") or os.getenv("ENVIRONMENT_PATH", "")
base_url = f"{forwarded_proto}://{host}"
if env_path:
    base_url = f"{base_url}{env_path}"

# Result: issuer = "https://domain.com/chatgpt"
```

**Note**: `ENVIRONMENT_PATH` env var is only a fallback for non-proxied runs. When behind NGINX, the header is preferred.

## NGINX Configuration

### Essential Configuration Snippets

These snippets are already present in `nginx/conf.d/default.conf`:

#### 1. Enable Slash Merging (Critical)
```nginx
http {
    # Prevent double slashes from causing 404
    merge_slashes on;
    
    # ... other http config
}
```

#### 2. Root-Level Discovery Proxy
```nginx
# ChatGPT initial probes hit root-level /.well-known/*
location ~ ^/\.well-known/(oauth-authorization-server|oauth-protected-resource|openid-configuration)$ {
    # Forward without modifying path
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_http_version 1.1;
    
    # Standard headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-Host $host;
    
    # CRITICAL: Tell backend this is for /chatgpt scope
    proxy_set_header X-Environment-Path /chatgpt;
    
    # CORS headers
    add_header Access-Control-Allow-Origin * always;
    add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS' always;
    add_header Access-Control-Allow-Headers 'Authorization, Content-Type' always;
}
```

#### 3. Scoped Discovery Under /chatgpt
```nginx
location ~ ^/chatgpt/\.well-known/(oauth-authorization-server|oauth-protected-resource|openid-configuration)$ {
    # Strip /chatgpt prefix before proxying
    rewrite ^/chatgpt(/.*)$ $1 break;
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_http_version 1.1;
    
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Environment-Path /chatgpt;
    
    add_header Access-Control-Allow-Origin * always;
    add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS' always;
    add_header Access-Control-Allow-Headers 'Authorization, Content-Type' always;
}
```

#### 4. SSE Endpoint Configuration
```nginx
location = /chatgpt/sse {
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
    
    # Strip /chatgpt prefix
    rewrite ^/chatgpt(/.*)$ $1 break;
    proxy_pass http://mcp-server-chatgpt:8008;
    
    # SSE-specific settings
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 86400s;
    proxy_send_timeout 86400s;
    chunked_transfer_encoding off;
    
    # Forward authorization
    proxy_set_header Authorization $http_authorization;
    
    # Standard headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Environment-Path /chatgpt;
    
    # SSE response headers
    add_header Content-Type text/event-stream;
    add_header Cache-Control no-cache;
    add_header X-Accel-Buffering no;
    add_header Access-Control-Allow-Origin * always;
}
```

#### 5. Quirk Handling Redirects
```nginx
# Handle /.well-known/{endpoint}/chatgpt/sse → /.well-known/{endpoint}
location ~ ^/\.well-known/(oauth-authorization-server|oauth-protected-resource|openid-configuration)/chatgpt/sse$ {
    return 302 /.well-known/$1;
}

# Handle /chatgpt/sse/.well-known/{endpoint} → /chatgpt/.well-known/{endpoint}
location ~ ^/chatgpt/sse/\.well-known/(oauth-authorization-server|oauth-protected-resource|openid-configuration)$ {
    return 302 /chatgpt/.well-known/$1;
}
```

#### 6. OAuth Endpoints
```nginx
# Registration
location = /chatgpt/register {
    rewrite ^/chatgpt(/.*)$ $1 break;
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header Content-Type $content_type;
    proxy_set_header X-Environment-Path /chatgpt;
    add_header Access-Control-Allow-Origin * always;
}

# Authorization
location = /chatgpt/authorize {
    rewrite ^/chatgpt(/.*)$ $1 break;
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_set_header X-Environment-Path /chatgpt;
}

# Token Exchange
location = /chatgpt/token {
    rewrite ^/chatgpt(/.*)$ $1 break;
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_set_header Content-Type $content_type;
    proxy_set_header X-Environment-Path /chatgpt;
}
```

## Deployment Steps

### Step 1: Build Services

```powershell
# From repository root
docker compose build mcp-server-chatgpt nginx

# Or build specific service
docker compose build mcp-server-chatgpt
```

### Step 2: Start Services

```powershell
# Start in detached mode
docker compose up -d mcp-server-chatgpt nginx

# Or start with logs
docker compose up mcp-server-chatgpt nginx
```

### Step 3: Verify Deployment

```powershell
# Check service status
docker compose ps

# View logs
docker compose logs -f mcp-server-chatgpt
docker compose logs -f nginx
```

## Testing and Verification

### 1. Health Check
```powershell
# Basic health check
curl https://data.forensic-bot.com/chatgpt/health

# Expected response:
{
  "status": "healthy",
  "transport": "sse",
  "oauth": "enabled",
  "database": "your_database",
  "mcp_version": "2025-06-18",
  "tools": ["search", "fetch"],
  "compatible_with": "ChatGPT Deep Research"
}
```

### 2. OAuth Discovery
```powershell
# Test root-level discovery
curl https://data.forensic-bot.com/.well-known/openid-configuration

# Test scoped discovery
curl https://data.forensic-bot.com/chatgpt/.well-known/oauth-authorization-server

# Both should return issuer with /chatgpt scope:
{
  "issuer": "https://data.forensic-bot.com/chatgpt",
  "authorization_endpoint": "https://data.forensic-bot.com/chatgpt/authorize",
  "token_endpoint": "https://data.forensic-bot.com/chatgpt/token",
  ...
}
```

### 3. SSE Capability Check
```powershell
# Should return 200 with SSE headers (no stream without POST data)
curl -I https://data.forensic-bot.com/chatgpt/sse

# Expected headers:
HTTP/2 200
content-type: text/event-stream
cache-control: no-cache
...
```

### 4. Test OAuth Flow (Optional)
```powershell
# Register test client
$response = Invoke-RestMethod -Method Post `
    -Uri "https://data.forensic-bot.com/chatgpt/register" `
    -Headers @{"Content-Type"="application/json"} `
    -Body '{"client_name":"Test Client","redirect_uris":["https://example.com/callback"]}'

Write-Host "Client ID: $($response.client_id)"
Write-Host "Client Secret: $($response.client_secret)"
```

## Adding Connector in ChatGPT

### Step-by-Step Setup

1. **Open ChatGPT Settings**
   - Navigate to ChatGPT → Settings → Beta Features
   - Enable "Deep Research" if not already enabled
   - Go to Settings → Connectors (or Actions/Plugins depending on version)

2. **Add Custom Connector**
   - Click "Create custom connector" or "Add connector"
   - Select "Create from scratch" or "Import OpenAPI spec"

3. **Configure Connector Details**
   ```
   Name: MSSQL Database
   Description: Query Microsoft SQL Server database
   Base URL: https://data.forensic-bot.com/chatgpt/sse
   ```

4. **OAuth Configuration**
   - Authentication Type: OAuth 2.0
   - Discovery URL: `https://data.forensic-bot.com/chatgpt/.well-known/oauth-authorization-server`
   - ChatGPT will auto-discover endpoints

5. **Authorize**
   - Click "Authorize" or "Connect"
   - ChatGPT will execute OAuth flow:
     1. POST `/chatgpt/register` → Get client credentials
     2. GET `/chatgpt/authorize` → Redirect with code
     3. POST `/chatgpt/token` → Receive Bearer token
   - Server validates redirect_uri against `ALLOWED_REDIRECT_HOSTS`

6. **First Connection**
   - ChatGPT calls `POST /chatgpt/sse`:
     - Sends `initialize` method
     - Receives `tools/list` with search and fetch
     - Ready to accept queries

### Verification in ChatGPT

After setup, test with:
```
"Show me available database tools"
```

ChatGPT should respond indicating it has access to `search` and `fetch` tools.

## Usage Examples

### Basic Queries

```text
User: "List all tables in the database"
ChatGPT: [Calls search tool with "list tables"]
Response: Lists all tables from INFORMATION_SCHEMA

User: "Describe the Customers table"
ChatGPT: [Calls search tool with "describe Customers"]
Response: Shows columns, types, keys, constraints

User: "Show me 5 sample records from Orders"
ChatGPT: [Calls search tool with "sample Orders limit 5"]
Response: Returns TOP 5 rows from Orders table
```

### SQL Queries

```text
User: "Find top 10 customers by total order value"
ChatGPT: [Calls search tool with SQL query]
Tool: SELECT TOP 10 CustomerID, SUM(OrderTotal) as TotalValue
      FROM Orders
      GROUP BY CustomerID
      ORDER BY TotalValue DESC
Response: Returns aggregated customer data with IDs

User: "Get full details for customer #result-id-123"
ChatGPT: [Calls fetch tool with ID from previous results]
Response: Returns complete customer record
```

### Complex Analysis

```text
User: "Analyze sales trends by month for 2024"
ChatGPT: [Calls search tool with complex query]
Tool: SELECT 
        DATEPART(MONTH, OrderDate) as Month,
        COUNT(*) as OrderCount,
        SUM(Total) as Revenue
      FROM Orders
      WHERE YEAR(OrderDate) = 2024
      GROUP BY DATEPART(MONTH, OrderDate)
      ORDER BY Month
Response: Monthly breakdown with analysis
```

### Search Result Caching

The server caches search results with record IDs:
```json
{
  "results": [
    {
      "id": "customers-12345",
      "name": "Acme Corp",
      "revenue": 150000
    }
  ],
  "cached_until": "2025-10-01T15:30:00Z"
}
```

Use fetch to get full details:
```text
"Get complete information for customers-12345"
```

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: 404 on Discovery URLs

**Symptoms:**
```
GET /.well-known/oauth-authorization-server → 404
GET /chatgpt/.well-known/openid-configuration → 404
```

**Solutions:**
1. Verify root-level `.well-known` proxy exists in NGINX config
2. Ensure `proxy_pass http://mcp-server-chatgpt:8008;` (no `/$uri` suffix)
3. Confirm `merge_slashes on;` is set in http block
4. Check `X-Environment-Path: /chatgpt` header is sent
5. Restart NGINX: `docker compose restart nginx`

**Verification:**
```powershell
# Test discovery
curl -v https://data.forensic-bot.com/.well-known/openid-configuration

# Should see X-Environment-Path in request headers (check NGINX logs)
docker compose logs nginx | Select-String "X-Environment-Path"
```

#### Issue 2: 401 Unauthorized on /sse

**Symptoms:**
```
POST /chatgpt/sse → 401 Unauthorized
```

**Solutions:**
1. Ensure Bearer token is provided in Authorization header
2. Check token hasn't expired (1-hour default)
3. Verify OAuth flow completed successfully
4. For testing only: temporarily set `ALLOW_UNAUTH_METHODS=true`

**Verification:**
```powershell
# Check if token authentication is enforced
curl -I https://data.forensic-bot.com/chatgpt/sse

# With token (get from OAuth flow)
curl -H "Authorization: Bearer YOUR_TOKEN" `
     https://data.forensic-bot.com/chatgpt/sse
```

#### Issue 3: 405 Method Not Allowed

**Symptoms:**
```
HEAD /chatgpt/sse → 405
OPTIONS /chatgpt/sse → 405
```

**Solutions:**
1. Verify server_chatgpt.py implements HEAD/OPTIONS handlers
2. Check NGINX doesn't block these methods
3. Ensure CORS configuration allows all methods

**Verification:**
```powershell
# Test each method
curl -X HEAD https://data.forensic-bot.com/chatgpt/sse
curl -X OPTIONS https://data.forensic-bot.com/chatgpt/sse
curl -X GET https://data.forensic-bot.com/chatgpt/sse
```

#### Issue 4: 302 Redirect Loops

**Symptoms:**
```
GET /authorize → 302 → 302 → 302 (infinite loop)
OAuth flow fails with redirect error
```

**Solutions:**
1. Verify `ALLOWED_REDIRECT_HOSTS` includes `chatgpt.com`
2. Check redirect_uri validation in server_chatgpt.py
3. Ensure chatgpt.com is in default list or .env override

**Configuration:**
```bash
# In .env
ALLOWED_REDIRECT_HOSTS=chatgpt.com,openai.com

# Default in server_chatgpt.py
ALLOWED_REDIRECT_HOSTS = [h.strip().lower() for h in os.getenv(
    "ALLOWED_REDIRECT_HOSTS",
    "chatgpt.com,openai.com,claude.ai,anthropic.com"
).split(",")]
```

#### Issue 5: Double-Slash 404 Errors

**Symptoms:**
```
GET //.well-known/oauth-authorization-server → 404
GET /chatgpt//sse → 404
```

**Solutions:**
1. Enable `merge_slashes on;` in nginx.conf http block
2. Avoid using `/$uri` in proxy_pass directives
3. Use `proxy_pass http://backend;` (no trailing slash after host)

**NGINX Configuration:**
```nginx
http {
    # CRITICAL: Enable slash merging
    merge_slashes on;
    
    # Correct proxy_pass usage
    location ~ ^/chatgpt/sse$ {
        proxy_pass http://mcp-server-chatgpt:8008;  # ✓ Correct
        # proxy_pass http://mcp-server-chatgpt:8008/$uri;  # ✗ Wrong
    }
}
```

#### Issue 6: 500 Internal Server Error After OAuth

**Symptoms:**
```
POST /chatgpt/sse → 200 (OAuth success)
Subsequent POST /chatgpt/sse → 500 Internal Server Error
```

**Solutions:**
1. Check server logs for UnboundLocalError
2. Verify request body is properly initialized
3. Ensure tools/call requests have valid arguments

**Debug Commands:**
```powershell
# View detailed server logs
docker compose logs -f mcp-server-chatgpt | Select-String "ERROR"

# Check for UnboundLocalError
docker compose logs mcp-server-chatgpt | Select-String "UnboundLocalError"
```

**Fix Applied:** Server defensively initializes request body to avoid this error.

#### Issue 7: Database Connection Failures

**Symptoms:**
```
Error: pyodbc.Error: ('08001', '[08001] ...')
Cannot connect to MSSQL server
```

**Solutions:**
1. Verify MSSQL_HOST is reachable from container
2. Check firewall allows connection from Docker network
3. Validate credentials in .env
4. Test ODBC driver installation

**Verification:**
```powershell
# Test from container
docker compose exec mcp-server-chatgpt python -c "
import pyodbc
import os
from dotenv import load_dotenv
load_dotenv()
conn_str = f\"Driver={{ODBC Driver 18 for SQL Server}};Server={os.getenv('MSSQL_HOST')};UID={os.getenv('MSSQL_USER')};PWD={os.getenv('MSSQL_PASSWORD')};Database={os.getenv('MSSQL_DATABASE')};TrustServerCertificate=yes\"
conn = pyodbc.connect(conn_str)
print('Connection successful!')
"
```

## Security Best Practices

### Production Security Checklist

- [ ] **Enable READ_ONLY_MODE=true**
  - Prevents INSERT/UPDATE/DELETE operations
  - Restricts to SELECT queries only
  - Recommended for all production environments

- [ ] **Disable Testing Flags**
  ```bash
  ALLOW_UNAUTH_METHODS=false
  ALLOW_UNAUTH_TOOLS_CALL=false
  ```
  - Never bypass OAuth in production
  - Always require Bearer token authentication

- [ ] **Restrict Redirect Hosts**
  ```bash
  ALLOWED_REDIRECT_HOSTS=chatgpt.com,openai.com
  ```
  - Only allow trusted OAuth redirect URIs
  - Remove unnecessary domains
  - Prevents authorization hijacking

- [ ] **Use Least-Privilege Database User**
  ```sql
  -- Create read-only user
  CREATE LOGIN chatgpt_readonly WITH PASSWORD = 'SecurePassword123!';
  CREATE USER chatgpt_readonly FOR LOGIN chatgpt_readonly;
  GRANT SELECT ON SCHEMA::dbo TO chatgpt_readonly;
  ```

- [ ] **Forward Minimal Headers**
  - Only forward: Host, X-Forwarded-*, Authorization
  - Don't expose internal headers to backend
  - Use NGINX header filtering

- [ ] **Implement Rate Limiting** (NGINX)
  ```nginx
  limit_req_zone $binary_remote_addr zone=chatgpt:10m rate=10r/s;
  
  location /chatgpt/sse {
      limit_req zone=chatgpt burst=20;
      # ... rest of config
  }
  ```

- [ ] **Enable NGINX Access Logs**
  ```nginx
  access_log /var/log/nginx/chatgpt.access.log combined;
  error_log /var/log/nginx/chatgpt.error.log warn;
  ```

- [ ] **Rotate Logs Regularly**
  ```bash
  # Add to cron or use logrotate
  /var/log/nginx/*.log {
      daily
      missingok
      rotate 14
      compress
      delaycompress
      notifempty
      create 0640 www-data adm
  }
  ```

### Network Security

- Use GCP firewall rules to restrict access
- Only allow HTTPS (443) and SSH (22) ports
- Consider IP whitelisting for known ChatGPT ranges
- Monitor for unusual access patterns

### Database Security

- Never use sa or admin accounts
- Create dedicated service account
- Implement column-level security if needed
- Enable SQL Server auditing
- Regular security patching

## Advanced Configuration

### Custom Tool Limits

```bash
# Adjust search result limits
MAX_SEARCH_RESULTS=100

# Adjust cache duration (seconds)
CACHE_TTL_SECONDS=7200  # 2 hours
```

### Multiple Database Support

For multi-tenant or multiple database scenarios:
```bash
# Primary database
MSSQL_HOST=primary.database.windows.net
MSSQL_DATABASE=primary_db

# Secondary database (not currently supported)
# Would require code changes to support
```

### Custom Logging

Enhance logging in server_chatgpt.py:
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/chatgpt-mcp.log'),
        logging.StreamHandler()
    ]
)
```

## Monitoring and Maintenance

### Health Monitoring

```powershell
# Automated health check script
while ($true) {
    $health = Invoke-RestMethod https://data.forensic-bot.com/chatgpt/health
    if ($health.status -ne "healthy") {
        Send-MailMessage -To admin@domain.com -Subject "ChatGPT MCP Health Alert"
    }
    Start-Sleep -Seconds 300  # Check every 5 minutes
}
```

### Log Analysis

```powershell
# Check for errors in last hour
docker compose logs --since 1h mcp-server-chatgpt | Select-String "ERROR"

# Monitor OAuth flow
docker compose logs -f mcp-server-chatgpt | Select-String "OAuth|token|register"

# Track search queries
docker compose logs -f mcp-server-chatgpt | Select-String "search|fetch"
```

### Performance Metrics

Monitor these key metrics:
- OAuth token generation rate
- Search tool execution time
- Cache hit/miss ratio
- Database query performance
- SSE connection duration
- Error rate per endpoint

## Appendix

### Complete Endpoint Reference

**Discovery Endpoints:**
- `GET /.well-known/oauth-authorization-server`
- `GET /.well-known/openid-configuration`
- `GET /.well-known/oauth-protected-resource`
- `GET /chatgpt/.well-known/oauth-authorization-server`
- `GET /chatgpt/.well-known/openid-configuration`
- `GET /chatgpt/.well-known/oauth-protected-resource`

**OAuth Endpoints:**
- `POST /chatgpt/register` - Client registration
- `GET /chatgpt/authorize` - Authorization request
- `POST /chatgpt/token` - Token exchange

**MCP Endpoints:**
- `HEAD /chatgpt/sse` - Capability check
- `GET /chatgpt/sse` - SSE probe
- `OPTIONS /chatgpt/sse` - CORS preflight
- `POST /chatgpt/sse` - MCP JSON-RPC

**Utility Endpoints:**
- `GET /chatgpt/health` - Health status

### Quick Reference Commands

```powershell
# Build
docker compose build mcp-server-chatgpt

# Start
docker compose up -d mcp-server-chatgpt nginx

# Stop
docker compose stop mcp-server-chatgpt nginx

# Restart
docker compose restart mcp-server-chatgpt nginx

# Logs
docker compose logs -f mcp-server-chatgpt

# Health
curl https://data.forensic-bot.com/chatgpt/health

# Discovery
curl https://data.forensic-bot.com/.well-known/openid-configuration

# Shell access
docker compose exec mcp-server-chatgpt /bin/bash
```

### Support and Resources

- **MCP Specification**: https://spec.modelcontextprotocol.io
- **OAuth 2.0 RFC**: https://tools.ietf.org/html/rfc6749
- **Server-Sent Events**: https://html.spec.whatwg.org/multipage/server-sent-events.html
- **ChatGPT Connectors**: https://platform.openai.com/docs/actions

---

**Document Version**: 2.0.0  
**Last Updated**: October 2025  
**Compatibility**: ChatGPT (Deep Research), MCP 2025-06-18  
**Server**: server_chatgpt.py  
**Tested With**: Docker 20.10+, NGINX 1.24+, SQL Server 2019+