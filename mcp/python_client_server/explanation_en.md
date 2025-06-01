# The USB-C for AI: Model Context Protocol Explained

The Model Context Protocol (MCP) is an open standard developed by Anthropic that standardizes how AI applications connect with external data sources, tools, and systems. Often compared to "USB for AI integrations," MCP transforms the complex M×N problem of connecting multiple AI applications with numerous data sources into a simpler M+N problem through a universal protocol. This overview explains the core concepts of MCP with practical Python implementation examples.

## Server: The foundation of MCP communication

The server component acts as a bridge between AI models and external systems, exposing standardized capabilities according to the MCP specification. It handles the communication protocol, negotiates capabilities, and manages the flow of data between clients and external systems.

```python
from mcp.server.fastmcp import FastMCP

# Create a simple MCP server
mcp = FastMCP("Demo Server")

# Configure for HTTP transport
mcp = FastMCP(
    "Analytics Server",
    dependencies=["pandas", "numpy"],
    stateless_http=True
)

# Run with specified transport
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)
```

Servers can use different transport mechanisms including stdio for local communication and HTTP for remote connections. They follow a client-host-server architecture where the host application (like Claude Desktop) contains clients that maintain connections with specific MCP servers.

## Resources: Structured data for context

Resources are a core MCP primitive that expose data and content to clients for use as context in LLM interactions. They represent any kind of data an MCP server wants to make available, providing a standardized way to share read-only information.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Resources Server")

@mcp.resource("config://app-version")
def get_app_version() -> str:
    """Returns the application version."""
    return "v2.1.0"

# Dynamic resources with templates
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting for a user"""
    return f"Hello, {name}!"
```

Resources have unique URIs and can contain text or binary data with appropriate metadata. They can be static (fixed content), dynamic (generated on request), or template-based (parameterized). Clients can list, read, and potentially subscribe to resources for updates.

## Tools: Executable functions for AI-driven actions

Tools are **model-controlled** executable functions that LLMs can call to perform specific actions or access external systems. They allow AI models to retrieve information or modify external systems based on user requests.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Calculator Server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
async def fetch_weather(city: str) -> str:
    """Fetch current weather for a city"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.weather.com/{city}")
        return response.text
```

Tools have defined input schemas (using JSON Schema), descriptive names, and can return responses in various formats including text, images, and embedded resources. They're exposed through standardized endpoints and can be synchronous or asynchronous.

## Prompts: Reusable interaction templates

Prompts are **user-controlled** templates or instructions that clients can surface to users for interacting with language models. They provide standardized patterns for common interactions and can be customized with arguments.

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

mcp = FastMCP("Prompts Server")

@mcp.prompt()
def review_code(code: str) -> str:
    """Generate a prompt asking for a code review."""
    return f"Please review this code:\n\n{code}"

@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    """Creates a structured debugging help session."""
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("Okay, I can help with that. Can you provide the full traceback and tell me what you were trying to do?")
    ]
```

Prompts can be simple templates or complex multi-message interactions. They can reference resources to incorporate server-managed content and include parameters that customize their behavior.

## Images: Supporting multimodal interactions

While not a separate primitive in the specification, image support is crucial for enabling multimodal interactions. Images can be embedded in resources and tool responses, allowing visual information to be shared between servers and clients.

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.types import Image
import io

mcp = FastMCP("Screenshot Demo", dependencies=["pyautogui", "Pillow"])

@mcp.tool()
def take_screenshot() -> Image:
    """
    Take a screenshot of the user's screen and return it as an image.
    Use this tool anytime the user wants you to look at something they're doing.
    """
    import pyautogui
    
    # Capture screenshot
    screenshot = pyautogui.screenshot()
    
    # Convert to bytes
    buffer = io.BytesIO()
    screenshot.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()
    
    # Return as MCP Image
    return Image(data=image_bytes, format="png")
```

Images are transmitted as base64-encoded data with appropriate MIME types. They can provide visual context for LLMs, be generated by tools, or serve as documentation.

## Context: Managing the information environment

The context component represents the information environment within which LLMs operate. While not a distinct primitive, context is a fundamental concept that MCP enhances by providing standardized access to external information.

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("Context Demo Server")

@mcp.tool()
async def process_large_file(file_uri: str, ctx: Context) -> str:
    """Process a large file with progress reporting and logging."""
    
    # Log message to client
    await ctx.info(f"Starting processing for {file_uri}")
    
    # Read resource using Context
    file_content_resource = await ctx.read_resource(file_uri)
    file_content = file_content_resource[0].content  # Assuming single text content
    
    # Report progress
    await ctx.report_progress(50, 100)
    await ctx.info(f"Processing {file_uri}")
    
    return f"Processed file with {len(file_content)} bytes."
```

