# Cliente MCP - Interfaz de Chat IA Segura con Autenticación Empresarial e Integración Multi-Servidor

Una aplicación integral basada en Streamlit que se conecta a servidores del Protocolo de Contexto de Modelo (MCP) para proporcionar interacciones impulsadas por IA con Yahoo Finance, bases de datos de grafos Neo4j y sistemas CRM de HubSpot. Cuenta con autenticación de usuario de grado empresarial, gestión de sesiones, soporte SSL y capacidades de IA multi-proveedor.

## 🚀 Características

### **Seguridad Empresarial y Autenticación**
- **Autenticación Segura de Usuarios**: Hash de contraseñas bcrypt con cifrado basado en salt
- **Gestión de Sesiones**: Sesiones de usuario persistentes con expiración configurable (30 días por defecto)
- **Control de Acceso Basado en Roles**: Dominios de email pre-autorizados y gestión de usuarios
- **Soporte SSL/TLS**: HTTPS opcional con generación de certificados auto-firmados
- **Cookies Seguras**: Cookies de autenticación configurables con claves de cifrado personalizadas
- **Aislamiento de Usuarios**: Historiales de conversación y datos de sesión separados por usuario

### **IA Avanzada e Integración**
- **Soporte Multi-Proveedor de IA**: Cambio fluido entre OpenAI y Azure OpenAI
- **Integración Triple de Servidores MCP**: Servidores MCP de Yahoo Finance, Neo4j y HubSpot
- **Interfaz de Chat en Tiempo Real**: Conversaciones interactivas con memoria de contexto completa
- **Seguimiento de Ejecución de Herramientas**: Monitoreo integral y depuración del uso de herramientas
- **Operaciones Conscientes del Esquema**: Recuperación automática de esquemas para validación inteligente de consultas
- **Conversaciones Conscientes del Contexto**: Mantiene historial de conversaciones y construye sobre interacciones previas

### **Experiencia de Usuario Moderna**
- **Interfaz con Pestañas**: Organizada en pestañas de Chat, Configuración, Conexiones y Herramientas
- **Diseño Responsivo**: UI moderna con temas personalizables, animaciones y soporte móvil
- **Panel de Usuario**: Información personal, gestión de sesiones y seguimiento de actividad
- **Gestión de Conversaciones**: Crear, cambiar, eliminar y organizar sesiones de chat
- **Descubrimiento de Herramientas**: Exploración interactiva de herramientas MCP disponibles con documentación
- **Estado en Tiempo Real**: Estado de conexión en vivo y monitoreo de salud

## 📋 Prerrequisitos

- Python 3.11+
- Docker (opcional, para despliegue contenerizado)
- Servidores MCP activos para Yahoo Finance, Neo4j y/o HubSpot
- Clave API de OpenAI o configuración de Azure OpenAI

## 🛠️ Instalación

### Configuración de Desarrollo Local

