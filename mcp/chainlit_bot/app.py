# MUST be imported first, before any other async libraries
import sys
import asyncio
import warnings
import logging
import os

# Targeted async fixes - MUST BE FIRST
def apply_targeted_async_fixes():
    """Apply targeted async fixes while preserving functionality"""
    
    # Set asyncio policy early
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    else:
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    
    # Ensure we have an event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Patch sniffio before it's used by httpcore
    try:
        import sniffio
        original_current_async_library = sniffio.current_async_library
        
        def patched_current_async_library():
            try:
                return original_current_async_library()
            except Exception:
                return "asyncio"
        
        sniffio.current_async_library = patched_current_async_library
    except ImportError:
        pass
    
    # Set environment variables
    os.environ['ASYNC_BACKEND'] = 'asyncio'
    
    # Targeted warning suppression (don't suppress everything)
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.filterwarnings("ignore", message=".*async generator ignored GeneratorExit.*")
    warnings.filterwarnings("ignore", message=".*cannot create weak reference.*")
    
    # Target specific problematic loggers only
    problematic_modules = ['httpcore._async', 'httpx._transports']
    
    for module_name in problematic_modules:
        logger = logging.getLogger(module_name)
        logger.setLevel(logging.ERROR)
        logger.addHandler(logging.NullHandler())
        logger.propagate = False
    
    # Targeted exception handler - only ignore specific async cleanup issues
    def targeted_exception_handler(loop, context):
        exception = context.get('exception')
        message = context.get('message', '')
        
        # Only ignore very specific async cleanup errors
        ignore_patterns = [
            'async generator ignored GeneratorExit',
            'HTTP11ConnectionByteStream.__aiter__',
            'PoolByteStream.__aiter__',
            'cancel scope in a different task',
            'weak reference to \'NoneType\'',
            'task_states'
        ]
        
        if exception or message:
            error_str = str(exception) + str(message)
            if any(pattern in error_str for pattern in ignore_patterns):
                return  # Ignore only these specific errors
        
        # Log other exceptions normally (this is important for debugging)
        if exception and 'chainlit' not in str(exception).lower():
            print(f"Async exception: {exception}")
    
    loop.set_exception_handler(targeted_exception_handler)
    
    # More targeted stderr filtering - only filter specific patterns
    original_stderr_write = sys.stderr.write
    
    def filtered_stderr_write(text):
        ignore_patterns = [
            'Exception ignored in: <async_generator object',
            'StopAsyncIteration:',
            'RuntimeError: Attempted to exit cancel scope',
            'HTTP11ConnectionByteStream',
            'PoolByteStream'
        ]
        
        # Only filter very specific error patterns
        if any(pattern in text for pattern in ignore_patterns):
            return len(text)  # Pretend we wrote it
        
        return original_stderr_write(text)
    
    sys.stderr.write = filtered_stderr_write

# Apply targeted fixes immediately
apply_targeted_async_fixes()

# Now import other libraries
import json
from mcp.types import TextContent, ImageContent
import chainlit as cl
from openai import  AsyncAzureOpenAI

from dotenv import load_dotenv
from mcp_client import MCPClient

load_dotenv(".env")

