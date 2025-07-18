# MCP Server Migration: Moving Company Tagging to stdio MCP Server

## Overview

This guide implements the migration of company tagging functionality from the Perplexity SSE server (server1) to a new stdio-based MCP server that runs within the client container. This change provides better integration and reduces the complexity of managing multiple external servers.

## Architecture Changes

### Before
```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Streamlit Client  │    │  Google Search API  │    │  Perplexity AI API  │
│                     │    │                     │    │                     │
│  - AI Chat UI       │◄──►│  - Web Search       │    │  - AI Search        │
│  - Authentication   │    │  - Content Extract  │    │  - Smart Analysis   │
│  - Multi-Provider   │    │  - Custom Search    │    │  - Multiple Models  │
│                     │    │                     │    │  - Company Tagging  │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           ▲                         ▲                          ▲
           │                    ┌────┴─────┐              ┌────┴─────┐
           │                    │ Server 2 │              │ Server 1 │
           │                    │ Google   │              │Perplexity│
           │                    │ Search   │              │ + Company│
           │                    │ MCP      │              │ Tagging  │
           │                    │ Server   │              │ MCP      │
           │                    └──────────┘              └──────────┘
```

### After
```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Streamlit Client  │    │  Google Search API  │    │  Perplexity AI API  │
│                     │    │                     │    │                     │
│  - AI Chat UI       │◄──►│  - Web Search       │    │  - AI Search        │
│  - Authentication   │    │  - Content Extract  │    │  - Smart Analysis   │
│  - Multi-Provider   │    │  - Custom Search    │    │  - Multiple Models  │
│  - Company Tagging  │    │                     │    │                     │
│    (stdio MCP)      │    └─────────────────────┘    └─────────────────────┘
└─────────────────────┘              ▲                          ▲
           ▲                    ┌────┴─────┐              ┌────┴─────┐
           │                    │ Server 2 │              │ Server 1 │
           │                    │ Google   │              │Perplexity│
           │                    │ Search   │              │ (Search  │
           │                    │ MCP      │              │  Only)   │
           │                    │ Server   │              │ MCP      │
           │                    └──────────┘              └──────────┘
```

## Complete Step-by-Step Implementation

### Step 1: Create Company Tagging MCP Server Directory Structure

```bash
# Navigate to the client directory
cd client

# Create the new MCP server directory structure
mkdir -p mcp_servers/company_tagging/categories

# This creates:
# client/
# ├── mcp_servers/
# │   └── company_tagging/
# │       ├── __init__.py
# │       ├── server.py
# │       ├── requirements.txt
# │       └── categories/
# │           └── classes.csv
```

### Step 2: Create New MCP Server Files

#### Create `client/mcp_servers/company_tagging/__init__.py`
```python
"""Company Tagging MCP Server."""

__version__ = "0.1.0"
```

#### Create `client/mcp_servers/company_tagging/requirements.txt`
```
mcp>=1.0.2
aiohttp>=3.8.0
python-dotenv>=1.1.0
pydantic>=2.0.0
```

#### Create `client/mcp_servers/company_tagging/server.py`
Copy the complete stdio MCP server implementation (provided in the artifacts above).

#### Create `client/mcp_servers/company_tagging/categories/classes.csv`
Copy the CSV content from `servers/server1/src/perplexity_mcp/categories/classes.csv`.

### Step 3: Update Client Configuration Files

#### Update `client/servers_config.json`
Replace the existing content with:
```json
{
  "mcpServers": {
    "Google Search": {
      "transport": "sse",
      "url": "http://mcpserver2:8002/sse",
      "timeout": 600,
      "headers": null,
      "sse_read_timeout": 900
    },
    "Perplexity Search": {
      "transport": "sse",
      "url": "http://mcpserver1:8001/sse", 
      "timeout": 600,
      "headers": null,
      "sse_read_timeout": 900
    },
    "Company Tagging": {
      "transport": "stdio",
      "command": "python",
      "args": ["-m", "mcp_servers.company_tagging.server"],
      "env": {
        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}",
        "PERPLEXITY_MODEL": "${PERPLEXITY_MODEL}"
      }
    }
  }
}
```

#### Update `client/requirements.txt`
Add the MCP dependency:
```
# Add this line to the existing requirements
mcp>=1.0.2
```

#### Update `client/config.py`
Replace with the updated version (provided in artifacts above) that includes the new stdio server configuration.

### Step 4: Update Docker Configuration

#### Update `client/Dockerfile`
Replace with the updated version (provided in artifacts above) that includes:
- Installation of MCP dependencies
- Creation of mcp_servers directory structure
- Copying of the new MCP server files

