# Guion del Video: Crear un Servidor MCP para conectar tus datos a Claude.ai

## 0:00 — Hook
- “Hoy vas a crear tu propio servidor MCP (Model Context Protocol) para conectar una base de datos SQL Server a Claude.ai, con seguridad OAuth 2.0, SSE y despliegue en Docker detrás de Nginx con TLS de Let's Encrypt.”

## 0:20 — Objetivo del video (Qué vamos a lograr)
- Construir un servidor MCP que actúe como puente seguro entre Claude.ai y tu base de datos.
- Permitir preguntas en lenguaje natural y que el servidor ejecute consultas SQL reales (SELECT, INSERT, UPDATE, DELETE).
- Dejarlo listo para producción con Nginx (reverse proxy), TLS/SSL, y renovación automática con Certbot.

## 0:45 — ¿Por qué es útil?
- Evita exportaciones manuales y copy/paste.
- Conecta datos en tiempo real, con control de acceso y auditoría.
- Mantiene tu esquema y tus datos dentro de tu perímetro, con OAuth 2.0 y tokens de corta duración.

## 1:10 — Agenda (Lo que aprenderás)
1. Qué es Model Context Protocol (MCP) y por qué usar SSE (Server-Sent Events).
2. Estructura del servidor MCP: endpoints, herramientas (tools) y negociación de capacidades.
3. Seguridad con OAuth 2.0: authorization_code, access_token, Bearer, discovery endpoints.
4. Infraestructura: Nginx como reverse proxy, TLS con Let's Encrypt y Certbot.
5. Despliegue con Docker, health checks y logs.
6. Integración con Claude Desktop (MCP client) y demo.

---

## 1:40 — Arquitectura (High-level)
- Cliente: Claude.ai (Claude Desktop) → HTTPS → Nginx (reverse proxy, SSL termination)
- Nginx → MCP Server (Python/Starlette) via HTTP interno (puerto 8008)
- MCP Server → SQL Server (ODBC Driver 18) con credenciales desde variables de entorno
- Transporte MCP: SSE para streaming bidireccional (event-driven)

Diagrama breve:
- Claude.ai ⇄ Nginx (443/TLS)
- Nginx ⇄ MCP Server (8008)
- MCP Server ⇄ MSSQL

---

## 2:20 — Model Context Protocol (MCP)
- Protocolo para que un assistant consuma herramientas (tools) expuestas por un servidor externo.
- Métodos típicos: initialize, tools/list, tools/call, notifications/initialized.
- Tools de base de datos:
  - list_tables
  - describe_table
  - execute_sql
  - get_table_sample
- Transporte: Server-Sent Events (SSE) para streams estables y eficientes.

---

## 3:10 — Seguridad: OAuth 2.0 (Authorization Code Flow)
- Estándar de autorización; el cliente obtiene acceso a recursos protegidos sin conocer credenciales del usuario.
- Discovery endpoints:
  - /.well-known/oauth-authorization-server
  - /.well-known/oauth-protected-resource
- Pasos en esta app:
  1) Registro dinámico:
     - Cliente envía {client_name, redirect_uris}
     - Servidor retorna client_id y client_secret
  2) Autorización:
     - Validación de client_id y redirect_uri
     - Emisión de authorization_code temporal
  3) Intercambio por token:
     - Cliente solicita access_token con authorization_code
     - Respuesta: {access_token, token_type="Bearer", expires_in=3600}
  4) Conexión SSE autenticada:
     - Cliente abre /sse con Authorization: Bearer <token>
  5) Comunicación MCP sobre SSE:
     - initialize → tools/list → tools/call
  6) Validación continua:
     - Verificación de expiración
     - Renovación repitiendo el flujo
- Almacenamiento en memoria: clientes, codes, tokens (para demo); en prod, usar store persistente.

---

## 4:30 — Nginx (Reverse Proxy)
- Software de alto rendimiento, arquitectura event-driven.
- Termina TLS, hace proxy a /sse con configuraciones críticas para SSE:
  - proxy_buffering off
  - proxy_read_timeout 24h
  - add_header Content-Type text/event-stream
- Beneficios: seguridad, performance, control de headers y timeouts.

---

## 5:10 — TLS con Let's Encrypt y Certbot
- Let's Encrypt: CA gratuita y automatizada que emite certificados SSL/TLS.
- Certbot: cliente ACME que obtiene y renueva certificados automáticamente.
- Flujo:
  - Validación HTTP-01 en puerto 80
  - Emisión de certificados
  - Renovación automática (cada 60–90 días)
- En contenedores: volumen compartido entre Nginx y Certbot para live certs.

---

## 5:50 — Stack Técnico
- Python 3.11 + Starlette (ASGI)
- ODBC Driver 18 for SQL Server (pyodbc)
- MCP 2025-06-18 con SSE
- OAuth 2.0 (RFC 9728 discovery)
- Docker + Docker Compose
- Nginx 1.24+ con optimización SSE
- GCP VM (ejemplo de plataforma de despliegue)

---

## 6:20 — Endpoints del Servidor
- Health: GET /health
- OAuth:
  - POST /register
  - GET /authorize
  - POST /token
  - Discovery: /.well-known/oauth-authorization-server, /.well-known/oauth-protected-resource
- MCP:
  - HEAD /sse (capability check)
  - POST /sse (stream MCP sobre SSE con Bearer token)

---

## 6:50 — Demo (flujo end-to-end)
1. Arrancar con Docker Compose (mcp-server, nginx, certbot).
2. Verificar /health.
3. Registrar cliente (POST /register) y anotar client_id/client_secret.
4. Completar authorization_code flow y obtener access_token.
5. Abrir conexión SSE con Authorization: Bearer.
6. Enviar initialize → tools/list → tools/call (ejemplo execute_sql con SELECT TOP 5).
7. Mostrar resultados serializados a JSON (tipos: Decimal, DateTime, etc.).

---

## 7:40 — Seguridad en Base de Datos
- Usuario read-only en producción.
- Consultas parametrizadas.
- TLS para conexiones a SQL Server (TrustServerCertificate según entorno).
- Variables de entorno para secretos (no hardcode).

---

## 8:05 — Despliegue y Operación
- Docker:
  - build, up -d, logs -f, healthcheck
- Nginx:
  - Config SSE, headers, HTTP/2
- Certificados:
  - setup inicial (HTTP-01), renovación automatizada con Certbot
- Monitoreo:
  - Métricas clave: latencia por tool, conexiones SSE activas, rate de tokens, performance SQL
  - Logs de contenedores y del app server

---

## 8:40 — Multi-tenant (opcional)
- Patrón para servir múltiples instancias MCP con distintas configs de base de datos.
- Aislamiento de credenciales y scopes por tenant.

---

## 9:00 — Troubleshooting rápido
- Database:
  - Validar drivers ODBC y cadena de conexión
- SSE:
  - Confirmar proxy_buffering off y timeouts en Nginx
- OAuth:
  - Revisar redirect_uri, expiración de tokens, clocks del servidor
- Certificados:
  - Verificar puertos 80/443 abiertos y renovación (dry-run)

---

## 9:30 — Cierre
- Ya tienes un servidor MCP seguro con OAuth 2.0, SSE y TLS, conectando SQL Server a Claude.ai.
- Siguientes pasos:
  - Endurecer almacenamiento de tokens y clientes
  - Añadir auditoría de queries
  - Extender tools (p.ej. paginación, explain, plantillas de queries)