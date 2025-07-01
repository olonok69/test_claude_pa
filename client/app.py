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
    page_title="Google Search MCP Client",
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
    st.title("🔍 Google Search MCP Client")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ### Welcome to Google Search MCP Client
        
        This application provides AI-powered web search and content extraction through 
        **Google Custom Search API** integration via Model Context Protocol (MCP) servers.
        
        **Please authenticate using the sidebar to access the application.**
        
        ---
        
        #### 🚀 Features Available After Login:
        
        - **💬 AI Chat Interface**: Interactive conversations with AI agents
        - **🔍 Google Web Search**: Comprehensive search across the web using Google Custom Search API
        - **📄 Content Extraction**: Clean webpage content extraction and analysis
        - **🔧 Tool Management**: Execute specialized Google Search MCP tools
        - **📊 Research Workflows**: Combined search and content analysis capabilities
        - **🌐 Real-time Results**: Current web information and news
        
        ---
        
        #### 🔍 Google Search Capabilities:
        
        **Web Search Tools:**
        - **google-search**: Perform Google searches with customizable result counts (1-10 results)
        - **read-webpage**: Extract and clean content from web pages with automatic formatting
        - **Research workflows**: Multi-step search and analysis processes
        - **Content filtering**: Clean, readable text extraction from web pages
        
        **Search Features:**
        - Real-time web search using Google Custom Search API
        - Configurable result counts for targeted or comprehensive searches
        - Content extraction with automatic cleanup (removes scripts, ads, navigation)
        - Support for any publicly accessible web content
        - Cross-reference multiple sources for comprehensive research
        
        **AI-Powered Analysis:**
        - Natural language queries for web search
        - Intelligent content summarization and analysis
        - Multi-source information synthesis
        - Context-aware search result interpretation
        
        ---
        
        #### 🔑 Authentication
        
        Use the **Authentication** section in the sidebar to log in with your credentials.
        
        If you don't have access credentials, please contact your administrator.
        """)
        
        # Add visual elements with updated info
        st.info("👈 Use the sidebar to authenticate and start using the Google Search platform")
        
        # Add quick stats about the platform
        with st.container():
            st.markdown("#### 📈 Platform Overview")
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric(
                    label="🔍 Search Tools",
                    value="2",
                    help="Web search and content extraction"
                )
            
            with col_b:
                st.metric(
                    label="🌐 Data Sources", 
                    value="Web",
                    help="Google Custom Search API"
                )
            
            with col_c:
                st.metric(
                    label="🔌 MCP Servers",
                    value="1",
                    help="Google Search MCP server"
                )
        
        # Add usage examples
        with st.expander("💡 Example Queries", expanded=False):
            st.markdown("""
            **Web Search Examples:**
            - "Search for the latest developments in artificial intelligence"
            - "Find recent news about climate change"
            - "What are the current trends in web development?"
            - "Search for Python programming tutorials"
            
            **Content Extraction Examples:**
            - "Search for climate reports and read the full content from the first result"
            - "Find the latest tech news and extract content from the articles"
            - "Search for React documentation and read the official guide"
            
            **Research Workflows:**
            - "Research the current state of renewable energy technology"
            - "Find and analyze multiple sources about cryptocurrency trends"
            - "Search for best practices in software engineering and summarize them"
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