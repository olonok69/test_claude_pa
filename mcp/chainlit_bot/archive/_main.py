import asyncio
import sys
import os
import json
from typing import Optional, Union
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent, ImageContent

from anthropic import Anthropic
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv, dotenv_values

load_dotenv()  # load environment variables from .env
config = dotenv_values(".env")

def get_azure_openai_client():
    """
    Creates and returns Azure OpenAI client instance.
    
    Returns:
        AsyncAzureOpenAI: Configured Azure OpenAI client
    """
    print("Loading Azure OpenAI client from environment variables...")
    return AsyncAzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.memory = []
        
        # Initialize AI client based on environment variable
        ai_provider = config.get("AI_PROVIDER", "anthropic").lower()
        
        if ai_provider == "azure":
            self.ai_client = get_azure_openai_client()
            self.ai_provider = "azure"
            self.default_model = config.get("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4o")
            print(f"Using Azure OpenAI with model: {self.default_model}")
        else:
            self.ai_client = Anthropic()
            self.ai_provider = "anthropic"
            self.default_model = config.get("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
            print(f"Using Anthropic Claude with model: {self.default_model}")

    async def connect_to_server(self, server_config: dict):
        """Connect to an MCP server"""
        # Handle simple script path (backward compatibility)
        if isinstance(server_config, str):
            server_config = {"script_path": server_config}
        
        # Default environment variables
        environment = {
            "GOOGLE_API_KEY": config.get("GOOGLE_API_KEY", ""),
            "GOOGLE_SEARCH_ENGINE_ID": config.get("GOOGLE_SEARCH_ENGINE_ID", ""),
            "BRAVE_API_KEY": config.get("BRAVE_API_KEY", ""),
            "NEO4J_URI": config.get("NEO4J_URI", "bolt://localhost:7687"),
            "NEO4J_USERNAME": config.get("NEO4J_USERNAME", "neo4j"),
            "NEO4J_PASSWORD": config.get("NEO4J_PASSWORD", ""),
            "NEO4J_DATABASE": config.get("NEO4J_DATABASE", "neo4j"),
        }
        
        # Add any additional environment variables from config
        if "env" in server_config:
            environment.update(server_config["env"])
        
        # Determine command and args
        if "command" in server_config and "args" in server_config:
            command = server_config["command"]
            args = server_config["args"]
        elif "script_path" in server_config:
            script_path = server_config["script_path"]
            is_python = script_path.endswith('.py')
            is_js = script_path.endswith('.js')
            if not (is_python or is_js):
                raise ValueError("Server script must be a .py or .js file")
            
            command = "python" if is_python else "node"
            args = [script_path]
        else:
            raise ValueError("Server config must specify either 'command'+'args' or 'script_path'")
        
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=environment
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def call_mcp_tool(self, function_name: str, function_args: dict):
        """Call an MCP tool and return the response"""
        try:
            func_response = await self.session.call_tool(function_name, function_args)
            resp_items = []
            
            for item in func_response.content:
                if isinstance(item, TextContent):
                    resp_items.append({"type": "text", "text": item.text})
                elif isinstance(item, ImageContent):
                    resp_items.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{item.mimeType};base64,{item.data}",
                        },
                    })
                else:
                    resp_items.append({"type": "text", "text": str(item)})
            
            return json.dumps(resp_items)
            
        except Exception as e:
            print(f"Error calling tool {function_name}: {e}")
            return json.dumps([{"type": "text", "text": f"Error: {str(e)}"}])

    async def process_query(self, query: str) -> str:
        """Process a query using the configured AI model and available tools - based on original working version"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]
        
        response = await self.session.list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]
        
        # Add message to memory context if available
        if self.memory:
            messages = self.memory + messages
            
        final_text = []
        
        if self.ai_provider == "azure":
            # Convert to OpenAI format
            tools = [{"type": "function", "function": tool} for tool in available_tools]
            
            # Add user message to memory
            self.memory.append({
                "role": "user",
                "content": query
            })
            
            # Make API call
            response = await self.ai_client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                tools=tools if tools else None,
                temperature=0
            )
            
            message = response.choices[0].message
            
            # Handle assistant content
            if message.content:
                final_text.append(message.content)
            
            # Handle tool calls
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        function_args = {}
                    
                    print(f"[Calling tool {function_name} with args {function_args}]")
                    
                    # Execute tool call
                    result = await self.call_mcp_tool(function_name, function_args)
                    
                    # Add tool call to memory
                    self.memory.append({
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "function": {
                                    "name": function_name,
                                    "arguments": tool_call.function.arguments
                                },
                                "type": "function"
                            }
                        ]
                    })
                    
                    # Add tool result to memory
                    self.memory.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": result,
                    })
                    
                    # Get next response from AI
                    response = await self.ai_client.chat.completions.create(
                        model=self.default_model,
                        messages=self.memory.copy(),
                        tools=tools,
                        temperature=0
                    )
                    
                    if response.choices[0].message.content:
                        final_text.append(response.choices[0].message.content)
                        
                        # Add final response to memory
                        self.memory.append({
                            "role": "assistant",
                            "content": response.choices[0].message.content
                        })
            else:
                # No tool calls, add assistant response to memory
                if message.content:
                    self.memory.append({
                        "role": "assistant",
                        "content": message.content
                    })
        
        else:  # Anthropic - use original working pattern
            # Add user message to memory first
            self.memory.append({
                "role": "user",
                "content": query
            })
            
            # Initial Claude API call
            response = self.ai_client.messages.create(
                model=self.default_model,
                max_tokens=8192,
                messages=messages,
                tools=available_tools
            )

            # Process response and handle tool calls - EXACTLY like original
            for content in response.content:
                if content.type == 'text':
                    final_text.append(content.text)
                elif content.type == 'tool_use':
                    tool_name = content.name
                    tool_args = content.input
                    
                    # Execute tool call
                    result = await self.session.call_tool(tool_name, tool_args)
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                    # Continue conversation with tool results - EXACTLY like original
                    if hasattr(content, 'text') and content.text:
                        messages.append({
                          "role": "assistant",
                          "content": content.text
                        })
                        self.memory.append({
                            "role": "assistant",
                            "content": content.text
                        })
                    messages.append({
                        "role": "user", 
                        "content": result.content
                    })
                    self.memory.append({
                        "role": "user",
                        "content": result.content
                    })
                    
                    # Get next response from Claude - EXACTLY like original
                    response = self.ai_client.messages.create(
                        model=self.default_model,
                        max_tokens=8192,
                        messages=messages,
                    )

                    final_text.append(response.content[0].text)
                    self.memory.append({
                        "role": "assistant",
                        "content": response.content[0].text
                    })

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() in ['quit', 'exit']:
                    break
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
                import traceback
                traceback.print_exc()
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

# Predefined server configurations
SERVER_CONFIGS = {
    "neo4j-aura": {
        "command": "uvx",
        "args": ["mcp-neo4j-cypher@0.2.1"],
        "env": {
            # These will be merged with environment variables from .env
        }
    },
    "neo4j": {
        "command": "uv",
        "args": [
            "--directory", "servers/mcp-neo4j-cypher/src",  # Adjust this path as needed
            "run", "mcp-neo4j-cypher"
        ],
        "env": {
            # These will be merged with environment variables from .env
        }
    },
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
        "env": {}
    }
}

async def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python client.py <server_name>           # Use predefined config")
        print("  python client.py <path_to_server_script> # Use script path")
        print("\nAvailable predefined servers:", list(SERVER_CONFIGS.keys()))
        sys.exit(1)
    
    server_arg = sys.argv[1]
    
    # Check if it's a predefined server config
    if server_arg in SERVER_CONFIGS:
        server_config = SERVER_CONFIGS[server_arg]
        print(f"Using predefined config for {server_arg}")
    else:
        # Treat as script path (backward compatibility)
        server_config = {"script_path": server_arg}
        print(f"Using script path: {server_arg}")
        
    client = MCPClient()
    try:
        await client.connect_to_server(server_config)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())