# Guía Técnica Extendida: Construyendo un Servidor MCP para Integración de Base de Datos con Claude.ai

## Tabla de Contenidos
- [Parte 1: Introducción y Conceptos (0:00-5:00)](#parte-1-introducción-y-conceptos-000-500)
- [Parte 2: Arquitectura y Diseño (5:00-15:00)](#parte-2-arquitectura-y-diseño-500-1500)
- [Parte 3: Implementación de Seguridad (15:00-25:00)](#parte-3-implementación-de-seguridad-1500-2500)
- [Parte 4: Desarrollo e Implementación (25:00-40:00)](#parte-4-desarrollo-e-implementación-2500-4000)
- [Parte 5: Despliegue e Infraestructura (40:00-55:00)](#parte-5-despliegue-e-infraestructura-4000-5500)
- [Parte 6: Testing y Validación (55:00-65:00)](#parte-6-testing-y-validación-5500-6500)
- [Parte 7: Operaciones en Producción (65:00-80:00)](#parte-7-operaciones-en-producción-6500-8000)
- [Parte 8: Temas Avanzados y Mejores Prácticas (80:00-90:00)](#parte-8-temas-avanzados-y-mejores-prácticas-8000-9000)

---

## Parte 1: Introducción y Conceptos (0:00-5:00)

### 0:00 — Apertura y Gancho
**"Bienvenido a esta guía técnica comprehen

siva sobre la construcción de un servidor MCP listo para producción que conecta de forma segura tu base de datos Microsoft SQL Server con Claude.ai."**

En este tutorial extendido, aprenderás a construir un puente de nivel empresarial entre tu base de datos e IA, implementando seguridad estándar de la industria con OAuth 2.0, cifrado TLS y despliegue containerizado.

### 0:30 — Qué Vamos a Construir
Al final de esta guía, tendrás:
- Un servidor MCP (Model Context Protocol) completamente funcional
- Autenticación segura OAuth 2.0 con registro dinámico de clientes
- Server-Sent Events (SSE) para comunicación bidireccional en tiempo real
- Despliegue listo para producción con Docker, Nginx y Let's Encrypt
- Capacidades completas de monitoreo, logging y troubleshooting

### 1:00 — Por Qué Esto Importa

**Problemas del Enfoque Tradicional:**
- Exportaciones manuales de datos (consume tiempo, propenso a errores)
- Flujos de trabajo copy-paste (sin pista de auditoría)
- Datos obsoletos (snapshots se vuelven desactualizados)
- Riesgos de seguridad (credenciales en emails/documentos)
- Sin control de acceso (enfoque todo-o-nada)

**Beneficios del Servidor MCP:**
- **Acceso en Tiempo Real**: Queries de base de datos en vivo mediante lenguaje natural
- **Seguridad**: Tokens OAuth 2.0, cifrado TLS, credenciales de corta duración
- **Pista de Auditoría**: Cada query registrado con atribución de usuario
- **Control de Acceso**: Permisos granulares (solo lectura, tablas específicas, etc.)
- **Residencia de Datos**: Tus datos permanecen en tu infraestructura
- **Escalabilidad**: Soporte multi-tenant para diferentes equipos/entornos

### 2:00 — Casos de Uso del Mundo Real

**Equipo Financiero:**
```
Query Claude: "Muestra ingresos por categoría de producto para Q4 2024"
Servidor MCP → Ejecuta SQL → Retorna resultados formateados
Beneficios: Análisis financiero en tiempo real sin exportar datos sensibles
```

**Equipo de Operaciones:**
```
Query Claude: "Lista todas las transacciones fallidas en la última hora"
Servidor MCP → Consulta logs → Alerta sobre patrones
Beneficios: Respuesta inmediata a incidentes con contexto
```

**Analistas de Negocio:**
```
Query Claude: "Compara costos de adquisición de clientes entre regiones"
Servidor MCP → Queries JOIN complejas → Análisis de tendencias
Beneficios: Analítica self-service sin conocimiento de SQL
```

### 3:00 — Entendiendo el Model Context Protocol (MCP)

**¿Qué es MCP?**
- Protocolo abierto desarrollado por Anthropic
- Versión de especificación: 2025-06-18
- Estandariza cómo los asistentes IA consumen herramientas y datos externos
- Comunicación basada en JSON-RPC
- Transport agnóstico (usamos Server-Sent Events)

**Conceptos Core:**

**1. Tools** - Acciones que el servidor puede realizar:
```json
{
  "name": "execute_sql",
  "description": "Ejecutar queries SQL contra base de datos",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "SQL a ejecutar"}
    }
  }
}
```

**2. Resources** - Datos que el servidor puede proveer (nos enfocamos en database tools)

**3. Prompts** - Workflows template (opcional, no cubierto aquí)

**4. Sampling** - Servidor solicitando completions LLM (opcional)

### 4:00 — ¿Por Qué Server-Sent Events (SSE)?

**Ventajas de SSE:**
- Conexión persistente unidireccional (servidor → cliente)
- Construido sobre HTTP/HTTPS (funciona a través de firewalls)
- Auto-reconexión con Last-Event-ID
- Basado en texto (fácil de debuggear)
- Soporte nativo en navegadores
- Menos overhead que WebSockets para nuestro caso de uso

**SSE vs WebSockets:**
- SSE: Más simple, funciona sobre HTTP/2, mejor para server-push
- WebSockets: Bidireccional, soporte binario, más complejo

**SSE vs Polling:**
- SSE: Tiempo real, eficiente, conexión única
- Polling: Retrasado, desperdiciador, múltiples requests

**Nuestra Implementación:**
- SSE para capa de transporte
- JSON-RPC para formato de mensaje
- Conexiones de larga duración (timeout 24 horas)
- Autenticación OAuth Bearer token

---

## Parte 2: Arquitectura y Diseño (5:00-15:00)

### 5:00 — Arquitectura de Alto Nivel

```
┌─────────────────┐
│   CLAUDE.AI     │
│  (Web/Desktop)  │
│                 │
│ Cliente OAuth   │
│ Consumidor SSE  │
└────────┬────────┘
         │ HTTPS (443)
         │ TLS 1.2+
         ▼
┌─────────────────┐
│     NGINX       │
│ Reverse Proxy   │
│                 │
│ - Term. SSL     │
│ - Load Balance  │
│ - Rate Limit    │
└────────┬────────┘
         │ HTTP (8008)
         │ Interno
         ▼
┌─────────────────┐
│ SERVIDOR MCP    │
│  (Python 3.11)  │
│                 │
│ - Starlette     │
│ - Lógica OAuth  │
│ - Tool Handlers │
└────────┬────────┘
         │ ODBC
         │ TLS
         ▼
┌─────────────────┐
│  SQL SERVER     │
│  Base de Datos  │
│                 │
│ - Gestión User  │
│ - Row Security  │
│ - Auditoría     │
└─────────────────┘
```

### 6:00 — Deep Dive de Componentes

**1. Cliente Claude.ai**
- Claude Desktop App (servidores MCP locales)
- Claude Web Interface (servidores MCP remotos)
- Inicia flujo OAuth automáticamente
- Gestiona refresh de tokens
- Presenta capacidades de tools a usuarios

**2. NGINX Reverse Proxy**
- **Propósito**: Límite de seguridad, terminación SSL
- **Versión**: 1.24+ recomendado
- **Características Clave**:
  - TLS 1.2/1.3 con ciphers modernos
  - Soporte HTTP/2 para performance
  - Optimizaciones específicas SSE
  - Control de buffering request/response
  - Gestión de timeout de conexión

**Configuraciones NGINX Críticas para SSE:**
```nginx
location /demo/sse {
    proxy_pass http://mcp-server:8008;
    
    # CRÍTICO: Deshabilitar buffering para SSE
    proxy_buffering off;
    proxy_cache off;
    
    # CRÍTICO: Timeouts largos para conexiones persistentes
    proxy_read_timeout 86400s;  # 24 horas
    proxy_send_timeout 86400s;  # 24 horas
    
    # HTTP/1.1 requerido para SSE
    proxy_http_version 1.1;
    
    # SSE requiere Connection: ''
    proxy_set_header Connection '';
    
    # Deshabilitar chunked transfer encoding
    chunked_transfer_encoding off;
    
    # Forward authentication
    proxy_set_header Authorization $http_authorization;
    
    # Headers de respuesta SSE
    add_header Content-Type text/event-stream;
    add_header Cache-Control no-cache;
    add_header X-Accel-Buffering no;
}
```

**3. Servidor MCP (Python)**
- **Framework**: Starlette (async ASGI)
- **Lenguaje**: Python 3.11+
- **Bibliotecas**:
  - `starlette`: Framework ASGI
  - `pyodbc`: Conectividad SQL Server
  - `python-dotenv`: Configuración de entorno
  - `secrets`: Generación segura de tokens

**Responsabilidades del Servidor:**
- Implementación OAuth 2.0 (AS + RS)
- Manejo de protocolo MCP (JSON-RPC)
- Ejecución de tools (operaciones de base de datos)
- Serialización de datos (tipos SQL → JSON)
- Validación y gestión de tokens
- Logging y auditoría de requests

**4. Base de Datos SQL Server**
- **Versión**: 2019+ recomendado
- **Driver**: ODBC Driver 18 para SQL Server
- **Conexión**: Cifrada TLS
- **Autenticación**: Autenticación SQL Server (usuario/contraseña)

### 8:00 — Flujo de Datos: Ejecución de Query

**Flujo Paso a Paso:**

```
1. Usuario pregunta a Claude: "Muestra top 10 clientes por ingresos"

2. Claude analiza y determina tool necesario:
   Tool: execute_sql
   Arguments: {
     "query": "SELECT TOP 10 CustomerID, SUM(Revenue) as TotalRev..."
   }

3. Claude envía request MCP sobre SSE:
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

4. Servidor MCP valida:
   - ¿Token Bearer válido y no expirado?
   - ¿Usuario tiene permiso para execute_sql?
   - ¿Query es seguro (si READ_ONLY_MODE, verificar solo SELECT)?

5. Ejecutar query:
   - Abrir conexión de base de datos (pooled)
   - Ejecutar query parametrizado
   - Obtener resultados
   - Serializar tipos de datos (Decimal, DateTime → JSON)
   - Cerrar cursor

6. Enviar respuesta:
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

7. Claude recibe resultados, formatea para usuario:
   "Aquí están tus top 10 clientes por ingresos:
    1. CustomerID 1: $150,000
    2. CustomerID 2: $125,000
    ..."
```

### 10:00 — Formatos Request/Response

**Mensajes de Protocolo MCP:**

**Initialize (Negociación de Capacidades):**
```json
// Cliente → Servidor
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

// Servidor → Cliente
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
// Cliente → Servidor
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}

// Servidor → Cliente
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "list_tables",
        "description": "Listar todas las tablas en la base de datos",
        "inputSchema": {
          "type": "object",
          "properties": {},
          "required": []
        }
      },
      {
        "name": "describe_table",
        "description": "Obtener estructura y metadatos de tabla",
        "inputSchema": {
          "type": "object",
          "properties": {
            "table_name": {
              "type": "string",
              "description": "Nombre de la tabla a describir"
            }
          },
          "required": ["table_name"]
        }
      },
      {
        "name": "execute_sql",
        "description": "Ejecutar query SQL (solo SELECT en modo read-only)",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "Query SQL a ejecutar"
            }
          },
          "required": ["query"]
        }
      },
      {
        "name": "get_table_sample",
        "description": "Obtener datos de muestra de una tabla",
        "inputSchema": {
          "type": "object",
          "properties": {
            "table_name": {
              "type": "string",
              "description": "Nombre de la tabla"
            },
            "limit": {
              "type": "integer",
              "description": "Número de filas a retornar",
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

### 12:00 — Arquitectura Multi-Tenant

**Soportando Múltiples Entornos:**

```
Configuración Producción:
├── /demo/sse         → Entorno demo (DemoDB, read-only)
├── /production/sse   → Entorno producción (ProdDB, read-write)
└── /analytics/sse    → Entorno analytics (AnalyticsDB, read-only)

Cada entorno tiene:
- Conexión de base de datos separada
- Credenciales diferentes
- Scopes OAuth aislados
- Permisos de tools personalizados
- Monitoreo independiente
```

**Beneficios:**
- Separación segura de responsabilidades
- Diferentes niveles de acceso por entorno
- Configuraciones específicas por equipo
- Entorno de testing seguro
- Capacidad de rollout gradual

**Patrón de Implementación:**
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

### 14:00 — Gestión de Scoping y Paths

**¿Por Qué Paths con Scope?**
- `/demo/sse` vs `/production/sse`
- Cada scope tiene su propio issuer OAuth
- Previene reutilización de tokens entre entornos
- Separación clara en logs y monitoreo

**Reescritura de Path en NGINX:**
```nginx
# Entorno demo
location ~ ^/demo/(.*)$ {
    rewrite ^/demo(/.*)$ $1 break;
    proxy_pass http://mcp-server-demo:8008;
    proxy_set_header X-Environment-Path /demo;
}

# Entorno producción
location ~ ^/production/(.*)$ {
    rewrite ^/production(/.*)$ $1 break;
    proxy_pass http://mcp-server-production:8008;
    proxy_set_header X-Environment-Path /production;
}
```

**El Servidor Usa X-Environment-Path:**
```python
# En server_oauth.py
def get_base_url(request: Request) -> str:
    env_path = request.headers.get("x-environment-path", "")
    proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("host", "domain.com")
    
    base = f"{proto}://{host}"
    if env_path:
        base += env_path
    
    return base  # ej., "https://domain.com/demo"
```

---

## Parte 3: Implementación de Seguridad (15:00-25:00)

### 15:00 — Flujo OAuth 2.0 Authorization Code

**¿Por Qué OAuth 2.0?**
- Estándar de industria (RFC 6749)
- Autorización delegada (sin compartir contraseña)
- Tokens de corta duración (default 1 hora)
- Capacidad de refresh
- Permisos basados en scope
- Auditable (quién accedió qué, cuándo)

**Diagrama de Flujo:**

```
┌──────────┐                               ┌──────────┐
│  Claude  │                               │   MCP    │
│ Desktop  │                               │ Servidor │
└────┬─────┘                               └────┬─────┘
     │                                          │
     │  1. Iniciar OAuth                        │
     ├─────────────────────────────────────────>│
     │     POST /demo/register                  │
     │     {client_name, redirect_uris}         │
     │                                          │
     │<─────────────────────────────────────────┤
     │     200 OK                               │
     │     {client_id, client_secret}           │
     │                                          │
     │  2. Request de Autorización              │
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
     │  3. Intercambio de Token                 │
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
     │  4. Conexión SSE Autenticada             │
     ├─────────────────────────────────────────>│
     │     POST /demo/sse                       │
     │     Authorization: Bearer eyJ...         │
     │                                          │
     │<═════════════════════════════════════════│
     │     Stream SSE (persistente)             │
     │                                          │
```

### 17:00 — OAuth Discovery (RFC 8414)

**¿Por Qué Discovery?**
- Claude encuentra automáticamente endpoints OAuth
- No se necesita configuración manual
- Soporta clientes OAuth estándar
- Compatibilidad de versiones

**Respuesta del Endpoint de Discovery:**
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

**Metadatos de Recurso Protegido:**
```json
GET /.well-known/oauth-protected-resource

{
  "resource": "https://data.forensic-bot.com/demo/sse",
  "oauth_authorization_server": "https://data.forensic-bot.com/demo",
  "bearer_methods_supported": ["header"],
  "resource_documentation": "https://data.forensic-bot.com/docs"
}
```

### 19:00 — Gestión de Tokens

**Generación de Token (Segura):**
```python
import secrets

def generate_token() -> str:
    """Generar token aleatorio criptográficamente seguro"""
    return secrets.token_urlsafe(32)  # 256 bits de entropía

# Ejemplo de salida: "dGhpcyBpcyBhIHJhbmRvbSB0b2tlbg"
```

**Almacenamiento de Token (En Memoria para Demo):**
```python
from datetime import datetime, timedelta
from typing import Dict, Any

# Store global de tokens
valid_tokens: Dict[str, Dict[str, Any]] = {}

def store_token(access_token: str, client_id: str) -> None:
    """Almacenar token con expiración"""
    valid_tokens[access_token] = {
        "client_id": client_id,
        "issued_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }

def validate_token(access_token: str) -> bool:
    """Verificar si token existe y no está expirado"""
    if access_token not in valid_tokens:
        return False
    
    token_data = valid_tokens[access_token]
    expires_at = datetime.fromisoformat(token_data["expires_at"])
    
    return datetime.utcnow() < expires_at
```

**Almacenamiento de Token en Producción:**
```python
# Para producción, usar almacenamiento persistente:
# - Redis (rápido, en memoria, soporte TTL)
# - PostgreSQL (persistente, transaccional)
# - DynamoDB (AWS, gestionado, escalable)

# Ejemplo con Redis:
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def store_token_redis(access_token: str, client_id: str) -> None:
    redis_client.setex(
        name=f"token:{access_token}",
        time=3600,  # TTL 1 hora
        value=json.dumps({"client_id": client_id})
    )
```

### 21:00 — Mejores Prácticas de Seguridad

**1. Modo Read-Only (Altamente Recomendado):**
```python
READ_ONLY_MODE = os.getenv("READ_ONLY_MODE", "true").lower() == "true"

def execute_sql_impl(query: str) -> str:
    if READ_ONLY_MODE:
        # Verificar que query solo contiene SELECT
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT") and \
           not query_upper.startswith("WITH"):
            raise ValueError("Solo queries SELECT permitidas en modo read-only")
    
    # Ejecutar query...
```

**2. Usuario de Base de Datos con Menor Privilegio:**
```sql
-- Crear usuario read-only para entorno demo
CREATE LOGIN claude_demo WITH PASSWORD = 'SecurePassword123!';
CREATE USER claude_demo FOR LOGIN claude_demo;

-- Otorgar permisos mínimos
GRANT CONNECT ON DATABASE::DemoDB TO claude_demo;
GRANT SELECT ON SCHEMA::dbo TO claude_demo;

-- Para tablas específicas solamente
GRANT SELECT ON dbo.Customers TO claude_demo;
GRANT SELECT ON dbo.Orders TO claude_demo;

-- Denegar operaciones peligrosas
DENY INSERT, UPDATE, DELETE, EXECUTE ON SCHEMA::dbo TO claude_demo;
```

**3. Row-Level Security:**
```sql
-- Ejemplo: Usuarios solo pueden ver datos de su departamento
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

**4. Auditoría de SQL Server:**
```sql
-- Crear especificación de auditoría
CREATE SERVER AUDIT MCP_Audit
TO FILE (FILEPATH = 'C:\Audits\', MAXSIZE = 100 MB)
WITH (ON_FAILURE = CONTINUE);

ALTER SERVER AUDIT MCP_Audit WITH (STATE = ON);

-- Auditar todos los statements SELECT
CREATE DATABASE AUDIT SPECIFICATION MCP_DB_Audit
FOR SERVER AUDIT MCP_Audit
    ADD (SELECT ON DATABASE::DemoDB BY claude_demo)
WITH (STATE = ON);
```

### 23:00 — Configuración TLS/SSL

**Emisión de Certificado Let's Encrypt:**
```bash
# Comando Certbot para emisión de certificado
certbot certonly --webroot \
    -w /var/www/certbot \
    --email admin@domain.com \
    -d data.forensic-bot.com \
    --rsa-key-size 4096 \
    --agree-tos \
    --non-interactive

# Archivos de certificado generados:
# /etc/letsencrypt/live/data.forensic-bot.com/fullchain.pem
# /etc/letsencrypt/live/data.forensic-bot.com/privkey.pem
```

**Configuración SSL en NGINX:**
```nginx
server {
    listen 443 ssl http2;
    server_name data.forensic-bot.com;
    
    # Certificado SSL
    ssl_certificate /etc/letsencrypt/live/data.forensic-bot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/data.forensic-bot.com/privkey.pem;
    
    # Configuración SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/data.forensic-bot.com/chain.pem;
    
    # Headers de Seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

### 24:00 — Checklist de Seguridad

**Auditoría de Seguridad Pre-Producción:**

✅ **Autenticación y Autorización**
- [ ] OAuth 2.0 completamente implementado
- [ ] Expiración de token configurada a 1 hora o menos
- [ ] Rotación de refresh token habilitada
- [ ] ALLOWED_REDIRECT_HOSTS configurado correctamente
- [ ] No hay flags de test/desarrollo habilitados

✅ **Seguridad de Base de Datos**
- [ ] READ_ONLY_MODE habilitado (si aplica)
- [ ] Usuario de base de datos con menor privilegio
- [ ] No usar cuentas sa o admin
- [ ] Row-level security implementada (si es necesario)
- [ ] Audit logging habilitado
- [ ] Connection string en variables de entorno (no en código)

✅ **Seguridad de Red**
- [ ] TLS 1.2+ forzado
- [ ] Solo cipher suites fuertes
- [ ] Header HSTS configurado
- [ ] Reglas de firewall restrictivas
- [ ] Rate limiting implementado
- [ ] CORS configurado correctamente

✅ **Seguridad de Aplicación**
- [ ] Validación de entrada en todos los queries
- [ ] Prevención de inyección SQL (queries parametrizados)
- [ ] Mensajes de error no filtran info sensible
- [ ] Logging excluye passwords/tokens
- [ ] Dependencias actualizadas y escaneadas
- [ ] Secrets en variables de entorno

---

## Parte 4: Desarrollo e Implementación (25:00-40:00)

### 25:00 — Estructura del Proyecto

**Organización del Repositorio:**
```
mssql-mcp-server/
├── server_oauth.py          # Servidor MCP principal para Claude.ai
├── requirements.txt         # Dependencias Python
├── Dockerfile              # Build de contenedor
├── docker-compose.yml      # Orquestación de servicios
├── .env                    # Variables de entorno (gitignored)
├── .env.example            # Template para .env
├── nginx/
│   ├── nginx.conf          # Config principal NGINX
│   └── conf.d/
│       └── default.conf    # Configuración del sitio
├── certbot/
│   ├── conf/              # Certificados SSL
│   └── www/               # Desafío ACME
├── logs/
│   ├── nginx/             # Logs NGINX
│   └── mcp/               # Logs de aplicación
├── docs/
│   ├── claude-connector-setup.md
│   ├── explicacion_es.md
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

### 26:30 — Dependencias Core

**requirements.txt:**
```txt
# Framework ASGI
starlette==0.35.1
uvicorn[standard]==0.27.0

# Base de Datos
pyodbc==5.0.1

# Entorno
python-dotenv==1.0.0

# Desarrollo
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.12.1
mypy==1.7.1
```

### 27:00 — Gestión de Conexión a Base de Datos

**Constructor de Connection String:**
```python
from typing import Tuple, Dict
import os
import pyodbc

def get_db_config() -> Tuple[Dict[str, str], str]:
    """
    Construir connection string ODBC desde variables de entorno.
    
    Returns:
        Tupla de (dict config, connection string)
    
    Raises:
        ValueError: Si faltan variables de entorno requeridas
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
    
    # Validar campos requeridos
    if not all([config["server"], config["user"], 
                config["password"], config["database"]]):
        raise ValueError("Falta configuración de base de datos requerida")
    
    # Construir connection string
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

**Connection Pool (Producción):**
```python
from contextlib import contextmanager
import queue
import threading

class ConnectionPool:
    """Pool simple de conexiones para base de datos"""
    
    def __init__(self, connection_string: str, pool_size: int = 5):
        self.connection_string = connection_string
        self.pool = queue.Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        
        # Inicializar pool
        for _ in range(pool_size):
            conn = pyodbc.connect(connection_string)
            self.pool.put(conn)
    
    @contextmanager
    def get_connection(self):
        """Obtener conexión del pool"""
        conn = self.pool.get()
        try:
            yield conn
        finally:
            self.pool.put(conn)
    
    def close_all(self):
        """Cerrar todas las conexiones en pool"""
        while not self.pool.empty():
            conn = self.pool.get()
            conn.close()
```

### 29:00 — Detalles de Implementación de Tools

**Tool 1: list_tables**
```python
def list_tables_impl() -> str:
    """
    Listar todas las tablas en base de datos usando INFORMATION_SCHEMA.
    
    Returns:
        String JSON de lista de tablas con info de schema
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
    Obtener estructura detallada de tabla incluyendo columnas, tipos, constraints.
    
    Args:
        table_name: Nombre de tabla a describir
        
    Returns:
        String JSON con metadatos de tabla
    """
    _, connection_string = get_db_config()
    
    # Obtener columnas
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
    
    # Obtener primary keys
    pk_query = """
        SELECT 
            COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_NAME = ?
        AND CONSTRAINT_NAME LIKE 'PK_%'
    """
    
    # Obtener foreign keys
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
        
        # Obtener columnas
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
        
        # Obtener primary keys
        cursor.execute(pk_query, (table_name,))
        primary_keys = [row.COLUMN_NAME for row in cursor.fetchall()]
        
        # Obtener foreign keys
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

### 33:00 — Serialización de Datos

**Manejando Tipos de Datos de SQL Server:**
```python
from decimal import Decimal
from datetime import datetime, date
import json

def serialize_row_data(data):
    """
    Convertir datos de Row de pyodbc a formato serializable JSON.
    
    Maneja:
    - Decimal → float
    - datetime → string ISO 8601
    - date → string ISO 8601
    - bytes → string base64
    - None → null
    
    Args:
        data: Valor de fila de base de datos
        
    Returns:
        Valor serializable JSON
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
        # Fallback: convertir a string
        return str(data)
```

Debido a límites de longitud, he completado las partes más críticas. ¿Te gustaría que continúe con las secciones restantes (Parte 5-8) que incluyen despliegue, testing, operaciones en producción y temas avanzados?