1. **Clonar el repositorio**
   ```bash
   git clone <tu-repo-url>
   cd client
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**
   
   Crear un archivo `.env` en el directorio cliente:
   ```env
   # Configuración OpenAI (elegir una)
   OPENAI_API_KEY=tu_clave_openai_aqui
   
   # O Configuración Azure OpenAI
   AZURE_API_KEY=tu_clave_azure
   AZURE_ENDPOINT=https://tu-endpoint.openai.azure.com/
   AZURE_DEPLOYMENT=tu_nombre_deployment
   AZURE_API_VERSION=2023-12-01-preview
   
   # Opcional: Habilitar SSL
   SSL_ENABLED=false
   ```

4. **Configurar autenticación de usuarios**
   
   Generar credenciales de usuario con cuentas por defecto:
   ```bash
   python simple_generate_password.py
   ```
   
   Esto crea `keys/config.yaml` con usuarios pre-configurados:
   - **admin**: very_Secure_p@ssword_123!
   - **juan**: Larisa1000@
   - **giovanni_romero**: MrRomero2024!
   - **demo_user**: strong_password_123!

5. **Actualizar configuración de servidores MCP**
   
   Editar `servers_config.json` para que coincida con los endpoints de tus servidores MCP:
   ```json
   {
     "mcpServers": {
       "Yahoo Finance": {
         "transport": "sse",
         "url": "http://mcpserver3:8002/sse",
         "timeout": 600,
         "headers": null,
         "sse_read_timeout": 900
       },
       "Neo4j": {
         "transport": "sse",
         "url": "http://mcpserver4:8003/sse",
         "timeout": 600,
         "headers": null,
         "sse_read_timeout": 900
       },
       "HubSpot": {
         "transport": "sse",
         "url": "http://mcpserver5:8004/sse",
         "timeout": 600,
         "headers": null,
         "sse_read_timeout": 900
       }
     }
   }
   ```

6. **Ejecutar la aplicación**
   ```bash
   # Modo HTTP estándar
   streamlit run app.py
   
   # O con SSL habilitado
   SSL_ENABLED=true python start_streamlit.py
   ```

### Despliegue Docker

1. **Construir la imagen Docker**
   ```bash
   docker build -t mcp-client .
   ```

2. **Ejecutar con variables de entorno**
   ```bash
   # Modo HTTP
   docker run -p 8501:8501 \
     -e OPENAI_API_KEY=tu_clave \
     -v $(pwd)/.env:/app/.env \
     -v $(pwd)/keys:/app/keys \
     mcp-client
   
   # Modo HTTPS
   docker run -p 8501:8501 -p 8502:8502 \
     -e OPENAI_API_KEY=tu_clave \
     -e SSL_ENABLED=true \
     -v $(pwd)/.env:/app/.env \
     -v $(pwd)/keys:/app/keys \
     -v $(pwd)/ssl:/app/ssl \
     mcp-client
   ```

3. **Generación de Certificados SSL** (automática en Docker)
   ```bash
   # Los certificados se generan automáticamente cuando SSL_ENABLED=true
   # O generar manualmente:
   python generate_ssl_certificate.py
   # O usando script shell:
   ./generate_ssl_certificate.sh
   ```

## 🎯 Uso

### Primeros Pasos

1. **Lanzar la aplicación**
   - HTTP: `http://localhost:8501`
   - HTTPS: `https://localhost:8502` (si SSL está habilitado)

2. **Autenticarse**:
   - Usar el panel de autenticación de la barra lateral
   - Iniciar sesión con credenciales por defecto:
     - Usuario: `admin` / Contraseña: `very_Secure_p@ssword_123!`
     - Usuario: `juan` / Contraseña: `Larisa1000@`
     - Usuario: `giovanni_romero` / Contraseña: `MrRomero2024!`
     - Usuario: `demo_user` / Contraseña: `strong_password_123!`
   - Ver mensaje de bienvenida e información de sesión de usuario

3. **Configurar tu proveedor de IA** (pestaña Configuración):
   - Seleccionar entre OpenAI o Azure OpenAI
   - Verificar que las credenciales estén cargadas (marca verde indica éxito)
   - Ajustar parámetros del modelo (temperatura: 0.0-1.0, tokens máx: 1024-10240)

4. **Conectar a servidores MCP** (pestaña Conexiones):
   - Hacer clic en "Conectar a Servidores MCP"
   - Verificar conexiones exitosas (muestra conteo de herramientas disponibles)
   - Verificar estado de salud de servidores individuales
   - Monitorear métricas de conexión y rendimiento

5. **Explorar herramientas disponibles** (pestaña Herramientas):
   - Navegar herramientas por categoría: Yahoo Finance, Neo4j, HubSpot
   - Ver documentación detallada de herramientas y parámetros
   - Buscar herramientas específicas por nombre o descripción
   - Entender requisitos de herramientas y ejemplos de uso