SYSTEM_PROMPT = """You are a helpful assistant with access to Neo4j graph database and HubSpot CRM through MCP tools. 
You can help users query and analyze data from both systems.

**Available Systems:**
- **Neo4j**: Graph database for complex relationship analysis
- **HubSpot**: CRM system for contacts, companies, deals, and marketing data

**Neo4j Tools:**
- `get_neo4j_schema`: Get the database schema (nodes, relationships, properties)
- `read_neo4j_cypher`: Execute read-only Cypher queries
- `write_neo4j_cypher`: Execute write Cypher queries (CREATE, UPDATE, DELETE)

**HubSpot Tools:**
- Various HubSpot API endpoints for managing contacts, companies, deals, etc.

**IMPORTANT WORKFLOW FOR DATA QUESTIONS:**

1. **First**: Always start by getting the schema/structure of the relevant system
   - For Neo4j: Use `get_neo4j_schema`
   - For HubSpot: Use appropriate listing tools to understand available data

2. **Second**: Be FLEXIBLE with natural language terms. When users mention:
   - Job titles (e.g., "surgeon") → explore similar/related terms that might exist
   - Categories or types → look for variations, partial matches, or related concepts
   - Properties → check what values actually exist in the database

3. **Third**: Use exploratory queries to understand the data before building the final query:
   - Query for similar/partial matches: `CONTAINS`, `STARTS WITH`, `ENDS WITH`
   - Explore actual values: `RETURN DISTINCT property_name` to see what's really there
   - Look for patterns and variations in the data

4. **Fourth**: Build the final query based on what you actually found in the database

5. **Finally**: Execute the optimized query and explain results

**Cross-System Analysis:**
When users ask questions that might involve both systems:
- Check if data exists in both Neo4j and HubSpot
- Look for opportunities to correlate data between systems
- Suggest data enrichment possibilities

**KEY PRINCIPLES:**
- 🔍 **Explore first**: Don't assume exact matches - explore what's actually in the systems
- 🎯 **Be inclusive**: Use CONTAINS, case-insensitive matching, and partial matches
- 📊 **Verify data**: Always check what values actually exist before building final queries
- 💡 **Learn and adapt**: If first query returns no results, explore alternatives
- 🔄 **Cross-reference**: Look for connections between Neo4j and HubSpot data

Always explain your exploration process to users so they understand how you found the relevant data."""

class ChatClient:
    def __init__(self) -> None:
        self.deployment_name = os.environ["AZURE_OPENAI_MODEL"]
        
        # Create client with good settings that still allow proper responses
        self.client = AsyncAzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ["OPENAI_API_VERSION"],
            timeout=60.0,
            max_retries=1,
        )
        self.messages = []
        self.system_prompt = SYSTEM_PROMPT
        
    async def process_response_stream(self, response_stream, tools, temperature=0):
        """Process response stream with targeted error handling"""
        function_arguments = ""
        function_name = ""
        tool_call_id = ""
        is_collecting_function_args = False
        collected_messages = []
        tool_called = False
        
        try:
            async for part in response_stream:
                if not part.choices:
                    continue
                    
                delta = part.choices[0].delta
                finish_reason = part.choices[0].finish_reason
                
                # Process assistant content
                if delta.content:
                    collected_messages.append(delta.content)
                    yield delta.content
                
                # Handle tool calls
                if delta.tool_calls and len(delta.tool_calls) > 0:
                    tool_call = delta.tool_calls[0]
                    
                    if tool_call.function.name:
                        function_name = tool_call.function.name
                        tool_call_id = tool_call.id
                    
                    if tool_call.function.arguments:
                        function_arguments += tool_call.function.arguments
                        is_collecting_function_args = True
                
                # Check if we've reached the end of a tool call
                if finish_reason == "tool_calls" and is_collecting_function_args:
                    try:
                        function_args = json.loads(function_arguments)
                    except json.JSONDecodeError:
                        print(f"JSON decode error for function arguments: {function_arguments}")
                        break
                    
                    # Find which MCP server has this tool
                    mcp_client = cl.user_session.get("mcp_client")
                    server_name = None
                    for srv_name, srv_tools in mcp_client.tools.items():
                        if any(tool.get("name") == function_name for tool in srv_tools):
                            server_name = srv_name
                            break

                    if server_name:
                        # Add the assistant message with tool call
                        self.messages.append({
                            "role": "assistant", 
                            "tool_calls": [{
                                "id": tool_call_id,
                                "function": {
                                    "name": function_name,
                                    "arguments": function_arguments
                                },
                                "type": "function"
                            }]
                        })
                        
                        # Call the tool and add response to messages
                        func_response = await call_tool(server_name, function_name, function_args)
                        self.messages.append({
                            "tool_call_id": tool_call_id,
                            "role": "tool",
                            "name": function_name,
                            "content": func_response,
                        })
                        
                        self.last_tool_called = function_name
                        tool_called = True
                    break
                
                # Check if we've reached the end of assistant's response
                if finish_reason == "stop":
                    if collected_messages:
                        final_content = ''.join([msg for msg in collected_messages if msg is not None])
                        if final_content.strip():
                            self.messages.append({"role": "assistant", "content": final_content})
                    break
                    
        except Exception as e:
            # Only suppress specific async cleanup errors
            error_str = str(e)
            if not any(pattern in error_str for pattern in [
                'async generator', 'GeneratorExit', 'StopAsyncIteration', 'cancel scope'
            ]):
                print(f"Stream processing error: {e}")
                # Still try to yield something useful
                yield f"I encountered an issue processing the response: {str(e)}"
        
        # Store result in instance variables
        self.tool_called = tool_called
        self.last_function_name = function_name if tool_called else None
    
    async def generate_response(self, human_input, tools, temperature=0):
        self.messages.append({"role": "user", "content": human_input})
        
        max_iterations = 5  # Prevent infinite loops
        current_iteration = 0
        
        while current_iteration < max_iterations:
            try:
                print(f"Making OpenAI API call (iteration {current_iteration + 1})...")
                
                response_stream = await self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=self.messages,
                    tools=tools,
                    parallel_tool_calls=False,
                    stream=True,
                    temperature=temperature,
                    max_tokens=2048,
                )
                
                # Stream and process the response
                response_generated = False
                async for token in self._stream_and_process(response_stream, tools, temperature):
                    response_generated = True
                    yield token
                
                # If no response was generated, yield an error message
                if not response_generated:
                    yield "I didn't generate a response. Please try asking your question again."
                
                # Check if we need to continue (tool was called)
                if not self.tool_called:
                    break
                    
                current_iteration += 1
                
            except Exception as e:
                error_str = str(e)
                print(f"Generate response error: {e}")
                
                # Only suppress specific async cleanup errors
                if any(pattern in error_str for pattern in [
                    'async generator', 'GeneratorExit', 'StopAsyncIteration'
                ]):
                    break  # Exit silently for cleanup errors
                else:
                    yield f"I encountered an error: {str(e)}. Please try again."
                    break

    async def _stream_and_process(self, response_stream, tools, temperature):
        """Helper method to yield tokens"""
        self.tool_called = False
        self.last_function_name = None
        
        async for token in self.process_response_stream(response_stream, tools, temperature):
            yield token

