# client/ui_components/logout_warning.py
import streamlit as st

def show_mcp_logout_warning():
    """Show warning about MCP disconnection on logout."""
    if st.session_state.get("agent") is not None:
        with st.sidebar:
            st.warning("⚠️ MCP servers will disconnect when you log out")
            
            # Show reconnection info
            with st.expander("ℹ️ After Logout", expanded=False):
                st.markdown("""
                **What happens when you log out:**
                - MCP servers will be disconnected
                - All tools will be released
                - System prompts will be cleared
                - Chat history remains saved
                
                **To reconnect after login:**
                1. Go to Configuration tab
                2. Set up your AI provider
                3. Go to Connections tab
                4. Connect to MCP servers
                5. System prompts will be regenerated
                """)

def show_connection_status_on_logout():
    """Show current connection status that will be affected by logout."""
    if st.session_state.get("agent") is not None:
        tool_count = len(st.session_state.get("tools", []))
        server_count = len(st.session_state.get("servers", {}))
        
        with st.sidebar:
            st.info(f"🔌 Active: {server_count} servers, {tool_count} tools")
            
            if st.session_state.get("system_prompt"):
                prompt_length = len(st.session_state.system_prompt)
                st.info(f"🎯 System prompt: {prompt_length} characters")