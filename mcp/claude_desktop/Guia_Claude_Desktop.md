# Guía de Documentación de la Aplicación de Escritorio Claude

## Tabla de Contenidos
1. [Introducción](#introducción)
2. [Requisitos del Sistema](#requisitos-del-sistema)
3. [Guía de Instalación](#guía-de-instalación)
4. [Primeros Pasos](#primeros-pasos)
5. [Funciones Principales](#funciones-principales)
6. [Protocolo de Contexto de Modelo (MCP)](#protocolo-de-contexto-de-modelo-mcp)
7. [Funcionalidad de Proyectos](#funcionalidad-de-proyectos)
8. [Navegación de la Interfaz](#navegación-de-la-interfaz)
9. [Versión de Escritorio vs Web](#versión-de-escritorio-vs-web)
10. [Configuración y Ajustes](#configuración-y-ajustes)
11. [Mejores Prácticas](#mejores-prácticas)
12. [Solución de Problemas](#solución-de-problemas)

## Introducción

La aplicación de escritorio Claude es un cliente nativo que lleva las capacidades de Claude AI directamente a tu escritorio con rendimiento mejorado, soporte del Protocolo de Contexto de Modelo (MCP) y funciones avanzadas de productividad. Disponible para Windows y macOS, ofrece un flujo de trabajo más integrado y eficiente comparado con la versión web.

## Requisitos del Sistema

### Windows
- **Sistema Operativo**: Windows 10 (64-bit) o posterior
- **Procesador**: CPU multinúcleo moderno (8+ núcleos recomendado)
- **Memoria**: Mínimo 16 GB RAM (32 GB+ recomendado)
- **Almacenamiento**: SSD con al menos 100 GB de espacio libre
- **Gráficos**: GPU NVIDIA con soporte CUDA recomendado
- **Dependencias**: Node.js requerido para funcionalidad MCP

### macOS
- **Sistema Operativo**: macOS 11 (Big Sur) o posterior
- **Procesador**: Apple Silicon o Intel (ambos compatibles)
- **Memoria**: 16 GB RAM mínimo (32 GB+ recomendado)
- **Almacenamiento**: SSD con 100 GB+ de espacio libre
- **Dependencias**: Node.js para servidores MCP

### Linux (Soporte Comunitario)
- **Nota**: Sin soporte oficial de Anthropic
- **Distribuciones**: Ubuntu 20.04 LTS+, Debian 10+, Fedora, Arch Linux
- **Disponible a través de**: Scripts de construcción mantenidos por la comunidad

## Guía de Instalación

### Instalación en Windows

1. **Descargar el instalador**
   - Visita [claude.ai/download](https://claude.ai/download)
   - Descarga el instalador de Windows (típicamente "ClaudeSetup.exe")

2. **Ejecutar la instalación**
   ```
   - Hacer doble clic en el instalador
   - Seguir el asistente de instalación
   - Elegir directorio de instalación
   - Completar la instalación
   ```

3. **Iniciar y acceder**
   - Encontrar Claude en el menú Inicio
   - Iniciar sesión con tu cuenta de Claude

### Instalación en macOS

1. **Descargar la aplicación**
   - Visita [claude.ai/download](https://claude.ai/download)
   - Descarga la imagen de disco de macOS ("Claude.dmg")

2. **Instalar la aplicación**
   ```
   - Hacer doble clic en el archivo .dmg
   - Arrastrar Claude a la carpeta Aplicaciones
   - Desmontar la imagen de disco
   ```

3. **Primer inicio**
   - Abrir desde la carpeta Aplicaciones
   - Puede necesitar aprobación en Preferencias del Sistema > Seguridad y Privacidad
   - Habilitar acceso al micrófono para funciones de voz

### Instalación en Linux (Comunidad)

**Debian/Ubuntu:**
```bash
# Clonar repositorio
git clone https://github.com/aaddrick/claude-desktop-debian.git
cd claude-desktop-debian

# Construir e instalar
./build.sh
sudo dpkg -i ./claude-desktop_VERSION_ARCHITECTURE.deb
sudo apt --fix-broken install
```

## Primeros Pasos

### Configuración Inicial

1. **Iniciar sesión** con tu cuenta de Claude
2. **Elegir tu modelo predeterminado** (Sonnet, Haiku, u Opus)
3. **Configurar preferencias**:
   - Tema (modo oscuro/claro)
   - Atajos de teclado
   - Configuración de privacidad

### Navegación Básica

- **Área de chat principal**: Interfaz central de conversación
- **Barra lateral**: Proyectos, historial de chat y navegación
- **Área de entrada**: Entrada de texto con acceso a herramientas
- **Configuración**: Accedida a través del menú Claude (no configuración en la aplicación)

## Funciones Principales

### Capacidades Esenciales

- **Soporte multi-modelo**: Claude 3.5 Sonnet, Haiku y Opus
- **Manejo de archivos**: Cargar documentos, imágenes, PDFs (hasta 30MB)
- **Artefactos**: Generar y refinar contenido interactivo
- **Dictado por voz**: Hablar a Claude usando el micrófono
- **Proyectos**: Organizar conversaciones con contexto persistente
- **Herramienta de análisis**: Ejecutar código para cálculos
- **Herramienta de captura de pantalla**: Capturar imágenes de la pantalla

### Atajos de Teclado

- **Atajo global**:
  - macOS: `Option + Espacio`
  - Windows: `Ctrl + Alt + Espacio`
- **Nuevo chat**: `Ctrl/Cmd + K`
- **Enviar mensaje**: `Enter`
- **Nueva línea**: `Shift + Enter`

## Protocolo de Contexto de Modelo (MCP)

### ¿Qué es MCP?

MCP es un estándar abierto que permite comunicación segura entre Claude y herramientas externas. Piénsalo como un "puerto USB para IA" - proporciona conexiones estandarizadas a varias fuentes de datos y herramientas.

### Configurar MCP

1. **Prerrequisitos**
   - Node.js versión 16 o superior
   - Última versión de Claude Desktop

2. **Acceder a la configuración**
   ```
   Menú Claude → Configuración → Desarrollador → Editar Config
   ```

3. **Ubicación del archivo de configuración**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Configuración Básica de MCP

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/username/Desktop",
        "/Users/username/Documents"
      ]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "tu_token_aquí"
      }
    }
  }
}
```

### Servidores MCP Disponibles

**Servidores Oficiales:**
- Filesystem - Operaciones de archivos locales
- GitHub - Gestión de repositorios
- Slack - Comunicación de equipo
- Google Drive - Acceso a almacenamiento en la nube
- PostgreSQL - Operaciones de base de datos
- Puppeteer - Automatización de navegador

**Servidores Comunitarios:**
- AWS, Docker, MongoDB, Notion, Discord, Firebase, Kubernetes, y más

### Usar Funciones MCP

1. **Descubrimiento de herramientas**: Buscar el ícono de control deslizante en el área de entrada
2. **Solicitudes de permisos**: Claude pregunta antes de ejecutar herramientas
3. **Comandos de ejemplo**:
   - "Crear un nuevo archivo llamado notas.txt"
   - "Mostrar commits recientes en mi repositorio"
   - "Buscar en mi Google Drive documentos del proyecto"

## Funcionalidad de Proyectos

### Crear Proyectos (Solo Pro/Team/Enterprise)

1. Hacer clic en **"Proyectos"** en la esquina superior izquierda
2. Seleccionar **"Nuevo Proyecto"**
3. Proporcionar nombre y descripción
4. Establecer visibilidad (Solo planes Team)

### Funciones de Proyecto

- **Ventana de contexto de 200K tokens** (~500 páginas)
- **Instrucciones personalizadas**: Definir comportamiento de Claude por proyecto
- **Base de conocimiento**: Cargar y gestionar documentos
- **Contexto persistente**: Mantiene historial de conversación
- **Colaboración en equipo**: Compartir proyectos con miembros del equipo

### Gestionar Base de Conocimiento

1. **Agregar contenido** mediante el botón "Agregar Contenido"
2. **Formatos compatibles**: PDF, DOCX, CSV, TXT, HTML, RTF, EPUB
3. **Límite de tamaño de archivo**: 30MB por archivo
4. **Modo RAG automático**: Se activa al acercarse a los límites de tokens

### Ejemplo de Instrucciones Personalizadas

```
Rol: Desarrollador Senior de Python
Enfoque: Código limpio y eficiente con documentación integral
Estilo: Profesional pero accesible
Salida: Incluir type hints y docstrings
```

## Navegación de la Interfaz

### Diseño Principal

```
┌─────────────┬──────────────────────┬─────────────┐
│ Barra Lat.  │     Área de Chat     │   Panel de  │
│             │                      │ Conocimiento│
│ • Proyectos │   Conversación       │             │
│ • Historial │                      │ • Documentos│
│ • Favoritos │                      │ • Config.   │
└─────────────┴──────────────────────┴─────────────┘
                [Área de Entrada con Herramientas]
```

### Elementos Clave de la Interfaz

- **Control deslizante de herramientas**: Parte inferior izquierda de entrada (cuando MCP está configurado)
- **Selector de proyecto**: Menú desplegable en interfaz de chat principal
- **Menú de tres puntos**: Configuración y opciones de proyecto
- **Ícono de estrella**: Favoritos rápidos de proyecto
- **Feed de actividad**: Actualizaciones de colaboración en equipo

## Versión de Escritorio vs Web

### Ventajas del Escritorio

| Función | Escritorio | Web |
|---------|------------|-----|
| Integración MCP | ✓ | ✗ |
| Rendimiento Nativo | ✓ | ✗ |
| Integración del Sistema | ✓ | ✗ |
| Preparación Sin Conexión | ✓ | ✗ |
| Atajos Globales | ✓ | ✗ |
| Acceso al Sistema de Archivos | ✓ | Limitado |

### Limitaciones del Escritorio

- Sin función Computer Use (solo web/API)
- Limitado a Windows/macOS oficialmente
- Mismos modelos centrales de IA que la web

## Configuración y Ajustes

### Acceder a la Configuración

- **Windows**: `Ctrl + ,`
- **macOS**: `Cmd + ,`
- **Configuración de desarrollador**: Menú Claude → Configuración → Desarrollador

### Opciones de Configuración

```json
{
  "mcpServers": {
    // Configuraciones de servidor MCP
  },
  "theme": "dark",
  "shortcuts": {
    "globalHotkey": "Alt+Space"
  },
  "privacy": {
    "optOutTraining": true
  }
}
```

### Configuración de Seguridad

- **Restricciones de acceso a archivos**: Limitar MCP a directorios específicos
- **Gestión de claves API**: Almacenar de forma segura en configuración
- **Controles de permisos**: Aprobación explícita para operaciones
- **Aislamiento del entorno**: Servidores MCP ejecutados en sandbox

## Mejores Prácticas

### Uso Efectivo

1. **Selección de Modelo**
   - Usar Haiku para tareas simples
   - Usar Sonnet para rendimiento equilibrado
   - Usar Opus para razonamiento complejo

2. **Ingeniería de Prompts**
   - Ser específico y claro
   - Usar etiquetas XML para estructura
   - Proporcionar contexto en Proyectos

3. **Integración MCP**
   - Comenzar con acceso al sistema de archivos
   - Agregar servidores gradualmente
   - Monitorear impacto en el rendimiento

### Optimización del Flujo de Trabajo

- **Agrupar tareas relacionadas** para eficiencia
- **Usar atajos de teclado** para velocidad
- **Organizar con Proyectos** para contexto
- **Crear plantillas** para patrones comunes

### Consejos de Rendimiento

- **Cerrar aplicaciones innecesarias** para liberar recursos
- **Limitar servidores MCP concurrentes**
- **Limpiar caché regularmente**
- **Actualizar dependencias** frecuentemente

## Solución de Problemas

### Problemas Comunes y Soluciones

#### Problemas de Instalación

**Problema**: La aplicación no se inicia
```
Soluciones:
- Verificar compatibilidad del SO
- Actualizar a la última versión del SO
- Verificar requisitos del sistema
- Ejecutar como Administrador (Windows)
```

**Problema**: Bloqueo de seguridad de macOS
```
Solución:
Preferencias del Sistema → Seguridad y Privacidad → General → "Abrir de Todos Modos"
```

#### Problemas de Conexión MCP

**Problema**: Los servidores MCP no se conectan
```
Soluciones:
1. Verificar instalación de Node.js: node --version
2. Verificar sintaxis del archivo de configuración (JSON válido)
3. Usar rutas absolutas en la configuración
4. Reiniciar Claude después de cambios de configuración
5. Verificar logs en configuración de Desarrollador
```

#### Problemas de Rendimiento

**Problema**: Rendimiento lento
```
Soluciones:
- Verificar recursos del sistema (RAM/CPU)
- Reducir número de servidores MCP activos
- Limpiar caché de la aplicación
- Actualizar a la última versión
```

### Mensajes de Error

| Error | Solución |
|-------|----------|
| "MCP server failed to start" | Verificar instalación de Node.js y rutas |
| "Invalid configuration" | Validar sintaxis JSON en archivo de configuración |
| "Permission denied" | Otorgar permisos necesarios del sistema de archivos |
| "Token limit exceeded" | Reducir tamaño de base de conocimiento del proyecto |

### Obtener Ayuda

- **Soporte oficial**: status.anthropic.com
- **Comunidad**: r/ClaudeAI, r/AnthropicAI
- **Documentación**: Guías oficiales de inicio rápido
- **Logs**: Configuración de desarrollador → Ver logs

---

Esta guía de documentación proporciona cobertura integral de la aplicación de escritorio Claude. Para las últimas actualizaciones y funciones, siempre consulta la documentación oficial de Anthropic y las notas de lanzamiento.