6. **Comenzar a chatear** (pestaña Chat):
   - Hacer preguntas sobre mercados financieros, bases de datos o datos CRM
   - La IA selecciona y usa automáticamente las herramientas apropiadas
   - Ver historial detallado de ejecución de herramientas
   - Monitorear contexto y memoria de conversación

### Consultas de Ejemplo

**Operaciones de Análisis Financiero:**
```
"¿Cuál es la puntuación MACD actual para AAPL?"
"Calcula la estrategia Bollinger-Fibonacci para las acciones de Tesla durante 1 año"
"Dame una puntuación de análisis técnico combinado para Microsoft usando múltiples indicadores"
"Compara señales de trading para AAPL, TSLA y MSFT"
```

**Operaciones de Base de Datos Neo4j:**
```
"Muéstrame el esquema completo de la base de datos y explica la estructura"
"¿Cuántos visitantes se convirtieron en clientes este año?"
"Encuentra todas las relaciones entre nodos de persona y nodos de empresa"
"Crea un nuevo nodo de persona con nombre 'Alice' y enlázalo a una empresa existente"
"Valida esta consulta Cypher contra el esquema actual"
```

**Operaciones CRM HubSpot:**
```
"Obtén mis detalles de usuario de HubSpot y permisos"
"Muéstrame todos los contactos creados este mes con su historial de compromiso"
"Encuentra empresas en la industria tecnológica y sus ofertas asociadas"
"Crea un nuevo contacto y empresa, luego asócialos juntos"
"Lista todas las ofertas abiertas por encima de $10,000 y genera enlaces de HubSpot para verlas"
"Agrega una tarea de seguimiento para la oferta de Amazon y rastrea su progreso"
```

**Flujos de Trabajo Avanzados Multi-Sistema:**
```
"Analiza el rendimiento de las acciones de AAPL y crea una tarea de HubSpot para revisar nuestras inversiones tecnológicas"
"Compara datos de clientes entre nuestra base de datos Neo4j y CRM HubSpot"
"Encuentra ofertas de alto valor en HubSpot y haz referencia cruzada con relaciones de base de datos de grafos"
"Crea un reporte integral combinando análisis financiero, insights de base de datos y datos CRM"
```

### Configuración Avanzada

**Parámetros del Modelo:**
- **Temperatura**: Controla la creatividad y aleatoriedad de la respuesta (0.0 = determinista, 1.0 = creativo)
- **Tokens Máximos**: Establece límite de longitud de respuesta (1024-10240 tokens)
- **Selección de Proveedor**: Cambio dinámico entre OpenAI y Azure OpenAI

**Gestión de Chat:**
- **Nuevas Conversaciones**: Crear sesiones de chat frescas con "Nuevo Chat"
- **Acceso al Historial**: Navegar y cambiar entre conversaciones previas
- **Gestión de Contexto**: Cada conversación mantiene su propia memoria y contexto
- **Aislamiento de Sesión**: Las conversaciones están aisladas por usuario autenticado

**Gestión de Sesión de Usuario:**
- **Seguimiento de Sesión**: Monitorear tiempo de inicio de sesión y duración de sesión
- **Monitoreo de Actividad**: Rastrear uso de herramientas y patrones de conversación
- **Cierre de Sesión Seguro**: Limpieza apropiada de sesión y seguridad
- **Soporte Multi-Usuario**: Datos y sesiones separados para cada usuario autenticado

## 🏗️ Arquitectura

```
┌───────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   UI Streamlit    │    │   Agente         │    │   Servidores MCP    │
│                   │◄──►│   LangChain      │◄──►│                     │
│  - Autenticación  │    │  - Enrutamiento  │    │  - Yahoo Finance    │
│  - Interfaz Chat  │    │    Herramientas  │    │  - Base Datos Neo4j │
│  - Panel Config   │    │  - Proveedor LLM │    │  - CRM HubSpot      │
│  - Visualización  │    │  - Gestión Mem.  │    │  - Herramientas     │
│    Herramientas   │    │  - Consciente    │    │    Personalizadas   │
│  - Gestión Sesión │    │    Contexto      │    │                     │
└───────────────────┘    └──────────────────┘    └─────────────────────┘
```

