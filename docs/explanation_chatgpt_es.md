# Guía Técnica Extendida: Construcción de un Servidor MCP para Integración de Base de Datos con ChatGPT

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

### 0:00 — Apertura y Presentación
**"Bienvenido a esta guía técnica comprensiva sobre la construcción de un servidor MCP listo para producción que conecta de forma segura tu base de datos Microsoft SQL Server con la funcionalidad Deep Research de ChatGPT."**

En este tutorial extendido, aprenderás a construir un puente de nivel empresarial entre tu base de datos e IA, implementando seguridad estándar de la industria con OAuth 2.0, cifrado TLS y despliegue containerizado específicamente optimizado para la integración con ChatGPT.

### 0:30 — Qué Vamos a Construir
Al final de esta guía, tendrás:
- Un servidor MCP (Model Context Protocol) completamente funcional para ChatGPT
- Autenticación segura OAuth 2.0 con registro dinámico de clientes
- Server-Sent Events (SSE) para comunicación bidireccional en tiempo real
- Despliegue listo para producción con Docker, NGINX y Let's Encrypt
- Tools especializadas (`search` y `fetch`) optimizadas para Deep Research de ChatGPT
- Capacidades completas de monitoreo, logging y troubleshooting

### 1:00 — Por Qué Esto Importa

**Problemas del Enfoque Tradicional:**
- Exportaciones manuales de datos (consume tiempo, propenso a errores)
- Flujos de trabajo copy-paste (sin pista de auditoría)
- Datos obsoletos (snapshots se vuelven desactualizados)
- Riesgos de seguridad (credenciales en emails/documentos)
- Sin control de acceso (enfoque todo-o-nada)
- ChatGPT no puede acceder a información de base de datos en tiempo real

**Beneficios del Servidor MCP:**
- **Acceso en Tiempo Real**: Queries de base de datos en vivo mediante lenguaje natural vía ChatGPT
- **Seguridad**: Tokens OAuth 2.0, cifrado TLS, credenciales de corta duración
- **Pista de Auditoría**: Cada query registrado con atribución de usuario
- **Control de Acceso**: Permisos granulares (solo lectura, tablas específicas, etc.)
- **Escalabilidad**: Manejo de múltiples sesiones concurrentes de ChatGPT
- **Integración Deep Research**: Diseñado específicamente para las capacidades avanzadas de investigación de ChatGPT

### 2:00 — Arquitectura Específica para ChatGPT

**Características de ChatGPT Deep Research:**
- Queries de investigación multi-paso
- Exploración iterativa de datos
- Caching de resultados y recuperación de registros
- Traducción de lenguaje natural a SQL
- Formateo de salida estructurada

**Diferencias Clave vs Claude.ai:**
```
Conector ChatGPT            vs          Conector Claude.ai
├── search tool                         ├── list_tables
├── fetch tool                          ├── describe_table
├── Caching de resultados               ├── execute_sql
├── Recuperación basada en ID           ├── get_table_sample
└── Optimizado para Deep Research       └── Mapeo directo de tools
```

### 3:00 — Visión General de Model Context Protocol (MCP)

**¿Qué es MCP?**
- Especificación: versión `2025-06-18`
- Propósito: Forma estandarizada para que modelos de IA interactúen con sistemas externos
- Transporte: Server-Sent Events (SSE) para conexiones persistentes
- Formato: Mensajes JSON-RPC 2.0
- Seguridad: Tokens bearer OAuth 2.0

**Flujo de Request MCP:**
```
ChatGPT → initialize → Servidor responde con capacidades
ChatGPT → tools/list → Servidor describe tools disponibles
ChatGPT → tools/call → Servidor ejecuta y retorna resultados
```

### 4:00 — Explicación de Server-Sent Events (SSE)

**¿Por Qué SSE para ChatGPT?**
- **Conexión Persistente**: Mantiene canal abierto para múltiples requests
- **Unidireccional**: Streaming Servidor→Cliente (perfecto para respuestas de IA)
- **Basado en HTTP**: Funciona a través de firewalls y proxies
- **Reconexión Automática**: Mecanismo de retry incorporado
- **Compatible con ChatGPT**: Soporte nativo de SSE en Deep Research

**SSE vs WebSockets:**
```
SSE (Nuestra Elección)          WebSockets
├── Implementación más simple   ├── Full duplex
├── Reconexión automática       ├── Menor overhead
├── Compatible con HTTP/1.1     ├── Requiere upgrade
├── Soporte nativo en browsers  ├── Setup más complejo
└── Perfecto para queries de IA └── Mejor para apps de chat
```

---

## Parte 2: Arquitectura y Diseño (5:00-15:00)

### 5:00 — Visión General de Arquitectura del Sistema