### Step 5: Update Streamlit Services

#### Update `client/services/mcp_service.py`
Replace with the updated version (provided in artifacts above) that includes:
- Support for stdio transport alongside SSE
- Environment variable expansion for stdio servers
- Improved error handling and debugging
- Testing functionality for stdio servers

#### Update `client/ui_components/tab_components.py`
Replace with the updated version (provided in artifacts above) that includes:
- Support for Company Tagging tools in categorization
- Updated connection tab with stdio server testing
- Enhanced tools tab with company tagging category

### Step 6: Clean Up Server1 (Perplexity Server)

#### Update `servers/server1/perplexity_sse_server.py`
Replace with the cleaned version (provided in artifacts above) that removes:
- `tag_company` tool
- `company_tagging_analyst` prompt
- `categories://for-tagging` resource
- Company tagging related functionality from health check

The cleaned server1 now only provides:
- **Tools**: `perplexity_search_web`, `perplexity_advanced_search`, `search_show_categories`
- **Resources**: `categories://all`, `categories://shows`, `categories://shows/{show_name}`, `categories://industries`, `categories://industries/{industry_name}`, `categories://search/{query}`

### Step 7: Test the Migration

#### Build and Start the Updated System
```bash
# Navigate to project root
cd /path/to/your/project

# Rebuild containers to include the new MCP server
docker-compose build --no-cache

# Start the system
docker-compose up
```

#### Verify the Migration
1. **Access the Streamlit interface**: http://localhost:8501 or https://localhost:8503
2. **Authenticate** using your credentials
3. **Go to Connections tab** and click "Connect to MCP Servers"
4. **Verify all three servers connect**:
   - Google Search: 2 tools (google-search, read-webpage)
   - Perplexity Search: 3 tools (perplexity_search_web, perplexity_advanced_search, search_show_categories)
   - Company Tagging: 2 tools (tag_company, search_show_categories)
5. **Test Company Tagging functionality** in the Chat tab

#### Test Company Tagging Specifically
Try these example queries:
```
"Tag Microsoft Corporation for CAI and BDAIW shows"
"Research and categorize Google Inc for Cloud and AI Infrastructure"
"Find show categories for CAI"
```

### Step 8: Environment Variables Verification

Ensure your `.env` file includes all necessary variables:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# OR Azure OpenAI Configuration
AZURE_API_KEY=your_azure_api_key
AZURE_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_DEPLOYMENT=your_deployment_name
AZURE_API_VERSION=2023-12-01-preview

# Google Search Configuration
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_custom_search_engine_id

# Perplexity Configuration (used by both server1 and stdio server)
PERPLEXITY_API_KEY=your_perplexity_api_key
PERPLEXITY_MODEL=sonar

# SSL Configuration (Optional)
SSL_ENABLED=true
```

## Migration Benefits

### 1. **Simplified Architecture**
- Reduced from 3 external servers to 2 external + 1 embedded
- Company tagging now runs within the client container
- No additional network configuration needed for company tagging

### 2. **Better Resource Management**
- Stdio transport is more efficient than SSE for embedded servers
- Reduced memory footprint (no separate container for company tagging)
- Faster tool execution (no network latency for company tagging)

### 3. **Improved Reliability**
- No network dependency for company tagging functionality
- Stdio transport is more reliable than network connections
- Better error handling and debugging capabilities

### 4. **Enhanced Development Experience**
- Easier debugging of company tagging functionality
- All client-related tools in one place
- Simpler deployment and testing process

## Troubleshooting

### Common Issues and Solutions

#### 1. **Stdio Server Not Starting**
**Error**: "Failed to start stdio server"
**Solution**:
```bash
# Test manually
cd client
python -m mcp_servers.company_tagging.server

# Check for import errors
python -c "import mcp_servers.company_tagging.server"
```

#### 2. **Company Tagging Tools Not Available**
**Error**: "No company tagging tools found"
**Solution**:
- Verify `PERPLEXITY_API_KEY` is set in environment
- Check CSV file exists at `client/mcp_servers/company_tagging/categories/classes.csv`
- Test stdio server using the "Test Company Tagging Server" button

#### 3. **Environment Variable Issues**
**Error**: "Environment variable expansion failed"
**Solution**:
- Ensure all variables in `servers_config.json` exist in `.env`
- Check variable names match exactly (case-sensitive)
- Restart the container after environment changes

#### 4. **Permission Errors**
**Error**: "Permission denied accessing MCP server"
**Solution**:
```bash
# Fix permissions
chmod +x client/mcp_servers/company_tagging/server.py
chmod -R 755 client/mcp_servers/
```

#### 5. **CSV Data Not Loading**
**Error**: "No category data available"
**Solution**:
- Verify CSV file exists and has correct headers: `Show,Industry,Product`
- Check file encoding is UTF-8
- Ensure file is copied correctly during Docker build

### Testing Commands

#### Test Individual Components
```bash
# Test stdio server directly
cd client
python -m mcp_servers.company_tagging.server

