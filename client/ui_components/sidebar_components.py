# Updated ui_components/sidebar_components.py with user session isolation and chat settings

import streamlit as st
import os
from services.chat_service import create_chat, delete_chat, switch_chat
from ui_components.chat_settings_component import create_chat_settings_sidebar, create_advanced_chat_settings, create_chat_actions_panel


def create_sidebar_header_with_icon():
    """Create sidebar header with logo and title at the very top."""
    # Check if Logo.png exists (updated path for mcp-chatbot)
    icon_path = os.path.join('.', 'icons', 'Logo.png')
    
    if os.path.exists(icon_path):
        # Create columns for better layout
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.image(icon_path, width=60)
        
        with col2:
            st.markdown("""
            <div style="padding-top: 10px;">
                <h3 style="margin: 0; color: #2F2E78;">CloserStill Media</h3>
                <p style="margin: 0; font-size: 12px; color: #666;">MCP Client</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Fallback if icon doesn't exist
        st.markdown("""
        <div class="icon-text-container">
            <span>🔍 MCP Client</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Add separator
    st.markdown("---")


def categorize_tools_for_sidebar(tools):
    """Categorize tools by server type for sidebar display."""
    mssql_tools = 0
    other_tools = 0
    
    for tool in tools:
        tool_name_lower = tool.name.lower()
        tool_desc_lower = tool.description.lower() if hasattr(tool, 'description') and tool.description else ""
        
        # MSSQL tool detection - improved logic
        if (any(keyword in tool_name_lower for keyword in ['sql', 'mssql', 'execute_sql', 'list_tables', 'describe_table', 'get_table_sample']) or
              any(keyword in tool_desc_lower for keyword in ['sql', 'mssql', 'database', 'table', 'execute'])):
            mssql_tools += 1
        else:
            other_tools += 1
    
    return mssql_tools, other_tools


def create_history_chat_container():
    """Create the chat history container in the sidebar with user session isolation."""
    # Only show chat history if user is authenticated
    current_user = st.session_state.get('username')
    if not current_user or not st.session_state.get("authentication_status"):
        return
    
    st.subheader("💬 Chat History")
    
    # Get user-specific chat history
    user_history_key = f"user_{current_user}_history_chats"
    user_chats = st.session_state.get(user_history_key, [])
    
    history_container = st.container(height=300, border=True)
    with history_container:
        if not user_chats:
            st.info("No chat history yet")
            return
        
        chat_history_menu = [
            f"{chat['chat_name']}_::_{chat['chat_id']}"
            for chat in user_chats
            if chat.get('created_by') == current_user  # Only show chats created by current user
        ]
        chat_history_menu = chat_history_menu[:50][::-1]  # Limit and reverse order
        
        if chat_history_menu:
            # Get current selection index
            current_chat_id = st.session_state.get("current_chat_id")
            current_selection = None
            
            for i, chat_option in enumerate(chat_history_menu):
                chat_id = chat_option.split("_::_")[1]
                if chat_id == current_chat_id:
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
                key=f"chat_selector_{current_user}"  # User-specific key
            )
            
            if selected_chat:
                selected_chat_id = selected_chat.split("_::_")[1]
                # Only switch if it's a different chat
                if selected_chat_id != current_chat_id:
                    switch_chat(selected_chat_id)
                    st.rerun()
        else:
            st.info("No chats for current user")


def create_sidebar_chat_buttons():
    """Create chat management buttons in the sidebar with user session isolation."""
    # Only show chat buttons if user is authenticated
    current_user = st.session_state.get('username')
    if not current_user or not st.session_state.get("authentication_status"):
        return
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        create_chat_button = st.button(
            "🆕 New Chat", 
            use_container_width=True, 
            key=f"create_chat_button_{current_user}",  # User-specific key
            help="Start a new conversation"
        )
        if create_chat_button:
            create_chat()
            st.rerun()

    with col2:
        current_chat_id = st.session_state.get('current_chat_id')
        delete_chat_button = st.button(
            "🗑️ Delete", 
            use_container_width=True, 
            key=f"delete_chat_button_{current_user}",  # User-specific key
            help="Delete current conversation"
        )
        if delete_chat_button and current_chat_id:
            delete_chat(current_chat_id)
            st.rerun()

    # Quick stats for current user
    st.markdown("---")
    with st.container():
        col1, col2 = st.columns(2)
        
        # Get user-specific statistics
        user_history_key = f"user_{current_user}_history_chats"
        user_messages_key = f"user_{current_user}_messages"
        
        user_chats = st.session_state.get(user_history_key, [])
        user_messages = st.session_state.get(user_messages_key, [])
        
        # Filter chats to only include those created by current user
        user_owned_chats = [chat for chat in user_chats if chat.get('created_by') == current_user]
        
        with col1:
            st.metric("Your Chats", len(user_owned_chats))
        with col2:
            st.metric("Messages", len(user_messages))

    # Enhanced status indicators
    st.markdown("---")
    st.markdown("**🔌 Connection Status:**")
    
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
        mssql_count, other_count = categorize_tools_for_sidebar(st.session_state.get('tools', []))
        
        with st.container():
            st.markdown("**Tool Categories:**")
            
            # Create a compact display
            categories = []
            if mssql_count > 0:
                categories.append(f"🗃️ MSSQL: {mssql_count}")
            if other_count > 0:
                categories.append(f"🔧 Other: {other_count}")
            
            # Display categories in a compact format
            for category in categories:
                st.text(category)


