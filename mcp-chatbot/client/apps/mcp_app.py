import streamlit as st
from ui_components.tab_components import (
    create_configuration_tab, 
    create_connection_tab, 
    create_tools_tab
)
import ui_components.sidebar_components as sd_compents
from utils.async_helpers import check_authentication
from services.chat_service import ChatService

# Import user management with error handling
try:
    from ui_components.user_management_tab import create_user_management_tab
    USER_MANAGEMENT_AVAILABLE = True
    print("✅ User management module loaded successfully")
except ImportError as e:
    USER_MANAGEMENT_AVAILABLE = False
    print(f"⚠️  User management module not available: {str(e)}")

def main():
    """Main application function with authentication check."""
    # Check authentication before proceeding
    check_authentication()
    
    # Initialize the title
    st.title("🤖 CSM MCP Servers - AI Chat Interface")
    
    # Add user welcome message
    if st.session_state.get("name"):
        st.success(f"Welcome back, **{st.session_state['name']}**! 👋")
    
    # Check if current user is admin
    current_user = st.session_state.get('username')
    is_admin = current_user == 'admin'
    
    # Debug: Show current user info
    if st.session_state.get('authentication_status'):
        st.info(f"🔍 Debug: Current user: {current_user}, Admin: {is_admin}, User Management Available: {USER_MANAGEMENT_AVAILABLE}")
    
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
    
    # Sidebar with chat history and user info
    with st.sidebar:
        # Show user info at the top
        sd_compents.create_user_info_sidebar()
        
        # Chat history (only shown if authenticated)
        sd_compents.create_history_chat_container()
        sd_compents.create_sidebar_chat_buttons()

    # Chat Tab - Main conversation interface
    with tab1:
        # Show authentication status
        if st.session_state.get("authentication_status"):
            # Initialize chat service
            if "chat_service" not in st.session_state:
                st.session_state.chat_service = ChatService()
            
            # Main chat interface
            create_chat_interface()
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
                print(f"User Management Error: {str(e)}")

def create_chat_interface():
    """Create the main chat interface."""
    # Check if we have active connections
    if not st.session_state.get("agent"):
        st.warning("🔌 No MCP server connections found")
        st.info("👉 Go to the **Connections** tab to establish server connections")
        return
    
    # Check if we have tools available
    if not st.session_state.get("tools"):
        st.warning("🧰 No tools available")
        st.info("Tools are loaded automatically when MCP servers are connected")
        return
    
    # Chat interface
    st.markdown("### 💬 AI Chat Interface")
    st.markdown("Chat with AI agents that can execute database operations and specialized tools.")
    
    # Show available tools summary
    with st.expander("🧰 Available Tools", expanded=False):
        tools = st.session_state.get("tools", [])
        if tools:
            st.write(f"**{len(tools)} tools available:**")
            for tool in tools[:5]:  # Show first 5 tools
                st.write(f"• **{tool.name}**: {tool.description[:100]}...")
            if len(tools) > 5:
                st.write(f"... and {len(tools) - 5} more tools")
        else:
            st.write("No tools available")
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Process the message with ChatService
        try:
            chat_service = st.session_state.chat_service
            
            with st.spinner("🤖 AI is thinking..."):
                response = chat_service.process_message(user_input)
            
            # Add assistant response
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            st.error(f"❌ Error processing message: {str(e)}")
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"I encountered an error: {str(e)}"
            })
    
    # Display chat history
    if "messages" in st.session_state:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

def show_debug_info():
    """Show debug information for troubleshooting."""
    if st.checkbox("🐛 Show Debug Info"):
        st.markdown("### Debug Information")
        
        debug_info = {
            "Authentication Status": st.session_state.get("authentication_status"),
            "Username": st.session_state.get("username"),
            "Name": st.session_state.get("name"),
            "Is Admin": st.session_state.get("username") == 'admin',
            "User Management Available": USER_MANAGEMENT_AVAILABLE,
            "MCP Agent": st.session_state.get("agent") is not None,
            "Tools Available": len(st.session_state.get("tools", [])),
            "Servers Connected": len(st.session_state.get("servers", {}))
        }
        
        for key, value in debug_info.items():
            st.write(f"**{key}:** {value}")

if __name__ == "__main__":
    main()