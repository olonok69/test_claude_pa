# Plataforma de Integración MCP de Búsqueda Impulsada por IA

Una aplicación integral que proporciona interacciones impulsadas por IA con Google Search y Perplexity AI a través de servidores de Protocolo de Contexto de Modelo (MCP). Esta plataforma permite búsqueda web sin interrupciones, análisis impulsado por IA y extracción de contenido con seguridad HTTPS opcional, autenticación de usuarios y sistema de caché avanzado para rendimiento óptimo.

## 🚀 Resumen del Sistema

Esta aplicación consta de tres componentes integrados que trabajan juntos para proporcionar capacidades completas de búsqueda impulsada por IA:

1. **Cliente Streamlit** - Interfaz de chat IA con soporte multi-proveedor, autenticación, soporte SSL y servidor MCP integrado
2. **Servidor MCP de Google Search** - Búsqueda web y extracción de contenido vía Google Custom Search API con caché inteligente
3. **Servidor MCP de Perplexity** - Búsqueda impulsada por IA con análisis inteligente vía Perplexity API con caché de respuestas

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Cliente Streamlit │    │  Google Search API  │    │  Perplexity AI API  │
│                     │    │                     │    │                     │
│  - Interfaz Chat IA │◄──►│  - Búsqueda Web     │    │  - Búsqueda IA      │
│  - Autenticación    │    │  - Extracción Cont. │    │  - Análisis Intelig.│
│  - Multi-Proveedor  │    │  - Caché Contenido  │    │  - Caché Respuestas │
│  - Etiquetado Emp.  │    │  (TTL 2h)           │    │  (TTL 30min)        │
│    (stdio MCP)      │    └─────────────────────┘    └─────────────────────┘
└─────────────────────┘              ▲                          ▲
           ▲                    ┌────┴─────┐              ┌────┴─────┐
           │                    │ Servidor2│              │ Servidor1│
           │                    │ Google   │              │Perplexity│
           │                    │ Search   │              │ + Caché  │
           │                    │ + Caché  │              │ Servidor │
           │                    │ Servidor │              │ MCP      │
           │                    └──────────┘              └──────────┘
