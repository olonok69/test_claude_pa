import streamlit as st
import asyncio
import os
import nest_asyncio
import atexit
import yaml
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
import logging
from services.chat_service import init_session
from utils.async_helpers import on_shutdown
from apps import mcp_app

# Enhanced security imports (with fallback)
try:
    from utils.enhanced_security_config import StreamlitSecureAuth, SecurityConfig
    ENHANCED_SECURITY_AVAILABLE = True
except ImportError:
    ENHANCED_SECURITY_AVAILABLE = False
    print("⚠️  Enhanced security module not available. Using YAML fallback.")

# Apply nest_asyncio to allow nested asyncio event loops
nest_asyncio.apply()

page_icon_path = os.path.join('.', 'icons', 'playground.png')

st.set_page_config(
    page_title="The CloserStill Media - MCP Client",
    page_icon=page_icon_path,
    layout='wide',
    initial_sidebar_state="expanded"
)

# FIXED: Customize css with proper encoding
css_path = os.path.join('.', '.streamlit', 'style.css')
if os.path.exists(css_path):
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except UnicodeDecodeError:
        # Fallback for encoding issues
        try:
            with open(css_path, 'r', encoding='latin1') as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        except Exception as e:
            print(f"Warning: Could not load CSS file: {str(e)}")


def load_config():
    """Load authentication configuration from secure storage or YAML fallback."""
    try:
        # Check if SQLite is enabled and available
        use_sqlite = os.getenv('USE_SQLITE', 'false').lower() == 'true'
        
        if use_sqlite and ENHANCED_SECURITY_AVAILABLE:
            print("🔒 Using SQLite authentication")
            # Use enhanced SQLite authentication
            secure_auth = StreamlitSecureAuth('sqlite')
            return secure_auth.get_config_for_streamlit_authenticator()
        else:
            print("📋 Using YAML authentication")
            # Fallback to YAML configuration
            config_path = os.path.join('keys', 'config.yaml')
            if not os.path.exists(config_path):
                st.error("❌ Configuration file not found at keys/config.yaml")
                st.stop()
            
            # FIXED: Read YAML with proper encoding
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.load(file, Loader=SafeLoader)
                
    except FileNotFoundError:
        st.error("❌ Configuration not found. Please check your setup.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading configuration: {str(e)}")
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
    """Handle user authentication in the sidebar."""
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
            st.success(f"✅ Welcome, **{st.session_state['name']}**!")
            st.info(f"👤 Username: {st.session_state['username']}")
            
            # Add logout button
            authenticator.logout("Logout")
            
            # Add separator
            st.markdown("---")
    
    # Log authentication status
    logging.info(
        f'Authentication Status: {st.session_state["authentication_status"]}, '
        f'Name: {st.session_state["name"]}, '
        f'Username: {st.session_state["username"]}'
    )
    
    return st.session_state["authentication_status"]


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
        
        - **💬 AI Chat Interface**: Interactive conversations with AI agents
        - **🗃️ MSSQL Database Operations**: Execute SQL queries, explore tables, and manage data
        - **🔧 Tool Management**: Execute specialized MCP tools for database operations
        - **📊 Real-time Analytics**: Monitor and analyze your data
        - **🔄 Database Integration**: Comprehensive SQL Server connectivity and management
        
        ---
        
        #### 🗃️ Database Capabilities:
        
        **MSSQL Database:**
        - Table exploration and schema analysis
        - SQL query execution with proper SQL Server syntax
        - Sample data retrieval and analysis
        - Data modification and management operations
        - Comprehensive database operations through MCP tools
        
        **Available Tools:**
        - **execute_sql**: Run SQL queries with proper SQL Server syntax
        - **list_tables**: Explore database structure and available tables
        - **describe_table**: Get detailed information about table schemas
        - **get_table_sample**: Retrieve sample data from tables
        
        ---
        
        #### 🔑 Authentication
        
        Use the **Authentication** section in the sidebar to log in with your credentials.
        
        If you don't have access credentials, please contact your administrator.
        """)
        
        # Add visual elements with updated info
        st.info("👈 Use the sidebar to authenticate and start using the database platform")
        
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
                    label="🔌 MCP Servers",
                    value="1",
                    help="MSSQL specialized protocol server"
                )
        
        # Add usage examples
        with st.expander("💡 Example Queries", expanded=False):
            st.markdown("""
            **Database Exploration:**
            - "Show me all tables in the database"
            - "Describe the structure of the users table"
            - "Give me 5 sample records from the products table"
            
            **Data Analysis:**
            - "Count all records in the orders table"
            - "Find all customers from New York"
            - "Show me the top 10 products by sales"
            
            **SQL Operations:**
            - "Execute: SELECT TOP 5 * FROM employees ORDER BY hire_date DESC"
            - "Get all orders from the last 30 days"
            - "Find the average price of products in each category"
            
            **Advanced Queries:**
            - "Show me sales trends by month"
            - "Find customers who haven't placed orders recently"
            - "Analyze product performance across different regions"
            """)


def main():
    """Main application function with authentication."""
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
        # Still show authentication if there's an error
        if st.session_state.get("authentication_status") is None:
            show_authentication_required_message()


if __name__ == "__main__":
    main()