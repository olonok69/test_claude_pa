import asyncio
import os
import json
import weakref
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv(".env")

def validate_and_fix_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and fix common schema issues for OpenAI function calling
    """
    
    def fix_array_schema(obj: Any, path: str = "") -> Any:
        """Recursively fix array schemas that are missing 'items'"""
        if isinstance(obj, dict):
            fixed_obj = {}
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, (dict, list)):
                    fixed_obj[key] = fix_array_schema(value, current_path)
                else:
                    fixed_obj[key] = value
            
            # Special case: if this object has type: array but no items
            if fixed_obj.get("type") == "array" and "items" not in fixed_obj:
                fixed_obj["items"] = {"type": "string", "description": "Array item"}
                print(f"🔧 Fixed missing 'items' for array at path: {path}")
                
            return fixed_obj
            
        elif isinstance(obj, list):
            return [fix_array_schema(item, f"{path}[{i}]") for i, item in enumerate(obj)]
        else:
            return obj
    
    def remove_invalid_properties(obj: Any) -> Any:
        """Remove properties that might cause issues"""
        if isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                # Skip properties that might cause issues
                if key in ['$schema', '$id', '$ref']:
                    continue
                cleaned[key] = remove_invalid_properties(value)
            return cleaned
        elif isinstance(obj, list):
            return [remove_invalid_properties(item) for item in obj]
        else:
            return obj
    
    # First, remove potentially problematic properties
    cleaned_schema = remove_invalid_properties(schema)
    
    # Then fix array schemas
    fixed_schema = fix_array_schema(cleaned_schema)
    
    return fixed_schema

def validate_tool_schema(tool: Dict[str, Any]) -> bool:
    """
    Validate if a tool schema is compatible with OpenAI function calling
    """
    try:
        # Check required fields
        if "name" not in tool:
            return False
            
        if "parameters" not in tool:
            return False
        
        # Validate parameters schema
        params = tool["parameters"]
        if not isinstance(params, dict):
            return False
        
        # Check for array issues recursively
        def has_array_issues(obj: Any) -> bool:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "type" and value == "array" and "items" not in obj:
                        return True
                    elif isinstance(value, (dict, list)):
                        if has_array_issues(value):
                            return True
            elif isinstance(obj, list):
                for item in obj:
                    if has_array_issues(item):
                        return True
            return False
        
        return not has_array_issues(params)
        
    except Exception as e:
        print(f"❌ Error validating tool '{tool.get('name', 'unknown')}': {e}")
        return False

class MCPClient:
    def __init__(self):
        self.sessions = {}
        self.tools = {}
        self.connections = {}  # Store connection details for manual cleanup
        self._cleanup_tasks = []
        
    async def connect_to_server(self, server_name: str, command: str, args: list, env: dict = None):
        """Connect to an MCP server with improved async handling"""
        try:
            # Prepare environment variables
            server_env = os.environ.copy()
            if env:
                server_env.update(env)
            
            # Create server parameters
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=server_env
            )
            
            print(f"Connecting to {server_name} with command: {command} {' '.join(args)}")
            
            # Use a separate AsyncExitStack for each connection
            exit_stack = AsyncExitStack()
            
            # Connect using the exit stack
            stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
            stdio, write = stdio_transport
            
            # Create session
            session = await exit_stack.enter_async_context(ClientSession(stdio, write))
            await session.initialize()
            
            # Store everything we need for cleanup
            self.sessions[server_name] = session
            self.connections[server_name] = {
                'exit_stack': exit_stack,
                'stdio': stdio,
                'write': write
            }
            
            # Get available tools
            tools_result = await session.list_tools()
            raw_tools = [{
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
                "server": server_name
            } for tool in tools_result.tools]
            
            # Validate and fix tools
            print(f"📋 Validating {len(raw_tools)} tools from {server_name}...")
            validated_tools = self.filter_and_fix_tools(raw_tools, server_name)
            
            self.tools[server_name] = validated_tools
            
            print(f"Successfully connected to {server_name}")
            print(f"Available tools: {[tool['name'] for tool in validated_tools]}")
            
            if len(validated_tools) < len(raw_tools):
                excluded_count = len(raw_tools) - len(validated_tools)
                print(f"⚠️  Excluded {excluded_count} tools with schema issues")
            
            return session, validated_tools
            
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")
            import traceback
            traceback.print_exc()
            return None, []
    
    def filter_and_fix_tools(self, tools: List[Dict[str, Any]], server_name: str) -> List[Dict[str, Any]]:
        """Filter out problematic tools and fix fixable ones"""
        fixed_tools = []
        problematic_tools = []
        
        for tool in tools:
            tool_name = tool.get("name", "unknown")
            
            # First try to validate as-is
            if validate_tool_schema(tool):
                fixed_tools.append(tool)
                continue
            
            # Try to fix the tool
            try:
                print(f"🔧 Fixing tool '{tool_name}' from {server_name}...")
                
                fixed_tool = tool.copy()
                if "parameters" in fixed_tool:
                    fixed_tool["parameters"] = validate_and_fix_schema(fixed_tool["parameters"])
                
                # Validate the fixed tool
                if validate_tool_schema(fixed_tool):
                    fixed_tools.append(fixed_tool)
                    print(f"✅ Tool '{tool_name}' fixed successfully")
                else:
                    problematic_tools.append(tool_name)
                    print(f"❌ Tool '{tool_name}' could not be fixed - excluding")
                    
            except Exception as e:
                problematic_tools.append(tool_name)
                print(f"❌ Error fixing tool '{tool_name}': {e}")
        
        if problematic_tools:
            print(f"⚠️  {server_name}: Excluded {len(problematic_tools)} problematic tools: {', '.join(problematic_tools)}")
        
        return fixed_tools
    
    async def connect_from_config(self, config_path: str = "mcp_config.json"):
        """Connect to all servers defined in config file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            for server_name, server_config in config.get("mcpServers", {}).items():
                command = server_config.get("command")
                args = server_config.get("args", [])
                env = server_config.get("env", {})
                
                # Replace environment variable placeholders
                for key, value in env.items():
                    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                        env_var = value[2:-1]
                        env[key] = os.environ.get(env_var, value)
                
                session, tools = await self.connect_to_server(server_name, command, args, env)
                if session is None:
                    print(f"Failed to connect to {server_name}, continuing without it...")
                
        except Exception as e:
            print(f"Failed to load config: {e}")
            import traceback
            traceback.print_exc()
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: dict):
        """Call a tool on a specific server"""
        if server_name not in self.sessions:
            raise ValueError(f"No session found for server: {server_name}")
        
        session = self.sessions[server_name]
        result = await session.call_tool(tool_name, arguments)
        return result
    
    def get_all_tools(self):
        """Get all available tools from all connected servers"""
        all_tools = []
        for server_name, tools in self.tools.items():
            for tool in tools:
                tool_copy = tool.copy()
                tool_copy["server"] = server_name
                all_tools.append(tool_copy)
        return all_tools
    
    def is_connected(self, server_name: str = None):
        """Check if we have any connections or a specific connection"""
        if server_name:
            return server_name in self.sessions
        return len(self.sessions) > 0
    
    async def close_all(self):
        """Close all connections with improved cleanup"""
        cleanup_tasks = []
        
        # Close each connection individually to avoid async context issues
        for server_name in list(self.connections.keys()):
            try:
                connection = self.connections[server_name]
                exit_stack = connection['exit_stack']
                
                # Create a task for each cleanup to isolate async contexts
                async def cleanup_connection(stack, name):
                    try:
                        await stack.aclose()
                    except Exception as e:
                        # Ignore common async cleanup errors
                        if "cancel scope" not in str(e).lower():
                            print(f"Error cleaning up {name}: {e}")
                
                task = asyncio.create_task(cleanup_connection(exit_stack, server_name))
                cleanup_tasks.append(task)
                
            except Exception as e:
                if "cancel scope" not in str(e).lower():
                    print(f"Error initiating cleanup for {server_name}: {e}")
        
        # Wait for all cleanup tasks with timeout
        if cleanup_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*cleanup_tasks, return_exceptions=True),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                print("Cleanup timeout - some connections may not have closed cleanly")
            except Exception as e:
                if "cancel scope" not in str(e).lower():
                    print(f"Error during cleanup: {e}")
        
        # Clear all references
        self.sessions.clear()
        self.tools.clear()
        self.connections.clear()

# Test function with connection retry
async def test_connection():
    client = MCPClient()
    
    try:
        # Connect to servers
        await client.connect_from_config()
        
        if not client.is_connected():
            print("❌ No MCP connections established")
            return False
        
        # List available tools
        tools = client.get_all_tools()
        print(f"Total validated tools available: {len(tools)}")
        for tool in tools:
            print(f"- {tool['name']} (from {tool['server']}): {tool['description']}")
        
        return True
        
    finally:
        await client.close_all()

if __name__ == "__main__":
    asyncio.run(test_connection())