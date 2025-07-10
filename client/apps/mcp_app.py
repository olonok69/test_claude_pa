import streamlit as st
from ui_components.tab_components import (
    create_configuration_tab, 
    create_connection_tab, 
    create_tools_tab
)
import ui_components.sidebar_components as sd_components
from utils.async_helpers import check_authentication
from services.chat_service import ChatService, on_user_login, on_user_logout
from ui_components.enhanced_chat_interface import create_enhanced_chat_interface
import logging

# Import user management with error handling
try:
    from ui_components.user_management_tab import create_user_management_tab
    USER_MANAGEMENT_AVAILABLE = True
    logging.info("✅ User management module loaded successfully")
except ImportError as e:
    USER_MANAGEMENT_AVAILABLE = False
    logging.info(f"⚠️  User management module not available: {str(e)}")

def main():
    """Main application function with enhanced authentication and user session management."""
    # Check authentication before proceeding
    current_user = st.session_state.get('username')
    authentication_status = st.session_state.get("authentication_status")
    
    # Handle authentication state changes
    handle_authentication_changes()
    
    if not authentication_status:
        check_authentication()
        return
    
    # Initialize the title
    st.title("🤖 CSM MCP Servers - AI Chat Interface")
    
    # Add user welcome message
    if st.session_state.get("name"):
        st.success(f"Welcome back, **{st.session_state['name']}**! 👋")
    
    # Check if current user is admin
    is_admin = current_user == 'admin'
    
    # Create tabs based on permissions
    if is_admin and USER_MANAGEMENT_AVAILABLE:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "💬 Chat", 
            "⚙️ Configuration", 
            "🔌 Connections", 
            "🧰 Tools",
            "👥 User Management"
        ])
        user_management_tab = tab5
    else:
        tab1, tab2, tab3, tab4 = st.tabs([
            "💬 Chat", 
            "⚙️ Configuration", 
            "🔌 Connections", 
            "🧰 Tools"
        ])
        user_management_tab = None
        
        # Show why User Management tab is not available
        if current_user:
            if not is_admin:
                st.sidebar.warning("👥 User Management: Admin access required")
            elif not USER_MANAGEMENT_AVAILABLE:
                st.sidebar.error("👥 User Management: Module not available")
    
    # Sidebar with chat history, user info, and chat settings
    with st.sidebar:
        # Show user info at the top
        sd_components.create_user_info_sidebar()
        
        # Chat settings section
        from ui_components.chat_settings_component import create_chat_settings_sidebar
        create_chat_settings_sidebar()
        
        # Chat history (only shown if authenticated)
        sd_components.create_history_chat_container()
        sd_components.create_sidebar_chat_buttons()

    # Chat Tab - Enhanced conversation interface with reverse order and tool toggles
    with tab1:
        # Show authentication status and enhanced chat interface
        if st.session_state.get("authentication_status"):
            # Initialize chat service
            if "chat_service" not in st.session_state:
                st.session_state.chat_service = ChatService()
            
            # Enhanced chat interface with reverse order and tool output controls
            create_enhanced_chat_interface()
        else:
            st.warning("🔐 Please authenticate to access the chat interface")
            st.info("👈 Use the sidebar to log in")
    
    # Configuration Tab
    with tab2:
        check_authentication()
        create_configuration_tab()

    # Connections Tab  
    with tab3:
        check_authentication()
        create_connection_tab()

    # Tools Tab
    with tab4:
        check_authentication()
        create_tools_tab()
    
    # User Management Tab (admin only)
    if user_management_tab is not None:
        with user_management_tab:
            check_authentication()
            try:
                if USER_MANAGEMENT_AVAILABLE:
                    create_user_management_tab()
                else:
                    st.error("❌ User Management module not available")
                    st.info("Please ensure ui_components/user_management_tab.py is installed")
                    
                    # Show installation instructions
                    with st.expander("📋 Installation Instructions"):
                        st.markdown("""
                        **To enable User Management:**
                        
                        1. Ensure the user management files are in place:
                           ```
                           ui_components/user_management_tab.py
                           utils/enhanced_security_config.py
                           ```
                        
                        2. Restart the application
                        
                        3. Login as 'admin' user
                        
                        **Current Status:**
                        - Current user: {current_user}
                        - Is admin: {is_admin}
                        - Module available: {USER_MANAGEMENT_AVAILABLE}
                        """.format(
                            current_user=current_user,
                            is_admin=is_admin,
                            USER_MANAGEMENT_AVAILABLE=USER_MANAGEMENT_AVAILABLE
                        ))
                        
            except Exception as e:
                st.error(f"❌ Error loading User Management: {str(e)}")
                st.info("Check the console for detailed error information")
                logging.error(f"User Management Error: {str(e)}")


