from typing import Dict, List, Union
import streamlit as st
import logging

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage
from services.ai_service import create_llm_model
from utils.async_helpers import run_async, safe_reset_connection_state

async def setup_mcp_client(server_config: Dict[str, Dict]) -> MultiServerMCPClient:
    """Initialize a MultiServerMCPClient with the provided server configuration."""
    try:
        client = MultiServerMCPClient(server_config)
        return await client.__aenter__()
    except Exception as e:
        logging.error(f"Error setting up MCP client: {str(e)}")
        raise

async def get_tools_from_client(client: MultiServerMCPClient) -> List[BaseTool]:
    """Get tools from the MCP client."""
    try:
        return client.get_tools()
    except Exception as e:
        logging.error(f"Error getting tools from client: {str(e)}")
        raise

async def run_agent(agent, messages: Union[str, List[BaseMessage]]) -> Dict:
    """Run the agent with the provided message(s)."""
    try:
        if isinstance(messages, str):
            # If it's a string, treat it as a simple message
            return await agent.ainvoke({"messages": [messages]})
        elif isinstance(messages, list):
            # If it's a list of messages, use them directly for conversation memory
            return await agent.ainvoke({"messages": messages})
        else:
            # Fallback for other types
            return await agent.ainvoke({"messages": str(messages)})
    except Exception as e:
        logging.error(f"Error running agent: {str(e)}")
        raise

async def run_tool(tool, **kwargs):
    """Run a tool with the provided parameters."""
    try:
        return await tool.ainvoke(**kwargs)
    except Exception as e:
        logging.error(f"Error running tool: {str(e)}")
        raise

def connect_to_mcp_servers():
    """Connect to MCP servers with improved error handling."""
    try:
        # Show progress
        progress_container = st.empty()
        progress_container.info("🔄 Initializing connection to MCP servers...")
        
        # Clean up existing client if any
        cleanup_existing_client()
        
        # Collect LLM config dynamically from session state
        params = st.session_state.get('params', {})
        llm_provider = params.get("model_id")
        
        if not llm_provider:
            st.error("❌ No AI provider selected. Please configure in the Configuration tab.")
            return False
        
        progress_container.info(f"🤖 Creating {llm_provider} model instance...")
        
        try:
            llm = create_llm_model(
                llm_provider, 
                temperature=params.get('temperature', 0.7), 
                max_tokens=params.get('max_tokens', 4096)
            )
        except Exception as e:
            progress_container.empty()
            st.error(f"❌ Failed to initialize {llm_provider}: {str(e)}")
            
            # Show troubleshooting info
            with st.expander("🔧 Troubleshooting", expanded=True):
                st.markdown(f"""
                **Error initializing {llm_provider}:**
                
                1. **Check Configuration Tab:**
                   - Verify credentials are properly set
                   - Test the AI provider connection
                
                2. **Check Environment Variables:**
                   - Ensure all required variables are in your .env file
                   - Restart the application after adding variables
                
                3. **Provider-specific issues:**
                   - **OpenAI**: Check API key and credits
                   - **Azure OpenAI**: Verify endpoint, deployment, and API version
                
                **Error details:** `{str(e)}`
                """)
            return False
        
        progress_container.info("🔌 Connecting to MCP servers...")
        
        # Setup new client
        try:
            servers_config = st.session_state.get('servers', {})
            if not servers_config:
                progress_container.empty()
                st.error("❌ No MCP servers configured")
                return False
            
            st.session_state.client = run_async(setup_mcp_client(servers_config))
            
            if st.session_state.client is None:
                progress_container.empty()
                st.error("❌ Failed to create MCP client")
                return False
                
        except Exception as e:
            progress_container.empty()
            st.error(f"❌ Failed to connect to MCP servers: {str(e)}")
            
            # Show server-specific troubleshooting
            with st.expander("🔧 MCP Server Troubleshooting", expanded=True):
                st.markdown(f"""
                **MCP Server Connection Failed:**
                
                1. **Check Server Status:**
                   - Ensure MCP servers are running
                   - Verify server URLs in configuration
                
                2. **Network Issues:**
                   - Check if ports are accessible
                   - Verify firewall settings
                
                3. **Configuration Issues:**
                   - Check servers_config.json
                   - Verify server endpoints
                
                **Error details:** `{str(e)}`
                """)
            return False
        
        progress_container.info("🧰 Loading available tools...")
        
        # Get tools
        try:
            tools = run_async(get_tools_from_client(st.session_state.client))
            st.session_state.tools = tools if tools else []
            
            if not st.session_state.tools:
                progress_container.empty()
                st.warning("⚠️ No tools available from MCP servers")
                return False
                
        except Exception as e:
            progress_container.empty()
            st.error(f"❌ Failed to load tools: {str(e)}")
            return False
        
        progress_container.info("🤖 Creating AI agent...")
        
        # Create agent
        try:
            st.session_state.agent = create_react_agent(llm, st.session_state.tools)
            
            if st.session_state.agent is None:
                progress_container.empty()
                st.error("❌ Failed to create AI agent")
                return False
                
        except Exception as e:
            progress_container.empty()
            st.error(f"❌ Failed to create AI agent: {str(e)}")
            return False
        
        # Success
        progress_container.empty()
        
        # Show success message with details
        st.success("✅ Successfully connected to MCP servers!")
        
        # Show connection summary
        with st.container():
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🔌 Servers", len(st.session_state.get('servers', {})))
            
            with col2:
                st.metric("🧰 Tools", len(st.session_state.tools))
            
            with col3:
                st.metric("🤖 Provider", llm_provider)
        
        return True
        
    except Exception as e:
        st.error(f"❌ Unexpected error during connection: {str(e)}")
        logging.error(f"Unexpected error in connect_to_mcp_servers: {str(e)}")
        return False

