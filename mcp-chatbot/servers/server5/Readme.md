# HubSpot MCP Server

A comprehensive Model Context Protocol (MCP) server implementation for HubSpot CRM integration, providing complete access to HubSpot's API through 25 specialized tools. Built with Express.js and Server-Sent Events (SSE) transport for real-time communication with AI assistants and applications.

## 🎯 Overview

This MCP server enables seamless integration with HubSpot CRM, allowing you to manage contacts, companies, deals, tickets, and more through a standardized protocol. The implementation provides full CRUD operations, advanced search capabilities, association management, and direct UI integration.

## ✨ Features

### **Complete HubSpot Integration (25 Tools)**
- **OAuth & Authentication**: User details and token validation
- **Object Management**: Full CRUD operations for all HubSpot object types
- **Advanced Search**: Complex filtering and query capabilities with boolean logic
- **Association Management**: Link and manage relationships between objects
- **Property Management**: Create and manage custom fields and definitions
- **Engagement Tracking**: Notes and tasks with full lifecycle support
- **Workflow Integration**: Access to automation insights and workflow details
- **UI Integration**: Generate direct links to HubSpot interface

### **Technical Capabilities**
- **Server-Sent Events (SSE)**: Real-time bidirectional communication
- **Docker Support**: Containerized deployment with Docker Compose
- **Schema Validation**: Zod-based input validation for all tools
- **Error Handling**: Comprehensive error messages and debugging
- **Type Safety**: Full TypeScript-style type checking with JavaScript
- **Auto-Registration**: Dynamic tool discovery and registration

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ or Docker
- HubSpot Private App Access Token with appropriate scopes
- MCP-compatible client (Claude Desktop, custom applications, etc.)

### 1. Environment Setup

Create a `.env` file in the server directory:
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

# Or build individually
docker build -t hubspot-mcp-server .
docker run -p 8004:8004 --env-file .env hubspot-mcp-server
```

#### Option B: Node.js
```bash
# Install dependencies
npm install

# Start the server
npm start

# Or run in development mode with auto-reload
npm run dev
```

### 3. Verify Installation
- **Health check**: http://localhost:8004/health
- **MCP endpoint**: http://localhost:8004/sse
- **Expected response**: Server status and version information

## 🔧 HubSpot Configuration

### 1. Create a HubSpot Private App
1. Go to your HubSpot Developer Account
2. Navigate to "Private Apps" section
3. Create a new Private App
4. Configure the required scopes (see below)
5. Copy the access token to your `.env` file

### 2. Required Scopes
Grant the following scopes for full functionality:

**CRM Scopes:**
- `crm.objects.contacts.read` / `crm.objects.contacts.write`
- `crm.objects.companies.read` / `crm.objects.companies.write`
- `crm.objects.deals.read` / `crm.objects.deals.write`
- `crm.objects.tickets.read` / `crm.objects.tickets.write`
- `crm.objects.owners.read`
- `crm.schemas.contacts.read` / `crm.schemas.contacts.write`
- `crm.associations.read` / `crm.associations.write`

**Additional Scopes:**
- `automation` (for workflow access)
- `oauth` (for token validation)
- `account-info.security.read` (for account details)

### 3. MCP Client Configuration
Add to your MCP client configuration:
```json
{
  "mcpServers": {
    "hubspot": {
      "transport": "sse",
      "url": "http://localhost:8004/sse",
      "timeout": 600,
      "sse_read_timeout": 900
    }
  }
}
```

## 📚 Available Tools (25 Tools)

For complete tool documentation, see [HUBSPOT_TOOLS_GUIDE.md](./HUBSPOT_TOOLS_GUIDE.md).

### **Authentication (1 tool)**
- `hubspot-get-user-details` - Get user context, permissions, and account information

### **Object Management (7 tools)**
- `hubspot-list-objects` - List objects with pagination and filtering
- `hubspot-search-objects` - Advanced search with complex filter groups
- `hubspot-batch-read-objects` - Read multiple objects by ID efficiently
- `hubspot-batch-create-objects` - Create multiple objects with associations
- `hubspot-batch-update-objects` - Update multiple objects in batch
- `hubspot-get-schemas` - Get custom object schemas and definitions

### **Property Management (4 tools)**
- `hubspot-list-properties` - List all properties for object types
- `hubspot-get-property` - Get specific property details and metadata
- `hubspot-create-property` - Create custom properties with validation
- `hubspot-update-property` - Update property definitions and options

### **Association Management (3 tools)**
- `hubspot-create-association` - Link objects with relationship types
- `hubspot-list-associations` - Get object relationships and associations
- `hubspot-get-association-definitions` - Get valid association types

### **Engagement Tracking (3 tools)**
- `hubspot-create-engagement` - Create notes and tasks with associations
- `hubspot-get-engagement` - Retrieve engagement details by ID
- `hubspot-update-engagement` - Update existing engagements and metadata

### **Workflow Integration (2 tools)**
- `hubspot-list-workflows` - List automation workflows with pagination
- `hubspot-get-workflow` - Get detailed workflow information and actions

### **UI Integration (2 tools)**
- `hubspot-get-link` - Generate direct links to HubSpot UI pages
- `hubspot-generate-feedback-link` - Generate feedback submission links

## 💡 Usage Examples

### Basic Contact Management
```javascript
// First, authenticate and get user context
hubspot-get-user-details

