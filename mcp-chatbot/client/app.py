# Updated app.py with enhanced authentication and user session isolation

import streamlit as st
import asyncio
import os
import nest_asyncio
import atexit
import yaml
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
import logging
from services.chat_service import init_session, on_user_login, on_user_logout
from utils.async_helpers import on_shutdown
from apps import mcp_app
from pathlib import Path
from utils.logger_util import set_up_logging
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
Path(LOGS_PATH).mkdir(parents=True, exist_ok=True)
script_name = os.path.join(LOGS_PATH, "debug.log")
# create loggers
if not set_up_logging(
    console_log_output="stdout",
    console_log_level="info",
    console_log_color=True,
    logfile_file=script_name,
    logfile_log_level="info",
    logfile_log_color=True,
    log_line_template="%(color_on)s[%(asctime)s] [%(threadName)s] [%(levelname)-8s] [%(filename)s:%(lineno)d:%(funcName)s] %(message)s%(color_off)s",
):
    print("Failed to set up logging, aborting.")
    raise AttributeError("failed to create logging")

# Enhanced security imports (with fallback)
try:
    from utils.enhanced_security_config import StreamlitSecureAuth, SecurityConfig
    ENHANCED_SECURITY_AVAILABLE = True
    logging.info("✅ Enhanced security module loaded successfully")
except ImportError as e:
    ENHANCED_SECURITY_AVAILABLE = False
    logging.info(f"⚠️  Enhanced security module not available: {str(e)}")
    logging.info("📋 Using YAML authentication fallback")

# Apply nest_asyncio to allow nested asyncio event loops
nest_asyncio.apply()

page_icon_path = os.path.join('.', 'icons', 'playground.png')

st.set_page_config(
    page_title="The CloserStill Media - MCP Client",
    page_icon=page_icon_path,
    layout='wide',
    initial_sidebar_state="expanded"
)

# Load custom CSS with enhanced chat styles
css_path = os.path.join('.', '.streamlit', 'style.css')
if os.path.exists(css_path):
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # Add enhanced chat styles
        enhanced_chat_css = """
        /* Enhanced Chat Interface Styles */
        .chat-message-user {
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            padding: 12px 16px;
            border-radius: 12px 12px 4px 12px;
            margin: 8px 0 12px 15%;
            border-left: 4px solid #2196f3;
            box-shadow: 0 2px 4px rgba(33, 150, 243, 0.1);
            word-wrap: break-word;
            animation: slideInRight 0.3s ease-out;
        }

        .chat-message-assistant {
            background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
            padding: 12px 16px;
            border-radius: 12px 12px 12px 4px;
            margin: 8px 15% 12px 0;
            border-left: 4px solid #9c27b0;
            box-shadow: 0 2px 4px rgba(156, 39, 176, 0.1);
            word-wrap: break-word;
            animation: slideInLeft 0.3s ease-out;
        }

        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        @keyframes slideInLeft {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .stContainer[data-testid="metric-container"] {
            background: linear-gradient(135deg, rgba(47, 46, 120, 0.05) 0%, rgba(76, 75, 154, 0.05) 100%);
            border-radius: 8px;
            padding: 12px;
            border: 1px solid rgba(47, 46, 120, 0.1);
        }
        """
        
        combined_css = css_content + enhanced_chat_css
        st.markdown(f'<style>{combined_css}</style>', unsafe_allow_html=True)
    except UnicodeDecodeError:
        # Fallback for encoding issues
        try:
            with open(css_path, 'r', encoding='latin1') as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        except Exception as e:
            logging.warning(f"Warning: Could not load CSS file: {str(e)}")


def load_config():
    """Load authentication configuration from secure storage or YAML fallback."""
    try:
        # Check if SQLite is enabled and available
        use_sqlite = os.getenv('USE_SQLITE', 'false').lower() == 'true'
        
        if use_sqlite and ENHANCED_SECURITY_AVAILABLE:
            logging.info("🔒 Using SQLite authentication")
            # Use enhanced SQLite authentication
            secure_auth = StreamlitSecureAuth('sqlite')
            return secure_auth.get_config_for_streamlit_authenticator()
        else:
            logging.info("📋 Using YAML authentication")
            # Fallback to YAML configuration
            config_path = os.path.join('keys', 'config.yaml')
            if not os.path.exists(config_path):
                st.error("❌ Configuration file not found at keys/config.yaml")
                st.info("Please run: python simple_generate_password.py")
                st.stop()
            
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.load(file, Loader=SafeLoader)
                
    except FileNotFoundError:
        st.error("❌ Configuration not found. Please check your setup.")
        st.info("Run the password generation script: python simple_generate_password.py")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading configuration: {str(e)}")
        if "enhanced_security_config" in str(e):
            st.info("💡 Enhanced security features not available. Using YAML authentication.")
            # Force YAML fallback
            try:
                config_path = os.path.join('keys', 'config.yaml')
                with open(config_path, 'r', encoding='utf-8') as file:
                    return yaml.load(file, Loader=SafeLoader)
            except Exception as fallback_error:
                st.error(f"❌ YAML fallback also failed: {str(fallback_error)}")
                st.stop()
        else:
            st.stop()


