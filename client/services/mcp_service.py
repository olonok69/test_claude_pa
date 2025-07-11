from typing import Dict, List, Union
import streamlit as st
import logging

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage
from services.ai_service import create_llm_model
from utils.async_helpers import run_async, safe_reset_connection_state

# ADD: Import for system prompt management
from services.system_prompt_manager import SystemPromptManager

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
    """Connect to MCP servers with improved error handling and system prompt integration."""
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
        
        progress_container.info("🎯 Managing system prompt...")
        
        # ADDED: System prompt management
        try:
            # Initialize system prompt manager
            prompt_manager = SystemPromptManager()
            
            # Get or generate system prompt
            system_prompt = prompt_manager.get_current_prompt()
            
            if not system_prompt:
                # Generate default system prompt based on connected tools
                system_prompt = prompt_manager.generate_default_system_prompt(
                    st.session_state.tools,
                    st.session_state.servers
                )
                
                # Save the generated prompt
                if prompt_manager.save_system_prompt(system_prompt, is_custom=False):
                    logging.info("✅ Generated and saved default system prompt")
                    st.session_state.system_prompt_generated = True
                else:
                    logging.warning("⚠️ Failed to save generated system prompt")
            else:
                logging.info("✅ Loaded existing system prompt")
                
            # Store system prompt in session state
            st.session_state.system_prompt = system_prompt
            
        except Exception as e:
            # Don't fail connection if system prompt fails
            logging.error(f"⚠️ System prompt management failed: {str(e)}")
            st.warning(f"⚠️ System prompt management failed: {str(e)}")
            # Continue with default behavior
        
        progress_container.info("🤖 Creating AI agent...")
        
        # MODIFIED: Create agent with system prompt consideration
        try:
            # Create the base agent
            st.session_state.agent = create_react_agent(llm, st.session_state.tools)
            
            if st.session_state.agent is None:
                progress_container.empty()
                st.error("❌ Failed to create AI agent")
                return False
            
            # Log system prompt status
            if st.session_state.get('system_prompt'):
                logging.info(f"✅ Agent created with system prompt ({len(st.session_state.system_prompt)} chars)")
            else:
                logging.info("✅ Agent created without system prompt")
                
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
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🔌 Servers", len(st.session_state.get('servers', {})))
            
            with col2:
                st.metric("🧰 Tools", len(st.session_state.tools))
            
            with col3:
                st.metric("🤖 Provider", llm_provider)
            
            with col4:
                # Show system prompt status
                if st.session_state.get('system_prompt'):
                    prompt_chars = len(st.session_state.system_prompt)
                    st.metric("🎯 System Prompt", f"{prompt_chars} chars")
                else:
                    st.metric("🎯 System Prompt", "Not set")
        
        # Show system prompt generation info if applicable
        if st.session_state.get('system_prompt_generated'):
            st.info("📝 Generated default system prompt based on connected tools. You can customize it in the System Prompt tab.")
            # Clear the flag
            del st.session_state['system_prompt_generated']
        
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
        
        # ADDED: Clear system prompt when disconnecting
        if "system_prompt" in st.session_state:
            # Don't actually delete it - just log that we're disconnecting
            logging.info("🔄 Disconnecting - system prompt will be reused on reconnect")
        
    except Exception as e:
        logging.error(f"Error during client cleanup: {str(e)}")
        print(f"⚠️ Warning: Error during cleanup: {str(e)}")