def create_user_info_sidebar():
    """Create user information section in sidebar for authenticated users with session isolation."""
    current_user = st.session_state.get('username')
    if not current_user or not st.session_state.get("authentication_status"):
        return
    
    st.markdown("### 👤 User Information")
    
    with st.container(border=True):
        st.markdown(f"**Name:** {st.session_state.get('name', 'N/A')}")
        st.markdown(f"**Username:** {current_user}")
        
        # Add session info
        import datetime
        if "login_time" not in st.session_state:
            st.session_state["login_time"] = datetime.datetime.now()
        
        session_time = datetime.datetime.now() - st.session_state["login_time"]
        hours, remainder = divmod(int(session_time.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        
        st.markdown(f"**Session Time:** {hours:02d}:{minutes:02d}")
        
        # User role information
        is_admin = current_user == 'admin'
        role_text = "👑 Administrator" if is_admin else "👤 User"
        st.markdown(f"**Role:** {role_text}")
    
    st.markdown("---")


def create_user_session_controls():
    """Create user session control buttons in sidebar."""
    current_user = st.session_state.get('username')
    if not current_user or not st.session_state.get("authentication_status"):
        return
    
    st.markdown("### 🔧 Session Controls")
    
    with st.container(border=True):
        # Export user data
        if st.button("📤 Export My Data", use_container_width=True, key=f"export_data_{current_user}"):
            export_user_chat_data(current_user)
        
        # Clear user data with confirmation
        if st.button("🗑️ Clear My Data", use_container_width=True, key=f"clear_data_{current_user}"):
            st.session_state[f"confirm_clear_{current_user}"] = True
        
        # Confirmation for data clearing
        if st.session_state.get(f"confirm_clear_{current_user}", False):
            st.warning("⚠️ This will delete ALL your chat history!")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Confirm", key=f"confirm_clear_yes_{current_user}"):
                    clear_user_data(current_user)
                    st.session_state[f"confirm_clear_{current_user}"] = False
                    st.success("Data cleared!")
                    st.rerun()
            
            with col2:
                if st.button("❌ Cancel", key=f"confirm_clear_no_{current_user}"):
                    st.session_state[f"confirm_clear_{current_user}"] = False
                    st.rerun()


def export_user_chat_data(username: str):
    """Export user's chat data as JSON."""
    import json
    from datetime import datetime
    
    # Get user-specific data
    user_history_key = f"user_{username}_history_chats"
    user_chats = st.session_state.get(user_history_key, [])
    
    # Filter to only include chats created by this user
    user_owned_chats = [chat for chat in user_chats if chat.get('created_by') == username]
    
    export_data = {
        "user_chat_export": {
            "username": username,
            "exported_at": datetime.now().isoformat(),
            "total_chats": len(user_owned_chats),
            "chats": user_owned_chats
        }
    }
    
    json_str = json.dumps(export_data, indent=2)
    
    st.download_button(
        label="💾 Download Chat History",
        data=json_str,
        file_name=f"chat_history_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        key=f"download_chats_{username}"
    )


def clear_user_data(username: str):
    """Clear all data for a specific user."""
    # Clear user-specific session keys
    keys_to_clear = [key for key in st.session_state.keys() if key.startswith(f"user_{username}_")]
    
    for key in keys_to_clear:
        del st.session_state[key]
    
    # Clear global references if they belong to this user
    current_user = st.session_state.get('username')
    if current_user == username:
        global_keys = ["params", "current_chat_id", "current_chat_index", 
                      "history_chats", "messages", "conversation_memory"]
        for key in global_keys:
            if key in st.session_state:
                del st.session_state[key]


def show_user_activity_summary():
    """Show a summary of user activity."""
    current_user = st.session_state.get('username')
    if not current_user or not st.session_state.get("authentication_status"):
        return
    
    st.markdown("### 📊 Activity Summary")
    
    # Get user statistics
    user_history_key = f"user_{current_user}_history_chats"
    user_chats = st.session_state.get(user_history_key, [])
    
    # Filter to user's own chats
    user_owned_chats = [chat for chat in user_chats if chat.get('created_by') == current_user]
    
    # Calculate statistics
    total_chats = len(user_owned_chats)
    total_messages = sum(len(chat.get('messages', [])) for chat in user_owned_chats)
    
    # Count tool executions
    total_tool_executions = 0
    for chat in user_owned_chats:
        for msg in chat.get('messages', []):
            if msg.get('role') == 'tool' or msg.get('message_type') == 'tool_execution':
                total_tool_executions += 1
    
    # Recent activity (chats created today)
    from datetime import datetime, timedelta
    today = datetime.now().date()
    recent_chats = 0
    
    for chat in user_owned_chats:
        try:
            created_at = chat.get('created_at', '')
            if created_at:
                chat_date = datetime.fromisoformat(created_at).date()
                if chat_date == today:
                    recent_chats += 1
        except:
            pass
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Chats", total_chats)
    
    with col2:
        st.metric("Total Messages", total_messages)
    
    with col3:
        st.metric("Tool Executions", total_tool_executions)
    
    # Additional metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Today's Chats", recent_chats)
    
    with col2:
        # Average messages per chat
        if total_chats > 0:
            avg_messages = total_messages / total_chats
            st.metric("Avg Msg/Chat", f"{avg_messages:.1f}")
        else:
            st.metric("Avg Msg/Chat", "0")


def create_complete_sidebar():
    """Create the complete sidebar with all components including user session management and chat settings."""
    current_user = st.session_state.get('username')
    
    # Add the logo header at the top
    create_sidebar_header_with_icon()
    
    # Show user info if authenticated
    if current_user and st.session_state.get("authentication_status"):
        create_user_info_sidebar()
        
        # Chat settings section
        create_chat_settings_sidebar()
        
        # Show chat history and controls
        create_history_chat_container()
        create_sidebar_chat_buttons()
        
        # Advanced chat settings
        create_advanced_chat_settings()
        
        # Chat actions panel
        create_chat_actions_panel()
        
        # Add user session controls
        create_user_session_controls()
        
        # Show activity summary
        with st.expander("📊 Activity Summary", expanded=False):
            show_user_activity_summary()
    
    else:
        st.info("👈 Please log in to access chat features")


def create_enhanced_user_info():
    """Create enhanced user information with session isolation indicators."""
    current_user = st.session_state.get('username')
    if not current_user or not st.session_state.get("authentication_status"):
        return
    
    with st.expander("👤 Detailed User Info", expanded=False):
        # User details
        st.markdown(f"**Username:** `{current_user}`")
        st.markdown(f"**Full Name:** {st.session_state.get('name', 'N/A')}")
        st.markdown(f"**Email:** {st.session_state.get('email', 'N/A')}")
        
        # Session isolation info
        st.markdown("---")
        st.markdown("**🔒 Session Isolation Status:**")
        
        # Count user-specific session keys
        user_keys = [key for key in st.session_state.keys() if key.startswith(f"user_{current_user}_")]
        st.markdown(f"• Session keys: {len(user_keys)}")
        
        # Show if user has isolated data
        user_chats = st.session_state.get(f"user_{current_user}_history_chats", [])
        user_owned_chats = [chat for chat in user_chats if chat.get('created_by') == current_user]
        st.markdown(f"• Isolated chats: {len(user_owned_chats)}")
        
        # Tool output settings
        show_tools = st.session_state.get('show_tool_outputs', True)
        st.markdown(f"• Tool outputs: {'Visible' if show_tools else 'Hidden'}")
        
        # Message order setting
        message_order = st.session_state.get('message_order', 'Latest First')
        st.markdown(f"• Message order: {message_order}")
        
        # Session security indicator
        st.success("✅ Your data is isolated from other users")


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


# User switching detection
def detect_user_switch():
    """Detect if user has switched and handle appropriately."""
    current_user = st.session_state.get('username')
    previous_user = st.session_state.get('_sidebar_previous_user')
    
    if current_user != previous_user:
        # User has switched
        if previous_user:
            st.info(f"👋 Switched from {previous_user} to {current_user}")
        
        # Update tracking
        st.session_state['_sidebar_previous_user'] = current_user
        
        # Clear any user-specific UI state
        keys_to_clear = [key for key in st.session_state.keys() 
                        if key.startswith('confirm_clear_') and previous_user in key]
        for key in keys_to_clear:
            del st.session_state[key]
        
        return True
    
    return False


# Enhanced sidebar with user switch detection
def create_smart_sidebar():
    """Create sidebar with smart user switch detection."""
    # Detect user switches
    user_switched = detect_user_switch()
    
    if user_switched:
        st.sidebar.success("🔄 User session updated!")
    
    # Create complete sidebar
    with st.sidebar:
        create_complete_sidebar()