# Test Perplexity API connectivity
curl -X POST "https://api.perplexity.ai/chat/completions" \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"test"}]}'

# Test Google Search API
curl "https://www.googleapis.com/customsearch/v1?key=$GOOGLE_API_KEY&cx=$GOOGLE_SEARCH_ENGINE_ID&q=test"
```

#### Monitor Logs
```bash
# Container logs
docker-compose logs hostclient
docker-compose logs mcpserver1
docker-compose logs mcpserver2

# Specific container logs
docker-compose logs -f hostclient | grep -i "company\|mcp\|error"
```

## Rollback Plan

If issues arise during migration:

### Immediate Rollback
1. **Revert server1**: Replace `servers/server1/perplexity_sse_server.py` with the original version
2. **Revert client config**: Replace `client/servers_config.json` with original (remove Company Tagging entry)
3. **Rebuild containers**: `docker-compose build --no-cache && docker-compose up`

### Partial Rollback
- Keep new stdio server but disable it by removing from `servers_config.json`
- Re-enable company tagging in server1 by restoring original functionality
- Gradually test and migrate again

## Performance Monitoring

### Key Metrics to Monitor
1. **Tool Execution Time**: Company tagging should be faster via stdio
2. **Memory Usage**: Client container may use slightly more memory
3. **Error Rates**: Monitor for stdio-specific errors
4. **API Usage**: Perplexity API calls should remain the same

### Monitoring Commands
```bash
# Container resource usage
docker stats

# Tool execution timing
# Monitor in Streamlit "Tool Execution History" 

# Server health
curl http://localhost:8001/health  # Perplexity
curl http://localhost:8002/health  # Google Search
```

## Future Considerations

### Potential Additional Migrations
1. **Move Google Search to stdio**: If network latency becomes an issue
2. **Combine all search functionality**: Single stdio server with multiple APIs
3. **Add more specialized tools**: Company research, data validation, etc.

### Optimization Opportunities
1. **Caching**: Add caching for company research results
2. **Batch Processing**: Process multiple companies in one request
3. **Background Tasks**: Move long-running research to background jobs

## Migration Checklist

### Pre-Migration
- [ ] Backup current working configuration
- [ ] Verify all environment variables are set
- [ ] Test existing functionality is working
- [ ] Document current tool count and types

### During Migration
- [ ] Create stdio MCP server directory structure
- [ ] Copy company tagging functionality to stdio server
- [ ] Update client configuration files
- [ ] Update Docker configuration
- [ ] Update Streamlit services and UI components
- [ ] Clean up server1 (remove company tagging)

### Post-Migration Testing
- [ ] Build and start updated containers successfully
- [ ] Connect to all MCP servers (2 SSE + 1 stdio)
- [ ] Verify tool categorization is correct
- [ ] Test company tagging functionality
- [ ] Test Google Search functionality (unchanged)
- [ ] Test Perplexity search functionality (unchanged)
- [ ] Monitor for errors in logs

### Validation
- [ ] Company tagging produces same results as before
- [ ] Performance is equal or better
- [ ] No regression in existing functionality
- [ ] All error cases are handled properly

### Documentation
- [ ] Update README.md with new architecture
- [ ] Update API documentation
- [ ] Create troubleshooting guide
- [ ] Document rollback procedures

## Success Criteria

The migration is considered successful when:

1. **All three MCP servers connect successfully** (Google Search, Perplexity, Company Tagging)
2. **Company tagging functionality works identically** to the previous implementation
3. **No regression** in Google Search or Perplexity functionality
4. **Performance is maintained or improved** for company tagging operations
5. **Error handling is robust** for all transport types
6. **Logs show no persistent errors** after migration

This migration simplifies the architecture while maintaining all functionality and improving the development experience.  │
│  - Company Tagging  │    │                     │    │                     │
│    (stdio MCP)      │    └─────────────────────┘    └─────────────────────┘
└─────────────────────┘              ▲                          ▲
           ▲                    ┌────┴─────┐              ┌────┴─────┐
           │                    │ Server 2 │              │ Server 1 │
           │                    │ Google   │              │Perplexity│
           │                    │ Search   │              │ (Search  │
           │                    │ MCP      │              │  Only)   │
           │                    │ Server   │              │ MCP      │
           │                    └──────────┘              └──────────┘
```