def initialize_authentication_state():
    """Initialize authentication-related session state variables."""
    if "authentication_status" not in st.session_state:
        st.session_state["authentication_status"] = None
    if "name" not in st.session_state:
        st.session_state["name"] = None
    if "username" not in st.session_state:
        st.session_state["username"] = None


def handle_authentication():
    """Handle user authentication in the sidebar with enhanced user session management."""
    try:
        # Load configuration
        config = load_config()
        
        # Initialize authentication state
        initialize_authentication_state()
        
        # Create authenticator using the updated API
        authenticator = stauth.Authenticate(
            config["credentials"],
            config["cookie"]["name"],
            config["cookie"]["key"],
            config["cookie"]["expiry_days"],
        )
        
        # Track previous authentication state for user switching detection
        prev_auth_status = st.session_state.get("_prev_auth_status")
        prev_username = st.session_state.get("_prev_username")
        
        # Create sidebar authentication section
        with st.sidebar:
            st.markdown("## 🔐 Authentication")
            
            # Show login form or logout button based on authentication status
            if st.session_state["authentication_status"] is None:
                # Show login form
                try:
                    authenticator.login()
                except Exception as e:
                    st.error(f"Authentication error: {str(e)}")
                    
                if st.session_state["authentication_status"] is False:
                    st.error("❌ Username/password is incorrect")
                elif st.session_state["authentication_status"] is None:
                    st.warning("⚠️ Please enter your username and password")
                    
            elif st.session_state["authentication_status"]:
                # User is authenticated - show user info and logout button
                current_user = st.session_state['username']
                st.success(f"✅ Welcome, **{st.session_state['name']}**!")
                st.info(f"👤 Username: {current_user}")
                
                # Show session isolation indicator
                user_chats = st.session_state.get(f"user_{current_user}_history_chats", [])
                user_owned_chats = [chat for chat in user_chats if chat.get('created_by') == current_user]
                if user_owned_chats:
                    st.success(f"🔒 {len(user_owned_chats)} isolated chats")
                
                # Add logout button
                authenticator.logout("Logout")
                
                # Add separator
                st.markdown("---")
        
        # Handle authentication state changes
        current_auth_status = st.session_state["authentication_status"]
        current_username = st.session_state.get("username")
        
        # Detect authentication state changes
        if current_auth_status != prev_auth_status or current_username != prev_username:
            handle_authentication_state_change(prev_auth_status, current_auth_status, 
                                              prev_username, current_username)
        
        # Update tracking variables
        st.session_state["_prev_auth_status"] = current_auth_status
        st.session_state["_prev_username"] = current_username
        
        # Log authentication status for debugging
        logging.info(
            f'Authentication Status: {st.session_state["authentication_status"]}, '
            f'Name: {st.session_state["name"]}, '
            f'Username: {st.session_state["username"]}'
        )
        
        return st.session_state["authentication_status"]
        
    except Exception as e:
        st.error(f"❌ Authentication system error: {str(e)}")
        st.info("Please check your configuration and try again.")
        return None


def handle_authentication_state_change(prev_auth_status, current_auth_status, 
                                     prev_username, current_username):
    """Handle authentication state changes and user switching."""
    
    # User logged in
    if current_auth_status and current_username and not prev_auth_status:
        logging.info(f"🔐 User {current_username} logged in")
        on_user_login(current_username)
        
        # Set login time
        import datetime
        st.session_state["login_time"] = datetime.datetime.now()
    
    # User switched (logged out and logged in as different user)
    elif (current_auth_status and current_username and 
          prev_auth_status and prev_username and 
          current_username != prev_username):
        logging.info(f"🔄 User switched from {prev_username} to {current_username}")
        
        # Logout previous user
        on_user_logout(prev_username)
        
        # Login new user
        on_user_login(current_username)
        
        # Set new login time
        import datetime
        st.session_state["login_time"] = datetime.datetime.now()
        
        # Show switch notification
        st.sidebar.info(f"🔄 Switched to {current_username}")
    
    # User logged out
    elif not current_auth_status and prev_auth_status and prev_username:
        logging.info(f"🚪 User {prev_username} logged out")
        on_user_logout(prev_username)
        
        # Clear login time
        if "login_time" in st.session_state:
            del st.session_state["login_time"]


