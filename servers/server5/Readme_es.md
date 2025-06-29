# Servidor MCP HubSpot

Una implementación integral del servidor del Protocolo de Contexto de Modelo (MCP) para integración con CRM HubSpot, proporcionando acceso completo a la API de HubSpot a través de 25 herramientas especializadas.

## 🎯 Visión General

Este servidor MCP permite integración perfecta con CRM HubSpot, permitiéndote gestionar contactos, empresas, ofertas, tickets y más a través de un protocolo estandarizado. Construido con Express.js y transporte Server-Sent Events (SSE), proporciona capacidades de comunicación en tiempo real para asistentes de IA y aplicaciones.

## ✨ Características

### **Integración Completa HubSpot (25 Herramientas)**
- **OAuth y Autenticación**: Detalles de usuario y validación de tokens
- **Gestión de Objetos**: Operaciones CRUD completas para todos los tipos de objeto HubSpot
- **Búsqueda Avanzada**: Capacidades de filtrado y consulta complejas
- **Gestión de Asociaciones**: Enlazar y gestionar relaciones entre objetos
- **Gestión de Propiedades**: Crear y gestionar campos personalizados
- **Seguimiento de Compromisos**: Notas y tareas con soporte de ciclo de vida completo
- **Integración de Flujos de Trabajo**: Acceso a insights de automatización
- **Integración UI**: Generar enlaces directos a la interfaz HubSpot

### **Capacidades Técnicas**
- **Server-Sent Events (SSE)**: Comunicación bidireccional en tiempo real
- **Soporte Docker**: Despliegue contenerizado con Docker Compose
- **Validación de Esquema**: Validación de entrada basada en Zod para todas las herramientas
- **Manejo de Errores**: Mensajes de error integrales y depuración
- **Seguridad de Tipos**: Verificación completa de tipos estilo TypeScript

## 🚀 Inicio Rápido

### Prerrequisitos
- Node.js 18+ o Docker
- Token de Acceso de App Privada HubSpot
- Cliente compatible con MCP (Claude Desktop, etc.)

### 1. Configuración de Entorno

Crear un archivo `.env`:
```env
PRIVATE_APP_ACCESS_TOKEN=tu_token_hubspot_app_privada
PORT=8004
HOST=0.0.0.0
```

### 2. Instalación y Ejecución

#### Opción A: Docker (Recomendado)
```bash
# Construir y ejecutar con Docker Compose
docker-compose build --no-cache mcpserver5
docker-compose up mcpserver5
```

#### Opción B: Node.js
```bash
# Instalar dependencias
npm install

# Iniciar el servidor
npm start

# O ejecutar en modo desarrollo
npm run dev
```

### 3. Verificar Instalación
- Verificación de salud: `http://localhost:8004/health`
- Endpoint MCP: `http://localhost:8004/sse`

## 🔧 Configuración

### Configuración HubSpot
1. Ir a Cuenta de Desarrollador HubSpot
2. Crear una App Privada
3. Otorgar scopes necesarios (CRM, Automatización, etc.)
4. Copiar el token de acceso a tu archivo `.env`

### Configuración Cliente MCP
Agregar a la configuración de tu cliente MCP:
```json
{
  "mcpServers": {
    "hubspot": {
      "command": "http",
      "args": ["http://localhost:8004/sse"]
    }
  }
}
```

## 📚 Herramientas Disponibles

Para documentación completa de herramientas, ver [HUBSPOT_TOOLS_GUIDE.md](./HUBSPOT_TOOLS_GUIDE.md).

### Categorías Principales

#### **Autenticación (1 herramienta)**
- `hubspot-get-user-details` - Obtener contexto de usuario y permisos

#### **Gestión de Objetos (7 herramientas)**
- `hubspot-list-objects` - Listar objetos con paginación
- `hubspot-search-objects` - Búsqueda avanzada con filtros
- `hubspot-batch-read-objects` - Leer múltiples objetos por ID
- `hubspot-batch-create-objects` - Crear múltiples objetos
- `hubspot-batch-update-objects` - Actualizar múltiples objetos
- `hubspot-get-schemas` - Obtener esquemas de objetos personalizados