## Step-by-Step Implementation

### Step 1: Create Company Tagging MCP Server Structure

First, let's create the directory structure for the new stdio MCP server:

```
client/
├── mcp_servers/
│   └── company_tagging/
│       ├── __init__.py
│       ├── server.py
│       ├── requirements.txt
│       └── categories/
│           └── classes.csv
├── config.py (updated)
├── servers_config.json (updated)
└── ...existing files...
```

### Step 2: Create the stdio MCP Server Files

#### client/mcp_servers/company_tagging/requirements.txt
```
mcp>=1.0.2
aiohttp>=3.8.0
python-dotenv>=1.1.0
pydantic>=2.0.0
```

#### client/mcp_servers/company_tagging/__init__.py
```python
"""Company Tagging MCP Server."""

__version__ = "0.1.0"
```

#### client/mcp_servers/company_tagging/categories/classes.csv
Copy the CSV content from servers/server1/src/perplexity_mcp/categories/classes.csv

#### client/mcp_servers/company_tagging/server.py
Main server implementation with stdio transport

### Step 3: Update Client Configuration

#### client/servers_config.json (updated)
```json
{
  "mcpServers": {
    "Google Search": {
      "transport": "sse",
      "url": "http://mcpserver2:8002/sse",
      "timeout": 600,
      "headers": null,
      "sse_read_timeout": 900
    },
    "Perplexity Search": {
      "transport": "sse",
      "url": "http://mcpserver1:8001/sse", 
      "timeout": 600,
      "headers": null,
      "sse_read_timeout": 900
    },
    "Company Tagging": {
      "transport": "stdio",
      "command": "python",
      "args": ["-m", "mcp_servers.company_tagging.server"],
      "env": {
        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}"
      }
    }
  }
}
```

### Step 4: Update Client Dependencies

#### client/requirements.txt (additions)
Add MCP dependencies for stdio transport:
```
# Existing dependencies...

# MCP stdio support
mcp>=1.0.2
```

### Step 5: Update Docker Configuration

#### client/Dockerfile (updated)
Add installation of the new MCP server

### Step 6: Clean Up Server1

Remove company tagging functionality from servers/server1/perplexity_sse_server.py:
- Remove `tag_company` tool
- Remove `company_tagging_analyst` prompt  
- Remove `categories://for-tagging` resource
- Update health check response

### Step 7: Update Streamlit Services

#### client/services/mcp_service.py (updated)
Add support for stdio transport alongside SSE

### Step 8: Update Configuration

#### client/config.py (updated)
Add configuration for the new stdio server

## Implementation Files

The following sections contain the complete implementation of each file needed for this migration.

## Testing & Validation

### Test Plan
1. **Unit Tests**: Test stdio MCP server functionality
2. **Integration Tests**: Test client-server communication
3. **UI Tests**: Verify Streamlit interface works with new server
4. **Regression Tests**: Ensure existing functionality unchanged

### Validation Steps
1. Start the updated client container
2. Verify all three MCP servers connect properly
3. Test company tagging functionality through the UI
4. Verify Google Search and Perplexity still work
5. Check logs for any errors or warnings

## Migration Checklist

- [ ] Create client/mcp_servers/company_tagging/ directory structure
- [ ] Implement stdio MCP server with company tagging tools
- [ ] Copy CSV data to new location
- [ ] Update client configuration files
- [ ] Update Docker configuration
- [ ] Update MCP service to handle stdio transport
- [ ] Clean up server1 (remove company tagging)
- [ ] Test the new setup
- [ ] Update documentation

## Rollback Plan

If issues arise:
1. Revert client/servers_config.json to original
2. Restore server1 company tagging functionality
3. Remove stdio MCP server files
4. Rebuild containers with original configuration

## Benefits of This Migration

1. **Simplified Deployment**: Reduces external server dependencies
2. **Better Integration**: Direct stdio communication is more reliable
3. **Resource Efficiency**: No need for separate container for company tagging
4. **Easier Maintenance**: All client-related functionality in one place
5. **Improved Security**: No network exposure for company tagging server

## Next Steps

After successful migration:
1. Monitor performance and resource usage
2. Consider migrating other specialized tools to stdio servers
3. Update documentation to reflect new architecture
4. Optimize stdio server performance if needed