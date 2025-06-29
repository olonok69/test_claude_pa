# Servidor MCP Cypher Neo4j

Un servidor del Protocolo de Contexto de Modelo (MCP) que proporciona herramientas para interactuar con bases de datos de grafos Neo4j a través de consultas Cypher. Este servidor permite que asistentes de IA y aplicaciones lean, escriban y analicen datos en bases de datos Neo4j con validación apropiada de esquemas y gestión de conexiones.

## Características

- **Descubrimiento de Esquema**: Recupera y comprende automáticamente la estructura de la base de datos Neo4j
- **Operaciones de Lectura**: Ejecuta consultas MATCH seguras para recuperación de datos
- **Operaciones de Escritura**: Realiza operaciones CREATE, MERGE, SET, DELETE
- **Validación de Consultas**: Valida consultas contra el esquema de la base de datos para prevenir errores
- **Gestión de Conexiones**: Manejo robusto de conexiones asíncronas con manejo apropiado de errores
- **Monitoreo de Salud**: Endpoint de verificación de salud integrado para monitoreo
- **Compatible con MCP**: Implementa el Protocolo de Contexto de Modelo para integración con asistentes de IA

## Prerrequisitos

- Python 3.11+
- Base de datos Neo4j (local o remota)
- Plugin APOC instalado en Neo4j (requerido para descubrimiento de esquema)
- Docker (opcional, para despliegue contenerizado)

## Instalación

### Desarrollo Local

1. Clonar el repositorio y navegar al directorio del servidor:
```bash
cd servers/server4
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Crear un archivo `.env` con los detalles de conexión de Neo4j:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=tu_contraseña
NEO4J_DATABASE=neo4j
```

4. Ejecutar el servidor:
```bash
python main.py
```

### Despliegue Docker

1. Construir la imagen Docker:
```bash
docker build -t neo4j-mcp-server .
```

2. Ejecutar el contenedor:
```bash
docker run -p 8003:8003 \
  -e NEO4J_URI=bolt://tu-host-neo4j:7687 \
  -e NEO4J_USERNAME=neo4j \
  -e NEO4J_PASSWORD=tu_contraseña \
  -e NEO4J_DATABASE=neo4j \
  neo4j-mcp-server
```

## Configuración

### Variables de Entorno

| Variable | Descripción | Por Defecto |
|----------|-------------|-------------|
| `NEO4J_URI` | URI de conexión Neo4j | `bolt://localhost:7687` |
| `NEO4J_USERNAME` | Nombre de usuario Neo4j | `neo4j` |
| `NEO4J_PASSWORD` | Contraseña Neo4j | `password` |
| `NEO4J_DATABASE` | Nombre de base de datos Neo4j | `neo4j` |

### Configuración Neo4j

Asegurar que el plugin APOC esté instalado y habilitado en tu instancia Neo4j:

1. Para Neo4j Desktop: Instalar APOC a través de la pestaña plugins
2. Para Neo4j Server: Agregar jar APOC al directorio plugins
3. Para Neo4j Docker: Usar la imagen `neo4j/neo4j:latest` con APOC pre-instalado

## Endpoints API

### Herramientas MCP

El servidor expone tres herramientas MCP principales:

#### 1. `get_neo4j_schema`
**Paso requerido primero** - Recupera el esquema completo de la base de datos incluyendo etiquetas de nodos, propiedades y relaciones.

```python
# Retorna estructura JSON con:
{
  "label": "TipoNodo",
  "attributes": {"propiedad": "tipo"},
  "relationships": {"relacion": "NodoDestino"}
}
```

#### 2. `read_neo4j_cypher`
Ejecuta consultas Cypher de solo lectura (operaciones MATCH).

**Parámetros:**
- `query` (string): La consulta Cypher a ejecutar
- `params` (dict, opcional): Parámetros de consulta

**Ejemplo:**
```cypher
MATCH (n:Person {name: $name}) RETURN n
```

#### 3. `write_neo4j_cypher`
Ejecuta consultas Cypher de escritura (operaciones CREATE, MERGE, SET, DELETE).

**Parámetros:**
- `query` (string): La consulta Cypher a ejecutar
- `params` (dict, opcional): Parámetros de consulta

**Ejemplo:**
```cypher
CREATE (p:Person {name: $name, age: $age}) RETURN p
```

### Endpoints HTTP

