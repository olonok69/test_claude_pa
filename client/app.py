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

page_icon_path = os.path.join(".", "icons", "playground.png")

st.set_page_config(
    page_title="Firecrawl & Google Search MCP Client",
    page_icon=page_icon_path,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Customize css
with open(os.path.join(".", ".streamlit", "style.css")) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def load_config():
    """Load authentication configuration from YAML file."""
    config_path = os.path.join("keys", "config.yaml")
    try:
        with open(config_path, "r") as file:
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
    st.title("🔥 Firecrawl & Google Search MCP Client")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Add  logo in the welcome message if available
        csm_logo_path = os.path.join(".", "icons", "Logo.png")
        if os.path.exists(csm_logo_path):
            # Center the logo
            col_a, col_b, col_c = st.columns([1, 1, 1])
            with col_b:
                st.image(csm_logo_path, width=120)
            st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
        ### Welcome to Firecrawl & Google Search MCP Client
        
        This application provides advanced web scraping, content extraction, and search capabilities 
        through Firecrawl and Google Search integration via Model Context Protocol (MCP) servers.
        
        **Please authenticate using the sidebar to access the application.**
        
        ---
        
        #### 🚀 Features Available After Login:
        
        - **💬 AI Chat Interface**: Interactive conversations with AI agents
        - **🔥 Firecrawl Integration**: Advanced web scraping and content extraction
        - **🔍 Google Web Search**: Comprehensive search across the web using Google Custom Search API
        - **📄 Content Extraction**: Clean webpage content extraction and analysis
        - **🔧 Tool Management**: Execute specialized scraping and search tools
        - **📊 Research Workflows**: Multi-step search and analysis capabilities
        - **🌐 Real-time Results**: Current web information and data extraction
        
        ---
        
        #### 🔥 Firecrawl Capabilities:
        
        **Web Scraping Tools:**
        - **firecrawl_scrape**: Extract content from single pages with advanced options
        - **firecrawl_batch_scrape**: Process multiple URLs simultaneously
        - **firecrawl_crawl**: Deep crawl websites with configurable depth
        - **firecrawl_map**: Discover all URLs on a website
        - **firecrawl_extract**: Extract structured data using LLM
        - **firecrawl_deep_research**: Conduct comprehensive research on topics
        - **firecrawl_generate_llmstxt**: Generate LLMs.txt files for websites
        
        **Features:**
        - Advanced content extraction with multiple formats (Markdown, HTML, Screenshot)
        - Intelligent crawling with depth control and URL filtering
        - Batch operations for processing multiple pages
        - LLM-powered structured data extraction
        - Support for both cloud and self-hosted Firecrawl instances
        
        ---
        
        #### 🔍 Google Search Capabilities:
        
        **Google Search Tools:**
        - **google-search**: Perform Google searches with customizable result counts
        - **read-webpage**: Extract and clean content from web pages
        - **Research workflows**: Multi-step search and analysis processes
        - **Content filtering**: Clean, readable text extraction
        
        ---
        
        #### 🔑 Authentication
        
        Use the **Authentication** section in the sidebar to log in with your credentials.
        
        If you don't have access credentials, please contact your administrator.
        """
        )

        # Add visual elements
        st.info("👈 Use the sidebar to authenticate and start using the platform")

        # Add quick stats about the platform
        with st.container():
            st.markdown("#### 📈 Platform Overview")
            col_a, col_b, col_c, col_d = st.columns(4)

            with col_a:
                st.metric(
                    label="🔥 Firecrawl Tools",
                    value="8+",
                    help="Advanced scraping tools",
                )

            with col_b:
                st.metric(
                    label="🔍 Search Tools", value="2+", help="Google Search tools"
                )

            with col_c:
                st.metric(
                    label="🔌 MCP Servers", value="2", help="Firecrawl & Google Search"
                )

            with col_d:
                st.metric(
                    label="🤖 AI Models", value="2+", help="OpenAI and Azure OpenAI"
                )

        # Add usage examples
        with st.expander("💡 Example Queries", expanded=False):
            st.markdown(
                """
            **Firecrawl Web Scraping:**
            - "Scrape the content from https://example.com"
            - "Crawl the entire documentation site at docs.example.com"
            - "Extract all product information from this e-commerce page"
            - "Map all URLs on example.com website"
            - "Do deep research on renewable energy trends"
            
            **Google Search & Analysis:**
            - "Search for the latest AI developments and extract key insights"
            - "Find Python tutorials and summarize the best resources"
            - "Search for climate change reports and analyze the findings"
            
            **Combined Workflows:**
            - "Search for top AI companies, then scrape their websites for job openings"
            - "Find documentation about React hooks, then extract code examples"
            - "Research quantum computing companies and extract their product offerings"
            """
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
            st.error(
                "❌ Authentication failed. Please check your credentials and try again."
            )

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
