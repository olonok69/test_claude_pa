## Model Context Protocol (MCP) Server Transports

The Model Context Protocol (MCP) is an open standard that enables AI
applications to connect with external tools, data sources, and
services. MCP supports different transport mechanisms for
communication between clients and servers, with **stdio** and **SSE
(Server-Sent Events)** being the two primary options.

## Transport Overview

MCP includes two standard transport implementations: The stdio
transport enables communication through standard input and output
streams, particularly useful for local integrations and command-line
tools. SSE transport enables server-to-client streaming with HTTP POST
requests for client-to-server communication.

Both transports use JSON-RPC 2.0 as the underlying message format for
communication.

## STDIO Transport

### What it is:
STDIO transport runs locally on your machine and communicates via
standard input/output streams. The client spawns an MCP server as a
child process.

### Key Characteristics:
**Local Execution**: This transport launches the server as a child
process and communicates via standard input and output streams. It's
ideal for local integrations and command-line tools.

**Process Communication**: Communication happens through process
streams: client writes to server's STDIN, server responds to STDOUT

**Security**: More secure by default since communication stays within
the local machine

**Deployment**: The server executable must be installed on each user's machine

### Configuration Example:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["./server.js"],
      "env": {
        "API_KEY": "value"
      }
    }
  }
}
```

### Advantages:
- Simple to implement and debug
- Secure (no network exposure)
- Direct process communication
- Lower latency
- The official MCP specification recommends that clients support stdio
whenever possible

### Limitations:
- One-to-one client-server relationship
- Both client and server must run on the same machine
- No network access capability
- Limited scalability

## SSE (Server-Sent Events) Transport

### What it is:
Works over standard HTTP (no special protocols needed), maintains a
persistent connection for server-to-client messages, and can use
standard HTTP authentication mechanisms.

### Key Characteristics:
**Network-based**: Can run on different machines across networks

**HTTP-based**: Uses HTTP POST requests for client-to-server
communication and Server-Sent Events for server-to-client streaming.

**Remote Access**: Enables distributed deployments

**Authentication**: Supports standard HTTP authentication mechanisms

### Configuration Example:
```json
{
  "mcpServers": {
    "remote-server": {
      "type": "sse",
      "url": "https://emea01.safelinks.protection.outlook.com/?url=http%3A%2F%2Fapi.example.com%2Fsse&data=05%7C02%7C%7Cb0411060e2ba45a71bd808dd9aa315aa%7C84df9e7fe9f640afb435aaaaaaaaaaaa%7C1%7C0%7C638836747416471961%7CUnknown%7CTWFpbGZsb3d8eyJFbXB0eU1hcGkiOnRydWUsIlYiOiIwLjAuMDAwMCIsIlAiOiJXaW4zMiIsIkFOIjoiTWFpbCIsIldUIjoyfQ%3D%3D%7C0%7C%7C%7C&sdata=%2B6DNKx6u9UTMp77x6FxwYvG2Go8nnC%2Ft1oGPY9jiH10%3D&reserved=0",
      "headers": {
        "Authorization": "Bearer token"
      }
    }
  }
}
```

### Advantages:
- Can serve multiple clients simultaneously
- Enables remote/distributed deployments
- Works across networks
- Supports authentication and authorization
- Better for cloud-based solutions
- Can be exposed via URLs for broader access

### Limitations:
**Security Considerations**: SSE transports can be vulnerable to DNS
rebinding attacks if not properly secured. To prevent this: Always
validate Origin headers on incoming SSE connections, avoid binding
servers to all network interfaces (0.0.0.0) when running locally, and
implement proper authentication for all SSE connections.

- More complex to implement
- Requires network configuration
- Potential security vulnerabilities if not properly configured
- Higher latency compared to stdio

## When to Choose Which Transport

### Choose STDIO when:
- Building local development tools
- Creating simple command-line integrations
- Security is a primary concern
- Single-user scenarios
- Local file system access is needed
- Working with command-line tools that require direct communication
between processes on the same machine

### Choose SSE when:
- Building web-based applications
- Need to serve multiple clients
- Remote server deployment is required
- Cloud-based solutions
- Authentication/authorization is needed
- Cross-platform compatibility is important
- Working in distributed environments where clients and servers are
separated across different systems or networks

## Current Ecosystem Support

**Client Support**: At the moment, Claude Desktop doesn't support SSE,
though there are proxy solutions available.

**Community Solutions**: Many community MCP servers only implement
stdio transport, which is typically inaccessible to remote assistants.
Tools like Supergateway have been developed as open-source utilities
that convert stdio MCP servers to SSE.

## Summary

The choice between stdio and SSE ultimately depends on your specific
use case, deployment requirements, and security considerations. STDIO
is preferred for simplicity and local development, while SSE is better
suited for distributed, multi-client scenarios.