The Context object provides access to MCP capabilities within tools and resources, enabling progress reporting, logging, resource access, and other functionality. It helps manage the limited context window of LLMs by organizing and prioritizing information.

## How these components work together

In a typical MCP implementation:

1. The server initializes and advertises its capabilities (tools, resources, and prompts)
2. Clients connect and negotiate protocol versions and capabilities
3. The host application makes resources and prompts available to users
4. When an LLM needs to use a tool, the host directs the client to send an invocation request to the appropriate server
5. The server executes the underlying logic and returns structured results

This standardized flow enables a growing ecosystem of compatible servers, clients, and tools that can work together seamlessly, significantly reducing development complexity while maintaining appropriate security boundaries.

## Conclusion

The Model Context Protocol represents a significant advancement in AI system interoperability. By providing a standardized way for AI models to access external data and functionality, MCP enables more context-aware, capable AI assistants while reducing integration complexity. Its modular, security-focused design allows developers to build tools that work across different AI models and platforms, fostering an ecosystem of interoperable components that can be mixed and matched as needed.




## What is SSE (Server-Sent Events)?

SSE (Server-Sent Events) is a web technology that allows a server to push updates to a client over a single HTTP connection. Unlike traditional HTTP requests where the client makes a request and the server responds once, SSE establishes a long-lived connection where:

1. The client opens a connection to the server
2. The server can continuously send data to the client without the client needing to make new requests
3. The connection remains open until explicitly closed by either party

Key characteristics of SSE:
- One-way communication (server to client)
- Text-based (usually sends data in JSON format)
- Built on standard HTTP, so it works through firewalls and proxies
- Automatically reconnects if the connection is lost
# Server (mcp_server_sse.py)

## Server-Side Explanation

This code implements a FastAPI server that exposes financial analysis tools through a server-sent events (SSE) interface. Here's what it does:

### 1. Financial Analysis Tools

The server implements several financial analysis tools using the `yfinance` library to download stock data and then apply various technical indicators:

- **MACD Score Calculator**: Calculates Moving Average Convergence Divergence scores
- **Donchian Channel Score Calculator**: Calculates scores based on Donchian Channels 
- **Combined MACD-Donchian Score**: Combines both indicators for a comprehensive signal
- **Bollinger-Fibonacci Score**: Integrates Bollinger Bands with Fibonacci retracement levels
- **Bollinger Z-Score Calculator**: Measures how many standard deviations a price is from its moving average

Each tool is implemented as a function that:
1. Downloads stock data using `yfinance`
2. Performs calculations using pandas and numpy
3. Returns formatted analysis results as a string

### 2. MCP Server Implementation

The code sets up a Message Control Protocol (MCP) server using FastMCP:

```python
mcp = FastMCP(name="Finance Tools")
transport = SseServerTransport("/messages/")
```

Each financial analysis function is registered as a tool with the MCP server using the `@mcp.tool()` decorator, making it available to be called remotely.

### 3. SSE Transport Layer

The server uses Server-Sent Events (SSE) as the transport mechanism:

```python
async def handle_sse(request):
    async with transport.connect_sse(request.scope, request.receive, request._send) as (in_stream, out_stream):
        await mcp._mcp_server.run(in_stream, out_stream, mcp._mcp_server.create_initialization_options())
```

This function:
- Establishes bidirectional communication over SSE
- Connects incoming requests to the MCP server
- Sends responses back to clients

### 4. API Endpoints

The server exposes two main endpoints:
- `/sse`: For establishing SSE connections
- `/messages/`: For handling message posting (part of the MCP protocol)

There's also a simple health check endpoint at `/health`.

## How Client and Server Work Together

Now that we've seen both the client and server code, here's how the whole system works together:

1. **Server Initialization**:
   - The server starts up on port 8100
   - It registers financial analysis tools with the MCP server
   - It sets up SSE endpoints for communication