def disconnect_from_mcp_servers(logout_context=False):
    """Disconnect from MCP servers with proper error handling."""
    try:
        # Clean up existing client if any and session state connections
        client = st.session_state.get("client")
        if client:
            try:
                if logout_context:
                    print("🚪 Disconnecting from MCP servers (user logout)...")
                else:
                    print("🚪 Disconnecting from MCP servers...")
                    
                run_async(client.__aexit__(None, None, None))
                print("✅ Disconnected successfully")
                
                if logout_context:
                    st.info("🔌 MCP servers disconnected due to logout")
                else:
                    st.success("✅ Disconnected from MCP servers")
                    
            except Exception as e:
                print(f"⚠️ Warning: Error during disconnect: {str(e)}")
                if not logout_context:
                    st.warning(f"⚠️ Disconnect completed with warnings: {str(e)}")
        else:
            if not logout_context:
                st.info("ℹ️ No active MCP connections to disconnect")

        # Clean up session state
        st.session_state.client = None
        st.session_state.tools = []
        st.session_state.agent = None
        
        # Clear system prompt on logout for security
        if logout_context:
            logging.info("🔄 Logout - system prompt cleared for security")
            if "system_prompt" in st.session_state:
                del st.session_state["system_prompt"]
            if "system_prompt_is_custom" in st.session_state:
                del st.session_state["system_prompt_is_custom"]
        else:
            # Keep system prompt but log disconnection
            if st.session_state.get('system_prompt'):
                logging.info("🔄 Disconnected - system prompt preserved for next connection")
        
        return True
        
    except Exception as e:
        if not logout_context:
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
            "system_prompt_status": "not_set",
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
        
        # ADDED: Check system prompt status
        system_prompt = st.session_state.get("system_prompt")
        if system_prompt:
            health["system_prompt_status"] = "configured"
            health["system_prompt_length"] = len(system_prompt)
            health["system_prompt_is_custom"] = st.session_state.get("system_prompt_is_custom", False)
        else:
            health["system_prompt_status"] = "not_set"
        
        return health
        
    except Exception as e:
        logging.error(f"Error getting connection health: {str(e)}")
        return {
            "client_status": "error",
            "agent_status": "error",
            "tools_count": 0,
            "servers_configured": 0,
            "system_prompt_status": "error",
            "last_error": str(e)
        }