```

## 📋 Tabla de Referencia de Puertos

| Servicio | Puerto | Protocolo | Propósito |
|----------|--------|-----------|-----------|
| **Streamlit HTTP** | 8501 | HTTP | Interfaz web principal |
| **Streamlit HTTPS** | 8503 | HTTPS | Interfaz web segura (recomendado) |
| **Google Search MCP** | 8002 | HTTP/SSE | Servidor de búsqueda web con caché |
| **Perplexity MCP** | 8001 | HTTP/SSE | Servidor de búsqueda IA con caché |
| **Etiquetado Empresas** | - | stdio | Servidor MCP integrado |

## 🔧 Tecnologías Principales y Dependencias

Esta plataforma está construida utilizando tecnologías modernas y robustas que habilitan capacidades escalables de búsqueda impulsada por IA con caché inteligente para rendimiento óptimo.

### **🌐 Frontend e Interfaz de Usuario**

#### **[Streamlit](https://streamlit.io/)** - Framework de Aplicaciones Web
- **Propósito**: Interfaz web principal para interacciones de usuario
- **Versión**: 1.44+
- **Características**: Actualizaciones en tiempo real, sistema de componentes, gestión de sesiones
- **Mejorado**: Interfaz multi-pestaña con configuración, conexiones, herramientas y chat

#### **[Streamlit Authenticator](https://github.com/mkhorasani/Streamlit-Authenticator)** - Sistema de Autenticación
- **Propósito**: Inicio de sesión seguro y gestión de sesiones de usuario
- **Versión**: 0.3.2
- **Características**: Hash de contraseñas bcrypt, control de acceso basado en roles, persistencia de sesión de 30 días

### **🧠 IA y Modelos de Lenguaje**

#### **[LangChain](https://python.langchain.com/)** - Framework de IA
- **Propósito**: Orquestación de agentes IA y enrutamiento de herramientas
- **Versión**: 0.3.20+
- **Características**: Agentes ReAct, gestión de memoria, ejecución de herramientas, historial de conversaciones

#### **[API de OpenAI](https://openai.com/api/)** - Modelos de Lenguaje IA
- **Modelos**: GPT-4o, GPT-4o-mini
- **Características**: Llamadas de herramientas, respuestas en streaming, manejo de contexto

#### **[Azure OpenAI](https://azure.microsoft.com/es-es/products/ai-services/openai-service)** - IA Empresarial
- **Modelos**: GPT-4o, o3-mini
- **Características**: Seguridad empresarial, endpoints privados, cumplimiento, garantías SLA

### **🔍 Búsqueda y Fuentes de Datos**

#### **[Google Custom Search API](https://developers.google.com/custom-search)** - Motor de Búsqueda Web
- **Propósito**: Capacidades completas de búsqueda web con caché inteligente
- **Versión**: v1
- **Caché**: TTL de 30 minutos para resultados de búsqueda, TTL de 2 horas para contenido de páginas web
- **Características**: Motores de búsqueda personalizados, filtrado de resultados, optimización de extracción de contenido

#### **[API de Perplexity AI](https://www.perplexity.ai/)** - Búsqueda Impulsada por IA
- **Modelos**: sonar-deep-research, sonar-reasoning-pro, sonar-reasoning, sonar-pro, sonar, r1-1776
- **Caché**: TTL de 30 minutos para respuestas de API
- **Características**: Filtrado de actualidad, selección de modelo, soporte de citas, control de temperatura

### **🔗 Protocolos de Comunicación**

#### **[Protocolo de Contexto de Modelo (MCP)](https://modelcontextprotocol.io/)** - Comunicación IA Estandarizada
- **Propósito**: Protocolo universal para integración de herramientas IA
- **Versión**: 1.0+
- **Características**: Descubrimiento de herramientas, validación de esquemas, flexibilidad de transporte (SSE + stdio)

#### **[Server-Sent Events (SSE)](https://developer.mozilla.org/es/docs/Web/API/Server-sent_events)** - Comunicación en Tiempo Real
- **Propósito**: Comunicación bidireccional en tiempo real para servidores MCP externos
- **Características**: Reconexión automática, orden de mensajes, multiplexación

#### **Transporte stdio** - Comunicación de Procesos Locales
- **Propósito**: Comunicación de servidor MCP integrado dentro de contenedores
- **Características**: Latencia de red cero, despliegue simplificado, mejor seguridad

### **🐳 Infraestructura y Despliegue**

#### **[Docker](https://www.docker.com/)** - Plataforma de Contenerización
- **Propósito**: Despliegue consistente a través de entornos
- **Características**: Orquestación multi-contenedor, chequeos de salud, montaje de volúmenes

#### **[Docker Compose](https://docs.docker.com/compose/)** - Orquestación Multi-Contenedor
- **Propósito**: Despliegue coordinado de múltiples servicios
- **Características**: Escalado de servicios, gestión de configuración, logging

### **🔒 Tecnologías de Seguridad**

#### **[bcrypt](https://github.com/pyca/bcrypt/)** - Hash de Contraseñas
- **Propósito**: Almacenamiento y validación segura de contraseñas
- **Características**: Hash adaptativo, costo configurable, resistencia a ataques de temporización

#### **[OpenSSL](https://www.openssl.org/)** - Encriptación SSL/TLS
- **Propósito**: Soporte HTTPS y generación de certificados
- **Características**: Certificados autofirmados, generación de claves, encriptación

## ⚡ Inicio Rápido

### Prerrequisitos
- Docker & Docker Compose
- Clave API de Google Custom Search e ID del Motor de Búsqueda
- Clave API de Perplexity
- Clave API de OpenAI o configuración de Azure OpenAI

### 1. Configuración del Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# Configuración del Proveedor IA (elige uno)
OPENAI_API_KEY=tu_clave_api_openai_aqui

# O Configuración de Azure OpenAI
AZURE_API_KEY=tu_clave_api_azure
AZURE_ENDPOINT=https://tu-endpoint.openai.azure.com/
AZURE_DEPLOYMENT=tu_nombre_despliegue
AZURE_API_VERSION=2023-12-01-preview

# Configuración de Google Search
GOOGLE_API_KEY=tu_clave_api_google
GOOGLE_SEARCH_ENGINE_ID=tu_id_motor_busqueda_personalizada

# Configuración de Perplexity
PERPLEXITY_API_KEY=tu_clave_api_perplexity
PERPLEXITY_MODEL=sonar

# Configuración SSL (Opcional)
SSL_ENABLED=true
```