**Arquitectura de Tres Capas:**
```
┌─────────────┐         HTTPS 443        ┌─────────────┐
│   ChatGPT   │◄────────────────────────►│    NGINX    │
│ (Deep Res.) │      SSL/TLS, CORS       │   Reverse   │
└─────────────┘                           │    Proxy    │
                                          └──────┬──────┘
                                                 │ HTTP 8008
                                                 │ Proxy SSE
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

**Responsabilidades de Componentes:**

**1. NGINX (Frontend)**
- Terminación SSL/TLS con certificados Let's Encrypt
- Enrutamiento de requests con scoping basado en path (`/chatgpt/*`)
- Configuración optimizada para SSE (sin buffering, timeouts largos)
- Headers CORS para dominio ChatGPT
- Headers de seguridad (HSTS, X-Frame-Options, etc.)
- Rate limiting y protección DDoS

**2. Servidor MCP (Aplicación)**
- Implementación de servidor OAuth 2.0
- Manejador de protocolo MCP (initialize, tools/list, tools/call)
- Implementaciones de tools (search, fetch)
- Connection pooling de base de datos
- Validación y sanitización de requests
- Logging y pista de auditoría
- Gestión y validación de tokens

**3. SQL Server (Datos)**
- Almacenamiento y recuperación de datos
- Ejecución de queries con application intent de solo lectura
- Row-level security (opcional)
- Audit logging (opcional)

### 6:30 — Estrategia de Enrutamiento Basada en Path

**¿Por Qué Scope `/chatgpt/*`?**
- Aísla tráfico de ChatGPT de otros servicios
- Permite despliegues multi-tenant (diferentes scopes para diferentes clientes)
- Simplifica reglas de firewall y monitoreo
- Permite configuración específica por scope
- Separación clara en logs y métricas

**Configuración de Enrutamiento NGINX:**
```nginx
# Discovery a nivel raíz para sondeos iniciales de ChatGPT
location ~ ^/\.well-known/(oauth-authorization-server|openid-configuration|oauth-protected-resource)$ {
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_set_header X-Environment-Path /chatgpt;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Host $host;
}

# Endpoints de ChatGPT con scope
location ~ ^/chatgpt/(.*)$ {
    # Remover prefijo /chatgpt antes de pasar al servidor
    rewrite ^/chatgpt(/.*)$ $1 break;
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_set_header X-Environment-Path /chatgpt;
    
    # Configuración específica para SSE
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

**El Servidor Usa X-Environment-Path:**
```python
def get_base_url(request: Request) -> str:
    """Construir URL base con environment path del header del proxy."""
    env_path = request.headers.get("x-environment-path", "")
    proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("host", "data.forensic-bot.com")
    
    base = f"{proto}://{host}"
    if env_path:
        base += env_path
    
    return base  # e.g., "https://data.forensic-bot.com/chatgpt"
```

### 8:00 — Arquitectura de Tools para ChatGPT

**Requerimientos de Tools de ChatGPT:**
A diferencia de Claude.ai que usa múltiples tools específicas, ChatGPT Deep Research espera:
1. **Tools de propósito amplio** que puedan manejar múltiples operaciones
2. **Interpretación inteligente de parámetros**
3. **Caching de resultados** para exploración iterativa
4. **Recuperación de registros basada en ID**

**Diseño de Tools:**

#### 1. Tool `search` (Multi-Propósito)
```python
{
    "name": "search",
    "description": """Búsqueda de base de datos multi-propósito que soporta:
    - Listar todas las tablas: query="list tables"
    - Describir schema de tabla: query="describe TableName"
    - Datos de muestra: query="sample TableName limit 10"
    - Ejecutar SQL: query="SELECT * FROM Table WHERE condition"
    """,
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Query de búsqueda o sentencia SQL"
            }
        },
        "required": ["query"]
    }
}
```

**Lógica de Implementación de Search:**
```python
def handle_search(query: str) -> str:
    """
    Enruta query inteligentemente al manejador apropiado:
    1. Verificar "list tables" → llamar list_tables_impl()
    2. Verificar "describe TableName" → llamar describe_table_impl()
    3. Verificar "sample TableName" → llamar get_table_sample_impl()
    4. De otro modo → llamar execute_sql_impl()
    
    Cachea resultados con TTL para la tool fetch.
    """
    query_lower = query.lower().strip()
    
    # Listar tablas
    if query_lower == "list tables":
        return list_tables_impl()
    
    # Describir tabla
    if query_lower.startswith("describe "):
        table_name = query.split("describe ", 1)[1].strip()
        return describe_table_impl(table_name)
    
    # Datos de muestra
    if query_lower.startswith("sample "):
        # Extraer nombre de tabla y límite
        parts = query.split("sample ", 1)[1].strip().split()
        table_name = parts[0]
        limit = 10
        if len(parts) > 2 and parts[1].lower() == "limit":
            limit = int(parts[2])
        return get_table_sample_impl(table_name, limit)
    
    # Default: ejecutar como SQL
    return execute_sql_impl(query)
```

#### 2. Tool `fetch` (Recuperación de Registros)
```python
{
    "name": "fetch",
    "description": """Recupera registros específicos por ID desde resultados de búsqueda cacheados.
    Usa IDs retornados por la tool search.""",
    "inputSchema": {
        "type": "object",
        "properties": {
            "record_id": {
                "type": "string",
                "description": "ID de registro desde resultados de búsqueda"
            }
        },
        "required": ["record_id"]
    }
}
```

**Implementación de Fetch:**
```python
def handle_fetch(record_id: str) -> str:
    """
    Recupera registro desde:
    1. Cache en memoria (si fue buscado recientemente)
    2. Base de datos (si cache miss)
    
    Retorna detalles completos del registro.
    """
    # Verificar cache primero
    if record_id in search_cache:
        cached = search_cache[record_id]
        # Verificar TTL
        if is_cache_valid(cached['cached_at']):
            return json.dumps({
                'id': record_id,
                'data': cached['data'],
                'source': 'cache'
            })
    
    # Cache miss - consultar base de datos
    # Intentar extraer tabla e ID del formato record_id: "TableName_123"
    table, pk_value = parse_record_id(record_id)
    return fetch_from_database(table, pk_value)
```

### 10:00 — Estrategia de Caching de Resultados

**¿Por Qué Caching para ChatGPT?**
- Deep Research realiza queries iterativas
- Recupera registros individuales después de búsqueda inicial
- Reduce carga en base de datos
- Mejora tiempo de respuesta para queries de seguimiento

**Estructura de Cache:**
```python
search_cache: Dict[str, Any] = {}

# Formato de entrada de cache:
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

**Gestión de Cache:**
```python
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

def is_cache_valid(cached_at: str) -> bool:
    """Verificar si entrada de cache aún es válida según TTL."""
    cached_time = datetime.fromisoformat(cached_at)
    age_seconds = (datetime.utcnow() - cached_time).total_seconds()
    return age_seconds < CACHE_TTL_SECONDS

def clean_expired_cache():
    """Remover entradas expiradas del cache."""
    now = datetime.utcnow()
    expired_keys = []
    
    for key, value in search_cache.items():
        cached_time = datetime.fromisoformat(value['cached_at'])
        if (now - cached_time).total_seconds() >= CACHE_TTL_SECONDS:
            expired_keys.append(key)
    
    for key in expired_keys:
        del search_cache[key]
```

### 12:00 — Flujo OAuth Específico para ChatGPT

**Discovery OAuth de ChatGPT:**
```
1. ChatGPT sondea: GET /.well-known/oauth-authorization-server
2. Servidor responde con issuer: https://domain.com/chatgpt
3. ChatGPT sigue endpoints con scope:
   - POST /chatgpt/register → credenciales de cliente
   - GET /chatgpt/authorize → código de autorización
   - POST /chatgpt/token → token bearer
4. ChatGPT usa token para todos los requests /chatgpt/sse
```

**Diferencias Clave vs Claude.ai:**
- ChatGPT requiere discovery tanto a nivel raíz como con scope
- Usa `chatgpt.com` como redirect URI
- Puede reintentar autorización múltiples veces
- Espera URLs de issuer consistentes

### 14:00 — Scoping de Environment Path

**Arquitectura Multi-Scope:**
```
Setup de Producción:
├── /chatgpt/* → mcp-server-chatgpt:8008 (scope ChatGPT)
├── /claude/*  → mcp-server-claude:8009 (scope Claude.ai)
└── /demo/*    → mcp-server-demo:8010 (scope Demo)
```

**Beneficios:**
- Issuers OAuth separados por scope
- Almacenamiento independiente de tokens
- Logging específico por scope
- Usuarios de base de datos diferentes por scope
- Políticas de seguridad aisladas

---

## Parte 3: Implementación de Seguridad (15:00-25:00)

### 15:00 — OAuth 2.0 para ChatGPT

**Flujo OAuth de ChatGPT:**

```
┌──────────┐                               ┌──────────┐
│ ChatGPT  │                               │   MCP    │
│   Deep   │                               │  Server  │
│ Research │                               └────┬─────┘
└────┬─────┘                                    │
     │                                          │
     │  1. Registro de Cliente                  │
     ├─────────────────────────────────────────>│
     │     POST /chatgpt/register               │
     │     {client_name, redirect_uris}         │
     │                                          │
     │<─────────────────────────────────────────┤
     │     200 OK                               │
     │     {client_id, client_secret}           │
     │                                          │
     │  2. Request de Autorización              │
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
     │  3. Intercambio de Token                 │
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
     │  4. Conexión SSE Autenticada             │
     ├─────────────────────────────────────────>│
     │     POST /chatgpt/sse                    │
     │     Authorization: Bearer eyJ...         │
     │                                          │
     │<═════════════════════════════════════════│
     │     Stream SSE (persistente)             │
     │                                          │
```

### 17:00 — Gestión de Tokens

**Almacenamiento de Tokens:**
```python
# Almacén de tokens en memoria (producción debería usar Redis)
valid_tokens: Dict[str, Dict[str, Any]] = {}

# Estructura de token:
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

**Validación de Tokens:**
```python
def _is_token_valid(token: str) -> bool:
    """
    Validar token bearer:
    1. Verificar si token existe en almacén
    2. Verificar tiempo de expiración
    3. Retornar True si válido, False de otro modo
    """
    data = valid_tokens.get(token)
    if not data:
        logger.warning(f"Token no encontrado: {token[:10]}...")
        return False
    
    try:
        expires_at = datetime.fromisoformat(data.get("expires_at"))
    except Exception as e:
        logger.error(f"Formato de expiración inválido: {e}")
        return False
    
    is_valid = datetime.utcnow() < expires_at
    if not is_valid:
        logger.info(f"Token expirado: {token[:10]}...")
    
    return is_valid

def _extract_bearer_token(request: Request) -> Optional[str]:
    """
    Extraer token bearer del header Authorization.
    Formato: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    return auth.split(" ", 1)[1].strip()
```

### 19:00 — Validación de Redirect URI

**Seguridad Crítica: Prevenir Open Redirects**
```python
ALLOWED_REDIRECT_HOSTS = [h.strip().lower() for h in os.getenv(
    "ALLOWED_REDIRECT_HOSTS",
    "chatgpt.com,openai.com,claude.ai,anthropic.com"
).split(",") if h.strip()]

def _is_host_allowed(redirect_uri: Optional[str]) -> bool:
    """
    Validar redirect URI para prevenir intercepción de código de autorización.
    
    Consideraciones de seguridad:
    - Debe ser coincidencia exacta de dominio o subdominio
    - Comparación case-insensitive
    - Previene ataques de open redirect
    """
    if not redirect_uri:
        return False
    
    try:
        parsed = urlparse(redirect_uri)
        host = parsed.hostname or ""
        host = host.lower()
        
        # Verificar coincidencia exacta o subdominio
        return any(
            host == h or host.endswith("." + h)
            for h in ALLOWED_REDIRECT_HOSTS
        )
    except Exception as e:
        logger.error(f"Fallo al parsear redirect URI: {e}")
        return False
```

**Validaciones de Ejemplo:**
```python
# Redirects válidos:
_is_host_allowed("https://chatgpt.com/callback")  # True
_is_host_allowed("https://www.chatgpt.com/callback")  # True
_is_host_allowed("https://openai.com/oauth")  # True

# Redirects inválidos:
_is_host_allowed("https://evil.com/callback")  # False
_is_host_allowed("https://chatgpt.com.evil.com/callback")  # False
_is_host_allowed("https://notchatgpt.com/callback")  # False
```

### 21:00 — Configuración TLS

**Setup SSL de NGINX:**
```nginx
server {
    listen 443 ssl http2;
    server_name data.forensic-bot.com;
    
    # Certificados Let's Encrypt
    ssl_certificate /etc/letsencrypt/live/data.forensic-bot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/data.forensic-bot.com/privkey.pem;
    
    # Configuración TLS moderna
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    
    # Caching de sesión SSL
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/data.forensic-bot.com/chain.pem;
    
    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

### 23:00 — Seguridad de Base de Datos (Modo Read-Only)

**¿Por Qué Read-Only para ChatGPT?**
- Previene modificación accidental de datos
- Reduce superficie de ataque
- Satisface requerimientos de compliance
- Seguro para queries dirigidas por IA

**Implementación:**
```python
READ_ONLY_MODE = os.getenv("READ_ONLY_MODE", "true").lower() == "true"

def get_db_config():
    """Configurar conexión de base de datos con application intent de solo lectura."""
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
    Ejecutar SQL con verificaciones de seguridad de solo lectura.
    """
    if READ_ONLY_MODE:
        # Bloquear operaciones de escritura
        dangerous_keywords = ["insert", "update", "delete", "drop", "alter", 
                             "create", "truncate", "grant", "revoke"]
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in dangerous_keywords):
            return json.dumps({
                "error": "Operaciones de escritura no permitidas en modo read-only",
                "query": query
            })
    
    # Ejecutar query...
```

### 24:00 — IP Whitelisting para ChatGPT

**Rangos IP de ChatGPT (al Octubre 2025):**
```
23.102.140.112/28
13.66.11.96/28
23.98.142.176/28
40.84.180.224/28
76.16.33.0/24
128.252.147.0/24
```

**Restricción IP en NGINX:**
```nginx
# Definir IPs permitidas
geo $chatgpt_allowed {
    default 0;
    23.102.140.112/28 1;
    13.66.11.96/28 1;
    23.98.142.176/28 1;
    40.84.180.224/28 1;
    76.16.33.0/24 1;
    128.252.147.0/24 1;
}

# Aplicar a endpoints de ChatGPT
location ~ ^/chatgpt/ {
    if ($chatgpt_allowed = 0) {
        return 403 "Acceso denegado - IP no está en whitelist";
    }
    # ... resto de configuración
}
```

**Importante:** OpenAI puede actualizar estos rangos IP sin aviso. Monitorea logs para requests legítimos bloqueados.

---

## Parte 4: Desarrollo e Implementación (25:00-40:00)

### 25:00 — Estructura del Proyecto

```
mssql-mcp-server/
├── server_chatgpt.py           # Servidor MCP específico para ChatGPT
├── server_oauth.py             # Lógica compartida OAuth/DB
├── requirements.txt            # Dependencias Python
├── Dockerfile.chatgpt          # Container del servidor ChatGPT
├── docker-compose.yml          # Orquestación desarrollo
├── docker-compose.prod.yml     # Orquestación producción
├── .env                        # Variables de entorno (gitignored)
├── .env.example                # Template de entorno
├── nginx/
│   ├── nginx.conf              # Config principal NGINX
│   └── conf.d/
│       └── default.conf        # Configuración del sitio con enrutamiento ChatGPT
├── certbot/
│   ├── conf/                   # Certificados SSL
│   └── www/                    # Archivos de desafío ACME
├── logs/
│   ├── nginx/                  # Logs de acceso/error NGINX
│   └── mcp/                    # Logs de aplicación
├── docs/
│   ├── chatgpt-connector-setup.md
│   ├── explicacion_chatgpt_es.md  # Este documento
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

### 26:30 — Dependencias Core

**requirements.txt:**
```txt
# Framework ASGI
starlette==0.35.1
uvicorn[standard]==0.27.0

# Base de datos
pyodbc==5.0.1

# Entorno
python-dotenv==1.0.0

# Desarrollo/Testing
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.12.1
mypy==1.7.1
```

### 27:00 — Configuración de Base de Datos

**Gestión de Conexión:**
```python
from typing import Tuple, Dict, Any
import os
import pyodbc
from dotenv import load_dotenv

load_dotenv(".env")

def get_db_config() -> Tuple[Dict[str, str], str]:
    """
    Construir connection string ODBC desde variables de entorno.
    
    Returns:
        Tupla de (dict de config, connection string)
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
    
    # Validar campos requeridos
    if not all([config["user"], config["password"], config["database"]]):
        raise ValueError("Falta configuración requerida de base de datos")
    
    # Construir connection string
    connection_string = (
        f"Driver={{{config['driver']}}};Server={config['server']};"
        f"UID={config['user']};PWD={config['password']};"
        f"Database={config['database']};"
        f"TrustServerCertificate={config['trusted_server_certificate']};"
        f"ApplicationIntent={config['application_intent']};"
    )
    
    return config, connection_string

def test_connection() -> bool:
    """Probar conectividad de base de datos."""
    try:
        _, conn_string = get_db_config()
        conn = pyodbc.connect(conn_string)
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"Conectado a: {version}")
        conn.close()
        return True
    except Exception as e:
        print(f"Conexión falló: {e}")
        return False
```

### 28:30 — Serialización de Datos

**Manejo de Tipos de Datos de SQL Server:**
```python
from decimal import Decimal
from datetime import datetime, date
import base64
import json

def serialize_row_data(data):
    """
    Convertir objetos Row de pyodbc y tipos no-JSON a formato compatible con JSON.
    
    Maneja:
    - Decimal → float
    - datetime → string ISO 8601
    - date → string ISO 8601
    - bytes → string base64
    - None → null
    
    Args:
        data: Valor de fila de base de datos
        
    Returns:
        Valor serializable a JSON
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
        # Fallback: convertir a string
        return str(data)

def serialize_results(rows) -> List[Dict[str, Any]]:
    """
    Serializar conjunto completo de resultados.
    
    Args:
        rows: Lista de objetos Row de pyodbc
        
    Returns:
        Lista de diccionarios con valores serializados
    """
    if not rows:
        return []
    
    # Obtener nombres de columnas de primera fila
    columns = list(rows[0].cursor_description)
    column_names = [col[0] for col in columns]
    
    # Serializar cada fila
    serialized = []
    for row in rows:
        row_dict = {}
        for col_name, value in zip(column_names, row):
            row_dict[col_name] = serialize_row_data(value)
        serialized.append(row_dict)
    
    return serialized
```

### 30:00 — Implementación de Tool Search

**Manejador Completo de Search:**
```python
def handle_search(query: str) -> str:
    """
    Tool de búsqueda multi-propósito para ChatGPT.
    
    Soporta:
    1. Listar tablas: "list tables"
    2. Describir tabla: "describe TableName"
    3. Datos de muestra: "sample TableName limit 10"
    4. Ejecutar SQL: Cualquier sentencia SELECT válida
    
    Los resultados se cachean para la tool fetch.
    
    Args:
        query: Query en lenguaje natural o sentencia SQL
        
    Returns:
        String JSON con resultados
    """
    try:
        query_lower = query.lower().strip()
        
        # Ruta 1: Listar todas las tablas
        if query_lower == "list tables":
            result = list_tables_impl()
            logger.info("Tablas listadas")
            return result
        
        # Ruta 2: Describir schema de tabla
        if query_lower.startswith("describe "):
            table_name = query.split("describe ", 1)[1].strip()
            result = describe_table_impl(table_name)
            logger.info(f"Tabla descrita: {table_name}")
            return result
        
        # Ruta 3: Datos de muestra de tabla
        if query_lower.startswith("sample "):
            # Parsear: "sample TableName limit 10"
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
            logger.info(f"Muestra de {table_name} con límite {limit}")
            
            # Cachear resultados para fetch
            cache_search_results(result, table_name)
            return result
        
        # Ruta 4: Ejecutar query SQL
        result = execute_sql_impl(query)
        logger.info(f"SQL ejecutado: {query[:100]}...")
        
        # Cachear resultados para fetch
        cache_search_results(result, extract_table_from_query(query))
        return result
        
    except Exception as e:
        logger.error(f"Búsqueda falló: {e}")
        return json.dumps({
            "error": f"Búsqueda falló: {str(e)}",
            "query": query
        })

def cache_search_results(result_json: str, table_name: str):
    """
    Cachear resultados de búsqueda para tool fetch.
    
    Genera IDs de registro en formato: TableName_PrimaryKeyValue
    """
    try:
        result = json.loads(result_json)
        if "results" in result:
            for row in result["results"]:
                # Intentar encontrar columna primary key
                record_id = generate_record_id(table_name, row)
                search_cache[record_id] = {
                    'table': table_name,
                    'data': row,
                    'cached_at': datetime.utcnow().isoformat()
                }
    except Exception as e:
        logger.warning(f"Fallo al cachear resultados: {e}")

def generate_record_id(table_name: str, row: Dict) -> str:
    """
    Generar ID único de registro desde nombre de tabla y datos de fila.
    
    Estrategia:
    1. Buscar columnas PK comunes (ID, TableNameID, etc.)
    2. Usar primera columna si no se encuentra PK
    3. Formato: TableName_Value
    """
    # Nombres comunes de columnas primary key
    pk_candidates = [
        f"{table_name}ID",
        "ID",
        f"{table_name}_ID",
        "RecordID",
        "RowID"
    ]
    
    # Intentar encontrar columna PK
    for pk in pk_candidates:
        if pk in row:
            return f"{table_name}_{row[pk]}"
    
    # Fallback: usar primera columna
    if row:
        first_col = list(row.keys())[0]
        return f"{table_name}_{row[first_col]}"
    
    # Último recurso: ID aleatorio
    return f"{table_name}_{uuid.uuid4().hex[:8]}"
```

### 33:00 — Implementación de Tool Fetch

**Manejador Completo de Fetch:**
```python
def handle_fetch(record_id: str) -> str:
    """
    Recuperar registro específico por ID desde cache o base de datos.
    
    Args:
        record_id: Identificador de registro en formato "TableName_PrimaryKeyValue"
        
    Returns:
        String JSON con detalles del registro
    """
    try:
        logger.info(f"Recuperando registro: {record_id}")
        
        # Verificar cache primero
        if record_id in search_cache:
            cached = search_cache[record_id]
            # Verificar TTL
            if is_cache_valid(cached['cached_at']):
                logger.info(f"Cache hit: {record_id}")
                return json.dumps({
                    'id': record_id,
                    'table': cached['table'],
                    'data': cached['data'],
                    'source': 'cache',
                    'cached_at': cached['cached_at']
                }, indent=2)
        
        # Cache miss - consultar base de datos
        logger.info(f"Cache miss: {record_id}, consultando base de datos")
        
        # Parsear record ID: "TableName_123"
        if "_" not in record_id:
            return json.dumps({
                'error': f'Formato de record ID inválido: {record_id}',
                'expected': 'TableName_PrimaryKeyValue'
            })
        
        table_name = record_id.rsplit("_", 1)[0]
        pk_value = record_id.rsplit("_", 1)[1]
        
        # Consultar base de datos
        _, conn_string = get_db_config()
        conn = pyodbc.connect(conn_string)
        cursor = conn.cursor()
        
        # Intentar nombres comunes de columnas PK
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
                        
                        # Actualizar cache
                        search_cache[record_id] = {
                            'table': table_name,
                            'data': serialized,
                            'cached_at': datetime.utcnow().isoformat()
                        }
                        
                        logger.info(f"Recuperado de base de datos: {record_id}")
                        return json.dumps({
                            'id': record_id,
                            'table': table_name,
                            'data': serialized,
                            'source': 'database'
                        }, indent=2)
            except Exception:
                continue
        
        conn.close()
        
        # No encontrado
        return json.dumps({
            'error': f'Registro no encontrado: {record_id}',
            'table': table_name,
            'pk_value': pk_value
        })
        
    except Exception as e:
        logger.error(f"Fetch falló: {e}")
        return json.dumps({
            'error': f'Fetch falló: {str(e)}',
            'record_id': record_id
        })
```

### 36:00 — Manejador de Protocolo MCP

**Implementación de Endpoint SSE:**
```python
async def handle_sse(request: Request) -> Response:
    """
    Endpoint SSE principal para protocolo MCP.
    
    Maneja:
    - HEAD: Verificación de capacidad
    - OPTIONS: Preflight CORS
    - GET: Sondeo de conexión SSE
    - POST: Mensajes JSON-RPC de MCP
    """
    method = request.method
    
    # HEAD: Verificación de capacidad
    if method == "HEAD":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS, HEAD",
                "Access-Control-Allow-Headers": "Authorization, Content-Type"
            }
        )
    
    # OPTIONS: Preflight CORS
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
    
    # GET: Sondeo SSE (respuesta simple)
    if method == "GET":
        return Response(
            content="Endpoint SSE listo\n",
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
    
    # POST: JSON-RPC de MCP
    if method == "POST":
        # Validar autenticación
        token = _extract_bearer_token(request)
        if not token or not _is_token_valid(token):
            return JSONResponse(
                {"error": "No autorizado"},
                status_code=401,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        # Parsear request JSON-RPC
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                {"error": "JSON inválido"},
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        jsonrpc_method = body.get("method", "")
        jsonrpc_id = body.get("id")
        params = body.get("params", {})
        
        # Enrutar a manejador
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
                        "message": f"Método no encontrado: {jsonrpc_method}"
                    }
                },
                headers={"Access-Control-Allow-Origin": "*"}
            )
    
    return Response(status_code=405)

async def handle_initialize(request_id) -> JSONResponse:
    """Respuesta de initialize de MCP."""
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
    """Respuesta de tools/list de MCP."""
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "tools": [
                {
                    "name": "search",
                    "description": "Búsqueda de base de datos multi-propósito que soporta: listar tablas, describir tabla, datos de muestra, ejecutar SQL",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Query de búsqueda o sentencia SQL"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "fetch",
                    "description": "Recuperar registro específico por ID desde resultados de búsqueda cacheados",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "record_id": {
                                "type": "string",
                                "description": "ID de registro desde resultados de búsqueda"
                            }
                        },
                        "required": ["record_id"]
                    }
                }
            ]
        }
    }, headers={"Access-Control-Allow-Origin": "*"})

async def handle_tools_call(request_id, params) -> JSONResponse:
    """Respuesta de tools/call de MCP."""
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
                "message": f"Tool desconocida: {tool_name}"
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

## Parte 5: Despliegue e Infraestructura (40:00-55:00)

### 40:00 — Configuración Docker

**Dockerfile.chatgpt:**
```dockerfile
FROM python:3.11-slim

# Instalar ODBC Driver para SQL Server
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de aplicación
COPY server_chatgpt.py .
COPY server_oauth.py .

# Crear usuario non-root
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

USER mcpuser

# Exponer puerto
EXPOSE 8008

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8008/health', timeout=5)"

# Ejecutar servidor
CMD ["python", "server_chatgpt.py"]
```

**docker-compose.prod.yml (sección ChatGPT):**
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
    command: certonly --webroot --webroot-path=/var/www/certbot --email tu-email@example.com --agree-tos --no-eff-email -d data.forensic-bot.com
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: bridge
```

### 43:00 — Configuración NGINX para ChatGPT

**nginx/conf.d/default.conf (específico para ChatGPT):**
```nginx
# Habilitar merge de slashes para prevenir 404s de double-slash
merge_slashes on;

upstream mcp-server-chatgpt {
    server mcp-server-chatgpt:8008;
    keepalive 32;
}

server {
    listen 80;
    server_name data.forensic-bot.com;
    
    # Desafío ACME para Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirigir a HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name data.forensic-bot.com;
    
    # Configuración SSL
    ssl_certificate /etc/letsencrypt/live/data.forensic-bot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/data.forensic-bot.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    
    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    
    # Discovery OAuth a nivel raíz (para sondeos iniciales de ChatGPT)
    location ~ ^/\.well-known/(oauth-authorization-server|openid-configuration|oauth-protected-resource)$ {
        proxy_pass http://mcp-server-chatgpt;
        proxy_set_header X-Environment-Path /chatgpt;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # CORS para ChatGPT
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
    }
    
    # Endpoints de ChatGPT con scope
    location ~ ^/chatgpt/(.*)$ {
        # Remover prefijo /chatgpt
        rewrite ^/chatgpt(/.*)$ $1 break;
        
        proxy_pass http://mcp-server-chatgpt;
        proxy_set_header X-Environment-Path /chatgpt;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Configuración específica para SSE
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 3600s;
        
        # Mantener conexión viva para SSE
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        
        # CORS para ChatGPT
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

### 46:00 — Configuración de Entorno

**Template .env:**
```bash
# Configuración de Base de Datos
MSSQL_HOST=tu-sql-server.database.windows.net
MSSQL_USER=usuario_readonly_chatgpt
MSSQL_PASSWORD=tu_password_seguro_aqui
MSSQL_DATABASE=nombre_tu_base_datos
MSSQL_DRIVER=ODBC Driver 18 for SQL Server

# Configuración de Seguridad
TrustServerCertificate=yes
Trusted_Connection=no
READ_ONLY_MODE=true

# Configuración OAuth
ALLOWED_REDIRECT_HOSTS=chatgpt.com,openai.com
# Nota: Nunca habilitar estos en producción
ALLOW_UNAUTH_METHODS=false
ALLOW_UNAUTH_TOOLS_CALL=false

# Configuración Específica de ChatGPT
MAX_SEARCH_RESULTS=50
CACHE_TTL_SECONDS=3600

# Environment Path (opcional, establecido por NGINX)
ENVIRONMENT_PATH=/chatgpt

# Logging
LOG_LEVEL=INFO
```

### 48:00 — Setup de Certificado SSL

**setup-letsencrypt.sh:**
```bash
#!/bin/bash
set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # Sin Color

echo -e "${GREEN}Setup SSL de Let's Encrypt para Servidor MCP ChatGPT${NC}"

# Solicitar dominio
read -p "Ingresa tu dominio (ej., data.forensic-bot.com): " DOMAIN
read -p "Ingresa tu email: " EMAIL
read -p "¿Usar certificados de producción (0) o staging (1)? " STAGING

# Establecer rutas
DATA_PATH="./certbot"
mkdir -p "$DATA_PATH/conf"
mkdir -p "$DATA_PATH/www"

# Descargar parámetros TLS recomendados
if [ ! -e "$DATA_PATH/conf/ssl-dhparams.pem" ]; then
    echo -e "${YELLOW}Descargando parámetros DH...${NC}"
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$DATA_PATH/conf/ssl-dhparams.pem"
fi

# Actualizar dominio en docker-compose y config nginx
echo -e "${YELLOW}Actualizando archivos de configuración...${NC}"
sed -i.bak "s/data.forensic-bot.com/$DOMAIN/g" docker-compose.prod.yml
sed -i.bak "s/data.forensic-bot.com/$DOMAIN/g" nginx/conf.d/default.conf

# Iniciar nginx solo con HTTP (para desafío ACME)
echo -e "${YELLOW}Iniciando nginx para desafío ACME...${NC}"
docker-compose -f docker-compose.prod.yml up -d nginx

# Esperar nginx
sleep 5

# Solicitar certificado
if [ "$STAGING" == "1" ]; then
    STAGING_ARG="--staging"
    echo -e "${YELLOW}Usando entorno STAGING de Let's Encrypt${NC}"
else
    STAGING_ARG=""
    echo -e "${YELLOW}Usando entorno PRODUCCIÓN de Let's Encrypt${NC}"
fi

echo -e "${YELLOW}Solicitando certificado de Let's Encrypt...${NC}"
docker-compose -f docker-compose.prod.yml run --rm certbot \
    certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    $STAGING_ARG \
    -d "$DOMAIN"

# Verificar certificado
if [ ! -f "$DATA_PATH/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo -e "${RED}¡Fallo al obtener certificado!${NC}"
    exit 1
fi

# Recargar nginx con SSL
echo -e "${YELLOW}Recargando nginx con SSL...${NC}"
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Iniciar todos los servicios
echo -e "${YELLOW}Iniciando todos los servicios...${NC}"
docker-compose -f docker-compose.prod.yml up -d

echo -e "${GREEN}¡Setup Completo!${NC}"
echo -e "Tu servidor MCP ChatGPT ahora está disponible en: ${GREEN}https://$DOMAIN${NC}"
echo -e "Endpoint de discovery: ${GREEN}https://$DOMAIN/.well-known/oauth-authorization-server${NC}"
```

### 50:00 — Pasos de Despliegue

**Proceso de Despliegue Completo:**
```bash
# 1. Clonar repositorio
git clone https://github.com/tu-org/mssql-mcp-server.git
cd mssql-mcp-server

# 2. Configurar entorno
cp .env.example .env
nano .env  # Editar con tus credenciales de base de datos

# 3. Ejecutar setup SSL
chmod +x setup-letsencrypt.sh
./setup-letsencrypt.sh

# 4. Construir e iniciar servicios
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 5. Verificar despliegue
curl https://tu-dominio.com/health
curl https://tu-dominio.com/.well-known/oauth-authorization-server

# 6. Revisar logs
docker-compose -f docker-compose.prod.yml logs -f mcp-server-chatgpt
```

### 52:00 — Monitoreo y Health Checks

**Endpoint de Health Check:**
```python
@app.route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """
    Health check comprensivo para sistemas de monitoreo.
    
    Verifica:
    - Uptime del servidor
    - Conectividad de base de datos
    - Funcionalidad OAuth
    - Estado del cache
    
    Returns:
        JSON con estado de salud
    """
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Verificar base de datos
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
    
    # Verificar OAuth
    status["checks"]["oauth"] = {
        "active_tokens": len(valid_tokens),
        "auth_codes": len(auth_codes)
    }
    
    # Verificar cache
    status["checks"]["cache"] = {
        "entries": len(search_cache),
        "ttl_seconds": CACHE_TTL_SECONDS
    }
    
    return JSONResponse(status)
```

**Script de Monitoreo:**
```bash
#!/bin/bash
# monitor-chatgpt.sh

LOG_FILE="/var/log/mcp/chatgpt-server.log"

echo "=== Monitor de Salud Servidor MCP ChatGPT ==="
echo "Fecha: $(date)"
echo ""

# Health check
echo "=== Estado de Salud ==="
curl -s https://data.forensic-bot.com/chatgpt/health | jq '.'
echo ""

# Análisis de errores
echo "=== Resumen de Errores (Últimas 24h) ==="
grep "ERROR" $LOG_FILE | grep "$(date -d '24 hours ago' '+%Y-%m-%d')" | wc -l | xargs echo "Total de errores:"
grep "ERROR" $LOG_FILE | tail -5
echo ""

# Actividad OAuth
echo "=== Actividad OAuth ==="
grep "oauth" $LOG_FILE | grep "register" | wc -l | xargs echo "Registros de cliente:"
grep "oauth" $LOG_FILE | grep "token" | wc -l | xargs echo "Intercambios de token:"
echo ""

# Uso de tools
echo "=== Estadísticas de Uso de Tools ==="
grep "tool_execution" $LOG_FILE | \
    jq -r '.tool' 2>/dev/null | \
    sort | uniq -c | sort -rn
echo ""

# Estadísticas de cache
echo "=== Rendimiento de Cache ==="
grep "Cache" $LOG_FILE | tail -10
echo ""

# Queries recientes
echo "=== Queries de Búsqueda Recientes (Últimos 10) ==="
grep "handle_search" $LOG_FILE | tail -10 | \
    grep -oP '(?<=query: ).*' | head -10
```

---

## Parte 6: Testing y Validación (55:00-65:00)

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
    """Probar funciones helper de OAuth."""
    
    def test_extract_bearer_token_valid(self):
        """Probar extracción de token bearer válido."""
        request = Mock()
        request.headers.get.return_value = "Bearer abc123token"
        
        token = _extract_bearer_token(request)
        assert token == "abc123token"
    
    def test_extract_bearer_token_invalid(self):
        """Probar headers de autorización inválidos."""
        request = Mock()
        
        # Sin prefijo bearer
        request.headers.get.return_value = "abc123token"
        assert _extract_bearer_token(request) is None
        
        # Header vacío
        request.headers.get.return_value = ""
        assert _extract_bearer_token(request) is None
        
        # Header None
        request.headers.get.return_value = None
        assert _extract_bearer_token(request) is None
    
    def test_is_host_allowed_valid(self):
        """Probar URIs de redirect válidas."""
        assert _is_host_allowed("https://chatgpt.com/callback") == True
        assert _is_host_allowed("https://www.chatgpt.com/callback") == True
        assert _is_host_allowed("https://openai.com/oauth") == True
    
    def test_is_host_allowed_invalid(self):
        """Probar URIs de redirect inválidas."""
        assert _is_host_allowed("https://evil.com/callback") == False
        assert _is_host_allowed("https://chatgpt.com.evil.com/callback") == False
        assert _is_host_allowed("") == False
        assert _is_host_allowed(None) == False
    
    def test_is_token_valid(self):
        """Probar validación de token con expiración."""
        # Setup token válido
        token = "test_token_123"
        valid_tokens[token] = {
            "client_id": "test_client",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        assert _is_token_valid(token) == True
        
        # Setup token expirado
        expired_token = "expired_token_456"
        valid_tokens[expired_token] = {
            "client_id": "test_client",
            "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
        }
        
        assert _is_token_valid(expired_token) == False
        
        # Token no existente
        assert _is_token_valid("nonexistent") == False

class TestDataSerialization:
    """Probar serialización de datos para tipos de SQL Server."""
    
    def test_serialize_decimal(self):
        """Probar conversión de Decimal a float."""
        result = serialize_row_data(Decimal("123.45"))
        assert result == 123.45
        assert isinstance(result, float)
    
    def test_serialize_datetime(self):
        """Probar datetime a string ISO."""
        dt = datetime(2025, 10, 1, 12, 30, 45)
        result = serialize_row_data(dt)
        assert result == "2025-10-01T12:30:45"
    
    def test_serialize_bytes(self):
        """Probar bytes a string base64."""
        data = b"Hello World"
        result = serialize_row_data(data)
        assert result == "SGVsbG8gV29ybGQ="
    
    def test_serialize_none(self):
        """Probar manejo de None."""
        assert serialize_row_data(None) is None
    
    def test_serialize_primitives(self):
        """Probar que tipos primitivos pasan sin cambios."""
        assert serialize_row_data(123) == 123
        assert serialize_row_data(123.45) == 123.45
        assert serialize_row_data("test") == "test"
        assert serialize_row_data(True) == True

@pytest.mark.asyncio
class TestEndpoints:
    """Probar endpoints HTTP."""
    
    async def test_health_endpoint(self, client):
        """Probar endpoint de health check."""
        response = await client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "checks" in data
        assert "database" in data["checks"]
    
    async def test_oauth_discovery(self, client):
        """Probar endpoint de OAuth discovery."""
        response = await client.get("/.well-known/oauth-authorization-server")
        assert response.status_code == 200
        
        data = response.json()
        assert "issuer" in data
        assert "authorization_endpoint" in data
        assert "token_endpoint" in data
    
    async def test_sse_unauthorized(self, client):
        """Probar endpoint SSE sin auth."""
        response = await client.post("/sse")
        assert response.status_code == 401
    
    async def test_sse_with_valid_token(self, client):
        """Probar endpoint SSE con token válido."""
        # Crear token válido
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
    """Crear cliente de test."""
    from starlette.testclient import TestClient
    from server_chatgpt import app
    return TestClient(app)
```

### 58:00 — Testing de Integración

**Testing Manual con cURL:**
```bash
# Probar OAuth Discovery
curl -v https://data.forensic-bot.com/.well-known/oauth-authorization-server

# Esperado: 200 OK con metadata OAuth

# Probar discovery con scope
curl -v https://data.forensic-bot.com/chatgpt/.well-known/oauth-authorization-server

# Probar Registro de Cliente
curl -X POST https://data.forensic-bot.com/chatgpt/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Cliente de Test",
    "redirect_uris": ["https://chatgpt.com/callback"]
  }'

# Guardar client_id y client_secret de respuesta
CLIENT_ID="client_abc123"
CLIENT_SECRET="secret_xyz789"

# Probar Autorización
curl -v "https://data.forensic-bot.com/chatgpt/authorize?\
client_id=$CLIENT_ID&\
redirect_uri=https://chatgpt.com/callback&\
response_type=code&\
state=random123"

# Esperado: 302 redirect con código de autorización
AUTH_CODE="code_from_redirect"

# Probar Intercambio de Token
curl -X POST https://data.forensic-bot.com/chatgpt/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=$AUTH_CODE" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "redirect_uri=https://chatgpt.com/callback"

# Guardar access_token de respuesta
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Probar Endpoints MCP
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

# Listar tools
curl -X POST https://data.forensic-bot.com/chatgpt/sse \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 2,
    "params": {}
  }'

# Llamar tool search
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

### 61:00 — Testing de Performance

**Script de Load Testing:**
```python
#!/usr/bin/env python3
"""
Load test para servidor MCP ChatGPT.
"""
import asyncio
import aiohttp
import time
from statistics import mean, median

BASE_URL = "https://data.forensic-bot.com/chatgpt"
CONCURRENT_REQUESTS = 10
TOTAL_REQUESTS = 100

async def get_token(session):
    """Obtener token OAuth."""
    # Registrar cliente
    async with session.post(
        f"{BASE_URL}/register",
        json={"client_name": "Load Test", "redirect_uris": ["https://test.com"]}
    ) as resp:
        data = await resp.json()
        client_id = data["client_id"]
        client_secret = data["client_secret"]
    
    # Obtener código de auth
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
    
    # Intercambiar por token
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
    """Ejecutar query de búsqueda y medir tiempo."""
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
    """Ejecutar load test."""
    async with aiohttp.ClientSession() as session:
        # Obtener token
        print("Obteniendo token OAuth...")
        token = await get_token(session)
        print("Token obtenido")
        
        # Preparar queries
        queries = [
            "list tables",
            "describe Customers",
            "sample Orders limit 10",
            "SELECT TOP 5 * FROM Products"
        ]
        
        # Ejecutar requests concurrentes
        tasks = []
        results = []
        for i in range(TOTAL_REQUESTS):
            query = queries[i % len(queries)]
            tasks.append(search_query(session, token, query))
            
            # Limitar concurrencia
            if len(tasks) >= CONCURRENT_REQUESTS:
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
                tasks = []
        
        # Ejecutar tareas restantes
        if tasks:
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        
        # Agregar resultados
        durations = [r[0] for r in results]
        statuses = [r[1] for r in results]
        
        print(f"\n=== Resultados de Load Test ===")
        print(f"Total de requests: {TOTAL_REQUESTS}")
        print(f"Concurrentes: {CONCURRENT_REQUESTS}")
        print(f"Tasa de éxito: {statuses.count(200)/len(statuses)*100:.1f}%")
        print(f"Tiempo promedio de respuesta: {mean(durations):.3f}s")
        print(f"Tiempo mediano de respuesta: {median(durations):.3f}s")
        print(f"Tiempo mínimo de respuesta: {min(durations):.3f}s")
        print(f"Tiempo máximo de respuesta: {max(durations):.3f}s")

if __name__ == "__main__":
    asyncio.run(load_test())
```

---

## Parte 7: Operaciones en Producción (65:00-80:00)

### 65:00 — Configuración de Logging

**Setup de Logging Mejorado:**
```python
import logging
import json
from datetime import datetime

# Configurar logging estructurado
class JSONFormatter(logging.Formatter):
    """Formatear logs como JSON para parseo más fácil."""
    
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
        
        # Agregar info de excepción si está presente
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Agregar campos personalizados
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

# Ejemplos de uso
def log_oauth_event(event_type, client_id, details=None):
    """Registrar eventos OAuth con contexto."""
    extra = {'user_id': client_id}
    logger.info(f"Evento OAuth: {event_type}", extra=extra)
    if details:
        logger.debug(f"Detalles: {json.dumps(details)}", extra=extra)

def log_tool_execution(tool_name, query, duration_ms, success=True):
    """Registrar métricas de ejecución de tools."""
    logger.info(
        f"Ejecución de tool: {tool_name}",
        extra={
            'tool': tool_name,
            'query': query[:100],
            'duration_ms': duration_ms,
            'success': success
        }
    )

def log_error(error_msg, exception=None):
    """Registrar errores con contexto completo."""
    logger.error(error_msg, exc_info=exception)
```

### 67:00 — Backup y Recuperación

**Script de Backup de Base de Datos:**
```bash
#!/bin/bash
# backup-database.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mssql"
DATABASE="tu_base_datos"
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR

# Crear backup usando backup nativo de SQL Server
docker-compose exec -T mcp-server-chatgpt python << EOF
import pyodbc
from server_chatgpt import get_db_config

_, conn_string = get_db_config()
# Modificar para backup: remover intent de solo lectura
conn_string = conn_string.replace("ApplicationIntent=ReadOnly", "ApplicationIntent=ReadWrite")

conn = pyodbc.connect(conn_string)
cursor = conn.cursor()

backup_path = f"/var/opt/mssql/backup/${DATABASE}_${TIMESTAMP}.bak"
cursor.execute(f"BACKUP DATABASE [{DATABASE}] TO DISK = '{backup_path}' WITH COMPRESSION, INIT")
conn.commit()
print(f"Backup creado: {backup_path}")
EOF

# Copiar backup desde container
docker cp $(docker-compose ps -q mcp-server-chatgpt):/var/opt/mssql/backup/${DATABASE}_${TIMESTAMP}.bak \
    ${BACKUP_DIR}/

# Comprimir backup
gzip ${BACKUP_DIR}/${DATABASE}_${TIMESTAMP}.bak

# Subir a almacenamiento en la nube (opcional)
# aws s3 cp ${BACKUP_DIR}/${DATABASE}_${TIMESTAMP}.bak.gz s3://tu-bucket/backups/

# Limpiar backups antiguos
find $BACKUP_DIR -name "*.bak.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completo: ${DATABASE}_${TIMESTAMP}.bak.gz"
```

### 69:00 — Gestión de Cache

**Limpieza Automática de Cache:**
```python
import asyncio
from datetime import datetime, timedelta

async def cache_cleanup_task():
    """
    Tarea en background para limpiar entradas de cache expiradas.
    Se ejecuta cada 5 minutos.
    """
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutos
            
            now = datetime.utcnow()
            expired_keys = []
            
            for key, value in search_cache.items():
                cached_time = datetime.fromisoformat(value['cached_at'])
                age_seconds = (now - cached_time).total_seconds()
                
                if age_seconds >= CACHE_TTL_SECONDS:
                    expired_keys.append(key)
            
            # Remover entradas expiradas
            for key in expired_keys:
                del search_cache[key]
            
            if expired_keys:
                logger.info(f"Limpiadas {len(expired_keys)} entradas de cache expiradas")
                
        except Exception as e:
            logger.error(f"Limpieza de cache falló: {e}")

# Iniciar tarea de limpieza al arrancar servidor
@app.on_event("startup")
async def startup_event():
    """Inicializar tareas en background."""
    asyncio.create_task(cache_cleanup_task())
    logger.info("Tarea de limpieza de cache iniciada")
```

### 72:00 — Troubleshooting de Problemas Comunes

**Problema 1: 404 Not Found en Discovery**
```bash
# Diagnóstico
curl -v https://data.forensic-bot.com/.well-known/oauth-authorization-server

# Verificar configuración NGINX
docker-compose exec nginx nginx -t
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf | grep "well-known"

# Verificar header X-Environment-Path
docker-compose logs nginx | grep "X-Environment-Path"

# Solución: Asegurar que NGINX hace proxy de discovery a nivel raíz al servidor
```

**Problema 2: 401 Unauthorized en SSE**
```bash
# Verificar validez de token
docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import valid_tokens
from datetime import datetime
print('Tokens activos:', len(valid_tokens))
for token, data in list(valid_tokens.items())[:5]:
    expires = datetime.fromisoformat(data['expires_at'])
    print(f'{token[:10]}... expira en {expires}')
"

# Re-autenticar
# Completar nuevo flujo OAuth para obtener token fresco
```

**Problema 3: Fallos de Conexión de Base de Datos**
```bash
# Probar conexión
docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import get_db_config
import pyodbc

try:
    _, conn_string = get_db_config()
    conn = pyodbc.connect(conn_string, timeout=10)
    cursor = conn.cursor()
    cursor.execute('SELECT @@VERSION')
    print('Conexión exitosa:', cursor.fetchone()[0][:50])
except Exception as e:
    print('Conexión falló:', e)
"

# Verificar reglas de firewall
# Verificar que servidor de base de datos permite conexiones desde red Docker

# Verificar credenciales
docker-compose exec mcp-server-chatgpt env | grep MSSQL
```

### 75:00 — Respuesta a Incidentes de Seguridad

**Checklist de Seguridad:**
```bash
#!/bin/bash
# security-audit.sh

echo "=== Auditoría de Seguridad ==="
echo ""

# Verificar intentos de acceso no autorizado
echo "1. Intentos de autenticación fallidos:"
docker-compose logs mcp-server-chatgpt | grep "401" | wc -l

# Verificar patrones de query inusuales
echo "2. Intentos potenciales de SQL injection:"
docker-compose logs mcp-server-chatgpt | grep -i "union\|or 1=1\|drop table"

# Verificar tokens activos
echo "3. Tokens OAuth activos:"
docker-compose exec mcp-server-chatgpt python -c "
from server_chatgpt import valid_tokens
print(f'Total: {len(valid_tokens)}')
"

# Verificar intentos de operaciones de escritura
echo "4. Operaciones de escritura bloqueadas:"
docker-compose logs mcp-server-chatgpt | grep "Write operations not allowed"

# Revisar conexiones recientes
echo "5. Conexiones recientes:"
docker-compose logs nginx | grep -E "POST /chatgpt/sse" | tail -20

# Verificar estado de certificado SSL
echo "6. Expiración de certificado SSL:"
docker-compose exec certbot certbot certificates

echo ""
echo "Auditoría completa"
```

### 78:00 — Métricas y Alertas

**Endpoint de Métricas Prometheus:**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response

# Definir métricas
oauth_registrations = Counter('oauth_registrations_total', 'Total de registros de clientes OAuth')
oauth_token_exchanges = Counter('oauth_token_exchanges_total', 'Total de intercambios de tokens OAuth')
tool_executions = Counter('tool_executions_total', 'Total de ejecuciones de tools', ['tool_name', 'status'])
tool_duration = Histogram('tool_execution_seconds', 'Duración de ejecución de tool', ['tool_name'])
active_tokens = Gauge('active_tokens', 'Número de tokens OAuth activos')
cache_size = Gauge('search_cache_size', 'Número de entradas en cache de búsqueda')

# Actualizar métricas en manejadores
def handle_register():
    oauth_registrations.inc()
    # ... resto del manejador

def handle_token():
    oauth_token_exchanges.inc()
    # ... resto del manejador

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

# Endpoint de métricas
@app.route("/metrics", methods=["GET"])
async def metrics(request: Request):
    """Endpoint de métricas Prometheus."""
    # Actualizar gauges
    active_tokens.set(len(valid_tokens))
    cache_size.set(len(search_cache))
    
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

---

## Parte 8: Temas Avanzados y Mejores Prácticas (80:00-90:00)

### 80:00 — Arquitectura Multi-Tenant

**Aislamiento Basado en Scope:**
```nginx
# En nginx/conf.d/default.conf

# Scope ChatGPT
location ~ ^/chatgpt/(.*)$ {
    rewrite ^/chatgpt(/.*)$ $1 break;
    proxy_pass http://mcp-server-chatgpt:8008;
    proxy_set_header X-Environment-Path /chatgpt;
}

# Scope Claude
location ~ ^/claude/(.*)$ {
    rewrite ^/claude(/.*)$ $1 break;
    proxy_pass http://mcp-server-claude:8009;
    proxy_set_header X-Environment-Path /claude;
}

# Scope Cliente A
location ~ ^/customer-a/(.*)$ {
    rewrite ^/customer-a(/.*)$ $1 break;
    proxy_pass http://mcp-server-customer-a:8010;
    proxy_set_header X-Environment-Path /customer-a;
}
```

### 82:00 — Rate Limiting

**Rate Limiting en NGINX:**
```nginx
# En bloque http de nginx.conf

# Definir zonas de rate limit
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=oauth:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=tools:10m rate=20r/s;

server {
    # Aplicar a endpoints OAuth
    location ~ ^/chatgpt/(register|authorize|token)$ {
        limit_req zone=oauth burst=10 nodelay;
        # ... resto de config
    }
    
    # Aplicar a endpoint SSE
    location = /chatgpt/sse {
        limit_req zone=tools burst=50 nodelay;
        # ... resto de config
    }
}
```

### 84:00 — Optimización Avanzada de Queries

**Paginación de Resultados de Query:**
```python
def handle_search_with_pagination(query: str, page: int = 1, page_size: int = 50) -> str:
    """
    Ejecutar búsqueda con soporte de paginación.
    
    Args:
        query: Query SQL o lenguaje natural
        page: Número de página (1-indexed)
        page_size: Resultados por página
        
    Returns:
        JSON con resultados y metadata de paginación
    """
    # Calcular offset
    offset = (page - 1) * page_size
    
    # Modificar query para paginación
    if "SELECT" in query.upper():
        # Agregar OFFSET-FETCH para SQL Server
        if "ORDER BY" not in query.upper():
            query += " ORDER BY (SELECT NULL)"  # Requerido para OFFSET
        
        query += f" OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY"
    
    # Ejecutar query
    result = execute_sql_impl(query)
    result_data = json.loads(result)
    
    # Agregar metadata de paginación
    result_data["pagination"] = {
        "page": page,
        "page_size": page_size,
        "has_more": len(result_data.get("results", [])) == page_size
    }
    
    return json.dumps(result_data)
```

### 86:00 — Mejores Prácticas de Observabilidad

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

# Usar en manejadores
async def handle_tools_call_with_tracing(request_id, params):
    """Manejar tools/call con distributed tracing."""
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

### 88:00 — Recuperación ante Desastres

**Estrategia de Backup:**
```markdown
## Estrategia de Backup

### Backups Diarios
- Base de datos: Backup completo a las 02:00 UTC
- Configuración: archivos /etc, .env
- Logs: Últimos 7 días
- Retención: 30 días

### Backups Semanales
- Snapshot completo del sistema
- Backups de certificados
- Retención: 90 días

### Backups Mensuales
- Archivo a almacenamiento en la nube (S3/Azure Blob)
- Retención: 1 año

### Recovery Time Objectives (RTO)
- Base de datos: 1 hora
- Aplicación: 30 minutos
- Certificados SSL: 2 horas

### Recovery Point Objectives (RPO)
- Base de datos: 24 horas
- Configuración: 1 hora
```

### 90:00 — Conclusión y Recursos

**Puntos Clave:**
1. **Seguridad Primero**: OAuth 2.0, TLS, modo read-only, IP whitelisting
2. **Integración ChatGPT**: Tools específicas (search/fetch) con caching
3. **Escalabilidad**: Despliegue containerizado, rate limiting, caching
4. **Operaciones**: Monitoreo, logging, backup, respuesta a incidentes
5. **Mejores Prácticas**: Testing, documentación, observabilidad

**Recursos Adicionales:**
- Especificación MCP: https://spec.modelcontextprotocol.io
- OAuth 2.0 RFC 6749: https://tools.ietf.org/html/rfc6749
- Conectores ChatGPT: https://platform.openai.com/docs/actions
- ODBC SQL Server: https://learn.microsoft.com/es-es/sql/connect/odbc/
- Mejores Prácticas Docker: https://docs.docker.com/develop/dev-best-practices/
- Configuración NGINX SSE: https://nginx.org/en/docs/http/ngx_http_proxy_module.html

**Próximos Pasos:**
1. Revisar base de conocimiento del proyecto para código completo
2. Configurar .env con tus credenciales de base de datos
3. Ejecutar setup-letsencrypt.sh para SSL
4. Desplegar usando docker-compose.prod.yml
5. Agregar conector en configuración de ChatGPT
6. Monitorear logs y métricas
7. Iterar y mejorar basado en uso

---

**Versión del Documento**: 1.0.0  
**Última Actualización**: Octubre 2025  
**Compatibilidad**: ChatGPT (Deep Research), MCP 2025-06-18  
**Servidor**: server_chatgpt.py  
**Probado Con**: Docker 20.10+, NGINX 1.24+, SQL Server 2019+, Python 3.11+
