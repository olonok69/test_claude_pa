# HubSpot MCP Server - Complete Tools Implementation Guide

## Current Implementation Status

✅ **Currently Implemented Tools (13 tools):**
- `hubspot-get-user-details` - Get authentication and user context
- `hubspot-list-objects` - List objects with pagination
- `hubspot-search-objects` - Advanced search with filters (**FIXED** schema issue)
- `hubspot-batch-read-objects` - Read multiple objects by ID
- `hubspot-batch-create-objects` - Create multiple objects ⭐ **NEW**
- `hubspot-batch-update-objects` - Update multiple objects ⭐ **NEW**
- `hubspot-get-schemas` - Get custom object schemas
- `hubspot-list-properties` - List object properties
- `hubspot-get-property` - Get specific property details ⭐ **NEW**
- `hubspot-create-engagement` - Create notes and tasks
- `hubspot-get-engagement` - Retrieve engagement details ⭐ **NEW**
- `hubspot-create-association` - Link objects together ⭐ **NEW**
- `hubspot-list-associations` - Get object relationships ⭐ **NEW**

## 🔧 Recent Fixes

### ✅ **Schema Issue Resolved**
Fixed the `hubspot-search-objects` tool schema error by properly defining the `values` array:
```javascript
// Fixed: values array now properly typed as string[]
values: z.array(z.string()).optional()
```

This resolves the OpenAI function calling error: "array schema missing items"

## 🚀 Quick Setup for Additional Tools

To add more tools from the original HubSpot MCP package, follow this process:

### Step 1: Copy Tool Files
Copy the desired tool files from the original package to the corresponding directories:

```bash
# Example: Copy batch create objects tool
cp hubspot-mcp-server-0.3.3/package/dist/tools/objects/batchCreateObjectsTool.js \
   servers/server5/tools/objects/

# Example: Copy associations tools
cp hubspot-mcp-server-0.3.3/package/dist/tools/associations/*.js \
   servers/server5/tools/associations/
```

### Step 2: Update Import Paths
In each copied file, update the import statements:

**Change:**
```javascript
import { BaseTool } from '../baseTool.js';
import HubSpotClient from '../../utils/client.js';
import { HUBSPOT_OBJECT_TYPES } from '../../types/objectTypes.js';
```

**To:** (ensure paths match your directory structure)

### Step 3: Register the Tool
Add the import and registration in `tools/toolsRegistry.js`:

```javascript
import { NewToolName } from './path/to/NewToolName.js';
registerTool(new NewToolName());
```

### Step 4: Test and Rebuild
```bash
docker-compose build --no-cache mcpserver5
docker-compose up mcpserver5
```

## 📋 Available Tools to Add

### **Objects Category (High Priority)**
- `batchCreateObjectsTool.js` - Create multiple objects
- `batchUpdateObjectsTool.js` - Update multiple objects

### **Properties Category**
- `getPropertyTool.js` - Get specific property details
- `createPropertyTool.js` - Create custom properties
- `updatePropertyTool.js` - Update property definitions

### **Associations Category**
- `createAssociationTool.js` - Link objects together
- `listAssociationsTool.js` - Get object relationships
- `getAssociationDefinitionsTool.js` - Get valid association types

### **Engagements Category**
- `getEngagementTool.js` - Retrieve engagement details
- `updateEngagementTool.js` - Update existing engagements

### **Workflows Category**
- `listWorkflowsTool.js` - List automation workflows
- `getWorkflowTool.js` - Get workflow details

### **Links Category**
- `getHubspotLinkTool.js` - Generate HubSpot UI links
- `feedbackLinkTool.js` - Generate feedback links

## 🎯 Recommended Implementation Priority

### Phase 1: Core CRUD Operations
1. `batchCreateObjectsTool.js` - Essential for data creation
2. `batchUpdateObjectsTool.js` - Essential for data updates
3. `getPropertyTool.js` - Property inspection
4. `createAssociationTool.js` - Link related objects

### Phase 2: Advanced Features
5. `listAssociationsTool.js` - Explore relationships
6. `getAssociationDefinitionsTool.js` - Understand valid associations
7. `createPropertyTool.js` - Custom field creation
8. `updatePropertyTool.js` - Field management

### Phase 3: Workflow & Management
9. `listWorkflowsTool.js` - Automation insights
10. `getWorkflowTool.js` - Workflow details
11. `getHubspotLinkTool.js` - UI integration
12. `updateEngagementTool.js` - Engagement management

## 📁 Directory Structure After Full Implementation

```
servers/server5/tools/
├── index.js
├── baseTool.js
├── toolsRegistry.js
├── oauth/
│   └── getUserDetailsTool.js ✅
├── objects/
│   ├── listObjectsTool.js ✅
│   ├── searchObjectsTool.js ✅
│   ├── batchReadObjectsTool.js ✅
│   ├── batchCreateObjectsTool.js 🔄
│   ├── batchUpdateObjectsTool.js 🔄
│   └── getSchemaTool.js ✅
├── properties/
│   ├── listPropertiesTool.js ✅
│   ├── getPropertyTool.js 🔄
│   ├── createPropertyTool.js 🔄
│   └── updatePropertyTool.js 🔄
├── associations/
│   ├── createAssociationTool.js 🔄
│   ├── listAssociationsTool.js 🔄
│   └── getAssociationDefinitionsTool.js 🔄
├── engagements/
│   ├── createEngagementTool.js ✅
│   ├── getEngagementTool.js 🔄
│   └── updateEngagementTool.js 🔄
├── workflows/
│   ├── listWorkflowsTool.js 🔄
│   └── getWorkflowTool.js 🔄
└── links/
    ├── getHubspotLinkTool.js 🔄
    └── feedbackLinkTool.js 🔄
```

Legend: ✅ Implemented | 🔄 Available to copy

## 🔧 Common Modifications Needed

When copying tools, you may need to make these adjustments:

### 1. Import Statement Updates
```javascript
// Original imports (TypeScript)
import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';

// Keep as-is for our JavaScript implementation
```

### 2. Class Export Updates
```javascript
// Ensure proper export at the end of each file
export class YourToolName extends BaseTool {
    // ... implementation
}
```

### 3. Client Integration
All tools should use the same HubSpotClient pattern:
```javascript
import HubSpotClient from '../../utils/client.js';

export class YourTool extends BaseTool {
    client;
    
    constructor() {
        super(Schema, ToolDefinition);
        this.client = new HubSpotClient();
    }
}
```

## 🧪 Testing Your Implementation

1. **Build and run:**
   ```bash
   docker-compose build --no-cache mcpserver5
   docker-compose up mcpserver5
   ```

2. **Check tool registration:**
   - Connect to MCP servers in the UI
   - Verify new tools appear in the "Available Tools" list

3. **Test basic functionality:**
   - Try `hubspot-get-user-details` first to ensure authentication
   - Test a simple read operation like `hubspot-list-objects`
   - Test your newly added tools

## 🎉 Full Implementation Result

Once all tools are implemented, you'll have a complete HubSpot MCP server with:
- **25+ tools** covering all major HubSpot operations
- **Full CRUD capabilities** for all object types
- **Association management** for relating objects
- **Property management** for custom fields
- **Engagement tracking** for activities
- **Workflow integration** for automation insights

This provides comprehensive HubSpot CRM integration through the MCP protocol!

## 📞 Support

If you encounter issues while adding tools:
1. Check the server logs for specific error messages
2. Verify import paths are correct
3. Ensure the tool is registered in `toolsRegistry.js`
4. Test the HubSpot API access token has required permissions