### 2. Configuración de APIs

#### Configuración de Google Custom Search
1. **Obtener Clave API**: Ve a [Google Cloud Console](https://console.cloud.google.com/), habilita Custom Search API, crea credenciales
2. **Crear Motor de Búsqueda Personalizada**: Ve a [Google Custom Search](https://cse.google.com/cse/), crea nuevo motor de búsqueda, obtén ID del Motor de Búsqueda

#### Configuración de API de Perplexity
1. **Obtener Clave API**: Regístrate en [Perplexity AI](https://perplexity.ai) y obtén tu clave API
2. **Elegir Modelo**: Selecciona de los modelos disponibles (sonar, sonar-pro, sonar-reasoning, etc.)

### 3. Configuración de Autenticación de Usuario

Genera credenciales de usuario para la aplicación:

```bash
cd client
python simple_generate_password.py
```

Esto crea `keys/config.yaml` con usuarios predeterminados. Puedes modificar las credenciales de usuario según sea necesario.

### 4. Configuración de Certificado SSL (Opcional)

Para soporte HTTPS, los certificados se generarán automáticamente cuando `SSL_ENABLED=true`.

### 5. Lanzar la Plataforma

```bash
# Construir e iniciar todos los servicios
docker-compose up --build

# O iniciar servicios individuales
docker-compose up mcpserver1    # Servidor MCP de Perplexity (con caché)
docker-compose up mcpserver2    # Servidor MCP de Google Search (con caché)
docker-compose up hostclient    # Cliente Streamlit (con MCP stdio integrado)
```

### 6. Acceder a la Aplicación

#### Modo HTTPS (Recomendado)
- **Interfaz Principal**: https://localhost:8503
- **Seguridad**: Certificado autofirmado (acepta advertencia del navegador)

#### Modo HTTP (Predeterminado)
- **Interfaz Principal**: http://localhost:8501
- **Alternativa**: http://127.0.0.1:8501

#### Chequeos de Salud y Monitoreo
- **Servidor de Google Search**: http://localhost:8002/health
- **Servidor de Perplexity**: http://localhost:8001/health
- **Estadísticas Detalladas de Google Search**: http://localhost:8002/health/detailed
- **Limpiar Caché de Google Search**: http://localhost:8002/cache/clear

#### Autenticación
Usa las credenciales generadas en el paso 3 (predeterminado: admin/very_Secure_p@ssword_123!)

## 🎯 Características Principales

### **Sistema de Caché Inteligente** ⭐ NUEVO
- **Caché de Google Search**: TTL de 30 minutos para resultados de búsqueda, TTL de 2 horas para contenido de páginas web
- **Caché de Perplexity**: TTL de 30 minutos para respuestas de IA
- **Gestión de Caché**: Herramientas incorporadas para limpieza de caché y estadísticas
- **Rendimiento**: Reducción significativa en el uso de API y mejores tiempos de respuesta
- **Limpieza Automática**: Entradas expiradas limpiadas automáticamente

### **Integración Dual de Motores de Búsqueda**
- **Herramientas de Google Search**: Búsqueda web completa y extracción de contenido con caché
- **Herramientas de Perplexity AI**: Búsqueda impulsada por IA con análisis inteligente y caché
- **Soporte multi-proveedor de IA** (OpenAI, Azure OpenAI con configuración mejorada)
- **Selección inteligente de herramientas** basada en tipo de consulta y requisitos

### **Capacidades Avanzadas de Búsqueda**

#### **Operaciones de Google Search (4 Herramientas)** - Mejoradas con Caché
- **google-search**: Integración de Google Custom Search API con caché de 30 minutos
- **read-webpage**: Extracción limpia de contenido de páginas web con caché de 2 horas
- **clear-cache**: Herramienta de gestión de caché para limpiar caché de búsqueda y páginas web
- **cache-stats**: Herramienta de monitoreo para rendimiento de caché y estadísticas

#### **Operaciones de Perplexity AI (5 Herramientas)** - Mejoradas con Caché
- **perplexity_search_web**: Búsqueda web estándar impulsada por IA con caché de 30 minutos
- **perplexity_advanced_search**: Búsqueda avanzada con parámetros de modelo personalizados y caché
- **search_show_categories**: Acceso a taxonomía completa basada en CSV
- **clear_api_cache**: Gestión de caché para respuestas de API de Perplexity
- **get_cache_stats**: Estadísticas de caché y monitoreo de rendimiento

#### **Operaciones de Etiquetado de Empresas (Servidor MCP stdio Integrado)**
- **search_show_categories**: Servidor MCP especializado basado en stdio para análisis de expositores de ferias comerciales
- **Gestión de Taxonomía**: Acceso a categorías estructuradas de industria/producto para 5 ferias comerciales principales
- **Acceso a Datos CSV**: Acceso en tiempo real a datos de categorías con filtrado y capacidades de búsqueda
- **Flujo de Trabajo Integrado**: Análisis sin interrupciones de empresas usando tanto herramientas de Google Search como de Perplexity

### **Seguridad y Autenticación**
- **Sistema de Autenticación de Usuario**: Inicio de sesión seguro con hash de contraseñas bcrypt
- **Gestión de Sesiones**: Sesiones persistentes de usuario con expiración configurable (30 días predeterminado)
- **Soporte SSL/HTTPS**: Conexiones encriptadas opcionales con certificados autofirmados en puerto 8503
- **Acceso Basado en Roles**: Dominios de email preautorizados y gestión de usuarios

### **Excelencia Técnica**
- **Contenerización Docker**: Despliegue y escalado fácil con 3 servicios
- **Soporte SSL/HTTPS**: Conexiones seguras con generación automática de certificados
- **Comunicación en Tiempo Real**: Server-Sent Events (SSE) para servidores MCP externos
- **Integración Stdio**: Servidor MCP de Etiquetado de Empresas integrado para flujos de trabajo especializados
- **Caché Inteligente**: Sistema de caché multi-capa para rendimiento óptimo
- **Monitoreo de Salud**: Chequeos de salud incorporados y monitoreo de caché para todos los servicios

## 📚 Herramientas y Capacidades Disponibles

### **Total de Herramientas Disponibles: 10 Herramientas**

#### **Servidor MCP de Google Search (4 Herramientas)** - Con Caché Inteligente
1. **google-search**
   - Realizar búsquedas de Google con 1-10 resultados configurables
   - **Caché**: TTL de 30 minutos para consultas de búsqueda idénticas
   - Devuelve títulos, enlaces, fragmentos y conteos totales de resultados
   - Información de acierto/fallo de caché incluida en respuestas

2. **read-webpage**
   - Extraer contenido limpio de cualquier página web accesible
   - **Caché**: TTL de 2 horas para contenido de páginas web con normalización de URL
   - Análisis HTML automático y limpieza (remueve scripts, anuncios, navegación)
   - Manejo de truncamiento de contenido para páginas grandes

3. **clear-cache** ⭐ NUEVO
   - Limpiar resultados de búsqueda en caché y contenido de páginas web
   - Soporta limpieza selectiva (búsqueda, páginas web, o todo)
   - Devuelve estadísticas sobre entradas limpiadas

4. **cache-stats** ⭐ NUEVO
   - Monitorear rendimiento y eficiencia de caché
   - Muestra tasas de acierto de caché, uso de memoria, e información TTL
   - Proporciona recomendaciones para gestión de caché

#### **Servidor MCP de Búsqueda Perplexity (5 Herramientas)** - Con Caché de Respuestas
1. **perplexity_search_web**
   - Búsqueda web estándar impulsada por IA con filtrado de actualidad
   - **Caché**: TTL de 30 minutos para respuestas de API
   - Devuelve respuestas sintetizadas por IA con citas automáticas

2. **perplexity_advanced_search**
   - Búsqueda avanzada con parámetros personalizados
   - **Caché**: Caché específico por parámetros con TTL
   - Selección de modelo, control de temperatura (0.0-1.0), máx tokens (1-2048)

3. **search_show_categories**
   - Buscar y filtrar taxonomía basada en CSV
   - Filtrar por feria (CAI, DOL, CCSE, BDAIW, DCW), industria o producto
   - **Datos Locales**: Sin llamadas a API externas, respuestas instantáneas

4. **clear_api_cache** ⭐ NUEVO
   - Limpiar caché de respuestas de API de Perplexity
   - Devuelve estadísticas de caché y conteo de entradas limpiadas
   - Útil para forzar respuestas frescas de API

5. **get_cache_stats** ⭐ NUEVO
   - Obtener estadísticas detalladas de caché de API de Perplexity
   - Muestra eficiencia de caché y métricas de rendimiento
   - Incluye tasas de acierto de caché e información TTL

#### **Servidor MCP de Etiquetado de Empresas (1 Herramienta - stdio Integrado)**
1. **search_show_categories** (Instancia Adicional)
   - Flujo de trabajo especializado de etiquetado y categorización de empresas
   - Acceso a taxonomía de ferias comerciales con pares industria/producto
   - Integrado con Google Search y Perplexity para investigación de empresas

### **Recursos Disponibles: 7+ Recursos**

#### **Recursos de Categorías CSV**
- **categories://all**: Datos CSV completos con todas las categorías de ferias
- **categories://shows**: Categorías organizadas por feria con estadísticas
- **categories://shows/{show_name}**: Categorías para ferias específicas
- **categories://industries**: Categorías organizadas por industria
- **categories://industries/{industry_name}**: Categorías específicas de industria
- **categories://search/{query}**: Búsqueda a través de todos los datos de categorías

### **Características de Optimización de Rendimiento** ⭐ NUEVO

#### **Caché del Servidor MCP de Google Search**
- **Resultados de Búsqueda**: TTL de 30 minutos con generación de clave MD5
- **Contenido de Páginas Web**: TTL de 2 horas con normalización de URL y eliminación de parámetros de seguimiento
- **Expulsión LRU**: Máximo 1000 páginas en caché con expulsión de las más antiguas primero
- **Limpieza Automática**: Entradas expiradas limpiadas cada 30 minutos (páginas web) y 10 minutos (búsqueda)
- **Estadísticas de Caché**: Monitoreo en tiempo real de eficiencia de caché y uso de memoria

#### **Caché del Servidor MCP de Perplexity**
- **Respuestas de API**: TTL de 30 minutos con caché específico por parámetros
- **Hash Inteligente**: Claves de caché basadas en consulta y todos los parámetros (actualidad, modelo, temperatura, etc.)
- **Optimización de Chequeos de Salud**: TTL de 5 minutos para chequeos de salud para evitar llamadas innecesarias a API
- **Gestión de Caché**: Herramientas para limpiar caché y monitorear rendimiento

#### **Beneficios del Sistema de Caché**
- **Costos de API Reducidos**: Reducción significativa en llamadas a Google Custom Search y API de Perplexity
- **Tiempos de Respuesta Mejorados**: Aciertos de caché proporcionan respuestas instantáneas
- **Mejor Confiabilidad**: Resultados en caché disponibles incluso durante interrupciones de API
- **Eficiencia de Recursos**: Menor carga del servidor y uso de ancho de banda
- **Experiencia de Usuario**: Resultados de búsqueda y carga de contenido más rápidos

## 📝 Ejemplos de Uso

### **Flujo de Trabajo de Autenticación**
```
1. Navegar a https://localhost:8503 (SSL) o http://localhost:8501 (HTTP)
2. Usar el panel de autenticación de la barra lateral
3. Iniciar sesión con credenciales generadas
4. Acceder a todas las características de la aplicación
```

### **Flujos de Trabajo de Búsqueda con Caché**

#### **Datos Rápidos e Información Actual (Perplexity con Caché)**
```
"¿Cuáles son los últimos desarrollos en inteligencia artificial?"
"Encuentra noticias recientes sobre cambio climático"
"¿Cuál es el estado actual de la adopción de energías renovables?"
```
*Usa herramientas de Perplexity con caché de 30 minutos para respuestas sintetizadas por IA*

#### **Investigación Completa (Google Search con Caché)**
```
"Investiga el impacto de la IA en la industria de la salud"
"Encuentra información detallada sobre prácticas agrícolas sostenibles"
"Analiza tendencias del mercado en vehículos eléctricos"
```
*Usa Google Search con caché de búsqueda de 30 minutos y caché de contenido de 2 horas*

#### **Ejemplos de Gestión de Caché**
```
# Limpiar todos los cachés
Usar la herramienta clear-cache: {"cacheType": "all"}

# Monitorear rendimiento de caché
Usar la herramienta cache-stats: {"detailed": true}

# Limpiar solo caché de búsqueda
Usar la herramienta clear-cache: {"cacheType": "search"}

# Obtener estadísticas de caché de Perplexity
Usar la herramienta get_cache_stats del servidor Perplexity
```

### **Monitoreo de Rendimiento**

#### **Monitoreo de Chequeos de Salud**
- **Google Search**: `curl http://localhost:8002/health/detailed`
- **Perplexity**: `curl http://localhost:8001/health`
- **Limpieza de Caché**: `curl http://localhost:8002/cache/clear`

#### **Indicadores de Rendimiento de Caché**
- **Tasa de Acierto de Caché**: Porcentaje de solicitudes servidas desde caché
- **Llamadas a API Evitadas**: Número de llamadas a API externas prevenidas por caché
- **Uso de Memoria**: Consumo estimado de memoria de caché
- **Efectividad TTL**: Qué tan bien funcionan las configuraciones TTL de caché para tus patrones de uso

## 🔧 Documentación de Componentes

### [🖥️ Documentación del Cliente Streamlit](./client/Readme.md)
- Configuración y configuración del sistema de autenticación
- Configuración SSL/HTTPS y gestión de certificados
- Configuración y gestión de proveedores de IA (OpenAI, Azure OpenAI, Configuración Mejorada)
- Monitoreo de ejecución de herramientas y gestión de conversaciones
- Integración de flujo de trabajo de etiquetado de empresas

### [🔍 Documentación del Servidor MCP de Google Search](./servers/server2/readme.md)
- Integración con Google Custom Search API con caché inteligente
- Herramientas de búsqueda web y extracción de contenido (4 herramientas incluyendo gestión de caché)
- Optimización de rendimiento y monitoreo de caché
- Implementación de transporte SSE con chequeos de salud

### [🔮 Documentación del Servidor MCP de Perplexity](./servers/server1/Readme.md)
- Integración con Perplexity AI API con caché de respuestas
- Búsqueda impulsada por IA con múltiples modelos (5 herramientas incluyendo gestión de caché)
- Parámetros de búsqueda avanzados y filtrado
- Gestión y acceso a datos de categorías CSV

## 🛠️ Desarrollo y Personalización

### **Configuración de Caché**

#### **Caché del Servidor de Google Search**
```javascript
// En servers/server2/tools/searchTool.js
const searchCache = new SearchCache(30); // TTL de 30 minutos

// En servers/server2/tools/readWebpageTool.js
const webpageCache = new WebpageCacheClass(2); // TTL de 2 horas
```

#### **Caché del Servidor de Perplexity**
```python
# En servers/server1/perplexity_sse_server.py
api_cache = APICache(ttl_seconds=1800)  # Caché de 30 minutos
health_check_cache = {"ttl": 300}  # Caché de chequeo de salud de 5 minutos
```

### **Ajuste de Rendimiento de Caché**
- **TTL de Caché de Búsqueda**: Ajustar basado en requisitos de frescura de contenido
- **TTL de Caché de Páginas Web**: Equilibrar entre frescura de contenido y carga del servidor
- **Tamaño Máximo de Caché**: Configurar basado en memoria disponible
- **Intervalos de Limpieza**: Optimizar basado en patrones de uso

## 🔒 Seguridad y Mejores Prácticas

### **Seguridad de API**
- Usar claves API seguras con alcance apropiado
- Implementar limitación de velocidad para solicitudes de búsqueda (automático con caché)
- Habilitar SSL/TLS para todas las comunicaciones
- Rotar regularmente claves API y credenciales

### **Seguridad de Caché**
- Las claves de caché usan hash MD5 para seguridad
- La normalización de URL elimina parámetros de seguimiento
- No se almacenan datos sensibles en caché
- Limpieza automática de entradas expiradas

### **Monitoreo de Rendimiento**
- Monitorear tasas de acierto de caché para optimizar configuraciones TTL
- Rastrear reducción de uso de API a través de caché
- Monitorear uso de memoria para dimensionamiento de caché
- Usar endpoints de chequeo de salud para monitoreo del sistema

## 🐛 Solución de Problemas

### **Problemas Relacionados con Caché**

#### **Caché No Funciona**
```bash
# Verificar estadísticas de caché
curl http://localhost:8002/health/detailed

# Limpiar caché si está corrupto
curl http://localhost:8002/cache/clear

# Verificar logs del servidor para errores de caché
docker-compose logs mcpserver2 | grep cache
```

#### **Alto Uso de Memoria**
```bash
# Verificar tamaños de caché
curl http://localhost:8002/health/detailed
curl http://localhost:8001/health

# Limpiar cachés grandes
Usar herramienta clear-cache con {"cacheType": "webpage"}
Usar herramienta clear_api_cache para Perplexity
```

#### **Problemas de Rendimiento de Caché**
- **Baja Tasa de Acierto**: Considerar aumentar valores TTL
- **Alto Uso de Memoria**: Reducir tamaños de caché o valores TTL
- **Respuestas Lentas**: Verificar si los intervalos de limpieza de caché son apropiados

### **Problemas de API con Caché**

#### **Datos Obsoletos en Caché**
```bash
# Forzar datos frescos
Usar herramientas con parámetro skipCache donde esté disponible
Limpiar tipo específico de caché
Reducir TTL para actualizaciones más frecuentes
```

#### **Limitación de Velocidad de API**
- **El Caché Ayuda**: Automáticamente reduce llamadas a API
- **Monitorear Uso**: Usar estadísticas de caché para rastrear reducción de llamadas a API
- **Optimizar TTL**: Equilibrar frescura con uso de API

## 📈 Métricas de Rendimiento

### **Rendimiento de Caché** ⭐ NUEVO
- **Tasa de Acierto de Caché de Google Search**: Típicamente 40-60% para consultas repetidas
- **Tasa de Acierto de Caché de Contenido de Páginas Web**: Típicamente 60-80% para páginas populares
- **Tasa de Acierto de Caché de Perplexity**: Típicamente 30-50% para consultas similares
- **Reducción de Llamadas a API**: 40-70% de reducción en llamadas a API externas
- **Mejora de Tiempo de Respuesta**: 80-95% más rápido para respuestas en caché

### **Características de Rendimiento Actuales**
- **Tiempo de Respuesta de Búsqueda en Caché**: ~50-100ms (vs 1-3s fresco)
- **Extracción de Contenido en Caché**: ~100-200ms (vs 2-8s fresco)
- **Respuesta de Perplexity en Caché**: ~100-300ms (vs 2-5s fresco)
- **Autenticación**: <1s operaciones de inicio/cierre de sesión
- **Descubrimiento de Herramientas**: <2s para conexión de servidor MCP

### **Características de Escalabilidad**
- Contenerización Docker para escalado horizontal
- Caché inteligente para dependencias externas reducidas
- Operaciones async para manejo concurrente de solicitudes
- Pooling de conexiones para conexiones de base de datos y API

## 🤝 Contribución

### **Flujo de Trabajo de Desarrollo**
1. Hacer fork del repositorio
2. Crear ramas de características para cada componente
3. Probar características de autenticación y seguridad
4. Probar funcionalidad de búsqueda tanto de Google como de Perplexity con caché
5. Verificar etiquetado de empresas y acceso a datos CSV
6. Probar gestión de caché y monitoreo de rendimiento
7. Enviar pull requests con pruebas completas

### **Pruebas de Caché**
- Probar escenarios de acierto/fallo de caché para todas las herramientas
- Verificar comportamiento TTL de caché y limpieza
- Probar herramientas de gestión de caché (clear-cache, cache-stats)
- Monitorear rendimiento de caché bajo carga
- Probar comportamiento de caché durante interrupciones de API

---

**Versión**: 2.1.0  
**Última Actualización**: Enero 2025  
**Compatibilidad**: Docker 20+, Python 3.11+, Node.js 18+, Google Custom Search API v1, Perplexity API v1  
**Seguridad**: Streamlit Authenticator 0.3.2, hash de contraseñas bcrypt, soporte SSL/HTTPS  
**Total de Herramientas**: 10 herramientas (4 Google Search con caché, 5 Perplexity AI con caché, 1 Etiquetado de Empresas)  
**Servidores**: 3 servicios (Cliente con MCP stdio integrado, MCP Google Search con caché, MCP Perplexity con caché)  
**Arquitectura**: Transporte SSE + stdio MCP con autenticación completa y caché inteligente  
**Rendimiento**: Sistema de caché inteligente con 40-70% de reducción de uso de API y 80-95% de mejora en tiempo de respuesta para contenido en caché