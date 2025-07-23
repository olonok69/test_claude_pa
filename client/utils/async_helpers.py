# client/utils/async_helpers.py - Enhanced version

import streamlit as st
import asyncio
import os
from typing import Optional, Tuple
from services.ai_service import create_llm_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent


# Helper function for running async functions
def run_async(coro):
    """Run an async function within the stored event loop."""
    return st.session_state.loop.run_until_complete(coro)


def reset_connection_state():
    """Reset all connection-related session state variables."""
    if st.session_state.client is not None:
        try:
            # Close the existing client properly
            run_async(st.session_state.client.__aexit__(None, None, None))
        except Exception as e:
            st.error(f"Error closing previous client: {str(e)}")

    st.session_state.client = None
    st.session_state.agent = None
    st.session_state.tools = []


def on_shutdown():
    # Proper cleanup when the session ends
    if st.session_state.client is not None:
        try:
            # Close the client properly
            run_async(st.session_state.client.__aexit__(None, None, None))
        except Exception as e:
            st.error(f"Error during shutdown: {str(e)}")


async def create_perplexity_research_client() -> Tuple[bool, Optional[object], str]:
    """
    Create a dedicated MCP client for Perplexity research

    Returns:
        success: bool
        agent: Optional[object] - Created agent or None
        message: str - Status message
    """
    try:
        # Perplexity server configuration
        perplexity_config = {
            "Perplexity Search": {
                "transport": "sse",
                "url": os.getenv("PERPLEXITY_SERVER_URL", "http://mcpserver3:8003/sse"),
                "timeout": 600,
                "headers": None,
                "sse_read_timeout": 900,
            }
        }

        # Create LLM
        llm = create_llm_model("Anthropic", temperature=0.7, max_tokens=4096)

        # Setup MCP client
        client = MultiServerMCPClient(perplexity_config)
        await client.__aenter__()

        # Get tools
        tools = client.get_tools()

        # Verify we have perplexity tools
        perplexity_tools = [tool for tool in tools if "perplexity" in tool.name.lower()]

        if not perplexity_tools:
            await client.__aexit__(None, None, None)
            return False, None, "No Perplexity tools found in server response"

        # Create agent
        agent = create_react_agent(llm, tools)

        return (
            True,
            agent,
            f"Created research client with {len(perplexity_tools)} Perplexity tools",
        )

    except Exception as e:
        return False, None, f"Failed to create research client: {str(e)}"


def get_best_available_agent() -> Tuple[Optional[object], str, str]:
    """
    Get the best available agent for research

    Returns:
        agent: Optional[object] - Agent or None
        agent_type: str - 'main', 'dedicated', or 'none'
        status_message: str - Status description
    """
    # First try to use the main MCP agent from session state
    main_agent = st.session_state.get("agent")
    if main_agent:
        # Check if perplexity tools are available
        main_tools = st.session_state.get("tools", [])
        perplexity_tools = [
            tool for tool in main_tools if "perplexity" in tool.name.lower()
        ]
        if perplexity_tools:
            return (
                main_agent,
                "main",
                f"Using main agent with {len(perplexity_tools)} Perplexity tools",
            )

    return None, "none", "No suitable agent available"


async def run_research_with_agent(agent, prompt: str) -> Tuple[bool, str]:
    """
    Run research using the provided agent and prompt

    Args:
        agent: The MCP agent to use
        prompt: Research prompt to execute

    Returns:
        success: bool
        response_text: str - Either response text or error message
    """
    try:
        from langchain_core.messages import HumanMessage
        from services.mcp_service import run_agent

        # Create conversation memory
        conversation_memory = [HumanMessage(content=prompt)]

        # Run the agent
        response = await run_agent(agent, conversation_memory)

        # Extract response text and check for tool execution
        response_text = ""
        tool_executed = False

        if "messages" in response:
            # Skip the original conversation memory
            new_messages = response["messages"][len(conversation_memory) :]

            for msg in new_messages:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    # Check if perplexity tool was executed
                    for tool_call in msg.tool_calls:
                        if "perplexity" in tool_call.get("name", "").lower():
                            tool_executed = True
                            break
                elif hasattr(msg, "content") and msg.content:
                    response_text += str(msg.content) + "\n"

        if not tool_executed:
            return False, "No Perplexity research tools were executed"

        if not response_text.strip():
            return False, "No response text received from AI agent"

        return True, response_text.strip()

    except Exception as e:
        return False, f"Error running research: {str(e)}"


def initialize_event_loop():
    """Initialize the event loop for async operations"""
    if "loop" not in st.session_state:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        st.session_state["loop"] = loop


def run_research_safely(research_func, *args, **kwargs):
    """
    Safely run research function with proper async handling

    Args:
        research_func: Async function to run
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Result of the research function
    """
    try:
        # Ensure event loop is initialized
        initialize_event_loop()

        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(research_func(*args, **kwargs))

        return result

    except Exception as e:
        return False, f"Error in research execution: {str(e)}", None
    finally:
        # Clean up the loop
        try:
            loop.close()
        except:
            pass


# Convenience function for wheat production research
async def run_wheat_production_research(
    db_helper, current_data
) -> Tuple[bool, str, Optional[dict]]:
    """
    Run research specifically for wheat production data

    Args:
        db_helper: Database helper instance
        current_data: Current wheat production data

    Returns:
        success: bool
        message: str
        parsed_data: Optional[dict]
    """
    from utils.ai_research_components import AIResearchManager

    # Create research manager
    research_manager = AIResearchManager("wheat", "production", db_helper)

    # Run research
    return await research_manager.research_data()


# Error handling wrapper
def handle_research_errors(func):
    """Decorator to handle common research errors"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except asyncio.TimeoutError:
            return False, "Research timed out. Please try again.", None
        except ConnectionError:
            return (
                False,
                "Could not connect to Perplexity server. Check connection.",
                None,
            )
        except Exception as e:
            return False, f"Unexpected error: {str(e)}", None

    return wrapper