- **Verificación de Salud**: `GET /health` - Verificar estado del servidor y conexión Neo4j
- **Endpoint SSE**: `GET /sse` - Server-Sent Events para comunicación MCP
- **Manejador de Mensajes**: `POST /messages/` - Manejar mensajes de protocolo MCP

## Ejemplos de Uso

### Flujo de Trabajo Básico

1. **Obtener Esquema** (Siempre primero):
```python
esquema = await get_neo4j_schema()
```

2. **Leer Datos**:
```python
resultado = await read_neo4j_cypher(
    query="MATCH (p:Person) RETURN p.name, p.age LIMIT 10",
    params={}
)
```

3. **Escribir Datos**:
```python
resultado = await write_neo4j_cypher(
    query="CREATE (p:Person {name: $name, age: $age})",
    params={"name": "Juan Pérez", "age": 30}
)
```

### Patrones de Consulta Comunes

**Encontrar todos los tipos de nodo:**
```cypher
MATCH (n) RETURN DISTINCT labels(n) as tipos_nodo
```

**Obtener conteos de nodos:**
```cypher
MATCH (n) RETURN labels(n) as etiqueta, count(n) as conteo
```

**Encontrar relaciones:**
```cypher
MATCH (a)-[r]->(b) 
RETURN type(r) as relacion, labels(a) as nodo_origen, labels(b) as nodo_destino 
LIMIT 10
```

## Manejo de Errores

El servidor incluye manejo integral de errores:

- **Errores de Conexión**: Reintentos automáticos y logging detallado
- **Validación de Consultas**: Verificaciones para etiquetas y propiedades inválidas
- **Validación de Esquema**: Asegura que las consultas usen la estructura existente de la base de datos
- **Seguridad de Tipos**: Valida tipos de consulta (operaciones de lectura vs escritura)

## Logging

El servidor usa logging estructurado con los siguientes niveles:
- `INFO`: Información general de operación
- `ERROR`: Condiciones de error y stack traces
- Detalles de estado de conexión y ejecución de consultas

Formato de log: `YYYY-MM-DD HH:MM:SS | NIVEL | MENSAJE`

## Monitoreo de Salud

Monitorear la salud del servidor usando el endpoint `/health`:

```bash
curl http://localhost:8003/health
```

La respuesta incluye:
- Estado del servidor
- Salud de conexión Neo4j
- Nombre de la base de datos
- Detalles de error (si los hay)

## Integración con Asistentes de IA

Este servidor implementa el Protocolo de Contexto de Modelo (MCP), haciéndolo compatible con:
- Claude Desktop
- Otros asistentes de IA compatibles con MCP
- Aplicaciones personalizadas usando clientes MCP

### Configuración Cliente MCP

Agregar a la configuración de tu cliente MCP:
```json
{
  "mcpServers": {
    "neo4j-cypher": {
      "command": "python",
      "args": ["main.py"],
      "cwd": "/ruta/a/servers/server4"
    }
  }
}
```

## Consideraciones de Seguridad

- Usar contraseñas fuertes para Neo4j
- Restringir acceso de red a puertos Neo4j
- Validar todas las consultas de entrada
- Monitorear ejecución de consultas para rendimiento
- Usar conexiones de solo lectura donde sea apropiado
- Implementar autenticación apropiada en producción

## Solución de Problemas

### Problemas Comunes

**Plugin APOC No Encontrado:**
```
Neo.ClientError.Procedure.ProcedureNotFound
```
Solución: Instalar y habilitar el plugin APOC en Neo4j

**Conexión Rechazada:**
```
ServiceUnavailable: Failed to establish connection
```
Solución: Verificar que Neo4j esté ejecutándose y los detalles de conexión sean correctos

**Consulta Inválida:**
```
Invalid node labels in query: [Etiqueta]. Available labels: [...]
```
Solución: Siempre llamar `get_neo4j_schema` primero para entender las etiquetas disponibles

### Modo Debug

Habilitar logging de debug estableciendo el nivel de log a DEBUG en el código:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Consideraciones de Rendimiento

- Usar consultas parametrizadas para mejorar rendimiento
- Limitar conjuntos de resultados con cláusulas `LIMIT`
- Crear índices apropiados en Neo4j
- Monitorear tiempos de ejecución de consultas
- Usar pooling de conexiones para escenarios de alta carga

---

**Versión**: 1.0.0  
**Compatible con**: Neo4j 5.0+, Python 3.11+, MCP 1.6.0+