#### **Gestión de Propiedades (4 herramientas)**
- `hubspot-list-properties` - Listar propiedades de objetos
- `hubspot-get-property` - Obtener detalles específicos de propiedad
- `hubspot-create-property` - Crear propiedades personalizadas
- `hubspot-update-property` - Actualizar definiciones de propiedades

#### **Gestión de Asociaciones (3 herramientas)**
- `hubspot-create-association` - Enlazar objetos juntos
- `hubspot-list-associations` - Obtener relaciones de objetos
- `hubspot-get-association-definitions` - Obtener tipos de asociación válidos

#### **Seguimiento de Compromisos (3 herramientas)**
- `hubspot-create-engagement` - Crear notas y tareas
- `hubspot-get-engagement` - Recuperar detalles de compromisos
- `hubspot-update-engagement` - Actualizar compromisos existentes

#### **Integración de Flujos de Trabajo (2 herramientas)**
- `hubspot-list-workflows` - Listar flujos de trabajo de automatización
- `hubspot-get-workflow` - Obtener detalles de flujos de trabajo

#### **Integración UI (2 herramientas)**
- `hubspot-get-link` - Generar enlaces UI HubSpot
- `hubspot-generate-feedback-link` - Generar enlaces de retroalimentación

## 💡 Ejemplos de Uso

### Gestión Básica de Contactos
```javascript
// Obtener detalles de usuario primero
hubspot-get-user-details

// Crear un nuevo contacto
hubspot-batch-create-objects {
  "objectType": "contacts",
  "inputs": [{
    "properties": {
      "firstname": "Juan",
      "lastname": "García",
      "email": "juan@ejemplo.com"
    }
  }]
}

// Buscar contactos
hubspot-search-objects {
  "objectType": "contacts",
  "query": "juan@ejemplo.com"
}
```

### Flujo de Trabajo CRM Completo
```javascript
// 1. Crear contacto y empresa
// 2. Asociarlos juntos
// 3. Agregar una tarea de seguimiento
// 4. Generar enlace para ver en HubSpot

// Esto demuestra el poder completo de las 25 herramientas disponibles
// trabajando juntas para gestión CRM completa
```

## 🏗️ Arquitectura

### Estructura del Proyecto
```
servers/server5/
├── main.js                 # Servidor Express con transporte SSE
├── package.json           # Dependencias y scripts
├── Dockerfile            # Configuración de contenedor
├── .dockerignore         # Reglas ignore Docker
├── HUBSPOT_TOOLS_GUIDE.md # Documentación completa de herramientas
├── tools/                # Implementaciones de herramientas
│   ├── index.js          # Registro y manejador de herramientas
│   ├── baseTool.js       # Clase base de herramienta
│   ├── toolsRegistry.js  # Auto-registro de todas las herramientas
│   ├── oauth/            # Herramientas de autenticación
│   ├── objects/          # Herramientas gestión objetos
│   ├── properties/       # Herramientas gestión propiedades
│   ├── associations/     # Herramientas gestión asociaciones
│   ├── engagements/      # Herramientas compromisos
│   ├── workflows/        # Herramientas flujos trabajo
│   └── links/           # Herramientas integración UI
├── prompts/             # Prompts MCP (extensible)
├── types/               # Definiciones de tipos
└── utils/               # Utilidades y cliente HubSpot
```

### Componentes Clave

#### **Clase BaseTool**
Todas las herramientas extienden la clase `BaseTool` que proporciona:
- Validación de esquema Zod
- Manejo estandarizado de errores
- Formato consistente de respuestas

#### **Cliente HubSpot**
Cliente HTTP centralizado con:
- Autenticación automática
- Manejo de request/response
- Gestión de errores
- Soporte para todos los métodos HTTP

#### **Registro de Herramientas**
Sistema de auto-registro que:
- Descubre todas las implementaciones de herramientas
- Proporciona listado de herramientas para clientes MCP
- Enruta llamadas de herramientas a manejadores apropiados

