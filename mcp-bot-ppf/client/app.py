import streamlit as st
import os
from datetime import datetime
import nest_asyncio
import atexit
import yaml
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
import logging

# Apply nest_asyncio
nest_asyncio.apply()

# Page configuration
st.set_page_config(
    page_title="PPF Europe Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide default navigation
st.markdown(
    """
<style>
    /* Hide Streamlit's default page navigation */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    section[data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    [data-testid="stSidebarNav"] > ul {
        display: none !important;
    }
    
    [data-testid="stSidebarNav"] > div:first-child {
        display: none !important;
    }
    
    .css-1d391kg {
        padding-top: 1rem;
    }
    
    [kind="navlink"] {
        display: none !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Authentication functions
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
    """Handle user authentication and return status."""
    config = load_config()
    initialize_authentication_state()

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )

    return authenticator, config


# Navigation functions
def navigate_to_page(page_path):
    """Navigate to a specific page"""
    st.switch_page(page_path)


# Main application
def main():
    """Main application with integrated navigation."""

    # Initialize authentication
    authenticator, config = handle_authentication()

    # Create sidebar with authentication and navigation
    with st.sidebar:
        # Logo section
        logo_path = os.path.join(".", "icons", "Logo.png")
        if os.path.exists(logo_path):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(logo_path, width=60)
            with col2:
                st.markdown(
                    """
                <div style="padding-top: 10px;">
                    <h3 style="margin: 0; color: #2F2E78;">PPF Europe</h3>
                    <p style="margin: 0; font-size: 12px; color: #666;">Analysis Platform</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        # Authentication section
        st.markdown("## 🔐 Authentication")

        if st.session_state["authentication_status"] is None:
            try:
                authenticator.login()
            except Exception as e:
                st.error(f"Authentication error: {str(e)}")

            if st.session_state["authentication_status"] is False:
                st.error("❌ Username/password is incorrect")
            elif st.session_state["authentication_status"] is None:
                st.warning("⚠️ Please enter your username and password")

        elif st.session_state["authentication_status"]:
            st.success(f"✅ Welcome, **{st.session_state['name']}**!")
            st.info(f"👤 Username: {st.session_state['username']}")

            # Logout button
            authenticator.logout("Logout")

            st.markdown("---")

            # Navigation section (only shown when authenticated)
            st.title("🌾 Navigation")

            # Supply & Demand Section
            with st.expander("📊 Supply & Demand", expanded=True):
                if st.button("🌾 Production", use_container_width=True):
                    navigate_to_page("wheat_pages/1_wheat_production.py")
                if st.button("📦 Exports", use_container_width=True):
                    navigate_to_page("wheat_pages/2_wheat_exports.py")
                if st.button("📥 Imports", use_container_width=True):
                    navigate_to_page("wheat_pages/3_wheat_imports.py")
                if st.button("🏢 Ending Stocks", use_container_width=True):
                    navigate_to_page("wheat_pages/4_wheat_stocks.py")
                if st.button("📊 Stock-to-Use Ratio", use_container_width=True):
                    navigate_to_page("wheat_pages/5_stock_to_use_ratio.py")
                if st.button("🌾 Acreage", use_container_width=True):
                    navigate_to_page("wheat_pages/6_wheat_acreage.py")
                if st.button("🌱 Yield", use_container_width=True):
                    navigate_to_page("wheat_pages/7_wheat_yield.py")

            # MCP Tools Section
            with st.expander("🤖 AI & MCP Tools", expanded=False):
                if st.button("💬 MCP Chat Interface", use_container_width=True):
                    navigate_to_page("mcp_pages/mcp_app.py")
                if st.button("🔥 Firecrawl Tools", use_container_width=True):
                    navigate_to_page("mcp_pages/mcp_app.py")
                if st.button("🔍 Google Search", use_container_width=True):
                    navigate_to_page("mcp_pages/mcp_app.py")
                if st.button("🔮 Perplexity Search", use_container_width=True):
                    navigate_to_page("mcp_pages/mcp_app.py")

            # Future sections
            with st.expander("📈 Analysis (Coming Soon)", expanded=False):
                st.info(
                    "Price Analysis, Trade Flows, and Market Forecasting coming soon!"
                )

    # Main page content
    if st.session_state["authentication_status"]:
        show_authenticated_content()
    else:
        show_unauthenticated_content()


def show_authenticated_content():
    """Show content for authenticated users."""
    st.title("🌾 PPF Europe Analysis Platform")
    st.markdown("### Integrated Wheat Market Analysis & AI Tools")

    # Check database status
    db_exists = os.path.exists("wheat_production.db")

    if db_exists:
        st.success("✅ Database is connected and ready")
    else:
        st.warning(
            "⚠️ Database not found. Please run `python database_setup.py` to initialize the database."
        )

    # Dashboard overview
    st.markdown("---")
    st.markdown("## 📊 Available Dashboards")

    # Supply & Demand dashboards
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        ### 📊 Supply & Demand Analysis
        - **🌾 Production**: Track global wheat production
        - **📦 Exports**: Monitor export volumes and trends
        - **📥 Imports**: Analyze import patterns
        - **🏢 Stocks**: Ending stocks and reserves
        - **📊 S/U Ratio**: Stock-to-use analysis
        - **🌾 Acreage**: Area harvested trends
        - **🌱 Yield**: Productivity analysis
        """
        )

        if st.button("Start Supply & Demand Analysis", type="primary"):
            st.switch_page("wheat_pages/1_wheat_production.py")

    with col2:
        st.markdown(
            """
        ### 🤖 AI & MCP Tools
        - **💬 Chat Interface**: AI-powered conversations
        - **🔥 Firecrawl**: Web scraping and extraction
        - **🔍 Google Search**: Comprehensive web search
        - **🔮 Perplexity**: AI-powered search
        - **📄 Content Analysis**: Extract and analyze
        - **🔧 Tool Management**: Execute specialized tools
        - **💾 Smart Caching**: Optimized performance
        """
        )

        if st.button("Launch AI Tools", type="primary"):
            st.switch_page("mcp_pages/mcp_app.py")

    # Key metrics if database exists
    if db_exists:
        st.markdown("---")
        st.markdown("## 📈 Key Metrics")

        from wheat_helpers.database_helper import WheatProductionDB

        db = WheatProductionDB()

        # Get latest data
        production_data = db.get_all_production_data()
        export_data = db.get_all_export_data()
        import_data = db.get_all_import_data()
        stocks_data = db.get_all_stocks_data()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if production_data and "WORLD" in production_data:
                world_prod = production_data["WORLD"].get("2024/2025", 0)
                st.metric("Global Production", f"{world_prod:.1f} Mt")

        with col2:
            if export_data and "TOTAL MAJOR EXPORTERS" in export_data:
                total_exports = export_data["TOTAL MAJOR EXPORTERS"].get("2024/2025", 0)
                st.metric("Major Exports", f"{total_exports:.1f} Mt")

        with col3:
            if import_data and "TOTAL MAJOR IMPORTERS" in import_data:
                total_imports = import_data["TOTAL MAJOR IMPORTERS"].get("2024/2025", 0)
                st.metric("Major Imports", f"{total_imports:.1f} Mt")

        with col4:
            if stocks_data and "WORLD" in stocks_data:
                world_stocks = stocks_data["WORLD"].get("2024/2025", 0)
                st.metric("Global Stocks", f"{world_stocks:.1f} Mt")


def show_unauthenticated_content():
    """Show content for unauthenticated users."""
    st.title("🌾 PPF Europe Analysis Platform")
    st.markdown("### Welcome to the Integrated Analysis Platform")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Logo
        logo_path = os.path.join(".", "icons", "Logo.png")
        if os.path.exists(logo_path):
            col_a, col_b, col_c = st.columns([1, 1, 1])
            with col_b:
                st.image(logo_path, width=120)
            st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
        This platform combines comprehensive wheat market analysis with advanced AI-powered tools 
        for web scraping, search, and content analysis.
        
        **Please authenticate using the sidebar to access the platform.**
        
        ---
        
        #### 🚀 Features Available After Login:
        
        **📊 Supply & Demand Analysis**
        - Global wheat production tracking
        - Export/import monitoring
        - Stock levels and S/U ratios
        - Acreage and yield analysis
        
        **🤖 AI & MCP Tools**
        - AI chat interface
        - Firecrawl web scraping
        - Google Search integration
        - Perplexity AI search
        - Content extraction and analysis
        
        ---
        
        #### 🔑 Authentication
        
        Use the **Authentication** section in the sidebar to log in with your credentials.
        """
        )

        st.info("👈 Use the sidebar to authenticate and start using the platform")


if __name__ == "__main__":
    main()
