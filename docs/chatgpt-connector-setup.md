# ChatGPT Connector Setup (Deep Research) for MSSQL MCP Server

This guide explains how to expose the MSSQL MCP server to ChatGPT as a custom connector with OAuth 2.0, including NGINX routing, discovery endpoints, security controls, and troubleshooting.

## Scope and Capabilities

- Protocol: MCP 2025-06-18
- Transport: Server-Sent Events (SSE)
- Tools available to ChatGPT: search, fetch
  - search multiplexes DB operations:
    - "list tables" → INFORMATION_SCHEMA tables
    - "describe <table>" → INFORMATION_SCHEMA columns/PK
    - "sample <table> limit N" → SELECT TOP N
    - "SELECT/WITH ..." → read-only query
  - fetch resolves result IDs returned by search

## Architecture and Routing

```
ChatGPT ◄─HTTPS 443─► NGINX (SSL, CORS, SSE, OAuth discovery) ◄─HTTP 8008─► mcp-server-chatgpt
                                                  │
                                Root + /chatgpt /.well-known discovery
```

Key NGINX behaviors configured in `nginx/conf.d/default.conf`:
- Proxies ChatGPT traffic under `/chatgpt/*` to `mcp-server-chatgpt:8008`
- Exposes OAuth discovery endpoints at BOTH root and `/chatgpt` scopes:
  - /.well-known/oauth-authorization-server
  - /.well-known/openid-configuration
  - /.well-known/oauth-protected-resource
- Handles quirks ChatGPT may probe:
  - `/.well-known/{endpoint}/chatgpt/sse` → 302 to `/.well-known/{endpoint}`
  - `/chatgpt/sse/.well-known/{endpoint}` → 302 to `/chatgpt/.well-known/{endpoint}`
- Sets `merge_slashes on;` so double slashes `//...` don’t 404
- For SSE: disables buffering, extends timeouts, and forwards `Authorization`
- Sends `X-Environment-Path: /chatgpt` so the backend builds correct issuer URLs

## Backend Endpoints (server_chatgpt.py)

Discovery and OAuth:
- `/.well-known/oauth-authorization-server` (issuer + endpoints)
- `/.well-known/openid-configuration` (OIDC discovery alias)
- `/.well-known/oauth-protected-resource` (resource metadata)
- `/register` (dynamic client registration)
- `/authorize` (code grant)
- `/token` (token exchange)

MCP transport:
- `/sse` (HEAD/GET/OPTIONS for probes/CORS; POST for MCP JSON-RPC)
- `/health` (status)

The app prefers `X-Environment-Path` from NGINX to form `issuer` and endpoint URLs; `ENVIRONMENT_PATH` is only a fallback for non-proxied runs.

## Prerequisites

- Public domain with DNS A record (e.g., data.forensic-bot.com)
- Valid TLS certs (Let’s Encrypt via certbot in this repo)
- Docker Engine and Docker Compose
- Reachable MSSQL instance; set DB env vars in `.env`

## Environment Variables

Minimum required for the ChatGPT server:
- MSSQL_HOST, MSSQL_USER, MSSQL_PASSWORD, MSSQL_DATABASE
- MSSQL_DRIVER (default: ODBC Driver 18 for SQL Server)
- TrustServerCertificate=yes | Trusted_Connection=no (as applicable)
- READ_ONLY_MODE=true (recommended)
- ALLOWED_REDIRECT_HOSTS must include `chatgpt.com` (default list includes it)
- OPTIONAL (testing only):
  - ALLOW_UNAUTH_METHODS=true
  - ALLOW_UNAUTH_TOOLS_CALL=true
  Set to false in production.

No need to set `ENVIRONMENT_PATH` when behind NGINX; the proxy header is used.

## NGINX Essentials for ChatGPT

Relevant snippets (already in `nginx/conf.d/default.conf`):

- Root-level discovery proxy (avoid double slashes):
```nginx
merge_slashes on;
location ~ ^/\.well-known/(oauth-authorization-server|oauth-protected-resource|openid-configuration)$ {
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_set_header X-Environment-Path /chatgpt;
    # ... standard headers and CORS
}
```