def handle_authentication_changes():
    """Handle authentication state changes and user switching."""
    current_user = st.session_state.get('username')
    previous_user = st.session_state.get('_previous_user')
    authentication_status = st.session_state.get("authentication_status")
    
    # Handle user login
    if authentication_status and current_user and current_user != previous_user:
        # User has logged in or switched
        if previous_user:
            # User switched - logout previous user
            on_user_logout(previous_user)
        
        # Login new user
        on_user_login(current_user)
        st.session_state['_previous_user'] = current_user
        
        # Set login time
        import datetime
        st.session_state["login_time"] = datetime.datetime.now()
        
        # Initialize default chat settings for new user
        initialize_user_chat_settings(current_user)
        
        logging.info(f"User {current_user} logged in successfully")
    
    # Handle user logout
    elif not authentication_status and previous_user:
        # User has logged out
        on_user_logout(previous_user)
        st.session_state['_previous_user'] = None
        
        # Clear login time
        if "login_time" in st.session_state:
            del st.session_state["login_time"]
        
        # Clear chat settings
        clear_user_chat_settings(previous_user)
        
        logging.info(f"User {previous_user} logged out")


def initialize_user_chat_settings(username: str):
    """Initialize default chat settings for a user."""
    default_settings = {
        'show_tool_outputs': True,
        'message_order': 'Latest First',
        'auto_scroll_enabled': True,
        'show_timestamps': True,
        'show_mssql_outputs': True,
        'show_general_outputs': True,
        'max_message_length': 500,
        'max_tool_output_length': 300,
        'include_tool_outputs_in_export': True,
        'include_timestamps_in_export': True
    }
    
    # Only set defaults if not already set
    for key, value in default_settings.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_user_chat_settings(username: str):
    """Clear chat settings when user logs out."""
    settings_keys = [
        'show_tool_outputs',
        'message_order',
        'auto_scroll_enabled',
        'show_timestamps',
        'show_mssql_outputs',
        'show_general_outputs',
        'max_message_length',
        'max_tool_output_length',
        'include_tool_outputs_in_export',
        'include_timestamps_in_export'
    ]
    
    for key in settings_keys:
        if key in st.session_state:
            del st.session_state[key]


def show_debug_info():
    """Show debug information for troubleshooting."""
    if st.checkbox("🐛 Show Debug Info"):
        st.markdown("### Debug Information")
        
        current_user = st.session_state.get('username')
        previous_user = st.session_state.get('_previous_user')
        
        debug_info = {
            "Authentication Status": st.session_state.get("authentication_status"),
            "Current Username": current_user,
            "Previous Username": previous_user,
            "Name": st.session_state.get("name"),
            "Is Admin": current_user == 'admin' if current_user else False,
            "User Management Available": USER_MANAGEMENT_AVAILABLE,
            "MCP Agent": st.session_state.get("agent") is not None,
            "Tools Available": len(st.session_state.get("tools", [])),
            "Servers Connected": len(st.session_state.get("servers", {})),
            "Tool Outputs Visible": st.session_state.get('show_tool_outputs', True),
            "Message Order": st.session_state.get('message_order', 'Latest First')
        }
        
        # User-specific debug info
        if current_user:
            user_keys = [key for key in st.session_state.keys() if key.startswith(f"user_{current_user}_")]
            debug_info["User-specific Keys"] = len(user_keys)
            debug_info["User Chat History"] = len(st.session_state.get(f"user_{current_user}_history_chats", []))
            debug_info["User Messages"] = len(st.session_state.get(f"user_{current_user}_messages", []))
            
            # Count tool messages
            user_messages = st.session_state.get(f"user_{current_user}_messages", [])
            tool_messages = [msg for msg in user_messages if msg.get('role') == 'tool']
            debug_info["Tool Messages"] = len(tool_messages)
        
        for key, value in debug_info.items():
            st.write(f"**{key}:** {value}")
        
        # Show user-specific session keys
        if st.checkbox("Show User Session Keys") and current_user:
            st.markdown("### User-Specific Session Keys")
            user_keys = {k: type(v).__name__ for k, v in st.session_state.items() 
                        if k.startswith(f"user_{current_user}_")}
            for key, value_type in user_keys.items():
                st.write(f"**{key}:** {value_type}")
        
        # Show chat settings
        if st.checkbox("Show Chat Settings"):
            st.markdown("### Current Chat Settings")
            chat_settings = {
                'show_tool_outputs': st.session_state.get('show_tool_outputs', True),
                'message_order': st.session_state.get('message_order', 'Latest First'),
                'auto_scroll_enabled': st.session_state.get('auto_scroll_enabled', True),
                'show_timestamps': st.session_state.get('show_timestamps', True),
                'show_mssql_outputs': st.session_state.get('show_mssql_outputs', True),
                'show_general_outputs': st.session_state.get('show_general_outputs', True),
                'max_message_length': st.session_state.get('max_message_length', 500),
                'max_tool_output_length': st.session_state.get('max_tool_output_length', 300)
            }
            
            for key, value in chat_settings.items():
                st.write(f"**{key}:** {value}")


