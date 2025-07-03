# Neo4j MCP Cypher Server

A Model Context Protocol (MCP) server that provides tools for interacting with Neo4j graph databases through Cypher queries. This server enables AI assistants and applications to read, write, and analyze data in Neo4j databases with proper schema validation and connection management.

## Features

- **Schema Discovery**: Automatically retrieve and understand Neo4j database structure
- **Read Operations**: Execute safe MATCH queries for data retrieval
- **Write Operations**: Perform CREATE, MERGE, SET, DELETE operations
- **Query Validation**: Validates queries against database schema to prevent errors
- **Connection Management**: Robust async connection handling with proper error handling
- **Health Monitoring**: Built-in health check endpoint for monitoring
- **MCP Compatible**: Implements the Model Context Protocol for AI assistant integration

## Prerequisites

- Python 3.11+
- Neo4j database (local or remote)
- APOC plugin installed in Neo4j (required for schema discovery)
- Docker (optional, for containerized deployment)

## Installation

### Local Development

1. Clone the repository and navigate to the server directory:
```bash
cd servers/server4
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Neo4j connection details:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

4. Run the server:
```bash
python main.py
```

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t neo4j-mcp-server .
```

2. Run the container:
```bash
docker run -p 8003:8003 \
  -e NEO4J_URI=bolt://your-neo4j-host:7687 \
  -e NEO4J_USERNAME=neo4j \
  -e NEO4J_PASSWORD=your_password \
  -e NEO4J_DATABASE=neo4j \
  neo4j-mcp-server
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USERNAME` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `password` |
| `NEO4J_DATABASE` | Neo4j database name | `neo4j` |

### Neo4j Setup

Ensure the APOC plugin is installed and enabled in your Neo4j instance:

1. For Neo4j Desktop: Install APOC through the plugins tab
2. For Neo4j Server: Add APOC jar to the plugins directory
3. For Neo4j Docker: Use the `neo4j/neo4j:latest` image with APOC pre-installed

## API Endpoints

### MCP Tools

The server exposes three main MCP tools:

#### 1. `get_neo4j_schema`
**Required first step** - Retrieves the complete database schema including node labels, properties, and relationships.

```python
# Returns JSON structure with:
{
  "label": "NodeType",
  "attributes": {"property": "type"},
  "relationships": {"relationship": "TargetNode"}
}
```

#### 2. `read_neo4j_cypher`
Executes read-only Cypher queries (MATCH operations).

**Parameters:**
- `query` (string): The Cypher query to execute
- `params` (dict, optional): Query parameters

**Example:**
```cypher
MATCH (n:Person {name: $name}) RETURN n
```

#### 3. `write_neo4j_cypher`
Executes write Cypher queries (CREATE, MERGE, SET, DELETE operations).

**Parameters:**
- `query` (string): The Cypher query to execute
- `params` (dict, optional): Query parameters

**Example:**
```cypher
CREATE (p:Person {name: $name, age: $age}) RETURN p
```

### HTTP Endpoints

- **Health Check**: `GET /health` - Verify server and Neo4j connection status
- **SSE Endpoint**: `GET /sse` - Server-Sent Events for MCP communication
- **Message Handler**: `POST /messages/` - Handle MCP protocol messages

## Usage Examples

### Basic Workflow

1. **Get Schema** (Always first):
```python
schema = await get_neo4j_schema()
```

2. **Read Data**:
```python
result = await read_neo4j_cypher(
    query="MATCH (p:Person) RETURN p.name, p.age LIMIT 10",
    params={}
)
```

3. **Write Data**:
```python
result = await write_neo4j_cypher(
    query="CREATE (p:Person {name: $name, age: $age})",
    params={"name": "John Doe", "age": 30}
)
```

### Common Query Patterns

**Find all node types:**
```cypher
MATCH (n) RETURN DISTINCT labels(n) as node_types
```

**Get node counts:**
```cypher
MATCH (n) RETURN labels(n) as label, count(n) as count
```

**Find relationships:**
```cypher
MATCH (a)-[r]->(b) 
RETURN type(r) as relationship, labels(a) as from_node, labels(b) as to_node 
LIMIT 10
```

## Error Handling

The server includes comprehensive error handling:

- **Connection Errors**: Automatic retry and detailed logging
- **Query Validation**: Checks for invalid labels and properties
- **Schema Validation**: Ensures queries use existing database structure
- **Type Safety**: Validates query types (read vs write operations)

## Logging

The server uses structured logging with the following levels:
- `INFO`: General operation information
- `ERROR`: Error conditions and stack traces
- Connection status and query execution details

Log format: `YYYY-MM-DD HH:MM:SS | LEVEL | MESSAGE`

## Health Monitoring

Monitor server health using the `/health` endpoint:

```bash
curl http://localhost:8003/health
```

Response includes:
- Server status
- Neo4j connection health
- Database name
- Error details (if any)

## Integration with AI Assistants

This server implements the Model Context Protocol (MCP), making it compatible with:
- Claude Desktop
- Other MCP-compatible AI assistants
- Custom applications using MCP clients

### MCP Client Configuration

Add to your MCP client configuration:
```json
{
  "mcpServers": {
    "neo4j-cypher": {
      "command": "python",
      "args": ["main.py"],
      "cwd": "/path/to/servers/server4"
    }
  }
}
```

## Security Considerations

- Use strong Neo4j passwords
- Restrict network access to Neo4j ports
- Validate all input queries
- Monitor query execution for performance
- Use read-only connections where appropriate
- Implement proper authentication in production

## Troubleshooting

### Common Issues

**APOC Plugin Not Found:**
```
Neo.ClientError.Procedure.ProcedureNotFound
```
Solution: Install and enable the APOC plugin in Neo4j

**Connection Refused:**
```
ServiceUnavailable: Failed to establish connection
```
Solution: Verify Neo4j is running and connection details are correct

**Invalid Query:**
```
Invalid node labels in query: [Label]. Available labels: [...]
```
Solution: Always call `get_neo4j_schema` first to understand available labels

### Debug Mode

Enable debug logging by setting log level to DEBUG in the code:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

- Use parameterized queries to improve performance
- Limit result sets with `LIMIT` clauses
- Create appropriate indexes in Neo4j
- Monitor query execution times
- Use connection pooling for high-load scenarios



---

**Version**: 1.0.0  
**Compatible with**: Neo4j 5.0+, Python 3.11+, MCP 1.6.0+