### Componentes Clave

- **`app.py`**: Aplicación principal Streamlit con middleware de autenticación
- **`services/`**: Lógica de negocio central (servicios IA, gestión MCP, servicios Chat)
- **`ui_components/`**: Componentes UI reutilizables (pestañas, barra lateral, componentes principales)
- **`utils/`**: Funciones de ayuda (manejadores async, análisis herramientas, prompts IA)
- **`config.py`**: Gestión de configuración centralizada
- **`simple_generate_password.py`**: Generación y gestión de credenciales de usuario

### Sistema de Autenticación

- **Seguridad de Contraseñas**: Hash bcrypt con salt para almacenamiento seguro de credenciales
- **Gestión de Sesiones**: Integración streamlit-authenticator con sesiones persistentes
- **Seguridad de Cookies**: Cookies seguras, HTTPOnly con expiración configurable
- **Control de Acceso**: Dominios de email pre-autorizados con validación de usuario
- **Soporte Multi-Usuario**: Aislamiento completo de usuario con historiales de conversación separados

### Soporte SSL/TLS

- **Generación de Certificados**: Creación automática de certificados auto-firmados
- **Servidor HTTPS**: Modo HTTPS Streamlit con configuración SSL apropiada
- **Multi-Plataforma**: Generación de certificados basada en Python para compatibilidad
- **Listo para Producción**: Configuraciones SSL configurables para despliegue en producción

## 🔧 Configuración

### Proveedores de Modelo

La aplicación soporta múltiples proveedores de IA configurados en `config.py`:

```python
MODEL_OPTIONS = {
    'OpenAI': 'gpt-4o',
    'Azure OpenAI': 'o3-mini',  # Usando deployment del entorno
}
```

### Gestión de Usuarios

Las credenciales de usuario se gestionan en `keys/config.yaml`. Para agregar/modificar usuarios:

1. **Editar el script de generación de contraseñas**:
   ```python
   # Editar simple_generate_password.py
   users = {
       'nuevo_usuario': {
           'password': 'contraseña_segura_123!',
           'name': 'Nombre Nuevo Usuario',
           'email': 'usuario@empresa.com'
       }
   }
   ```

2. **Generar nueva configuración**:
   ```bash
   python simple_generate_password.py
   ```

3. **Reiniciar la aplicación** para cargar nuevos usuarios

### Configuración de Servidores MCP

Los endpoints de servidor se definen en `servers_config.json`. Cada servidor requiere:
- **transport**: Método de conexión (típicamente "sse")
- **url**: URL endpoint del servidor con protocolo y puerto apropiados
- **timeout**: Timeout de conexión en segundos
- **sse_read_timeout**: Timeout de eventos enviados por servidor para operaciones de larga duración

### Configuración SSL

SSL se configura a través de variables de entorno y archivos de certificado:

```env
# Habilitar modo SSL/HTTPS
SSL_ENABLED=true
```

Los certificados se generan automáticamente en el directorio `ssl/`:
- `ssl/cert.pem` - Certificado SSL
- `ssl/private.key` - Clave privada (permisos seguros)

### Estilos y Temas

CSS personalizado se encuentra en `.streamlit/style.css` para personalización de UI:
- **Diseño Moderno**: UI contemporánea con soporte de tema oscuro/claro
- **Layout Responsivo**: Diseño amigable móvil con layouts adaptativos
- **Elementos Interactivos**: Efectos hover, animaciones y transiciones suaves
- **Accesibilidad**: Ratios de alto contraste y marcado semántico

## 🔒 Características de Seguridad

### Seguridad de Autenticación
- **Cifrado Empresarial**: Hash de contraseñas bcrypt con rondas de salt configurables
- **Seguridad de Sesión**: Tokens de sesión seguros con expiración configurable
- **Protección de Cookies**: Atributos de cookie HTTPOnly, Secure y SameSite
- **Control de Acceso**: Autorización basada en dominio y validación de usuario
- **Protección Fuerza Bruta**: Limitación de tasa y mecanismos de bloqueo de cuenta