@cl.step(type="tool") 
async def call_tool(server_name, function_name, function_args):
    print(f"Calling tool: {function_name} on server: {server_name}")
    
    try:
        mcp_client = cl.user_session.get("mcp_client")
        if not mcp_client or server_name not in mcp_client.sessions:
            error_result = [{"type": "text", "text": f"Error: MCP server {server_name} not connected"}]
            return json.dumps(error_result)
        
        # Moderate delay between tool calls
        await asyncio.sleep(0.5)
        
        func_response = await mcp_client.call_tool(server_name, function_name, function_args)
        
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
        
        result = json.dumps(resp_items)
        print(f"Tool {function_name} executed successfully")
        return result
        
    except Exception as e:
        print(f"Tool execution error: {e}")
        error_result = [{"type": "text", "text": f"Error executing {function_name}: {str(e)}"}]
        return json.dumps(error_result)

@cl.on_chat_start
async def start_chat():
    """Initialize the chat session and connect to MCP servers"""
    msg = cl.Message(content="🔌 Connecting to Neo4j database and HubSpot CRM...")
    await msg.send()
    
    try:
        mcp_client = MCPClient()
        await mcp_client.connect_from_config("mcp_config.json")
        
        cl.user_session.set("mcp_client", mcp_client)
        cl.user_session.set("messages", [])
        cl.user_session.set("system_prompt", SYSTEM_PROMPT)
        
        connected_servers = list(mcp_client.sessions.keys())
        
        if not connected_servers:
            error_msg = """❌ Failed to connect to any MCP servers.

**Possible solutions:**
1. **For Neo4j:**
   - Check your Neo4j database is running and accessible
   - Verify your `.env` file has correct Neo4j credentials
   - Make sure `uvx` is installed: `pip install uvx`

2. **For HubSpot:**
   - Verify your HubSpot Private App token is correct
   - Check that `npx` is available (Node.js required)
   - Ensure the token has the necessary permissions

**I can still help with general queries, but I won't be able to execute them directly.**"""
            await cl.Message(content=error_msg).send()
            return
        
        tools = mcp_client.get_all_tools()
        neo4j_tools = [tool['name'] for tool in tools if tool.get('server') == 'neo4j']
        hubspot_tools = [tool['name'] for tool in tools if tool.get('server') == 'hubspot']
        
        success_msg = f"""✅ Connected to MCP servers! 

**Connected Systems:**
{f"🗄️  **Neo4j**: {', '.join(neo4j_tools)}" if neo4j_tools else "❌ Neo4j: Not connected"}
{f"🏢 **HubSpot**: {', '.join(hubspot_tools)}" if hubspot_tools else "❌ HubSpot: Not connected"}

🎯 **How I work:**
When you ask about your data, I will:
1. 📋 Check the relevant system's schema/structure
2. 🔍 Build the right query based on your data  
3. ⚡ Execute queries on your systems
4. 📊 Present results clearly
5. 🔄 Cross-reference data between systems when relevant

**Try asking questions like:**
• "What's in my Neo4j database?" 
• "Show me my HubSpot contacts"
• "How many nodes do I have in Neo4j?"
• "What companies are in HubSpot?"
• "Find connections between my Neo4j and HubSpot data"

I'll execute real queries on your actual data! 🚀"""
        await cl.Message(content=success_msg).send()
        
    except Exception as e:
        error_msg = f"""❌ Error during setup: {str(e)}

**I can still help with:**
• Writing Cypher queries for Neo4j
• Explaining HubSpot API concepts
• Database design advice

**But I won't be able to execute queries directly.**"""
        await cl.Message(content=error_msg).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages"""
    print(f"Received message: {message.content}")
    
    try:
        mcp_client = cl.user_session.get("mcp_client")
        
        if not mcp_client or not mcp_client.is_connected():
            await cl.Message(content="""⚠️ No active connections to Neo4j or HubSpot.