def show_authentication_required_message():
    """Show a message when user is not authenticated."""
    st.title("🔐 Authentication Required")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Add logo in the welcome message if available
        logo_path = os.path.join('.', 'icons', 'Logo.png')
        if os.path.exists(logo_path):
            # Center the logo
            col_a, col_b, col_c = st.columns([1, 1, 1])
            with col_b:
                st.image(logo_path, width=120)
            st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
        ### Welcome to CloserStill Media - MCP Client
        
        This application provides AI-powered interactions with **MSSQL databases** 
        through Model Context Protocol (MCP) servers.
        
        **Please authenticate using the sidebar to access the application.**
        
        ---
        
        #### 🚀 Features Available After Login:
        
        - **💬 Enhanced AI Chat Interface**: Interactive conversations with improved UI
        - **🗃️ MSSQL Database Operations**: Execute SQL queries, explore tables, and manage data
        - **🔧 Tool Management**: Execute specialized MCP tools for database operations
        - **📊 Real-time Analytics**: Monitor and analyze your data
        - **🔄 Database Integration**: Comprehensive SQL Server connectivity and management
        - **🔒 User Session Isolation**: Your conversations are kept separate from other users
        
        ---
        
        #### 🆕 Enhanced Features:
        
        **Improved Chat Interface:**
        - Scrollable conversation area with better message styling
        - Copy functionality for messages
        - Tools information panel at the bottom
        - Better visual distinction between user and assistant messages
        
        **User Session Management:**
        - Complete isolation between different users
        - Personal chat history that doesn't mix with other users
        - Secure session handling with automatic cleanup
        
        ---
        
        #### 🔑 Authentication
        
        Use the **Authentication** section in the sidebar to log in with your credentials.
        Your chat history and data will be completely isolated from other users.
        
        If you don't have access credentials, please contact your administrator.
        """)
        
        # Add visual elements with updated info
        st.info("👈 Use the sidebar to authenticate and start using the enhanced database platform")
        
        # Add quick stats about the platform
        with st.container():
            st.markdown("#### 📈 Platform Overview")
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric(
                    label="🗃️ Database Types",
                    value="1",
                    help="MSSQL Server"
                )
            
            with col_b:
                st.metric(
                    label="🧰 Tool Categories", 
                    value="4+",
                    help="SQL operations and management"
                )
            
            with col_c:
                st.metric(
                    label="👥 User Isolation",
                    value="✅ Secure",
                    help="Complete session isolation between users"
                )


def main():
    """Main application function with enhanced authentication and user session management."""
    try:
        # Initialize session state for event loop
        if "loop" not in st.session_state:
            st.session_state.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(st.session_state.loop)
        
        # Register shutdown handler
        atexit.register(on_shutdown)
        
        # Always show logo at the top of sidebar first
        with st.sidebar:
            from ui_components.sidebar_components import create_sidebar_header_with_icon
            create_sidebar_header_with_icon()
        
        # Handle authentication
        authentication_status = handle_authentication()
        
        # Check authentication status and proceed accordingly
        if authentication_status:
            # User is authenticated - initialize and run the main application
            init_session()
            mcp_app.main()
            
        elif authentication_status is False:
            # Authentication failed - show error message
            show_authentication_required_message()
            st.error("❌ Authentication failed. Please check your credentials and try again.")
            
        else:
            # Not authenticated yet - show welcome message
            show_authentication_required_message()
            
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        logging.error(f"Application error: {str(e)}")
        
        # Show debugging information
        st.markdown("---")
        with st.expander("🐛 Debug Information", expanded=False):
            st.code(f"Error: {str(e)}")
            st.code(f"Enhanced Security Available: {ENHANCED_SECURITY_AVAILABLE}")
            st.code(f"USE_SQLITE: {os.getenv('USE_SQLITE', 'not set')}")
            st.code(f"YAML Config Exists: {os.path.exists('keys/config.yaml')}")
            st.code(f"SQLite DB Exists: {os.path.exists('keys/users.db')}")
        
        # Still show authentication if there's an error
        if st.session_state.get("authentication_status") is None:
            show_authentication_required_message()


if __name__ == "__main__":
    main()