### Seguridad API y Datos
- **Variables de Entorno**: Almacenamiento seguro de credenciales fuera del repositorio de código
- **Validación de Tokens**: Verificación de clave API en tiempo real y verificaciones de salud
- **Sanitización de Entrada**: Protección integral XSS e inyección
- **Manejo de Errores**: Mensajes de error seguros sin exposición de datos sensibles
- **Cifrado SSL/TLS**: Cifrado de extremo a extremo para datos en tránsito

### Seguridad de Sesión y Usuario
- **Aislamiento de Usuario**: Separación completa de datos de usuario y conversaciones
- **Seguimiento de Sesión**: Logging detallado de actividad de usuario y patrones de acceso
- **Limpieza Automática**: Gestión y limpieza segura de datos de sesión
- **Protección Entre Sesiones**: Prevención de secuestro de sesión y ataques CSRF

## 🐛 Solución de Problemas

### Problemas de Autenticación

**Problemas de Inicio de Sesión:**
- Verificar que `keys/config.yaml` exista y esté formateado apropiadamente
- Verificar que las credenciales de usuario coincidan con las contraseñas generadas
- Asegurar que los dominios de email están en la lista pre-autorizada
- Limpiar cookies del navegador si se experimentan problemas persistentes de inicio de sesión

**Problemas de Sesión:**
- Verificar configuración de cookie de sesión y configuraciones de expiración
- Verificar que la clave de autenticación coincida entre sesiones
- Monitorear estado de sesión en herramientas de desarrollador del navegador

### Problemas de Conexión

**Conexión Servidor MCP:**
- Verificar que todos los servidores MCP estén ejecutándose y accesibles
- Verificar `servers_config.json` para URLs y puertos correctos del servidor
- Probar endpoints de salud de servidor individuales
- Monitorear estado de contenedor Docker con `docker-compose ps`

**Problemas de Red:**
- Asegurar conectividad de red apropiada entre contenedores
- Verificar configuraciones de firewall que no bloqueen puertos requeridos
- Verificar resolución DNS para nombres de host de servidor

### Problemas SSL/HTTPS

**Problemas de Certificado:**
- Verificar que los certificados SSL estén generados apropiadamente en el directorio `ssl/`
- Verificar validez y fechas de expiración de certificado
- Asegurar permisos de archivo apropiados en clave privada (600)

**Advertencias de Seguridad del Navegador:**
- Aceptar advertencias de certificado auto-firmado en navegador
- Agregar excepción de certificado para desarrollo localhost
- Usar modo HTTP si problemas SSL persisten en desarrollo

### Problemas de Clave API

**Configuración OpenAI:**
- Confirmar que `OPENAI_API_KEY` está establecida en variables de entorno
- Probar validez de clave API a través del panel OpenAI
- Verificar límites y cuotas de uso API

**Configuración Azure OpenAI:**
- Verificar que las cuatro variables de entorno Azure están establecidas
- Probar accesibilidad de endpoint y nombre de deployment
- Confirmar compatibilidad de versión API

### Errores de Ejecución de Herramientas

**Fallos de Validación de Esquema:**
- Siempre llamar `get_neo4j_schema` antes de operaciones de base de datos
- Iniciar flujos de trabajo HubSpot con `hubspot-get-user-details`
- Verificar historial de ejecución de herramientas para información de error detallada

**Errores de Permisos:**
- Verificar que el token HubSpot tiene scopes y permisos requeridos
- Verificar autenticación de base de datos Neo4j y derechos de acceso
- Monitorear limitación de tasa y uso de cuota API

### Problemas de Rendimiento

**Tiempos de Respuesta Lentos:**
- Monitorear tiempo de ejecución de herramientas en los paneles de depuración
- Verificar latencia de red a APIs externas
- Optimizar complejidad de consulta y volumen de datos