2. **Client Connection**:
   - The client connects to the server via SSE (`http://localhost:8100/sse`)
   - It establishes an MCP session over this connection
   - It lists available tools from the server

3. **Processing User Queries**:
   - When a user asks something like "What is the z-score of AAPL for the last 20 days?"
   - The client uses GPT-4o-mini to identify which tool to use (e.g., `calculate_bollinger_z_score`)
   - The client sends a tool call with arguments (symbol="AAPL", period=20) to the server

4. **Server Processing**:
   - The server receives the tool call through the SSE connection
   - It runs the appropriate financial analysis function with the provided arguments
   - It returns the result back to the client via the SSE connection

5. **Result Handling**:
   - The client receives the tool response
   - It uses GPT-4o-mini again to format a user-friendly response
   - It presents the final answer to the user

## Overall Architecture

This is an example of an "agentic" system where:

1. Natural language queries are translated into specific tool calls
2. Specialized tools perform domain-specific calculations (financial analysis)
3. Results are translated back into user-friendly natural language

The system uses:
- **SSE** for real-time bidirectional communication
- **MCP** as the protocol for discovering and calling tools
- **yfinance** for financial data acquisition
- **GPT-4o-mini** for natural language understanding and response generation
- **FastAPI** for creating the server endpoints

This architecture allows financial analysis capabilities to be exposed as an API that can be integrated with a language model, creating an intelligent assistant that can perform complex financial calculations based on natural language requests.

# Client (mcp_client_sse_chat_improved.py)

This code creates an AI agent framework that uses SSE to communicate with a local server that provides various tools the agent can use. Here's a breakdown of what it does:

### 1. Overall Purpose

The code implements an intelligent chatbot agent that can:
- Understand user queries
- Determine which specialized tools are needed to answer those queries
- Call those tools with appropriate arguments
- Process the tool responses
- Either respond directly to the user or continue processing with additional tools

### 2. The SSE Connection

In this code, SSE is used to establish a connection with a tool server running at `http://localhost:8100/sse`. This server implements:

- The Message Control Protocol (MCP) - a protocol for interacting with specialized tools
- A way to discover what tools are available 
- A mechanism to call those tools with arguments

The code connects to this server using `sse_client` and creates an MCP session, which allows it to:
- List available tools
- Call specific tools with arguments
- Receive results from those tools

### 3. The Main Processing Flow

The agent's processing flow works like this:

1. **Receive user input**: The user types a query like "What is the z-score of AAPL for the last 20 days?"

2. **Tool selection**: The agent uses GPT-4o-mini to determine which tool should handle this query (like perhaps a financial data tool)

3. **SSE communication**: 
   - The agent connects to the tool server via SSE
   - Lists available tools
   - Selects the appropriate tool based on LLM recommendations
   - Sends the arguments to that tool (like ticker="AAPL", days=20)

4. **Process response**: When the tool returns results, the agent uses GPT-4o-mini again to:
   - Determine if the response answers the user's question completely
   - Format a user-friendly response or decide if more tool calls are needed

5. **Memory management**: The agent keeps track of the conversation history to provide context for future queries

### 4. Practical Example

If a user asks "What is the z-score of AAPL for the last 20 days?", the flow would be:

1. Agent receives query
2. Agent uses LLM to determine it needs a financial data tool
3. Agent connects to tool server via SSE
4. Agent calls the appropriate financial tool with arguments for AAPL and 20 days
5. Tool server processes the request and returns stock data
6. Agent uses LLM to calculate the z-score from the data or interpret the tool's calculation
7. Agent formats a user-friendly response
8. Agent presents the result to the user

### 5. Technical Implementation

The refactored code implements this using several specialized classes:

- **AgentProcessor**: Manages the SSE connection and tool processing pipeline
- **LLMClient**: Handles interactions with the language model
- **PromptGenerator**: Creates specialized prompts for different stages of processing
- **ResponseParser**: Parses and validates the JSON responses from the LLM and tools

The SSE-specific code appears primarily in the `process_query` method of the `AgentProcessor` class, which:
1. Establishes the SSE connection
2. Creates an MCP session
3. Lists available tools
4. Coordinates the tool selection and calling process

This architecture allows the agent to dynamically select and use specialized tools based on user queries, providing much more functionality than a simple chatbot that can only access its built-in knowledge.