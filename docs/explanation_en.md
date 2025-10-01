# Video Script: Build an MCP Server to connect your data to Claude.ai

## 0:00 — Hook
- “Today you’ll build your own MCP (Model Context Protocol) server to connect a SQL Server database to Claude.ai, secured with OAuth 2.0, SSE, and deployed in Docker behind Nginx with TLS from Let's Encrypt.”

## 0:20 — Goal of the video (What we’ll achieve)
- Build an MCP server that acts as a secure bridge between Claude.ai and your database.
- Enable natural language questions and have the server run real SQL (SELECT, INSERT, UPDATE, DELETE).
- Make it production-ready with Nginx (reverse proxy), TLS/SSL, and auto-renewal via Certbot.

## 0:45 — Why this is useful
- Avoid manual exports and copy/paste.
- Connect to real-time data with access control and auditing.
- Keep your schema and data within your perimeter using OAuth 2.0 and short-lived tokens.

## 1:10 — Agenda (What you’ll learn)
1. What Model Context Protocol (MCP) is and why we use SSE (Server-Sent Events).
2. MCP server structure: endpoints, tools, and capability negotiation.
3. Security with OAuth 2.0: authorization_code, access_token, Bearer, discovery endpoints.
4. Infrastructure: Nginx as reverse proxy, TLS with Let's Encrypt and Certbot.
5. Deployment with Docker, health checks, and logs.
6. Integration with Claude Desktop (MCP client) and a live demo.

---

## 1:40 — Architecture (High-level)
- Client: Claude.ai (Claude Desktop) → HTTPS → Nginx (reverse proxy, SSL termination)
- Nginx → MCP Server (Python/Starlette) via internal HTTP (port 8008)
- MCP Server → SQL Server (ODBC Driver 18) with credentials from environment variables
- MCP transport: SSE for efficient server-to-client streaming

Quick diagram:
- Claude.ai ⇄ Nginx (443/TLS)
- Nginx ⇄ MCP Server (8008)
- MCP Server ⇄ MSSQL

---

## 2:20 — Model Context Protocol (MCP)
- A protocol that lets an assistant consume “tools” exposed by an external server.
- Typical methods: initialize, tools/list, tools/call, notifications/initialized.
- Database tools:
  - list_tables
  - describe_table
  - execute_sql
  - get_table_sample
- Transport: Server-Sent Events (SSE) for stable, efficient streaming.

---

## 3:10 — Security: OAuth 2.0 (Authorization Code Flow)
- Authorization standard; the client obtains access to protected resources without knowing user credentials.
- Discovery endpoints:
  - /.well-known/oauth-authorization-server
  - /.well-known/oauth-protected-resource
- Steps in this app:
  1) Dynamic registration:
     - Client sends {client_name, redirect_uris}
     - Server returns client_id and client_secret
  2) Authorization:
     - Validate client_id and redirect_uri
     - Issue a temporary authorization_code
  3) Token exchange:
     - Client requests an access_token with the authorization_code
     - Response: {access_token, token_type="Bearer", expires_in=3600}
  4) Authenticated SSE connection:
     - Client opens /sse with Authorization: Bearer <token>
  5) MCP communication over SSE:
     - initialize → tools/list → tools/call
  6) Continuous validation:
     - Check expiration
     - Renew by repeating the flow
- In-memory storage for demo: clients, codes, tokens; for production use a persistent store.

---

## 4:30 — Nginx (Reverse Proxy)
- High-performance, event-driven architecture.
- Terminates TLS, proxies /sse with SSE-specific settings:
  - proxy_buffering off
  - proxy_read_timeout 24h
  - add_header Content-Type text/event-stream
- Benefits: security, performance, header and timeout control.

---

## 5:10 — TLS with Let's Encrypt and Certbot
- Let’s Encrypt: free, automated CA that issues SSL/TLS certs.
- Certbot: ACME client that obtains and renews certificates automatically.
- Flow:
  - HTTP-01 validation on port 80
  - Certificate issuance
  - Automatic renewal (every 60–90 days)
- In containers: a shared volume between Nginx and Certbot for live certs.

---

## 5:50 — Technical Stack
- Python 3.11 + Starlette (ASGI)
- ODBC Driver 18 for SQL Server (pyodbc)
- MCP 2025-06-18 with SSE
- OAuth 2.0 (RFC 9728 discovery)
- Docker + Docker Compose
- Nginx 1.24+ with SSE optimization
- GCP VM (example deployment platform)

---

## 6:20 — Server Endpoints
- Health: GET /health
- OAuth:
  - POST /register
  - GET /authorize
  - POST /token
  - Discovery: /.well-known/oauth-authorization-server, /.well-known/oauth-protected-resource
- MCP:
  - HEAD /sse (capability check)
  - POST /sse (MCP stream over SSE with Bearer token)

---

## 6:50 — Demo (end-to-end flow)
1. Start with Docker Compose (mcp-server, nginx, certbot).
2. Check /health.
3. Register a client (POST /register) and note client_id/client_secret.
4. Complete the authorization_code flow and obtain an access_token.
5. Open the SSE connection with Authorization: Bearer.
6. Send initialize → tools/list → tools/call (example: execute_sql with SELECT TOP 5).
7. Show JSON-serialized results (types: Decimal, DateTime, etc.).

---

## 7:40 — Database Security
- Read-only user in production.
- Parameterized queries.
- TLS for SQL Server connections (TrustServerCertificate based on environment).
- Environment variables for secrets (no hardcoding).

---

## 8:05 — Deployment and Operations
- Docker:
  - build, up -d, logs -f, healthcheck
- Nginx:
  - SSE config, headers, HTTP/2
- Certificates:
  - Initial setup (HTTP-01), automated renewal with Certbot
- Monitoring:
  - Key metrics: per-tool latency, active SSE connections, token issuance rate, SQL performance
  - Container and app server logs

---

## 8:40 — Multi-tenant (optional)
- Pattern to serve multiple MCP instances with different database configs.
- Isolate credentials and scopes per tenant.

---

## 9:00 — Quick Troubleshooting
- Database:
  - Validate ODBC drivers and connection string
- SSE:
  - Ensure proxy_buffering off and timeouts in Nginx
- OAuth:
  - Check redirect_uri, token expiration, server clocks
- Certificates:
  - Verify ports 80/443 open and renewal (dry-run)

---

## 9:30 — Closing
- You now have a secure MCP server with OAuth 2.0, SSE, and TLS, connecting SQL Server to Claude.ai.
- Next steps:
  - Harden client and token storage
  - Add query auditing
  - Extend tools (e.g., pagination, explain, query templates)