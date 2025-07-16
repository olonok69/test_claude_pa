import streamlit as st
from services.chat_service import create_chat, delete_chat, switch_chat


def categorize_tools_for_sidebar(tools):
    """Categorize tools by server type for sidebar display."""
    neo4j_tools = 0
    hubspot_tools = 0
    mssql_tools = 0
    other_tools = 0
    
    for tool in tools:
        tool_name_lower = tool.name.lower()
        tool_desc_lower = tool.description.lower() if hasattr(tool, 'description') and tool.description else ""
        
        # Neo4j tool detection
        if any(keyword in tool_name_lower for keyword in ['neo4j', 'cypher', 'graph']):
            neo4j_tools += 1
        # HubSpot tool detection
        elif any(keyword in tool_name_lower for keyword in ['hubspot', 'crm']) or tool_name_lower.startswith('hubspot'):
            hubspot_tools += 1
        # MSSQL tool detection - improved logic
        elif (any(keyword in tool_name_lower for keyword in ['sql', 'mssql', 'execute_sql', 'list_tables', 'describe_table', 'get_table_sample']) or
              any(keyword in tool_desc_lower for keyword in ['sql', 'mssql', 'database', 'table', 'execute'])):
            mssql_tools += 1
        else:
            other_tools += 1
    
    return neo4j_tools, hubspot_tools, mssql_tools, other_tools


def create_history_chat_container():
    """Create the chat history container in the sidebar."""
    # Only show chat history if user is authenticated
    if not st.session_state.get("authentication_status"):
        return
    
    st.subheader("💬 Chat History")
    
    history_container = st.container(height=300, border=True)
    with history_container:
        chat_history_menu = [
                f"{chat['chat_name']}_::_{chat['chat_id']}"
                for chat in st.session_state["history_chats"]
            ]
        chat_history_menu = chat_history_menu[:50][::-1]
        
        if chat_history_menu:
            # Get current selection index
            current_selection = None
            for i, chat_option in enumerate(chat_history_menu):
                chat_id = chat_option.split("_::_")[1]
                if chat_id == st.session_state.get("current_chat_id"):
                    current_selection = i
                    break
            
            if current_selection is None:
                current_selection = 0
            
            selected_chat = st.radio(
                label="Select Chat",
                format_func=lambda x: x.split("_::_")[0] + '...' if "_::_" in x else x,
                options=chat_history_menu,
                label_visibility="collapsed",
                index=current_selection,
                key="chat_selector"
            )
            
            if selected_chat:
                selected_chat_id = selected_chat.split("_::_")[1]
                # Only switch if it's a different chat
                if selected_chat_id != st.session_state.get("current_chat_id"):
                    switch_chat(selected_chat_id)
                    st.rerun()


def create_sidebar_chat_buttons():
    """Create chat management buttons in the sidebar."""
    # Only show chat buttons if user is authenticated
    if not st.session_state.get("authentication_status"):
        return
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        create_chat_button = st.button(
            "🆕 New Chat", 
            use_container_width=True, 
            key="create_chat_button",
            help="Start a new conversation"
        )
        if create_chat_button:
            create_chat()
            st.rerun()

    with col2:
        delete_chat_button = st.button(
            "🗑️ Delete", 
            use_container_width=True, 
            key="delete_chat_button",
            help="Delete current conversation"
        )
        if delete_chat_button and st.session_state.get('current_chat_id'):
            delete_chat(st.session_state['current_chat_id'])
            st.rerun()

    # Quick stats
    st.markdown("---")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Chats", len(st.session_state.get("history_chats", [])))
        with col2:
            current_messages = len(st.session_state.get("messages", []))
            st.metric("Messages", current_messages)

    # Quick status indicators
    st.markdown("---")
    st.markdown("**🔌 Quick Status:**")
    
    # Connection status
    if st.session_state.get("agent"):
        st.success("🟢 Connected to MCP")
    else:
        st.error("🔴 Not Connected")
    
    # Provider status  
    provider = st.session_state.get('params', {}).get('model_id', 'Not Set')
    st.info(f"🤖 Provider: {provider}")
    
    # Tools count with categorization
    tools_count = len(st.session_state.get('tools', []))
    st.info(f"🧰 Total Tools: {tools_count}")
    
    # Show tool breakdown if tools are available
    if tools_count > 0:
        neo4j_count, hubspot_count, mssql_count, other_count = categorize_tools_for_sidebar(st.session_state.get('tools', []))
        
        with st.container():
            st.markdown("**Tool Breakdown:**")
            if neo4j_count > 0:
                st.text(f"🗄️ Neo4j: {neo4j_count}")
            if hubspot_count > 0:
                st.text(f"🏢 HubSpot: {hubspot_count}")
            if mssql_count > 0:
                st.text(f"🗃️ MSSQL: {mssql_count}")
            if other_count > 0:
                st.text(f"🔧 Other: {other_count}")


def create_user_info_sidebar():
    """Create user information section in sidebar for authenticated users."""
    if st.session_state.get("authentication_status"):
        st.markdown("---")
        st.markdown("### 👤 User Information")
        
        with st.container(border=True):
            st.markdown(f"**Name:** {st.session_state.get('name', 'N/A')}")
            st.markdown(f"**Username:** {st.session_state.get('username', 'N/A')}")
            
            # Add session info
            import datetime
            if "login_time" not in st.session_state:
                st.session_state["login_time"] = datetime.datetime.now()
            
            session_time = datetime.datetime.now() - st.session_state["login_time"]
            hours, remainder = divmod(int(session_time.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            
            st.markdown(f"**Session Time:** {hours:02d}:{minutes:02d}")


# Legacy functions maintained for backward compatibility but not used in new tab layout
def create_provider_select_widget():
    """Legacy function - moved to tab_components.py"""
    pass

def create_advanced_configuration_widget():
    """Legacy function - moved to tab_components.py"""
    pass

def create_mcp_connection_widget():
    """Legacy function - moved to tab_components.py"""
    pass

def create_mcp_tools_widget():
    """Legacy function - moved to tab_components.py"""
    pass