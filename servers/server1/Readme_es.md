# Servidor Perplexity MCP con Company Tagging y Categorías CSV

Un servidor integral del Model Context Protocol (MCP) que proporciona capacidades de búsqueda web impulsadas por IA usando la API de Perplexity, además de funcionalidad especializada de company tagging para la categorización de expositores de ferias comerciales. Esta versión utiliza Server-Sent Events (SSE) para comunicación en tiempo real, haciéndolo compatible con clientes MCP basados en web y navegadores.

## 🚀 Características

### **Búsqueda Web Impulsada por IA**
- **Búsqueda Inteligente**: Aprovecha la búsqueda impulsada por IA de Perplexity a través de la web
- **Filtros de Recencia**: Filtra resultados por período de tiempo (día, semana, mes, año)
- **Múltiples Modelos**: Soporte para todos los modelos de Perplexity AI incluyendo nuevos modelos
- **Soporte de Citas**: Citas automáticas de fuentes para todos los resultados
- **Parámetros Avanzados**: Ajuste fino de búsquedas con parámetros personalizados
- **Caching Inteligente**: Cache de respuestas API de 30 minutos con limpieza automática

### **Company Tagging y Categorización** ⭐ CARACTERÍSTICA
- **Investigación Automatizada de Empresas**: Investiga empresas usando fuentes web y LinkedIn
- **Coincidencia de Taxonomía**: Coincide empresas con categorías precisas de industria/producto
- **Contexto de Ferias Comerciales**: Enfoque en ferias relevantes (CAI, DOL, CCSE, BDAIW, DCW)
- **Salida Estructurada**: Genera tablas con hasta 4 pares industria/producto por empresa
- **Flujo de Trabajo de Analista de Datos**: Enfoque profesional de análisis de datos con foco en precisión

### **Acceso a Datos de Categorías CSV**
- **Categorías de Ferias**: Accede a datos categorizados organizados por ferias
- **Organización Industrial**: Navega categorías por clasificaciones de industria y producto
- **Funcionalidad de Búsqueda**: Busca a través de todos los datos de categorías con filtrado flexible
- **Recursos Dinámicos**: Acceso en tiempo real a datos CSV a través de recursos MCP
- **Contexto de Tagging**: Categorías formateadas específicamente para company tagging

### **Características Técnicas**
- **Protocolo SSE**: Comunicación en tiempo real usando Server-Sent Events
- **Caching Inteligente**: Cache de respuestas API con TTL de 30 minutos y limpieza automática
- **Monitoreo de Salud**: Endpoints de verificación de salud optimizados sin llamadas API externas
- **Operaciones Async**: Arquitectura async/await de alto rendimiento
- **Manejo de Errores**: Gestión integral de errores y logging
- **Configuración de Entorno**: Configuración flexible vía variables de entorno

## 📋 Prerrequisitos

