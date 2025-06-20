# HubSpot MCP Server

A comprehensive Model Context Protocol (MCP) server implementation for HubSpot CRM integration, providing complete access to HubSpot's API through 25 specialized tools.

## 🎯 Overview

This MCP server enables seamless integration with HubSpot CRM, allowing you to manage contacts, companies, deals, tickets, and more through a standardized protocol. Built with Express.js and Server-Sent Events (SSE) transport, it provides real-time communication capabilities for AI assistants and applications.

## ✨ Features

### **Complete HubSpot Integration (25 Tools)**
- **OAuth & Authentication**: User details and token validation
- **Object Management**: Full CRUD operations for all HubSpot object types
- **Advanced Search**: Complex filtering and query capabilities
- **Association Management**: Link and manage relationships between objects
- **Property Management**: Create and manage custom fields
- **Engagement Tracking**: Notes and tasks with full lifecycle support
- **Workflow Integration**: Access to automation insights
- **UI Integration**: Generate direct links to HubSpot interface

### **Technical Capabilities**
- **Server-Sent Events (SSE)**: Real-time bidirectional communication
- **Docker Support**: Containerized deployment with Docker Compose
- **Schema Validation**: Zod-based input validation for all tools
- **Error Handling**: Comprehensive error messages and debugging
- **Type Safety**: Full TypeScript-style type checking

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ or Docker
- HubSpot Private App Access Token
- MCP-compatible client (Claude Desktop, etc.)

### 1. Environment Setup

Create a `.env` file:
```env
PRIVATE_APP_ACCESS_TOKEN=your_hubspot_private_app_token
PORT=8004
HOST=0.0.0.0
```

### 2. Installation & Running

#### Option A: Docker (Recommended)
```bash
# Build and run with Docker Compose
docker-compose build --no-cache mcpserver5
docker-compose up mcpserver5
```

#### Option B: Node.js
```bash
# Install dependencies
npm install

# Start the server
npm start

# Or run in development mode
npm run dev
```

### 3. Verify Installation
- Health check: `http://localhost:8004/health`
- MCP endpoint: `http://localhost:8004/sse`

## 🔧 Configuration

### HubSpot Setup
1. Go to HubSpot Developer Account
2. Create a Private App
3. Grant necessary scopes (CRM, Automation, etc.)
4. Copy the access token to your `.env` file

### MCP Client Configuration
Add to your MCP client configuration:
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

## 📚 Available Tools

For complete tool documentation, see [HUBSPOT_TOOLS_GUIDE.md](./HUBSPOT_TOOLS_GUIDE.md).

### Core Categories

#### **Authentication (1 tool)**
- `hubspot-get-user-details` - Get user context and permissions

#### **Object Management (7 tools)**
- `hubspot-list-objects` - List objects with pagination
- `hubspot-search-objects` - Advanced search with filters
- `hubspot-batch-read-objects` - Read multiple objects by ID
- `hubspot-batch-create-objects` - Create multiple objects
- `hubspot-batch-update-objects` - Update multiple objects
- `hubspot-get-schemas` - Get custom object schemas

#### **Property Management (4 tools)**
- `hubspot-list-properties` - List object properties
- `hubspot-get-property` - Get specific property details
- `hubspot-create-property` - Create custom properties
- `hubspot-update-property` - Update property definitions

#### **Association Management (3 tools)**
- `hubspot-create-association` - Link objects together
- `hubspot-list-associations` - Get object relationships
- `hubspot-get-association-definitions` - Get valid association types

#### **Engagement Tracking (3 tools)**
- `hubspot-create-engagement` - Create notes and tasks
- `hubspot-get-engagement` - Retrieve engagement details
- `hubspot-update-engagement` - Update existing engagements

#### **Workflow Integration (2 tools)**
- `hubspot-list-workflows` - List automation workflows
- `hubspot-get-workflow` - Get workflow details

#### **UI Integration (2 tools)**
- `hubspot-get-link` - Generate HubSpot UI links
- `hubspot-generate-feedback-link` - Generate feedback links

## 💡 Usage Examples

### Basic Contact Management
```javascript
// Get user details first
hubspot-get-user-details

// Create a new contact
hubspot-batch-create-objects {
  "objectType": "contacts",
  "inputs": [{
    "properties": {
      "firstname": "John",
      "lastname": "Smith",
      "email": "john@example.com"
    }
  }]
}

// Search for contacts
hubspot-search-objects {
  "objectType": "contacts",
  "query": "john@example.com"
}
```