- Scoped discovery and SSE under `/chatgpt`:
```nginx
location ~ ^/chatgpt/\.well-known/(oauth-authorization-server|oauth-protected-resource|openid-configuration)$ {
    rewrite ^/chatgpt(/.*)$ $1 break;
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_set_header X-Environment-Path /chatgpt;
}

location = /chatgpt/sse {
    # HEAD/OPTIONS handling, SSE proxy settings
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_set_header Authorization $http_authorization;
}
```

- Quirk redirects:
```nginx
location ~ ^/\.well-known/(oauth-authorization-server|oauth-protected-resource|openid-configuration)/chatgpt/sse$ {
    return 302 /.well-known/$1;
}
location ~ ^/chatgpt/sse/\.well-known/(oauth-authorization-server|oauth-protected-resource|openid-configuration)$ {
    return 302 /chatgpt/.well-known/$1;
}
```

## Deploy and Verify

1) Build and start services (Windows PowerShell examples):
```powershell
# From repo root
docker compose build mcp-server-chatgpt nginx
docker compose up -d mcp-server-chatgpt nginx
```

2) Verify health and discovery:
```powershell
# Health
curl https://data.forensic-bot.com/chatgpt/health

# Discovery (either path should work)
curl https://data.forensic-bot.com/.well-known/openid-configuration
curl https://data.forensic-bot.com/chatgpt/.well-known/oauth-authorization-server
```

3) Optional: quick SSE probe
```powershell
# Should return 200 with SSE headers (no stream)
curl -I https://data.forensic-bot.com/chatgpt/sse
```

## Add Connector in ChatGPT

- Open ChatGPT → Settings → Connectors → Add custom connector.
- Base URL: `https://data.forensic-bot.com/chatgpt/sse`
- OAuth will auto-discover via `.well-known/*` and perform:
  1. POST `/register`
  2. GET `/authorize` → redirect back to chatgpt.com with `code`
  3. POST `/token` → receive Bearer token
- On first use, ChatGPT will call `initialize`, `tools/list`, and then `tools/call`.

## Usage Hints (search/fetch)

Examples you can type in ChatGPT:
- "list all tables"
- "describe table Registration_data_csm"
- "sample Registration_data_csm limit 5"
- "select top 3 * from control.control_daily_copy"

The server caches search results and lets you `fetch` full content by the returned ids.

## Troubleshooting

- 404 on discovery URLs:
  - Confirm root-level `.well-known` proxy exists and uses `proxy_pass http://mcp-server-chatgpt:8008;` (no `/$uri`).
  - Ensure `merge_slashes on;` is set to normalize `//` paths.
  - Check that NGINX sends `X-Environment-Path: /chatgpt`.

- 401 on `/sse`:
  - Provide Bearer token from ChatGPT.
  - For testing only, set `ALLOW_UNAUTH_METHODS=true` and `ALLOW_UNAUTH_TOOLS_CALL=true`.

- 405 on GET/HEAD/OPTIONS:
  - Handlers for these methods are in the app; verify they are reachable via NGINX.

- 302 loops or redirect errors:
  - Ensure `ALLOWED_REDIRECT_HOSTS` contains `chatgpt.com`.

- Double-slash `//.well-known/...` returning 404:
  - The config here enables `merge_slashes` and avoids `/$uri` on `proxy_pass` to fix this.

- 500 in `/sse` after OAuth:
  - The app initializes request body defensively to avoid `UnboundLocalError`.

## Security Recommendations

- Keep `READ_ONLY_MODE=true` in production.
- Set `ALLOW_UNAUTH_METHODS=false` and `ALLOW_UNAUTH_TOOLS_CALL=false`.
- Restrict `ALLOWED_REDIRECT_HOSTS` to trusted domains.
- Forward only necessary headers (Host, X-Forwarded-*, Authorization).
- Use a DB user with least privileges.

## Appendix: Endpoint Reference

- Discovery
  - `/.well-known/oauth-authorization-server`
  - `/.well-known/openid-configuration`
  - `/.well-known/oauth-protected-resource`
- OAuth
  - `/register`, `/authorize`, `/token`
- MCP
  - `/sse` (HEAD/GET/OPTIONS/POST)
- Health
  - `/health`

---

Last updated: 2025-09-19