// Create a new contact with properties
hubspot-batch-create-objects {
  "objectType": "contacts",
  "inputs": [{
    "properties": {
      "firstname": "John",
      "lastname": "Smith",
      "email": "john@example.com",
      "phone": "+1-555-0123"
    }
  }]
}

// Search for contacts using filters
hubspot-search-objects {
  "objectType": "contacts",
  "filterGroups": [{
    "filters": [{
      "propertyName": "email",
      "operator": "EQ",
      "value": "john@example.com"
    }]
  }]
}
```

### Advanced CRM Workflow
```javascript
// 1. Create contact and company
hubspot-batch-create-objects {
  "objectType": "contacts",
  "inputs": [{"properties": {"firstname": "Jane", "email": "jane@techcorp.com"}}]
}

hubspot-batch-create-objects {
  "objectType": "companies", 
  "inputs": [{"properties": {"name": "TechCorp", "website": "techcorp.com"}}]
}

// 2. Associate contact with company
hubspot-create-association {
  "fromObjectType": "contacts",
  "fromObjectId": "contact_id_here",
  "toObjectType": "companies", 
  "toObjectId": "company_id_here",
  "associations": [{
    "associationCategory": "HUBSPOT_DEFINED",
    "associationTypeId": 1
  }]
}

// 3. Add follow-up task
hubspot-create-engagement {
  "type": "TASK",
  "ownerId": 12345,
  "metadata": {
    "subject": "Follow up with Jane at TechCorp",
    "body": "Discuss implementation timeline",
    "status": "NOT_STARTED"
  },
  "associations": {
    "contactIds": ["contact_id_here"],
    "companyIds": ["company_id_here"]
  }
}