## 🔍 Depuración y Monitoreo

### Verificación de Salud
```bash
curl http://localhost:8004/health
```

### Logs
El servidor proporciona logging detallado para:
- Ejecución de herramientas
- Requests/responses API
- Errores de validación
- Estado de conexión

### Manejo de Errores
- Errores de validación de esquema
- Errores de API HubSpot
- Problemas de conectividad de red
- Problemas de autenticación

## 🔒 Seguridad

### Autenticación
- Autenticación segura basada en tokens con HubSpot
- Protección de variables de entorno
- Sin exposición de tokens en logs

### Validación
- Validación integral de entrada usando esquemas Zod
- Seguridad de tipos a través de la aplicación
- Mensajes de error sanitizados

### Seguridad Docker
- Ejecución de usuario no-root
- Superficie de ataque mínima
- Valores por defecto seguros

## 🧪 Pruebas

### Conectividad Básica
```bash
# Probar endpoint de salud
curl http://localhost:8004/health

# Probar conexión MCP
# Conectar tu cliente MCP a http://localhost:8004/sse
```

### Validación de Herramientas
1. Comenzar con `hubspot-get-user-details` para verificar autenticación
2. Usar `hubspot-list-objects` para probar recuperación básica de datos
3. Probar `hubspot-search-objects` para funcionalidad avanzada

## 📈 Rendimiento

### Características de Optimización
- Operaciones batch eficientes para manejo de datos masivos
- Respuestas paginadas para datasets grandes
- Pooling de conexiones para requests HTTP
- Huella de memoria mínima

### Consideraciones de Escalado
- Diseño sin estado para escalado horizontal
- Contenedor Docker listo para orquestación
- Soporte configurable de limitación de tasa

## 🤝 Contribuir

### Configuración de Desarrollo
```bash
# Clonar repositorio
git clone <url-repositorio>
cd servers/server5

# Instalar dependencias
npm install

# Iniciar en modo desarrollo
npm run dev
```

### Agregar Nuevas Herramientas
1. Crear clase de herramienta extendiendo `BaseTool`
2. Implementar el método `process`
3. Agregar a `toolsRegistry.js`
4. Actualizar documentación

### Estilo de Código
- Módulos ES6+
- Zod para validación de esquema
- Manejo integral de errores
- Nomenclatura clara y descriptiva

## 🐛 Solución de Problemas

### Problemas Comunes

#### Error "Se requiere token de acceso"
- Verificar `PRIVATE_APP_ACCESS_TOKEN` en `.env`
- Verificar configuración de App Privada HubSpot
- Asegurar que la app tiene scopes necesarios

#### Conexión Rechazada
- Verificar que el servidor está ejecutándose en puerto correcto
- Verificar configuraciones de firewall
- Confirmar configuración de cliente MCP

#### Errores de Validación de Herramientas
- Revisar requisitos de esquema de entrada
- Verificar documentación de API HubSpot
- Verificar tipos de objeto y nombres de propiedades

#### Limitación de Tasa
- HubSpot impone límites de tasa API
- Implementar delays entre requests si es necesario
- Usar operaciones batch para datos masivos

### Obtener Ayuda
- Verificar [Documentación de Desarrollador HubSpot](https://developers.hubspot.com/)
- Revisar [HUBSPOT_TOOLS_GUIDE.md](./HUBSPOT_TOOLS_GUIDE.md) para uso detallado de herramientas
- Enviar retroalimentación vía herramienta `hubspot-generate-feedback-link`

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT. Ver el archivo LICENSE para detalles.

## 🔗 Recursos

- [Documentación del Protocolo de Contexto de Modelo](https://modelcontextprotocol.io/)
- [Documentación de API HubSpot](https://developers.hubspot.com/docs/api/overview)
- [Guía de Herramientas HubSpot](./HUBSPOT_TOOLS_GUIDE.md)
- [Documentación Docker](https://docs.docker.com/)

---