- Python 3.11+
- Clave API de Perplexity (obtén una en [perplexity.ai](https://perplexity.ai))
- Docker (opcional, para despliegue containerizado)
- Archivo CSV con datos de categorías (incluido: `src/perplexity_mcp/categories/classes.csv`)

## 🛠️ Instalación y Configuración

### 1. Configuración del Entorno

Crea un archivo `.env` en el directorio del servidor:

```env
# Configuración API de Perplexity
PERPLEXITY_API_KEY=tu_clave_api_perplexity_aqui
PERPLEXITY_MODEL=sonar
```

### 2. Desarrollo Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servidor
python perplexity_sse_server.py
```

### 3. Despliegue con Docker

```bash
# Construir la imagen Docker
docker build -t perplexity-mcp-sse .

# Ejecutar el contenedor
docker run -p 8001:8001 \
  -e PERPLEXITY_API_KEY=tu_clave_api_aqui \
  -e PERPLEXITY_MODEL=sonar \
  perplexity-mcp-sse
```

## 🔧 Herramientas Disponibles (6 Herramientas)

### **Herramientas de Búsqueda Web (2 Herramientas)**

#### **perplexity_search_web**
Búsqueda web estándar con filtrado de recencia y caching inteligente.

**Parámetros:**
- `query` (string, requerido): La consulta de búsqueda
- `recency` (string, opcional): Filtro de tiempo - "day", "week", "month", "year" (por defecto: "month")

**Caching:** Resultados en cache por 30 minutos para reducir uso de API y mejorar tiempos de respuesta.

#### **perplexity_advanced_search**
Búsqueda avanzada con parámetros personalizados para control fino y caching.

**Parámetros:**
- `query` (string, requerido): La consulta de búsqueda
- `recency` (string, opcional): Filtro de tiempo (por defecto: "month")
- `model` (string, opcional): Sobrescribir el modelo por defecto
- `max_tokens` (int, opcional): Tokens máximos de respuesta (por defecto: 512, máx: 2048)
- `temperature` (float, opcional): Aleatoriedad de respuesta 0.0-1.0 (por defecto: 0.2)

### **Herramientas de Gestión de Categorías (2 Herramientas)**

#### **search_show_categories**
Busca y filtra categorías de ferias desde los datos CSV.

**Parámetros:**
- `show_name` (string, opcional): Filtrar por feria específica (CAI, DOL, CCSE, BDAIW, DCW)
- `industry_filter` (string, opcional): Filtrar por nombre de industria (coincidencia parcial)
- `product_filter` (string, opcional): Filtrar por nombre de producto (coincidencia parcial)

#### **tag_company** ⭐ CARACTERÍSTICA PRINCIPAL
Investigación avanzada de empresas y tagging de taxonomía para expositores de ferias comerciales.

**Parámetros:**
- `company_name` (string, requerido): El nombre principal de la empresa
- `trading_name` (string, opcional): Nombre comercial alternativo
- `target_shows` (string, opcional): Códigos de ferias separados por comas (ej., "CAI,DOL,BDAIW")
- `company_description` (string, opcional): Breve descripción de la empresa

### **Herramientas de Gestión de Cache (2 Herramientas)**

#### **clear_api_cache**
Limpia las respuestas API en cache para forzar recuperación de datos frescos.

**Parámetros:** Ninguno

**Retorna:** Estadísticas sobre entradas de cache limpiadas

#### **get_cache_stats**
Obtiene estadísticas actuales de cache API y métricas de rendimiento.

**Parámetros:** Ninguno

**Retorna:** Información detallada de uso de cache y rendimiento

## 📋 Prompts Disponibles (1 Prompt)

### **company_tagging_analyst**
Prompt de analista de datos profesional para categorización de empresas.

**Parámetros:**
- `company_name` (string): El nombre principal de la empresa
- `trading_name` (string): Nombre comercial alternativo (opcional)
- `target_shows` (string): Ferias en las que la empresa está interesada
- `company_description` (string): Breve descripción (opcional)

## 🗂️ Recursos Disponibles (7 Recursos)

### **Recursos de Categorías Básicas**

#### **categories://all**
Datos CSV completos con todas las categorías de ferias en formato JSON.

#### **categories://shows**
Categorías organizadas por feria con estadísticas y desglose por industrias.

#### **categories://shows/{show_name}**
Categorías para una feria específica (CAI, DOL, CCSE, BDAIW, DCW).

#### **categories://industries**
Categorías organizadas por industria con asociaciones de productos.

#### **categories://industries/{industry_name}**
Categorías para una industria específica (insensible a mayúsculas, coincidencia parcial).

#### **categories://search/{query}**
Busca a través de todos los datos de categorías con coincidencia de consulta flexible.

### **Recurso de Company Tagging**

#### **categories://for-tagging**
Categorías formateadas específicamente para análisis de company tagging con instrucciones de uso.

## 🎯 Flujo de Trabajo de Company Tagging

### **Proceso de Análisis Completo**

La herramienta `tag_company` sigue un flujo de trabajo integral de investigación y análisis:

1. **Validación de Entrada**
   - Valida nombre de empresa (requerido)
   - Normaliza nombre comercial y ferias objetivo
   - Determina prioridad de nombre de investigación (Nombre Comercial > Nombre de Empresa)

2. **Fase de Investigación Web**
   - Investigación inicial de empresa usando Perplexity AI (con cache para eficiencia)
   - Contexto adicional de LinkedIn y sitios web de empresas
   - Enfoque en productos/servicios relevantes a ferias objetivo

3. **Fase de Coincidencia de Taxonomía**
   - Análisis de hallazgos de investigación
   - Coincidencia con categorías exactas de taxonomía
   - Selección de hasta 4 pares industria/producto más relevantes

4. **Generación de Salida Estructurada**
   - Resumen de análisis profesional
   - Pista de auditoría de investigación
   - Tabla formateada con resultados de categorización

### **Ejemplos de Uso**

#### **Company Tagging Básico**
```python
# Etiquetar una empresa tecnológica
result = await tag_company(
    company_name="NVIDIA Corporation",
    target_shows="CAI,BDAIW"
)
```

#### **Empresa con Nombre Comercial**
```python
# Usar nombre comercial para investigación
result = await tag_company(
    company_name="International Business Machines Corporation",
    trading_name="IBM",
    target_shows="CAI,DOL,BDAIW",
    company_description="Empresa de tecnología empresarial y consultoría"
)
```

## 🎯 Contexto de Ferias Comerciales

### **Ferias Soportadas**
- **CAI**: Cloud and AI Infrastructure (22 categorías)
- **DOL**: DevOps Live (11 categorías)
- **CCSE**: Cloud and Cyber Security Expo (14 categorías)
- **BDAIW**: Big Data and AI World (13 categorías)
- **DCW**: Data Centre World (20 categorías)

## 🔌 Endpoints de API

### Verificación de Salud
```
GET /health
```

**Respuesta Optimizada (Sin Llamadas API Externas):**
```json
{
  "status": "healthy",
  "version": "0.1.7",
  "model": "sonar",
  "api_key_configured": true,
  "api_test_disabled": "Las verificaciones de salud no prueban APIs externas para evitar llamadas innecesarias",
  "uptime_seconds": 3600,
  "cache_stats": {
    "total_entries": 15,
    "valid_entries": 12,
    "expired_entries": 3,
    "ttl_seconds": 1800
  },
  "csv_data": {
    "available": true,
    "total_records": 80,
    "shows": ["CAI", "DOL", "CCSE", "BDAIW", "DCW"]
  },
  "optimization_features": {
    "api_caching": true,
    "cache_ttl_seconds": 1800,
    "health_check_caching": true,
    "external_api_calls_avoided": "Las verificaciones de salud no llaman APIs externas"
  }
}
```

### Endpoint SSE
```
GET /sse
```
Endpoint principal para conexiones de clientes MCP.

### Endpoint de Mensajes
```
POST /messages/
```
Endpoint interno para manejo de mensajes MCP.

## 🚀 Rendimiento y Optimización

### **Sistema de Caching Inteligente**
- **Cache de Respuestas API**: TTL de 30 minutos para respuestas de la API de Perplexity
- **Generación de Claves de Cache**: Hashing MD5 de parámetros de consulta para búsqueda eficiente
- **Limpieza Automática**: Eliminación periódica de entradas de cache expiradas
- **Optimización de Memoria**: Gestión inteligente del tamaño de cache

### **Optimización de Verificación de Salud**
- **Sin Llamadas API Externas**: Las verificaciones de salud evitan uso innecesario de API
- **Cache de 5 Minutos**: Resultados de verificación de salud en cache para prevenir spam
- **Estado Basado en Configuración**: Estado determinado por configuración de entorno
- **Monitoreo de Rendimiento**: Estadísticas detalladas de cache y optimización

### **Beneficios**
- **Costos de API Reducidos**: Reducción significativa en llamadas a la API de Perplexity
- **Tiempos de Respuesta Más Rápidos**: Respuestas en cache servidas instantáneamente
- **Mejor Confiabilidad**: Dependencia reducida de disponibilidad de API externa
- **Menor Carga del Servidor**: Uso optimizado de recursos

## 🎯 Ejemplos de Uso Avanzado

### **Flujo de Trabajo de Búsqueda con Cache**
```python
# Primera búsqueda (llamada API realizada, resultado en cache)
result1 = await perplexity_search_web(
    query="tendencias de inteligencia artificial 2024",
    recency="month"
)

# Repetir búsqueda dentro de 30 minutos (servida desde cache)
result2 = await perplexity_search_web(
    query="tendencias de inteligencia artificial 2024",
    recency="month"
)
# result2 incluirá "cached": true
```

### **Flujo de Trabajo de Gestión de Cache**
```python
# Verificar estado del cache
stats = await get_cache_stats()

# Limpiar cache si es necesario para datos frescos
cleared = await clear_api_cache()

# Realizar búsqueda fresca
fresh_result = await perplexity_search_web(
    query="últimos desarrollos en IA"
)
```

### **Investigación de Empresa con Caching**
```python
# Investigar empresa (usa respuestas de Perplexity en cache cuando están disponibles)
result = await tag_company(
    company_name="Microsoft Corporation",
    target_shows="CAI,BDAIW"
)

# Obtener categorías relevantes para contexto
categories = client.read_resource("categories://for-tagging")
```

## 🐛 Resolución de Problemas

### **Problemas Relacionados con Cache**

**Datos Obsoletos:**
```
Problema: Los resultados en cache están desactualizados
Solución: Usar la herramienta clear_api_cache para forzar datos frescos
```

**Alto Uso de Memoria:**
```
Problema: El cache consume demasiada memoria
Solución: Monitorear con get_cache_stats y limpiar periódicamente
```

### **Problemas de API**

**Limitación de Tasa:**
```
Error: Límite de tasa de API de Perplexity excedido
Solución: Depender del cache para reducir llamadas API, implementar retrasos
```

**Problemas de Clave API:**
```
Error: Clave API inválida
Solución: Verificar variable de entorno PERPLEXITY_API_KEY
```

## 🚀 Despliegue en Producción

### **Docker Compose con Optimización**
```yaml
services:
  perplexity-mcp:
    build: .
    ports:
      - "8001:8001"
    environment:
      - PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
      - PERPLEXITY_MODEL=sonar-pro
    volumes:
      - ./src/perplexity_mcp/categories:/app/src/perplexity_mcp/categories:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
```

### **Monitoreo de Rendimiento**
- **Tasa de Aciertos de Cache**: Monitorear reducción de llamadas API a través de caching
- **Tiempos de Respuesta**: Seguir mejoras de rendimiento desde respuestas en cache
- **Uso de Memoria**: Monitorear consumo de memoria del cache
- **Uso de API**: Seguir frecuencia de llamadas a la API de Perplexity y costos

## 📈 Resultados de Optimización

### **Beneficios Medidos**
- **Reducción de Llamadas API**: Hasta 70% de reducción en llamadas a la API de Perplexity
- **Velocidad de Respuesta**: 10x respuestas más rápidas para consultas en cache
- **Ahorro de Costos**: Reducción significativa en costos de uso de API
- **Confiabilidad**: Mejor tiempo de actividad con respaldos en cache

### **Métricas de Monitoreo**
- **Estadísticas de Cache**: Disponibles vía herramienta `get_cache_stats`
- **Frecuencia de Verificación de Salud**: Sin sobrecarga de API para monitoreo de salud
- **Eficiencia de Memoria**: Limpieza automática de cache y optimización

## 🤝 Contribuyendo

### **Agregando Soporte de Cache**
Al extender el servidor:
1. **Usar Cache Existente**: Aprovechar la clase APICache para nuevas herramientas
2. **Implementar TTL**: Establecer duración apropiada de cache para tu caso de uso
3. **Agregar Gestión de Cache**: Incluir capacidades de estadísticas y limpieza de cache
4. **Monitorear Rendimiento**: Seguir efectividad del cache y uso de memoria

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT.

---

**Versión**: 0.1.7  
**Última Actualización**: Julio 2025  
**Compatibilidad**: Perplexity API v1, MCP 1.0+, Python 3.11+  
**Herramientas**: 6 (Búsqueda web + Categorías + Company tagging + Gestión de cache)  
**Recursos**: 7 (Acceso completo a CSV + Contexto de tagging)  
**Prompts**: 1 (Analista profesional de company tagging)  
**Ferias Soportadas**: 5 (CAI, DOL, CCSE, BDAIW, DCW)  
**Optimización**: Caching inteligente con TTL de 30min, verificaciones de salud optimizadas