I can help you write queries and understand concepts, but I can't execute them directly.""").send()
            return
        
        tools = mcp_client.get_all_tools()
        if not tools:
            await cl.Message(content="⚠️ Connected to MCP servers but no tools available.").send()
            return
            
        openai_tools = [{"type": "function", "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"]
        }} for tool in tools]
        
        print(f"Available tools: {len(openai_tools)}")
        
        client = ChatClient()
        client.messages = cl.user_session.get("messages", [])
        
        if not client.messages:
            connected_servers = list(mcp_client.sessions.keys())
            available_tools_text = ', '.join([t['name'] for t in tools])
            
            enhanced_prompt = f"""{SYSTEM_PROMPT}

**Currently Connected:** {', '.join(connected_servers)}
**Available Tools:** {available_tools_text}

**Remember: Be EXPLORATORY and FLEXIBLE!**

When users mention terms like:
- "surgeon" → explore "vet surgeon", "heart surgeon", etc.
- "manager" → look for "project manager", "sales manager", etc.  
- "engineer" → find "software engineer", "civil engineer", etc.

ALWAYS explore what values actually exist in the systems before building final queries!

**Suggested Exploration Pattern:**
1. Get schema/structure → understand what's available
2. Exploratory queries → find actual values and patterns
3. Optimized final queries → get comprehensive results
4. Cross-system analysis → find connections between Neo4j and HubSpot data"""
            client.messages.append({"role": "system", "content": enhanced_prompt})
        
        msg = cl.Message(content="")
        
        print("Starting response generation...")
        
        response_generated = False
        async for text in client.generate_response(human_input=message.content, tools=openai_tools):
            response_generated = True
            await msg.stream_token(text)
        
        if not response_generated:
            await cl.Message(content="I didn't generate a response. Please try asking your question again.").send()
        
        cl.user_session.set("messages", client.messages)
        print("Response completed")
        
    except Exception as e:
        print(f"Message handling error: {e}")
        await cl.Message(content=f"An error occurred: {str(e)}. Please try again.").send()

async def safe_cleanup(mcp_client):
    """Safely cleanup MCP client connections"""
    try:
        await asyncio.wait_for(mcp_client.close_all(), timeout=2.0)
    except:
        pass

@cl.on_chat_end
async def end_chat():
    """Clean up when chat ends"""
    try:
        mcp_client = cl.user_session.get("mcp_client")
        if mcp_client:
            asyncio.create_task(safe_cleanup(mcp_client))
    except:
        pass

# if __name__ == "__main__":
    # import chainlit as cl
    # cl.run(host="127.0.0.1", port=9999)