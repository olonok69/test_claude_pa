# Claude.ai Connector Setup (MSSQL MCP Server)

This guide explains how to connect Claude.ai to the MSSQL MCP server using SSE and OAuth, via the demo scope `/demo` fronted by NGINX.

## Scope and Capabilities

- Protocol: MCP 2025-06-18
- Transport: Server-Sent Events (SSE)
- Tools: Full SQL toolkit in `server_oauth.py` (list_tables, describe_table, get_table_sample, execute_sql)
- OAuth 2.0: Dynamic registration, authorization code, token exchange

## Architecture

```
Claude.ai ◄─HTTPS 443─► NGINX (SSL, CORS, SSE, OAuth discovery) ◄─HTTP 8008─► mcp-server (server_oauth.py)
                                      │
                        Scoped discovery and endpoints under /demo
```

Key NGINX behaviors for Claude (`nginx/conf.d/default.conf`):
- Proxy `/demo/*` to the OAuth server
- Expose OAuth discovery under `/demo/.well-known/` for:
  - oauth-authorization-server
  - oauth-protected-resource
- Handle Claude’s quirk: requests may append `/sse` after the `.well-known` path
- Forward `Authorization` header on `/demo/sse`
- Send `X-Environment-Path: /demo` so backend builds correct issuer URLs

## Backend Endpoints (server_oauth.py)

- Discovery (RFC 9728):
  - `/demo/.well-known/oauth-authorization-server`
  - `/demo/.well-known/oauth-protected-resource`
- OAuth:
  - `/demo/register`, `/demo/authorize`, `/demo/token`
- MCP:
  - `/demo/sse` (HEAD/GET/OPTIONS/POST)
- Health:
  - `/demo/health`

Note: The app uses `X-Environment-Path` when present; `ENVIRONMENT_PATH` is a fallback.

## Prerequisites

- Public domain with DNS and TLS
- Docker + Compose
- MSSQL connection details in `.env`

## Environment Variables

- Database: MSSQL_HOST, MSSQL_USER, MSSQL_PASSWORD, MSSQL_DATABASE, MSSQL_DRIVER
- Security:
  - READ_ONLY_MODE=true (recommended)
  - ALLOWED_REDIRECT_HOSTS includes `claude.ai`
  - Testing only: ALLOW_UNAUTH_METHODS=true, ALLOW_UNAUTH_TOOLS_CALL=true

## NGINX Essentials for Claude

Already present in `nginx/conf.d/default.conf`:

- Scoped discovery under `/demo`:
```nginx
location ~ ^/demo/\.well-known/(oauth-authorization-server|oauth-protected-resource)$ {
    rewrite ^/demo(/.*)$ $1 break;
    proxy_pass http://mcp-server-production:8008;
    proxy_set_header X-Environment-Path /demo;
    add_header Access-Control-Allow-Origin "*" always;
    add_header Access-Control-Allow-Methods "GET, OPTIONS" always;
    add_header Access-Control-Allow-Headers 'Authorization, Content-Type' always;
}
```

- Quirk redirect for `/sse` suffix:
```nginx
location ~ ^/demo/\.well-known/(oauth-authorization-server|oauth-protected-resource)/sse$ {
    rewrite ^/demo/\.well-known/(.*)/sse$ /demo/.well-known/$1 redirect;
}
```

- SSE endpoint with Authorization forwarding:
```nginx
location = /demo/sse {
    # ... SSE proxy settings
    proxy_pass http://mcp-server-production:8008;
    proxy_set_header Authorization $http_authorization;
    proxy_set_header X-Environment-Path /demo;
}
```

## Deploy and Verify

1) Bring up services (PowerShell):
```powershell
# From repo root
docker compose build mcp-server-production nginx
docker compose up -d mcp-server-production nginx
```

2) Verify health and discovery:
```powershell
curl https://your-domain/demo/health
curl https://your-domain/demo/.well-known/oauth-authorization-server
curl https://your-domain/demo/.well-known/oauth-protected-resource
```

3) Optional SSE probe
```powershell
curl -I https://your-domain/demo/sse
```

## Add in Claude.ai

- In Claude Desktop or Web, add a custom MCP server.
- Base URL: `https://your-domain/demo/sse`
- OAuth steps:
  1. POST `/demo/register`
  2. GET `/demo/authorize` → redirects back to claude.ai
  3. POST `/demo/token` → returns access token

## Usage Examples

- "List tables"
- "Describe table Registration_data_csm"
- "Run: SELECT TOP 5 * FROM control.control_daily_copy"

## Troubleshooting

- 404 discovery:
  - Make sure `/demo/.well-known/...` proxies to the backend and includes `X-Environment-Path /demo`.
- 401 on `/demo/sse`:
  - Provide Bearer token. For testing, temporarily enable `ALLOW_UNAUTH_METHODS` and `ALLOW_UNAUTH_TOOLS_CALL`.
- 405 on probes:
  - Ensure HEAD/GET/OPTIONS are allowed by the app (they are implemented) and not blocked by NGINX.
- Redirect blocked:
  - Include `claude.ai` in `ALLOWED_REDIRECT_HOSTS`.

## Security Tips

- Keep DB user least-privilege and enable `READ_ONLY_MODE` for production.
- Disable `ALLOW_UNAUTH_*` in production.
- Restrict `ALLOWED_REDIRECT_HOSTS` to trusted domains: `claude.ai`, your SSO if applicable.

---

Last updated: 2025-09-19