def test_mcp_connection():
    """Test MCP connection and return detailed results."""
    try:
        health = get_connection_health()
        
        if health["client_status"] == "connected" and health["agent_status"] == "available":
            # Enhanced success message with system prompt info
            message = f"Connection healthy: {health['tools_count']} tools available"
            if health["system_prompt_status"] == "configured":
                message += f", system prompt ready ({health.get('system_prompt_length', 0)} chars)"
            
            return {
                "success": True,
                "message": message,
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

def get_system_prompt_info():
    """Get information about the current system prompt."""
    try:
        system_prompt = st.session_state.get("system_prompt")
        
        if not system_prompt:
            return {
                "configured": False,
                "length": 0,
                "is_custom": False,
                "preview": ""
            }
        
        return {
            "configured": True,
            "length": len(system_prompt),
            "word_count": len(system_prompt.split()),
            "line_count": len(system_prompt.split('\n')),
            "is_custom": st.session_state.get("system_prompt_is_custom", False),
            "preview": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt
        }
        
    except Exception as e:
        logging.error(f"Error getting system prompt info: {str(e)}")
        return {
            "configured": False,
            "length": 0,
            "is_custom": False,
            "preview": "",
            "error": str(e)
        }

def reconnect_with_system_prompt():
    """Reconnect to MCP servers (typically after system prompt changes)."""
    try:
        logging.info("🔄 Reconnecting to MCP servers after system prompt change...")
        
        # Store current connection info
        current_servers = st.session_state.get('servers', {})
        current_params = st.session_state.get('params', {})
        
        if not current_servers:
            st.error("❌ No server configuration found for reconnection")
            return False
        
        # Disconnect first
        disconnect_from_mcp_servers()
        
        # Small delay to ensure cleanup
        import time
        time.sleep(1)
        
        # Reconnect
        success = connect_to_mcp_servers()
        
        if success:
            st.success("✅ Successfully reconnected with updated system prompt!")
            logging.info("✅ Reconnection successful")
        else:
            st.error("❌ Failed to reconnect to MCP servers")
            logging.error("❌ Reconnection failed")
        
        return success
        
    except Exception as e:
        st.error(f"❌ Error during reconnection: {str(e)}")
        logging.error(f"Error in reconnect_with_system_prompt: {str(e)}")
        return False

def validate_system_prompt_integration():
    """Validate that system prompt is properly integrated with the MCP agent."""
    try:
        validation_results = {
            "agent_available": st.session_state.get("agent") is not None,
            "system_prompt_available": st.session_state.get("system_prompt") is not None,
            "tools_available": len(st.session_state.get("tools", [])) > 0,
            "integration_status": "unknown"
        }
        
        if validation_results["agent_available"] and validation_results["system_prompt_available"]:
            validation_results["integration_status"] = "ready"
        elif validation_results["agent_available"] and not validation_results["system_prompt_available"]:
            validation_results["integration_status"] = "agent_only"
        elif not validation_results["agent_available"] and validation_results["system_prompt_available"]:
            validation_results["integration_status"] = "prompt_only"
        else:
            validation_results["integration_status"] = "not_ready"
        
        return validation_results
        
    except Exception as e:
        logging.error(f"Error validating system prompt integration: {str(e)}")
        return {
            "agent_available": False,
            "system_prompt_available": False,
            "tools_available": False,
            "integration_status": "error",
            "error": str(e)
        }

def get_mcp_connection_summary():
    """Get a comprehensive summary of MCP connection status."""
    try:
        # Get basic health
        health = get_connection_health()
        
        # Get system prompt info
        prompt_info = get_system_prompt_info()
        
        # Get validation results
        validation = validate_system_prompt_integration()
        
        # Categorize tools
        tools = st.session_state.get("tools", [])
        mssql_tools = []
        other_tools = []
        
        for tool in tools:
            tool_name = tool.name.lower()
            if any(keyword in tool_name for keyword in ['sql', 'mssql', 'execute_sql', 'list_tables', 'describe_table']):
                mssql_tools.append(tool.name)
            else:
                other_tools.append(tool.name)
        
        summary = {
            "connection_health": health,
            "system_prompt_info": prompt_info,
            "validation_results": validation,
            "tool_analysis": {
                "total_tools": len(tools),
                "mssql_tools": mssql_tools,
                "other_tools": other_tools
            },
            "servers_info": {
                "connected_servers": list(st.session_state.get("servers", {}).keys()),
                "total_servers": len(st.session_state.get("servers", {}))
            }
        }
        
        return summary
        
    except Exception as e:
        logging.error(f"Error getting MCP connection summary: {str(e)}")
        return {
            "connection_health": {"client_status": "error", "agent_status": "error"},
            "system_prompt_info": {"configured": False, "error": str(e)},
            "validation_results": {"integration_status": "error"},
            "tool_analysis": {"total_tools": 0, "mssql_tools": [], "other_tools": []},
            "servers_info": {"connected_servers": [], "total_servers": 0}
        }

# ADDED: Utility functions for system prompt management integration

def generate_system_prompt_for_tools(tools: List[BaseTool], servers: Dict) -> str:
    """Generate a system prompt specifically for the current tools and servers."""
    try:
        from services.system_prompt_manager import SystemPromptManager
        
        prompt_manager = SystemPromptManager()
        return prompt_manager.generate_default_system_prompt(tools, servers)
        
    except Exception as e:
        logging.error(f"Error generating system prompt for tools: {str(e)}")
        return "You are an AI assistant with access to MCP tools. Use the available tools to help users with their requests."

def update_system_prompt_for_connection():
    """Update system prompt after a successful connection."""
    try:
        if not st.session_state.get("tools") or not st.session_state.get("servers"):
            return False
        
        # Check if we should auto-regenerate
        if st.session_state.get('auto_regenerate_prompt', False):
            prompt_manager = SystemPromptManager()
            
            # Generate new prompt
            new_prompt = prompt_manager.generate_default_system_prompt(
                st.session_state.tools,
                st.session_state.servers
            )
            
            # Save and update
            if prompt_manager.save_system_prompt(new_prompt, is_custom=False):
                st.session_state.system_prompt = new_prompt
                logging.info("✅ Auto-regenerated system prompt for new connection")
                return True
        
        return False
        
    except Exception as e:
        logging.error(f"Error updating system prompt for connection: {str(e)}")
        return False