def create_user_session_info():
    """Create a detailed user session information panel."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    with st.expander("👤 User Session Details", expanded=False):
        from services.chat_service import get_user_chat_stats
        
        # Get user statistics
        stats = get_user_chat_stats(current_user)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Your Chats", stats["total_chats"])
        
        with col2:
            st.metric("Your Messages", stats["total_messages"])
        
        with col3:
            st.metric("Tool Executions", stats.get("tool_executions", 0))
        
        # Session duration
        import datetime
        if "login_time" in st.session_state:
            session_time = datetime.datetime.now() - st.session_state["login_time"]
            hours, remainder = divmod(int(session_time.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            st.metric("Session Time", f"{hours:02d}:{minutes:02d}")
        
        # Chat settings summary
        st.markdown("**Current Settings:**")
        st.write(f"Tool Outputs: {'Visible' if st.session_state.get('show_tool_outputs', True) else 'Hidden'}")
        st.write(f"Message Order: {st.session_state.get('message_order', 'Latest First')}")
        st.write(f"Timestamps: {'Shown' if st.session_state.get('show_timestamps', True) else 'Hidden'}")
        
        # User session controls
        st.markdown("**Session Controls:**")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Clear My Data", help="Clear all your chat data", key="session_clear_data"):
                clear_user_data_confirmation()
        
        with col2:
            if st.button("📊 Export My Data", help="Export all your chat data", key="session_export_data"):
                export_user_data()


def clear_user_data_confirmation():
    """Show confirmation dialog for clearing user data."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    st.warning(f"⚠️ This will delete ALL chat history for user: **{current_user}**")
    
    if st.button("❌ Confirm Clear All My Data", key="confirm_clear_session_data"):
        from services.chat_service import clear_user_session_data
        clear_user_session_data(current_user)
        clear_user_chat_settings(current_user)
        st.success("✅ All your data has been cleared!")
        st.rerun()


def export_user_data():
    """Export all user data as JSON."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    import json
    from datetime import datetime
    
    # Collect all user data
    user_data = {}
    for key, value in st.session_state.items():
        if key.startswith(f"user_{current_user}_"):
            # Remove the user prefix for cleaner export
            clean_key = key.replace(f"user_{current_user}_", "")
            try:
                # Try to serialize the value
                json.dumps(value)
                user_data[clean_key] = value
            except (TypeError, ValueError):
                # If not serializable, convert to string
                user_data[clean_key] = str(value)
    
    # Add chat settings
    chat_settings = {
        'show_tool_outputs': st.session_state.get('show_tool_outputs', True),
        'message_order': st.session_state.get('message_order', 'Latest First'),
        'auto_scroll_enabled': st.session_state.get('auto_scroll_enabled', True),
        'show_timestamps': st.session_state.get('show_timestamps', True),
        'show_mssql_outputs': st.session_state.get('show_mssql_outputs', True),
        'show_general_outputs': st.session_state.get('show_general_outputs', True),
        'max_message_length': st.session_state.get('max_message_length', 500),
        'max_tool_output_length': st.session_state.get('max_tool_output_length', 300)
    }
    
    export_data = {
        "user_data_export": {
            "username": current_user,
            "exported_at": datetime.now().isoformat(),
            "data": user_data,
            "chat_settings": chat_settings
        }
    }
    
    json_str = json.dumps(export_data, indent=2)
    
    st.download_button(
        label="💾 Download My Data",
        data=json_str,
        file_name=f"user_data_{current_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        key="download_user_data"
    )


# Additional sidebar components for user session management
def enhanced_sidebar():
    """Enhanced sidebar with user session management and chat settings."""
    with st.sidebar:
        # Standard sidebar components
        sd_components.create_user_info_sidebar()
        
        # Chat settings
        from ui_components.chat_settings_component import create_chat_settings_sidebar, create_advanced_chat_settings
        create_chat_settings_sidebar()
        
        # Chat history
        sd_components.create_history_chat_container()
        sd_components.create_sidebar_chat_buttons()
        
        # Advanced settings
        create_advanced_chat_settings()
        
        # Additional user session info
        create_user_session_info()
        
        # Debug information (for development)
        if st.checkbox("🔧 Debug Mode"):
            show_debug_info()


def create_chat_metrics_display():
    """Create a metrics display for chat statistics."""
    current_user = st.session_state.get('username')
    if not current_user:
        return
    
    from services.chat_service import get_user_chat_stats, get_messages_by_type
    
    stats = get_user_chat_stats(current_user)
    messages_by_type = get_messages_by_type(current_user)
    
    with st.container():
        st.markdown("### 📊 Your Chat Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Chats", stats["total_chats"])
        
        with col2:
            st.metric("Total Messages", stats["total_messages"])
        
        with col3:
            st.metric("Tool Executions", stats.get("tool_executions", 0))
        
        with col4:
            # Calculate efficiency metric
            if stats["total_messages"] > 0:
                tool_ratio = stats.get("tool_executions", 0) / stats["total_messages"]
                st.metric("Tool Usage %", f"{tool_ratio:.1%}")
            else:
                st.metric("Tool Usage %", "0%")


if __name__ == "__main__":
    # Add enhanced sidebar
    with st.sidebar:
        enhanced_sidebar()
    
    main()