def cleanup_existing_client():
    """Clean up existing client with proper error handling."""
    try:
        client = st.session_state.get("client")
        if client:
            try:
                print("🔄 Cleaning up existing MCP client...")
                run_async(client.__aexit__(None, None, None))
                print("✅ Existing client cleaned up")
            except Exception as e:
                print(f"⚠️ Warning: Error closing previous client: {str(e)}")
                # Continue anyway, don't fail the cleanup
        
        # Reset state
        st.session_state.client = None
        st.session_state.agent = None
        st.session_state.tools = []
        
    except Exception as e:
        logging.error(f"Error during client cleanup: {str(e)}")
        print(f"⚠️ Warning: Error during cleanup: {str(e)}")

def disconnect_from_mcp_servers():
    """Disconnect from MCP servers with proper error handling."""
    try:
        # Clean up existing client if any and session state connections
        client = st.session_state.get("client")
        if client:
            try:
                print("🚪 Disconnecting from MCP servers...")
                run_async(client.__aexit__(None, None, None))
                print("✅ Disconnected successfully")
                st.success("✅ Disconnected from MCP servers")
            except Exception as e:
                print(f"⚠️ Warning: Error during disconnect: {str(e)}")
                st.warning(f"⚠️ Disconnect completed with warnings: {str(e)}")
        else:
            st.info("ℹ️ No active MCP connections to disconnect")

        # Clean up session state
        st.session_state.client = None
        st.session_state.tools = []
        st.session_state.agent = None
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error during disconnect: {str(e)}")
        logging.error(f"Error in disconnect_from_mcp_servers: {str(e)}")
        
        # Force cleanup even if there were errors
        st.session_state.client = None
        st.session_state.tools = []
        st.session_state.agent = None
        
        return False

def get_connection_health():
    """Get detailed connection health information."""
    try:
        health = {
            "client_status": "disconnected",
            "agent_status": "unavailable", 
            "tools_count": 0,
            "servers_configured": 0,
            "last_error": None
        }
        
        # Check client
        if st.session_state.get("client") is not None:
            health["client_status"] = "connected"
        
        # Check agent
        if st.session_state.get("agent") is not None:
            health["agent_status"] = "available"
        
        # Check tools
        tools = st.session_state.get("tools", [])
        health["tools_count"] = len(tools)
        
        # Check servers
        servers = st.session_state.get("servers", {})
        health["servers_configured"] = len(servers)
        
        return health
        
    except Exception as e:
        logging.error(f"Error getting connection health: {str(e)}")
        return {
            "client_status": "error",
            "agent_status": "error",
            "tools_count": 0,
            "servers_configured": 0,
            "last_error": str(e)
        }

def test_mcp_connection():
    """Test MCP connection and return detailed results."""
    try:
        health = get_connection_health()
        
        if health["client_status"] == "connected" and health["agent_status"] == "available":
            return {
                "success": True,
                "message": f"Connection healthy: {health['tools_count']} tools available",
                "details": health
            }
        else:
            return {
                "success": False,
                "message": f"Connection issues: Client={health['client_status']}, Agent={health['agent_status']}",
                "details": health
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Test failed: {str(e)}",
            "details": {"error": str(e)}
        }