// 4. Generate UI link to view contact
hubspot-get-link {
  "portalId": "your_portal_id",
  "uiDomain": "app.hubspot.com",
  "pageRequests": [{
    "pagetype": "record",
    "objectTypeId": "0-1",
    "objectId": "contact_id_here"
  }]
}
```

### Complex Search with Boolean Logic
```javascript
// Find contacts that are either:
// 1. Created this month AND work at tech companies, OR
// 2. Have high lead scores
hubspot-search-objects {
  "objectType": "contacts",
  "filterGroups": [
    {
      "filters": [
        {
          "propertyName": "createdate",
          "operator": "GTE", 
          "value": "2025-06-01"
        },
        {
          "propertyName": "industry",
          "operator": "EQ",
          "value": "Technology"
        }
      ]
    },
    {
      "filters": [
        {
          "propertyName": "hs_lead_score",
          "operator": "GTE",
          "value": "80"
        }
      ]
    }
  ]
}
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
│   ├── baseTool.js       # Base tool class with validation
│   ├── toolsRegistry.js  # Auto-registration of all tools
│   ├── oauth/            # Authentication tools
│   │   └── getUserDetailsTool.js
│   ├── objects/          # Object management tools
│   │   ├── listObjectsTool.js
│   │   ├── searchObjectsTool.js
│   │   ├── batchReadObjectsTool.js
│   │   ├── batchCreateObjectsTool.js
│   │   ├── batchUpdateObjectsTool.js
│   │   └── getSchemaTool.js
│   ├── properties/       # Property management tools
│   │   ├── listPropertiesTool.js
│   │   ├── getPropertyTool.js
│   │   ├── createPropertyTool.js
│   │   └── updatePropertyTool.js
│   ├── associations/     # Association management tools
│   │   ├── createAssociationTool.js
│   │   ├── listAssociationsTool.js
│   │   └── getAssociationDefinitionsTool.js
│   ├── engagements/      # Engagement tools
│   │   ├── createEngagementTool.js
│   │   ├── getEngagementTool.js
│   │   └── updateEngagementTool.js
│   ├── workflows/        # Workflow tools
│   │   ├── listWorkflowsTool.js
│   │   └── getWorkflowTool.js
│   └── links/           # UI integration tools
│       ├── getHubspotLinkTool.js
│       └── feedbackLinkTool.js
├── prompts/             # MCP prompts (extensible)
│   ├── index.js
│   └── promptsRegistry.js
├── types/               # Type definitions
│   └── objectTypes.js
└── utils/               # Utilities and HubSpot client
    └── client.js
```

### Key Components

#### **BaseTool Class**
All tools extend the `BaseTool` class which provides:
- **Zod Schema Validation**: Input parameter validation
- **Standardized Error Handling**: Consistent error responses
- **Consistent Response Formatting**: Uniform tool output structure
- **Type Safety**: Runtime type checking for all inputs

#### **HubSpot Client**
Centralized HTTP client (`utils/client.js`) with:
- **Automatic Authentication**: Bearer token management
- **Request/Response Handling**: Standardized API communication
- **Error Management**: Comprehensive error handling and retries
- **Support for All HTTP Methods**: GET, POST, PUT, PATCH, DELETE

#### **Tool Registry**
Auto-registration system (`toolsRegistry.js`) that:
- **Discovers Tool Implementations**: Automatic tool loading
- **Provides Tool Listing**: Dynamic tool discovery for MCP clients
- **Routes Tool Calls**: Directs requests to appropriate handlers
- **Manages Tool Lifecycle**: Registration and cleanup

#### **Type System**
Comprehensive type definitions for:
- **HubSpot Object Types**: All supported CRM object types
- **Property Schemas**: Input validation schemas
- **Association Types**: Relationship type definitions
- **API Response Types**: Structured response validation

## 🔍 Advanced Features

### **Complex Search Capabilities**
The `hubspot-search-objects` tool supports sophisticated filtering:

```javascript
// Multiple filter groups with OR logic
{
  "filterGroups": [
    {
      "filters": [
        {"propertyName": "industry", "operator": "IN", "values": ["Tech", "Software"]},
        {"propertyName": "state", "operator": "EQ", "value": "California"}
      ]
    },
    {
      "filters": [
        {"propertyName": "annual_revenue", "operator": "GTE", "value": "1000000"}
      ]
    }
  ]
}
```

### **Batch Operations**
Efficient batch processing for high-volume operations:

```javascript
// Create up to 100 objects in a single request
hubspot-batch-create-objects {
  "objectType": "contacts",
  "inputs": [
    {"properties": {"firstname": "User1", "email": "user1@example.com"}},
    {"properties": {"firstname": "User2", "email": "user2@example.com"}},
    // ... up to 100 objects
  ]
}
```

### **Association Management**
Link objects across different types:

```javascript
// Create complex associations
hubspot-create-association {
  "fromObjectType": "deals",
  "fromObjectId": "deal_123",
  "toObjectType": "contacts",
  "toObjectId": "contact_456",
  "associations": [{
    "associationCategory": "HUBSPOT_DEFINED",
    "associationTypeId": 3  // Decision maker association
  }]
}
```

### **Property Customization**
Create and manage custom properties:

```javascript
// Create enumeration property with options
hubspot-create-property {
  "objectType": "contacts",
  "name": "lead_source",
  "label": "Lead Source",
  "type": "enumeration",
  "fieldType": "select",
  "options": [
    {"label": "Website", "value": "website"},
    {"label": "Referral", "value": "referral"},
    {"label": "Advertisement", "value": "ad"}
  ]
}
```

## 🔍 Debugging & Monitoring

### Health Check
```bash
curl http://localhost:8004/health
```

**Response includes:**
- Server status and version
- Active connection count
- Timestamp information

### Comprehensive Logging
The server provides detailed logging for:
- **Tool Execution**: All tool calls with parameters and results
- **API Requests/Responses**: HubSpot API communication
- **Validation Errors**: Input validation failures
- **Connection Status**: MCP client connections and disconnections

### Error Handling
Robust error management for:
- **Schema Validation Errors**: Detailed parameter validation messages
- **HubSpot API Errors**: Formatted API error responses
- **Network Connectivity Issues**: Connection timeout and retry logic
- **Authentication Problems**: Token validation and permission errors

### Performance Monitoring
Track performance metrics:
- **Request Timing**: API call duration monitoring
- **Batch Operation Efficiency**: Bulk operation performance
- **Connection Health**: MCP transport status
- **Resource Usage**: Memory and CPU utilization

## 🧪 Testing

### Basic Connectivity
```bash
# Test health endpoint
curl http://localhost:8004/health

