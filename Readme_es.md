# Plataforma de Integración MCP de Búsqueda Impulsada por IA

Una aplicación integral que proporciona interacciones impulsadas por IA con Google Search y Perplexity AI a través de servidores de Protocolo de Contexto de Modelo (MCP). Esta plataforma permite búsqueda web sin interrupciones, análisis impulsado por IA y extracción de contenido con seguridad HTTPS opcional y autenticación de usuarios.

## 🚀 Resumen del Sistema

Esta aplicación consta de tres componentes integrados que trabajan juntos para proporcionar capacidades completas de búsqueda impulsada por IA:

1. **Cliente Streamlit** - Interfaz de chat IA con soporte multi-proveedor, autenticación y soporte SSL
2. **Servidor MCP de Google Search** - Búsqueda web y extracción de contenido vía Google Custom Search API
3. **Servidor MCP de Perplexity** - Búsqueda impulsada por IA con análisis inteligente vía Perplexity API

## 🏗️ Arquitectura del Sistema

![Diagrama de Arquitectura](docs/mcp_platform_architecture.svg)

## 🔧 Tecnologías Principales y Dependencias

Esta plataforma está construida utilizando tecnologías modernas y robustas que habilitan capacidades escalables de búsqueda impulsada por IA. Aquí tienes una descripción completa de las tecnologías clave y sus roles:

### **🌐 Frontend e Interfaz de Usuario**

