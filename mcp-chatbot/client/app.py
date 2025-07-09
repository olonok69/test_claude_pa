# FIXED VERSION - app.py with proper SQLite authentication integration

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

# Set up logging
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
    from utils.enhanced_security_config import StreamlitSecureAuth, SecurityConfig, migrate_yaml_users_to_sqlite
    ENHANCED_SECURITY_AVAILABLE = True
    logging.info("✅ Enhanced security module loaded successfully")
except ImportError as e:
    ENHANCED_SECURITY_AVAILABLE = False
    logging.info(f"⚠️  Enhanced security module not available: {str(e)}")
    logging.info("📋 Using YAML authentication fallback")

# Configure logging early
logging.getLogger('watchdog.observers.inotify_buffer').setLevel(logging.WARNING)
logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

# Apply nest_asyncio to allow nested asyncio event loops
nest_asyncio.apply()

page_icon_path = os.path.join('.', 'icons', 'playground.png')

st.set_page_config(
    page_title="The CloserStill Media - MCP Client",
    page_icon=page_icon_path,
    layout='wide',
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_path = os.path.join('.', '.streamlit', 'style.css')
if os.path.exists(css_path):
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
    except Exception as e:
        logging.warning(f"Warning: Could not load CSS file: {str(e)}")


def load_config():
    """FIXED VERSION - Load authentication configuration from secure storage or YAML fallback."""
    try:
        # Check if SQLite is enabled and available
        use_sqlite = os.getenv('USE_SQLITE', 'false').lower() == 'true'
        
        if use_sqlite and ENHANCED_SECURITY_AVAILABLE:
            logging.info("🔒 Using SQLite authentication")
            
            # Check if migration is needed
            yaml_path = os.path.join('keys', 'config.yaml')
            sqlite_path = os.path.join('keys', 'users.db')
            
            # If YAML exists but SQLite doesn't have migrated users, migrate
            if (os.path.exists(yaml_path) and 
                (not os.path.exists(sqlite_path) or should_migrate_users())):
                
                logging.info("🔄 Migrating users from YAML to SQLite...")
                migration_success = migrate_yaml_users_to_sqlite()
                
                if migration_success:
                    logging.info("✅ Migration completed successfully")
                else:
                    logging.error("❌ Migration failed, falling back to YAML")
                    return load_yaml_config()
            
            # Use enhanced SQLite authentication
            try:
                secure_auth = StreamlitSecureAuth('sqlite')
                config = secure_auth.get_config_for_streamlit_authenticator()
                
                # Validate config has users
                if not config.get('credentials', {}).get('usernames'):
                    logging.error("❌ No users found in SQLite, falling back to YAML")
                    return load_yaml_config()
                
                logging.info(f"✅ SQLite config loaded with {len(config['credentials']['usernames'])} users")
                return config
                
            except Exception as e:
                logging.error(f"❌ SQLite authentication failed: {str(e)}")
                logging.info("📋 Falling back to YAML authentication")
                return load_yaml_config()
        else:
            logging.info("📋 Using YAML authentication")
            return load_yaml_config()
                
    except Exception as e:
        logging.error(f"❌ Error in load_config: {str(e)}")
        return load_yaml_config()


def should_migrate_users() -> bool:
    """Check if users need to be migrated from YAML to SQLite."""
    try:
        sqlite_path = os.path.join('keys', 'users.db')
        if not os.path.exists(sqlite_path):
            return True
        
        import sqlite3
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Check if any users exist
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        # Check if any users are marked as migrated
        cursor.execute('SELECT COUNT(*) FROM users WHERE migrated_from_yaml = TRUE')
        migrated_count = cursor.fetchone()[0]
        
        conn.close()
        
        # If no users or no migrated users, need migration
        return user_count == 0 or migrated_count == 0
        
    except Exception as e:
        logging.error(f"Error checking migration status: {str(e)}")
        return True


def load_yaml_config():
    """Load YAML configuration as fallback."""
    try:
        config_path = os.path.join('keys', 'config.yaml')
        if not os.path.exists(config_path):
            st.error("❌ Configuration file not found at keys/config.yaml")
            st.info("Please run: python simple_generate_password.py")
            st.stop()
        
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.load(file, Loader=SafeLoader)
            logging.info(f"✅ YAML config loaded with {len(config.get('credentials', {}).get('usernames', {}))} users")
            return config
            
    except Exception as e:
        st.error(f"❌ Error loading YAML configuration: {str(e)}")
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
    """FIXED VERSION - Handle user authentication with proper SQLite integration."""
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
            
            # Show current storage method
            use_sqlite = os.getenv('USE_SQLITE', 'false').lower() == 'true'
            if use_sqlite and ENHANCED_SECURITY_AVAILABLE:
                st.info("🔒 SQLite Authentication Active")
            else:
                st.info("📋 YAML Authentication Active")
            
            # Show login form or logout button based on authentication status
            if st.session_state["authentication_status"] is None:
                # Show login form
                try:
                    authenticator.login()
                except Exception as e:
                    st.error(f"Authentication error: {str(e)}")
                    logging.error(f"Authentication widget error: {str(e)}")
                    
                if st.session_state["authentication_status"] is False:
                    st.error("❌ Username/password is incorrect")
                    
                    # Show debugging info for SQLite
                    if use_sqlite and ENHANCED_SECURITY_AVAILABLE:
                        with st.expander("🔧 SQLite Debug Info", expanded=False):
                            show_sqlite_debug_info()
                            
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
        logging.error(f"Authentication system error: {str(e)}")
        st.info("Please check your configuration and try again.")
        return None


def show_sqlite_debug_info():
    """Show SQLite debugging information."""
    try:
        from utils.enhanced_security_config import SecureUserStore
        
        store = SecureUserStore('sqlite')
        
        st.markdown("**SQLite Database Status:**")
        
        # Check if database exists
        import sqlite3
        db_path = store.db_path
        if os.path.exists(db_path):
            st.success("✅ Database file exists")
            
            # Get user count
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = TRUE')
            admin_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT username, email, is_admin FROM users LIMIT 5')
            sample_users = cursor.fetchall()
            
            conn.close()
            
            st.info(f"👥 Total users: {total_users}")
            st.info(f"👑 Admin users: {admin_users}")
            
            if sample_users:
                st.markdown("**Sample Users:**")
                for username, email, is_admin in sample_users:
                    role = "👑 Admin" if is_admin else "👤 User"
                    st.write(f"• {username} ({email}) - {role}")
            
            # Test password verification
            if st.button("🧪 Test Admin Login"):
                success, user_data, message = store.authenticate_user('admin', 'admin_password_change_immediately')
                if success:
                    st.success(f"✅ Direct auth successful: {user_data['name']}")
                else:
                    st.error(f"❌ Direct auth failed: {message}")
        else:
            st.error("❌ Database file not found")
            
    except Exception as e:
        st.error(f"❌ Debug error: {str(e)}")


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
        
        #### 🔑 Authentication
        
        Use the **Authentication** section in the sidebar to log in with your credentials.
        Your chat history and data will be completely isolated from other users.
        
        If you don't have access credentials, please contact your administrator.
        """)
        
        # Add authentication troubleshooting
        use_sqlite = os.getenv('USE_SQLITE', 'false').lower() == 'true'
        if use_sqlite and ENHANCED_SECURITY_AVAILABLE:
            with st.expander("🔧 SQLite Authentication Troubleshooting", expanded=False):
                st.markdown("""
                **If you're having trouble logging in with SQLite authentication:**
                
                1. **Default Admin Credentials:**
                   - Username: `admin`
                   - Password: `admin_password_change_immediately`
                
                2. **Check Migration Status:**
                   - SQLite database should be automatically populated
                   - Users are migrated from YAML config if it exists
                
                3. **Fallback to YAML:**
                   - Set `USE_SQLITE=false` in your .env file
                   - Restart the application
                
                4. **Manual User Creation:**
                   - Run: `python promote_admin.py` 
                   - Or check the User Management tab as admin
                """)
        
        st.info("👈 Use the sidebar to authenticate and start using the enhanced database platform")


def main():
    """FIXED VERSION - Main application function with enhanced authentication."""
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