# Test MCP connection (requires MCP client)
# Connect your MCP client to http://localhost:8004/sse
```

### Tool Validation Workflow
1. **Authentication**: Start with `hubspot-get-user-details`
2. **Data Exploration**: Use `hubspot-list-objects` with contacts
3. **Property Discovery**: Try `hubspot-list-properties` for contacts
4. **Search Testing**: Use `hubspot-search-objects` with simple filters
5. **Advanced Operations**: Test batch operations and associations

### Common Test Scenarios
```javascript
// Test authentication
hubspot-get-user-details

// Test basic listing
hubspot-list-objects {"objectType": "contacts", "limit": 5}

// Test search functionality
hubspot-search-objects {
  "objectType": "contacts",
  "query": "test@example.com"
}

// Test property information
hubspot-list-properties {"objectType": "contacts"}
```

## 📈 Performance & Optimization

### Optimization Features
- **Efficient Batch Operations**: Handle up to 100 objects per request
- **Paginated Responses**: Handle large datasets with cursor-based pagination
- **Connection Pooling**: Reuse HTTP connections for better performance
- **Minimal Memory Footprint**: Optimized for server deployment
- **Request Caching**: Cache frequently accessed data (schema, properties)

### Scaling Considerations
- **Stateless Design**: Horizontal scaling support
- **Docker Container Ready**: Easy orchestration and deployment
- **Configurable Rate Limiting**: Respect HubSpot API limits
- **Resource Monitoring**: Built-in performance tracking

### HubSpot API Limits
- **Daily Limits**: Respect HubSpot's daily API call limits
- **Rate Limiting**: Built-in handling of rate limit responses
- **Batch Optimization**: Use batch operations to minimize API calls
- **Efficient Queries**: Optimize search filters and property selection

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

1. **Create Tool Class**: Extend `BaseTool` with required functionality
2. **Implement Process Method**: Handle the tool logic and API calls
3. **Define Schema**: Use Zod for input validation
4. **Add to Registry**: Import and register in `toolsRegistry.js`
5. **Update Documentation**: Add tool details to guides

Example tool structure:
```javascript
import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';
import { BaseTool } from '../baseTool.js';
import HubSpotClient from '../../utils/client.js';