### Complete CRM Workflow
```javascript
// 1. Create contact and company
// 2. Associate them together
// 3. Add a follow-up task
// 4. Generate link to view in HubSpot

// This demonstrates the full power of the 25 available tools
// working together for complete CRM management
```

## 🏗️ Architecture

### Project Structure
```
servers/server5/
├── main.js                 # Express server with SSE transport
├── package.json           # Dependencies and scripts
├── Dockerfile            # Container configuration
├── .dockerignore         # Docker ignore rules
├── HUBSPOT_TOOLS_GUIDE.md # Complete tool documentation
├── tools/                # Tool implementations
│   ├── index.js          # Tool registry and handler
│   ├── baseTool.js       # Base tool class
│   ├── toolsRegistry.js  # Auto-registration of all tools
│   ├── oauth/            # Authentication tools
│   ├── objects/          # Object management tools
│   ├── properties/       # Property management tools
│   ├── associations/     # Association management tools
│   ├── engagements/      # Engagement tools
│   ├── workflows/        # Workflow tools
│   └── links/           # UI integration tools
├── prompts/             # MCP prompts (extensible)
├── types/               # Type definitions
└── utils/               # Utilities and HubSpot client
```

### Key Components

#### **BaseTool Class**
All tools extend the `BaseTool` class which provides:
- Zod schema validation
- Standardized error handling
- Consistent response formatting

#### **HubSpot Client**
Centralized HTTP client with:
- Automatic authentication
- Request/response handling
- Error management
- Support for all HTTP methods

#### **Tool Registry**
Auto-registration system that:
- Discovers all tool implementations
- Provides tool listing for MCP clients
- Routes tool calls to appropriate handlers

## 🔍 Debugging & Monitoring

### Health Check
```bash
curl http://localhost:8004/health
```

### Logs
The server provides detailed logging for:
- Tool execution
- API requests/responses
- Validation errors
- Connection status

### Error Handling
- Schema validation errors
- HubSpot API errors
- Network connectivity issues
- Authentication problems

## 🔒 Security

### Authentication
- Secure token-based authentication with HubSpot
- Environment variable protection
- No token exposure in logs

### Validation
- Comprehensive input validation using Zod schemas
- Type safety throughout the application
- Sanitized error messages

### Docker Security
- Non-root user execution
- Minimal attack surface
- Secure defaults

## 🧪 Testing

### Basic Connectivity
```bash
# Test health endpoint
curl http://localhost:8004/health

# Test MCP connection
# Connect your MCP client to http://localhost:8004/sse
```

### Tool Validation
1. Start with `hubspot-get-user-details` to verify authentication
2. Use `hubspot-list-objects` to test basic data retrieval
3. Try `hubspot-search-objects` for advanced functionality

## 📈 Performance

### Optimization Features
- Efficient batch operations for bulk data handling
- Paginated responses for large datasets
- Connection pooling for HTTP requests
- Minimal memory footprint

### Scaling Considerations
- Stateless design for horizontal scaling
- Docker container ready for orchestration
- Configurable rate limiting support

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd servers/server5

# Install dependencies
npm install

# Start in development mode
npm run dev
```

### Adding New Tools
1. Create tool class extending `BaseTool`
2. Implement the `process` method
3. Add to `toolsRegistry.js`
4. Update documentation

### Code Style
- ES6+ modules
- Zod for schema validation
- Comprehensive error handling
- Clear, descriptive naming

## 🐛 Troubleshooting

### Common Issues

#### "Access token required" Error
- Verify `PRIVATE_APP_ACCESS_TOKEN` in `.env`
- Check HubSpot Private App configuration
- Ensure app has necessary scopes

#### Connection Refused
- Verify server is running on correct port
- Check firewall settings
- Confirm MCP client configuration

#### Tool Validation Errors
- Review input schema requirements
- Check HubSpot API documentation
- Verify object types and property names

#### Rate Limiting
- HubSpot enforces API rate limits
- Implement delays between requests if needed
- Use batch operations for bulk data

### Getting Help
- Check [HubSpot Developer Documentation](https://developers.hubspot.com/)
- Review [HUBSPOT_TOOLS_GUIDE.md](./HUBSPOT_TOOLS_GUIDE.md) for detailed tool usage
- Submit feedback via `hubspot-generate-feedback-link` tool

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🔗 Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [HubSpot API Documentation](https://developers.hubspot.com/docs/api/overview)
- [HubSpot Tools Guide](./HUBSPOT_TOOLS_GUIDE.md)
- [Docker Documentation](https://docs.docker.com/)

---
