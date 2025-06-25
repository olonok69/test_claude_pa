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

# Apply nest_asyncio to allow nested asyncio event loops (needed for Streamlit's execution model)
nest_asyncio.apply()

page_icon_path = os.path.join('.', 'icons', 'playground.png')

st.set_page_config(
    page_title="CSM MCP Servers",
    page_icon=page_icon_path,
    layout='wide',
    initial_sidebar_state="expanded"
)

# Customize css
with open(os.path.join('.', '.streamlit', 'style.css')) as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def load_config():
    """Load authentication configuration from YAML file."""
    config_path = os.path.join('keys', 'config.yaml')
    try:
        with open(config_path, 'r') as file:
            return yaml.load(file, Loader=SafeLoader)
    except FileNotFoundError:
        st.error("❌ Configuration file not found at keys/config.yaml")
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
        st.markdown("""
        ### Welcome to CSM MCP Servers
        
        This application provides AI-powered interactions with **Neo4j graph databases**, 
        **HubSpot CRM systems**, and **MSSQL databases** through Model Context Protocol (MCP) servers.
        
        **Please authenticate using the sidebar to access the application.**
        
        ---
        
        #### 🚀 Features Available After Login:
        
        - **💬 AI Chat Interface**: Interactive conversations with AI agents
        - **🗄️ Neo4j Database Operations**: Query and manage graph data with Cypher
        - **🏢 HubSpot CRM Integration**: Access contacts, companies, deals, tickets, and more
        - **🗃️ MSSQL Database Operations**: Execute SQL queries, explore tables, and manage data
        - **🔧 Tool Management**: Execute specialized MCP tools across all platforms
        - **📊 Real-time Analytics**: Monitor and analyze your data across databases
        - **🔄 Cross-Platform Integration**: Compare and sync data between systems
        
        ---
        
        #### 🗄️ Database Capabilities:
        
        **Neo4j Graph Database:**
        - Schema discovery and visualization
        - Complex relationship queries with Cypher
        - Graph data creation and modification
        - Performance analytics and insights
        
        **HubSpot CRM System:**
        - Contact and company management
        - Deal tracking and pipeline analysis
        - Ticket management and support workflows
        - Custom properties and associations
        
        **MSSQL Database:**
        - Table exploration and schema analysis
        - SQL query execution with proper syntax
        - Sample data retrieval and analysis
        - Data modification and management operations
        
        ---
        
        #### 🔑 Authentication
        
        Use the **Authentication** section in the sidebar to log in with your credentials.
        
        If you don't have access credentials, please contact your administrator.
        """)
        
        # Add visual elements with updated info
        st.info("👈 Use the sidebar to authenticate and start using the multi-database platform")
        
        # Add quick stats about the platform
        with st.container():
            st.markdown("#### 📈 Platform Overview")
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric(
                    label="🗄️ Database Types",
                    value="3",
                    help="Neo4j, HubSpot CRM, MSSQL"
                )
            
            with col_b:
                st.metric(
                    label="🧰 Tool Categories", 
                    value="25+",
                    help="Graph, CRM, SQL operations"
                )
            
            with col_c:
                st.metric(
                    label="🔌 MCP Servers",
                    value="3",
                    help="Specialized protocol servers"
                )



def main():
    """Main application function with authentication."""
    try:
        # Initialize session state for event loop
        if "loop" not in st.session_state:
            st.session_state.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(st.session_state.loop)
        
        # Register shutdown handler
        atexit.register(on_shutdown)
        
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