const MyToolSchema = z.object({
  parameter: z.string().describe('Description of the parameter'),
});

const ToolDefinition = {
  name: 'hubspot-my-tool',
  description: 'Tool description and usage guidance',
  inputSchema: zodToJsonSchema(MyToolSchema),
  annotations: {
    title: 'My Custom Tool',
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: true,
  },
};

export class MyCustomTool extends BaseTool {
  client;

  constructor() {
    super(MyToolSchema, ToolDefinition);
    this.client = new HubSpotClient();
  }

  async process(args) {
    try {
      const response = await this.client.get(`/endpoint/${args.parameter}`);
      return {
        content: [{ type: 'text', text: JSON.stringify(response, null, 2) }],
      };
    } catch (error) {
      return {
        content: [{ type: 'text', text: `Error: ${error.message}` }],
        isError: true,
      };
    }
  }
}
```

### Code Standards
- **ES6+ Modules**: Use modern JavaScript syntax
- **Zod Validation**: Comprehensive input validation for all tools
- **Error Handling**: Robust error management with user-friendly messages
- **Documentation**: Clear, descriptive tool names and documentation
- **Consistent Formatting**: Follow established patterns for responses

### Testing Guidelines
- **Unit Tests**: Test individual tool functionality
- **Integration Tests**: Test with actual HubSpot API
- **Error Scenarios**: Test with invalid inputs and network failures
- **Performance Tests**: Validate batch operations and large datasets

## 🐛 Troubleshooting

### Common Issues

#### "Access token required" Error
- **Solution**: Verify `PRIVATE_APP_ACCESS_TOKEN` in `.env`
- **Check**: HubSpot Private App configuration and token generation
- **Ensure**: App has necessary scopes for the operations you're performing

#### Connection Refused
- **Solution**: Verify server is running on correct port (8004)
- **Check**: Firewall settings and network connectivity
- **Confirm**: MCP client configuration matches server endpoint

#### Tool Validation Errors
- **Solution**: Review input schema requirements for each tool
- **Check**: HubSpot API documentation for valid parameters
- **Verify**: Object types and property names exist in your HubSpot account

#### Rate Limiting Issues
- **Solution**: HubSpot enforces API rate limits per account
- **Implement**: Delays between requests if hitting limits frequently
- **Use**: Batch operations to reduce total API call count
- **Monitor**: Daily usage against your account limits

#### Schema or Property Not Found
- **Solution**: Use `hubspot-list-properties` to see available properties
- **Check**: Custom objects with `hubspot-get-schemas`
- **Verify**: Property names match exactly (case-sensitive)

### Getting Help
- **Documentation**: Check [HubSpot Developer Documentation](https://developers.hubspot.com/)
- **Tool Guide**: Review [HUBSPOT_TOOLS_GUIDE.md](./HUBSPOT_TOOLS_GUIDE.md)
- **Feedback**: Use `hubspot-generate-feedback-link` tool for issues
- **Logs**: Check server logs for detailed error information

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🔗 Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [HubSpot API Documentation](https://developers.hubspot.com/docs/api/overview)
- [HubSpot Private Apps Guide](https://developers.hubspot.com/docs/api/private-apps)
- [HubSpot CRM API Reference](https://developers.hubspot.com/docs/api/crm/understanding-the-crm)
- [Express.js Documentation](https://expressjs.com/)
- [Zod Schema Validation](https://zod.dev/)
- [Docker Documentation](https://docs.docker.com/)

---

**Version**: 2.0.0  
**Last Updated**: June 2025  
**API Compatibility**: HubSpot CRM API v3/v4  
**Node.js**: 18+  
**Tools**: 25 complete implementations