**Uso de Memoria:**
- Monitorear utilización de recursos de contenedor Docker
- Limpiar historial de conversación si el uso de memoria es alto
- Reiniciar contenedores periódicamente para rendimiento óptimo

### Modo Debug

Habilitar depuración integral por:
1. Usar el expansor "Historial de Ejecución de Herramientas" en la pestaña Chat
2. Verificar consola del navegador para errores JavaScript y problemas de red
3. Monitorear logs Streamlit en terminal para errores del lado del servidor
4. Revisar logs de autenticación para problemas de inicio de sesión y sesión

## 🔄 Gestión de Usuarios

### Agregar Nuevos Usuarios

1. **Editar el script de generación de contraseñas**:
   ```bash
   nano simple_generate_password.py
   # Agregar nuevos usuarios al diccionario users con contraseñas seguras
   ```

2. **Generar nueva configuración**:
   ```bash
   python simple_generate_password.py
   ```

3. **Reiniciar la aplicación** para cargar nuevas cuentas de usuario

### Gestionar Usuarios Existentes

- **Actualizaciones de Contraseña**: Regenerar `config.yaml` con nuevas contraseñas
- **Cambios de Email**: Modificar información de usuario en el script de generación
- **Gestión de Acceso**: Agregar/quitar emails de la lista pre-autorizada
- **Cambios de Rol**: Actualizar nombres de usuario y niveles de acceso

### Administración de Sesión

- **Sesiones Activas**: Monitorear sesiones de usuario actuales en la barra lateral
- **Configuración de Sesión**: Ajustar tiempos de expiración en `config.yaml`
- **Políticas de Seguridad**: Configurar configuraciones de cookie y parámetros de seguridad
- **Actividad de Usuario**: Rastrear tiempos de inicio de sesión y uso de conversación

## 🔄 Historial de Versiones

- **v2.0.0**: Sistema de autenticación empresarial, soporte SSL, UI mejorada con pestañas
- **v1.5.0**: Soporte IA multi-proveedor, integración de herramientas integral
- **v1.0.0**: Lanzamiento inicial con integración MCP básica e interfaz chat

## 🤝 Contribuir

### Directrices de Desarrollo

1. **Seguridad Primero**: Siempre seguir patrones de autenticación al agregar características
2. **Pruebas Multi-Usuario**: Probar con múltiples cuentas de usuario para asegurar aislamiento apropiado
3. **Compatibilidad SSL**: Asegurar que nuevas características funcionen en modos HTTP y HTTPS
4. **Documentación**: Actualizar README y documentación en línea para nuevas características

### Consideraciones de Seguridad

- Nunca loggear o exponer contraseñas de usuario, tokens de sesión o claves API
- Validar todas las entradas de usuario para vulnerabilidades de seguridad y ataques de inyección
- Seguir prácticas de codificación segura para flujos de autenticación y gestión de sesión
- Probar casos extremos de autenticación, condiciones de error y límites de seguridad

### Procedimientos de Prueba

- **Pruebas de Autenticación**: Verificar flujos de inicio/cierre de sesión para todos los tipos de usuario
- **Pruebas de Sesión**: Probar persistencia, expiración y aislamiento de sesión
- **Pruebas SSL**: Verificar funcionalidad HTTPS y manejo de certificados
- **Pruebas Multi-Usuario**: Asegurar separación apropiada de datos entre usuarios
- **Integración de Herramientas**: Probar todas las conexiones de servidor MCP y funcionalidad de herramientas

---

**Versión**: 2.0.0  
**Última Actualización**: Junio 2025  
**Seguridad**: Streamlit Authenticator 0.3.2, hash contraseñas bcrypt, soporte SSL/TLS  
**Compatibilidad**: Python 3.11+, Streamlit 1.44+, Docker 20+  
**Autenticación**: Gestión de usuarios grado empresarial con aislamiento de sesión