#### **[Streamlit](https://streamlit.io/)** - Framework de Aplicaciones Web
- **Propósito**: Interfaz web principal para interacciones de usuario
- **Versión**: 1.44+
- **Por qué**: Desarrollo rápido de aplicaciones de datos con autenticación incorporada
- **Características**: Actualizaciones en tiempo real, sistema de componentes, gestión de sesiones
- **Documentación**: [Documentos de Streamlit](https://docs.streamlit.io/)

#### **[Streamlit Authenticator](https://github.com/mkhorasani/Streamlit-Authenticator)** - Sistema de Autenticación
- **Propósito**: Inicio de sesión seguro y gestión de sesiones de usuario
- **Versión**: 0.3.2
- **Por qué**: Hash de contraseñas bcrypt, control de acceso basado en roles
- **Características**: Persistencia de sesión, cookies seguras, gestión de usuarios
- **Seguridad**: Hash de contraseñas estándar de la industria y validación

### **🧠 IA y Modelos de Lenguaje**

#### **[LangChain](https://python.langchain.com/)** - Framework de IA
- **Propósito**: Orquestación de agentes IA y enrutamiento de herramientas
- **Versión**: 0.3.20+
- **Por qué**: Integración estandarizada de modelos IA con llamadas de herramientas
- **Características**: Agentes ReAct, gestión de memoria, ejecución de herramientas
- **Documentación**: [Documentos de LangChain](https://python.langchain.com/docs/introduction/)

#### **[API de OpenAI](https://openai.com/api/)** - Modelos de Lenguaje IA
- **Propósito**: Proveedor principal de IA para respuestas inteligentes
- **Modelos**: GPT-4o, GPT-4o-mini
- **Por qué**: Comprensión y generación de lenguaje de vanguardia
- **Características**: Llamadas de herramientas, respuestas en streaming, manejo de contexto
- **Documentación**: [Documentos de API de OpenAI](https://platform.openai.com/docs)

#### **[Azure OpenAI](https://azure.microsoft.com/es-es/products/ai-services/openai-service)** - IA Empresarial
- **Propósito**: Proveedor alternativo de IA para despliegues empresariales
- **Modelos**: GPT-4o, o3-mini
- **Por qué**: Características empresariales, residencia de datos, seguridad mejorada
- **Características**: Endpoints privados, cumplimiento, garantías SLA
- **Documentación**: [Documentos de Azure OpenAI](https://learn.microsoft.com/es-es/azure/ai-services/openai/)

### **🔍 Búsqueda y Fuentes de Datos**

#### **[Google Custom Search API](https://developers.google.com/custom-search)** - Motor de Búsqueda Web
- **Propósito**: Capacidades completas de búsqueda web
- **Versión**: v1
- **Por qué**: Resultados de búsqueda confiables y de alta calidad con personalización
- **Características**: Motores de búsqueda personalizados, filtrado de resultados, metadatos
- **Documentación**: [Documentos de Google Custom Search](https://developers.google.com/custom-search/v1/overview)

#### **[API de Perplexity AI](https://www.perplexity.ai/)** - Búsqueda Impulsada por IA
- **Propósito**: Búsqueda inteligente con respuestas generadas por IA
- **Modelos**: sonar, sonar-pro, sonar-reasoning
- **Por qué**: Combina búsqueda con análisis IA y citas
- **Características**: Filtrado de actualidad, selección de modelo, parámetros avanzados
- **Documentación**: [Documentos de API de Perplexity](https://docs.perplexity.ai/)

### **🔗 Protocolos de Comunicación**

#### **[Protocolo de Contexto de Modelo (MCP)](https://modelcontextprotocol.io/)** - Comunicación IA Estandarizada
- **Propósito**: Protocolo universal para integración de herramientas IA
- **Versión**: 1.0+
- **Por qué**: Estándar agnóstico al proveedor para comunicación de herramientas IA
- **Características**: Descubrimiento de herramientas, validación de esquemas, flexibilidad de transporte
- **Documentación**: [Especificación MCP](https://spec.modelcontextprotocol.io/)

#### **[Server-Sent Events (SSE)](https://developer.mozilla.org/es/docs/Web/API/Server-sent_events)** - Comunicación en Tiempo Real
- **Propósito**: Comunicación bidireccional en tiempo real para servidores MCP externos
- **Por qué**: Streaming eficiente, compatible con navegadores, baja latencia
- **Características**: Reconexión automática, orden de mensajes, multiplexación
- **Documentación**: [Documentos MDN SSE](https://developer.mozilla.org/es/docs/Web/API/Server-sent_events)

#### **Transporte stdio** - Comunicación de Procesos Locales
- **Propósito**: Comunicación de servidor MCP integrado dentro de contenedores
- **Por qué**: Latencia de red cero, despliegue simplificado, mejor seguridad
- **Características**: Aislamiento de procesos, manejo de errores, gestión del ciclo de vida

### **🐳 Infraestructura y Despliegue**

#### **[Docker](https://www.docker.com/)** - Plataforma de Contenerización
- **Propósito**: Despliegue consistente a través de entornos
- **Versión**: 20+
- **Por qué**: Aislamiento de entorno, escalabilidad, gestión de dependencias
- **Características**: Orquestación multi-contenedor, chequeos de salud, montaje de volúmenes
- **Documentación**: [Documentos de Docker](https://docs.docker.com/)

#### **[Docker Compose](https://docs.docker.com/compose/)** - Orquestación Multi-Contenedor
- **Propósito**: Despliegue coordinado de múltiples servicios
- **Por qué**: Dependencias de servicios, redes, gestión de entorno
- **Características**: Escalado de servicios, gestión de configuración, logging
- **Documentación**: [Documentos de Docker Compose](https://docs.docker.com/compose/)

### **🐍 Tecnologías Backend (Python)**

#### **[FastAPI](https://fastapi.tiangolo.com/)** - Framework Web Python Moderno
- **Propósito**: Servidores API de alto rendimiento para servicios MCP
- **Por qué**: Generación automática de OpenAPI, validación de tipos, soporte async
- **Características**: Inyección de dependencias, middleware, autenticación
- **Documentación**: [Documentos de FastAPI](https://fastapi.tiangolo.com/)

#### **[asyncio](https://docs.python.org/es/3/library/asyncio.html)** - Programación Asíncrona
- **Propósito**: Manejo concurrente de solicitudes y operaciones I/O
- **Por qué**: Alto rendimiento, operaciones concurrentes escalables
- **Características**: Bucles de eventos, corrutinas, gestión de tareas
- **Documentación**: [Documentos de asyncio](https://docs.python.org/es/3/library/asyncio.html)

#### **[Pydantic](https://pydantic.dev/)** - Validación de Datos
- **Propósito**: Validación y serialización de datos con seguridad de tipos
- **Versión**: 2.0+
- **Por qué**: Verificación de tipos en tiempo de ejecución, validación automática, esquema JSON
- **Características**: Validadores personalizados, manejo de errores, serialización
- **Documentación**: [Documentos de Pydantic](https://docs.pydantic.dev/)

### **🟢 Tecnologías Backend (Node.js)**

#### **[Node.js](https://nodejs.org/)** - Runtime de JavaScript
- **Propósito**: Servidor de alto rendimiento para servidor MCP de Google Search
- **Versión**: 18+
- **Por qué**: Operaciones I/O rápidas, ecosistema npm, motor V8
- **Características**: Arquitectura dirigida por eventos, I/O no bloqueante
- **Documentación**: [Documentos de Node.js](https://nodejs.org/docs/)

#### **[Express.js](https://expressjs.com/)** - Framework de Aplicaciones Web
- **Propósito**: Framework de servidor HTTP para endpoints SSE de MCP
- **Versión**: 5.1+
- **Por qué**: Ligero, flexible, extenso ecosistema de middleware
- **Características**: Enrutamiento, middleware, motores de plantillas
- **Documentación**: [Documentos de Express.js](https://expressjs.com/)

#### **[Cheerio](https://cheerio.js.org/)** - Análisis HTML del Lado del Servidor
- **Propósito**: Extraer y limpiar contenido de páginas web
- **Versión**: 1.0+
- **Por qué**: Manipulación HTML del lado del servidor similar a jQuery
- **Características**: Selectores CSS, manipulación DOM, extracción de texto
- **Documentación**: [Documentos de Cheerio](https://cheerio.js.org/)

### **🔒 Tecnologías de Seguridad**

#### **[bcrypt](https://github.com/pyca/bcrypt/)** - Hash de Contraseñas
- **Propósito**: Almacenamiento y validación segura de contraseñas
- **Versión**: 4.0+
- **Por qué**: Hash de contraseñas estándar de la industria con salt
- **Características**: Hash adaptativo, costo configurable, resistencia a ataques de temporización
- **Documentación**: [Documentos de bcrypt](https://github.com/pyca/bcrypt/)

#### **[OpenSSL](https://www.openssl.org/)** - Encriptación SSL/TLS
- **Propósito**: Soporte HTTPS y generación de certificados
- **Por qué**: Encriptación estándar de la industria, gestión de certificados
- **Características**: Certificados autofirmados, generación de claves, encriptación
- **Documentación**: [Documentos de OpenSSL](https://www.openssl.org/docs/)

#### **[cryptography](https://cryptography.io/)** - Librería Criptográfica de Python
- **Propósito**: Generación de certificados y operaciones criptográficas
- **Versión**: 42.0+
- **Por qué**: Recetas criptográficas de alto nivel y primitivas
- **Características**: Certificados X.509, generación de claves, aleatorio seguro
- **Documentación**: [Documentos de Cryptography](https://cryptography.io/)

## 📋 Tabla de Referencia de Puertos

| Servicio | Puerto | Protocolo | Propósito |
|----------|--------|-----------|-----------|
| **Streamlit HTTP** | 8501 | HTTP | Interfaz web principal |
| **Streamlit HTTPS** | 8503 | HTTPS | Interfaz web segura (recomendado) |
| **Google Search MCP** | 8002 | HTTP/SSE | Servidor de búsqueda web |
| **Perplexity MCP** | 8001 | HTTP/SSE | Servidor de búsqueda IA |
| **Company Tagging** | - | stdio | Servidor MCP integrado |

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
docker-compose up mcpserver1    # Servidor MCP de Perplexity
docker-compose up mcpserver2    # Servidor MCP de Google Search  
docker-compose up hostclient    # Cliente Streamlit
```

### 6. Acceder a la Aplicación

#### Modo HTTPS (Recomendado)
- **Interfaz Principal**: https://localhost:8503
- **Seguridad**: Certificado autofirmado (acepta advertencia del navegador)

#### Modo HTTP (Predeterminado)
- **Interfaz Principal**: http://localhost:8501
- **Alternativa**: http://127.0.0.1:8501

#### Chequeos de Salud
- **Servidor de Google Search**: http://localhost:8002/health
- **Servidor de Perplexity**: http://localhost:8001/health

#### Autenticación
Usa las credenciales generadas en el paso 2 (predeterminado: admin/very_Secure_p@ssword_123!)

## 🎯 Características Principales

### **Integración Dual de Motores de Búsqueda**
- **Herramientas de Google Search**: Búsqueda web completa y extracción de contenido usando Google Custom Search API
- **Herramientas de Perplexity AI**: Búsqueda impulsada por IA con análisis inteligente y síntesis
- **Soporte multi-proveedor de IA** (OpenAI, Azure OpenAI con soporte de configuración mejorado)
- **Selección inteligente de herramientas** basada en tipo de consulta y requisitos

### **Capacidades Avanzadas de Búsqueda**

#### **Operaciones de Google Search (2 Herramientas)**
- **google-search**: Integración completa de Google Custom Search API con 1-10 resultados configurables
- **read-webpage**: Extracción limpia de contenido de páginas web con análisis Cheerio y limpieza automática
- **Flujos de Trabajo de Investigación**: Búsqueda combinada y extracción de contenido para investigación completa
- **Resultados Visuales**: Presentación de datos estructurados con formato JSON

#### **Operaciones de Perplexity AI (3 Herramientas)**
- **perplexity_search_web**: Búsqueda web estándar impulsada por IA con respuestas inteligentes y citas
- **perplexity_advanced_search**: Búsqueda avanzada con parámetros de modelo personalizados, control de temperatura y límites de tokens
- **search_show_categories**: Acceso a taxonomía completa basada en CSV para categorías de ferias comerciales
- **Filtrado de Actualidad**: Filtrar resultados por período de tiempo (día, semana, mes, año)
- **Múltiples Modelos**: Soporte para sonar, sonar-pro, sonar-reasoning y otros modelos de Perplexity

#### **Operaciones de Etiquetado de Empresas (Servidor MCP Integrado)**
- **Investigación y Categorización de Empresas**: Servidor MCP especializado basado en stdio para análisis de expositores de ferias comerciales
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
- **Comunicación en Tiempo Real**: Server-Sent Events (SSE) para ambos servidores MCP externos
- **Integración Stdio**: Servidor MCP de Etiquetado de Empresas integrado para flujos de trabajo especializados
- **Validación de Esquemas**: Validación completa de entrada con Zod
- **Manejo de Errores**: Gestión robusta de errores y depuración
- **Monitoreo de Salud**: Chequeos de salud incorporados para todos los servicios

## 📚 Herramientas y Capacidades Disponibles

### **Total de Herramientas Disponibles: 6 Herramientas**

#### **Servidor MCP de Google Search (2 Herramientas)**
1. **google-search**
   - Realizar búsquedas de Google con 1-10 resultados configurables
   - Devuelve títulos, enlaces, fragmentos y conteos totales de resultados
   - Usa Google Custom Search API con cobertura web completa

2. **read-webpage**
   - Extraer contenido limpio de cualquier página web accesible
   - Análisis HTML automático y limpieza (remueve scripts, anuncios, navegación)
   - Manejo de truncamiento de contenido para páginas grandes
   - Devuelve título, texto limpio, URL y metadatos de contenido

#### **Servidor MCP de Búsqueda Perplexity (3 Herramientas)**
1. **perplexity_search_web**
   - Búsqueda web estándar impulsada por IA con filtrado de actualidad
   - Devuelve respuestas sintetizadas por IA con citas automáticas
   - Soporta filtros de actualidad día/semana/mes/año

2. **perplexity_advanced_search**
   - Búsqueda avanzada con parámetros personalizados
   - Selección de modelo, control de temperatura (0.0-1.0), máx tokens (1-2048)
   - Metadatos de respuesta detallados y formato de resultado completo

3. **search_show_categories**
   - Buscar y filtrar taxonomía basada en CSV
   - Filtrar por feria (CAI, DOL, CCSE, BDAIW, DCW), industria o producto
   - Resultados estructurados con información completa de categorías

#### **Servidor MCP de Etiquetado de Empresas (1 Herramienta - Stdio Integrado)**
1. **search_show_categories** (Instancia Adicional)
   - Flujo de trabajo especializado de etiquetado y categorización de empresas
   - Acceso a taxonomía de ferias comerciales con pares industria/producto
   - Integrado con Google Search y Perplexity para investigación de empresas

## 📝 Ejemplos de Uso

### **Flujo de Trabajo de Autenticación**
```
1. Navegar a https://localhost:8503 (SSL) o http://localhost:8501 (HTTP)
2. Usar el panel de autenticación de la barra lateral
3. Iniciar sesión con credenciales generadas
4. Acceder a todas las características de la aplicación
```

### **Flujos de Trabajo de Búsqueda**

#### **Datos Rápidos e Información Actual**
```
"¿Cuáles son los últimos desarrollos en inteligencia artificial?"
"Encuentra noticias recientes sobre cambio climático"
"¿Cuál es el estado actual de la adopción de energías renovables?"
```
*Usa herramientas de Perplexity para respuestas sintetizadas por IA con citas*

#### **Investigación Completa**
```
"Investiga el impacto de la IA en la industria de la salud"
"Encuentra información detallada sobre prácticas agrícolas sostenibles"
"Analiza tendencias del mercado en vehículos eléctricos"
```
*Usa Google Search para encontrar fuentes, luego extrae contenido detallado*

#### **Investigación y Categorización de Empresas**
```
"Busca categorías de ferias para CAI"
"Encuentra todas las categorías relacionadas con infraestructura en la nube"
"¿Qué empresas encajarían en la feria Data Centre World?"
```
*Usa herramientas de categorías CSV y capacidades de investigación integradas*

#### **Flujos de Trabajo de Investigación Híbrida**
```
"Compara diferentes enfoques para energías renovables y analiza su efectividad"
"Investiga amenazas actuales de ciberseguridad y proporciona análisis de estrategias de mitigación"
"Encuentra empresas en el espacio de IA y categorízalas para ferias comerciales"
```
*Usa ambos conjuntos de herramientas para cobertura y análisis completos*

### **Parámetros de Búsqueda Avanzados**

#### **Búsqueda Avanzada de Perplexity**
```
"Busca investigación sobre cambio climático con alto detalle y fuentes recientes"
# Usa perplexity_advanced_search con:
# - recency: "month"
# - max_tokens: 1500
# - temperature: 0.2 (para precisión factual)
```

#### **Google Search con Extracción de Contenido**
```
"Encuentra la documentación más reciente de React y lee la guía completa de inicio"
# Usa google-search seguido de read-webpage para contenido detallado
```

#### **Investigación Basada en Categorías**
```
"Busca empresas en categorías de Cloud e Infraestructura de IA"
# Usa search_show_categories con filtrado de ferias
```

## 🔧 Documentación de Componentes

### [🖥️ Documentación del Cliente Streamlit](./client/Readme.md)
- Configuración y configuración del sistema de autenticación
- Configuración SSL/HTTPS y gestión de certificados
- Configuración y gestión de proveedores de IA (OpenAI, Azure OpenAI, Configuración Mejorada)
- Monitoreo de ejecución de herramientas y gestión de conversaciones
- Integración de flujo de trabajo de etiquetado de empresas

### [🔍 Documentación del Servidor MCP de Google Search](./servers/server2/readme.md)
- Integración con Google Custom Search API
- Herramientas de búsqueda web y extracción de contenido (2 herramientas)
- Optimización de rendimiento y solución de problemas
- Implementación de transporte SSE

### [🔮 Documentación del Servidor MCP de Perplexity](./servers/server1/Readme.md)
- Integración con Perplexity AI API
- Búsqueda impulsada por IA con múltiples modelos (3 herramientas)
- Parámetros de búsqueda avanzados y filtrado
- Gestión y acceso a datos de categorías CSV

## 🛠️ Desarrollo y Personalización

### **Configuración de Desarrollo Local**
```bash
# Clonar el repositorio
git clone <tu-url-repo>
cd <directorio-proyecto>

# Instalar dependencias para cada componente
cd client && pip install -r requirements.txt
cd ../servers/server1 && pip install -r requirements.txt
cd ../servers/server2 && npm install
```

### **Configuración de API**
Asegúrate de tener:
- **Proyecto de Google Cloud Console** con Custom Search API habilitado
- **Google Custom Search Engine** configurado para búsqueda web
- **Cuenta de API de Perplexity** con clave API válida
- **Credenciales de OpenAI o Azure OpenAI** para el cliente IA

### **Agregar Herramientas Personalizadas**
1. **Herramientas de Google Search**: Extender server2 con operaciones de búsqueda adicionales
2. **Herramientas de Perplexity**: Agregar nuevas herramientas de análisis impulsadas por Perplexity en server1
3. **Herramientas de Etiquetado de Empresas**: Extender el servidor MCP stdio integrado
4. **Herramientas de Cliente**: Integrar servicios adicionales vía protocolo MCP

## 🔒 Seguridad y Mejores Prácticas

### **Seguridad de API**
- Usar claves API seguras con alcance apropiado
- Implementar limitación de velocidad para solicitudes de búsqueda
- Habilitar SSL/TLS para todas las comunicaciones
- Rotar regularmente claves API y credenciales

### **Seguridad de Autenticación**
- Hash de contraseñas bcrypt con salt
- Gestión segura de sesiones con expiración configurable
- Validación de dominios de email preautorizados
- Atributos de cookies HTTPOnly y seguras

### **Seguridad de Búsqueda**
- Validar todas las consultas de búsqueda y URLs
- Implementar filtrado de contenido para texto extraído
- Monitorear uso de API y cuotas para ambos servicios
- Usar manejo apropiado de errores que no exponga datos sensibles

## 📊 Monitoreo y Depuración

### **Chequeos de Salud**
- **Sistema General**: Indicadores de estado de interfaz Streamlit
- **Servidor de Google Search**: http://localhost:8002/health
- **Servidor de Perplexity**: http://localhost:8001/health
- **Etiquetado de Empresas**: Pruebas de servidor stdio integrado

### **Monitoreo de Búsqueda**
- Seguimiento de uso de API para Google y Perplexity
- Rendimiento de consultas de búsqueda y tiempos de respuesta
- Tasas de error y solicitudes fallidas
- Tasas de éxito de extracción de contenido
- Historial de ejecución de herramientas con logging detallado

### **Monitoreo de Autenticación**
- Seguimiento de sesiones de usuario y monitoreo de actividad
- Tasas de éxito/falla de inicio de sesión
- Logging de eventos de seguridad

## 🚀 Opciones de Despliegue

### **Despliegue de Desarrollo**
```bash
# Modo HTTP (predeterminado)
docker-compose up --build

# Modo HTTPS
echo "SSL_ENABLED=true" >> .env
docker-compose up --build
```

### **Despliegue de Producción**
- Usar archivos `.env` específicos del entorno
- Configurar certificados SSL apropiados
- Implementar gestión apropiada de secretos
- Configurar monitoreo y alertas para los 3 servicios
- Usar pooling de conexiones para escenarios de alto tráfico
- Configurar autenticación de usuario con credenciales de producción

## 🐛 Solución de Problemas

### **Problemas Comunes**

**Problemas de Conexión de API de Google**
- Verificar GOOGLE_API_KEY y GOOGLE_SEARCH_ENGINE_ID
- Revisar cuota y facturación de Custom Search API
- Asegurar que Custom Search Engine esté configurado para búsqueda web

**Problemas de API de Perplexity**
- Verificar que PERPLEXITY_API_KEY sea correcta y activa
- Revisar cuotas de API y estado de facturación
- Asegurar que PERPLEXITY_MODEL seleccionado esté disponible

**Problemas de Conexión de Servidor MCP**
- Verificar que ambos servidores estén ejecutándose (puertos 8001 y 8002)
- Verificar conectividad de red entre servicios
- Revisar logs del servidor para información detallada de errores

**Problemas de Autenticación**
- Verificar que `keys/config.yaml` exista y esté formateado apropiadamente
- Revisar que las credenciales de usuario coincidan con las contraseñas generadas
- Limpiar cookies del navegador si se experimentan problemas de inicio de sesión

**Problemas de Etiquetado de Empresas**
- Verificar que los datos CSV sean accesibles en el servidor stdio integrado
- Revisar que las herramientas de Etiquetado de Empresas aparezcan en la pestaña de Herramientas
- Probar conectividad del servidor stdio usando el botón "Test Company Tagging Server"

## 🤝 Contribución

### **Flujo de Trabajo de Desarrollo**
1. Hacer fork del repositorio
2. Crear ramas de características para cada componente
3. Probar características de autenticación y seguridad
4. Probar funcionalidad de búsqueda tanto de Google como de Perplexity
5. Verificar etiquetado de empresas y acceso a datos CSV
6. Enviar pull requests con pruebas completas

### **Pruebas de Búsqueda**
- Probar varias consultas de búsqueda y escenarios con ambos motores
- Verificar extracción de contenido de diferentes sitios web
- Probar manejo de errores y casos límite
- Validar gestión de cuota de API para ambos servicios
- Probar flujos de trabajo de categorización de empresas

## 📈 Métricas de Rendimiento

### **Características de Rendimiento Actuales**
- **Tiempo de Respuesta de Búsqueda**: Google Search ~1-3s, Perplexity ~2-5s
- **Extracción de Contenido**: ~2-8s dependiendo del tamaño de página
- **Autenticación**: <1s operaciones de inicio/cierre de sesión
- **Descubrimiento de Herramientas**: <2s para conexión de servidor MCP
- **Etiquetado de Empresas**: Rendimiento stdio integrado

### **Características de Escalabilidad**
- Contenerización Docker para escalado horizontal
- Operaciones async para manejo concurrente de solicitudes
- Pooling de conexiones para conexiones de base de datos y API
- Caché de contenido donde sea apropiado

## 🔧 Solución de Problemas Específicos

### **Error de Puerto en Uso**
Si encuentras errores de "puerto en uso":
```bash
# Verificar qué está usando los puertos
sudo lsof -i :8501
sudo lsof -i :8502
sudo lsof -i :8503

# Detener servicios Docker
docker-compose down

# Limpiar contenedores
docker system prune -f
```

### **Problemas de Certificado SSL**
Para problemas con certificados HTTPS:
```bash
# Regenerar certificados SSL
cd client
rm -rf ssl/
./generate_ssl_certificate.sh

# O usar el script de Python
python generate_ssl_certificate.py
```

### **Problemas de Permisos de Docker**
En sistemas Linux, si hay problemas de permisos:
```bash
# Agregar usuario al grupo docker
sudo usermod -aG docker $USER

# Reiniciar sesión o ejecutar
newgrp docker
```

---

**Versión**: 2.0.0  
**Última Actualización**: Enero 2025  
**Compatibilidad**: Docker 20+, Python 3.11+, Node.js 18+, Google Custom Search API v1, Perplexity API v1  
**Seguridad**: Streamlit Authenticator 0.3.2, hash de contraseñas bcrypt, soporte SSL/HTTPS  
**Total de Herramientas**: 6 herramientas (2 Google Search, 3 Perplexity AI, 1 Etiquetado de Empresas)  
**Servidores**: 3 servicios (Cliente con MCP stdio integrado, MCP Google Search, MCP Perplexity)  
**Arquitectura**: Transporte SSE + stdio MCP con autenticación completa